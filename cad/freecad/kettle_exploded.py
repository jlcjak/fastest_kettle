# Boiler30s v3 - exploded view in assembly order (docs/mech_notes.md):
#  jig blocks (cure only) -> cake ring + sealant -> board | backing plates, washers, nuts (top) | lugs + shoulder
#  washers -> M6 bolts + D18 washers (bottom) -> cable stubs (radial) -> feet + M5 bolts
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import builtins
builtins.BOILER_NO_MAIN = True
builtins.BOILER_ASM = True
from cadlib import *
from kettle_params import *
import kettle_assembly

# ---------------- parameters: (name prefixes, dz, radial) in mm ----------------
GROUPS = [
    (('jig_block',), 150, 60),
    (('cake_ring_304',), 120, 0),
    (('silicone_sealant',), 60, 0),
    (('m6_nuts',), 110, 0), (('m6_top_washers',), 90, 0), (('backing_plates_steel',), 70, 0),
    (('m5x12_foot_bolts',), 160, 0), (('m5_foot_washers',), 140, 0),
    (('heater_',), 0, 0),
    (('lug_35_m8',), -30, 0),
    (('shoulder_washers',), -55, 0),
    (('m6x25_terminal_bolts', 'm6_washers_d18'), -85, 0),
    (('cable_A', 'cable_B'), -30, 60),
    (('foot_',), -110, 40),
]
SKIP = ('water_1L',)


def offset_for(name, shape):
    for keys, dz, dr in GROUPS:
        if name.startswith(keys):
            c = shape.BoundBox.Center
            r = math.hypot(c.x, c.y)
            ux, uy = (c.x / r, c.y / r) if (dr and r > 1) else (0.0, 0.0)
            return V(ux * dr, uy * dr, dz)
    return V(0, 0, 0)


def main():
    set_log('kettle_exploded')
    try:
        items = []
        for it in kettle_assembly.collect():
            n, s = it[0], it[1]
            if n in SKIP:
                continue
            parts = s.Solids if (s.ShapeType == 'Compound' and len(s.Solids) > 1) else [s]
            for k, p in enumerate(parts):
                p = p.copy()
                p.translate(offset_for(n, p))
                items.append(((n if len(parts) == 1 else '%s_%d' % (n, k + 1)), p) + tuple(it[2:]))
        finish('kettle_exploded', items)
    except Exception:
        log('ERROR\n' + traceback.format_exc())
    if FreeCAD.GuiUp:
        os._exit(0)


main()
