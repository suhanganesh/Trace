from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.analytics.products import fetch_product_detail, fetch_product_rankings
from app.database.mongodb import (
    get_product_metadata_collection,
    get_product_metrics_collection,
)
from app.dependencies import require_compact_analytics
from app.schemas.responses import ProductDetailResponse, ProductListResponse

router = APIRouter(tags=["Products"])

MetricParam = Literal["views", "addtocart", "transactions"]


@router.get(
    "/products",
    response_model=ProductListResponse,
    summary="Top products by metric",
)
def list_products(
    metric: MetricParam = Query("views", description="Ranking metric"),
    limit: int = Query(10, ge=1, le=100),
    _: None = Depends(require_compact_analytics),
) -> ProductListResponse:
    return fetch_product_rankings(get_product_metrics_collection(), metric, limit)


@router.get(
    "/products/{item_id}",
    response_model=ProductDetailResponse,
    summary="Analytics for a single product",
)
def get_product(
    item_id: int,
    _: None = Depends(require_compact_analytics),
) -> ProductDetailResponse:
    if item_id <= 0:
        raise HTTPException(status_code=422, detail="item_id must be a positive integer.")
    return fetch_product_detail(
        get_product_metrics_collection(),
        get_product_metadata_collection(),
        item_id,
    )
