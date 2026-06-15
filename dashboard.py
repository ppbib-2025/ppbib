"""
Dashboard Monitoring Kualitas Air & Pakan
Instalasi Plasma Nutfah Perikanan Air Tawar Cijeruk
Jalankan: python dashboard.py
"""
import json
import os
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


# ── Data persistence ─────────────────────────────────────────────────────────

def load_data() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"entries": [], "kolam_list": ["Kolam 1", "Kolam 2", "Kolam 3"]}


def save_data(data: dict):
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Assessment engine ─────────────────────────────────────────────────────────

def _grade(key: str, value: float) -> str:
    p = PARAMS.get(key)
    if p is None or value is None:
        return "BAIK"
    lo_k = p["min_kritis"]
    lo_w = p["min_ok"]
    hi_w = p["max_ok"]
    hi_k = p["max_kritis"]
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
        if grade == "KRITIS":
            issues.append({
                "status": "KRITIS",
                "label": p["label"],
                "nilai": f"{val} {p['unit']}".strip(),
                "pesan": _issue_message(key, val, grade),
            })
        elif grade == "PERHATIAN":
            issues.append({
                "status": "PERHATIAN",
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

    recs = _recommendations(entry, issues)
    return {"overall": overall, "grades": grades, "issues": issues, "recommendations": recs}


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
        elif ph > 8.5:
            recs.append("💧 Ganti air 30–40% dengan air segar untuk menurunkan pH.")
            recs.append("🌿 Kurangi pertumbuhan alga berlebih — aerasi dan kurangi paparan sinar matahari.")

    if "DO" in issue_keys:
        recs.append("💨 Aktifkan aerator / kincir air tambahan segera — prioritas utama!")
        recs.append("🐟 Kurangi kepadatan ikan atau pindahkan sebagian ke kolam lain.")
        recs.append("🚫 Hentikan pemberian pakan sementara hingga DO kembali normal (>5 mg/L).")

    if "Suhu" in issue_keys:
        suhu = entry.get("suhu", 27)
        if suhu > 30:
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
        elif kec > 60:
            recs.append("🌱 Air terlalu jernih — pupuk kolam dengan pupuk organik untuk tumbuhkan fitoplankton.")

    if "Feeding Rate" in issue_keys:
        fr = entry.get("feeding_rate", 3)
        if fr > 5:
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


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    data = load_data()
    entries = data.get("entries", [])
    latest = entries[-1] if entries else None
    latest_assess = assess(latest) if latest else None
    kolam_list = data.get("kolam_list", ["Kolam 1"])
    return render_template(
        "aquaculture.html",
        latest=latest,
        assessment=latest_assess,
        kolam_list=kolam_list,
        total_entries=len(entries),
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
        "kolam": body.get("kolam", ""),
        "jenis_ikan": body.get("jenis_ikan", ""),
        # kualitas air
        "ph": _float("ph"),
        "do_level": _float("do_level"),
        "suhu": _float("suhu"),
        "kecerahan": _float("kecerahan"),
        "amonia": _float("amonia"),
        # pakan
        "feeding_rate": _float("feeding_rate"),
        "fcr": _float("fcr"),
        "jumlah_pakan": _float("jumlah_pakan"),
        "biomassa": _float("biomassa"),
        "survival_rate": _float("survival_rate"),
        "padat_tebar": _float("padat_tebar"),
        # catatan
        "catatan": body.get("catatan", ""),
    }

    result = assess(entry)
    entry["assessment"] = result["overall"]

    data = load_data()
    data["entries"].append(entry)
    # Simpan max 500 entri terakhir per kolam agar file tidak membengkak
    if len(data["entries"]) > 500:
        data["entries"] = data["entries"][-500:]
    save_data(data)

    return jsonify({"ok": True, "entry": entry, "assessment": result})


@app.route("/api/data", methods=["GET"])
def get_data():
    kolam = request.args.get("kolam")
    limit = int(request.args.get("limit", 20))
    data = load_data()
    entries = data.get("entries", [])
    if kolam:
        entries = [e for e in entries if e.get("kolam") == kolam]
    entries = entries[-limit:]
    return jsonify(entries)


@app.route("/api/assess", methods=["POST"])
def post_assess():
    body = request.get_json(silent=True) or {}
    result = assess(body)
    return jsonify(result)


@app.route("/api/kolam", methods=["GET"])
def get_kolam():
    data = load_data()
    return jsonify(data.get("kolam_list", []))


@app.route("/api/kolam", methods=["POST"])
def add_kolam():
    body = request.get_json(silent=True) or {}
    nama = body.get("nama", "").strip()
    if not nama:
        return jsonify({"ok": False, "error": "Nama kolam kosong"}), 400
    data = load_data()
    if nama not in data.get("kolam_list", []):
        data.setdefault("kolam_list", []).append(nama)
        save_data(data)
    return jsonify({"ok": True, "kolam_list": data["kolam_list"]})


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
    print("  Buka browser: http://localhost:5050")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5050, debug=True)
