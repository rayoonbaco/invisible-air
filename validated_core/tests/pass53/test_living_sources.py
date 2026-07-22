from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = (ROOT / 'static/js/governing_field_renderer.js').read_text(encoding='utf-8')
CSS = (ROOT / 'static/css/observatory.css').read_text(encoding='utf-8')


def test_drag_recomputes_only_released_source():
    assert "commitSourceMove" in JS
    assert "await fetchSourceField(nextSource)" in JS
    assert "state.fields[index] = nextEntry" in JS
    assert "pointermove" in JS and "pointerup" in JS


def test_drag_does_not_fetch_continuously():
    pointer_move = JS.split("container.addEventListener('pointermove'", 1)[1].split("container.addEventListener('pointerleave'", 1)[0]
    assert "fetchSourceField" not in pointer_move
    assert "loadFields" not in pointer_move


def test_hover_whisper_and_crossfade_exist():
    assert "source-whisper" in CSS
    assert "Ground-level demonstration · independently modeled" in JS
    assert "transition = { index:index" in JS
    assert "duration:1100" in JS


def test_history_supports_move_add_and_reset():
    assert "state.history.push(snapshot)" in JS
    assert "restoreSnapshot(snapshot)" in JS
    assert "state.history = []" in JS
