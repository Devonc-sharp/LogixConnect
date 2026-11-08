"""Lay every hopper part out on one Bambu H2D plate (325 x 320 mm), each in its print orientation, as a 3MF."""
import importlib.util, os, zipfile
import cadquery as cq
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('h', os.path.join(HERE, 'make_hopper.py')); h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)
BED_X, BED_Y = 325.0, 320.0

def place(w, rot=None, x=0, y=0):
    s = w.val() if hasattr(w, 'val') else w
    for ax, ang in (rot or []):
        s = s.rotate(cq.Vector(0, 0, 0), cq.Vector(*ax), ang)
    b = s.BoundingBox(); return s.translate(cq.Vector(x - b.xmin, y - b.ymin, -b.zmin))

P = [('Base, magazine', place(h.base_a(), None, 0, 0)),
     ('Gate 5.0 (bottle cards)', place(h.gate(5.0), [((0, 1, 0), 90)], 250, 0)),
     ('Base, nest and chute', place(h.base_b(), None, 0, 87)),
     ('Shuttle plate (face down)', place(h.shuttle_plate(0), [((1, 0, 0), 180)], 134, 92)),
     ('Shuttle grip (top down, pegs up)', place(h.grip(0), [((1, 0, 0), 180)], 281, 92)),
     ('Exit tray', place(h.tray(), [((0, 0, 1), 90)], 0, 174)),
     ('Gate 3.0 (lot cards)', place(h.gate(3.0), [((0, 1, 0), 90)], 198, 174))]

if __name__ == '__main__':
    X = max(s.BoundingBox().xmax for _, s in P); Y = max(s.BoundingBox().ymax for _, s in P)
    assert X <= BED_X and Y <= BED_Y, (X, Y)
    for i, (n, a) in enumerate(P):
        for m, b in P[i + 1:]:
            assert a.intersect(b).Volume() == 0, (n, m)
    ox, oy = (BED_X - X) / 2, (BED_Y - Y) / 2
    f = lambda v: f'{round(v, 4):g}'
    objs, items = [], []
    for i, (n, s) in enumerate(P, 1):
        V, T = s.tessellate(0.02, 0.2)
        vx = ''.join(f'<vertex x="{f(p.x + ox)}" y="{f(p.y + oy)}" z="{f(p.z)}"/>' for p in V)
        tx = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in T)
        objs.append(f'<object id="{i}" type="model" name="{n}"><mesh><vertices>{vx}</vertices><triangles>{tx}</triangles></mesh></object>')
        items.append(f'<item objectid="{i}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             '<metadata name="Title">LogixConnect card hopper, one plate</metadata><metadata name="Application">Logix Connect</metadata>'
             f'<resources>{"".join(objs)}</resources><build>{"".join(items)}</build></model>')
    cfg = '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + '\n'.join(
        f'<object id="{i}">\n<metadata key="name" value="{n}"/>\n<metadata key="extruder" value="1"/>\n</object>' for i, (n, _) in enumerate(P, 1)) + '\n</config>\n'
    types = ('<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
             '<Default Extension="config" ContentType="text/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    out = os.path.join(HERE, 'hopper', 'hopper_one_plate.3mf')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', types); z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', model); z.writestr('Metadata/model_settings.config', cfg)
    print('plate', round(X, 1), 'x', round(Y, 1), 'on', BED_X, 'x', BED_Y, '; tallest', round(max(s.BoundingBox().zmax for _, s in P), 1))
    for n, s in P:
        b = s.BoundingBox(); print(f'  {n:34s} {b.xlen:6.1f} x {b.ylen:5.1f} x {b.zlen:5.1f}')
