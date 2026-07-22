from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_journal_markup_present():
    html = (ROOT / 'templates' / 'observatory.html').read_text(encoding='utf-8')
    assert 'id="experimentJournal"' in html
    assert 'id="journalToggleButton"' in html
    assert 'id="exportJournalButton"' in html


def test_journal_renderer_contract_present():
    js = (ROOT / 'static' / 'js' / 'governing_field_renderer.js').read_text(encoding='utf-8')
    for token in ['recordJournal(', 'bindJournalControls(map)', 'Reopen experiment', 'invisible-air-experiment-journal-v1']:
        assert token in js


def test_journal_styles_present():
    css = (ROOT / 'static' / 'css' / 'observatory.css').read_text(encoding='utf-8')
    assert 'PASS 60 — THE EXPERIMENT JOURNAL' in css
    assert '.experiment-journal' in css
