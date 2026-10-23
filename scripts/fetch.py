import json, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

POINTS = {
    "lalisquri": (42.099182, 45.418038, 780),
    "jidgeti": (42.178727, 44.880777, 1815),
    "ananuri": (42.184199, 44.739236, 1700),
    "tsivi": (41.779460, 45.451075, 1575),
    "udzilaurta": (42.443674, 44.979723, 2200),
}
MODELS = {"ecmwf": "ecmwf_ifs025", "gfs": "ncep_gfs_global", "icon": "icon_global"}
LEVELS = [925, 850, 700, 600, 500]
SURFACE = ["temperature_2m", "relative_humidity_2m", "cloud_cover",
           "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high",
           "precipitation", "shortwave_radiation", "wind_speed_10m",
           "wind_direction_10m", "cape", "boundary_layer_height"]
ALOFT = [f"{field}_{level}hPa" for level in LEVELS for field in
         ("temperature", "relative_humidity", "wind_speed",
          "wind_direction", "geopotential_height")]
OUT = Path("data")
OUT.mkdir(exist_ok=True)
now = datetime.now(timezone.utc)
results = {"generated_at_utc": now.isoformat(), "points": {}, "errors": [], "models": MODELS}
for point, (lat, lon, elev) in POINTS.items():
    results["points"][point] = {"latitude": lat, "longitude": lon,
        "takeoff_elevation_m_amsl": elev, "forecasts": {}}
    for name, model in MODELS.items():
        params = {"latitude": lat, "longitude": lon, "models": model,
                  "hourly": ",".join(SURFACE + ALOFT), "timezone": "Asia/Tbilisi",
                  "forecast_days": 5, "wind_speed_unit": "ms"}
        url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Georgia-XC-Weather/0.1"})
                with urllib.request.urlopen(req, timeout=55) as response:
                    data = json.load(response)
                if "hourly" not in data or not data["hourly"].get("time"):
                    raise ValueError("Missing hourly forecast")
                results["points"][point]["forecasts"][name] = data
                print("OK", point, name, len(data["hourly"]["time"]))
                break
            except Exception as exc:
                if attempt == 2:
                    results["errors"].append({"point": point, "model": name, "error": str(exc)})
                    print("ERROR", point, name, exc)
                else:
                    time.sleep(2 * (attempt + 1))
        time.sleep(0.25)
successful = sum(len(p["forecasts"]) for p in results["points"].values())
if successful == 0:
    raise SystemExit("All requests failed; existing forecast data preserved")
(OUT / "latest.json").write_text(json.dumps(results, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
(OUT / "status.json").write_text(json.dumps({"generated_at_utc": now.isoformat(),
    "successful": successful, "errors": results["errors"]}, ensure_ascii=False, indent=2), encoding="utf-8")
print("Saved", successful, "model/point forecasts")
