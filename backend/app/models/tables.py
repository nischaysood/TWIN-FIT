"""SQLAlchemy tables — the SaaS backbone."""
import uuid
from datetime import datetime

from sqlalchemy import (Column, String, DateTime, Integer, Float, Boolean,
                        Text, JSON, Index)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


class Merchant(Base):
    __tablename__ = "merchants"

    id          = Column(String, primary_key=True, default=_uuid)
    name        = Column(String, nullable=False)
    api_key     = Column(String, unique=True, nullable=False, index=True)
    brand_chart = Column(String, default="generic")      # default size chart
    plan        = Column(String, default="free")          # free | starter | growth
    monthly_tryon_quota = Column(Integer, default=50)
    tryons_this_month   = Column(Integer, default=0)
    active      = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


class TryonJob(Base):
    __tablename__ = "tryon_jobs"

    id          = Column(String, primary_key=True, default=_uuid)
    merchant_id = Column(String, index=True, nullable=True)
    status      = Column(String, default="queued")   # queued|processing|done|failed
    engine      = Column(String, nullable=True)
    result_url  = Column(Text, nullable=True)
    error       = Column(Text, nullable=True)
    garment_url = Column(Text, nullable=True)
    category    = Column(String, nullable=True)
    latency_s   = Column(Float, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GarmentCache(Base):
    """One analysis per unique garment image — shoppers 2..N wait 0ms."""
    __tablename__ = "garment_cache"

    url_hash    = Column(String, primary_key=True)   # sha256 of image URL
    image_url   = Column(Text, nullable=False)
    result      = Column(JSON, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)


class Event(Base):
    """Telemetry — the Stage-3 flywheel starts here."""
    __tablename__ = "events"

    id          = Column(String, primary_key=True, default=_uuid)
    merchant_id = Column(String, index=True, nullable=True)
    kind        = Column(String, nullable=False, index=True)
    # size_recommended | garment_analyzed | tryon_started | tryon_completed
    # | tryon_failed | fit_feedback
    payload     = Column(JSON, default=dict)
    created_at  = Column(DateTime, default=datetime.utcnow, index=True)


Index("ix_events_kind_created", Event.kind, Event.created_at)
