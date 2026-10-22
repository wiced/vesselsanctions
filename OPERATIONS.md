# Operations and maintenance (Insure Consult)

## Manual data update

GitHub → repository → Actions → **Update vessel sanctions and publish data** → **Run workflow**. The default schedule is every day 05:17 UTC. GitHub schedules are best-effort: runs may be delayed or dropped; do not assume the schedule itself proves freshness.

Open the Pages status page and verify `ready`, `generated_at`, three source timestamps and record counts. A result may only be treated as complete when **all three** feeds have passed and the timestamp is within `stale_after_days` (default 7 days). For high-stakes use, verify directly with the original official source.

## Repair changed CSV columns or URLs

1. Inspect the official new CSV header / official landing page.
2. In GitHub, edit `config/sources.json` for the source. `columns` accepts aliases, e.g., `"imo": ["IMO number", "IMO no.", "Ship IMO"]`. For OFAC's historical unheaded CSV, edit `positions` if the order changes; its IMO is extracted from `remarks` using the configured regex.
3. Use a PR, review the change and tests; merge to main and manually trigger the workflow if desired.
4. Inspect Actions logs and verify a known sanctioned IMO from **each** source. Do not reduce `min_records` just to force a green build without validating the results.

## On failures

- `Required column`: the upstream CSV header changed – update the relevant aliases.
- `Expected precisely one EU table`: DMA page HTML or heading changed – inspect the official source table and modify parser/config, or request developer support.
- `Sharp record count reduction`: potential mass delisting **or parser breakage** – verify source before adjusting threshold.
- HTTP timeout/403/429: the official site may block or rate-limit CI; manual inspection and/or change of officially published file endpoint required.
- Pages deploy failure: check Settings → Pages source is `GitHub Actions`, and environment permissions allow `github-pages`.
- Workflow success but file not updated: check `generated_at` and GitHub Actions logs; GitHub Pages CDN propagation may take time.

**Failure behavior:** the publisher downloads and validates all three feeds before writing any output. If one fails, it exits non-zero and leaves the last published Pages deployment intact. Do **not** interpret the absence of a match from stale data as a completed current screening. GitHub Actions failure notifications should be enabled for the client's maintenance contact.

## Security

Published JSON/CSV and status page are **public to the internet**. Never commit cargo declarations, customer vessels, private PDFs, usernames, passwords, API secrets or personal data. The code must not be embedded with a shared authentication secret in Nicepage JavaScript. Require authentication on the existing Nicepage site; the public dataset is separate.

## Handover and verification

Before production: manually compare a minimum of five known IMO numbers (EU/OFAC/UK positive cases and nonmatches), verify the UK and OFAC header parsers against **live** data, test failure simulation, test Windows Excel Desktop refresh and actual Nicepage CORS, document the responsible person, set GitHub failure notifications, and confirm what happens if this service is superseded by the partner solution.
