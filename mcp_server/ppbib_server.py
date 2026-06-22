#!/usr/bin/env python3
"""
PPBIB Daily Assistant — MCP Server
Tools untuk Claude: ringkasan leads, follow-up, status sistem, dan analytics harian.
"""
import sys
import os
import json
import asyncio
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

LEADS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "leads.json")
TOKEN_FILE  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tokens", "tiktok_token.json")
REPORT_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "reports")

server = Server("ppbib-daily-assistant")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_leads() -> dict:
    if not os.path.exists(LEADS_FILE):
        return {}
    with open(LEADS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save_leads(leads: dict):
    os.makedirs(os.path.dirname(LEADS_FILE), exist_ok=True)
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)


def _days_since(iso_str: str) -> int:
    return (datetime.now() - datetime.fromisoformat(iso_str)).days


STATUS_LABELS = {
    "new":          "🔵 Baru",
    "dm_sent":      "📩 DM Terkirim",
    "followup_d1":  "📅 Follow-up D1",
    "followup_d3":  "📅 Follow-up D3",
    "followup_d7":  "📅 Follow-up D7",
    "closed":       "✅ Closed",
}


# ── Tool definitions ─────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="ringkasan_harian",
            description=(
                "Ringkasan harian PPBIB: total leads per status, lead baru hari ini, "
                "dan jumlah follow-up yang jatuh tempo."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="daftar_leads",
            description="Lihat semua leads, bisa difilter berdasarkan status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter status. Gunakan 'all' untuk semua.",
                        "enum": ["all", "new", "dm_sent", "followup_d1",
                                 "followup_d3", "followup_d7", "closed"],
                        "default": "all",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="detail_lead",
            description="Lihat detail lengkap satu lead berdasarkan username TikTok.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Username TikTok (tanpa @)"}
                },
                "required": ["username"],
            },
        ),
        types.Tool(
            name="followup_hari_ini",
            description=(
                "Daftar leads yang harus di-follow up hari ini berdasarkan jadwal "
                "D1 (≥1 hari), D3 (≥2 hari sejak D1), D7 (≥4 hari sejak D3)."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="update_lead",
            description="Update status dan/atau catatan sebuah lead.",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Username lead yang diupdate",
                    },
                    "status": {
                        "type": "string",
                        "description": "Status baru",
                        "enum": ["new", "dm_sent", "followup_d1",
                                 "followup_d3", "followup_d7", "closed"],
                    },
                    "catatan": {
                        "type": "string",
                        "description": "Catatan tambahan (opsional)",
                    },
                },
                "required": ["username", "status"],
            },
        ),
        types.Tool(
            name="cek_status_sistem",
            description="Cek status koneksi WhatsApp bot dan ketersediaan TikTok token.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="laporan_terakhir",
            description="Baca laporan harian atau mingguan terakhir yang tersimpan.",
            inputSchema={
                "type": "object",
                "properties": {
                    "jenis": {
                        "type": "string",
                        "description": "Jenis laporan",
                        "enum": ["harian", "mingguan"],
                        "default": "harian",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="statistik_konversi",
            description=(
                "Hitung tingkat konversi dari keseluruhan funnel: "
                "komentar → DM → Follow-up → Closed."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


# ── Tool handlers ─────────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    # ── ringkasan_harian ──────────────────────────────────────────────────────
    if name == "ringkasan_harian":
        leads = _load_leads()
        now = datetime.now()
        today = now.date()

        status_counts: dict[str, int] = {}
        new_today = 0
        fu_due = 0

        for lead in leads.values():
            s = lead.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

            if datetime.fromisoformat(lead["created_at"]).date() == today:
                new_today += 1

            last = datetime.fromisoformat(lead.get("last_contact", lead["created_at"]))
            delta = now - last
            if s == "dm_sent" and delta >= timedelta(days=1):
                fu_due += 1
            elif s == "followup_d1" and delta >= timedelta(days=2):
                fu_due += 1
            elif s == "followup_d3" and delta >= timedelta(days=4):
                fu_due += 1

        lines = [
            f"📊 *RINGKASAN HARIAN PPBIB — {now.strftime('%d %B %Y')}*\n",
            f"👥 Total Leads    : {len(leads)}",
            f"🆕 Masuk Hari Ini : {new_today}",
            f"⏰ Follow-up Due  : {fu_due}\n",
            "📋 Breakdown Status:",
        ]
        for s, label in STATUS_LABELS.items():
            c = status_counts.get(s, 0)
            if c:
                lines.append(f"  {label}: {c}")

        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── daftar_leads ─────────────────────────────────────────────────────────
    elif name == "daftar_leads":
        leads = _load_leads()
        status_filter = arguments.get("status", "all")

        filtered = (
            leads if status_filter == "all"
            else {k: v for k, v in leads.items() if v.get("status") == status_filter}
        )

        if not filtered:
            return [types.TextContent(type="text", text=f"Tidak ada lead dengan status '{status_filter}'.")]

        lines = [f"📋 Leads — {status_filter} ({len(filtered)} total):\n"]
        for lead in filtered.values():
            created = datetime.fromisoformat(lead["created_at"]).strftime("%d/%m/%y")
            label = STATUS_LABELS.get(lead["status"], lead["status"])
            lines.append(f"• @{lead['username']}  [{label}]  masuk: {created}")

        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── detail_lead ──────────────────────────────────────────────────────────
    elif name == "detail_lead":
        leads = _load_leads()
        username = arguments.get("username", "").lstrip("@")
        lead = leads.get(username)

        if not lead:
            return [types.TextContent(type="text", text=f"Lead '@{username}' tidak ditemukan.")]

        created  = datetime.fromisoformat(lead["created_at"]).strftime("%d %B %Y %H:%M")
        last     = datetime.fromisoformat(lead["last_contact"]).strftime("%d %B %Y %H:%M")
        label    = STATUS_LABELS.get(lead["status"], lead["status"])

        text = (
            f"👤 Lead: @{username}\n\n"
            f"Status          : {label}\n"
            f"Sumber Video    : {lead.get('source_video', '-')}\n"
            f"Komentar Awal   : {lead.get('comment', '-')}\n"
            f"Pertama Masuk   : {created}\n"
            f"Kontak Terakhir : {last}\n"
            f"Catatan         : {lead.get('notes', '').strip() or '-'}"
        )
        return [types.TextContent(type="text", text=text)]

    # ── followup_hari_ini ─────────────────────────────────────────────────────
    elif name == "followup_hari_ini":
        leads = _load_leads()
        now = datetime.now()
        due: list[tuple[str, str, int]] = []

        for lead in leads.values():
            s = lead.get("status")
            last = datetime.fromisoformat(lead.get("last_contact", lead["created_at"]))
            delta = now - last

            if s == "dm_sent"      and delta >= timedelta(days=1):
                due.append((lead["username"], "DM → D1", delta.days))
            elif s == "followup_d1" and delta >= timedelta(days=2):
                due.append((lead["username"], "D1 → D3", delta.days))
            elif s == "followup_d3" and delta >= timedelta(days=4):
                due.append((lead["username"], "D3 → D7", delta.days))

        if not due:
            return [types.TextContent(type="text", text="✅ Tidak ada follow-up jatuh tempo hari ini.")]

        lines = [f"⏰ Follow-up Jatuh Tempo — {len(due)} lead:\n"]
        for username, step, days in due:
            lines.append(f"• @{username}  [{step}]  ({days} hari sejak kontak terakhir)")

        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── update_lead ──────────────────────────────────────────────────────────
    elif name == "update_lead":
        leads = _load_leads()
        username = arguments.get("username", "").lstrip("@")
        new_status = arguments["status"]
        catatan = arguments.get("catatan", "").strip()

        if username not in leads:
            return [types.TextContent(type="text", text=f"Lead '@{username}' tidak ditemukan.")]

        leads[username]["status"] = new_status
        leads[username]["last_contact"] = datetime.now().isoformat()
        if catatan:
            existing = leads[username].get("notes", "").strip()
            entry = f"{datetime.now().date()}: {catatan}"
            leads[username]["notes"] = (existing + "\n" + entry).strip()
        _save_leads(leads)

        label = STATUS_LABELS.get(new_status, new_status)
        return [types.TextContent(
            type="text",
            text=f"✅ @{username} diupdate ke {label}.{' Catatan ditambahkan.' if catatan else ''}",
        )]

    # ── cek_status_sistem ────────────────────────────────────────────────────
    elif name == "cek_status_sistem":
        import requests as req

        wa = "❌ Server tidak berjalan"
        try:
            r = req.get("http://localhost:3000/status", timeout=3)
            wa = "✅ Terhubung" if r.json().get("status") == "connected" else "⚠️ Disconnected"
        except Exception:
            pass

        tiktok = "✅ Token aktif" if os.path.exists(TOKEN_FILE) else "❌ Belum setup"

        text = (
            f"🔧 Status Sistem PPBIB\n\n"
            f"WhatsApp Bot  : {wa}\n"
            f"TikTok Token  : {tiktok}\n"
            f"Waktu Cek     : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        return [types.TextContent(type="text", text=text)]

    # ── laporan_terakhir ──────────────────────────────────────────────────────
    elif name == "laporan_terakhir":
        jenis = arguments.get("jenis", "harian")
        prefix = "weekly" if jenis == "mingguan" else "daily"

        if not os.path.exists(REPORT_DIR):
            return [types.TextContent(type="text", text="Belum ada laporan tersimpan.")]

        files = sorted(
            [f for f in os.listdir(REPORT_DIR) if f.startswith(prefix)],
            reverse=True,
        )
        if not files:
            return [types.TextContent(type="text", text=f"Belum ada laporan {jenis}.")]

        path = os.path.join(REPORT_DIR, files[0])
        with open(path, encoding="utf-8") as f:
            content = f.read()

        return [types.TextContent(type="text", text=f"📄 {files[0]}\n\n{content}")]

    # ── statistik_konversi ────────────────────────────────────────────────────
    elif name == "statistik_konversi":
        leads = _load_leads()
        total = len(leads)
        if total == 0:
            return [types.TextContent(type="text", text="Belum ada data leads.")]

        dm     = sum(1 for l in leads.values() if l["status"] != "new")
        fu_any = sum(1 for l in leads.values()
                     if l["status"] in ("followup_d1", "followup_d3", "followup_d7", "closed"))
        closed = sum(1 for l in leads.values() if l["status"] == "closed")

        def pct(n: int) -> str:
            return f"{round(n / total * 100, 1)}%" if total else "0%"

        text = (
            f"📈 Statistik Konversi Funnel PPBIB\n\n"
            f"Komentar Berminat : {total}  (100%)\n"
            f"DM Terkirim       : {dm}  ({pct(dm)})\n"
            f"Follow-up Dimulai : {fu_any}  ({pct(fu_any)})\n"
            f"Closed / Daftar   : {closed}  ({pct(closed)})\n"
        )
        return [types.TextContent(type="text", text=text)]

    return [types.TextContent(type="text", text=f"Tool '{name}' tidak dikenal.")]


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
