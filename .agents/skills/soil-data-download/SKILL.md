---
name: soil-data-download
description: "Downloads SoilGrids global soil property rasters (clay, sand, silt, bulk density, organic carbon, pH, water content at multiple depths) — by default SoilGrids v2 at 1 km from its Zarr datacube on Hugging Face, or 250 m from ISRIC on request — and optionally stacks them into a validated soil datacube. Trigger this skill whenever the user mentions SoilGrids, soil texture, soil organic carbon, soil pH, soil water retention, soil depth layers (`0-5`, `5-15`, `15-30`, `30-60`, `60-100` cm), or asks to download / build / stack soil data for any country, region, or bounding box — even if they don't say 'SoilGrids' explicitly (e.g. 'I need clay and sand for Malawi', 'soil cube for Mzimba', 'download soil data for the Sahel'). Also trigger when the user hits a `reference_variable: non-null string required` schema error trying to use `climate-data-download` for soil — that pipeline is climate-only; this skill handles the soil path. Do NOT trigger for climate variables (precipitation, temperature, RH, ET) — use `climate-data-download` for those."
license: "MIT"
---

# Soil Data Download

You orchestrate `aggeodata`'s SoilGrids downloader and the soil cube builder. The
user tells you what soil properties they need and over which area — you decide
which API to use (YAML pipeline or direct Python), download the rasters, and
optionally stack them into a validated NetCDF datacube that downstream tools
(`spatial-crop-modeler`, `geospatial-cube-processor`) can consume directly.

This skill is the soil counterpart to `climate-data-download`. For **mixed
climate + soil** (e.g. crop modeling), use `spatial-crop-modeler` instead — it
runs both via `ag-cube-cm`'s combined schema.

---

# WHAT SOILGRIDS PROVIDES

SoilGrids 2.0 is the only soil source `aggeodata` routes to. It comes from one of two
backends, chosen with `backend=`:

| Backend | Where | Resolution | Speed |
|---------|-------|------------|-------|
| **`hf` (default)** | SoilGrids v2 1 km Zarr datacube on Hugging Face — https://huggingface.co/datasets/aaguilar90/soilgrids-v2-1km | **1 km (1/120°) for every variable**, EPSG:4326 | one read per variable covers all depths — seconds for a district, about a minute for a country |
| `isric` | ISRIC's WCS coverage API (VRT fallback) + 1 km hydraulic bucket | 250 m texture & chemistry, 1 km `wv*` | one HTTP request per variable × depth — minutes |

**Use `hf` unless the user asks for 250 m / "high resolution" / ISRIC directly**, or is
mapping soil at field scale where 250 m detail is the point. Don't ask otherwise —
state the default in the plan so they can change it.

Variables (both backends; units are ISRIC's mapped units, as stored in the files):

| Variable | Description | Default? |
|----------|-------------|----------|
| `clay`   | Clay content (g/kg)                    | yes |
| `sand`   | Sand content (g/kg)                    | yes |
| `silt`   | Silt content (g/kg)                    | yes |
| `bdod`   | Bulk density (cg/cm³)                  | yes |
| `cfvo`   | Coarse fragments volumetric (cm³/dm³)  | yes |
| `soc`    | Soil organic carbon (dg/kg)            | yes |
| `phh2o`  | pH in H₂O (× 10)                       | yes |
| `nitrogen` | Total nitrogen (cg/kg)               | optional |
| `cec`    | Cation exchange capacity (mmol(c)/kg)  | optional |
| `wv0010` | Volumetric water content at 10 kPa (10⁻³ cm³/cm³)                   | crop modeling |
| `wv0033` | Volumetric water content at 33 kPa, field capacity (10⁻³ cm³/cm³)   | crop modeling |
| `wv1500` | Volumetric water content at 1500 kPa, wilting point (10⁻³ cm³/cm³)  | crop modeling |

Divide by 10 for %, g/kg → g/100 g, etc. (`bdod` and `nitrogen` by 100). The files
are identical in layout and units whichever backend wrote them, so the cube builder
and `spatial-crop-modeler` do not care which was used.

**With `hf`, every variable is on the same 1 km grid** — the reference variable does
not resample anything and the 250 m / 1 km discussion below does not apply.

**With `isric`, the resolution split is the thing to tell the user about.** A request
mixing texture with water content produces a cube at **one** resolution — whichever
`reference_variable` names — so one group is always resampled:

- `reference_variable: sand` (or any 250 m variable) → the water layers are upsampled
  from 1 km. The extra pixels are replicated, not measured; the cube looks sharper than
  the water data actually is.
- `reference_variable: wv1500` (the package default) → the texture layers are
  downsampled to 1 km. Nothing is invented, but real 250 m detail is averaged away.

Neither is wrong. For crop modeling the cube is usually resampled onto a coarser climate
grid anyway (CHIRPS is 5 km), so `wv1500` costs nothing and avoids fake precision. For
soil mapping, where texture detail is the point, prefer a 250 m reference. Say which you
picked and why.

**Not available**: `ocd` (organic carbon density) and `ocs` (organic carbon stocks) are
routed by neither backend. Asking for them logs `Unknown SoilGrids variable` and
**silently produces no file** — the run appears to succeed with those layers simply
absent. Do not offer them; if the user asks, say they are not wired up rather than
letting the gap show up later as a missing variable.

**Standard depths**: `0-5`, `5-15`, `15-30`, `30-60`, `60-100` cm. The `hf` store
holds exactly these five; `100-200` exists only at ISRIC, and the downloader fetches
it from there automatically (at 250 m for texture/chemistry) with a warning.

**CRS**: `hf` files are already EPSG:4326. `isric` files are in Interrupted Goode
Homolosine — **reproject explicitly to `EPSG:4326`** to use the cube with climate
data. Step 4 passes both CRS arguments, which is correct for either backend.

---

# STEP-BY-STEP WORKFLOW

## Step 0 — Environment check

Before doing anything else, run:

```bash
python -c "
import importlib.metadata, sys
for pkg in ['aggeodata']:
    try:
        print('OK', pkg, importlib.metadata.version(pkg))
    except importlib.metadata.PackageNotFoundError:
        print('MISSING', pkg); sys.exit(1)
"
```

If missing, install:

```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/CGIAR-Climate-Data-Hub/aggeodata.git"
```

## Step 1 — Collect parameters

| Parameter | Question | Default |
|-----------|----------|---------|
| Country / bbox | ISO3 code, country name, or `[xmin, ymin, xmax, ymax]` in EPSG:4326? | **required** |
| Source | Backend — see the table above | `hf` (SoilGrids v2 1 km Zarr). Switch to `isric` only on request |
| Variables | Which soil properties? | the 10 rows marked *yes* or *crop modeling* above. `ocd` / `ocs` are not available — do not offer them |
| Depths | Which depth layers? | all five (`0-5`, `5-15`, `15-30`, `30-60`, `60-100`) |
| Output folder | Where to save? **No spaces in path.** | **required** |
| Build cube? | Stack the downloaded rasters into a single NetCDF? | yes |
| Reference variable | The variable whose grid defines the cube's resolution. With `hf` all variables share one grid, so any works; with `isric` see the 250 m / 1 km split above | `wv1500` (package default; with `isric`, use a 250 m variable when texture detail is the point) |

If the user gives a country name, resolve to ISO3 + bounding box:

```python
from aggeodata.ingestion.boundaries import _fetch_geojson_cached
gdf = _fetch_geojson_cached("MWI", 0)        # ISO3, admin level 0
extent = [round(v, 4) for v in gdf.total_bounds.tolist()]   # [xmin, ymin, xmax, ymax]
```

## Step 2 — Show the plan and confirm

Display this table and wait for confirmation before downloading:

```
Soil download plan
| Setting     | Value                                                            |
|-------------|------------------------------------------------------------------|
| Source      | SoilGrids v2, 1 km — Hugging Face Zarr (default; say if you want 250 m from ISRIC) |
| Variables   | clay, sand, silt, bdod, cfvo, soc, phh2o, wv0010, wv0033, wv1500 |
| Depths      | 0-5, 5-15, 15-30, 30-60, 60-100 cm                               |
| Extent      | [32.67, -17.13, 35.92, -9.36]  (Malawi)                          |
| Output      | data/malawi/soil_raw                                             |
| Build cube? | yes → data/malawi/soil_malawi.nc                                 |
| Reference   | wv1500                                                           |

50 GeoTIFFs (10 variables × 5 depths), about a minute for a country. Shall I proceed?
```

With `isric`, say instead: "~50 requests, 5–15 min depending on extent; texture at
250 m, water content at 1 km" and name the reference variable you chose and why.

## Step 3 — Download

Two paths — pick based on whether the user is integrating with the wider `aggeodata`
config pipeline or just wants the rasters.

### Path A — Python API (recommended for soil-only)

Fastest, no schema overhead. Use this by default.

```python
from aggeodata.ingestion.soil import SoilGridsDownloader

dl = SoilGridsDownloader(
    soil_layers=["clay","sand","silt","bdod","cfvo","soc","phh2o","wv0010","wv0033","wv1500"],
    depths=["0-5","5-15","15-30","30-60","60-100"],
    output_folder="{OUTPUT}/soil_raw",
    backend="hf",        # default — SoilGrids v2 1 km Zarr; "isric" for 250 m WCS
)
downloaded = dl.download(boundaries=[{XMIN},{YMIN},{XMAX},{YMAX}])
# returns list[str] of GeoTIFF paths, e.g. .../clay_0-5cm_mean.tif
```

Check the log after it runs. A `Hugging Face SoilGrids store failed … falling back to
ISRIC` or `Fetching N layer(s) from ISRIC instead` warning means those layers came from
ISRIC — tell the user, because texture/chemistry from ISRIC is 250 m, not 1 km.

Use a **new output folder when switching backends**: existing files are reused whichever
backend wrote them, so an old 250 m `clay_0-5cm_mean.tif` would be kept as is.

Full signature is in [`references/python_api.md`](references/python_api.md).

### Path B — YAML pipeline (use when integrating with a climate config)

The `aggeodata` YAML pipeline accepts a `soil` block. **`general.reference_variable`
must be a non-null soil layer name** — use `sand` as the default. Setting it to
`null` or omitting it raises `reference_variable: non-null string required`.

Section keys are lowercase canonical (`spatial_info`, `soil`, `general`,
`paths`); the historical UPPERCASE keys are still accepted as aliases.

```yaml
spatial_info:
  extent: [{XMIN}, {YMIN}, {XMAX}, {YMAX}]
soil:
  enabled:   true
  variables: [clay, sand, silt, bdod, cfvo, soc, phh2o, wv0010, wv0033, wv1500]
  depths:    ["0-5", "5-15", "15-30", "30-60", "60-100"]
  backend:   hf        # default (1 km Zarr); "isric" for 250 m WCS
general:
  suffix:             "{SUFFIX}"
  ncores:             1
  task:               "download"
  reference_variable: sand    # non-null; any enabled soil layer is fine
paths:
  output_path: "{OUTPUT}/soil_raw"
```

Run with:

```python
from aggeodata.pipelines.download import run_download
run_download("{OUTPUT}/config.yaml")
```

`dates` and `climate` may be omitted entirely for soil-only configs.

## Step 4 — Build the soil cube (optional but usually wanted)

Downstream tools want a single multi-variable NetCDF, not loose tiles. Use
`SoilDataCubeBuilder` — **and always pass the CRS explicitly**.

```python
from aggeodata.transform.soil_cube import SoilDataCubeBuilder

# SoilGrids native projection, used only for ISRIC files that lack CRS metadata
# (hf files carry EPSG:4326). Never pass ESRI:54052 — some GDAL builds mis-apply it.
IGH = "+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs"

builder = SoilDataCubeBuilder(
    data_folder="{OUTPUT}/soil_raw",
    variables=["clay","sand","silt","bdod","cfvo","soc","phh2o","wv0010","wv0033","wv1500"],
    reference_variable="wv1500",
    crs=IGH,
    target_crs="EPSG:4326",
)
builder.build_and_save(
    output_path="{OUTPUT}",
    filename="soil_{SUFFIX}.nc",
)
```

**Zarr output.** `build_and_save` also takes `output_format="zarr"` with
`codec="zstd"`, which writes a Zarr v3 store instead of a NetCDF file — the same
format the climate cube can use, so a pipeline can keep one format throughout:

```python
builder.build_and_save(
    output_path="{OUTPUT}",
    filename="soil_{SUFFIX}.zarr",
    output_format="zarr",      # "netcdf" (default) | "zarr"
    codec="zstd",              # "blosc" is smaller; "zstd" is the one GDAL reads
)
```

Two things to know before choosing it. Soil variables are written as **float32, not
scaled integers** — a soil profile has no time axis, so the archive is small enough
that quantisation buys little, and each property would need its own scale. And the
`depth` coordinate is a string (`'0-5'`), a dtype Zarr v3 has no specification for;
Python readers handle it, `ag-cube-cm` opens such a cube directly, but another Zarr
implementation may not. Prefer NetCDF if the cube is going somewhere outside Python.

The `reference_variable` here is the SAME one chosen in Step 1 / 3 — it defines
the cube's reference grid.

## Step 5 — Validate the cube

Always validate before passing the cube to a model. Three checks:

```python
import xarray as xr
soil = xr.open_dataset("{OUTPUT}/soil_{SUFFIX}.nc")

# 1. Flat-format check — older pipelines emit one variable per depth (e.g. clay_0-5cm_mean).
flat_vars = [v for v in soil.data_vars if "_cm_mean" in v]
if flat_vars:
    from aggeodata.transform.soil_cube import reshape_flat_soil_cube
    soil = reshape_flat_soil_cube(soil)
    soil.to_netcdf("{OUTPUT}/soil_{SUFFIX}.nc")   # overwrite with fixed version

# 2. CRS check — coordinates must be in degrees, not projected metres.
assert abs(float(soil.y.min())) < 90,  "Soil y is projected (metres). Rebuild with target_crs='EPSG:4326'."
assert abs(float(soil.x.min())) < 180, "Soil x is projected (metres). Rebuild with target_crs='EPSG:4326'."

# 3. Variable & depth check
expected_vars = {"clay","sand","silt","bdod","cfvo","soc","phh2o","wv0010","wv0033","wv1500"}
missing = expected_vars - set(soil.data_vars)
assert not missing, f"Missing soil variables: {missing}"
print("Soil cube OK:", dict(soil.dims))
```

If a soil cube will be paired with a climate cube downstream, also assert
**extent overlap**:

```python
weather = xr.open_dataset("{OUTPUT}/climate_{SUFFIX}.nc")
assert float(soil.y.min()) <= float(weather.y.max()), "Soil and weather extents don't overlap on Y axis."
assert float(soil.x.min()) <= float(weather.x.max()), "Soil and weather extents don't overlap on X axis."
```

## Step 6 — Summary

Report back to the user:

```
Soil download complete:

| Stage      | Action                                             | Status |
|------------|----------------------------------------------------|--------|
| Download   | {N_VARS} variables × {N_DEPTHS} depths → soil_raw  | ✓ done |
| Build cube | SoilDataCubeBuilder → soil_{SUFFIX}.nc (EPSG:4326) | ✓ done |
| Validate   | flat-format / CRS / variable checks                | ✓ pass |

Output cube: {OUTPUT}/soil_{SUFFIX}.nc
Shape: {DIMS}   (y, x, depth, variable as appropriate)
```

---

# COMMON ISSUES

| Symptom | Cause | Fix |
|---------|-------|-----|
| `reference_variable: non-null string required` | Used the climate YAML schema with `soil.enabled: true` but didn't set `general.reference_variable` | Set `general.reference_variable: sand` (or another enabled soil layer) |
| Cube coordinates are huge numbers (e.g. `y = 1500000`) | (`isric`) The builder kept SoilGrids' native projected CRS | Pass `crs=IGH` and `target_crs="EPSG:4326"` explicitly to `SoilDataCubeBuilder` |
| `no valid index for a 0-dimensional object` when sampling the cube | Cube is in flat format (`clay_0-5cm_mean`, etc.) | Run `reshape_flat_soil_cube(ds).to_netcdf(...)` then reopen |
| `TypeError: ... unexpected keyword argument 'backend'` | The installed `aggeodata` predates the Hugging Face backend | Reinstall with the Step 0 `pip install` command (add `--force-reinstall --no-deps` if pip says it is already satisfied), then rerun |
| `Hugging Face SoilGrids store failed (…); falling back to ISRIC` | Hugging Face unreachable (network, proxy, outage) | The run continues on ISRIC — slower, texture at 250 m. Tell the user; rerun later into a **new** folder for a uniform 1 km set |
| `Extent [...] does not intersect the SoilGrids store` | Box outside 60°S–84°N, or lon/lat swapped | Check the order is `[xmin, ymin, xmax, ymax]` in degrees |
| Downloads fail with HTTP 403 / connection errors (`isric`) | SoilGrids rate limit | Wait, then retry — `SoilGridsDownloader` resumes; existing tiles are skipped |
| `CPLE_AppDefined in wv0010_0-5cm_mean.tif: This file used to have optimizations in its layout, but those have been... invalidated by later changes` (`isric` only) | **Harmless.** The 1 km `wv*` GeoTIFFs in ISRIC's pre-release bucket were written as cloud-optimized files and later edited in place, so part of the COG layout no longer matches. GDAL still reads the data correctly; it just can't use the optimized streaming path, so those reads need more HTTP range requests and run slower | Nothing to fix — reassure the user rather than letting them think the download failed. One line per `wv*` file is expected. To quiet just this message without hiding real GDAL warnings, filter the `rasterio._env` logger on the substring `invalidated by later changes` |
| `UnicodeEncodeError` on Windows | Non-ASCII chars in output path | Use ASCII-only paths (e.g. `D:/data/malawi`) |
| Soil cube doesn't overlap weather cube | Extent rounding or CRS mismatch | Re-clip both to the same bounding box and ensure both are EPSG:4326 |

---

# RESPONSE STYLE

- Show the plan table before doing anything; wait for explicit confirmation.
- After each stage (download, build, validate): one short sentence — what landed
  on disk and the output path.
- On error, quote the message, identify which step (download / build / validate)
  it came from, then propose the specific fix from the table above.
- After the cube is validated, point the user at `geospatial-cube-processor`
  (to clip / aggregate per admin unit) or `spatial-crop-modeler` (if they're
  doing yield simulation next).

---

*Evaluation examples: [evals/evals.json](evals/evals.json)*
