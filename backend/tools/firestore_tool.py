"""Firestore operations tool with in-memory fallback when Firestore is unavailable."""

import copy
import logging
from datetime import datetime
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton Firestore client / in-memory fallback
# ---------------------------------------------------------------------------

_firestore_client: Any = None
_in_memory_store: dict[str, dict[str, dict]] = {}
_using_memory_fallback: bool = False
_initialized: bool = False


def _get_client() -> Any:
    """Return a Firestore client or None (triggering in-memory fallback)."""
    global _firestore_client, _using_memory_fallback, _initialized

    if _initialized:
        return _firestore_client

    _initialized = True

    try:
        from google.cloud import firestore as _firestore_lib

        import os
        if settings.FIRESTORE_EMULATOR_HOST:
            os.environ["FIRESTORE_EMULATOR_HOST"] = settings.FIRESTORE_EMULATOR_HOST
        else:
            os.environ.pop("FIRESTORE_EMULATOR_HOST", None)

        _firestore_client = _firestore_lib.Client(project=settings.GOOGLE_CLOUD_PROJECT)
        # Quick connectivity test
        _firestore_client.collection("_health").document("_ping").get()
        logger.info("Connected to Firestore (project=%s)", settings.GOOGLE_CLOUD_PROJECT)
        return _firestore_client
    except Exception as exc:
        logger.warning("Firestore unavailable (%s). Using in-memory fallback.", exc)
        _using_memory_fallback = True
        _firestore_client = None
        return None


# ---------------------------------------------------------------------------
# In-memory helpers
# ---------------------------------------------------------------------------

def _mem_collection(collection: str) -> dict[str, dict]:
    if collection not in _in_memory_store:
        _in_memory_store[collection] = {}
    return _in_memory_store[collection]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def write_document(collection: str, doc_id: str, data: dict) -> dict:
    """Write a document to a Firestore collection (or in-memory fallback).

    Args:
        collection: Collection name.
        doc_id: Document ID.
        data: Document data.

    Returns:
        {"status": "ok", "collection", "doc_id"}
    """
    max_retries = 2
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            client = _get_client()
            if client is not None:
                client.collection(collection).document(doc_id).set(data)
            else:
                _mem_collection(collection)[doc_id] = copy.deepcopy(data)

            logger.debug("Wrote %s/%s", collection, doc_id)
            return {"status": "ok", "collection": collection, "doc_id": doc_id}
        except Exception as exc:
            last_error = exc
            logger.warning(
                "write_document attempt %d/%d failed: %s", attempt + 1, max_retries, exc
            )

    # Final fallback: write to memory even if Firestore was supposed to work
    _mem_collection(collection)[doc_id] = copy.deepcopy(data)
    logger.error(
        "write_document failed after retries (%s), stored in memory fallback", last_error
    )
    return {"status": "ok", "collection": collection, "doc_id": doc_id, "fallback": True}


async def read_document(collection: str, doc_id: str) -> dict | None:
    """Read a single document.

    Returns:
        Document dict or None if not found.
    """
    max_retries = 2

    for attempt in range(max_retries):
        try:
            client = _get_client()
            if client is not None:
                doc = client.collection(collection).document(doc_id).get()
                if doc.exists:
                    return doc.to_dict()
                return None
            else:
                return copy.deepcopy(_mem_collection(collection).get(doc_id))
        except Exception as exc:
            logger.warning(
                "read_document attempt %d/%d failed: %s", attempt + 1, max_retries, exc
            )

    # Fallback to memory
    return copy.deepcopy(_mem_collection(collection).get(doc_id))


async def query_collection(collection: str, filters: dict | None = None) -> list[dict]:
    """Query a collection with optional equality filters.

    Args:
        collection: Collection name.
        filters: Dict of field=value equality filters.

    Returns:
        List of matching documents.
    """
    if filters is None:
        filters = {}

    max_retries = 2

    for attempt in range(max_retries):
        try:
            client = _get_client()
            if client is not None:
                query = client.collection(collection)
                for field, value in filters.items():
                    query = query.where(field, "==", value)
                docs = query.stream()
                return [doc.to_dict() for doc in docs]
            else:
                results = []
                for doc_data in _mem_collection(collection).values():
                    match = all(doc_data.get(k) == v for k, v in filters.items())
                    if match:
                        results.append(copy.deepcopy(doc_data))
                return results
        except Exception as exc:
            logger.warning(
                "query_collection attempt %d/%d failed: %s", attempt + 1, max_retries, exc
            )

    # Fallback to memory
    results = []
    for doc_data in _mem_collection(collection).values():
        match = all(doc_data.get(k) == v for k, v in filters.items())
        if match:
            results.append(copy.deepcopy(doc_data))
    return results


async def update_document(collection: str, doc_id: str, updates: dict) -> dict:
    """Update specific fields of an existing document.

    Args:
        collection: Collection name.
        doc_id: Document ID.
        updates: Dict of field=value updates.

    Returns:
        {"status": "ok", "collection", "doc_id", "updated_fields": [...]}
    """
    max_retries = 2

    for attempt in range(max_retries):
        try:
            client = _get_client()
            if client is not None:
                client.collection(collection).document(doc_id).update(updates)
            else:
                store = _mem_collection(collection)
                if doc_id in store:
                    store[doc_id].update(copy.deepcopy(updates))
                else:
                    store[doc_id] = copy.deepcopy(updates)

            logger.debug("Updated %s/%s fields=%s", collection, doc_id, list(updates.keys()))
            return {
                "status": "ok",
                "collection": collection,
                "doc_id": doc_id,
                "updated_fields": list(updates.keys()),
            }
        except Exception as exc:
            logger.warning(
                "update_document attempt %d/%d failed: %s", attempt + 1, max_retries, exc
            )

    # Fallback
    store = _mem_collection(collection)
    if doc_id in store:
        store[doc_id].update(copy.deepcopy(updates))
    else:
        store[doc_id] = copy.deepcopy(updates)
    return {
        "status": "ok",
        "collection": collection,
        "doc_id": doc_id,
        "updated_fields": list(updates.keys()),
        "fallback": True,
    }
