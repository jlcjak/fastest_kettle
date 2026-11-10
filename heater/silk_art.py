"""Silkscreen artwork for the Boiler30s heater (copper side, black silk on white mask).

Called from gen_heater.py. Everything stays off the exposed busbar pads (|y| <= 20 for |x| >= 136), off the holes
(r 152) and off the KSD301 bar footprint (the 45 deg diagonal y = x, 20 mm wide; KiCad y points down).
"""
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sim"))

W_LINE = 0.25          # mm, general silk line width (JLC min 0.15)


def add_art(board, vec, mm, arm_a, arm_b, hole_r, n_holes):
    def seg(p0, p1, w=W_LINE):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(vec(*p0)); s.SetEnd(vec(*p1)); s.SetWidth(mm(w)); s.SetLayer(pcbnew.F_SilkS)
        board.Add(s)

    def poly(pts, w=W_LINE, filled=False, closed=True):
        if filled:
            s = pcbnew.PCB_SHAPE(board)
            s.SetShape(pcbnew.SHAPE_T_POLY)
            s.SetPolyPoints([vec(*p) for p in pts])
            s.SetFilled(True); s.SetWidth(mm(w)); s.SetLayer(pcbnew.F_SilkS)
            board.Add(s)
            return
        q = pts + [pts[0]] if closed else pts
        for i in range(len(q) - 1):
            seg(q[i], q[i + 1], w)

    def text(t_, x, y, h=3.0, angle=0.0, bold=0.15, just=0):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(t_); t.SetPosition(vec(x, y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(h), mm(h))); t.SetTextThickness(mm(max(0.15, h * bold)))
        t.SetTextAngleDegrees(angle)
        if just < 0:
            t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        elif just > 0:
            t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
        board.Add(t)

    def circle(cx, cy, r, w=W_LINE):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetCenter(vec(cx, cy)); s.SetEnd(vec(cx + r, cy))
        s.SetWidth(mm(w)); s.SetLayer(pcbnew.F_SilkS)
        board.Add(s)

    # ---------------- rim: text running round the board + a tick ring ----------------
    def ring_text(msg, r, a0, a1, h, top=True):
        """Lay msg along the circle radius r between angles a0..a1 (deg, screen coords, y down).
        top arc reads clockwise (letters' tops outward), bottom arc reads counter-clockwise (tops inward)."""
        step = math.degrees(h * 0.92 / r)
        span = step * (len(msg) - 1)
        mid = (a0 + a1) / 2
        for i, ch in enumerate(msg):
            if ch == " ":
                continue
            if top:
                phi = mid - span / 2 + i * step
                ang = -(phi + 90)
            else:
                phi = mid + span / 2 - i * step
                ang = 90 - phi
            p = math.radians(phi)
            text(ch, r * math.cos(p), r * math.sin(p), h, ang, bold=0.16)

    ring_text("BOILER30S  ·  1 LITRE  ·  15 → 100 °C  ·  UNDER 30 SECONDS  ·  16 kW  ·  48 V  ·  400 A",
              141.2, -162, -18, 3.0, top=True)
    ring_text("DANGER: HOT >150 °C  ·  NEVER RUN DRY  ·  SELV ≤ 60 V DC  ·  THIS SIDE FACES DOWN",
              142.6, 162, 18, 3.0, top=False)

    # bezel tick ring outside the bolt circle (r 155.5..157.8, edge at 160); long ticks halfway between holes
    for k in range(120):
        a = k * 3.0
        off = a % 15.0
        if off < 2.9 or off > 12.1:          # keep clear of the bolt holes (hole edge at r 154.75)
            continue
        if min(abs(a - 0), abs(a - 360), abs(a - 180)) < 14:   # keep clear of the busbars
            continue
        r0 = 155.6 if abs(off - 7.5) < 0.1 else 156.4
        p = math.radians(a)
        seg((r0 * math.cos(p), r0 * math.sin(p)), (157.8 * math.cos(p), 157.8 * math.sin(p)), 0.22)

    # ---------------- terminals: polarity ----------------
    for sgn, sym, lab in ((1, "+", "BAT +"), (-1, "-", "BAT -")):
        x = sgn * 141.5
        circle(x, 30.5, 5.2, 0.3)
        text(sym, x, 30.5, 6.0, bold=0.2)
        text(lab, sgn * 128.5, 30.5, 2.6, bold=0.16)
        text("400 A", sgn * 128.5, 35.0, 2.0)
        # little lightning bolt
        bx, by = sgn * 152.0, -30.0
        bolt = [(0, -6), (-2.5, 0.5), (0, 0.5), (-1.5, 6), (2.8, -1.2), (0.3, -1.2), (2.0, -6)]
        poly([(bx + u, by + v) for u, v in bolt], 0.15, filled=True)

    # ---------------- current-flow chevrons along both arms ----------------
    def chevrons(arm, reverse):
        n = len(arm)
        for frac in (0.18, 0.38, 0.58, 0.78, 0.94):
            i = int(frac * (n - 2))
            (x0, y0), (x1, y1) = arm[i], arm[i + 1]
            dx, dy = x1 - x0, y1 - y0
            L = math.hypot(dx, dy) or 1.0
            ux, uy = dx / L, dy / L
            if reverse:
                ux, uy = -ux, -uy
            nx, ny = -uy, ux
            cx, cy = arm[i]
            s = 2.2
            tip = (cx + ux * s, cy + uy * s)
            seg((cx - ux * s + nx * s, cy - uy * s + ny * s), tip, 0.35)
            seg((cx - ux * s - nx * s, cy - uy * s - ny * s), tip, 0.35)

    # ---------------- left: mini wiring schematic ----------------
    ox, oy = -112.0, -8.0
    def bat(x, y):
        seg((x, y - 3.5), (x, y + 3.5), 0.35); seg((x + 1.6, y - 2.0), (x + 1.6, y + 2.0), 0.6)
    for i in range(4):
        bat(ox + i * 5.5, oy)
        if i < 3:
            seg((ox + i * 5.5 + 1.6, oy), (ox + (i + 1) * 5.5, oy), 0.2)
    text("4 x 12 V", ox + 8.0, oy - 6.5, 2.0)
    x = ox + 3 * 5.5 + 1.6
    seg((x, oy), (x + 6, oy), 0.25)
    # fuse
    poly([(x + 6, oy - 1.4), (x + 14, oy - 1.4), (x + 14, oy + 1.4), (x + 6, oy + 1.4)], 0.25)
    seg((x + 6, oy), (x + 14, oy), 0.15)
    text("500 A", x + 10, oy - 4.0, 1.6)
    seg((x + 14, oy), (x + 18, oy), 0.25)
    # contactor contact
    circle(x + 18.6, oy, 0.6, 0.25); circle(x + 25.4, oy, 0.6, 0.25)
    seg((x + 19.2, oy - 0.2), (x + 25.0, oy - 3.0), 0.25)
    text("K1", x + 22, oy - 5.5, 1.6)
    seg((x + 26.0, oy), (x + 30, oy), 0.25)
    # heater (zig-zag)
    zz = [(x + 30, oy)] + [(x + 31 + i * 1.6, oy + (2.0 if i % 2 == 0 else -2.0)) for i in range(7)] + [(x + 42.5, oy)]
    poly(zz, 0.25, closed=False)
    text("65 mΩ", x + 36.5, oy - 4.5, 1.6)
    # return line
    seg((x + 42.5, oy), (x + 44, oy), 0.25); seg((x + 44, oy), (x + 44, oy + 7), 0.25)
    seg((x + 44, oy + 7), (ox, oy + 7), 0.25); seg((ox, oy + 7), (ox, oy + 3.5), 0.25)
    # push button + KSD301 driving K1
    text("hold button  →  K1  →  15 kW", ox + 22, oy + 12.0, 1.8)
    text("KSD301 130 °C cuts K1 if dry", ox + 22, oy + 15.5, 1.8)

    # ---------------- right: numbers ----------------
    rx, ry = 92.0, -12.0
    for i, line in enumerate(("2.7 m of copper, 133 squares",
                              "65 mΩ cold  /  96 mΩ hot",
                              "28 W/cm² into the water",
                              "copper ~145 °C, floor ~113 °C",
                              "dielectric 3 kV, 1 W/mK")):
        text(line, rx, ry + i * 4.2, 2.0)

    # ---------------- logo block (above centre) ----------------
    text("BOILER30S", 0, -74, 9.0, bold=0.17)
    text("1 L  ·  30 s  ·  16 kW", 0, -63.5, 3.6, bold=0.15)
    # water drop (left) with steam
    dx0, dy0 = -60.0, -73.0
    drop = []
    for k in range(25):
        t = math.pi * k / 24
        drop.append((dx0 + 4.2 * math.cos(t + math.pi), dy0 + 2.0 + 4.2 * math.sin(t)))
    drop = [(dx0 - 4.2, dy0 + 2.0)] + drop[1:] + [(dx0 + 4.2, dy0 + 2.0), (dx0, dy0 - 7.5)]
    poly(drop, 0.2, filled=True)
    for j in (-3.5, 0.0, 3.5):
        wave = [(dx0 + j + 0.9 * math.sin(v * 1.6), dy0 - 9.5 - v) for v in [i * 0.5 for i in range(9)]]
        poly(wave, 0.3, closed=False)
    # lightning (right)
    bx, by = 60.0, -74.0
    bolt = [(0, -7.5), (-3.2, 0.6), (0, 0.6), (-2.0, 7.5), (3.6, -1.5), (0.4, -1.5), (2.6, -7.5)]
    poly([(bx + u, by + v) for u, v in bolt], 0.15, filled=True)

    # ---------------- boil curve graph (below centre) ----------------
    gx0, gx1, gy_top, gy_bot = -34.0, 34.0, 58.0, 90.0          # plot box (screen y down)
    t_max, T_lo, T_hi = 32.0, 10.0, 105.0
    X = lambda t_: gx0 + (gx1 - gx0) * t_ / t_max
    Y = lambda T_: gy_bot - (gy_bot - gy_top) * (T_ - T_lo) / (T_hi - T_lo)
    seg((gx0, gy_bot), (gx1, gy_bot), 0.25)
    seg((gx0, gy_bot), (gx0, gy_top), 0.25)
    for t_ in (0, 10, 20, 30):
        seg((X(t_), gy_bot), (X(t_), gy_bot + 1.2), 0.2)
        text(f"{t_}", X(t_), gy_bot + 3.2, 1.8)
    for T_ in (20, 60, 100):
        seg((gx0 - 1.2, Y(T_)), (gx0, Y(T_)), 0.2)
        text(f"{T_}", gx0 - 4.6, Y(T_), 1.8)
    text("s", gx1 + 2.4, gy_bot + 3.2, 1.8)
    text("°C", gx0 - 4.6, gy_top - 3.0, 1.8)
    # 100 C line, dashed
    t_ = 0.0
    while t_ < t_max:
        seg((X(t_), Y(100)), (X(min(t_ + 0.9, t_max)), Y(100)), 0.15)
        t_ += 1.8
    # simulated curves (sim/sizing.py): good and tired used car batteries
    try:
        import sizing
        for name, lw in (("4x lead-acid, good (5.5 mOhm/batt)", 0.45), ("4x lead-acid, tired (8 mOhm/batt)", 0.25)):
            tb, L, _ = sizing.simulate(sizing.SOURCES[name])
            pts = [(float(X(r[0])), float(Y(r[1]))) for r in L[::200]] + [(float(X(tb)), float(Y(100.0)))]
            poly(pts, lw, closed=False)
            text(f"{tb:.0f} s", float(X(tb)), float(Y(100.0)) - 2.6, 1.8)
    except Exception as e:                                            # never let art break the board
        print("silk_art: boil curve skipped:", e)
    text("simulated boil, 1 L from 15 °C", 0, gy_bot + 7.0, 2.0)

    # ---------------- warning + spec blocks ----------------
    tri = [(-36.0, 111.0), (-30.0, 100.5), (-24.0, 111.0)]
    poly(tri, 0.45)
    text("!", -30.0, 107.5, 5.0, bold=0.2)
    text("HOT COPPER >150 °C", -20.0, 103.5, 3.0, just=-1)
    text("NEVER POWER WITHOUT WATER", -20.0, 108.8, 3.0, just=-1)
    text("rev 2.2  ·  2026-10  ·  R20 ≈ 65 mΩ  ·  1 oz Cu / 1.6 mm Al IMS", 0, -101.0, 2.2)
    text("bifilar spiral  ·  2 x 2.4 turns  ·  18 mm track", 0, -96.5, 2.2)
