# PPBIB — Project Context

## Tentang Bisnis

PPBIB (Pusat Pelatihan Budidaya Ikan Bogor) — konsultan dan pelatihan akuakultur berbasis di Cijeruk, Bogor.
Fokus: optimasi FCR, formulasi pakan, budidaya lele/nila/gurame/patin/mas.
Kontak utama/owner: Aditiya (nomor WA untuk eskalasi leads besar).

## Produk & Harga

| Produk | Harga |
|--------|-------|
| Bundle Digital (PDF + FCR Calculator) | Rp 75.000–200.000 |
| Online Bootcamp (Zoom) | Rp 299.000–999.000 |
| Workshop Offline (1 hari) | Rp 1.499.000 |

Discount request → eskalasi ke Aditiya, jangan tangani sendiri.

## Funnel Leads (F1–F4)

- **F1 Awareness** — baru tahu PPBIB, belum ada species/masalah spesifik
- **F2 Interest** — sudah sebut species atau masalah teknis (FCR, pakan, kolam)
- **F3 Consideration** — bicara modal, lahan, rencana, timeline
- **F4 Decision** — tanya harga, biaya, cara daftar, transfer

Override: F3 dengan latar pemula → treat as F2 dulu.

## Eskalasi ke Aditiya

Langsung eskalasi jika:
- Skala MENENGAH atau BESAR
- Tanya harga di pesan pertama
- Angka kematian ikan >30%

## Species & FCR Benchmark

| Species | FCR Ideal | Catatan |
|---------|-----------|---------|
| Lele | 0.8–1.0 | Paling efisien |
| Nila | 1.2–1.4 | |
| Gurame | 1.5–1.8 | Lambat, harga jual tinggi |
| Mas | 1.5–1.7 | |
| Patin | 1.2–1.5 | |

Skala: mikro (<500 ekor / <50 kg), kecil, menengah, besar.

## Gaya Komunikasi Bot WA

- Plain text — tidak ada **, ##, bullet points, numbered list
- Pendek: 4–5 kalimat per balasan
- Tanya SATU pertanyaan di akhir
- Nada: santai + authority, seperti teman yang ahli — bukan CS formal
- Frame dari sisi ROI pembudidaya: "kalau FCR turun 0.2, itu Rp X langsung ke margin"
- Tidak sebut harga produk di pesan pertama

## Stack Teknis

- **Flask webhook** (`waha_integration.py`) — menerima event dari WAHA, panggil AI, kirim reply
- **WAHA** — WhatsApp HTTP API, session `default`, host: `waha-qelypbwuouqo.cgk-srikandi.sumopod.my.id`
- **AI model** — `claude-haiku-4-5` via Dinoiki API proxy (`https://ai.dinoiki.com/v1`)
- **Deploy** — Railway: `https://ppbib-production.up.railway.app`
- **Webhook URL** — `https://ppbib-production.up.railway.app/webhook`
- **Health check** — `https://ppbib-production.up.railway.app/health`

## Environment Variables (Railway)

```
WAHA_URL
WAHA_API_KEY
WAHA_SESSION=default
DINOIKI_API_KEY
```

## File Penting

| File | Fungsi |
|------|--------|
| `ppbib_agents.md` | System prompt utama bot WA |
| `leads_flow.md` | Metadirektif chain: intake → FCR calc → reply |
| `lead_intake.md` | SOP identifikasi leads: species, skala, funnel stage |
| `fcr_calculator.py` | Kalkulasi kerugian FCR dalam Rupiah |
| `followup_sequence.md` | Template follow-up 7 hari per species |
| `closing_offer.md` | Skenario closing A/B/C |
| `content_tiktok.md` | Workflow 5 agent untuk konten TikTok edukasi |
| `waha_integration.py` | Flask server — inti sistem |

## Cara Ubah Balasan Bot

Edit `ppbib_agents.md` → push ke branch `claude/ppbib-agents-doc-n5eEh` → Railway auto-redeploy.
Tidak perlu restart manual.
