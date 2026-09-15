#!/usr/bin/env python3
"""HOLDFAST one-pager + BP-PUD-1 PCDI structural drawing.

Chemistry and numbers: Scout task d702c83f-8602-45a6-b98d-c7839808b7e2 only.
Visual still-life: Imagine. Structure: RDKit from Scout SMILES (Imagine's
freehand structure was the wrong connectivity and is not used).
Brand: blackpathlabs.com 2026-09-15 (paper #F5F5F1, ink #101112, path #1F3FBF).
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from PIL import Image as PILImage
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

ROOT = Path("/workspace/personal/artifacts/holdfast")
ROOT.mkdir(parents=True, exist_ok=True)

IMAGINE_PRODUCT = Path(
    "/home/ubuntu/swarm-host/grok-home/sessions/"
    "%2Fworkspace/01a0a5b9-6419-7a32-8e15-9c6aa65e0d5f/images/3.jpg"
)

# Scout d702c83f — do not invent a different molecule
PCDI_SMILES = "CC(C)(N=C=N)C1=CC=CC(C(C)(C)N=C=N)=C1"
# Bracket nitrogens so RDKit does not draw terminal =NH on the repeat unit
PCDI_SMILES_DRAW = "CC(C)([N]=C=[N])C1=CC=CC(C(C)(C)[N]=C=[N])=C1"
PCDI_NAME = "1,3-bis(1-carbodiimido-1-methylethyl)benzene"
PCDI_IUPAC_NOTE = "m-phenylene-bis(2-propylcarbodiimide) repeat"
KIT = "BP-PUD-1"
SOURCE_TASK = "d702c83f-8602-45a6-b98d-c7839808b7e2"

PAPER = HexColor("#F5F5F1")
INK = HexColor("#101112")
BLUE = HexColor("#1F3FBF")
MUTED = HexColor("#5A5C5E")
RULE = Color(16 / 255, 17 / 255, 18 / 255, alpha=0.14)
PANEL = Color(16 / 255, 17 / 255, 18 / 255, alpha=0.04)

pdfmetrics.registerFont(TTFont("Sans", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono", "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Mono-Bold", "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"))


def wrap_para(text: str, style: ParagraphStyle, width: float) -> Paragraph:
    p = Paragraph(text, style)
    p.wrapOn(None, width, 2000)
    return p


def draw_mark(c: canvas.Canvas, x: float, y: float, size: float) -> None:
    """Official BPL path mark (viewBox 0 0 512 512), y is bottom of the plate."""
    s = size / 512.0
    c.saveState()
    c.translate(x, y)
    c.scale(s, s)
    p = c.beginPath()
    p.roundRect(0, 0, 512, 512, 104)
    c.setFillColor(PAPER)
    c.setStrokeColor(RULE)
    c.setLineWidth(8)
    c.drawPath(p, fill=1, stroke=1)
    c.setLineCap(1)
    c.setLineJoin(1)
    c.setLineWidth(56)
    c.setStrokeColor(INK)
    c.line(80, 512 - 368, 206, 512 - 368)
    c.setStrokeColor(BLUE)
    c.line(206, 512 - 368, 306, 512 - 144)
    c.setStrokeColor(INK)
    c.line(306, 512 - 144, 432, 512 - 144)
    c.restoreState()


def render_pcdi_png_svg() -> tuple[Path, Path]:
    mol = Chem.MolFromSmiles(PCDI_SMILES_DRAW)
    if mol is None:
        raise SystemExit("Scout SMILES did not parse")
    Chem.rdDepictor.Compute2DCoords(mol)

    # N=C=N groups: atoms 3-4-5 and 14-15-16
    ncn = [3, 4, 5, 14, 15, 16]
    ncn_bonds = [3, 4, 14, 15]
    blue = (31 / 255, 63 / 255, 191 / 255)
    ink = (16 / 255, 17 / 255, 18 / 255)

    w, h = 2800, 1440
    highlight_atoms = ncn
    highlight_bonds = ncn_bonds
    atom_cols = {i: blue for i in ncn}
    bond_cols = {i: blue for i in ncn_bonds}

    def _draw(drawer):
        opts = drawer.drawOptions()
        opts.setBackgroundColour((245 / 255, 245 / 255, 241 / 255, 1))
        opts.bondLineWidth = 3.2
        opts.padding = 0.06
        opts.fixedBondLength = 42
        opts.minFontSize = 18
        opts.maxFontSize = 24
        drawer.DrawMolecule(
            mol,
            highlightAtoms=highlight_atoms,
            highlightBonds=highlight_bonds,
            highlightAtomColors=atom_cols,
            highlightBondColors=bond_cols,
        )
        drawer.FinishDrawing()

    drawer = rdMolDraw2D.MolDraw2DCairo(w, h)
    _draw(drawer)
    png_path = ROOT / "bp-pud-1-pcdi-core.png"
    png_path.write_bytes(drawer.GetDrawingText())
    crop_to_ink(png_path, pad=28)

    svg_drawer = rdMolDraw2D.MolDraw2DSVG(w, h)
    _draw(svg_drawer)
    svg_path = ROOT / "bp-pud-1-pcdi.svg"
    svg_path.write_text(svg_drawer.GetDrawingText())
    return png_path, svg_path


def crop_to_ink(path: Path, pad: int = 24, bg=(245, 245, 241), tol: int = 12) -> None:
    im = PILImage.open(path).convert("RGB")
    pix = im.load()
    w, h = im.size
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            r, g, b = pix[x, y]
            if abs(r - bg[0]) > tol or abs(g - bg[1]) > tol or abs(b - bg[2]) > tol:
                minx = min(minx, x)
                miny = min(miny, y)
                maxx = max(maxx, x)
                maxy = max(maxy, y)
    if maxx <= minx:
        return
    minx = max(0, minx - pad)
    miny = max(0, miny - pad)
    maxx = min(w, maxx + pad + 1)
    maxy = min(h, maxy + pad + 1)
    im.crop((minx, miny, maxx, maxy)).save(path)


def draw_cover(c: canvas.Canvas, path: Path, x: float, y: float, w: float, h: float) -> None:
    im = PILImage.open(path)
    iw, ih = im.size
    scale = max(w / iw, h / ih)
    nw, nh = iw * scale, ih * scale
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, w, h, 6)
    c.clipPath(p, stroke=0)
    c.drawImage(ImageReader(str(path)), x - (nw - w) / 2, y - (nh - h) / 2, width=nw, height=nh, mask="auto")
    c.restoreState()
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, h, 6, fill=0, stroke=1)


def molecule_stand_alone(core_png: Path) -> Path:
    """Labeled letter-landscape-ish stand-alone drawing, portrait-friendly 4:3."""
    out_pdf = ROOT / "bp-pud-1-pcdi.pdf"
    W, H = 11 * inch, 8.5 * inch  # landscape letter, stand-alone drop-in
    c = canvas.Canvas(str(out_pdf), pagesize=(W, H))
    c.setTitle("BP-PUD-1 polycarbodiimide crosslinker — Black Path Labs")
    c.setAuthor("Black Path Labs")
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    msize = 28
    draw_mark(c, 36, H - 36 - msize, msize)
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 13)
    c.drawString(36 + msize + 10, H - 36 - 12, "Black Path Labs")
    c.setFillColor(MUTED)
    c.setFont("Sans", 9)
    c.drawString(36 + msize + 10, H - 36 - 26, "MOL drawing  ·  kit BP-PUD-1  ·  Scout " + SOURCE_TASK[:8])
    c.setFillColor(BLUE)
    c.setFont("Sans-Bold", 9)
    c.drawRightString(W - 36, H - 36 - 14, "Do not use a different molecule")

    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.line(36, H - 72, W - 36, H - 72)

    c.setFillColor(INK)
    c.setFont("Sans-Bold", 22)
    c.drawString(36, H - 104, "Polycarbodiimide crosslinker")
    c.setFillColor(MUTED)
    c.setFont("Sans", 11)
    c.drawString(36, H - 122, PCDI_NAME)
    c.setFont("Sans", 10)
    c.drawString(36, H - 138, PCDI_IUPAC_NOTE + "  ·  Picassian XL-732 / Carbodilite E-02 type")

    img = ImageReader(str(core_png))
    iw, ih = PILImage.open(core_png).size
    left_w = 6.05 * inch
    left_h = H - 250
    scale = min(left_w / iw, left_h / ih)
    img_w, img_h = iw * scale, ih * scale
    c.drawImage(img, 36 + (left_w - img_w) / 2, 90 + (left_h - img_h) / 2, width=img_w, height=img_h)

    # legend panel
    lx = 36 + left_w + 16
    ly = 90
    lw = W - 36 - lx
    lh = left_h
    c.setFillColor(PANEL)
    c.setStrokeColor(RULE)
    c.roundRect(lx, ly, lw, lh, 8, fill=1, stroke=1)

    body = ParagraphStyle(
        "leg",
        fontName="Sans",
        fontSize=8.5,
        leading=12,
        textColor=INK,
    )
    head = ParagraphStyle(
        "legh",
        fontName="Sans-Bold",
        fontSize=9.5,
        leading=13,
        textColor=INK,
        spaceAfter=4,
    )
    muted = ParagraphStyle(
        "legm",
        fontName="Sans",
        fontSize=8,
        leading=11,
        textColor=MUTED,
    )
    mono = ParagraphStyle(
        "legx",
        fontName="Mono",
        fontSize=7,
        leading=10,
        textColor=INK,
    )

    y = ly + lh - 18
    items = [
        (head, "What this is"),
        (body, "The room-temperature crosslinker in kit <b>BP-PUD-1</b>. The film is a soft anionic aliphatic polyester polyurethane dispersion. This drawing is the polycarbodiimide repeat that ties that film to wool carboxyl groups."),
        (head, "How to read it"),
        (body, "<font color='#1F3FBF'><b>Blue</b></font> = carbodiimide (N=C=N), the group that adds to carboxyl on wool keratin. The aromatic ring is meta-substituted. Each arm is a gem-dimethyl spacer from m-TMXDI."),
        (head, "SMILES (Scout)"),
        (muted, "CC(C)(N=C=N)C1=CC=CC"),
        (muted, "(C(C)(C)N=C=N)=C1"),
        (head, "What it is not"),
        (body, "Not BP-CA-1 (ethyl 2-cyanoacrylate). Not BP-DA-1 (MDI / furfurylamine). Not a peptide, catechol, or tissue adhesive. Wool here is a fiber substrate."),
        (muted, "Facts and numbers from Scout task d702c83f, 2026-09-15. Structure drawn from that SMILES in RDKit, not from an image model."),
    ]
    pad = 14
    floor = ly + pad
    for style, text in items:
        p = Paragraph(text, style)
        w, h = p.wrap(lw - 2 * pad, 400)
        y -= h + 6
        if y < floor:
            break
        p.drawOn(c, lx + pad, y)

    c.setFillColor(MUTED)
    c.setFont("Sans", 7.5)
    c.drawString(36, 40, "Black Path Labs  ·  Winnipeg  ·  blackpathlabs.com")
    c.drawRightString(W - 36, 40, "Stand-alone structural drawing  ·  drop into HOLDFAST one-pager")
    c.showPage()
    c.save()
    return out_pdf


def mol_panel_png(core_png: Path, w_px: int, h_px: int) -> Path:
    """Composite a high-contrast structure panel so PDF rasterization cannot wash it out."""
    paper = (245, 245, 241)
    canvas_im = PILImage.new("RGB", (w_px, h_px), paper)
    mol = PILImage.open(core_png).convert("RGB")
    mw, mh = mol.size
    margin = 36
    caption = 52
    box_w, box_h = w_px - 2 * margin, h_px - margin - caption
    scale = min(box_w / mw, box_h / mh)
    nw, nh = int(mw * scale), int(mh * scale)
    mol = mol.resize((nw, nh), PILImage.Resampling.LANCZOS)
    x = (w_px - nw) // 2
    y = margin + (box_h - nh) // 2
    canvas_im.paste(mol, (x, y))
    out = ROOT / "onepager-mol-panel.png"
    canvas_im.save(out, "PNG")
    return out


def onepager(core_png: Path, product_jpg: Path) -> Path:
    out = ROOT / "holdfast-onepager.pdf"
    W, H = letter
    c = canvas.Canvas(str(out), pagesize=letter)
    c.setTitle("HOLDFAST — extra-sticky body glitter — Black Path Labs")
    c.setAuthor("Black Path Labs")
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    ML, MR = 0.48 * inch, 0.48 * inch
    y = H - 0.38 * inch

    # header
    msize = 22
    draw_mark(c, ML, y - msize, msize)
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 11)
    c.drawString(ML + msize + 8, y - 10, "Black Path Labs")
    c.setFillColor(MUTED)
    c.setFont("Sans", 8)
    c.drawString(ML + msize + 8, y - 21, "Performer cosmetics  ·  kit BP-PUD-1")
    c.setFillColor(BLUE)
    c.setFont("Sans-Bold", 8)
    c.drawRightString(W - MR, y - 10, "HOLDFAST")
    c.setFillColor(MUTED)
    c.setFont("Sans", 8)
    c.drawRightString(W - MR, y - 21, "One-pager  ·  15 Sep 2026")

    y -= 32
    c.setStrokeColor(RULE)
    c.setLineWidth(0.7)
    c.line(ML, y, W - MR, y)

    # title
    y -= 28
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 28)
    c.drawString(ML, y, "HOLDFAST")
    c.setFillColor(BLUE)
    c.setFont("Sans-Bold", 9)
    c.drawString(ML + 168, y + 6, "EXTRA-STICKY BODY GLITTER")

    y -= 16
    c.setFillColor(INK)
    c.setFont("Sans", 11)
    c.drawString(ML, y, "A soft film that holds PET glitter on skin and wool, then comes off in cold water.")

    y -= 14
    c.setFillColor(MUTED)
    c.setFont("Sans", 8)
    c.drawString(
        ML,
        y,
        "Chemistry from Scout MOL design d702c83f. Claims stop where that design stops. No wear-hour number was measured.",
    )

    # photo + molecule row
    y -= 10
    gap = 10
    photo_w = 4.15 * inch
    photo_h = 2.22 * inch
    mol_w = W - ML - MR - photo_w - gap
    mol_h = photo_h
    row_bottom = y - photo_h

    draw_cover(c, product_jpg, ML, row_bottom, photo_w, photo_h)

    panel = mol_panel_png(core_png, int(mol_w / inch * 220), int(mol_h / inch * 220))
    c.saveState()
    pth = c.beginPath()
    pth.roundRect(ML + photo_w + gap, row_bottom, mol_w, mol_h, 6)
    c.clipPath(pth, stroke=0)
    c.drawImage(ImageReader(str(panel)), ML + photo_w + gap, row_bottom, width=mol_w, height=mol_h)
    c.restoreState()
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.roundRect(ML + photo_w + gap, row_bottom, mol_w, mol_h, 6, fill=0, stroke=1)
    c.setFillColor(PAPER)
    c.rect(ML + photo_w + gap + 1, row_bottom + 1, mol_w - 2, 16, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont("Sans", 6.5)
    c.drawCentredString(
        ML + photo_w + gap + mol_w / 2,
        row_bottom + 6,
        "PCDI crosslinker  ·  N=C=N in blue  ·  Scout SMILES",
    )

    y = row_bottom - 16

    # benefits
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 9)
    c.drawString(ML, y, "On the body. On the wool.")
    y -= 6
    c.setStrokeColor(BLUE)
    c.setLineWidth(1.4)
    c.line(ML, y, ML + 36, y)

    bullets = [
        (
            "Holds through movement",
            "Once the film has set, glitter is meant to stay on skin and on wool instead of migrating. Wear hours were not measured. Do not read a timed all-night claim into that.",
        ),
        (
            "Flexes. Does not flake by design.",
            "Soft anionic aliphatic polyester PUD, minimum film-forming temperature under 15 °C. Wool can drape. A rigid bondline was rejected because it cracks and sheds.",
        ),
        (
            "Leaves when you wash it out",
            "Cold hand-wash after three days is the expected removal. Perchloroethylene sheds the flake. Machine or hot water is out — wool felts, and this film is not built for that.",
        ),
        (
            "Sets at room temperature",
            "Twenty-four hours at room temp. Optional 40 °C for twenty minutes. No 60 °C oven. Full carbodiimide crosslink takes 3–7 days.",
        ),
    ]
    col_w = (W - ML - MR - 18) / 2
    col_h = 70
    y -= 8
    for i, (title, body) in enumerate(bullets):
        col = i % 2
        row = i // 2
        x = ML + col * (col_w + 18)
        by = y - row * (col_h + 8) - col_h
        c.setFillColor(PAPER)
        c.setStrokeColor(RULE)
        c.roundRect(x, by, col_w, col_h, 6, fill=0, stroke=1)
        c.setFillColor(BLUE)
        c.setFont("Mono-Bold", 7)
        c.drawString(x + 10, by + col_h - 14, f"0{i+1}")
        c.setFillColor(INK)
        c.setFont("Sans-Bold", 9)
        c.drawString(x + 32, by + col_h - 15, title)
        style = ParagraphStyle("b", fontName="Sans", fontSize=8, leading=10.5, textColor=MUTED)
        p = Paragraph(body, style)
        pw, ph = p.wrap(col_w - 20, col_h - 28)
        p.drawOn(c, x + 10, by + col_h - 22 - ph)

    y = y - 2 * (col_h + 8) - 6

    # how it works
    hw_h = 108
    c.setFillColor(PANEL)
    c.setStrokeColor(RULE)
    c.roundRect(ML, y - hw_h, W - ML - MR, hw_h, 6, fill=1, stroke=1)
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 9)
    c.drawString(ML + 12, y - 16, "How it works")
    c.setFillColor(BLUE)
    c.setFont("Sans", 8)
    c.drawString(ML + 92, y - 16, "Plain language from BP-PUD-1. Not a different chemistry.")

    how = (
        "Print a thin coat of a soft waterborne polyurethane. Drop the flake onto the wet film. "
        "A polycarbodiimide (Picassian XL-732 or Carbodilite E-02, 4 % on polymer) ties the film "
        "to carboxyl groups on wool. A small dose of pre-hydrolyzed GPTMS helps the same film wet "
        "PET glitter at carboxyl and hydroxyl ends, and wool amine. Acrylic-lacquered glitter needs "
        "no extra flake primer. CPO is for polypropylene, not PET. APTES only if aluminum is exposed. "
        "The film stays soft so the garment can move. This is a textile binder used as a cosmetic coating, "
        "not a medical adhesive and not a cleared cosmetic formula."
    )
    style = ParagraphStyle("h", fontName="Sans", fontSize=8.2, leading=11.2, textColor=INK)
    p = Paragraph(how, style)
    pw, ph = p.wrap(W - ML - MR - 24, hw_h - 28)
    p.drawOn(c, ML + 12, y - 22 - ph)
    y -= hw_h + 12

    # spec strip
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 9)
    c.drawString(ML, y, "Spec  ·  mix, apply, cure")
    y -= 4
    specs = [
        ("Mix (wet)", "100 PUD : 4 XL-732 : 0.4 GPTMS"),
        ("PUD", "40% solids, pH 8-8.5, MFFT &lt;15C"),
        ("Apply", "Print thin film, drop flake"),
        ("Cure", "24h room temp · optional 40C / 20 min · no 60C oven"),
        ("Full CDI", "3–7 days at room temperature"),
        ("Wash", "Cold hand-wash after 3 days, expected. Perc sheds. Machine/hot: no."),
    ]
    colw = (W - ML - MR) / 3
    row_h = 32
    y -= 8
    for i, (k, v) in enumerate(specs):
        col = i % 3
        row = i // 3
        x = ML + col * colw
        by = y - (row + 1) * row_h
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        c.line(x, by, x + colw - 8, by)
        c.setFillColor(MUTED)
        c.setFont("Sans-Bold", 6.5)
        c.drawString(x, by + 20, k.upper())
        c.setFillColor(INK)
        c.setFont("Sans", 7.2)
        # wrap value if needed
        style = ParagraphStyle("s", fontName="Sans", fontSize=7.2, leading=9.2, textColor=INK)
        p = Paragraph(v, style)
        pw, ph = p.wrap(colw - 10, 24)
        p.drawOn(c, x, by + 4)

    y = y - 2 * row_h - 8

    # caveats — keep above the footer rule at 0.42"
    footer_top = 0.50 * inch
    cav_h = y - footer_top
    if cav_h < 56:
        cav_h = 56
    c.setStrokeColor(BLUE)
    c.setLineWidth(2)
    c.line(ML, y, ML, y - cav_h)
    c.setFillColor(INK)
    c.setFont("Sans-Bold", 8)
    c.drawString(ML + 10, y - 12, "What this page will not claim")
    cave = (
        "Scout did not measure wear hours, sweat, or mucous-membrane contact — so we do not. "
        "Not hypoallergenic. Not dermatologist-tested. Patch-test. GPTMS is an epoxy silane. "
        "Avoid eyes and mucous membranes. Not BP-CA-1 (wicks, stiffens, blooms, yellows wool) and not BP-DA-1 "
        "(60 °C, MDI respiratory sensitizer). Perc dry-clean sheds the flake. Full wash hold is expected after "
        "three days, not after the first night. Backup kit BP-ACR-1 (DAAM/ADH) if PUD is unavailable."
    )
    style = ParagraphStyle("c", fontName="Sans", fontSize=7.2, leading=9.6, textColor=MUTED)
    p = Paragraph(cave, style)
    pw, ph = p.wrap(W - ML - MR - 16, cav_h - 18)
    p.drawOn(c, ML + 10, y - 16 - ph)

    # footer
    c.setStrokeColor(RULE)
    c.setLineWidth(0.6)
    c.line(ML, 0.42 * inch, W - MR, 0.42 * inch)
    c.setFillColor(MUTED)
    c.setFont("Sans", 7)
    c.drawString(ML, 0.28 * inch, "Black Path Labs  ·  Winnipeg, MB  ·  blackpathlabs.com  ·  matt@blackpathlabs.com")
    c.drawRightString(W - MR, 0.28 * inch, "Source: Scout d702c83f  ·  visual still-life: Imagine  ·  structure: RDKit")

    c.showPage()
    c.save()
    return out


def raster(pdf: Path, prefix: str, dpi: int = 200) -> Path:
    os.system(f"pdftoppm -png -r {dpi} '{pdf}' '{prefix}'")
    # pdftoppm writes prefix-1.png
    produced = Path(f"{prefix}-1.png")
    if not produced.exists():
        # maybe prefix.png
        alt = Path(f"{prefix}.png")
        if alt.exists():
            return alt
        raise SystemExit(f"raster missing for {pdf}")
    return produced


def write_html(product: Path, mol: Path, onepager_png: Path, mol_png: Path) -> Path:
    html = ROOT / "holdfast-onepager.html"
    html.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>HOLDFAST extra-sticky body glitter — Black Path Labs</title>
<meta name="description" content="HOLDFAST is extra-sticky body glitter on a soft BP-PUD-1 polyurethane film. It is designed to hold PET flake on skin and wool, then come off in cold water. Chemistry from Scout kit BP-PUD-1.">
<link rel="canonical" href="https://www.blackpathlabs.com/">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{ --paper:#F5F5F1; --ink:#101112; --blue:#1F3FBF; --muted:#5A5C5E; --rule:rgba(16,17,18,.14); }}
html,body {{ margin:0; background:var(--paper); color:var(--ink);
  font:16px/1.5 "Liberation Sans","Helvetica Neue",Arial,sans-serif; }}
main {{ max-width: 52rem; margin: 0 auto; padding: 32px 24px 64px; }}
h1 {{ font-size: 2rem; letter-spacing:-0.03em; margin: 0 0 8px; }}
.lede {{ color:var(--muted); margin:0 0 24px; }}
img {{ max-width:100%; height:auto; border:1px solid var(--rule); border-radius:8px; }}
figcaption {{ color:var(--muted); font-size:13px; margin:8px 0 28px; }}
a {{ color:var(--blue); }}
</style>
</head>
<body>
<main>
<p>Black Path Labs</p>
<h1>HOLDFAST</h1>
<p class="lede">Extra-sticky body glitter. A soft film that holds PET glitter on skin and wool, then comes off in cold water.</p>
<figure>
<img src="{onepager_png.name}" alt="HOLDFAST letter-size one-pager, Black Path Labs branded, product photo of glitter on charcoal wool plus the BP-PUD-1 polycarbodiimide structure.">
<figcaption>Letter-size one-pager (portrait). Source PDF in this folder.</figcaption>
</figure>
<figure>
<img src="{mol_png.name}" alt="Skeletal structure of 1,3-bis(1-carbodiimido-1-methylethyl)benzene, the BP-PUD-1 polycarbodiimide crosslinker, carbodiimide groups highlighted.">
<figcaption>Stand-alone structural drawing of the Scout BP-PUD-1 polycarbodiimide crosslinker. SVG source in this folder.</figcaption>
</figure>
<p>Kit BP-PUD-1. Facts from Scout task d702c83f. Visual still-life by Imagine. Structure from Scout SMILES in RDKit.</p>
</main>
</body>
</html>
"""
    )
    return html


def main() -> None:
    product = ROOT / "product-glitter-wool.jpg"
    if IMAGINE_PRODUCT.exists():
        shutil.copy(IMAGINE_PRODUCT, product)
    core_png, svg = render_pcdi_png_svg()
    mol_pdf = molecule_stand_alone(core_png)
    sheet = onepager(core_png, product)
    sheet_png = raster(sheet, str(ROOT / "holdfast-onepager"), dpi=220)
    final_sheet = ROOT / "holdfast-onepager.png"
    if sheet_png != final_sheet:
        shutil.copy(sheet_png, final_sheet)
    mol_png = raster(mol_pdf, str(ROOT / "bp-pud-1-pcdi"), dpi=200)
    final_mol = ROOT / "bp-pud-1-pcdi.png"
    if mol_png != final_mol:
        shutil.copy(mol_png, final_mol)
    write_html(product, svg, final_sheet, final_mol)
    notes = ROOT / "chemistry-source.md"
    notes.write_text(
        f"""# HOLDFAST chemistry source

All numbers and the molecule are from Scout task `{SOURCE_TASK}` (completed 2026-09-15).

Primary kit: **{KIT}**

- 100 parts soft anionic aliphatic polyester PUD (40% solids, pH 8-8.5, MFFT <15C)
- 4 parts Picassian XL-732 or Carbodilite E-02 (40% solids = 4% PCDI on polymer)
- 0.4 parts pre-hydrolyzed GPTMS
- Mix 100:4:0.4 wet
- Print thin film, drop flake
- RT 24h (optional 40C 20min)
- Full CDI 3-7 days
- No 60C oven

Key binder molecule (this drawing):

- Name: {PCDI_NAME}
- Note: {PCDI_IUPAC_NOTE}
- SMILES: `{PCDI_SMILES}`

Primer: GPTMS `CO[Si](CCCOCC1CO1)(OC)OC` for PET carboxyl/hydroxyl and wool amine. CPO is for PP/PE, not PET. APTES only if Al is exposed. Acrylic-lacquered glitter needs no extra flake primer.

Wash: cold hand after 3d expected; perc sheds; machine/hot no (wool felts).

Why not known kits: CA-1 wicks/stiffens/blooms/yellows. DA-1 needs 60C and MDI (respiratory sensitizer).

Backup: BP-ACR-1 BA/MMA/AA/DAAM 70/22/3/5 + ADH 2.45 g/100 g polymer + GPTMS 1%.

OA: Chen ACS Omega 2022 PMC9753492; Hassan/Carr J Adv Res 2019 PMC6369147; Li Molecules 2025 PMC12195955.

Imagine still-life used on the one-pager: product-glitter-wool.jpg (glitter on charcoal wool, no people).
Imagine freehand structure was the wrong connectivity (tetramethylbenzene, not the Scout SMILES) and was discarded.
"""
    )
    print("wrote", ROOT)
    for p in sorted(ROOT.iterdir()):
        print(f"  {p.name:40} {p.stat().st_size:8d}")


if __name__ == "__main__":
    main()
