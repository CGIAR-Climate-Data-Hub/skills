# Using the GCF Pipeline in Antigravity

**Audience:** Users running a local AI agent (Antigravity) who want to use the climate
pipeline without installing Claude Code or touching a terminal. No programming experience
required after the one-time setup.

Antigravity loads the skill files directly from GitHub at runtime using its
`read_url_content` tool. This means you always get the latest version of the pipeline
automatically — no copy-pasting, no local files to manage.

---

## Prerequisites

| Requirement | How to get it |
|-------------|---------------|
| Antigravity installed locally | [antigravity docs](https://antigravity.dev) |
| Python 3.10+ with `aggeodata` | See below |
| Internet access | Required to fetch skill files from GitHub |

**Install aggeodata once** (in your system Python or a virtual environment):

```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git" s3fs zarr
```

---

## Step 0 — One-time system prompt setup (administrator / power user)

Paste the following block as the **system prompt** in Antigravity. Regular users never
see or touch this — it runs silently in the background.

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

> **Why this works:** Every time a user starts a climate task, Antigravity fetches the
> latest skill instructions from GitHub, then follows them step by step. When skills are
> updated, all users get the new version automatically.

---

## Step 1 — User types one sentence

After setup, the user just describes what they want in plain language:

```
Download and visualize monthly accumulated solar radiation and wind speed
from NASA POWER for Bolivia from 2000 to 2010, per department (admin level 1).
Output to D:/tmp/bolivia_climate
```

Antigravity will:
1. Fetch the `gcf-pipeline` skill from GitHub
2. Show the user a plan and ask for confirmation
3. Download data from NASA POWER
4. Clip to Bolivia department boundaries
5. Compute monthly statistics per department
6. Write a Jupyter notebook with interactive charts
7. Write a standalone HTML dashboard

---

## More example prompts users can type

```
Monthly precipitation for Ghana per region, 2020 to 2022.
Save results to D:/tmp/ghana_climate
```

```
Solar radiation and wind speed for Uruguay in 2020.
Output to D:/tmp/uruguay
```

```
Annual temperature and reference ET for Ethiopia per region, 2018 to 2022.
Save to D:/tmp/ethiopia_climate
```

---

## What users get

| File | What it is |
|------|------------|
| `*.nc` | Raw climate rasters |
| `summary_*.csv` | Monthly values per admin unit |
| `*_analysis.ipynb` | Jupyter notebook — open with Jupyter or VS Code |
| `*_dashboard.html` | Standalone dashboard — just double-click to open in a browser |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `read_url_content` returns an error | Check internet connection; verify Antigravity has web access enabled |
| `ModuleNotFoundError: aggeodata` | Run the pip install command above, then restart Antigravity |
| Agent says it can't find the skill | Confirm the system prompt was saved correctly (Step 0) |
