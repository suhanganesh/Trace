from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routes import behavior, dataset, funnel, health, overview, products, report, time_series
from app.schemas.responses import ErrorResponse
from app.utils.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("trace.api")

app = FastAPI(
    title="Trace API",
    description=(
        "Server-side analytics API for Trace. Aggregations run in MongoDB; "
        "responses contain summarized metrics only."
    ),
    version="1.0.0",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    payload = ErrorResponse(detail=str(exc.detail), error_code=f"http_{exc.status_code}")
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    payload = ErrorResponse(detail="Invalid request parameters.", error_code="validation_error")
    logger.debug("Validation error: %s", exc.errors())
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled server error")
    payload = ErrorResponse(
        detail="An unexpected error occurred while processing the request.",
        error_code="internal_error",
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


app.include_router(health.router, prefix="/api")
app.include_router(overview.router, prefix="/api")
app.include_router(funnel.router, prefix="/api")
app.include_router(behavior.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(time_series.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(dataset.router, prefix="/api")
