from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.schemas import GarmentAnalysisResponse
from app.services.garment_service import analyze_garment

router = APIRouter()

class GarmentAnalysisRequest(BaseModel):
    image_url: str

@router.post("/analyze", response_model=GarmentAnalysisResponse)
async def analyze_garment_endpoint(req: GarmentAnalysisRequest):
    try:
        result = await analyze_garment(req.image_url)
        return GarmentAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Garment analysis failed: {str(e)}")
