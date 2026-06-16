"""
Dashboard analytics PPBIB — bisa dibuka di browser kapan saja.
Routes:
  GET  /                       -> status bot
  GET  /analytics              -> tabel performa konten semua platform
  GET  /analytics/refresh      -> trigger collect metrics, redirect ke /analytics
  GET  /setup                  -> halaman setup token OAuth
  GET  /setup/tiktok           -> mulai OAuth TikTok
  GET  /setup/tiktok/callback  -> callback dari TikTok OAuth
  GET  /terms                  -> halaman syarat & ketentuan
  GET  /privacy                -> halaman kebijakan privasi
"""
import json
import os
import threading
from datetime import datetime
from flask import Flask, redirect, request

app = Flask(__name__)

TIKTOK_FILE   = "data/analytics_tiktok.json"
IG_FILE        = "data/analytics_instagram.json"
FB_FILE        = "data/analytics_facebook.json"
STRATEGY_FILE  = "data/strategy_insights.json"
REFRESH_FLAG   = "data/.refresh_running"


def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def _er_class(er: float) -> str:
    if er >= 3:
        return "er-high"
    if er >= 1:
        return "er-mid"
    return "er-low"


def _num(n: int) -> str:
    return f"{n:,}"


BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f4f4;color:#222}
.hdr{background:#1a1a2e;color:#fff;padding:18px 24px;display:flex;align-items:center;justify-content:space-between}
.hdr h1{font-size:18px;font-weight:700}
.hdr p{font-size:12px;opacity:.6;margin-top:3px}
.hdr-links a{color:#a5b4fc;font-size:13px;text-decoration:none;margin-left:16px}
.wrap{max-width:1100px;margin:0 auto;padding:20px}
.card{background:#fff;border-radius:10px;padding:18px 20px;margin-bottom:18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.card h2{font-size:14px;font-weight:700;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid #eee}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;padding:7px 9px;background:#f8f8f8;font-weight:600;color:#555;border-bottom:2px solid #e8e8e8}
td{padding:7px 9px;border-bottom:1px solid #f0f0f0;vertical-align:top}
tr:last-child td{border:none}
.er{font-weight:700}
.er-high{color:#16a34a}
.er-mid{color:#d97706}
.er-low{color:#dc2626}
.badge{display:inline-block;padding:1px 6px;border-radius:4px;font-size:11px;font-weight:600;background:#e0e7ff;color:#4338ca}
.empty{color:#999;font-size:13px;padding:6px 0}
.strat{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:13px;font-size:13px;line-height:1.7}
.meta{font-size:11px;color:#777;margin-bottom:8px}
ul{margin-left:18px;margin-top:4px}
li{margin-bottom:3px}
.btn{display:inline-block;padding:10px 20px;border-radius:8px;font-size:14px;font-weight:600;text-decoration:none;cursor:pointer;border:none}
.btn-primary{background:#1a1a2e;color:#fff}
.btn-tiktok{background:#000;color:#fff}
.btn-refresh{background:#059669;color:#fff}
.alert{padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:13px}
.alert-ok{background:#d1fae5;border:1px solid #6ee7b7;color:#065f46}
.alert-err{background:#fee2e2;border:1px solid #fca5a5;color:#991b1b}
.alert-info{background:#e0f2fe;border:1px solid #7dd3fc;color:#075985}
p{line-height:1.7}
h3{margin:20px 0 8px}
"""


def _page(title: str, body: str, refresh_secs: int = 0) -> str:
    refresh_tag = f'<meta http-equiv="refresh" content="{refresh_secs}">' if refresh_secs else ""
    now_str = datetime.now().strftime("%d %b %Y %H:%M")
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
{refresh_tag}
<title>{title}</title>
<style>{BASE_CSS}</style>
</head>
<body>
<div class="hdr">
  <div>
    <h1>&#128202; PPBIB Analytics Dashboard</h1>
    <p>Update terakhir: {now_str}</p>
  </div>
  <div class="hdr-links">
    <a href="/analytics">Analytics</a>
    <a href="/setup">Setup Token</a>
    <a href="/analytics/refresh">&#128260; Refresh</a>
  </div>
</div>
<div class="wrap">{body}</div>
</body></html>"""


@app.route("/")
def home():
    body = """
    <div class="card">
      <h2>&#127774; Status Bot</h2>
      <p style="font-size:14px;margin-bottom:16px">PPBIB Bot aktif &#9989;</p>
      <a href="/analytics" class="btn btn-primary" style="margin-right:8px">Lihat Analytics</a>
      <a href="/setup" class="btn" style="background:#6366f1;color:#fff">Setup Token OAuth</a>
    </div>
    """
    return _page("PPBIB Bot", body)


@app.route("/analytics")
def analytics():
    is_refreshing = os.path.exists(REFRESH_FLAG)

    tiktok_rows = []
    for vid_id, d in _load(TIKTOK_FILE).items():
        snaps = d.get("snapshots", [])
        if not snaps:
            continue
        s = snaps[-1]
        views    = s.get("view_count", 0)
        likes    = s.get("like_count", 0)
        comments = s.get("comment_count", 0)
        shares   = s.get("share_count", 0)
        er = round((likes + comments + shares) / max(views, 1) * 100, 2)
        tiktok_rows.append({
            "title":    (d.get("title") or d.get("description", ""))[:65] or "(tanpa judul)",
            "views":    views, "likes": likes, "comments": comments,
            "shares":   shares, "er": er,
        })
    tiktok_rows.sort(key=lambda x: x["er"], reverse=True)

    ig_rows = []
    for pid, d in _load(IG_FILE).items():
        snaps = d.get("snapshots", [])
        if not snaps:
            continue
        s = snaps[-1]
        likes    = s.get("like_count", 0)
        comments = s.get("comments_count", 0)
        impr     = s.get("impressions", 0)
        er = round((likes + comments) / max(impr, 1) * 100, 2)
        ig_rows.append({
            "caption":     (d.get("caption", ""))[:65] or "(tanpa caption)",
            "media_type":  d.get("media_type", "IMAGE"),
            "likes": likes, "comments": comments, "impressions": impr, "er": er,
        })
    ig_rows.sort(key=lambda x: x["er"], reverse=True)

    fb_rows = []
    for pid, d in _load(FB_FILE).items():
        snaps = d.get("snapshots", [])
        if not snaps:
            continue
        s = snaps[-1]
        likes    = s.get("like_count", 0)
        comments = s.get("comment_count", 0)
        shares   = s.get("share_count", 0)
        impr     = s.get("impressions", 0)
        er = round((likes + comments + shares) / max(impr, 1) * 100, 2)
        fb_rows.append({
            "message": (d.get("message", ""))[:65] or "(tanpa pesan)",
            "likes": likes, "comments": comments, "shares": shares,
            "impressions": impr, "er": er,
        })
    fb_rows.sort(key=lambda x: x["er"], reverse=True)

    strategy = _load(STRATEGY_FILE)

    def _table_tiktok(rows):
        if not rows:
            return '<p class="empty">Belum ada data. <a href="/setup">Setup token TikTok</a> lalu klik Refresh.</p>'
        h  = '<table><thead><tr><th>#</th><th>Konten</th><th>Views</th><th>Likes</th>'
        h += '<th>Komentar</th><th>Share</th><th>ER%</th></tr></thead><tbody>'
        for i, r in enumerate(rows[:15], 1):
            ec = _er_class(r["er"])
            h += (f'<tr><td style="color:#aaa">{i}</td><td>{r["title"]}</td>'
                  f'<td>{_num(r["views"])}</td><td>{_num(r["likes"])}</td>'
                  f'<td>{_num(r["comments"])}</td><td>{_num(r["shares"])}</td>'
                  f'<td class="er {ec}">{r["er"]}%</td></tr>')
        return h + '</tbody></table>'

    def _table_ig(rows):
        if not rows:
            return '<p class="empty">Belum ada data. Token Instagram belum di-setup.</p>'
        h  = '<table><thead><tr><th>#</th><th>Konten</th><th>Tipe</th><th>Likes</th>'
        h += '<th>Komentar</th><th>Impresi</th><th>ER%</th></tr></thead><tbody>'
        for i, r in enumerate(rows[:15], 1):
            ec = _er_class(r["er"])
            h += (f'<tr><td style="color:#aaa">{i}</td><td>{r["caption"]}</td>'
                  f'<td><span class="badge">{r["media_type"]}</span></td>'
                  f'<td>{_num(r["likes"])}</td><td>{_num(r["comments"])}</td>'
                  f'<td>{_num(r["impressions"])}</td>'
                  f'<td class="er {ec}">{r["er"]}%</td></tr>')
        return h + '</tbody></table>'

    def _table_fb(rows):
        if not rows:
            return '<p class="empty">Belum ada data Facebook.</p>'
        h  = '<table><thead><tr><th>#</th><th>Konten</th><th>Likes</th>'
        h += '<th>Komentar</th><th>Share</th><th>Impresi</th><th>ER%</th></tr></thead><tbody>'
        for i, r in enumerate(rows[:15], 1):
            ec = _er_class(r["er"])
            h += (f'<tr><td style="color:#aaa">{i}</td><td>{r["message"]}</td>'
                  f'<td>{_num(r["likes"])}</td><td>{_num(r["comments"])}</td>'
                  f'<td>{_num(r["shares"])}</td><td>{_num(r["impressions"])}</td>'
                  f'<td class="er {ec}">{r["er"]}%</td></tr>')
        return h + '</tbody></table>'

    refresh_banner = ""
    refresh_secs = 0
    if is_refreshing:
        refresh_banner = '<div class="alert alert-info">&#9203; Sedang mengambil data terbaru... halaman akan refresh otomatis.</div>'
        refresh_secs = 4

    body = refresh_banner
    body += f'<div class="card"><h2>&#127916; TikTok</h2>{_table_tiktok(tiktok_rows)}</div>'
    body += f'<div class="card"><h2 style="color:#C13584">&#128247; Instagram</h2>{_table_ig(ig_rows)}</div>'
    body += f'<div class="card"><h2 style="color:#1877F2">&#128216; Facebook</h2>{_table_fb(fb_rows)}</div>'

    body += '<div class="card"><h2>&#128300; Auto Research'
    if strategy:
        iteration = strategy.get("iteration", "-")
        week      = strategy.get("week_analyzed", "-")
        strat_txt = strategy.get("strategy_prompt", "-")
        patterns  = strategy.get("top_performing_patterns", {})
        body += f' &mdash; Iterasi #{iteration}</h2>'
        body += f'<p class="meta">Analisis pekan {week}</p>'
        body += f'<div class="strat">{strat_txt}</div>'
        if patterns.get("winning_topics"):
            body += '<p style="margin-top:12px;font-size:13px"><strong>&#9989; Topik pemenang:</strong></p><ul>'
            for t in patterns["winning_topics"]:
                body += f'<li style="font-size:13px">{t}</li>'
            body += '</ul>'
        if patterns.get("avoid_patterns"):
            body += '<p style="margin-top:10px;font-size:13px"><strong>&#10060; Hindari:</strong></p><ul>'
            for t in patterns["avoid_patterns"]:
                body += f'<li style="font-size:13px">{t}</li>'
            body += '</ul>'
    else:
        body += '</h2><p class="empty">Auto research belum pernah jalan. Akan berjalan otomatis tiap Sabtu 17:00.</p>'
    body += '</div>'

    return _page("PPBIB Analytics", body, refresh_secs=refresh_secs)


@app.route("/analytics/refresh")
def analytics_refresh():
    if os.path.exists(REFRESH_FLAG):
        return redirect("/analytics")
    os.makedirs("data", exist_ok=True)
    open(REFRESH_FLAG, "w").close()

    def _do_refresh():
        try:
            from src.analytics import (
                collect_tiktok_metrics,
                collect_instagram_metrics,
                collect_facebook_metrics,
            )
            try:
                collect_tiktok_metrics()
            except Exception as e:
                print(f"[Refresh] TikTok error: {e}")
            try:
                collect_instagram_metrics()
            except Exception as e:
                print(f"[Refresh] Instagram error: {e}")
            try:
                collect_facebook_metrics()
            except Exception as e:
                print(f"[Refresh] Facebook error: {e}")
        finally:
            if os.path.exists(REFRESH_FLAG):
                os.remove(REFRESH_FLAG)

    threading.Thread(target=_do_refresh, daemon=True).start()
    return redirect("/analytics")


@app.route("/setup")
def setup():
    from src.tiktok_auth import load_token as tiktok_load
    tk_ok = tiktok_load() is not None
    tk_status = '&#9989; Token aktif' if tk_ok else '&#10060; Belum ada token'
    tk_btn_label = 'Perbarui Token TikTok' if tk_ok else 'Hubungkan TikTok'

    tiktok_key    = os.getenv("TIKTOK_CLIENT_KEY", "")
    tiktok_secret = os.getenv("TIKTOK_CLIENT_SECRET", "")
    tiktok_redir  = os.getenv("TIKTOK_REDIRECT_URI", "")

    if not tiktok_key or not tiktok_secret or not tiktok_redir:
        env_warn = '<div class="alert alert-err">&#9888; Env vars TikTok belum diset di Railway: <code>TIKTOK_CLIENT_KEY</code>, <code>TIKTOK_CLIENT_SECRET</code>, <code>TIKTOK_REDIRECT_URI</code></div>'
    else:
        env_warn = '<div class="alert alert-ok">&#9989; Env vars TikTok sudah diset.</div>'

    body = f"""
    <div class="card">
      <h2>&#128273; Setup Token OAuth</h2>
      <p style="font-size:13px;color:#555;margin-bottom:20px">Hubungkan akun media sosial untuk mengambil data analytics.</p>

      <h3 style="font-size:13px;font-weight:700;margin-bottom:10px">&#127916; TikTok</h3>
      {env_warn}
      <p style="font-size:13px;margin-bottom:12px">Status: {tk_status}</p>
      <a href="/setup/tiktok" class="btn btn-tiktok">&#9654; {tk_btn_label}</a>
    </div>
    <div class="card">
      <h2>&#128247; Instagram / Facebook</h2>
      <p style="font-size:13px;color:#555">Setup Instagram dan Facebook menggunakan Facebook OAuth. Panduan akan ditambahkan di langkah berikutnya.</p>
    </div>
    """
    return _page("Setup Token", body)


@app.route("/setup/tiktok")
def setup_tiktok():
    from src.tiktok_auth import get_auth_url
    try:
        url = get_auth_url()
        return redirect(url)
    except Exception as e:
        body = f'<div class="card"><div class="alert alert-err">Error: {e}<br><br>Pastikan env vars <code>TIKTOK_CLIENT_KEY</code>, <code>TIKTOK_CLIENT_SECRET</code>, dan <code>TIKTOK_REDIRECT_URI</code> sudah diset di Railway.</div></div>'
        return _page("TikTok OAuth Error", body)


@app.route("/setup/tiktok/callback")
def setup_tiktok_callback():
    code       = request.args.get("code", "")
    error      = request.args.get("error", "")
    error_desc = request.args.get("error_description", "")

    if error:
        body = f'<div class="card"><div class="alert alert-err"><strong>TikTok error:</strong> {error}<br>{error_desc}</div><p style="margin-top:12px"><a href="/setup">Coba lagi</a></p></div>'
        return _page("TikTok OAuth Gagal", body)

    if not code:
        body = '<div class="card"><div class="alert alert-err">Tidak ada kode dari TikTok.</div><p style="margin-top:12px"><a href="/setup">Coba lagi</a></p></div>'
        return _page("TikTok OAuth Gagal", body)

    from src.tiktok_auth import exchange_code_for_token
    result = exchange_code_for_token(code)

    if "data" in result and "access_token" in result.get("data", {}):
        body = """
        <div class="card">
          <div class="alert alert-ok">&#9989; Token TikTok berhasil disimpan!</div>
          <p style="font-size:13px;margin-top:12px">Sekarang kamu bisa klik <strong>Refresh</strong> untuk mengambil data video TikTok.</p>
          <p style="margin-top:16px">
            <a href="/analytics" class="btn btn-primary" style="margin-right:8px">Ke Analytics</a>
            <a href="/analytics/refresh" class="btn btn-refresh">Refresh Data Sekarang</a>
          </p>
        </div>
        """
        return _page("TikTok Terhubung!", body)
    else:
        err_msg = json.dumps(result, indent=2)
        body = f'<div class="card"><div class="alert alert-err"><strong>Gagal tukar token:</strong><br><pre style="font-size:11px;margin-top:8px;overflow:auto">{err_msg}</pre></div><p style="margin-top:12px"><a href="/setup">Coba lagi</a></p></div>'
        return _page("TikTok OAuth Gagal", body)


@app.route("/terms")
def terms():
    body = """
    <div class="card" style="max-width:780px">
      <h2>Syarat &amp; Ketentuan Penggunaan</h2>
      <p class="meta">Terakhir diperbarui: Juni 2026</p>

      <h3>1. Tentang Layanan</h3>
      <p>PPBIB Analytics adalah platform internal untuk mengelola dan menganalisis performa konten media sosial milik PPBIB (Persatuan Pedagang Batik Indonesia Bangkalan). Layanan ini hanya digunakan oleh tim internal PPBIB.</p>

      <h3>2. Penggunaan Data</h3>
      <p>Platform ini mengakses data performa konten (views, likes, komentar, share) dari akun TikTok, Instagram, dan Facebook resmi PPBIB untuk keperluan analisis internal. Data tidak dibagikan kepada pihak ketiga.</p>

      <h3>3. Akses dan Izin</h3>
      <p>Akses ke platform ini terbatas hanya untuk anggota tim resmi PPBIB. Pengguna bertanggung jawab untuk menjaga kerahasiaan kredensial akses mereka.</p>

      <h3>4. Batasan Tanggung Jawab</h3>
      <p>PPBIB tidak bertanggung jawab atas gangguan layanan yang disebabkan oleh pihak ketiga (TikTok, Instagram, Facebook, atau layanan hosting). Data analytics disediakan sebagai referensi dan mungkin mengalami keterlambatan.</p>

      <h3>5. Perubahan Ketentuan</h3>
      <p>Kami dapat memperbarui syarat ini sewaktu-waktu. Penggunaan berkelanjutan atas layanan merupakan persetujuan terhadap perubahan tersebut.</p>

      <h3>6. Kontak</h3>
      <p>Untuk pertanyaan, hubungi tim PPBIB melalui saluran internal.</p>
    </div>
    """
    return _page("Syarat & Ketentuan", body)


@app.route("/privacy")
def privacy():
    body = """
    <div class="card" style="max-width:780px">
      <h2>Kebijakan Privasi</h2>
      <p class="meta">Terakhir diperbarui: Juni 2026</p>

      <h3>1. Data yang Dikumpulkan</h3>
      <p>Platform PPBIB Analytics mengumpulkan data performa konten publik dari akun media sosial resmi PPBIB, meliputi: jumlah tayangan, suka, komentar, dan berbagi. Kami tidak mengumpulkan data pribadi pengguna TikTok.</p>

      <h3>2. Penggunaan Data</h3>
      <p>Data yang dikumpulkan digunakan semata-mata untuk keperluan analisis performa konten internal PPBIB guna meningkatkan strategi konten media sosial.</p>

      <h3>3. Penyimpanan Data</h3>
      <p>Data disimpan secara aman di server internal dan hanya dapat diakses oleh tim resmi PPBIB. Token OAuth disimpan secara terenkripsi dan tidak dibagikan kepada pihak manapun.</p>

      <h3>4. Berbagi Data</h3>
      <p>Kami tidak menjual, memperdagangkan, atau mentransfer data kepada pihak ketiga. Data hanya digunakan untuk keperluan operasional internal PPBIB.</p>

      <h3>5. Hak Pengguna</h3>
      <p>Pengguna dapat mencabut akses OAuth kapan saja melalui pengaturan akun TikTok/Instagram/Facebook mereka. Pencabutan akses akan menghentikan pengumpulan data baru.</p>

      <h3>6. Kontak</h3>
      <p>Untuk pertanyaan terkait privasi, hubungi tim PPBIB melalui saluran internal.</p>
    </div>
    """
    return _page("Kebijakan Privasi", body)
