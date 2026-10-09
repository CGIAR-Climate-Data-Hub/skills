# `verify_record.py` — check catalogue

Each check writes findings as `{severity, path, check, message, record_value, observed, hint}`.
Paths are JSON-pointer-like into the record; `/structures[name]/…` addresses a structure by name.
v0.3.0 records are normalised first (root `dimensions`/`variables` → one structure, `joins` →
`foreign_keys`, `spatial.resolution` → an `xy` dimension, `data[].nodata` → variable nodata) so
every check below runs on the live catalog too.

| check | evidence | HIGH | MED | LOW / INFO |
| --- | --- | --- | --- | --- |
| `schema` | `validate-yaml.js` (needs `--standard-dir`) | fails on a record of the tooling's version | | INFO when record and tooling versions differ |
| `id`, `id-filename`, `schema-version`, `version` | record | id missing/invalid; `cdh_schema_version` missing; `version` missing (v0.4) | | file name ≠ id |
| `dates` | record | `created`/`updated` in the future; `updated` < `created` | missing (v0.4); processing date > `updated` | |
| `license-spdx` | spdx.org licenses.json | token not an SPDX id / `LicenseRef-` | | |
| `license-vs-page` | citation / first additional link page text | | licence tokens on the page do not include the declared licence | |
| `access` | record | restricted/non-public without `access_note` | | |
| `contacts` | record | no `licensor`; no `maintainer` (v0.4) | `custodian` (renamed); person without org; bad email | orcid/ror not full URLs |
| `citation`, `doi`, `doi-title`, `doi-year`, `doi-authors` | Crossref API, doi.org | no doi and no citation; author strings (v0.4); DOI does not resolve; Crossref title similarity < 0.55 | year or first authors disagree | DOI not in Crossref (DataCite) |
| `geography-vocab`, `geography-redundant` | `vocab/geography.json` | id not in vocab | | child listed beside its parent |
| `link`, `extensions-version` | HEAD / ranged GET of every URL | unreachable on `data`, `doi`, `citation.url`, `processing`, `extensions`, `file_index`; extension version ≠ schema version | unreachable elsewhere | 403 on non-blocking (bot-blocked) |
| `assets`, `assets-names` | record | no `data[]`; no location; duplicate asset names | | `media_type` missing |
| `asset-url`, `asset-size`, `asset-media-type` | HEAD of the primary location (Zarr root via `zarr.json`) | primary location unreachable | `file_size` off by > 5 % | Content-Type ≠ `media_type` |
| `asset-prefix` | S3 ListObjects on the prefix | prefix empty | prefix with neither template nor index (unverifiable) | |
| `template`, `template-expansion` | expand `href_template` from dimension values/categories/extent (+ `{variable}`), HEAD first/middle/last of each axis | any sampled expansion missing | template cannot be expanded from the structure | INFO count when all exist |
| `file-index` | fetch `cdh-inventory` CSV / HEAD other index files | no `url` column; row URL dead; index unreachable | cannot read | |
| `inspect` | open the asset (rasterio / xarray+zarr / duckdb / HTTP GET) | API endpoint ≥ 400 | cannot open | no inspector for the media type; library missing |
| `variable-missing`, `variable-undeclared`, `variable-dtype`, `variable-nodata`, `variable-unit`, `variable-count` | store arrays / raster bands / Parquet columns | declared variable absent | array/column not described; dtype or fill value differs; many variables on a one-band file without a template | unit attr differs; numeric variable without unit |
| `dimension-missing`, `dimension-values` | store dims/coords, Parquet columns + distinct values | declared values ≠ stored coordinate / column values | declared dimension not in the store | |
| `categories-coverage` | coarsest raster overview unique values; Parquet distinct values | stored codes with no category | | |
| `grid-step` | raster pixel size | declared `xy`/`x`/`y` step ≠ pixel size (rel 2e-3) | | |
| `cog-layout` | GDAL `LAYOUT` tag | | media type says cloud-optimized, GDAL says not | |
| `geometry-column`, `columns-undeclared` | Parquet columns | `geometry_column` absent | | columns not described |
| `bbox`, `bbox-vs-asset`, `crs-vs-asset`, `crs` | raster bounds / zarr coords | bbox malformed; asset extends outside the declared box; CRS differs | asset inside but much smaller than the box; crs missing | |
| `temporal`, `temporal-vs-asset` | zarr time coordinate | `date` with `start/end`; end < start; asset starts before / ends after the declared range | declared end later than the last time step | |
| `fk-fields`, `fk-reference`, `fk-target`, `fk-target-fields` | structure columns; cdh-catalog record list; target Parquet schema | FK field not in structure; no reference; target id not in catalog / URL dead; referenced field not in target | | |
| `provenance`, `parent` | record; cdh-catalog | `derived_from` with both id and url; id not in catalog; placeholder code URL; `parent` not in catalog | derived product with no `processing[]` | source version / code version not pinned |
| `prose`, `prose-year`, `usage` | record text | placeholder markers; SAMPLE/FICTIONAL | description < 80 chars | year in description not in `temporal`; no `not_recommended_for` |

## Tolerances

- bbox: max(0.05°, 2 % of the declared extent); CRS compared as normalised strings.
- grid step: relative 2e-3. File size: 5 %. Title similarity: `difflib` ratio 0.55.
- Template sampling: first, middle and last value of every token axis, capped by `--max-template`.
- Raster category sampling reads the coarsest overview only; a code that appears in < 1 overview
  pixel can be missed — treat "no finding" as *not contradicted*, not proven.

## Known limits (report as UNVERIFIED, never as pass)

- NetCDF and GeoPackage assets are not opened (download needed); only their URLs are probed.
- `gs://` locations are not converted to HTTPS.
- Licence-vs-page is a token search on one page; bot-blocked providers (OECD, IMF, DHS, IUCN …)
  return nothing and the licence stays unverified.
- Crossref covers DOIs registered there; DataCite DOIs (Dataverse, Zenodo) resolve but are not
  cross-checked for title/authors.
- Nothing here judges whether a *description* is honest, a *contact* is real, or a *licence* is
  the right one for a redistribution — that is Part 2 of the skill.
