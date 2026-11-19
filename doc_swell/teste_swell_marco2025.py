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

    "day": [
        "15", "16", "17", "18", "19", "20", "21",
        "22", "23", "24", "25", "26", "27", "28"
    ],

    "time": [
        "00:00", "01:00", "02:00", "03:00",
        "04:00", "05:00", "06:00", "07:00",
        "08:00", "09:00", "10:00", "11:00",
        "12:00", "13:00", "14:00", "15:00",
        "16:00", "17:00", "18:00", "19:00",
        "20:00", "21:00", "22:00", "23:00"
    ],

    "area": [-3.5, -38.5, -3.5, -38.5],

    "format": "netcdf"
}

client.retrieve(
    "reanalysis-era5-single-levels",
    request,
    "era5_swell_marco2025.nc"
)

print("DOWNLOAD SWELL MARCO 2025 OK")