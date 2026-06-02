---
title: Claude Code
description: Run the full GCF pipeline from your terminal with direct MCP server integration.
sidebar:
  order: 1
---

**Audience:** Developers with a Claude Pro / Max / Team subscription and Python installed.

Claude Code is the recommended way to run the full pipeline. It connects directly to the
`aggeodata` MCP server, reads the skills automatically from the `skills/` folder, and
executes all code locally in your terminal.

## Prerequisites

| Requirement | How to get it |
|-------------|---------------|
| Claude Pro / Max / Team plan | [claude.ai/upgrade](https://claude.ai/upgrade) |
| Claude Code CLI | `npm install -g @anthropic/claude-code` |
| Python 3.10+ | [python.org](https://www.python.org/downloads/) |
| `aggeodata` package | See Step 2 below |

## Step 1 — Open a terminal in the skills directory

```bash
cd path/to/skills
```

This folder contains `.mcp.json`. Claude Code reads it automatically on startup.

## Step 2 — Install the aggeodata package

```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git" s3fs zarr
```

> One-time setup. Run again only after package updates.

## Step 3 — Launch Claude Code

```bash
claude
```

At startup you should see `✓ aggeodata MCP server connected`. If not, run `/mcp` inside
Claude Code — it should list `aggeodata`. Verify `.mcp.json` exists in the current directory.

## Step 4 — Type your request

```
Download and visualize monthly accumulated solar radiation and wind speed
from NASA POWER for Bolivia from 2020 to 2022, per department (admin level 1).
Output to D:/tmp/bolivia_climate
```

Claude will show a plan, wait for confirmation, then deliver a Jupyter notebook and
HTML dashboard.

## More example prompts

```
Show me accumulated precipitation for Kenya for the 2021 long rains
(March–May) at district level. Save to D:/tmp/kenya_2021
```

```
Annual mean temperature and reference ET for Ethiopia per region, 2018–2022.
Output to D:/tmp/ethiopia_climate
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `aggeodata` not listed in `/mcp` | Launch `claude` from inside the `skills/` folder |
| `ModuleNotFoundError: aggeodata` | Re-run the pip install in Step 2 |
| Download fails with 422 error | Update `aggeodata` to the latest version |
