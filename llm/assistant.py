# Initialize the model
import json
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from api.weather import get_weather, parse_and_get_weather


model = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


# -------------------------
# Prompt templates
# -------------------------

forecast_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a practical weather assistant for travelers. "
            "The user will see a separate climatology panel that already explains the typical weather "
            "and gives general packing advice for this trip. "
            "Your job is to provide a SHORT, supplementary note based ONLY on the forecast data. "
            "Do NOT repeat general climatology, do NOT repeat generic packing advice. "
            "Focus on concrete specifics in this particular forecast window: which days are rainy, "
            "unusually hot or cold, windy, or otherwise notable. "
            "Use ONLY the provided data; if something is missing/unavailable, say so briefly. "
            "Be SHORT and skimmable. Do not add extra sections. Do not repeat raw JSON. "
            "Hard limit: ~120 words (about 750 characters). "
            "Output format (exact headings):\n"
            "Short forecast note: <1-2 sentences>\n"
            "Notable days:\n"
            "- <up to 4 bullets; each bullet <= 12 words>\n"
            "Units: always show both C and F when you mention temps.",
        ),
        (
            "user",
            "Trip location: {location}\n"
            "Date range: {start_date} to {end_date}\n\n"
            "FORECAST (daily + summary stats, for a subset of the trip):\n"
            "{forecast}\n\n"
            "Remember: the user already has a separate climatology summary and packing advice panel. "
            "Your job is ONLY to highlight concrete specifics in this forecast data: "
            "which days are rainy, dry, hotter, cooler, or windy, and any short runs of similar days. "
            "Do not restate general patterns for the whole season. "
            "If precipitation/rain is not provided, do not speculate.",
        ),
    ]
)

climatology_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a practical weather assistant for travelers. "
            "Use ONLY the provided data; if something is missing/unavailable, say so briefly. "
            "This is climatology (what's typical), not a day-by-day forecast. "
            "Hard limit: ~140 words (about 900 characters). "
            "Output format (exact headings):\n"
            "Typical conditions: <1-2 sentences>\n"
            "What it means:\n"
            "- <up to 3 bullets; each bullet <= 12 words>\n"
            "Pack/plan:\n"
            "- <up to 5 bullets; each bullet <= 12 words>\n"
            "Units: always show both C and F when you mention temps.",
        ),
        (
            "user",
            "Trip location: {location}\n"
            "Date range: {start_date} to {end_date}\n\n"
            "CLIMATOLOGY (historical averages over multiple years):\n"
            "{climatology}\n\n"
            "If years_analyzed is present, mention it once in Typical conditions. "
            "Do not guess rain/precip if it is not provided.",
        ),
    ]
)

forecast_chain = forecast_prompt | model
climatology_chain = climatology_prompt | model


def _to_pretty_json(value) -> str:
    """Make nested dict/list data readable in the prompt."""
    if value is None:
        return "Not available."
    if isinstance(value, str):
        return value if value.strip() else "Not available."
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except TypeError:
        # fallback for non-serializable objects
        return str(value)
  


def formulate_response(query: str, country : str = None, start_date : datetime = None, end_date : str = None):
    """
    Returns the model response formatted from either forecast data or climatology data.
    Expects get_city_weather(query) to return a dict that may include:
      - location: {"name": str, "country": str} OR a string
      - date_range: {"start": str, "end": str} OR start_date/end_date
      - forecast: {"daily": [...], "summary": {...}} OR similar
      - climatology: {...}
    """
    weather_data = None
    # if the request provided the necessary data, don't try to parse the 
    if not start_date or not end_date or not country:
        weather_data = parse_and_get_weather(query, country) or {}
    else:
        weather_data = get_weather(query, country, start_date, end_date) or {}

    # Location string
    loc = weather_data.get("location")
    if isinstance(loc, dict):
        location_str = ", ".join([p for p in [loc.get("name"), loc.get("country")] if p])
    else:
        location_str = str(loc) if loc else "Unknown location"

    # Date range (if not provided, see if the parser caught it)
    dr = weather_data.get("date_range") or {}
    start_date = dr.get("start") or weather_data.get("start_date") or "Unknown start"
    end_date = dr.get("end") or weather_data.get("end_date") or "Unknown end"

    # Payloads (pretty JSON for readability)
    forecast_payload = weather_data.get("forecast") or weather_data.get("forecast_data")
    climatology_payload = weather_data.get("climatology") or weather_data.get("climatology_data")

    llm_data = {
        "location": location_str,
        "start_date": start_date,
        "end_date": end_date,
        "forecast": _to_pretty_json(forecast_payload),
        "climatology": _to_pretty_json(climatology_payload),
    }

    # Always prefer to show climatology as the main panel, with forecast as optional supplement
    climatology_result = None
    forecast_result = None

    if climatology_payload is not None:
        climatology_result = climatology_chain.invoke(llm_data)

    if forecast_payload is not None:
        forecast_result = forecast_chain.invoke(llm_data)

    if climatology_result is not None or forecast_result is not None:
        # Determine mode based on what we actually have
        if climatology_result is not None and forecast_result is not None:
            mode = "hybrid"
        elif climatology_result is not None:
            mode = "climatology_only"
        else:
            mode = "error"

        return {
            # Main panel text: climatology when available, otherwise forecast
            "mode": mode,
            "climatology_summary": (climatology_result.content if climatology_result is not None else forecast_result.content),
            "forecast_summary": forecast_result.content if forecast_result is not None else None,
        }

    # Fallback: nothing usable; do not call the LLM here
    llm_data["forecast"] = "Not available."
    llm_data["climatology"] = "Not available."
    return {
        "summary": (
            f"No forecast or climatology data is available for {location_str} "
            f"between {start_date} and {end_date}."
        ),
        "mode": "unavailable",
    }
