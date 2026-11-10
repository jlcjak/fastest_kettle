"""Boiler30s heater v2: Ø320 aluminium IMS board, bifilar copper spiral, solderless bolted busbar terminals.

Run: python3 boards/heater/gen_heater.py
Writes heater.kicad_pcb / heater.kicad_pro / heater_numbers.json next to this script.
Board centre at (CX, CY); KiCad Y points down. Copper side faces DOWN in the kettle, aluminium side is the wet floor.
"""
import math, os, json
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "heater.kicad_pcb")

# ---------------- geometry (mm) ----------------
CX, CY = 170.0, 170.0
BOARD_R = 160.0            # Ø320 disc
HOLE_R, HOLE_D, N_HOLES = 152.0, 5.5, 24   # M5 clamp bolts through the CNC ring, at k*15 deg
BUS_HOLE_D = 6.5          # the 0 and 180 deg holes take M6 bolts that clamp the busbars (~8 kN each)
POCKET_R = 138.0           # wetted area (CNC ring bore Ø276)
HEAT_EDGE = 135.0          # outermost heated copper edge
G = 1.0                    # gap between turns
CENTRE = "disc"            # "disc": v2 junction disc + round keyholes at the gap ends; "s": wide-radius S-bend
R0_DISC = 35.0             # disc-junction arm start radius
ISLAND_R_DISC = float(os.environ.get("HEATER_ISLAND", 9.0))   # KSD301 copper-free island (cap is Ø15)
CH_Q = float(os.environ.get("HEATER_CHQ", 4.0))   # chamfer meets the lead edge this far inside the busbar pad
KEYHOLE = [(8.0, 0.0, 0.0)]  # [(radius, dr, dtheta_deg)] round reliefs tangent to the arm at each inter-arm gap end
                           # (calc/heater_currentflow.py: centre hot spot 5.1x -> 2.3x average power density)
K_S = 5.0                  # S-bend: arm start radius r0 = K_S * w, semicircle inner radius = r0/2 - w/2 = 2 w
                           # -> current crowding at the S inner edge <= 1.23x (power 1.5x), like the spiral body
CHAMFER_DEG = 12.0         # blend from the arm's outer edge into the terminal lead (kills the re-entrant corner)
R20_TARGET = 0.0654 * 65.4 / 67.3   # ohm at 20 C; analytic estimate calibrated to the 2D current-flow solve (-> 65.4 mOhm)
STEP_DEG = 1.5
CU_T = 35e-3               # 1 oz (mm)
RHO20 = 1.72e-5            # ohm*mm
ALPHA = 0.00393
# terminal (both at the same geometry, A at 0 deg / +X, B at 180 deg / -X)
LEAD_W1 = 36.0             # lead width at the pad
PAD_R0, PAD_R1 = 139.5, 156.0   # exposed contact zone r 139.5-156; pad corner (156, 18) sits 3 mm inside the Al edge (burr margin)
HOLE_PULLBACK = 3.75       # copper clearance around the M5 holes (copper-free radius 6.5 mm)
BUS_PULLBACK = 3.25        # around the M6 busbar holes (copper-free radius 6.5 mm)


if os.environ.get("HEATER_KEYHOLE"):
    KEYHOLE = [tuple(map(float, k.split(","))) for k in os.environ["HEATER_KEYHOLE"].split(";")]


def r0_of(w):
    return K_S * w if CENTRE == "s" else R0_DISC


def spiral_geometry(w):
    r_out = HEAT_EDGE - w / 2
    b = (w + G) / math.pi
    th_max = (r_out - r0_of(w)) / b
    return r_out, b, th_max


def arm(w, phase):
    r_out, b, th_max = spiral_geometry(w)
    rot = -th_max
    pts, th, step = [], 0.0, math.radians(STEP_DEG)
    while True:
        t = min(th, th_max)
        r = r0_of(w) + b * t
        a = t + phase + rot
        pts.append((r * math.cos(a), r * math.sin(a)))
        if t >= th_max:
            break
        th += step
    return pts


def polylen(p):
    return sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1))


def s_bend(w):
    """Two semicircles of radius r0/2 joining arm A's inner end (r0, 0) to arm B's inner end (-r0, 0),
    tangent to both arms, rotated like the arms."""
    r0 = r0_of(w)
    rot = -spiral_geometry(w)[2]
    a = r0 / 2
    pts = []
    n = int(180 / STEP_DEG)
    for k in range(n + 1):           # lower half of the circle centred (a, 0): (r0,0) -> (0,0)
        f = -math.pi * k / n
        pts.append((a + a * math.cos(f), a * math.sin(f)))
    for k in range(1, n + 1):        # upper half of the circle centred (-a, 0): (0,0) -> (-r0,0)
        f = math.pi * k / n
        pts.append((-a + a * math.cos(f), a * math.sin(f)))
    c, s_ = math.cos(rot), math.sin(rot)
    return [(x * c - y * s_, x * s_ + y * c) for x, y in pts]


def resistance(w):
    """R20 estimate: centre (S-bend, or disc ~0.5 sq) + two arms + leads."""
    r_out = spiral_geometry(w)[0]
    lead_sq = 2 * (PAD_R0 - r_out) / ((w + LEAD_W1) / 2)
    if CENTRE == "s":
        sq = (2 * polylen(arm(w, 0.0)) + polylen(s_bend(w))) / w + lead_sq
    else:
        th_detach = math.pi * w / (2 * (w + G))
        n = int(math.degrees(th_detach) / STEP_DEG)
        sq = 2 * polylen(arm(w, 0.0)[n:]) / w + lead_sq + 0.5
    return sq * RHO20 / CU_T, sq


def solve_width():
    lo, hi = 8.0, 30.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if resistance(mid)[0] > R20_TARGET:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 2)


def mm(v):
    return pcbnew.FromMM(v)


def vec(x, y):
    return pcbnew.VECTOR2I(mm(CX + x), mm(CY + y))


def main():
    W = solve_width()
    R20, squares = resistance(W)
    r_out, b, th_max = spiral_geometry(W)
    A = arm(W, 0.0)
    B = arm(W, math.pi)
    R0 = r0_of(W)
    rot = -th_max
    if CENTRE == "s":
        S = s_bend(W)
        ISLAND = ((R0 / 2) * math.cos(rot), (R0 / 2) * math.sin(rot))   # centre of the S's first loop: copper-free
        ISLAND_R = R0 / 2 - W / 2
    else:
        S = []
        ISLAND, ISLAND_R = (0.0, 0.0), ISLAND_R_DISC
    heated = math.pi * HEAT_EDGE ** 2 / 100
    # worst current crowding: inner edge of the S loops, J_in/J_avg = w / (r_in * ln(r_out/r_in))
    r_c = R0 / 2
    crowd = W / ((r_c - W / 2) * math.log((r_c + W / 2) / (r_c - W / 2)))
    # clearance between the S and the arms (centrelines, excluding the joints)
    def mind(p, q):
        return min(math.dist(a_, b_) for a_ in p for b_ in q)
    gap_s = (min(mind(S[len(S)//6: -len(S)//6], A[len(A)//8:]), mind(S[len(S)//6: -len(S)//6], B[len(B)//8:])) - W
             if S else G)
    info = dict(track_width_mm=W, gap_mm=G, r0_mm=round(R0, 1), turns_per_arm=round(th_max / (2 * math.pi), 2),
                s_bend_loop_radius_mm=round(R0 / 2, 1), s_to_arm_min_gap_mm=round(gap_s, 2),
                ksd_island_xy_mm=[round(ISLAND[0], 1), round(ISLAND[1], 1)], ksd_island_radius_mm=round(ISLAND_R, 1),
                squares_estimate=round(squares, 1), R20_estimate_mohm=round(R20 * 1e3, 1),
                R20_mohm=round(R20 * 1e3 * 67.3 / 65.4, 1),   # 2D current-flow corrected (calc/heater_currentflow.py)
                R140_mohm=round(R20 * 67.3 / 65.4 * (1 + ALPHA * 120) * 1e3, 1), heated_area_cm2=round(heated),
                current_density_A_mm2_at_400A=round(400 / (W * CU_T)),
                worst_inner_edge_J_ratio=round(crowd, 2), worst_inner_edge_power_ratio=round(crowd ** 2, 2))
    print(json.dumps(info, indent=1))

    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(1.6))
    ds.SetCopperLayerCount(2)   # KiCad needs >= 2; B.Cu stays empty and isn't plotted (1-layer Al board)
    net = pcbnew.NETINFO_ITEM(board, "HEATER")
    board.Add(net)

    def seg(p0, p1, width):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(vec(*p0)); t.SetEnd(vec(*p1)); t.SetWidth(mm(width)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net)
        board.Add(t)

    assert gap_s > 0.9, f"S-bend too close to the arms ({gap_s:.2f} mm)"
    for poly in (A, B, S):
        for i in range(len(poly) - 1):
            seg(poly[i], poly[i + 1], W)

    def zone(outline, holes=(), clearance=0.5):
        z = pcbnew.ZONE(board)
        z.SetLayer(pcbnew.F_Cu); z.SetNet(net)
        ps = z.Outline()
        ps.NewOutline()
        for x, y in outline:
            ps.Append(mm(CX + x), mm(CY + y))
        for h in holes:
            ps.NewHole()
            for x, y in h:
                ps.Append(mm(CX + x), mm(CY + y), -1, 0)
        z.SetLocalClearance(mm(clearance))
        z.SetMinThickness(mm(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        board.Add(z)
        return z

    def circle(r, n=72, cx=0.0, cy=0.0, rev=False):  # noqa
        pts = [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
        return pts[::-1] if rev else pts


    if CENTRE == "disc":
        # junction disc, KSD island, and round keyholes where the inter-arm gaps end (blunts the sharp crescent tips)
        th_d = W / (2 * b)                        # arm parameter where the arm's inner edge leaves the disc
        def sps(poly):
            q = pcbnew.SHAPE_POLY_SET(); q.NewOutline()
            for x_, y_ in poly:
                q.Append(mm(CX + x_), mm(CY + y_))
            return q
        disc = sps(circle(R0, 144))
        disc.BooleanSubtract(sps(circle(ISLAND_R, 48)))
        for (kr, dr, dth) in KEYHOLE:
            for ph in (0.0, math.pi):
                ang = th_d + rot + ph + math.radians(dth)
                rc = R0 - kr + dr
                disc.BooleanSubtract(sps(circle(kr, 72, cx=rc * math.cos(ang), cy=rc * math.sin(ang))))
        zd = pcbnew.ZONE(board); zd.SetLayer(pcbnew.F_Cu); zd.SetNet(net)
        zd.SetOutline(disc); zd.SetLocalClearance(mm(0.5)); zd.SetMinThickness(mm(0.3))
        zd.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); zd.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
        board.Add(zd)
        fpc = pcbnew.FOOTPRINT(board); fpc.SetReference("J0"); fpc.SetValue("CENTRE"); fpc.Reference().SetVisible(False)
        fpc.Value().SetVisible(False); fpc.SetPosition(vec(0, -(R0 + ISLAND_R) / 2)); board.Add(fpc)
        pc_ = pcbnew.PAD(fpc); pc_.SetAttribute(pcbnew.PAD_ATTRIB_SMD); pc_.SetShape(pcbnew.PAD_SHAPE_RECT)
        pc_.SetSize(pcbnew.VECTOR2I(mm(2), mm(2))); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); pc_.SetLayerSet(ls)
        pc_.SetNumber("1"); pc_.SetNet(net); fpc.Add(pc_); pc_.SetPosition(fpc.GetPosition())

    # leads + terminal zones (copper pulled back around the clamp bolt hole by the zone clearance)
    for sgn in (1, -1):
        x0 = r_out - 2.0
        lead = [(x0, -W / 2), (PAD_R0 - 4, -LEAD_W1 / 2), (PAD_R1, -LEAD_W1 / 2),
                (PAD_R1, LEAD_W1 / 2), (PAD_R0 - 4, LEAD_W1 / 2), (x0, W / 2)]
        lead = [(sgn * x, y) for x, y in lead]
        if sgn < 0:
            lead = lead[::-1]
        # explicit copper-free circle around the clamp bolt (NPTH clearance alone would leave 0.25 mm)
        zone(lead, holes=[circle(BUS_HOLE_D / 2 + BUS_PULLBACK, 48, cx=sgn * HOLE_R, rev=True)])
        # chamfer between the arm's outer edge (the side the arm arrives from) and the lead's edge
        ph = math.radians(CHAMFER_DEG)
        re_ = r_out - b * ph + W / 2 - 0.3
        ri_ = r_out - b * ph - W / 2 + 2.0
        ch = [(ri_ * math.cos(-ph), ri_ * math.sin(-ph)), (re_ * math.cos(-ph), re_ * math.sin(-ph)),
              (PAD_R0 + CH_Q, -LEAD_W1 / 2), (PAD_R0 - 6, -LEAD_W1 / 2 + 6), (r_out - 2, 0.0)]
        ch = [(sgn * x, sgn * y) for x, y in ch]       # B is the point reflection of A
        zone(ch).SetAssignedPriority(1)                 # overlaps the lead zone on purpose (same net)
        # small anchor pad so the zone belongs to a pad (no isolated-copper warning); covered by mask
        fpa = pcbnew.FOOTPRINT(board); fpa.SetReference("T" + ("A" if sgn > 0 else "B")); fpa.SetValue("HEATER_TERMINAL")
        fpa.Reference().SetVisible(False); fpa.Value().SetVisible(False); fpa.SetPosition(vec(sgn * (PAD_R0 - 2), 0)); board.Add(fpa)
        pa = pcbnew.PAD(fpa); pa.SetAttribute(pcbnew.PAD_ATTRIB_SMD); pa.SetShape(pcbnew.PAD_SHAPE_RECT)
        pa.SetSize(pcbnew.VECTOR2I(mm(2), mm(2))); ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); pa.SetLayerSet(ls)
        pa.SetNumber("1"); pa.SetNet(net); fpa.Add(pa); pa.SetPosition(fpa.GetPosition())
        # exposed contact zone (solder-mask opening) where the copper busbar clamps
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_RECT); s.SetLayer(pcbnew.F_Mask)
        s.SetStart(vec(sgn * PAD_R0, -LEAD_W1 / 2 + 0.5)); s.SetEnd(vec(sgn * PAD_R1, LEAD_W1 / 2 - 0.5))
        s.SetFilled(True); s.SetWidth(0); board.Add(s)

    # outline
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetCenter(vec(0, 0)); s.SetEnd(vec(BOARD_R, 0)); s.SetWidth(mm(0.1)); board.Add(s)

    # clamp-bolt holes (NPTH)
    for k in range(N_HOLES):
        a = 2 * math.pi * k / N_HOLES
        fp = pcbnew.FOOTPRINT(board)
        fp.SetReference(f"H{k+1}"); fp.SetValue("M5"); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        fp.SetPosition(vec(HOLE_R * math.cos(a), HOLE_R * math.sin(a)))
        board.Add(fp)
        p = pcbnew.PAD(fp)
        p.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        d = BUS_HOLE_D if k in (0, N_HOLES // 2) else HOLE_D
        p.SetSize(pcbnew.VECTOR2I(mm(d), mm(d))); p.SetDrillSize(pcbnew.VECTOR2I(mm(d), mm(d)))
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); ls.AddLayer(pcbnew.F_Mask)
        p.SetLayerSet(ls); p.SetNumber("")
        fp.Add(p); p.SetPosition(fp.GetPosition())

    # silkscreen
    def text(t_, x, y, size=3.0):
        t = pcbnew.PCB_TEXT(board); t.SetText(t_); t.SetPosition(vec(x, y)); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(size * 0.15)); board.Add(t)

    text("KSD301", ISLAND[0], ISLAND[1] - 11.5, 1.8)
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetLayer(pcbnew.F_SilkS)
    s.SetCenter(vec(*ISLAND)); s.SetEnd(vec(ISLAND[0] + 8, ISLAND[1])); s.SetWidth(mm(0.25)); board.Add(s)
    import silk_art
    silk_art.add_art(board, vec, mm, A, B, HOLE_R, N_HOLES)
    for sgn in (1, -1):  # busbar footprint 40 x 6 mm copper, r 139..189
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_RECT); s.SetLayer(pcbnew.F_Fab)
        s.SetStart(vec(sgn * 139, -20)); s.SetEnd(vec(sgn * 189, 20)); s.SetWidth(mm(0.2)); board.Add(s)
    for r in (POCKET_R,):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_CIRCLE); s.SetLayer(pcbnew.User_1)
        s.SetCenter(vec(0, 0)); s.SetEnd(vec(r, 0)); s.SetWidth(mm(0.2)); board.Add(s)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(OUT)
    with open(os.path.join(HERE, "heater.kicad_pro"), "w") as f:
        json.dump({"meta": {"filename": "heater.kicad_pro", "version": 1}}, f)
    with open(os.path.join(HERE, "heater_numbers.json"), "w") as f:
        json.dump(info, f, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
