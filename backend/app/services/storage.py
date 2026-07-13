"""
Result image storage — Cloudflare R2 (S3-compatible), env-gated.

Configured  → upload PNG, return a public URL (tiny API responses).
Unconfigured → return None; callers keep using base64 data URIs.
"""
import base64
import uuid
from typing import Optional

from app.core.config import settings

_client = None


def storage_enabled() -> bool:
    return bool(settings.R2_ENDPOINT and settings.R2_ACCESS_KEY_ID
                and settings.R2_SECRET_ACCESS_KEY and settings.R2_BUCKET)


def _get_client():
    global _client
    if _client is None:
        import boto3
        _client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
    return _client


def store_result_image(image_data_uri_or_b64: str) -> Optional[str]:
    """Upload a try-on result; returns public URL or None if storage is off."""
    if not storage_enabled():
        return None

    raw = image_data_uri_or_b64
    if raw.startswith("data:"):
        raw = raw.split(",", 1)[1]
    png_bytes = base64.b64decode(raw)

    key = f"tryons/{uuid.uuid4()}.png"
    client = _get_client()
    client.put_object(
        Bucket=settings.R2_BUCKET, Key=key,
        Body=png_bytes, ContentType="image/png",
    )
    base = (settings.R2_PUBLIC_BASE_URL or "").rstrip("/")
    if base:
        # public bucket: stable public URL
        return f"{base}/{key}"
    # private bucket (e.g. Backblaze B2 free tier): presigned URL, 7-day expiry
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.R2_BUCKET, "Key": key},
        ExpiresIn=7 * 24 * 3600,
    )
