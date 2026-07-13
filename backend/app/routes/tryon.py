from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from app.models.schemas import TryOnRequest, TryOnJobResponse, TryOnResultResponse
from app.services.tryon_service import create_job, get_job, run_tryon_async
from app.core.auth import get_merchant, MerchantCtx

router = APIRouter()


@router.post("/start", response_model=TryOnJobResponse)
async def start_tryon(req: TryOnRequest, background_tasks: BackgroundTasks,
                      merchant: MerchantCtx = Depends(get_merchant)):
    if merchant.over_quota:
        raise HTTPException(
            429, "Monthly try-on quota reached — upgrade your plan at twinfit.app")

    job_id = create_job(merchant_id=merchant.id,
                        garment_url=req.garment_image_url,
                        category=req.garment_category)
    background_tasks.add_task(
        run_tryon_async,
        job_id=job_id,
        user_photo_b64=req.user_photo_b64,
        garment_image_url=req.garment_image_url,
        garment_category=req.garment_category,
        merchant_id=merchant.id,
    )
    return TryOnJobResponse(
        job_id=job_id,
        status="queued",
        message="Try-on job started. Poll /api/tryon/status/{job_id} for result."
    )


@router.get("/status/{job_id}", response_model=TryOnResultResponse)
def get_tryon_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return TryOnResultResponse(
        job_id=job_id,
        status=job["status"],
        result_url=job.get("result_url"),
        error=job.get("error"),
        engine=job.get("engine"),
    )
