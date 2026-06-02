---
title: Climate Data Download
description: Downloads CHIRPS, CHIRTS-ERA5, AgERA5, and NASA POWER climate data for any country or bounding box.
sidebar:
  order: 2
---

**Type:** Data ingestion  
**Skill file:** `skills/climate-data-download/skill.md`  
**Raw URL:** `https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/climate-data-download/skill.md`

---

You say what variable and region you need. The skill routes each variable to the correct
source, shows you the plan, and downloads in sequence using `aggeodata`.

## Variable → source routing

| Variable requested | Source | Notes |
|--------------------|--------|-------|
| Precipitation / rainfall | **CHIRPS** | Daily 0.05°, 1981–present |
| Temperature (Tmax / Tmin) | **CHIRTS-ERA5** | Daily 0.05°, 1983–present |
| Solar radiation, wind speed, RH | **NASA POWER** | S3 Zarr — no API key, 1981–2029 |
| Hourly RH (06/09/12/15/18 UTC) | **AgERA5** | CDS key required |
| VPD, reference ET, dew point | **AgERA5** | CDS key required |

## NASA POWER variable names

The downloaded NetCDF uses **CF standard names**, not the NASA POWER parameter codes:

| NASA POWER code | CF name in NetCDF |
|-----------------|-------------------|
| `ALLSKY_SFC_SW_DWN` | `rsds` |
| `WS2M` | `sfcWind` |
| `T2M_MAX` | `tasmax` |
| `T2M_MIN` | `tasmin` |
| `RH2M` | `hurs` |
| `PRECTOTCORR` | `pr` |

Always use the CF name (right column) when accessing the dataset after download.

## Example

```
I need 6 AM relative humidity and reference ET for the Ashanti region
of Ghana, January–June 2021. Output to D:/data/ashanti
```

The skill responds:

```
Here's what I'll download (all via AgERA5):

| Variable    | Key                           |
|-------------|-------------------------------|
| RH 06:00    | relative_humidity_06          |
| Ref. ET     | reference_evapotranspiration  |

Region: Ashanti (admin level 1) | Period: 2021-01-01 → 2021-06-30
CDS API key required — do you have one configured?

Shall I proceed?
```

## Python fallback pattern (NASA POWER)

```python
from aggeodata.ingestion.nasa_power import NASAPowerDownloader

dl = NASAPowerDownloader(parameters=["ALLSKY_SFC_SW_DWN", "WS2M"])
nc = dl.download(extent=extent, starting_date="2020-01-01",
                 ending_date="2022-12-31", output_folder="D:/tmp/data")
print("Saved:", nc)
```

## AgERA5 setup (CDS key)

Required only for AgERA5 variables. Register free at
[cds.climate.copernicus.eu](https://cds.climate.copernicus.eu/), then create `~/.cdsapirc`:

```
url: https://cds.climate.copernicus.eu/api
key: <YOUR-UID>:<YOUR-API-KEY>
```
