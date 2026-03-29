"""Public Alert agent: drafts bilingual emergency alerts for affected regions."""

import logging
from datetime import datetime

from backend.services.gemini_client import generate_json

logger = logging.getLogger(__name__)

# Alert templates by severity
_ALERT_TEMPLATES = {
    "critical": {
        "en": (
            "EMERGENCY ALERT: {hazard_type} - Immediate action required in {region}. "
            "Seek shelter immediately. Do NOT attempt to travel. "
            "Follow instructions from emergency personnel. "
            "For emergency assistance call 911. "
            "Shelter locations: {shelters}. "
            "Stay tuned to emergency broadcast channels for updates."
        ),
        "es": (
            "ALERTA DE EMERGENCIA: {hazard_type} - Se requiere accion inmediata en {region}. "
            "Busque refugio inmediatamente. NO intente viajar. "
            "Siga las instrucciones del personal de emergencia. "
            "Para asistencia de emergencia llame al 911. "
            "Ubicaciones de refugio: {shelters}. "
            "Mantengase informado a traves de los canales de transmision de emergencia."
        ),
    },
    "high": {
        "en": (
            "SEVERE WEATHER ALERT: {hazard_type} affecting {region}. "
            "Prepare to evacuate if instructed. Secure your property. "
            "Avoid unnecessary travel. Monitor emergency channels. "
            "Shelter locations: {shelters}. "
            "For non-emergency assistance, call 311."
        ),
        "es": (
            "ALERTA DE CLIMA SEVERO: {hazard_type} afectando {region}. "
            "Preparese para evacuar si se lo indican. Asegure su propiedad. "
            "Evite viajes innecesarios. Monitoree los canales de emergencia. "
            "Ubicaciones de refugio: {shelters}. "
            "Para asistencia no urgente, llame al 311."
        ),
    },
    "medium": {
        "en": (
            "WEATHER ADVISORY: {hazard_type} possible in {region}. "
            "Stay informed and have an emergency plan ready. "
            "Check on elderly neighbors and those with special needs. "
            "Shelter information: {shelters}."
        ),
        "es": (
            "AVISO METEOROLOGICO: {hazard_type} posible en {region}. "
            "Mantengase informado y tenga un plan de emergencia listo. "
            "Verifique el estado de vecinos mayores y personas con necesidades especiales. "
            "Informacion de refugios: {shelters}."
        ),
    },
}


async def run_public_alert(scenario: dict) -> dict:
    """Draft bilingual public alerts for affected regions.

    Args:
        scenario: Dict with "scenario" text, "severity", optional
                  "impacted_zones", "recommendations", "shelters".

    Returns:
        List of drafted alert objects with en/es versions for each region.
    """
    scenario_text = scenario.get("scenario", "")
    severity = scenario.get("severity", "high")
    impacted_zones = scenario.get("impacted_zones", [])
    recommendations = scenario.get("recommendations", [])
    shelters = scenario.get("shelters", [])

    # Try LLM-generated alerts first
    llm_alerts = await _llm_generate_alerts(scenario)
    if llm_alerts:
        logger.info("Using LLM-generated alerts (%d total)", len(llm_alerts))
        return {
            "alerts": llm_alerts,
            "total_alerts": len(llm_alerts),
            "languages": ["en", "es"],
            "regions_covered": impacted_zones or ["Tampa Metro Area"],
            "source": "gemini",
            "drafted_at": datetime.utcnow().isoformat(),
        }

    # Fallback: template-based alerts
    logger.info("Using template-based alerts (Gemini unavailable)")
    # Determine hazard type from scenario text
    hazard_type = _infer_hazard_type(scenario_text)

    # Determine regions to alert
    regions = impacted_zones if impacted_zones else ["Tampa Metro Area"]

    # Format shelter names
    if shelters:
        shelter_names = ", ".join(
            s.get("name", s.get("shelter_id", "Unknown")) for s in shelters[:3]
        )
    else:
        shelter_names = "Lincoln Community Center, Riverside High School Gymnasium, Metro Convention Center"

    # Select template tier
    template_key = severity if severity in _ALERT_TEMPLATES else "high"
    templates = _ALERT_TEMPLATES[template_key]

    alerts: list[dict] = []
    for region in regions:
        format_vars = {
            "hazard_type": hazard_type,
            "region": region,
            "shelters": shelter_names,
        }

        # English alert
        alerts.append({
            "message": templates["en"].format(**format_vars),
            "language": "en",
            "severity": severity,
            "region": region,
            "target_audience": "general_public",
        })

        # Spanish alert
        alerts.append({
            "message": templates["es"].format(**format_vars),
            "language": "es",
            "severity": severity,
            "region": region,
            "target_audience": "general_public",
        })

    # Add special-needs targeted alert if relevant
    if any("medical" in r.lower() or "elderly" in r.lower() or "vulnerable" in r.lower()
           for r in recommendations):
        alerts.append({
            "message": (
                f"SPECIAL NEEDS ALERT: If you or someone you know requires medical equipment, "
                f"mobility assistance, or has special needs, contact 911 immediately for "
                f"priority evacuation assistance. Accessible shelters available at: {shelter_names}."
            ),
            "language": "en",
            "severity": "critical",
            "region": "All Affected Zones",
            "target_audience": "special_needs",
        })
        alerts.append({
            "message": (
                f"ALERTA DE NECESIDADES ESPECIALES: Si usted o alguien que conoce requiere "
                f"equipo medico, asistencia de movilidad o tiene necesidades especiales, "
                f"llame al 911 inmediatamente para asistencia prioritaria de evacuacion. "
                f"Refugios accesibles disponibles en: {shelter_names}."
            ),
            "language": "es",
            "severity": "critical",
            "region": "Todas las Zonas Afectadas",
            "target_audience": "special_needs",
        })

    result = {
        "alerts": alerts,
        "total_alerts": len(alerts),
        "languages": ["en", "es"],
        "regions_covered": regions,
        "drafted_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        "Public alert agent complete: %d alerts drafted for %d regions",
        len(alerts), len(regions),
    )
    return result


async def _llm_generate_alerts(scenario: dict) -> list[dict] | None:
    """Use Gemini to draft contextual bilingual alerts."""
    zones = scenario.get("impacted_zones", ["Tampa Metro Area"])
    shelters = scenario.get("shelters", [])
    shelter_names = ", ".join(s.get("name", "Shelter") for s in shelters[:3]) or "Local emergency shelters"

    prompt = f"""Draft emergency public alerts for this disaster scenario.

Scenario: {scenario.get("scenario", "Unknown emergency")}
Severity: {scenario.get("severity", "high")}
Affected zones: {", ".join(zones)}
Available shelters: {shelter_names}

Create alerts for each zone in BOTH English and Spanish.
Also create one special-needs alert in each language.

Return a JSON array where each alert has:
- "message": the full alert text (2-4 sentences, clear, actionable)
- "language": "en" or "es"
- "severity": "{scenario.get("severity", "high")}"
- "region": the zone name
- "target_audience": "general_public" or "special_needs"

Make alerts specific to the scenario, not generic. Include shelter names and 911 call instruction."""

    result = await generate_json(
        prompt,
        system_instruction="You are a FEMA-certified emergency alert writer. Write clear, actionable, non-panicking alerts. Spanish alerts must be natural, not machine-translated.",
    )

    if isinstance(result, list) and len(result) >= 2:
        return result
    if isinstance(result, dict) and "alerts" in result:
        return result["alerts"]
    return None


def _infer_hazard_type(scenario_text: str) -> str:
    """Infer a human-readable hazard type from scenario text."""
    text = scenario_text.lower()
    if "tornado" in text:
        return "Tornado"
    if "ice" in text or "freezing" in text:
        return "Ice Storm"
    if "flood" in text:
        return "Flash Flooding"
    if "storm" in text and "thunder" in text:
        return "Severe Thunderstorm"
    if "storm" in text:
        return "Severe Storm"
    if "outage" in text or "power" in text:
        return "Power Grid Emergency"
    if "multi" in text or "widespread" in text:
        return "Multi-Hazard Severe Weather"
    if "hurricane" in text:
        return "Hurricane"
    if "earthquake" in text:
        return "Earthquake"
    return "Severe Weather Event"
