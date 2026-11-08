"""Logix Connect calibration plate: a checkerboard for In-Sight's grid calibration, same footprint as the bottle cards.

100 x 70 x 4 mm, the 10 mm keyed corner top right, so it drops into the card nest and its top face sits at the
height of a card's base surface (calibrate at the plane you measure in).
Squares 5.00 mm, 16 x 12 (80 x 60 mm), inlaid flush 0.6 mm (three 0.2 mm layers): a flat top, no raised edges to throw
shadows. Light squares red (bright through the red filter), base dark. No fiducial: the grid's origin is the vertex
In-Sight picks. Underside engraved with the pitch.
Each red square is 0.05 mm smaller per side so neighbours only meet at a gap, not at a shared corner (a shared corner is
not a valid solid); the vertex positions are unchanged.
"""
import os, math, zipfile
import cadquery as cq
from shapely.geometry import Polygon, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'calplate')
W, H, T = 100.0, 70.0, 4.0
KEY, CORNER_R = 10.0, 2.0
PITCH, NX, NY = 5.0, 16, 12
INLAY = 0.6
SHRINK = 0.05
ENGRAVE = 0.4
X0, Y0 = (W - NX * PITCH) / 2, (H - NY * PITCH) / 2
NAME = f'CAL-{PITCH:.0f}mm'
FONT = FontProperties(fname='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')


def blank():
    return box(0, 0, W, H).difference(Polygon([(W - KEY, H), (W, H), (W, H - KEY)]))


def squares():
    out = []
    for j in range(NY):
        for i in range(NX):
            if (i + j) % 2 == 0:
                x, y = X0 + i * PITCH, Y0 + j * PITCH
                out.append(box(x + SHRINK, y + SHRINK, x + PITCH - SHRINK, y + PITCH - SHRINK))
    return out


def text_poly(s, h, cx, cy):
    tp = TextPath((0, 0), s, size=10, prop=FONT)
    polys = []
    for poly in tp.to_polygons():
        if len(poly) >= 3:
            polys.append(Polygon(poly))
    # even-odd fill: letters with holes
    geom = None
    for p in sorted(polys, key=lambda p: -p.area):
        p = p.buffer(0)
        if geom is None:
            geom = p
        elif geom.contains(p):
            geom = geom.difference(p)
        else:
            geom = geom.union(p)
    b = geom.bounds
    sc = h / 10 * 1.0
    geom = affinity.scale(geom, sc, sc, origin=(0, 0))
    b = geom.bounds
    geom = affinity.translate(geom, cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2)
    return affinity.scale(geom, -1, 1, origin=(cx, cy))   # mirrored: it reads right way round from underneath


def faces(geom):
    gs = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    fs = []
    for p in gs:
        p = p.simplify(0.01)
        ow = cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in list(p.exterior.coords)[:-1]], close=True)
        iws = [cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in list(i.coords)[:-1]], close=True) for i in p.interiors]
        fs.append(cq.Face.makeFromWires(ow, iws))
    return fs


def prism(geom, z0, h):
    return [cq.Solid.extrudeLinear(f, cq.Vector(0, 0, h)).translate(cq.Vector(0, 0, z0)) for f in faces(geom)]


def mesh_of(shape):
    v, t = shape.tessellate(0.01, 0.2)
    return [(p.x, p.y, p.z) for p in v], t


def write_3mf(path, parts):
    """parts: list of (name, extruder, [shapes]). One object of components, each part given its filament."""
    f = lambda x: f'{round(x, 4):g}'
    objs, comps, cfg = [], [], []
    for i, (nm, ext, shapes) in enumerate(parts, 1):
        V, Tr = [], []
        for s in shapes:
            v, t = mesh_of(s)
            b = len(V); V += v; Tr += [(a + b, c + b, d + b) for a, c, d in t]
        vx = ''.join(f'<vertex x="{f(x)}" y="{f(y)}" z="{f(z)}"/>' for x, y, z in V)
        tx = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in Tr)
        objs.append(f'<object id="{i}" type="model"><mesh><vertices>{vx}</vertices><triangles>{tx}</triangles></mesh></object>')
        comps.append(f'<component objectid="{i}"/>')
        cfg.append(f'<part id="{i}" subtype="normal_part">\n<metadata key="name" value="{nm}"/>\n<metadata key="extruder" value="{ext}"/>\n</part>')
    oid = len(parts) + 1
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<metadata name="Title">{NAME}</metadata><metadata name="Application">Logix Connect</metadata><resources>{"".join(objs)}'
             f'<object id="{oid}" type="model"><components>{"".join(comps)}</components></object></resources>'
             f'<build><item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/></build></model>')
    conf = (f'<?xml version="1.0" encoding="UTF-8"?>\n<config>\n<object id="{oid}">\n<metadata key="name" value="{NAME}"/>\n'
            f'<metadata key="extruder" value="1"/>\n' + '\n'.join(cfg) + '\n</object>\n</config>\n')
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
             '<Default Extension="config" ContentType="text/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', types); z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', model); z.writestr('Metadata/model_settings.config', conf)


if __name__ == '__main__':
    os.makedirs(os.path.join(OUT, 'step_parts'), exist_ok=True)
    sq = squares()
    plate = cq.Workplane('XY').add(prism(blank(), 0, T)[0]).edges('|Z').fillet(CORNER_R).val()
    red = prism(unary_union(sq), T - INLAY, INLAY)
    label = text_poly(f'LOGIX CONNECT  CAL GRID {PITCH:.2f} mm  {NX}x{NY}', 3.6, W / 2, H / 2)
    cut = cq.Compound.makeCompound(red + prism(label, 0, ENGRAVE))
    base = plate.cut(cut)
    dark, rc = cq.Color(0.08, 0.08, 0.1), cq.Color(0.85, 0.08, 0.08)
    asm = cq.Assembly(name=NAME); asm.add(base, name=f'{NAME}_base_dark', color=dark)
    asm.add(cq.Compound.makeCompound(red), name=f'{NAME}_squares_red', color=rc)
    asm.export(os.path.join(OUT, f'{NAME}.step'))
    a1 = cq.Assembly(name=f'{NAME}_base_file'); a1.add(base, name=f'{NAME} base', color=dark)
    a1.export(os.path.join(OUT, 'step_parts', f'{NAME}_1_base_dark.step'))
    a2 = cq.Assembly(name=f'{NAME}_red_file'); a2.add(cq.Compound.makeCompound(red), name=f'{NAME} red squares', color=rc)
    a2.export(os.path.join(OUT, 'step_parts', f'{NAME}_2_squares_red.step'))
    write_3mf(os.path.join(OUT, f'{NAME}.3mf'), [('Plate', 1, [base]), ('Squares', 2, red)])
    bb = base.BoundingBox()
    print('base valid', base.isValid(), 'vol', round(base.Volume(), 1), 'bbox', [round(x, 2) for x in (bb.xlen, bb.ylen, bb.zlen)])
    print('red squares', len(red), 'all valid', all(s.isValid() for s in red), 'vol', round(sum(s.Volume() for s in red), 1))
    print('grid origin x0,y0', X0, Y0, 'span', NX * PITCH, NY * PITCH)
