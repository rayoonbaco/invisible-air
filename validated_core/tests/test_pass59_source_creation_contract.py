from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_template_exposes_release_assumption():
    text=(ROOT/'templates/observatory.html').read_text(encoding='utf-8')
    assert 'activeReleaseAssumption' in text
    assert 'Release assumption' in text

def test_renderer_declares_assumed_not_measured_release():
    text=(ROOT/'static/js/governing_field_renderer.js').read_text(encoding='utf-8')
    assert 'explicit normalized release assumption' in text
    assert 'did not infer a measured emission rate' in text
    assert 'retrieving local atmosphere' in text

def test_active_source_receives_release_contract():
    text=(ROOT/'static/js/live_atmosphere_status.js').read_text(encoding='utf-8')
    assert 'releaseAssumption' in text
    assert 'continuous relative release' in text
