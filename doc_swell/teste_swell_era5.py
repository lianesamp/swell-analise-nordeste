import cdsapi

client = cdsapi.Client()

request = {
    "product_type": "reanalysis",

    "variable": [
        "significant_height_of_total_swell",
        "mean_direction_of_total_swell",
        "mean_period_of_total_swell"
    ],

    "year": "2025",
    "month": "03",
    "day": ["15"],
    "time": ["12:00"],

    "area": [-3.5, -38.5, -3.5, -38.5],

    "format": "netcdf"
}

client.retrieve(
    "reanalysis-era5-single-levels",
    request,
    "teste_swell_era5.nc"
)

print("DOWNLOAD SWELL ERA5 OK")