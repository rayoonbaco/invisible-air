from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.governing_model import input_from_dict, run_governing_model
out=ROOT/'artifacts'/'pass48'; out.mkdir(parents=True,exist_ok=True)
manifest=[]
for path in sorted((ROOT/'data'/'pass48_benchmarks').glob('*.json')):
    result=run_governing_model(input_from_dict(json.loads(path.read_text(encoding='utf-8'))))
    target=out/f'{path.stem}.field.json'; target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    manifest.append({'case':path.stem,'fingerprint':result['fingerprint'],'diagnostics':result['diagnostics']})
(out/'benchmark_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2))
