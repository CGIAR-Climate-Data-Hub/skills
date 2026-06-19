---
title: Getting started
description: Install aggeodata and run your first climate pipeline in Claude Code.
sidebar:
  order: 1
---

Skills are domain-specific instruction sets loaded into an AI agent. When you describe what you
need, the agent reads the relevant skill and acts as a specialist — calling the right APIs,
writing correct code, and following established workflows. You don't need to know the tool
names or parameters.

## Choose your agent

| Agent | Audience | Setup effort |
|-------|----------|--------------|
| **Claude Code** | Developers with a Claude Pro/Max/Team plan | Low — one terminal command |
| **Antigravity** | Any user, no subscription needed | Low — paste a system prompt |
| **OpenAI Codex** | Any user with a Codex subscription | Low — paste a system prompt |

See the [usage guides](/skills/usage/claude-code/) for step-by-step instructions per platform.

## Install aggeodata

All skills are powered by the `aggeodata` Python package. Install it once:

```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git" s3fs zarr
```

> **AgERA5 only:** If you need hourly relative humidity, vapour pressure, or reference ET,
> also register for a free CDS API key at [cds.climate.copernicus.eu](https://cds.climate.copernicus.eu/)
> and create `~/.cdsapirc` with your credentials.

## Run your first pipeline

Open Claude Code in the project root directory and type:

```
Download and visualize monthly solar radiation and wind speed
from NASA POWER for Bolivia from 2020 to 2022, per department.
Output to D:/tmp/bolivia_climate
```

Claude will show you a plan, ask for confirmation, then deliver:

| File | Description |
|------|-------------|
| `*.nc` | Raw climate rasters |
| `summary_*.csv` | Monthly statistics per admin unit |
| `*_analysis.ipynb` | Jupyter notebook with Plotly charts |
| `*_dashboard.html` | Standalone HTML dashboard |

## How skills are loaded

In **Claude Code**, skills live in `.agents/skills/` and are loaded automatically via `CLAUDE.md`.

In **Antigravity and Codex**, skills are fetched from GitHub at runtime. The system prompt
tells the agent which URLs to read — see the [usage guides](/skills/usage/antigravity/) for the
exact prompts to paste.
