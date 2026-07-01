# CDH Metadata — Full Annotated YAML Template

This is a complete template showing every field. Fields marked `# REQUIRED` must be present.
Fields marked `# optional` may be omitted. Inline comments explain purpose and constraints.

```yaml
# yaml-language-server: $schema=../../spec/schemas/profiles/cdh.schema.json

# ── Schema version ────────────────────────────────────────────────────────────
cdh_schema_version: "v0.1.0"   # REQUIRED — always this value

# ── Extension declarations ────────────────────────────────────────────────────
# List only the extensions you actually use. cdh is almost always needed.
extensions:
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.1.0/extensions/cdh/schema.json
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.1.0/extensions/datacube/schema.json
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.1.0/extensions/agriculture/schema.json
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.1.0/extensions/climate/schema.json
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.1.0/extensions/classification/schema.json

# ── Core identity ─────────────────────────────────────────────────────────────
id: my-dataset-slug          # REQUIRED — lowercase letters, digits, hyphens; e.g. chirps-2020-ethiopia
title: "My Dataset Title"   # REQUIRED — human-readable title
description: >               # REQUIRED — canonical 2–5 sentence summary; AI-readable
  Describe what the dataset contains, how it was produced, the units of measurement,
  and any important caveats about interpretation.

license: CC-BY-4.0           # REQUIRED — SPDX identifier or plain string for proprietary licenses
resource_type: dataset       # REQUIRED — dataset | software | service | ai-skill | document

version: "v1.0"             # optional — version of the dataset (string)
doi: "10.xxxx/xxxxx"        # optional — bare DOI, no https://doi.org/ prefix

# ── Keywords ──────────────────────────────────────────────────────────────────
keywords:                    # REQUIRED — at least one item; plain strings or linked objects
  - gridded
  - precipitation
  - term: rainfall            # linked keyword — connects to an external vocabulary
    scheme: https://agrovoc.fao.org/
    uri: http://aims.fao.org/aos/agrovoc/c_6498

note: >                      # optional — caveats or warnings not captured in description
  Values are densities, so reproject to equal-area CRS before aggregation.

# ── Contacts ─────────────────────────────────────────────────────────────────
contact:                     # REQUIRED — at least one entry; at least one must have licensor role
  - organization: Food and Agriculture Organization of the United Nations
    roles: [licensor, producer]
    url: https://www.fao.org/home/en/
  - name: Jane Doe
    organization: Alliance of Bioversity International and CIAT
    email: j.doe@cgiar.org
    roles: [point-of-contact, processor]
    url: null

# ── Citation ─────────────────────────────────────────────────────────────────
# At least one of citation or doi is REQUIRED
citation:
  title: "Dataset Title for Citation Purposes"
  authors:
    - "Last, First"
    - "Organization Name"
  date: "2024"               # year or full date YYYY-MM-DD
  publisher: "Repository or Journal Name"
  url: https://doi.org/10.xxxx/xxxxx

# ── Related publications ──────────────────────────────────────────────────────
related_publications:        # optional
  - doi: 10.xxxx/xxxxx
  - doi: null
    citation:
      authors: ["Smith, J.", "Jones, K."]
      date: "2023"
      title: "A study on X"
      publisher: "Nature"
      url: https://example.com/paper

# ── Metadata tracking ─────────────────────────────────────────────────────────
created: "2026-07-01"        # REQUIRED — date record was first published (YYYY-MM-DD)
updated: "2026-07-01"        # REQUIRED — date record was last revised (YYYY-MM-DD)
previous_version: null       # optional — id of the predecessor record

# ── Spatial ───────────────────────────────────────────────────────────────────
spatial:                     # optional block — strongly recommended for geospatial data
  bbox: [-180.0, -90.0, 180.0, 90.0]   # [west, south, east, north] WGS84
  crs: "EPSG:4326"
  geography: [world]         # CDH geography vocab; common: world, africa, ethiopia, colombia
  geometry_column: null      # name of geometry column in vector tables
  resolution:
    - type: xy               # xy | x | y | point | polygon
      unit: degree
      value: 0.05
      label: "~5.5 km at equator"
      note: null

# ── Temporal ─────────────────────────────────────────────────────────────────
temporal:                    # optional block
  start_date: "2020-01-01"
  end_date: "2020-12-31"
  resolution:
    unit: year               # e.g. day, month, year
    step: P1Y                # ISO 8601 duration: P1D=daily, P1M=monthly, P1Y=annual
    note: "Static reference year 2020"
    values: null             # e.g. [1,2,3,...,12] for months; omit when continuous

# ── Data assets ───────────────────────────────────────────────────────────────
data:                        # REQUIRED — at least one entry
  - name: "Primary raster"
    description: "Cloud-optimized GeoTIFF of the main variable"
    locations:
      - url: https://example.com/data/my-dataset.tif
        title: HTTPS
      - url: s3://my-bucket/data/my-dataset.tif
        title: S3
    media_type: "image/tiff; application=geotiff; profile=cloud-optimized"
    file_size: "120 MB"
    nodata: -9999
    processing_steps: [cloud-optimize]   # references processing[].id values

  # Template-based asset (expands one entry per combination of dimension values)
  - name: "Per-species COGs"
    locations:
      - url: https://example.com/data/cogs/
        title: HTTPS
    href_template: "mydata-{species}.tif"   # {species} must match a dimensions[].name
    media_type: "image/tiff; application=geotiff; profile=cloud-optimized"
    nodata: null
    processing_steps: [cloud-optimize]

# ── Additional assets (non-data sidecars) ─────────────────────────────────────
additional_assets:           # optional
  - name: Thumbnail
    roles: [thumbnail]
    locations:
      - url: https://example.com/data/thumbnail.png
        title: HTTPS
    media_type: "image/png"
    file_size: null

# ── Additional links ──────────────────────────────────────────────────────────
additional_links:            # optional
  - name: "Source dataset landing page"
    rel: related
    url: https://example.com/landing-page
  - name: "User guide"
    rel: describedby
    url: https://example.com/docs

# ── Funding ───────────────────────────────────────────────────────────────────
funding:                     # optional
  - name: CGIAR Research Initiative on Climate Resilience
    url: https://www.cgiar.org/

# ── Processing / provenance ───────────────────────────────────────────────────
processing:                  # optional, but strongly recommended
  - id: source               # REQUIRED step id — marks the original data source
    description: "Original data release from the data provider"
    date: "2024-01-15"
    derived_from:
      - url: https://zenodo.org/record/12345
        title: "Original dataset v1"
    code: null               # omit when no code is published for this step

  - id: cloud-optimize
    description: "Converted to Cloud-Optimized GeoTIFF and staged on S3"
    date: "2026-07-01"
    code:
      url: https://github.com/org/repo/blob/main/scripts/optimize.py
      version: "abc1234"     # git commit hash or version tag
    derived_from: []

# ── CDH extension ─────────────────────────────────────────────────────────────
# Required when the cdh extension URL is in extensions[]
cdh:
  domain: [climate]          # REQUIRED within this block; at least one domain value
  use_cases:
    - "Monitoring precipitation trends for agricultural planning"
    - "Bias-correction baseline for climate projections"
  not_recommended_for:
    - use: "Near-real-time weather monitoring"
      reason: "Data is available with a 3-month lag"
      use_instead: "CHIRPS-Prelim for near-real-time estimates"

# ── Datacube extension ────────────────────────────────────────────────────────
# Use when the data has meaningful named dimensions beyond lat/lon/time
dimensions:
  - name: species
    type: species             # can be any label; spatial | temporal | bands | or domain axis
    description: "Livestock species"
    values: [cattle, sheep, goats, pigs, chickens, buffalo]
  - name: time
    type: temporal
    description: "Year of the data"
    values: [2010, 2015, 2020]

variables:
  - name: density
    description: "Number of animals per km²"
    data_type: float32       # numpy-style dtype
    unit: "{head}/km2"       # UDUNITS-2 or UCUM; use {head} for dimensionless counts
    note: null
  - name: uncertainty
    description: "Coefficient of variation of the density estimate"
    data_type: float32
    unit: null
    note: "Values > 1 indicate high uncertainty; use with caution"

# ── Classification extension ─────────────────────────────────────────────────
# Use for categorical / classified variables
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

# ── Agriculture extension ────────────────────────────────────────────────────
# Use when the dataset relates to specific agricultural commodities
commodities: [cattle, wheat, maize, rice]
# Full commodity vocab: livestock, buffalo, cattle, chickens, goats, swine, sheep,
# wheat, maize, rice, sorghum, millet, barley, cassava, potato, soybean, groundnut, etc.

# ── Climate extension ─────────────────────────────────────────────────────────
# Use for climate projection datasets (CMIP5/CMIP6 derived data)
climate:
  mip_era: CMIP6             # CMIP5 | CMIP6
  models: [GFDL-ESM4, MPI-ESM1-2-HR]   # use "ensemble" for multi-model mean
  scenarios: [SSP2-4.5, SSP5-8.5]
  baseline:
    start_date: "1981-01-01"
    end_date: "2010-12-31"
  bias_adjustment:
    method: "ISIMIP3BASD"
    reference_dataset: "W5E5 v2.0"
  downscaling:
    method: "Statistical delta-mapping"
    resolution: 0.25
```

---

## Minimal valid record (no extensions)

The smallest record that passes schema validation:

```yaml
cdh_schema_version: "v0.1.0"
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
created: "2026-07-01"
updated: "2026-07-01"
citation:
  authors:
    - "Author, Name"
  date: "2024"
data:
  - locations:
      - url: https://example.com/data/my-dataset.tif
```
