"""Plots the Nov 7 2026 test results for the README (img/result_*.png).
Run: python3 sim/results_plots.py"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sizing

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
BLUE, ORANGE = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": INK2, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF})

# ---- sim for the real conditions: 1.05 kg from 12 C, measured batteries 4.0/4.5/8.3/~10 mOhm ----
sizing.M_WATER, sizing.T0 = 1.05, 12.0
t_real, _, _ = sizing.simulate(dict(n=4, voc=12.65, r=(4.0 + 4.5 + 8.3 + 10.0) / 4 * 1e-3, pol=0.45, tau=12.0))
sizing.M_WATER, sizing.T0 = 1.0, 15.0
t_good, _, _ = sizing.simulate(sizing.SOURCES["4x lead-acid, good (5.5 mOhm/batt)"])

# ---- 1: how fast is it ----
rows = [("Normal 2 kW electric kettle", 185.0, INK2),
        ("Impulse Labs cooktop", 40.0, INK2),
        ("Fastest Kettle - measured, 1.05 L from 12 °C", 29.5, ORANGE),
        (f"Fastest Kettle - sim, same conditions", t_real, BLUE),
        (f"Fastest Kettle - sim, good batteries, 1 L from 15 °C", t_good, BLUE)]
fig, ax = plt.subplots(figsize=(9.5, 3.6))
for i, (lab, v, c) in enumerate(rows[::-1]):
    ax.barh(i, v, color=c, height=0.62)
    ax.text(v + 2, i, f"{v:.1f} s" if v < 100 else f"~{v/60:.0f} min", va="center", color=INK, fontsize=11, fontweight="bold")
ax.set_yticks(range(len(rows)), [r[0] for r in rows[::-1]], color=INK)
ax.set_xlabel("seconds to boil 1 litre")
ax.set_xlim(0, 215)
ax.grid(axis="x", color=GRID); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
ax.set_title("Time to boil", loc="left", color=INK, fontsize=14, fontweight="bold")
fig.tight_layout(); fig.savefig(os.path.join(ROOT, "img", "result_boil_times.png"), dpi=150)

print(f"sim same conditions {t_real:.1f} s, sim good {t_good:.1f} s")
