"""Boiler30s sizing + boil-time simulation.

Run: python3 sim/sizing.py   (writes img/boil_sim.png and prints a summary)
All SI units unless noted.
"""
import math
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------- water / target ----------------
M_WATER = 1.0          # kg (1 L)
CP_W = 4186.0          # J/kg/K
T0 = 15.0              # start temp, deg C (cold tap, conservative)
T_BOIL = 100.0
E_WATER = M_WATER * CP_W * (T_BOIL - T0)

# ---------------- heater v2 (IMS aluminium PCB Ø320, JLC: 1 oz Cu, 1 W/mK) ----------------
HEATER_D = 0.269        # Ø of the heated copper zone (heater/heater_numbers.json: 569 cm2)
A_HEAT = math.pi * HEATER_D**2 / 4
FILL = 0.94             # copper fill of the spiral (17.8 mm track, 1 mm gap)
CU_T = 35e-6            # 1 oz
RHO_CU20 = 1.72e-8
ALPHA_CU = 0.00393
DIEL_T = 100e-6         # dielectric thickness (typ. IMS)
DIEL_K = 1.0            # W/mK (JLC)
AL_T = 1.6e-3
AL_K = 200.0
BOARD_D = 0.290         # effective Al disc taking part (wet Ø276 + part of the clamped rim)
C_PLATE = math.pi * BOARD_D**2 / 4 * AL_T * 2700 * 900   # J/K
R20_NOM = 0.0654       # heater resistance at 20 C (heater/heater_numbers.json)

# CNC aluminium ring behind a 1.5 mm silicone liner + gasket: only a few kJ leak into it; lump as extra mass
C_RING = 60.0

# ---------------- sources ----------------
SOURCES = {
    "4x lead-acid, good (5.5 mOhm/batt)": dict(n=4, voc=12.65, r=5.5e-3, pol=0.45, tau=12.0),
    "4x lead-acid, tired (8 mOhm/batt)": dict(n=4, voc=12.5, r=8.0e-3, pol=0.6, tau=12.0),
    "LiPo 12S2P (4x 6S 5Ah, 3 mOhm/cell)": dict(n=12, voc=4.15, r=1.5e-3, pol=0.12, tau=30.0),
}
R_WIRING = 3.0e-3      # 3.3 m of 35 mm2 (1.75 mOhm), contactor, ANL fuse, lugs, busbar clamps

def rohsenow_dT(q):
    """wall superheat (K) for saturated nucleate pool boiling of water at q (W/m2)."""
    mu, hfg, cp, pr, csf = 2.79e-4, 2.257e6, 4217.0, 1.76, 0.013
    k = mu * hfg * math.sqrt(9.81 * (957.9 - 0.6) / 0.0589)
    return (q / k) ** (1 / 3) * csf * hfg * pr / cp

Q_CHF = 0.149 * 2.257e6 * math.sqrt(0.596) * (0.0589 * 9.81 * 957.3) ** 0.25

def q_wall(Tp, Tw):
    """heat flux plate->water (W/m2). natural convection + (sub)cooled nucleate boiling."""
    q_nc = 1500.0 * max(Tp - Tw, 0.0)
    q_nb = 0.0
    if Tp > T_BOIL:
        # invert Rohsenow: q = k*(dT*cp/(csf*hfg*pr))^3
        mu, hfg, cp, pr, csf = 2.79e-4, 2.257e6, 4217.0, 1.76, 0.013
        k = mu * hfg * math.sqrt(9.81 * (957.9 - 0.6) / 0.0589)
        q_nb = k * ((Tp - T_BOIL) * cp / (csf * hfg * pr)) ** 3
    return q_nc + q_nb

def simulate(src, r20=R20_NOM, dt=0.005, tmax=60.0):
    Tw, Tp, t = T0, T0, 0.0
    log = []
    e_bat = 0.0
    while Tw < T_BOIL and t < tmax:
        # trace temperature = plate + dielectric drop (iterate with power)
        Ttr = Tp
        for _ in range(4):
            R = r20 * (1 + ALPHA_CU * (Ttr - 20))
            voc = src["n"] * (src["voc"] - src["pol"] * (1 - math.exp(-t / src["tau"])))
            rs = src["n"] * src["r"] + R_WIRING
            I = voc / (R + rs)
            P = I * I * R
            q_tr = P / (A_HEAT * FILL)
            Ttr = Tp + q_tr * (DIEL_T / DIEL_K + AL_T / AL_K)
        q = q_wall(Tp, Tw)
        Q = q * A_HEAT
        Tp += (P - Q) / C_PLATE * dt
        Tw += (Q - 30.0) / (M_WATER * CP_W + C_RING) * dt
        e_bat += voc * I * dt
        log.append((t, Tw, Tp, Ttr, I, voc - I * rs, P, R))
        t += dt
    return t, np.array(log), e_bat

def main():
    print(f"Energy to heat 1 L {T0:.0f}->100 C : {E_WATER/1e3:.0f} kJ = {E_WATER/3600:.0f} Wh")
    print(f"  -> average heat into water for 30 s: {E_WATER/30/1e3:.1f} kW")
    print(f"Heater zone {HEATER_D*1e3:.0f} mm dia, {A_HEAT*1e4:.0f} cm2; plate C = {C_PLATE:.0f} J/K")
    print(f"Zuber CHF ~ {Q_CHF/1e4:.0f} W/cm2")
    rs_sheet20 = RHO_CU20 / CU_T
    sq = R20_NOM / rs_sheet20
    w = math.sqrt(A_HEAT * FILL / sq)
    print(f"Heater trace: R20={R20_NOM*1e3:.0f} mOhm, 1 oz sheet {rs_sheet20*1e3:.3f} mOhm/sq -> {sq:.0f} squares")
    print(f"  width ~{w*1e3:.1f} mm, length ~{sq*w:.2f} m (bifilar spiral)")
    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    for name, src in SOURCES.items():
        t, L, e = simulate(src)
        print(f"\n[{name}]  t_boil = {t:.1f} s   battery energy {e/3600:.0f} Wh")
        print(f"  I start/avg/end = {L[1,4]:.0f}/{L[:,4].mean():.0f}/{L[-1,4]:.0f} A,"
              f"  P avg {L[:,6].mean()/1e3:.1f} kW, peak {L[:,6].max()/1e3:.1f} kW")
        print(f"  V_bus under load end {L[-1,5]:.1f} V; trace T max {L[:,3].max():.0f} C;"
              f" plate T max {L[:,2].max():.0f} C; q avg {L[:,6].mean()/A_HEAT/1e4:.0f} W/cm2")
        ax[0, 0].plot(L[:, 0], L[:, 1], label=name)
        ax[0, 1].plot(L[:, 0], L[:, 6] / 1e3, label=name)
        ax[1, 0].plot(L[:, 0], L[:, 4], label=name)
        ax[1, 1].plot(L[:, 0], L[:, 3], label=name)
    # sensitivity on copper thickness tolerance (+-20 %) for good lead-acid
    for f in (0.8, 1.2):
        t, L, e = simulate(SOURCES["4x lead-acid, good (5.5 mOhm/batt)"], r20=R20_NOM / f)
        print(f"\nCu thickness x{f}: R20={R20_NOM/f*1e3:.0f} mOhm -> t_boil {t:.1f} s, I peak {L[:,4].max():.0f} A, trace max {L[:,3].max():.0f} C")
    for a, title, yl in ((ax[0, 0], "Water temperature", "deg C"), (ax[0, 1], "Heater power", "kW"),
                         (ax[1, 0], "Current", "A"), (ax[1, 1], "Heater trace temperature", "deg C")):
        a.set_title(title); a.set_ylabel(yl); a.set_xlabel("s"); a.grid(alpha=.3)
    ax[0, 0].axvline(30, color="k", ls="--", lw=.8)
    ax[0, 0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img", "boil_sim.png"), dpi=110)

if __name__ == "__main__":
    main()
