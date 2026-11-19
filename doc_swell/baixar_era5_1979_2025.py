import cdsapi
import os
import time

client = cdsapi.Client()

PASTA = r"C:\Users\USER\ERA5_CEARA_MARCO"

os.makedirs(PASTA, exist_ok=True)

dias = [
    "15", "16", "17", "18", "19", "20", "21",
    "22", "23", "24", "25", "26", "27", "28"
]

horas = [
    "00:00", "01:00", "02:00", "03:00",
    "04:00", "05:00", "06:00", "07:00",
    "08:00", "09:00", "10:00", "11:00",
    "12:00", "13:00", "14:00", "15:00",
    "16:00", "17:00", "18:00", "19:00",
    "20:00", "21:00", "22:00", "23:00"
]

for ano in range(1979, 2026):

    arquivo = os.path.join(
        PASTA,
        f"era5_swell_marco_{ano}.nc"
    )

    if os.path.exists(arquivo):
        print(f"{ano}: arquivo já existe. Pulando.")
        continue

    print()
    print("=" * 60)
    print(f"BAIXANDO {ano}")
    print("=" * 60)

    request = {
        "product_type": "reanalysis",

        "variable": [
            "significant_height_of_total_swell",
            "mean_direction_of_total_swell",
            "mean_period_of_total_swell"
        ],

        "year": str(ano),

        "month": "03",

        "day": dias,

        "time": horas,

        "area": [-3.5, -38.5, -3.5, -38.5],

        "format": "netcdf"
    }

    try:

        client.retrieve(
            "reanalysis-era5-single-levels",
            request,
            arquivo
        )

        print(f"{ano}: DOWNLOAD OK")
        print(f"Arquivo: {arquivo}")

    except Exception as erro:

        print(f"{ano}: ERRO")
        print(erro)

        with open(
            os.path.join(PASTA, "erros_download.txt"),
            "a",
            encoding="utf-8"
        ) as f:

            f.write(f"{ano}: {erro}\n")

    time.sleep(2)

print()
print("=" * 60)
print("DOWNLOAD TERMINADO")
print("=" * 60)
print(f"Arquivos estão em: {PASTA}")