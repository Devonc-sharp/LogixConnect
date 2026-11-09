"""Logix Connect badge, three colours: the app's monoline mark -( o )- and the name, inlaid flush in a dark plate.

The mark is the title bar's SVG (viewBox 64: the two leads, the two coil arcs of radius 16, the dot), drawn with the
same round-capped stroke. Colour 1 the plate (dark), colour 2 the mark's strokes and LOGIX CONNECT (white),
colour 3 the dot, v2.0 and a thin inset frame (the accent: green in the app). Inlays are flush, 0.6 mm (three 0.2 mm
layers), so the top is flat for printing face up.
"""
import os, math
import cadquery as cq
from shapely.geometry import Polygon, LineString, Point, MultiPolygon, box
from shapely.ops import unary_union
from shapely import affinity
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import make_calplate as cp

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'badge')
NAME = 'LogixConnect-Badge'
T, INLAY, CORNER_R = 3.0, 0.6, 6.0
MARK_SCALE = 0.46          # mm per SVG unit: the mark about 29 mm wide
TITLE_H, SUB_H = 6.2, 4.4  # letter heights (mm)
SUB = 'v2.0'               # '' for none
MARGIN, GAP = 5.0, 5.0
FRAME_IN, FRAME_W = 2.0, 0.9
FONT = FontProperties(fname='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')


def text_poly(s, h):
    tp = TextPath((0, 0), s, size=10, prop=FONT)
    geom = None
    for poly in sorted((Polygon(p).buffer(0) for p in tp.to_polygons() if len(p) >= 3), key=lambda p: -p.area):
        if geom is None: geom = poly
        elif geom.contains(poly): geom = geom.difference(poly)
        else: geom = geom.union(poly)
    b = geom.bounds
    geom = affinity.scale(geom, h / (b[3] - b[1]), h / (b[3] - b[1]), origin=(0, 0))
    b = geom.bounds
    return affinity.translate(geom, -b[0], -b[1])


def mark():
    """the SVG mark in SVG units, y flipped to point up (it is symmetric top to bottom)"""
    sw = 5.5 / 2
    leads = [LineString([(3, 32), (18, 32)]), LineString([(46, 32), (61, 32)])]
    off = math.sqrt(16 ** 2 - 14 ** 2)
    def arc(cx, a0, a1):
        n = 64
        return LineString([(cx + 16 * math.cos(math.radians(a0 + (a1 - a0) * i / n)), 32 + 16 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)])
    a = math.degrees(math.atan2(14, off))
    coil = [arc(26 + off, 180 - a, 180 + a), arc(38 - off, -a, a)]
    strokes = unary_union([g.buffer(sw, quad_segs=24) for g in leads + coil])
    dot = Point(32, 32).buffer(5.5, quad_segs=32)
    return strokes, dot


def layout():
    st, dot = mark()
    st = affinity.scale(st, MARK_SCALE, MARK_SCALE, origin=(0, 0)); dot = affinity.scale(dot, MARK_SCALE, MARK_SCALE, origin=(0, 0))
    title = text_poly('LOGIX CONNECT', TITLE_H)
    sub = text_poly(SUB, SUB_H) if SUB else None
    tw = title.bounds[2]
    th = TITLE_H + (SUB_H + 3.2 if sub else 0)
    mb = st.bounds; mw, mh = mb[2] - mb[0], mb[3] - mb[1]
    W = 2 * MARGIN + 2 + mw + GAP + tw + 2
    H = max(mh, th) + 2 * MARGIN + 6
    cy = H / 2
    st = affinity.translate(st, MARGIN + 2 - mb[0], cy - (mb[1] + mb[3]) / 2); dot = affinity.translate(dot, MARGIN + 2 - mb[0], cy - (mb[1] + mb[3]) / 2)
    tx = MARGIN + 2 + mw + GAP
    ty = cy + th / 2 - TITLE_H
    title = affinity.translate(title, tx, ty)
    if sub:
        sub = affinity.translate(sub, tx, ty - 3.2 - SUB_H)
    plate = box(0, 0, W, H)
    outer = box(FRAME_IN, FRAME_IN, W - FRAME_IN, H - FRAME_IN).buffer(-0.01)
    frame = outer.difference(box(FRAME_IN + FRAME_W, FRAME_IN + FRAME_W, W - FRAME_IN - FRAME_W, H - FRAME_IN - FRAME_W))
    # round the frame's corners to follow the plate's
    r_out = CORNER_R - FRAME_IN
    o = box(FRAME_IN + r_out, FRAME_IN + r_out, W - FRAME_IN - r_out, H - FRAME_IN - r_out).buffer(r_out, quad_segs=24)
    i = box(FRAME_IN + r_out, FRAME_IN + r_out, W - FRAME_IN - r_out, H - FRAME_IN - r_out).buffer(r_out - FRAME_W, quad_segs=24)
    frame = o.difference(i)
    white = unary_union([st, title])
    accent = unary_union([dot, frame] + ([sub] if sub else []))
    return W, H, plate, white, accent


if __name__ == '__main__':
    os.makedirs(os.path.join(OUT, 'step_parts'), exist_ok=True)
    W, H, plate2d, white, accent = layout()
    plate = cq.Workplane('XY').add(cp.prism(plate2d, 0, T)[0]).edges('|Z').fillet(CORNER_R).val()
    wsol, asol = cp.prism(white, T - INLAY, INLAY), cp.prism(accent, T - INLAY, INLAY)
    base = plate.cut(cq.Compound.makeCompound(wsol + asol))
    dark, wc, gc = cq.Color(0.08, 0.08, 0.1), cq.Color(0.95, 0.95, 0.95), cq.Color(0.18, 0.56, 0.31)
    asm = cq.Assembly(name=NAME)
    asm.add(base, name=f'{NAME}_1_plate_dark', color=dark)
    asm.add(cq.Compound.makeCompound(wsol), name=f'{NAME}_2_mark_white', color=wc)
    asm.add(cq.Compound.makeCompound(asol), name=f'{NAME}_3_accent', color=gc)
    asm.export(os.path.join(OUT, f'{NAME}.step'))
    for k, (nm, shp, col) in enumerate([('plate_dark', base, dark), ('mark_white', cq.Compound.makeCompound(wsol), wc), ('accent', cq.Compound.makeCompound(asol), gc)], 1):
        a = cq.Assembly(name=f'{NAME}_{nm}'); a.add(shp, name=f'{NAME} {nm}', color=col); a.export(os.path.join(OUT, 'step_parts', f'{NAME}_{k}_{nm}.step'))
        cq.exporters.export(shp, os.path.join(OUT, 'step_parts', f'{NAME}_{k}_{nm}.stl'))
    cp.NAME = NAME
    cp.write_3mf(os.path.join(OUT, f'{NAME}.3mf'), [('Plate', 1, [base]), ('Mark and name', 2, wsol), ('Accent', 3, asol)])
    bb = base.BoundingBox()
    print('size', round(W, 1), 'x', round(H, 1), 'x', T, 'base valid', base.isValid(), 'white', len(wsol), all(s.isValid() for s in wsol), 'accent', len(asol), all(s.isValid() for s in asol))
    # a top-view preview
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path
    def draw(ax, g, col):
        for p in (g.geoms if hasattr(g, 'geoms') else [g]):
            verts, codes = [], []
            for ring in [p.exterior] + list(p.interiors):
                cs = list(ring.coords); verts += cs; codes += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), fc=col, ec='none'))
    fig, ax = plt.subplots(figsize=(W / 12, H / 12), dpi=160)
    draw(ax, box(0, 0, W, H).buffer(-CORNER_R).buffer(CORNER_R, quad_segs=24), '#17181c'); draw(ax, white, '#f2f2f2'); draw(ax, accent, '#2f8f4e')
    ax.set_xlim(-2, W + 2); ax.set_ylim(-2, H + 2); ax.set_aspect('equal'); ax.axis('off'); fig.patch.set_facecolor('#c9ced4')
    fig.savefig(os.path.join(OUT, f'{NAME}-preview.png'), bbox_inches='tight', facecolor=fig.get_facecolor()); print('preview ok')
