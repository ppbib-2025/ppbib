require("dotenv").config({ path: "../.env" });
const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const express = require("express");
const axios = require("axios");

const PYTHON_API = "http://localhost:5000";

// Nomor yang diabaikan (bot itu sendiri, broadcast, status)
const IGNORED_SUFFIXES = ["@broadcast", "@g.us", "status@broadcast"];

// ── Setup WhatsApp client ──────────────────────────────────────────────
const client = new Client({
  authStrategy: new LocalAuth({ dataPath: "./session" }),
  puppeteer: { args: ["--no-sandbox", "--disable-setuid-sandbox"] },
});

client.on("qr", (qr) => {
  console.log("\n==============================");
  console.log("SCAN QR CODE INI DENGAN WHATSAPP BUSINESS KAMU:");
  console.log("==============================\n");
  qrcode.generate(qr, { small: true });
});

client.on("ready", () => {
  console.log("\n✅ WhatsApp Bot PPBIB siap digunakan!\n");
});

client.on("auth_failure", () => {
  console.log("❌ Autentikasi gagal. Hapus folder session/ dan coba lagi.");
});

// ── Handler pesan masuk → AI response ──────────────────────────────────
client.on("message", async (msg) => {
  // Abaikan pesan dari grup, broadcast, dan pesan dari bot sendiri
  if (IGNORED_SUFFIXES.some((s) => msg.from.endsWith(s))) return;
  if (msg.fromMe) return;

  const phone = msg.from.replace("@c.us", "");
  const body = msg.body?.trim();

  if (!body) return;

  console.log(`📩 Pesan masuk dari ${phone}: ${body.substring(0, 60)}`);

  try {
    // Kirim ke Python untuk AI response
    const resp = await axios.post(
      `${PYTHON_API}/ai-reply`,
      { phone, message: body },
      { timeout: 30000 }
    );

    if (resp.data.success) {
      console.log(`✓ AI reply terkirim ke ${phone}`);
    }
  } catch (err) {
    console.error(`❌ Gagal kirim ke Python AI: ${err.message}`);
    // Fallback: reply default jika Python tidak bisa dihubungi
    try {
      await msg.reply(
        "Halo! Terima kasih sudah menghubungi PPBIB 🙏\n" +
          "Kami sedang memproses pesanmu. Mohon tunggu sebentar ya!"
      );
    } catch (e) {
      console.error("Gagal kirim fallback reply:", e.message);
    }
  }
});

// ── Fungsi kirim pesan ─────────────────────────────────────────────────
async function sendMessage(phoneNumber, message) {
  const chatId = phoneNumber.replace(/[^0-9]/g, "") + "@c.us";
  await client.sendMessage(chatId, message);
  console.log(`✓ Pesan terkirim ke ${phoneNumber}`);
}

// ── API server (dipanggil dari Python) ────────────────────────────────
const app = express();
app.use(express.json());

app.post("/send", async (req, res) => {
  const { phone, message } = req.body;
  if (!phone || !message) {
    return res.status(400).json({ error: "phone dan message wajib diisi" });
  }
  try {
    await sendMessage(phone, message);
    res.json({ success: true });
  } catch (err) {
    console.error("Gagal kirim:", err.message);
    res.status(500).json({ error: err.message });
  }
});

app.get("/status", (req, res) => {
  res.json({ status: client.info ? "connected" : "disconnected" });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`API server berjalan di http://localhost:${PORT}`);
});

client.initialize();
