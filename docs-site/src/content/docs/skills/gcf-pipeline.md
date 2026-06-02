---
title: GCF Pipeline
description: Full download → process → notebook + dashboard workflow in one conversation.
sidebar:
  order: 1
  label: GCF Pipeline
---

**Type:** End-to-end pipeline  
**Skill file:** `skills/gcf-pipeline/skill.md`  
**Raw URL:** `https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/gcf-pipeline/skill.md`

---

The GCF Pipeline is an orchestrator. It collects your parameters, shows a plan, then
delegates each stage to the specialist sub-skills below. You interact with one skill;
three run under the hood.

## What it does

| Stage | Sub-skill | Output |
|-------|-----------|--------|
| **Download** | `climate-data-download` | NetCDF rasters |
| **Process** | `geospatial-cube-processor` | CSV — monthly values per admin unit |
| **Visualize** | `notebook-plots` + `climate-dashboard` | Jupyter notebook + standalone HTML dashboard |

## Trigger phrases

Say any of these and the skill activates automatically in Claude Code:

- "download and visualize", "get and show"
- "show me [variable] for [country/year]"
- "map [variable] over [country]"
- "accumulated [variable] in [country]"
- "full pipeline", "per department / per region / per province"

## Parameters

| Parameter | Required | Default | Notes |
|-----------|----------|---------|-------|
| Country | yes | — | Full name or ISO3 |
| Variable(s) | yes | — | precipitation, solar radiation, temperature… |
| Date range | yes | — | YYYY-MM-DD start and end |
| Output folder | yes | — | No spaces in path |
| Admin level | no | 0 | 0 = country, 1 = province, 2 = district |
| Aggregation | no | auto | "sum" if "accumulated/total"; "mean" otherwise |
| Temporal frequency | no | `"YE"` | `"ME"` monthly, `"YE"` annual |

## Example

```
Download and visualize monthly solar radiation and wind speed
from NASA POWER for Bolivia from 2020 to 2022, per department (admin level 1).
Output to D:/tmp/bolivia_climate
```

The skill shows this plan before running:

```
STAGE 3 — DOWNLOAD  (NASA POWER — ALLSKY_SFC_SW_DWN, WS2M)
STAGE 4 — PROCESS   (mask BOL admin 1 · sum/mean monthly · CSV)
STAGE 5 — VISUALIZE (Jupyter notebook + Plotly HTML + Chart.js dashboard)
```

:::tip[Keep date ranges short for testing]
The spatial aggregation loop (one clip per department × months × years) dominates runtime.
2–3 years is fast (~1–2 min). 10+ years can take 15–30 min and more tokens.
:::

## Outputs

| File | Description |
|------|-------------|
| `*.nc` | Raw climate rasters (one per variable) |
| `summary_ME_BOL_2020_2022.csv` | Monthly statistics per department |
| `bolivia_rsds_sfcWind_2020_2022.ipynb` | Jupyter notebook — open in VS Code or Jupyter |
| `bolivia_rsds_sfcWind_2020_2022.html` | Standalone dashboard — double-click to open |
