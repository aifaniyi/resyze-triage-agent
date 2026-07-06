import json
import logging
import uuid

import nats

from src.config import settings

logger = logging.getLogger(__name__)

_nc = None


async def connect():
    global _nc
    _nc = await nats.connect(settings.nats_url)
    logger.info("Connected to NATS at %s", settings.nats_url)


async def disconnect():
    global _nc
    if _nc:
        await _nc.drain()


async def send_triage_report(alert_name: str, service: str, severity: str, report: str):
    """Publish a triage report email via NATS to resyze-mailer."""
    if not _nc:
        logger.error("NATS not connected, cannot send triage report")
        return

    payload = {
        "id": str(uuid.uuid4()),
        "type": "alert_triage_report",
        "to": settings.alert_recipient_email,
        "subject": f"[{severity.upper()}] Triage Report: {alert_name} ({service})",
        "data": {
            "alert_name": alert_name,
            "service": service,
            "severity": severity,
            "report": report,
        },
    }

    await _nc.publish(settings.nats_mailer_subject, json.dumps(payload).encode())
    logger.info("Triage report sent for alert=%s service=%s", alert_name, service)
