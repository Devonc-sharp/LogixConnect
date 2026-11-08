"""Logix Connect card hopper and slider: a gravity magazine of cards, a push shuttle, a nest under the camera, an exit tray.

x runs along the push (+x toward the camera), y across the card (0 = track centre), z up from the baseboard. Cards travel
long side first (100 mm along x, 70 across). One push carries the bottom card out of the magazine, under the gate, into the
nest; the same push shoves the card already in the nest off the end into the tray.

How it singles out one card: the shuttle is a 1.8 mm plate, thinner than any card, so it pushes only the bottom card's
trailing edge. The gate at the front of the magazine leaves a gap one card high (+0.4 mm): the bottom card goes under it,
the one above it is held back. On the way home the plate slides out from under the stack and the next card drops.
Two gate inserts: 5.0 mm for the bottle cards (4.6 mm with their raised print), 3.0 mm for the Level 11 lot cards (2.6 mm).
Stops: home when the shuttle's ribs reach the closed back end of their grooves (the plate's face 1 mm behind the stack);
full stroke when the grip meets the magazine's back wall (the face at x 120: the card in the nest at x 120..220, centred at
x 170 under the CCS FPQ3-120, whose stand straddles the track; the light spans x 110..240, 2 mm clear of the magazine).
The grooves are open at the joint: slide the shuttle in from the front, then fit the nest half.
"""
import os
import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'hopper')

CARD_L, CARD_W = 100.0, 70.0
CH_W = 71.0                 # channel between the side walls
WALL = 4.0
ZF = 25.0                   # floor top above the baseboard: the card plane
FLOOR = 4.0                 # floor plate thickness (z ZF-FLOOR .. ZF)
SKIRT = 3.0
MAG_H = 60.0                # magazine walls above the floor (13 bottle cards, 23 lot cards)
LOW_H = 3.0                 # guide walls elsewhere: low, out of the light and the camera's view
TS = 1.8                    # shuttle plate
SLOT_CLR = 0.6              # gap above the plate under the magazine's back wall
GROOVE_Y, GROOVE_W, GROOVE_D = 20.0, 6.0, 2.5
RIB_W, RIB_H = 5.4, 2.3
GATES = {'bottle-cards-5.0mm': 5.0, 'lot-cards-3.0mm': 3.0}
KEY_LEG = 7.0               # key prism in the magazine's front-left corner (+y): the card's 10 mm cut corner clears it
X_BACK = -110.0             # back of the base
X_SPLIT = 120.0             # the base prints in two pieces joined by a dovetail here (230 and 95 mm long)
X_MAG0, X_MAG1 = 0.0, 101.0 # magazine cavity
X_GATE0, X_GATE1 = 101.0, 105.0
X_END = 225.0               # end of the flat floor: the nest holds the card at x 120..220, centred at 170 under the light
RAMP_L, RAMP_DROP = 21.0, 12.0   # then a chute, about 30 degrees down, that tips the pushed-out card into the tray
PLATE_L = 124.0             # shuttle plate length behind its pushing face: full stroke puts the face at x 120
GRIP_L, GRIP_H = 15.0, 14.0
GROOVE_X0 = -106.0          # the grooves stop here: the ribs meet the end at home (the plate's face at x -1)
RIB_BACK = 105.0            # ribs run from face-105 to face-1
TRAY_X0 = 248.0             # past the light stand's legs (they end at x 246.5)
TRAY_H = 12.0
CLR = 0.2

def bx(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))

def hollow_base(x0, x1):
    """The base under the floor: solid, so it prints with no bridging; the slicer's infill (15 % is plenty) does the hollowing."""
    hw = CH_W / 2 + WALL
    return bx(x0, x1, -hw, hw, 0, ZF)

def walls(x0, x1, h):
    hw = CH_W / 2
    return bx(x0, x1, -hw - WALL, -hw, ZF, ZF + h).union(bx(x0, x1, hw, hw + WALL, ZF, ZF + h))

def grooves(x0, x1):
    g = None
    for s in (-1, 1):
        t = bx(x0, x1, s * GROOVE_Y - GROOVE_W / 2, s * GROOVE_Y + GROOVE_W / 2, ZF - GROOVE_D, ZF + 1)
        g = t if g is None else g.union(t)
    return g

def dovetail(grow=0.0):
    """Plan-view dovetail on the split line, through the base's full height, between the shuttle grooves."""
    n, w, L = 9.0 + grow, 13.0 + grow, 12.0
    pts = [(X_SPLIT - 0.01, -n), (X_SPLIT + L + grow, -w), (X_SPLIT + L + grow, w), (X_SPLIT - 0.01, n)]
    return cq.Workplane('XY').polyline(pts).close().extrude(ZF - 0.01)

def gate_slots():
    hw = CH_W / 2
    return bx(X_GATE0 - CLR, X_GATE1 + CLR, hw - 0.1, hw + 2.0, ZF, ZF + MAG_H + 1).union(
        bx(X_GATE0 - CLR, X_GATE1 + CLR, -hw - 2.0, -hw + 0.1, ZF, ZF + MAG_H + 1))

def base_a():
    b = hollow_base(X_BACK, X_SPLIT)
    hw = CH_W / 2
    b = b.union(walls(X_BACK, X_MAG0 - WALL, LOW_H)).union(walls(X_MAG0 - WALL, X_GATE1 + 3, MAG_H)).union(walls(X_GATE1 + 3, X_SPLIT, LOW_H))
    back = bx(X_MAG0 - WALL, X_MAG0, -hw, hw, ZF + TS + SLOT_CLR, ZF + MAG_H)          # the magazine's back wall, open under it for the plate
    b = b.union(back)
    b = b.union(bx(X_SPLIT - 12, X_SPLIT, -hw - WALL, hw + WALL, 0, ZF - FLOOR))        # solid around the joint
    b = b.union(dovetail())
    b = b.cut(gate_slots())
    b = b.cut(grooves(GROOVE_X0, X_SPLIT + 20))   # open at the joint: slide the shuttle in from the front before the nest half goes on
    b = b.union(key_prism(max(GATES.values())))   # above the thickest bottom card, so it only keys the cards waiting above
    return b

def key_prism(gap):
    hw = CH_W / 2
    pts = [(X_MAG1, hw), (X_MAG1 - KEY_LEG, hw), (X_MAG1, hw - KEY_LEG)]
    return cq.Workplane('XY').polyline(pts).close().extrude(MAG_H - gap - 1).translate((0, 0, ZF + gap + 1))

def chute():
    """From the end of the floor down about 30 degrees toward the tray, with low side walls; it ends over the tray."""
    hw = CH_W / 2
    prof = [(X_END - 0.01, ZF), (X_END, ZF), (X_END + RAMP_L, ZF - RAMP_DROP), (X_END + RAMP_L, 0), (X_END - 0.01, 0)]   # solid to the plate: no overhang under the slope
    floor = cq.Workplane('XZ').polyline(prof).close().extrude(-(hw + WALL)).union(cq.Workplane('XZ').polyline(prof).close().extrude(hw + WALL))
    sides = None
    for sg in (-1, 1):
        y0, y1 = (hw, hw + WALL) if sg > 0 else (-hw - WALL, -hw)
        wp = [(X_END, ZF + LOW_H), (X_END + RAMP_L, ZF - RAMP_DROP + LOW_H), (X_END + RAMP_L, ZF - RAMP_DROP), (X_END, ZF)]
        w = cq.Workplane('XZ').polyline(wp).close().extrude(-(y1 - y0)).translate((0, y0, 0))
        sides = w if sides is None else sides.union(w)
    return floor.union(sides)

def base_b():
    b = hollow_base(X_SPLIT, X_END)
    b = b.union(walls(X_SPLIT, X_END, LOW_H)).union(chute())
    b = b.union(bx(X_SPLIT, X_SPLIT + 18, -CH_W / 2 - WALL, CH_W / 2 + WALL, 0, ZF - FLOOR))
    b = b.cut(dovetail(CLR))
    
    return b

PEG_D, PEG_H = 4.0, 6.0
PEGS = [(-20.0,), (0.0,), (20.0,)]

def shuttle_plate(face=0.0):
    """Plate and ribs: prints face down (the plate's top on the bed), ribs up. The plate runs on under the grip."""
    hw = 35.0
    p = bx(face - PLATE_L - GRIP_L, face, -hw, hw, ZF, ZF + TS)
    for s in (-1, 1):
        p = p.union(bx(face - RIB_BACK, face - 1, s * GROOVE_Y - RIB_W / 2, s * GROOVE_Y + RIB_W / 2, ZF - RIB_H, ZF))
    for (y,) in PEGS:
        p = p.cut(cq.Workplane('XY').circle(PEG_D / 2 + 0.15).extrude(TS + 2).translate((face - PLATE_L - GRIP_L / 2, y, ZF - 1)))
    return p

def grip(face=0.0):
    """The grip: a block on the plate's back end with three pegs down through the plate (glue them). Its front face is the
    full-stroke stop against the magazine's back wall; prints standing on its top face, pegs up."""
    hw = 35.0
    g = bx(face - PLATE_L - GRIP_L, face - PLATE_L, -hw, hw, ZF + TS, ZF + GRIP_H)
    g = g.cut(bx(face - PLATE_L - GRIP_L - 1, face - PLATE_L - 5, -22, 22, ZF + 4, ZF + GRIP_H + 1))   # finger pocket
    for (y,) in PEGS:
        g = g.union(cq.Workplane('XY').circle(PEG_D / 2).extrude(TS).translate((face - PLATE_L - GRIP_L / 2, y, ZF)))
    return g

def shuttle(face=0.0):
    return shuttle_plate(face).union(grip(face))

def gate(gap):
    hw = CH_W / 2
    g = bx(X_GATE0, X_GATE1, -hw - 1.8, hw + 1.8, ZF + gap, ZF + MAG_H + 6)
    g = g.cut(bx(X_GATE0 - 1, X_GATE1 + 1, -12, 12, ZF + MAG_H - 4, ZF + MAG_H + 7))        # lift notch
    return g

def tray():
    """Two compartments side by side (y): slide it sideways to put GOOD or REJECT under the drop."""
    L, Wc, Hh, t = 120.0, 92.0, TRAY_H, 2.0
    x0 = TRAY_X0
    t_ = bx(x0, x0 + L, -Wc - t * 1.5, Wc + t * 1.5, 0, Hh)
    t_ = t_.cut(bx(x0 + t, x0 + L - t, -Wc - t / 2, -t / 2, t, Hh + 1)).cut(bx(x0 + t, x0 + L - t, t / 2, Wc + t / 2, t, Hh + 1))
    return t_

def card(x0, z0, th=4.6):
    return bx(x0, x0 + CARD_L, -CARD_W / 2, CARD_W / 2, z0, z0 + th)

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    parts = {'1_base_magazine': base_a(), '2_base_nest': base_b(), '3_shuttle_plate': shuttle_plate(0.0), '3_shuttle_grip': grip(0.0)}
    for nm, gp in GATES.items():
        parts[f'4_gate_{nm}'] = gate(gp)
    parts['5_exit_tray'] = tray()
    for nm, p in parts.items():
        s = p.val() if hasattr(p, 'val') else p
        bb = s.BoundingBox()
        print(f'{nm:28s} valid {s.isValid()} size {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}')
        cq.exporters.export(p, os.path.join(OUT, f'hopper_{nm}.step'))
        cq.exporters.export(p, os.path.join(OUT, f'hopper_{nm}.stl'), tolerance=0.02, angularTolerance=0.15)
    asm = cq.Assembly(name='card_hopper')
    cols = {'1': (0.25, 0.27, 0.3), '2': (0.25, 0.27, 0.3), '3': (0.47, 0.42, 0.85), '4': (0.85, 0.62, 0.2), '5': (0.55, 0.6, 0.65)}
    for nm, p in parts.items():
        if nm.startswith('4_gate_lot'):
            continue
        asm.add(p, name=nm, color=cq.Color(*cols[nm[0]]))
    for i in range(6):
        asm.add(card(X_MAG0 + 0.5, ZF + i * 4.6), name=f'card_stack_{i}', color=cq.Color(0.1, 0.1, 0.12))
    asm.add(card(120.5, ZF), name='card_in_nest', color=cq.Color(0.1, 0.1, 0.12))
    asm.export(os.path.join(OUT, 'hopper_assembly.step'))
    print('assembly ok')
