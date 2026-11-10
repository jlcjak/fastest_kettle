# Small helper library shared by the Boiler30s FreeCAD part scripts.
import os, sys, math, time, traceback, builtins
import FreeCAD, Part
from FreeCAD import Vector as V

import os
MECH = os.path.dirname(os.path.abspath(__file__))
LOGDIR = os.path.join(MECH, 'logs')
os.makedirs(LOGDIR, exist_ok=True)

_logname = ['cad']


def set_log(name, fresh=True):
    _logname[0] = name
    if fresh:
        open(os.path.join(LOGDIR, name + '.log'), 'w').close()


def log(*a):
    msg = ' '.join(str(x) for x in a)
    with open(os.path.join(LOGDIR, _logname[0] + '.log'), 'a') as f:
        f.write(msg + '\n')
    try:
        FreeCAD.Console.PrintMessage(msg + '\n')
    except Exception:
        pass


def is_assembly_import():
    return getattr(builtins, 'BOILER_ASM', False)


# ---------------- primitives ----------------
def cyl(r, h, x=0, y=0, z=0, d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(x, y, z), V(*d))


def box(x0, y0, z0, x1, y1, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def polar(r, ang_deg, z=0):
    a = math.radians(ang_deg)
    return V(r * math.cos(a), r * math.sin(a), z)


def revolve_rz(pts, ang0=0, ang=360):
    """Revolve a closed (r, z) polygon (in the XZ plane, x=r) about Z."""
    wire = Part.makePolygon([V(r, 0, z) for r, z in pts] + [V(pts[0][0], 0, pts[0][1])])
    face = Part.Face(wire)
    s = face.revolve(V(0, 0, 0), V(0, 0, 1), ang)
    if ang0:
        s.rotate(V(0, 0, 0), V(0, 0, 1), ang0)
    return s


def prism_xz(pts, y0, y1):
    """Extrude a closed (x, z) polygon from y0 to y1."""
    wire = Part.makePolygon([V(x, y0, z) for x, z in pts] + [V(pts[0][0], y0, pts[0][1])])
    return Part.Face(wire).extrude(V(0, y1 - y0, 0))


def prism_yz(pts, x0, x1):
    wire = Part.makePolygon([V(x0, y, z) for y, z in pts] + [V(x0, pts[0][0], pts[0][1])])
    return Part.Face(wire).extrude(V(x1 - x0, 0, 0))


def prism_xy(pts, z0, z1):
    wire = Part.makePolygon([V(x, y, z0) for x, y in pts] + [V(pts[0][0], pts[0][1], z0)])
    return Part.Face(wire).extrude(V(0, 0, z1 - z0))


def wedge(a0, a1, r=400, z0=-50, z1=400):
    """Angular sector solid from a0 to a1 degrees (CCW)."""
    n = max(2, int(abs(a1 - a0) / 5) + 1)
    pts = [(0, 0)] + [(r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
                        r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]
    return prism_xy(pts, z0, z1)


def radial_box(ang, r0, r1, hw, z0, z1):
    """Box spanning radius r0..r1 along direction ang, half-width hw."""
    b = box(r0, -hw, z0, r1, hw, z1)
    b.rotate(V(0, 0, 0), V(0, 0, 1), ang)
    return b


def rounded_rect_xz(x0, z0, x1, z1, radii, y=0.0):
    """Closed wire in the XZ plane, radii = (bl, br, tr, tl)."""
    bl, br, tr, tl = radii
    segs = []
    def arc(cx, cz, r, a0):
        a0r = math.radians(a0); am = math.radians(a0 + 45); a1 = math.radians(a0 + 90)
        return Part.Arc(V(cx + r * math.cos(a0r), y, cz + r * math.sin(a0r)),
                        V(cx + r * math.cos(am), y, cz + r * math.sin(am)),
                        V(cx + r * math.cos(a1), y, cz + r * math.sin(a1))).toShape()
    P = lambda x, z: V(x, y, z)
    segs.append(Part.LineSegment(P(x0 + bl, z0), P(x1 - br, z0)).toShape())
    segs.append(arc(x1 - br, z0 + br, br, -90))
    segs.append(Part.LineSegment(P(x1, z0 + br), P(x1, z1 - tr)).toShape())
    segs.append(arc(x1 - tr, z1 - tr, tr, 0))
    segs.append(Part.LineSegment(P(x1 - tr, z1), P(x0 + tl, z1)).toShape())
    segs.append(arc(x0 + tl, z1 - tl, tl, 90))
    segs.append(Part.LineSegment(P(x0, z1 - tl), P(x0, z0 + bl)).toShape())
    segs.append(arc(x0 + bl, z0 + bl, bl, 180))
    return Part.Wire(Part.__sortEdges__(segs))


def fuse_all(shapes):
    s = shapes[0]
    if len(shapes) > 1:
        s = s.fuse(shapes[1:])
    return s.removeSplitter()


def cut_all(s, tools):
    if not tools:
        return s
    t = tools[0] if len(tools) == 1 else tools[0].fuse(tools[1:])
    return s.cut(t)


def solid_of(s):
    """Return a single Solid if possible (largest), else the shape."""
    if s.ShapeType == 'Solid':
        return s
    sols = s.Solids
    if len(sols) == 1:
        return sols[0]
    if sols:
        return Part.makeCompound(sols)
    return s


# ---------------- checks ----------------
def bed_fit(shape, plane='xy', bed=250.0, step=3):
    """Min footprint over in-plane rotations: returns (angle, w, h, fits)."""
    pts = []
    try:
        mesh = shape.tessellate(2.0)[0]
        pts = mesh
    except Exception:
        pts = [v.Point for v in shape.Vertexes]
    if plane == 'xy':
        P = [(p.x, p.y) for p in pts]
    elif plane == 'xz':
        P = [(p.x, p.z) for p in pts]
    else:
        P = [(p.y, p.z) for p in pts]
    best = None
    for a in range(0, 180, step):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        xs = [c * x - s * y for x, y in P]
        ys = [s * x + c * y for x, y in P]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        key = max(w, h)
        if w <= bed and h <= bed:
            return a, w, h, True
        if best is None or key < best[0]:
            best = (key, a, w, h)
    _, a, w, h = best
    return a, w, h, (w <= bed and h <= bed)


def overlap(a, b):
    try:
        return a.common(b).Volume
    except Exception:
        return -1.0


# ---------------- output ----------------
def finish(partname, items):
    """items: list of (objname, shape, (r,g,b)[, transparency 0..100]). Saves FCStd + STEP."""
    doc = FreeCAD.newDocument(partname)
    objs = []
    allok = True
    # STEP colours only survive per solid: split multi-solid compounds into one object per solid
    flat = []
    for it in items:
        shp = it[1]
        if shp.ShapeType == 'Compound' and len(shp.Solids) >= 1:
            sols = shp.Solids
            if len(sols) == 1:
                flat.append((it[0], sols[0]) + tuple(it[2:]))
            else:
                for k, so in enumerate(sols):
                    flat.append(('%s_%d' % (it[0], k + 1), so) + tuple(it[2:]))
        else:
            flat.append(tuple(it))
    items = flat
    for it in items:
        name, shp, col = it[0], it[1], it[2]
        tr = it[3] if len(it) > 3 else 0
        ok = shp.isValid()
        if not ok:
            shp2 = shp.copy(); shp2.fix(1e-3, 1e-3, 1e-3)
            if shp2.isValid():
                shp, ok = shp2, True
                log('  %s: fixed invalid shape' % name)
        allok &= ok
        bb = shp.BoundBox
        log('  %-22s valid=%s vol=%9.0f mm3  bbox x[%.1f,%.1f] y[%.1f,%.1f] z[%.1f,%.1f]' % (
            name, ok, shp.Volume, bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
        o = doc.addObject('Part::Feature', name)
        o.Shape = shp
        objs.append((o, col, tr))
    doc.recompute()
    if FreeCAD.GuiUp:
        for o, col, tr in objs:
            o.ViewObject.ShapeColor = tuple(col)
            o.ViewObject.Transparency = int(tr)
            try:   # per-face colours: needed for multi-solid compounds to keep their colour in STEP
                o.ViewObject.DiffuseColor = [tuple(col) + (tr / 100.0,)] * len(o.Shape.Faces)
            except Exception:
                pass
    fc = os.path.join(MECH, partname + '.FCStd')
    st = os.path.join(MECH, partname + '.step')
    doc.saveAs(fc)
    if FreeCAD.GuiUp:
        import ImportGui
        ImportGui.export([o for o, _, _ in objs], st)
    else:
        import Import
        Import.export([o for o, _, _ in objs], st)
    log('saved %s and %s (gui colours=%s) all valid=%s' % (fc, st, FreeCAD.GuiUp, allok))
    return allok


def run_main(partname, build, extra=None):
    """Standard script tail: build items, optional checks, write files, exit if GUI."""
    if is_assembly_import():
        return
    set_log(partname)
    t0 = time.time()
    try:
        items = build()
        if extra:
            extra(items)
        finish(partname, items)
        log('done in %.1f s' % (time.time() - t0))
    except Exception:
        log('ERROR\n' + traceback.format_exc())
    if FreeCAD.GuiUp:
        os._exit(0)


# ---------------- 2D outputs ----------------
class DXF:
    """Minimal DXF (R12-style entities, mm) writer: circles, lines, polylines, text."""
    def __init__(self):
        self.e = []

    def circle(self, x, y, r, layer='CUT'):
        self.e.append('0\nCIRCLE\n8\n%s\n10\n%.4f\n20\n%.4f\n30\n0.0\n40\n%.4f\n' % (layer, x, y, r))

    def line(self, x1, y1, x2, y2, layer='CUT'):
        self.e.append('0\nLINE\n8\n%s\n10\n%.4f\n20\n%.4f\n30\n0.0\n11\n%.4f\n21\n%.4f\n31\n0.0\n' % (layer, x1, y1, x2, y2))

    def rect(self, x0, y0, x1, y1, layer='CUT'):
        for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            self.line(a[0], a[1], b[0], b[1], layer)

    def text(self, x, y, h, s, layer='NOTES'):
        self.e.append('0\nTEXT\n8\n%s\n10\n%.4f\n20\n%.4f\n30\n0.0\n40\n%.3f\n1\n%s\n' % (layer, x, y, h, s))

    def save(self, path):
        with open(path, 'w') as f:
            f.write('0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n9\n$INSUNITS\n70\n4\n9\n$MEASUREMENT\n70\n1\n0\nENDSEC\n')
            layers = sorted(set(l.split('\n')[3] for l in self.e))
            colours = {'CUT': 7, 'CENTER': 1, 'NOTES': 3}
            f.write('0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n%d\n' % len(layers))
            for l in layers:
                f.write('0\nLAYER\n2\n%s\n70\n0\n62\n%d\n6\nCONTINUOUS\n' % (l, colours.get(l, 7)))
            f.write('0\nENDTAB\n0\nENDSEC\n')
            f.write('0\nSECTION\n2\nENTITIES\n' + ''.join(self.e) + '0\nENDSEC\n0\nEOF\n')
