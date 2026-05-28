"""
FCR Calculator — PPBIB Lead Intake Step 1
Dipanggil saat identifikasi species selesai untuk menghasilkan angka kerugian konkret.
"""

from dataclasses import dataclass

def rp(angka: int) -> str:
    """Format angka rupiah dengan titik sebagai pemisah ribuan."""
    return f"Rp {angka:,}".replace(",", ".")


FCR_BENCHMARK = {
    "nila":   {"min": 1.2, "max": 1.4, "label": "Nila (Oreochromis niloticus)"},
    "lele":   {"min": 0.8, "max": 1.0, "label": "Lele (Clarias sp.)"},
    "gurame": {"min": 1.5, "max": 1.8, "label": "Gurame (Osphronemus goramy)"},
    "mas":    {"min": 1.5, "max": 1.7, "label": "Mas (Cyprinus carpio)"},
    "patin":  {"min": 1.2, "max": 1.5, "label": "Patin (Pangasius sp.)"},
}

SKALA_LABEL = {
    "mikro":    "Mikro (<500 ekor / <20 m²)",
    "kecil":    "Kecil (500–5.000 ekor / 20–200 m²)",
    "menengah": "Menengah (5.000–50.000 ekor / 200–2.000 m²)",
    "besar":    "Besar (>50.000 ekor / >2.000 m²)",
}

# Batas wajar target panen (kg) untuk skala MIKRO per species.
# Melebihi batas ini = data tidak konsisten, perlu konfirmasi ulang ke leads.
MIKRO_PANEN_MAX_KG: dict[str, float] = {
    "lele":  200.0,
    "nila":  150.0,
}


@dataclass
class FCRResult:
    species: str
    skala: str
    fcr_aktual: float
    fcr_ideal_min: float
    fcr_ideal_max: float
    fcr_ideal_tengah: float
    selisih_fcr: float
    target_panen_kg: float
    harga_pakan_per_kg: int
    pemborosan_pakan_kg: float
    kerugian_per_siklus_rp: int
    penghematan_potensial_rp: int
    kesimpulan: str
    warning: str


def hitung_fcr(
    species: str,
    skala: str,
    fcr_aktual: float,
    harga_pakan_per_kg: int,
    target_panen_kg: float,
) -> FCRResult:
    species = species.lower().strip()
    skala = skala.lower().strip()

    if species not in FCR_BENCHMARK:
        raise ValueError(f"Species tidak dikenal: '{species}'. Pilih: {', '.join(FCR_BENCHMARK)}")
    if skala not in SKALA_LABEL:
        raise ValueError(f"Skala tidak dikenal: '{skala}'. Pilih: {', '.join(SKALA_LABEL)}")
    if fcr_aktual <= 0:
        raise ValueError("FCR aktual harus lebih dari 0.")
    if harga_pakan_per_kg <= 0:
        raise ValueError("Harga pakan harus lebih dari 0.")
    if target_panen_kg <= 0:
        raise ValueError("Target panen harus lebih dari 0.")

    bench = FCR_BENCHMARK[species]
    fcr_ideal_min = bench["min"]
    fcr_ideal_max = bench["max"]
    fcr_ideal_tengah = round((fcr_ideal_min + fcr_ideal_max) / 2, 2)

    selisih = round(fcr_aktual - fcr_ideal_tengah, 2)
    if selisih < 0:
        selisih = 0.0

    pemborosan_kg = round(selisih * target_panen_kg, 2)
    kerugian_rp = int(pemborosan_kg * harga_pakan_per_kg)

    pakan_aktual = fcr_aktual * target_panen_kg
    pakan_ideal = fcr_ideal_tengah * target_panen_kg
    penghematan_rp = int((pakan_aktual - pakan_ideal) * harga_pakan_per_kg)
    if penghematan_rp < 0:
        penghematan_rp = 0

    if kerugian_rp == 0:
        kesimpulan = (
            f"FCR {fcr_aktual} untuk {bench['label']} sudah dalam rentang ideal "
            f"({fcr_ideal_min}–{fcr_ideal_max}) — tidak ada pemborosan terdeteksi."
        )
    else:
        kesimpulan = (
            f"Dengan FCR {fcr_aktual}, Bapak/Ibu membuang sekitar {pemborosan_kg:.1f} kg pakan "
            f"per siklus — setara {rp(kerugian_rp)} yang bisa dihemat jika FCR turun ke {fcr_ideal_tengah}."
        )

    warning = ""
    if skala == "mikro" and species in MIKRO_PANEN_MAX_KG:
        batas = MIKRO_PANEN_MAX_KG[species]
        if target_panen_kg > batas:
            warning = (
                f"⚠ Data tidak konsisten — target panen {target_panen_kg:.0f} kg "
                f"melebihi batas wajar skala Mikro untuk {bench['label']} ({batas:.0f} kg). "
                f"Konfirmasi ulang skala kolam ke leads sebelum kirim reply."
            )

    return FCRResult(
        species=bench["label"],
        skala=SKALA_LABEL[skala],
        fcr_aktual=fcr_aktual,
        fcr_ideal_min=fcr_ideal_min,
        fcr_ideal_max=fcr_ideal_max,
        fcr_ideal_tengah=fcr_ideal_tengah,
        selisih_fcr=selisih,
        target_panen_kg=target_panen_kg,
        harga_pakan_per_kg=harga_pakan_per_kg,
        pemborosan_pakan_kg=pemborosan_kg,
        kerugian_per_siklus_rp=kerugian_rp,
        penghematan_potensial_rp=penghematan_rp,
        kesimpulan=kesimpulan,
        warning=warning,
    )


def format_for_wa(result: FCRResult) -> str:
    """Mengubah FCRResult menjadi teks siap paste ke reply WA."""
    if result.kerugian_per_siklus_rp == 0:
        return (
            f"FCR Bapak/Ibu saat ini ({result.fcr_aktual}) sudah masuk rentang ideal "
            f"untuk {result.species} ({result.fcr_ideal_min}–{result.fcr_ideal_max}). "
            f"Kita bisa fokus ke aspek lain untuk meningkatkan efisiensi produksi."
        )

    nama_species = result.species.split("(")[0].strip()
    return (
        f"Sedikit gambaran dari data yang ada — untuk target panen {result.target_panen_kg:.0f} kg "
        f"{nama_species}, FCR saat ini {result.fcr_aktual} "
        f"vs idealnya {result.fcr_ideal_min}–{result.fcr_ideal_max}. "
        f"Selisih {result.selisih_fcr} itu artinya sekitar {result.pemborosan_pakan_kg:.1f} kg pakan "
        f"terbuang per siklus, atau {rp(result.kerugian_per_siklus_rp)} yang keluar sia-sia. "
        f"Kalau FCR bisa turun ke angka ideal, Bapak/Ibu bisa hemat "
        f"{rp(result.penghematan_potensial_rp)} per siklus — tanpa harus tambah ekor atau perbesar kolam."
    )


def print_laporan(result: FCRResult) -> None:
    """Cetak laporan lengkap ke terminal."""
    sep = "─" * 50
    print(sep)
    print("  LAPORAN FCR CALCULATOR — PPBIB")
    print(sep)
    print(f"  Species       : {result.species}")
    print(f"  Skala         : {result.skala}")
    print(f"  FCR Aktual    : {result.fcr_aktual}")
    print(f"  FCR Ideal     : {result.fcr_ideal_min}–{result.fcr_ideal_max} (tengah: {result.fcr_ideal_tengah})")
    print(f"  Selisih FCR   : {result.selisih_fcr}")
    print(sep)
    print(f"  Target panen  : {result.target_panen_kg:.1f} kg")
    print(f"  Harga pakan   : {rp(result.harga_pakan_per_kg)}/kg")
    print(sep)
    print(f"  Pemborosan    : {result.pemborosan_pakan_kg:.2f} kg pakan/siklus")
    print(f"  Kerugian      : {rp(result.kerugian_per_siklus_rp)}/siklus")
    print(f"  Penghematan   : {rp(result.penghematan_potensial_rp)}/siklus (jika FCR → ideal)")
    print(sep)
    print(f"  KESIMPULAN    : {result.kesimpulan}")
    print(sep)
    if result.warning:
        print(f"\n  {result.warning}\n")
    print("\n  [TEKS WA]\n")
    print(format_for_wa(result))
    print()


if __name__ == "__main__":
    import sys

    def usage():
        print("Usage: python fcr_calculator.py <species> <skala> <fcr_aktual> <harga_pakan_rp> <target_panen_kg>")
        print("  species       : nila | lele | gurame | mas | patin")
        print("  skala         : mikro | kecil | menengah | besar")
        print("  fcr_aktual    : angka desimal, misal 1.8")
        print("  harga_pakan   : rupiah per kg, misal 10000")
        print("  target_panen  : kg per siklus, misal 300")
        print("\nContoh:")
        print("  python fcr_calculator.py nila kecil 1.8 10000 300")

    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        usage()
        sys.exit(0)

    if len(sys.argv) != 6:
        usage()
        sys.exit(1)

    try:
        result = hitung_fcr(
            species=sys.argv[1],
            skala=sys.argv[2],
            fcr_aktual=float(sys.argv[3]),
            harga_pakan_per_kg=int(sys.argv[4]),
            target_panen_kg=float(sys.argv[5]),
        )
        print_laporan(result)
    except (ValueError, KeyError) as e:
        print(f"Error: {e}")
        sys.exit(1)
