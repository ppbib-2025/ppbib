"""
Dashboard analytics PPBIB — bisa dibuka di browser kapan saja.
Route: GET /                  → status bot
       GET /analytics         → tabel performa konten semua platform
       GET /analytics/refresh → collect metrics sekarang, redirect ke /analytics
       GET/POST /digital      → landing page produk digital
       GET/POST /digital/order/<id> → buat + konfirmasi order
       GET /digital/download/<order_id> → download produk (dengan token)
"""
import json
import os
import threading
from datetime import datetime
from flask import Flask, redirect, url_for, request
from src.digital_products import (
    get_products, get_product, create_order, confirm_payment, deliver_order, verify_download
)
from templates.digital_products import render_product_lp
from src.wa_webhook import handle_wa_webhook

app = Flask(__name__)

TIKTOK_FILE   = "data/analytics_tiktok.json"
IG_FILE       = "data/analytics_instagram.json"
FB_FILE       = "data/analytics_facebook.json"
STRATEGY_FILE = "data/strategy_insights.json"

_refresh_status = {"running": False, "last": None, "message": ""}


# ── TikTok OAuth ──────────────────────────────────────────────

@app.route("/tiktok/connect")
def tiktok_connect():
    from src.tiktok_auth import CLIENT_KEY, CLIENT_SECRET, REDIRECT_URI, get_auth_url

    if not all((CLIENT_KEY, CLIENT_SECRET, REDIRECT_URI)):
        return "TikTok OAuth belum dikonfigurasi di server.", 503
    return redirect(get_auth_url())


@app.route("/tiktok/callback")
def tiktok_callback():
    from src.tiktok_auth import exchange_code_for_token, verify_state

    if request.args.get("error"):
        return f"TikTok authorization gagal: {request.args.get('error_description', request.args['error'])}", 400

    code = request.args.get("code")
    if not code or not verify_state(request.args.get("state", "")):
        return "TikTok authorization tidak valid. Mulai ulang dari /tiktok/connect.", 400

    result = exchange_code_for_token(code)
    if "access_token" not in result:
        error = result.get("error", "unknown_error")
        description = result.get("error_description", "Periksa konfigurasi aplikasi dan coba lagi.")
        return f"TikTok authorization gagal ({error}): {description}", 400

    return "TikTok berhasil terhubung. Token tersimpan di server PPBIB; halaman ini boleh ditutup."


# ── Instagram/Facebook OAuth ────────────────────────────────────

@app.route("/instagram/connect")
def instagram_connect():
    from src.instagram_auth import (
        APP_ID, APP_SECRET, REDIRECT_URI, get_auth_url,
    )

    if not all((APP_ID, APP_SECRET, REDIRECT_URI)):
        return "Instagram OAuth belum dikonfigurasi di server.", 503
    try:
        return redirect(get_auth_url())
    except RuntimeError as e:
        return str(e), 503


@app.route("/instagram/callback")
def instagram_callback():
    from src.instagram_auth import exchange_code_for_token

    if request.args.get("error"):
        return f"Instagram authorization gagal: {request.args.get('error_description', request.args['error'])}", 400

    code = request.args.get("code")
    if not code or request.args.get("state") != "ppbib_ig_auth":
        return "Instagram authorization tidak valid. Mulai ulang dari /instagram/connect.", 400

    result = exchange_code_for_token(code)
    if "access_token" not in result:
        return f"Instagram authorization gagal: {result}", 400

    return "Instagram berhasil terhubung. Token tersimpan di server PPBIB; halaman ini boleh ditutup."


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


def _do_refresh():
    """Jalankan collect metrics di background thread."""
    _refresh_status["running"] = True
    _refresh_status["message"] = "Sedang mengambil data..."
    try:
        from src.analytics import (
            collect_tiktok_metrics,
            collect_instagram_metrics,
            collect_facebook_metrics,
        )
        from src.tiktok_auth import load_token
        msgs = []
        if load_token():
            collect_tiktok_metrics()
            msgs.append("TikTok ✓")
        collect_instagram_metrics()
        msgs.append("Instagram ✓")
        collect_facebook_metrics()
        msgs.append("Facebook ✓")
        _refresh_status["message"] = " | ".join(msgs)
        _refresh_status["last"] = datetime.now().strftime("%d %b %Y %H:%M:%S")
    except Exception as e:
        _refresh_status["message"] = f"Error: {e}"
    finally:
        _refresh_status["running"] = False


# ── Digital Products ──────────────────────────────────────────

@app.route("/digital")
def digital_products():
    return render_product_lp()


@app.route("/digital/order/<product_id>", methods=["POST"])
def digital_order(product_id):
    product = get_product(product_id)
    if not product:
        return render_product_lp('<div class="flash flash-error">Produk tidak ditemukan.</div>')

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    if not name or not phone:
        return render_product_lp('<div class="flash flash-error">Isi nama dan nomor WA dulu.</div>')

    order = create_order(product_id, name, phone)
    if not order:
        return render_product_lp('<div class="flash flash-error">Gagal membuat order. Coba lagi.</div>')

    # Kirim instruksi pembayaran via WA
    from src.whatsapp import send_whatsapp
    pay_msg = (
        f"Halo {name} 👋\n\n"
        f"Terima kasih sudah order *{product['name']}* — "
        f"{product['price_formatted']}.\n\n"
        f"Silakan transfer ke:\n"
        f"🏦 BCA a.n. Aditiya Nugraha\n\n"
        f"Setelah transfer, balas pesan ini dengan "
        f"*KONFIRMASI [order_id]*\n\n"
        f"Contoh: KONFIRMASI {order['order_id']}\n\n"
        f"Link download akan kami kirim otomatis setelah pembayaran terverifikasi ✅"
    ).format(order_id=order['order_id'])

    try:
        send_whatsapp(phone, pay_msg)
    except Exception as e:
        print(f"[Digital] Gagal kirim WA order: {e}")

    # Tampilkan halaman sukses
    html = f"""<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pesanan Dibuat — PPBIB</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0fdf4;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px}}
.card{{background:#fff;border-radius:16px;padding:36px 28px;max-width:480px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.08)}}
.icon{{font-size:52px;margin-bottom:8px}}
h2{{font-size:20px;margin-bottom:6px;color:#1a5e2a}}
p{{font-size:14px;color:#555;line-height:1.6;margin-bottom:4px}}
.oid{{background:#f0fdf4;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:700;color:#1a5e2a;display:inline-block;margin:12px 0}}
.note{{font-size:12px;color:#999;margin-top:14px;padding-top:14px;border-top:1px solid #eee}}
a{{color:#1a5e2a;font-weight:600}}
</style>
</head>
<body>
<div class="card">
  <div class="icon">🎉</div>
  <h2>Pesanan Dibuat!</h2>
  <p>Kami sudah kirim instruksi pembayaran<br>ke WhatsApp <strong>{phone}</strong>.</p>
  <div class="oid">{order['order_id']}</div>
  <p style="font-size:13px;color:#666">Simpan ID order di atas untuk konfirmasi.</p>
  <p class="note">Sudah transfer? Balas *KONFIRMASI {order['order_id']}*<br>ke nomor WA yang tadi kami kirimi pesan.</p>
  <p style="margin-top:14px"><a href="/digital">← Kembali ke produk</a></p>
</div>
</body>
</html>"""
    return html


@app.route("/digital/confirm", methods=["POST"])
def digital_confirm():
    """Webhook untuk konfirmasi pembayaran — bisa dari WA atau form."""
    order_id = request.form.get("order_id", "").strip().upper()
    phone = request.form.get("phone", "").strip()

    order_data = confirm_payment(order_id)
    if not order_data:
        return {"success": False, "message": "Order tidak ditemukan atau sudah diproses."}

    delivery = deliver_order(order_id)
    if not delivery:
        return {"success": False, "message": "Gagal deliver. Coba lagi."}

    msg = delivery["whatsapp_message"]
    from src.whatsapp import send_whatsapp
    try:
        send_whatsapp(order_data["customer_phone"], msg)
        print(f"[Digital] WA terkirim ke {order_data['customer_phone']} untuk order {order_id}")
    except Exception as e:
        print(f"[Digital] Gagal kirim WA: {e}")

    return {"success": True, "message": "Link download sudah dikirim ke WA."}


@app.route("/digital/download/<order_id>")
def digital_download(order_id):
    token = request.args.get("token", "")
    product = verify_download(order_id, token)
    if not product:
        return "<h3>Link tidak valid atau sudah kadaluarsa.</h3>"

    download_url = product["delivery"]["url"]
    html = f"""<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Download — {product['name']}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0fdf4;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;padding:20px}}
.card{{background:#fff;border-radius:16px;padding:36px 28px;max-width:460px;text-align:center;box-shadow:0 4px 20px rgba(0,0,0,.08)}}
.icon{{font-size:48px;margin-bottom:8px}}
h2{{font-size:20px;margin-bottom:6px;color:#1a5e2a}}
p{{font-size:14px;color:#555;margin-bottom:12px}}
.btn{{display:inline-block;padding:12px 32px;border-radius:10px;font-size:15px;font-weight:700;text-decoration:none;background:#1a5e2a;color:#fff}}
.btn:hover{{background:#144d22}}
</style>
</head>
<body>
<div class="card">
  <div class="icon">📥</div>
  <h2>{product['name']}</h2>
  <p>Terima kasih sudah membeli produk PPBIB 🙏</p>
  <a class="btn" href="{download_url}" target="_blank">Download Sekarang</a>
  <p style="margin-top:12px;font-size:12px;color:#999">Link ini bisa diakses 1x24 jam. Simpan file setelah download.</p>
</div>
</body>
</html>"""
    return html


@app.route("/")
def home():
    return (
        "<h3 style='font-family:sans-serif;padding:20px'>PPBIB Bot aktif ✅</h3>"
        "<p style='font-family:sans-serif;padding:0 20px'>"
        "<a href='/analytics'>Lihat Analytics</a></p>"
    )


# ── WhatsApp Webhook ─────────────────────────────────────────

@app.route("/webhook/wa", methods=["POST"])
def wa_webhook():
    """Terima webhook dari WAHA saat pesan masuk."""
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return {"status": "error", "reason": "no_payload"}, 400

    try:
        result = handle_wa_webhook(payload)
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Webhook error: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}, 500


@app.route("/webhook/wa", methods=["GET"])
def wa_webhook_verify():
    """WAHA kadang kirim GET untuk verify webhook."""
    return {"status": "ok"}


# ── Messenger Webhook ────────────────────────────────────────

@app.route("/webhook/messenger", methods=["GET"])
def messenger_verify():
    """Verifikasi webhook oleh Meta (hub.challenge)."""
    from src.messenger_webhook import verify_token

    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token", "")
    challenge = request.args.get("hub.challenge", "")
    if mode == "subscribe" and verify_token(token):
        return challenge, 200
    return "verification failed", 403


@app.route("/webhook/messenger", methods=["POST"])
def messenger_webhook():
    """Terima pesan masuk dari Facebook Page."""
    from src.messenger_webhook import handle_messenger_webhook

    payload = request.get_json(force=True, silent=True)
    if not payload:
        return {"status": "error", "reason": "no_payload"}, 400
    try:
        return handle_messenger_webhook(payload)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Messenger webhook error: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}, 500


@app.route("/leads")
def leads_page():
    """Lihat semua lead yang masuk."""
    import json as _json
    leads_file = "data/wa_leads.json"
    try:
        with open(leads_file) as f:
            leads = _json.load(f)
    except (FileNotFoundError, _json.JSONDecodeError):
        leads = {}

    rows = ""
    for phone, d in sorted(leads.items(), key=lambda x: x[1].get("updated_at", ""), reverse=True):
        status = d.get("status", "-")
        tahap = d.get("tahap", "-")
        keyword = d.get("keyword_trigger", "-")
        last_msg = (d.get("last_message", ""))[:60]
        updated = (d.get("updated_at", ""))[:16]
        color = "#16a34a" if status == "sent" else "#d97706" if status == "pending_approval" else "#dc2626"
        rows += f"""
        <tr>
          <td style='padding:8px;border-bottom:1px solid #eee;font-family:monospace'>{phone}</td>
          <td style='padding:8px;border-bottom:1px solid #eee'>{tahap}</td>
          <td style='padding:8px;border-bottom:1px solid #eee'>{keyword}</td>
          <td style='padding:8px;border-bottom:1px solid #eee'>{last_msg}</td>
          <td style='padding:8px;border-bottom:1px solid #eee'><span style='color:{color};font-weight:600'>{status}</span></td>
          <td style='padding:8px;border-bottom:1px solid #eee;font-size:12px'>{updated}</td>
        </tr>"""

    return f"""
    <!DOCTYPE html>
    <html><head><meta charset='utf-8'><title>PPBIB Leads</title>
    <style>body{{font-family:sans-serif;padding:20px;max-width:1100px;margin:0 auto}}
    table{{width:100%;border-collapse:collapse}}
    th{{text-align:left;padding:8px;border-bottom:2px solid #333;font-size:13px}}</style></head>
    <body>
    <h2>📋 WA Leads ({len(leads)} total)</h2>
    <p><a href='/'>← Dashboard</a></p>
    <table>
      <tr><th>Phone</th><th>Tahap</th><th>Keyword</th><th>Pesan Terakhir</th><th>Status</th><th>Updated</th></tr>
      {rows}
    </table>
    </body></html>
    """


@app.route("/analytics/refresh")
def refresh():
    if not _refresh_status["running"]:
        t = threading.Thread(target=_do_refresh, daemon=True)
        t.start()
    return redirect(url_for("analytics"))


@app.route("/analytics")
def analytics():
    # ── TikTok
    tiktok_rows = []
    for vid_id, d in _load(TIKTOK_FILE).items():
        snaps = d.get("snapshots", [])
        if not snaps:
            continue
        s        = snaps[-1]
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

    # ── Instagram
    ig_rows = []
    for pid, d in _load(IG_FILE).items():
        snaps = d.get("snapshots", [])
        if not snaps:
            continue
        s        = snaps[-1]
        likes    = s.get("like_count", 0)
        comments = s.get("comments_count", 0)
        impr     = s.get("impressions", 0)
        er = round((likes + comments) / max(impr, 1) * 100, 2)
        ig_rows.append({
            "caption":    (d.get("caption", ""))[:65] or "(tanpa caption)",
            "media_type": d.get("media_type", "IMAGE"),
            "likes": likes, "comments": comments, "impressions": impr, "er": er,
        })
    ig_rows.sort(key=lambda x: x["er"], reverse=True)

    # ── Facebook
    fb_rows = []
    for pid, d in _load(FB_FILE).items():
        snaps = d.get("snapshots", [])
        if not snaps:
            continue
        s        = snaps[-1]
        likes    = s.get("like_count", 0)
        comments = s.get("comment_count", 0)
        shares   = s.get("share_count", 0)
        impr     = s.get("impressions", 0)
        er = round((likes + comments + shares) / max(impr, 1) * 100, 2)
        fb_rows.append({
            "message":    (d.get("message", ""))[:65] or "(tanpa pesan)",
            "likes": likes, "comments": comments, "shares": shares,
            "impressions": impr, "er": er,
        })
    fb_rows.sort(key=lambda x: x["er"], reverse=True)

    strategy = _load(STRATEGY_FILE)
    now_str  = datetime.now().strftime("%d %b %Y %H:%M")

    # refresh status banner
    refresh_banner = ""
    if _refresh_status["running"]:
        refresh_banner = '<div class="banner running">&#9203; Mengambil data... halaman akan diperbarui otomatis.</div>'
    elif _refresh_status["last"]:
        refresh_banner = (
            f'<div class="banner ok">&#9989; Data diperbarui: {_refresh_status["last"]} '
            f'&mdash; {_refresh_status["message"]}</div>'
        )

    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
{'<meta http-equiv="refresh" content="4">' if _refresh_status['running'] else ''}
<title>PPBIB Analytics</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f4f4;color:#222}}
.hdr{{background:#1a1a2e;color:#fff;padding:18px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}}
.hdr h1{{font-size:18px;font-weight:700}}
.hdr p{{font-size:12px;opacity:.6;margin-top:2px}}
.refresh-btn{{background:#3b82f6;color:#fff;border:none;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;text-decoration:none;display:inline-block}}
.refresh-btn:hover{{background:#2563eb}}
.banner{{padding:10px 24px;font-size:13px;font-weight:500}}
.banner.running{{background:#fef9c3;color:#854d0e}}
.banner.ok{{background:#dcfce7;color:#166534}}
.wrap{{max-width:1100px;margin:0 auto;padding:20px}}
.card{{background:#fff;border-radius:10px;padding:18px 20px;margin-bottom:18px;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
.card h2{{font-size:14px;font-weight:700;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid #eee}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
th{{text-align:left;padding:7px 9px;background:#f8f8f8;font-weight:600;color:#555;border-bottom:2px solid #e8e8e8}}
td{{padding:7px 9px;border-bottom:1px solid #f0f0f0;vertical-align:top}}
tr:last-child td{{border:none}}
.er{{font-weight:700}}
.er-high{{color:#16a34a}}
.er-mid{{color:#d97706}}
.er-low{{color:#dc2626}}
.badge{{display:inline-block;padding:1px 6px;border-radius:4px;font-size:11px;font-weight:600;background:#e0e7ff;color:#4338ca}}
.empty{{color:#999;font-size:13px;padding:6px 0}}
.strat{{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:13px;font-size:13px;line-height:1.7}}
.meta{{font-size:11px;color:#777;margin-bottom:8px}}
ul{{margin-left:18px;margin-top:4px}}
li{{margin-bottom:3px;font-size:13px}}
</style>
</head>
<body>
<div class="hdr">
  <div>
    <h1>&#128202; PPBIB Analytics Dashboard</h1>
    <p>Update terakhir: {now_str}</p>
  </div>
  <a href="/analytics/refresh" class="refresh-btn">&#128257; Refresh Data Sekarang</a>
</div>
{refresh_banner}
<div class="wrap">
"""

    def _table_tiktok(rows):
        if not rows:
            return '<p class="empty">Belum ada data. Klik "Refresh Data Sekarang" atau tunggu snapshot jam 19:00.</p>'
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
            return '<p class="empty">Belum ada data. Pastikan Instagram token sudah di-setup.</p>'
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

    html += f'<div class="card"><h2>&#127916; TikTok</h2>{_table_tiktok(tiktok_rows)}</div>'
    html += f'<div class="card"><h2 style="color:#C13584">&#128247; Instagram</h2>{_table_ig(ig_rows)}</div>'
    html += f'<div class="card"><h2 style="color:#1877F2">&#128216; Facebook</h2>{_table_fb(fb_rows)}</div>'

    html += '<div class="card"><h2>&#128300; Auto Research'
    if strategy:
        iteration = strategy.get("iteration", "-")
        week      = strategy.get("week_analyzed", "-")
        strat_txt = strategy.get("strategy_prompt", "-")
        patterns  = strategy.get("top_performing_patterns", {})
        html += f' &mdash; Iterasi #{iteration}</h2>'
        html += f'<p class="meta">Analisis pekan {week}</p>'
        html += f'<div class="strat">{strat_txt}</div>'
        if patterns.get("winning_topics"):
            html += '<p style="margin-top:12px;font-size:13px"><strong>&#9989; Topik pemenang:</strong></p><ul>'
            for t in patterns["winning_topics"]:
                html += f'<li>{t}</li>'
            html += '</ul>'
        if patterns.get("avoid_patterns"):
            html += '<p style="margin-top:10px;font-size:13px"><strong>&#10060; Hindari:</strong></p><ul>'
            for t in patterns["avoid_patterns"]:
                html += f'<li>{t}</li>'
            html += '</ul>'
    else:
        html += '</h2><p class="empty">Auto research belum pernah jalan. Akan berjalan otomatis tiap Sabtu 17:00.</p>'
    html += '</div>'

    html += '</div></body></html>'
    return html
