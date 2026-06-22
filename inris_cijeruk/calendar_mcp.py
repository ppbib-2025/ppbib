#!/usr/bin/env python3
"""
Inris Cijeruk — Google Calendar MCP Server
Tambah dan baca event dari Google Calendar Inris Cijeruk.
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CREDS_FILE  = os.path.join(BASE_DIR, "credentials.json")
CALENDAR_ID = os.environ.get("INRIS_CALENDAR_ID", "")

SCOPES = ["https://www.googleapis.com/auth/calendar"]

server = Server("inris-calendar-assistant")


def _get_service():
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds)


def _fmt(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d %b %Y %H:%M")
    except Exception:
        return iso


# ── Tool Definitions ──────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="tambah_event",
            description="Tambah kegiatan ke Google Calendar Inris Cijeruk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "judul":       {"type": "string",  "description": "Judul kegiatan"},
                    "tanggal":     {"type": "string",  "description": "Tanggal YYYY-MM-DD"},
                    "jam_mulai":   {"type": "string",  "description": "Jam mulai HH:MM (opsional, misal '08:00')"},
                    "jam_selesai": {"type": "string",  "description": "Jam selesai HH:MM (opsional)"},
                    "lokasi":      {"type": "string",  "description": "Lokasi kegiatan"},
                    "deskripsi":   {"type": "string",  "description": "Catatan/deskripsi"},
                    "reminder_menit": {
                        "type": "integer",
                        "description": "Pengingat berapa menit sebelum acara (default 60)",
                        "default": 60,
                    },
                },
                "required": ["judul", "tanggal"],
            },
        ),
        types.Tool(
            name="lihat_agenda",
            description="Lihat event Google Calendar Inris Cijeruk dalam rentang waktu tertentu.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dari":    {"type": "string", "description": "Tanggal mulai YYYY-MM-DD (default: hari ini)"},
                    "sampai":  {"type": "string", "description": "Tanggal akhir YYYY-MM-DD (default: 7 hari ke depan)"},
                },
                "required": [],
            },
        ),
        types.Tool(
            name="sinkron_dari_sheets",
            description="Sinkronkan semua agenda dari Google Sheets ke Google Calendar sekaligus.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


# ── Tool Handlers ─────────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if not CALENDAR_ID:
        return [types.TextContent(type="text",
            text="❌ INRIS_CALENDAR_ID belum diset. Set environment variable dulu.")]
    try:
        svc = _get_service()
    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Gagal konek ke Google Calendar: {e}")]

    # ── tambah_event ──────────────────────────────────────────────────────────
    if name == "tambah_event":
        tgl        = arguments["tanggal"]
        jam_mulai  = arguments.get("jam_mulai", "")
        jam_selesai= arguments.get("jam_selesai", "")
        reminder   = arguments.get("reminder_menit", 60)

        if jam_mulai:
            start = {"dateTime": f"{tgl}T{jam_mulai}:00", "timeZone": "Asia/Jakarta"}
            end_t = jam_selesai or (
                datetime.strptime(f"{tgl}T{jam_mulai}", "%Y-%mT%H:%M")
                + timedelta(hours=2)
            ).strftime("%H:%M")
            end   = {"dateTime": f"{tgl}T{end_t}:00", "timeZone": "Asia/Jakarta"}
        else:
            start = {"date": tgl}
            end   = {"date": tgl}

        body = {
            "summary":     arguments["judul"],
            "location":    arguments.get("lokasi", ""),
            "description": arguments.get("deskripsi", ""),
            "start":       start,
            "end":         end,
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup",  "minutes": reminder},
                    {"method": "email",  "minutes": reminder},
                ],
            },
        }

        ev = svc.events().insert(calendarId=CALENDAR_ID, body=body).execute()
        return [types.TextContent(type="text",
            text=(
                f"✅ Event ditambahkan ke Google Calendar!\n"
                f"📌 {arguments['judul']}\n"
                f"📅 {tgl}{' jam '+jam_mulai if jam_mulai else ''}\n"
                f"🔔 Reminder: {reminder} menit sebelum acara\n"
                f"🔗 {ev.get('htmlLink','')}"
            ))]

    # ── lihat_agenda ──────────────────────────────────────────────────────────
    elif name == "lihat_agenda":
        dari   = arguments.get("dari",   datetime.now().strftime("%Y-%m-%d"))
        sampai = arguments.get("sampai", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"))

        hasil = svc.events().list(
            calendarId=CALENDAR_ID,
            timeMin=f"{dari}T00:00:00+07:00",
            timeMax=f"{sampai}T23:59:59+07:00",
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = hasil.get("items", [])
        if not events:
            return [types.TextContent(type="text",
                text=f"Tidak ada event dari {dari} s/d {sampai}.")]

        lines = [f"📅 Agenda {dari} s/d {sampai} ({len(events)} kegiatan):\n"]
        for ev in events:
            start = ev["start"].get("dateTime", ev["start"].get("date",""))
            lines.append(f"• {_fmt(start)}  {ev['summary']}")
        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── sinkron_dari_sheets ───────────────────────────────────────────────────
    elif name == "sinkron_dari_sheets":
        import gspread
        from google.oauth2.service_account import Credentials as GCreds

        sheet_id = os.environ.get("INRIS_SHEET_ID","")
        if not sheet_id:
            return [types.TextContent(type="text",
                text="❌ INRIS_SHEET_ID belum diset.")]

        scopes_sheets = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/calendar",
        ]
        creds  = GCreds.from_service_account_file(CREDS_FILE, scopes=scopes_sheets)
        gc     = gspread.authorize(creds)
        wb     = gc.open_by_key(sheet_id)
        rows   = wb.worksheet("AGENDA").get_all_records()
        svc2   = build("calendar", "v3", credentials=creds)

        berhasil = 0
        for r in rows:
            tgl = str(r.get("Tanggal","")).strip()
            if not tgl:
                continue
            jam = str(r.get("Jam","")).strip()
            body = {
                "summary":     r.get("Judul",""),
                "location":    r.get("Lokasi",""),
                "description": f"PJ: {r.get('Penanggung Jawab','')}\n{r.get('Catatan','')}",
                "start": ({"dateTime": f"{tgl}T{jam}:00", "timeZone": "Asia/Jakarta"}
                          if jam else {"date": tgl}),
                "end":   ({"dateTime": f"{tgl}T{jam}:00", "timeZone": "Asia/Jakarta"}
                          if jam else {"date": tgl}),
                "reminders": {
                    "useDefault": False,
                    "overrides": [{"method": "popup", "minutes": 60}],
                },
            }
            svc2.events().insert(calendarId=CALENDAR_ID, body=body).execute()
            berhasil += 1

        return [types.TextContent(type="text",
            text=f"✅ Sinkronisasi selesai! {berhasil} agenda dari Sheets masuk ke Google Calendar.")]

    return [types.TextContent(type="text", text=f"Tool '{name}' tidak dikenal.")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
