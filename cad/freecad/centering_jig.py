# Boiler30s v3 - 4 printed centering blocks for the silicone cure (PLA/PETG, removed afterwards). No bolts.
# Each block is an arc segment whose inner face is concave, concentric with the cake ring (R = ring OD/2 + gap), and it
# drops onto the board with TWO crush-rib pins into two adjacent r152 holes (15 deg apart), so it lands at the right
# angle and radius by itself and is a snug push fit. Bottom inner edge undercut 45 deg so the outer fillet can't glue it.
# Print upside down (flat top on the bed, pins pointing up): no supports.
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from cadlib import *
from kettle_params import *

# ---------------- parameters (mm) ----------------
FACE_GAP    = 0.2                          # radial clearance to the ring OD (snug; raise if your ring is oversize)
FACE_R      = CR_RO + FACE_GAP             # 141.0
OUT_R       = HB_R                         # 160, flush with the board edge
H           = 30.0                         # face height above the Al floor (ring is 50 tall)
UNDERCUT_H  = 6.0
END_MARGIN  = 4.0                          # degrees of arc beyond each pin
PIN_CORE_D  = 5.0                          # board holes are D5.5 +/-0.1
PIN_RIB_OD  = 5.7                          # 4 crush ribs: deform ~0.1 mm on insertion -> tight but goes in
PIN_RIB_W   = 0.8
PIN_L       = 8.0                          # through the 1.6 board and 6.4 out the copper side (only bare rim there)
PIN_CHAMFER = 0.8                          # longer lead-in so the ribs start straight


def pin(x, y):
    z0 = Z_AL - PIN_L
    p = cyl(PIN_CORE_D / 2, PIN_L, x, y, z0)
    for k in range(4):
        rib = box(-PIN_RIB_W / 2, 0, z0 + PIN_CHAMFER, PIN_RIB_W / 2, PIN_RIB_OD / 2, Z_AL)
        rib.rotate(V(0, 0, 0), V(0, 0, 1), 45 + 90 * k)
        rib.translate(V(x, y, 0))
        p = p.fuse(rib)
    tip = Part.makeCone(PIN_CORE_D / 2 - PIN_CHAMFER, PIN_CORE_D / 2, PIN_CHAMFER, V(x, y, z0), V(0, 0, 1))
    return p.cut(cyl(PIN_CORE_D, PIN_CHAMFER, x, y, z0).cut(tip))


def block(a0, a1):
    prof = [(FACE_R + UNDERCUT_H, Z_AL), (OUT_R, Z_AL), (OUT_R, Z_AL + H), (FACE_R, Z_AL + H), (FACE_R, Z_AL + UNDERCUT_H)]
    b = revolve_rz(prof, a0 - END_MARGIN, (a1 - a0) + 2 * END_MARGIN)
    for a in (a0, a1):
        b = b.fuse(pin(HB_HOLE_R * math.cos(math.radians(a)), HB_HOLE_R * math.sin(math.radians(a))))
    return solid_of(b.removeSplitter())


def build():
    return [('jig_block_%03d' % round((a0 + a1) / 2), block(a0, a1), (0.20, 0.55, 0.85)) for a0, a1 in JIG_PAIRS]


def checks(items):
    import builtins; builtins.BOILER_ASM = True
    import cake_ring
    seal, ring = cake_ring.build_sealant(), cake_ring.build_ring()
    for n, s, *_ in items:
        log('%s: to sealant %.2f mm, to ring %.2f mm, size %.0f x %.0f x %.0f, vol %.0f mm3' % (
            n, s.distToShape(seal)[0], s.distToShape(ring)[0], s.BoundBox.XLength, s.BoundBox.YLength, s.BoundBox.ZLength, s.Volume))
    log('pin: core D%.1f, ribs to D%.2f (hole D%.1f) -> %.2f mm interference per side' % (PIN_CORE_D, PIN_RIB_OD, HB_HOLE_D, (PIN_RIB_OD - HB_HOLE_D) / 2))


run_main('centering_jig', build, checks)
