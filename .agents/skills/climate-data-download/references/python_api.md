# Python API Reference for aggeodata

Use these class signatures and methods when writing Python scripts to download or process data if the MCP tools are unavailable.

## 1. CHIRPS Precipitation Downloader

```python
from aggeodata.ingestion.chirps import CHIRPSDownloader

dl = CHIRPSDownloader()
# returns dict: {date_string: local_path}
downloaded_paths = dl.download(
    extent=[-3.2554, 4.7367, 1.1918, 11.1733], # [xmin, ymin, xmax, ymax]
    starting_date="YYYY-MM-DD",
    ending_date="YYYY-MM-DD",
    output_folder="D:/data/pr_raw",
    ncores=1 # Keep at 1 to respect rate limits
)
```

## 2. CHIRTS Temperature Downloader

```python
from aggeodata.ingestion.chirts import CHIRTSDownloader

dl = CHIRTSDownloader(
    variables=["tmax", "tmin"], # or ["tmax"], ["tmin"]
    source="era5"               # "era5" (1983-present) or "chirts" (1983-2016)
)
# returns dict: {variable: {year: local_path}}
downloaded_paths = dl.download(
    extent=[-3.2554, 4.7367, 1.1918, 11.1733],
    starting_date="YYYY-MM-DD",
    ending_date="YYYY-MM-DD",
    output_folder="D:/data/temp_raw",
    ncores=1 # Keep at 1 to respect rate limits
)
```

## 3. NASA POWER Downloader (No API key needed)

```python
from aggeodata.ingestion.nasa_power import NASAPowerDownloader

dl = NASAPowerDownloader(
    parameters=["T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN"]
)
# returns str: path to the saved NetCDF file
nc_path = dl.download(
    extent=[-3.2554, 4.7367, 1.1918, 11.1733],
    starting_date="YYYY-MM-DD",
    ending_date="YYYY-MM-DD",
    output_folder="D:/data/nasa_power"
)
```

## 4. AgERA5 Downloader (Copernicus CDS API key required)

```python
from aggeodata.ingestion.agera5 import AgEra5Downloader

dl = AgEra5Downloader()
# returns dict: {year: local_path}
downloaded_paths = dl.download(
    variable="2m_temperature",         # AgERA5 native parameter name
    statistic="maximum",               # "maximum", "minimum", or None
    time="daily",                      # "daily" or specific hour like "06:00"
    starting_date="YYYY-MM-DD",
    ending_date="YYYY-MM-DD",
    output_folder="D:/data/agera5_raw",
    aoi_extent=[-3.2554, 4.7367, 1.1918, 11.1733],
    ncores=4
)
```

## 5. AgERA5 variable keys

Pass one of these as the `variable` argument to `download_agera5` (MCP tool) or to
`AgEra5Downloader.download(variable=...)` (Python API):

| Key | Description |
|-----|-------------|
| `temperature_tmax` | Daily maximum 2 m air temperature |
| `temperature_tmin` | Daily minimum 2 m air temperature |
| `solar_radiation` | Surface downwelling shortwave flux (J m⁻²) |
| `wind_speed` | 10 m wind speed (m s⁻¹) |
| `vapour_pressure` | 2 m vapour pressure (hPa) |
| `vapour_pressure_defficit` | Vapour pressure deficit at Tmax |
| `relative_humidity_max` | Daily maximum relative humidity |
| `relative_humidity_min` | Daily minimum relative humidity |
| `relative_humidity_06` | Relative humidity snapshot at 06:00 UTC |
| `relative_humidity_09` | Relative humidity snapshot at 09:00 UTC |
| `relative_humidity_12` | Relative humidity snapshot at 12:00 UTC |
| `relative_humidity_15` | Relative humidity snapshot at 15:00 UTC |
| `relative_humidity_18` | Relative humidity snapshot at 18:00 UTC |
| `dew_point_temperature` | Mean 2 m dew-point temperature |
| `reference_evapotranspiration` | FAO-56 reference ET (mm day⁻¹) |
