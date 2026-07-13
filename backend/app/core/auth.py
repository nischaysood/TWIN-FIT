"""
Multi-tenant auth — X-API-Key header (or ?key= for iframe embeds).

REQUIRE_API_KEY=false (default): requests without a key run as the demo
merchant — local dev and the public demo keep working unchanged.
REQUIRE_API_KEY=true (hosted): unknown/missing keys get 401, over-quota 429.
"""
from typing import Optional

from fastapi import Header, HTTPException, Query

from app.core.config import settings
from app.core.db import db_enabled, db_session


class MerchantCtx:
    def __init__(self, id=None, name="demo", brand_chart="generic",
                 plan="free", over_quota=False):
        self.id = id
        self.name = name
        self.brand_chart = brand_chart
        self.plan = plan
        self.over_quota = over_quota


DEMO = MerchantCtx()


async def get_merchant(
    x_api_key: Optional[str] = Header(default=None),
    key: Optional[str] = Query(default=None),
) -> MerchantCtx:
    api_key = x_api_key or key

    if not db_enabled():
        return DEMO

    if not api_key:
        if settings.REQUIRE_API_KEY:
            raise HTTPException(401, "Missing API key (X-API-Key header)")
        api_key = settings.DEMO_API_KEY

    from app.models.tables import Merchant
    with db_session() as s:
        m = s.query(Merchant).filter_by(api_key=api_key, active=True).first()
        if not m:
            if settings.REQUIRE_API_KEY:
                raise HTTPException(401, "Invalid API key")
            return DEMO
        return MerchantCtx(
            id=m.id, name=m.name, brand_chart=m.brand_chart, plan=m.plan,
            over_quota=(m.tryons_this_month >= m.monthly_tryon_quota),
        )


def count_tryon(merchant_id: Optional[str]):
    """Increment usage — this number becomes the Shopify metered bill."""
    if not (db_enabled() and merchant_id):
        return
    from app.models.tables import Merchant
    with db_session() as s:
        m = s.get(Merchant, merchant_id)
        if m:
            m.tryons_this_month += 1


def seed_demo_merchant():
    """Ensure a demo merchant exists so the public demo always works."""
    if not db_enabled():
        return
    from app.models.tables import Merchant
    with db_session() as s:
        if not s.query(Merchant).filter_by(api_key=settings.DEMO_API_KEY).first():
            s.add(Merchant(name="TwinFit Demo Store",
                           api_key=settings.DEMO_API_KEY,
                           brand_chart="myntra",
                           monthly_tryon_quota=1000))
