# Direktif: Closing Offer PPBIB
## Dipanggil saat leads sudah reply dan mulai masuk ke zona keputusan

---

## Konteks & Trigger

Direktif ini aktif ketika leads memenuhi minimal satu kondisi berikut:
- Menyebut kata: "harga", "biaya", "berapa", "daftar", "ikut", "bayar", "program"
- Sudah mendapat reply edukasi FCR dari `leads_flow.md` dan follow-up dari `followup_sequence.md`
- Mulai mengajukan pertanyaan spesifik tentang cara kerja program atau apa yang didapat

**Sebelum masuk skenario:** pastikan data leads berikut sudah tersedia dari `lead_intake.md`:

| Data | Sumber | Wajib? |
|------|--------|--------|
| Species | lead_intake.md | ✓ |
| Skala | lead_intake.md | ✓ |
| Masalah utama | lead_intake.md | ✓ |
| Kerugian FCR (Rp) | fcr_calculator.py | ✓ |
| Funnel stage sebelumnya | lead_intake.md | ✓ |
| Sudah pernah pelatihan? | dari percakapan | ○ opsional |

---

## Produk PPBIB

| Produk | Format | Harga | Cocok untuk |
|--------|--------|-------|-------------|
| **Bundle Digital** | PDF + video mandiri | Rp 75.000–200.000 | MIKRO / KECIL / pemula yang butuh referensi dulu |
| **Online Bootcamp** | Multi-sesi live | — *(tanyakan ke Aditiya)* | KECIL / MENENGAH yang aktif tapi tidak bisa hadir fisik |
| **Offline Workshop** | Tatap muka + praktik | Rp 1.499.000 | KECIL / MENENGAH / BESAR yang butuh pendampingan langsung |

**Aturan match produk:**
- Jangan tawarkan semua produk sekaligus — pilih satu yang paling relevan
- Skala MIKRO + pemula → mulai dari Bundle Digital dulu
- Skala KECIL ke atas + ada masalah teknis konkret → Offline Workshop atau Online Bootcamp
- Leads yang tanya diskon → **jangan jawab angka**, eskalasi ke Aditiya

---

## Aturan Global

- **Selalu anchor ke angka FCR** — setiap framing harga harus disandingkan dengan kerugian FCR yang sudah dikalkulasi
- **Tidak boleh price drop** tanpa izin Aditiya — termasuk "nanti bisa dikurangi", "ada promo", "fleksibel kok"
- **Diskon:** catat permintaannya, balas dengan jembatan, eskalasi ke Aditiya
- **Output wajib:** analisis skenario (internal) + reply WA siap kirim (untuk leads)

---

## Skenario A — Leads Tanya Harga Langsung

### Kapan Aktif
Leads menyebut harga/biaya/berapa di pesan mereka, tapi belum ada cukup data untuk matching produk yang tepat.

### Prinsip
Jangan sebut harga dulu. Harga yang disebutkan sebelum konteks = angka kosong. Harga yang disebutkan setelah leads tahu kerugian FCR mereka = investasi yang masuk akal.

### Langkah

**1. Gali tiga hal sebelum sebut harga:**

| Pertanyaan Gali | Tujuan |
|-----------------|--------|
| Skala kolam saat ini atau yang direncanakan | Menentukan produk yang relevan |
| Masalah teknis yang paling dirasakan sekarang | Memastikan produk sesuai kebutuhan |
| Sudah pernah ikut pelatihan budidaya sebelumnya? | Hindari menawarkan level yang terlalu dasar/tinggi |

**2. Framing investasi vs kerugian FCR:**

Gunakan angka dari `fcr_calculator.py`. Struktur framing:
```
"Kerugian FCR leads saat ini = Rp [X]/siklus"
"Produk PPBIB = Rp [Y]"
"Break even = [X ÷ Y] siklus"
```

Jika break even ≤ 2 siklus → framing sangat kuat, sebut langsung.
Jika break even 3–5 siklus → framing masih solid, tambahkan angle akumulasi tahunan.
Jika break even > 5 siklus → tunda sebut harga, gali lebih dalam dulu atau pertimbangkan Bundle Digital sebagai entry point.

**3. Reply struktur:**
```
[Apresiasi pertanyaan leads — tanpa menghindari]
[1 pertanyaan gali skala/kondisi — framing sebagai "supaya saya rekomendasikan yang paling pas"]
[1 pertanyaan gali pengalaman sebelumnya]
[Jembatan: "begitu saya tahu kondisinya, saya bisa kasih gambaran lengkap termasuk hitungannya"]
```

---

### Contoh End-to-End Skenario A

**Input leads:**
> *"Kak berapa sih biaya pelatihannya? Saya tertarik mau ikut."*

**Analisis Internal:**
- Leads tanya harga langsung sebelum ada data skala/kondisi yang cukup
- Data sebelumnya: LELE, skala KECIL (1.000 ekor), kerugian FCR Rp 600.000/siklus
- Skenario A aktif — gali dulu sebelum sebut harga
- Setelah dapat data → kalkulasi break even: Offline Workshop Rp 1.499.000 ÷ Rp 600.000/siklus = 2,5 siklus (~5 bulan untuk lele)

**Reply WA:**
```
Wah senang Kakak tertarik — sebelum saya kasih gambaran lengkapnya, boleh
saya tanya dua hal dulu supaya saya bisa rekomendasikan yang paling sesuai?

Pertama, untuk 1.000 ekor lele yang direncanakan, kolamnya sudah jadi atau
masih tahap persiapan lahan?

Kedua, sebelumnya pernah ikut pelatihan atau kelas budidaya ikan sebelumnya,
atau ini benar-benar mulai dari nol?
```

---

## Skenario B — Leads Tertarik Tapi Ragu

### Kapan Aktif
Leads tidak menolak, tidak langsung setuju — ada sinyal ketertarikan tapi diikuti keraguan. Contoh: "kayaknya menarik tapi...", "saya pikir-pikir dulu", "nanti deh kak", "mahal ya".

### Identifikasi Sumber Keraguan

Baca pesan leads dan cocokkan ke empat tipe keraguan:

| Tipe | Sinyal dari Pesan | Cara Handle |
|------|-------------------|-------------|
| **HARGA** | "mahal", "belum ada budget", "nanti kalau ada uang" | Anchor ke kerugian FCR — bandingkan biaya program vs kerugian yang sedang berjalan tiap siklus |
| **WAKTU** | "lagi sibuk", "belum sempat", "nanti dulu" | Validasi, tunjukkan format fleksibel, sebut bahwa kerugian FCR berjalan tiap hari tanpa menunggu |
| **TRUST** | "yakin hasilnya?", "buktinya apa", "takut zonk" | Gunakan social proof dari `followup_sequence.md` Hari 3, tawarkan entry point rendah (Bundle Digital) |
| **HASIL** | "belum tentu cocok buat saya", "situasi saya beda" | Personalisasi — sebut kembali species, skala, dan masalah spesifik leads, jelaskan relevansi langsung |

### Aturan Handle

- **Satu keraguan per pesan** — jangan selesaikan semua keraguan sekaligus
- **Jangan defensive** — validasi dulu keraguan leads sebelum counter
- **Selalu kembali ke angka FCR** sebagai anchor netral, bukan sebagai tekanan

### Struktur Reply per Tipe:

**HARGA:**
```
[Validasi — "iya, investasi yang perlu dipertimbangkan"]
[Anchor FCR: "tapi kalau dihitung, tiap siklus leads sudah keluar Rp X lebih dari yang seharusnya"]
[Framing: "jadi bukan apakah mampu, tapi lebih ke kapan titik baliknya"]
[Buka opsi entry point lebih kecil jika relevan]
```

**WAKTU:**
```
[Validasi — "paham, timing memang penting"]
[Insight ringan: "yang menarik, masalah FCR ini terus jalan meski kita belum sempat ngurusnya"]
[Tunjukkan format yang fleksibel tanpa sebut nama produk spesifik dulu]
[Pertanyaan: "kira-kira dalam 1–2 bulan ke depan ada window waktu tidak?"]
```

**TRUST:**
```
[Validasi — "wajar kalau mau pastiin dulu"]
[Social proof singkat yang relevan dengan species leads]
[Tawarkan langkah kecil dulu: Bundle Digital sebagai "coba dulu"]
[Pertanyaan: "kalau ada materi yang bisa dicoba dulu dengan investasi kecil, itu membantu tidak?"]
```

**HASIL:**
```
[Validasi — "betul, setiap kondisi kolam memang beda"]
[Personalisasi: sebut kembali species + masalah spesifik leads]
[Tunjukkan bahwa rekomendasi akan disesuaikan, bukan template]
[Pertanyaan lanjut untuk menggali kekhawatiran spesifik]
```

---

### Contoh End-to-End Skenario B

**Input leads:**
> *"Menarik sih kak, tapi Rp 1.499.000 itu lumayan juga buat saya yang baru mau mulai."*

**Analisis Internal:**
- Tipe keraguan: HARGA
- Data: LELE, KECIL (1.000 ekor), kerugian FCR Rp 600.000/siklus
- Break even Offline Workshop: Rp 1.499.000 ÷ Rp 600.000 = 2,5 siklus ≈ 5 bulan
- Opsi entry point alternatif: Bundle Digital Rp 75.000–200.000 sebagai jembatan

**Reply WA:**
```
Iya, Rp 1.499.000 itu angka yang wajar untuk dipertimbangkan, apalagi kalau
baru mulai.

Tapi kalau boleh saya kasih perspektif lain — dari kalkulasi yang kita bahas
sebelumnya, dengan FCR yang belum optimal di 1.000 ekor lele, ada sekitar
Rp 600.000 yang keluar sia-sia tiap siklus panen.

Artinya dalam 2–3 siklus, biaya program itu sudah balik — sisanya murni
penghematan yang terus berjalan.

Kalau mau mulai lebih kecil dulu sambil lihat hasilnya, ada opsi lain yang
harganya jauh di bawah itu — boleh saya jelaskan?
```

---

## Skenario C — Leads Siap, Tanya Cara Daftar

### Kapan Aktif
Leads secara eksplisit menyatakan kesiapan: "mau daftar", "gimana caranya", "transfer ke mana", "kapan mulainya", "saya mau ikut".

### Langkah

**1. Konfirmasi profil leads sebelum berikan info:**

Cek apakah data berikut sudah lengkap:
- Species ✓ / ✗
- Skala ✓ / ✗
- Masalah utama ✓ / ✗

Jika ada yang kosong → isi dulu dengan satu pertanyaan singkat sebelum lanjut.

**2. Match produk ke profil:**

| Profil Leads | Produk yang Direkomendasikan |
|--------------|------------------------------|
| MIKRO + pemula + modal terbatas | Bundle Digital (entry point) |
| MIKRO/KECIL + pemula + mau belajar mandiri | Bundle Digital atau Online Bootcamp |
| KECIL + ada masalah teknis konkret + bisa hadir fisik | Offline Workshop |
| KECIL/MENENGAH + tidak bisa hadir fisik + aktif | Online Bootcamp |
| MENENGAH/BESAR | Eskalasi ke Aditiya sebelum offer apapun |

**3. CTA — satu langkah konkret, bukan banyak pilihan:**

Jangan tawarkan semua produk sekaligus. Berikan satu rekomendasi dengan reasoning singkat, lalu satu langkah konkret berikutnya.

**Struktur reply:**
```
[Konfirmasi kesiapan leads — hangat, tidak berlebihan]
[Rekomendasi satu produk + reasoning singkat berdasarkan profil leads]
[Detail singkat: apa yang didapat / format / kapan bisa mulai]
[Satu CTA konkret: "kalau mau lanjut, [langkah X]"]
```

---

### Contoh End-to-End Skenario C

**Input leads:**
> *"Oke kak saya mau daftar aja. Gimana caranya?"*

**Analisis Internal:**
- Skenario C aktif
- Data: LELE, KECIL (1.000 ekor), pemula, masalah PAKAN + FCR
- Profil: KECIL + pemula + ada masalah teknis konkret → Offline Workshop paling relevan
- Tidak ada permintaan diskon → lanjut normal, tidak perlu eskalasi

**Reply WA:**
```
Mantap Kak — keputusan yang tepat, apalagi sebelum siklus pertama dimulai.

Berdasarkan rencana 1.000 ekor lele dan masalah yang kita bahas soal FCR
dan formulasi pakan, saya rekomendasikan Offline Workshop PPBIB — formatnya
tatap muka langsung plus sesi praktik, jadi Kakak bisa langsung terapkan
setelah selesai.

Investasinya Rp 1.499.000 dan mencakup materi formulasi pakan, manajemen
kolam, sampai kalkulasi biaya produksi yang bisa langsung dipakai.

Untuk lanjut, saya akan sambungkan Kakak ke tim kami — boleh saya minta
nama lengkap dan lokasi Kakak dulu?
```

---

### Contoh Skenario C — Leads Minta Diskon

**Input leads:**
> *"Bisa diskon tidak kak? Budget saya cuma sampai Rp 1.200.000."*

**Analisis Internal:**
- Permintaan diskon → tidak boleh jawab angka
- Catat: leads minta turun ke Rp 1.200.000 (selisih Rp 299.000 dari harga Offline Workshop)
- Tindakan: jembatan dulu, eskalasi ke Aditiya
- Opsi alternatif yang bisa disebutkan: Bundle Digital sebagai entry point sah

**Reply WA:**
```
Noted Kak, saya catat dulu ya.

Untuk soal harga program saya perlu cek dulu ke tim — saya tidak bisa
konfirmasi sendiri karena setiap keputusan itu ada prosesnya.

Sementara itu, ada juga opsi lain yang harganya jauh di bawah itu dan
bisa jadi langkah pertama yang solid — boleh saya jelaskan dulu
sambil saya cek ke tim?
```

*(Internal: eskalasi ke Aditiya — leads: [nama/nomor], species: LELE, skala: KECIL, minta diskon ke Rp 1.200.000 dari Offline Workshop Rp 1.499.000)*

---

## Ringkasan Decision Tree

```
Leads masuk zona keputusan
        │
        ├── Tanya harga langsung ──────────────→ SKENARIO A
        │   (belum ada konteks cukup)              Gali dulu → framing FCR → sebut harga
        │
        ├── Tertarik tapi ragu ────────────────→ SKENARIO B
        │   ("tapi...", "pikir-pikir", "mahal")    Identifikasi tipe → handle spesifik
        │
        └── Siap, tanya cara daftar ──────────→ SKENARIO C
            ("mau daftar", "gimana caranya")       Match produk → 1 CTA konkret
                    │
                    └── Minta diskon ────────────→ Jembatan + Eskalasi ke Aditiya
```

---

## Referensi Komponen

| Komponen | File | Kapan Digunakan |
|----------|------|-----------------|
| Data profil leads | `lead_intake.md` | Sebelum masuk skenario apapun |
| Angka kerugian FCR | `fcr_calculator.py` | Anchor di semua skenario |
| Social proof | `followup_sequence.md` Hari 3 | Skenario B tipe TRUST |
| Eskalasi | `lead_intake.md` § Eskalasi ke Aditiya | Skenario C diskon + skala MENENGAH/BESAR |
