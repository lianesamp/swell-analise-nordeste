import cdsapi
import os
import time
import calendar

# Pasta onde os arquivos serão salvos
PASTA = r"C:\Users\USER\ERA5_CEARA_HISTORICO"
os.makedirs(PASTA, exist_ok=True)

# Período histórico completo
ANO_INICIAL = 1979
ANO_FINAL = 2025

# Ponto de referência ao largo de Fortaleza
# Formato da área: [Norte, Oeste, Sul, Leste]
AREA = [-3.5, -38.5, -3.5, -38.5]

HORAS = [
    "00:00", "01:00", "02:00", "03:00",
    "04:00", "05:00", "06:00", "07:00",
    "08:00", "09:00", "10:00", "11:00",
    "12:00", "13:00", "14:00", "15:00",
    "16:00", "17:00", "18:00", "19:00",
    "20:00", "21:00", "22:00", "23:00"
]

client = cdsapi.Client()

for ano in range(ANO_INICIAL, ANO_FINAL + 1):
    for mes in range(1, 13):
        nome_arquivo = f"era5_swell_{ano}_{mes:02d}.nc"
        arquivo = os.path.join(PASTA, nome_arquivo)

        # Permite retomar sem baixar novamente arquivos já existentes
        if os.path.exists(arquivo) and os.path.getsize(arquivo) > 0:
            print(f"{ano}-{mes:02d}: arquivo já existe. Pulando.")
            continue

        # Usa apenas os dias válidos de cada mês
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        dias = [f"{dia:02d}" for dia in range(1, ultimo_dia + 1)]

        request = {
            "product_type": "reanalysis",
            "variable": [
                "significant_height_of_total_swell",
                "mean_direction_of_total_swell",
                "mean_period_of_total_swell"
            ],
            "year": str(ano),
            "month": f"{mes:02d}",
            "day": dias,
            "time": HORAS,
            "area": AREA,
            "format": "netcdf"
        }

        print()
        print("=" * 60)
        print(f"BAIXANDO {ano}-{mes:02d}")
        print("=" * 60)

        try:
            client.retrieve(
                "reanalysis-era5-single-levels",
                request,
                arquivo
            )
            print(f"{ano}-{mes:02d}: DOWNLOAD OK")
            print(f"Arquivo: {arquivo}")

        except Exception as erro:
            print(f"{ano}-{mes:02d}: ERRO")
            print(erro)

            with open(
                os.path.join(PASTA, "erros_download.txt"),
                "a",
                encoding="utf-8"
            ) as f:
                f.write(f"{ano}-{mes:02d}: {erro}\n")

            # Remove eventual arquivo incompleto
            if os.path.exists(arquivo):
                os.remove(arquivo)

        time.sleep(2)

print()
print("=" * 60)
print("PROCESSO DE DOWNLOAD TERMINADO")
print("=" * 60)
print(f"Arquivos salvos em: {PASTA}")
print("Serão gerados até 564 arquivos mensais (1979-2025).")
