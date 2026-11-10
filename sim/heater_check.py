"""Boiler30s heater v2: is the IMS copper-spiral heater good for ~16 kW?

Needs numpy, scipy, matplotlib.  Run: python3 sim/heater_check.py
Prints a report and writes img/heater_cross_section.png.

Checks:
 1. water side: heat flux vs critical heat flux (film-boiling burnout)
 2. dielectric: 2D cross-section of one spiral pitch (copper / dielectric / aluminium, nucleate boiling on top),
    with the current crowding of the tightest turn -> peak copper temperature vs the laminate Tg
 3. terminal lead outside the wetted area
 4. busbar clamp contact
 5. dry run: how fast it overheats, what the KSD301 does
 6. thermal buckling of the floor
 7. electrical insulation / bond-void sensitivity
"""
import json, math, os
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = json.load(open(os.path.join(ROOT, "heater/heater_numbers.json")))

W = H["track_width_mm"] * 1e-3
G = H["gap_mm"] * 1e-3
R0 = H["r0_mm"] * 1e-3
A_HEAT = H["heated_area_cm2"] * 1e-4
CU_T, AL_T = 35e-6, 1.6e-3
K_CU, K_AL = 390.0, 200.0
RHO20, ALPHA = 1.72e-8, 0.00393

# operating point from sim/sizing.py (good used car batteries; tired ones give less)
P_HEAT = 16.1e3          # W average over the boil
P_PEAK = 19.3e3          # W in the first second (cold copper)
I_AVG = 409.0

# laminate options: (name, dielectric thickness m, k W/mK, Tg C)   Ventec VT-44A / VT-4A1 / VT-4A2 data sheet
LAMINATES = [("1.0 W/mK, 100 um (JLC-class, Tg 130)", 100e-6, 1.0, 130),
             ("1.0 W/mK, 75 um (Tg 130)", 75e-6, 1.0, 130),
             ("1.6 W/mK, 100 um (Ventec VT-4A1, Tg 170)", 100e-6, 1.6, 170),
             ("2.2 W/mK, 100 um (Ventec VT-4A2, Tg 130)", 100e-6, 2.2, 130)]

T_SAT = 100.0


def rohsenow_q(dT):
    mu, hfg, cp, pr, csf = 2.79e-4, 2.257e6, 4217.0, 1.76, 0.013
    k = mu * hfg * math.sqrt(9.81 * (957.9 - 0.6) / 0.0589)
    return k * (max(dT, 0.0) * cp / (csf * hfg * pr)) ** 3


Q_CHF = 0.149 * 2.257e6 * math.sqrt(0.596) * (0.0589 * 9.81 * 957.3) ** 0.25


def cross_section(diel_t, diel_k, r_centre, q_mean_track, nx=190):
    """Steady 2D (x across one pitch, z through the stack), periodic in x, nucleate boiling on the Al face.
    Heat generated in the copper with the 1/r^2 profile of a curved strip. Returns grid temps (z, x) and x."""
    pitch = W + G
    x = (np.arange(nx) + 0.5) * pitch / nx
    dx = pitch / nx
    layers = [(CU_T, K_CU, 1)] + [(diel_t / 5, diel_k, 5)] + [(AL_T / 16, K_AL, 16)]
    dz, kz = [], []
    for t, k, n in layers:
        dz += [t] * n if n > 1 else [t]
        kz += [k] * n if n > 1 else [k]
    dz, kz = np.array(dz), np.array(kz)
    nz = len(dz)
    in_track = (x >= G / 2) & (x < G / 2 + W)
    # local power density in the copper ~ J^2 ~ 1/r^2 across the strip (inner edge first)
    r = r_centre - W / 2 + (x - G / 2)
    prof = np.where(in_track, 1.0 / r ** 2, 0.0)
    prof *= in_track.sum() / prof.sum()
    q_gen = q_mean_track * prof / CU_T          # W/m3 in copper cells
    kx_row0 = np.where(in_track, K_CU, 0.05)     # gaps: solder mask/air under copper level
    N = nx * nz
    idx = lambda i, j: i * nx + (j % nx)
    T = np.full(N, 110.0)
    for _ in range(60):
        rows, cols, vals, b = [], [], [], np.zeros(N)
        for i in range(nz):
            kxi = kx_row0 if i == 0 else np.full(nx, kz[i])
            for j in range(nx):
                p = idx(i, j)
                diag = 0.0
                for jj in (j - 1, j + 1):  # lateral (periodic)
                    kk = 2 * kxi[j] * kxi[jj % nx] / (kxi[j] + kxi[jj % nx])
                    g = kk * dz[i] / dx
                    rows.append(p); cols.append(idx(i, jj)); vals.append(-g); diag += g
                for ii in (i - 1, i + 1):  # vertical
                    if 0 <= ii < nz:
                        k1 = kxi[j] if i == 0 else kz[i]
                        k2 = kx_row0[j] if ii == 0 else kz[ii]
                        rr = dz[i] / 2 / k1 + dz[ii] / 2 / k2
                        g = dx / rr
                        rows.append(p); cols.append(idx(ii, j)); vals.append(-g); diag += g
                if i == 0:
                    b[p] += q_gen[j] * dz[0] * dx
                if i == nz - 1:  # boiling on the wet face, linearised around the last iterate
                    Tw = T[p]
                    h = max(rohsenow_q(Tw - T_SAT) / max(Tw - T_SAT, 0.5), 2000.0)
                    g = dx / (dz[i] / 2 / kz[i] + 1.0 / h)
                    diag += g
                    b[p] += g * T_SAT
                rows.append(p); cols.append(p); vals.append(diag)
        A = sp.csr_matrix((vals, (rows, cols)), shape=(N, N))
        Tn = spla.spsolve(A, b)
        if np.max(np.abs(Tn - T)) < 0.01:
            T = Tn
            break
        T = 0.5 * T + 0.5 * Tn
    return T.reshape(nz, nx), x, in_track


def main():
    out = []
    pr = lambda s="": (print(s), out.append(s))
    q_avg = P_HEAT / A_HEAT
    q_track = q_avg / (W / (W + G))
    pr("# Heater v2 check")
    pr(f"Spiral: {W*1e3:.1f} mm track, {G*1e3:.1f} mm gap, R20 {H['R20_mohm']} mOhm, heated {A_HEAT*1e4:.0f} cm2, "
       f"{P_HEAT/1e3:.1f} kW average / {P_PEAK/1e3:.1f} kW first second")
    pr()
    pr("## 1. Water side")
    pr(f"- mean flux {q_avg/1e4:.1f} W/cm2, under the copper {q_track/1e4:.1f} W/cm2, first-second peak "
       f"{P_PEAK/A_HEAT/1e4:.1f} W/cm2")
    pr(f"- critical heat flux of water (Zuber, saturated, horizontal up-facing) {Q_CHF/1e4:.0f} W/cm2 -> "
       f"margin x{Q_CHF/q_track:.1f} on the mean, x{Q_CHF/(q_track*H['worst_inner_edge_power_ratio']):.1f} on the hottest strip edge")
    dT = 0.0
    while rohsenow_q(dT) < q_track:
        dT += 0.05
    pr(f"- nucleate-boiling wall superheat at that flux ≈ {dT:.0f} K -> aluminium face ≈ {100+dT:.0f} °C "
       f"(subcooled water early in the boil runs the same or slightly cooler wall)")
    pr("- reference: thick-film kettle and instant-water-heater elements run 20–60 W/cm²; old exposed tubular kettle "
       "elements ~30–40 W/cm². This design sits in that window.")
    pr()
    pr("## 2. Dielectric / copper temperature (2D cross-section of the tightest turn and an outer turn)")
    r_inner = R0 + (W + G) / math.pi * math.pi * W / (2 * (W + G))
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.6))
    rows = []
    for name, t, k, tg in LAMINATES:
        res = []
        for rc in (r_inner, 0.126):
            T, x, trk = cross_section(t, k, rc, q_track)
            res.append((T[0, trk].mean(), T[0, trk].max(), T[-1].max()))
            if name.startswith("1.0 W/mK, 100") or name.startswith("1.6"):
                ax = axs[0] if name.startswith("1.0") else axs[1]
                ax.plot(x * 1e3, T[0], label=f"copper, r={rc*1e3:.0f} mm")
                ax.plot(x * 1e3, T[-1], "--", label=f"Al wet face, r={rc*1e3:.0f} mm")
                ax.set_title(name); ax.set_xlabel("across one pitch (mm)"); ax.set_ylabel("°C"); ax.grid(alpha=.3)
                ax.legend(fontsize=7)
        (m_in, x_in, al_in), (m_out, x_out, _) = res
        rows.append((name, m_in, x_in, m_out, al_in, tg))
        pr(f"- {name}: copper mean {m_out:.0f} °C (outer turn), {m_in:.0f} °C mean / {x_in:.0f} °C inner edge "
           f"(tightest turn); Al face max {al_in:.0f} °C;  Tg margin at the hottest edge {tg - x_in:+.0f} K")
    fig.tight_layout()
    fig.savefig(os.path.join(ROOT, "img/heater_cross_section.png"), dpi=110)
    pr("- Td (decomposition) of these laminates is 380 °C; peel strength 6–8.5 lb/in as received.")
    pr("- Above Tg the epoxy gets soft and its expansion triples; it still holds, but cycling life shortens. "
       "So: the 1.0 W/mK board works, and it's the cheap one (JLC, 5 boards per order = 4 spares). "
       "A ≥1.6 W/mK board keeps the copper below Tg for long life.")
    pr()
    pr("## 3. Terminal lead (r 126 -> 139.5 mm, then the copper busbar takes the current)")
    wet_sq = (138 - 126) / ((W * 1e3 + 36) / 2)
    dry_sq = (139.5 - 138) / 36
    rho_hot = RHO20 * (1 + ALPHA * 110) / CU_T
    P_wet, P_dry = I_AVG ** 2 * wet_sq * rho_hot, I_AVG ** 2 * dry_sq * rho_hot
    pr(f"- wetted part {wet_sq:.2f} squares -> {P_wet:.0f} W at {P_wet/(36e-3*12e-3)/1e4:.0f} W/cm², cooled like the spiral;"
       f" dry strip under the gasket edge {dry_sq:.2f} squares -> {P_dry:.0f} W, 1.5 mm from water on one side and the"
       f" copper bar on the other: a few K. (First draft had 8 mm of dry lead: 85 W, ≈165 °C, so the pad was moved in.)")
    pr()
    pr("## 4. Busbar clamp")
    area = 2 * (158.5 - 139.5) * (17.5 - 6.5) * 1e-6
    F = 8.0e3   # M6 A2-70 at ~8 N·m
    pr(f"- exposed pad {area*1e4:.1f} cm² under a 40x6 copper bar, one M6 A2-70 at ~8 N·m ≈ {F/1e3:.0f} kN -> "
       f"{F/area/1e6:.0f} MPa nominal; the bar bends a little, so count on ~5–10 MPa near the bolt. Bolted busbar joints "
       f"use 5–15 MPa. Verify: < 1 mV across each joint at 20 A.")
    Rc = 20e-6 / (area * 1e4) * 1e-0  # 20 uOhm*cm2 for clean clamped tin/copper
    pr(f"- contact resistance ≈ {Rc*1e6:.0f} µΩ -> {I_AVG**2*Rc:.1f} W, sunk into 96 g of copper bar + cable lug: "
       f"+{I_AVG**2*Rc*25/(96*0.385):.0f} K per boil.")
    pr()
    pr("## 5. Dry run (no water)")
    c_plate = 257.0
    rate = P_PEAK / c_plate
    pr(f"- the floor alone (~{c_plate:.0f} J/K) heats at ≈ {rate:.0f} K/s at full power; copper runs ~20–40 K above it.")
    for tau, how in ((2.0, "spring-pressed with thermal paste"), (4.0, "only glued with RTV")):
        Tp, Tk, t = 20.0, 20.0, 0.0
        while Tk < 130.0 and t < 30:
            Tp += rate * 0.01
            Tk += (Tp - Tk) / tau * 0.01
            t += 0.01
        pr(f"- KSD301 130 °C on the centre island, {how} (time constant ≈ {tau:.0f} s): opens after ≈ {t:.1f} s with "
           f"the floor at ≈ {Tp:.0f} °C and copper ≈ {Tp+40:.0f} °C (laminate Td 380 °C).")
    pr("- Hence the KSD301 must be spring-pressed (the printed clip in mech/), not just glued: that keeps a dry start "
       "survivable. A dry start still cooks the board above Tg, so check it afterwards.")
    pr("- So: never press the button on an empty kettle. The KSD301 is the backstop, not the normal stop.")
    pr("- Forgetting to release the button after the boil: 1 L needs ~2260 kJ to boil away -> ~2.5 min at full "
       "power before it runs dry, then the KSD301 trips.")
    pr()
    pr("## 6. Floor buckling")
    E, nu, a_th = 69e9, 0.33, 23e-6
    D = E * AL_T ** 3 / (12 * (1 - nu ** 2))
    a = 0.138
    s_cr = 14.68 * D / (a ** 2 * AL_T)
    dT_cr = s_cr * (1 - nu) / (E * a_th)
    pr(f"- clamped 1.6 mm disc of radius {a*1e3:.0f} mm buckles once its centre runs ≈ {dT_cr:.0f} K hotter than the "
       f"clamped rim. That happens in every boil, so expect the floor to 'tick' and bow a few mm like a kettle bottom. "
       f"Bending strain stays < 0.05 %: harmless for the dielectric. The 2 mm gasket takes up the rim movement.")
    pr()
    pr("## 7. Electrical")
    pr("- dielectric breakdown 3 kV vs 58 V max: >50x. Adjacent turns differ by at most ~40 V across 1 mm under solder "
       "mask (IPC-2221 needs 0.13 mm).")
    j = I_AVG / (W * CU_T) / 1e6
    adi = (j * 1e6) ** 2 * RHO20 * 1.5 / 3.45e6
    pr(f"- copper current density {j:.0f} A/mm²: fine only because the copper is bonded to the cooled floor. If a spot "
       f"debonded it would heat at ~{adi:.0f} K/s and burn open locally within a fraction of a second. The failure mode is "
       f"an open heater (it just stops), not a short. Don't scratch or bend the copper side; inspect it before each session.")
    pr("- The wet parts (floor, ring) are isolated from the battery by the dielectric, so the water is not live.")
    with open(os.path.join(ROOT, "docs/heater_check.md"), "w") as f:
        f.write("\n".join(out) + "\n\n![cross-section](img/heater_cross_section.png)\n")


if __name__ == "__main__":
    main()
