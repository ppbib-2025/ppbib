#!/usr/bin/env python3
"""
Inris Cijeruk — Google Sheets MCP Server
Baca dan tulis langsung ke Google Sheets via gspread.
"""
import sys
import os
import asyncio
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE  = os.path.join(BASE_DIR, "credentials.json")
SHEET_ID    = os.environ.get("INRIS_SHEET_ID", "")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

server = Server("inris-sheets-assistant")


def _get_sheet():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc    = gspread.authorize(creds)
    return gc.open_by_key(SHEET_ID)


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ── Tool Definitions ──────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="baca_agenda",
            description="Baca semua agenda dari Google Sheets Inris Cijeruk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tanggal": {
                        "type": "string",
                        "description": "Filter tanggal YYYY-MM-DD. Kosongkan untuk semua.",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="tulis_agenda",
            description="Tambah agenda baru ke Google Sheets Inris Cijeruk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tanggal":           {"type": "string", "description": "Tanggal YYYY-MM-DD"},
                    "jam":               {"type": "string", "description": "Jam mulai, misal '09:00'"},
                    "jenis":             {"type": "string", "description": "Jenis: penyuluhan/pelatihan/rapat/kunjungan_lapangan/magang/administrasi"},
                    "judul":             {"type": "string", "description": "Judul kegiatan"},
                    "lokasi":            {"type": "string", "description": "Lokasi kegiatan"},
                    "penanggung_jawab":  {"type": "string", "description": "Nama PJ"},
                    "catatan":           {"type": "string", "description": "Catatan tambahan"},
                },
                "required": ["tanggal", "jam", "jenis", "judul"],
            },
        ),
        types.Tool(
            name="baca_magang",
            description="Baca data mahasiswa magang dari Google Sheets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter status: aktif/selesai/dijadwalkan. Kosongkan untuk semua.",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="tulis_magang",
            description="Tambah atau perbarui data mahasiswa magang di Google Sheets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nama":             {"type": "string", "description": "Nama lengkap mahasiswa"},
                    "universitas":      {"type": "string", "description": "Nama universitas"},
                    "jurusan":          {"type": "string", "description": "Jurusan/prodi"},
                    "tanggal_mulai":    {"type": "string", "description": "Tanggal mulai YYYY-MM-DD"},
                    "tanggal_selesai":  {"type": "string", "description": "Tanggal selesai YYYY-MM-DD"},
                    "topik":            {"type": "string", "description": "Topik magang"},
                    "pembimbing":       {"type": "string", "description": "Nama pembimbing"},
                    "status":           {"type": "string", "description": "Status: aktif/selesai/dijadwalkan"},
                },
                "required": ["nama", "universitas", "jurusan", "tanggal_mulai", "tanggal_selesai"],
            },
        ),
        types.Tool(
            name="baca_pelatihan",
            description="Baca jadwal pelatihan dari Google Sheets.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="tulis_pelatihan",
            description="Tambah program pelatihan baru ke Google Sheets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nama":             {"type": "string", "description": "Nama program pelatihan"},
                    "tanggal_mulai":    {"type": "string", "description": "Tanggal mulai YYYY-MM-DD"},
                    "tanggal_selesai":  {"type": "string", "description": "Tanggal selesai YYYY-MM-DD"},
                    "materi":           {"type": "string", "description": "Topik/materi utama"},
                    "target_peserta":   {"type": "integer", "description": "Jumlah target peserta"},
                    "lokasi":           {"type": "string", "description": "Lokasi pelaksanaan"},
                    "instruktur":       {"type": "string", "description": "Nama instruktur/narasumber"},
                    "anggaran":         {"type": "string", "description": "Anggaran kegiatan"},
                },
                "required": ["nama", "tanggal_mulai", "tanggal_selesai", "materi", "target_peserta"],
            },
        ),
        types.Tool(
            name="ringkasan_harian",
            description="Ringkasan kegiatan hari ini dan besok dari semua sheet.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


# ── Tool Handlers ─────────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        wb = _get_sheet()
    except Exception as e:
        return [types.TextContent(type="text",
            text=f"❌ Gagal konek ke Google Sheets: {e}\nPastikan credentials.json sudah ada dan INRIS_SHEET_ID sudah diset.")]

    # ── baca_agenda ───────────────────────────────────────────────────────────
    if name == "baca_agenda":
        ws      = wb.worksheet("AGENDA")
        rows    = ws.get_all_records()
        tgl_f   = arguments.get("tanggal", "")
        items   = [r for r in rows if not tgl_f or str(r.get("Tanggal","")) == tgl_f]

        if not items:
            label = f"tanggal {tgl_f}" if tgl_f else "semua tanggal"
            return [types.TextContent(type="text",
                text=f"Tidak ada agenda untuk {label}.")]

        lines = [f"📅 Agenda{' — '+tgl_f if tgl_f else ''} ({len(items)} kegiatan):\n"]
        for r in sorted(items, key=lambda x: (str(x.get("Tanggal","")), str(x.get("Jam","")))):
            pj  = f"  PJ: {r['Penanggung Jawab']}" if r.get("Penanggung Jawab") else ""
            lok = f"  📍 {r['Lokasi']}" if r.get("Lokasi") else ""
            lines.append(f"• {r['Tanggal']} {r['Jam']}  [{r['Jenis']}]  {r['Judul']}{lok}{pj}")
        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── tulis_agenda ──────────────────────────────────────────────────────────
    elif name == "tulis_agenda":
        ws   = wb.worksheet("AGENDA")
        rows = ws.get_all_records()
        nid  = f"AGD-{len(rows)+1:03d}"
        ws.append_row([
            nid,
            arguments["tanggal"],
            arguments["jam"],
            arguments["jenis"],
            arguments["judul"],
            arguments.get("lokasi", ""),
            arguments.get("penanggung_jawab", ""),
            arguments.get("catatan", ""),
            _today(),
        ])
        return [types.TextContent(type="text",
            text=(
                f"✅ Agenda ditambahkan [{nid}]\n"
                f"📌 {arguments['judul']}\n"
                f"📅 {arguments['tanggal']} jam {arguments['jam']}\n"
                f"🏷️ {arguments['jenis']}"
                + (f"\n📍 {arguments['lokasi']}" if arguments.get("lokasi") else "")
                + (f"\n👤 PJ: {arguments['penanggung_jawab']}" if arguments.get("penanggung_jawab") else "")
            ))]

    # ── baca_magang ───────────────────────────────────────────────────────────
    elif name == "baca_magang":
        ws     = wb.worksheet("MAGANG")
        rows   = ws.get_all_records()
        sf     = arguments.get("status", "")
        items  = [r for r in rows if not sf or str(r.get("Status","")).lower() == sf.lower()]

        if not items:
            return [types.TextContent(type="text", text="Tidak ada data mahasiswa magang.")]

        lines = [f"🎓 Mahasiswa Magang ({len(items)} orang):\n"]
        for r in items:
            lines.append(
                f"• {r['Nama']}  [{r.get('Status','').upper()}]\n"
                f"  {r['Universitas']} / {r['Jurusan']}\n"
                f"  {r['Tanggal Mulai']} s/d {r['Tanggal Selesai']}"
                + (f"\n  Topik: {r['Topik']}" if r.get("Topik") else "")
                + (f"\n  Pembimbing: {r['Pembimbing']}" if r.get("Pembimbing") else "")
            )
        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── tulis_magang ──────────────────────────────────────────────────────────
    elif name == "tulis_magang":
        ws   = wb.worksheet("MAGANG")
        rows = ws.get_all_records()
        nid  = f"MGG-{len(rows)+1:03d}"
        ws.append_row([
            nid,
            arguments["nama"],
            arguments["universitas"],
            arguments["jurusan"],
            arguments["tanggal_mulai"],
            arguments["tanggal_selesai"],
            arguments.get("topik", ""),
            arguments.get("pembimbing", ""),
            arguments.get("status", "dijadwalkan"),
            "",
            "",
        ])
        return [types.TextContent(type="text",
            text=(
                f"✅ Mahasiswa magang didaftarkan [{nid}]\n"
                f"👤 {arguments['nama']}\n"
                f"🏫 {arguments['universitas']} — {arguments['jurusan']}\n"
                f"📅 {arguments['tanggal_mulai']} s/d {arguments['tanggal_selesai']}"
            ))]

    # ── baca_pelatihan ────────────────────────────────────────────────────────
    elif name == "baca_pelatihan":
        ws    = wb.worksheet("PELATIHAN")
        rows  = ws.get_all_records()

        if not rows:
            return [types.TextContent(type="text", text="Belum ada data pelatihan.")]

        lines = [f"🎯 Jadwal Pelatihan ({len(rows)} program):\n"]
        for r in rows:
            peserta = f"{r.get('Peserta Aktual') or r.get('Target Peserta','?')} peserta"
            lines.append(
                f"• [{r.get('Status','').upper()}]  {r['Nama Program']}\n"
                f"  📅 {r['Tanggal Mulai']} s/d {r['Tanggal Selesai']}\n"
                f"  📚 {r['Materi']}  |  👥 {peserta}"
                + (f"\n  📍 {r['Lokasi']}" if r.get("Lokasi") else "")
                + (f"\n  🎤 {r['Instruktur']}" if r.get("Instruktur") else "")
            )
        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── tulis_pelatihan ───────────────────────────────────────────────────────
    elif name == "tulis_pelatihan":
        ws   = wb.worksheet("PELATIHAN")
        rows = ws.get_all_records()
        nid  = f"PLT-{len(rows)+1:03d}"
        ws.append_row([
            nid,
            arguments["nama"],
            arguments["tanggal_mulai"],
            arguments["tanggal_selesai"],
            arguments["materi"],
            arguments["target_peserta"],
            "",
            arguments.get("lokasi", ""),
            arguments.get("instruktur", ""),
            arguments.get("anggaran", ""),
            "dijadwalkan",
            "",
        ])
        return [types.TextContent(type="text",
            text=(
                f"✅ Pelatihan terdaftar [{nid}]\n"
                f"📌 {arguments['nama']}\n"
                f"📅 {arguments['tanggal_mulai']} s/d {arguments['tanggal_selesai']}\n"
                f"📚 {arguments['materi']}  |  Target: {arguments['target_peserta']} peserta"
                + (f"\n📍 {arguments['lokasi']}" if arguments.get("lokasi") else "")
                + (f"\n🎤 {arguments['instruktur']}" if arguments.get("instruktur") else "")
            ))]

    # ── ringkasan_harian ──────────────────────────────────────────────────────
    elif name == "ringkasan_harian":
        today    = _today()
        besok    = (datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
                    .__class__.fromordinal(datetime.now().toordinal()+1)).strftime("%Y-%m-%d")

        agenda   = wb.worksheet("AGENDA").get_all_records()
        magang   = wb.worksheet("MAGANG").get_all_records()

        hari_ini = [r for r in agenda if str(r.get("Tanggal","")) == today]
        esok     = [r for r in agenda if str(r.get("Tanggal","")) == besok]
        aktif    = [m for m in magang if str(m.get("Status","")).lower() == "aktif"]

        lines = [
            f"☀️ Ringkasan Harian Inris Cijeruk — {today}\n",
            f"📅 Kegiatan hari ini   : {len(hari_ini)}",
            f"📅 Kegiatan besok      : {len(esok)}",
            f"🎓 Mahasiswa magang aktif : {len(aktif)}",
        ]
        if hari_ini:
            lines.append("\n📋 Hari ini:")
            for r in sorted(hari_ini, key=lambda x: str(x.get("Jam",""))):
                lines.append(f"  • {r['Jam']}  {r['Judul']}")
        if esok:
            lines.append("\n📋 Besok:")
            for r in sorted(esok, key=lambda x: str(x.get("Jam",""))):
                lines.append(f"  • {r['Jam']}  {r['Judul']}")

        return [types.TextContent(type="text", text="\n".join(lines))]

    return [types.TextContent(type="text", text=f"Tool '{name}' tidak dikenal.")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
