"""
AI lead scoring dan response generation menggunakan Claude API.
"""
import json
import os

import anthropic

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def score_lead(username: str, comment: str) -> dict:
    """
    Analisis komentar dengan AI untuk skor kesiapan beli (1-10) dan intent.
    Returns: {score, intent, priority}
    """
    try:
        msg = _get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            system="""Kamu adalah analis sales untuk program pelatihan pakan ternak PPBIB (budidaya ayam/ikan buras).
Analisis komentar TikTok dan berikan skor kesiapan beli (1-10) dan intent singkat dalam format JSON.

Panduan skor:
- 9-10: Sangat panas — sebut harga spesifik, siap daftar, tanya kapan mulai
- 7-8: Panas — tanya harga, biaya, cara daftar
- 5-6: Hangat — tanya info umum, cara kerja program
- 3-4: Dingin — sekedar penasaran, belum jelas tujuannya
- 1-2: Sangat dingin — komentar tidak relevan dengan pelatihan

Balas HANYA dengan JSON valid: {"score": N, "intent": "deskripsi singkat", "priority": "high|medium|low"}""",
            messages=[{
                "role": "user",
                "content": f"Username: @{username}\nKomentar: {comment}",
            }],
        )
        return json.loads(msg.content[0].text.strip())
    except Exception as e:
        print(f"[AI] Gagal score lead: {e}")
        return {"score": 5, "intent": "tidak diketahui", "priority": "medium"}


def generate_wa_response(username: str, incoming_message: str, lead_context: dict) -> str:
    """
    Generate balasan WhatsApp yang personal berdasarkan pesan masuk dan konteks lead.
    """
    try:
        msg = _get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system="""Kamu adalah asisten penjualan PPBIB (Pusat Pelatihan Budidaya dan Pakan Ternak).
Program kami: pelatihan profesional bersertifikat budidaya ayam buras dan ikan, termasuk cara membuat pakan sendiri yang hemat biaya.

Tugas: balas pesan WhatsApp calon peserta dengan ramah, informatif, dan persuasif dalam Bahasa Indonesia.

Panduan:
- Sapa dengan nama
- Jawab pertanyaan secara spesifik
- Jika tanya harga: sampaikan investasi mulai dari Rp 500rb, arahkan ke konsultasi untuk detail
- Jika siap daftar: minta nama lengkap, kota asal, pilihan jadwal (online/offline)
- Jika ragu: berikan 2-3 manfaat konkret pelatihan (hemat pakan 30-40%, hasil panen lebih optimal)
- Maksimal 3 paragraf pendek
- Akhiri dengan pertanyaan atau CTA yang jelas
- Gunakan bahasa santai dan hangat""",
            messages=[{
                "role": "user",
                "content": (
                    f"Konteks lead:\n"
                    f"- Username TikTok: @{username}\n"
                    f"- Komentar awal: {lead_context.get('comment', '-')}\n"
                    f"- Skor lead: {lead_context.get('score', '-')}/10\n"
                    f"- Riwayat: {lead_context.get('notes', 'baru pertama kali kontak') or 'baru pertama kali kontak'}\n\n"
                    f"Pesan WhatsApp masuk: {incoming_message}"
                ),
            }],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        print(f"[AI] Gagal generate response: {e}")
        return (
            f"Halo {username}! Terima kasih sudah menghubungi PPBIB. "
            "Tim kami akan segera membalas ya 🙏"
        )
