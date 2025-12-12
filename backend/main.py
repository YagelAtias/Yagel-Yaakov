from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.signals.text_entropy import router as entropy_router

app = FastAPI(
    title="Yagel-Yaakov Platform",
    description="Educational management and distress detection system.",
    version="0.1.0"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=['*'])

app.include_router(entropy_router, prefix="/api/signals", tags=["Distress Signals"])


@app.get("/")
def read_root():
    return {
        "system": "Yagel-Yaakov Platform",
        "status": "online",
        "version": "0.1.0"
    }
