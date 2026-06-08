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

## Step 0 — One-time system prompt (administrator)

Paste this block as the **system prompt** in Antigravity. Regular users never touch this.

```
When the user gives you a climate data task, use the CDH climate pipeline skills from GitHub.

Before planning or executing anything, use read_url_content to fetch ALL five skill files now:

1. https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/gcf-pipeline/skill.md
2. https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/climate-data-download/SKILL.md
3. https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/geospatial-cube-processor/SKILL.md
4. https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/notebook-plots/SKILL.md
5. https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/climate-dashboard/SKILL.md

Fetch all five BEFORE reading any of them. Treat gcf-pipeline as the controlling workflow.

Do NOT re-fetch sub-skill files mid-task — they are already loaded.
Do NOT run environment or folder existence checks before starting.
Do NOT inspect the aggeodata package with inspect() or dir() — all API patterns are in the skill files.
Execute all generated code using run_command.
```

:::tip[Why pre-fetch all five?]
Fetching sub-skills on demand mid-task adds one round-trip each time, compounding context growth.
Pre-fetching upfront costs one small burst and eliminates all mid-task pauses.
:::

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `read_url_content` returns an error | Verify Antigravity has web access enabled |
| `ModuleNotFoundError: aggeodata` | Run the pip install command above |
| Agent invents code | Confirm the system prompt was saved correctly |
