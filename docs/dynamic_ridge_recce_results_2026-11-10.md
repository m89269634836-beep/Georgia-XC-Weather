# Dynamic soaring near Tbilisi — four new user points + six DEM candidates
Generated 2026-11-10, Georgia local time

## Status — actual executed calculations
1. Four user-supplied coordinates added to `data/dynamic_sites_registry.json`. Sagarejo/Kaspi DMS converted exactly to WGS84 decimals.
2. 400 m and 1,500 m radial terrain drops measured from SRTM90m for all four in `data/dynamic_sites_terrain_probe.json`.
3. 10m ESA WorldCover 2021 vegetation composition near each exact point, and OSM roads, in `data/dynamic_new_sites_access_vegetation.json`.
4. OSM core API checked road geometry for all ten points, including roads missed by unreliable Overpass queries: `data/dynamic_scout_osm_roads.json`.
5. **Real** WindNinja 4.0 Windows CLI executed successfully 11 neutral domain-average scenarios over 8x8 km Copernicus GLO-90 DEM, 125 m UTM input raster sampled from the original ~90 m source, WindNinja 200 m mass-conserving mesh, homogeneous grass vegetation. Results and four source/target outputs per scenario saved in `data/windninja_spatial_prototype/`. No rotor prediction or local safety validation.
6. DEM and ESA WorldCover scan of four Tbilisi vicinity areas returned six unverified reconnaissance ridge pixels; `data/dynamic_tbilisi_dem_scout.json`.
7. Forecast `data/dynamic_ridge_forecast.json` now covers twenty points (fourteen registered + six **unverified** DEM candidates), ICON-EU, ECMWF IFS, GFS, with winds at model 10 and 80m and gusts.

## Original 4 surveyed coordinates
| Point | WGS84 decimal | 90m DEM altitude | Downhill over 400 m | 2021 tree cover within 250m | Mapped nearest route |
|---|---|---:|---|---:|---|
| Медвежий | 42.527694, 45.054976 | 2807m | SW -249m, W -210m | 0.4% | mapped footway about 15m, not vehicle road |
| Сагареджо | 41.68368056, 45.28197222 | 941m | E -137m, NE -105m | 36.6% | mapped track ~15m, untagged surface |
| Каспи | 41.89015556, 44.54378889 | 825m | NE -109m, SE -102m, E -80m | 0.5% | OSM track tagged ground ~446m |
| Каспи 2 | 41.86036667, 44.47746111 | 741m | N -83m, NE -65m | 2.0% | OSM track tagged ground ~619m |

DEM altitude is a modelled surface elevation, not a flight altimeter. Tree-cover fractions use ESA 2021 WorldCover. Track distance is a ground straight-line geometric gap to road segments, not a road route, passage right or snow/mud assessment.

## WindNinja neutral-scenario comparison
All examples assume **constant 6 m/s input from a declared FROM direction at 80 m above vegetation**, and report output at 20 m above uniform model grass. This is **not** an operational weather forecast. Mass conservation can show horizontal terrain acceleration/deflection, not lee rotors.

| Point | Wind FROM | Mean near point / local max at 20 m (m/s) |
|---|---|---|
| Медвежий | SW 210° | 5.73 / 7.76 |
| Медвежий | W 270° | 6.13 / 8.55 |
| Сагареджо | NE 45° | 5.44 / 6.28 |
| Сагареджо | E 90° | 5.32 / 6.22 |
| Каспи | E 90° | 5.57 / 6.14 |
| Каспи | ESE 110° | 5.42 / 5.94 |
| Каспи 2 | E 90° | 5.08 / 5.21 |
| Каспи 2 | ESE 110° | 5.15 / 5.41 |

**Conclusion:** Kaspi is more favourable for exploring east-wind dynamic conditions than Kaspi 2 in this first test. Medvezhiy shows strong terrain speedups but has difficult 2807m high-altitude exposure. All require actual ridge shape, landing and takeoff inspection. WindNinja speed magnitude is nearly symmetric for opposite flow in mass-only runs — not evidence that each flow direction is equally good for lift.

## New Tbilisi reconnaissance pixels (NOT takeoffs)
| Region | Coordinate | Hypothetical windward face | 360m terrain drop | Open-class nearby (90m sampled) | Nearest OSM line |
|---|---|---|---:|---:|---|
| West of Mtskheta | 41.874566,44.657796 | NW | 88m | 94% | unclassified unpaved ~8m |
| Martkopi 1 | 41.789341,45.044892 | SW | 120m | 100% | unclassified gravel (grade2) ~300m |
| Martkopi 2 | 41.794996,45.079560 | SW | 105m | 82% | track ~34m |
| Martkopi 3 | 41.754460,45.086005 | NW | 83m | 92% | track ~112m |
| Kojori 1 | 41.662223,44.738416 | NE | 103m | 92% | track grade3 ~164m |
| Kojori 2 | 41.643626,44.760106 | SE | 79m | 86% | unpaved residential ~190m |

All four regions near Tbilisi must be checked against the current airspace chart and NOTAMs, especially CTRs. No statement of lawful flight access is made here. Live terrain/satellite checks needed for obstacles, power lines and real grass condition. OSM is not a field road survey; in winter these tracks may be impassable.

## Next calibration logic
- Add exact launch face sectors and ridge endpoints after reconnaissance.
- Include 10/80m ICON-EU and ECMWF winds plus full-profile wind and gusts. Estimate normal component against exposed face and report probability bands rather than a binary go/no-go.
- Add measured anemometer and actual ridge-dynamic IGC, including unsuccessful conditions, to calibrate local valley wind turns and the threshold for sustained dynamic lift.
- Later improve GLO-90 DEM to verifiably available GLO-30 or ALOS 30m for final candidate selection. Re-test mass-model WindNinja against observations, then consider WindNinja foam/momentum mode for complex lee separated-flow effects (not a substitute for flight operations assessments).
