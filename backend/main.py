from fastapi import FastAPI
from app.signals.text_entropy import router as entropy_router

app = FastAPI(
    title="Yagel-Yaakov Platform",
    description="Educational management and distress detection system.",
    version="0.1.0"
)

app.include_router(entropy_router, prefix="/api/signals", tags=["Distress Signals"])

@app.get("/")
def read_root():
    return {
        "system": "Yagel-Yaakov Platform",
        "status": "online",
        "version": "0.1.0"
    }