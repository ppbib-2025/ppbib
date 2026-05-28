# Direktif: Follow-up Sequence PPBIB — 7 Hari Tanpa Reply

## Konteks

Digunakan ketika leads sudah menerima reply WA pertama dari `leads_flow.md` tetapi tidak membalas dalam 24 jam atau lebih. Sequence ini menjaga koneksi tanpa menekan, sambil terus memberikan nilai nyata.

---

## Aturan Global

| Aturan | Detail |
|--------|--------|
| Panjang pesan | Maksimal 4 kalimat per pesan |
| Harga | Tidak boleh disebut di seluruh sequence ini |
| Batas pengiriman | Maksimal 3 pesan jika tidak ada reply sama sekali |
| Leads reply | Stop sequence seketika — balik ke `leads_flow.md` dari titik leads terakhir |
| Nada umum | Tidak menagih, tidak mengingatkan "sudah baca belum", tidak minta maaf berulang |
| Personalisasi | Sesuaikan species dan masalah utama dari data `lead_intake.md` sebelumnya |

---

## Struktur Sequence

```
Hari 0   → Reply WA pertama dikirim (leads_flow.md)
Hari 1   → [PESAN 1] Soft ping — tambah value
Hari 3   → [PESAN 2] Social proof — cerita peternak relevan
Hari 7   → [PESAN 3] Soft exit — tutup loop, buka pintu
Hari 8+  → Tidak ada pesan lagi. Leads diarsip sebagai "cold lead".
```

---

## Hari 1 — Soft Ping

**Trigger:** 24 jam setelah reply pertama, belum ada balasan.

**Prinsip:**
- Tambah satu informasi baru yang langsung relevan dengan species/masalah leads
- Jangan tanya "sudah baca belum" atau "gimana kabar rencana ternaknya"
- Tone seperti teman yang ingat sesuatu dan mau berbagi

**Template:**
```
[Sapaan singkat tanpa basa-basi panjang]
[1 fakta/tips baru yang relevan dengan species + masalah leads]
[Kenapa ini penting untuk kondisi spesifik leads]
[Kalimat ringan yang membuka ruang untuk balas — bukan pertanyaan langsung]
```

---

### Pesan Hari 1 — LELE

> Kak, satu hal yang sering bikin FCR lele melonjak di awal budidaya itu bukan pakan — tapi ukuran kolam terpal yang tidak sesuai rasio kepadatan.
> Untuk 1.000 ekor, kepadatan ideal di kolam terpal sekitar 100–150 ekor/m², jadi butuh minimal 7–10 m².
> Kalau terlalu padat, lele stres, nafsu makan turun, dan pakan yang masuk tidak terserap optimal meski kualitasnya bagus.
> Kalau Kakak mau, bisa share ukuran terpal yang sudah disiapkan — saya bisa bantu hitung apakah sudah pas.

---

### Pesan Hari 1 — NILA

> Kak, untuk nila di kolam terpal atau beton, satu faktor yang sering diabaikan pemula adalah aerasi — terutama di siang hari saat suhu air naik.
> Nila mulai stres dan berhenti makan efisien di atas 32°C, dan ini langsung naikkan FCR meski pakannya sudah bagus.
> Di skala 1.000 ekor ke atas, satu aerator kecil saja bisa cukup untuk menjaga DO dan efisiensi pakan tetap stabil.
> Kalau Kakak mau cerita kondisi kolamnya lebih detail, saya bisa bantu rekomendasikan setup yang paling efisien.

---

### Pesan Hari 1 — GURAME

> Kak, gurame itu salah satu species yang paling diuntungkan dari pakan mandiri dibanding beli komersial — karena kebutuhan protein hariannya lebih rendah dari lele atau nila.
> Protein 25–28% sudah cukup untuk gurame tumbuh optimal, sementara pakan komersial biasanya 30–32% dan harganya jauh lebih mahal.
> Artinya formulasi pakan sendiri untuk gurame itu lebih mudah dan lebih murah dibanding species lain.
> Kalau Kakak mau tahu bahan baku lokal apa yang bisa dipakai, saya siap bantu hitung komposisinya.

---

## Hari 3 — Social Proof

**Trigger:** 72 jam setelah reply pertama, masih belum ada balasan.

**Prinsip:**
- Ceritakan hasil nyata peternak lain yang situasinya mirip dengan leads
- Spesifik: sebutkan species, skala, dan angka yang berubah
- Jangan terdengar seperti testimoni iklan — cerita harus terasa natural dan manusiawi
- Tidak menyebut nama program atau harga

**Template:**
```
[Pembuka kasual — "ada yang menarik" / "baru ngobrol sama..."]
[Cerita singkat peternak lain: species sama, masalah mirip, hasil konkret]
[Angka spesifik: FCR sebelum vs sesudah, atau penghematan Rp]
[Kalimat yang menghubungkan cerita itu dengan situasi leads — tanpa tekanan]
```

---

### Pesan Hari 3 — LELE

> Kak, minggu lalu sempat ngobrol sama peternak lele di Jawa Tengah yang awalnya juga pakai pakan murah untuk 800 ekor di kolam terpal.
> FCR-nya waktu itu di angka 1,7 — habis pakan cepat tapi ikan tumbuh lambat, persis seperti yang sering terjadi di awal.
> Setelah ganti ke formulasi yang proteinnya lebih pas (bukan yang paling mahal), FCR turun ke 1,0 dalam dua siklus — dan biaya pakan per siklus justru lebih hemat Rp 400.000–500.000.
> Kondisi Kakak yang 1.000 ekor punya potensi penghematan yang lebih besar lagi — kalau mau kita hitung bareng, tinggal kabarin saja.

---

### Pesan Hari 3 — NILA

> Kak, ada cerita menarik dari peternak nila di Sumatera Selatan yang baru mulai tahun lalu dengan 1.500 ekor di kolam beton.
> Awalnya dia frustrasi karena FCR-nya 1,9 padahal sudah pakai pakan yang katanya "bagus" — ternyata masalahnya di frekuensi pemberian pakan, bukan kualitas pakan.
> Setelah ubah dari 2× sehari jadi 3× sehari dengan porsi lebih kecil, FCR turun ke 1,4 dan berat panen naik rata-rata 20 gram per ekor.
> Perubahan seperti itu tidak butuh modal tambahan — dan untuk skala Kakak itu dampaknya bisa cukup signifikan.

---

### Pesan Hari 3 — GURAME

> Kak, baru ngobrol sama peternak gurame di Jawa Barat yang sudah 3 tahun budidaya skala rumahan, sekitar 500–800 ekor per siklus.
> Dulu dia bilang gurame "susah dan lama" karena siklus panennya 8–10 bulan, tapi sekarang justru itu yang dia jadikan keunggulan — dia jual ke restoran Sunda langsung, harga per kg Rp 35.000–40.000, jauh di atas harga pasar.
> Kuncinya menurut dia ada di konsistensi pakan dan kualitas air, bukan di percepatan siklus.
> Kalau Kakak ada rencana ke arah yang sama, saya bisa bantu petakan dari sisi pakan dan manajemen kolamnya dulu.

---

## Hari 7 — Soft Exit

**Trigger:** 7 hari setelah reply pertama, tidak ada balasan sama sekali.

**Prinsip:**
- Tutup loop dengan elegan — bukan menghilang begitu saja, tapi juga tidak memaksa
- Validasi bahwa leads mungkin sedang sibuk atau belum siap — dan itu tidak masalah
- Buka pintu dengan jelas: kapanpun siap, kontak lagi, tidak perlu mulai dari nol
- Pesan ini adalah pesan terakhir — setelah ini tidak ada follow-up lagi

**Template:**
```
[Pengakuan bahwa leads mungkin sedang sibuk / belum siap — tanpa menghakimi]
[Ringkasan satu kalimat tentang apa yang bisa PPBIB bantu — sebagai pengingat]
[Pernyataan bahwa pintu tetap terbuka kapanpun]
[Penutup hangat yang tidak meminta apapun]
```

---

### Pesan Hari 7 — LELE

> Kak, saya paham mungkin lagi banyak hal yang harus diselesaikan dulu sebelum mulai proyek ternaknya.
> Kalau nanti sudah siap — mau itu soal formulasi pakan, setup kolam terpal, atau hitung estimasi biaya per siklus — langsung kabarin saja, tidak perlu cerita dari awal lagi.
> Saya simpan konteks rencana Kakak yang 1.000 ekor lele itu.
> Semoga lancar semua urusannya, Kak — sukses selalu.

---

### Pesan Hari 7 — NILA

> Kak, mungkin timing-nya memang belum pas sekarang, dan itu tidak masalah sama sekali.
> Kalau nanti ada pertanyaan soal budidaya nila — dari hal teknis sekecil apapun sampai ke rencana yang lebih besar — pintu tetap terbuka.
> Tidak perlu mulai dari awal, konteks rencana Kakak sudah saya catat.
> Semoga sehat selalu dan sukses dengan apapun yang sedang dikerjakan sekarang.

---

### Pesan Hari 7 — GURAME

> Kak, budidaya gurame memang butuh persiapan yang lebih matang dibanding species lain — jadi wajar kalau masih perlu waktu untuk memutuskan.
> Kapanpun Kakak siap — entah itu 2 minggu lagi atau 6 bulan lagi — langsung chat saja dan kita lanjut dari titik yang sudah dibahas.
> Tidak ada tenggat waktu di sini.
> Semoga rencana ternaknya terwujud, Kak — saya tunggu kabar baiknya.

---

## Decision Tree Sequence

```
Reply WA Pertama Terkirim
        │
        ├── Leads reply < 24 jam ──────────────────→ Balik ke leads_flow.md
        │
        ├── 24 jam tidak reply
        │       │
        │       └── Kirim Pesan Hari 1
        │               │
        │               ├── Leads reply ───────────→ Balik ke leads_flow.md
        │               │
        │               └── 48 jam tidak reply
        │                       │
        │                       └── Kirim Pesan Hari 3
        │                               │
        │                               ├── Leads reply ──→ Balik ke leads_flow.md
        │                               │
        │                               └── 4 hari tidak reply
        │                                       │
        │                                       └── Kirim Pesan Hari 7
        │                                               │
        │                                               ├── Leads reply ──→ Balik ke leads_flow.md
        │                                               │
        │                                               └── Tidak reply ──→ Arsip sebagai cold lead
        │                                                                    Tidak ada pesan lagi.
```

---

## Referensi Komponen

| Komponen | File | Kapan Digunakan |
|----------|------|-----------------|
| Reply pertama | `leads_flow.md` | Hari 0 — trigger awal sequence |
| Data leads | `lead_intake.md` | Untuk personalisasi species + masalah di setiap pesan |
| Kalkulasi angka | `fcr_calculator.py` | Opsional di Hari 1 jika ingin tambahkan angka Rp baru |
| Eskalasi | `lead_intake.md` § Eskalasi ke Aditiya | Jika leads reply di Hari 3/7 dengan sinyal skala besar atau tanya harga |
