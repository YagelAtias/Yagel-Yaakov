from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.signals.analysis_engine import router as master_router
from app.api.auth import router as auth_router
from app.api.logs import router as logs_router
from app.api.classrooms import router as classrooms_router
from app.api.management import router as management_router
from app.api.dashboard import router as dashboard_router
from app.api.admin import router as admin_router
from app.db.database import engine
from app.db import models

# Initialize SQLite database tables
models.Base.metadata.create_all(bind=engine)

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

# Include the routers with clean prefixes.
app.include_router(auth_router, prefix="/api/v2/auth", tags=["Authentication"])
app.include_router(master_router, prefix="/api/v2", tags=["Multi-Signal Analysis"])
app.include_router(logs_router, prefix="/api/v2", tags=["Secure Data Access"])
app.include_router(classrooms_router, prefix="/api/v2", tags=["School Management"])
app.include_router(management_router, prefix="/api/v2", tags=["School Management"])
app.include_router(dashboard_router, prefix="/api/v2", tags=["Mobile App Core"])
app.include_router(admin_router, prefix="/api/v2/admin", tags=["Admin"])

@app.get("/")
def read_root():
    return {
        "system": "Yagel-Yaakov Platform",
        "status": "online",
        "version": "0.2.0"
    }