# Logix Connect bottle cards

20 vision cards for the bench camera, used by card mode on Level 8 (and Level 9 from v1.17).
Each card is 100 x 70 x 4 mm, with a keyed corner (10 mm chamfer, top right).
Every STEP file holds two bodies:

- `*_base_dark`: print it black or dark blue.
- `*_features_red`: print it red. It is inlaid 0.8 mm into the base and stands 0.6 mm proud.

Under the red band-pass filter, the red reads bright and the base reads dark.

## Card number SN-48RK

**R = product**

| R | Product |
|---|---------|
| 0 | SODA |
| 1 | WATER |
| 2 | MILK |
| 3 | JUICE |
| 4 | OIL |

**K = defect**

| K | Defect |
|---|--------|
| 1 | good |
| 2 | no cap |
| 3 | no label |
| 4 | short fill (70 %) |

**Inspection_Results byte 10 = R*10 + K.** SODA cards are 1-4, which is what Level 8 already reads. WATER cards are 11-14, MILK 21-24, JUICE 31-34 and OIL 41-44.

## What the camera job reads

All dimensions are in mm, measured from the card's bottom-left corner.

- **Bottle outline:** 1.2 mm wall, open mouth. Use it to locate the part (PatMax/edges). The bottle centre line is at x 27.
- **Cap:** 18 x 7 at y 59-66. Present means bright. It is missing on K=2.
- **Liquid:**
  - The fill edge is the top of the bright area inside the bottle.
  - The interior bottom is at y 6.2.
  - The 100 % line is at y 40, and 70 % is at y 29.9.
  - Fill % = (edge - 6.2) / 33.8 * 100.
- **Label window:**
  - Dark rectangle at x 11-43, y 12-27, cut out of the liquid.
  - It holds the product name in red (DejaVu Sans Bold, the same letter size on every card), so one trained OCR font covers all five.
  - It is missing on K=3, where the liquid runs straight through.
- **DataMatrix:**
  - ECC200, 12x12, 1.5 mm modules, 2-module bright quiet zone, centred at (75, 35).
  - Dark modules on a bright pad (normal polarity once the red reads bright).
  - It encodes `SN-48RK`. Byte 10 = the last two digits as a number.

## Files

- `step_parts/`: one folder per card with two STEP files, base and features (for the printer).
- `step/`: one STEP per card with both bodies, e.g. `SN-4804_SODA_short-fill.step`. `cards.json` lists them all.
- `preview/`:
  - `cards-colour.png`: as printed.
  - `cards-camera.png`: through the red filter.
  - 3D renders from the STEP files.
  - `check.json`: every card decoded and OCR'd from its camera view.
- `make_cards.py` builds the STEP files. `preview.py` renders the previews and checks them. Needs CadQuery, shapely, ppf-datamatrix, zxing-cpp and tesseract.

## Printing (Bambu H2D, 0.4 mm nozzle)

Bambu Studio colours parts, not the bodies inside one STEP, so use the two-file version of each card in `step_parts/`:

1. Open the card's folder, e.g. `step_parts/SN-4801_SODA_good/`.
2. Select **both** files (`SN-4801_1_base_dark.step` and `SN-4801_2_features_red.step`) and drag them onto the plate together.
3. Answer **Yes** to "Load these files as a single object with multiple parts?".
4. In the Objects list, expand the card. The parts are named: `SN-4801 base` gets your dark filament; every `SN-4801 red …` piece (bottle, label letters, code) gets red. Shift-click to select all the red rows, right-click → Change filament.
5. Print face up, with 0.2 mm layers or finer. Each 1.2 mm wall is three lines.

The single files in `step/` hold both bodies, for CAD.

## Calibration plate (`calplate/`, `make_calplate.py`)

A checkerboard for In-Sight's grid calibration, so the camera's tools report in mm.

- Same footprint as the bottle cards: 100 x 70 x 4 mm with the 10 mm keyed corner. It sits in the card nest, and its top face is at the height of a card's base, which is the plane the camera measures in.
- Grid: 16 x 12 squares of 5.00 mm (80 x 60 mm), starting at x 10, y 5 (mm from the bottom-left corner). No fiducial, so In-Sight picks the origin.
- The light squares are red, inlaid **flush**, 0.6 mm deep. The top is flat, with no raised edges to throw shadows under the low-angle light. Each square is 0.05 mm smaller per side, so neighbouring squares don't share a corner; the vertex positions are unchanged.
- The underside is engraved "LOGIX CONNECT CAL GRID 5.00 mm 16x12".
- Files:
  - `CAL-5mm.3mf`: opens in Bambu Studio already in two colours (Plate = filament 1, Squares = filament 2).
  - `CAL-5mm.step`: both bodies in one file.
  - `step_parts/`: one file per colour.
- Print face up, with 0.2 mm layers.
- Measure 10 squares (50 mm) with calipers and enter the measured pitch in the calibration, not 5.00. Printers run a little off in XY.

## Card hopper and slider (`hopper/`, `make_hopper.py`)

A gravity magazine and a push shuttle. One push carries the bottom card into the nest under the camera, and the same push shoves the card already in the nest down a chute into a tray. The nest sits under the CCS FPQ3-120 low-angle light, whose stand straddles the track.

- **Shuttle:** a 1.8 mm plate, thinner than any card, so it pushes only the bottom card. It runs on two ribs in grooves in the floor.
  - Home: the ribs reach the closed back end of the grooves.
  - Full stroke: the grip meets the magazine's back wall. That leaves the card in the nest at x 120–220 mm, centred at x 170.
- **Light:** it spans x 110–240 with its emitting face at Z 64, about 34 mm over a card. It clears the magazine by 2 mm and the gate by 5 mm. The 88 mm window sees x 126–214 of the card.
- **Gate:** a swappable insert at the front of the magazine. `gate_bottle-cards-5.0mm` is for the bottle cards (4.6 mm with their print); `gate_lot-cards-3.0mm` is for the Level 11 cards (2.6 mm). The gap passes one card and holds back the next.
- **Key:** a prism in the magazine's front corner on the +y side. A card loaded with its cut corner the wrong way won't sit flat. The prism starts above the bottom card, so it never blocks the one being pushed.
- **Height:** the card plane is 25 mm above the baseboard. Set the light's posts to keep your working distance over the card, and lay the calibration plate in the nest to calibrate at the card's height.
- **Chute and tray:** the chute runs about 30° down from the end of the floor (x 225–246). The tray starts at x 248, past the stand's legs, and is 12 mm tall. Slide it sideways to put GOOD or REJECT under the chute.
- **Parts:**
  1. Base with magazine: 242 mm.
  2. Base with nest and chute: 126 mm, joins part 1 with a dovetail.
  3. Shuttle plate: print it face down (ribs up).
  4. Shuttle grip: print it top down, pegs up. Glue its three 4 mm pegs into the plate's holes.
  5. The two gates, printed flat.
  6. Exit tray.
- **One plate:** `hopper_one_plate.3mf` lays out all seven pieces in print orientation in 311 × 294 mm, on the H2D's 325 × 320 single-nozzle plate. Nothing needs support. The bases are solid in the model, so set infill to about 15 %.
- **Assembly:** glue the grip on, slide the shuttle into the grooves from the front, then fit the nest half.
- **Checked:** every part against the light and the four leg envelopes from `hopper_with_light.step`, at home and at full stroke, with the tray in both positions. Nothing touches.
