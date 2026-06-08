"""
Template pesan sales funnel PPBIB.
Sesuaikan teks sesuai kebutuhan.
"""

KEYWORDS_MINAT = [
    "info", "daftar", "harga", "berapa", "gimana", "cara", "mau", "ikut",
    "join", "bisa", "pelatihan", "ppbib", "kursus", "belajar", "biaya",
    "minat", "tertarik", "pengen", "pengin", "nanya", "tanya", "kapan",
    "dimana", "online", "offline", "sertifikat", "bonus", "hemat", "pakan",
]


def is_interested(comment_text: str) -> bool:
    text = comment_text.lower()
    return any(kw in text for kw in KEYWORDS_MINAT)


def reply_komentar(username: str) -> str:
    return (
        f"Halo @{username}! Terima kasih sudah tertarik 😊 "
        "Untuk info lengkap pelatihan PPBIB, silakan cek DM ya — "
        "kami sudah kirimkan detailnya untuk kamu! 🎯"
    )


def pesan_dm_awal(username: str) -> str:
    return f"""Halo {username}! 👋

Terima kasih sudah komentar di konten kami.

Kami dari tim PPBIB ingin berbagi info pelatihan eksklusif yang bisa membantu kamu:

✅ Pelatihan profesional bersertifikat
✅ Mentor berpengalaman di bidangnya
✅ Kuota terbatas setiap batch

Boleh kami tahu, apa yang paling ingin kamu pelajari atau capai dari pelatihan ini?

Kami siap bantu carikan program yang paling sesuai untuk kamu 🙏"""


def followup_d1(username: str) -> str:
    return f"""Halo {username}! 😊

Kami dari PPBIB mau follow up sebentar.

Apakah kamu sudah sempat lihat info pelatihan yang kami kirimkan kemarin?

Jika ada pertanyaan, kami siap bantu jawab ya!
Atau jika mau langsung konsultasi via WhatsApp, bisa hubungi kami di sini 👇"""


def followup_d3(username: str, wa_number: str) -> str:
    return f"""Halo {username}!

Kami PPBIB kembali menyapa 🙏

Kuota batch berikutnya sudah hampir penuh!

Jika kamu masih tertarik dan ingin info lebih detail, langsung chat kami via WhatsApp:
👉 wa.me/{wa_number}

Kami akan bantu proses pendaftaran kamu dengan mudah dan cepat ✨"""


def followup_d7(username: str, wa_number: str) -> str:
    return f"""Halo {username}!

Ini pesan terakhir dari kami 😊

Kami ingin memastikan kamu tidak melewatkan kesempatan bergabung di pelatihan PPBIB.

🎁 Khusus yang daftar minggu ini: ada bonus materi eksklusif!

Daftar sekarang via WhatsApp:
👉 wa.me/{wa_number}

Atau balas pesan ini jika ada yang ingin ditanyakan 🙏"""


# ── Template Onboarding (pasca pembayaran) ────────────────────────────────────

def materi_hari1(username: str) -> str:
    return f"""Selamat datang di PPBIB, {username}! 🎉

Pembayaran kamu sudah kami terima. Yuk kita mulai perjalanan belajarnya!

📚 *MATERI HARI 1 — Pengenalan Budidaya Ayam Buras*

1️⃣ Memahami karakteristik ayam buras vs broiler
2️⃣ Persiapan kandang yang benar (ventilasi, alas, kepadatan)
3️⃣ Pemilihan bibit DOC berkualitas

📌 Tips hari ini:
Kandang yang baik bisa menekan angka kematian DOC hingga 80%. Prioritaskan sirkulasi udara sebelum yang lain.

Simpan nomor ini ya — besok lusa kami kirim materi lanjutan 💪

Ada pertanyaan? Langsung balas pesan ini!"""


def materi_hari3(username: str) -> str:
    return f"""Halo {username}! Hari ke-3 sudah tiba 🌱

📚 *MATERI HARI 3 — Formulasi Pakan Sendiri*

Ini bagian favorit banyak peserta karena langsung menghemat biaya!

1️⃣ Bahan baku lokal yang murah dan bergizi (jagung, dedak, bungkil kelapa)
2️⃣ Cara hitung kebutuhan protein per fase (starter, grower, finisher)
3️⃣ Contoh formula pakan sederhana dengan bahan lokal

💡 Contoh penghematan nyata:
Pakan pabrikan: Rp 8.000/kg
Pakan racikan sendiri: Rp 4.500–5.500/kg
*Hemat 30–40% biaya operasional per bulan!*

Coba hitung untuk skala kandang kamu sendiri, lalu share hasilnya ke kami 😊

Materi penutup akan kami kirim dalam 4 hari lagi!"""


def materi_hari7(username: str) -> str:
    return f"""Halo {username}! Ini materi terakhir dari batch ini 🏆

📚 *MATERI HARI 7 — Manajemen Produksi & Pemasaran*

1️⃣ Pencatatan sederhana: FCR, mortalitas, dan break-even point
2️⃣ Strategi jual: pasar tradisional vs. konsumen langsung vs. restoran
3️⃣ Cara scale-up dari 100 ekor ke 500–1000 ekor

🎁 *Bonus Eksklusif:*
- Template spreadsheet perhitungan biaya pakan (langsung pakai)
- Grup alumni PPBIB untuk sharing pengalaman

Kamu sudah resmi lulus pelatihan dasar PPBIB! 🎓

Sertifikat akan dikirim dalam 3–5 hari kerja ke email/WA kamu.

Terima kasih sudah belajar bersama kami. Sukses selalu! 🙏"""


def pesan_upsell_alumni(username: str) -> str:
    return f"""Halo {username}! Apa kabar? 😊

Sudah sebulan lebih sejak kamu menyelesaikan pelatihan dasar PPBIB.

Bagaimana perkembangan usaha budidayamu? Kami harap sudah mulai terasa manfaatnya!

🚀 *Kabar baik untuk kamu:*

Kami buka *Batch Lanjutan PPBIB — Level Intermediate* yang membahas:

✅ Manajemen kesehatan ternak & vaksinasi mandiri
✅ Optimasi produksi skala 500–5000 ekor
✅ Pengolahan hasil panen menjadi produk bernilai tambah
✅ Strategi ekspansi ke pasar modern (supermarket, horeka)

Khusus alumni, ada *diskon 25%* untuk batch ini 🎁

Slot terbatas. Balas pesan ini dengan kata *LANJUT* untuk reservasi tempat!"""
