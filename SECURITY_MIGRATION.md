# Authentication and ADK security migration

Authentication defaults to required. An empty key registry returns 503 instead
of granting administrator access. Startup loads existing persisted key hashes,
or requires an operator-provided `ADMIN_API_KEY` of at least 32 characters.
Startup never generates or logs a credential. Set secrets through your existing
deployment secret mechanism; do not commit them. Creating or changing deployed
credentials is a separate operator action.

For an explicitly local demonstration only, `USE_MOCK=true AUTH_REQUIRED=false`
retains the no-key demo behavior. Disabling authentication outside mock mode is
rejected. Mock Firestore access stays in memory and never constructs a cloud
client. Mock workflows do not invoke Gemini even if a key happens to be present.
Unexpected HTTP errors return a generic message rather than exception content.

## Temporary ADK compatibility distribution

Upstream ADK 2.13.0 caps OpenTelemetry API/SDK at 1.44. The patched tracestate
parser requires 1.45.1. `backend/build_adk_compat.py` checks the official wheel's
SHA-256 before building local version `2.13.0+gridguardian.1`. It changes only
the distribution version and the two telemetry bounds to `>=1.45.1,<1.46`.
All upstream Python bytes and its Apache license remain unchanged; RECORD is
recomputed. This is a locally maintained compatibility patch, not an upstream
release or a claim of upstream support. Remove it once a compatible upstream
release is tested. Never install with `--no-deps` to hide this conflict.

From the repository root:

```sh
python backend/build_adk_compat.py
python -m pip install --require-hashes -r backend/requirements.lock
python -m pip check
USE_MOCK=true AUTH_REQUIRED=false GEMINI_API_KEY= python -m pytest -q tests/backend
```

The local wheel is deterministic and untracked. Its expected SHA-256 is recorded
in the lock. CI tests real ADK session state, LLM orchestration and exported spans
with a local fixture model; no Google service or credential is required. The
application now reads the updated session after the runner completes.

Upstream references: [ADK 2.13.0](https://pypi.org/project/google-adk/2.13.0/),
[OpenTelemetry 1.45.1 parser fix](https://github.com/open-telemetry/opentelemetry-python/releases/tag/v1.45.1).
