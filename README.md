# Insure Consult – vessel sanctions data publisher

A low-maintenance, public-source **IMO-based vessel list matcher**. GitHub Actions fetches EU/DMA, OFAC SDN and UK Sanctions List data once per day, normalizes and validates the records, and deploys public-only CSV/JSON to GitHub Pages. Insure Consult's vessel master data, declarations, credentials and private compliance evidence **must not** be stored in this repository.

**Status (2026-10-22):** The initial live import, offline tests and GitHub Pages deployment succeeded. Spot checks against official EU/OFAC/UK announcements matched sample IMO identifiers. Excel and the protected Nicepage customer page are **not yet deployed or verified**; see [INTEGRATION.md](INTEGRATION.md).

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
examples/nicepage-embed.html    Nicepage form replacing the former hard-coded IMO list
examples/nicepage-imo.js       API-only sample (not authentication)
examples/Sanktsioonid.pq       Excel public JSON -> IMO/source flags with freshness validation
examples/SanktsiooniVasted.pq   Alternative long-form match rows with source details
examples/LaevadeKontroll.pq     Merge onto existing private Vessel_List table
INTEGRATION.md                Deployment and acceptance checklist
```

## First-time deployment

1. Repository currently: [wiced/vesselsanctions](https://github.com/wiced/vesselsanctions), branch `main`, public. Plan transfer of ownership/administration to the Insure Consult team before handover.
2. Upload/commit the entire repository content, preserving `.github/workflows/` and `config/`.
3. Open repository **Settings → Pages → Build and deployment → Source: GitHub Actions**. GitHub requires this setting to enable custom Pages deployments.
4. Open **Actions → Update vessel sanctions and publish data → Run workflow**. The workflow tests, downloads all three official feeds, validates, commits last-good snapshots, and deploys Pages **only if all three succeed**.
5. The first successful run published `site/data/status.json`, `site/data/vessels.json` and `site/data/vessels.csv`. Periodically validate IMO examples against the official sources; see `OPERATIONS.md`.
6. Prepare Nicepage and Excel using [INTEGRATION.md](INTEGRATION.md); integration examples are committed but have not yet been applied to the client's private site or workbook.

GitHub Pages publication URLs (once activated):

- `https://wiced.github.io/vesselsanctions/data/vessels.json`
- `https://wiced.github.io/vesselsanctions/data/vessels.csv`
- `https://wiced.github.io/vesselsanctions/data/status.json`

**Pages is public, even if Nicepage is password-protected.** No credentials, customer vessels or private declarations may be placed on Pages. The example `nicepage-imo.js` is not an authentication mechanism. Hosting security must remain at the protected Nicepage site.

## Read-only usage

- **Excel / Power Query**: The verified user's actual Excel input table is `Vessel_List` and IMO column is `Vessel IMO No`. Use `examples/Sanktsioonid.pq` and `examples/LaevadeKontroll.pq` to create a separate refreshed results sheet. Keep private master rows and any premium formulas separate. Read `INTEGRATION.md`.
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
