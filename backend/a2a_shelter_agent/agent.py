"""Shelter Specialist Agent - analyzes shelter capacity and accessibility."""

from __future__ import annotations

import math
from typing import Any

MOCK_SHELTERS: list[dict[str, Any]] = [
    {
        "shelter_id": "SH-001",
        "name": "Tampa Convention Center",
        "address": "333 S Franklin St, Tampa",
        "capacity": 500,
        "occupancy": 127,
        "accessibility": "full_ada",
        "supplies": {
            "water_gallons": 800,
            "cots": 350,
            "first_aid_kits": 75,
            "blankets": 400,
            "mre_meals": 2000,
        },
        "backup_power": True,
        "medical_staff": True,
        "pet_friendly": True,
        "coordinates": {"lat": 27.9425, "lng": -82.4515},
    },
    {
        "shelter_id": "SH-002",
        "name": "Hillsborough High School Gymnasium",
        "address": "5000 N Central Ave, Tampa",
        "capacity": 300,
        "occupancy": 289,
        "accessibility": "wheelchair",
        "supplies": {
            "water_gallons": 200,
            "cots": 150,
            "first_aid_kits": 20,
            "blankets": 180,
            "mre_meals": 600,
        },
        "backup_power": False,
        "medical_staff": False,
        "pet_friendly": False,
        "coordinates": {"lat": 27.9750, "lng": -82.4590},
    },
    {
        "shelter_id": "SH-003",
        "name": "Idlewild Baptist Church",
        "address": "18333 Exciting Idlewild Blvd, Lutz",
        "capacity": 200,
        "occupancy": 45,
        "accessibility": "standard",
        "supplies": {
            "water_gallons": 400,
            "cots": 180,
            "first_aid_kits": 40,
            "blankets": 200,
            "mre_meals": 1000,
        },
        "backup_power": True,
        "medical_staff": False,
        "pet_friendly": True,
        "coordinates": {"lat": 28.0750, "lng": -82.4850},
    },
    {
        "shelter_id": "SH-004",
        "name": "Florida State Fairgrounds",
        "address": "4800 US Hwy 301 N, Tampa",
        "capacity": 1000,
        "occupancy": 312,
        "accessibility": "full_ada",
        "supplies": {
            "water_gallons": 1500,
            "cots": 800,
            "first_aid_kits": 100,
            "blankets": 900,
            "mre_meals": 5000,
        },
        "backup_power": True,
        "medical_staff": True,
        "pet_friendly": True,
        "coordinates": {"lat": 27.9650, "lng": -82.3980},
    },
]

# ---------------------------------------------------------------------------
# Thresholds & constants
# ---------------------------------------------------------------------------

OCCUPANCY_CRITICAL_PCT = 0.80  # 80 % occupancy = near-capacity
WATER_GALLONS_PER_PERSON_PER_DAY = 1.0
MEALS_PER_PERSON_PER_DAY = 3.0
MIN_SUPPLY_DAYS = 3  # we want at least 3 days of runway

ACCESSIBILITY_RANK = {"full_ada": 3, "wheelchair": 2, "standard": 1}


def _occupancy_pct(shelter: dict) -> float:
    """Return occupancy as a fraction 0-1."""
    if shelter["capacity"] == 0:
        return 1.0
    return shelter["occupancy"] / shelter["capacity"]


def _available_capacity(shelter: dict) -> int:
    return max(0, shelter["capacity"] - shelter["occupancy"])


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _supply_warnings(shelter: dict) -> list[str]:
    """Check each supply category against minimum runway thresholds."""
    warnings: list[str] = []
    current_occupancy = max(shelter["occupancy"], 1)  # avoid division by zero
    supplies = shelter["supplies"]

    water_days = supplies["water_gallons"] / (current_occupancy * WATER_GALLONS_PER_PERSON_PER_DAY)
    if water_days < MIN_SUPPLY_DAYS:
        warnings.append(
            f"Water supply critically low: ~{water_days:.1f} days remaining "
            f"({supplies['water_gallons']} gal for {current_occupancy} occupants)"
        )

    meal_days = supplies["mre_meals"] / (current_occupancy * MEALS_PER_PERSON_PER_DAY)
    if meal_days < MIN_SUPPLY_DAYS:
        warnings.append(
            f"MRE supply low: ~{meal_days:.1f} days remaining "
            f"({supplies['mre_meals']} meals for {current_occupancy} occupants)"
        )

    if supplies["cots"] < current_occupancy:
        deficit = current_occupancy - supplies["cots"]
        warnings.append(f"Cot shortage: {deficit} additional cots needed")

    if supplies["blankets"] < current_occupancy:
        deficit = current_occupancy - supplies["blankets"]
        warnings.append(f"Blanket shortage: {deficit} additional blankets needed")

    if supplies["first_aid_kits"] < current_occupancy * 0.05:
        warnings.append(
            f"First-aid kits below recommended level "
            f"({supplies['first_aid_kits']} kits for {current_occupancy} occupants; recommend 1 per 20)"
        )

    return warnings


def _score_shelter(shelter: dict, query: dict) -> float:
    """Higher is better.  Factors: available capacity, supplies runway, features."""
    available = _available_capacity(shelter)
    score = available * 1.0  # base: raw available beds

    # Bonus for backup power
    if shelter["backup_power"]:
        score += 50
    # Bonus for medical staff
    if shelter["medical_staff"]:
        score += 40
    # Bonus for pet-friendly
    if shelter["pet_friendly"]:
        score += 20

    # Penalty for being near capacity
    occ_pct = _occupancy_pct(shelter)
    if occ_pct >= OCCUPANCY_CRITICAL_PCT:
        score -= 200

    # Penalty for supply warnings
    warnings = _supply_warnings(shelter)
    score -= len(warnings) * 30

    # Accessibility bonus if the caller requires it
    required = query.get("accessibility_required")
    if required:
        shelter_rank = ACCESSIBILITY_RANK.get(shelter["accessibility"], 0)
        required_rank = ACCESSIBILITY_RANK.get(required, 0)
        if shelter_rank >= required_rank:
            score += 60
        else:
            score -= 500  # does not meet requirements

    return score


def _build_recommendations(
    shelters: list[dict],
    critical: list[dict],
    all_warnings: list[dict],
    query: dict,
) -> list[str]:
    """Generate human-readable recommendations."""
    recs: list[str] = []

    total_available = sum(_available_capacity(s) for s in shelters)
    capacity_needed = query.get("capacity_needed")

    if capacity_needed and total_available < capacity_needed:
        deficit = capacity_needed - total_available
        recs.append(
            f"URGENT: Total available shelter capacity ({total_available}) is insufficient "
            f"for the requested {capacity_needed}. Need {deficit} additional spots. "
            "Activate overflow / mutual-aid agreements."
        )
    elif capacity_needed and total_available >= capacity_needed:
        recs.append(
            f"Available capacity ({total_available}) meets the requested need ({capacity_needed})."
        )

    if critical:
        names = ", ".join(s["name"] for s in critical)
        recs.append(
            f"Near-capacity shelters requiring immediate attention: {names}. "
            "Consider redirecting new arrivals to shelters with more availability."
        )

    # Identify the best shelter to redirect to
    if shelters:
        best = max(shelters, key=lambda s: _available_capacity(s))
        if _available_capacity(best) > 0:
            recs.append(
                f"Recommended primary intake shelter: {best['name']} "
                f"({_available_capacity(best)} spots available, "
                f"{'has' if best['backup_power'] else 'NO'} backup power, "
                f"{'has' if best['medical_staff'] else 'NO'} medical staff)."
            )

    # Supply-related recommendations
    shelters_with_warnings = [w for w in all_warnings if w["warnings"]]
    if shelters_with_warnings:
        for sw in shelters_with_warnings:
            recs.append(
                f"Supply alert at {sw['shelter_name']}: {'; '.join(sw['warnings'])}"
            )

    # Power concerns
    no_power = [s for s in shelters if not s["backup_power"]]
    if no_power:
        names = ", ".join(s["name"] for s in no_power)
        recs.append(
            f"Shelters without backup power: {names}. "
            "Deploy generators if extended outage is expected."
        )

    scenario = query.get("scenario", "").lower()
    if scenario:
        if "hurricane" in scenario or "flood" in scenario:
            recs.append(
                "Flooding scenario detected: prioritize shelters on higher ground "
                "and those with backup power."
            )
        if "earthquake" in scenario:
            recs.append(
                "Earthquake scenario detected: structural inspections recommended "
                "before accepting occupants."
            )
        if "heat" in scenario or "cold" in scenario or "winter" in scenario:
            recs.append(
                "Extreme temperature scenario detected: ensure HVAC is operational "
                "and blankets/cooling supplies are stocked."
            )

    return recs


async def analyze_shelters(query: dict | None = None) -> dict:
    """Analyze shelter capacity, accessibility, and supply status.

    Args:
        query: dict with optional keys:
            - zone (str): geographic zone hint (not used for mock data but accepted)
            - accessibility_required (str): "standard" | "wheelchair" | "full_ada"
            - capacity_needed (int): minimum total capacity the caller needs
            - scenario (str): disaster scenario context string

    Returns:
        Structured analysis dict.
    """
    if query is None:
        query = {}

    shelters = list(MOCK_SHELTERS)  # start with all shelters

    # ----- Filter by accessibility -----
    accessibility_required = query.get("accessibility_required")
    if accessibility_required:
        req_rank = ACCESSIBILITY_RANK.get(accessibility_required, 0)
        shelters = [
            s for s in shelters
            if ACCESSIBILITY_RANK.get(s["accessibility"], 0) >= req_rank
        ]

    # ----- Filter by minimum capacity -----
    capacity_needed = query.get("capacity_needed")
    # We do NOT remove shelters that individually lack capacity; the caller
    # cares about aggregate.  But we annotate each shelter.

    # ----- Build per-shelter detail -----
    enriched_shelters: list[dict] = []
    critical_shelters: list[dict] = []
    all_supply_warnings: list[dict] = []
    accessibility_summary: dict[str, int] = {"full_ada": 0, "wheelchair": 0, "standard": 0}

    for shelter in shelters:
        available = _available_capacity(shelter)
        occ_pct = _occupancy_pct(shelter)
        warnings = _supply_warnings(shelter)
        score = _score_shelter(shelter, query)

        enriched = {
            **shelter,
            "available_capacity": available,
            "occupancy_pct": round(occ_pct * 100, 1),
            "supply_warnings": warnings,
            "score": round(score, 1),
        }
        enriched_shelters.append(enriched)

        if occ_pct >= OCCUPANCY_CRITICAL_PCT:
            critical_shelters.append(enriched)

        all_supply_warnings.append({
            "shelter_id": shelter["shelter_id"],
            "shelter_name": shelter["name"],
            "warnings": warnings,
        })

        acc = shelter["accessibility"]
        if acc in accessibility_summary:
            accessibility_summary[acc] += 1

    # Sort by score descending (best shelter first)
    enriched_shelters.sort(key=lambda s: s["score"], reverse=True)

    total_available_capacity = sum(s["available_capacity"] for s in enriched_shelters)

    # Flatten all supply warnings to a single list with shelter context
    flat_warnings: list[str] = []
    for sw in all_supply_warnings:
        for w in sw["warnings"]:
            flat_warnings.append(f"[{sw['shelter_name']}] {w}")

    recommendations = _build_recommendations(
        enriched_shelters, critical_shelters, all_supply_warnings, query
    )

    return {
        "shelters": enriched_shelters,
        "total_available_capacity": total_available_capacity,
        "critical_shelters": [
            {
                "shelter_id": s["shelter_id"],
                "name": s["name"],
                "occupancy_pct": s["occupancy_pct"],
                "available_capacity": s["available_capacity"],
            }
            for s in critical_shelters
        ],
        "supply_warnings": flat_warnings,
        "recommendations": recommendations,
        "accessibility_summary": accessibility_summary,
    }
