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

- `step/`: one STEP per card, e.g. `SN-4804_SODA_short-fill.step`. `cards.json` lists them all.
- `preview/`:
  - `cards-colour.png`: as printed.
  - `cards-camera.png`: through the red filter.
  - 3D renders from the STEP files.
  - `check.json`: every card decoded and OCR'd from its camera view.
- `make_cards.py` builds the STEP files. `preview.py` renders the previews and checks them. Needs CadQuery, shapely, ppf-datamatrix, zxing-cpp and tesseract.

## Printing (Bambu H2D, 0.4 mm nozzle)

1. Import a STEP, and answer *yes* to loading it as one object with multiple parts.
2. Give the base part a dark filament and the features part red.
3. Print face up, with 0.2 mm layers or finer. Each 1.2 mm wall is three lines.
