from __future__ import annotations

from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app import app


def main():
    client=app.test_client()
    required=["/","/scene","/health","/self-test.json","/scientific-synthesis.json","/level-five-visual-composition.json","/release-proof","/release-proof.json"]
    for route in required:
        response=client.get(route)
        assert response.status_code==200, f"{route} returned {response.status_code}"
    health=client.get("/health").get_json()
    assert health.get("pass_id")=="SV2-57"
    release=client.get("/release-proof.json").get_json()
    assert release.get("pass_id")=="SV2-57"
    assert release.get("status")=="ready"
    assert release.get("passed_count")==release.get("total_count")
    assert len(release.get("guardrails") or [])>=5
    assert "does not validate methane detection" in release.get("claim_boundary","")
    print("SV2-57 release audit: PASS")
    print(f"Release gates: {release['passed_count']} / {release['total_count']}")
    print("Routes checked:", len(required))

if __name__=="__main__":
    main()
