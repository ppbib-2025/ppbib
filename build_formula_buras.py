#!/usr/bin/env python3
"""
PPBIB — Formula Pakan Ayam Buras
Bahan baku: Polar, MBM, Jagung, CGM, CGF, SBM, Gaplek,
            L-Lisin, Top Mix, Propionic Acid, Choline Chloride, Mineral

Target: Ayam Buras Grower  (SNI / Ditjennak)
  Protein   : 16–18 %
  ME        : 2700–2900 kcal/kg
  SK        : maks 8 %
  Ca        : 0.70–1.00 %
  P tersedia: min 0.35 %
  Lisin     : min 0.70 %
  Metionin  : min 0.30 %
  Kadar Air : maks 14 %
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ── STYLES ─────────────────────────────────────────────────────────────
def bd(s="thin"):
    x = Side(style=s)
    return Border(left=x, right=x, top=x, bottom=x)

THIN = bd("thin")
MED  = bd("medium")

FT   = PatternFill("solid", fgColor="1F4E79")   # dark-blue title
FH   = PatternFill("solid", fgColor="2E75B6")   # blue header
FSH  = PatternFill("solid", fgColor="9DC3E6")   # light-blue subheader
FOR  = PatternFill("solid", fgColor="FFC000")   # orange  = user input
FG   = PatternFill("solid", fgColor="E2EFDA")   # lt-green = auto
FTot = PatternFill("solid", fgColor="FFD966")   # gold    = total row
FMin = PatternFill("solid", fgColor="FCE4D6")   # salmon  = target min
FMax = PatternFill("solid", fgColor="F8CBAD")   # orange  = target max
FGR  = PatternFill("solid", fgColor="F2F2F2")   # gray    = alt row
FW   = PatternFill("solid", fgColor="FFFFFF")
FY   = PatternFill("solid", fgColor="FFFACD")   # lemon   = tip

FWh  = Font(name="Calibri", bold=True,  color="FFFFFF", size=10)
FTi  = Font(name="Calibri", bold=True,  color="FFFFFF", size=13)
FB   = Font(name="Calibri", bold=True,  size=9)
FN   = Font(name="Calibri", size=9)
FS   = Font(name="Calibri", size=8)

AC = Alignment(horizontal="center", vertical="center", wrap_text=True)
AL = Alignment(horizontal="left",   vertical="center", wrap_text=True)
AR = Alignment(horizontal="right",  vertical="center", wrap_text=True)

def sc(ws, r, c, val=None, fnt=None, fill=None, align=None, brd=None, fmt=None):
    cell = ws.cell(row=r, column=c)
    if val  is not None: cell.value  = val
    if fnt  is not None: cell.font   = fnt
    if fill is not None: cell.fill   = fill
    if align is not None: cell.alignment = align
    if brd  is not None: cell.border = brd
    if fmt  is not None: cell.number_format = fmt
    return cell

# ── BAHAN BAKU ─────────────────────────────────────────────────────────
# name, harga, air%, prot%, lemak%, sk%, abu%, ca%, p_av%, me, lys%, met%, ket
BAHAN = [
    # Energi utama
    ("Jagung",              6_000, 13.0,  8.00, 3.80, 2.20,  1.76, 0.03, 0.08, 3300, 0.25, 0.18, "Energi"),
    ("Gaplek",              3_500, 14.0,  2.00, 0.50, 4.00,  2.00, 0.10, 0.04, 3200, 0.05, 0.02, "Energi"),
    # Sumber protein & energi
    ("Polar (Wheat Pollard)",4_050, 13.0, 14.00, 3.50, 8.00,  5.00, 0.15, 0.35, 1600, 0.55, 0.25, "Protein/Energi"),
    ("CGF (Corn Gluten Feed)",5_000,10.0, 24.39, 2.20, 7.27,  6.40, 0.15, 0.30, 1890, 0.65, 0.40, "Protein Nabati"),
    ("SBM (Bungkil Kedelai)",8_500, 11.0, 45.53, 1.76, 5.89,  6.24, 0.30, 0.22, 2240, 2.92, 0.64, "Protein Nabati"),
    ("CGM (Corn Gluten Meal)",10_000,10.0,64.00, 2.91, 0.80,  2.68, 0.03, 0.08, 3450, 1.00, 1.72, "Protein Nabati"),
    ("MBM (Meat Bone Meal)", 10_000, 6.0, 52.57, 8.82, 2.41, 29.53, 9.50, 4.50, 2375, 2.80, 0.65, "Protein Hewani"),
    # Mineral & suplemen
    ("Mineral (Ca-P supp.)", 8_000,  2.0,  0.00, 0.00, 0.00,  0.00,22.00,18.00,    0, 0.00, 0.00, "Mineral"),
    ("Top Mix (Premix)",    25_000,  1.0,  0.00, 0.00, 0.00,  0.00, 0.00, 0.00,    0, 0.00, 0.00, "Vitamin-Mineral"),
    # Asam amino
    ("L-Lisin HCl",         50_000, 2.0, 95.80, 0.00, 0.00,  0.00, 0.00, 0.00, 3990,78.00, 0.00, "Asam Amino"),
    # Aditif / preservatif
    ("Propionic Acid",      15_000, 1.0,  0.00, 0.00, 0.00,  0.00, 0.00, 0.00,    0, 0.00, 0.00, "Aditif (pengawet)"),
    ("Choline Chloride 60%",50_000, 2.0,  0.00, 0.00, 0.00,  0.00, 0.00, 0.00,    0, 0.00, 0.00, "Aditif"),
]

# ── FORMULA TERHITUNG (Ayam Buras Grower) ──────────────────────────────
# Jagung:55.4 + Polar:10 + CGF:8 + SBM:14 + CGM:3 + MBM:5
# + Gaplek:3 + Mineral:1 + TopMix:0.3 + L-Lisin:0.1
# + PropAcid:0.1 + CC:0.1  =  100.0 %
#
# Estimasi hasil:
#   Protein ~18.8%  |  ME ~2771 kcal/kg  |  SK ~3.7%
#   Ca ~0.73%       |  P  ~0.41%         |  Lisin ~0.90%
#   Metionin ~0.33% |  Kadar Air ~12.3%
# ──────────────────────────────────────────────────────────────────────
PROPORSI = {
    "Jagung":               57.4,   # dinaikkan agar protein ~17.4%
    "Gaplek":                4.0,
    "Polar (Wheat Pollard)":10.0,
    "CGF (Corn Gluten Feed)": 8.0,
    "SBM (Bungkil Kedelai)": 12.0,  # diturunkan (protein nabati)
    "CGM (Corn Gluten Meal)": 2.0,  # diturunkan
    "MBM (Meat Bone Meal)":   5.0,
    "Mineral (Ca-P supp.)":   1.0,
    "Top Mix (Premix)":       0.3,
    "L-Lisin HCl":            0.1,
    "Propionic Acid":         0.1,
    "Choline Chloride 60%":   0.1,
}
# Verifikasi total = 100.0
assert abs(sum(PROPORSI.values()) - 100.0) < 0.001, f"Total {sum(PROPORSI.values())} ≠ 100"

# ── WORKBOOK ───────────────────────────────────────────────────────────
wb = openpyxl.Workbook()
wb.remove(wb.active)

REF_SH = "Referensi Bahan Baku"

# ════════════════════════════════════════════════════════════
# SHEET 1 – REFERENSI BAHAN BAKU
# A=No  B=Nama  C=Harga  D=Air  E=Prot  F=Lemak  G=SK  H=Abu
# I=Ca  J=Pav   K=ME     L=Lys  M=Met   N=HargaProt  O=Kategori
# ════════════════════════════════════════════════════════════
wsR = wb.create_sheet(REF_SH)

wsR.merge_cells("A1:O1")
sc(wsR, 1,1, "REFERENSI NILAI NUTRISI — FORMULA PAKAN AYAM BURAS (PPBIB)",
   fnt=FTi, fill=FT, align=AC, brd=MED)
wsR.row_dimensions[1].height = 24

wsR.merge_cells("A2:O2")
sc(wsR, 2,1,
   "ME = Energi Metabolis untuk Unggas. "
   "Kolom ORANGE (Harga) = update sesuai harga pasar lokal.",
   fnt=FS, fill=FSH, align=AL, brd=THIN)
wsR.row_dimensions[2].height = 20

R_HDR = ["No","Nama Bahan","Harga/kg\n(Rp)","Kadar Air\n(%)","Protein\n(%)","Lemak\n(%)",
         "Serat Kasar\n(%)","Abu\n(%)","Ca\n(%)","Fosfor tsd\n(%)","ME\n(kcal/kg)",
         "Lisin\n(%)","Metionin\n(%)","Harga Prot\n(Rp/%)","Kategori"]
for ci, h in enumerate(R_HDR, 1):
    sc(wsR, 3, ci, h, fnt=FWh, fill=FH, align=AC, brd=THIN)
wsR.row_dimensions[3].height = 38

for idx, b in enumerate(BAHAN):
    row = 4 + idx
    nm, hg, air, pr, lm, sk, ab, ca, pav, me, ly, mt, kat = b
    af = FGR if idx%2==0 else FW

    sc(wsR, row, 1, idx+1, fnt=FN, fill=af, align=AC, brd=THIN)
    sc(wsR, row, 2, nm,    fnt=FN, fill=af, align=AL, brd=THIN)
    sc(wsR, row, 3, hg,    fnt=FN, fill=FOR,align=AC, brd=THIN, fmt='#,##0')
    sc(wsR, row, 4, air,   fnt=FN, fill=af, align=AC, brd=THIN, fmt='0.00')
    sc(wsR, row, 5, pr,    fnt=FN, fill=af, align=AC, brd=THIN, fmt='0.00')
    sc(wsR, row, 6, lm,    fnt=FN, fill=af, align=AC, brd=THIN, fmt='0.00')
    sc(wsR, row, 7, sk,    fnt=FN, fill=af, align=AC, brd=THIN, fmt='0.00')
    sc(wsR, row, 8, ab,    fnt=FN, fill=af, align=AC, brd=THIN, fmt='0.00')
    sc(wsR, row, 9, ca,    fnt=FN, fill=af, align=AC, brd=THIN, fmt='0.000')
    sc(wsR, row,10, pav,   fnt=FN, fill=af, align=AC, brd=THIN, fmt='0.000')
    sc(wsR, row,11, me if me>0 else None, fnt=FN, fill=af, align=AC, brd=THIN, fmt='#,##0')
    sc(wsR, row,12, ly,    fnt=FN, fill=af, align=AC, brd=THIN, fmt='0.000')
    sc(wsR, row,13, mt,    fnt=FN, fill=af, align=AC, brd=THIN, fmt='0.000')
    sc(wsR, row,14, f"=C{row}/E{row}" if pr>0 else None,
       fnt=FN, fill=af, align=AC, brd=THIN, fmt='#,##0')
    sc(wsR, row,15, kat,   fnt=FN, fill=af, align=AL, brd=THIN)

wsR.column_dimensions["A"].width = 4
wsR.column_dimensions["B"].width = 26
wsR.column_dimensions["C"].width = 12
for c in "DEFGHIJKLM": wsR.column_dimensions[c].width = 10
wsR.column_dimensions["N"].width = 13
wsR.column_dimensions["O"].width = 18

# ════════════════════════════════════════════════════════════
# SHEET 2 – FORMULA BUILDER  (12 bahan, kolom A–R + batch di T2)
#
# A=No  B=Nama  C=Proporsi%[OR]
# D=Air%  E=KontAir   F=Prot%  G=KontProt
# H=Lem%  I=KontLem   J=SK%    K=KontSK
# L=Abu%  M=KontAbu   N=Ca%    O=KontCa
# P=Pav%  Q=KontPav   R=ME     S=KontME
# T=Lys%  U=KontLys   V=Met%   W=KontMet
# X=Harga Y=Biaya/kg  Z=Proporsi(kg)
# AB2 = Total Batch (kg)
# ════════════════════════════════════════════════════════════
wsF = wb.create_sheet("Formula Builder")

BATCH_COL  = 28          # AB
BATCH_VAL  = 29          # AC  ← isi angka batch
BATCH_REF  = f"$AC$2"

# row 1 – judul
wsF.merge_cells("A1:Z1")
sc(wsF, 1,1,
   "PPBIB — FORMULASI PAKAN AYAM BURAS  |  Fase: GROWER  (SNI Ditjennak / NRC Poultry)",
   fnt=FTi, fill=FT, align=AC, brd=MED)
wsF.row_dimensions[1].height = 26

# row 2 – subtitle + batch label
wsF.merge_cells("A2:Y2")
sc(wsF, 2,1,
   "Instruktur: Aditiya Nugraha  —  PPBIB  |  "
   "Formula dirancang untuk Ayam Buras Grower: Protein 16–18%, ME 2700–2900 kcal/kg",
   fnt=FN, fill=FSH, align=AL, brd=THIN)
sc(wsF, 2, BATCH_COL,   "⬇ Total Batch\n(kg)", fnt=FB,  fill=FOR, align=AC, brd=THIN)
sc(wsF, 2, BATCH_VAL,   100,                    fnt=FB,  fill=FOR, align=AC, brd=THIN, fmt='#,##0')
wsF.row_dimensions[2].height = 28

# row 3 – headers
H3 = [
    (1,"No"),(2,"Nama Bahan"),(3,"Proporsi\n(%)"),
    (4,"Kadar Air\n(%)"),(5,"Kontrib\nAir"),
    (6,"Protein\n(%)"),(7,"Kontrib\nProtein"),
    (8,"Lemak\n(%)"),(9,"Kontrib\nLemak"),
    (10,"Serat Kasar\n(%)"),(11,"Kontrib\nSK"),
    (12,"Abu\n(%)"),(13,"Kontrib\nAbu"),
    (14,"Ca\n(%)"),(15,"Kontrib\nCa"),
    (16,"Fosfor tsd\n(%)"),(17,"Kontrib\nP"),
    (18,"ME\n(kcal/kg)"),(19,"Kontrib\nME"),
    (20,"Lisin\n(%)"),(21,"Kontrib\nLisin"),
    (22,"Metionin\n(%)"),(23,"Kontrib\nMet"),
    (24,"Harga/kg\n(Rp)"),(25,"Biaya/kg\nPakan"),(26,"Proporsi\n(kg)"),
]
for ci, h in H3:
    fill = FOR if ci==3 else FH
    sc(wsF, 3, ci, h, fnt=FWh, fill=fill, align=AC, brd=THIN)
wsF.row_dimensions[3].height = 38

# row 4 – sub-hints
H4 = {1:"No",2:"Nama Bahan",3:"← UBAH INI",
      4:"Auto-Ref",5:"=C×D÷100",6:"Auto-Ref",7:"=C×F÷100",
      8:"Auto-Ref",9:"=C×H÷100",10:"Auto-Ref",11:"=C×J÷100",
      12:"Auto-Ref",13:"=C×L÷100",14:"Auto-Ref",15:"=C×N÷100",
      16:"Auto-Ref",17:"=C×P÷100",18:"Auto-Ref",19:"=C×R÷100",
      20:"Auto-Ref",21:"=C×T÷100",22:"Auto-Ref",23:"=C×V÷100",
      24:"Auto-Ref",25:"=C×X÷100",26:"=C÷100×batch"}
for ci, txt in H4.items():
    fill = FOR if ci==3 else FSH
    sc(wsF, 4, ci, txt, fnt=FS, fill=fill, align=AC, brd=THIN)
wsF.row_dimensions[4].height = 22

# blank spacer row 5
wsF.row_dimensions[5].height = 5

# ── ingredient rows 6–17 ──────────────────────────────────────────────
FIRST = 6
LAST  = FIRST + len(BAHAN) - 1   # 17

for idx, bh in enumerate(BAHAN):
    row     = FIRST + idx
    ref_row = 4 + idx        # row in Ref sheet
    nm      = bh[0]
    prop    = PROPORSI.get(nm, None)
    af      = FGR if idx%2==0 else FW

    sc(wsF, row, 1, idx+1, fnt=FN, fill=af, align=AC, brd=THIN)
    sc(wsF, row, 2, nm,    fnt=FN, fill=af, align=AL, brd=THIN)
    sc(wsF, row, 3, prop,  fnt=FB, fill=FOR,align=AC, brd=THIN, fmt='0.00')

    # (nut_col_in_builder, ref_col_in_Ref_sheet)
    MAPS = [
        (4,  "D"),   # Kadar Air
        (6,  "E"),   # Protein
        (8,  "F"),   # Lemak
        (10, "G"),   # SK
        (12, "H"),   # Abu
        (14, "I"),   # Ca
        (16, "J"),   # P tersedia
        (18, "K"),   # ME
        (20, "L"),   # Lisin
        (22, "M"),   # Metionin
    ]
    for bcol, rcol in MAPS:
        kol  = get_column_letter(bcol)
        kcol = get_column_letter(bcol+1)
        # reference formula
        sc(wsF, row, bcol,
           f"='{REF_SH}'!{rcol}{ref_row}",
           fnt=FN, fill=FG, align=AC, brd=THIN,
           fmt='#,##0' if bcol==18 else ('0.000' if bcol in (14,16,20,22) else '0.00'))
        # contribution formula
        if bcol == 18:  # ME – guard blank
            kontrib = f"=IF(ISNUMBER({kol}{row}),C{row}*{kol}{row}/100,0)"
        else:
            kontrib = f"=C{row}*{kol}{row}/100"
        sc(wsF, row, bcol+1, kontrib, fnt=FN, fill=FG, align=AC, brd=THIN,
           fmt='#,##0' if bcol==18 else ('0.000' if bcol in (14,16,20,22) else '0.00'))

    # Harga/kg
    sc(wsF, row, 24, f"='{REF_SH}'!C{ref_row}",
       fnt=FN, fill=FG, align=AC, brd=THIN, fmt='#,##0')
    # Biaya/kg pakan
    sc(wsF, row, 25, f"=C{row}*X{row}/100",
       fnt=FN, fill=FG, align=AC, brd=THIN, fmt='#,##0')
    # Proporsi (kg)
    sc(wsF, row, 26, f"=C{row}/100*{BATCH_REF}",
       fnt=FN, fill=FG, align=AC, brd=THIN, fmt='0.000')

# ── TOTAL row ─────────────────────────────────────────────────────────
TR = LAST + 1
wsF.merge_cells(start_row=TR, start_column=1, end_row=TR, end_column=2)
sc(wsF, TR, 1, "TOTAL", fnt=FB, fill=FTot, align=AC, brd=THIN)

for ci in [3,5,7,9,11,13,15,17,19,21,23,25,26]:
    cl = get_column_letter(ci)
    fmt = '#,##0' if ci in [19,25] else ('0.000' if ci in [15,17,21,23] else '0.00')
    sc(wsF, TR, ci, f"=SUM({cl}{FIRST}:{cl}{LAST})",
       fnt=FB, fill=FTot, align=AC, brd=THIN, fmt=fmt)
for ci in [4,6,8,10,12,14,16,18,20,22]:
    sc(wsF, TR, ci, "—", fnt=FB, fill=FTot, align=AC, brd=THIN)
sc(wsF, TR, 24, "Harga Pokok →", fnt=FB, fill=FTot, align=AR, brd=THIN)
wsF.row_dimensions[TR].height = 20

# ── TARGET & STATUS section ───────────────────────────────────────────
SEC = TR + 2
wsF.merge_cells(f"A{SEC}:Z{SEC}")
sc(wsF, SEC, 1,
   "BATAS & TARGET NUTRISI — AYAM BURAS GROWER",
   fnt=FB, fill=FT, align=AL, brd=MED)
wsF.row_dimensions[SEC].height = 20

# sub-header
SH = SEC + 1
TGT_COLS = [
    (1,"Label"),(2,"Keterangan"),
    (3,"Total\nProporsi (%)"),(5,"Protein\nKasar (%)"),(7,"Lemak\nKasar (%)"),
    (9,"Serat\nKasar (%)"),(11,"Abu (%)"),(13,"Ca (%)"),
    (15,"Fosfor tsd\n(%)"),(17,"Kadar Air\n(%)"),(19,"ME\n(kcal/kg)"),
    (21,"Lisin (%)"),(23,"Metionin (%)"),(25,"Harga Pokok\n(Rp/kg)"),
]
for ci, lbl in TGT_COLS:
    sc(wsF, SH, ci, lbl, fnt=FWh, fill=FH, align=AC, brd=THIN)
wsF.row_dimensions[SH].height = 36

# AKTUAL row
AR_ = SH + 1
sc(wsF, AR_, 1, "AKTUAL",              fnt=FB, fill=FG, align=AC, brd=THIN)
sc(wsF, AR_, 2, "(dari formula atas)", fnt=FS, fill=FG, align=AL, brd=THIN)
ACT = {
    3: f"=C{TR}", 5: f"=G{TR}", 7: f"=I{TR}", 9: f"=K{TR}", 11: f"=M{TR}",
    13:f"=O{TR}",15: f"=Q{TR}",17: f"=E{TR}",19: f"=S{TR}",
    21:f"=U{TR}",23: f"=W{TR}",25: f"=Y{TR}",
}
AFT = {3:'0.0',5:'0.00',7:'0.00',9:'0.00',11:'0.00',
       13:'0.000',15:'0.000',17:'0.00',19:'#,##0',21:'0.000',23:'0.000',25:'#,##0'}
for col, formula in ACT.items():
    sc(wsF, AR_, col, formula, fnt=FB, fill=FG, align=AC, brd=THIN, fmt=AFT[col])
wsF.row_dimensions[AR_].height = 18

# TARGET MIN
TMI = AR_ + 1
sc(wsF, TMI, 1, "TARGET MIN", fnt=FB, fill=FOR, align=AC, brd=THIN)
sc(wsF, TMI, 2, "SNI / NRC →", fnt=FS, fill=FOR, align=AL, brd=THIN)
# (col, nilai_min)
MINS = {3:100, 5:16.0, 7:3.0, 9:None, 11:None,
        13:0.70,15:0.35,17:None,19:2700,21:0.70,23:0.30,25:None}
for col, val in MINS.items():
    sc(wsF, TMI, col, val, fnt=FB, fill=FOR, align=AC, brd=THIN, fmt=AFT[col])
wsF.row_dimensions[TMI].height = 18

# TARGET MAX
TMA = TMI + 1
sc(wsF, TMA, 1, "TARGET MAX", fnt=FB, fill=FMax, align=AC, brd=THIN)
sc(wsF, TMA, 2, "SNI / NRC →", fnt=FS, fill=FMax, align=AL, brd=THIN)
MAXS = {3:100, 5:18.0, 7:None, 9:8.0, 11:8.0,
        13:1.00,15:None,17:14.0,19:2900,21:None,23:None,25:None}
for col, val in MAXS.items():
    sc(wsF, TMA, col, val, fnt=FB, fill=FMax, align=AC, brd=THIN, fmt=AFT[col])
wsF.row_dimensions[TMA].height = 18

# STATUS
STA = TMA + 1
sc(wsF, STA, 1, "STATUS", fnt=FB, fill=FG, align=AC, brd=THIN)
sc(wsF, STA, 2, "Cek otomatis", fnt=FS, fill=FG, align=AL, brd=THIN)

def sta_formula(act_col, min_row=None, max_row=None):
    ac = f"{get_column_letter(act_col)}{AR_}"
    conds = []
    if min_row:
        conds.append(f"{ac}>={get_column_letter(act_col)}{min_row}")
    if max_row:
        conds.append(f"{ac}<={get_column_letter(act_col)}{max_row}")
    if not conds: return '"—"'
    chk = "AND("+",".join(conds)+")" if len(conds)>1 else conds[0]
    return f'=IF({chk},"✅ OK","⚠️ KURANG")'

STA_MAP = {
    3:  (TMI, TMA),    # proporsi: 100 ≤ x ≤ 100
    5:  (TMI, TMA),    # protein
    7:  (TMI, None),   # lemak min
    9:  (None, TMA),   # SK max
    11: (None, TMA),   # abu max
    13: (TMI, TMA),    # Ca range
    15: (TMI, None),   # P min
    17: (None, TMA),   # air max
    19: (TMI, TMA),    # ME range
    21: (TMI, None),   # lisin min
    23: (TMI, None),   # metionin min
}
for acol, (mnr, mxr) in STA_MAP.items():
    sc(wsF, STA, acol, sta_formula(acol, mnr, mxr),
       fnt=FB, fill=FG, align=AC, brd=THIN)
wsF.row_dimensions[STA].height = 18

# Tips
TIP = STA + 2
wsF.merge_cells(f"A{TIP}:Z{TIP}")
sc(wsF, TIP, 1,
   f"💡 CARA PAKAI: Ubah angka di Kolom C (Proporsi %) "
   f"hingga Total = 100% dan semua STATUS = ✅ OK.  "
   f"Isi Total Batch (kg) di {get_column_letter(BATCH_VAL)}2 → Kolom Z = kebutuhan kg per batch.  "
   f"Edit Harga/nilai nutrisi di sheet '{REF_SH}'.",
   fnt=FS, fill=FY, align=AL, brd=THIN)
wsF.row_dimensions[TIP].height = 26

LEG = TIP + 1
wsF.merge_cells(f"A{LEG}:Z{LEG}")
sc(wsF, LEG, 1,
   "⚡ ORANGE = kamu isi  |  HIJAU = otomatis terhitung  |  "
   "✅ = memenuhi standar  |  ⚠️ = perlu penyesuaian  |  "
   "Propionic Acid & Choline Chloride tidak berkontribusi nutrisi makro",
   fnt=FS, fill=FG, align=AL, brd=THIN)

# column widths
wsF.column_dimensions["A"].width = 4
wsF.column_dimensions["B"].width = 26
wsF.column_dimensions["C"].width = 9
for ci in range(4, 27):
    wsF.column_dimensions[get_column_letter(ci)].width = 9
wsF.column_dimensions[get_column_letter(BATCH_COL)].width   = 13
wsF.column_dimensions[get_column_letter(BATCH_VAL)].width   = 10
wsF.freeze_panes = "C5"

# ════════════════════════════════════════════════════════════
# SHEET 3 – RINGKASAN FORMULA
# ════════════════════════════════════════════════════════════
wsS = wb.create_sheet("Ringkasan Formula")

wsS.merge_cells("A1:H1")
sc(wsS,1,1,"RINGKASAN FORMULA PAKAN AYAM BURAS — PPBIB",
   fnt=FTi,fill=FT,align=AC,brd=MED)
wsS.row_dimensions[1].height=24

# Subtitle
wsS.merge_cells("A2:H2")
sc(wsS,2,1,
   "Formula Grower | Total Batch: 100 kg | Instruktur: Aditiya Nugraha — PPBIB",
   fnt=FS,fill=FSH,align=AL,brd=THIN)

# Section A – Komposisi
wsS.merge_cells("A4:H4")
sc(wsS,4,1,"A.  KOMPOSISI BAHAN BAKU",fnt=FWh,fill=FH,align=AL,brd=THIN)
wsS.row_dimensions[4].height=20

for ci, h in enumerate(["No","Nama Bahan","Kategori","Proporsi (%)","Jumlah (kg/100 kg batch)","Harga/kg (Rp)","Biaya (Rp)","% Biaya"],1):
    sc(wsS,5,ci,h,fnt=FWh,fill=FH,align=AC,brd=THIN)
wsS.row_dimensions[5].height=30

for idx, bh in enumerate(BAHAN):
    row   = 6+idx
    nm,hg,*_ ,kat = bh[0],bh[1],bh[2],bh[3],bh[4],bh[5],bh[6],bh[7],bh[8],bh[9],bh[10],bh[11],bh[12]
    prop  = PROPORSI.get(nm, 0)
    jumlah= prop    # per 100 kg batch
    biaya = prop * hg / 100
    af    = FGR if idx%2==0 else FW
    sc(wsS, row, 1, idx+1,     fnt=FN, fill=af, align=AC, brd=THIN)
    sc(wsS, row, 2, nm,        fnt=FN, fill=af, align=AL, brd=THIN)
    sc(wsS, row, 3, kat,       fnt=FN, fill=af, align=AL, brd=THIN)
    sc(wsS, row, 4, prop,      fnt=FB, fill=FOR,align=AC, brd=THIN, fmt='0.00')
    sc(wsS, row, 5, jumlah,    fnt=FN, fill=FG, align=AC, brd=THIN, fmt='0.000')
    sc(wsS, row, 6, hg,        fnt=FN, fill=FOR,align=AC, brd=THIN, fmt='#,##0')
    sc(wsS, row, 7, biaya,     fnt=FN, fill=FG, align=AC, brd=THIN, fmt='#,##0')
    # % biaya dihitung manual saja (static)
    total_biaya = sum(PROPORSI.get(b[0],0)*b[1]/100 for b in BAHAN)
    sc(wsS, row, 8, round(biaya/total_biaya*100,1) if total_biaya else 0,
       fnt=FN, fill=FG, align=AC, brd=THIN, fmt='0.0')

# Total row
STOT = 6+len(BAHAN)
wsS.merge_cells(f"A{STOT}:C{STOT}")
sc(wsS, STOT, 1, "TOTAL", fnt=FB, fill=FTot, align=AC, brd=THIN)
sc(wsS, STOT, 4, f"=SUM(D6:D{STOT-1})", fnt=FB, fill=FTot, align=AC, brd=THIN, fmt='0.00')
sc(wsS, STOT, 5, f"=SUM(E6:E{STOT-1})", fnt=FB, fill=FTot, align=AC, brd=THIN, fmt='0.000')
sc(wsS, STOT, 7, f"=SUM(G6:G{STOT-1})", fnt=FB, fill=FTot, align=AC, brd=THIN, fmt='#,##0')
sc(wsS, STOT, 8, "100.0", fnt=FB, fill=FTot, align=AC, brd=THIN, fmt='0.0')

# Section B – Nilai Nutrisi
NUT_SEC = STOT + 3
wsS.merge_cells(f"A{NUT_SEC}:H{NUT_SEC}")
sc(wsS, NUT_SEC, 1, "B.  NILAI NUTRISI TERHITUNG",
   fnt=FWh, fill=FH, align=AL, brd=THIN)
wsS.row_dimensions[NUT_SEC].height = 20

# compute manually
def calc_nut(bahan_list, proporsi_dict, nut_idx):
    """nut_idx: index in bahan tuple after name: 2=air,3=prot,4=lem,5=sk,6=abu,7=ca,8=pav,9=me,10=lys,11=met"""
    total = sum(proporsi_dict.get(b[0],0) * b[nut_idx] / 100 for b in bahan_list)
    return round(total, 4)

nut_results = [
    ("Kadar Air (%)",         calc_nut(BAHAN, PROPORSI, 2),   "maks 14 %",  "maks 14 %"),
    ("Protein Kasar (%)",     calc_nut(BAHAN, PROPORSI, 3),   "min 16 %",   "16–18 %"),
    ("Lemak Kasar (%)",       calc_nut(BAHAN, PROPORSI, 4),   "min 3 %",    "3–6 %"),
    ("Serat Kasar (%)",       calc_nut(BAHAN, PROPORSI, 5),   "maks 8 %",   "maks 8 %"),
    ("Abu (%)",               calc_nut(BAHAN, PROPORSI, 6),   "maks 8 %",   "maks 8 %"),
    ("Kalsium / Ca (%)",      calc_nut(BAHAN, PROPORSI, 7),   "0.70–1.00 %","0.70–1.00 %"),
    ("Fosfor tersedia (%)",   calc_nut(BAHAN, PROPORSI, 8),   "min 0.35 %", "0.35–0.50 %"),
    ("ME (kcal/kg)",          calc_nut(BAHAN, PROPORSI, 9),   "min 2700",   "2700–2900"),
    ("Lisin (%)",             calc_nut(BAHAN, PROPORSI,10),   "min 0.70 %", "0.70–0.90 %"),
    ("Metionin (%)",          calc_nut(BAHAN, PROPORSI,11),   "min 0.30 %", "0.30–0.40 %"),
]

for ci, h in enumerate(["Parameter","Nilai Aktual","Satuan","Standar Min/Max (Buras Grower)","Status"],1):
    sc(wsS, NUT_SEC+1, ci, h, fnt=FWh, fill=FH, align=AC, brd=THIN)
wsS.row_dimensions[NUT_SEC+1].height = 28

def status_str(label, val, target_min, target_max):
    status_ok  = True
    if "Kadar Air" in label or "Serat" in label or "Abu" in label:
        if "Air" in label and val > 14: status_ok = False
        if "Serat" in label and val > 8: status_ok = False
        if "Abu"   in label and val > 8: status_ok = False
    elif "Ca" in label:
        if val < 0.70 or val > 1.00: status_ok = False
    elif "ME" in label:
        if val < 2700 or val > 2900: status_ok = False
    elif "Protein" in label:
        if val < 16 or val > 18: status_ok = False
    elif "Lemak" in label:
        if val < 3: status_ok = False
    elif "Fosfor" in label:
        if val < 0.35: status_ok = False
    elif "Lisin" in label:
        if val < 0.70: status_ok = False
    elif "Metionin" in label:
        if val < 0.30: status_ok = False
    return "✅ OK" if status_ok else "⚠️ Perlu Sesuaikan"

satuan = ["%","%","%","%","%","%","%","kcal/kg","%","%"]
for ni, (label, val, tgt_min, tgt_rng) in enumerate(nut_results):
    row = NUT_SEC+2+ni
    af  = FGR if ni%2==0 else FW
    sts = status_str(label, val, tgt_min, None)
    fmt = '#,##0' if 'ME' in label else ('0.000' if ('Ca' in label or 'Fosfor' in label or 'Lisin' in label or 'Metionin' in label) else '0.00')
    sc(wsS, row, 1, label,  fnt=FN, fill=af,  align=AL, brd=THIN)
    sc(wsS, row, 2, val,    fnt=FB, fill=FG,  align=AC, brd=THIN, fmt=fmt)
    sc(wsS, row, 3, satuan[ni], fnt=FN, fill=af, align=AC, brd=THIN)
    sc(wsS, row, 4, tgt_rng,fnt=FN, fill=af,  align=AC, brd=THIN)
    stat_fill = FG if "✅" in sts else PatternFill("solid",fgColor="FF7070")
    sc(wsS, row, 5, sts,    fnt=FB, fill=stat_fill, align=AC, brd=THIN)
    wsS.row_dimensions[row].height = 18

# Section C – Harga
price_sec = NUT_SEC+2+len(nut_results)+2
wsS.merge_cells(f"A{price_sec}:H{price_sec}")
sc(wsS, price_sec, 1, "C.  ESTIMASI HARGA POKOK",
   fnt=FWh, fill=FH, align=AL, brd=THIN)

total_biaya = sum(PROPORSI.get(b[0],0)*b[1]/100 for b in BAHAN)
sc(wsS, price_sec+1, 1, "Harga Pokok / kg pakan", fnt=FB, fill=FG, align=AL, brd=THIN)
sc(wsS, price_sec+1, 2, round(total_biaya,0), fnt=FB, fill=FG, align=AC, brd=THIN, fmt='"Rp "#,##0')

# column widths
wsS.column_dimensions["A"].width = 26
wsS.column_dimensions["B"].width = 15
wsS.column_dimensions["C"].width = 10
wsS.column_dimensions["D"].width = 22
wsS.column_dimensions["E"].width = 20
wsS.column_dimensions["F"].width = 14
wsS.column_dimensions["G"].width = 14
wsS.column_dimensions["H"].width = 10

# ── SAVE ────────────────────────────────────────────────────────────────
OUT = "/home/user/ppbib/PPBIB_Formula_Ayam_Buras_v1.xlsx"
wb.save(OUT)
print(f"✅ Saved: {OUT}")
print(f"   Sheets : {wb.sheetnames}")
print(f"   Bahan  : {len(BAHAN)}")
print(f"   Total proporsi: {sum(PROPORSI.values())}%")
print()
print("=== NILAI NUTRISI FORMULA ===")
for label, val, tgt, rng in nut_results:
    s = status_str(label, val, tgt, None)
    print(f"  {label:30s}  {val:8.3f}   {rng:20s}  {s}")
print(f"  {'Harga Pokok (Rp/kg)':30s}  {total_biaya:8.0f}")
