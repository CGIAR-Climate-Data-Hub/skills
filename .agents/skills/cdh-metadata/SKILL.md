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

You produce valid YAML metadata records for the CGIAR Climate Data Hub (CDH) standard **v0.4.1**.
Inspect the dataset automatically where possible, ask the user for fields you cannot derive, and
write a YAML file that validates against the CDH schema.

Profile schema: `https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/schemas/profiles/cdh.schema.json`  
Official repository: `https://github.com/CGIAR-Climate-Data-Hub/cdh-metadata-standard`  
Real catalog records: `https://github.com/CGIAR-Climate-Data-Hub/cdh-catalog/tree/main/records`  
Full annotated template: read `https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/.agents/skills/cdh-metadata/references/cdh-annotated-template.md` whenever you need to check
a field, see all optional fields, or the user asks for a more complete record.  
Authoring guide: read `https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/cdh-metadata-standard/main/spec/authoring-guide.md` when you need what a
field *means* rather than what shape it takes — see **Reference** at the end of this file.

> **Coming from v0.3.0?** The data model changed substantially. Read **Moving a v0.3.0 record to
> v0.4.1** at the end of this file before editing an existing record; a v0.3.0 record will not
> validate, and several fields were renamed rather than removed.

---

## What auto-extracts vs. what to ask

| Source | Fields |
|--------|--------|
| **File inspection** | bbox, CRS, grid spacing, variable names, data types, fill values, file size, media type |
| **Always ask** | id, version, title, description, license, contact (licensor **and** maintainer), citation or DOI, data URLs, `cdh.domain`, keywords, `commodities` and `climate.*` where they apply, and the *meaning*, units, and caveats of each variable |
| **Ask only if missing** | temporal dates, `update_frequency`, processing provenance, additional contacts, series, `parent`, `attribution`, `cdh.usage` |

Inspection gives you the technical shape of a file; it cannot tell you what the data *means*. That
line is what the "always ask" row is drawn along — catalog reviewers can fill technical facts from
the assets themselves, but nobody downstream can recover authorial intent. Variable *names* come
from the file; what a variable measures, its units, and its caveats have to come from the user. A
record listing `hsd: float32` with no indication that it counts heat-stress days is schema-valid
and useless to the next person who finds it.

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
        "file_size_bytes": size,
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
    "dims": dict(ds.sizes),
    "dtypes": {v: str(ds[v].dtype) for v in ds.data_vars},
    "fill_values": {v: ds[v].encoding.get("_FillValue") for v in ds.data_vars},
    "bbox": [round(float(lon.min()),6), round(float(lat.min()),6),
             round(float(lon.max()),6), round(float(lat.max()),6)]
             if lat is not None and lon is not None else None,
    "global_attrs": dict(ds.attrs),
    "file_size_bytes": os.path.getsize(path),
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
    "dims": dict(ds.sizes),
    "dtypes": {v: str(ds[v].dtype) for v in ds.data_vars},
    "fill_values": {v: ds[v].encoding.get("_FillValue") for v in ds.data_vars},
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
    "dtypes": {c: str(t) for c, t in gdf.dtypes.items()},
    "row_count": len(gdf),
    "file_size_bytes": os.path.getsize(path),
}, default=str, indent=2))
```

---

## Stage 2 — Collect user inputs

After inspecting the file, ask the **Round 1** questions together (not one at a time). Once
answered, ask **Round 2** only for fields that are still missing.

**Round 1 — always required:**

| Field | Prompt |
|-------|--------|
| `id` | "Short URL-safe ID for this record? (suggest: `<filename-slug>`). Lowercase letters, digits, hyphens only — and no version in it." |
| `version` | "Which release is this? Copy the source's own label (`v2r2`, `2.1`, `2020`); if it isn't versioned, use `\"1\"`." |
| `title` | "Human-readable title for the dataset?" |
| `description` | "2–5 sentence description: what does it represent, how was it produced, what do values mean?" |
| `license` | "License as an SPDX expression? Common: `CC-BY-4.0`, `CC-BY-SA-4.0`, `CC0-1.0`. A custom `LicenseRef-*` also needs an `additional_links` entry with `rel: license`." |
| `contact` | "Two roles are mandatory. Who is the **licensor** (the party that granted the license), and who is the **maintainer** (accountable for this record)? For each: organization (required), plus optional name, email, url, and ORCID/ROR. Other roles: `producer`, `processor`, `point-of-contact`." |
| `citation or DOI` | "Is there a DOI (bare, e.g. `10.xxxx/...`) or a structured citation? Authors are objects: `{family, given}` for a person, `{organization}` for a body." |
| `data locations` | "Where is the data accessible? Absolute HTTPS URL(s) or S3 URI(s). If multiple formats (Zarr + COGs), list each separately with a short name (e.g. `zarr`, `cogs`). I will resolve each URL before writing the record." |
| `cdh.domain` | "CDH domain(s)? Options: `adaptation`, `agricultural-production`, `boundaries`, `climate`, `hydrology`, `mitigation`, `socioeconomic`" |
| `keywords` | "At least one keyword — required by the schema. I'll suggest some; they can optionally be linked to AGROVOC or another vocabulary." |
| variable meaning | "For each variable: what does it measure, in what unit, and what should a reader know before using it? If any variable is coded, what does each code mean?" |

**Round 2 — ask only if unknown:**

| Field | Prompt |
|-------|--------|
| `temporal` | "Time period the data covers? A single value for a static dataset (e.g. `2020`), or start/end dates. `end_date: null` means the resource itself keeps growing." |
| `temporal.update_frequency` | "How often does this resource gain new data? `daily`, `weekly`, `monthly`, `quarterly`, `semiannual`, `annual`, `irregular`. This is the resource's own cadence, not the data's time step." |
| `previous_version` | "Does this supersede an earlier release? If so, what was its `version` label? (Not its id — releases share one id.)" |
| `parent` | "Is this a child representation of another Hub record — an aggregation, a reprojection, a subset? If so, the parent's `id`." |
| `attribution` | "Does the source mandate a credit line (Copernicus, OpenStreetMap), or do you want to be credited in a specific form?" |
| `series` | "Does this belong to a series — a program, initiative, or product brand (e.g. MapSPAM, GLW, CHIRPS)? A series is a discovery grouping, not a version or parent relationship. If so, name and URL?" |
| `processing[source]` | "Where did the raw/source data originally come from? A URL, or the `id` of another Hub record — and which version of it?" |
| `spatial.geography` | "What geographic area does this cover? (country name, region, or `world`)" |
| `cdh.usage.intended_uses` | "What was this dataset produced for? (optional; free-text list. Illustrative, not exhaustive — don't force it if nothing specific comes to mind.)" |
| `cdh.usage.not_recommended_for` | "Any uses this dataset is NOT suitable for? (optional; each needs a reason, and can optionally suggest an alternative)" |

Never block on optional fields. If the user says "I don't know" or skips a field, omit it and move
on.

**What makes a good answer.** The schema accepts weak values, so this is where records quietly lose
their worth. Each rule below exists for the same reason: a fact stored in the wrong place stops
being findable.

- `description` — say what the resource is and what it can be used for. Keep filterable facts out of
  it (variables, units, geographies, dates); they belong in their structured fields, where people
  and machines can actually filter on them. A description is not a substitute for the schema.
- `keywords` — extra search terms only: aliases, method names, acronyms, user-facing phrasing. Do
  not repeat anything that already has a structured field; route it instead — places →
  `spatial.geography`, crops or livestock → `commodities`, coverage period → `temporal`, cadence →
  a `type: temporal` dimension's `step`.
- `cdh.usage` — terms like "research" or "decision-making" are too broad to guide anyone, so skip
  them. `not_recommended_for` is usually the more valuable half: it prevents misuse without
  narrowing the legitimate uses, especially when each entry carries a reason.
- `id` — keep the version out of it. The unversioned `id` always names the current release, and
  `id` + `version` is the citable identity.
- `note` — not a catch-all. Use it only for a caveat a reader would miss. Credit lines go in
  `attribution`, provenance in `processing[].derived_from`, axis labelling in that dimension's
  `description`.

When a field's intent is unclear, or a value would pass validation but read poorly, consult the
authoring guide (see **Reference**) rather than guessing.

---

## Stage 3 — Verify every link

A record can validate against the schema and still ship dead URLs. Before you show the user a
summary, resolve **every** URL the record will contain. A broken link in a catalogue record is
worse than a missing one: it looks authoritative and sends the next person nowhere.

**Never present a link as verified unless you resolved it in this session.**

### What to check

| Link | Usually comes from | A failure is |
|------|--------------------|--------------|
| `data[].locations[].url` (the data itself) | user | blocking |
| `doi` — resolve `https://doi.org/<doi>` | user | blocking |
| `citation.url`, `related_publications[].citation.url` | user or drafted | blocking |
| `series.url`, `processing[].derived_from[].url`, `processing[].code.url` | often drafted | blocking |
| `contact[].url`, `orcid`, `ror` | user | warning |
| `additional_links[].url`, `additional_assets[].locations[].url` | user | warning |
| every `extensions[]` URL | this skill | blocking — a dead extension URL makes the record unusable to every downstream tool |

`s3://` URIs cannot be resolved over HTTP. Check the matching HTTPS endpoint where one exists,
otherwise report the URI as **unchecked** rather than ok. A relative path (`./AGENTS.md`) is checked
on disk, not over the network.

### How to check

Issue a HEAD request; if the host answers 403/405/501, retry with a ranged GET
(`Range: bytes=0-0`) before concluding anything. Then classify:

| Result | Meaning | Action |
|--------|---------|--------|
| 2xx | live | keep |
| 3xx | moved | follow it, record the **final** URL, and tell the user you did |
| 401 / 403 after GET retry | reachable but gated | keep, and set `access: restricted` with an `access_note` |
| 404 / 410 | dead | see below |
| DNS failure / timeout | unreachable | see below |

### When a link fails

- **You drafted it** → drop the field. Never keep a URL you produced from memory and could not
  resolve; a plausible-looking dead link is the worst outcome of this whole skill.
- **The user supplied it** → ask once with the status code quoted, e.g. *"`https://…` returned 404 —
  is the data not uploaded yet, or is the URL wrong?"* Do not silently fix it, and do not silently
  keep it.
- **The data is not published yet** → this is normal, not a failure. Authors routinely write the
  record before the upload lands. Keep the URL exactly as given, say in your summary that it is
  **not yet resolvable**, and move on. Never block a record on a deliberate forward reference, and
  never quietly delete the URL the author intends to publish at.
- **An extension URL** → stop. Do not write the record. Report which URL failed; the standard may
  have moved and the skill needs updating.

### When you have no network access

Say so plainly, list every URL you could not check, and mark the record **LINKS UNVERIFIED** in
your summary to the user. Do not describe unchecked links as working, and do not quietly skip
this stage.

### Report

Print the results before moving on:

```
Links checked (n):
  ok        200  https://data.example.org/chirts/tmax.zarr
  moved     301  https://old.example.org/doc  ->  https://new.example.org/doc
  gated     403  https://api.example.org/private
  DEAD      404  https://example.org/typo.tif        (user-supplied - needs a decision)
  unchecked  -   s3://bucket/path                    (no HTTPS equivalent given)
```

---

## Stage 4 — Confirm the plan

Show a compact summary before writing the file:

```
ID:         <id>
Version:    <version>   (supersedes <previous_version>)
Title:      <title>
License:    <license>
Temporal:   <date or start_date → end_date>
Spatial:    [<west>, <south>, <east>, <north>] — <crs>
Domain:     <domain>
Structures: <n> (<names>)  — <n> dimensions, <n> variables
Data:       <url(s)>
Links:      <n> ok, <n> moved, <n> gated, <n> DEAD, <n> unchecked
Output:     <output_path>/<id>.yaml
```

Ask: **"Does this look right? I'll generate the YAML."**

---

## Stage 5 — Generate the YAML

Write the file to the **same directory as the dataset** (or the directory the user specifies),
named `<id>.yaml`.

**Mandatory header:**
```yaml
# yaml-language-server: $schema=https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/schemas/profiles/cdh.schema.json
cdh_schema_version: "v0.4.1"
extensions:
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/extensions/cdh/schema.json
```

There is **no `$schema` key**. It was removed in v0.4.0 — nothing read it. The editor binding is the
`yaml-language-server` comment, and `cdh_schema_version` names the release.

### Hard rules (v0.4.1)

**Identity and lifecycle**
- `cdh_schema_version`: always `"v0.4.1"`
- `version`: **required** by the CDH profile. Letters, digits, dots, underscores, hyphens only.
  Quote labels YAML would read as numbers (`"2.0"`, `"2020"`).
- `id`: never carries the version. Every release shares one `id`; `id` + `version` is the citable
  identity, and catalog uniqueness is the pair.
- `previous_version` holds the predecessor's **`version`**, not its id.
- A superseded release keeps its `id` and gains `deprecated: true` — never a renamed snapshot copy.
- `created` / `updated`: **required**. Use today's date, e.g. `"2026-10-07"`.
- `parent`: the `id` of the record this one is a child representation of. It inherits **nothing** —
  a child repeats its own license, contacts, and extent.

**Required by core**: `cdh_schema_version`, `id`, `title`, `description`, `created`, `updated`,
`license`, `resource_type`, `keywords`, `contact`, `data`. The profile adds `cdh`, `extensions`,
`version`.

**Conditionally required — these are not in `required`, so they fail only at validation time:**
- **`citation` or `doi`.** Every record needs at least one. A record with neither is invalid.
- `access_note` when `access` is `restricted` or `non-public`.
- An `additional_links` entry with `rel: license` when `license` is a `LicenseRef-*` expression.
- `data[].structures` on **every** asset once the record has two or more structures.
- Each `data[]` entry needs `locations` **or** `file_index` — and never both `href_template` and
  `file_index`.
- `unit` on every `x` / `y` / `xy` dimension.
- `start_date` and `end_date` come as a pair; `date` excludes both.

**Contacts and citation**
- `contact[]`: every entry needs `organization` and a non-empty `roles` array. At least one entry
  must hold `licensor`, and — **new in v0.4.0** — at least one must hold `maintainer`. One entry can
  hold both.
- `citation.authors[]` entries are **objects**, never plain strings: `{family, given?}` for a
  person, `{organization}` for a body, mixed in citation order. Optional `orcid` / `ror` as full
  `https://orcid.org/…` and `https://ror.org/…` URLs. The same shape applies to
  `related_publications[].citation`.
- `citation.date` must be a year, month, date, or date-time — not free text.
- `doi`: bare DOI only (e.g. `10.7910/DVN/SWPENT`) — no `https://doi.org/` prefix.

**`structures[]` — the data dictionary (replaces the datacube extension)**
- `dimensions[]` and `variables[]` live **inside a structure**, never at record level. The datacube
  extension no longer exists and must not appear in `extensions[]`.
- One layout → one structure. A record whose assets hold different dimensions or variables (monthly
  and seasonal file sets; tables with different columns) gets **one structure per layout**.
- Names are unique **within** a structure and may repeat across structures.
- With more than one structure, every `data[]` entry names the ones it holds in `data[].structures`,
  and holds each variable in only one of them. With exactly one structure, every asset holds it.
- `variables[]` must list at least one variable. Every variable needs `name` and `description`;
  every dimension needs `name`, `type`, and `description`; every category needs `value` and `label`.
- `variables[].dimensions` is gone — a variable has every dimension of its structure. Variables on
  different axes within one asset are two structures.
- `variables[].nodata` is where a fill value lives. `data[].nodata` was **removed**; a representation
  storing a variable with a different fill value or type is a different structure.
- `variables[].unit` is optional — omit it for unitless values such as class codes.
- `variables[].data_type` is a closed list (see **Controlled vocabularies**).
- `foreign_keys[]` (was `joins[]`) sits on the structure whose columns it names:
  `{fields: [...], reference: {resource, asset?, fields: [...]}}`. `reference.resource` is a catalog
  record id or an absolute URI; `reference.asset` is required when the target has more than one
  `data[]` entry.
- `geometry_column` sits on the structure, not on `spatial`.

**Dimensions**
- `type` is lowercase, `^[a-z][a-z0-9_-]*$`. Reserved: `temporal` (ISO 8601 axis), `xy` / `x` / `y`
  (horizontal axes), `z` (vertical, at most one per record), `location` (a place-key column; any
  number). Rejected outright: `time`, `times`, `date`, `dates`, `datetime`, `timestamp`, `spatial`,
  `geometry`, `lat`, `latitude`, `lon`, `lng`, `longitude`.
- **`spatial.resolution` is removed.** Grid spacing is now a horizontal dimension: `xy` with one
  numeric `step`, or `x` and `y` each with their own, plus `unit`. A table's coordinate columns get
  horizontal axes with **no** `step`. A table's reporting unit is a `type: location` dimension, with
  the boundary set named in `reference_system` and ideally a `foreign_keys` entry to the catalogued
  boundary record.
- `step` is a **duration** on `temporal` (`P10Y`) and a **number** on horizontal axes (`0.05`). It
  must have a nonzero component — `P0D` is rejected — and it is only the spacing between values. A
  30-year window every 10 years is `step: P10Y`, with the window length in `description`.
- A horizontal axis (`x` / `y` / `xy`) **requires `unit`** and must carry neither `values` nor
  `categories` — it never enumerates coordinates.
- `values[]` must list at least one value when present; omit it rather than writing `[]`. Duplicates
  are rejected. `categories` and `values` are mutually exclusive, and `categories` is not allowed on
  a `temporal` dimension.
- On a `type: temporal` dimension, every `values[]` entry is an ISO 8601 **string** (`"2020"`,
  `"2020-06"`, `"2020-06-23"`). Bare numbers and range labels (`"2020-2040"`) are rejected. A
  date-time must be RFC 3339 with seconds and an offset (`2020-01-01T01:00:00Z`), and must be a real
  calendar date.
- `extent: [first, last]` **replaces** listing every value on a regular temporal axis. It requires
  `step` and excludes `values`. On a horizontal axis, `extent` is an optional numeric `[min, max]`.
- `data_type` is available on dimensions too — give key columns one, so an admin code stored as
  `"001"` is read as text.
- A cyclic label axis (`DJF`/`MAM`/`JJA`/`SON`) is not temporal — name it as a domain axis.

**Categories (replaces the classification extension)**
- Coded values live on `variables[].categories` or `dimensions[].categories` as
  `{value, label, description?}`. The classification extension is **removed** and must not appear in
  `extensions[]`.
- On a variable, `categories` lists the codes it can contain. On a dimension, it labels the axis
  values **in place of** `values`.
- `value` is a string or an integer.
- For long lists, link a sidecar file as an `additional_assets` entry instead.

**Assets**
- `data[]`: each entry needs a unique `name`. `locations[].url` must be an **absolute URI**.
- `file_size`: whole bytes, or a number and unit (`31.1 MB`). Units B, KB, MB, GB, TB, PB in powers
  of 1000. Free text is rejected.
- `data[].checksum`: `<algorithm>:<hex>` for single-file entries only — not allowed alongside
  `href_template` or `file_index`, and the digest must be the right length for its algorithm.
- `data[].spatial`: one asset's own coverage, for selecting files by area. Never copied down from
  the top-level `spatial`.
- `data[].file_index[]`: `{format, locations, title?, media_type?}` for file sets a template cannot
  describe. `format` ∈ `stac-geoparquet`, `gti`, `vrt`, `kerchunk`, `icechunk`, `cdh-inventory`. Any
  one index is enough. `locations[]` may be omitted on the entry when a `file_index` carries them.
- `href_template` tokens on a temporal dimension may carry a strftime format (`{date:%Y.%m.%d}`),
  limited to `%Y`, `%m`, `%d`.
- `additional_links[].name` was renamed **`title`**.
- `additional_assets[].roles` suggested values: `metadata`, `validation`, `describedby`, `thumbnail`,
  `overview`, `visual`, `example` (a runnable notebook/script), `agents` (a Markdown guide for AI
  agents). A small sidecar may use a relative `url` (`./AGENTS.md`); validation checks it exists.
- Bands are **not** variables. Bands are how a file stores values; when band descriptions don't say
  what each holds, `data[].description` does.

**Other**
- `resource_type`: one of `dataset | software | service | document`
- `access`: `public | restricted | non-public`; `restricted` and `non-public` require an
  `access_note`.
- `temporal`: use `date` (single instant/period) OR `start_date`/`end_date` (span) — mutually
  exclusive. `end_date: null` means the resource itself grows continuously; a scheduled mirror
  states its real end date.
- `bbox`: 4-number array `[west, south, east, north]`, or a list of such arrays for disjoint
  coverage. Never a string.
- `crs`: EPSG string, e.g. `"EPSG:4326"`.
- `processing[]`: if present, at least one step must have `id: source`, and every step needs `id`
  and `description`. `derived_from[]` entries take **either** `url` **or** `id` (a Hub record), never
  both, plus an optional `version` pinning the source release.
- `license`: an SPDX expression. A custom `LicenseRef-*` needs an `additional_links[]` entry with
  `rel: license`.
- `attribution`: a credit line reusers must reproduce. Keeps mandated wording out of `note`.
- Do NOT write stray `null` values for fields you are simply omitting; only use `null` where it is
  meaningful, as in an open-ended `end_date`.
- Every link URL must be a valid URI — `additional_links`, `contact`, `citation`, `funding`,
  `series`, `code`, `derived_from` included.

**Media types by format:**

| Format | `media_type` value |
|--------|--------------------|
| GeoTIFF | `image/tiff; application=geotiff` |
| Cloud-Optimized GeoTIFF | `image/tiff; application=geotiff; profile=cloud-optimized` |
| NetCDF | `application/x-netcdf` |
| Zarr v3 | `application/vnd.zarr; version=3` |
| GeoPackage | `application/geopackage+sqlite3` |
| Parquet | `application/vnd.apache.parquet` |
| CSV | `text/csv` |
| Jupyter notebook | `application/vnd.jupyter` |
| Python / R source | `text/x-python` / `text/x-r` |

Use the IANA type where one is registered, otherwise the type in common use.

**Extension URLs (add to `extensions[]` when the matching block is used):**
```
# Always add — required for CDH Hub records:
https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/extensions/cdh/schema.json

# Add when using the climate: block:
https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/extensions/climate/schema.json

# Add when using the commodities: field:
https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/extensions/agriculture/schema.json
```

There are only three. The **datacube** and **classification** extensions were removed in v0.4.0 —
their URLs 404, and declaring one makes the record invalid.

### Minimal valid record

```yaml
# yaml-language-server: $schema=https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/schemas/profiles/cdh.schema.json
cdh_schema_version: "v0.4.1"
extensions:
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/extensions/cdh/schema.json

id: example-dataset
version: "1"
title: Example Dataset
description: >
  What the resource is and what it can be used for.
license: CC-BY-4.0
resource_type: dataset
created: "2026-10-07"
updated: "2026-10-07"

keywords:
  - example

contact:
  - organization: Alliance of Bioversity International and CIAT
    name: Jane Doe
    email: jane.doe@example.org
    roles: [licensor, maintainer]

citation:
  title: Example Dataset
  authors:
    - family: Doe
      given: J.
  date: "2026"
  publisher: Example Repository

spatial:
  bbox: [-89.4, 12.9, -83.1, 16.6]
  crs: EPSG:4326
  geography: [honduras]

temporal:
  date: "2024"

structures:
  - name: main
    dimensions:
      - name: cell
        type: xy
        description: 3 arc-second grid (~30 m at the equator).
        step: 0.00089831
        unit: degree
    variables:
      - name: forest_class
        description: Forest type class assigned to each cell.
        data_type: uint8
        nodata: 255
        categories:
          - { value: 1, label: Broadleaf }
          - { value: 2, label: Conifer }

cdh:
  domain: [boundaries]

data:
  - name: cog
    description: Cloud Optimized GeoTIFF of the classified raster.
    locations:
      - url: https://example.org/data/example-dataset.tif
    media_type: "image/tiff; application=geotiff; profile=cloud-optimized"
    file_size: 48 MB
```

After writing, print the file path and show a 30-line preview.

Then re-read the finished file and confirm that every URL in it is one you resolved in Stage 3 —
including any `extensions[]` URL you added while generating. If a URL appears in the file that was
never checked, check it now or flag it to the user. The record is not finished while it contains an
unverified link.

---

## Controlled vocabularies

### `resource_type`
`dataset` | `software` | `service` | `document`

### `cdh.domain` (pick one or more)
`adaptation` | `agricultural-production` | `boundaries` | `climate` | `hydrology` | `mitigation` | `socioeconomic`

### `access`
`public` | `restricted` | `non-public` — the latter two require `access_note`.

### Contact roles (array — one or more per contact entry)
`licensor` | `producer` | `processor` | `point-of-contact` | `maintainer`

At least one `licensor` (core) **and** at least one `maintainer` (CDH profile).
`custodian` was renamed `maintainer` in v0.4.0.

### `temporal.update_frequency`
`daily` | `weekly` | `monthly` | `quarterly` | `semiannual` | `annual` | `irregular`

### `variables[].data_type` / `dimensions[].data_type` (closed list)
Binary stores: `int8` `int16` `int32` `int64` `uint8` `uint16` `uint32` `uint64` `float16`
`float32` `float64` `cint16` `cint32` `cfloat32` `cfloat64`  
Text formats (CSV, fixed-width, JSON): `integer` `number`  
Also: `decimal` (fixed-point with declared precision in a binary store), `boolean`, `string`,
`binary`, `date`, `time`, `datetime`, `other` (nested types)

### Dimension types
**Reserved (change how the dimension is read):**
- `temporal` — ISO 8601 axis; `step` is a duration; takes `values` or `extent`, not both.
- `xy` / `x` / `y` — horizontal axes; `step` is a number in `unit`. No `step` on a table's
  coordinate columns.
- `z` — vertical axis (depth, height, pressure); **at most one per record**.
- `location` — a place-key column (admin or station code); any number allowed.

**Rejected:** `time`, `times`, `date`, `dates`, `datetime`, `timestamp`, `spatial`, `geometry`,
`lat`, `latitude`, `lon`, `lng`, `longitude`.

**Common non-reserved** (any descriptive lowercase string is valid):
`crop` | `species` | `technology` | `scenario` | `model`

### `data[].file_index[].format`
`stac-geoparquet` | `gti` | `vrt` | `kerchunk` | `icechunk` | `cdh-inventory`

### Common licenses (SPDX)
`CC-BY-4.0` | `CC-BY-SA-4.0` | `CC0-1.0` | `CC-BY-NC-4.0` | `ODbL-1.0`  
For proprietary data use a `LicenseRef-*` expression plus an `additional_links` entry with
`rel: license`.

### Common geography vocab values
`world` | `africa` | `asia` | `latin-america-and-the-caribbean` | `sub-saharan-africa`  
Country codes follow ISO 3166-1 alpha-2 lower-case or UN M49 names in the CDH vocab
(e.g. `ethiopia`, `colombia`, `kenya`). When in doubt, use the country name in lower-kebab-case.

---

## Moving a v0.3.0 record to v0.4.1

If the user hands you an existing record, check `cdh_schema_version` first. A v0.3.0 record needs
these edits before it will validate:

| v0.3.0 | v0.4.1 |
|--------|--------|
| `"$schema": <url>` | **delete the key** |
| `cdh_schema_version: "v0.3.0"` | `"v0.4.1"` |
| `extensions: [… datacube …]` | delete; the datacube extension is folded into core |
| `extensions: [… classification …]` | delete; use `variables[].categories` |
| record-level `dimensions:` / `variables:` | move inside `structures[0]` |
| `variables[].dimensions` | delete — a variable has all of its structure's dimensions |
| `data[].nodata` | move to `variables[].nodata` |
| `classes[]` | `variables[].categories` (`{value, label, description?}`) |
| `spatial.resolution[]` | an `xy` (or `x` + `y`) dimension with a numeric `step` and `unit` |
| `spatial.geometry_column` | `structures[].geometry_column` |
| `joins[]` | `foreign_keys[]`, Frictionless shape |
| contact role `custodian` | `maintainer` |
| `citation.authors: ["Doe, J."]` | `[{family: Doe, given: J.}]` |
| `additional_links[].name` | `title` |
| `previous_version: <id>` | the predecessor's **`version`** label |
| `media_type: application/netcdf` | `application/x-netcdf` |
| *(absent)* `version` | **now required** |
| *(optional)* `created` / `updated` | **now required** |
| *(no maintainer)* | add a contact with `roles: [maintainer]` |
| `dimensions[].step: P0D` or window length | spacing only, nonzero |
| `file_size: "about 30 megabytes"` | `31.1 MB` or whole bytes |
| relative or partial `locations[].url` | absolute URI |

Also check: `temporal` date-times now need an offset and must be real calendar dates, and every
`values[]` must be non-empty and free of duplicates.

---

## Reference

Three documents back this skill, and they answer different questions. Pick by what you are actually
stuck on: **the examples show you a working record, the template shows you the slot, the guide tells
you what belongs in it.**

**Worked examples** — *a complete, validated record to start from.*
`https://github.com/CGIAR-Climate-Data-Hub/cdh-metadata-standard/tree/main/examples`
The `kitchen-sink` example fills in almost every field the standard offers, including multiple
structures, categories, `file_index`, a `parent` child record, and a deprecated previous release.
`templates/` and draft validation were removed in v0.4.0 — start from a validated example instead.

**`references/cdh-annotated-template.md`** — *what fields exist and what shape they take.*
The full YAML template with every optional field annotated. Read it when:
- The user asks about a specific field you're unsure of
- The dataset warrants a more complete record (climate projections, livestock, crop data)
- You need examples of `structures`, `categories`, `foreign_keys`, `file_index`, `climate`, or
  `commodities` blocks

**CDH authoring guide** — *what a field means and what a good value looks like.*
`https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/cdh-metadata-standard/main/spec/authoring-guide.md`
Read it when:
- You are unsure whether a field applies at all, or whether to omit it. Its *What To Leave Out*
  rule: drop a field when it does not apply, when the value would only repeat another field, or
  when it is unknown and not required — and avoid inventing new fields, since `additional_links`,
  `additional_assets`, a sidecar, or an extension already cover the gap.
- A value would validate but read poorly, and you want the intent behind the field
- The user is superseding or versioning an existing Hub record
- You want a pre-submission checklist to verify the finished record against (*Validation Checklist*)

Where the two appear to disagree, the template describes the current schema and the guide describes
authorial intent: follow the template for structure, the guide for content.
