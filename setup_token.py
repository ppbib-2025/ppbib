"""
Jalankan setelah login TikTok untuk tukar code dengan token.
Usage: python setup_token.py <authorization_code>
"""
import sys
from src.tiktok_auth import exchange_code_for_token

if len(sys.argv) < 2:
    print("Usage: python setup_token.py <code>")
    sys.exit(1)

code = sys.argv[1]
result = exchange_code_for_token(code)
print("Hasil:", result)

if "data" in result and "access_token" in result["data"]:
    print("\n✅ Token berhasil disimpan! Sekarang jalankan: python main.py")
else:
    print("\n❌ Gagal. Cek client key/secret atau coba auth ulang.")
