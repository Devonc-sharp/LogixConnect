"""Renders every card two ways and checks it the way the camera will:
  colour  - dark base + red features as printed
  camera  - monochrome through the red band-pass filter (red reads bright, the base dark)
The camera view is decoded (DataMatrix via zxing-cpp) and the label window OCR'd (tesseract)."""
import os, sys, json, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import MultiPolygon
import zxingcpp
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_cards as mc

PX = 8                                    # px per mm
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'preview')
os.makedirs(OUT, exist_ok=True)


def raster(geom, fg, bg, img=None):
    w, h = int(mc.W * PX), int(mc.H * PX)
    if img is None:
        img = Image.new('RGB', (w, h), bg)
    d = ImageDraw.Draw(img)
    geoms = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    for p in geoms:
        tr = lambda cs: [(x * PX, (mc.H - y) * PX) for x, y in cs]
        d.polygon(tr(p.exterior.coords), fill=fg)
        for i in p.interiors:
            d.polygon(tr(i.coords), fill=bg)
    return img


def card_images(r, k):
    g, info = mc.card_features(r, k)
    blank = mc.card_blank()
    paper = (235, 235, 235)
    col = raster(blank, (28, 30, 36), paper)
    col = raster(g, (205, 30, 30), (28, 30, 36), col)
    cam = raster(blank, (22, 22, 22), (8, 8, 8))           # base (and the bench behind) dark through the red filter
    cam = raster(g, (225, 225, 225), (22, 22, 22), cam)
    return col, cam, info


def check(cam, info):
    res = zxingcpp.read_barcodes(cam.convert('L'))
    dm = [x.text for x in res if str(x.format).replace(' ', '') == 'DataMatrix']
    ocr = ''
    if info['defect'] != 'no label':
        x0, y0, x1, y1 = mc.LABEL
        crop = cam.convert('L').crop((int(x0 * PX), int((mc.H - y1) * PX), int(x1 * PX), int((mc.H - y0) * PX)))
        crop = Image.eval(crop, lambda v: 255 - v)          # dark text on light for tesseract
        crop = crop.resize((crop.width, crop.height))
        p = os.path.join(OUT, '_ocr.png'); crop.save(p)
        ocr = subprocess.run(['tesseract', p, '-', '--psm', '7', '-c', 'tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'],
                             capture_output=True, text=True).stdout.strip()
        os.remove(p)
    return dm[0] if dm else '', ocr


if __name__ == '__main__':
    rows = []
    sheet_col, sheet_cam = [], []
    for r, prod in enumerate(mc.PRODUCTS):
        for k in mc.DEFECTS:
            col, cam, info = card_images(r, k)
            dm, ocr = check(cam, info)
            ok = dm == info['sn'] and (ocr == info['product'] or info['defect'] == 'no label')
            rows.append((info['sn'], prod, info['defect'], info['byte10'], dm, ocr, 'OK' if ok else 'FAIL'))
            sheet_col.append((col, info)); sheet_cam.append((cam, info))
            print(*rows[-1])
    # contact sheets: 5 products down, 4 defects across
    def sheet(items, name, bg):
        tw, th = int(mc.W * PX * 0.5), int(mc.H * PX * 0.5)
        pad = 14
        S = Image.new('RGB', (4 * (tw + pad) + pad, 5 * (th + pad + 18) + pad), bg)
        d = ImageDraw.Draw(S)
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
        for i, (im, info) in enumerate(items):
            r, c = divmod(i, 4)
            x, y = pad + c * (tw + pad), pad + r * (th + pad + 18)
            S.paste(im.resize((tw, th), Image.LANCZOS), (x, y + 18))
            d.text((x, y), f"{info['sn']}  {info['product']} · {info['defect']}  (byte 10 = {info['byte10']})", font=f,
                   fill=(30, 30, 30) if bg[0] > 128 else (230, 230, 230))
        S.save(os.path.join(OUT, name))
    sheet(sheet_col, 'cards-colour.png', (245, 245, 245))
    sheet(sheet_cam, 'cards-camera.png', (40, 40, 40))
    sheet_col[0][0].save(os.path.join(OUT, 'SN-4801-colour.png'))
    sheet_cam[0][0].save(os.path.join(OUT, 'SN-4801-camera.png'))
    json.dump(rows, open(os.path.join(OUT, 'check.json'), 'w'), indent=1)
    print('fails:', sum(1 for x in rows if x[-1] != 'OK'))
