# Using the GCF Pipeline in OpenAI Codex

**Audience:** Users running OpenAI Codex (or similar agents without a dedicated
`read_url_content` tool) who want to use the climate pipeline. No programming experience
required after the one-time setup.

The setup is slightly different from Antigravity: instead of fetching one URL, you give
Codex the URLs for all skill files upfront in the system prompt. Codex fetches them using
whatever network tool is available in its environment (`curl`, `wget`,
`Invoke-WebRequest`, a browser fetch, or any web-access tool).

---

## Prerequisites

| Requirement | How to get it |
|-------------|---------------|
| OpenAI Codex access | [platform.openai.com](https://platform.openai.com) |
| Python 3.10+ with `aggeodata` | See below |
| Internet access | Required to fetch skill files from GitHub |

**Install aggeodata once** (in your system Python or a virtual environment):

```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git" s3fs zarr
```

---

## Step 0 — One-time system prompt setup (administrator / power user)

Paste the following block as the **system prompt** or **custom instructions** in Codex.
Regular users never see or touch this.

```
When the user gives you a climate data task, use the CDH climate pipeline skills from GitHub.

Before planning or executing anything, fetch and read ALL of these skill files:

1. Main pipeline orchestrator:
   https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/.agents/skills/gcf-pipeline/SKILL.md

2. Data download sub-skill:
   https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/.agents/skills/climate-data-download/SKILL.md

3. Geospatial processing sub-skill:
   https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/.agents/skills/geospatial-cube-processor/SKILL.md

4. Notebook plotting sub-skill:
   https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/.agents/skills/notebook-plots/SKILL.md

5. Dashboard sub-skill:
   https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/.agents/skills/climate-dashboard/SKILL.md

Treat the gcf-pipeline file as the controlling workflow. Treat the other four as delegated
sub-skills referenced by that workflow.

To fetch these files: if your environment has a URL-reading tool, use it. Otherwise use curl,
wget, Invoke-WebRequest, or any equivalent shell command. If network access is blocked, tell
the user exactly which URLs could not be read and ask for approval.

Execute all generated code using run_command, or the closest equivalent shell/code-execution
tool available in your environment.

Do NOT invent the skill contents from memory. Fetch the current files from the URLs above
at the start of each new climate task, unless they were already fetched in the same session.

Do NOT inspect the aggeodata package with inspect() or dir() — all API patterns are in the
skill files.
```

> **Why fetch all files upfront?** Unlike Antigravity's `read_url_content`, Codex may not
> automatically follow internal cross-references in the skill files. Giving all five URLs
> at once ensures nothing is missed. The skill files are small (a few KB each), so fetching
> all of them adds only a few seconds.

---

## Step 1 — User types one sentence

After setup, the user just describes what they want in plain language:

```
Download and visualize monthly accumulated solar radiation and wind speed
from NASA POWER for Bolivia from 2020 to 2022, per department (admin level 1).
Output to D:/tmp/bolivia_climate
```

> **Tip — keep the date range short for testing.** NASA POWER downloads ~1–2 seconds/year,
> but the spatial aggregation loop (one clip per department × months × years) dominates
> runtime. 2–3 years is fast (~1–2 min total). 10+ years can take 15–30 min and
> significantly more tokens. Start short; extend once the pipeline is verified.

Codex will:
1. Fetch all five skill files from GitHub
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

## Comparison: Antigravity vs Codex setup

| | Antigravity | Codex |
|--|-------------|-------|
| URL fetch tool | `read_url_content` (built-in) | `curl` / `wget` / web tool |
| URLs in system prompt | 5 (all skills upfront) | 5 (all skills upfront) |
| Sub-skill loading | Pre-fetched at task start | Pre-fetched at task start |
| Execution tool | `run_command` | `run_command` or equivalent |
| Offline fallback | Ask user | Ask user |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Codex says it cannot access URLs | Enable internet access in Codex settings, or manually paste the skill file contents |
| `ModuleNotFoundError: aggeodata` | Run the pip install command above, then restart Codex |
| Agent invents code instead of following the skill | Verify the system prompt was saved (Step 0) and the fetch succeeded |
| Output notebook is empty | Confirm `run_command` executed the code — look for error messages in Codex's tool output |
