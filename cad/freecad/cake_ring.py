# Boiler30s v3 - pot wall: bought 304 stainless cake ring (ID 280, wall 0.8, height 80) bonded to the heater's
# aluminium face with food-safe neutral-cure silicone (bead under the edge + ~3 mm 45 deg fillets inside and outside).
# Also the 1 L water body for the assembly. Kettle frame (kettle_params.py).
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from cadlib import *
from kettle_params import *

# ---------------- parameters (mm) ----------------
RI, RO, H   = CR_RI, CR_RO, CR_H          # 140 / 140.8 / 80
Z0          = Z_CR0                        # 2.1 (0.5 mm bead under the edge)
BEAD_W      = 1.0                          # bead extends 1 mm past each face under the edge
FIL         = SEAL_FILLET                  # 3 mm legs
WATER_L     = 1.0


def build_ring():
    return cyl(RO, H, z=Z0).cut(cyl(RI, H + 2, z=Z0 - 1))


def build_sealant():
    bead = revolve_rz([(RI - BEAD_W, Z_AL), (RO + BEAD_W, Z_AL), (RO + BEAD_W, Z0), (RI - BEAD_W, Z0)])
    fin = revolve_rz([(RI - FIL, Z_AL), (RI, Z_AL), (RI, Z_AL + FIL)])
    fout = revolve_rz([(RO, Z_AL), (RO + FIL, Z_AL), (RO, Z_AL + FIL)])
    return solid_of(fuse_all([bead, fin, fout]).cut(build_ring()))


def water_depth():
    return WATER_L * 1e6 / (math.pi * RI ** 2)


def build_water():
    return cyl(RI - 0.01, water_depth(), z=Z_AL).cut(build_sealant())


def build():
    return [('cake_ring_304', build_ring(), (0.82, 0.83, 0.86)),
            ('silicone_sealant', build_sealant(), (0.70, 0.70, 0.72), 50),
            ('water_1L', build_water(), (0.45, 0.70, 0.95), 70)]


def checks(items):
    log('water depth for %.1f L in D%.0f: %.2f mm (ring top %.1f mm above the floor)' % (WATER_L, 2 * RI, water_depth(), Z_CR0 + H - Z_AL))
    log('ring mass %.0f g, sealant %.1f ml' % (items[0][1].Volume / 1000 * 7.93, items[1][1].Volume / 1000))


run_main('cake_ring', build, checks)
