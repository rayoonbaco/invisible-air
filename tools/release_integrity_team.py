from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "validated_core"
REPORT_DIR = ROOT / "release_integrity" / "latest"

@dataclass
class Check:
    team: str
    name: str
    status: str
    seconds: float
    detail: str
    blocking: bool = True

CHECKS: list[Check] = []


def record(team: str, name: str, status: str, started: float, detail: str, blocking: bool = True) -> None:
    CHECKS.append(Check(team, name, status, round(time.perf_counter() - started, 4), detail.strip(), blocking))


def run_check(team: str, name: str, fn: Callable[[], str], blocking: bool = True) -> None:
    started = time.perf_counter()
    try:
        detail = fn() or "Passed"
        record(team, name, "PASS", started, detail, blocking)
    except Exception as exc:
        record(team, name, "FAIL", started, f"{exc}\n{traceback.format_exc(limit=2)}", blocking)


def command(cmd: list[str], cwd: Path = ROOT, timeout: int = 180) -> str:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    if proc.returncode != 0:
        raise RuntimeError(f"Exit {proc.returncode}: {' '.join(cmd)}\n{output[-6000:]}")
    return output[-6000:] or "Command completed successfully"


def discover_python() -> str:
    candidates = []
    if os.name == "nt":
        candidates.append(CORE / ".venv" / "Scripts" / "python.exe")
    else:
        candidates.append(CORE / ".venv" / "bin" / "python")
    candidates.append(Path(sys.executable))
    for path in candidates:
        if path.exists():
            return str(path)
    return sys.executable


def check_required_files() -> str:
    required = [
        CORE / "app.py",
        CORE / "templates" / "observatory.html",
        CORE / "templates" / "base.html",
        CORE / "static" / "css" / "styles.css",
        CORE / "static" / "js" / "governing_field_renderer.js",
        CORE / "engine" / "governing_model.py",
        CORE / "engine" / "scenario_registry.py",
        CORE / "engine" / "material_profiles.py",
        CORE / "engine" / "live_atmosphere.py",
        CORE / "engine" / "site_registry.py",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise AssertionError("Missing required files: " + ", ".join(missing))
    return f"{len(required)} critical files present"


def check_python_syntax() -> str:
    py = discover_python()
    files = [p for p in CORE.rglob("*.py") if ".venv" not in p.parts and "__pycache__" not in p.parts]
    return command([py, "-m", "compileall", "-q", str(CORE)], timeout=240) + f"; {len(files)} Python files scanned"


def _lightweight_js_integrity(file: Path) -> None:
    """Dependency-free JavaScript release sanity check.

    This deliberately avoids pretending to be a JavaScript parser. Modern JS can
    contain regex literals and nested template expressions that make naive bracket
    counting produce false failures. When Node.js is unavailable, we instead check
    for corruption markers and rely on the live HTTP/browser smoke gate for runtime
    coverage.
    """
    text = file.read_text(encoding="utf-8", errors="strict")
    if not text.strip():
        raise AssertionError(f"Empty JavaScript file: {file.name}")
    forbidden = ["<<<<<<<", "=======", ">>>>>>>", "\x00"]
    hits = [marker for marker in forbidden if marker in text]
    if hits:
        raise AssertionError(f"JavaScript corruption marker(s) in {file.name}: {hits}")
    # Required renderer anchors catch accidental truncation of the primary script.
    if file.name == "governing_field_renderer.js":
        anchors = ["observatory-field.json", "sourceObservation", "sourceExplanation"]
        missing = [anchor for anchor in anchors if anchor not in text]
        if missing:
            raise AssertionError(f"Renderer appears incomplete; missing: {', '.join(missing)}")


def check_js_syntax() -> str:
    files = sorted((CORE / "static" / "js").glob("*.js"))
    node = shutil.which("node")
    if node:
        for file in files:
            command([node, "--check", str(file)], timeout=30)
        return f"{len(files)} JavaScript files passed Node.js syntax validation"
    for file in files:
        _lightweight_js_integrity(file)
    return (f"{len(files)} JavaScript files passed dependency-free structural integrity; "
            "Node.js was not installed, so full ECMAScript parsing was not performed")


def check_secrets() -> str:
    patterns = [
        re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"ghp_[A-Za-z0-9]{30,}"),
        re.compile(r"sk-[A-Za-z0-9]{20,}"),
    ]
    ignore_parts = {".venv", ".git", "__pycache__", "release_integrity"}
    hits: list[str] = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or any(part in ignore_parts for part in p.parts):
            continue
        if p.suffix.lower() not in {".py", ".js", ".html", ".json", ".md", ".txt", ".env", ".yaml", ".yml"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in patterns:
            if pattern.search(text):
                hits.append(str(p.relative_to(ROOT)))
                break
    if hits:
        raise AssertionError("Possible secrets detected: " + ", ".join(hits[:20]))
    forbidden = [p for p in ROOT.rglob(".env") if ".venv" not in p.parts]
    if forbidden:
        raise AssertionError(".env file(s) present: " + ", ".join(str(p.relative_to(ROOT)) for p in forbidden))
    return "No obvious embedded credentials or repository .env files detected"


def check_repository_hygiene() -> str:
    removed = 0
    for directory in list(ROOT.rglob("__pycache__")) + list(ROOT.rglob(".pytest_cache")):
        if ".venv" in directory.parts or "release_integrity" in directory.parts:
            continue
        if directory.is_dir():
            shutil.rmtree(directory, ignore_errors=True)
            removed += 1
    for p in ROOT.rglob("*"):
        if any(part in {".git", "release_integrity", ".venv"} for part in p.parts):
            continue
        if p.is_file() and p.name in {"Thumbs.db", ".DS_Store"}:
            p.unlink(missing_ok=True)
            removed += 1
    return f"Release janitor removed {removed} cache or desktop-artifact item(s)"


def check_navigation_contract() -> str:
    base = (CORE / "templates" / "base.html").read_text(encoding="utf-8")
    css = (CORE / "static" / "css" / "styles.css").read_text(encoding="utf-8")
    assert 'class="way-home"' in base, "Return-to-Observatory link missing"
    assert 'href="/observatory"' in base, "Return link target is not /observatory"
    marker = "PASS 62 — RELEASE INTEGRITY CLEARANCE"
    assert marker in css, "Pass 62 navigation clearance CSS marker missing"
    assert re.search(r"\.way-home\s*\{[^}]*top:\s*3[2-9]\dpx", css, re.S), "Desktop return control is not below the hero copy"
    return "Return navigation exists, points home, and is positioned below the hero copy"


def check_ui_language_contracts() -> str:
    paths = [CORE / "templates" / "observatory.html", CORE / "static" / "js" / "governing_field_renderer.js"]
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in paths)
    required = [
        "Parent demonstration", "Active experiment", "Release assumption",
        "sourceObservation", "sourceExplanation", "Journal",
        "not measured", "relative", "Add source", "Reset",
    ]
    missing = [item for item in required if item.lower() not in text.lower()]
    if missing:
        raise AssertionError("Missing public integrity language: " + ", ".join(missing))
    forbidden = ["guaranteed exposure", "verified wildfire", "measured concentration detected"]
    found = [item for item in forbidden if item.lower() in text.lower()]
    if found:
        raise AssertionError("Unsupported claim language found: " + ", ".join(found))
    return f"{len(required)} required integrity concepts present; unsupported claim scan clear"


def check_test_suite() -> str:
    """Run the regression suite without assuming pytest is installed.

    The project tests are unittest-compatible, so a clean Windows virtual
    environment can execute them directly. If pytest exists we use it; otherwise
    we run every selected test module with the project interpreter.
    """
    py = discover_python()
    test_paths = [
        "tests/pass48", "tests/pass49", "tests/pass50", "tests/pass52", "tests/pass53",
        "tests/pass54", "tests/pass55", "tests/pass58", "tests/test_pass56_living_sites.py",
        "tests/test_pass59_source_creation_contract.py", "tests/test_pass60_experiment_journal.py",
        "tests/final", "tests/final_instrument", "tests/release_audit_test.py", "tests/smoke_test.py",
    ]
    existing = [CORE / p for p in test_paths if (CORE / p).exists()]
    probe = subprocess.run([py, "-c", "import pytest"], cwd=str(CORE), capture_output=True, text=True)
    if probe.returncode == 0:
        return command([py, "-m", "pytest", "-q", *[str(p.relative_to(CORE)) for p in existing]], cwd=CORE, timeout=600)

    files = []
    for path in existing:
        if path.is_file():
            files.append(path)
        else:
            files.extend(sorted(path.rglob("test*.py")))
    failures = []
    completed = 0
    test_env = os.environ.copy()
    # Direct script execution places the test folder first on sys.path. Explicitly
    # expose validated_core so imports such as `from app import app` and
    # `from engine...` behave the same way they do under pytest. Force UTF-8 so
    # Windows code-page defaults cannot break templates containing typographic text.
    test_env["PYTHONPATH"] = str(CORE) + os.pathsep + test_env.get("PYTHONPATH", "")
    test_env["PYTHONUTF8"] = "1"
    test_env["PYTHONIOENCODING"] = "utf-8"
    test_env["AW_DISABLE_LIVE_FETCH"] = "1"
    for file in files:
        proc = subprocess.run(
            [py, str(file)],
            cwd=str(CORE),
            env=test_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        if proc.returncode != 0:
            failures.append(f"{file.relative_to(CORE)}\n{(proc.stdout + proc.stderr)[-2500:]}")
        else:
            completed += 1
    if failures:
        raise RuntimeError("Direct unittest regression failures:\n" + "\n---\n".join(failures[:8]))
    return f"{completed} regression modules passed using dependency-free direct unittest execution (pytest not installed)"


def _route_probe_worker() -> str:
    return r'''
import json, os, statistics, sys, time
os.environ["AW_DISABLE_LIVE_FETCH"] = "1"
sys.path.insert(0, r"%s")
from app import app
routes = [
  "/", "/observatory", "/observatory?scenario=oxnard-coastal&material=fine-smoke-aerosol",
  "/health", "/api/scenarios", "/api/material-profiles", "/api/curated-sites",
  "/observatory-field.json?scenario=four-corners&material=fine-smoke-aerosol",
  "/api/live-atmosphere/four-corners"
]
results=[]
with app.test_client() as client:
  for route in routes:
    samples=[]; status=None; size=0; content_type=""
    for _ in range(3):
      t=time.perf_counter(); response=client.get(route); samples.append((time.perf_counter()-t)*1000)
      status=response.status_code; size=len(response.data); content_type=response.content_type
    results.append({"route":route,"status":status,"median_ms":round(statistics.median(samples),2),"max_ms":round(max(samples),2),"bytes":size,"content_type":content_type})
print(json.dumps(results))
''' % str(CORE).replace("\\", "\\\\")


def check_routes_and_performance() -> str:
    py = discover_python()
    proc = subprocess.run([py, "-c", _route_probe_worker()], cwd=str(CORE), capture_output=True, text=True, timeout=240)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-5000:] or proc.stdout[-5000:])
    rows = json.loads(proc.stdout.strip().splitlines()[-1])
    failures = [r for r in rows if r["status"] != 200]
    if failures:
        raise AssertionError("Non-200 routes: " + json.dumps(failures))
    slow = [r for r in rows if r["median_ms"] > 2500]
    if slow:
        raise AssertionError("Median route response exceeded 2500 ms: " + json.dumps(slow))
    (REPORT_DIR / "route_performance.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    max_row = max(rows, key=lambda r: r["median_ms"])
    return f"{len(rows)} routes returned 200; slowest median {max_row['median_ms']} ms ({max_row['route']})"


def check_api_contracts() -> str:
    py = discover_python()
    code = r'''
import json, os, sys
os.environ["AW_DISABLE_LIVE_FETCH"]="1"
sys.path.insert(0, r"%s")
from app import app
with app.test_client() as c:
  scenarios=c.get('/api/scenarios').get_json()
  materials=c.get('/api/material-profiles').get_json()
  sites=c.get('/api/curated-sites').get_json()
  field=c.get('/observatory-field.json?scenario=four-corners&material=fine-smoke-aerosol').get_json()
  out={
    'scenario_count':len(scenarios.get('scenarios',[])),
    'material_count':len(materials.get('material_profiles',[])),
    'site_count':len(sites.get('sites',[])),
    'field_keys':sorted(field.keys()),
    'grid_keys':sorted(field.get('grid',{}).keys()),
  }
  assert out['scenario_count'] >= 2
  assert out['material_count'] >= 4
  assert out['site_count'] >= 10
  assert 'diagnostics' in field and 'grid' in field
  assert 'relative_influence' in field['grid'] and 'model_support' in field['grid']
print(json.dumps(out))
''' % str(CORE).replace("\\", "\\\\")
    return command([py, "-c", code], cwd=CORE, timeout=180)


def check_error_responses() -> str:
    py = discover_python()
    code = r'''
import os, sys
os.environ["AW_DISABLE_LIVE_FETCH"]="1"
sys.path.insert(0, r"%s")
from app import app
with app.test_client() as c:
  assert c.get('/api/curated-site/not-a-real-site').status_code == 404
  bad=c.get('/api/live-atmosphere/four-corners?source_lat=bad&source_lon=bad')
  assert bad.status_code in (200,400)
  assert c.get('/definitely-not-a-route').status_code == 404
print('Graceful 404 and malformed-coordinate handling passed')
''' % str(CORE).replace("\\", "\\\\")
    return command([py, "-c", code], cwd=CORE, timeout=120)


def check_live_server_optional(base_url: str) -> str:
    routes = ["/", "/observatory", "/health", "/api/curated-sites"]
    timings=[]
    for route in routes:
        start=time.perf_counter()
        try:
            with urllib.request.urlopen(base_url.rstrip("/") + route, timeout=15) as response:
                body=response.read()
                if response.status != 200:
                    raise AssertionError(f"{route}: HTTP {response.status}")
                timings.append((route, round((time.perf_counter()-start)*1000,2), len(body)))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach {base_url}: {exc}")
    return "; ".join(f"{r} {ms}ms {size}B" for r,ms,size in timings)


def write_reports() -> tuple[Path, Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": "Invisible Air Atmospheric Observatory",
        "checks": [asdict(c) for c in CHECKS],
    }
    blocking_failures = [c for c in CHECKS if c.status == "FAIL" and c.blocking]
    data["release_gate"] = "GO" if not blocking_failures else "NO-GO"
    json_path = REPORT_DIR / "release_integrity_report.json"
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    lines = [
        "# Invisible Air Release Integrity Report", "",
        f"**Generated:** {data['generated_at']}",
        f"**Release Council Decision:** {data['release_gate']}", "",
        "| Team | Check | Result | Time | Detail |",
        "|---|---|---:|---:|---|",
    ]
    for c in CHECKS:
        detail = c.detail.replace("\n", " ").replace("|", "\\|")[:700]
        lines.append(f"| {c.team} | {c.name} | **{c.status}** | {c.seconds:.2f}s | {detail} |")
    lines += ["", "## Release rule", "", "GitHub and Render are approved only when all blocking checks pass. A GO report does not certify atmospheric truth; it certifies that the tested software contracts passed in this environment."]
    md_path = REPORT_DIR / "RELEASE_INTEGRITY_REPORT.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    html_rows = "".join(
        f"<tr class='{c.status.lower()}'><td>{c.team}</td><td>{c.name}</td><td>{c.status}</td><td>{c.seconds:.2f}s</td><td><pre>{c.detail}</pre></td></tr>" for c in CHECKS
    )
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Invisible Air Release Integrity</title><style>body{{font:15px system-ui;background:#09100f;color:#e8e1cf;margin:32px}}h1{{font-family:Georgia,serif}}.decision{{font-size:28px;color:{'#77e2c7' if data['release_gate']=='GO' else '#ff8b74'}}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #31413d;padding:10px;text-align:left;vertical-align:top}}th{{color:#d2ad65}}tr.pass td:nth-child(3){{color:#77e2c7;font-weight:700}}tr.fail td:nth-child(3){{color:#ff8b74;font-weight:700}}pre{{white-space:pre-wrap;margin:0;font:12px/1.4 ui-monospace,monospace}}</style></head><body><h1>Invisible Air Release Integrity Team</h1><p class='decision'>{data['release_gate']}</p><p>{data['generated_at']}</p><table><thead><tr><th>Team</th><th>Check</th><th>Result</th><th>Time</th><th>Detail</th></tr></thead><tbody>{html_rows}</tbody></table><p>A GO decision verifies tested software contracts, not real-world atmospheric truth or measured emissions.</p></body></html>"""
    html_path = REPORT_DIR / "RELEASE_INTEGRITY_REPORT.html"
    html_path.write_text(html, encoding="utf-8")
    return json_path, md_path, html_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Invisible Air dynamic pre-GitHub release integrity team")
    parser.add_argument("--live-url", default="", help="Optional running local or deployed URL, such as http://127.0.0.1:8000")
    parser.add_argument("--skip-full-tests", action="store_true", help="Skip the long pytest suite; produces a NO-GO advisory check")
    args = parser.parse_args()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    run_check("Sentinel", "Critical project structure", check_required_files)
    run_check("Sentinel", "Python syntax", check_python_syntax)
    run_check("Sentinel", "JavaScript syntax", check_js_syntax)
    run_check("Sentinel", "Secret and credential scan", check_secrets)
    run_check("Sentinel", "Repository hygiene", check_repository_hygiene, blocking=False)
    run_check("Navigator", "Return navigation clearance", check_navigation_contract)
    run_check("Curator", "Scientific and UI language contracts", check_ui_language_contracts)
    run_check("Experimentalist", "API contract diversity", check_api_contracts)
    run_check("Responder", "Error and malformed-input behavior", check_error_responses)
    run_check("Performance", "Route response and performance budget", check_routes_and_performance)
    if args.skip_full_tests:
        started=time.perf_counter(); record("Experimentalist", "Full regression suite", "FAIL", started, "Skipped by operator; rerun without --skip-full-tests before GitHub", True)
    else:
        run_check("Experimentalist", "Full regression suite", check_test_suite)
    if args.live_url:
        run_check("Navigator", f"Live HTTP probe: {args.live_url}", lambda: check_live_server_optional(args.live_url))

    json_path, md_path, html_path = write_reports()
    gate = "GO" if not [c for c in CHECKS if c.status == "FAIL" and c.blocking] else "NO-GO"
    print("\n" + "="*72)
    print(f"INVISIBLE AIR RELEASE COUNCIL: {gate}")
    print(f"JSON: {json_path}")
    print(f"MARKDOWN: {md_path}")
    print(f"HTML: {html_path}")
    print("="*72)
    return 0 if gate == "GO" else 1

if __name__ == "__main__":
    raise SystemExit(main())
