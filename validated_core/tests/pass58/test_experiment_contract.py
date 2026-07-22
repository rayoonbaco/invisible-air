from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_template_exposes_parent_and_active_context():
    text=(ROOT/'templates'/'observatory.html').read_text(encoding='utf-8')
    assert 'Parent demonstration' in text
    assert 'Active experiment' in text
    assert 'stateIntegrityBadge' in text

def test_live_state_marks_synchronization_and_source_kind():
    text=(ROOT/'static'/'js'/'live_atmosphere_status.js').read_text(encoding='utf-8')
    assert "badge.textContent = synchronized ? 'Synchronized' : 'Fallback inputs'" in text
    assert "activeSource.kind === 'visitor'" in text

def test_renderer_publishes_source_kind():
    text=(ROOT/'static'/'js'/'governing_field_renderer.js').read_text(encoding='utf-8')
    assert "kind: (sourceAtIndex(index) || {}).kind || 'curated'" in text
