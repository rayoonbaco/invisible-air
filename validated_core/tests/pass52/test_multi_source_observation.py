from pathlib import Path
import unittest
from app import app

ROOT = Path(__file__).resolve().parents[2]


class MultiSourceObservationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_source_coordinate_override_changes_field_source_and_fingerprint(self):
        first = self.client.get('/observatory-field.json?scenario=four-corners&material=fine-smoke-aerosol&live=0&source_lat=36.73&source_lon=-108.22')
        second = self.client.get('/observatory-field.json?scenario=four-corners&material=fine-smoke-aerosol&live=0&source_lat=36.61&source_lon=-108.04')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        a = first.get_json(); b = second.get_json()
        self.assertAlmostEqual(a['grid']['source']['latitude'], 36.73)
        self.assertAlmostEqual(a['grid']['source']['longitude'], -108.22)
        self.assertNotEqual(a['fingerprint'], b['fingerprint'])
        self.assertEqual(a['observatory']['source_mode'], 'independent_single_source_run')

    def test_invalid_source_coordinates_are_rejected(self):
        response = self.client.get('/observatory-field.json?source_lat=hello&source_lon=-108')
        self.assertEqual(response.status_code, 400)
        response = self.client.get('/observatory-field.json?source_lat=95&source_lon=-108')
        self.assertEqual(response.status_code, 400)

    def test_public_instrument_exposes_compact_source_controls_and_boundary(self):
        text = self.client.get('/observatory').get_data(as_text=True)
        self.assertIn('id="addSourceButton"', text)
        self.assertIn('id="undoSourceButton"', text)
        self.assertIn('Independent fields', text)
        self.assertIn('not measured smoke concentration or chemical interaction', text)

    def test_renderer_uses_independent_requests_and_no_randomness(self):
        js = (ROOT / 'static' / 'js' / 'governing_field_renderer.js').read_text(encoding='utf-8')
        self.assertIn("endpoint.searchParams.set('source_lat'", js)
        self.assertIn('Promise.all(sources.map(fetchSourceField))', js)
        self.assertIn("sourceMode: 'independent-fields-visually-combined'", js)
        self.assertNotIn('Math.random', js)


if __name__ == '__main__':
    unittest.main(verbosity=2)
