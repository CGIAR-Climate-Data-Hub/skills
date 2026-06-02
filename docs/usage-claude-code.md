# Using the GCF Pipeline in Claude Code

**Audience:** Developers with a Claude Pro/Max/Team subscription and Python installed.

Claude Code is the recommended way to run the full pipeline. It connects directly to the
`aggeodata` MCP server, reads the skills automatically from the `skills/` folder, and
executes all code locally in your terminal.

---

## Prerequisites

| Requirement | How to get it |
|-------------|---------------|
| Claude Pro / Max / Team plan | [claude.ai/upgrade](https://claude.ai/upgrade) |
| Claude Code CLI | `npm install -g @anthropic/claude-code` |
| Python 3.10+ | [python.org](https://www.python.org/downloads/) |
| `aggeodata` package | See Step 2 below |

---

## Step 1 — Open a terminal and go to the skills directory

```bash
cd "cdh_skills"
```

This folder contains `.claude/mcp_config.json`. Claude Code reads it automatically on
startup — no extra configuration needed.

---

## Step 2 — Install the aggeodata package

```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git" s3fs zarr
```

> **One-time setup.** You only need to run this once (or after package updates).

---

## Step 3 — Launch Claude Code

```bash
claude
```

At startup you should see:

```
✓ aggeodata MCP server connected
```

If the server does not appear, run `/mcp` inside Claude Code — it should list `aggeodata`.
If it is missing, verify that `.claude/mcp_config.json` exists in the current directory.

---

## Step 4 — Type your request in plain language

```
Download and visualize monthly accumulated solar radiation and wind speed
from NASA POWER for Bolivia from 2000 to 2010, per department (admin level 1).
Output to D:/tmp/bolivia_climate
```

Claude will:
1. Read the `gcf-pipeline` skill and show you a plan
2. Ask for one confirmation before downloading
3. Download the data (NASA POWER via S3)
4. Clip to Bolivia department boundaries
5. Compute monthly statistics per department
6. Write a Jupyter notebook with an interactive Plotly chart
7. Write a standalone HTML dashboard (open in any browser — no server needed)

---

## More example prompts

```
Show me accumulated precipitation for Kenya for the 2021 long rains
(March–May) at district level. Save to D:/tmp/kenya_2021
```

```
Annual mean temperature and reference ET for Ethiopia per region, 2018–2022.
Output to D:/tmp/ethiopia_climate
```

```
Monthly precipitation for bounding box lon -87.5 to -86.5 lat 13.5 to 14.5,
years 2019–2021. Save to D:/tmp/hnd
```

---

## What you get

| Output file | Description |
|-------------|-------------|
| `*.nc` | Raw climate rasters (one per variable) |
| `summary_*.csv` | Monthly statistics per admin unit |
| `*_analysis.ipynb` | Jupyter notebook with Plotly time-series charts |
| `*_dashboard.html` | Standalone HTML dashboard with KPI cards and filters |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `aggeodata MCP server` not listed in `/mcp` | Confirm you launched `claude` from inside the `cdh_skills/` folder |
| `ModuleNotFoundError: aggeodata` | Re-run the pip install in Step 2 |
| Download fails with 422 error | NASA POWER rejects bounding boxes exactly 10° wide — the package handles this automatically; update to the latest `aggeodata` version |
| Merge error with different grid sizes | Update `aggeodata` — the S3/REST grid alignment fix is included in the latest version |
