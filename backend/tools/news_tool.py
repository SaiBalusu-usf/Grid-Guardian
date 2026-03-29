"""News and social media feed tool returning mock disaster-relevant articles."""

import logging
from datetime import datetime, timedelta

from backend.config import settings

logger = logging.getLogger(__name__)

_MOCK_ARTICLES_BY_SCENARIO: dict[str, list[dict]] = {
    "storm": [
        {
            "title": "Severe Thunderstorm Complex Rapidly Intensifying Over Central Region",
            "source": "National Weather Service",
            "summary": "A powerful mesoscale convective system is producing widespread severe weather including confirmed tornadoes, large hail, and damaging winds across multiple counties.",
            "relevance_score": 0.97,
        },
        {
            "title": "Emergency Services Overwhelmed as Storm Damage Reports Surge",
            "source": "Local Emergency Management",
            "summary": "911 call centers report a 400% increase in emergency calls. Multiple structure collapses reported in downtown area. Power outages affecting 50,000+ customers.",
            "relevance_score": 0.94,
        },
        {
            "title": "Residents Share Tornado Footage on Social Media",
            "source": "Twitter/X Aggregated",
            "summary": "Dozens of videos showing funnel clouds and structural damage circulating online. Reports of injuries near Oak Valley subdivision.",
            "relevance_score": 0.88,
        },
        {
            "title": "Red Cross Opens Emergency Shelters Across Three Counties",
            "source": "American Red Cross",
            "summary": "Six emergency shelters activated with capacity for 2,000 displaced residents. Volunteers needed for overnight staffing.",
            "relevance_score": 0.85,
        },
    ],
    "outage": [
        {
            "title": "Ice Storm Cripples Power Grid: 200,000 Without Electricity",
            "source": "Regional Power Authority",
            "summary": "Heavy ice accumulation has downed power lines across the metro area. Restoration estimated to take 3-5 days for hardest-hit zones.",
            "relevance_score": 0.96,
        },
        {
            "title": "Hospitals Switch to Emergency Generators Amid Prolonged Outage",
            "source": "Healthcare Network",
            "summary": "Three major hospitals operating on backup power. Generator fuel supplies expected to last 48 hours without resupply.",
            "relevance_score": 0.93,
        },
        {
            "title": "Warming Centers Open for Vulnerable Residents",
            "source": "City Emergency Management",
            "summary": "City opens 12 warming centers as temperatures drop below freezing. Special focus on elderly and unhoused populations.",
            "relevance_score": 0.90,
        },
    ],
    "multi-zone": [
        {
            "title": "Multi-County Disaster Declaration as Severe Weather Continues",
            "source": "Governor's Office",
            "summary": "State of emergency declared for six counties. National Guard activated to assist with search and rescue, road clearance, and shelter operations.",
            "relevance_score": 0.98,
        },
        {
            "title": "Major Highway Closures Due to Flooding and Debris",
            "source": "Department of Transportation",
            "summary": "Interstate 35 closed in both directions. Multiple state highways impassable. Motorists advised to shelter in place.",
            "relevance_score": 0.95,
        },
        {
            "title": "Search and Rescue Operations Underway in Three Zones",
            "source": "FEMA Region VI",
            "summary": "Urban search and rescue teams deployed to zones A, B, and C. Confirmed structural collapses in residential and commercial areas.",
            "relevance_score": 0.93,
        },
        {
            "title": "Community Volunteers Self-Organize Rescue Efforts on Social Media",
            "source": "Facebook/Reddit Aggregated",
            "summary": "Local community groups coordinating boat rescues and supply drops via social media. Officials urge caution and coordination with official channels.",
            "relevance_score": 0.82,
        },
    ],
}

_DEFAULT_ARTICLES: list[dict] = [
    {
        "title": "Severe Weather Event Prompts Emergency Response Activation",
        "source": "Local News Network",
        "summary": "Emergency management agencies have activated their operations centers in response to developing severe weather conditions.",
        "relevance_score": 0.85,
    },
    {
        "title": "Utility Companies Preparing for Potential Service Disruptions",
        "source": "Energy Commission",
        "summary": "Regional utilities have pre-positioned repair crews and equipment ahead of the forecasted severe weather event.",
        "relevance_score": 0.78,
    },
]


async def get_news_feed(query: str, scenario: str = "") -> dict:
    """Retrieve news and social media articles relevant to a disaster scenario.

    Args:
        query: Search query string.
        scenario: Optional scenario hint for mock selection.

    Returns:
        Structured news feed with relevance-scored articles.
    """
    if settings.is_mock:
        return _mock_news(query, scenario)
    return await _live_news(query, scenario)


def _mock_news(query: str, scenario: str) -> dict:
    """Return mock news articles matched by scenario keywords."""
    combined = f"{scenario} {query}".lower()
    now = datetime.utcnow()

    selected: list[dict] | None = None
    for key, articles in _MOCK_ARTICLES_BY_SCENARIO.items():
        if key in combined:
            selected = articles
            break

    if selected is None:
        selected = _DEFAULT_ARTICLES

    # Add timestamps working backwards from now
    timestamped = []
    for i, article in enumerate(selected):
        entry = {
            **article,
            "timestamp": (now - timedelta(minutes=15 * i)).isoformat(),
        }
        timestamped.append(entry)

    logger.info("Mock news feed returned %d articles for query '%s'", len(timestamped), query)
    return {
        "articles": timestamped,
        "query": query,
        "retrieved_at": now.isoformat(),
    }


async def _live_news(query: str, scenario: str) -> dict:
    """Fetch real news from GDELT DOC API (free, no key required).

    Falls back to mock if the API is unreachable.
    """
    import httpx

    try:
        search_terms = query.replace(",", " ")[:100]
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.gdeltproject.org/api/v2/doc/doc",
                params={
                    "query": search_terms,
                    "mode": "ArtList",
                    "maxrecords": "5",
                    "format": "json",
                    "sort": "DateDesc",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        now = datetime.utcnow()
        articles = []
        for i, art in enumerate(data.get("articles", [])[:5]):
            articles.append({
                "title": art.get("title", "Untitled")[:150],
                "source": art.get("domain", "Unknown"),
                "summary": art.get("seendate", ""),
                "relevance_score": round(0.95 - i * 0.05, 2),
                "timestamp": art.get("seendate", now.isoformat()),
                "url": art.get("url", ""),
            })

        if not articles:
            return _mock_news(query, scenario)

        logger.info("Live news: %d articles from GDELT for '%s'", len(articles), search_terms[:40])
        return {
            "articles": articles,
            "query": query,
            "source": "gdelt",
            "retrieved_at": now.isoformat(),
        }

    except Exception as exc:
        logger.warning("GDELT news API failed (%s), falling back to mock", exc)
        return _mock_news(query, scenario)
