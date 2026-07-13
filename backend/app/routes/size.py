from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import SizeRecommendationRequest, SizeRecommendationResponse
from app.services.size_service import recommend_size
from app.services.telemetry import log_event
from app.core.auth import get_merchant, MerchantCtx

router = APIRouter()

@router.post("/recommend", response_model=SizeRecommendationResponse)
def get_size_recommendation(req: SizeRecommendationRequest,
                            merchant: MerchantCtx = Depends(get_merchant)):
    try:
        result = recommend_size(
            height_cm=req.height_cm,
            weight_kg=req.weight_kg,
            chest_cm=req.chest_cm,
            waist_cm=req.waist_cm,
            hip_cm=req.hip_cm,
            brand=req.brand.value,
            category=req.category,
        )
        log_event("size_recommended", merchant.id,
                  brand=req.brand.value, category=req.category,
                  size=result["recommended_size"],
                  confidence=result["confidence_pct"],
                  risk=result["return_risk"])
        return SizeRecommendationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/brands")
def list_supported_brands():
    return {
        "brands": ["h&m", "zara", "myntra", "generic"],
        "categories": ["top", "kurta", "kurti", "dress", "bottom", "jeans", "jacket"]
    }
