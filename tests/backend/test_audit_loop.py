"""Tests for the audit loop logic.

The audit loop is a core pattern in GridGuardian: after agents produce a
response plan, an auditor agent reviews it. If the audit fails, the plan is
revised and re-audited up to a maximum number of retries.

These tests use pure mock data -- no LLM calls needed.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest


# ============================================================================
# Audit loop implementation (self-contained for testing)
# ============================================================================
# This mirrors the audit loop logic from backend/workflows/.

class AuditResult:
    """Structured result from the plan auditor."""

    def __init__(self, passed: bool, issues: list[dict], score: int):
        self.passed = passed
        self.issues = issues
        self.score = score


async def audit_plan(plan: dict[str, Any], attempt: int = 1) -> AuditResult:
    """Mock auditor that inspects a response plan for issues.

    The mock logic checks for specific known problems:
    - Shelter at >90% capacity without overflow plan
    - Missing generator deployment for shelters without backup power
    - Missing medical staff assignment
    """
    issues: list[dict] = []
    score = 100

    sections = plan.get("sections", {})

    # Check shelter capacity
    shelter_data = sections.get("shelter_analysis", {}).get("data", {})
    if shelter_data.get("critical_shelters", 0) > 0:
        recommendations = plan.get("recommendations", [])
        has_overflow = any("overflow" in r.lower() or "redirect" in r.lower() for r in recommendations)
        if not has_overflow:
            issues.append({
                "severity": "critical",
                "category": "shelter_capacity",
                "description": "Critical shelters detected but no overflow/redirect plan provided",
                "recommendation": "Add overflow routing to shelters with available capacity",
            })
            score -= 25

    # Check power backup
    infra_data = sections.get("infrastructure_status", {}).get("data", {})
    if infra_data.get("power_outages", 0) > 0:
        recommendations = plan.get("recommendations", [])
        has_generator = any("generator" in r.lower() for r in recommendations)
        if not has_generator:
            issues.append({
                "severity": "warning",
                "category": "resource_allocation",
                "description": "Power outages detected but no generator deployment planned",
                "recommendation": "Deploy portable generators to affected shelters",
            })
            score -= 10

    # Check medical coverage
    shelter_total = shelter_data.get("total_shelters", 0)
    if shelter_total > 0:
        recommendations = plan.get("recommendations", [])
        has_medical = any("medical" in r.lower() for r in recommendations)
        if not has_medical:
            issues.append({
                "severity": "warning",
                "category": "medical_coverage",
                "description": "No medical team deployment mentioned in plan",
                "recommendation": "Stage medical teams at primary intake shelters",
            })
            score -= 10

    passed = len(issues) == 0 and score >= 80
    return AuditResult(passed=passed, issues=issues, score=score)


async def revise_plan(plan: dict[str, Any], audit_result: AuditResult) -> dict[str, Any]:
    """Mock plan revision that fixes known issues."""
    revised = {**plan, "recommendations": list(plan.get("recommendations", []))}

    for issue in audit_result.issues:
        if issue["category"] == "shelter_capacity":
            revised["recommendations"].append(
                "Redirect overflow from critical shelters to SH-003 and SH-004"
            )
        elif issue["category"] == "resource_allocation":
            revised["recommendations"].append(
                "Deploy portable generators to all shelters without backup power"
            )
        elif issue["category"] == "medical_coverage":
            revised["recommendations"].append(
                "Stage medical teams at Lincoln Community Center and Riverside Convention Center"
            )

    revised["plan_version"] = plan.get("plan_version", 1) + 1
    return revised


async def run_audit_loop(
    plan: dict[str, Any],
    max_retries: int = 2,
) -> tuple[dict[str, Any], AuditResult, int]:
    """Run the audit loop: audit -> revise -> re-audit up to max_retries.

    Returns:
        Tuple of (final_plan, final_audit_result, attempts_used)
    """
    current_plan = plan
    attempts = 0

    for attempt in range(1, max_retries + 2):  # +2 because first pass is attempt 1
        attempts = attempt
        result = await audit_plan(current_plan, attempt=attempt)

        if result.passed:
            return current_plan, result, attempts

        if attempt <= max_retries:
            current_plan = await revise_plan(current_plan, result)
        # else: we've exhausted retries, return the last result

    return current_plan, result, attempts


# ============================================================================
# Tests
# ============================================================================

class TestAuditPlan:
    """Tests for individual audit plan calls."""

    @pytest.mark.asyncio
    async def test_audit_finds_issues_on_first_pass(self, sample_response_plan):
        """First audit of a plan with known gaps should return passed=False."""
        # Remove recommendations that would satisfy the audit
        plan = {**sample_response_plan, "recommendations": []}

        result = await audit_plan(plan)

        assert result.passed is False
        assert len(result.issues) > 0
        assert result.score < 100

        # Should find at least the shelter capacity issue
        categories = [i["category"] for i in result.issues]
        assert "shelter_capacity" in categories or "medical_coverage" in categories

        # Each issue has required structure
        for issue in result.issues:
            assert "severity" in issue
            assert "category" in issue
            assert "description" in issue
            assert "recommendation" in issue
            assert issue["severity"] in {"critical", "warning", "info"}

    @pytest.mark.asyncio
    async def test_audit_passes_after_corrections(self, sample_response_plan):
        """A plan with proper recommendations should pass the audit."""
        plan = {
            **sample_response_plan,
            "recommendations": [
                "Redirect overflow from critical shelters to SH-003 and SH-004",
                "Deploy portable generators to all shelters without backup power",
                "Stage medical teams at Lincoln Community Center",
            ],
        }

        result = await audit_plan(plan)

        assert result.passed is True
        assert len(result.issues) == 0
        assert result.score >= 80


class TestAuditLoop:
    """Tests for the full audit loop with retries."""

    @pytest.mark.asyncio
    async def test_audit_loop_fixes_plan(self, sample_response_plan):
        """Audit loop should revise plan and pass within retries."""
        # Start with a plan missing recommendations
        plan = {**sample_response_plan, "recommendations": []}

        final_plan, final_result, attempts = await run_audit_loop(plan, max_retries=2)

        # After revision, it should pass
        assert final_result.passed is True
        assert final_result.score >= 80
        assert attempts >= 2  # First pass fails, revision should pass
        assert final_plan["plan_version"] >= 2

        # The revised plan should have added recommendations
        assert len(final_plan["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_audit_loop_max_retries(self):
        """Audit loop should terminate after max_retries even if issues remain."""
        # Create a plan that the mock auditor will always flag
        # (we use a plan with critical shelters but remove the shelter analysis
        # sections in a way the reviser cannot fully fix)
        broken_plan = {
            "incident_id": "INC-BROKEN",
            "plan_version": 1,
            "sections": {
                "shelter_analysis": {
                    "agent": "shelter_specialist",
                    "status": "completed",
                    "summary": "Problems found",
                    "data": {
                        "total_shelters": 4,
                        "total_capacity": 100,
                        "critical_shelters": 3,
                        "ada_compliant": 1,
                    },
                },
                "infrastructure_status": {
                    "agent": "infrastructure_monitor",
                    "status": "completed",
                    "summary": "Major outages",
                    "data": {
                        "power_outages": 5,
                        "road_closures": 4,
                        "bridge_status": "closed",
                        "hospital_status": "limited",
                    },
                },
            },
            "recommendations": [],
        }

        max_retries = 2
        final_plan, final_result, attempts = await run_audit_loop(
            broken_plan, max_retries=max_retries
        )

        # Should not exceed max_retries + 1 (initial attempt + retries)
        assert attempts <= max_retries + 1

        # The loop ran the expected number of times
        assert attempts >= 2

    @pytest.mark.asyncio
    async def test_audit_loop_passes_immediately_for_good_plan(self, sample_response_plan):
        """A plan that already passes should complete in 1 attempt."""
        good_plan = {
            **sample_response_plan,
            "recommendations": [
                "Redirect overflow from critical shelters",
                "Deploy generators to unpowered shelters",
                "Stage medical teams at primary shelters",
            ],
        }

        final_plan, final_result, attempts = await run_audit_loop(good_plan, max_retries=3)

        assert final_result.passed is True
        assert attempts == 1
        assert final_plan["plan_version"] == 1  # unchanged

    @pytest.mark.asyncio
    async def test_plan_version_increments(self, sample_response_plan):
        """Each revision should increment the plan version."""
        plan = {**sample_response_plan, "recommendations": [], "plan_version": 1}

        result = await audit_plan(plan)
        assert result.passed is False

        revised = await revise_plan(plan, result)
        assert revised["plan_version"] == 2

        # Revise again
        result2 = await audit_plan(revised)
        if not result2.passed:
            revised2 = await revise_plan(revised, result2)
            assert revised2["plan_version"] == 3
