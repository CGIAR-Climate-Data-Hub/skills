---
name: soil-data-download
description: "Downloads SoilGrids global soil property rasters (clay, sand, silt, bulk density, organic carbon, pH, water content at multiple depths) and optionally stacks them into a validated soil datacube. Trigger this skill whenever the user mentions SoilGrids, soil texture, soil organic carbon, soil pH, soil water retention, soil depth layers (`0-5`, `5-15`, `15-30`, `30-60`, `60-100` cm), or asks to download / build / stack soil data for any country, region, or bounding box — even if they don't say 'SoilGrids' explicitly (e.g. 'I need clay and sand for Malawi', 'soil cube for Mzimba', 'download soil data for the Sahel'). Also trigger when the user hits a `reference_variable: non-null string required` schema error trying to use `climate-data-download` for soil — that pipeline is climate-only; this skill handles the soil path. Do NOT trigger for climate variables (precipitation, temperature, RH, ET) — use `climate-data-download` for those."
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

SoilGrids is the only soil source `aggeodata` currently routes to. It serves
global rasters at 250 m, available at six standard depths.

| Variable | Description | Default? |
|----------|-------------|----------|
| `clay`   | Clay content (g/kg)                    | yes |
| `sand`   | Sand content (g/kg)                    | yes |
| `silt`   | Silt content (g/kg)                    | yes |
| `bdod`   | Bulk density (cg/cm³)                  | yes |
| `cfvo`   | Coarse fragments volumetric (cm³/dm³)  | yes |
| `soc`    | Soil organic carbon (dg/kg)            | yes |
| `phh2o`  | pH in H₂O                              | yes |
| `wv0010` | Volumetric water content at 10 kPa     | crop modeling |
| `wv0033` | Volumetric water content at 33 kPa (field capacity) | crop modeling |
| `wv1500` | Volumetric water content at 1500 kPa (wilting point) | crop modeling |
| `nitrogen` | Total nitrogen (cg/kg)               | optional |
| `cec`    | Cation exchange capacity (mmol(c)/kg)  | optional |
| `ocd`    | Organic carbon density (hg/m³)         | optional |
| `ocs`    | Organic carbon stocks (t/ha)           | optional |

**Standard depths**: `0-5`, `5-15`, `15-30`, `30-60`, `60-100` cm (cm).

**Native CRS**: Interrupted Goode Homolosine. **You must reproject explicitly to
`EPSG:4326`** to use the cube with climate data — see Step 4.

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
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git"
```

## Step 1 — Collect parameters

| Parameter | Question | Default |
|-----------|----------|---------|
| Country / bbox | ISO3 code, country name, or `[xmin, ymin, xmax, ymax]` in EPSG:4326? | **required** |
| Variables | Which soil properties? | the 10 "default" / "crop modeling" rows above |
| Depths | Which depth layers? | all five (`0-5`, `5-15`, `15-30`, `30-60`, `60-100`) |
| Output folder | Where to save? **No spaces in path.** | **required** |
| Build cube? | Stack the downloaded rasters into a single NetCDF? | yes |
| Reference variable | The variable whose grid defines the cube's reference resolution | `sand` |

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
| Source      | SoilGrids                                                        |
| Variables   | clay, sand, silt, bdod, cfvo, soc, phh2o, wv0010, wv0033, wv1500 |
| Depths      | 0-5, 5-15, 15-30, 30-60, 60-100 cm                               |
| Extent      | [32.67, -17.13, 35.92, -9.36]  (Malawi)                          |
| Output      | D:/data/malawi/soil_raw                                          |
| Build cube? | yes → D:/data/malawi/soil_malawi.nc                              |
| Reference   | sand                                                             |

~50 raster tiles, 2–10 min depending on extent. Shall I proceed?
```

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
)
downloaded = dl.download(boundaries=[{XMIN},{YMIN},{XMAX},{YMAX}])
# returns {filename: local_path}
```

Full signature is in [`references/python_api.md`](references/python_api.md).

### Path B — YAML pipeline (use when integrating with a climate config)

The `aggeodata` YAML pipeline accepts a `SOIL` block. **`GENERAL.reference_variable`
must be a non-null soil layer name** — use `sand` as the default. Setting it to
`null` or omitting it raises `reference_variable: non-null string required`.

```yaml
SPATIAL_INFO:
  extent: [{XMIN}, {YMIN}, {XMAX}, {YMAX}]
SOIL:
  enabled:   true
  variables: [clay, sand, silt, bdod, cfvo, soc, phh2o, wv0010, wv0033, wv1500]
  depths:    ["0-5", "5-15", "15-30", "30-60", "60-100"]
GENERAL:
  suffix:             "{SUFFIX}"
  ncores:             1
  task:               "download"
  reference_variable: sand    # non-null; any enabled soil layer is fine
PATHS:
  output_path: "{OUTPUT}/soil_raw"
```

Run with:

```python
from aggeodata.pipelines.download import run_download
run_download("{OUTPUT}/config.yaml")
```

`DATES` and `CLIMATE` may be omitted entirely for soil-only configs.

## Step 4 — Build the soil cube (optional but usually wanted)

Downstream tools want a single multi-variable NetCDF, not loose tiles. Use
`SoilDataCubeBuilder` — **and always pass the CRS explicitly**.

```python
from aggeodata.transform.soil_cube import SoilDataCubeBuilder

# SoilGrids native projection — never accept the builder's default ESRI:54052,
# it produces a cube with bad geographic extents.
IGH = "+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs"

builder = SoilDataCubeBuilder(
    data_folder="{OUTPUT}/soil_raw",
    variables=["clay","sand","silt","bdod","cfvo","soc","phh2o","wv0010","wv0033","wv1500"],
    reference_variable="sand",
    crs=IGH,
    target_crs="EPSG:4326",
)
builder.build_and_save(
    output_path="{OUTPUT}",
    filename="soil_{SUFFIX}.nc",
)
```

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
| `reference_variable: non-null string required` | Used the climate YAML schema with `SOIL.enabled: true` but didn't set `GENERAL.reference_variable` | Set `GENERAL.reference_variable: sand` (or another enabled soil layer) |
| Cube coordinates are huge numbers (e.g. `y = 1500000`) | The builder kept SoilGrids' native projected CRS | Pass `crs=IGH` and `target_crs="EPSG:4326"` explicitly to `SoilDataCubeBuilder` |
| `no valid index for a 0-dimensional object` when sampling the cube | Cube is in flat format (`clay_0-5cm_mean`, etc.) | Run `reshape_flat_soil_cube(ds).to_netcdf(...)` then reopen |
| Downloads fail with HTTP 403 / connection errors | SoilGrids rate limit | Wait, then retry — `SoilGridsDownloader` resumes; existing tiles are skipped |
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

*Evaluation examples: [references/evals.json](references/evals.json)*
