#!/usr/bin/env python3
"""
Build PPBIB Formula Builder - Pakan Ayam (Chicken Feed) v1
Adapted from v4 (ikan air tawar) with full poultry nutrient parameters:
Kadar Air, Protein Kasar, Lemak Kasar, Serat Kasar, Abu,
Kalsium/Ca, Fosfor tersedia, ME, Lisin, Metionin
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────

def border(style="thin"):
    s = Side(style=style)
    return Border(left=s, right=s, top=s, bottom=s)

THIN = border("thin")
MED  = border("medium")

F_TITLE     = PatternFill("solid", fgColor="1F4E79")
F_HEADER    = PatternFill("solid", fgColor="2E75B6")
F_SUBHDR    = PatternFill("solid", fgColor="9DC3E6")
F_ORANGE    = PatternFill("solid", fgColor="FFC000")   # user input
F_GREEN_LT  = PatternFill("solid", fgColor="E2EFDA")   # auto-calc
F_GREEN_BR  = PatternFill("solid", fgColor="92D050")   # highlight green
F_TOTAL     = PatternFill("solid", fgColor="FFD966")
F_TARGET    = PatternFill("solid", fgColor="FCE4D6")
F_STATUS_OK = PatternFill("solid", fgColor="92D050")
F_STATUS_WN = PatternFill("solid", fgColor="FF7070")
F_GRAY      = PatternFill("solid", fgColor="F2F2F2")
F_WHITE     = PatternFill("solid", fgColor="FFFFFF")
F_YELLOW    = PatternFill("solid", fgColor="FFFF99")

FWHITE = Font(name="Calibri", bold=True, color="FFFFFF", size=10)
FBOLD  = Font(name="Calibri", bold=True, size=9)
FNORM  = Font(name="Calibri", size=9)
FSMALL = Font(name="Calibri", size=8)
FTITLE = Font(name="Calibri", bold=True, color="FFFFFF", size=13)

AC = Alignment(horizontal="center", vertical="center", wrap_text=True)
AL = Alignment(horizontal="left",   vertical="center", wrap_text=True)
AR = Alignment(horizontal="right",  vertical="center", wrap_text=True)

def sc(ws, r, c, val=None, font=None, fill=None, align=None, bord=None, fmt=None):
    cell = ws.cell(row=r, column=c)
    if val  is not None: cell.value  = val
    if font is not None: cell.font   = font
    if fill is not None: cell.fill   = fill
    if align is not None: cell.alignment = align
    if bord is not None: cell.border = bord
    if fmt  is not None: cell.number_format = fmt
    return cell

# ─────────────────────────────────────────────
# INGREDIENT DATA
# name, price, water%, prot%, fat%, sk%, abu%, ca%, p_avail%, me(kcal/kg), lys%, met%, category, note
# ─────────────────────────────────────────────

ING = [
    # Energi / Karbohidrat
    ("Jagung",              6000,   13.0,  8.00,  3.80,  2.20,  1.76,  0.03,  0.08,  3300, 0.25,  0.18, "Energi / Karbo",   None),
    ("Dedak halus",         4500,   10.0,  9.88,  3.17,  8.00, 14.22,  0.07,  0.18,  2011, 0.52,  0.22, "Energi / Karbo",   None),
    ("Pollard",             4050,   13.0, 12.68,  4.00, 15.00,  4.00,  0.12,  0.28,  1430, 0.52,  0.22, "Energi / Karbo",   None),
    ("Tapioka",            11000,   13.0,  2.50,  0.70,  4.60,  2.50,  0.10,  0.05,  3020, 0.05,  0.02, "Binder",           None),
    # Protein Nabati
    ("Bungkil kedelai",     8500,   11.0, 45.53,  1.76,  5.89,  6.24,  0.30,  0.22,  2240, 2.92,  0.64, "Protein Nabati",   None),
    ("Corn gluten meal",   10000,   10.0, 64.00,  2.91,  0.80,  2.68,  0.03,  0.08,  3450, 1.00,  1.72, "Protein Nabati",   "CGM"),
    ("Corn gluten feed",    5000,   10.0, 24.39,  2.20,  7.27,  6.40,  0.15,  0.30,  1890, 0.65,  0.40, "Protein Nabati",   None),
    ("DDGS",                7900,   12.0, 30.23,  5.48,  8.46,  4.87,  0.18,  0.55,  2855, 0.75,  0.56, "Protein Nabati",   None),
    ("Bungkil sawit",       3000,    9.0, 16.70,  9.20, 19.80,  4.70,  0.35,  0.18,  1650, 0.65,  0.35, "Protein Nabati",   None),
    ("Bungkil kelapa",      4500,   13.0, 18.00,  6.00, 17.33,  6.65,  0.20,  0.20,  1700, 0.56,  0.32, "Protein Nabati",   None),
    # Protein Hewani
    ("Tepung ikan impor",  15000,    8.0, 55.00,  7.52,  0.70, 26.00,  4.50,  2.55,  3050, 4.20,  1.60, "Protein Hewani",   None),
    ("Tepung ikan lokal",   9000,    6.0, 44.20,  6.97,  2.70, 42.26,  5.50,  2.10,  2650, 3.20,  1.25, "Protein Hewani",   None),
    ("Meat bone meal",     10000,    6.0, 52.57,  8.82,  2.41, 29.53,  9.50,  4.50,  2375, 2.80,  0.65, "Protein Hewani",   "MBM"),
    # Lemak
    ("CPO / Minyak sawit", 20000,    1.0,  0.00, 99.00,  0.00,  0.50,  0.00,  0.00,  7500, 0.00,  0.00, "Lemak / Minyak",   None),
    # Mineral
    ("Kapur (limestone)",   1200,    1.0,  0.00,  0.00,  0.00,  0.00, 38.50,  0.00,     0, 0.00,  0.00, "Mineral",          "Sumber Ca"),
    ("DCP",                 8000,    2.0,  0.00,  0.00,  0.00,  0.00, 22.00, 18.00,     0, 0.00,  0.00, "Mineral",          "Dicalcium Phosphate"),
    ("Garam (NaCl)",        3000,    1.0,  0.00,  0.00,  0.00, 99.00,  0.00,  0.00,     0, 0.00,  0.00, "Mineral",          None),
    # Aditif & Lainnya
    ("Kolin Klorida 60%",  50000,    2.0,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,     0, 0.00,  0.00, "Aditif",           "CC-60"),
    ("Premix vit-mineral", 25000,    1.0,  0.00,  0.00,  0.00,  0.00,  0.00,  0.00,     0, 0.00,  0.00, "Vitamin-Mineral",  None),
    ("Konsentrat",          2600,    9.0, 16.70,  9.20, 19.80,  4.70,  0.35,  0.18,  2650, 0.65,  0.35, "Protein Campuran", None),
    # Asam Amino
    ("L-Lysin HCl",        50000,    2.0, 95.80,  0.00,  0.00,  0.00,  0.00,  0.00,  3990,78.00,  0.00, "Asam Amino",       None),
    ("DL-Methionine",      90000,    2.0, 58.00,  0.00,  0.00,  0.00,  0.00,  0.00,  5020, 0.00, 99.00, "Asam Amino",       None),
    ("Threonine",          90000,    2.0, 72.60,  0.00,  0.00,  0.00,  0.00,  0.00,  3764, 0.00,  0.00, "Asam Amino",       None),
    ("Triptofan",         150000,    2.0, 85.00,  0.00,  0.00,  0.00,  0.00,  0.00,  3900, 0.00,  0.00, "Asam Amino",       None),
    # Aditif khusus unggas
    ("Toxin binder",       12000,   10.0,  0.00,  2.00,  0.00, 70.00,  0.00,  0.00,     0, 0.00,  0.00, "Aditif",           None),
    ("Enzim Fitase",      150000,    1.0,  7.00,  0.00,  1.00,  5.00,  0.00,  0.00,     0, 0.00,  0.00, "Aditif",           "Meningkatkan P tersedia"),
    ("Enzim NSP",          85000,    1.0,  7.00,  0.00,  1.00,  5.00,  0.00,  0.00,     0, 0.00,  0.00, "Aditif",           "Xylanase / Glucanase"),
]

# Default proportions – Broiler Starter (total = 100%)
# Jagung:59 + Dedak:8 + BkKedelai:20 + CGM:3 + TepIkan:4 + CPO:3 + Kapur:1 + DCP:0.5
# + Garam:0.3 + Premix:0.3 + L-Lys:0.1 + Met:0.1 + ToxBinder:0.5 + Fitase:0.2 = 100
DEF_PROP = {
    "Jagung":              59.0,
    "Dedak halus":          8.0,
    "Bungkil kedelai":     20.0,
    "Corn gluten meal":     3.0,
    "Tepung ikan lokal":    4.0,
    "CPO / Minyak sawit":   3.0,
    "Kapur (limestone)":    1.0,
    "DCP":                  0.5,
    "Garam (NaCl)":         0.3,
    "Premix vit-mineral":   0.3,
    "L-Lysin HCl":          0.1,
    "DL-Methionine":        0.1,
    "Toxin binder":         0.5,
    "Enzim Fitase":         0.2,
}

# ─────────────────────────────────────────────
# WORKBOOK SETUP
# ─────────────────────────────────────────────
wb = openpyxl.Workbook()
wb.remove(wb.active)

# ══════════════════════════════════════════════════════════
# SHEET 1 – REFERENSI BAHAN BAKU
# Cols: A=No, B=Nama, C=Harga, D=KadarAir, E=Protein,
#       F=Lemak, G=SK, H=Abu, I=Ca, J=Ptersedia,
#       K=ME, L=Lisin, M=Metionin, N=HargaProt, O=Kategori, P=Catatan
# ══════════════════════════════════════════════════════════
wsR = wb.create_sheet("Referensi Bahan Baku")

# Row 1 – title
wsR.merge_cells("A1:P1")
sc(wsR, 1, 1, "REFERENSI NILAI NUTRISI BAHAN BAKU PAKAN AYAM — PPBIB",
   font=FTITLE, fill=F_TITLE, align=AC, bord=MED)
wsR.row_dimensions[1].height = 24

# Row 2 – subtitle
wsR.merge_cells("A2:P2")
sc(wsR, 2, 1,
   "Sumber data: referensi nutrisi unggas (NRC/EVONIK/BSLA). "
   "Sesuaikan harga sesuai kondisi pasar lokal. "
   "ME = Energi Metabolis untuk Unggas (Broiler).",
   font=FSMALL, fill=F_SUBHDR, align=AL, bord=THIN)
wsR.row_dimensions[2].height = 30

# Row 3 – column headers
REF_HEADERS = [
    "No", "Nama Bahan", "Harga/kg\n(Rp)",
    "Kadar Air\n(%)", "Protein Kasar\n(%)", "Lemak Kasar\n(%)",
    "Serat Kasar\n(%)", "Abu\n(%)", "Kalsium/Ca\n(%)",
    "Fosfor tersedia\n(%)", "ME\n(kcal/kg)", "Lisin\n(%)",
    "Metionin\n(%)", "Harga Protein\n(Rp/% prot)", "Kategori", "Catatan"
]
for ci, h in enumerate(REF_HEADERS, 1):
    sc(wsR, 3, ci, h, font=FWHITE, fill=F_HEADER, align=AC, bord=THIN)
wsR.row_dimensions[3].height = 36

# Ingredients (rows 4–30)
for ri, ing in enumerate(ING):
    row = 4 + ri
    name, price, water, prot, fat, sk, abu, ca, pav, me, lys, met, cat, note = ing
    prop = DEF_PROP.get(name, None)  # not used in ref sheet, just for reference
    alt_fill = F_GRAY if ri % 2 == 0 else F_WHITE

    sc(wsR, row, 1,  ri+1,  font=FNORM, fill=alt_fill, align=AC, bord=THIN)
    sc(wsR, row, 2,  name,  font=FNORM, fill=alt_fill, align=AL, bord=THIN)
    sc(wsR, row, 3,  price, font=FNORM, fill=F_ORANGE, align=AC, bord=THIN, fmt='#,##0')
    sc(wsR, row, 4,  water, font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='0.00')
    sc(wsR, row, 5,  prot,  font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='0.00')
    sc(wsR, row, 6,  fat,   font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='0.00')
    sc(wsR, row, 7,  sk,    font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='0.00')
    sc(wsR, row, 8,  abu,   font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='0.00')
    sc(wsR, row, 9,  ca,    font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='0.000')
    sc(wsR, row, 10, pav,   font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='0.000')
    sc(wsR, row, 11, me if me > 0 else None,
                       font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='#,##0')
    sc(wsR, row, 12, lys,  font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='0.000')
    sc(wsR, row, 13, met,  font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='0.000')
    # Harga Protein = Harga / Protein%
    if prot > 0:
        sc(wsR, row, 14, f"=C{row}/E{row}", font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='#,##0')
    else:
        sc(wsR, row, 14, None, font=FNORM, fill=alt_fill, align=AC, bord=THIN)
    sc(wsR, row, 15, cat,  font=FNORM, fill=alt_fill, align=AL, bord=THIN)
    sc(wsR, row, 16, note, font=FSMALL, fill=alt_fill, align=AL, bord=THIN)

# Column widths for Ref sheet
wsR.column_dimensions["A"].width = 4
wsR.column_dimensions["B"].width = 22
wsR.column_dimensions["C"].width = 11
for col in "DEFGHIJKLM":
    wsR.column_dimensions[col].width = 10
wsR.column_dimensions["N"].width = 13
wsR.column_dimensions["O"].width = 16
wsR.column_dimensions["P"].width = 22

# Legenda (below ingredients)
leg_row = 4 + len(ING) + 2
wsR.merge_cells(f"A{leg_row}:P{leg_row}")
sc(wsR, leg_row, 1, "LEGENDA KATEGORI", font=FBOLD, fill=F_TITLE,
   align=AC, bord=THIN)
wsR.row_dimensions[leg_row].height = 18

cats_list = [
    ("Energi / Karbo", F_GREEN_LT),
    ("Protein Nabati", PatternFill("solid", fgColor="BDD7EE")),
    ("Protein Hewani", PatternFill("solid", fgColor="9DC3E6")),
    ("Lemak / Minyak", PatternFill("solid", fgColor="FFD966")),
    ("Mineral",        PatternFill("solid", fgColor="F4B942")),
    ("Asam Amino",     PatternFill("solid", fgColor="FCE4D6")),
    ("Vitamin-Mineral",PatternFill("solid", fgColor="E2EFDA")),
    ("Aditif",         PatternFill("solid", fgColor="F2F2F2")),
]
# Print 4 per row
for gi, (cname, cfill) in enumerate(cats_list):
    gr = leg_row + 1 + gi // 4
    gc = 1 + (gi % 4) * 4
    wsR.merge_cells(start_row=gr, start_column=gc, end_row=gr, end_column=gc+3)
    sc(wsR, gr, gc, cname, font=FBOLD, fill=cfill, align=AC, bord=THIN)

# Row for orange = user-editable note
note_row = leg_row + 4
wsR.merge_cells(f"A{note_row}:P{note_row}")
sc(wsR, note_row, 1,
   "⬆ Kolom ORANGE (Harga/kg) = kamu yang isi sesuai harga pasar lokal. "
   "Kolom lain = nilai nutrisi referensi (edit jika ada data lab sendiri).",
   font=FSMALL, fill=F_ORANGE, align=AL, bord=THIN)

print(f"✅ Sheet 'Referensi Bahan Baku' selesai ({len(ING)} bahan baku)")

# ══════════════════════════════════════════════════════════
# SHEET 2 – FORMULA BUILDER
#
# Column layout (26 cols A–Z, plus batch at AB2):
#  A=No, B=Nama, C=Proporsi%[ORANGE]
#  D=KadarAir%,  E=KontribAir
#  F=Protein%,   G=KontribProt
#  H=Lemak%,     I=KontribLemak
#  J=SK%,        K=KontribSK
#  L=Abu%,       M=KontribAbu
#  N=Ca%,        O=KontribCa
#  P=Ptsd%,      Q=KontribP
#  R=ME,         S=KontribME
#  T=Lisin%,     U=KontribLisin
#  V=Metionin%,  W=KontribMet
#  X=Harga/kg,   Y=Biaya/kgPakan
#  Z=Proporsi(kg)
#  AB2 = Total Batch (kg)
# ══════════════════════════════════════════════════════════
wsF = wb.create_sheet("Formula Builder")

BATCH_COL = 28  # AB

# Row 1 – title
wsF.merge_cells("A1:Z1")
sc(wsF, 1, 1,
   "PPBIB — TEMPLATE FORMULASI PAKAN AYAM (UNGGAS)",
   font=FTITLE, fill=F_TITLE, align=AC, bord=MED)
wsF.row_dimensions[1].height = 26

# Row 2 – subtitle + batch label
wsF.merge_cells("A2:Y2")
sc(wsF, 2, 1,
   "Pusat Pelatihan Budidaya Unggas  |  Instruktur: Aditiya Nugraha  |  "
   "Standar nutrisi: Broiler Starter (SNI 01-3931)",
   font=FNORM, fill=F_SUBHDR, align=AL, bord=THIN)
sc(wsF, 2, BATCH_COL, "⬇ Total Batch (kg)", font=FBOLD, fill=F_ORANGE, align=AC, bord=THIN)
sc(wsF, 2, BATCH_COL+1, 100, font=FBOLD, fill=F_ORANGE, align=AC, bord=THIN, fmt='#,##0')
wsF.row_dimensions[2].height = 24

BATCH_REF = f"${get_column_letter(BATCH_COL+1)}$2"   # e.g. $AC$2

# Row 3 – column headers
HDR3 = [
    ("No",1), ("Nama Bahan",2), ("Proporsi\n(%)",3),
    ("Kadar Air\n(%)",4),  ("Kontrib\nAir",5),
    ("Protein\n(%)",6),    ("Kontrib\nProtein",7),
    ("Lemak\n(%)",8),      ("Kontrib\nLemak",9),
    ("Serat Kasar\n(%)",10),("Kontrib\nSK",11),
    ("Abu\n(%)",12),        ("Kontrib\nAbu",13),
    ("Ca\n(%)",14),         ("Kontrib\nCa",15),
    ("Fosfor tsd\n(%)",16), ("Kontrib\nP",17),
    ("ME\n(kcal/kg)",18),   ("Kontrib\nME",19),
    ("Lisin\n(%)",20),      ("Kontrib\nLisin",21),
    ("Metionin\n(%)",22),   ("Kontrib\nMet",23),
    ("Harga/kg\n(Rp)",24),  ("Biaya/kg\nPakan",25),
    ("Proporsi\n(kg)",26),
]
for label, ci in HDR3:
    fill = F_ORANGE if ci == 3 else F_HEADER
    sc(wsF, 3, ci, label, font=FWHITE, fill=fill, align=AC, bord=THIN)
wsF.row_dimensions[3].height = 38

# Row 4 – sub-headers (hints)
HDR4 = {
    1: "Nomor urutan", 2: "Daftar bahan baku",
    3: "← Ini yang kamu ubah",
    4: "Auto-link Ref", 5: "=C×D÷100",
    6: "Auto-link Ref", 7: "=C×F÷100",
    8: "Auto-link Ref", 9: "=C×H÷100",
    10:"Auto-link Ref",11: "=C×J÷100",
    12:"Auto-link Ref",13: "=C×L÷100",
    14:"Auto-link Ref",15: "=C×N÷100",
    16:"Auto-link Ref",17: "=C×P÷100",
    18:"Auto-link Ref",19: "=C×R÷100",
    20:"Auto-link Ref",21: "=C×T÷100",
    22:"Auto-link Ref",23: "=C×V÷100",
    24:"Auto-link Ref",25: "=C×X÷100",
    26: f"← Isi batch di {get_column_letter(BATCH_COL+1)}2",
}
for ci, txt in HDR4.items():
    fill = F_ORANGE if ci == 3 else F_SUBHDR
    sc(wsF, 4, ci, txt, font=FSMALL, fill=fill, align=AC, bord=THIN)
wsF.row_dimensions[4].height = 28

# Row 5 – blank separator
wsF.row_dimensions[5].height = 4

# ─────────────────────────────────────────────
# Ingredient rows 6–32 (27 bahan)
# Ref sheet rows: ingredient i → ref row (4 + i-1) = i+3
# ─────────────────────────────────────────────
REF = "Referensi Bahan Baku"
FIRST_ING_ROW = 6
LAST_ING_ROW  = FIRST_ING_ROW + len(ING) - 1   # 32

for idx, ing in enumerate(ING):
    row     = FIRST_ING_ROW + idx
    ref_row = 4 + idx   # row in Ref sheet
    name    = ing[0]
    prop    = DEF_PROP.get(name, None)

    alt_fill = F_GRAY if idx % 2 == 0 else F_WHITE

    sc(wsF, row, 1, idx+1, font=FNORM, fill=alt_fill, align=AC, bord=THIN)
    sc(wsF, row, 2, name,  font=FNORM, fill=alt_fill, align=AL, bord=THIN)
    sc(wsF, row, 3, prop,  font=FBOLD, fill=F_ORANGE, align=AC, bord=THIN, fmt='0.0')

    # auto-link pairs (nutrient col from ref, contribution = C * nut / 100)
    PAIRS = [
        (4,  f"='{REF}'!D{ref_row}"),   # Kadar Air
        (6,  f"='{REF}'!E{ref_row}"),   # Protein
        (8,  f"='{REF}'!F{ref_row}"),   # Lemak
        (10, f"='{REF}'!G{ref_row}"),   # SK
        (12, f"='{REF}'!H{ref_row}"),   # Abu
        (14, f"='{REF}'!I{ref_row}"),   # Ca
        (16, f"='{REF}'!J{ref_row}"),   # P tersedia
        (18, f"='{REF}'!K{ref_row}"),   # ME
        (20, f"='{REF}'!L{ref_row}"),   # Lisin
        (22, f"='{REF}'!M{ref_row}"),   # Metionin
    ]
    for nut_col, ref_formula in PAIRS:
        kontrib_col = nut_col + 1
        nut_letter  = get_column_letter(nut_col)
        # ME: guard for blank cells
        if nut_col == 18:
            sc(wsF, row, nut_col, ref_formula,
               font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt='#,##0')
            sc(wsF, row, kontrib_col,
               f"=IF(ISNUMBER({nut_letter}{row}),C{row}*{nut_letter}{row}/100,0)",
               font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt='#,##0')
        else:
            fmt = '0.000' if nut_col in (14,16,20,22) else '0.00'
            sc(wsF, row, nut_col, ref_formula,
               font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt=fmt)
            kfmt = '0.000' if nut_col in (14,16,20,22) else '0.00'
            sc(wsF, row, kontrib_col,
               f"=C{row}*{nut_letter}{row}/100",
               font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt=kfmt)

    # Harga/kg
    sc(wsF, row, 24, f"='{REF}'!C{ref_row}",
       font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt='#,##0')
    # Biaya/kg pakan
    sc(wsF, row, 25, f"=C{row}*X{row}/100",
       font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt='#,##0')
    # Proporsi (kg)
    sc(wsF, row, 26, f"=C{row}/100*{BATCH_REF}",
       font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt='0.00')

# ─────────────────────────────────────────────
# TOTAL ROW (row 33)
# ─────────────────────────────────────────────
TOTAL_ROW = LAST_ING_ROW + 1   # 33
R6 = FIRST_ING_ROW
RL = LAST_ING_ROW

sc(wsF, TOTAL_ROW, 1, None, fill=F_TOTAL, bord=THIN)
wsF.merge_cells(start_row=TOTAL_ROW, start_column=1, end_row=TOTAL_ROW, end_column=2)
sc(wsF, TOTAL_ROW, 1, "TOTAL", font=FBOLD, fill=F_TOTAL, align=AC, bord=THIN)

# Sum all numeric columns
for ci in [3,5,7,9,11,13,15,17,19,21,23,25,26]:
    cl = get_column_letter(ci)
    fmt = '#,##0' if ci in [19,25] else ('0.000' if ci in [15,17,21,23] else '0.00')
    sc(wsF, TOTAL_ROW, ci, f"=SUM({cl}{R6}:{cl}{RL})",
       font=FBOLD, fill=F_TOTAL, align=AC, bord=THIN, fmt=fmt)

# Sum of nutrient% columns (weighted averages shown as sums of contributions)
for ci in [4,6,8,10,12,14,16,18,20,22,24]:
    cl = get_column_letter(ci)
    sc(wsF, TOTAL_ROW, ci, "—", font=FBOLD, fill=F_TOTAL, align=AC, bord=THIN)

# Label for Harga Pokok in col 24
sc(wsF, TOTAL_ROW, 24, "Harga Pokok →", font=FBOLD, fill=F_TOTAL, align=AR, bord=THIN)
wsF.row_dimensions[TOTAL_ROW].height = 20

# ─────────────────────────────────────────────
# BATAS & TARGET NUTRISI section (rows 35–41)
# ─────────────────────────────────────────────
SEP = TOTAL_ROW + 2   # blank separator row 34, section starts row 35
TARGET_SECTION = SEP

wsF.merge_cells(f"A{TARGET_SECTION}:Z{TARGET_SECTION}")
sc(wsF, TARGET_SECTION, 1,
   "BATAS & TARGET NUTRISI — STANDAR BROILER STARTER (SNI 01-3931 / NRC)",
   font=FBOLD, fill=F_TITLE, align=AL, bord=MED)
wsF.row_dimensions[TARGET_SECTION].height = 20

# Header row for target section
T_HDR = TARGET_SECTION + 1
T_LABELS = [
    (1,"Label"), (2,"Keterangan"),
    (3,"Total\nProporsi (%)"),
    (5,"Protein\nKasar (%)"), (7,"Lemak\nKasar (%)"),
    (9,"Serat\nKasar (%)"), (11,"Abu (%)"),
    (13,"Kalsium/Ca\n(%)"), (15,"Fosfor tsd\n(%)"),
    (17,"Kadar Air\n(%)"), (19,"ME\n(kcal/kg)"),
    (21,"Lisin\n(%)"), (23,"Metionin\n(%)"),
    (25,"Harga Pokok\n(Rp/kg)"),
]
for col, lbl in T_LABELS:
    sc(wsF, T_HDR, col, lbl, font=FWHITE, fill=F_HEADER, align=AC, bord=THIN)
wsF.row_dimensions[T_HDR].height = 36

# AKTUAL row
T_ACT = T_HDR + 1
sc(wsF, T_ACT, 1, "AKTUAL",       font=FBOLD, fill=F_GREEN_LT, align=AC, bord=THIN)
sc(wsF, T_ACT, 2, "(dari formula di atas)", font=FSMALL, fill=F_GREEN_LT, align=AL, bord=THIN)
# pull totals from TOTAL_ROW
ACT_MAP = {
    3: f"=C{TOTAL_ROW}",      # total proporsi
    5: f"=G{TOTAL_ROW}",      # protein contribution total
    7: f"=I{TOTAL_ROW}",      # lemak
    9: f"=K{TOTAL_ROW}",      # SK
   11: f"=M{TOTAL_ROW}",      # abu
   13: f"=O{TOTAL_ROW}",      # Ca
   15: f"=Q{TOTAL_ROW}",      # P tersedia
   17: f"=E{TOTAL_ROW}",      # kadar air
   19: f"=S{TOTAL_ROW}",      # ME
   21: f"=U{TOTAL_ROW}",      # lisin
   23: f"=W{TOTAL_ROW}",      # metionin
   25: f"=Y{TOTAL_ROW}",      # harga pokok
}
ACT_FMT = {3:'0.0', 5:'0.00', 7:'0.00', 9:'0.00', 11:'0.00',
           13:'0.000', 15:'0.000', 17:'0.00', 19:'#,##0', 21:'0.000', 23:'0.000', 25:'#,##0'}
for col, formula in ACT_MAP.items():
    sc(wsF, T_ACT, col, formula, font=FBOLD, fill=F_GREEN_LT, align=AC, bord=THIN,
       fmt=ACT_FMT.get(col,'0.00'))
wsF.row_dimensions[T_ACT].height = 18

# TARGET MIN row
T_MIN = T_ACT + 1
sc(wsF, T_MIN, 1, "TARGET MIN", font=FBOLD, fill=F_ORANGE, align=AC, bord=THIN)
sc(wsF, T_MIN, 2, "Standar min SNI/NRC →", font=FSMALL, fill=F_ORANGE, align=AL, bord=THIN)
MIN_VALS = {
    3: 100, 5: 21.0, 7: 5.0, 9: None, 11: None,
    13: 0.90, 15: 0.45, 17: None, 19: 2900, 21: 1.00, 23: 0.40, 25: None
}
for col, val in MIN_VALS.items():
    sc(wsF, T_MIN, col, val, font=FBOLD, fill=F_ORANGE, align=AC, bord=THIN,
       fmt=ACT_FMT.get(col,'0.00'))
wsF.row_dimensions[T_MIN].height = 18

# TARGET MAX row
T_MAX = T_MIN + 1
sc(wsF, T_MAX, 1, "TARGET MAX", font=FBOLD, fill=F_TARGET, align=AC, bord=THIN)
sc(wsF, T_MAX, 2, "Standar maks SNI/NRC →", font=FSMALL, fill=F_TARGET, align=AL, bord=THIN)
MAX_VALS = {
    3: 100, 5: None, 7: None, 9: 6.0, 11: 8.0,
    13: 1.20, 15: None, 17: 14.0, 19: None, 21: None, 23: None, 25: None
}
for col, val in MAX_VALS.items():
    sc(wsF, T_MAX, col, val, font=FBOLD, fill=F_TARGET, align=AC, bord=THIN,
       fmt=ACT_FMT.get(col,'0.00'))
wsF.row_dimensions[T_MAX].height = 18

# STATUS row
T_STA = T_MAX + 1
sc(wsF, T_STA, 1, "STATUS", font=FBOLD, fill=F_STATUS_OK, align=AC, bord=THIN)
sc(wsF, T_STA, 2, "Cek otomatis", font=FSMALL, fill=F_GREEN_LT, align=AL, bord=THIN)

def status_cell(ws, row, act_col, min_col=None, max_col=None,
                min_row=None, max_row=None, label=""):
    """Generate status formula: ✅ or ⚠️"""
    act = f"{get_column_letter(act_col)}{T_ACT}"
    conditions = []
    if min_col and min_row:
        mn = f"{get_column_letter(min_col)}{min_row}"
        conditions.append(f'{act}>={mn}')
    if max_col and max_row:
        mx = f"{get_column_letter(max_col)}{max_row}"
        conditions.append(f'{act}<={mx}')
    if not conditions:
        return f'="—"'
    cond = "AND(" + ",".join(conditions) + ")" if len(conditions)>1 else conditions[0]
    return f'=IF({cond},"✅ OK","⚠️ KURANG")'

STA_MAP = {
    3:  (3,  T_MIN, 3,  T_MAX),   # proporsi: min AND max = 100
    5:  (5,  T_MIN, None, None),  # protein: min only
    7:  (7,  T_MIN, None, None),  # lemak: min only
    9:  (9,  None,  9,   T_MAX),  # SK: max only
    11: (11, None,  11,  T_MAX),  # abu: max only
    13: (13, T_MIN, 13,  T_MAX),  # Ca: min AND max
    15: (15, T_MIN, None,None),   # P: min only
    17: (17, None,  17,  T_MAX),  # kadar air: max only
    19: (19, T_MIN, None,None),   # ME: min only
    21: (21, T_MIN, None,None),   # lisin: min only
    23: (23, T_MIN, None,None),   # metionin: min only
}
for act_col, (_, min_row, max_c, max_row) in STA_MAP.items():
    min_c = act_col if min_row else None
    formula = status_cell(wsF, T_STA, act_col,
                          min_col=min_c, min_row=min_row,
                          max_col=max_c, max_row=max_row)
    sc(wsF, T_STA, act_col, formula, font=FBOLD, fill=F_GREEN_LT, align=AC, bord=THIN)
wsF.row_dimensions[T_STA].height = 18

# Tips
TIP_ROW = T_STA + 2
wsF.merge_cells(f"A{TIP_ROW}:Z{TIP_ROW}")
sc(wsF, TIP_ROW, 1,
   "💡 CARA PAKAI: Ubah Proporsi (%) di Kolom C → nutrisi & biaya otomatis terhitung. "
   f"Isi Total Batch (kg) di {get_column_letter(BATCH_COL+1)}2 → Kolom Z = kebutuhan bahan per batch. "
   "Edit nilai nutrisi / harga di sheet 'Referensi Bahan Baku' → langsung update ke sini. "
   "Pastikan Total Proporsi = 100%.",
   font=FSMALL, fill=F_YELLOW, align=AL, bord=THIN)
wsF.row_dimensions[TIP_ROW].height = 28

LEG_ROW = TIP_ROW + 1
wsF.merge_cells(f"A{LEG_ROW}:Z{LEG_ROW}")
sc(wsF, LEG_ROW, 1,
   "⚡ KOLOM ORANGE = Kamu yang isi  |  KOLOM HIJAU = Otomatis terhitung  |"
   "  TOTAL ROW = Cek keseluruhan  |  STATUS ✅ = memenuhi standar  |  ⚠️ = perlu penyesuaian",
   font=FSMALL, fill=F_GREEN_LT, align=AL, bord=THIN)

# Column widths for Formula Builder
wsF.column_dimensions["A"].width = 4
wsF.column_dimensions["B"].width = 24
wsF.column_dimensions["C"].width = 9
for col_idx in range(4, 27):
    cl = get_column_letter(col_idx)
    wsF.column_dimensions[cl].width = 9
wsF.column_dimensions[get_column_letter(BATCH_COL)].width   = 14
wsF.column_dimensions[get_column_letter(BATCH_COL+1)].width = 10

# Freeze panes: freeze rows 1-4 and columns A-B
wsF.freeze_panes = "C5"

print(f"✅ Sheet 'Formula Builder' selesai (rows 6–{LAST_ING_ROW})")

# ══════════════════════════════════════════════════════════
# SHEET 3 – PERBANDINGAN FORMULA
# ══════════════════════════════════════════════════════════
wsP = wb.create_sheet("Perbandingan Formula")

wsP.merge_cells("A1:I1")
sc(wsP, 1, 1, "LEMBAR PERBANDINGAN FORMULA PAKAN AYAM — PPBIB",
   font=FTITLE, fill=F_TITLE, align=AC, bord=MED)
wsP.row_dimensions[1].height = 24

# Header row 2
P_HDRS = [
    "No", "Nama Bahan", "Harga/kg\n(Rp)", "Protein\n(%)",
    "Formula A\nProporsi (%)\n⬅ auto Builder",
    "Formula A\nKontrib\nProtein",
    "Formula B\nProporsi (%)\n(isi manual)",
    "Formula B\nKontrib\nProtein",
    "Selisih\nProporsi",
]
for ci, h in enumerate(P_HDRS, 1):
    sc(wsP, 2, ci, h, font=FWHITE, fill=F_HEADER, align=AC, bord=THIN)
wsP.row_dimensions[2].height = 38

# Data rows 3–29 (27 ingredients)
for idx in range(len(ING)):
    row     = 3 + idx
    ref_row = 4 + idx
    fb_row  = FIRST_ING_ROW + idx

    alt_fill = F_GRAY if idx % 2 == 0 else F_WHITE

    sc(wsP, row, 1, idx+1, font=FNORM, fill=alt_fill, align=AC, bord=THIN)
    sc(wsP, row, 2, f"='{REF}'!B{ref_row}", font=FNORM, fill=alt_fill, align=AL, bord=THIN)
    sc(wsP, row, 3, f"='{REF}'!C{ref_row}", font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='#,##0')
    sc(wsP, row, 4, f"='{REF}'!E{ref_row}", font=FNORM, fill=alt_fill, align=AC, bord=THIN, fmt='0.00')
    sc(wsP, row, 5, f"='Formula Builder'!C{fb_row}",
       font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt='0.0')
    sc(wsP, row, 6, f"=E{row}*D{row}/100",
       font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt='0.00')
    sc(wsP, row, 7, None, font=FNORM, fill=F_ORANGE, align=AC, bord=THIN, fmt='0.0')
    sc(wsP, row, 8, f"=G{row}*D{row}/100",
       font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt='0.00')
    sc(wsP, row, 9, f"=G{row}-E{row}",
       font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt='0.0')

# TOTAL row
PTOT = 3 + len(ING)
wsP.merge_cells(f"A{PTOT}:B{PTOT}")
sc(wsP, PTOT, 1, "TOTAL", font=FBOLD, fill=F_TOTAL, align=AC, bord=THIN)
for ci in [3,5,6,7,8,9]:
    cl  = get_column_letter(ci)
    fmt = '#,##0' if ci==3 else '0.00'
    sc(wsP, PTOT, ci, f"=SUM({cl}3:{cl}{PTOT-1})",
       font=FBOLD, fill=F_TOTAL, align=AC, bord=THIN, fmt=fmt)
sc(wsP, PTOT, 3, "Harga Pokok →", font=FBOLD, fill=F_TOTAL, align=AR, bord=THIN)

# Summary section
SUM_ROW = PTOT + 2
wsP.merge_cells(f"A{SUM_ROW}:I{SUM_ROW}")
sc(wsP, SUM_ROW, 1,
   "📊  RINGKASAN OTOMATIS — FORMULA A vs FORMULA B",
   font=FBOLD, fill=F_TITLE, align=AL, bord=MED)

SH2 = SUM_ROW + 1
for ci, lbl in [(1,"Nutrisi"),(5,"Formula A"),(7,"Formula B"),(9,"Selisih (A−B)")]:
    sc(wsP, SH2, ci, lbl, font=FWHITE, fill=F_HEADER, align=AC, bord=THIN)
wsP.row_dimensions[SH2].height = 22

METRICS = [
    ("Total Proporsi (%)",
     f"=SUM(E3:E{PTOT-1})", f"=SUM(G3:G{PTOT-1})", "0.0"),
    ("Protein Kasar (%)",
     f"=SUMPRODUCT(E3:E{PTOT-1},'{REF}'!E4:E{3+len(ING)})/100",
     f"=SUMPRODUCT(G3:G{PTOT-1},'{REF}'!E4:E{3+len(ING)})/100", "0.00"),
    ("Lemak Kasar (%)",
     f"=SUMPRODUCT(E3:E{PTOT-1},'{REF}'!F4:F{3+len(ING)})/100",
     f"=SUMPRODUCT(G3:G{PTOT-1},'{REF}'!F4:F{3+len(ING)})/100", "0.00"),
    ("Serat Kasar (%)",
     f"=SUMPRODUCT(E3:E{PTOT-1},'{REF}'!G4:G{3+len(ING)})/100",
     f"=SUMPRODUCT(G3:G{PTOT-1},'{REF}'!G4:G{3+len(ING)})/100", "0.00"),
    ("Abu (%)",
     f"=SUMPRODUCT(E3:E{PTOT-1},'{REF}'!H4:H{3+len(ING)})/100",
     f"=SUMPRODUCT(G3:G{PTOT-1},'{REF}'!H4:H{3+len(ING)})/100", "0.00"),
    ("Kalsium/Ca (%)",
     f"=SUMPRODUCT(E3:E{PTOT-1},'{REF}'!I4:I{3+len(ING)})/100",
     f"=SUMPRODUCT(G3:G{PTOT-1},'{REF}'!I4:I{3+len(ING)})/100", "0.000"),
    ("Fosfor tersedia (%)",
     f"=SUMPRODUCT(E3:E{PTOT-1},'{REF}'!J4:J{3+len(ING)})/100",
     f"=SUMPRODUCT(G3:G{PTOT-1},'{REF}'!J4:J{3+len(ING)})/100", "0.000"),
    ("Kadar Air (%)",
     f"=SUMPRODUCT(E3:E{PTOT-1},'{REF}'!D4:D{3+len(ING)})/100",
     f"=SUMPRODUCT(G3:G{PTOT-1},'{REF}'!D4:D{3+len(ING)})/100", "0.00"),
    ("ME (kcal/kg)",
     f"=SUMPRODUCT(E3:E{PTOT-1},IF(ISNUMBER('{REF}'!K4:K{3+len(ING)}),'{REF}'!K4:K{3+len(ING)},0))/100",
     f"=SUMPRODUCT(G3:G{PTOT-1},IF(ISNUMBER('{REF}'!K4:K{3+len(ING)}),'{REF}'!K4:K{3+len(ING)},0))/100", "#,##0"),
    ("Lisin (%)",
     f"=SUMPRODUCT(E3:E{PTOT-1},'{REF}'!L4:L{3+len(ING)})/100",
     f"=SUMPRODUCT(G3:G{PTOT-1},'{REF}'!L4:L{3+len(ING)})/100", "0.000"),
    ("Metionin (%)",
     f"=SUMPRODUCT(E3:E{PTOT-1},'{REF}'!M4:M{3+len(ING)})/100",
     f"=SUMPRODUCT(G3:G{PTOT-1},'{REF}'!M4:M{3+len(ING)})/100", "0.000"),
    ("Harga Pokok (Rp/kg)",
     f"=SUMPRODUCT(E3:E{PTOT-1},C3:C{PTOT-1})/100",
     f"=SUMPRODUCT(G3:G{PTOT-1},C3:C{PTOT-1})/100", "#,##0"),
]

for mi, (label, fa, fb, fmt) in enumerate(METRICS):
    mr = SH2 + 1 + mi
    alt = F_GRAY if mi % 2 == 0 else F_WHITE
    sc(wsP, mr, 1, label, font=FNORM, fill=alt, align=AL, bord=THIN)
    sc(wsP, mr, 5, fa,    font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt=fmt)
    sc(wsP, mr, 7, fb,    font=FNORM, fill=F_GREEN_LT, align=AC, bord=THIN, fmt=fmt)
    diff_col = 9
    sc(wsP, mr, diff_col, f"=E{mr}-G{mr}",
       font=FNORM, fill=alt, align=AC, bord=THIN, fmt=fmt)

# Footer tip
TIP_P = SH2 + 1 + len(METRICS) + 1
wsP.merge_cells(f"A{TIP_P}:I{TIP_P}")
sc(wsP, TIP_P, 1,
   "💡 Formula A = otomatis dari sheet 'Formula Builder'. "
   "Formula B = isi manual di Kolom G untuk membandingkan alternatif formulasi.",
   font=FSMALL, fill=F_YELLOW, align=AL, bord=THIN)

# Column widths for Perbandingan
wsP.column_dimensions["A"].width = 4
wsP.column_dimensions["B"].width = 22
wsP.column_dimensions["C"].width = 12
wsP.column_dimensions["D"].width = 10
for col in "EFGHI":
    wsP.column_dimensions[col].width = 14

print("✅ Sheet 'Perbandingan Formula' selesai")

# ─────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────
output_path = "/home/user/ppbib/PPBIB_Formula_Builder_Pakan_Ayam_v1.xlsx"
wb.save(output_path)
print(f"\n✅ File saved: {output_path}")
print(f"   Sheets   : {wb.sheetnames}")
print(f"   Bahan baku: {len(ING)} ingredients")
print(f"   Nutrisi   : 10 parameter (Kadar Air, Protein, Lemak, SK, Abu, Ca, P, ME, Lisin, Metionin)")
