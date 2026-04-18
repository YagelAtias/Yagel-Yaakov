from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.signals.analysis_engine import router as master_router

app = FastAPI(
    title="Yagel-Yaakov Platform",
    description="Educational management and distress detection system.",
    version="0.2.0"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=['*']
)

# Include the router with a clean prefix.
app.include_router(master_router, prefix="/api/v2", tags=["Multi-Signal Analysis"])

@app.get("/")
def read_root():
    return {
        "system": "Yagel-Yaakov Platform",
        "status": "online",
        "version": "0.2.0"
    }