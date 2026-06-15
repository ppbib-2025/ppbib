"""
Dashboard Monitoring Kualitas Air & Pakan
Instalasi Plasma Nutfah Perikanan Air Tawar Cijeruk
Jalankan: python dashboard.py
"""
import json
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder="templates")

DATA_FILE = Path(__file__).parent / "data" / "aquaculture_data.json"

# ── Rentang parameter optimal ────────────────────────────────────────────────

PARAMS = {
    "ph":            {"min_kritis": 5.5, "min_ok": 6.5, "max_ok": 8.5, "max_kritis": 9.5, "unit": "", "label": "pH"},
    "do":            {"min_kritis": 2.0, "min_ok": 5.0, "max_ok": 12.0, "max_kritis": 14.0, "unit": "mg/L", "label": "DO"},
    "suhu":          {"min_kritis": 18,  "min_ok": 25,  "max_ok": 30,   "max_kritis": 35,   "unit": "°C", "label": "Suhu"},
    "kecerahan":     {"min_kritis": 15,  "min_ok": 30,  "max_ok": 60,   "max_kritis": 100,  "unit": "cm", "label": "Kecerahan"},
    "amonia":        {"min_kritis": None,"min_ok": None, "max_ok": 0.02, "max_kritis": 0.05, "unit": "mg/L", "label": "Amonia"},
    "feeding_rate":  {"min_kritis": 1.0, "min_ok": 2.0, "max_ok": 5.0,  "max_kritis": 8.0,  "unit": "%", "label": "Feeding Rate"},
    "fcr":           {"min_kritis": None,"min_ok": None, "max_ok": 1.8,  "max_kritis": 2.5,  "unit": "", "label": "FCR"},
    "survival_rate": {"min_kritis": 60,  "min_ok": 80,  "max_ok": 100,  "max_kritis": 100,  "unit": "%", "label": "Survival Rate"},
}

DEFAULT_BLOK = [
    {"nama": "Blok Depan",   "kolam": ["Kolam D1", "Kolam D2", "Kolam D3", "Kolam D4"]},
    {"nama": "Blok Tengah",  "kolam": ["Kolam T1", "Kolam T2", "Kolam T3", "Kolam T4"]},
    {"nama": "Blok Belakang","kolam": ["Kolam B1", "Kolam B2", "Kolam B3", "Kolam B4"]},
]


# ── Data persistence ──────────────────────────────────────────────────────────

def load_data() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        # Migrasi data lama yang belum punya blok_list
        if "blok_list" not in d:
            d["blok_list"] = DEFAULT_BLOK
            # Pindahkan kolam_list lama ke Blok Umum
            old_kolam = d.pop("kolam_list", [])
            if old_kolam:
                d["blok_list"].insert(0, {"nama": "Blok Umum", "kolam": old_kolam})
        return d
    return {"entries": [], "blok_list": DEFAULT_BLOK}


def save_data(data: dict):
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def all_kolam(data: dict) -> list[str]:
    """Gabungan semua nama kolam dari semua blok."""
    result = []
    for b in data.get("blok_list", []):
        result.extend(b.get("kolam", []))
    return result


# ── Assessment engine ─────────────────────────────────────────────────────────

def _grade(key: str, value: float) -> str:
    p = PARAMS.get(key)
    if p is None or value is None:
        return "BAIK"
    lo_k, lo_w, hi_w, hi_k = p["min_kritis"], p["min_ok"], p["max_ok"], p["max_kritis"]
    if (lo_k is not None and value < lo_k) or (hi_k is not None and value > hi_k):
        return "KRITIS"
    if (lo_w is not None and value < lo_w) or (hi_w is not None and value > hi_w):
        return "PERHATIAN"
    return "BAIK"


def assess(entry: dict) -> dict:
    grades = {}
    issues = []
    check_fields = {
        "ph": entry.get("ph"),
        "do": entry.get("do_level"),
        "suhu": entry.get("suhu"),
        "kecerahan": entry.get("kecerahan"),
        "amonia": entry.get("amonia"),
        "feeding_rate": entry.get("feeding_rate"),
        "fcr": entry.get("fcr"),
        "survival_rate": entry.get("survival_rate"),
    }
    for key, val in check_fields.items():
        if val is None:
            continue
        grade = _grade(key, val)
        grades[key] = grade
        p = PARAMS[key]
        if grade in ("KRITIS", "PERHATIAN"):
            issues.append({
                "status": grade,
                "label": p["label"],
                "nilai": f"{val} {p['unit']}".strip(),
                "pesan": _issue_message(key, val, grade),
            })

    if any(g == "KRITIS" for g in grades.values()):
        overall = "KRITIS"
    elif any(g == "PERHATIAN" for g in grades.values()):
        overall = "PERHATIAN"
    else:
        overall = "BAIK"

    return {"overall": overall, "grades": grades, "issues": issues,
            "recommendations": _recommendations(entry, issues)}


def _issue_message(key: str, val: float, grade: str) -> str:
    p = PARAMS[key]
    u = p["unit"]
    msgs = {
        "ph": {
            "KRITIS":    f"pH {val} sangat berbahaya! Ikan akan stres berat. Rentang aman: 6.5–8.5",
            "PERHATIAN": f"pH {val} di luar rentang optimal (6.5–8.5). Perlu penyesuaian segera.",
        },
        "do": {
            "KRITIS":    f"DO {val} {u} — ikan berisiko mati lemas! Segera aerasi maksimal.",
            "PERHATIAN": f"DO {val} {u} di bawah optimal (>5 mg/L). Tingkatkan aerasi.",
        },
        "suhu": {
            "KRITIS":    f"Suhu {val}{u} ekstrem! Metabolisme ikan terganggu. Optimal: 25–30°C",
            "PERHATIAN": f"Suhu {val}{u} sedikit di luar rentang optimal (25–30°C).",
        },
        "kecerahan": {
            "KRITIS":    f"Kecerahan {val} {u} abnormal. Cek kualitas air secara menyeluruh.",
            "PERHATIAN": f"Kecerahan {val} {u} di luar rentang ideal (30–60 cm).",
        },
        "amonia": {
            "KRITIS":    f"Amonia {val} {u} sangat toksik! Lakukan ganti air segera.",
            "PERHATIAN": f"Amonia {val} {u} mendekati batas bahaya (>0.02 mg/L).",
        },
        "feeding_rate": {
            "KRITIS":    f"Feeding rate {val}{u} jauh dari normal. Hitung ulang dosis pakan.",
            "PERHATIAN": f"Feeding rate {val}{u} perlu disesuaikan (optimal 2–5% bobot tubuh).",
        },
        "fcr": {
            "KRITIS":    f"FCR {val} sangat buruk! Efisiensi pakan rendah sekali. Target: <1.8",
            "PERHATIAN": f"FCR {val} kurang efisien (optimal 1.0–1.8). Evaluasi kualitas pakan.",
        },
        "survival_rate": {
            "KRITIS":    f"Survival rate {val}{u} sangat rendah! Investigasi penyakit/kematian massal.",
            "PERHATIAN": f"Survival rate {val}{u} di bawah target (>85%). Pantau lebih ketat.",
        },
    }
    return msgs.get(key, {}).get(grade, "Parameter di luar rentang normal.")


def _recommendations(entry: dict, issues: list) -> list:
    recs = []
    issue_keys = {i["label"] for i in issues}
    statuses = {i["label"]: i["status"] for i in issues}

    if "pH" in issue_keys:
        ph = entry.get("ph", 7)
        if ph < 6.5:
            recs.append("🪨 Taburkan kapur pertanian (CaCO₃) 10–20 kg/ha untuk menaikkan pH secara bertahap.")
            recs.append("🔄 Lakukan partial water change 20–30% dengan air pH netral.")
        else:
            recs.append("💧 Ganti air 30–40% dengan air segar untuk menurunkan pH.")
            recs.append("🌿 Kurangi pertumbuhan alga berlebih — aerasi dan kurangi paparan sinar matahari.")

    if "DO" in issue_keys:
        recs.append("💨 Aktifkan aerator / kincir air tambahan segera — prioritas utama!")
        recs.append("🐟 Kurangi kepadatan ikan atau pindahkan sebagian ke kolam lain.")
        recs.append("🚫 Hentikan pemberian pakan sementara hingga DO kembali normal (>5 mg/L).")

    if "Suhu" in issue_keys:
        if entry.get("suhu", 27) > 30:
            recs.append("⛱️ Pasang paranet 60–70% untuk mengurangi intensitas sinar matahari.")
            recs.append("🌊 Tambah debit air masuk — air baru biasanya lebih dingin.")
            recs.append("⏰ Beri pakan di pagi hari (06:00–07:00) saat suhu masih rendah.")
        else:
            recs.append("🌡️ Kurangi debit air masuk atau pasang plastik UV pada malam hari.")

    if "Amonia" in issue_keys:
        if statuses.get("Amonia") == "KRITIS":
            recs.append("🚨 DARURAT: Ganti air 50% segera. Hentikan pemberian pakan 24 jam.")
        recs.append("🧹 Sifon dasar kolam untuk membuang sisa pakan dan kotoran ikan.")
        recs.append("🦠 Pertimbangkan aplikasi probiotik untuk mempercepat nitrifikasi.")

    if "Kecerahan" in issue_keys:
        kec = entry.get("kecerahan", 40)
        if kec < 30:
            recs.append("🔬 Air terlalu keruh — cek curah hujan, erosi, atau bloom fitoplankton.")
            recs.append("🌊 Lakukan water change 30% dan kurangi pemberian pakan 24 jam.")
        else:
            recs.append("🌱 Air terlalu jernih — pupuk kolam dengan pupuk organik untuk tumbuhkan fitoplankton.")

    if "Feeding Rate" in issue_keys:
        if entry.get("feeding_rate", 3) > 5:
            recs.append("📊 Lakukan sampling biomassa (timbang 30 ekor sampel) untuk hitung ulang dosis pakan.")
            recs.append("⬇️ Kurangi dosis pakan 20% dan pantau nafsu makan ikan.")
        else:
            recs.append("📊 Update data biomassa ikan — kemungkinan pertumbuhan lebih cepat dari estimasi.")

    if "FCR" in issue_keys:
        recs.append("🔍 Evaluasi kualitas pakan: cek kadar protein, tanggal kadaluarsa, dan cara penyimpanan.")
        recs.append("⏱️ Beri pakan 3×/hari dengan dosis terbagi — pantau sisa pakan 30 menit setelah pemberian.")
        recs.append("🧹 Bersihkan sisa pakan dari kolam setiap hari untuk cegah pembusukan.")

    if "Survival Rate" in issue_keys:
        recs.append("🏥 Lakukan pemeriksaan klinis: periksa insang, sisik, dan perilaku renang ikan.")
        recs.append("🔬 Ambil sampel ikan mati untuk identifikasi patogen di laboratorium.")
        recs.append("📋 Karantina ikan baru sebelum masuk kolam utama (min. 14 hari).")

    if not issues:
        recs.append("✅ Semua parameter dalam kondisi prima! Pertahankan manajemen budidaya saat ini.")
        recs.append("📋 Jadwalkan sampling pertumbuhan minggu depan untuk update FCR dan biomassa.")

    return recs


# ── Blok summary helper ───────────────────────────────────────────────────────

def blok_summary(data: dict) -> list[dict]:
    """Status terbaru per blok berdasarkan entri terakhir masing-masing kolam."""
    entries = data.get("entries", [])
    blok_list = data.get("blok_list", [])

    # Cari entri terakhir per (blok, kolam)
    latest_per_kolam: dict[str, dict] = {}
    for e in entries:
        key = f"{e.get('blok','')}|{e.get('kolam','')}"
        latest_per_kolam[key] = e

    result = []
    ORDER = {"KRITIS": 0, "PERHATIAN": 1, "BAIK": 2, "NODATA": 3}
    for blok in blok_list:
        nama = blok["nama"]
        kolam_statuses = []
        kolam_details = []
        for k in blok.get("kolam", []):
            key = f"{nama}|{k}"
            entry = latest_per_kolam.get(key)
            if entry:
                a = assess(entry)
                st = a["overall"]
                ts = entry.get("timestamp", "")
            else:
                st = "NODATA"
                ts = ""
            kolam_statuses.append(st)
            kolam_details.append({"kolam": k, "status": st, "timestamp": ts})

        # Blok status = status terburuk kolam-kolamnya
        worst = min(kolam_statuses, key=lambda s: ORDER.get(s, 9)) if kolam_statuses else "NODATA"
        result.append({
            "nama": nama,
            "status": worst,
            "kolam_count": len(blok.get("kolam", [])),
            "kritis_count": kolam_statuses.count("KRITIS"),
            "perhatian_count": kolam_statuses.count("PERHATIAN"),
            "baik_count": kolam_statuses.count("BAIK"),
            "nodata_count": kolam_statuses.count("NODATA"),
            "kolam": kolam_details,
        })
    return result


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    data = load_data()
    entries = data.get("entries", [])
    latest = entries[-1] if entries else None
    latest_assess = assess(latest) if latest else None
    return render_template(
        "aquaculture.html",
        latest=latest,
        assessment=latest_assess,
        blok_list=data.get("blok_list", []),
        blok_summary=blok_summary(data),
        total_entries=len(entries),
        active_blok=None,
    )


@app.route("/blok/<nama>")
def blok_view(nama: str):
    """Tampilan khusus satu blok — bisa di-bookmark oleh petugas blok tsb."""
    data = load_data()
    entries = data.get("entries", [])
    blok_entries = [e for e in entries if e.get("blok") == nama]
    latest = blok_entries[-1] if blok_entries else None
    latest_assess = assess(latest) if latest else None
    return render_template(
        "aquaculture.html",
        latest=latest,
        assessment=latest_assess,
        blok_list=data.get("blok_list", []),
        blok_summary=blok_summary(data),
        total_entries=len(blok_entries),
        active_blok=nama,
    )


@app.route("/api/data", methods=["POST"])
def post_data():
    body = request.get_json(silent=True) or {}
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def _float(key):
        v = body.get(key)
        try:
            return float(v) if v not in (None, "", "null") else None
        except (ValueError, TypeError):
            return None

    entry = {
        "timestamp": now,
        "blok": body.get("blok", ""),
        "kolam": body.get("kolam", ""),
        "petugas": body.get("petugas", ""),
        "jenis_ikan": body.get("jenis_ikan", ""),
        "ph": _float("ph"),
        "do_level": _float("do_level"),
        "suhu": _float("suhu"),
        "kecerahan": _float("kecerahan"),
        "amonia": _float("amonia"),
        "feeding_rate": _float("feeding_rate"),
        "fcr": _float("fcr"),
        "jumlah_pakan": _float("jumlah_pakan"),
        "biomassa": _float("biomassa"),
        "survival_rate": _float("survival_rate"),
        "padat_tebar": _float("padat_tebar"),
        "catatan": body.get("catatan", ""),
    }

    result = assess(entry)
    entry["assessment"] = result["overall"]

    data = load_data()
    data["entries"].append(entry)
    if len(data["entries"]) > 1000:
        data["entries"] = data["entries"][-1000:]
    save_data(data)

    return jsonify({"ok": True, "entry": entry, "assessment": result,
                    "blok_summary": blok_summary(data)})


@app.route("/api/data", methods=["GET"])
def get_data():
    blok  = request.args.get("blok")
    kolam = request.args.get("kolam")
    limit = int(request.args.get("limit", 30))
    data  = load_data()
    entries = data.get("entries", [])
    if blok:
        entries = [e for e in entries if e.get("blok") == blok]
    if kolam:
        entries = [e for e in entries if e.get("kolam") == kolam]
    return jsonify(entries[-limit:])


@app.route("/api/summary", methods=["GET"])
def get_summary():
    data = load_data()
    return jsonify(blok_summary(data))


@app.route("/api/blok", methods=["GET"])
def get_blok():
    data = load_data()
    return jsonify(data.get("blok_list", []))


@app.route("/api/blok", methods=["POST"])
def add_blok():
    body = request.get_json(silent=True) or {}
    nama = body.get("nama", "").strip()
    if not nama:
        return jsonify({"ok": False, "error": "Nama blok kosong"}), 400
    data = load_data()
    blok_list = data.get("blok_list", [])
    if any(b["nama"] == nama for b in blok_list):
        return jsonify({"ok": False, "error": "Blok sudah ada"}), 400
    blok_list.append({"nama": nama, "kolam": []})
    data["blok_list"] = blok_list
    save_data(data)
    return jsonify({"ok": True, "blok_list": blok_list})


@app.route("/api/blok/<nama>/kolam", methods=["POST"])
def add_kolam_to_blok(nama: str):
    body = request.get_json(silent=True) or {}
    kolam_nama = body.get("kolam", "").strip()
    if not kolam_nama:
        return jsonify({"ok": False, "error": "Nama kolam kosong"}), 400
    data = load_data()
    for blok in data.get("blok_list", []):
        if blok["nama"] == nama:
            if kolam_nama not in blok["kolam"]:
                blok["kolam"].append(kolam_nama)
            save_data(data)
            return jsonify({"ok": True, "blok": blok})
    return jsonify({"ok": False, "error": "Blok tidak ditemukan"}), 404


@app.route("/api/delete/<int:idx>", methods=["DELETE"])
def delete_entry(idx: int):
    data = load_data()
    entries = data.get("entries", [])
    if 0 <= idx < len(entries):
        entries.pop(idx)
        data["entries"] = entries
        save_data(data)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Index tidak valid"}), 404


if __name__ == "__main__":
    print("=" * 60)
    print("  Dashboard Plasma Nutfah Perikanan Air Tawar Cijeruk")
    print("  Buka browser : http://localhost:5050")
    print("  Per blok     : http://localhost:5050/blok/Blok%20A")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5050, debug=True)
