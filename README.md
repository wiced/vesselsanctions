# Insure Consult – vessel sanctions data publisher

A low-maintenance, public-source **IMO-based vessel list matcher**. GitHub Actions fetches EU/DMA, OFAC SDN and UK Sanctions List data once per day, normalizes and validates the records, and deploys public-only CSV/JSON to GitHub Pages. Insure Consult's vessel master data, declarations, credentials and private compliance evidence **must not** be stored in this repository.

**Status: initial integration starter.** The website initially says `NOT READY`. The first live import must pass tests and manual spot checks before it can be relied upon. Live feed connectivity and the Nicepage integration have not yet been verified.

## Components

```text
config/sources.json             Self-service URLs, column mappings, thresholds
scripts/build.py                Download, normalize, validate, publish
.github/workflows/sanctions.yml Daily + manually triggered update and Pages deploy
.github/workflows/test.yml      Unit tests on PRs / manually
site/index.html                 Public status page (not customer-facing IMO search)
site/data/vessels.json          Generated IMO -> source match records (after successful run)
site/data/vessels.csv           Generated rows for Excel Power Query
site/data/status.json           Generated data freshness / counts
PROJECT_PLAN.md                Project phases, owner and acceptance criteria
OPERATIONS.md                  How to maintain, verify and troubleshoot
examples/nicepage-imo.js       Safe integration example, not login/authentication
```

## First-time deployment

1. Create a **new public** repository named `insure-consult-vessel-sanctions` under an appropriate account (preferably owned by Insure Consult). Do **not** place customer data here. Set default branch to `main`.
2. Upload/commit the entire repository content, preserving `.github/workflows/` and `config/`.
3. Open repository **Settings → Pages → Build and deployment → Source: GitHub Actions**. GitHub requires this setting to enable custom Pages deployments.
4. Open **Actions → Update vessel sanctions and publish data → Run workflow**. The workflow tests, downloads all three official feeds, validates, commits last-good snapshots, and deploys Pages **only if all three succeed**.
5. Verify Actions run, `site/data/status.json`, `site/data/vessels.json` and `site/data/vessels.csv`. Check IMO `9179842` against the EU source and spot-check OFAC and UK source matches. If an adapter fails, see `OPERATIONS.md`.
6. Add Nicepage and Excel integrations **only after** data correctness and freshness are verified.

GitHub Pages publication URLs (once activated):

- `https://<OWNER>.github.io/insure-consult-vessel-sanctions/data/vessels.json`
- `https://<OWNER>.github.io/insure-consult-vessel-sanctions/data/vessels.csv`
- `https://<OWNER>.github.io/insure-consult-vessel-sanctions/data/status.json`

**Pages is public, even if Nicepage is password-protected.** No credentials, customer vessels or private declarations may be placed on Pages. The example `nicepage-imo.js` is not an authentication mechanism. Hosting security must remain at the protected Nicepage site.

## Read-only usage

- **Excel / Power Query**: Data → Get Data → From Web → CSV URL; cast `imo` to **text**, never an integer; do a merge on IMO. Prefer stable, refreshed local query data over cross-workbook formula links. Keep the existing master vessel register and premium formulas separate.
- **Nicepage (authenticated)**: Load JSON/status from Pages, validate IMO, display matches by source. Test Cross-Origin Resource Sharing (CORS) in the actual hosting environment. Do not label a nonmatch `cleared` or `allowed`.
- **Power Automate**: Future phase – check monthly cargo lists and save PDF with vessel IMO, list versions, results and check timestamp in a private SharePoint library. Do not disclose declarations publicly.

## Changing a source URL or column name

Open `config/sources.json` in GitHub; edit the affected source's HTTPS `url` or `columns` mapping. Create a PR and check tests, then merge. When changed on main, the import workflow runs automatically. A failed import **does not deploy** new data. Test with a known IMO after any change.

Source list choices: EU/DMA currently reads the Russia/Belarus designated-vessels table corresponding to Regulation 833/2014 Annex XLII (mirroring the original EU sheet). DMA additionally lists DPRK vessels on the same page; they are *not* silently added to the EU-RU parser. If business scope changes, extend and retest the configuration explicitly. OFAC checks **SDN** only, not every US non-SDN restriction; UK checks the UK Sanctions List. This is not a comprehensive legality assessment.

## Official references

- EU/DMA https://www.dma.dk/growth-and-framework-conditions/maritime-sanctions/general-information/eu-vessel-designations
- OFAC https://ofac.treasury.gov/sanctions-list-service
- OFAC SDN CSV https://www.treasury.gov/ofac/downloads/sdn.csv
- UK https://www.gov.uk/government/publications/the-uk-sanctions-list
- UK static CSV https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv
- UK fields https://www.gov.uk/guidance/format-guide-for-the-uk-sanctions-list

No claim is made that nonmatches are free of all sanctions. See project plan for constraints.
