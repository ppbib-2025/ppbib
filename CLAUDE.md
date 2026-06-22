# PPBIB Bot — Panduan Claude

## Gambaran Proyek

PPBIB adalah sistem otomasi marketing yang mengelola leads dari TikTok, mengirim follow-up via WhatsApp, dan melacak konversi di CRM lokal.

## Arsitektur

```
main.py              — Entry point; APScheduler + Flask dashboard
src/
  bot.py             — Scan komentar TikTok, reply, simpan leads
  crm.py             — Baca/tulis leads (data/leads.json)
  analytics.py       — Snapshot metrics harian + laporan
  content_generator.py — Buat rencana konten mingguan via AI
  auto_research.py   — Evaluasi performa konten tiap Sabtu
  video_producer.py  — Produksi video via Seedance/Higgsfield
  whatsapp.py        — Kirim pesan via WhatsApp bot (port 3000)
  dashboard.py       — Flask web dashboard analytics
templates/
  funnel.py          — Template pesan sales funnel (DM, follow-up)
whatsapp/
  bot.js             — WhatsApp bot (whatsapp-web.js, port 3000)
mcp_server/
  ppbib_server.py    — MCP server daily assistant (tools untuk Claude)
```

## MCP Daily Assistant

Server MCP lokal di `mcp_server/ppbib_server.py` mengekspos 8 tool ke Claude:

| Tool | Fungsi |
|------|--------|
| `ringkasan_harian` | Total leads, lead baru hari ini, follow-up jatuh tempo |
| `daftar_leads` | List semua/filter leads per status |
| `detail_lead` | Detail lengkap satu lead |
| `followup_hari_ini` | Leads yang harus di-follow up hari ini |
| `update_lead` | Update status + catatan lead |
| `cek_status_sistem` | Cek koneksi WhatsApp dan TikTok token |
| `laporan_terakhir` | Baca laporan harian/mingguan terakhir |
| `statistik_konversi` | Tingkat konversi seluruh funnel |

### Cara Aktifkan MCP

Tambahkan ke `.mcp.json` di root project:

```json
{
  "mcpServers": {
    "ppbib-daily-assistant": {
      "command": "python",
      "args": ["mcp_server/ppbib_server.py"]
    }
  }
}
```

Atau via Claude Code CLI:

```bash
claude mcp add ppbib-daily-assistant -- python mcp_server/ppbib_server.py
```

## Status Funnel Leads

```
new → dm_sent → followup_d1 → followup_d3 → followup_d7 → closed
```

Jadwal follow-up otomatis:
- **D1**: 1 hari setelah DM dikirim
- **D3**: 2 hari setelah follow-up D1
- **D7**: 4 hari setelah follow-up D3

## File Data Penting

```
data/leads.json                 — Database leads CRM
data/tokens/tiktok_token.json   — OAuth token TikTok
data/analytics_tiktok.json      — Snapshot metrics TikTok
data/analytics_instagram.json   — Snapshot metrics Instagram
data/analytics_facebook.json    — Snapshot metrics Facebook
data/reports/                   — Laporan harian/mingguan tersimpan
data/replied_comments.txt       — ID komentar yang sudah direply
```

## Variabel Lingkungan (.env)

```
TIKTOK_CLIENT_KEY       — TikTok OAuth client key
TIKTOK_CLIENT_SECRET    — TikTok OAuth client secret
TIKTOK_REDIRECT_URI     — Redirect URI untuk OAuth callback
WHATSAPP_NUMBER         — Nomor WA untuk kirim follow-up
REPORT_WA_NUMBER        — Nomor WA untuk laporan (default = WHATSAPP_NUMBER)
ANTHROPIC_API_KEY       — Claude API key (untuk AI content generator)
FAL_KEY                 — Fal.ai key (untuk produksi video AI)
PORT                    — Port Flask dashboard (default: 8080)
```

## Menjalankan

```bash
# Install dependencies
pip install -r requirements.txt
cd whatsapp && npm install

# Setup TikTok token (sekali)
python setup_token.py

# Jalankan WhatsApp bot (terminal terpisah)
cd whatsapp && node bot.js

# Jalankan bot utama
python main.py
```

## Jadwal Otomatis

| Waktu | Job |
|-------|-----|
| Setiap 15 menit | Scan komentar TikTok |
| Setiap 6 jam | Run follow-up leads |
| Tiap hari 07:00 | Reminder konten harian |
| Tiap hari 08:00 | Produksi video AI |
| Tiap hari 19:00 | Snapshot analytics |
| Tiap hari 20:00 | Kirim laporan harian via WA |
| Senin 07:00 | Laporan mingguan via WA |
| Sabtu 17:00 | Auto research & evaluasi konten |
| Minggu 18:00 | Generate rencana konten minggu depan |
