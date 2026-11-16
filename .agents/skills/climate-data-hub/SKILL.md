---
name: climate-data-hub
description: >
  Finds, inspects, and loads datasets from the CGIAR Climate Action Data Hub
  (cgiar-climate-data-hub.github.io), a catalog of openly licensed climate and
  agriculture data. Use when the user mentions the Climate Action Data Hub or
  the Hub, pastes a Hub URL, or asks what data exists for a topic ("is there
  rainfall data for Kenya?", "load SoilGrids clay for Malawi"). Needs only web
  fetch; Python is optional.
license: "MIT"
---

# Climate Action Data Hub

The Hub (`https://cgiar-climate-data-hub.github.io`, called `HUB` below) is a
catalog. Each dataset has a metadata record saying where the data is hosted and
how to read it.

## 1. Find

Fetch `HUB/llms.txt`. Its **Datasets** section lists every dataset with a
one-line description. Suggest 1-3 that fit, with a reason for each. To filter
by area, time, or variable, fetch `HUB/catalog.json`.

## 2. Inspect

Fetch the record as Markdown: `HUB/catalog/<id>/index.md`. The top lines give a
**Cite** line and links to file lists. The YAML below is the full record. Check:

- `access`: if `restricted`, the user needs an account or token. Ask for it;
  never invent one.
- `deprecated: true`: an older release. Use the current one at
  `HUB/catalog/<id>/index.md`.
- `note`, and each variable's `note` under `structures`: caveats you must
  apply, such as projection, scale factors, units, or update lag. Read them
  before using any values.
- `cdh.usage.not_recommended_for`: if the user's goal is listed, say so and
  suggest its `use_instead`.
- `data[]`: the ways to get the data. Pick one:
  - The one described as "Primary access", if any.
  - Zarr for an area, time range, or point from a large dataset.
  - GeoTIFF for a single map or file.
  - An `https://` location over `s3://` or `gs://`.
  - If it has an `href_template` (many files), pick files from the matching
    file list CSV in the header, not by filling in the template.

Tell the user the dataset, the format, and the license before loading.

## 3. Load

Use the code in [references/loading.md](references/loading.md). (Fetched from
the web? It's at
`https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/.agents/skills/climate-data-hub/references/loading.md`.)

- Read a small subset first. Never load a whole dataset unless the user asks
  and the size is known.
- Can't run code? Give the user the code with the URL filled in.
- A data host is blocked? Name it, give the code to run locally, and stop.

## 4. Cite

Give the record's **Cite** line verbatim with every result.

## Other skills

Pass on to these if they are installed:

- Process loaded data: `geospatial-cube-processor`
- Plot: `notebook-plots`, `climate-dashboard`, `sciplot-skill`
- Data not on the Hub: `climate-data-download`, `soil-data-download`
- Add a dataset to the Hub: `cdh-metadata`
