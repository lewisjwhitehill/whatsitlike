# Initialize the model
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from api.weather import get_city_weather


model = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


# -------------------------
# Prompt templates
# -------------------------

forecast_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a practical weather assistant for travelers. "
            "Use ONLY the provided data; if something is missing/unavailable, say so briefly. "
            "Be SHORT and skimmable. Do not add extra sections. Do not repeat raw JSON. "
            "Hard limit: ~140 words (about 900 characters). "
            "Output format (exact headings):\n"
            "Overview: <1-2 sentences>\n"
            "Key days:\n"
            "- <up to 3 bullets; each bullet <= 12 words>\n"
            "Pack/plan:\n"
            "- <up to 5 bullets; each bullet <= 12 words>\n"
            "Units: always show both C and F when you mention temps.",
        ),
        (
            "user",
            "Trip location: {location}\n"
            "Date range: {start_date} to {end_date}\n\n"
            "FORECAST (daily + summary stats):\n"
            "{forecast}\n\n"
            "Write the response using ONLY the data above. "
            "Prefer summary stats for numbers when present; otherwise pick the most relevant daily values. "
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


def formulate_response(query: str):
    """
    Returns the model response formatted from either forecast data or climatology data.
    Expects get_city_weather(query) to return a dict that may include:
      - location: {"name": str, "country": str} OR a string
      - date_range: {"start": str, "end": str} OR start_date/end_date
      - forecast: {"daily": [...], "summary": {...}} OR similar
      - climatology: {...}
    """
    weather_data = get_city_weather(query) or {}

    # Location string
    loc = weather_data.get("location")
    if isinstance(loc, dict):
        location_str = ", ".join([p for p in [loc.get("name"), loc.get("country")] if p])
    else:
        location_str = str(loc) if loc else "Unknown location"

    # Date range
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

    # Choose chain: prefer forecast when present, otherwise climatology when present
    # maybe add the content extraction as part of the pipeline?
    if forecast_payload is not None:
        result = forecast_chain.invoke(llm_data)
        return {
            "summary": result.content,
            "mode": "forecast",  # 0-like
        }

    if climatology_payload is not None:
        result = climatology_chain.invoke(llm_data)
        return {
            "summary": result.content,
            "mode": "climatology",  # 1-like
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
