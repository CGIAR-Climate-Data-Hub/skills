---
name: cdh-metadata
description: >
  Generates a valid Climate Data Hub (CDH) YAML metadata record for a geospatial dataset.
  Use this skill whenever the user wants to: create or write CDH metadata, document a raster,
  vector, NetCDF, or Zarr file for the CDH catalog, produce a YAML metadata record following
  the CDH standard, prepare a dataset for upload to the Climate Data Hub, or fill in metadata
  fields. Trigger even when phrased informally: "write metadata for my file", "document this
  dataset", "create a YAML for CDH", "how do I add my data to the hub", "I need to describe
  my raster", "help me fill the metadata", or "generate the catalog record". This skill is the
  go-to for any CDH metadata authoring task — invoke it whenever a dataset + a CDH context appear
  together, even if the user does not use the word "metadata" explicitly.
---

# CDH Metadata Generator

You produce valid YAML metadata records for the CGIAR Climate Data Hub (CDH) standard. Inspect
the dataset automatically where possible, ask the user for fields you cannot derive, and write a
YAML file that validates against the CDH schema.

Schema root: `https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.1.0/schemas/core.schema.json`  
Full annotated template: read `references/cdh-annotated-template.md` whenever you need to check
a field, see all optional fields, or the user asks for a more complete record.

---

## What auto-extracts vs. what to ask

| Source | Fields |
|--------|--------|
| **File inspection** | bbox, CRS, spatial resolution, variable names, data types, nodata, file size, media type |
| **Always ask** | id, title, description, license, contact (licensor), citation or DOI, data URLs, `cdh.domain` |
| **Ask only if missing** | temporal dates, keywords, version, processing provenance, additional contacts |

---

## Stage 1 — Inspect the dataset

Ask: **"What is the path to your geospatial file?"**

Then run the matching inspection script below. Print the result as a clean summary and ask
"Does anything look wrong?" before continuing.

**Raster (.tif / .tiff / .img)**
```python
import rasterio, os, json
path = r"FILEPATH"
size = os.path.getsize(path)
with rasterio.open(path) as src:
    b = src.bounds
    print(json.dumps({
        "bbox": [round(b.left,6), round(b.bottom,6), round(b.right,6), round(b.top,6)],
        "crs": src.crs.to_string() if src.crs else None,
        "width": src.width, "height": src.height, "bands": src.count,
        "dtypes": list(src.dtypes), "nodata": src.nodata,
        "res_deg": [round(src.res[0],8), round(src.res[1],8)],
        "driver": src.driver,
        "file_size_mb": round(size/1e6, 2),
    }, indent=2))
```

**NetCDF (.nc / .nc4)**
```python
import xarray as xr, os, json
path = r"FILEPATH"
ds = xr.open_dataset(path)
lat = ds.coords.get("lat", ds.coords.get("latitude"))
lon = ds.coords.get("lon", ds.coords.get("longitude"))
print(json.dumps({
    "variables": list(ds.data_vars),
    "dims": dict(ds.dims),
    "dtypes": {v: str(ds[v].dtype) for v in ds.data_vars},
    "bbox": [round(float(lon.min()),6), round(float(lat.min()),6),
             round(float(lon.max()),6), round(float(lat.max()),6)]
             if lat is not None and lon is not None else None,
    "global_attrs": dict(ds.attrs),
    "file_size_mb": round(os.path.getsize(path)/1e6, 2),
}, default=str, indent=2))
ds.close()
```

**Zarr (.zarr or directory)**
```python
import xarray as xr, json
path = r"FILEPATH"
ds = xr.open_zarr(path)
lat = ds.coords.get("lat", ds.coords.get("latitude"))
lon = ds.coords.get("lon", ds.coords.get("longitude"))
print(json.dumps({
    "variables": list(ds.data_vars),
    "dims": dict(ds.dims),
    "dtypes": {v: str(ds[v].dtype) for v in ds.data_vars},
    "bbox": [round(float(lon.min()),6), round(float(lat.min()),6),
             round(float(lon.max()),6), round(float(lat.max()),6)]
             if lat is not None and lon is not None else None,
    "chunks": {v: str(ds[v].encoding.get("chunks")) for v in ds.data_vars},
}, default=str, indent=2))
ds.close()
```

**Vector (.gpkg / .shp / .fgb / .parquet)**
```python
import geopandas as gpd, os, json
path = r"FILEPATH"
gdf = gpd.read_file(path)
b = gdf.total_bounds
print(json.dumps({
    "bbox": [round(float(b[0]),6), round(float(b[1]),6),
             round(float(b[2]),6), round(float(b[3]),6)],
    "crs": str(gdf.crs),
    "geometry_types": gdf.geom_type.unique().tolist(),
    "columns": list(gdf.columns),
    "row_count": len(gdf),
    "file_size_mb": round(os.path.getsize(path)/1e6, 2),
}, default=str, indent=2))
```

---

## Stage 2 — Collect user inputs

After inspecting the file, ask the **Round 1** questions together (not one at a time). Once
answered, ask **Round 2** only for fields that are still missing.

**Round 1 — always required:**

| Field | Prompt |
|-------|--------|
| `id` | "Short URL-safe ID for this record? (suggest: `<filename-slug>`). Lowercase letters, digits, hyphens only." |
| `title` | "Human-readable title for the dataset?" |
| `description` | "2–5 sentence description: what does it represent, how was it produced, what do values mean?" |
| `license` | "License? Common: `CC-BY-4.0`, `CC-BY-SA-4.0`, `CC0-1.0`. Or enter a custom string." |
| `contact (licensor)` | "Who is the licensor? Name, organization, email. (The organization that owns or published the data.)" |
| `citation or DOI` | "Is there a DOI (e.g. `10.xxxx/...`) or citation (authors, year, title, publisher) for this dataset?" |
| `data locations` | "Where is the data accessible? Provide HTTPS URL(s) or S3 path(s). If not yet hosted, enter a placeholder." |
| `cdh.domain` | "CDH domain(s)? Options: `adaptation`, `agricultural-production`, `boundaries`, `climate`, `hydrology`, `mitigation`, `socioeconomic`" |

**Round 2 — ask only if unknown:**

| Field | Prompt |
|-------|--------|
| `temporal` | "Time period the data covers? (start date and end date, YYYY-MM-DD)" |
| `temporal resolution` | "What is the time step? (e.g. daily, monthly, annual, static)" |
| `keywords` | "Any keywords to add? I'll suggest some from the variables." |
| `version` | "Is this a versioned release? (e.g. `v1.0`, `2020`)" |
| `processing[source]` | "Where did the raw/source data originally come from? (URL or repository)" |
| `spatial.geography` | "What geographic area does this cover? (country name, region, or `world`)" |

Never block on optional fields. If the user says "I don't know" or skips a field, use `null`
or omit it per the schema and move on.

---

## Stage 3 — Confirm the plan

Show a compact summary before writing the file:

```
ID:       <id>
Title:    <title>
License:  <license>
Temporal: <start_date> → <end_date>
Spatial:  [<west>, <south>, <east>, <north>] — <crs>
Domain:   <domain>
Data:     <url>
Output:   <output_path>/<id>.yaml
```

Ask: **"Does this look right? I'll generate the YAML."**

---

## Stage 4 — Generate the YAML

Write the file to the **same directory as the dataset** (or the directory the user specifies),
named `<id>.yaml`.

**Mandatory header line** (adjust relative path if needed):
```yaml
# yaml-language-server: $schema=../../spec/schemas/profiles/cdh.schema.json
```

**Hard rules:**
- `cdh_schema_version`: always `"v0.1.0"`
- `created` / `updated`: today → `"2026-07-01"`
- `bbox`: 4-number array `[west, south, east, north]` — never a string
- `crs`: EPSG string, e.g. `"EPSG:4326"`
- `contact`: at least one entry must include `licensor` in its `roles` list — schema enforces this
- `processing`: if present, at least one step must have `id: source`
- `extensions`: list every extension schema URL you actually use (see below)
- Use `null` for unknown nullable fields; omit fields that are fully optional and unknown

**Media types by format:**

| Format | `media_type` value |
|--------|--------------------|
| GeoTIFF | `image/tiff; application=geotiff` |
| Cloud-Optimized GeoTIFF | `image/tiff; application=geotiff; profile=cloud-optimized` |
| NetCDF | `application/netcdf` |
| Zarr v3 | `application/vnd.zarr; version=3` |
| GeoPackage | `application/geopackage+sqlite3` |
| Parquet | `application/vnd.apache.parquet` |
| CSV | `text/csv` |

**Extension URLs (add to `extensions[]` when the matching block is used):**
```
# Always add when using the cdh: block:
https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.1.0/extensions/cdh/schema.json

# Add when using dimensions: / variables: blocks:
https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.1.0/extensions/datacube/schema.json

# Add when using commodities: field:
https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.1.0/extensions/agriculture/schema.json

# Add when using climate: block:
https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.1.0/extensions/climate/schema.json

# Add when using classes: field:
https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.1.0/extensions/classification/schema.json
```

After writing, print the file path and show a 30-line preview.

---

## Controlled vocabularies

### `resource_type`
`dataset` | `software` | `service` | `ai-skill` | `document`

### `cdh.domain` (pick one or more)
`adaptation` | `agricultural-production` | `boundaries` | `climate` | `hydrology` | `mitigation` | `socioeconomic`

### Common licenses (SPDX)
`CC-BY-4.0` | `CC-BY-SA-4.0` | `CC0-1.0` | `CC-BY-NC-4.0` | `ODbL-1.0`  
For proprietary data use a plain string, e.g. `"FAO Internal Use Only"`.

### Contact roles
`licensor` | `producer` | `processor` | `point-of-contact`

### Spatial resolution type
`xy` (regular grid, same x and y) | `x` | `y` | `point` | `polygon`

### Common geography vocab values
`world` | `africa` | `asia` | `latin-america-and-the-caribbean` | `sub-saharan-africa`  
Country codes follow ISO 3166-1 alpha-2 lower-case or UN M49 names in the CDH vocab  
(e.g. `ethiopia`, `colombia`, `kenya`). When in doubt, use country name in lower-kebab-case.

---

## Reference

Read `references/cdh-annotated-template.md` for the full YAML template with every optional field
annotated. Use it when:
- The user asks about a specific field you're unsure of
- The dataset warrants a more complete record (climate projections, livestock, crop data)
- You need examples of `dimensions`, `variables`, `classes`, `climate`, or `commodities` blocks
