"""API key authentication and role-based access control.

Key management:
  - On first boot, bootstrap_admin_key() creates an admin key if none exist.
  - Keys are stored hashed (SHA-256) in an in-memory registry (and optionally
    Firestore via the firestore_tool).  The plain-text key is only printed once
    at startup.
  - validate_api_key is a FastAPI Security dependency that checks the
    X-API-Key header.  When no keys are configured it allows all requests
    as admin (dev mode).
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
    """Create an admin API key on first boot if none exist.

    The plain-text key is logged once so the operator can copy it.
    Subsequent calls are a no-op.
    """
    global _bootstrapped
    if _bootstrapped:
        return
    _bootstrapped = True

    if _key_store:
        logger.info("API keys already loaded (%d keys)", len(_key_store))
        return

    raw_key = _generate_raw_key()
    hashed = _hash_key(raw_key)

    api_key = ApiKey(
        key_hash=hashed,
        role="admin",
        label="bootstrap-admin",
    )
    _key_store[hashed] = api_key

    # Store in Firestore for persistence (best-effort)
    try:
        from backend.tools.firestore_tool import write_document
        await write_document("api_keys", api_key.key_id, api_key.model_dump())
    except Exception:
        pass

    logger.info("=" * 60)
    logger.info("BOOTSTRAP ADMIN API KEY (save this, shown only once):")
    logger.info("  %s", raw_key)
    logger.info("=" * 60)


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

    Dev mode: if no keys are configured, all requests are allowed as admin.

    Returns:
        Dict with "role" and "key_id".

    Raises:
        HTTPException 401 if the key is invalid or inactive.
    """
    # Dev mode: no keys configured -> allow everything as admin
    if not _key_store:
        return {"role": "admin", "key_id": "dev-mode"}

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
