# PPBIB — Instruksi Rutin Harian

## Konteks Bisnis

PPBIB adalah platform investasi dan kemitraan **budidaya ikan air tawar komersial**.

**Target audiens:** Investor dan pengusaha menengah ke atas (modal Rp 50 juta+) yang mencari
peluang passive income atau diversifikasi bisnis ke sektor akuakultur. Bukan peternak kecil.

**Niche:** Lele, nila, gurame, patin, mas — skala komersial (kolam terpal besar, sistem RAS, bioflok, hatchery).

**Angle konten selalu:** ROI, proyeksi keuntungan, modal masuk, payback period, kemitraan bisnis.

---

## Tugas Rutin Harian (Berjalan Setiap Pagi)

Urutan kerja: ambil trend → filter premium → susun brief → **kirim email langsung** → simpan ke file → push repo.

### Langkah 1 — Ambil Data Trend

Panggil TrendsMCP untuk mengambil data dari beberapa sumber:

```
get_top_trends(type="Google Trends", limit=50)
get_top_trends(type="YouTube Trending", limit=20)
get_top_trends(type="Reddit Hot Posts", limit=20)

get_growth(keyword="budidaya ikan nila", source="google search", percent_growth=["7D","1M"])
get_growth(keyword="budidaya ikan lele", source="google search", percent_growth=["7D","1M"])
get_growth(keyword="kolam terpal ikan", source="google search", percent_growth=["7D","1M"])
get_growth(keyword="investasi budidaya ikan", source="google search", percent_growth=["7D","1M"])
get_growth(keyword="sistem RAS ikan", source="google search", percent_growth=["7D","1M"])
get_growth(keyword="bioflok ikan", source="google search", percent_growth=["7D","1M"])
get_growth(keyword="budidaya ikan gurame", source="youtube", percent_growth=["7D","1M"])
get_growth(keyword="budidaya ikan komersial", source="youtube", percent_growth=["7D","1M"])
```

### Langkah 2 — Filter untuk Target Premium

**MASUKKAN** topik yang mengandung sinyal:
- Intent investasi/bisnis: `investasi`, `ROI`, `modal`, `keuntungan`, `profit`, `komersial`,
  `skala besar`, `hatchery`, `RAS`, `bioflok`, `kemitraan`, `ekspor`, `margin`, `omzet`,
  `harga pasar`, `supplier`, `distributor`, `kontrak`, `sertifikasi`
- Keyword niche: `budidaya ikan`, `lele`, `nila`, `gurame`, `patin`, `mas`, `bawal`,
  `kolam terpal`, `kolam beton`, `pakan ikan`, `benih ikan`, `akuakultur`, `aquaculture`
- Momentum positif: pertumbuhan 7D atau 1M > +10%

**KELUARKAN** topik yang mengandung:
- `pemula`, `murah`, `hemat`, `cara membuat sendiri`, `gratis`, `modal kecil`,
  `tanpa modal`, `sederhana`, `rumahan`, `ternak sampingan`, `tutorial dasar`

### Langkah 3 — Susun Content Brief

Buat ringkasan content brief harian berisi:
- Top 3 topik premium dengan skor tertinggi
- Momentum keyword (naik/turun berapa %)
- 3 rekomendasi judul konten siap pakai (angle investasi/ROI)
- 1 insight pasar yang bisa jadi hook konten hari ini

Format brief harus ringkas, padat, dan actionable — bisa langsung dipakai tim konten.

### Langkah 4 — Kirim Email (WAJIB, BUKAN DRAFT)

> **PENTING: Gunakan fungsi KIRIM langsung, BUKAN buat draft.**
> Jangan pernah menggunakan `create_draft` — selalu gunakan `send_email` atau tool kirim yang tersedia.

Kirim email dengan format:

```
Kepada : ditnug@gmail.com
Subjek : [PPBIB] Content Brief Harian — {tanggal hari ini}
Isi    : (lihat template di bawah)
```

**Template isi email:**

```
Content Brief Harian PPBIB
{hari}, {tanggal} — Budidaya Ikan Air Tawar Premium

📈 TOPIK TRENDING HARI INI

1. [Topik #1] — Skor: XX | Growth 7D: +X%
   Angle: ...

2. [Topik #2] — Skor: XX | Growth 7D: +X%
   Angle: ...

3. [Topik #3] — Skor: XX | Growth 7D: +X%
   Angle: ...

🎯 REKOMENDASI JUDUL KONTEN

1. "[Judul konten siap pakai dengan angle investasi/ROI]"
2. "[Judul konten siap pakai dengan angle investasi/ROI]"
3. "[Judul konten siap pakai dengan angle investasi/ROI]"

💡 INSIGHT PASAR
[1-2 kalimat insight yang bisa jadi hook konten hari ini]

📊 DATA KEYWORD
Budidaya ikan nila  : 7D [X%] | 1M [X%]
Budidaya ikan lele  : 7D [X%] | 1M [X%]
Kolam terpal ikan   : 7D [X%] | 1M [X%]
Investasi budidaya  : 7D [X%] | 1M [X%]
Sistem RAS ikan     : 7D [X%] | 1M [X%]
Bioflok ikan        : 7D [X%] | 1M [X%]

---
Dikirim otomatis oleh Rutin PPBIB — setiap pagi 07:00 WIB
```

### Langkah 5 — Simpan ke `data/trend_insights.json`

Setelah email terkirim, simpan data lengkap ke file:

```json
{
  "date": "YYYY-MM-DD",
  "premium_topics": [
    {"topic": "nama topik", "score": 80, "source": "google search", "growth_7d": 15.2}
  ],
  "rising_topics": ["topik yang tumbuh >20% dalam 7 hari"],
  "youtube_trending": ["topik video budidaya ikan yang sedang naik"],
  "keyword_growth": {
    "budidaya ikan nila": {"7d": 0.0, "1m": 0.0},
    "budidaya ikan lele": {"7d": 0.0, "1m": 0.0},
    "kolam terpal ikan": {"7d": 0.0, "1m": 0.0},
    "investasi budidaya ikan": {"7d": 0.0, "1m": 0.0},
    "sistem RAS ikan": {"7d": 0.0, "1m": 0.0},
    "bioflok ikan": {"7d": 0.0, "1m": 0.0}
  },
  "content_recommendations": [
    "Rekomendasi 1", "Rekomendasi 2", "Rekomendasi 3"
  ],
  "saved_at": "ISO timestamp"
}
```

### Langkah 6 — Commit dan Push

```bash
git add data/trend_insights.json
git commit -m "data: update trend insights harian $(date +%Y-%m-%d)"
git push
```

---

## Aturan Konten (Selalu Berlaku)

| | Lakukan | Hindari |
|---|---|---|
| **Angle** | ROI, investasi, proyeksi, skala komersial | Tips pemula, hemat, DIY |
| **Angka** | Rp/bulan, % ROI, m², ekor/siklus, payback | Harga satuan murah |
| **CTA** | Konsultasi, feasibility study, kemitraan | Download ebook gratis |
| **Tone** | Konsultan bisnis berpengalaman | Tutorial channel YouTube |

---

## Struktur File Penting

```
data/
  trend_insights.json      ← ditulis rutin ini setiap hari
  strategy_insights.json   ← ditulis auto_research.py setiap Sabtu
  content_queue.json       ← ditulis content_generator.py setiap Minggu

src/
  trend_researcher.py      ← membaca trend_insights.json, scoring, filter
  content_generator.py     ← generate konten mingguan dengan context trend
  auto_research.py         ← evaluasi performa + update strategi
```

---

## Alur Kerja Mingguan

```
Harian 07:00  → Rutin ini: trend → filter → brief → KIRIM EMAIL → simpan file
Sabtu  17:00  → auto_research.py: evaluasi performa + update strategi
Minggu 18:00  → content_generator.py: generate rencana konten lengkap
```

---

## Catatan Teknis

- **Email HARUS dikirim langsung** — jangan buat draft
- `data/trend_insights.json` selalu ditimpa setiap hari (bukan append)
- Jika TrendsMCP gagal total, tetap kirim email dengan topik evergreen premium
  dan tandai sebagai "Data trend tidak tersedia hari ini"
- Skor 0 pada keyword bukan error — artinya tidak ada data momentum
