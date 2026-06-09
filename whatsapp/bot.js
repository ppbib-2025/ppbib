require("dotenv").config({ path: "../.env" });
const { Client, LocalAuth } = require("whatsapp-web.js");
const QRCode = require("qrcode");
const express = require("express");
const https = require("https");

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

// Analisis semua lead dari seluruh riwayat chat WA
app.get("/analyze-leads", async (req, res) => {
  if (!isReady) return res.status(503).json({ error: "WhatsApp belum terhubung" });
  const apiKey = process.env.DINOIKI_API_KEY;
  if (!apiKey) return res.status(500).json({ error: "DINOIKI_API_KEY belum di-set" });

  try {
    const chats = await client.getChats();
    const privateChats = chats.filter(c => !c.isGroup);
    console.log(`[LeadAnalyzer] Memulai scan ${privateChats.length} chat...`);

    const hotLeads = [];
    const BATCH = 10;

    for (let i = 0; i < privateChats.length; i += BATCH) {
      const batch = privateChats.slice(i, i + BATCH);
      const results = await Promise.allSettled(batch.map(async (chat) => {
        const messages = await chat.fetchMessages({ limit: 20 });
        const customerMsgs = messages.filter(m => !m.fromMe && (m.body || "").trim());
        if (customerMsgs.length === 0) return null;

        const conv = messages
          .filter(m => (m.body || "").trim())
          .map(m => `${m.fromMe ? "saya" : "customer"}: ${m.body}`)
          .join("\n");

        const prompt = `PPBIB jual ebook itik Rp75.000 dan kalkulator pakan.\n\nAnalisis chat ini:\n---\n${conv}\n---\n\nApakah ini lead panas (minat tapi belum closing)? Kriteria: tanya harga, bilang nanti/pikir-pikir, atau tidak balas setelah minat.\n\nReturn JSON saja: {"is_hot_lead":true/false,"score":1-10,"reason":"1 kalimat","last_intent":"apa terakhir mereka tanya","suggested_reply":"pesan follow-up 2-3 kalimat Bahasa Indonesia untuk dikirim manual oleh pemilik"}`;

        const result = await callDinoiki(apiKey, prompt);
        if (result && result.is_hot_lead && result.score >= 6) {
          return { phone: chat.id.user, name: chat.name || chat.id.user, ...result };
        }
        return null;
      }));

      for (const r of results) {
        if (r.status === "fulfilled" && r.value) hotLeads.push(r.value);
      }
      console.log(`[LeadAnalyzer] Progress: ${Math.min(i + BATCH, privateChats.length)}/${privateChats.length}`);
    }

    hotLeads.sort((a, b) => (b.score || 0) - (a.score || 0));
    console.log(`[LeadAnalyzer] Selesai. ${hotLeads.length} lead panas ditemukan.`);
    res.json({ leads: hotLeads, count: hotLeads.length, total_scanned: privateChats.length });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

function callDinoiki(apiKey, prompt) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      model: "claude-sonnet-4-6",
      max_tokens: 250,
      messages: [{ role: "user", content: prompt }]
    });
    const req = https.request({
      hostname: "ai.dinoiki.com",
      path: "/v1/chat/completions",
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${apiKey}`, "Content-Length": Buffer.byteLength(body) }
    }, (r) => {
      let data = "";
      r.on("data", d => data += d);
      r.on("end", () => {
        try {
          const json = JSON.parse(data);
          const text = json.choices[0].message.content.trim();
          resolve(JSON.parse(text));
        } catch (_) { resolve(null); }
      });
    });
    req.on("error", reject);
    setTimeout(() => reject(new Error("timeout")), 15000);
    req.write(body);
    req.end();
  });
}

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`API server berjalan di port ${PORT}`);
  console.log(`Buka URL public Railway di browser untuk lihat QR code`);
});

client.initialize();
