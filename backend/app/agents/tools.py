from app.llm.types import ToolDefinition

# ─── Diagnostic Agent Tools ───

DIAGNOSTIC_TOOLS = [
    ToolDefinition(
        name="get_portfolio_overview",
        description="Get aggregate portfolio health snapshot. Returns total restaurants, quadrant distribution, total revenue, revenue at risk, velocity alert count.",
        parameters={
            "type": "object",
            "properties": {
                "kam_name": {"type": "string", "description": "KAM name to filter by. Omit for all KAMs."},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_kam_briefing",
        description="Get prioritized action list for a KAM. Returns restaurants ordered by urgency: RESCUE first, then velocity alerts, TRIAGE, GROW opportunities.",
        parameters={
            "type": "object",
            "properties": {
                "kam_name": {"type": "string", "description": "KAM name."},
            },
            "required": ["kam_name"],
        },
    ),
    ToolDefinition(
        name="get_velocity_alerts",
        description="Get restaurants with velocity deterioration (rating crashing or demand collapsing). Returns escalation level: 'immediate' or '5_day'.",
        parameters={
            "type": "object",
            "properties": {
                "kam_name": {"type": "string", "description": "KAM name to filter. Omit for all."},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_revenue_at_risk",
        description="Get total weekly revenue exposed in RESCUE, TRIAGE, and velocity-threatened restaurants.",
        parameters={
            "type": "object",
            "properties": {
                "kam_name": {"type": "string", "description": "KAM name to filter. Omit for all."},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_restaurant_detail",
        description="Get complete signal profile for one restaurant. Returns all 6 risk signals (raw + normalized), health score, quadrant, revenue, velocity status, and metadata.",
        parameters={
            "type": "object",
            "properties": {
                "restaurant_id": {"type": "string", "description": "Restaurant ID (e.g., R0005)."},
            },
            "required": ["restaurant_id"],
        },
    ),
    ToolDefinition(
        name="get_restaurants_by_quadrant",
        description="Get all restaurants in a specific quadrant (GROW, RESCUE, NURTURE, or TRIAGE), sorted by health score.",
        parameters={
            "type": "object",
            "properties": {
                "quadrant": {"type": "string", "enum": ["GROW", "RESCUE", "NURTURE", "TRIAGE"]},
                "kam_name": {"type": "string", "description": "KAM name to filter. Omit for all."},
            },
            "required": ["quadrant"],
        },
    ),
    ToolDefinition(
        name="compare_restaurants",
        description="Side-by-side comparison of 2-5 restaurants. Returns full signal profiles for each.",
        parameters={
            "type": "object",
            "properties": {
                "restaurant_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of restaurant IDs to compare.",
                },
            },
            "required": ["restaurant_ids"],
        },
    ),
    ToolDefinition(
        name="get_city_breakdown",
        description="Geographic performance analysis: health, revenue, and quadrant distribution by city.",
        parameters={
            "type": "object",
            "properties": {
                "kam_name": {"type": "string", "description": "KAM name to filter. Omit for all."},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_vertical_breakdown",
        description="Vertical performance analysis: health, revenue, and quadrant distribution by business vertical.",
        parameters={
            "type": "object",
            "properties": {
                "kam_name": {"type": "string", "description": "KAM name to filter. Omit for all."},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="search_restaurants",
        description="Search restaurants by name, city, vertical, KAM, or ID. Case-insensitive substring match.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
            },
            "required": ["query"],
        },
    ),
]

# ─── RGM Strategy Agent Tools ───

RGM_TOOLS = [
    ToolDefinition(
        name="get_restaurant_detail",
        description="Get complete signal profile for one restaurant to inform strategy recommendations.",
        parameters={
            "type": "object",
            "properties": {
                "restaurant_id": {"type": "string", "description": "Restaurant ID."},
            },
            "required": ["restaurant_id"],
        },
    ),
    ToolDefinition(
        name="get_restaurants_by_quadrant",
        description="Get peer restaurants in the same quadrant for benchmarking.",
        parameters={
            "type": "object",
            "properties": {
                "quadrant": {"type": "string", "enum": ["GROW", "RESCUE", "NURTURE", "TRIAGE"]},
                "kam_name": {"type": "string", "description": "KAM name to filter."},
            },
            "required": ["quadrant"],
        },
    ),
    ToolDefinition(
        name="get_intervention_history",
        description="Get past interventions and outcomes for a restaurant. Helps avoid repeating ineffective strategies.",
        parameters={
            "type": "object",
            "properties": {
                "restaurant_id": {"type": "string", "description": "Restaurant ID."},
            },
            "required": ["restaurant_id"],
        },
    ),
]

# ─── Budget Agent Tools ───

BUDGET_TOOLS = [
    ToolDefinition(
        name="get_budget_balance",
        description="Get current weekly budget balance for a KAM. Shows remaining budget, total spent, and spend by category.",
        parameters={
            "type": "object",
            "properties": {
                "kam_name": {"type": "string", "description": "KAM name."},
            },
            "required": ["kam_name"],
        },
    ),
    ToolDefinition(
        name="log_intervention",
        description="Record a budget spend on a restaurant. Validates balance, logs the intervention, and returns updated balance.",
        parameters={
            "type": "object",
            "properties": {
                "kam_name": {"type": "string", "description": "KAM name."},
                "restaurant_id": {"type": "string", "description": "Restaurant ID."},
                "amount": {"type": "number", "description": "Amount in MXN."},
                "category": {
                    "type": "string",
                    "enum": ["promo", "credit", "ops_support", "growth_investment"],
                    "description": "Intervention category.",
                },
                "description": {"type": "string", "description": "What the spend is for."},
            },
            "required": ["kam_name", "restaurant_id", "amount", "category", "description"],
        },
    ),
    ToolDefinition(
        name="get_intervention_history",
        description="Get past interventions, optionally filtered by restaurant or KAM.",
        parameters={
            "type": "object",
            "properties": {
                "restaurant_id": {"type": "string", "description": "Filter by restaurant."},
                "kam_name": {"type": "string", "description": "Filter by KAM."},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="get_budget_roi",
        description="ROI analysis: revenue impact per dollar invested, broken down by quadrant and intervention type.",
        parameters={
            "type": "object",
            "properties": {
                "kam_name": {"type": "string", "description": "KAM name to filter."},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="request_escalation",
        description="Request supervisor approval for a spend that exceeds the weekly budget. Packages the request with diagnostic context.",
        parameters={
            "type": "object",
            "properties": {
                "kam_name": {"type": "string", "description": "KAM name."},
                "restaurant_id": {"type": "string", "description": "Restaurant ID."},
                "amount": {"type": "number", "description": "Amount requested in MXN."},
                "justification": {"type": "string", "description": "Why this investment is needed."},
            },
            "required": ["kam_name", "restaurant_id", "amount", "justification"],
        },
    ),
]

# ─── Router Agent Tools ───

ROUTER_TOOLS = [
    ToolDefinition(
        name="call_diagnostic_agent",
        description="Delegate to the Diagnostic Agent for: portfolio overview, weekly briefings, velocity alerts, restaurant details, comparisons, city/vertical breakdowns, restaurant search.",
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The message or sub-task to delegate to the diagnostic agent."},
            },
            "required": ["message"],
        },
    ),
    ToolDefinition(
        name="call_rgm_strategy_agent",
        description="Delegate to the RGM Strategy Agent for: growth strategies, recovery plans, menu optimization advice, ads recommendations, any 'what should I do?' question. Always call diagnostic agent first to get context.",
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The message or sub-task to delegate."},
                "diagnostic_context": {"type": "string", "description": "Output from the diagnostic agent to provide context for the strategy recommendation."},
            },
            "required": ["message"],
        },
    ),
    ToolDefinition(
        name="call_budget_agent",
        description="Delegate to the Budget Agent for: logging spends, checking balance, ROI queries, escalation requests.",
        parameters={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The message or sub-task to delegate."},
            },
            "required": ["message"],
        },
    ),
]
