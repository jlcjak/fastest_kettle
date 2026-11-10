# Boiler30s v3 - heater terminals (replaces busbar.py): a 35 mm2 M8 tube lug (lug_35_m8.py) bolted straight onto each
# heater pad at 0 deg (A) and 180 deg (B), r152, through the board's D6.5 hole.
# Stack bottom -> top: M6x25 A2-70 socket head, D18 washer, nylon/PTFE shoulder washer (flange D13 x 1.5 on the lug palm,
# sleeve D8 x 2.5 inside the lug's D8.4 hole, 0.5 mm short of the board), lug palm flat on the pad, board, 30x14x5 steel
# backing plate on the Al face, DIN 125 washer, M6 nut, 8 N.m.
# The shoulder washer is the only thing keeping the bolt (and through it the aluminium core and the other terminal)
# off the lug: never assemble without it.
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from cadlib import *
from kettle_params import *
import builtins as _b
_prev = getattr(_b, 'BOILER_ASM', False); _b.BOILER_ASM = True
import lug_35_m8 as LUG          # import without running its main
_b.BOILER_ASM = _prev

# ---------------- parameters (mm) ----------------
R           = TERM_R                         # 152
CABLE_STUB_L = 70.0
A2          = (0.66, 0.67, 0.70)
NYLON       = (0.95, 0.95, 0.92)
STEEL       = (0.45, 0.46, 0.50)
Z_LUG       = Z_CU                           # lug palm top face on the copper pad
Z_FLANGE_TOP = Z_LUG - LUG_PALM_T            # -3
Z_BEAR      = Z_FLANGE_TOP - SHOULDER_FLANGE_T - M6_WASHER_T   # -6.1 bolt head bearing face


def hexagon(af, h, x, y, z0):
    r = af / math.sqrt(3)
    return prism_xy([(x + r * math.cos(math.radians(30 + 60 * i)), y + r * math.sin(math.radians(30 + 60 * i))) for i in range(6)], z0, z0 + h)


def rot(s, a):
    s = s.copy(); s.rotate(V(0, 0, 0), V(0, 0, 1), a); return s


def shoulder_washer(a):
    z0 = Z_FLANGE_TOP - SHOULDER_FLANGE_T
    s = cyl(SHOULDER_FLANGE_D / 2, SHOULDER_FLANGE_T, R, 0, z0).fuse(cyl(SHOULDER_SLEEVE_OD / 2, SHOULDER_SLEEVE_L, R, 0, Z_FLANGE_TOP))
    return rot(s.cut(cyl(SHOULDER_ID / 2, 20, R, 0, z0 - 1)), a)


def backing_plate(a):
    p = box(R - BP_RAD / 2, -BP_TANG / 2, Z_AL, R + BP_RAD / 2, BP_TANG / 2, Z_AL + BP_T)
    try:
        p = p.makeChamfer(0.5, [e for e in p.Edges if abs(e.BoundBox.ZLength) < 1e-6])
    except Exception:
        pass
    return rot(p.cut(cyl(BP_HOLE_D / 2, 20, R, 0, -5)), a)


def stack_length():
    return M6_WASHER_T + SHOULDER_FLANGE_T + LUG_PALM_T + HB_T + BP_T + M6_WASHER_T + M6_NUT_H


def parts():
    """dict name -> (shape, colour) for both terminals."""
    out = {}
    bolts, wbig, wtop, nuts, plates, sw = [], [], [], [], [], []
    for a in TERM_ANG:
        bolts.append(rot(cyl(M6_HEAD_D / 2, M6_HEAD_H, R, 0, Z_BEAR - M6_HEAD_H).fuse(cyl(3.0, M6_BOLT_L, R, 0, Z_BEAR)), a))
        wbig.append(rot(cyl(M6_WASHER_BIG_D / 2, M6_WASHER_T, R, 0, Z_BEAR).cut(cyl(3.2, 5, R, 0, Z_BEAR - 1)), a))
        sw.append(shoulder_washer(a))
        plates.append(backing_plate(a))
        zt = Z_AL + BP_T
        wtop.append(rot(cyl(M6_WASHER_D / 2, M6_WASHER_T, R, 0, zt).cut(cyl(3.2, 5, R, 0, zt - 1)), a))
        nuts.append(rot(hexagon(M6_NUT_AF, M6_NUT_H, R, 0, zt + M6_WASHER_T).cut(cyl(3.0, 10, R, 0, zt)), a))
    out['m6x25_terminal_bolts'] = (fuse_all(bolts), A2)
    out['m6_washers_d18'] = (fuse_all(wbig), A2)
    out['shoulder_washers'] = (fuse_all(sw), NYLON)
    out['backing_plates_steel'] = (fuse_all(plates), STEEL)
    out['m6_top_washers'] = (fuse_all(wtop), A2)
    out['m6_nuts'] = (fuse_all(nuts), A2)
    for a, n in zip(TERM_ANG, ('A', 'B')):
        out['lug_35_m8_' + n] = (LUG.placed(a, R, Z_LUG), LUG.TINNED)
    cab = []
    for a in TERM_ANG:
        m = LUG.mouth_point(a, R, Z_LUG)
        d = polar(1, a)
        cab.append(Part.makeCylinder(CABLE_D / 2, CABLE_STUB_L, m, V(d.x, d.y, 0)))
    out['cable_A_pos'] = (cab[0], (0.75, 0.08, 0.06))
    out['cable_B_neg'] = (cab[1], (0.05, 0.05, 0.05))
    return out


def build():
    return [(n, s, c) for n, (s, c) in parts().items()]


def checks(items):
    d = dict((n, s) for n, s, *_ in items)
    import builtins; builtins.BOILER_ASM = True
    import cake_ring, heater_board
    seal = cake_ring.build_sealant()
    board = cyl(HB_R, HB_T, z=0)
    bolts = d['m6x25_terminal_bolts']
    L = stack_length()
    log('stack (head bearing face to nut top) %.1f mm -> M6x20 protrudes %.1f, M6x25 protrudes %.1f mm' % (L, 20 - L, M6_BOLT_L - L))
    for n in ('A', 'B'):
        lug = d['lug_35_m8_' + n]
        log('lug %s: M6 shank to lug bore %.2f mm (>= 1), D18 washer to lug %.2f mm (flange), bolt overlap %.3f, lug to board-edge region %.2f' % (
            n, lug.distToShape(bolts)[0], lug.distToShape(d['m6_washers_d18'])[0], overlap(lug, bolts),
            lug.distToShape(board)[0]))
    log('shoulder sleeve top z %.1f (board copper face z 0): gap %.1f mm' % (Z_FLANGE_TOP + SHOULDER_SLEEVE_L, -(Z_FLANGE_TOP + SHOULDER_SLEEVE_L)))
    log('backing plates to sealant fillet %.2f mm (>= 1)' % d['backing_plates_steel'].distToShape(seal)[0])
    lug = d['lug_35_m8_A']
    log('lug barrel start r %.1f vs board edge r %.0f; lug highest z %.2f' % (R + LUG.PALM_L_OUT + LUG.NECK_L, HB_R, lug.BoundBox.ZMax))


run_main('terminal', build, checks)
