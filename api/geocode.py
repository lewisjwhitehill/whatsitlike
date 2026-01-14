from dataclasses import dataclass
import requests

OM_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"

@dataclass
class GeocodeResult:
    name: str
    latitude: float
    longitude: float
    country: str | None = None
    admin1: str | None = None
    tz: str | None = None


def geocodeCity(q: str) -> GeocodeResult:
	params = {
		"name": q,
    "count": 1,
    "language": "en",
    "format": "json",
  }   
     
	res = requests.get(OM_GEOCODE, params=params, timeout=10)
	if not res.ok:
		raise RuntimeError(f"Geocoding failed: {res.status_code}")
     
	data = res.json()
	results = data.get("results") or []
	if not results:
		raise ValueError("No results for that place.")
     
	r = results[0]
	return GeocodeResult(
        name=r["name"],
        latitude=r["latitude"],
        longitude=r["longitude"],
        country=r.get("country"),
        admin1=r.get("admin1"),
        tz=r.get("timezone"),
  )