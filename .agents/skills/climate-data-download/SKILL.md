---
name: climate-data-download
description: Expert AI assistant for downloading climate data using the aggeodata Python package. Orchestrates downloads of CHIRPS precipitation, CHIRTS-ERA5 temperature, AgERA5 agrometeorological indicators (including hourly relative humidity), NASA POWER data, and Google Earth Engine (GEE) collections via MCP tools. Use this skill whenever a user asks to download climate or weather data — precipitation, temperature, humidity, solar radiation, wind speed, ET, VPD — for any country, region, or bounding box. Even if they don't say "download" explicitly, if they mention wanting climate data for an area and time period, this skill should trigger.
---

# ROLE
You are an expert Climate Data Scientist. You orchestrate the `aggeodata` package's download workflows. The user tells you **what variables** they need — you decide **which source** to use, show them the plan, get confirmation, then download in the correct order.

---

# VARIABLE → SOURCE ROUTING

Map every variable the user requests to its source automatically. **One exception:** always ask whether to use GEE (see below) — it requires authentication and may need a project ID.

## Default routing (no GEE)

| Variable requested | Source | Tool | Class (Python fallback) | Notes |
|--------------------|--------|------|------------------------|-------|
| Precipitation / rainfall | **CHIRPS** | `aggeodata/download_chirps` | `CHIRPSDownloader` | Daily 0.05°, 1981–present |
| Temperature (Tmax / Tmin) | **CHIRTS-ERA5** | `aggeodata/download_chirts` | `CHIRTSDownloader` | Daily 0.05°, 1983–present |
| Solar radiation, RH, wind speed, temperature | **NASA POWER** | `aggeodata/download_nasa_power` | `NASAPowerDownloader` | Handles any parameter code; routes to S3 or REST automatically |
| Hourly RH (06/09/12/15/18 UTC) | **AgERA5** | `aggeodata/download_agera5` | `AgEra5Downloader` | CDS key required; vars: `relative_humidity_06/09/12/15/18` |
| Vapour pressure | **AgERA5** | `aggeodata/download_agera5` | `AgEra5Downloader` | CDS key required; var: `vapour_pressure` |
| Vapour pressure deficit | **AgERA5** | `aggeodata/download_agera5` | `AgEra5Downloader` | CDS key required; var: `vapour_pressure_defficit` |
| Reference ET | **AgERA5** | `aggeodata/download_agera5` | `AgEra5Downloader` | CDS key required; var: `reference_evapotranspiration` |
| Dew point | **AgERA5** | `aggeodata/download_agera5` | `AgEra5Downloader` | CDS key required; var: `dew_point_temperature` |

When multiple variables share the same source, group them into a single tool call where possible.  
**Exception:** each AgERA5 variable requires its own `download_agera5` call (one variable per call).

## GEE routing (when user chooses GEE)

When the user selects GEE, all variables route through `source: gee` in the YAML. The downloader picks the correct GEE collection automatically:

| CF variable | GEE collection | GEE band |
|-------------|---------------|----------|
| `pr` | `UCSB-CHG/CHIRPS/DAILY` | `precipitation` |
| `tasmax` | `UCSB-CHG/CHIRTS/DAILY` | `Tmax` |
| `tasmin` | `UCSB-CHG/CHIRTS/DAILY` | `Tmin` |
| `tas` | `projects/climate-engine-pro/assets/ce-ag-era5-v2/daily` | `Temperature_Air_2m_Mean_24h` (K→°C) |
| `tdps` | `projects/climate-engine-pro/assets/ce-ag-era5-v2/daily` | `Dew_Point_Temperature_2m_Mean_24h` (K→°C) |
| `rsds` | `projects/climate-engine-pro/assets/ce-ag-era5-v2/daily` | `Solar_Radiation_Flux` |
| `vp` | `projects/climate-engine-pro/assets/ce-ag-era5-v2/daily` | `Vapour_Pressure_Mean_24h` |
| `etr` | `projects/climate-engine-pro/assets/ce-ag-era5-v2/daily` | `ReferenceET_PenmanMonteith_FAO56` |

**Note:** hourly RH (`hurs_06/09/12/15/18`), VPD, and wind speed are not yet in the GEE routing table. Fall back to AgERA5 for those.

---

# BACKEND: ZARR DATACUBES VS PER-FILE ENDPOINTS

Routing decides *which archive*. `use_zarr` decides *how it is read*, and it is the single
biggest lever on how long a download takes.

The official endpoints hand out **one file per day** for CHIRPS and CHIRTS — throttled to a
single connection — and **queue one request per year** for AgERA5. A three-year, three-variable
request is thousands of sequential HTTP round trips or a morning in the CDS queue. The same
archives are published as consolidated **Zarr datacubes**, where a bounding box plus a date
range is one indexed read.

| Source | Zarr store | Credentials |
|--------|-----------|-------------|
| CHIRPS v3 daily | `aaguilar90/chirps-v3-daily-rnl` (Hugging Face) | none |
| CHIRTS-ERA5 daily | `aaguilar90/chirts-era5-daily` (Hugging Face) | none |
| AgERA5 | ECMWF ARCO datastore | the same `~/.cdsapirc` key |

Turn it on in `general`, where it applies to every CHIRPS / CHIRTS / AgERA5 variable in the plan:

```yaml
general:
  use_zarr: true
```

or per variable, which overrides the general default:

```yaml
climate:
  variables:
    pr:
      source: chirps
      use_zarr: true
    tasmax:
      source: chirts
      use_zarr: false        # this one stays on the UCSB servers
    rsds:
      source: agera5
      use_zarr: true
      agera5_chunking: geo   # "geo" (default) | "time"
```

**The default is `false`** — opt in deliberately, and say so in the plan. Both backends write
the **same per-day NetCDF layout in the same native units**, so the datacube step is unchanged
either way.

## When NOT to use it

`use_zarr` is valid only for `chirps`, `chirts`, and `agera5`; setting it on `nasa_power` or
`gee` raises a validation error. Four more cases where the per-file endpoint is the right answer:

- **`chirts_source: chirts`** (the original CHIRTS-daily v1.0) — the mirror carries CHIRTS-**ERA5**
  only, and the combination is rejected outright.
- **Monthly frequency** — the mirrors are daily only; also rejected.
- **Continuing an existing time series** that was downloaded from UCSB. The two backends serve
  *different precipitation products*: the mirror is CHIRPS v3 (station-blended), the UCSB v3
  endpoint in this package is CHIRP v3 (satellite-only, no station blending). Pick one and keep
  it for the whole series.
- **Adding days to a folder that already holds per-file downloads.** Server-side clipping can
  keep one extra edge pixel that the Zarr coordinate slice drops, so the per-day grids differ.
  The downloader warns when it spots this; don't mix backends inside one variable folder.

Two smaller differences worth stating when you propose it: mirror temperatures are stored
rounded to **0.1 °C** (the UCSB GeoTIFFs are full float32, max difference 0.05 °C), and the
AgERA5 ARCO store exposes the 16 variables aggeodata maps today.

`use_huggingface` and `hf_url` are still accepted as aliases for `use_zarr` and `zarr_url`.

---

# MCP TOOLS AVAILABLE

These tools are exposed by the `aggeodata` MCP server:

| Tool | What it does |
|------|-------------|
| `aggeodata/list_admin_units` | Lists province/district names for a country |
| `aggeodata/download_chirps` | Downloads CHIRPS daily precipitation → clipped NetCDF |
| `aggeodata/download_chirts` | Downloads CHIRTS-ERA5 daily Tmax/Tmin → clipped NetCDF |
| `aggeodata/download_agera5` | Downloads one AgERA5 variable via CDS API → clipped NetCDF |
| `aggeodata/download_nasa_power` | Downloads NASA POWER via S3 Zarr → clipped NetCDF (fast, no rate limits) |

---

# STEP-BY-STEP WORKFLOW

## Step 1 — Collect parameters

Ask these before doing anything else. Accept "I don't know" gracefully and apply defaults.

| Parameter | Question | Default |
|-----------|----------|---------|
| Country | Full name or ISO3 code? | **required** |
| Variables | What climate variables? (precipitation, Tmax/Tmin, humidity, solar radiation, ET, wind speed…) | **required** |
| Date range | Start and end date (YYYY-MM-DD)? | **required** |
| Region | Full country or specific province/department? | full country |
| Admin level | If sub-country: level 1 (province/region) or level 2 (district)? | 1 |
| Output folder | Where to save files? **No spaces in path.** | **required** |
| **Download source** | Use default sources (CHIRPS/CHIRTS/AgERA5/NASA POWER) **or Google Earth Engine (GEE)**? | default |
| **Backend** | Read CHIRPS/CHIRTS/AgERA5 from the fast Zarr datacubes (`use_zarr: true`)? | propose `true` — see below |
| **What is the cube for?** | Analysis/slicing, or feeding a crop model? | decides `output_format` — see below |
| CPU cores | Parallel download workers? | derived from the backend — see the ncores rule |

### When to propose `use_zarr: true`

Propose it by default for any CHIRPS / CHIRTS / AgERA5 request and say what it buys: one
indexed read instead of a file per day or a year in the CDS queue, and `ncores: 4` instead of
`1`. On a multi-year request the difference is hours.

Do **not** propose it, and say why, when the user is:
- continuing or extending a time series already downloaded from UCSB (different precipitation
  product; mixed grids in one folder),
- asking for the original CHIRTS-daily v1.0 (`chirts_source: chirts`) or monthly data — both
  rejected by the Zarr backend,
- requesting only `nasa_power` or `gee` variables, where the option does not apply.

If the user has been rate-limited by `data.chc.ucsb.edu`, `use_zarr: true` is the better answer
than GEE: same archive, no authentication, no project ID.

### Ask what the cube is for

`use_zarr` and `output_format` are different decisions that happen to share a word. The first is
how the data is **downloaded**; the second is how the stacked cube is **written**, and it is the
one that can break the next tool in the chain.

This skill writes a Zarr v3 store by default. **`ag-cube-cm` cannot read one** — so if the answer
to "what will you do with it?" involves DSSAT, crop modelling, or the `spatial-crop-modeler`
skill, set `output_format: "both"` and say why. When the user has no particular destination in
mind, `both` is the forgiving choice. See *Datacube output format* in the technical notes.

Alternatively, accept a **bounding box** `[xmin, ymin, xmax, ymax]` in EPSG:4326 instead of a country/region — pass it as the `bbox` parameter.

### When to ask about GEE

Always ask the source question when any of these is true:
- The user mentions being **rate-limited or banned** from `data.chc.ucsb.edu`
- The user explicitly mentions **Google Earth Engine** or **GEE**
- The variables requested are **all covered by GEE** (`pr`, `tasmax`, `tasmin`, `tas`, `tdps`, `rsds`, `vp`, `etr`)

If none apply, default to the standard sources silently.

### If the user chooses GEE — ask two follow-up questions

1. **GEE project ID** — "Do you have a GEE cloud project ID? (e.g. `my-gee-project`). Leave blank if you are using a legacy account."
2. **Authentication** — "Have you run `earthengine authenticate` on this machine before?"  
   If no: instruct them to run `! earthengine authenticate` in the terminal before proceeding.

## Step 2 — Show the routing plan and confirm

Before calling any tool, display the mapping using an ASCII box table and ask for confirmation.

**Default sources example:**
```
┌─────────────────┬─────────────┬───────────────────────────────────────────────┐
│    Variable     │   Source    │                     Tool                      │
├─────────────────┼─────────────┼───────────────────────────────────────────────┤
│ Precipitation   │ CHIRPS      │ download_chirps                               │
├─────────────────┼─────────────┼───────────────────────────────────────────────┤
│ Tmax / Tmin     │ CHIRTS-ERA5 │ download_chirts                               │
├─────────────────┼─────────────┼───────────────────────────────────────────────┤
│ Solar radiation │ AgERA5      │ download_agera5 (solar_radiation)             │
├─────────────────┼─────────────┼───────────────────────────────────────────────┤
│ RH 06:00        │ AgERA5      │ download_agera5 (relative_humidity_06)        │
├─────────────────┼─────────────┼───────────────────────────────────────────────┤
│ Reference ET    │ AgERA5      │ download_agera5 (reference_evapotranspiration)│
└─────────────────┴─────────────┴───────────────────────────────────────────────┘

Country: Ghana | Period: 2020-01-01 → 2022-12-31 | Output: D:/data/ghana_climate
Download: Zarr datacubes (use_zarr: true) | ncores: 4
Cube:     Zarr v3 store, zstd codec (open with open_cube; not readable by ag-cube-cm)

Note: AgERA5 is in the plan — do you have ~/.cdsapirc configured? The same key
authenticates the ARCO Zarr store, so nothing extra is needed.
Shall I proceed, or would you like to change any source?
```

**GEE source example:**
```
┌─────────────────┬────────────┬─────────────────────────────────────────────────────────────────┐
│    Variable     │   Source   │                         GEE Collection                          │
├─────────────────┼────────────┼─────────────────────────────────────────────────────────────────┤
│ Precipitation   │ GEE        │ UCSB-CHG/CHIRPS/DAILY                                           │
├─────────────────┼────────────┼─────────────────────────────────────────────────────────────────┤
│ Tmax            │ GEE        │ UCSB-CHG/CHIRTS/DAILY                                           │
├─────────────────┼────────────┼─────────────────────────────────────────────────────────────────┤
│ Solar radiation │ GEE        │ projects/climate-engine-pro/assets/ce-ag-era5-v2/daily           │
├─────────────────┼────────────┼─────────────────────────────────────────────────────────────────┤
│ Reference ET    │ GEE        │ projects/climate-engine-pro/assets/ce-ag-era5-v2/daily           │
└─────────────────┴────────────┴─────────────────────────────────────────────────────────────────┘

Country: Ghana | Period: 2020-01-01 → 2022-12-31 | Output: D:/data/ghana_climate
GEE project: my-gee-project | No server rate limits apply.

Shall I proceed?
```

Include the "Note: AgERA5..." line only when AgERA5 (not GEE) appears in the plan.  
Include the "GEE project:" line only when GEE is in the plan.

Only continue once the user confirms.

## Step 3 — Environment check

Before the first tool call, verify:
- `aggeodata` package is installed with download extras (see below)
- If AgERA5 is in the plan: CDS API key is configured (see below)
- If GEE is in the plan: `earthengine-api` is installed and `earthengine authenticate` has been run
- Output folder path has **no spaces**

## Step 4 — Generate YAML config and run pipeline

**Always use the YAML pipeline, never call downloaders directly.**  
Direct API calls bypass the rate-limit safeguards and have caused CrowdSec bans on `data.chc.ucsb.edu`.

### ncores rule (critical)

**`ncores` depends on the backend, not only on the source.** The cap on CHIRPS and CHIRTS
exists because `data.chc.ucsb.edu` bans more than one connection — a rule about *that server*.
With `use_zarr: true` no request reaches it, so the cap does not apply and parallel workers
fetch concurrent time-batches instead.

| Sources in plan | `use_zarr` | ncores | Reason |
|-----------------|-----------|--------|--------|
| CHIRPS or CHIRTS present | `false` | **1** | CrowdSec bans >1 worker on data.chc.ucsb.edu |
| CHIRPS or CHIRTS present | `true` | 4 | Hugging Face Zarr store; workers read concurrent time-batches |
| AgERA5 only | either | 4 | CDS queues in parallel; the ARCO store reads in parallel |
| NASA POWER only | n/a | 1 | S3 Zarr backend; ncores ignored |
| GEE (any variable) | n/a | **1** | GEE writes per-day GeoTIFFs through HDF5 without parallel I/O — `ncores > 1` crashes downstream models (e.g. ag-cube-cm) |

When mixing GEE with anything else, always set `ncores: 1`. When mixing CHIRPS/CHIRTS with
anything else, set `ncores: 1` **unless every CHIRPS/CHIRTS variable in the plan reads from
Zarr** — one per-file variable in the plan reinstates the cap for the whole run.

### Install (run once)

```bash
pip install "aggeodata[download] @ git+https://github.com/CGIAR-Climate-Data-Hub/aggeodata.git" s3fs zarr
```

### Resolve country → extent (skip if bbox given)

Use the `run_command` tool to run python or write a temporary script to execute this:

```python
from aggeodata.ingestion.boundaries import _fetch_geojson_cached
gdf = _fetch_geojson_cached("{ISO3}", 0)
extent = [round(v, 4) for v in gdf.total_bounds.tolist()]
# extent = [xmin, ymin, xmax, ymax]
```

### Generate the YAML config

Build the config file from the confirmed plan. Use CF variable names as keys under `climate.variables`. Write the configuration to file using `write_to_file`.

Section keys are **lowercase canonical** (`dates`, `spatial_info`, `climate`,
`soil`, `general`, `paths`). The historical UPPERCASE keys (`DATES`,
`SPATIAL_INFO`, …) are still accepted as input aliases so old YAMLs keep
working, but new configs should use the lowercase form — that's the same
shape consumed by `spatial-crop-modeler`'s `full_pipeline`, so blocks
copy-paste cleanly between the two skills.

```yaml
dates:
  starting_date: "{START}"   # YYYY-MM-DD
  ending_date:   "{END}"

spatial_info:
  spatial_file: null
  extent: [{XMIN}, {YMIN}, {XMAX}, {YMAX}]  # from extent resolution above

climate:
  variables:
    pr:
      source: chirps
    tasmax:
      source: chirts
    tasmin:
      source: chirts
    rsds:
      source: nasa_power   # or agera5 — per user confirmation

soil:
  enabled: false

general:
  suffix:              "{SUFFIX}"   # short label, no spaces
  use_zarr:            true         # Zarr datacubes for chirps/chirts/agera5 — far faster.
                                    # false = official per-file endpoints. Default: false.
  ncores:              4            # 4 with use_zarr: true; 1 when any chirps/chirts
                                    # variable still reads from UCSB, or when GEE is present
  task:                "download"
  reference_variable:  "pr"
  agera5_version:      "2_0"
  nasa_power_backend:  "s3"         # "s3" (Zarr, default, fast) | "rest" (tile API)
  # Datacube output. Package defaults are "netcdf" + "blosc"; this skill defaults to
  # a Zarr v3 store with the zstd codec, because that is the combination GDAL, QGIS
  # and R terra can actually open. See "Datacube output format" below before changing
  # it — a cube destined for ag-cube-cm must be netcdf.
  output_format:       "zarr"       # "zarr" | "netcdf" | "both"
  zarr_codec:          "zstd"       # "zstd" (readable outside Python) | "blosc" (smaller)
  zarr_quantize:       true         # scaled integers; false = exact float32
  zarr_sharded:        false        # keep false — GDAL cannot read sharded stores

paths:
  output_path: "{OUTPUT}"
```

**CF variable → valid source mapping** (schema-enforced — wrong pairs will raise a validation error):

| CF variable | Valid sources |
|-------------|--------------|
| `pr` | `chirps`, `agera5`, `nasa_power`, `gee` |
| `tasmax` / `tasmin` | `chirts`, `agera5`, `nasa_power`, `gee` |
| `tas` | `agera5`, `nasa_power`, `gee` |
| `rsds` | `agera5`, `nasa_power`, `gee` |
| `vp` | `agera5`, `gee` |
| `etr` | `agera5`, `gee` |
| `tdps` | `agera5`, `gee` |
| `hurs`, `hurs_06/09/12/15/18` | `agera5` |
| `vpd`, `sfcWind` | `agera5` |

**GEE YAML template** (when user selects GEE):

```yaml
dates:
  starting_date: "{START}"
  ending_date:   "{END}"

spatial_info:
  spatial_file: null
  extent: [{XMIN}, {YMIN}, {XMAX}, {YMAX}]

climate:
  variables:
    pr:
      source: gee
      gee_project: "{GEE_PROJECT}"   # omit if legacy account / already initialised
    tasmax:
      source: gee
      gee_project: "{GEE_PROJECT}"
    rsds:
      source: gee
      gee_project: "{GEE_PROJECT}"
    etr:
      source: gee
      gee_project: "{GEE_PROJECT}"

soil:
  enabled: false

general:
  suffix:   "{SUFFIX}"
  ncores:   1            # GEE requires ncores=1 — HDF5 writer is not parallel-safe
  task:     "download"

paths:
  output_path: "{OUTPUT}"
```

Omit `gee_project` lines entirely if the user left the project blank (legacy account).  
Repeat `gee_project` under each variable — it is a per-variable field in the schema.

### `reference_variable` (required, never `null`)

`general.reference_variable` is a non-null string identifying one of the enabled
`climate.variables` (default: `pr` if precipitation is present, otherwise the first
listed variable). Climate-only YAMLs always have at least one valid choice here.

For **soil data** (SoilGrids), don't extend this pipeline — use the dedicated
`soil-data-download` skill, which handles the soil-only YAML schema, the SoilGrids CRS
gotcha, and cube validation. For **mixed climate + soil** (e.g. crop modeling), use
the `spatial-crop-modeler` skill.

### Run the pipeline

Execute this using python via `run_command`:

```python
from aggeodata.pipelines.download import run_download
results = run_download("{OUTPUT}/config.yaml")
```

Or from the command line using `run_command`:
```bash
python -m aggeodata.pipelines.download {OUTPUT}/config.yaml
```

Save the YAML to `{OUTPUT}/config.yaml` before calling `run_download`.

**Skip/resume:** aggeodata automatically skips files that already exist on disk. Re-run safely after interruptions.

## Step 5 — Summary

When all downloads are done, show a table:

```
Download complete:

| Variable      | Source      | Output path                           | Status  |
|---------------|-------------|---------------------------------------|---------|
| Precipitation | CHIRPS      | D:/data/ghana_climate/chirps/...      | ✓ OK    |
| Tmax / Tmin   | CHIRTS-ERA5 | D:/data/ghana_climate/chirts/...      | ✓ OK    |
| Solar rad.    | NASA POWER  | D:/data/ghana_climate/nasa_power/...  | ✓ OK    |
| RH 06:00      | AgERA5      | D:/data/ghana_climate/agera5/...      | ✓ OK    |
```

Then ask:

```
All files downloaded. Would you like to create a datacube by stacking these into a single aligned multi-variable NetCDF?

| Setting            | Default                  |
|--------------------|--------------------------|
| Target resolution  | coarsest                 |
| Resampling method  | bilinear                 |
| Output file        | {OUTPUT}/datacube.nc     |

Shall I proceed with the datacube, or change any of these settings?
```

Only continue to datacube creation once the user confirms. If confirmed, invoke the `geospatial-cube-processor` skill (`stack_datasets` function) using the downloaded NetCDF paths.

---

# ENVIRONMENT SETUP

## Package installation

```bash
# From the aggeodata project root:
pip install -e ".[download,mcp]"
# [download] adds: cdsapi (AgERA5), s3fs + zarr (NASA POWER S3, and the
#            CHIRPS/CHIRTS/AgERA5 Zarr datacubes behind use_zarr)
# [mcp]      adds: mcp[cli] for the MCP server

# Or install directly from GitHub:
pip install "aggeodata[download,mcp] @ git+https://github.com/CGIAR-Climate-Data-Hub/aggeodata.git"
```

If only CHIRPS, CHIRTS, or NASA POWER are needed (no AgERA5):
```bash
pip install -e ".[mcp]"
```

## CDS API key — required only if AgERA5 is in the plan

Register free at https://cds.climate.copernicus.eu/ then create `%USERPROFILE%\.cdsapirc` (Windows) or `~/.cdsapirc` (Linux/Mac):

```
url: https://cds.climate.copernicus.eu/api
key: <YOUR-UID>:<YOUR-API-KEY>
```

Quick check:
```python
import cdsapi; cdsapi.Client()   # should print "Welcome to the CDS"
```

## Output folder — no spaces

Paths **must not contain spaces**. Spaces corrupt rasterio's HTTP range requests on Windows.

- BAD:  `D:/OneDrive - CGIAR/data`
- GOOD: `D:/data/climate` or `C:/tmp/aggeodata`

---

# TECHNICAL NOTES

## Datacube output format

`run_datacube` writes the stacked cube as a **Zarr v3 store** by default in this skill
(`output_format: "zarr"`), laid out like the published GeoSPOptimizer archives — same chunk
geometry, codec and integer quantisation — so a cube built here matches the CHIRPS / CHIRTS /
AgERA5 datacubes and can be sliced without reading the whole thing.

| Option | This skill | Package default | Why |
|--------|-----------|-----------------|-----|
| `output_format` | `zarr` | `netcdf` | chunked, sliceable, matches the published archives |
| `zarr_codec` | `zstd` | `blosc` | `blosc` gives *"blosc compressor not available"* in GDAL/QGIS/R `terra`; `zstd` opens fine |
| `zarr_quantize` | `true` | `true` | scaled integers, roughly half the payload, quanta far finer than the products' own uncertainty |
| `zarr_sharded` | `false` | `false` | GDAL rejects `sharding_indexed` |

**What `run_datacube` returns changes with the format.** `zarr` returns the `.zarr` **directory**
path; `netcdf` and `both` return the `.nc` file path. Code that assumes a file will mis-handle a
store.

**Reading it back** — a Zarr store is not a NetCDF file, so `xr.open_dataset(path)` does not work:

```python
from aggeodata.transform.zarr_export import open_cube
ds = open_cube("climate_hnd_2020_2020.zarr")   # float32, spatial_ref promoted, ds.rio.crs resolves
```

`open_cube` uses `xr.open_zarr(consolidated=True, decode_coords="all")` and casts back to float32 —
the CF decoder would otherwise promote the quantised variables to float64 and double the payload.

### When to use `netcdf` or `both` instead

**`ag-cube-cm` cannot open a Zarr store.** Its loader accepts `.nc`, `.tif` and `.pkl` only, and
raises `ValueError: Unsupported file extension '.zarr'`. So whenever the cube is headed for
`spatial-crop-modeler`'s `with_cubes` mode, or for DSSAT by any other route, set:

```yaml
general:
  output_format: "both"    # or "netcdf"
```

`both` writes the store *and* the `.nc`, and returns the `.nc` path — the safe choice when you do
not know where the cube will end up. Ask the user what the cube is for before accepting the Zarr
default; "I want to run a crop model with it" is the answer that changes it.

Other reasons to choose `netcdf`: a downstream tool that only reads NetCDF, or a single small cube
a colleague will open by double-clicking.

## CHIRPS / CHIRTS rate limit
Applies to the **per-file backend only**. Workers are hard-capped at **1** to avoid HTTP 403 from `data.chc.ucsb.edu`. If the user has been rate-limited or banned (403 on all requests), the first answer is **`use_zarr: true`** — the Hugging Face mirrors are a different host entirely, need no authentication, and lift the worker cap. `source: gee` remains an alternative but costs an authenticated account and a project ID. Waiting 24–48 hours is the last resort, not the first suggestion.

## Google Earth Engine (GEE)

GEE has no per-IP connection ban. It uses `getDownloadURL` to pull a clipped GeoTIFF for each day, so it works for any AOI size up to ~10 M pixels. For very large extents at full resolution you may hit GEE's pixel limit — reduce `scale` in `_DATASET_CONFIGS` or clip the extent.

**Authentication (once per machine):**
```bash
pip install earthengine-api
earthengine authenticate   # opens browser; saves token to ~/.config/earthengine/
```

**Project ID:** new GEE accounts (post-2023) require a cloud project. Find it at console.cloud.google.com. Legacy accounts can leave `gee_project` blank.

**Quick check:**
```python
import ee; ee.Initialize(); print(ee.String("GEE OK").getInfo())
```

## NASA POWER — S3 Zarr backend
`download_nasa_power` reads directly from the NASA POWER public S3 Zarr store. No REST API tiling, no rate limits, no API key needed. Coverage: 1981–2029.

| Variable | Code |
|----------|------|
| Solar radiation (shortwave) | `ALLSKY_SFC_SW_DWN` |
| Relative humidity at 2 m | `RH2M` |
| 2 m temperature max | `T2M_MAX` |
| 2 m temperature min | `T2M_MIN` |
| Wind speed at 2 m | `WS2M` |
| Precipitation | `PRECTOTCORR` |

## AgERA5 downloads by year
**Per-file backend only** — with `use_zarr: true` the ARCO store is read directly and there is no queue at all. Otherwise: the CDS API queues one request per year. Multi-year ranges run in parallel (`ncores` controls this). Each year may take 5–30 minutes depending on CDS queue load. Use `ncores=2` on shared machines. Already-downloaded years are skipped automatically.

## CHIRTS-ERA5 vs original CHIRTS
- `chirts_source="era5"` (default) — CHIRTS-ERA5 experimental reanalysis. Coverage: **1983–present**.
- `chirts_source="chirts"` — original CHIRTS-daily v1.0. Coverage: **1983–2016** only.
  Not available from the Zarr mirror: `chirts_source: chirts` with `use_zarr: true` is
  rejected. Use the per-file backend for it.

## Sub-country downloads
Always confirm admin unit spelling with `list_admin_units` before passing `feature_name`. Clips reduce file sizes by 10–100× vs full country.

## AgERA5 variable keys

When the plan includes AgERA5, read [`references/python_api.md`](references/python_api.md)
(section 5) for the full list of `variable` keys accepted by `download_agera5` and
`AgEra5Downloader.download(...)` — covers temperature, solar radiation, wind speed,
vapour pressure, hourly relative humidity (06/09/12/15/18 UTC), dew point, and
reference ET.

---

# EXAMPLE — GEE source (after UCSB ban)

**User:** I keep getting banned from data.chc.ucsb.edu. Can you download precipitation and temperature via GEE instead?

**You:**
```
Sure — Google Earth Engine serves the same CHIRPS and CHIRTS data with no rate limits.

Before I proceed, two quick questions:
1. Do you have a GEE cloud project ID? (e.g. `my-gee-project` — find it at console.cloud.google.com)
2. Have you run `earthengine authenticate` on this machine?
   If not, run: ! earthengine authenticate
```

**User:** project is `cgiar-climate`, yes I've authenticated.

**You:**
```
Here's the plan:

┌───────────────┬────────┬──────────────────────────────┐
│   Variable    │ Source │       GEE Collection          │
├───────────────┼────────┼──────────────────────────────┤
│ Precipitation │ GEE    │ UCSB-CHG/CHIRPS/DAILY        │
├───────────────┼────────┼──────────────────────────────┤
│ Tmax / Tmin   │ GEE    │ UCSB-CHG/CHIRTS/DAILY        │
└───────────────┴────────┴──────────────────────────────┘

GEE project: cgiar-climate | ncores: 1 (HDF5 writer not parallel-safe) | No UCSB rate limits.
Shall I proceed?
```

[After confirmation: generate YAML with `source: gee` and `gee_project: cgiar-climate` for each variable, call run_download]

---

# RESPONSE STYLE
- Keep confirmations brief — show the routing table, get a yes/no, proceed.
- After each tool call: 2 sentences — what landed on disk and the output path.
- On error: quote the error message, diagnose (missing CDS key, spaces in path, rate limit), suggest the fix.
- After all downloads complete, point the user to the datacube-stack skill for the next step.
