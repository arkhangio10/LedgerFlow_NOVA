"""
LedgerFlow AI — FastAPI Application Entrypoint
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_tables
from routes.cases import router as cases_router

# Import all models to ensure they are registered with SQLAlchemy's metadata
import models.case
import models.evidence
import models.decision_step
import models.approval
import models.ui_execution
import models.policy_document


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    await create_tables()
    yield


app = FastAPI(
    title="LedgerFlow AI",
    description="Multimodal Agentic UI Automation for Legacy ERP Exceptions",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(cases_router, prefix="/cases", tags=["cases"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "LedgerFlow AI"}
