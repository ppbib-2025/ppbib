"""
Setup token Instagram Graph API.
Usage:
  python setup_instagram_token.py          → tampilkan URL login
  python setup_instagram_token.py <code>   → tukar code dengan token
"""
import sys
from src.instagram_auth import get_auth_url, exchange_code_for_token

if len(sys.argv) < 2:
    print("Buka URL ini di browser untuk login Instagram:")
    print()
    print(get_auth_url())
    print()
    print("Setelah login, salin 'code' dari URL redirect, lalu jalankan:")
    print("  python setup_instagram_token.py <code>")
else:
    code = sys.argv[1]
    result = exchange_code_for_token(code)
    if "access_token" in result:
        print("\n✅ Token Instagram berhasil disimpan! (berlaku ~60 hari)")
    else:
        print("\n❌ Gagal:", result)
