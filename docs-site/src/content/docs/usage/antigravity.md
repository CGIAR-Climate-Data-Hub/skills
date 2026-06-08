---
title: Antigravity
description: Set up Antigravity with the CDH skills system prompt for climate data workflows.
sidebar:
  order: 2
---

**Audience:** Any user running a local Antigravity agent. No programming experience required
after the one-time system prompt setup.

Antigravity loads skill files directly from GitHub at runtime using its `read_url_content`
tool — you always get the latest skill version automatically.

## Prerequisites

| Requirement | How to get it |
|-------------|---------------|
| Antigravity installed | [antigravity.dev](https://antigravity.dev) |
| Python 3.10+ with `aggeodata` | See below |
| Internet access | Required to fetch skill files |

```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git" s3fs zarr
```

## Step 0 — System prompt

Each skill page includes the system prompt to paste into Antigravity. Find it in the **Antigravity** tab of the skill you want to use — for example, [GCF Pipeline → Antigravity](../skills/gcf-pipeline/).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `read_url_content` returns an error | Verify Antigravity has web access enabled |
| `ModuleNotFoundError: aggeodata` | Run the pip install command above |
| Agent invents code | Confirm the system prompt was saved correctly |
