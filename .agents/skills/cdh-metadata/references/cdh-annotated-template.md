# CDH Metadata — Full Annotated YAML Template (v0.4.1)

A complete reference template showing every field. Inline comments explain purpose, constraints, and
examples. Fields not marked optional are required when the parent block is used.

Official schema: https://github.com/CGIAR-Climate-Data-Hub/cdh-metadata-standard  
Worked examples: https://github.com/CGIAR-Climate-Data-Hub/cdh-metadata-standard/tree/main/examples  
Real catalog records: https://github.com/CGIAR-Climate-Data-Hub/cdh-catalog/tree/main/records

> **v0.4.0 reshaped the data model.** `dimensions` and `variables` now live inside `structures[]`,
> the datacube and classification extensions are gone, `spatial.resolution` is replaced by
> horizontal dimensions, and `version`, `created`, `updated` and a `maintainer` contact are
> required. See **Key v0.4.x breaking changes** at the end.

```yaml
# yaml-language-server: $schema=https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/schemas/profiles/cdh.schema.json

# ── Schema declaration ────────────────────────────────────────────────────────
# There is NO `$schema` key — it was removed in v0.4.0 because nothing read it.
# The editor binds the profile through the yaml-language-server comment above,
# and cdh_schema_version names the release the record targets.
cdh_schema_version: "v0.4.1"         # REQUIRED. Always the release you authored against.

extensions:                          # REQUIRED. List every extension actually used.
  # The cdh extension is mandatory for every Hub record.
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/extensions/cdh/schema.json
  # Add only when the matching block is present:
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/extensions/climate/schema.json       # climate:
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/extensions/agriculture/schema.json   # commodities:
  # There is no datacube extension (folded into core as structures[]) and no
  # classification extension (replaced by variables[].categories). Their URLs 404.

# ── Identity ──────────────────────────────────────────────────────────────────
id: banana-climate-risk-indicators   # REQUIRED. Lowercase, digits, hyphens. URL-safe and stable.
                                     # NEVER put the version in the id — every release shares one id.
version: "2.1"                       # REQUIRED by the CDH profile. Copy the source's own label
                                     # (v2r2, 2.1, 2020); start at "1" if the source is unversioned.
                                     # Letters, digits, dots, underscores, hyphens. Quote it.
previous_version: "2.0"              # Optional. The predecessor's VERSION label, not its id.
deprecated: false                    # Optional. true on a superseded release, which keeps its id.
parent: banana-climate-risk-grid     # Optional. The id of the record this one is a child
                                     # representation of (an aggregation, reprojection, subset).
                                     # Inherits NOTHING — repeat license, contacts, extent here.

title: Banana Climate Risk Indicators for East Africa
description: >                       # REQUIRED. 2–5 sentences: what it is and what it is for.
  Gridded climate risk indicators for banana production across East Africa, derived from
  bias-adjusted CMIP6 projections. Values describe heat and water stress exposure during the
  growing period. Keep variables, units, geographies and dates OUT of this text — they each have
  a structured field where people and machines can filter on them.

license: CC-BY-4.0                   # REQUIRED. An SPDX expression. A custom LicenseRef-* also
                                     # needs an additional_links entry with rel: license.
resource_type: dataset               # REQUIRED. dataset | software | service | document

attribution: >                       # Optional. A credit line reusers must reproduce, for sources
  Contains modified Copernicus Climate Change Service information (2026).
                                     # that mandate wording. Keeps such text out of `note`.

access: public                       # Optional. public | restricted | non-public
access_note: >                       # REQUIRED when access is restricted or non-public.
  Discoverable, but download requires an account at https://example.org/request.

note: >                              # Optional. ONLY for a caveat a reader would miss — a known
  Values over open water are masked. The regular lat/lon grid has cells whose
  ground area shrinks toward the poles.
                                     # artefact, an invalid region, a source version mismatch.
                                     # Not a catch-all: credit → attribution, provenance →
                                     # processing[].derived_from, axis labels → dimension description.

created: "2026-10-07"                # REQUIRED. Date the record was first written.
updated: "2026-10-07"                # REQUIRED. Date it was last changed.

# ── Discovery ─────────────────────────────────────────────────────────────────
keywords:                            # REQUIRED. At least one. EXTRA SEARCH TERMS ONLY — aliases,
  - heat stress                      # method names, acronyms, user-facing phrasing. Never repeat
  - banana                           # something that already has a structured field: places go to
  - term: climate change             # spatial.geography, crops to commodities, period to temporal.
    scheme: https://agrovoc.fao.org/ # A keyword may be a plain string or a linked object.
    uri: http://aims.fao.org/aos/agrovoc/c_1666
    description: Linked keyword surfaced as an ontology theme in serialized output.

series:                              # Optional. A program or product brand (MapSPAM, GLW, CHIRPS).
  name: CGIAR Climate Risk Atlas     # A discovery grouping — NOT a version or parent relationship.
  url: https://example.org/atlas     # A series may hold heterogeneous datasets.

# ── People ────────────────────────────────────────────────────────────────────
contact:                             # REQUIRED. Every entry needs `organization` and ≥1 role.
  - organization: Alliance of Bioversity International and CIAT
    name: Jane Doe                   # Optional for an organization-only contact.
    email: jane.doe@example.org
    url: https://alliancebioversityciat.org
    orcid: https://orcid.org/0000-0002-1825-0097   # Optional. Full URL form.
    roles: [licensor, point-of-contact]            # ≥1 entry MUST hold `licensor` (core).
  - organization: Alliance of Bioversity International and CIAT
    name: Sam Sample
    email: sam.sample@example.org
    roles: [maintainer]                            # ≥1 entry MUST hold `maintainer` (CDH profile).
                                                   # `custodian` was renamed to this in v0.4.0.
  - organization: Food and Agriculture Organization of the United Nations
    url: https://www.fao.org
    ror: https://ror.org/00pe0tf51                 # Optional. Full URL form.
    roles: [producer, processor]
# Roles: licensor | producer | processor | point-of-contact | maintainer

citation:                            # citation OR doi is REQUIRED (an anyOf rule, so it is absent
                                     # from `required` and fails only at validation time).
  title: Banana Climate Risk Indicators for East Africa
  authors:                           # OBJECTS, never plain strings (v0.4.0 breaking change).
    - family: Doe                    # A person: {family, given?} (+ optional orcid).
      given: J.
      orcid: https://orcid.org/0000-0002-1825-0097
    - organization: Alliance of Bioversity International and CIAT   # A body: {organization}.
  date: "2026"                       # A year, month, date, or date-time. Not free text.
  publisher: CGIAR Climate Data Hub
  url: https://example.org/atlas/banana-climate-risk
doi: 10.7910/DVN/EXAMPLE             # Optional. BARE DOI — never the https://doi.org/ prefix.

related_publications:                # Optional. Each entry needs `doi` or `citation`.
  - doi: 10.1016/j.example.2026.01.001
  - citation:
      title: Modelling banana heat stress under CMIP6 scenarios
      authors:
        - family: Smith
          given: J.
        - family: Jones
          given: K.
      date: "2025"
      publisher: Journal of Example Studies
      url: https://example.org/papers/banana-heat

funding:                             # Optional. Each entry needs `name`.
  - name: CGIAR Initiative on Climate Resilience
    url: https://www.cgiar.org

# ── Coverage ──────────────────────────────────────────────────────────────────
spatial:
  bbox: [28.9, -11.8, 41.9, 5.1]     # [west, south, east, north]. Numbers, never a string.
                                     # For disjoint coverage use a list of boxes:
                                     #   bbox:
                                     #     - [10, -5, 22, 8]
                                     #     - [28, 6, 40, 20]
  crs: EPSG:4326                     # REQUIRED for geospatial assets.
  geography:                         # Optional. CDH geography vocabulary.
    - kenya
    - uganda
    - united-republic-of-tanzania
  # NOTE: spatial.resolution was REMOVED in v0.4.0. Grid spacing is a horizontal
  # dimension inside a structure — see `structures` below.
  # NOTE: spatial.geometry_column moved to structures[].geometry_column.

temporal:                            # Use `date` OR start_date/end_date — mutually exclusive.
  start_date: "2030"
  end_date: "2050"                   # null means the RESOURCE ITSELF keeps growing. A scheduled
                                     # mirror states its real end date instead.
  update_frequency: annual           # Optional. How often the resource gains new data — distinct
                                     # from the source's cadence and from a dimension's `step`.
                                     # daily | weekly | monthly | quarterly | semiannual |
                                     # annual | irregular
  # For a static dataset instead:
  #   date: "2024"

# ── structures[] — the data dictionary ────────────────────────────────────────
# Replaces the record-level `dimensions`/`variables` of v0.3.0 and the datacube
# extension. One layout → one structure. A record whose assets hold different
# dimensions or variables (monthly vs seasonal file sets; tables with different
# columns) gets one structure per layout. Names are unique WITHIN a structure and
# may repeat across structures, so two tables can each have a `value` column.
structures:
  - name: projections                # REQUIRED, unique across structures.
    dimensions:                      # Every dimension needs name, type, description.
      - name: cell
        type: xy                     # Horizontal axis. xy = one spacing for both; use `x` and `y`
        description: 5 arc-minute grid (~9 km at the equator).
        step: 0.0833                 # a NUMBER on horizontal axes (a duration on temporal).
        unit: degree                 # Omit `step` entirely for a table's coordinate columns.
        # extent: [28.9, 41.9]       # Optional numeric [min, max] in `unit`, for a grid whose
                                     # edges the WGS84 bbox does not give exactly.
      - name: horizon
        type: temporal               # The ONLY type whose step is an ISO 8601 duration.
        description: Projection horizon (reference year).
        extent: ["2030", "2050"]     # `extent` + `step` replaces listing every value on a regular
        step: P20Y                   # axis. Requires step, excludes values. Must be nonzero —
                                     # P0D is rejected. `step` is SPACING only: a 30-year window
                                     # every 10 years is step: P10Y with the length in description.
      - name: scenario
        type: scenario               # Any descriptive lowercase string is a valid non-reserved type.
        description: Emissions scenario label.
        reference_system: https://example.org/vocab/scenarios
        values: [ssp245, ssp585]     # Non-empty when present; omit rather than writing [].
                                     # Duplicates are rejected.
      - name: adm2_code
        type: location               # A place-key column. Any number of these allowed.
        description: GAUL admin-2 unit, the reporting unit of each row.
        data_type: string            # Give key columns a data_type so "001" reads as text, not 1.
        reference_system: https://example.org/boundaries/gaul-2015
    variables:                       # REQUIRED, at least one. name + description are required.
      - name: heat_stress_days
        description: >
          Days during the growing period when daily maximum temperature exceeded 38 °C. Higher
          values indicate greater heat hazard.
        data_type: float32           # Closed list — see the vocabulary table below.
        unit: day                    # Optional; omit for unitless values such as class codes.
        nodata: -9999                # The fill value lives HERE now, not on data[].nodata.
        note: Temperature stress only; does not represent full crop impact.
      - name: risk_class
        description: Categorical risk level derived by binning heat_stress_days.
        data_type: uint8
        nodata: 255                  # A uint8 cannot hold -9999, so this variable has its own.
        categories:                  # Replaces the classification extension's classes[].
          - value: 0                 # `value` is a string or an integer. label is required.
            label: Low
          - value: 1
            label: Moderate
            description: 10–20 heat stress days.
          - value: 2
            label: High
            description: More than 20 heat stress days.
    foreign_keys:                    # Optional. Was `joins[]`. Frictionless Table Schema shape.
      - fields: [adm2_code]          # Sits on the structure whose columns it names.
        reference:
          resource: gaul-admin2-boundaries   # A catalog record id, or an absolute URI.
          asset: boundaries                  # REQUIRED when the target has >1 data[] entry.
          fields: [ADM2_CODE]
    # geometry_column: geom          # Optional. Moved here from spatial in v0.4.0.

  - name: static                     # A second structure: variables on different axes.
    dimensions:
      - name: cell
        type: xy
        description: 5 arc-minute grid (~9 km at the equator).
        step: 0.0833
        unit: degree
    variables:
      - name: cropland_mask
        description: Cells modelled as banana cropland; risk is only meaningful where this is 1.
        data_type: uint8
        nodata: 255
        categories:
          - { value: 0, label: Not cropland }
          - { value: 1, label: Cropland }

# ── CDH extension (mandatory block) ───────────────────────────────────────────
cdh:
  domain: [adaptation, agricultural-production]   # REQUIRED. One or more.
  # adaptation | agricultural-production | boundaries | climate | hydrology |
  # mitigation | socioeconomic
  usage:                             # Optional. Omit entirely rather than writing usage: {}.
    intended_uses:                   # Illustrative, not exhaustive. Skip terms as broad as
      - regional hotspot mapping     # "research" or "decision-making" — they guide no one.
      - targeting of adaptation investment
    not_recommended_for:             # Usually the more valuable half: prevents misuse without
      - use: field-scale planting decisions      # narrowing the legitimate uses.
        reason: the grid is far too coarse to represent a single farm.
        use_instead: locally validated agronomic data.

# ── Climate extension (only when climate-related) ─────────────────────────────
climate:
  mip_era: CMIP6                     # CMIP5 | CMIP6
  scenarios: [ssp245, ssp585]
  models: [MPI-ESM1-2-HR, EC-Earth3]
  baseline:                          # Required for anomalies and baseline-relative indicators.
    start_date: "1995-01-01"
    end_date: "2014-12-31"
  bias_adjustment:
    method: Quantile delta mapping
    reference_dataset: CHIRTS-daily v1
  downscaling:
    method: Statistical downscaling
    resolution: 0.0833 degree

# ── Agriculture extension (only when commodity-specific) ──────────────────────
commodities:                         # Values from vocab/commodity.json.
  - banana

# ── Provenance ────────────────────────────────────────────────────────────────
processing:                          # Optional. Every step needs `id` and `description`.
  - id: source                       # At least one step must have id: source.
    description: >
      Bias-adjusted daily CMIP6 projections aggregated to growing-period indicators.
    code:
      url: https://github.com/example-org/banana-risk-pipeline
      version: 0f3ac9d               # Commit hash or version tag.
    date: "2026-04-21"
    derived_from:
      - title: NEX-GDDP-CMIP6        # An entry takes `url` OR `id`, never both.
        url: https://example.org/nex-gddp-cmip6
        version: "1.5"               # The source release used, as the source labels it.
      - title: The gridded parent record
        id: banana-climate-risk-grid # A Hub record id instead of a storage URL.
        version: "2.0"               # Pins the release this was computed from.
  - id: aggregate
    description: Area-weighted aggregation of the grid to GAUL admin-2 units.
    date: "2026-05-02"

# ── Assets ────────────────────────────────────────────────────────────────────
data:                                # REQUIRED. Each entry needs a unique `name`.
  - name: zarr
    description: Zarr representation of the full indicator cube.
    locations:                       # Each url must be an ABSOLUTE URI.
      - url: https://example.org/data/banana-risk/v2/cube.zarr
        title: HTTPS                 # Several locations = several addresses for the SAME file.
      - url: s3://example-bucket/banana-risk/v2/cube.zarr
        title: S3
    media_type: application/vnd.zarr; version=3
    file_size: 250 MB                # Whole bytes, or a number + unit (B/KB/MB/GB/TB/PB, ×1000).
                                     # Free text is rejected.
    processing_steps: [source, aggregate]       # No duplicates.
    structures: [projections, static]           # REQUIRED when the record has >1 structure.
                                                # Each variable belongs to only one of them.
  - name: netcdf-west
    description: The cube clipped to the western area, one NetCDF file.
    locations:
      - url: https://example.org/data/banana-risk/v2/west.nc
    media_type: application/x-netcdf            # NOT application/netcdf (changed in v0.4.0).
    file_size: 90 MB
    checksum: sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
                                     # Single-file entries only. Not allowed with href_template
                                     # or file_index. Digest length must match the algorithm.
    spatial:                         # This asset's OWN coverage, for selecting files by area.
      bbox: [28.9, -11.8, 35.0, 5.1] # Never copied down from the top-level spatial.
    structures: [projections, static]
  - name: cogs
    description: Per-slice Cloud Optimized GeoTIFFs, one file per scenario and horizon.
    locations:
      - url: https://example.org/data/banana-risk/v2/cogs/
    href_template: "risk_{scenario}_{horizon:%Y}.tif"
                                     # Tokens name dimensions. On a temporal dimension a token may
                                     # carry a strftime format — %Y, %m, %d only, fixed padding.
    media_type: "image/tiff; application=geotiff; profile=cloud-optimized"
    file_size: 3 MB
    structures: [projections]
  - name: tiles
    description: A file set too irregular for a template, described by an index.
    file_index:                      # locations[] may be omitted when a file_index carries them.
      - format: cdh-inventory        # stac-geoparquet | gti | vrt | kerchunk | icechunk |
        locations:                   # cdh-inventory. Any ONE index is enough.
          - url: https://example.org/data/banana-risk/v2/inventory.csv
        media_type: text/csv
      - format: vrt
        locations:
          - url: https://example.org/data/banana-risk/v2/tiles.vrt
    media_type: "image/tiff; application=geotiff"
    structures: [projections]

additional_assets:                   # Optional. Supporting files, not the data itself.
  - name: agent guide
    description: Keys, join columns, quirks, and a tested query for agents and analysts.
    locations:
      - url: ./AGENTS.md             # A small sidecar may use a relative path; validation checks
    media_type: text/markdown        # the file exists. Documentation only — never data.
    roles: [agents]
  - name: qa report
    description: QA/QC report documenting validation checks for this release.
    locations:
      - url: https://example.org/data/banana-risk/v2/qaqc.pdf
    media_type: application/pdf
    roles: [metadata, validation]
    file_size: 800 KB
  - name: usage notebook
    description: Runnable example that opens the cube and plots one indicator.
    locations:
      - url: https://example.org/data/banana-risk/v2/example.ipynb
    media_type: application/vnd.jupyter
    roles: [example]
# Suggested roles: metadata | validation | describedby | thumbnail | overview |
# visual | example (runnable code) | agents (a Markdown guide for AI agents)

additional_links:                    # Optional.
  - title: Project landing page      # `title` — renamed from `name` in v0.4.0.
    rel: about
    url: https://example.org/atlas
    description: Landing page describing the atlas and its methods.
  - title: Changelog
    rel: version-history
    url: https://example.org/atlas/banana-climate-risk/changelog
```

---

## Minimal valid record

Everything the core schema and the CDH profile require, and nothing else.

```yaml
# yaml-language-server: $schema=https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/schemas/profiles/cdh.schema.json
cdh_schema_version: "v0.4.1"
extensions:
  - https://cgiar-climate-data-hub.github.io/cdh-metadata-standard/v0.4.1/extensions/cdh/schema.json

id: my-dataset
version: "1"
title: My Dataset
description: >
  What this resource is and what it can be used for.
license: CC-BY-4.0
resource_type: dataset
created: "2026-10-07"
updated: "2026-10-07"

keywords:
  - example

contact:
  - organization: My Organization
    roles: [licensor, maintainer]

citation:                 # citation OR doi is required - an anyOf rule, so it is
  title: My Dataset       # absent from `required` and fails only at validation time.
  authors:
    - organization: My Organization
  date: "2026"

cdh:
  domain: [climate]

data:
  - name: data
    description: The dataset file.
    locations:
      - url: https://example.org/data/my-dataset.tif
    media_type: "image/tiff; application=geotiff"
```

A geospatial record also needs `spatial.bbox` (or `spatial.geography`) and `spatial.crs`, and a
record with named data values needs a `structures[]` entry. The validator cannot tell whether a
record is geospatial — check those by hand.

---

## Key v0.4.x breaking changes (from v0.3.0)

**Removed outright**

| Gone | Replacement |
|------|-------------|
| `$schema` key | nothing — the yaml-language-server comment binds the editor |
| datacube extension | folded into core as `structures[]` |
| classification extension | `variables[].categories` |
| `spatial.resolution` | an `xy` (or `x` + `y`) dimension with a numeric `step` |
| `data[].nodata` | `variables[].nodata` |
| `variables[].dimensions` | a variable has every dimension of its structure |
| `templates/`, draft validation | start from a record in `examples/` |

**Renamed**

| v0.3.0 | v0.4.1 |
|--------|--------|
| `joins[]` | `foreign_keys[]` (Frictionless shape) |
| `spatial.geometry_column` | `structures[].geometry_column` |
| contact role `custodian` | `maintainer` |
| `additional_links[].name` | `additional_links[].title` |
| `classes[]` | `variables[].categories` |
| `media_type: application/netcdf` | `application/x-netcdf` |

**Newly required**

- `version` (CDH profile), `created`, `updated` (core)
- at least one contact with `roles: [maintainer]`, alongside the existing `licensor`
- `variables[]` must be non-empty; every `processing[]` step needs `id` + `description`;
  `contact[].roles` needs at least one role; `funding[]` entries need `name`;
  `related_publications[]` entries need `doi` or `citation`

**Reshaped**

- `citation.authors[]` entries are objects — `{family, given?}` or `{organization}` — never strings
- `previous_version` holds the predecessor's **version**, not its id; superseded releases keep their
  `id` and gain `deprecated: true`
- `dimensions[].step` is spacing only, must be nonzero, and is a duration on `temporal` but a number
  on horizontal axes
- temporal date-times must be RFC 3339 with an offset, and real calendar dates
- `file_size` is whole bytes or a number + unit; `locations[].url` must be an absolute URI
- `variables[].data_type` is a closed list; `variables[].unit` is optional

**Added worth knowing**

`parent` · `attribution` · `temporal.update_frequency` · `data[].checksum` · `data[].file_index[]` ·
`data[].spatial` · `dimensions[].extent` · `dimensions[].data_type` · `categories` on dimensions ·
`orcid` / `ror` on contacts and authors · `processing[].derived_from[].id` and `.version` ·
strftime tokens in `href_template` · the `agents` asset role

---

## Key v0.3.0 breaking changes (from v0.2.0)

Kept for records that have not yet moved past v0.3.0.

- `cdh.not_recommended_for` moved under `cdh.usage`
- `spatial.resolution[]` took exactly one characterization per record
- `dimensions[].type` became a closed-ish list; `time`/`date` aliases rejected
- `classes[].values[].value` restricted to string or integer
