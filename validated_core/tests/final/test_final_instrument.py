import unittest
from app import app

class FinalInstrumentTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_observatory_route_renders(self):
        response = self.client.get('/observatory')
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn('See where the air may carry it.', text)
        self.assertIn('Model &amp; scientific basis', text)
        self.assertIn('Brightness', text)
        self.assertIn('Texture', text)

    def test_primary_route_has_no_campus_workflow(self):
        text = self.client.get('/observatory').get_data(as_text=True)
        self.assertNotIn('Open Gatehouse', text)
        self.assertNotIn('Enter judgment slowly', text)
        self.assertNotIn('Replay observation', text)
        self.assertNotIn('plume_canvas.js', text)

    def test_field_contract_is_live(self):
        response = self.client.get('/observatory-field.json?terrain=on')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn('grid', payload)
        self.assertIn('relative_influence', payload['grid'])
        self.assertIn('model_support', payload['grid'])
        self.assertTrue(payload.get('fingerprint'))

    def test_terrain_comparison_changes_fingerprint(self):
        on = self.client.get('/observatory-field.json?terrain=on&terrain_profile=cross_ridge').get_json()
        off = self.client.get('/observatory-field.json?terrain=off&terrain_profile=cross_ridge').get_json()
        self.assertNotEqual(on['fingerprint'], off['fingerprint'])

if __name__ == '__main__':
    unittest.main()
