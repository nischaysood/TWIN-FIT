"""
Telemetry — every product signal lands in the events table.
This is the seed of the Stage-3 fit-data flywheel. Free to collect now,
impossible to backfill later.

No DB configured → events are dropped silently (local dev stays clean).
"""
import logging

from app.core.db import db_enabled, db_session

logger = logging.getLogger("twinfit.telemetry")

from typing import Optional

def log_event(kind: str, merchant_id: Optional[str] = None, **payload):
    if not db_enabled():
        logger.debug("event (no db): %s %s", kind, payload)
        return
    try:
        from app.models.tables import Event
        with db_session() as s:
            s.add(Event(kind=kind, merchant_id=merchant_id, payload=payload))
    except Exception as e:  # telemetry must never break the product
        logger.warning("event log failed: %s", e)
