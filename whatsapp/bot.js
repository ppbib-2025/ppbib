require("dotenv").config({ path: "../.env" });
const { Client, LocalAuth } = require("whatsapp-web.js");
const QRCode = require("qrcode");
const express = require("express");

let currentQR = null;
let isReady = false;

const client = new Client({
  authStrategy: new LocalAuth({ dataPath: "./session" }),
  puppeteer: {
    executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || "/usr/bin/chromium",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
  },
});

client.on("qr", (qr) => {
  currentQR = qr;
  isReady = false;
  console.log("\n==============================");
  console.log("QR CODE SIAP — buka URL public Railway di browser HP kamu untuk scan!");
  console.log("==============================\n");
});

client.on("ready", () => {
  currentQR = null;
  isReady = true;
  console.log("\n✅ WhatsApp Bot PPBIB siap digunakan!\n");
});

client.on("auth_failure", () => {
  isReady = false;
  console.log("❌ Autentikasi gagal. Hapus folder session/ dan coba lagi.");
});

client.on("disconnected", () => {
  isReady = false;
  console.log("⚠️ WhatsApp terputus.");
});

async function sendMessage(phoneNumber, message) {
  const chatId = phoneNumber.replace(/[^0-9]/g, "") + "@c.us";
  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error("sendMessage timeout setelah 20s")), 20000)
  );
  await Promise.race([client.sendMessage(chatId, message), timeout]);
  console.log(`✓ Pesan terkirim ke ${phoneNumber}`);
}

const app = express();
app.use(express.json());

// Halaman QR code — buka di browser HP untuk scan
app.get("/", async (req, res) => {
  if (isReady) {
    return res.send(`<html><body style="font-family:sans-serif;text-align:center;padding:40px">
      <h2>✅ WhatsApp Bot PPBIB</h2>
      <p style="color:green;font-size:20px">Terhubung & siap kirim pesan</p>
    </body></html>`);
  }
  if (!currentQR) {
    return res.send(`<html><body style="font-family:sans-serif;text-align:center;padding:40px">
      <h2>⏳ WhatsApp Bot PPBIB</h2>
      <p>Menunggu QR code... refresh halaman ini dalam 5 detik</p>
      <script>setTimeout(()=>location.reload(),5000)</script>
    </body></html>`);
  }
  const qrImage = await QRCode.toDataURL(currentQR);
  res.send(`<html><body style="font-family:sans-serif;text-align:center;padding:40px">
    <h2>📱 Scan QR Code dengan WhatsApp Business</h2>
    <p>Buka WhatsApp Business → Linked Devices → Link a Device → Scan</p>
    <img src="${qrImage}" style="width:300px;height:300px"/>
    <p><small>QR code refresh otomatis tiap 20 detik</small></p>
    <script>setTimeout(()=>location.reload(),20000)</script>
  </body></html>`);
});

app.post("/send", async (req, res) => {
  const { phone, message } = req.body;
  if (!phone || !message)
    return res.status(400).json({ error: "phone dan message wajib diisi" });
  try {
    await sendMessage(phone, message);
    res.json({ success: true });
  } catch (err) {
    console.error("Gagal kirim:", err.message);
    res.status(500).json({ error: err.message });
  }
});

app.get("/status", (req, res) => {
  res.json({ status: isReady ? "connected" : "disconnected" });
});

// Ambil history chat untuk analisis lead
app.get("/chats", async (req, res) => {
  if (!isReady) return res.status(503).json({ error: "WhatsApp belum terhubung" });
  try {
    const chats = await client.getChats();
    const privateChats = chats.filter(c => !c.isGroup);
    const result = [];
    for (const chat of privateChats.slice(0, 100)) {
      try {
        const messages = await chat.fetchMessages({ limit: 25 });
        const filtered = messages
          .map(m => ({ from: m.fromMe ? "saya" : "customer", body: m.body || "", time: m.timestamp }))
          .filter(m => m.body.trim());
        if (filtered.length > 0) {
          result.push({ phone: chat.id.user, name: chat.name || chat.id.user, messages: filtered });
        }
      } catch (_) {}
    }
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`API server berjalan di port ${PORT}`);
  console.log(`Buka URL public Railway di browser untuk lihat QR code`);
});

client.initialize();
