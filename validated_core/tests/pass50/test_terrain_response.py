import unittest
import numpy as np
from engine.governing_model import input_from_dict, run_governing_model

BASE={
 "source":{"latitude":40.0,"longitude":-105.0,"relative_strength":1.0,"release_height_m":15.0},
 "meteorology":{"wind_from_deg":270.0,"wind_speed_mps":5.0,"stability_class":"neutral","boundary_layer_depth_m":700.0,"direction_variability_deg":8.0,"gust_factor":1.15},
 "grid":{"domain_downwind_km":70.0,"domain_crosswind_km":35.0,"nx":181,"ny":121}
}

def run(profile, enabled=True):
 p={**BASE,"terrain":{"regime":"open","local_profile":profile,"local_response_enabled":enabled,"response_strength":1.0,"evidence_support":0.9}}
 return run_governing_model(input_from_dict(p))

class TerrainResponseTests(unittest.TestCase):
 def test_open_on_equals_off(self):
  a,b=run("open",True),run("open",False)
  self.assertTrue(np.array_equal(np.array(a["grid"]["relative_influence"]),np.array(b["grid"]["relative_influence"])))
 def test_valley_compresses_field(self):
  a,b=run("open"),run("valley_aligned")
  self.assertLess(b["diagnostics"]["rms_crosswind_spread_km"],a["diagnostics"]["rms_crosswind_spread_km"])
 def test_cross_ridge_changes_cells(self):
  a,b=run("cross_ridge",False),run("cross_ridge",True)
  ga=np.array(a["grid"]["relative_influence"]); gb=np.array(b["grid"]["relative_influence"])
  self.assertGreater(float(np.mean(np.abs(ga-gb))),0.01)
 def test_cross_ridge_reduces_support(self):
  a,b=run("cross_ridge",False),run("cross_ridge",True)
  self.assertLess(b["diagnostics"]["mean_support_in_active_field"],a["diagnostics"]["mean_support_in_active_field"])
 def test_deterministic(self):
  self.assertEqual(run("complex")["fingerprint"],run("complex")["fingerprint"])
 def test_response_is_bounded(self):
  for profile in ["open","valley_aligned","cross_ridge","complex"]:
   r=run(profile)
   for key in ["relative_influence","model_support"]:
    a=np.array(r["grid"][key]); self.assertGreaterEqual(a.min(),0); self.assertLessEqual(a.max(),1)

if __name__=='__main__': unittest.main()
