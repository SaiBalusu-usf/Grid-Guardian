"""FunctionTool wrappers for all GridGuardian tools, grouped by agent role."""

from google.adk.tools import FunctionTool

from backend.tools.weather_tool import get_weather
from backend.tools.hazard_tool import get_hazard_zones
from backend.tools.news_tool import get_news_feed
from backend.tools.routing_tool import get_routes
from backend.tools.notification_tool import send_notification
from backend.tools.firestore_tool import query_collection

# ── Hazard Watcher Agent tools ───────────────────────────────────────────────
weather_tool = FunctionTool(get_weather)
hazard_tool = FunctionTool(get_hazard_zones)
news_tool = FunctionTool(get_news_feed)

HAZARD_WATCHER_TOOLS = [weather_tool, hazard_tool, news_tool]

# ── Route Planner Agent tools ────────────────────────────────────────────────
routing_tool = FunctionTool(get_routes)

ROUTE_PLANNER_TOOLS = [routing_tool]

# ── Resource Coordinator Agent tools ─────────────────────────────────────────
firestore_query_tool = FunctionTool(query_collection)

RESOURCE_TOOLS = [firestore_query_tool]

# ── Public Alert Agent tools ─────────────────────────────────────────────────
notification_tool = FunctionTool(send_notification)

ALERT_TOOLS = [notification_tool]
