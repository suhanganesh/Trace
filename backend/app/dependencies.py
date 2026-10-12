from fastapi import HTTPException

from app.database.mongodb import (
    get_analytics_global_collection,
    ping_database,
)


def require_mongodb() -> None:
    if not ping_database():
        raise HTTPException(
            status_code=503,
            detail=(
                "MongoDB is currently unavailable. Start MongoDB and verify "
                "MONGODB_URI, then try again."
            ),
        )


def require_compact_analytics() -> None:
    require_mongodb()
    if get_analytics_global_collection().estimated_document_count() == 0:
        raise HTTPException(
            status_code=503,
            detail=(
                "Compact analytics are not loaded. Run scripts/build_mongodb_rollups.py "
                "and scripts/import_analytics_to_mongodb.py."
            ),
        )
