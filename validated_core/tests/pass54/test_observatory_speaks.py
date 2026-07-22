from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = (ROOT / 'static/js/governing_field_renderer.js').read_text(encoding='utf-8')
HTML = (ROOT / 'templates/observatory.html').read_text(encoding='utf-8')
CSS = (ROOT / 'static/css/observatory.css').read_text(encoding='utf-8')


def test_deterministic_move_observation_contract():
    for marker in ('buildMoveObservation', 'strongestOverlap', 'rms_crosswind_spread_km', 'active_area_km2_at_0_10'):
        assert marker in JS
    assert ('setTimeout(function () { publishObservation(observation); }, 760)' in JS or
            'setTimeout(function () { publishObservation(observation, explanation); }, 760)' in JS)


def test_accessible_single_sentence_surface():
    assert 'id="sourceObservation"' in HTML
    assert 'aria-live="polite"' in HTML
    assert '.source-observation' in CSS
    assert "content:'MODEL OBSERVATION'" in CSS


def test_claim_language_remains_model_relative():
    assert 'displayed overlap' in JS
    assert 'modeled field' in JS
    assert 'measured smoke concentration or chemical interaction' in HTML
