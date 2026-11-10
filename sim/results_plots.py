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
        ("Impulse Labs cooktop (claim)", 40.0, INK2),
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

# ---- 2: attempt 2, pack collapse (small multiples, no dual axis) ----
T = [1, 3, 13, 23, 33, 43, 59]
V = [38.0, 37.2, 34.0, 29.9, 28.7, 25.2, 21.6]
A = [389, 329, 317, 281, 262, 227, 194.5]
P = [v * a / 1e3 for v, a in zip(V, A)]
fig, axs = plt.subplots(1, 3, figsize=(11, 3.4), sharex=True)
for ax, y, lab, unit in ((axs[0], P, "Heater power", "kW"), (axs[1], V, "Pack voltage (idle ~50 V)", "V"), (axs[2], A, "Current", "A")):
    ax.plot(T, y, color=ORANGE, lw=2, marker="o", ms=6, mec=SURF, mew=1.5)
    ax.set_title(lab, loc="left", color=INK, fontsize=12, fontweight="bold")
    ax.set_ylabel(unit); ax.set_xlabel("seconds after switch-on"); ax.grid(color=GRID); ax.set_ylim(0, max(y) * 1.18)
    fmt = "{:.0f}" if unit == "A" else "{:.1f}"
    ax.annotate(fmt.format(y[0]), (T[0], y[0]), textcoords="offset points", xytext=(8, 6) if unit == "V" else (8, -14), color=INK)
    ax.annotate(fmt.format(y[-1]), (T[-1], y[-1]), textcoords="offset points", xytext=(-14, 10), color=INK)
axs[0].axhline(16, color=BLUE, lw=1.5, ls="--"); axs[0].text(30, 16.4, "16 kW design point", color=BLUE)
fig.suptitle("Second run, straight after the first boil: the used batteries ran out of breath", x=0.01, ha="left",
             color=INK, fontsize=13, fontweight="bold")
fig.tight_layout(); fig.savefig(os.path.join(ROOT, "img", "result_pack_collapse.png"), dpi=150)
print(f"sim same conditions {t_real:.1f} s, sim good {t_good:.1f} s")
