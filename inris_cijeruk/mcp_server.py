#!/usr/bin/env python3
"""
Inris Cijeruk Daily Assistant — MCP Server
Tools harian untuk kantor pemerintah bidang perikanan:
agenda, mahasiswa magang, jadwal pelatihan, dan laporan bulanan.
"""
import sys
import os
import json
import asyncio
from datetime import datetime, date, timedelta

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
AGENDA_F   = os.path.join(DATA_DIR, "agenda.json")
MAGANG_F   = os.path.join(DATA_DIR, "mahasiswa_magang.json")
LATIH_F    = os.path.join(DATA_DIR, "pelatihan.json")

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

server = Server("inris-daily-assistant")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(path: str, data: list):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _today() -> str:
    return date.today().isoformat()


def _fmt_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d %B %Y")
    except Exception:
        return iso


JENIS_AGENDA = ["penyuluhan", "pelatihan", "kunjungan_lapangan",
                 "rapat", "magang", "administrasi", "lainnya"]

STATUS_MAGANG = ["aktif", "selesai", "dijadwalkan", "dibatalkan"]


# ── Tool Definitions ──────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ── AGENDA ──────────────────────────────────────────────────────────
        types.Tool(
            name="agenda_hari_ini",
            description=(
                "Tampilkan semua kegiatan hari ini atau tanggal tertentu. "
                "Mencakup penyuluhan, kunjungan lapangan, rapat, pelatihan, dll."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tanggal": {
                        "type": "string",
                        "description": "Tanggal format YYYY-MM-DD. Kosongkan untuk hari ini.",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="tambah_agenda",
            description="Tambah kegiatan baru ke agenda kantor.",
            inputSchema={
                "type": "object",
                "properties": {
                    "judul":    {"type": "string", "description": "Nama/judul kegiatan"},
                    "tanggal":  {"type": "string", "description": "Tanggal YYYY-MM-DD"},
                    "jam":      {"type": "string", "description": "Jam mulai, misal '09:00'"},
                    "jenis":    {
                        "type": "string",
                        "description": "Jenis kegiatan",
                        "enum": JENIS_AGENDA,
                    },
                    "lokasi":   {"type": "string", "description": "Lokasi kegiatan (opsional)"},
                    "catatan":  {"type": "string", "description": "Catatan tambahan (opsional)"},
                    "penanggung_jawab": {
                        "type": "string",
                        "description": "Nama PJ/penyuluh yang bertugas (opsional)",
                    },
                },
                "required": ["judul", "tanggal", "jam", "jenis"],
            },
        ),
        types.Tool(
            name="agenda_minggu_ini",
            description="Tampilkan semua agenda dalam 7 hari ke depan.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="hapus_agenda",
            description="Hapus atau batalkan kegiatan berdasarkan ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id_agenda": {"type": "string", "description": "ID agenda yang akan dihapus"},
                },
                "required": ["id_agenda"],
            },
        ),

        # ── MAGANG ───────────────────────────────────────────────────────────
        types.Tool(
            name="daftar_mahasiswa_magang",
            description="Lihat semua mahasiswa magang, bisa filter berdasarkan status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter status magang. Kosongkan untuk semua.",
                        "enum": ["semua"] + STATUS_MAGANG,
                        "default": "semua",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="tambah_mahasiswa_magang",
            description="Daftarkan mahasiswa magang baru ke sistem.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nama":          {"type": "string", "description": "Nama lengkap mahasiswa"},
                    "universitas":   {"type": "string", "description": "Nama universitas/politeknik"},
                    "jurusan":       {"type": "string", "description": "Jurusan/prodi"},
                    "tanggal_mulai": {"type": "string", "description": "Tanggal mulai magang YYYY-MM-DD"},
                    "tanggal_selesai": {"type": "string", "description": "Tanggal selesai magang YYYY-MM-DD"},
                    "pembimbing":    {"type": "string", "description": "Nama pembimbing lapangan (opsional)"},
                    "topik":         {"type": "string", "description": "Topik/judul magang (opsional)"},
                },
                "required": ["nama", "universitas", "jurusan", "tanggal_mulai", "tanggal_selesai"],
            },
        ),
        types.Tool(
            name="update_mahasiswa",
            description="Perbarui status atau tambah catatan progres mahasiswa magang.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nama":    {"type": "string", "description": "Nama mahasiswa (sebagian nama boleh)"},
                    "status":  {
                        "type": "string",
                        "description": "Status baru (opsional)",
                        "enum": STATUS_MAGANG,
                    },
                    "catatan": {"type": "string", "description": "Catatan progres (opsional)"},
                    "nilai":   {"type": "string", "description": "Nilai akhir jika sudah selesai (opsional)"},
                },
                "required": ["nama"],
            },
        ),
        types.Tool(
            name="magang_selesai_bulan_ini",
            description="Cek mahasiswa yang masa magangnya berakhir bulan ini.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),

        # ── PELATIHAN ────────────────────────────────────────────────────────
        types.Tool(
            name="jadwal_pelatihan",
            description="Lihat semua program pelatihan yang terdaftar.",
            inputSchema={
                "type": "object",
                "properties": {
                    "bulan": {
                        "type": "integer",
                        "description": "Filter bulan (1-12). Kosongkan untuk semua.",
                        "minimum": 1,
                        "maximum": 12,
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="tambah_pelatihan",
            description="Daftarkan program pelatihan baru.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nama":           {"type": "string", "description": "Nama program pelatihan"},
                    "tanggal_mulai":  {"type": "string", "description": "Tanggal mulai YYYY-MM-DD"},
                    "tanggal_selesai":{"type": "string", "description": "Tanggal selesai YYYY-MM-DD"},
                    "materi":         {"type": "string", "description": "Topik/materi utama pelatihan"},
                    "target_peserta": {"type": "integer", "description": "Jumlah target peserta"},
                    "lokasi":         {"type": "string", "description": "Lokasi pelaksanaan (opsional)"},
                    "instruktur":     {"type": "string", "description": "Nama instruktur/narasumber (opsional)"},
                    "anggaran":       {"type": "string", "description": "Anggaran kegiatan (opsional)"},
                },
                "required": ["nama", "tanggal_mulai", "tanggal_selesai", "materi", "target_peserta"],
            },
        ),
        types.Tool(
            name="update_pelatihan",
            description="Perbarui jumlah peserta aktual atau status program pelatihan.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nama":            {"type": "string", "description": "Nama pelatihan (sebagian boleh)"},
                    "peserta_aktual":  {"type": "integer", "description": "Jumlah peserta yang benar-benar hadir"},
                    "status":          {
                        "type": "string",
                        "description": "Status pelatihan",
                        "enum": ["dijadwalkan", "berjalan", "selesai", "dibatalkan"],
                    },
                    "catatan":         {"type": "string", "description": "Catatan tambahan"},
                },
                "required": ["nama"],
            },
        ),

        # ── LAPORAN ──────────────────────────────────────────────────────────
        types.Tool(
            name="laporan_bulanan",
            description=(
                "Rekap kegiatan bulan ini: jumlah agenda per jenis, pelatihan yang "
                "dilaksanakan, jumlah peserta, dan magang aktif."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "bulan": {
                        "type": "integer",
                        "description": "Bulan (1-12). Kosongkan untuk bulan ini.",
                        "minimum": 1,
                        "maximum": 12,
                    },
                    "tahun": {
                        "type": "integer",
                        "description": "Tahun. Kosongkan untuk tahun ini.",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="pengingat_besok",
            description="Ringkasan kegiatan esok hari — cocok untuk dikirim via WA malam ini.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


# ── Tool Handlers ─────────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    # ── agenda_hari_ini ───────────────────────────────────────────────────────
    if name == "agenda_hari_ini":
        tgl = arguments.get("tanggal") or _today()
        agenda = _load(AGENDA_F)
        items = [a for a in agenda if a.get("tanggal") == tgl]

        label = "Hari Ini" if tgl == _today() else _fmt_date(tgl)
        if not items:
            return [types.TextContent(type="text",
                text=f"📅 Tidak ada kegiatan terjadwal pada {label}.")]

        items.sort(key=lambda x: x.get("jam", ""))
        lines = [f"📅 *Agenda {label} — Inris Cijeruk*\n"]
        for a in items:
            pj = f"  PJ: {a['penanggung_jawab']}" if a.get("penanggung_jawab") else ""
            lok = f"  📍 {a['lokasi']}" if a.get("lokasi") else ""
            lines.append(
                f"⏰ {a['jam']}  [{a['jenis']}]  {a['judul']}{lok}{pj}"
                + (f"\n   📝 {a['catatan']}" if a.get("catatan") else "")
            )
        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── tambah_agenda ─────────────────────────────────────────────────────────
    elif name == "tambah_agenda":
        agenda = _load(AGENDA_F)
        new_id = f"AGD-{len(agenda)+1:04d}"
        item = {
            "id":                new_id,
            "judul":             arguments["judul"],
            "tanggal":           arguments["tanggal"],
            "jam":               arguments["jam"],
            "jenis":             arguments["jenis"],
            "lokasi":            arguments.get("lokasi", ""),
            "catatan":           arguments.get("catatan", ""),
            "penanggung_jawab":  arguments.get("penanggung_jawab", ""),
            "dibuat_pada":       datetime.now().isoformat(),
        }
        agenda.append(item)
        _save(AGENDA_F, agenda)
        return [types.TextContent(type="text",
            text=(
                f"✅ Agenda ditambahkan [{new_id}]\n"
                f"📌 {item['judul']}\n"
                f"📅 {_fmt_date(item['tanggal'])} jam {item['jam']}\n"
                f"🏷️ Jenis: {item['jenis']}"
            ))]

    # ── agenda_minggu_ini ─────────────────────────────────────────────────────
    elif name == "agenda_minggu_ini":
        agenda = _load(AGENDA_F)
        today  = date.today()
        dates  = [(today + timedelta(days=i)).isoformat() for i in range(7)]
        items  = [a for a in agenda if a.get("tanggal") in dates]

        if not items:
            return [types.TextContent(type="text",
                text="📅 Tidak ada kegiatan dalam 7 hari ke depan.")]

        items.sort(key=lambda x: (x.get("tanggal",""), x.get("jam","")))
        lines = ["📅 *Agenda 7 Hari ke Depan — Inris Cijeruk*\n"]
        cur_date = None
        for a in items:
            if a["tanggal"] != cur_date:
                cur_date = a["tanggal"]
                lines.append(f"\n📆 {_fmt_date(cur_date)}")
            lines.append(f"  {a['jam']}  [{a['jenis']}]  {a['judul']}")
        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── hapus_agenda ──────────────────────────────────────────────────────────
    elif name == "hapus_agenda":
        agenda  = _load(AGENDA_F)
        id_cari = arguments["id_agenda"].upper()
        before  = len(agenda)
        agenda  = [a for a in agenda if a.get("id") != id_cari]
        if len(agenda) == before:
            return [types.TextContent(type="text",
                text=f"Agenda '{id_cari}' tidak ditemukan.")]
        _save(AGENDA_F, agenda)
        return [types.TextContent(type="text",
            text=f"🗑️ Agenda {id_cari} berhasil dihapus.")]

    # ── daftar_mahasiswa_magang ───────────────────────────────────────────────
    elif name == "daftar_mahasiswa_magang":
        magang = _load(MAGANG_F)
        sf     = arguments.get("status", "semua")
        items  = magang if sf == "semua" else [m for m in magang if m.get("status") == sf]

        if not items:
            return [types.TextContent(type="text",
                text=f"Tidak ada data mahasiswa magang{' dengan status '+sf if sf != 'semua' else ''}.")]

        lines = [f"🎓 *Mahasiswa Magang Inris Cijeruk* ({sf}) — {len(items)} orang\n"]
        for m in items:
            selesai_info = f" s/d {_fmt_date(m['tanggal_selesai'])}"
            lines.append(
                f"• {m['nama']}  [{m['status'].upper()}]\n"
                f"  {m['universitas']} / {m['jurusan']}\n"
                f"  Mulai: {_fmt_date(m['tanggal_mulai'])}{selesai_info}"
                + (f"\n  Topik: {m['topik']}" if m.get("topik") else "")
                + (f"\n  Pembimbing: {m['pembimbing']}" if m.get("pembimbing") else "")
            )
        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── tambah_mahasiswa_magang ───────────────────────────────────────────────
    elif name == "tambah_mahasiswa_magang":
        magang  = _load(MAGANG_F)
        new_id  = f"MGG-{len(magang)+1:04d}"
        item = {
            "id":               new_id,
            "nama":             arguments["nama"],
            "universitas":      arguments["universitas"],
            "jurusan":          arguments["jurusan"],
            "tanggal_mulai":    arguments["tanggal_mulai"],
            "tanggal_selesai":  arguments["tanggal_selesai"],
            "pembimbing":       arguments.get("pembimbing", ""),
            "topik":            arguments.get("topik", ""),
            "status":           "dijadwalkan",
            "catatan":          "",
            "nilai":            "",
            "didaftarkan":      datetime.now().isoformat(),
        }
        magang.append(item)
        _save(MAGANG_F, magang)
        return [types.TextContent(type="text",
            text=(
                f"✅ Mahasiswa magang didaftarkan [{new_id}]\n"
                f"👤 {item['nama']}\n"
                f"🏫 {item['universitas']} — {item['jurusan']}\n"
                f"📅 {_fmt_date(item['tanggal_mulai'])} s/d {_fmt_date(item['tanggal_selesai'])}"
            ))]

    # ── update_mahasiswa ──────────────────────────────────────────────────────
    elif name == "update_mahasiswa":
        magang    = _load(MAGANG_F)
        cari      = arguments["nama"].lower()
        matches   = [m for m in magang if cari in m["nama"].lower()]

        if not matches:
            return [types.TextContent(type="text",
                text=f"Mahasiswa dengan nama '{arguments['nama']}' tidak ditemukan.")]
        if len(matches) > 1:
            names = ", ".join(m["nama"] for m in matches)
            return [types.TextContent(type="text",
                text=f"Ditemukan lebih dari 1 mahasiswa: {names}. Harap lebih spesifik.")]

        idx = magang.index(matches[0])
        if "status" in arguments:
            magang[idx]["status"] = arguments["status"]
        if "catatan" in arguments:
            existing = magang[idx].get("catatan", "").strip()
            entry    = f"{_today()}: {arguments['catatan']}"
            magang[idx]["catatan"] = (existing + "\n" + entry).strip()
        if "nilai" in arguments:
            magang[idx]["nilai"] = arguments["nilai"]

        _save(MAGANG_F, magang)
        return [types.TextContent(type="text",
            text=f"✅ Data {magang[idx]['nama']} berhasil diperbarui.")]

    # ── magang_selesai_bulan_ini ──────────────────────────────────────────────
    elif name == "magang_selesai_bulan_ini":
        magang  = _load(MAGANG_F)
        now     = date.today()
        items   = [
            m for m in magang
            if m.get("status") == "aktif"
            and datetime.fromisoformat(m["tanggal_selesai"]).date().year  == now.year
            and datetime.fromisoformat(m["tanggal_selesai"]).date().month == now.month
        ]
        if not items:
            return [types.TextContent(type="text",
                text="Tidak ada mahasiswa magang yang selesai bulan ini.")]

        lines = [f"📋 Magang Berakhir Bulan {now.strftime('%B %Y')}:\n"]
        for m in sorted(items, key=lambda x: x["tanggal_selesai"]):
            lines.append(
                f"• {m['nama']}  ({m['universitas']})\n"
                f"  Selesai: {_fmt_date(m['tanggal_selesai'])}"
                + (f"  Nilai: {m['nilai']}" if m.get("nilai") else "")
            )
        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── jadwal_pelatihan ──────────────────────────────────────────────────────
    elif name == "jadwal_pelatihan":
        pelatihan = _load(LATIH_F)
        bulan     = arguments.get("bulan")
        items     = (
            pelatihan if not bulan
            else [p for p in pelatihan
                  if datetime.fromisoformat(p["tanggal_mulai"]).month == bulan]
        )
        if not items:
            return [types.TextContent(type="text",
                text="Belum ada program pelatihan terdaftar.")]

        items.sort(key=lambda x: x["tanggal_mulai"])
        lines = ["🎯 *Jadwal Pelatihan — Inris Cijeruk*\n"]
        for p in items:
            peserta_info = (
                f"{p.get('peserta_aktual', '?')}/{p['target_peserta']}"
                if p.get("peserta_aktual") else f"Target: {p['target_peserta']}"
            )
            lines.append(
                f"• [{p.get('status','dijadwalkan').upper()}]  {p['nama']}\n"
                f"  📅 {_fmt_date(p['tanggal_mulai'])} s/d {_fmt_date(p['tanggal_selesai'])}\n"
                f"  📚 {p['materi']}  |  👥 Peserta: {peserta_info}"
                + (f"\n  📍 {p['lokasi']}" if p.get("lokasi") else "")
                + (f"\n  🎤 {p['instruktur']}" if p.get("instruktur") else "")
            )
        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── tambah_pelatihan ──────────────────────────────────────────────────────
    elif name == "tambah_pelatihan":
        pelatihan = _load(LATIH_F)
        new_id    = f"PLT-{len(pelatihan)+1:04d}"
        item = {
            "id":               new_id,
            "nama":             arguments["nama"],
            "tanggal_mulai":    arguments["tanggal_mulai"],
            "tanggal_selesai":  arguments["tanggal_selesai"],
            "materi":           arguments["materi"],
            "target_peserta":   arguments["target_peserta"],
            "peserta_aktual":   None,
            "lokasi":           arguments.get("lokasi", ""),
            "instruktur":       arguments.get("instruktur", ""),
            "anggaran":         arguments.get("anggaran", ""),
            "status":           "dijadwalkan",
            "catatan":          "",
            "dibuat_pada":      datetime.now().isoformat(),
        }
        pelatihan.append(item)
        _save(LATIH_F, pelatihan)
        return [types.TextContent(type="text",
            text=(
                f"✅ Pelatihan terdaftar [{new_id}]\n"
                f"📌 {item['nama']}\n"
                f"📅 {_fmt_date(item['tanggal_mulai'])} s/d {_fmt_date(item['tanggal_selesai'])}\n"
                f"📚 {item['materi']}  |  Target peserta: {item['target_peserta']}"
            ))]

    # ── update_pelatihan ──────────────────────────────────────────────────────
    elif name == "update_pelatihan":
        pelatihan = _load(LATIH_F)
        cari      = arguments["nama"].lower()
        matches   = [p for p in pelatihan if cari in p["nama"].lower()]

        if not matches:
            return [types.TextContent(type="text",
                text=f"Pelatihan '{arguments['nama']}' tidak ditemukan.")]
        if len(matches) > 1:
            names = ", ".join(p["nama"] for p in matches)
            return [types.TextContent(type="text",
                text=f"Ditemukan lebih dari 1 pelatihan: {names}. Harap lebih spesifik.")]

        idx = pelatihan.index(matches[0])
        if "peserta_aktual" in arguments:
            pelatihan[idx]["peserta_aktual"] = arguments["peserta_aktual"]
        if "status" in arguments:
            pelatihan[idx]["status"] = arguments["status"]
        if "catatan" in arguments:
            existing = pelatihan[idx].get("catatan", "").strip()
            entry    = f"{_today()}: {arguments['catatan']}"
            pelatihan[idx]["catatan"] = (existing + "\n" + entry).strip()

        _save(LATIH_F, pelatihan)
        return [types.TextContent(type="text",
            text=f"✅ Pelatihan '{pelatihan[idx]['nama']}' berhasil diperbarui.")]

    # ── laporan_bulanan ───────────────────────────────────────────────────────
    elif name == "laporan_bulanan":
        now    = datetime.now()
        bulan  = arguments.get("bulan",  now.month)
        tahun  = arguments.get("tahun",  now.year)
        label  = date(tahun, bulan, 1).strftime("%B %Y")

        agenda    = _load(AGENDA_F)
        magang    = _load(MAGANG_F)
        pelatihan = _load(LATIH_F)

        agenda_bln = [
            a for a in agenda
            if datetime.fromisoformat(a["tanggal"]).month == bulan
            and datetime.fromisoformat(a["tanggal"]).year  == tahun
        ]
        latih_bln = [
            p for p in pelatihan
            if datetime.fromisoformat(p["tanggal_mulai"]).month == bulan
            and datetime.fromisoformat(p["tanggal_mulai"]).year  == tahun
        ]
        magang_aktif = [m for m in magang if m.get("status") == "aktif"]

        jenis_count: dict[str, int] = {}
        for a in agenda_bln:
            j = a.get("jenis", "lainnya")
            jenis_count[j] = jenis_count.get(j, 0) + 1

        total_peserta = sum(
            (p.get("peserta_aktual") or p.get("target_peserta") or 0)
            for p in latih_bln
        )

        lines = [
            f"📊 *Laporan Bulanan Inris Cijeruk — {label}*\n",
            f"📅 Total Kegiatan    : {len(agenda_bln)}",
        ]
        for j, c in sorted(jenis_count.items()):
            lines.append(f"   • {j}: {c}")
        lines += [
            f"\n🎯 Pelatihan         : {len(latih_bln)} program  ({total_peserta} peserta)",
            f"🎓 Magang Aktif      : {len(magang_aktif)} mahasiswa",
        ]
        if latih_bln:
            lines.append("\n📋 Daftar Pelatihan:")
            for p in latih_bln:
                p_act = p.get("peserta_aktual")
                lines.append(f"  • {p['nama']} — {p_act or p['target_peserta']} peserta [{p['status']}]")

        return [types.TextContent(type="text", text="\n".join(lines))]

    # ── pengingat_besok ───────────────────────────────────────────────────────
    elif name == "pengingat_besok":
        besok = (date.today() + timedelta(days=1)).isoformat()
        agenda = _load(AGENDA_F)
        items  = sorted(
            [a for a in agenda if a.get("tanggal") == besok],
            key=lambda x: x.get("jam", ""),
        )
        tgl_label = _fmt_date(besok)

        if not items:
            return [types.TextContent(type="text",
                text=f"📅 Tidak ada kegiatan terjadwal untuk besok ({tgl_label}).")]

        lines = [
            f"🔔 *Pengingat Kegiatan Besok — {tgl_label}*",
            f"📍 Inris Cijeruk\n",
        ]
        for a in items:
            pj  = f" — PJ: {a['penanggung_jawab']}" if a.get("penanggung_jawab") else ""
            lok = f" di {a['lokasi']}" if a.get("lokasi") else ""
            lines.append(f"⏰ {a['jam']}  {a['judul']}{lok}{pj}")
        lines.append(f"\nTotal: {len(items)} kegiatan.")

        return [types.TextContent(type="text", text="\n".join(lines))]

    return [types.TextContent(type="text", text=f"Tool '{name}' tidak dikenal.")]


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
