# CDH Metadata — Full Annotated YAML Template (v0.2.0)

This is a complete reference template showing every field. Inline comments explain purpose,
constraints, and examples. Fields not marked optional are required when the parent block is used.

Official schema: https://github.com/CGIAR-Climate-Data-Hub/cdh-metadata-standard  
Real catalog records: https://github.com/CGIAR-Climate-Data-Hub/cdh-catalog/tree/main/records

```yaml
# yaml-language-server: $schema=../../spec/schemas/profiles/cdh.schema.json

# ── Schema declaration ────────────────────────────────────────────────────────
"$schema": https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.2.0/schemas/profiles/cdh.schema.json
cdh_schema_version: "v0.2.0"   # REQUIRED — always "v0.2.0"

# ── Extension declarations ────────────────────────────────────────────────────
# List ONLY the extensions you actually use. cdh is always required for Hub records.
extensions:
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.2.0/extensions/cdh/schema.json
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.2.0/extensions/datacube/schema.json
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.2.0/extensions/agriculture/schema.json
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.2.0/extensions/climate/schema.json
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.2.0/extensions/classification/schema.json

# ── Core identity ─────────────────────────────────────────────────────────────
id: my-dataset-slug             # REQUIRED — lowercase letters, digits, hyphens only
title: "My Dataset Title"       # REQUIRED — human-readable title
description: >                  # REQUIRED — canonical 2–5 sentence summary; AI-readable
  Describe what the dataset contains, how it was produced, the units of measurement,
  and any important caveats about interpretation.

license: CC-BY-4.0              # REQUIRED — SPDX identifier or plain string for proprietary
resource_type: dataset          # REQUIRED — one of: dataset | software | service | document

access: public                  # optional — public (default) | restricted | non-public
access_note: >                  # required only when access is restricted or non-public
  Describe access conditions here.

version: "v1.0"                 # optional — version string (e.g. v1.0, 2020, v2r2)
previous_version: ""            # optional — id of predecessor record when superseding

# ── Series ────────────────────────────────────────────────────────────────────
series:                         # optional — product family/series grouping
  name: MapSPAM
  url: https://mapspam.info

# ── Keywords ──────────────────────────────────────────────────────────────────
keywords:                       # REQUIRED — at least one item; plain strings or linked objects
  - gridded
  - precipitation
  - term: rainfall              # linked keyword — connects to external vocabulary
    scheme: https://agrovoc.fao.org/
    uri: http://aims.fao.org/aos/agrovoc/c_6498

note: >                         # optional — caveats or warnings not captured in description
  Values are densities (head/km²), so reproject to equal-area CRS before aggregation.

# ── Contacts ─────────────────────────────────────────────────────────────────
# REQUIRED — at least one entry must have licensor in roles.
# Every entry must include organization. roles is an array (one or more values).
# Valid roles: licensor | producer | processor | point-of-contact | custodian
contact:
  - organization: Food and Agriculture Organization of the United Nations
    roles: [licensor, producer]
    url: https://www.fao.org/home/en/
  - name: Jane Doe              # optional when organization alone identifies the contact
    organization: Alliance of Bioversity International and CIAT
    email: j.doe@cgiar.org
    roles: [point-of-contact, processor]
  - name: Brayden Youngberg
    roles: [processor, custodian]
    email: b.youngberg@cgiar.org
    organization: The Alliance of Bioversity International and CIAT

# ── Citation ─────────────────────────────────────────────────────────────────
# At least one of citation or doi is REQUIRED.
# citation is a structured object — NOT a plain string.
citation:
  title: "Dataset Title for Citation Purposes"  # optional
  authors:                      # REQUIRED — names in citation order
    - "Last, First"
    - "Organization Name"
  date: "2024"                  # REQUIRED — year or full date YYYY-MM-DD
  publisher: "Repository or Journal Name"        # optional
  url: https://example.com/landing-page          # optional

doi: 10.7910/DVN/SWPENT         # bare DOI only — no https://doi.org/ prefix
                                # if doi exists, citation is not required

# ── Related publications ──────────────────────────────────────────────────────
related_publications:           # optional
  - doi: 10.1371/journal.pone.0133381
  - citation:
      authors: ["Smith, J.", "Jones, K."]
      date: "2023"
      title: "A study on X"
      publisher: "Nature"
      url: https://example.com/paper

# ── Metadata tracking ─────────────────────────────────────────────────────────
created: "2026-07-28"           # optional — filled at publication if omitted (YYYY-MM-DD)
updated: "2026-07-28"           # optional — filled at publication if omitted (YYYY-MM-DD)

# ── Funding ───────────────────────────────────────────────────────────────────
funding:                        # optional
  - name: CGIAR Research Initiative on Climate Resilience
    url: https://www.cgiar.org/

# ── Spatial ───────────────────────────────────────────────────────────────────
spatial:                        # optional — strongly recommended for geospatial data
  bbox: [-180.0, -90.0, 180.0, 90.0]  # [west, south, east, north]; or [[...],[...]] for disjoint
  crs: "EPSG:4326"
  geography: [world]            # CDH geography vocab (UN M49 lower-kebab-case)
                                # e.g. [world], [kenya, uganda], [ethiopia]
  geometry_column: "geometry"   # conditional — name of geometry column for vector data
  resolution:
    - type: xy                  # one of: xy | x | y | point | polygon
      unit: degree
      value: 0.08333333
      label: "5 arc-minutes (~10km at equator)"
      note: ""                  # optional

# ── Temporal ─────────────────────────────────────────────────────────────────
# Use `date` for a single instant/period OR `start_date`/`end_date` for a span.
# These are mutually exclusive. Any ISO 8601 precision: year (2020), month (2020-06), day, datetime.
# Temporal CADENCE (daily, monthly, etc.) goes in dimensions[] with type: temporal — NOT here.
temporal:
  date: "2020"                  # static year; precision sets granularity
  # start_date: "2000-01-01"   # use instead of date for a span
  # end_date: "2023-12-31"     # null = open-ended (ongoing dataset)

# ── Datacube extension — Dimensions ───────────────────────────────────────────
# Use when the data has meaningful named dimensions beyond lat/lon.
# Cannot use "variable" as a dimension name (reserved for href_template).
dimensions:
  - name: species
    type: species               # any descriptive string; common: temporal | crop | species | technology | scenario
    description: "The livestock species for which the data is provided"
    values: [buffalo, cattle, chicken, goat, pig, sheep]
    reference_system: ""        # optional — vocabulary URI if values are controlled
  - name: time
    type: temporal
    description: "Year of the data"
    values: [2010, 2015, 2020]
    step: P5Y                   # optional — ISO 8601 duration for temporal cadence (P1D=daily, P1M=monthly, P1Y=annual)

# ── Datacube extension — Variables ────────────────────────────────────────────
variables:
  - name: density
    description: "Number of animals per km²"
    data_type: float32          # numpy-style dtype
    unit: "{head}/km2"          # UDUNITS-2 or UCUM; use {head} for dimensionless counts
    dimensions: []              # optional — which dimension axes this variable spans
    note: ""                    # optional — variable-specific caveats (dataset-wide → record note)
  - name: yield
    description: "Crop yield for each grid cell."
    data_type: float32
    unit: t ha-1
    note: >
      Relative quantity; do not sum yield values across grid cells. Regional summaries should use a
      weighted mean with harvested_area as the weight.

# ── Datacube extension — Joins ─────────────────────────────────────────────────
# Optional — for tables keyed to external spatial units (no embedded geometry)
joins:
  - target: "https://example.com/boundaries-dataset"  # target dataset URI or id
    left_fields: ["adm0_code"]   # key columns in this record
    right_fields: ["CODE"]        # matching columns in target

# ── Classification extension ─────────────────────────────────────────────────
# Use for categorical/classified variables. variable must match a variables[].name.
classes:
  - variable: land_cover
    values:
      - value: 1
        label: "Forest"
        description: "Closed and open broadleaved, mixed or needleleaved forest"
      - value: 2
        label: "Cropland"
        description: "Rainfed and irrigated croplands"
      - value: 0
        label: "NoData"
        description: "Fill value; masked area"

# ── Agriculture extension ─────────────────────────────────────────────────────
# Use when the dataset relates to specific agricultural commodities.
# Full commodity vocab includes: wheat, rice, maize, barley, sorghum, millets, pearl-millet,
# cassava, potato, sweet-potatoes, yams, common-bean, chickpeas, cowpeas, pigeon-pea, lentils,
# soybeans, groundnuts, coconuts, oil-palms, sunflower, rapeseed, sesame, sugarcane, sugarbeet,
# cotton, coffee, robusta-coffee, cocoa, tea, tobacco, banana, plantains, citrus, tomatoes,
# onions, vegetables, rubber, cattle, buffalo, chickens, goats, swine, sheep, and more.
commodities: [cattle, wheat, maize, rice]

# ── CDH extension ─────────────────────────────────────────────────────────────
# Required when the cdh extension URL is in extensions[].
cdh:
  domain: [climate]             # REQUIRED — at least one domain value (CDH vocab)
                                # options: adaptation | agricultural-production | boundaries |
                                #          climate | hydrology | mitigation | socioeconomic
  not_recommended_for:          # optional — discouraged uses to prevent misuse
    - use: "Near-real-time weather monitoring"
      reason: "Data is available with a 3-month lag"
      use_instead: "CHIRPS-Prelim for near-real-time estimates"  # optional

# ── Climate extension ─────────────────────────────────────────────────────────
# Use for climate projection datasets (CMIP5/CMIP6 derived data).
climate:
  mip_era: CMIP6                # optional — CMIP5 | CMIP6
  models: [GFDL-ESM4, MPI-ESM1-2-HR]  # optional — use "ensemble" for multi-model mean
  scenarios: [SSP245, SSP585]   # optional — scenario labels
  baseline:                     # optional
    start_date: "1981-01-01"
    end_date: "2010-12-31"
  bias_adjustment:              # optional
    method: "ISIMIP3BASD"
    reference_dataset: "W5E5 v2.0"
  downscaling:                  # optional
    method: "Statistical delta-mapping"
    resolution: 0.25

# ── Processing / provenance ───────────────────────────────────────────────────
# Optional but strongly recommended. At least one step MUST use id: source.
processing:
  - id: source
    description: "Original data release from the data provider"
    date: "2024-01-15"
    derived_from:
      - url: https://zenodo.org/record/12345
        title: "Original dataset v1"
    code: null                  # omit when no code is published for this step
  - id: cloud-optimize
    description: "Converted to Cloud-Optimized GeoTIFF and staged on S3"
    date: "2026-07-28"
    code:
      url: https://github.com/CGIAR-Climate-Data-Hub/cdh-data-pipeline/blob/main/recipes/example.py
      version: "abc1234"        # git commit hash or version tag

# ── Data assets (required) ────────────────────────────────────────────────────
# At least one entry required. Each entry must have a unique `name`.
# Different formats (Zarr vs COG) are SEPARATE entries, not extra locations.
# Extra locations = same content via different access paths (HTTPS + S3).
data:
  - name: zarr                  # REQUIRED — unique name across data[] and additional_assets[]
    locations:
      - url: https://digital-atlas.s3.amazonaws.com/cdh/data/example/example.zarr
        title: HTTPS            # optional access label
      - url: s3://digital-atlas/cdh/data/example/example.zarr
        title: S3
    processing_steps: [cloud-optimize]  # references processing[].id values
    description: "Zarr store of the dataset"
    nodata: "NaN"
    media_type: "application/vnd.zarr; version=3"
    file_size: "31.1 MB"

  - name: cogs
    locations:
      - url: https://digital-atlas.s3.amazonaws.com/cdh/data/example/cogs/
        title: HTTPS
      - url: s3://digital-atlas/cdh/data/example/cogs/
        title: S3
    # href_template splits one entry into many files per dimension combination.
    # Tokens in {braces} must match a dimensions[].name (not "variable" — that is reserved).
    href_template: "example-{species}.tif"
    processing_steps: [cloud-optimize]
    description: "Cloud-optimized GeoTIFFs per species"
    nodata: -3.4028235e+38
    media_type: "image/tiff; application=geotiff; profile=cloud-optimized"

# ── Additional assets (non-data sidecars) ─────────────────────────────────────
additional_assets:              # optional — same name-uniqueness rules as data[]
  - name: dimension-codes
    locations:
      - url: https://example.com/data/crop-codes.json
    description: "Dimension code list for crop values"
    media_type: application/json
    roles: [metadata, describedby]
    file_size: "5 KB"
  - name: thumbnail
    roles: [thumbnail]
    locations:
      - url: https://example.com/data/thumbnail.png
    media_type: "image/png"

# ── Additional links ──────────────────────────────────────────────────────────
additional_links:               # optional
  - name: "Project website"
    rel: about                  # common: about | related | describedby
    url: https://example.com/project
    description: "Project page describing methods and releases."
  - name: "User guide"
    rel: describedby
    url: https://example.com/docs
```

---

## Minimal valid record

The smallest record that passes CDH profile validation:

```yaml
# yaml-language-server: $schema=../../spec/schemas/profiles/cdh.schema.json
"$schema": https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.2.0/schemas/profiles/cdh.schema.json
cdh_schema_version: "v0.2.0"

extensions:
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.2.0/extensions/cdh/schema.json

id: my-dataset
title: "My Dataset"
description: "A brief description of the dataset."
license: CC-BY-4.0
resource_type: dataset
keywords:
  - climate
contact:
  - organization: My Organization
    roles: [licensor]
citation:
  authors:
    - "Author, Name"
  date: "2024"
data:
  - name: primary
    locations:
      - url: https://example.com/data/my-dataset.tif
cdh:
  domain: [climate]
```

---

## Key v0.2.0 breaking changes (from v0.1.0)

| What changed | v0.1.0 | v0.2.0 |
|---|---|---|
| Schema version | `"v0.1.0"` | `"v0.2.0"` |
| `$schema` field | not required | **required** |
| Contact roles field | `role: licensor` (scalar) | `roles: [licensor]` (array) |
| Citation format | plain string | structured object with `authors`, `date` |
| DOI format | URL allowed | bare DOI only (`10.xxx/yyy`) |
| `contact[].organization` | optional | **required** |
| `data[].name` | optional | **required**, unique |
| Temporal cadence | `temporal.resolution.unit/step` | `dimensions[]` with `type: temporal` + `step` |
| `resource_type` | includes `ai-skill` | removed; only `dataset \| software \| service \| document` |
| Stray nulls | allowed | rejected — omit optional fields instead |
