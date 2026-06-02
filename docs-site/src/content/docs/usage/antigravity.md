---
title: Antigravity
description: Run the GCF pipeline in Antigravity — no terminal, no Claude subscription needed.
sidebar:
  order: 2
---

**Audience:** Any user running a local Antigravity agent. No programming experience required
after the one-time system prompt setup.

Antigravity loads skill files directly from GitHub at runtime using its `read_url_content`
tool — you always get the latest pipeline version automatically.

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
When the user gives you a climate data task for downloading and visualization,
use read_url_content to fetch:

  https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/gcf-pipeline/skill.md

Follow those instructions exactly. When the skill tells you to read a sub-skill file,
fetch it using read_url_content at the corresponding URL:

  climate-data-download:
  https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/climate-data-download/skill.md

  geospatial-cube-processor:
  https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/geospatial-cube-processor/skill.md

  notebook-plots:
  https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/notebook-plots/skill.md

  climate-dashboard:
  https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/climate-dashboard/skill.md

Execute all generated code using run_command.
Do NOT inspect the aggeodata package with inspect() or dir() — all API patterns are in the skill files.
```

## Step 1 — User types one sentence

```
Download and visualize monthly accumulated solar radiation and wind speed
from NASA POWER for Bolivia from 2020 to 2022, per department (admin level 1).
Output to D:/tmp/bolivia_climate
```

Antigravity fetches the skill from GitHub, shows a plan, and delivers the outputs.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `read_url_content` returns an error | Verify Antigravity has web access enabled |
| `ModuleNotFoundError: aggeodata` | Run the pip install command above |
| Agent invents code | Confirm the system prompt was saved correctly |
