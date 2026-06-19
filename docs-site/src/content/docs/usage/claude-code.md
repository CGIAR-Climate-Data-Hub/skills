---
title: Claude Code
description: Set up Claude Code with the aggeodata MCP server for climate data workflows.
sidebar:
  order: 1
---

**Audience:** Developers with a Claude Pro / Max / Team subscription and Python installed.

Claude Code connects directly to the `aggeodata` MCP server, reads the skills automatically
from the `.agents/skills/` folder, and executes all code locally in your terminal.

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

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `aggeodata` not listed in `/mcp` | Launch `claude` from the project root |
| `ModuleNotFoundError: aggeodata` | Re-run the pip install in Step 2 |
| Download fails with 422 error | Update `aggeodata` to the latest version |
