from __future__ import annotations

import logging
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.utils.config import get_settings

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_database: Database | None = None


def get_mongo_client() -> MongoClient:
    global _client
    settings = get_settings()
    if not settings.mongodb_uri:
        raise RuntimeError("MONGODB_URI is not configured")
    if _client is None:
        _client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5_000,
            connectTimeoutMS=5_000,
            socketTimeoutMS=120_000,
            maxPoolSize=50,
            retryWrites=True,
        )
    return _client


def get_database() -> Database:
    global _database
    if _database is None:
        settings = get_settings()
        _database = get_mongo_client()[settings.mongodb_database]
    return _database


def is_compact_deployment() -> bool:
    return get_settings().mongodb_deployment_mode.strip().lower() == "compact"


def get_analytics_global_collection() -> Collection:
    return get_database()["analytics_global"]


def get_product_metrics_collection() -> Collection:
    return get_database()["product_metrics"]


def get_product_metadata_collection() -> Collection:
    return get_database()["product_metadata"]


def get_time_series_daily_collection() -> Collection:
    return get_database()["time_series_daily"]


def get_time_series_hourly_collection() -> Collection:
    return get_database()["time_series_hourly"]


def get_category_tree_collection() -> Collection:
    return get_database()["category_tree"]


def get_analytics_global_document() -> dict[str, Any]:
    document = get_analytics_global_collection().find_one({})
    if not document:
        raise RuntimeError("analytics_global is empty. Import compact analytics first.")
    return document


def ping_database() -> bool:
    try:
        get_mongo_client().admin.command("ping")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("MongoDB ping failed: %s", exc)
        return False


def aggregate_list(collection: Collection, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return list(collection.aggregate(pipeline, allowDiskUse=True))
