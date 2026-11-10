"""Rasterise the heater copper (tracks + zone fills) from the KiCad board -> sim/out/heater_copper_mask.npz.
Run with the system python (needs pcbnew). Grid pitch DX mm, board centre at (170,170) in board coords."""
import os, sys, numpy as np, pcbnew
from matplotlib.path import Path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DX = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
b = pcbnew.LoadBoard(os.path.join(ROOT, "heater/heater.kicad_pcb"))
import re
ps = pcbnew.SHAPE_POLY_SET()
for z in b.Zones():
    ps.Append(z.GetFilledPolysList(pcbnew.F_Cu))
# tracks: parse the file (the SWIG track iterator is broken on python 3.14) -> capsules
segs = [tuple(map(float, m)) for m in re.findall(
    r"\(segment\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)\s+\(width ([-\d.]+)\)",
    open(os.path.join(ROOT, "heater/heater.kicad_pcb")).read())]
n = int(330 / DX)
xs = (np.arange(n) + 0.5) * DX - 165 + 170
X, Y = np.meshgrid(xs, xs)
pts = np.column_stack([X.ravel(), Y.ravel()])
mask = np.zeros(n * n, bool)
for i in range(ps.OutlineCount()):
    def path_of(chain):
        p = [(pcbnew.ToMM(chain.CPoint(k).x), pcbnew.ToMM(chain.CPoint(k).y)) for k in range(chain.PointCount())]
        return Path(p)
    inside = path_of(ps.Outline(i)).contains_points(pts)
    for h in range(ps.HoleCount(i)):
        inside &= ~path_of(ps.Hole(i, h)).contains_points(pts)
    mask |= inside
for (x1, y1, x2, y2, w) in segs:
    dx_, dy_ = x2 - x1, y2 - y1
    L2 = dx_ * dx_ + dy_ * dy_ or 1e-12
    t = np.clip(((pts[:, 0] - x1) * dx_ + (pts[:, 1] - y1) * dy_) / L2, 0, 1)
    d2 = (pts[:, 0] - x1 - t * dx_) ** 2 + (pts[:, 1] - y1 - t * dy_) ** 2
    mask |= d2 <= (w / 2) ** 2
print("segments", len(segs))
os.makedirs(os.path.join(ROOT, "sim/out"), exist_ok=True)
np.savez_compressed(os.path.join(ROOT, "sim/out/heater_copper_mask.npz"), mask=mask.reshape(n, n), dx=DX, x0=xs[0] - 170)
print("copper pixels", mask.sum(), "area cm2", mask.sum() * DX * DX / 100, "outlines", ps.OutlineCount())
