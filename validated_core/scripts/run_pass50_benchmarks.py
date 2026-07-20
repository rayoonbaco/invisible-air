from pathlib import Path
import json, sys
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine.governing_model import input_from_dict, run_governing_model

ROOT=Path(__file__).resolve().parents[1]; out=ROOT/'artifacts'/'pass50'; out.mkdir(parents=True,exist_ok=True)
base={"source":{"latitude":40,"longitude":-105,"relative_strength":1,"release_height_m":15},"meteorology":{"wind_from_deg":270,"wind_speed_mps":5,"stability_class":"neutral","boundary_layer_depth_m":700,"direction_variability_deg":8,"gust_factor":1.15},"grid":{"domain_downwind_km":70,"domain_crosswind_km":35,"nx":181,"ny":121}}

def render(r,path):
 inf=np.array(r['grid']['relative_influence']); sup=np.array(r['grid']['model_support']); h,w=inf.shape
 rgba=np.zeros((h,w,4),dtype=np.uint8)
 rgba[...,0]=(255*np.power(inf,.55)).astype(np.uint8)
 rgba[...,1]=(220*np.power(inf,.7)).astype(np.uint8)
 rgba[...,2]=(120*np.power(inf,.9)+100*(1-sup)*inf).clip(0,255).astype(np.uint8)
 texture=((np.indices((h,w))[0]*37+np.indices((h,w))[1]*19)%100)/100
 alpha=(255*np.power(inf,.65)*(0.35+0.65*(texture<(.25+.7*sup)))).astype(np.uint8)
 rgba[...,3]=np.where(inf>.008,alpha,0)
 Image.fromarray(rgba,'RGBA').save(path)

manifest={}
for profile in ['open','valley_aligned','cross_ridge','complex']:
 for enabled in ([False,True] if profile!='open' else [True]):
  p={**base,'terrain':{'regime':'open','local_profile':profile,'local_response_enabled':enabled,'response_strength':1.0,'evidence_support':0.9}}
  r=run_governing_model(input_from_dict(p)); name=f'{profile}-terrain-{"on" if enabled else "off"}'
  (out/f'{name}.json').write_text(json.dumps(r,indent=2))
  render(r,out/f'{name}.png')
  manifest[name]={'fingerprint':r['fingerprint'],'spread_km':r['diagnostics']['rms_crosswind_spread_km'],'support':r['diagnostics']['mean_support_in_active_field'],'terrain':r['diagnostics']['terrain_local']}
(out/'pass50_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
