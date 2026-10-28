# XContest IGC automated retrieval — local pilot plan (2026-10-28)

## Verified facts
- Signed-in main XContest account can download a valid full IGC from flight page (user demonstrated for Lalisquri 2026-04-03).
- An alternate account could not load the same track. Access appears to depend on authorization, but it is NOT yet confirmed which rule applies.
- Our anonymous public probe returned HTTP 200 for a flight detail HTML page and HTTP 404 for an old routekml.php link. This does not confirm a public IGC API.
- The original 2026-04-03 IGC had 25,335 valid 1 Hz GPS B-records, so full-track analysis is feasible once we have authorized logs.

## Download options
1. **Own flights**: use the XContest native `My flights` → `ALL IGC` export; it should produce a ZIP, no scraping needed.
2. **Other pilots with downloadable files and appropriate permission**: test a *local* visible-browser script in a persistent Chromium session. Sign in interactively; no credentials or session cookies to GitHub.
3. If no exposed IGC download control, use the prototype's one-flight `--manual` mode to capture a legitimate user-initiated browser download. Do not scrape transient auth tokens, bypass CAPTCHA, or force download against HTTP 401/403/429.
4. For broad collection, obtain appropriate permission / documented bulk access from XContest or pilot-provided original logs.

## Local Windows prototype
Provided separately to project owner as `XContest_IGC_AutoDownload_Windows_Prototype.zip`.
Files:
- `xcontest_igc_browser.py`: Playwright Chromium persistent profile, download click, IGC structural check, deduplication, CSV journal, bounded batch.
- `make_flight_urls.py`: create 5+5 balanced low/high-distance links from `georgia_flights_merged.json`.
- `flight_urls_10.txt`: five Lalisquri and five Jidgeti candidate detail pages.
- `README_RU.md`: Windows commands.

Prototype has been tested locally with `python -m py_compile` and structurally validated against four real uploaded IGCs. Its download-selector logic **has not been tested against an authenticated live XContest browser** yet.

### Acceptance test
1. `py -m pip install playwright` and `py -m playwright install chromium`.
2. `py xcontest_igc_browser.py --login`: local interactive login.
3. `py xcontest_igc_browser.py --urls flight_urls.txt --max 1`. If unavailable, `--manual`.
4. Verify real IGC date/fix count saved to local log; then attempt up to five URLs with `--pause 20`.
5. If failure, inspect click selector / download event with user's visible browser UI, not undocumented API bypass.

## Privacy
- Browser profile/cookies and downloaded third-party IGC remain on user machine; never commit to public repo.
- Keep no passwords, private keys or signed URLs in public logs.
- Track original IGC provenance and G-record (not cryptographically checked by the prototype).
