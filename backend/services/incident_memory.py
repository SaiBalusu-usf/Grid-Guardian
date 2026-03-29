"""Incident memory service: extract and retrieve learnings from past incidents.

Uses Gemini to extract structured lessons from completed incidents and
stores them in a Firestore "incident_learnings" collection.  When Gemini
is unavailable, deterministic fallback learnings are generated.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend.services.gemini_client import generate_json
from backend.tools.firestore_tool import (
    write_document,
    query_collection,
)

logger = logging.getLogger(__name__)

COL_LEARNINGS = "incident_learnings"


async def extract_learnings(
    incident_id: str,
    scenario: str,
    plan: dict[str, Any] | None = None,
    audit_corrections: list[str] | None = None,
) -> dict[str, Any]:
    """Extract lessons learned from a completed incident.

    Attempts to use Gemini for intelligent extraction; falls back to a
    deterministic summary when Gemini is unavailable.

    Args:
        incident_id: The incident that was completed.
        scenario: Original scenario description.
        plan: Final response plan dict (optional).
        audit_corrections: List of corrections applied during audit (optional).

    Returns:
        The stored learning document.
    """
    audit_corrections = audit_corrections or []

    # Try LLM extraction
    prompt = (
        "You are a disaster response analyst. Given the following incident data, "
        "extract 2-4 concise lessons learned that could improve future responses.\n\n"
        f"Scenario: {scenario}\n"
        f"Plan summary: {json.dumps(plan, default=str)[:2000] if plan else 'N/A'}\n"
        f"Audit corrections applied: {audit_corrections}\n\n"
        "Return a JSON object:\n"
        "{\n"
        '  "lessons": [\n'
        '    {"topic": "...", "insight": "...", "severity": "low|medium|high"}\n'
        "  ],\n"
        '  "tags": ["tag1", "tag2"],\n'
        '  "summary": "One-sentence overall takeaway"\n'
        "}"
    )

    extracted = await generate_json(prompt)

    if extracted is None:
        # Fallback: deterministic extraction
        lessons = [
            {
                "topic": "Response Time",
                "insight": "Incident workflow completed; consider benchmarking agent durations.",
                "severity": "low",
            },
        ]
        if audit_corrections:
            lessons.append({
                "topic": "Audit Findings",
                "insight": f"{len(audit_corrections)} correction(s) applied during audit. "
                           "Review recurring audit gaps.",
                "severity": "medium",
            })
        extracted = {
            "lessons": lessons,
            "tags": ["auto-extracted", "fallback"],
            "summary": f"Incident {incident_id} completed with {len(audit_corrections)} audit correction(s).",
        }

    # Persist the learning
    doc_id = str(uuid4())
    doc = {
        "id": doc_id,
        "incident_id": incident_id,
        "scenario": scenario,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        **extracted,
    }
    await write_document(COL_LEARNINGS, doc_id, doc)
    logger.info("Stored learning %s for incident %s", doc_id, incident_id)
    return doc


async def get_relevant_learnings(
    scenario: str = "",
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Retrieve recent learnings, optionally filtered by keyword match.

    Args:
        scenario: Optional scenario text for keyword matching.
        limit: Maximum number of learnings to return.

    Returns:
        List of learning documents, most recent first.
    """
    all_docs = await query_collection(COL_LEARNINGS)

    # Sort by created_at descending
    all_docs.sort(key=lambda d: d.get("created_at", ""), reverse=True)

    if scenario:
        # Simple keyword relevance: score by overlap with scenario tokens
        scenario_tokens = set(scenario.lower().split())

        def _score(doc: dict) -> int:
            doc_text = (
                doc.get("scenario", "")
                + " "
                + " ".join(doc.get("tags", []))
                + " "
                + doc.get("summary", "")
            ).lower()
            return sum(1 for t in scenario_tokens if t in doc_text)

        all_docs.sort(key=_score, reverse=True)

    return all_docs[:limit]
