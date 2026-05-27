require("dotenv").config({ path: "../.env" });
const { Client, LocalAuth } = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const express = require("express");
const fs = require("fs");
const path = require("path");

// ── Setup WhatsApp client ──────────────────────────────────────────────
const client = new Client({
  authStrategy: new LocalAuth({ dataPath: "./session" }),
  puppeteer: { args: ["--no-sandbox", "--disable-setuid-sandbox"] },
});

// Tampilkan QR code di terminal saat pertama kali
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

// ── Fungsi kirim pesan ─────────────────────────────────────────────────
async function sendMessage(phoneNumber, message) {
  // Format nomor: 628xxx → 628xxx@c.us
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
