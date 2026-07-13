"""
Try-on job store — DB-backed when DATABASE_URL is set, in-memory otherwise.
Both expose the same three functions, so callers never care which is active.
"""
import uuid
from datetime import datetime
from typing import Optional

from app.core.db import db_enabled, db_session

# ── in-memory fallback (local dev, zero config) ──────────────────────────
_mem_jobs: dict = {}


def create_job(merchant_id: Optional[str] = None,
               garment_url: Optional[str] = None,
               category: Optional[str] = None) -> str:
    if db_enabled():
        from app.models.tables import TryonJob
        with db_session() as s:
            job = TryonJob(merchant_id=merchant_id, garment_url=garment_url,
                           category=category, status="queued")
            s.add(job)
            s.flush()
            return job.id

    job_id = str(uuid.uuid4())
    _mem_jobs[job_id] = {
        "status": "queued", "result_url": None, "error": None,
        "engine": None, "created_at": datetime.utcnow().isoformat(),
    }
    return job_id


def get_job(job_id: str) -> Optional[dict]:
    if db_enabled():
        from app.models.tables import TryonJob
        with db_session() as s:
            job = s.get(TryonJob, job_id)
            if not job:
                return None
            return {
                "status": job.status, "result_url": job.result_url,
                "error": job.error, "engine": job.engine,
            }
    return _mem_jobs.get(job_id)


def update_job(job_id: str, **kwargs):
    if db_enabled():
        from app.models.tables import TryonJob
        with db_session() as s:
            job = s.get(TryonJob, job_id)
            if job:
                for k, v in kwargs.items():
                    if hasattr(job, k):
                        setattr(job, k, v)
        return
    if job_id in _mem_jobs:
        _mem_jobs[job_id].update(kwargs)
