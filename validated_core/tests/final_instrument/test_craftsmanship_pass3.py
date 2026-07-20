from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class CraftsmanshipPass3Tests(unittest.TestCase):
    def test_final_freeze_css_exists(self):
        css = (ROOT / 'static/css/observatory.css').read_text(encoding='utf-8')
        self.assertIn('Craftsmanship Pass 3', css)
        self.assertIn('.model-status.is-ready{opacity:0', css)

    def test_source_motion_is_restrained(self):
        js = (ROOT / 'static/js/governing_field_renderer.js').read_text(encoding='utf-8')
        self.assertIn('state.sourcePhase += 0.018;', js)
        self.assertNotIn('Math.random()', js)

    def test_primary_visual_contract_remains(self):
        html = (ROOT / 'templates/observatory.html').read_text(encoding='utf-8')
        self.assertIn('Relative modeled influence', html)
        self.assertIn('Model support', html)
        self.assertIn('Model &amp; scientific basis', html)

if __name__ == '__main__':
    unittest.main()
