# Metadirektif: Leads Flow PPBIB
## Chain: lead_intake.md → fcr_calculator.py → Reply WA Final

---

## Tujuan

Dokumen ini adalah titik masuk tunggal untuk menangani leads baru PPBIB dari WA.
Ia meng-chain dua komponen yang sudah ada secara berurutan dan menghasilkan satu reply WA siap kirim.

```
[Teks WA mentah]
      │
      ▼
 lead_intake.md          ← ekstrak: species, skala, masalah, funnel stage
      │
      ▼
fcr_calculator.py        ← kalkulasi: kerugian FCR, penghematan potensial, warning
      │
      ▼
 Reply WA Final          ← 5 kalimat, 1 angka Rp, 1 pertanyaan terbuka
```

---

## Step 1 — Terima Input Leads

**Input:** teks WA mentah dari leads, copy-paste apa adanya. Tidak perlu diedit atau diringkas.

**Yang dicari dari teks:**
- Penyebutan species (nila, lele, gurame, mas, patin) — eksplisit atau tersirat
- Angka jumlah ekor atau luas kolam
- Keluhan, pertanyaan, atau niat yang disebutkan
- Sinyal urgensi atau timeline

**Jika teks terlalu pendek / ambigu:** catat sebagai F1 (Awareness), tetap jalankan Step 2 dengan data parsial, dan masukkan pertanyaan klarifikasi species ke reply akhir.

---

## Step 2 — Jalankan lead_intake.md

Referensi penuh: `lead_intake.md`

Ekstrak empat variabel berikut dari teks leads:

| Variabel | Nilai yang Dicari | Fallback jika Tidak Ada |
|----------|-------------------|-------------------------|
| `species` | nila / lele / gurame / mas / patin | tanyakan di reply |
| `skala` | mikro / kecil / menengah / besar | estimasi dari jumlah ekor jika ada |
| `masalah_utama` | PAKAN / KEMATIAN / KUALITAS_AIR / PERTUMBUHAN / MODAL / PASAR / TEKNIS_UMUM | TEKNIS_UMUM jika tidak jelas |
| `funnel_stage` | F1 / F2 / F3 / F4 | F1 jika pesan sangat singkat |

**Output Step 2:** empat variabel di atas, siap dipakai sebagai argumen Step 3.

---

## Step 3 — Jalankan fcr_calculator.py

Referensi penuh: `fcr_calculator.py`

Gunakan variabel dari Step 2 sebagai input. Untuk nilai yang belum diketahui dari leads, gunakan default berikut:

| Parameter | Cara Mengisi |
|-----------|-------------|
| `species` | dari Step 2 |
| `skala` | dari Step 2 |
| `fcr_aktual` | gunakan FCR aktual rata-rata pembudidaya dari tabel benchmark (bukan ideal) |
| `harga_pakan_per_kg` | default Rp 10.000 jika leads tidak menyebut angka |
| `target_panen_kg` | estimasi dari skala: mikro=50kg, kecil=300kg, menengah=3.000kg, besar=30.000kg |

**Perintah yang dijalankan (contoh untuk nila kecil):**
```bash
python fcr_calculator.py nila kecil 1.8 10000 300
```

**Output Step 3 yang dipakai ke Step 5:**
- `kerugian_per_siklus_rp` → angka Rp konkret untuk reply WA
- `penghematan_potensial_rp` → opsional, untuk memperkuat argumen
- `kesimpulan` → kalimat siap pakai dari `format_for_wa()`
- `warning` → diteruskan ke Step 4

---

## Step 4 — Cek Warning Validasi

Jika `result.warning` tidak kosong:

1. **Tampilkan warning** di output analisis internal (jangan sembunyikan)
2. **Jangan kirim reply** sampai skala dikonfirmasi ulang ke leads — atau gunakan skala yang lebih masuk akal sebagai asumsi dan tandai dengan `[ASUMSI SKALA]` di catatan internal
3. **Tetap generate reply WA** — tapi reply tidak menyebut angka kerugian yang mungkin salah; ganti dengan pertanyaan klarifikasi skala sebagai pertanyaan terbuka di akhir pesan

**Contoh penyesuaian reply jika ada warning:**
- Normal: *"...artinya sekitar Rp 1.500.000 terbuang per siklus..."*
- Warning aktif: *"...tergantung skala kolam pastinya, bisa kita hitung bersama setelah tahu detail kolamnya..."*

---

## Step 5 — Generate Reply WA Final

### Aturan Wajib

| Aturan | Detail |
|--------|--------|
| Panjang | Maksimal 5 kalimat |
| Bahasa | Indonesia natural — seperti obrolan konsultan, bukan surat resmi |
| Angka Rp | Wajib ada satu angka rupiah konkret dari kalkulasi FCR (kecuali warning aktif) |
| Penutup | Diakhiri satu pertanyaan terbuka — bukan ya/tidak |
| Larangan | Tidak menyebut nama produk, paket, atau harga pelatihan di pesan pertama |
| Nada | Hangat, membantu, tidak menggurui, tidak terasa jualan |

### Struktur 5 Kalimat

```
[K1] Sapaan hangat + validasi niat leads (1 kalimat)
[K2] Konteks singkat situasi leads berdasarkan data yang diceritakan (1 kalimat)
[K3] Insight data FCR + angka Rp kerugian konkret (1 kalimat)
[K4] Jembatan — apa yang bisa berubah jika masalah ini diatasi (1 kalimat)
[K5] Satu pertanyaan terbuka untuk menggali info lebih lanjut (1 kalimat)
```

### Penyesuaian Berdasarkan Funnel Stage

| Stage | Penyesuaian di Reply |
|-------|---------------------|
| F1 | K2 lebih banyak validasi, K5 tanya species/skala dulu |
| F2 | K3 langsung pakai angka FCR, K5 gali kondisi kolam atau bahan baku |
| F3 | K3 + K4 lebih ke eksekusi, K5 tanya timeline atau kendala konkret |
| F4 | Arahkan ke eskalasi Aditiya — jangan tangani sendiri |

---

## Contoh End-to-End

### Input: Teks WA Mentah dari Leads

> *"Halo kak, saya dapat buku PDF dari PPBIB tentang budidaya lele. Saya lagi coba-coba ternak lele di rumah, baru 300 ekor pakai kolam terpal 3x4. Problemnya FCR saya kayaknya boros banget, habis pakan terus tapi ikan ga gede-gede. Ada solusi?"*

---

### Step 2 — Output lead_intake.md

| Variabel | Nilai | Catatan |
|----------|-------|---------|
| `species` | lele | eksplisit disebutkan |
| `skala` | mikro | 300 ekor, kolam 3×4 m = 12 m² |
| `masalah_utama` | PERTUMBUHAN + PAKAN | FCR boros + ikan tidak tumbuh |
| `funnel_stage` | F2 | ada species, ada masalah spesifik, ada detail kolam |

---

### Step 3 — Perintah fcr_calculator.py

```bash
python fcr_calculator.py lele mikro 1.5 10000 30
```

*(target panen 30 kg = estimasi mikro untuk lele, FCR aktual default 1.5)*

**Output kalkulasi:**
```
FCR Ideal     : 0.8–1.0 (tengah: 0.9)
Selisih FCR   : 0.6
Pemborosan    : 18.00 kg pakan/siklus
Kerugian      : Rp 180.000/siklus
Penghematan   : Rp 180.000/siklus (jika FCR → ideal)
Warning       : (kosong — data konsisten)
```

---

### Step 4 — Cek Warning

`warning` kosong → tidak ada flag. Lanjut ke Step 5 dengan angka Rp 180.000.

---

### Step 5 — Reply WA Final (Siap Kirim)

```
Halo, makasih udah download PDF-nya dan langsung coba praktek — 300 ekor di kolam
terpal 3×4 itu langkah yang bagus untuk mulai.

Dari yang Kakak ceritain, pola "pakan habis tapi ikan ga besar" itu biasanya sinyal
FCR yang tidak efisien — artinya pakan masuk tapi tidak terkonversi optimal jadi
daging ikan.

Untuk skala Kakak, kalau FCR bisa turun dari rata-rata ke angka ideal lele (0.8–1.0),
ada potensi hemat sekitar Rp 180.000 per siklus — kecil tapi ini baru dari 300 ekor,
kalau skala nanti naik angkanya ikut naik proporsional.

Biasanya penyebabnya bisa dari frekuensi pemberian pakan, ukuran pelet yang tidak
sesuai bukaan mulut, atau kualitas air yang bikin ikan stres dan nafsu makan turun.

Boleh cerita, sehari Kakak kasih pakan berapa kali, dan pelet yang dipakai ukuran
berapa?"
```

---

### Ringkasan Analisis Internal (Tidak Dikirim ke Leads)

```
Species       : Lele (Clarias sp.)
Skala         : Mikro
Masalah Utama : PERTUMBUHAN + PAKAN
Funnel Stage  : F2
FCR Aktual    : 1.5 (default — belum konfirmasi)
Kerugian/siklus: Rp 180.000
Warning       : Tidak ada
Eskalasi      : Tidak perlu (F2, skala Mikro)
Langkah Berikut: Tunggu jawaban pertanyaan terbuka → jalankan flow lagi dengan data lebih lengkap
```

---

## Referensi Komponen

| Komponen | File | Fungsi |
|----------|------|--------|
| SOP Intake Leads | `lead_intake.md` | Ekstraksi variabel + penentuan funnel stage |
| Kalkulasi FCR | `fcr_calculator.py` | Angka kerugian konkret + warning validasi |
| Eskalasi | `lead_intake.md` § Eskalasi ke Aditiya | Trigger: MENENGAH/BESAR, tanya harga, kematian >30% |
