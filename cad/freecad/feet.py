# Boiler30s v3 - 4 identical printed PC feet under the heater board rim (45/135/225/315 deg). Each is a 45 mm cone
# (D16 top bearing only on the copper-free rim r144..160, D46 base) held by one M5x12 + washer from the Al face through
# the board hole into an M5 heat-set insert in the foot top. Print upright, base on the bed, no supports. 46 x 46 x 45 mm.
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from cadlib import *
from kettle_params import *

# ---------------- parameters (mm) ----------------
R_AX        = HB_HOLE_R                   # 152 bolt axis (board hole)
TOP_D, BASE_D = 16.0, 46.0
H           = FOOT_H                       # 45 (copper face above the table)
INS_D, INS_DEPTH = 6.4, 11.0               # M5 x 9.5 heat-set insert
COLOUR      = (0.30, 0.30, 0.32)


def foot(ang):
    s = Part.makeCone(BASE_D / 2, TOP_D / 2, H, V(R_AX, 0, Z_TABLE))
    s = solid_of(s.cut(cyl(INS_D / 2, INS_DEPTH + 1, R_AX, 0, Z_CU - INS_DEPTH)).removeSplitter())
    s.rotate(V(0, 0, 0), V(0, 0, 1), ang)
    return s


def build():
    return [('foot_%03d' % round(a), foot(a), COLOUR) for a in FOOT_ANG]


def checks(items):
    for n, s, *_ in items:
        bb = s.BoundBox
        log('%s: envelope %.0f x %.0f x %.0f, top face spans r %.1f..%.1f (copper-free >= 143)' % (
            n, bb.XLength, bb.YLength, bb.ZLength, R_AX - TOP_D / 2, R_AX + TOP_D / 2))


run_main('feet', build, checks)
