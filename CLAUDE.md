# PPBIB — Instruksi Rutin Harian

## Konteks Bisnis

PPBIB adalah platform investasi dan kemitraan **budidaya ikan air tawar komersial**.

**Target audiens:** Investor dan pengusaha menengah ke atas (modal Rp 50 juta+) yang mencari
peluang passive income atau diversifikasi bisnis ke sektor akuakultur. Bukan peternak kecil.

**Niche:** Lele, nila, gurame, patin, mas — skala komersial (kolam terpal besar, sistem RAS, bioflok, hatchery).

**Angle konten selalu:** ROI, proyeksi keuntungan, modal masuk, payback period, kemitraan bisnis.

---

## Tugas Rutin Harian (Berjalan Setiap Pagi)

Tugas utamamu adalah **mengambil data trending, menyaring yang relevan untuk target premium,
lalu menyimpan hasilnya ke `data/trend_insights.json`** agar dibaca otomatis oleh bot konten.

### Langkah 1 — Ambil Data Trend

Panggil TrendsMCP untuk mengambil data dari beberapa sumber:

```
# Topik trending umum (untuk dicari yang relevan)
get_top_trends(type="Google Trends", limit=50)
get_top_trends(type="YouTube", limit=20)       # jika tersedia
get_top_trends(type="Reddit Hot Posts", limit=20)

# Keyword spesifik niche — cek momentum
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

Dari semua data yang masuk, pilih topik yang memenuhi kriteria berikut:

**MASUKKAN jika mengandung sinyal:**
- Intent investasi/bisnis: `investasi`, `ROI`, `modal`, `keuntungan`, `profit`, `komersial`,
  `skala besar`, `hatchery`, `RAS`, `bioflok`, `kemitraan`, `ekspor`, `margin`, `omzet`,
  `harga pasar`, `supplier`, `distributor`, `kontrak`, `sertifikasi`
- Keyword niche: `budidaya ikan`, `lele`, `nila`, `gurame`, `patin`, `mas`, `bawal`,
  `kolam terpal`, `kolam beton`, `pakan ikan`, `benih ikan`, `akuakultur`, `aquaculture`
- Momentum positif: pertumbuhan 7D atau 1M > +10%

**KELUARKAN jika mengandung:**
- `pemula`, `murah`, `hemat`, `cara membuat sendiri`, `gratis`, `modal kecil`,
  `tanpa modal`, `sederhana`, `rumahan`, `ternak sampingan`, `tutorial dasar`

### Langkah 3 — Beri Skor Premium Intent (0-100)

Untuk setiap topik yang lolos filter:
- +20 poin per kata kunci intent premium yang ditemukan
- +10 poin per kata kunci niche yang ditemukan
- -30 poin per kata kunci eksklusi yang ditemukan
- Skor minimum 0, maksimum 100

### Langkah 4 — Simpan ke `data/trend_insights.json`

Buat atau timpa file `data/trend_insights.json` dengan format berikut:

```json
{
  "date": "YYYY-MM-DD",
  "premium_topics": [
    {"topic": "nama topik", "score": 80, "source": "google search", "growth_7d": 15.2},
    {"topic": "nama topik", "score": 60, "source": "youtube", "growth_7d": 8.5}
  ],
  "rising_topics": [
    "topik yang tumbuh >20% dalam 7 hari"
  ],
  "youtube_trending": [
    "topik video budidaya ikan yang sedang naik di YouTube"
  ],
  "keyword_growth": {
    "budidaya ikan nila": {"7d": 0.0, "1m": 0.0},
    "budidaya ikan lele": {"7d": 0.0, "1m": 0.0},
    "kolam terpal ikan": {"7d": 0.0, "1m": 0.0},
    "investasi budidaya ikan": {"7d": 0.0, "1m": 0.0},
    "sistem RAS ikan": {"7d": 0.0, "1m": 0.0},
    "bioflok ikan": {"7d": 0.0, "1m": 0.0}
  },
  "content_recommendations": [
    "Rekomendasi topik konten minggu ini berdasarkan trend + skor premium tertinggi",
    "Maksimal 5 rekomendasi, masing-masing 1 kalimat dengan angle bisnis/investasi"
  ],
  "saved_at": "ISO timestamp"
}
```

### Langkah 5 — Commit dan Push

Setelah file tersimpan, commit ke branch utama:

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
| **Platform** | LinkedIn, Instagram (infografis data), YouTube (farm tour) | — |

---

## Struktur File Penting

```
data/
  trend_insights.json      ← ditulis rutin ini setiap hari
  strategy_insights.json   ← ditulis auto_research.py setiap Sabtu
  content_queue.json       ← ditulis content_generator.py setiap Minggu
  analytics_tiktok.json    ← ditulis analytics.py setiap hari 19:00
  analytics_instagram.json ← ditulis analytics.py setiap hari 19:00
  analytics_facebook.json  ← ditulis analytics.py setiap hari 19:00

src/
  trend_researcher.py      ← membaca trend_insights.json, scoring, filter
  content_generator.py     ← generate konten mingguan dengan context trend
  auto_research.py         ← evaluasi performa + update strategi
  analytics.py             ← snapshot metrik harian
```

---

## Alur Kerja Mingguan

```
Harian 07:00  → Rutin ini: ambil trend → filter premium → simpan trend_insights.json
Harian 08:00  → video_producer.py: produksi video harian
Harian 19:00  → analytics.py: snapshot metrik platform
Harian 20:00  → kirim laporan harian via WA
Sabtu  17:00  → auto_research.py: evaluasi performa + update strategy_insights.json
Minggu 18:00  → content_generator.py: baca trend + strategi → generate rencana konten
```

---

## Catatan Teknis

- `data/trend_insights.json` **selalu ditimpa** setiap hari (bukan append)
- Jika TrendsMCP tidak mengembalikan data untuk keyword tertentu, isi dengan `null`
- Jika semua TrendsMCP gagal, tetap simpan file dengan `premium_topics: []` dan
  `content_recommendations` berisi topik evergreen premium default
- Skor 0 pada suatu keyword bukan error — artinya tidak ada data
