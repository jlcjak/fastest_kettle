# Boiler30s v3 - close-up of terminal A (0 deg) for review: the assembly clipped to a box around the terminal and
# flipped copper-side up (so the lug, shoulder washer, D18 washer and M6 head face the viewer).
# Exports mech/terminal_closeup.step; render it and keep the iso view as mech/renders/terminal_closeup.png.
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import builtins
builtins.BOILER_NO_MAIN = True
builtins.BOILER_ASM = True
from cadlib import *
from kettle_params import *
import kettle_assembly

# ---------------- parameters (mm) ----------------
CLIP        = (118.0, -32.0, -20.0, 215.0, 32.0, 25.0)    # x0, y0, z0, x1, y1, z1 around terminal A
FLIP        = True


def main():
    set_log('terminal_closeup')
    try:
        clip = box(*CLIP)
        items = []
        for it in kettle_assembly.collect(show_jig=False):
            n, s = it[0], it[1]
            if n == 'water_1L' or not s.BoundBox.intersect(clip.BoundBox):
                continue
            c = s.common(clip)
            if c.Volume < 0.01:
                continue
            if FLIP:
                c.rotate(V(0, 0, 0), V(1, 0, 0), 180)
            items.append((n, c) + tuple(it[2:]))
        finish('terminal_closeup', items)
    except Exception:
        log('ERROR\n' + traceback.format_exc())
    if FreeCAD.GuiUp:
        os._exit(0)


main()
