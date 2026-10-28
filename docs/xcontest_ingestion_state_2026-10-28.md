# XContest ingest: operational state (2026-10-28)

## Confirmed data held in conversation archives

- Source `georgia_flights.json`: 2,875 raw XContest list-flight records.
- After country ISO + coordinate bounding box filter and deduplication: **2,744** geographic Georgia records, 2023-03-16 to 2026-06-08.
- Additional `xcontest_xc_collector_v04_2026-10-19T10-15-29-778Z.json`: **1,155** list-flight records, scanned 2026-07-01 through 2026-09-30; zero duplicate flight IDs with the older set.
- Combined available metadata: **3,899** flight records, NO IGC/GPS fix sequences.
- The larger `part_0001(2).json` is an early **26,023-row worldwide slice (2006–2008)**, not a fresh complete Georgian track archive.
- Current gaps in these exports: 2026-06-09 through 2026-06-30 and 2026-10-01 onward.

## Joined site identifiers / historical cautions

- `gudauri_2792`: 1,322 merged records; `gudauri_2791`: 259. Do not mix physical Gudauri launch positions when modeling takeoff wind.
- `lalisquri`: 266 merged records.
- `ananuri`: 464 merged records (some are assigned by takeoff ID without precise takeoff coordinates).
- `jidgeti`: 46 matched by precise coordinates, plus potential unmatched id-0 records.
- `udzilaurta`: 24 matched by precise coordinates.
- `tsivi`: **5** matching the specified physical launch 41.779460,45.451075.
- `tsivi_area_unresolved`: 3 additional XContest records assigned by ID only; do not treat them as physically launching from that exact Tsivi coordinate.
- 824 of the 1,155 new collector rows lack precise launch coordinates (some have only an XContest hotspot URL). Store `geo_confidence` and keep low-confidence records separate.

Counts are based solely on the two archived datasets; they are NOT total XContest site flight counts. The area box is not the exact political border of Georgia.

## Next technical steps

1. Continue low-rate **public** list-flight collection for missing periods, preserving original flight IDs and forecast issue-time snapshots.
2. Try a single unauthenticated request to a public flight-detail and route-KML URL using the independent `XContest public access probe` GitHub workflow.
3. If these return HTTP 403/401, **stop**: do not bypass rate limits/authentication. Use original IGC logs exported by the pilot or obtained from consenting pilots, or request official XContest access.
4. Parse B-fixes from any authorized IGC: UTC timestamp, lat/lon, GPS altitude AMSL; keep original file, quality flags and source.
5. Later calculate thermal climbs, working altitude, corridor trajectories, wind estimates from circle drift (not simply initial GPS heading).
6. Link site/day labels to D−1/D−3 archived meteorology and evaluate chronologically, controlling for pilot skill and missing-day bias.

Raw metadata and public pilot identifiers were **not automatically committed to this public GitHub repository**; processed archives are distributed to the project owner separately.

Wind convention: direction wind comes FROM. Flight route: direction aircraft travels TO. All heights: AMSL.
