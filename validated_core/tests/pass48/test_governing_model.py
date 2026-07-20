import json
from pathlib import Path
import unittest
from dataclasses import replace
import numpy as np
from engine.governing_model import GoverningModelInput, MeteorologyInput, TerrainInput, run_governing_model

class GoverningModelTests(unittest.TestCase):
    def base(self): return GoverningModelInput()
    def test_deterministic(self):
        a=run_governing_model(self.base()); b=run_governing_model(self.base())
        self.assertEqual(a['fingerprint'],b['fingerprint'])
        self.assertEqual(a['grid']['relative_influence'],b['grid']['relative_influence'])
    def test_wind_direction_changes_bearing(self):
        east=run_governing_model(replace(self.base(),meteorology=replace(self.base().meteorology,wind_from_deg=270)))
        north=run_governing_model(replace(self.base(),meteorology=replace(self.base().meteorology,wind_from_deg=180)))
        self.assertAlmostEqual(east['diagnostics']['effective_transport_deg'],90,delta=1)
        self.assertAlmostEqual(north['diagnostics']['effective_transport_deg'],0,delta=1)
    def test_speed_changes_reach(self):
        low=run_governing_model(replace(self.base(),meteorology=replace(self.base().meteorology,wind_speed_mps=1.5)))
        high=run_governing_model(replace(self.base(),meteorology=replace(self.base().meteorology,wind_speed_mps=8.0)))
        self.assertGreater(high['diagnostics']['influence_centroid_downwind_km'],low['diagnostics']['influence_centroid_downwind_km'])
    def test_stability_changes_spread(self):
        stable=run_governing_model(replace(self.base(),meteorology=replace(self.base().meteorology,stability_class='very_stable')))
        unstable=run_governing_model(replace(self.base(),meteorology=replace(self.base().meteorology,stability_class='very_unstable')))
        self.assertGreater(unstable['diagnostics']['rms_crosswind_spread_km'],stable['diagnostics']['rms_crosswind_spread_km'])
    def test_variability_reduces_support(self):
        quiet=run_governing_model(replace(self.base(),meteorology=replace(self.base().meteorology,direction_variability_deg=3,gust_factor=1.05)))
        variable=run_governing_model(replace(self.base(),meteorology=replace(self.base().meteorology,direction_variability_deg=30,gust_factor=1.8)))
        self.assertLess(variable['diagnostics']['mean_support_in_active_field'],quiet['diagnostics']['mean_support_in_active_field'])
    def test_boundary_layer_changes_raw_mixing(self):
        shallow=run_governing_model(replace(self.base(),meteorology=replace(self.base().meteorology,boundary_layer_depth_m=250)))
        deep=run_governing_model(replace(self.base(),meteorology=replace(self.base().meteorology,boundary_layer_depth_m=1800)))
        self.assertGreater(shallow['diagnostics']['mixing_factor'],deep['diagnostics']['mixing_factor'])
    def test_terrain_changes_direction_or_spread(self):
        open_run=run_governing_model(replace(self.base(),terrain=TerrainInput(regime='open',response_strength=0,evidence_support=.9)))
        valley=run_governing_model(replace(self.base(),terrain=TerrainInput(regime='valley',alignment_deg=0,response_strength=1,evidence_support=.9)))
        self.assertNotEqual(open_run['diagnostics']['effective_transport_deg'],valley['diagnostics']['effective_transport_deg'])
        self.assertNotEqual(open_run['diagnostics']['rms_crosswind_spread_km'],valley['diagnostics']['rms_crosswind_spread_km'])
    def test_values_bounded(self):
        r=run_governing_model(self.base())
        for key in ('relative_influence','model_support'):
            a=np.asarray(r['grid'][key]); self.assertGreaterEqual(a.min(),0); self.assertLessEqual(a.max(),1)

if __name__=='__main__': unittest.main()
