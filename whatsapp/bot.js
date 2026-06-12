require("dotenv").config({ path: "../.env" });
const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const express = require("express");
const axios = require("axios");

const PYTHON_URL = process.env.PYTHON_WEBHOOK_URL || "http://localhost:5000";

// ── WhatsApp client ────────────────────────────────────────────────────────
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

// ── Forward pesan masuk ke Python ─────────────────────────────────────────
client.on("message", async (msg) => {
  if (msg.fromMe) return;

  const phone = msg.from.replace("@c.us", "").replace(/[^0-9]/g, "");
  const body  = msg.body;

  console.log(`[IN] ${phone}: ${body.substring(0, 60)}`);

  try {
    await axios.post(`${PYTHON_URL}/wa/incoming`, { phone, message: body }, { timeout: 10000 });
  } catch (err) {
    console.error(`[IN] Gagal forward ke Python: ${err.message}`);
  }
});

// ── API server (dipanggil dari Python) ────────────────────────────────────
const app = express();
app.use(express.json());

app.post("/send", async (req, res) => {
  const { phone, message } = req.body;
  if (!phone || !message) {
    return res.status(400).json({ error: "phone dan message wajib diisi" });
  }
  try {
    const chatId = phone.replace(/[^0-9]/g, "") + "@c.us";
    await client.sendMessage(chatId, message);
    console.log(`[OUT] Terkirim ke ${phone}`);
    res.json({ success: true });
  } catch (err) {
    console.error("Gagal kirim:", err.message);
    res.status(500).json({ error: err.message, success: false });
  }
});

app.get("/status", (req, res) => {
  res.json({ status: client.info ? "connected" : "disconnected" });
});

const PORT = process.env.WA_PORT || 3000;
app.listen(PORT, () => {
  console.log(`API server berjalan di http://localhost:${PORT}`);
});

client.initialize();
