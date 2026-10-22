import json
import unittest
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location('build', ROOT / 'scripts' / 'build.py')
build = module_from_spec(spec)
spec.loader.exec_module(build)
CFG = json.loads((ROOT / 'config' / 'sources.json').read_text(encoding='utf-8'))
CONFIG = {item['id']: item for item in CFG['sources']}
FIXTURES = Path(__file__).resolve().parent / 'fixtures'

class SanctionsBuildTests(unittest.TestCase):
    def test_eu_parses_only_designated_ru_table(self):
        source = {**CONFIG['EU'], 'min_records': 1}
        items, stats = build.process_source(source, (FIXTURES / 'eu.html').read_bytes())
        self.assertEqual({r['imo'] for r in items}, {'9179842', '9915090'})
        self.assertTrue(all(r['listed_date'] == '25.06.2024' for r in items))

    def test_uk_preamble_and_vessel_only(self):
        source = {**CONFIG['UK'], 'min_records': 1}
        items, stats = build.process_source(source, (FIXTURES / 'uk.csv').read_bytes())
        self.assertEqual(len(items), 2)
        self.assertEqual({r['reference'] for r in items}, {'UK-001', 'UK-003'})

    def test_ofac_remarks_and_type_filter(self):
        source = {**CONFIG['OFAC'], 'min_records': 1}
        items, stats = build.process_source(source, (FIXTURES / 'ofac.csv').read_bytes())
        self.assertEqual(len(items), 2)
        self.assertEqual({r['imo'] for r in items}, {'9179842', '9915090'})

    def test_check_digit_validation_diagnostic(self):
        self.assertTrue(build.checksum_valid('9179842'))
        self.assertFalse(build.checksum_valid('9179843'))
        self.assertEqual(build.find_imo('IMO: 9179842, IMO No. 9915090'), ['9179842','9915090'])

    def test_header_rename_failure_is_not_silent(self):
        source = {**CONFIG['UK'], 'min_records': 1}
        altered = (FIXTURES / 'uk.csv').read_text().replace('IMO number', 'Unexpected identifier')
        with self.assertRaises(build.ImportProblem):
            build.process_source(source, altered.encode('utf-8'))

    def test_sharp_drop_rejected(self):
        source = {**CONFIG['OFAC'], 'min_records': 1}
        with self.assertRaises(build.ImportProblem):
            build.process_source(source, (FIXTURES / 'ofac.csv').read_bytes(),
                                 previous={'records':[{}] * 20}, fraction=0.6)

    def test_combined_json_csv_and_status(self):
        snaps = {}
        for sid, filename in [('EU', 'eu.html'), ('OFAC', 'ofac.csv'), ('UK', 'uk.csv')]:
            cfg = {**CONFIG[sid], 'min_records': 1}
            items, stats = build.process_source(cfg, (FIXTURES / filename).read_bytes())
            snaps[sid] = {'source':sid, 'url':cfg['url'], 'fetched_at':'2026-10-22T09:00:00Z',
                          'sha256':'test', 'records':items, **stats}
        result = build.generate_public_files(snaps, '2026-10-22T09:00:00Z', 7)
        data = json.loads(result['vessels.json'])
        self.assertEqual(set(data['vessels']), {'9179842', '9915090'})
        self.assertEqual(len(data['vessels']['9179842']['matches']), 3)
        self.assertIn('imo,name,source,program,reference,listed_date', result['vessels.csv'])
        self.assertTrue(json.loads(result['status.json'])['ready'])

    def test_absent_imo_and_source_rejected(self):
        self.assertEqual(build.find_imo('Number 123456 or 12345678'), [])
        source = {**CONFIG['EU'], 'min_records': 10}
        with self.assertRaises(build.ImportProblem):
            build.process_source(source, (FIXTURES / 'eu.html').read_bytes())

if __name__ == '__main__':
    unittest.main()
