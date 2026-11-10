"""Current-flow (sheet resistance) simulation of the real heater copper.
Needs numpy, scipy, matplotlib. Input: sim/out/heater_copper_mask.npz (from heater_raster.py).
Solves Laplace's equation on the copper with the two busbar contact pads as electrodes, then maps the local
power density relative to the spiral average, smoothed over ~1 mm (lateral spreading length of 35 um copper on
a 100 um, 1 W/mK dielectric). Writes img/heater_hotspots.png."""
import os, numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spla
from scipy.ndimage import gaussian_filter, label
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = np.load(os.path.join(ROOT, "sim/out/heater_copper_mask.npz"))
M, DX, X0 = d["mask"], float(d["dx"]), float(d["x0"])
n = M.shape[0]
x = X0 + np.arange(n) * DX
XX, YY = np.meshgrid(x, x)
R = np.hypot(XX, YY)
# drop floating copper islands (not connected to the terminals): they carry no current
labs, _ = label(M)
keep = np.unique(labs[M & (np.abs(XX) >= 139.5) & (np.abs(YY) <= 17.5)])
M = np.isin(labs, keep[keep > 0])
padA = M & (XX >= 139.5) & (XX <= 156.0) & (np.abs(YY) <= 17.5)
padB = M & (XX <= -139.5) & (XX >= -156.0) & (np.abs(YY) <= 17.5)
free = M & ~padA & ~padB
idx = -np.ones(M.shape, int); idx[free] = np.arange(free.sum())
rows, cols, vals = [], [], []; b = np.zeros(free.sum())
fi, fj = np.nonzero(free)
for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
    ni, nj = fi + di, fj + dj
    ok = (ni >= 0) & (ni < n) & (nj >= 0) & (nj < n)
    ni, nj, ci, cj = ni[ok], nj[ok], fi[ok], fj[ok]
    me = idx[ci, cj]
    cu = M[ni, nj]
    rows.append(me[cu]); cols.append(me[cu]); vals.append(np.ones(cu.sum()))          # diagonal
    nb_free = free[ni, nj] & cu
    rows.append(me[nb_free]); cols.append(idx[ni[nb_free], nj[nb_free]]); vals.append(-np.ones(nb_free.sum()))
    nbA = padA[ni, nj]
    np.add.at(b, me[nbA], 1.0)                                                         # V=1 on pad A, 0 on B
A = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(free.sum(),) * 2)
V = np.zeros(M.shape); V[padA] = 1.0
V[free] = spla.spsolve(A.tocsc(), b)
# current leaving pad A (unit sheet conductance) -> resistance in squares
I = 0.0
for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
    Vs = np.roll(np.roll(V, di, 0), dj, 1); Ms = np.roll(np.roll(free, di, 0), dj, 1)
    I += np.sum((V - Vs)[padA & Ms])
squares = 1.0 / I
# dissipation per pixel from the copper-to-copper faces only (each face shared half/half): sums to the exact total
p = np.zeros(M.shape)
for ax_ in (0, 1):
    a = M & np.roll(M, -1, ax_)
    a[(n - 1, slice(None)) if ax_ == 0 else (slice(None), n - 1)] = False
    e = np.where(a, (np.roll(V, -1, ax_) - V) ** 2, 0.0) / DX ** 2
    p += 0.5 * e + 0.5 * np.roll(e, 1, ax_)
p = np.where(M, p, 0.0)
heated = free & (R <= 136)
p_rel = p / p[heated].mean()
ps = gaussian_filter(p_rel, 1.0 / DX) / np.maximum(gaussian_filter(free.astype(float), 1.0 / DX), 1e-9)
ps = np.where(free, ps, np.nan)
rs = 0.491e-3
print(f"resistance {squares:.1f} squares -> R20 {squares*rs*1e3:.1f} mOhm (generator estimate 65.4)")
zones = {"spiral body (r 50-125)": heated & (R > 50) & (R < 125),
         "centre junction (r<50)": free & (R < 50),
         "terminal leads (r 125-140)": free & (R >= 125) & (R < 140)}
for k, z in zones.items():
    v = ps[z]
    print(f"{k:28s} mean x{np.nanmean(v):.2f}  99th pct x{np.nanpercentile(v,99):.2f}  max x{np.nanmax(v):.2f}")
# top hotspots
cand = np.nan_to_num(ps) * free
lab, nl = label(cand > 1.6)
spots = []
for L in range(1, nl + 1):
    m = lab == L
    k = np.argmax(np.where(m, cand, 0)); i, j = np.unravel_index(k, M.shape)
    spots.append((cand[i, j], x[j], x[i], m.sum() * DX * DX))
for v, sx, sy, area in sorted(spots, reverse=True)[:8]:
    print(f"hotspot x{v:.2f} at ({sx:6.1f},{sy:6.1f}) mm, r={np.hypot(sx,sy):5.1f}, area >1.6x: {area:.1f} mm2")
fig, ax = plt.subplots(1, 2, figsize=(14, 6.5))
im = ax[0].imshow(ps, origin="upper", extent=[x[0], x[-1], x[-1], x[0]], cmap="inferno", vmin=0, vmax=2.5)
ax[0].set_title(f"local heating / spiral average (1 mm smoothing)\nR = {squares:.0f} squares = {squares*rs*1e3:.1f} mOhm at 20 C"); plt.colorbar(im, ax=ax[0])
im2 = ax[1].imshow(V, origin="upper", extent=[x[0], x[-1], x[-1], x[0]], cmap="viridis"); ax[1].set_title("potential (pad A = 1, pad B = 0)")
for a in ax: a.set_xlabel("mm"); a.set_aspect("equal")
fig.tight_layout(); fig.savefig(os.path.join(ROOT, "img/heater_hotspots.png"), dpi=100)
np.savez_compressed(os.path.join(ROOT, "sim/out/heater_power_map.npz"), p_rel=ps, x=x)
