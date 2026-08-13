import asyncio
import logging
import os
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.cache import cache_service
from services.scraper import ScrapeResult, scrape_website
from services.trust_engine import build_trust_report
from utils.helpers import InMemoryTaskStore, TaskState, enforce_api_key, normalize_url, rate_limit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("trustscore.api")

app = FastAPI(title="AI Trust Score Analyzer", version="3.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

task_store = InMemoryTaskStore()


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="Website URL to analyze")


def _security_dependency(request: Request) -> None:
    enforce_api_key(request.headers.get("x-api-key"))
    rate_limit(request.client.host if request.client else "unknown")


@app.on_event("startup")
async def startup() -> None:
    await cache_service.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    await cache_service.close()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError) -> JSONResponse:
    logger.warning("Validation error: %s", exc)
    return JSONResponse(
        status_code=422,
        content={"status": "failed", "detail": "Invalid request payload.", "errors": exc.errors()},
    )


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "success",
        "service": "AI Trust Score Analyzer",
        "cache": await cache_service.health(),
        "tasks_in_memory": task_store.size(),
    }


@app.post("/analyze", dependencies=[Depends(_security_dependency)])
async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    normalized_url = normalize_url(request.url)

    cached = await cache_service.get(normalized_url)
    if cached is not None:
        cached_task = task_store.create(url=normalized_url, state=TaskState.COMPLETED, result=cached)
        return {
            "status": "success",
            "task_id": cached_task.task_id,
            "cached": True,
            "message": "Cached analysis returned immediately.",
        }

    task = task_store.create(url=normalized_url, state=TaskState.QUEUED)
    background_tasks.add_task(run_analysis_task, task.task_id, normalized_url)

    return {
        "status": "success",
        "task_id": task.task_id,
        "cached": False,
        "message": "Analysis started.",
    }


@app.get("/status/{task_id}", dependencies=[Depends(_security_dependency)])
async def get_status(task_id: str) -> dict[str, Any]:
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    payload: dict[str, Any] = {
        "status": "success" if task.state != TaskState.FAILED else "failed",
        "task_id": task.task_id,
        "task_status": task.state.value,
        "url": task.url,
        "error": task.error,
    }

    if task.result is not None:
        payload["result"] = task.result

    return payload


async def run_analysis_task(task_id: str, url: str) -> None:
    task_store.update(task_id, state=TaskState.RUNNING)
    logger.info("Started analysis task %s for %s", task_id, url)

    try:
        scrape_result: ScrapeResult = await scrape_website(url)
        report = await build_trust_report(url, scrape_result)
        report["status"] = "success"
        await cache_service.set(url, report, ttl_seconds=3600)
        task_store.update(task_id, state=TaskState.COMPLETED, result=report)
        logger.info("Completed analysis task %s", task_id)
    except ValueError as exc:
        logger.warning("Task %s failed with user-facing error: %s", task_id, exc)
        task_store.update(task_id, state=TaskState.FAILED, error=str(exc))
    except asyncio.TimeoutError:
        message = "Timed out while scanning the website."
        logger.warning("Task %s timed out", task_id)
        task_store.update(task_id, state=TaskState.FAILED, error=message)
    except Exception as exc:  # pragma: no cover - runtime safeguard
        logger.exception("Unexpected task failure for %s", task_id)
        task_store.update(task_id, state=TaskState.FAILED, error=f"Analysis failed: {exc}")
