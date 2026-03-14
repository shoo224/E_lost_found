# main.py - FastAPI app entry point
# Wire CORS, routers, and APScheduler hourly matching job

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.routers import auth, lost, found, claims, admin, stats
from app.jobs.matching_job import hourly_matching_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# APScheduler - run matching every hour
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start scheduler on startup, shut down on shutdown."""
    scheduler.add_job(hourly_matching_job, "interval", hours=1, id="matching")
    scheduler.start()
    logger.info("APScheduler started: hourly matching job")
    yield
    scheduler.shutdown()
    logger.info("APScheduler stopped")


app = FastAPI(
    title="E Lost & Found API",
    description="Backend for E Lost & Found web application",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - allow frontend origins from .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clear error when MongoDB URI is still placeholder (from database.py)
@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    msg = str(exc)
    if "MONGODB_URI" in msg and "backend/.env" in msg:
        return JSONResponse(
            status_code=503,
            content={"detail": msg},
        )
    raise exc

# Include routers
app.include_router(auth.router)
app.include_router(stats.router)
app.include_router(lost.router)
app.include_router(found.router)
app.include_router(claims.router)
app.include_router(admin.router)


@app.get("/")
def root():
    """Health check / API info."""
    return {"message": "E Lost & Found API", "docs": "/docs"}


@app.get("/health")
def health():
    """Health check for deployment."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
