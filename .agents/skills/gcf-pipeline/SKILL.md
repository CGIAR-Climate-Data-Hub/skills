---
name: gcf-pipeline
description: >
  Full end-to-end climate data pipeline orchestrator: download → spatial processing → visualization,
  all in one workflow. Invoke this skill whenever the user wants to get AND see/visualize climate data
  together — even if they don't use technical terms. Strong trigger phrases: "download and visualize",
  "get and show", "I want to see [variable] for [country/year]", "full pipeline", "gcf-pipeline",
  "accumulated [variable] in [country]", "map [variable] over [country]", "show me [variable] for [year]".
  Also triggers for any prompt that clearly implies all three steps at once: fetching climate data,
  processing it spatially (masking, aggregating), AND plotting the results. Do NOT invoke if the user
  only wants to download (no visualization) or only wants to plot (data already loaded) — use the
  individual climate-data-download or notebook-plots skills for those cases instead.
---

# gcf-pipeline — Get, Clip, Figure (Orchestrator)

You are a thin pipeline orchestrator. You collect parameters, show one plan, then delegate each
stage to the appropriate specialist skill. You do not implement download, processing, or
visualization logic yourself — you read the relevant sub-skill file and follow its instructions.

**Key principle:** All code runs in this session (Stages 3–4). The notebook receives only
visualization cells (Stage 5).

**CRITICAL — never name a temp script `inspect.py`:** Writing `/tmp/inspect.py` (or any
`inspect.py` anywhere on the Python path) shadows Python's stdlib `inspect` module and
breaks `xarray`, `importlib.metadata`, and most other packages. Name temp scripts
`check_nc.py`, `run_pipeline.py`, `process.py`, etc.

**Sub-skill paths** (relative to the project root):
- Download: `.agents/skills/climate-data-download/SKILL.md`
- Temporal: `.agents/skills/datacube-temporal-aggregator/SKILL.md`
- Process:  `.agents/skills/geospatial-cube-processor/SKILL.md`
- Visualize: `.agents/skills/notebook-plots/SKILL.md`

---

## Stage 1 — Collect parameters (one turn)

Extract from the user's prompt first. Ask only for what is genuinely missing.

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| Country | yes | — | Full name or ISO3, or a bounding box |
| Variable(s) | yes | — | precipitation, solar radiation, temperature… |
| Date range | yes | — | YYYY-MM-DD start and end |
| Output folder | yes | — | **No spaces in path** |
| Admin level | no | 0 | 0 = full country, 1 = province, 2 = district |
| Aggregation | no | auto | "sum" if user says "accumulated/total"; "mean" otherwise |
| Temporal period | no | `"year"` | `"month"`, `"year"`, `"season"` (DJF/MAM/JJA/SON), `"window"` + `windows={"name": ("MM-DD", "MM-DD")}` for a crop or rainy season, `"monthly_climatology"`, `None` = native step. See `aggregate_time` in datacube-temporal-aggregator |
| Plot type | no | auto | auto-detected from variable count + temporal frequency |

**Auto-detect rules (apply silently):**
- "accumulated" / "total" → `agg_method="sum"`; otherwise → `"mean"`
- "monthly", "per month" → `period="month"`; "annual", "per year" → `"year"`; "per season", "DJF/MAM…"
  → `"season"`; named dates ("Jun–Sep", "Nov to Mar", "long rains Mar–May") → `"window"`;
  "average month", "climatology", "typical year" → `"monthly_climatology"`. A named season with no
  dates ("main season", "Meher") — ask for the dates; do not guess them
- Single variable + `period` in (`"month"`, `"monthly_climatology"`) → `plot_type="seasonal_pattern"`
- Multiple variables → `plot_type="dashboard"`
- `admin_level ≥ 1` + multi-year → `plot_type="time_series"`
- `admin_level ≥ 1` + single time step → `plot_type="admin_comparison"`
- No admin subdivision → `plot_type="spatial_map"` (uses NetCDF)

---

## Stage 2 — Show the full plan (one confirmation)

Display this table and wait for "yes" before running any code:

```
Here's what I'll do:

STAGE 3 — DOWNLOAD  (runs in this session via climate-data-download skill)
| Variable         | Source     | Tool/class                |
|------------------|------------|---------------------------|
| {variable}       | {source}   | {aggeodata class}         |

STAGE 4 — PROCESS  (runs in this session)
- Mask to: {Country} (ISO3: {ISO3}, admin level {N})                      (geospatial-cube-processor)
- Temporal: {agg_method} per {period} {windows, if any — e.g. JJAS 06-01 → 09-30}  (datacube-temporal-aggregator)
- Spatial: mean per admin unit                                             (geospatial-cube-processor)
- Incomplete periods at the edges of the date range are dropped (e.g. a DJF missing its December)
- Save: {OUTPUT_FOLDER}/summary_{period}_{ISO3}_{year_range}.csv

STAGE 5 — VISUALIZE
- Notebook:    {OUTPUT_FOLDER}/{country}_{variable}_{year}.ipynb          (notebook-plots skill, Plotly)
- Plotly HTML: {OUTPUT_FOLDER}/{country}_{variable}_{year}_plotly.html    (notebook-plots skill)
- Dashboard:   {OUTPUT_FOLDER}/{country}_{variables}_{year_range}.html    (climate-dashboard skill, Chart.js + KPIs + filters)
- Plot type: {plot_type}

Country: {Country} | Period: {start} → {end} | Output: {OUTPUT_FOLDER}

Shall I proceed?
```

State any defaults you applied so the user can correct them.

---

## Stage 3 — Download (delegate to climate-data-download)

> **Read** `.agents/skills/climate-data-download/SKILL.md`.
>
> Follow its variable → source routing table and download code blocks to fetch all
> requested variables. Use the parameters collected in Stage 1 (country/bbox, dates,
> output folder). Skip the sub-skill's own parameter-collection and confirmation steps —
> those were completed in Stages 1–2 of this pipeline.
>
> After each variable downloads successfully, report the saved path(s) before
> continuing. If a variable fails, diagnose using the sub-skill's troubleshooting
> notes (rate limits, CDS key, spaces in path), then proceed with the remaining
> variables.

---

## Stage 4 — Process (delegate to geospatial-cube-processor + datacube-temporal-aggregator)

> **Read** `.agents/skills/geospatial-cube-processor/SKILL.md` and
> `.agents/skills/datacube-temporal-aggregator/SKILL.md`.
>
> Execute via Bash Python (do not write the functions to the user's file — run them in-session
> to produce a CSV), in this order, with the parameters from Stage 1:
> 1. `mask_to_admin` (geospatial-cube-processor) — ISO3 country code and admin level
> 2. `aggregate_time` (datacube-temporal-aggregator) — `period`, `agg_method`, `windows`; skip when
>    `period` is `None`
> 3. `summarize_by_admin` (geospatial-cube-processor) — spatial mean per admin unit
> - Save the result CSV to `{OUTPUT_FOLDER}/summary_{period}_{ISO3}_{year_range}.csv`
>
> After saving: report the CSV path, print the first few rows, and name any periods dropped
> as incomplete.

---

## Stage 5 — Visualize (notebook + climate dashboard)

Run both sub-skills in sequence using the CSV from Stage 4.

### 5a — Jupyter notebook (delegate to notebook-plots)

> **Read** `.agents/skills/notebook-plots/SKILL.md`.
>
> Before writing the notebook, ensure `nbformat` and `plotly` are installed:
> ```python
> import subprocess, sys
> subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "nbformat", "plotly"])
> ```
>
> Follow its instructions to:
> 1. Write a three-cell notebook at `{OUTPUT_FOLDER}/{country}_{variable}_{year}.ipynb`
> 2. Export a Plotly HTML file at `{OUTPUT_FOLDER}/{country}_{variable}_{year}_plotly.html`
>    (Step 4 of the sub-skill — runs the plot in-session and calls `fig.write_html()`)

### 5b — Climate dashboard (delegate to climate-dashboard)

> **Read** `.agents/skills/climate-dashboard/SKILL.md`.
>
> Follow its instructions to build a Chart.js HTML dashboard at
> `{OUTPUT_FOLDER}/{country}_{variables}_{year_range}.html`.
> This dashboard includes KPI cards, interactive charts with filters, and a data table.
> Skip Step 1 of the sub-skill (parameters already collected in Stage 1).
> Use the CSV from Stage 4 and `OUTPUT_FOLDER` from Stage 1.

---

## Stage 6 — Summary

After the notebook is written:

```
Pipeline complete:

| Stage     | Action                                              | Status  |
|-----------|-----------------------------------------------------|---------|
| Download  | {variable} → {source} → {nc_path}                  | ✓ done  |
| Process   | mask {ISO3} + {agg} {freq} → {csv_path}             | ✓ done  |
| Notebook    | {notebook_path} — 3 cells ({plot_type})             | ✓ done  |
| Plotly HTML | {plotly_html_path} — Plotly chart                   | ✓ done  |
| Dashboard   | {dashboard_path} — Chart.js + KPIs + filters        | ✓ done  |

Open `{notebook_path}` and run all cells, or open either HTML file directly in any browser.
The dashboard (`{dashboard_path}`) includes KPI cards, interactive filters, and a data table.
```

---

## Error handling

- **Path with spaces**: warn before Stage 3, suggest alternative
- **Missing CDS key**: surface from climate-data-download skill notes; skip AgERA5 variables and continue with others
- **GADM fetch fails**: fall back to bounding-box clip using the country's known approximate extent
- **Empty CSV after masking**: warn the user — the extent may not overlap the country boundary


---

*Evaluation examples: [references/evals.json](references/evals.json)*
