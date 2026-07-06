import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

from src import notifier
from src.agent import investigate_alert
from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await notifier.connect()
    yield
    await notifier.disconnect()


app = FastAPI(title="resyze-triage-agent", lifespan=lifespan)


class GrafanaAlert(BaseModel):
    status: str
    alerts: list[dict]


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/webhook/alert")
async def receive_alert(payload: GrafanaAlert, background_tasks: BackgroundTasks):
    """Receive Grafana alert webhook and trigger triage investigation."""
    firing = [a for a in payload.alerts if a.get("status") == "firing"]
    logger.info("Received %d firing alert(s)", len(firing))

    for alert in firing:
        background_tasks.add_task(triage_alert, alert)

    return {"accepted": len(firing)}


async def triage_alert(alert: dict):
    """Investigate a single alert and send the report."""
    labels = alert.get("labels", {})
    alert_name = labels.get("alertname", "unknown")
    service = labels.get("service", "unknown")
    severity = labels.get("severity", "unknown")

    logger.info("Starting triage for alert=%s service=%s", alert_name, service)

    try:
        report = await investigate_alert(alert)
        await notifier.send_triage_report(alert_name, service, severity, report)
        logger.info("Triage complete for alert=%s", alert_name)
    except Exception:
        logger.exception("Triage failed for alert=%s", alert_name)
