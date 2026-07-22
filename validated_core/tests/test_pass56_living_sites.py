from engine.material_profiles import list_material_profiles
from engine.site_registry import list_curated_sites

def test_material_profiles_have_visual_identity():
    profiles=list_material_profiles()
    assert len(profiles)>=4
    assert all(p.get("visual_identity",{}).get("accent") for p in profiles)
    assert len({p["visual_identity"]["family"] for p in profiles})>=4

def test_site_registry_is_bounded_and_explicit():
    sites=list_curated_sites()
    assert len(sites)>=10
    assert all(s["status"] in {"curated_demo","planned_demo"} for s in sites)
    assert all(s.get("material_profile_id") and s.get("scenario_id") for s in sites)
