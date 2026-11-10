# Boiler30s - heater board v2 (bought aluminium IMS, boards/heater), modelled for fit.
# Kettle frame: copper face at z = 0 (facing DOWN), aluminium wet floor at z = 1.6.
# Copper geometry re-created from boards/heater/gen_heater.py (bifilar spiral, centre disc with KSD301 island,
# terminal leads at 0/180 deg with a copper-free circle around the busbar bolt hole).
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from cadlib import *
from kettle_params import *

# ---------------- parameters (mm) ----------------
R_DISC      = HB_R            # 160
T_BOARD     = HB_T            # 1.6
T_CU        = 0.035           # 1 oz copper (bottom-most layer in this model)
T_DIEL      = 0.065           # dielectric + mask (green), z 0.035 .. 0.1
W           = HB_TRACK_W      # 17.83 track
GAP         = 1.0
R0          = HB_R0           # 35
HEAT_EDGE   = HB_HEAT_R       # 135
ISLAND_R    = HB_ISLAND_R     # 11
STEP_DEG    = 3.0             # spiral discretisation for the model


def arm_pts(phase):
    r_out = HEAT_EDGE - W / 2
    b = (W + GAP) / math.pi
    th_max = (r_out - R0) / b
    pts, th = [], 0.0
    while True:
        t = min(th, th_max)
        r = R0 + b * t
        a = t + phase - th_max
        pts.append((r * math.cos(a), r * math.sin(a)))
        if t >= th_max:
            break
        th += math.radians(STEP_DEG)
    return pts


def thick_polyline(pts, w):
    """Closed outline of a polyline swept with width w (miter-free: per-vertex normals)."""
    left, right = [], []
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[max(i - 1, 0)]
        x1, y1 = pts[min(i + 1, n - 1)]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        x, y = pts[i]
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    return left + right[::-1]


def _face(pts):
    return Part.Face(Part.makePolygon([V(x, y, 0) for x, y in pts] + [V(pts[0][0], pts[0][1], 0)]))


def _disc(r, x=0.0, y=0.0):
    return Part.Face(Part.Wire(Part.makeCircle(r, V(x, y, 0))))


def copper_face():
    """2D copper outline (z = 0 plane): spiral arms, centre disc, terminal leads (2D booleans are robust)."""
    faces = [_face(thick_polyline(arm_pts(ph), W)) for ph in (0.0, math.pi)]
    faces.append(_disc(R0))
    for sgn in (1, -1):
        x0 = HB_LEAD_X0
        lead = [(x0, -W / 2), (HB_LEAD_TAPER_R, -HB_LEAD_HW), (HB_PAD_R1, -HB_LEAD_HW),
                (HB_PAD_R1, HB_LEAD_HW), (HB_LEAD_TAPER_R, HB_LEAD_HW), (x0, W / 2)]
        faces.append(_face([(sgn * x, y) for x, y in lead]))
    f = faces[0].fuse(faces[1:])
    cut = [_disc(ISLAND_R)] + [_disc(HB_HOLE_CU_CLR_R, sgn * HB_HOLE_R, 0) for sgn in (1, -1)]
    cut += [_disc(hole_d(a) / 2, *polar(HB_HOLE_R, a)[:2]) for a in HB_HOLE_ANG]
    f = f.cut(cut[0].fuse(cut[1:]))
    return f.removeSplitter()


def copper_shape(z0=Z_CU, t=T_CU):
    f = copper_face()
    s = f.extrude(V(0, 0, t))
    s.translate(V(0, 0, z0))
    return s


def hole_d(a):
    return HB_BUS_HOLE_D if a in (0.0, 180.0) else HB_HOLE_D


def holes(z0, h):
    return [cyl(hole_d(a) / 2, h + 2, *polar(HB_HOLE_R, a, z0 - 1)) for a in HB_HOLE_ANG]


def pad_openings(z0, h):
    return [radial_box(a, HB_PAD_R0, HB_PAD_R1, HB_PAD_HW, z0, z0 + h) for a in (0, 180)]


def build():
    al = cut_all(cyl(R_DISC, T_BOARD - T_CU - T_DIEL, z=Z_CU + T_CU + T_DIEL), holes(Z_CU + T_CU + T_DIEL, T_BOARD))
    diel = cut_all(cyl(R_DISC, T_DIEL, z=Z_CU + T_CU), holes(Z_CU, 1))
    f = copper_face()
    padf = [Part.Face(Part.makePolygon([V(sgn * HB_PAD_R0, -HB_PAD_HW, 0), V(sgn * HB_PAD_R1, -HB_PAD_HW, 0),
                                         V(sgn * HB_PAD_R1, HB_PAD_HW, 0), V(sgn * HB_PAD_R0, HB_PAD_HW, 0),
                                         V(sgn * HB_PAD_R0, -HB_PAD_HW, 0)])) for sgn in (1, -1)]
    padf = padf[0].fuse(padf[1])
    pads = f.common(padf).extrude(V(0, 0, T_CU))
    cu_masked = f.cut(padf).extrude(V(0, 0, T_CU))
    # exposed pads shown separately (bright copper), rest of copper is under translucent mask
    return [('heater_aluminium', solid_of(al), (0.80, 0.81, 0.83)),
            ('heater_dielectric_mask', solid_of(diel), (0.10, 0.42, 0.22)),
            ('heater_copper_masked', cu_masked, (0.62, 0.45, 0.22)),
            ('heater_contact_pads', pads, (0.90, 0.55, 0.30))]


def checks(items):
    d = dict((n, s) for n, s, *_ in items)
    cu = d['heater_copper_masked'].fuse(d['heater_contact_pads'])
    bb = cu.BoundBox
    log('copper extent x[%.1f,%.1f] y[%.1f,%.1f]; area %.0f cm2' % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, cu.Volume / T_CU / 100))
    isl = cyl(ISLAND_R - 0.01, 1, z=-0.5)
    log('island copper-free: overlap %.4f' % overlap(isl, cu))


run_main('heater_board', build, checks)
