# Georgia XC Weather

Cloud collector for Georgian paragliding XC forecasts using Open-Meteo (ECMWF, GFS, ICON).

Scheduled for 06:17, 12:17 and 18:17 Georgia time, plus manual runs under Actions.

Five confirmed takeoff points: Lalisquri, Jidgeti, Ananuri, Tsivi, Udzilaurta. Gudauri awaits verified coordinates.

Outputs: `data/latest.json` and `data/status.json`. This is a raw-data collector, not a validated XC scoring or Skew-T system yet.

To run: Actions → Georgia XC weather data → Run workflow. In Settings → Actions → General, enable workflow read/write permissions if publishing fails.

Forecast API requests may fail if a selected model lacks an hourly field; check Actions logs. No forecast is claimed until a successful workflow run.
