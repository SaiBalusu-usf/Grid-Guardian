"""API key authentication and role-based access control.

Key management:
  - On first boot, bootstrap_admin_key() loads persisted keys or an operator-provided key.
  - Keys are stored hashed (SHA-256) in an in-memory registry (and optionally
    Firestore via the firestore_tool). Bootstrap key material is never logged.
  - validate_api_key is a FastAPI Security dependency that checks the
    X-API-Key header. An empty key registry fails closed.
  - require_role() returns a dependency factory that checks the caller's role.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

from backend.models.api_key import ApiKey

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory key store  (key_hash -> ApiKey)
# ---------------------------------------------------------------------------
_key_store: dict[str, ApiKey] = {}
_bootstrapped: bool = False

# FastAPI security scheme
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_key(raw: str) -> str:
    """Return the SHA-256 hex digest of a raw API key."""
    return hashlib.sha256(raw.encode()).hexdigest()


def _generate_raw_key() -> str:
    """Generate a cryptographically random API key string."""
    return f"gg_{secrets.token_urlsafe(32)}"


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

async def bootstrap_admin_key() -> None:
    """Load existing keys, or use a key explicitly supplied by the operator."""
    global _bootstrapped
    if _bootstrapped:
        return
    from backend.config import settings
    if not settings.is_auth_required:
        if not settings.is_mock:
            raise RuntimeError("Authentication may only be disabled in explicit mock mode")
        _bootstrapped = True
        return
    from backend.tools.firestore_tool import query_collection
    for document in await query_collection("api_keys"):
        record = ApiKey.model_validate(document)
        _key_store[record.key_hash] = record
    if _key_store:
        logger.info("API keys already loaded (%d keys)", len(_key_store))
        _bootstrapped = True
        return
    raw_key = settings.ADMIN_API_KEY.get_secret_value()
    if len(raw_key) < 32:
        raise RuntimeError("Configure ADMIN_API_KEY with at least 32 characters before startup")
    hashed = _hash_key(raw_key)

    api_key = ApiKey(
        key_hash=hashed,
        role="admin",
        label="bootstrap-admin",
    )
    _key_store[hashed] = api_key

    _bootstrapped = True
    logger.info("Loaded operator-provided bootstrap admin key")


# ---------------------------------------------------------------------------
# Create key (for /api/keys endpoint)
# ---------------------------------------------------------------------------

async def create_api_key(role: str = "viewer", label: str = "") -> dict[str, Any]:
    """Create a new API key and return it (plain text shown once).

    Returns:
        Dict with key (plain text), key_id, role, label.
    """
    raw_key = _generate_raw_key()
    hashed = _hash_key(raw_key)

    api_key = ApiKey(
        key_hash=hashed,
        role=role,  # type: ignore[arg-type]
        label=label,
    )
    _key_store[hashed] = api_key

    # Persist best-effort
    try:
        from backend.tools.firestore_tool import write_document
        await write_document("api_keys", api_key.key_id, api_key.model_dump())
    except Exception:
        pass

    logger.info("Created API key %s (role=%s, label=%s)", api_key.key_id, role, label)
    return {
        "key": raw_key,
        "key_id": api_key.key_id,
        "role": api_key.role,
        "label": api_key.label,
    }


# ---------------------------------------------------------------------------
# Validation dependency
# ---------------------------------------------------------------------------

async def validate_api_key(
    api_key: str | None = Security(_api_key_header),
) -> dict[str, str]:
    """FastAPI dependency: validate the X-API-Key header.

    Authentication can be disabled only in explicit mock mode.

    Returns:
        Dict with "role" and "key_id".

    Raises:
        HTTPException 401 if the key is invalid or inactive.
    """
    from backend.config import settings
    if not settings.is_auth_required and settings.is_mock:
        return {"role": "admin", "key_id": "dev-mode"}
    if not settings.is_auth_required or not _key_store:
        raise HTTPException(status_code=503, detail="Authentication is not configured")

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    hashed = _hash_key(api_key)
    record = _key_store.get(hashed)

    if record is None or not record.active:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    # Update last_used_at
    record.last_used_at = datetime.now(tz=timezone.utc).isoformat()

    return {"role": record.role, "key_id": record.key_id}


# ---------------------------------------------------------------------------
# Role checker dependency factory
# ---------------------------------------------------------------------------

def require_role(*roles: str):
    """Return a FastAPI dependency that enforces role membership.

    Usage:
        @app.post("/api/foo", dependencies=[Depends(require_role("admin", "operator"))])

    Raises:
        HTTPException 403 if the caller's role is not in the allowed set.
    """
    async def _check(
        auth: dict[str, str] = Depends(validate_api_key),
    ) -> dict[str, str]:
        if auth["role"] not in roles:
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {', '.join(roles)}. Your role: {auth['role']}",
            )
        return auth

    return _check
