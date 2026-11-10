# Boiler30s - 35 mm2 tube cable lug for an M8 stud (DIN 46235 style / SC35-8, e.g. Greek "KOS PRESAS No35 F8"),
# tinned copper. Local frame: stud hole centre at the origin, palm top face (the face that sits flat on the heater pad)
# at z = 0, palm hanging below (z -3..0), barrel axis along +X. The barrel's top line is flush with the palm top face
# (flattened palm on one side of the barrel axis, like a real tube lug), so nothing rises above the pad plane.
# placed(angle, r) puts it on the heater pad (palm on the copper face, barrel pointing radially outward).
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from cadlib import *

# ---------------- parameters (mm), typical SC35-8 ----------------
HOLE_D      = 8.4
PALM_W      = 16.0          # R8 rounded end around the hole
PALM_T      = 3.0
PALM_L_OUT  = 11.0          # flat palm from the hole centre outward before the neck (clears the D18 head washer)
NECK_L      = 4.0
BARREL_OD, BARREL_ID, BARREL_L = 13.0, 9.0, 22.0
BORE_DEPTH  = 19.0          # conductor bore depth from the mouth
MOUTH_CHAMFER = 0.8
CRIMP_X0, CRIMP_L, CRIMP_AF = 6.0, 9.0, 11.6     # hex crimp impression (from the barrel start), across flats
TOTAL_L     = PALM_W / 2 + PALM_L_OUT + NECK_L + BARREL_L   # 45 mm
BARREL_Z    = -BARREL_OD / 2                      # axis 6.5 below the palm top face
TINNED      = (0.80, 0.73, 0.64)


def lug_local():
    # palm: stadium (semicircle R8 around the hole + rectangle to the neck)
    palm = cyl(PALM_W / 2, PALM_T, 0, 0, -PALM_T).fuse(box(0, -PALM_W / 2, -PALM_T, PALM_L_OUT, PALM_W / 2, 0))
    x_n0, x_b0 = PALM_L_OUT, PALM_L_OUT + NECK_L
    # neck: loft from the palm section to the barrel circle
    rect = Part.makePolygon([V(x_n0, -PALM_W / 2, -PALM_T), V(x_n0, PALM_W / 2, -PALM_T), V(x_n0, PALM_W / 2, 0),
                             V(x_n0, -PALM_W / 2, 0), V(x_n0, -PALM_W / 2, -PALM_T)])
    circ = Part.Wire(Part.makeCircle(BARREL_OD / 2, V(x_b0, 0, BARREL_Z), V(1, 0, 0)))
    try:
        neck = Part.makeLoft([rect, circ], True, False)
    except Exception as ex:
        log('neck loft failed (%s): using a box transition' % ex)
        neck = box(x_n0, -BARREL_OD / 2, -BARREL_OD, x_b0, BARREL_OD / 2, 0)
    barrel = cyl(BARREL_OD / 2, BARREL_L, x_b0, 0, BARREL_Z, d=(1, 0, 0))
    # hex crimp impression: replace a barrel section by its intersection with a hex prism along X
    xc = x_b0 + CRIMP_X0
    r = CRIMP_AF / math.sqrt(3)
    hexw = Part.makePolygon([V(xc, r * math.cos(math.radians(60 * i)), BARREL_Z + r * math.sin(math.radians(60 * i)))
                             for i in range(6)] + [V(xc, r, BARREL_Z)])
    hexp = Part.Face(hexw).extrude(V(CRIMP_L, 0, 0))
    crimp_zone = cyl(BARREL_OD / 2 + 1, CRIMP_L, xc, 0, BARREL_Z, d=(1, 0, 0))
    barrel = barrel.cut(crimp_zone.cut(hexp))
    s = fuse_all([palm, neck, barrel])
    x_m = x_b0 + BARREL_L
    bore = cyl(BARREL_ID / 2, BORE_DEPTH + 0.01, x_m - BORE_DEPTH, 0, BARREL_Z, d=(1, 0, 0))
    mouth = Part.makeCone(BARREL_ID / 2, BARREL_ID / 2 + MOUTH_CHAMFER, MOUTH_CHAMFER + 0.01,
                          V(x_m - MOUTH_CHAMFER, 0, BARREL_Z), V(1, 0, 0))
    s = cut_all(s, [cyl(HOLE_D / 2, PALM_T + 2, 0, 0, -PALM_T - 1), bore, mouth])
    return solid_of(s.removeSplitter())


def placed(angle, r, z_top=0.0):
    s = lug_local()
    s.translate(V(r, 0, z_top))
    s.rotate(V(0, 0, 0), V(0, 0, 1), angle)
    return s


def mouth_point(angle, r, z_top=0.0):
    """Centre of the barrel mouth in the kettle frame (for the cable stub)."""
    x = r + PALM_L_OUT + NECK_L + BARREL_L
    p = polar(x, angle)
    return V(p.x, p.y, z_top + BARREL_Z)


def build():
    return [('lug_35_m8', lug_local(), TINNED)]


def checks(items):
    s = items[0][1]
    bb = s.BoundBox
    log('lug: total length %.1f mm (bbox x %.1f..%.1f), width %.1f, height %.1f (z %.1f..%.1f), mass %.1f g' % (
        TOTAL_L, bb.XMin, bb.XMax, bb.YLength, bb.ZLength, bb.ZMin, bb.ZMax, s.Volume / 1000 * 8.9))


run_main('lug_35_m8', build, checks)
