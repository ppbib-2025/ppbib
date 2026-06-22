"""
Template pesan sales funnel PPBIB — Pelatihan Budidaya Koki.
"""

# Keyword umum ketertarikan
KEYWORDS_MINAT = [
    "info", "daftar", "harga", "berapa", "gimana", "cara", "mau", "ikut",
    "join", "bisa", "pelatihan", "ppbib", "kursus", "belajar", "biaya",
]

# Keyword spesifik koki — trigger prioritas tinggi
KEYWORDS_KOKI = [
    "koki", "ikan koki", "goldfish", "fancy", "indukan", "benih", "spawning",
    "pijah", "pemijahan", "breeding", "budidaya", "ternak koki", "anakan",
    "larva", "survival", "fcr", "kolam koki",
]


def is_interested(comment_text: str) -> bool:
    text = comment_text.lower()
    return any(kw in text for kw in KEYWORDS_MINAT + KEYWORDS_KOKI)


def is_koki_specific(comment_text: str) -> bool:
    """True jika komentar menyebut topik koki secara eksplisit."""
    text = comment_text.lower()
    return any(kw in text for kw in KEYWORDS_KOKI)


def reply_komentar(username: str, is_koki: bool = False) -> str:
    if is_koki:
        return (
            f"Halo @{username}! Sip, kamu di tempat yang tepat 🐟 "
            "Kami PPBIB Cijeruk — pusat riset koki resmi pemerintah. "
            "Cek DM ya, kami kirimkan info pelatihan breeding koki lengkap! 🎯"
        )
    return (
        f"Halo @{username}! Terima kasih sudah tertarik 😊 "
        "Untuk info lengkap pelatihan PPBIB, silakan cek DM ya — "
        "kami sudah kirimkan detailnya untuk kamu! 🎯"
    )


def pesan_dm_awal(username: str) -> str:
    return f"""Halo {username}! 👋

Terima kasih sudah tertarik dengan konten koki kami.

Kami tim PPBIB Cijeruk — lembaga riset perikanan resmi di bawah KKP/BRPBATPP, dan kami membuka *Pelatihan Budidaya Koki* untuk hobbyist & calon peternak serius.

🐟 *Yang akan kamu bawa pulang:*
✅ Cara seleksi indukan koki yang benar (bukan coba-coba)
✅ Sistem pemijahan & manajemen benih — survival rate >70%
✅ FCR koki: cara hitung & hemat biaya pakan
✅ Strategi jual koki ke komunitas hobbyist

🎁 *Bonus untuk peserta:*
→ 1 pasang indukan koki koleksi PPBIB (strain pilihan)
→ Program tampung benih 3 bulan di fasilitas kami
→ Modul digital + grup WA alumni 60 hari

📍 Lokasi: PPBIB Cijeruk, Bogor (fasilitas kolam lengkap)
🗓️ Format: 1 hari penuh, praktik langsung

Boleh tahu — kamu lebih tertarik untuk *hobi yang lebih serius*, atau sudah punya rencana *jual benih/ikan jadi*?

Biar kami bisa kasih rekomendasi yang paling pas 🙏"""


def pesan_dm_webinar(username: str, link_webinar: str, tanggal: str) -> str:
    """DM untuk lead yang masuk dari promosi webinar."""
    return f"""Halo {username}! 🎓

Terima kasih sudah daftar webinar *"Sistem Breeding Koki Sendiri di Rumah"* bersama PPBIB!

📅 Tanggal: {tanggal}
🔗 Link Zoom: {link_webinar}

Yang akan kamu pelajari dalam 3 jam:
• Kenapa hobbyist koki terus beli, bukan produksi
• Sistem breeding praktis dari nol
• Cara jual ke komunitas hobbyist (FB Group, WA, marketplace)

*Tips:* Siapkan pertanyaan spesifik tentang kendala breeding kamu — sesi Q&A akan fokus ke solusi praktis.

Sampai jumpa di webinar! 🐟"""


def followup_d1(username: str) -> str:
    return f"""Halo {username}! 😊

Kami dari PPBIB mau follow up sebentar.

Sudah sempat baca info pelatihan koki yang kami kirimkan kemarin?

Kalau ada pertanyaan soal materi, bonus indukan, atau teknis pendaftaran — langsung tanya ya, kami siap jawab!

Atau kalau lebih nyaman ngobrol langsung, balas pesan ini dan kami akan atur waktu konsultasi singkat 🙏"""


def followup_d3(username: str, wa_number: str) -> str:
    return f"""Halo {username}!

PPBIB kembali menyapa 🙏

Sekedar info — slot pelatihan koki batch ini *hampir penuh*. Kami batasi maks 10 peserta agar praktik bisa optimal dan semua mendapat perhatian langsung dari instruktur.

Yang sudah konfirmasi akan dapat:
🎁 Indukan koki PPBIB (1 pasang) — senilai Rp 750rb–1,5jt
🐟 Program tampung benih 3 bulan di fasilitas kami

Kalau kamu serius, langsung chat kami via WhatsApp sekarang:
👉 wa.me/{wa_number}

Kami bantu proses pendaftaran dalam 5 menit ✨"""


def followup_d7(username: str, wa_number: str) -> str:
    return f"""Halo {username}!

Ini pesan terakhir dari kami 😊

Batch pelatihan koki PPBIB bulan ini *segera tutup pendaftaran*.

Setelah batch ini penuh, batch berikutnya belum tentu ada bonus indukan — karena stok terbatas dari koleksi PPBIB.

Kalau kamu tidak ingin melewatkan kesempatan ini:
👉 wa.me/{wa_number}

Atau cukup balas "DAFTAR" di sini dan kami proses segera.

Kalau memang belum waktunya, tidak apa-apa — kami tetap simpan kontakmu untuk batch berikutnya 🙏"""
