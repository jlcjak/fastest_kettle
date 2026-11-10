# Boiler30s v3 - shared mechanical interface dimensions (source: docs/spec.md, boards/heater/gen_heater.py).
# Units mm. Kettle frame: origin on the kettle axis, Z = 0 = heater COPPER face (underside), Z up,
# terminal A at +X (0 deg), terminal B at -X (180 deg), front = -Y. The heater board is the chassis.
import math

# ---- heater board (aluminium IMS, copper side down; unchanged since v2) ----
HB_R        = 160.0          # D320 disc
HB_T        = 1.6
Z_CU        = 0.0            # copper face
Z_AL        = Z_CU + HB_T    # 1.6  wet aluminium floor
HB_HOLE_R, HB_HOLE_D, HB_N_HOLES = 152.0, 5.5, 24          # holes at k*15 deg
HB_HOLE_ANG = tuple(15.0 * k for k in range(HB_N_HOLES))
HB_HEAT_R   = 135.0          # heated copper r <= 135
HB_ISLAND_R = 11.0           # copper-free centre island (no longer used: KSD301 removed)
HB_R0       = 35.0           # centre junction disc radius
HB_TRACK_W  = 17.83          # spiral track width (heater_numbers.json)
HB_PAD_R0, HB_PAD_R1, HB_PAD_HW = 139.5, 158.5, 17.5      # exposed contact pads (mask opening) at 0/180 deg
HB_LEAD_HW  = 18.0           # copper lead half width at the pad
HB_LEAD_TAPER_R = HB_PAD_R0 - 4.0                          # lead reaches full width here (135.5)
HB_LEAD_X0  = HB_HEAT_R - HB_TRACK_W / 2 - 2.0             # lead starts on the outer turn (~124.1)
HB_BUS_HOLE_D = 6.5          # 0 and 180 deg holes take the M6 busbar clamp bolts
HB_HOLE_CU_CLR_R = 6.5       # copper-free radius around the busbar bolt hole

# ---- v3: stainless cake ring bonded to the Al face with neutral-cure silicone ----
CR_RI, CR_T, CR_H = 140.0, 0.8, 50.0                      # ID 280, wall 0.8, height 50 (bought: Skroutz 36140026, D28 x 5 cm)
CR_RO       = CR_RI + CR_T                                # 140.8
SEAL_BEAD_T = 0.5                                         # silicone bead under the ring edge
Z_CR0       = Z_AL + SEAL_BEAD_T                          # 2.1
Z_CR1       = Z_CR0 + CR_H                                # 82.1
SEAL_FILLET = 3.0                                         # 45 deg fillet leg, inside and outside

# ---- terminals: 35 mm2 M8 tube lug bolted straight onto each heater pad (0 deg = A, 180 deg = B) ----
# stack bottom -> top: M6x25 A2-70 socket head, D18 washer (DIN 9021), nylon/PTFE shoulder washer (flange on the lug,
# sleeve in the lug's D8.4 hole, stops 0.5 below the board), lug palm (flat on the pad), board, steel backing plate
# 30x14x5 on the Al face, DIN 125 washer, M6 nut (8 N.m).
TERM_ANG    = (0.0, 180.0)
TERM_R      = 152.0                                       # = HB_HOLE_R
M6_HEAD_D, M6_HEAD_H = 10.0, 6.0
M6_BOLT_L   = 25.0                                        # stack 19.3 -> M6x20 leaves 0.7 mm; M6x25 leaves 5.7 mm
M6_WASHER_BIG_D, M6_WASHER_T = 18.0, 1.6
M6_WASHER_D, M6_NUT_AF, M6_NUT_H = 12.0, 10.0, 5.0
LUG_PALM_T  = 3.0
SHOULDER_FLANGE_D, SHOULDER_FLANGE_T = 13.0, 1.5
SHOULDER_SLEEVE_OD, SHOULDER_SLEEVE_L, SHOULDER_ID = 8.0, 2.5, 6.4
BP_TANG, BP_RAD, BP_T, BP_HOLE_D = 30.0, 14.0, 5.0, 6.5
M6_TORQUE   = 8.0
CABLE_D     = 12.0                                        # 35 mm2 cable OD; leaves along +/-X at the barrel axis (z -6.5)

# ---- feet / table ----
FOOT_ANG    = (45.0, 135.0, 225.0, 315.0)
FOOT_H      = 45.0                                        # copper face above the table
Z_TABLE     = Z_CU - FOOT_H                               # -45
M5_FOOT_BOLT_L = 12.0
M5_HEAD_D, M5_HEAD_H, M5_WASHER_D, M5_WASHER_T = 8.5, 5.0, 10.0, 1.0

# ---- centering jig (cure only) ----
JIG_PAIRS   = ((15.0, 30.0), (105.0, 120.0), (195.0, 210.0), (285.0, 300.0))   # two free holes per block (clear of feet 45/135/225/315, terminals 0/180)
JIG_ANG     = tuple((a + b) / 2 for a, b in JIG_PAIRS)
