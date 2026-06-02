---
title: Climate Dashboard
description: Builds a self-contained interactive HTML dashboard — no server, no Jupyter needed.
sidebar:
  order: 5
---

**Type:** Visualization  
**Skill file:** `skills/climate-dashboard/skill.md`  
**Raw URL:** `https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/climate-dashboard/skill.md`

---

Builds a fully self-contained interactive HTML dashboard from a climate CSV or NetCDF.
No Jupyter, no Python runtime, no server — just one `.html` file that opens in any browser.

## What's included

- **KPI cards** — headline stats (mean, max, min) per variable
- **Interactive charts** — Chart.js time series or bar charts
- **Region / year filters** — dropdowns that update all charts at once
- **Sortable data table** — full CSV contents with search
- **Self-contained** — all JavaScript inline; no CDN dependency at open time

## Auto-detected chart type

| Data shape | Chart produced |
|------------|---------------|
| Monthly data, no admin unit | Seasonal bar chart (Jan–Dec pattern) |
| Multi-year + admin units | Time-series line chart per region |
| Single time step + admin units | Horizontal bar comparison |
| Multiple variables | One panel per variable |

## Example

```
Build a climate dashboard from D:/tmp/bolivia_climate/summary_ME_BOL_2020_2022.csv
and save it to D:/tmp/bolivia_climate
```

Output: `bolivia_rsds_sfcWind_2020_2022.html`

Double-click the file — it opens instantly in Chrome, Firefox, or Edge with all
charts and filters pre-loaded.

## Trigger phrases

"dashboard", "HTML file", "open in browser", "interactive chart", "visualize the CSV",
"no Jupyter", "standalone"
