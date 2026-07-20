from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

from engine.full_dem import RASTER_FILE, full_dem_context

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "terrain_derivatives_cache"
LANDFORM_FILE = CACHE_DIR / "default_scene_landforms.png"
CONFIDENCE_FILE = CACHE_DIR / "default_scene_landform_confidence.png"
METADATA_FILE = CACHE_DIR / "default_scene_landforms.json"
MIN_VALID_RATIO = 0.90

CLASS_DEFS = [
    (0, "flat", (112, 126, 124)),
    (1, "ridge", (224, 202, 128)),
    (2, "spur", (192, 169, 110)),
    (3, "valley", (67, 128, 147)),
    (4, "drainage", (46, 94, 124)),
    (5, "saddle", (171, 133, 175)),
    (6, "upper_slope", (151, 147, 112)),
    (7, "midslope", (124, 120, 100)),
    (8, "lower_slope", (100, 124, 108)),
    (9, "bench", (133, 154, 119)),
    (10, "basin", (73, 112, 113)),
    (11, "shoulder", (176, 156, 113)),
]
LABELS = {i:n for i,n,_ in CLASS_DEFS}
COLORS = np.asarray([c for _,_,c in CLASS_DEFS], dtype=np.uint8)


def _relative(path: Path) -> str:
    return str(path.relative_to(path.parents[2])).replace("\\", "/")


def _read_dem() -> np.ndarray:
    a=np.squeeze(np.asarray(tifffile.imread(RASTER_FILE))).astype(np.float64, copy=False)
    if a.ndim != 2: raise ValueError(f"DEM raster must be 2D, got {a.shape}")
    finite=np.isfinite(a) & (np.abs(a)<1e20)
    if float(finite.mean()) < MIN_VALID_RATIO: raise ValueError("DEM valid-cell ratio too low")
    if not finite.all():
        fill=float(np.nanmedian(np.where(finite,a,np.nan))); a=np.where(finite,a,fill)
    return a


def _box_mean(a: np.ndarray, radius: int) -> np.ndarray:
    p=np.pad(a, radius, mode="edge")
    integ=np.pad(p, ((1,0),(1,0)), mode="constant").cumsum(0).cumsum(1)
    k=2*radius+1
    return (integ[k:,k:] - integ[:-k,k:] - integ[k:,:-k] + integ[:-k,:-k])/(k*k)


def _derive(elev: np.ndarray, px: float, py: float):
    dy=max(float(py),0.01); dx=max(float(px),0.01)
    gy,gx=np.gradient(elev,dy,dx)
    slope=np.degrees(np.arctan(np.hypot(gx,gy)))
    small=_box_mean(elev,3); broad=_box_mean(elev,11)
    tpi_small=elev-small; tpi_broad=elev-broad
    gyy,_=np.gradient(gy,dy,dx); _,gxx=np.gradient(gx,dy,dx)
    curvature=gxx+gyy
    relief=np.sqrt(np.maximum(_box_mean((elev-broad)**2,7), 0.0))
    eps=1e-6
    zsmall=tpi_small/(relief+eps); zbroad=tpi_broad/(relief+eps)
    cls=np.full(elev.shape,7,dtype=np.uint8)
    # Ordered, reproducible geomorphometric rules.
    cls[slope < 2.0]=0
    cls[(slope>=2)&(slope<7)&(np.abs(zbroad)<0.18)]=9
    cls[(zbroad>0.42)&(zsmall>0.18)]=1
    cls[(zbroad>0.24)&(zsmall>0.05)&(slope>=7)]=2
    cls[(zbroad<-0.42)&(zsmall<-0.18)]=3
    cls[(zbroad<-0.24)&(zsmall<-0.05)&(slope>=5)]=4
    cls[(zbroad<-0.28)&(slope<7)]=10
    cls[(zbroad>0.18)&(zsmall<0.02)&(slope>=5)]=11
    cls[(zbroad>0.12)&(slope>=7)&(cls==7)]=6
    cls[(zbroad<-0.12)&(slope>=7)&(cls==7)]=8
    # Saddle: broad position near neutral but opposing local curvature signals and non-flat slope.
    saddle=(np.abs(zbroad)<0.16)&(np.abs(zsmall)>0.16)&(slope>=3)&(slope<22)&(np.abs(curvature)>np.percentile(np.abs(curvature),65))
    cls[saddle]=5
    # confidence is distance from class boundaries, bounded and intentionally conservative.
    position=np.clip(np.maximum(np.abs(zbroad),np.abs(zsmall))/0.65,0,1)
    slope_signal=np.clip(slope/18.0,0,1)
    confidence=0.42+0.36*position+0.22*slope_signal
    confidence[cls==0]=np.clip(1-slope[cls==0]/2.5,0.55,0.96)
    confidence[cls==9]=np.clip(0.55+(7-slope[cls==9])/25,0.5,0.86)
    confidence[cls==5]=np.clip(confidence[cls==5]-0.12,0.38,0.72)
    confidence=np.clip(confidence,0.35,0.97)
    rgb=COLORS[cls]
    conf_img=(confidence*255).astype(np.uint8)
    unique,counts=np.unique(cls,return_counts=True)
    total=cls.size
    distribution={LABELS[int(i)]:{"cells":int(c),"ratio":round(float(c/total),4)} for i,c in zip(unique,counts)}
    dominant=sorted(distribution.items(),key=lambda x:x[1]["cells"],reverse=True)[:5]
    stats={
        "class_count":int(len(unique)),"dominant_classes":[{"class":k,**v} for k,v in dominant],
        "mean_confidence":round(float(confidence.mean()),4),"p10_confidence":round(float(np.percentile(confidence,10)),4),
        "p90_confidence":round(float(np.percentile(confidence,90)),4),"classification_distribution":distribution,
        "method":"multi-scale topographic-position, slope, local relief, and curvature rules",
    }
    return rgb,conf_img,stats


def _base(scene:dict,dem:dict)->dict:
    return {"contract_version":"1.0","pass_id":"SV2-35","layer":"dem_derived_landform_classification",
      "source_dem_sha256":dem.get("sha256"),"source_dem_provider":dem.get("provider"),"source_dem_bbox":dem.get("bbox"),
      "source_dem_grid":dem.get("requested_grid"),"landform_output_path":_relative(LANDFORM_FILE),
      "confidence_output_path":_relative(CONFIDENCE_FILE),"metadata_path":_relative(METADATA_FILE),
      "evidence_state":"measured","class_definitions":[{"id":i,"label":n,"color_rgb":list(c)} for i,n,c in CLASS_DEFS],
      "visual_role":"reproducible terrain anatomy for human review and later atmospheric-context comparison",
      "claim_boundary":"Landforms are DEM-derived geomorphometric classes, not field-surveyed geology, atmospheric transport, methane evidence, event reconstruction, or source attribution."}


def refresh_landforms(scene:dict)->dict:
    dem=full_dem_context(scene); c=_base(scene,dem); now=datetime.now(timezone.utc).isoformat()
    if dem.get("data_state")!="continuous_dem_cache" or not RASTER_FILE.exists():
        c.update({"data_state":"landforms_unavailable_no_valid_dem","cache_status":"not_generated","coverage_status":"unresolved","generated_at_utc":None,"display_label":"landforms unavailable · valid DEM required","failure_reason":"No validated continuous DEM cache is available.","statistics":None})
    else:
        try:
            elev=_read_dem(); pix=dem.get("approx_pixel_size_m",{})
            rgb,conf,stats=_derive(elev,pix.get("x",1),pix.get("y",1))
            CACHE_DIR.mkdir(parents=True,exist_ok=True)
            Image.fromarray(rgb,"RGB").save(LANDFORM_FILE,"PNG",optimize=True)
            Image.fromarray(conf,"L").save(CONFIDENCE_FILE,"PNG",optimize=True)
            lb=LANDFORM_FILE.read_bytes(); cb=CONFIDENCE_FILE.read_bytes()
            c.update({"data_state":"dem_derived_landform_cache","cache_status":"refreshed","coverage_status":"source_dem_bbox_covered","generated_at_utc":now,
             "display_label":f"DEM-derived landforms ready · {elev.shape[1]} × {elev.shape[0]}","failure_reason":None,
             "output_grid":{"width":int(elev.shape[1]),"height":int(elev.shape[0])},"landform_sha256":hashlib.sha256(lb).hexdigest(),
             "confidence_sha256":hashlib.sha256(cb).hexdigest(),"landform_byte_size":len(lb),"confidence_byte_size":len(cb),"statistics":stats,
             "landform_image_url":"/landform-image","confidence_image_url":"/landform-confidence-image"})
        except Exception as exc:
            c.update({"data_state":"landform_generation_failed","cache_status":"refresh_failed","coverage_status":"unresolved","generated_at_utc":None,"display_label":"landform classification failed","failure_reason":str(exc)[:300],"statistics":None})
    CACHE_DIR.mkdir(parents=True,exist_ok=True); METADATA_FILE.write_text(json.dumps(c,indent=2),encoding="utf-8")
    return c


def landform_context(scene:dict,refresh:bool=False)->dict:
    if refresh:return refresh_landforms(scene)
    dem=full_dem_context(scene); c=_base(scene,dem)
    if METADATA_FILE.exists():
        try:
            cached=json.loads(METADATA_FILE.read_text(encoding="utf-8")); same=cached.get("source_dem_sha256")==dem.get("sha256")
            if cached.get("data_state")=="dem_derived_landform_cache" and same and LANDFORM_FILE.exists() and CONFIDENCE_FILE.exists():
                if hashlib.sha256(LANDFORM_FILE.read_bytes()).hexdigest()==cached.get("landform_sha256") and hashlib.sha256(CONFIDENCE_FILE.read_bytes()).hexdigest()==cached.get("confidence_sha256"):
                    cached["cache_status"]="loaded"; cached["pass_id"]="SV2-35"; return cached
        except (OSError,ValueError,TypeError): pass
    if dem.get("data_state")=="continuous_dem_cache":
        c.update({"data_state":"landforms_ready_to_generate","cache_status":"missing","coverage_status":"source_dem_available","generated_at_utc":None,"display_label":"validated DEM ready · landform cache pending","failure_reason":None,"statistics":None})
    else:
        c.update({"data_state":"landforms_unavailable_no_valid_dem","cache_status":"missing","coverage_status":"unresolved","generated_at_utc":None,"display_label":"landforms unavailable · valid DEM required","failure_reason":None,"statistics":None})
    return c
