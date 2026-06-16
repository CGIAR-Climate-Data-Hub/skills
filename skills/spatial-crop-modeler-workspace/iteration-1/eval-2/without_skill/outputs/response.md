# Ethiopia Spring Wheat Yield Simulation 2018-2020 (without skill)

## Summary

Explored the ag_cube_cm codebase to understand the full workflow, then produced a guide
for simulating spring wheat yield over [37.0, 8.0, 38.0, 9.0] for 2018-2020.

**Key decisions:**
- Climate: CHIRPS (pr), CHIRTS (tasmax/tasmin), NASA POWER for rsds (no CDS key)
  - NASA POWER downloaded via `aggeodata.ingestion.nasa_power.NASAPowerDownloader`
  - Interpolated from 0.5 deg to CHIRPS 0.05 deg grid, merged into climate NetCDF
- Soil: SoilGrids via `aggeodata.ingestion.soil.SoilGridsDownloader`
- Cultivar: IB1015 (spring wheat, confirmed via list_supported_crops)
- Working path: E:/dssat_runs (no spaces)
- Output: E:/ethiopia_wheat/yield_eth_wheat.nc with dims (planting_window, year, y, x)

## Config File

```yaml
GENERAL_INFO:
  country: 'Ethiopia'
  country_code: 'ETH'
  model: 'dssat'
  working_path: 'E:/dssat_runs'
  dssat_path: null
  ncores: 2

SPATIAL_INFO:
  feature_name: 'shapeName'
  adm_level: 2
  feature: null
  soil_path: 'E:/ethiopia_wheat/soil_eth.nc'
  weather_path: 'E:/ethiopia_wheat/climate_eth_2018_2020.nc'
  output_path: 'E:/ethiopia_wheat/yield_eth_wheat.nc'
  dem_path: null

CROP:
  name: 'Wheat'
  cultivar: 'IB1015'

MANAGEMENT:
  planting_date: '2018-10-01'
  n_planting_windows: 1
  planting_window_days: 14
```

## Running

The simulation uses `ag_cube_cm.mcp_server.run_simulation(config_path=..., max_pixels=None)` which handles
per-pixel, per-year, per-window DSSAT execution in parallel using ThreadPoolExecutor.

Note: NASA POWER for solar radiation requires a separate download step -- there is no
standard YAML-driven pipeline for this in ag-cube-cm. The user would need to manually:
1. Download NASA POWER rsds
2. Merge it into the climate datacube
3. Then run the simulation
