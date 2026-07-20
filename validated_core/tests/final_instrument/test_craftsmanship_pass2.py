from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
RENDERER = ROOT / 'static/js/governing_field_renderer.js'


class CraftsmanshipPass2Tests(unittest.TestCase):
    def test_renderer_adds_model_bounded_filaments(self):
        text = RENDERER.read_text()
        self.assertIn('branchImage', text)
        self.assertIn('branchSignal', text)
        self.assertIn('governing-model footprint', text)
        self.assertNotIn('Math.random', text)

    def test_terrain_contouring_uses_existing_grids(self):
        text = RENDERER.read_text()
        self.assertIn('supportGradient', text)
        self.assertIn('terrainCool', text)
        self.assertIn('relative_influence', text)
        self.assertIn('model_support', text)

    def test_source_halo_is_restrained(self):
        text = RENDERER.read_text()
        self.assertIn('const haloRadius = 27 + pulse * 3.5', text)
        self.assertIn('prefers-reduced-motion', text)


if __name__ == '__main__':
    unittest.main()
