"""
Jadwal konten harian tetap (18 Jun – 4 Jul 2026).
Dipakai oleh job_daily_content_reminder di main.py sebagai prioritas utama.
"""
from datetime import datetime

CONTENT_PLAN = [
    {
        "tanggal": "2026-06-18",
        "label": "Hari 0 — Re-Entry",
        "format": "Reels/TikTok",
        "hook": "Saya hilang 3 minggu. Ini alasannya.",
        "tujuan": "Bangkitkan algoritma + tease seri baru",
        "cta_trigger": "FOLLOW",
        "footage_hint": "BTS lapangan / fasilitas PPBIB",
        "reminder": "RE-ENTRY POST — Jangan skip ini. Algoritma butuh sinyal dulu sebelum seri dimulai.",
        "checklist": [
            "Record video BTS lapangan/fasilitas PPBIB",
            "Edit 25–35 detik",
            "Text overlay: 'Follow sekarang — episode #1 besok'",
            "Post jam 05.30–07.00",
        ],
    },
    {
        "tanggal": "2026-06-19",
        "label": "Hari 15 — Seri Kesalahan Mahal #1",
        "format": "Reels/TikTok",
        "hook": "Seri Kesalahan Mahal #1 — Salah hitung FCR",
        "tujuan": "Edukasi cara hitung FCR yang benar vs salah",
        "cta_trigger": "FORMULA",
        "footage_hint": "Teks visual angka besar + close up kolam",
        "reminder": "SERI MULAI — Ini episode pertama. Kualitas dan kejelasan angka sangat penting.",
        "checklist": [
            "Siapkan teks visual: perbandingan rumus FCR",
            "Sertakan contoh angka: 1.000 ÷ 800 vs 1.000 ÷ 700",
            "Edit 45–55 detik",
            "Post jam 05.30–07.00",
            "Story reminder jam 11.30: 'Episode #1 sudah tayang'",
        ],
    },
    {
        "tanggal": "2026-06-20",
        "label": "Hari 16 — Seri Kesalahan Mahal #2",
        "format": "Reels/TikTok",
        "hook": "Seri Kesalahan Mahal #2 — Ukuran pellet salah, ikan stres makan",
        "tujuan": "Edukasi kesesuaian ukuran pellet per fase ikan",
        "cta_trigger": "FORMULA",
        "footage_hint": "Close up ikan makan vs ukuran pelet",
        "reminder": "HARI 2 SERI — Cek engagement episode #1. Balas komentar untuk boost algoritma.",
        "checklist": [
            "Siapkan footage: close up ikan makan",
            "Tampilkan tabel ukuran pellet (lele per fase)",
            "Edit 40–50 detik",
            "Post jam 05.30–07.00",
            "Reply komentar episode #1 hari ini",
        ],
    },
    {
        "tanggal": "2026-06-21",
        "label": "Hari 17 — Seri Kesalahan Mahal #3",
        "format": "Reels/TikTok",
        "hook": "Seri Kesalahan Mahal #3 — Overfeeding yang kamu kira aman",
        "tujuan": "Edukasi feeding rate berbasis biomassa",
        "cta_trigger": "SISTEM",
        "footage_hint": "Footage pemberian pakan di kolam",
        "reminder": "HARI 3 SERI — Topik paling banyak yang salah. Ini bisa viral kalau eksekusinya tajam.",
        "checklist": [
            "Footage: pemberian pakan di kolam (tampak berlebih)",
            "Tampilkan rumus: Biomassa × 4% = pakan harian",
            "Edit 45–55 detik",
            "Post jam 05.30–07.00",
        ],
    },
    {
        "tanggal": "2026-06-22",
        "label": "Hari 18 — Seri Kesalahan Mahal #4",
        "format": "Reels/TikTok",
        "hook": "Seri Kesalahan Mahal #4 — Protein 32% tapi FCR malah tinggi",
        "tujuan": "Bongkar mitos protein tinggi = FCR bagus",
        "cta_trigger": "FORMULA",
        "footage_hint": "Teks angka besar + visual pelet close up",
        "reminder": "HARI 4 SERI — Kontra-intuitif = engagement tinggi. Pastikan angkanya jelas.",
        "checklist": [
            "Teks visual: protein 32% vs 28-30% + konteks energi",
            "Buat text overlay yang tajam per segmen",
            "Edit 45–55 detik",
            "Post jam 05.30–07.00",
        ],
    },
    {
        "tanggal": "2026-06-23",
        "label": "Hari 19 — Seri Kesalahan Mahal #5",
        "format": "Reels/TikTok",
        "hook": "Seri Kesalahan Mahal #5 — Air bagus, pakan cukup, tapi growth jelek",
        "tujuan": "Ungkap 3 faktor tersembunyi: DO, kepadatan, stres",
        "cta_trigger": "SISTEM",
        "footage_hint": "Footage kualitas air kolam — aerator aktif",
        "reminder": "HARI 5 SERI — Episode terakhir. Tease rekap besok di Stories untuk jaga engagement.",
        "checklist": [
            "Footage: kolam dengan aerator aktif + close up ikan",
            "3 poin harus jelas di teks layar",
            "Edit 50–60 detik",
            "Post jam 05.30–07.00",
            "Tease carousel rekap di Stories hari ini",
        ],
    },
    {
        "tanggal": "2026-06-24",
        "label": "Hari 20 — Rekap 5 Kesalahan Mahal",
        "format": "Carousel",
        "hook": "Rekap 5 Kesalahan Mahal — mana yang paling sering kamu buat?",
        "tujuan": "Konsolidasi seri, dorong save & komentar",
        "cta_trigger": "SISTEM",
        "footage_hint": "Visual infografis simpel — background gelap",
        "reminder": "CAROUSEL HARI INI — Konten ini yang paling banyak di-save. Desain harus bersih dan mudah dibaca.",
        "checklist": [
            "Desain 8 slide (Canva/template gelap)",
            "Slide 7 ada self-check checklist interaktif",
            "Slide 8 CTA: DM SISTEM",
            "Caption: minta komentar nomor kesalahan",
            "Post jam 07.00–09.00 (carousel performa bagus pagi)",
        ],
    },
    {
        "tanggal": "2026-06-25",
        "label": "Hari 21 — Mesin Pelet",
        "format": "Reels/TikTok",
        "hook": "Jangan beli mesin pelet sebelum tahu satu hal ini.",
        "tujuan": "Edukasi kriteria mesin + bridge ke pelatihan",
        "cta_trigger": "PELATIHAN",
        "footage_hint": "Footage mesin produksi pakan di fasilitas PPBIB",
        "reminder": "PIVOT KE CONVERSION — Mulai hari ini CTA berubah ke PELATIHAN. Pastikan footage fasilitas representatif.",
        "checklist": [
            "Footage mesin produksi pakan di fasilitas PPBIB",
            "3 kriteria tampil jelas di teks layar",
            "Edit 50–60 detik",
            "Post jam 05.30–07.00",
            "Ini transisi ke Conversion Week — pastikan CTA PELATIHAN jelas",
        ],
    },
    {
        "tanggal": "2026-06-26",
        "label": "Hari 22 — Trial vs Pelatihan (Angka)",
        "format": "Reels/TikTok",
        "hook": "Trial & error di budidaya punya harga yang tidak kecil — ini hitungannya.",
        "tujuan": "Kalkulasi ROI pelatihan vs kerugian trial-error",
        "cta_trigger": "PELATIHAN",
        "footage_hint": "Teks angka besar, background gelap",
        "reminder": "CONVERSION WEEK DIMULAI — Konten ini adalah pintu masuk closing. Angka harus jelas dan meyakinkan.",
        "checklist": [
            "Teks angka besar di layar: Rp5.400/kg, Rp10,8jt/tahun",
            "Background gelap, angka kontras",
            "Edit 45–55 detik",
            "Post jam 05.30–07.00",
        ],
    },
    {
        "tanggal": "2026-06-27",
        "label": "Hari 23 — Reframe Biaya Pelatihan",
        "format": "Reels/TikTok",
        "hook": "Yang mahal itu trial-error. Bukan biaya pelatihan.",
        "tujuan": "Reframe objeksi harga pelatihan",
        "cta_trigger": "PELATIHAN",
        "footage_hint": "Footage suasana pelatihan — peserta aktif, interaktif",
        "reminder": "HANDLING OBJEKSI — Ini konten untuk yang ragu soal harga. Pastikan tone confident, bukan defensif.",
        "checklist": [
            "Footage suasana pelatihan — peserta aktif",
            "Perbandingan biaya tersirat: bocor Rp3–8jt vs bayar pelatihan sekali",
            "Edit 40–50 detik",
            "Post jam 05.30–07.00",
            "Update urgency: 'batch Juli hampir penuh'",
        ],
    },
    {
        "tanggal": "2026-06-28",
        "label": "Hari 24 — 7 Hal dari Pelatihan",
        "format": "Carousel",
        "hook": "7 hal konkret yang kamu bawa pulang dari pelatihan ini.",
        "tujuan": "Detail deliverable pelatihan = kurangi friction pendaftaran",
        "cta_trigger": "PELATIHAN",
        "footage_hint": "Visual list profesional + background PPBIB",
        "reminder": "CAROUSEL DELIVERABLE — Ini menjawab 'dapat apa dari pelatihan?' Harus spesifik, bukan abstrak.",
        "checklist": [
            "Desain 9 slide (7 deliverable + hook + CTA)",
            "Setiap slide: konkret, spesifik, tidak generik",
            "Slide terakhir: DM PELATIHAN",
            "Post jam 07.00–09.00",
        ],
    },
    {
        "tanggal": "2026-06-29",
        "label": "Hari 25 — Studi Kasus Alumni",
        "format": "Reels/TikTok",
        "hook": "Simulasi angka nyata — peserta yang FCR-nya turun 0,4 dalam 1 siklus.",
        "tujuan": "Social proof berbasis angka nyata",
        "cta_trigger": "PELATIHAN",
        "footage_hint": "Screenshot WA alumni (disanitasi) + footage kolam",
        "reminder": "SOCIAL PROOF — Kalau ada testimonial alumni baru, ini waktu terbaik untuk tampilkan.",
        "checklist": [
            "Siapkan screenshot WA alumni (disanitasi nama & nomor)",
            "Footage kolam alumni atau kolam PPBIB",
            "Hitung angka: 0,4 × Rp9.000 × kapasitas kolam",
            "Edit 45–55 detik",
            "Post jam 05.30–07.00",
        ],
    },
    {
        "tanggal": "2026-06-30",
        "label": "Hari 26 — Stories BTS Persiapan Batch",
        "format": "Instagram/FB Stories",
        "hook": "Persiapan bahan baku untuk praktek batch Juli.",
        "tujuan": "Bukti kesiapan fasilitas + urgency slot",
        "cta_trigger": "PELATIHAN",
        "footage_hint": "BTS persiapan fasilitas: bahan baku, mesin, ruang kelas",
        "reminder": "STORIES HARI INI — Pakai foto/video asli fasilitas. Keaslian lebih powerful dari desain bagus.",
        "checklist": [
            "Foto/video bahan baku yang sudah disiapkan",
            "Foto ruang kelas + mesin dalam kondisi siap",
            "5 frame stories: bahan → mesin → info batch → countdown → personal",
            "Aktifkan 'Balas Stories' CTA di setiap frame",
            "Post jam 07.00–09.00",
        ],
    },
    {
        "tanggal": "2026-07-01",
        "label": "Hari 27 — Timeline Daftar ke Panen",
        "format": "Reels/TikTok",
        "hook": "Pelatihan bulan ini. Panen pertama: 4 bulan dari sekarang. Kalkulasinya masuk.",
        "tujuan": "Visualisasi ROI timeline nyata",
        "cta_trigger": "PELATIHAN",
        "footage_hint": "Footage kolam panen + visual timeline sederhana di layar",
        "reminder": "TIMELINE VISUAL — Ini konten yang mendorong keputusan. Pastikan urgency nyata dan berdasarkan fakta batch.",
        "checklist": [
            "Footage kolam panen (kalau ada)",
            "Visual timeline simpel: Juli → Akhir Juli → Oktober",
            "Angka hemat per siklus harus muncul jelas",
            "Edit 45–55 detik",
            "Post jam 05.30–07.00",
            "Urgency: slot tinggal beberapa",
        ],
    },
    {
        "tanggal": "2026-07-02",
        "label": "Hari 28 — Preview Modul Pelatihan",
        "format": "Carousel",
        "hook": "Preview isi modul — supaya kamu tahu persis apa yang dipelajari.",
        "tujuan": "Transparansi kurikulum = tingkatkan kepercayaan",
        "cta_trigger": "PELATIHAN",
        "footage_hint": "Visual modul/slide materi + background PPBIB",
        "reminder": "CAROUSEL KURIKULUM — Ini menjawab 'belajar apa saja?'. Harus terlihat profesional dan terstruktur.",
        "checklist": [
            "Desain 8 slide berdasarkan 5 modul + praktek + CTA",
            "Setiap slide: judul modul + 3 poin konkret",
            "Terlihat profesional dan terstruktur",
            "Slide terakhir: urgency 'hampir penuh'",
            "Post jam 07.00–09.00",
        ],
    },
    {
        "tanggal": "2026-07-03",
        "label": "Hari 29 — Cerita Alumni",
        "format": "Reels/TikTok",
        "hook": "Banyak yang baru sadar setelah ikut pelatihan — ini ceritanya.",
        "tujuan": "Soft sell via narasi + momen 'aha' alumni",
        "cta_trigger": "PELATIHAN",
        "footage_hint": "Video alumni natural / suasana pelatihan",
        "reminder": "HARI SEBELUM PENUTUP — Konten human touch terakhir. Kalau ada video alumni asli, gunakan sekarang.",
        "checklist": [
            "Video alumni singkat natural (jika tersedia)",
            "Atau footage suasana pelatihan + narasi audio",
            "Tone: storytelling, bukan hard sell",
            "Edit 45–55 detik",
            "Post jam 05.30–07.00",
        ],
    },
    {
        "tanggal": "2026-07-04",
        "label": "Hari 30 — Rekap 30 Hari",
        "format": "Reels/TikTok",
        "hook": "30 hari, ratusan peternak teredukasi. Ini yang kami pelajari dari kamu.",
        "tujuan": "Rekap bulan + buka batch 2 / Agustus",
        "cta_trigger": "PELATIHAN",
        "footage_hint": "Montase footage lapangan terbaik selama 30 hari",
        "reminder": "HARI PENUTUP — Rekap penuh. Mulai buka slot batch Agustus di akhir video.",
        "checklist": [
            "Montase footage lapangan terbaik 30 hari",
            "Highlight 3 pertanyaan paling banyak masuk",
            "Sebut: Batch Juli hampir penuh | Batch Agustus dibuka",
            "Edit 50–60 detik",
            "Post jam 05.30–07.00",
        ],
    },
]

# index by date for O(1) lookup
_PLAN_BY_DATE = {c["tanggal"]: c for c in CONTENT_PLAN}


def get_fixed_content_today() -> dict | None:
    today = datetime.now().strftime("%Y-%m-%d")
    return _PLAN_BY_DATE.get(today)


def get_fixed_content_ahead(days: int = 3) -> list[dict]:
    from datetime import timedelta
    results = []
    today = datetime.now()
    for i in range(1, days + 1):
        d = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        if d in _PLAN_BY_DATE:
            results.append(_PLAN_BY_DATE[d])
    return results


def format_fixed_reminder_wa(c: dict) -> str:
    lines = [
        "☀️ *Reminder Konten Hari Ini — PPBIB*",
        f"📅 {datetime.now().strftime('%d %b %Y')} | {c['label']}",
        "─" * 30,
        "",
        f"📱 *Format*    : {c['format']}",
        f"🎣 *Hook*      : _{c['hook']}_",
        f"🎯 *Tujuan*    : {c['tujuan']}",
        f"📣 *CTA*       : {c['cta_trigger']}",
        f"🎬 *Footage*   : {c['footage_hint']}",
        "",
        f"⚠️ {c['reminder']}",
        "",
        "*✅ CHECKLIST:*",
    ]
    for i, item in enumerate(c["checklist"], 1):
        lines.append(f"  {i}. {item}")

    ahead = get_fixed_content_ahead(3)
    if ahead:
        lines += ["", "─" * 30, "📆 *3 Hari ke Depan:*"]
        for a in ahead:
            from datetime import datetime as dt
            d = dt.strptime(a["tanggal"], "%Y-%m-%d")
            tgl = d.strftime("%d %b")
            lines.append(f"  • {tgl} — {a['label']} [{a['format']}]")

    lines += [
        "",
        "─" * 30,
        "💡 _Selesaikan syuting sehari sebelum jadwal posting._",
        "_Sistem PPBIB_",
    ]
    return "\n".join(lines)
