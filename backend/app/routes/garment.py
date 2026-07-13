from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.models.schemas import GarmentAnalysisResponse
from app.services.garment_service import analyze_garment
from app.services.telemetry import log_event
from app.core.auth import get_merchant, MerchantCtx

router = APIRouter()

class GarmentAnalysisRequest(BaseModel):
    image_url: str

@router.post("/analyze", response_model=GarmentAnalysisResponse)
async def analyze_garment_endpoint(req: GarmentAnalysisRequest,
                                   merchant: MerchantCtx = Depends(get_merchant)):
    try:
        result = await analyze_garment(req.image_url)
        log_event("garment_analyzed", merchant.id,
                  category=result.get("category"),
                  mock=bool(result.get("_mock")))
        return GarmentAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Garment analysis failed: {str(e)}")
