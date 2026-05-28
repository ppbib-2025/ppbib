# Direktif: Lead Intake PPBIB — WA dari Lead Magnet PDF

## Tujuan
Mengolah setiap leads baru yang masuk via WhatsApp (dari lead magnet PDF) menjadi percakapan konsultatif yang terstruktur — bukan pitch penjualan. Output akhir adalah draft reply WA pertama yang membangun kepercayaan dan menggerakkan leads ke tahap berikutnya.

---

## Step 1 — Identifikasi Species

Tentukan species dari pesan leads. Jika tidak disebutkan eksplisit, tanya sebelum lanjut.

| Kode | Species | Catatan Kunci |
|------|---------|---------------|
| NILA | Nila (*Oreochromis niloticus*) | FCR ideal 1,2–1,5; toleran kondisi ekstrem |
| LELE | Lele (*Clarias* sp.) | FCR ideal 0,8–1,2; siklus panen cepat 60–75 hari |
| GURAME | Gurame (*Osphronemus goramy*) | FCR ideal 1,5–2,0; harga jual tinggi, siklus panjang |
| MAS | Mas (*Cyprinus carpio*) | FCR ideal 1,5–2,0; sensitif kualitas air |
| PATIN | Patin (*Pangasius* sp.) | FCR ideal 1,3–1,6; potensi ekspor, butuh DO stabil |

**Jika species belum jelas:** tunda semua analisis, tanyakan dulu.

### Kalkulasi Estimasi Kerugian Akibat FCR Tinggi

Setelah species teridentifikasi, hitung estimasi kerugian finansial akibat FCR tidak optimal berdasarkan skala kolam leads. Output wajib berupa **angka rupiah konkret** yang relevan untuk leads tersebut.

**Asumsi harga pakan komersial:** Rp 9.000–12.000/kg (gunakan Rp 10.000/kg sebagai baseline).

**Formula:**

```
Selisih FCR      = FCR aktual rata-rata - FCR ideal
Bobot panen (kg) = jumlah ekor × berat panen rata-rata per ekor
Kelebihan pakan  = Selisih FCR × Bobot panen
Kerugian (Rp)    = Kelebihan pakan × harga pakan/kg
```

**Tabel referensi cepat per species:**

| Species | FCR Ideal | FCR Aktual Rata-rata Pembudidaya | Berat Panen Rata-rata | Selisih FCR |
|---------|-----------|----------------------------------|-----------------------|-------------|
| NILA    | 1,3       | 1,8                              | 300 g / ekor          | 0,5         |
| LELE    | 1,0       | 1,5                              | 100 g / ekor          | 0,5         |
| GURAME  | 1,7       | 2,5                              | 500 g / ekor          | 0,8         |
| MAS     | 1,7       | 2,4                              | 400 g / ekor          | 0,7         |
| PATIN   | 1,4       | 2,0                              | 600 g / ekor          | 0,6         |

**Contoh kalkulasi — NILA skala KECIL (1.000 ekor):**
- Bobot panen: 1.000 × 0,3 kg = 300 kg
- Kelebihan pakan: 0,5 × 300 kg = 150 kg pakan terbuang
- Kerugian per siklus: 150 kg × Rp 10.000 = **Rp 1.500.000/siklus**
- Kerugian per tahun (3 siklus): **Rp 4.500.000/tahun**

**Instruksi output:** Angka ini digunakan sebagai *pain point* konkret dalam draft reply WA (Step 5) — bukan untuk menakut-nakuti, tapi untuk memperlihatkan nilai nyata dari optimasi FCR.

---

## Step 2 — Identifikasi Skala Kolam

Klasifikasikan skala berdasarkan jumlah ekor ATAU luas kolam yang disebutkan leads.

| Skala | Jumlah Ekor | Luas Kolam | Profil |
|-------|-------------|------------|--------|
| MIKRO | < 500 ekor | < 20 m² | Pemula, hobi, uji coba |
| KECIL | 500–5.000 ekor | 20–200 m² | Usaha rumahan, sampingan |
| MENENGAH | 5.000–50.000 ekor | 200–2.000 m² | Semi-komersial |
| BESAR | > 50.000 ekor | > 2.000 m² | Komersial penuh |

**Catatan:** Jika leads menyebut luas lahan tapi belum ada kolam, catat sebagai *potensi skala* dan gunakan untuk rekomendasi.

---

## Step 3 — Identifikasi Masalah Utama

Klasifikasikan keluhan atau kebutuhan leads ke dalam kategori berikut. Satu leads bisa punya lebih dari satu masalah — prioritaskan yang disebut pertama.

| Kode Masalah | Deskripsi | Sinyal dari Pesan Leads |
|--------------|-----------|-------------------------|
| PAKAN | Biaya/formulasi pakan tinggi atau tidak tahu buat pakan sendiri | "pakan mahal", "tidak tahu cara buat pakan", "FCR tinggi" |
| KEMATIAN | Angka kematian tinggi (mortality rate) | "ikan mati terus", "banyak yang mati", "susah besar" |
| KUALITAS_AIR | Masalah pH, DO, amonia, warna air | "air keruh", "bau", "pH tidak stabil" |
| PERTUMBUHAN | Pertumbuhan lambat atau tidak seragam | "lama besar", "ukuran tidak rata", "FCR boros" |
| MODAL | Keterbatasan modal awal atau modal kerja | "modal terbatas", "belum ada dana", "cicilan" |
| PASAR | Tidak tahu jual ke mana atau harga rendah | "jual ke mana", "harga anjlok", "tidak ada pembeli" |
| TEKNIS_UMUM | Pemula total, belum punya pengetahuan dasar | "baru mau mulai", "belum pernah", "tidak tahu sama sekali" |

---

## Step 4 — Tentukan Funnel Stage

Gunakan kombinasi dari Step 1–3 untuk menentukan posisi leads dalam funnel.

| Stage | Nama | Ciri-Ciri | Tindakan |
|-------|------|-----------|----------|
| F1 | **Awareness** | Baru tahu PPBIB dari PDF, belum jelas mau apa, pertanyaan sangat umum | Bangun rapport, identifikasi lebih dalam |
| F2 | **Consideration** | Sudah tahu mau budidaya species tertentu, tapi masih ragu atau banyak pertanyaan teknis | Berikan data dan solusi spesifik, tawarkan konsultasi |
| F3 | **Intent** | Sudah ada rencana konkret (lahan, modal, target panen), butuh panduan eksekusi | Arahkan ke program pelatihan atau pendampingan |
| F4 | **Decision** | Sudah tanya harga, jadwal, atau mekanisme pelatihan | Fasilitasi pendaftaran, berikan social proof |

**Panduan penentuan stage:**
- Pesan sangat singkat + belum ada detail → F1
- Ada species + ada masalah spesifik → F2
- Ada species + skala + timeline → F3
- Ada pertanyaan harga/program → F4

---

## Step 5 — Susun Draft Reply WA Pertama

### Prinsip Wajib
- **Konsultatif, bukan promotif.** Jangan sebut harga atau nama program di pesan pertama.
- **Berbasis data.** Selipkan 1 angka relevan (FCR, mortality rate rata-rata, persentase biaya pakan, dll).
- **Ajukan maksimal 3 pertanyaan kualifikasi.** Pilih yang paling relevan dengan masalah utama.
- **Panjang pesan:** 80–150 kata. Singkat, tidak menggurui.
- **Nada:** Hangat, profesional, seperti konsultan — bukan sales, bukan guru.

### Template Struktur Reply

```
[Sambutan singkat + validasi niat leads]

[1 insight data relevan dengan species/masalah — membangun kredibilitas]

[Pertanyaan kualifikasi 1 — tentang kondisi saat ini]
[Pertanyaan kualifikasi 2 — tentang sumber daya yang dimiliki]
[Pertanyaan kualifikasi 3 — tentang target/timeline]

[Closing hangat yang mengundang respons]
```

### Pertanyaan Kualifikasi per Masalah Utama

| Masalah | Pertanyaan Kualifikasi yang Disarankan |
|---------|---------------------------------------|
| PAKAN | Bahan baku lokal apa yang tersedia? Sudah punya mesin pelet? Target FCR saat ini berapa? |
| KEMATIAN | Sudah berapa siklus panen? Gejala kematian di usia berapa? Sudah cek kualitas air? |
| KUALITAS_AIR | Sumber air dari mana? Kolam jenis apa? Pernah ukur pH/DO? |
| PERTUMBUHAN | Pakan apa yang dipakai sekarang? Frekuensi pemberian pakan per hari? |
| MODAL | Sudah ada lahan? Estimasi modal yang disiapkan berapa? |
| PASAR | Lokasi budidaya di mana? Sudah punya pembeli tetap? Ukuran panen target berapa? |
| TEKNIS_UMUM | Sudah punya lahan? Species apa yang diminati? Target mulai kapan? |

---

## Contoh Output Lengkap

### Input Leads
> "Halo, saya dapat PDF dari PPBIB. Saya mau ternak nila 1.000 ekor tapi belum tau cara buat pakan sendiri."

### Analisis
- **Species:** NILA
- **Skala:** KECIL (1.000 ekor)
- **Masalah Utama:** PAKAN
- **Funnel Stage:** F1 → F2 (ada species + masalah spesifik, tapi belum ada detail lahan/modal)
- **Estimasi Kerugian FCR Tinggi:**
  - Bobot panen: 1.000 × 0,3 kg = 300 kg
  - Kelebihan pakan (FCR 1,8 vs ideal 1,3): 0,5 × 300 = 150 kg terbuang
  - Kerugian per siklus: 150 kg × Rp 10.000 = **Rp 1.500.000**
  - Kerugian per tahun (3 siklus): **Rp 4.500.000** → angka ini digunakan di reply WA

### Draft Reply WA
```
Halo, selamat datang di PPBIB! Senang sekali Bapak/Ibu sudah mulai serius merencanakan budidaya nila. 🙏

Sedikit gambaran dulu — untuk skala 1.000 ekor nila, pembudidaya yang belum optimalkan formulasi pakan biasanya pakai FCR 1,8, padahal idealnya bisa 1,3. Selisihnya terlihat kecil, tapi dalam 1 siklus panen itu setara sekitar 150 kg pakan yang terbuang, atau ±Rp 1.500.000 per siklus. Kalau 3 siklus setahun, Rp 4.500.000 keluar sia-sia hanya dari inefisiensi pakan.

Nah, itu yang ingin kita pangkas dari awal.

Supaya saya bisa rekomendasikan formulasi yang paling pas untuk kondisi Bapak/Ibu:

1. Kolam yang dipakai jenis apa — tanah, terpal, atau beton?
2. Bahan baku lokal apa yang mudah didapat di sekitar sini (dedak, ampas tahu, ikan rucah, dll)?
3. Target panen dalam berapa bulan ke depan?

Dari tiga info itu saya bisa langsung bantu hitung kebutuhan dan formulasinya.
```

---

## Catatan Eskalasi

- Jika leads menyebut masalah **KEMATIAN massal (>20% dalam 1 siklus):** eskalasikan ke konsultan senior, jangan tangani dengan template.
- Jika leads sudah di **F4 dan tanya harga:** lanjutkan ke direktif `closing_consultation.md`.
- Jika species **di luar 5 species utama:** catat sebagai *out-of-scope sementara*, tanya ke tim sebelum balas.

---

## Eskalasi ke Aditiya

Langsung teruskan ke Aditiya — jangan tangani sendiri — jika leads memenuhi salah satu kondisi berikut:

| Kondisi | Kriteria |
|---------|----------|
| **Skala besar** | Leads mengindikasikan skala MENENGAH (5.000–50.000 ekor) atau BESAR (>50.000 ekor) |
| **Tanya harga di pesan pertama** | Leads langsung menanyakan harga program, biaya pelatihan, atau paket pendampingan sebelum ada diskusi teknis |
| **Kematian massal** | Leads melaporkan angka kematian >30% dalam satu siklus |

**Cara eskalasi:** Balas leads dengan pesan tunggu singkat, lalu forward percakapan ke Aditiya beserta ringkasan: species, skala, masalah utama, dan kutipan pesan asli leads.

**Template pesan tunggu untuk leads:**
```
Terima kasih sudah menghubungi PPBIB. Untuk kebutuhan Bapak/Ibu, saya akan sambungkan langsung dengan konsultan senior kami agar bisa ditangani lebih tepat. Mohon tunggu sebentar ya.
```
