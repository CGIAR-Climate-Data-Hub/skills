# DSSAT Spatial Crop Model -- Ethiopia Spring Wheat 2018-2020

## Plan (full_pipeline mode)

| Parameter | Value |
|---|---|
| Mode | full_pipeline |
| Bounding box | [37.0, 8.0, 38.0, 9.0] -- 1x1 degree tile, Ethiopia |
| Date range | 2018-01-01 to 2020-12-31 |
| Crop | Spring Wheat (IB1015) |
| Planting date | October 1 (per year) |
| Planting windows | 1 window, 14-day spread |
| Precipitation | CHIRPS |
| Temperature (max/min) | CHIRTS |
| Solar radiation | NASA POWER (0.5 deg, no CDS key needed) |
| Soil variables | clay, sand, silt, bdod, cfvo, soc, phh2o, wv0010, wv0033, wv1500 |
| Soil depths | 0-5, 5-15, 15-30, 30-60, 60-100 cm |
| Output directory | E:/ethiopia_wheat (no spaces -- Fortran-safe) |
| Yield output | E:/ethiopia_wheat/yield_eth_wheat.nc |
| CPU cores | 2 |

**User confirmed. Proceeding.**

## Generated YAML Config

```yaml
mode: full_pipeline
general:
  country: Ethiopia
  country_code: ETH
  working_path: E:/ethiopia_wheat
  ncores: 2
bbox: [37.0, 8.0, 38.0, 9.0]
dates:
  start_date: "2018-01-01"
  end_date:   "2020-12-31"
suffix: eth_wheat_2018_2020
climate:
  variables:
    pr:     {source: chirps}
    tasmax: {source: chirts}
    tasmin: {source: chirts}
    rsds:   {source: nasa_power}
  output_path: E:/ethiopia_wheat/climate_raw
soil:
  variables: [clay, sand, silt, bdod, cfvo, soc, phh2o, wv0010, wv0033, wv1500]
  depths:    ["0-5", "5-15", "15-30", "30-60", "60-100"]
  output_path: E:/ethiopia_wheat/soil_raw
spatial:
  output_path: E:/ethiopia_wheat/yield_eth_wheat.nc
simulation:
  crop:
    name: Wheat
    cultivar: IB1015
  management:
    planting_date: "2018-10-01"
    n_planting_windows: 1
    planting_window_days: 14
  max_pixels: null
```

## Step 4 -- Validate

```bash
ag-cube-cm validate E:/ethiopia_wheat/config.yaml
```

## Step 5 -- Run

```bash
ag-cube-cm run E:/ethiopia_wheat/config.yaml
```

Pipeline execution order:
1. Download CHIRPS precipitation tiles (2018-2020)
2. Download CHIRTS Tmax/Tmin tiles (2018-2020)
3. Download NASA POWER solar radiation (2018-2020, 0.5-deg grid)
4. Build weather datacube (NetCDF, daily, aligned to bbox)
5. Download SoilGrids variables at 5 depth layers
6. Build soil datacube (NetCDF, matched to weather grid)
7. Run DSSAT pixel-by-pixel using 2 cores, planting Oct 1 each year

## Step 6 -- Interpret Results

Output: `E:/ethiopia_wheat/yield_eth_wheat.nc`

Key variable: **HWAM** (kg/ha -- harvested dry matter at maturity)
Dimensions: `planting_window x year x y x x`

Pixel summary to report:
- pixels_ok: pixels where DSSAT converged
- pixels_skipped: pixels with missing climate or soil data (expected at edges)
- pixels_failed: DSSAT runtime errors (investigate if > 5% of ok+failed)
- mean HWAM: spatial mean yield across all successful pixels
