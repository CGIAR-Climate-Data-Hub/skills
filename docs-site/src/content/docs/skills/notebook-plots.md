---
title: Notebook Plots
description: Writes interactive Plotly charts into a Jupyter notebook and exports a standalone HTML file.
sidebar:
  order: 4
---

**Type:** Visualization  
**Skill file:** `skills/notebook-plots/skill.md`  
**Raw URL:** `https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/notebook-plots/skill.md`

---

Writes exactly **three cells** per visualization into an existing Jupyter notebook:

1. Markdown header (title, source, data path)
2. Imports + load CSV
3. Plot function + call

Never puts download or processing code in the notebook. The notebook loads a pre-existing CSV
or NetCDF and renders a chart.

## Plot types (auto-detected)

| Data shape | Plot type |
|-----------|-----------|
| Monthly frequency data | `seasonal_pattern` — bar chart by month |
| `admin_unit` column + multi-year | `time_series` — one line per region |
| `admin_unit` column + single time step | `admin_comparison` — sorted bar chart |
| No `admin_unit`, no time variation | `spatial_map` — raster heatmap from NetCDF |
| Multiple variables | `dashboard` — one panel per variable |

## Colorscale reference

| Variable (CF name) | Colorscale | Units |
|--------------------|-----------|-------|
| `rsds` (solar radiation) | `YlOrRd` | MJ/m²/month |
| `pr` (precipitation) | `Blues` | mm |
| `tasmax` / `tasmin` | `RdYlBu_r` | °C |
| `hurs` (relative humidity) | `BuGn` | % |
| `sfcWind` (wind speed) | `PuBu` | m/s |
| `etr` (reference ET) | `YlGn` | mm/day |

## Example

```
Plot monthly solar radiation per department for Bolivia
from D:/tmp/bolivia_climate/summary_ME_BOL_2020_2022.csv
```

The skill adds a Plotly line chart to the active notebook and exports:
- `bolivia_rsds_2020_2022.ipynb` — run all cells in Jupyter or VS Code
- `bolivia_rsds_2020_2022.html` — open in any browser

## Trigger phrases

"plot", "chart", "visualize", "show results in a notebook", "time series", "seasonal pattern",
"compare regions", "draw a map", "show me the [variable]"
