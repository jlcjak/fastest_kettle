# Boiler30s v3 - kettle assembly: heater board (chassis), stainless cake ring + silicone sealant + 1 L water,
# 35 mm2 M8 tube lugs bolted straight onto the heater pads (M6 stacks, shoulder washers, steel backing plates) + cable
# stubs, 4 feet + M5 bolts,
# and the 4 removable centering-jig blocks (cure only). No KSD301 (removed). Kettle frame, identity placement.
# Runs interference + clearance checks, mass and filament estimate; exports mech/kettle_assembly.step.
import sys; sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import builtins
_RUN_MAIN = not getattr(builtins, 'BOILER_NO_MAIN', False)
builtins.BOILER_ASM = True
from cadlib import *
from kettle_params import *
import importlib

# ---------------- parameters ----------------
SHOW_JIG    = True                                   # jig blocks are only used during the 48 h cure
A2 = (0.66, 0.67, 0.70)
DENS = {'heater_aluminium': 2.70, 'heater_dielectric_mask': 2.0, 'heater_copper_masked': 8.96, 'heater_contact_pads': 8.96,
        'cake_ring_304': 7.93, 'silicone_sealant': 1.1, 'lug_35_m8': 8.9, 'shoulder_washers': 1.14}
PRINTED_PC = ('foot_',)
PRINTED_JIG = ('jig_block',)


def collect(show_jig=SHOW_JIG):
    items = []
    mods = ['heater_board', 'cake_ring', 'terminal', 'feet'] + (['centering_jig'] if show_jig else [])
    for mod in mods:
        items += [tuple(x) for x in importlib.import_module(mod).build()]
    fb, fw = [], []
    for a in FOOT_ANG:
        x, y = polar(HB_HOLE_R, a)[:2]
        fw.append(cyl(M5_WASHER_D / 2, M5_WASHER_T, x, y, Z_AL).cut(cyl(2.7, 5, x, y, Z_AL - 1)))
        zb = Z_AL + M5_WASHER_T
        fb.append(cyl(M5_HEAD_D / 2, M5_HEAD_H, x, y, zb).fuse(cyl(2.5, M5_FOOT_BOLT_L, x, y, zb - M5_FOOT_BOLT_L)))
    items += [('m5x12_foot_bolts', fuse_all(fb), A2), ('m5_foot_washers', fuse_all(fw), A2)]
    return items


def checks(items):
    d = dict((x[0], x[1]) for x in items)
    names = list(d)
    import heater_board
    log('--- interference (all pairs) ---')
    allowed = {frozenset(('heater_aluminium', 'jig_block_%03d' % round(a))) for a in JIG_ANG}   # crush-rib press fit (intended); lug-pad, washer-lug, sleeve-lug etc. are face contacts (zero volume) and pass the check
    bad = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if frozenset((a, b)) in allowed or not d[a].BoundBox.intersect(d[b].BoundBox):
                continue
            v = overlap(d[a], d[b])
            if v > 0.05 or v < 0:
                bad += 1
                cc = d[a].common(d[b]).BoundBox
                log('  OVERLAP %-22s x %-22s %.2f mm3 at x[%.0f,%.0f] y[%.0f,%.0f] z[%.1f,%.1f]' % (
                    a, b, v, cc.XMin, cc.XMax, cc.YMin, cc.YMax, cc.ZMin, cc.ZMax))
    log('  interfering pairs: %d (of %d bodies)' % (bad, len(names)))
    log('--- clearances ---')
    cu = heater_board.copper_shape()
    seal = d['silicone_sealant']
    log('  backing plates to sealant fillet: %.2f mm (>= 1)' % d['backing_plates_steel'].distToShape(seal)[0])
    log('  backing plates / M6 nuts to cake ring: %.2f / %.2f mm' % (d['backing_plates_steel'].distToShape(d['cake_ring_304'])[0],
                                                                   d['m6_nuts'].distToShape(d['cake_ring_304'])[0]))
    for n in ('A', 'B'):
        lug = d['lug_35_m8_' + n]
        log('  lug %s: M6 shank to lug bore %.2f mm (>= 1, sleeve fills it), D18 washer to lug %.2f mm (flange), lug to pad contact %.2f mm' % (
            n, lug.distToShape(d['m6x25_terminal_bolts'])[0], lug.distToShape(d['m6_washers_d18'])[0], lug.distToShape(d['heater_contact_pads'])[0]))
    log('  M6 bolt to copper %.1f mm; M5 foot bolt washers to sealant %.1f mm' % (
        d['m6x25_terminal_bolts'].distToShape(cu)[0], d['m5_foot_washers'].distToShape(seal)[0]))
    hw_hot = [n for n in names if n.startswith(('lug_35', 'cable_', 'm6x25', 'm6_washers'))]
    for f in [n for n in names if n.startswith('foot_')]:
        s = d[f]
        log('  %-14s to copper %.1f mm, to lugs/cables/M6 stack %.1f mm, envelope %.0fx%.0fx%.0f' % (
            f, s.distToShape(cu)[0], min(s.distToShape(d[h])[0] for h in hw_hot),
            s.BoundBox.XLength, s.BoundBox.YLength, s.BoundBox.ZLength))
    board = d['heater_aluminium'].fuse([d['heater_dielectric_mask'], d['heater_copper_masked']])
    log('  copper face above the table: %.1f mm; lowest non-foot part z %.1f' % (Z_CU - Z_TABLE, min(
        d[n].BoundBox.ZMin for n in names if not n.startswith('foot_'))))
    if 'jig_block_030' in d:
        log('  jig blocks to sealant %.2f mm, to ring %.2f mm' % (min(d[n].distToShape(seal)[0] for n in names if n.startswith('jig')),
                                                                min(d[n].distToShape(d['cake_ring_304'])[0] for n in names if n.startswith('jig'))))
    bb = Part.makeCompound([x[1] for x in items if not x[0].startswith(('cable_A', 'cable_B', 'jig'))]).BoundBox
    log('  overall (without cable stubs / jig): X %.0f, Y %.0f, Z %.0f mm (z %.1f..%.1f)' % (bb.XLength, bb.YLength, bb.ZLength, bb.ZMin, bb.ZMax))
    log('--- mass / filament ---')
    tot, pc, jig = 0.0, 0.0, 0.0
    for n in names:
        if n == 'water_1L' or n.startswith(('cable_A', 'cable_B')):
            continue
        v = d[n].Volume / 1000
        if n.startswith(PRINTED_JIG):
            jig += v * 1.24; continue
        if n.startswith(PRINTED_PC):
            g = v * 1.20; pc += g
        else:
            g = v * next((rho for k, rho in DENS.items() if n.startswith(k)), 7.9)
        tot += g
        log('  %-24s %7.0f g' % (n, g))
    log('  printed PC (feet) solid %.0f g -> ~%.0f g printed; jig blocks (PLA/PETG) solid %.0f g' % (pc, pc * 0.8, jig))
    log('  KETTLE MASS (empty, excl. cables) ~ %.2f kg ; with 1 L water ~ %.2f kg' % (tot / 1000, tot / 1000 + 1.0))


def main():
    set_log('kettle_assembly')
    t0 = time.time()
    try:
        items = collect()
        checks(items)
        finish('kettle_assembly', items)
        log('done in %.1f s' % (time.time() - t0))
    except Exception:
        log('ERROR\n' + traceback.format_exc())
    if FreeCAD.GuiUp:
        os._exit(0)


if _RUN_MAIN:
    main()
