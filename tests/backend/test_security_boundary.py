"""Offline authentication and mock isolation regressions. No real credentials."""
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from backend.config import settings
from backend.models.api_key import ApiKey
from backend.services import auth
from backend.tools import firestore_tool


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_REQUIRED", "true")
    monkeypatch.setattr(settings, "USE_MOCK", "true")
    monkeypatch.setattr(settings, "ADMIN_API_KEY", SecretStr(""))
    monkeypatch.setattr(auth, "_key_store", {})
    monkeypatch.setattr(auth, "_bootstrapped", False)
    monkeypatch.setattr(firestore_tool, "query_collection", AsyncMock(return_value=[]))


@pytest.mark.asyncio
async def test_empty_registry_fails_closed():
    with pytest.raises(HTTPException) as error:
        await auth.validate_api_key(None)
    assert error.value.status_code == 503


@pytest.mark.asyncio
async def test_auth_cannot_be_disabled_in_live_mode(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_REQUIRED", "false")
    monkeypatch.setattr(settings, "USE_MOCK", "false")
    with pytest.raises(HTTPException) as error:
        await auth.validate_api_key(None)
    assert error.value.status_code == 503
    with pytest.raises(RuntimeError, match="explicit mock mode"):
        await auth.bootstrap_admin_key()


@pytest.mark.asyncio
async def test_explicit_mock_mode_can_disable_auth(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_REQUIRED", "false")
    assert (await auth.validate_api_key(None))["key_id"] == "dev-mode"


@pytest.mark.asyncio
async def test_bootstrap_never_generates_or_logs_key(monkeypatch, caplog):
    fixture = "test-only-not-a-real-credential-00000000"
    monkeypatch.setattr(settings, "ADMIN_API_KEY", SecretStr(fixture))
    monkeypatch.setattr(auth, "_generate_raw_key", lambda: pytest.fail("unexpected key generation"))
    await auth.bootstrap_admin_key()
    assert (await auth.validate_api_key(fixture))["role"] == "admin"
    assert fixture not in caplog.text
    assert fixture not in repr(settings)


@pytest.mark.asyncio
async def test_unconfigured_bootstrap_fails_without_partial_initialization():
    with pytest.raises(RuntimeError, match="Configure ADMIN_API_KEY"):
        await auth.bootstrap_admin_key()
    assert not auth._bootstrapped
    assert not auth._key_store


@pytest.mark.asyncio
async def test_persisted_viewer_retains_role(monkeypatch):
    fixture = "test-only-viewer-credential-00000000"
    record = ApiKey(key_hash=auth._hash_key(fixture), role="viewer", label="fixture")
    monkeypatch.setattr(firestore_tool, "query_collection", AsyncMock(return_value=[record.model_dump()]))
    await auth.bootstrap_admin_key()
    identity = await auth.validate_api_key(fixture)
    assert identity["role"] == "viewer"
    with pytest.raises(HTTPException) as error:
        await auth.require_role("admin")(identity)
    assert error.value.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("provided", [None, "incorrect-test-key"])
async def test_missing_or_invalid_key_rejected(provided):
    auth._key_store["fixture-hash"] = ApiKey(key_hash="fixture-hash", role="admin")
    with pytest.raises(HTTPException) as error:
        await auth.validate_api_key(provided)
    assert error.value.status_code == 401


def test_mock_store_does_not_construct_cloud_client(monkeypatch):
    from google.cloud import firestore
    monkeypatch.setattr(firestore, "Client", lambda **kwargs: pytest.fail("external client in mock mode"))
    monkeypatch.setattr(firestore_tool, "_initialized", False)
    monkeypatch.setattr(firestore_tool, "_firestore_client", None)
    assert firestore_tool._get_client() is None


def test_real_application_protects_read_endpoints():
    from fastapi.testclient import TestClient
    from backend.main import app
    fixture = "test-only-http-fixture-000000000000000"
    record = ApiKey(key_hash=auth._hash_key(fixture), role="viewer")
    auth._key_store[record.key_hash] = record
    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/api/incidents").status_code == 401
        assert client.get("/api/incidents", headers={"X-API-Key": fixture}).status_code == 200


@pytest.mark.asyncio
async def test_real_error_boundary_hides_exception_details():
    from starlette.requests import Request
    from backend.main import error_handling_middleware
    request = Request({"type": "http", "path": "/health", "headers": []})

    async def failing_handler(_request):
        raise RuntimeError("sensitive-fixture-internal-details")

    response = await error_handling_middleware(request, failing_handler)
    assert response.status_code == 500
    assert b"sensitive-fixture" not in response.body
