from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class CraftsmanshipPassTests(unittest.TestCase):
    def test_renderer_has_fine_deterministic_detail(self):
        text = (ROOT / 'static/js/governing_field_renderer.js').read_text()
        self.assertIn('detailImage', text)
        self.assertIn('supportGradient', text)
        self.assertNotIn('Math.random', text)

    def test_source_has_restrained_pulse(self):
        text = (ROOT / 'static/js/governing_field_renderer.js').read_text()
        self.assertIn('sourcePhase', text)
        self.assertIn('prefers-reduced-motion', text)

    def test_transport_basis_is_visible(self):
        html = (ROOT / 'templates/observatory.html').read_text()
        self.assertIn('transportBasis', html)
        self.assertIn('relative modeled atmospheric influence field', html.lower())

if __name__ == '__main__':
    unittest.main()
