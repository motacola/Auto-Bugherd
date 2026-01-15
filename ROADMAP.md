Roadmap

- Playwright integration (optional): isolate automation in a dedicated Chrome profile or separate browser instance to avoid extension conflicts.
- Add Playwright "optional mode" for JS-rendered checks + screenshots (isolated profile).
- Report upgrades: embed screenshots, include diff highlights, and add per-check timestamps.
- Reliability: retry/backoff + shared HTTP session for all network calls.
- Config validation: schema checks + clearer errors for malformed config.json.
