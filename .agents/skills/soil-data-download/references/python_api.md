# Python API reference — soil-data-download

Use these class signatures when writing scripts that download SoilGrids data or
build a soil datacube. All classes live under `aggeodata.ingestion.soil` and
`aggeodata.transform.soil_cube`.

## 1. `SoilGridsDownloader`

Pulls per-variable, per-depth GeoTIFF tiles clipped to a bounding box. Resumes
on rerun — existing files are skipped.

```python
from aggeodata.ingestion.soil import SoilGridsDownloader

dl = SoilGridsDownloader(
    soil_layers=[                                    # 14 valid layers, see SKILL.md
        "clay", "sand", "silt", "bdod", "cfvo",
        "soc", "phh2o", "wv0010", "wv0033", "wv1500",
    ],
    depths=["0-5", "5-15", "15-30", "30-60", "60-100"],   # cm
    output_folder="D:/data/soil_raw",
)

# returns dict: {filename: local_path}
downloaded_paths = dl.download(
    boundaries=[-3.2554, 4.7367, 1.1918, 11.1733],   # [xmin, ymin, xmax, ymax] WGS-84
)
```

Notes:
- One tile per (variable, depth, statistic) combination — typically ~50 files
  for the default 10 variables × 5 depths.
- The downloader uses `rasterio` HTTP range requests against the SoilGrids
  WCS service. No API key required.

## 2. `SoilDataCubeBuilder`

Stacks the downloaded tiles into a single multi-variable NetCDF, reprojected
to a consistent geographic CRS.

```python
from aggeodata.transform.soil_cube import SoilDataCubeBuilder

# SoilGrids native projection. Never accept the builder's default crs="ESRI:54052"
# — it produces a cube with broken geographic extents.
IGH = "+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs"

builder = SoilDataCubeBuilder(
    data_folder="D:/data/soil_raw",
    variables=[
        "clay", "sand", "silt", "bdod", "cfvo",
        "soc", "phh2o", "wv0010", "wv0033", "wv1500",
    ],
    reference_variable="sand",       # grid reference; default: "sand"
    crs=IGH,                         # ALWAYS pass explicitly
    target_crs="EPSG:4326",          # reproject to geographic for downstream tools
)

builder.build_and_save(
    output_path="D:/data/",
    filename="soil_<country>.nc",
)
```

The output NetCDF has dimensions `(y, x, depth)` for each variable, in degrees.

## 3. `reshape_flat_soil_cube`

Older pipelines emit one flat variable per (variable, depth) — e.g.
`clay_0-5cm_mean`, `clay_5-15cm_mean`, … This is incompatible with
`spatial-crop-modeler` and most downstream tools. Reshape before use.

```python
import xarray as xr
from aggeodata.transform.soil_cube import reshape_flat_soil_cube

ds = xr.open_dataset("soil_<country>.nc")

flat_vars = [v for v in ds.data_vars if "_cm_mean" in v]
if flat_vars:
    ds = reshape_flat_soil_cube(ds)
    ds.to_netcdf("soil_<country>.nc")   # overwrite with reshaped version
```

After reshaping, each variable has a `depth` dimension instead of being split
across many per-depth variables.

## 4. Resolving a country to a bounding box

Useful when the user gives a country name but the downloader needs an extent.

```python
from aggeodata.ingestion.boundaries import _fetch_geojson_cached

gdf = _fetch_geojson_cached("MWI", 0)                              # ISO3, admin level 0
extent = [round(v, 4) for v in gdf.total_bounds.tolist()]          # [xmin, ymin, xmax, ymax]
```

Admin level 1 (provinces / regions) or 2 (districts / departments) also work
if the user wants a sub-country extent.
