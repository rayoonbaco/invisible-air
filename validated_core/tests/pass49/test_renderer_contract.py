from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class Pass49RendererContractTests(unittest.TestCase):
    def test_observatory_loads_governing_renderer_not_legacy_plume(self):
        html = (ROOT / "templates" / "observatory.html").read_text(encoding="utf-8")
        self.assertIn("governing_field_renderer.js", html)
        self.assertNotIn("filename='js/plume_canvas.js'", html)

    def test_renderer_consumes_both_governing_grids(self):
        js = (ROOT / "static" / "js" / "governing_field_renderer.js").read_text(encoding="utf-8")
        self.assertIn("grid.relative_influence", js)
        self.assertIn("grid.model_support", js)
        self.assertIn("/observatory-field.json", js)

    def test_renderer_is_deterministic_and_has_no_randomness(self):
        js = (ROOT / "static" / "js" / "governing_field_renderer.js").read_text(encoding="utf-8")
        self.assertNotIn("Math.random", js)
        self.assertIn("function hash01", js)

    def test_legacy_breath_is_hidden(self):
        css = (ROOT / "static" / "css" / "observatory.css").read_text(encoding="utf-8")
        self.assertIn(".observatory-breath { display: none !important; }", css)

    def test_active_scene_endpoint_exists(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('@app.get("/observatory-field.json")', app)
        self.assertIn("_observatory_governing_input", app)


if __name__ == "__main__":
    unittest.main(verbosity=2)
