from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import size, tryon, garment
from app.core.config import settings

app = FastAPI(
    title="TwinFit API",
    description="AI-powered virtual try-on and size recommendation for Indian fashion",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(size.router,    prefix="/api/size",    tags=["Size Recommendation"])
app.include_router(garment.router, prefix="/api/garment", tags=["Garment Analysis"])
app.include_router(tryon.router,   prefix="/api/tryon",   tags=["Virtual Try-On"])

@app.get("/")
def root():
    return {"status": "TwinFit API is live", "version": "0.1.0"}

@app.get("/health")
def health():
    return {"status": "ok"}
