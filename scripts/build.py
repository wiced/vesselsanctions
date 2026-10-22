#!/usr/bin/env python3
"""Normalize public vessel sanctions data; publish ONLY if every source validates.

No commercial vessel database, client declarations or login credentials are stored here.
The schema and source field mappings are declared in config/sources.json.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / 'config' / 'sources.json'
SNAPSHOT_DIR = ROOT / 'data' / 'snapshots'
PUBLIC_DIR = ROOT / 'site' / 'data'
IMO_PATTERN = re.compile(r'(?<!\d)(\d{7})(?!\d)')


class ImportProblem(RuntimeError):
    """A feed could not be trusted; prior publication must remain unchanged."""


def clean(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def canon(value):
    return re.sub(r'[^a-z0-9]+', '', clean(value).casefold())


def find_imo(text, regex=None):
    pattern = re.compile(regex) if regex else IMO_PATTERN
    value = clean(text)
    candidates = []
    for found in pattern.finditer(value):
        val = found.group(1)
        if len(val) == 7 and val.isascii() and val.isdigit():
            candidates.append(val)
    return list(dict.fromkeys(candidates))


def map_headers(fields, columns, required=('imo', 'name')):
    by_normalized = {canon(field): ix for ix, field in enumerate(fields)}
    result = {}
    for key, aliases in columns.items():
        if isinstance(aliases, str):
            aliases = [aliases]
        ix = next((by_normalized[canon(a)] for a in aliases if canon(a) in by_normalized), None)
        if ix is None and key in required:
            raise ImportProblem(f'Required column {key!r} not found in headers: {fields!r}')
        result[key] = ix
    return result


def at(row, ix):
    return clean(row[ix]) if ix is not None and ix < len(row) else ''


def make_record(imo, name, source_id, program='', reference='', listed_date=''):
    return {
        'imo': imo, 'name': clean(name), 'source': source_id,
        'program': clean(program), 'reference': clean(reference),
        'listed_date': clean(listed_date)
    }


def decode_content(content):
    for encoding in ('utf-8-sig', 'utf-16', 'cp1252'):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise ImportProblem('Unable to decode source text')


def parse_csv_with_headers(content, cfg):
    rows = csv.reader(io.StringIO(decode_content(content)), delimiter=cfg.get('delimiter', ','))
    columns = cfg['columns']
    required = ('imo', 'name', 'type')
    indexes = None
    seen_rows = 0
    records = []
    skipped = 0
    for row in rows:
        seen_rows += 1
        if indexes is None:
            try:
                indexes = map_headers(row, columns, required=required)
                continue
            except ImportProblem:
                if seen_rows >= cfg.get('max_header_lines', 30):
                    raise ImportProblem('CSV header row missing or incompatible; check config/sources.json')
                continue
        if not any(clean(c) for c in row):
            continue
        entity_type = at(row, indexes.get('type')).casefold()
        if entity_type not in [v.casefold() for v in cfg.get('vessel_type_values', [])]:
            continue
        imos = find_imo(at(row, indexes['imo']))
        if not imos:
            skipped += 1
            continue
        for imo in imos:
            records.append(make_record(
                imo, at(row, indexes['name']), cfg['id'],
                at(row, indexes.get('program')) or cfg.get('program_default', ''),
                at(row, indexes.get('reference')), at(row, indexes.get('listed_date'))
            ))
    if indexes is None:
        raise ImportProblem('No CSV header could be found')
    return records, skipped


def parse_csv_no_headers(content, cfg):
    rows = csv.reader(io.StringIO(decode_content(content)), delimiter=cfg.get('delimiter', ','))
    idx = cfg['positions']
    records = []
    skipped = 0
    vessel_types = [v.casefold() for v in cfg['vessel_type_values']]
    for row in rows:
        if at(row, idx['type']).casefold() not in vessel_types:
            continue
        imos = find_imo(at(row, idx['remarks']), cfg['imo_regex'])
        if not imos:
            skipped += 1
            continue
        for imo in imos:
            records.append(make_record(
                imo, at(row, idx['name']), cfg['id'],
                at(row, idx['program']), at(row, idx['reference'])
            ))
    return records, skipped


def parse_html_table(content, cfg):
    soup = BeautifulSoup(decode_content(content), 'html.parser')
    candidates = []
    for table in soup.select('table'):
        tr = table.select('tr')
        if len(tr) < 2:
            continue
        header = [clean(v.get_text(' ', strip=True)) for v in tr[0].find_all(['th', 'td'], recursive=False)]
        if not header:
            continue
        required_headings = cfg.get('table_required_headers', [])
        if not all(canon(r) in [canon(h) for h in header] for r in required_headings):
            continue
        index = map_headers(header, cfg['columns'], required=('imo', 'name'))
        candidates.append((tr, index))
    if len(candidates) != 1:
        raise ImportProblem(f'Expected precisely one EU table matching headers; found {len(candidates)}')
    rows, ix = candidates[0]
    records = []
    skipped = 0
    for tr in rows[1:]:
        row = [clean(v.get_text(' ', strip=True)) for v in tr.find_all(['th', 'td'], recursive=False)]
        if not row:
            continue
        imos = find_imo(at(row, ix['imo']))
        if not imos:
            skipped += 1
            continue
        for imo in imos:
            records.append(make_record(
                imo, at(row, ix['name']), cfg['id'], cfg.get('program_default', ''),
                '', at(row, ix.get('listed_date'))
            ))
    return records, skipped


PARSERS = {
    'csv_with_headers': parse_csv_with_headers,
    'csv_no_headers': parse_csv_no_headers,
    'html_table': parse_html_table
}


def checksum_valid(imo):
    weights = (7, 6, 5, 4, 3, 2)
    return len(imo) == 7 and sum(int(a) * b for a, b in zip(imo[:6], weights)) % 10 == int(imo[6])


def process_source(cfg, content, previous=None, fraction=0.6):
    if cfg['format'] not in PARSERS:
        raise ImportProblem(f"Unknown parser: {cfg['format']}")
    records, skipped = PARSERS[cfg['format']](content, cfg)
    if any(not record['name'] for record in records):
        raise ImportProblem(f"Source {cfg['id']}: a record has no vessel name")
    # Preserve separate listing records, but remove identical duplicates.
    deduped = {(v['imo'], v['name'], v['program'], v['reference'], v['listed_date']): v for v in records}
    records = sorted(deduped.values(), key=lambda v: (v['imo'], v['source'], v['reference'], v['name']))
    if len(records) < int(cfg['min_records']):
        raise ImportProblem(f"Source {cfg['id']}: only {len(records)} vessel records (minimum {cfg['min_records']})")
    if previous and len(records) < len(previous.get('records', [])) * fraction:
        raise ImportProblem(f"Source {cfg['id']}: sharp record count reduction; manual review required")
    return records, {'record_count': len(records), 'skipped_without_imo': skipped,
                     'imo_checksum_warnings': sum(not checksum_valid(r['imo']) for r in records)}


def download(url, timeout):
    if not url.startswith('https://'):
        raise ImportProblem('Only HTTPS source URLs are allowed')
    resp = requests.get(url, timeout=timeout, headers={
        'User-Agent': 'InsureConsultVesselData/1.0 (+public-sanctions-data; automated retrieval)',
        'Accept': 'text/csv,text/html,application/octet-stream,*/*'
    })
    resp.raise_for_status()
    if len(resp.content) < 100:
        raise ImportProblem(f'Content suspiciously short: {url}')
    if len(resp.content) > 80_000_000:
        raise ImportProblem('Content exceeds configured safety limit (80 MB)')
    return resp.content


def read_previous(source_id):
    path = SNAPSHOT_DIR / (source_id + '.json')
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else None


def combine(snapshots, stale_after_days):
    by_imo = defaultdict(lambda: {'imo': '', 'name': '', 'matches': []})
    sources = {}
    for source_id in ('EU', 'OFAC', 'UK'):
        value = snapshots[source_id]
        sources[source_id] = {key: value[key] for key in ('url', 'fetched_at', 'record_count', 'sha256', 'skipped_without_imo', 'imo_checksum_warnings')}
        for rec in value['records']:
            ship = by_imo[rec['imo']]
            ship['imo'] = rec['imo']
            if not ship['name']:
                ship['name'] = rec['name']
            ship['matches'].append({key: rec[key] for key in ('source', 'name', 'program', 'reference', 'listed_date')})
    result = dict(sorted(by_imo.items()))
    return result, sources


def csv_safe(value):
    """Prevent spreadsheet formulas in untrusted external text fields."""
    value = str(value or '')
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@')) else value


def generate_public_files(snapshots, timestamp, stale_after_days):
    vessels, sources = combine(snapshots, stale_after_days)
    result = {
        'schema_version': 1,
        'generated_at': timestamp,
        'stale_after_days': stale_after_days,
        'sources': sources,
        'vessels': vessels
    }
    csv_buffer = io.StringIO(newline='')
    writer = csv.DictWriter(csv_buffer, fieldnames=('imo','name','source','program','reference','listed_date'), lineterminator='\n')
    writer.writeheader()
    for imo, vessel in vessels.items():
        for match in vessel['matches']:
            writer.writerow({'imo': imo, 'name': csv_safe(match['name']), 'source': match['source'],
                             'program': csv_safe(match['program']), 'reference': csv_safe(match['reference']),
                             'listed_date': csv_safe(match['listed_date'])})
    status = {'ready': True, 'schema_version': 1, 'generated_at': timestamp,
              'stale_after_days': stale_after_days, 'total_imo_count': len(vessels), 'sources': sources}
    return {
        'vessels.json': json.dumps(result, ensure_ascii=False, indent=2) + '\n',
        'vessels.csv': csv_buffer.getvalue(),
        'status.json': json.dumps(status, ensure_ascii=False, indent=2) + '\n'
    }


def write_atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False, newline='') as f:
        f.write(content)
        temp = f.name
    os.replace(temp, path)


def run():
    cfg = json.loads(SOURCES_PATH.read_text(encoding='utf-8'))
    settings = cfg['settings']
    source_ids = [x['id'] for x in cfg['sources']]
    if set(source_ids) != {'EU', 'OFAC', 'UK'} or len(source_ids) != 3:
        raise ImportProblem('Expected EU, OFAC and UK exactly once each')
    timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    snapshots = {}
    for source in cfg['sources']:
        sid = source['id']
        print(f'Downloading {sid}: {source["url"]}', flush=True)
        data = download(source['url'], settings['http_timeout_seconds'])
        old = read_previous(sid)
        records, stats = process_source(
            source, data, old, settings['minimum_source_fraction_of_previous']
        )
        snapshots[sid] = {
            'source': sid, 'url': source['url'], 'fetched_at': timestamp,
            'sha256': hashlib.sha256(data).hexdigest(), 'records': records, **stats
        }
        print(f'{sid}: {len(records)} records validated ({stats["skipped_without_imo"]} skipped without IMO)', flush=True)
    # CRITICAL: no files are altered until all three sources are validated.
    output = generate_public_files(snapshots, timestamp, settings['stale_after_days'])
    for sid, payload in snapshots.items():
        write_atomic(SNAPSHOT_DIR / (sid + '.json'), json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    for name, value in output.items():
        write_atomic(PUBLIC_DIR / name, value)
    print(f'Published prepared dataset, {len(json.loads(output["vessels.json"])["vessels"])} unique IMO numbers')


if __name__ == '__main__':
    try:
        run()
    except (ImportProblem, requests.RequestException, KeyError, ValueError) as error:
        print(f'IMPORT FAILED – previous published version retained: {error}', file=sys.stderr)
        sys.exit(1)
