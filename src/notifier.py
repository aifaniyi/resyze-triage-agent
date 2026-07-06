import logging
import time
import uuid

import nats

from src.config import settings
from src.proto import email_pb2

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

    event = email_pb2.EmailEvent(
        event_id=str(uuid.uuid4()),
        type=email_pb2.ALERT_TRIAGE_REPORT,
        recipient=settings.alert_recipient_email,
        timestamp=int(time.time()),
    )
    event.data["alert_name"] = alert_name
    event.data["service"] = service
    event.data["severity"] = severity
    event.data["report"] = report

    await _nc.publish(settings.nats_mailer_subject, event.SerializeToString())
    logger.info("Triage report sent for alert=%s service=%s", alert_name, service)
