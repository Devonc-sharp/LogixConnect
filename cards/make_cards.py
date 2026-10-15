"""Logix Connect bottle cards: 100 x 70 x 4 mm, two bodies (dark base, red features), one STEP per card.

Card SN-48RK: R = product digit, K = defect digit. Inspection_Results byte 10 = R*10 + K.
Features are inlaid 0.8 mm into the base and stand 0.6 mm proud of it.
Everything on a card is something the camera job uses: bottle outline + cap (locate, cap check),
liquid (fill edge), label window with the product name (label check + OCR), DataMatrix (card ID).
"""
import os, sys, json
import cadquery as cq
from shapely.geometry import Polygon, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from ppf.datamatrix import DataMatrix

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'step')
OUT_PARTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'step_parts')
W, H, T = 100.0, 70.0, 4.0           # card blank
INLAY, RAISE = 0.8, 0.6               # feature depth into the base / height above it
KEY = 10.0                            # keyed corner: 45-degree chamfer, top right
CORNER_R = 2.0
WALL = 1.2                            # bottle outline stroke (3 lines of a 0.4 nozzle)
FONT = FontProperties(fname='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')

PRODUCTS = ['SODA', 'WATER', 'MILK', 'JUICE', 'OIL']                # R = 0..4
DEFECTS = {1: ('good', 100), 2: ('no cap', 100), 3: ('no label', 100), 4: ('short fill', 70)}

# bottle geometry (mm, origin bottom-left of the card)
BX = 27.0                              # bottle centre line
BODY_W, NECK_W, CAP_W = 38.0, 14.0, 18.0
Y_BOT, Y_SHOULDER, Y_NECK, Y_MOUTH, Y_CAP = 5.0, 42.0, 53.0, 59.0, 66.0
FILL_FULL = 40.0                       # 100 % liquid line (top of the straight body)
LABEL = (11.0, 12.0, 43.0, 27.0)       # label window x0, y0, x1, y1
DM_MOD, DM_QUIET = 1.5, 2              # DataMatrix module (mm) and quiet zone (modules)
DM_CX, DM_CY = 75.0, 35.0


def card_blank():
    p = box(0, 0, W, H)
    p = p.difference(Polygon([(W - KEY, H), (W, H), (W, H - KEY)]))
    return p


def bottle_outline():
    """Closed outer silhouette of the bottle (body, shoulder, neck) without the cap."""
    hw, nw = BODY_W / 2, NECK_W / 2
    pts = [(BX - hw, Y_SHOULDER)]
    # rounded shoulder: quarter-ish curve from body to neck
    import math
    n = 16
    for i in range(1, n + 1):
        t = i / n
        x = (BX - hw) + (hw - nw) * (1 - math.cos(t * math.pi / 2))
        y = Y_SHOULDER + (Y_NECK - Y_SHOULDER) * math.sin(t * math.pi / 2)
        pts.append((x, y))
    pts += [(BX - nw, Y_MOUTH), (BX + nw, Y_MOUTH)]
    for i in range(n, -1, -1):
        t = i / n
        x = (BX + hw) - (hw - nw) * (1 - math.cos(t * math.pi / 2))
        y = Y_SHOULDER + (Y_NECK - Y_SHOULDER) * math.sin(t * math.pi / 2)
        pts.append((x, y))
    pts += [(BX + hw, Y_BOT), (BX - hw, Y_BOT)]
    body = Polygon(pts)
    # round the two bottom corners (4 mm)
    return body.buffer(-4, join_style=1).buffer(4, join_style=1).union(
        box(BX - nw, Y_NECK - 1, BX + nw, Y_MOUTH))


def text_scale(max_w, max_h):
    k = 1e9
    for w in PRODUCTS:
        tp = TextPath((0, 0), w, size=10, prop=FONT)
        b = tp.get_extents()
        k = min(k, max_w / b.width, max_h / b.height)
    return k


def text_poly(s, max_w, max_h, cx, cy):
    tp = TextPath((0, 0), s, size=10, prop=FONT)
    polys = [Polygon(v) for v in tp.to_polygons() if len(v) >= 3]
    # even-odd fill: outer contours minus counters
    polys.sort(key=lambda p: -p.area)
    g = Polygon()
    for p in polys:
        p = p.buffer(0)
        g = g.symmetric_difference(p)
    x0, y0, x1, y1 = g.bounds
    k = text_scale(max_w, max_h)          # one letter size on every card: one trained OCR font
    g = affinity.scale(g, k, k, origin=(x0, y0))
    x0, y0, x1, y1 = g.bounds
    return affinity.translate(g, cx - (x0 + x1) / 2, cy - (y0 + y1) / 2)


def datamatrix(text):
    m = DataMatrix(text).matrix
    n = len(m)
    side = (n + 2 * DM_QUIET) * DM_MOD
    x0, y0 = DM_CX - side / 2, DM_CY - side / 2
    pad = box(x0, y0, x0 + side, y0 + side)
    dark = []
    for r, row in enumerate(m):
        for c, v in enumerate(row):
            if v:
                xx = x0 + (DM_QUIET + c) * DM_MOD
                yy = y0 + side - (DM_QUIET + r + 1) * DM_MOD
                dark.append(box(xx, yy, xx + DM_MOD, yy + DM_MOD))
    # dark modules = base showing through the red pad (standard polarity once red reads bright)
    # modules that touch only at a corner would leave zero-width necks (non-manifold solids): pull the dark
    # areas in by 0.05 mm so diagonal neighbours separate cleanly (a 0.1 mm red bridge, below print resolution)
    holes = unary_union(dark).buffer(-0.05, join_style=2)
    return pad.difference(holes).buffer(0), n


def card_features(r, k):
    prod = PRODUCTS[r]
    sn = f'SN-48{r}{k}'
    outer = bottle_outline()
    inner = outer.buffer(-WALL, join_style=2)
    wall = outer.difference(inner)
    # open mouth: no wall across the top of the neck
    wall = wall.difference(box(BX - NECK_W / 2 + WALL, Y_MOUTH - WALL - 0.01, BX + NECK_W / 2 - WALL, Y_MOUTH + 0.01))
    feats = [wall]
    fill = DEFECTS[k][1]
    y_in = inner.bounds[1]
    y_fill = y_in + (FILL_FULL - y_in) * fill / 100.0
    liquid = inner.intersection(box(0, 0, W, y_fill))
    if k != 3:                                            # label window + product name
        lab = box(*LABEL)
        liquid = liquid.difference(lab)
        lx0, ly0, lx1, ly1 = LABEL
        feats.append(text_poly(prod, (lx1 - lx0) - 4.0, 8.0, (lx0 + lx1) / 2, (ly0 + ly1) / 2))
    feats.append(liquid)
    if k != 2:                                            # cap on the neck finish
        feats.append(box(BX - CAP_W / 2, Y_MOUTH, BX + CAP_W / 2, Y_CAP))
    dm, n = datamatrix(sn)
    feats.append(dm)
    g = unary_union(feats).buffer(0)
    return g, dict(sn=sn, product=prod, defect=DEFECTS[k][0], fill=fill, byte10=r * 10 + k,
                   dm=sn, dm_size=f'{n}x{n}', fill_y=round(y_fill, 2))


def to_faces(geom):
    geoms = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    faces = []
    for p in geoms:
        p = p.simplify(0.02)
        ow = cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in list(p.exterior.coords)[:-1]], close=True)
        iws = [cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in list(i.coords)[:-1]], close=True) for i in p.interiors]
        faces.append(cq.Face.makeFromWires(ow, iws))
    return faces


def extrude(geom, z0, h):
    sols = [cq.Solid.extrudeLinear(f, cq.Vector(0, 0, h)).translate(cq.Vector(0, 0, z0)) for f in to_faces(geom)]
    return cq.Compound.makeCompound(sols)


def build(r, k):
    g, info = card_features(r, k)
    blank = cq.Workplane('XY').add(extrude(card_blank(), 0, T)).val()
    blank = cq.Workplane('XY').add(blank).edges('|Z').fillet(CORNER_R).val()
    red = extrude(g, T - INLAY, INLAY + RAISE)
    base = blank.cut(red)
    red_c = red.fuse() if hasattr(red, 'fuse') else red
    asm = cq.Assembly(name=info['sn'])
    asm.add(base, name=f"{info['sn']}_base_dark", color=cq.Color(0.08, 0.08, 0.1))
    asm.add(red, name=f"{info['sn']}_features_red", color=cq.Color(0.85, 0.08, 0.08))
    return asm, base, red, g, info


def red_names(sn, prod, red):
    """Name each red piece so the slicer's list reads SN-4801 red bottle / red code / red label S, O, D, A."""
    sols = red.Solids()
    code = [x for x in sols if x.BoundingBox().xmin > 55]
    rest = [x for x in sols if x.BoundingBox().xmin <= 55]
    rest.sort(key=lambda x: -x.Volume())
    out = [(f"{sn} red bottle", rest[0])] if rest else []
    letters = sorted(rest[1:], key=lambda x: x.BoundingBox().xmin)
    for i, x in enumerate(letters):
        ch = prod[i] if len(letters) == len(prod) else str(i + 1)
        out.append((f"{sn} red label {ch}", x))
    for i, x in enumerate(code):
        out.append((f"{sn} red code" + ("" if len(code) == 1 else f" {i + 1}"), x))
    return out


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    index = []
    for r, prod in enumerate(PRODUCTS):
        for k in DEFECTS:
            sn = f'SN-48{r}{k}'
            if only and sn not in only:
                continue
            asm, base, red, g, info = build(r, k)
            fn = f"{sn}_{prod}_{info['defect'].replace(' ', '-')}.step"
            asm.export(os.path.join(OUT, fn))
            # the same card as two files, one per colour: Bambu Studio colours a part, not a STEP body. Load both together and
            # answer Yes to "load as a single object with multiple parts", then give each part its filament
            d = os.path.join(OUT_PARTS, fn[:-5]); os.makedirs(d, exist_ok=True)
            dark, rc = cq.Color(0.08, 0.08, 0.1), cq.Color(0.85, 0.08, 0.08)
            a1 = cq.Assembly(name=f"{sn}_base_file"); a1.add(base, name=f"{sn} base", color=dark)   # the names are what the slicer lists
            a1.export(os.path.join(d, f"{sn}_1_base_dark.step"))
            a2 = cq.Assembly(name=f"{sn}_red_file")
            for nm, sol in red_names(sn, prod, red):
                a2.add(sol, name=nm, color=rc)
            a2.export(os.path.join(d, f"{sn}_2_features_red.step"))
            info['file'] = fn
            info['red_volume_mm3'] = round(red.Volume(), 1)
            index.append(info)
            print(fn, info['dm_size'], info['red_volume_mm3'])
    with open(os.path.join(OUT, 'cards.json'), 'w') as f:
        json.dump(index, f, indent=1)
