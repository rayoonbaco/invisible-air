from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = (ROOT / 'static/js/governing_field_renderer.js').read_text(encoding='utf-8')
HTML = (ROOT / 'templates/observatory.html').read_text(encoding='utf-8')
CSS = (ROOT / 'static/css/observatory.css').read_text(encoding='utf-8')


def test_dual_explanation_contract():
    for marker in ('buildMoveExplanation', 'transportComponents', 'lastMoveExplanation'):
        assert marker in JS
    assert 'publishObservation(observation, explanation)' in JS


def test_explanation_surface_is_accessible_and_quiet():
    assert 'id="sourceExplanation"' in HTML
    assert 'aria-live="polite"' in HTML
    assert '.source-explanation' in CSS
    assert "content:'WHY THE MODEL CHANGED'" in CSS


def test_explanation_uses_model_relative_language():
    required = ('displayed fields', 'governing transport', 'modeled separation', 'atmospheric inputs')
    for phrase in required:
        assert phrase in JS
    forbidden = ('actual smoke went', 'health exposure', 'measured concentration increased')
    for phrase in forbidden:
        assert phrase not in JS


def test_no_freeform_ai_dependency():
    assert 'buildMoveExplanation' in JS
    assert 'openai' not in JS.lower()
    assert 'chatgpt' not in JS.lower()
