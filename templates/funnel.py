"""
Template pesan sales funnel PPBIB.
Sesuaikan teks sesuai kebutuhan.
"""

KEYWORDS_MINAT = [
    "info", "daftar", "harga", "berapa", "gimana", "cara", "mau", "ikut",
    "join", "bisa", "pelatihan", "ppbib", "kursus", "belajar", "biaya",
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
