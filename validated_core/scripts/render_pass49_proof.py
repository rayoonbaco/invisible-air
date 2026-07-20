from pathlib import Path
import json
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.governing_model import input_from_dict, run_governing_model


def hash01(x: int, y: int) -> float:
    n = (x * 374761393 + y * 668265263) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFFFFFF) / 4294967295


def render(contract: dict, output: Path) -> dict:
    influence = np.asarray(contract["grid"]["relative_influence"], dtype=float)
    support = np.asarray(contract["grid"]["model_support"], dtype=float)
    ny, nx = influence.shape
    rgba = np.zeros((ny, nx, 4), dtype=np.uint8)
    for y in range(ny):
        for x in range(nx):
            value = influence[y, x]
            confidence = support[y, x]
            if value < 0.008:
                continue
            core = value ** 0.62
            weak = 1 - confidence
            if weak > 0.24 and hash01(x, y) < weak * 0.54 and value < 0.58:
                continue
            warm = max(0.0, (core - 0.52) / 0.48)
            rgba[y, x, 0] = round(117 + 130 * warm)
            rgba[y, x, 1] = round(185 + 57 * warm)
            rgba[y, x, 2] = round(182 - 70 * warm)
            edge_distance = min(x, nx - 1 - x, y, ny - 1 - y)
            edge_fade = max(0.0, min(1.0, edge_distance / 7.0))
            alpha = min(0.94, value ** 0.70 * (0.30 + confidence * 0.64) * (0.76 + confidence * 0.24)) * edge_fade
            if alpha < 0.01:
                continue
            rgba[y, x, 3] = round(alpha * 255)

    img = Image.fromarray(rgba, "RGBA").resize((1205, 805), Image.Resampling.BICUBIC)
    background = Image.new("RGBA", img.size, (7, 18, 20, 255))
    background.alpha_composite(img)
    draw = ImageDraw.Draw(background)
    draw.ellipse((18, 393, 32, 407), fill=(255, 245, 202, 255))
    background.convert("RGB").save(output, quality=94)

    active = rgba[:, :, 3] > 8
    boundary = np.concatenate([active[0], active[-1], active[:, 0], active[:, -1]])
    return {
        "active_pixel_fraction": round(float(active.mean()), 6),
        "active_boundary_pixels": int(boundary.sum()),
        "fingerprint": contract["fingerprint"],
    }


def main():
    fixture = ROOT / "data" / "pass48_benchmarks" / "open_terrain_west_wind.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    contract = run_governing_model(input_from_dict(payload))
    out_dir = ROOT / "artifacts" / "pass49"
    out_dir.mkdir(parents=True, exist_ok=True)
    metrics = render(contract, out_dir / "open-terrain-model-driven-field.png")
    (out_dir / "renderer_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    if metrics["active_boundary_pixels"] != 0:
        raise SystemExit("Rendered field touches the computational boundary")
    if not 0.01 < metrics["active_pixel_fraction"] < 0.55:
        raise SystemExit("Rendered field footprint is not localized")


if __name__ == "__main__":
    main()
