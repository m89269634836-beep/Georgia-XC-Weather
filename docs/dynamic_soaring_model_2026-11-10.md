# Ridge soaring / dynamic wind model — Georgia (10 November 2026)

## Purpose
Late autumn and winter priority: **ridge lift**, with thermals as a bonus. Do not rank flyability using CAPE or surface LCL alone. Strong wind is useful only when a correctly oriented, accessible, verified slope is on the windward side, not in a lee rotor.

## Verified technical progress
- Terrain: 10 site/area coordinates, centre + 8 radial directions at 400 m and 1,500 m, SRTM90m elevations obtained via OpenTopoData. **Area centres are not launch locations.** See `data/dynamic_sites_terrain_probe.json`.
- Wind-model availability tested at 42.099182,45.418038: both `dwd_icon_eu` and `icon_eu` returned 48 hours of valid point wind in Open-Meteo, and `ecmwf_ifs` also returned non-null values. See `data/dynamic_forecast_models_probe.json`.
- Current supplementary wind forecast: ICON-EU, ECMWF IFS and GFS, wind at 10 m and 80 m above model surface, gusts, clouds, precipitation; daily 11:00–16:00 summaries. See `data/dynamic_ridge_forecast.json`.
- Automatically refresh twice daily via `.github/workflows/soaring-ridge-wind.yml`.
- Editable 10-point registry in `data/dynamic_sites_registry.json`. Editing it triggers both terrain and wind forecasts.
- All 10 registered coordinates have either a provenance or a clearly marked area-centre status; no invented takeoff coordinates.

## What the local wind calculation *cannot* yet do
ICON-EU is ~7 km; ECMWF IFS is ~9 km. A 1–2 km gorge and individual ridges remain sub-grid. Point winds at 10/80 m can be wrong because the model's terrain differs from the real launch elevation and valley orientation. Meteorological direction indicates wind FROM.

## Candidate places
**User-defined, exact launch coordinates**: Lalisquri (N), Jidgeti (N), Ananuri (N), Tsivi (N), Udzilaurta (N-NE). Guaduri reference is a general point only; several launch faces exist.

**Externally documented**:
- Tbilisi Sea, S/SE/E sector reported by Syride, AIP UGA3: upper limit stated 3500 ft AMSL (~1067 m), authorization/NOTAM to verify. Registry coordinate is centre of the published airspace, not exact takeoff.
- Rustavi, coordinates from public Parakiters listing, published ridge-soaring potential but reported airport CTR restrictions; not a recommended flight site absent authorization.
- Sighnaghi, official year-round tandem area on SE-facing Gombori slope; reported launch elevation/where to launch differs across references and has NOT been mapped. Registry point is centre of AIP UGA2, not launch.
- Kazaniani, published paragliding AIP UGA1 area; no confirmed launch, aspect or landing. The AIP centre is for reconnaissance only.
- Gudauri: Kudebi winter options documented for W/SW/S/SE/E winds (not every site or face); individual launch coordinates and landings needed.

## Model for each verified ridge
1. Record exact takeoff, verified wind-facing aspect and acceptable angular sectors; ridge crest endpoints and usable length; landing / escape route; access/obstructions/airspace.
2. Use DEM (prefer 30 m for geometry) to estimate slope normal, steepness, height gain, lateral ridge continuity, upstream blockage, and immediate lee; 400 m point-samples alone do **not** establish a usable ridge.
3. Take 7–9 km winds, vertical shear, gusts, stability and mesoscale pressure gradient; for valleys also evaluate the gorge axis and nearby north/south model sample differences.
4. For a known face bearing `alpha`, estimate wind normal component `V_normal = V * cos(wind_from - alpha)`. Positive alone never guarantees safe lift.
5. For sub-grid downscaling, investigate WindNinja with a DEM and mesoscale initialization. The US Forest Service describes ~100 m grids for up to 50x50 km. Do not treat its quick mass-conservation output as a rotor map; for deep canyon lee eddies it has known limitations.
6. Calibrate using wind-sensor logs and real ridge-soaring IGC: separate dynamic ridge flight (low climb, repeated tracks near crest) from thermal circles; use positive *and* poor days, avoid pilot-skill bias.
7. Output potential (not flight clearance) with evidence, uncertainty, access and airspace risk.

## Registry: adding a site
Append a new object to `data/dynamic_sites_registry.json` with distinct `id`, `name`, `latitude`, `longitude`, `coordinate_type` (for example `user-verified launch`), `reported_facing` (for example `NW-W`), `exact_launch_confirmed`, optional `ridge_axis_deg`, `valley_axis_deg`, `usable_wind_sector_deg`, `landing_coordinate`, `field_wind_notes`, `airspace_or_safety_note`. Preserve unknowns as null rather than guessing. The scripts currently use coordinates/facing, while the extra fields are reserved for the next scoring iteration.

## Source pointers
- Official Georgian eAIP ENR 5.5: https://airnav.ge/eaip/2026-07-09-000000/html/eAIP/UG-ENR-5.5-en-GB.html
- Tbilisi Sea: https://www.syride.com/en/flying-sites/Tblisi_Sea
- Rustavi hazards: https://www.flyappi.org/flysite/6321/
- Gudauri Kudebi: https://georgia.travel/paragliding-in-gudauri-kudebi-mountain
- WindNinja: https://research.fs.usda.gov/firelab/products/dataandtools/windninja
- Open-Meteo DWD: https://open-meteo.com/en/docs/dwd-api
- DEM: https://www.opentopodata.org/api/

**Important:** 3500 ft at Tbilisi Sea is the published top of the designated paragliding area, not a general permission to fly there. Check latest AIP, NOTAM and local federation requirements for the exact route/date.
