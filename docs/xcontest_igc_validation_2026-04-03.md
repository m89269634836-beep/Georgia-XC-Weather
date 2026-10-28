# First full IGC validation — Lalisquri, 2026-04-03

## Access
A signed-in XContest account was able to download the full IGC while a different account could not view the track. Access rights / session appear relevant; this does **not** establish anonymous API or mass-download access. Do not store account credentials, cookies or temporary signed URLs here.

## IGC facts (GPS records)
- Source: user-supplied `.igc`, exported from the account that can view this flight.
- Device: SeeYou Navigator on iPhone.
- Fixes: 25,335 B records, 1 Hz throughout, all flagged valid (`A`).
- Flight record: 2026-04-03 07:50:19–14:52:33 UTC = 11:50:19–18:52:33 Georgia time.
- IGC auxiliary metadata reports takeoff 07:51:10 UTC.
- First GPS point: 42.099383 N, 45.417917 E, 792 m GPS AMSL — Lalisquri.
- Max GPS altitude: 2,970 m AMSL.
- Full GPS trajectory length: 273.77 km including thermal circles; NOT the optimized ~167.6 km XContest scoring distance.
- Initial departure ground track approx. 106 degrees **TO** (east-southeast). NOT a direct wind direction (FROM) measurement.

## Provisional thermal extraction

Using smoothed 1 Hz GPS positions, 60-second turning consistency, sustained net climb, and merge/split heuristics:
- ~47 distinct climbing circle segments, totaling ~130.8 minutes.
- Median segment net climb rate **+1.85 m/s**.
- Strongest multi-minute segment mean **+3.38 m/s**.
- ~26 multi-orbit climb segments support a tentative drift-based wind calculation.
- Drift of thermal cores is only an approximate proxy for wind; pilot adjustments, changes in core location and incomplete circles create bias.
- Need independent checks of segment classification and meteorological wind using other IGCs from the same day.

## Next steps
1. Acquire 5–10 authorized full IGCs from distinct dates for Lalisquri and Jidgeti (prefer same-day multi-pilot comparisons).
2. Parse 1 Hz B records, fix flags, timestamps, coordinates and GPS/pressure altitudes, preserving raw source and provenance.
3. Store per-flight derived circling intervals, climb rates, altitudes, track corridors and wind estimates with confidence flags.
4. Retrieve the archived D-1 weather forecast for the corresponding date and coordinates.
5. Assess model bias and predictability with held-out dates, NOT just the strongest XContest result.
6. For bulk acquisition, prefer supported authenticated export or documented authorized APIs. Do not bypass account-level access restrictions.

The downloaded third-party raw IGC was not committed to the public repository.
