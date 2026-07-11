from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class Brand(str, Enum):
    HM       = "h&m"
    ZARA     = "zara"
    MYNTRA   = "myntra"
    GENERIC  = "generic"

class SizeRecommendationRequest(BaseModel):
    height_cm: float  = Field(..., gt=100, lt=250, example=165)
    weight_kg: float  = Field(..., gt=30,  lt=200, example=60)
    chest_cm:  float  = Field(..., gt=60,  lt=150, example=88)
    waist_cm:  float  = Field(..., gt=50,  lt=140, example=72)
    hip_cm:    float  = Field(..., gt=60,  lt=160, example=96)
    brand:     Brand  = Field(default=Brand.GENERIC)
    category:  str    = Field(default="top", example="kurta")

class SizeRecommendationResponse(BaseModel):
    recommended_size:   str
    confidence_pct:     float
    fit_notes:          str
    size_chart_used:    str
    alternate_size:     Optional[str] = None
    return_risk:        str

class GarmentAnalysisResponse(BaseModel):
    category:      str
    sleeve_type:   str
    fit_type:      str
    fabric_est:    str
    color:         str
    gender_target: str
    try_on_ready:  bool

class TryOnStatus(str, Enum):
    QUEUED     = "queued"
    PROCESSING = "processing"
    DONE       = "done"
    FAILED     = "failed"

class TryOnRequest(BaseModel):
    user_photo_b64:    str   = Field(..., description="Base64 encoded user photo")
    garment_image_url: str   = Field(..., description="URL of the garment image")
    garment_category:  str   = Field(default="top")

class TryOnJobResponse(BaseModel):
    job_id:   str
    status:   TryOnStatus
    message:  str

class TryOnResultResponse(BaseModel):
    job_id:       str
    status:       TryOnStatus
    result_url:   Optional[str] = None
    error:        Optional[str] = None
    engine:       Optional[str] = None  # "IDM-VTON @ AMD MI300X" or "FLUX Kontext @ Fireworks"
