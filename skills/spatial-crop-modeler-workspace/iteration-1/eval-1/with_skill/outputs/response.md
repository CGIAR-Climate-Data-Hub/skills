# DSSAT Spatial Crop Model -- Honduras Maize 2021

## Mode Decision
Mode: with_cubes -- datacubes already on disk, skipping download steps.

## Plan (confirmed by user)

| Parameter        | Value |
|------------------|-------|
| Mode             | with_cubes |
| Area (bbox)      | [-87.5, 14.2, -87.2, 14.5] -- Honduras |
| Period           | 2021 |
| Climate cube     | D:/cubes/climate_hnd_2021.nc |
| Soil cube        | D:/cubes/soil_hnd.nc |
| Crop             | Maize -- IB1072 (Tropical Maize) |
| Planting date    | 2021-05-15 |
| Planting windows | 1 window, 14-day span |
| Output           | D:/results/yield_hnd.nc |
| Working path     | D:/dssat_hnd |
| ncores           | 2 |

## YAML Config

```yaml
mode: with_cubes

general:
  country: Honduras
  country_code: HND
  working_path: D:/dssat_hnd
  ncores: 2

spatial:
  weather_path: D:/cubes/climate_hnd_2021.nc
  soil_path: D:/cubes/soil_hnd.nc
  output_path: D:/results/yield_hnd.nc

simulation:
  crop:
    name: Maize
    cultivar: IB1072
  management:
    planting_date: "2021-05-15"
    n_planting_windows: 1
    planting_window_days: 14
  max_pixels: null
```

## Step 4 -- Validate

```bash
ag-cube-cm validate D:/dssat_hnd/config_hnd_maize_2021.yaml
```

Expected: all required fields present, paths exist, no spaces in working_path.

## Step 5 -- Run (dry-run first, then full)

```bash
# Preview -- no DSSAT calls, shows pixel grid and config echo
ag-cube-cm run D:/dssat_hnd/config_hnd_maize_2021.yaml --dry-run

# Full simulation
ag-cube-cm run D:/dssat_hnd/config_hnd_maize_2021.yaml
```

## Step 6 -- Interpreting Results

- Output variable: **HWAM** (kg/ha) -- harvest grain yield at maturity
- Output dimensions: `planting_window x year x y x x`
- Check the pixel summary:
  - `pixels_ok` -- successfully simulated
  - `pixels_skipped` -- edge NaNs from coarser grids (expected near bbox boundary)
  - `pixels_failed` -- if > 5% of total, investigate soil/weather alignment

### Example post-run check (Python)

```python
import xarray as xr
ds = xr.open_dataset("D:/results/yield_hnd.nc")
hwam = ds["HWAM"]
print(f"Mean HWAM: {float(hwam.mean()):.0f} kg/ha")
print(f"Min: {float(hwam.min()):.0f}  Max: {float(hwam.max()):.0f}")
hwam.isel(planting_window=0, year=0).plot()  # quick spatial map
```

## Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| All pixels skipped | Edge NaNs from coarser soil grid | Expected; shrink bbox slightly |
| working_path error | Spaces in path | Use D:/dssat_hnd not "D:/dssat hnd" |
| ModuleNotFoundError: mcp | MCP not installed | pip install mcp |
