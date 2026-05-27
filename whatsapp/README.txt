==============================
CARA MENJALANKAN WHATSAPP BOT PPBIB
==============================

PRASYARAT:
- Node.js sudah terinstall (cek: node --version)
- WhatsApp Business aktif di HP kamu

LANGKAH-LANGKAH:

1. Buka Command Prompt / Terminal
2. Masuk ke folder whatsapp:
   cd path\ke\ppbib\whatsapp

3. Install dependencies (cukup sekali):
   npm install

4. Jalankan bot:
   npm start

5. Akan muncul QR code di terminal.
   Buka WhatsApp Business di HP → Linked Devices → Scan QR code

6. Setelah scan, bot sudah aktif!
   Biarkan terminal tetap terbuka.

CATATAN:
- Sesi tersimpan otomatis, tidak perlu scan ulang setiap hari
- Jika ada masalah, hapus folder "session/" dan scan ulang
- Bot menerima perintah kirim pesan dari bot Python secara otomatis

==============================
