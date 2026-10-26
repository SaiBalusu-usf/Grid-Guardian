"""Exercise real ADK sessions/LLM flow and patched telemetry without a service."""
from collections.abc import AsyncGenerator

import pytest
from google.adk.agents import LlmAgent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import TraceState

from backend.config import settings
from backend.services.streaming import StreamManager


class LocalModel(BaseLlm):
    """Deterministic model adapter; the real ADK runner performs all orchestration."""
    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False,
    ) -> AsyncGenerator[LlmResponse, None]:
        assert llm_request.contents
        yield LlmResponse(content=types.Content(
            role="model", parts=[types.Part(text='{"status":"offline-fixture"}')],
        ), finish_reason=types.FinishReason.STOP)


@pytest.mark.asyncio
async def test_adk_runner_persists_state_and_emits_telemetry(monkeypatch):
    from backend.agents import adk_agents, adk_runner

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(trace, "_TRACER_PROVIDER", provider)
    # A local fixture model receives the request: no Gemini client is constructed.
    agent = LlmAgent(name="offline_fixture", model=LocalModel(model="local-fixture"),
                     instruction="Return the offline fixture.", output_key="plan")
    monkeypatch.setattr(adk_agents, "gridguardian_agent", agent)
    monkeypatch.setattr(settings, "USE_MOCK", "false")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "offline-fixture-not-a-real-key")
    try:
        result = await adk_runner.run_adk_workflow(
            {"scenario": "Offline synthetic incident"}, "test-incident", StreamManager(),
        )
        assert result == {"plan": '{"status":"offline-fixture"}'}
        provider.force_flush()
        assert exporter.get_finished_spans()
    finally:
        provider.shutdown()


def test_telemetry_rejects_oversized_tracestate():
    assert list(TraceState.from_header(["a=" + "x" * 9000]).items()) == []
