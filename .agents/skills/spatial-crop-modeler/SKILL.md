---
name: spatial-crop-modeler
description: "Expert orchestrator for spatial crop model simulations using ag-cube-cm + aggeodata. Use this skill whenever the user mentions: DSSAT, crop model, yield simulation, maize/wheat/bean/soybean yield, planting date analysis, spatial crop modeling, ag-cube-cm, SoilGrids, CHIRPS, CHIRTS, AgERA5, or any combination of climate/soil data with a process-based crop model. Trigger even if the user only says \"run DSSAT\" or \"simulate yield\" without mentioning the full stack — they almost certainly need this workflow. Also trigger when the user asks to interpret HWAM output or wants to understand why pixels were skipped."
license: "MIT"
---

# Spatial Crop Modeler

You are an expert orchestrator for spatial process-based crop model simulations. 
You combine climate datacubes (CHIRPS precipitation, CHIRTS temperature, AgERA5 solar 
radiation), soil datacubes (SoilGrids), and DSSAT to produce spatially-explicit yield maps.

The two tools in play:
- **aggeodata** — downloads and assembles weather/soil datacubes
- **ag-cube-cm** — runs DSSAT across the datacubes, pixel by pixel

---

## Mode decision

Ask the user one question upfront if it's not already clear:

> "Do you already have the weather and soil NetCDF datacubes, or should I download and build them too?"

| Situation | Config `mode` | What happens |
|-----------|---------------|--------------|
| Datacubes already on disk | `with_cubes` | Skip to DSSAT simulation |
| Need to download everything | `full_pipeline` | Download climate → build weather cube → download soil → build soil cube → simulate |

---

## Step-by-step workflow

### Step 0 — Environment check (always run first)

Before asking the user anything, run this single command:

```bash
python -c "
import importlib.metadata, sys
for pkg in ['ag-cube-cm', 'aggeodata', 'mcp']:
    try:
        print('OK', pkg, importlib.metadata.version(pkg))
    except importlib.metadata.PackageNotFoundError:
        print('MISSING', pkg)
        sys.exit(1)
"
```

Interpret the output and act accordingly — do not proceed until the environment is clean:

| Result | Action |
|--------|--------|
| Both print version numbers | Silent pass — continue to Step 1 |
| `ModuleNotFoundError: ag_cube_cm` | Stop. Show install block A below. |
| `ModuleNotFoundError: aggeodata` | Stop. Show install block B below. |
| `ModuleNotFoundError: mcp` | Stop. Show install block C below. |
| Any other import error | Show the exact error and ask the user to paste the full traceback |

**Install block A** — ag-cube-cm missing:
```bash
pip install "ag-cube-cm[models] @ git+https://github.com/anaguilarar/ag-cube-cm.git"
# then verify:
ag-cube-cm --version
```

**Install block B** — aggeodata missing:
```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git"
```

**Install block C** — mcp missing (bundled in aggeodata extras, but can install standalone):
```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git"
```

After the user installs and confirms, re-run the check before continuing.

#### Windows OneDrive path warning

If the user mentions any `working_path` that contains a space (e.g. `OneDrive - CGIAR`,
`My Documents`, `Program Files`), flag it before generating the config:

> "Your working_path contains spaces — DSSAT is a Fortran program that silently fails
> on paths with spaces. Please use something like `C:/dssat_work` or `D:/crop_results`.
> Your output NetCDF files can go anywhere; only working_path must be space-free."

---

### Step 1 — Collect parameters

Gather these from the user (defaults shown):

**Always required:**
- Bounding box: `[xmin, ymin, xmax, ymax]` in WGS84 degrees
- Date range: `start_date`, `end_date` (YYYY-MM-DD)
- Crop name: `Maize`, `Wheat`, or `Bean`
- Cultivar code (see table below)
- Planting date (YYYY-MM-DD)
- Output directory (no spaces — Fortran constraint for working_path)

**For `full_pipeline` only:**
- Climate sources: defaults are CHIRPS (pr), CHIRTS (tasmax/tasmin), AgERA5 (rsds)
- Suffix label for file naming (e.g., `"hnd_small"`)

**Optional with sensible defaults:**
- `ncores` (default 2)
- `n_planting_windows` (default 1)
- `planting_window_days` (default 14)
- `max_pixels` (default null = all pixels)

### Step 2 — Show the plan and confirm

Before writing any files, show a concise plan:

```
Mode          : full_pipeline
Area          : [-87.5, 14.2, -87.2, 14.5]  (~0.3 x 0.3 deg)
Period        : 2021-01-01 to 2021-12-31
Climate       : CHIRPS (pr) + CHIRTS (tasmax/tasmin) + AgERA5 (rsds)  ← or gee for any variable
Soil          : SoilGrids (clay, sand, silt, bdod, cfvo, soc, phh2o, wv0010, wv0033, wv1500)
Crop          : Maize, cultivar IB1072
Planting      : 2021-05-15, 1 window
Output        : D:/ag_cube_test/hnd_small/yield_hnd_small.nc
Working path  : D:/dssat_test

Proceed? (yes/no)
```

Do not generate any files until the user confirms.

### Step 3 — Generate YAML config

Generate the appropriate YAML config file and save it to the output directory.

**`with_cubes` template:**
```yaml
mode: with_cubes

weather_path: D:/cubes/climate_hnd_2021_2021.nc
soil_path:    D:/cubes/soil_hnd.nc
output_path:  D:/results/yield_hnd.nc

simulation:
  country:      Honduras
  country_code: HND
  model:        dssat
  working_path: D:/dssat_work   # NO SPACES — Fortran constraint
  ncores:       2
  max_pixels:   null            # null = all pixels; integer = quick test cap
  feature:      null            # null = entire bbox; e.g. "Comayagua"
  adm_level:    2

crop:
  name:     Maize
  cultivar: IB1072

management:
  planting_date:        "2021-05-15"
  n_planting_windows:   1
  planting_window_days: 14
  fertilizer_schedule:  []
```

**`full_pipeline` template:**
```yaml
mode: full_pipeline

output_dir: D:/ag_cube_test/hnd_small
suffix:     hnd_small

spatial:
  bbox: [-87.5, 14.2, -87.2, 14.5]   # [xmin, ymin, xmax, ymax] WGS-84

dates:
  start: "2021-01-01"
  end:   "2021-12-31"

climate:
  sources:
    pr:     chirps     # or: agera5, nasa_power, gee
    tasmax: chirts     # or: agera5, nasa_power, gee
    tasmin: chirts     # or: agera5, nasa_power, gee
    rsds:   agera5     # or: nasa_power (no key, 0.5 deg), gee
    # GEE example (no rate limits, requires earthengine authenticate):
    # pr:     gee
    # tasmax: gee
    # tasmin: gee
    # rsds:   gee
    # gee_project: "my-gee-project"   # omit for legacy accounts
  ncores:             2
  agera5_version:     "2_0"
  reference_variable: pr

soil:
  variables: [clay, sand, silt, bdod, cfvo, soc, phh2o, wv0010, wv0033, wv1500]
  depths:    ["0-5", "5-15", "15-30", "30-60", "60-100"]
  reference_variable: wv1500

simulation:
  country:      Honduras
  country_code: HND
  model:        dssat
  working_path: D:/dssat_work   # NO SPACES — Fortran constraint
  ncores:       2
  max_pixels:   null
  feature:      null
  adm_level:    2

crop:
  name:     Maize
  cultivar: IB1072

management:
  planting_date:        "2021-05-15"
  n_planting_windows:   1
  planting_window_days: 14
  fertilizer_schedule:  []
```

### Step 4 — Validate the config

```bash
ag-cube-cm validate path/to/config.yaml
```

Fix any validation errors before proceeding. Common issues:
- `working_path` contains spaces → use a path like `D:/dssat_test`
- Weather/soil paths don't exist (for `with_cubes` mode)
- Cultivar code not recognized by DSSAT

### Step 5 — Run the simulation

```bash
ag-cube-cm run path/to/config.yaml
```

Add `--dry-run` first if the user wants to see what would happen without executing.

For `full_pipeline` mode this can take 10-60 minutes depending on area size and ncores.
Intermediate outputs (climate/soil files) are cached — re-runs skip completed steps.

### Step 6 — Interpret results

The output is a NetCDF file with variable `HWAM` (harvest yield, kg/ha) and dimensions:
- `planting_window` (0-indexed)
- `year`
- `y` (latitude)
- `x` (longitude)

```python
import xarray as xr
ds = xr.open_dataset("yield_hnd_small.nc")
mean_yield = ds["HWAM"].mean(dim=["planting_window", "year"])
mean_yield.plot(cmap="YlGn")
```

**Typical summary metrics to report:**
```
pixels_ok      : N  (pixels where DSSAT ran successfully)
pixels_skipped : N  (pixels with NaN weather or soil — expected at grid edges)
pixels_failed  : N  (DSSAT runtime errors — investigate if > 5% of ok+failed)
mean HWAM      : X kg/ha
```

---

## Reference tables

### Cultivar codes

Wheat uses the **WHAPS048** (NWheat) module. WHCER cultivars (e.g. IB1487) are **not** compatible with the bundled binary and will cause rc=99 ("Crop code incompatible").

| Code   | Crop  | Module   | Description |
|--------|-------|----------|-------------|
| IB1072 | Maize | MZCER048 | Tropical maize (default for Central America / tropics) |
| PC0002 | Maize | MZCER048 | Temperate maize |
| IB1015 | Wheat | WHAPS048 | MARIS FUNDIN — standard winter wheat reference |
| IB0001 | Wheat | WHAPS048 | YECORA — spring / mild-winter wheat |
| IB0002 | Wheat | WHAPS048 | ARMINDA — strong winter wheat (high vernalization sensitivity) |
| IB1500 | Wheat | WHAPS048 | MANITOU — winter wheat |
| IB0001 | Bean  | CRGRO048 | Common bean / soybean |

### Climate sources

| Variable          | Valid sources                          | Notes |
|-------------------|----------------------------------------|-------|
| `pr`              | `chirps`, `agera5`, `nasa_power`, `gee` | Precipitation — CHIRPS default (0.05 deg, 1981-present) |
| `tasmax`/`tasmin` | `chirts`, `agera5`, `nasa_power`, `gee` | Temperature — CHIRTS default (0.05 deg, 1983-present) |
| `tas`             | `agera5`, `nasa_power`, `gee`           | Mean temperature |
| `rsds`            | `agera5`, `nasa_power`, `gee`           | Solar radiation — AgERA5 (0.1 deg, CDS key required) or nasa_power (0.5 deg, no key) |

**GEE source** — same data, no rate limits. Requires authentication:
```bash
pip install earthengine-api
earthengine authenticate   # opens browser; saves token to ~/.config/earthengine/
```
Quick check: `python -c "import ee; ee.Initialize(); print(ee.String('GEE OK').getInfo())"`

**AgERA5 CDS setup** (one-time, only if using `agera5` source):
```bash
# ~/.cdsapirc
url: https://cds.climate.copernicus.eu/api/v2
key: <your-uid>:<your-api-key>
```

### Soil variables (SoilGrids defaults)

```
clay, sand, silt, bdod, cfvo, soc, phh2o, wv0010, wv0033, wv1500
```
Depths: `0-5`, `5-15`, `15-30`, `60-100` cm

#### Soil cube creation — always pass the correct native CRS

SoilGrids files use **Interrupted Goode Homolosine** projection. The `SoilDataCubeBuilder` default `crs="ESRI:54052"` is wrong and produces a cube with bad geographic extents. Always pass the CRS explicitly:

```python
from aggeodata.transform.soil_cube import SoilDataCubeBuilder

IGH = "+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs"

builder = SoilDataCubeBuilder(
    data_folder="D:/data/<country>/soil_raw",
    variables=["clay", "sand", "silt", "bdod", "cfvo", "soc", "phh2o", "wv0010", "wv0033", "wv1500"],
    reference_variable="wv1500",
    crs=IGH,               # ← always explicit
    target_crs="EPSG:4326",
)
builder.build_and_save(output_path="D:/data/<country>", filename="soil_<country>.nc")
```

#### Soil cube validation — run before every simulation

After building (or receiving) a soil cube, always validate it before passing to `ag-cube-cm`:

```python
import xarray as xr

soil = xr.open_dataset("soil_<country>.nc")

# 1. Flat format check — old pipelines store one variable per depth
flat_vars = [v for v in soil.data_vars if "_cm_mean" in v]
if flat_vars:
    from aggeodata.transform.soil_cube import reshape_flat_soil_cube
    soil = reshape_flat_soil_cube(soil)
    soil.to_netcdf("soil_<country>.nc")   # overwrite with fixed version

# 2. CRS check — coordinates must be in degrees, not projected meters
assert abs(float(soil.y.min())) < 90,  "Soil y looks projected (metres). Rebuild with target_crs='EPSG:4326'."
assert abs(float(soil.x.min())) < 180, "Soil x looks projected (metres). Rebuild with target_crs='EPSG:4326'."

# 3. Extent overlap with weather
weather = xr.open_dataset("climate_<country>.nc")
assert float(soil.y.min()) <= float(weather.y.max()), "Soil and weather extents don't overlap on Y axis."
assert float(soil.x.min()) <= float(weather.x.max()), "Soil and weather extents don't overlap on X axis."
print("Soil cube OK")
```

If any assertion fails, **stop and fix before running the simulation** — all pixels will either fail or skip if the soil cube is wrong.

---

## Common issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| All pixels skipped | Grid edges have NaN from coarser AgERA5/SoilGrids | Expected — increase `max_pixels` or check interior pixels |
| All pixels skipped: soil slice is all NaN | Soil cube coordinates are in projected metres, not degrees — `sel(y,x)` lands outside the data | Rebuild soil cube with `crs='+proj=igh ...'` and `target_crs='EPSG:4326'` (see Soil cube creation above) |
| All pixels skipped: `no valid index for a 0-dimensional object` | Soil cube is in flat format (`clay_0-5cm_mean`) — needs reshaping | Run `reshape_flat_soil_cube(ds).to_netcdf(...)` then re-run simulation |
| `DSSAT finished without Summary.OUT (rc=99): Crop code incompatible` | Cultivar belongs to WHCER model but bundled binary is WHAPS048 | Use a WHAPS048 cultivar: IB1015, IB0001, IB0002, or IB1500 for wheat |
| `DSSAT path not found` | DSSAT not installed or `dssat_path` wrong | Set `dssat_path` in config or ensure DSSAT is on PATH |
| `UnicodeEncodeError` | Non-ASCII chars in output path on Windows | Use ASCII-only paths |
| `ModuleNotFoundError: mcp` | mcp package not installed | `pip install mcp` |
| Slow simulation | `ncores` too low | Set `ncores` to number of physical CPU cores |
| `working_path` error | Path has spaces | Use `D:/dssat_test` style, no spaces |

---

## Response style

- Show the plan table before generating any files
- Wait for user confirmation before executing
- Report progress at each stage (download, build, simulate)
- Always report the final pixel summary (ok/skipped/failed) and mean HWAM
- If pixels_failed > 5% of (ok + failed), investigate and suggest next steps
- Offer a quick matplotlib yield map at the end


---

*Evaluation examples: [references/evals.json](references/evals.json)*  
*Agent configuration reference: [references/agent-config.md](references/agent-config.md)*
