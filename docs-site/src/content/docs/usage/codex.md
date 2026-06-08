---
title: OpenAI Codex
description: Set up OpenAI Codex with the CDH skills system prompt for climate data workflows.
sidebar:
  order: 3
---

**Audience:** Users running OpenAI Codex (or similar agents without a `read_url_content`
tool). No programming experience required after the one-time setup.

Unlike Antigravity, Codex may not automatically follow internal cross-references in skill
files, so all five URLs are provided upfront in the system prompt.

## Prerequisites

| Requirement | How to get it |
|-------------|---------------|
| OpenAI Codex access | [platform.openai.com](https://platform.openai.com) |
| Python 3.10+ with `aggeodata` | See below |
| Internet access | Required to fetch skill files |

```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git" s3fs zarr
```

## Step 0 — One-time system prompt (administrator)

Paste this block as the **system prompt** or **custom instructions** in Codex.

```
When the user gives you a climate data task, use the CDH climate pipeline skills from GitHub.

Before planning or executing anything, fetch and read ALL of these skill files:

1. Main pipeline orchestrator:
   https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/gcf-pipeline/skill.md

2. Data download sub-skill:
   https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/climate-data-download/SKILL.md

3. Geospatial processing sub-skill:
   https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/geospatial-cube-processor/SKILL.md

4. Notebook plotting sub-skill:
   https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/notebook-plots/SKILL.md

5. Dashboard sub-skill:
   https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/skills/main/skills/climate-dashboard/SKILL.md

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

## Antigravity vs Codex

| | Antigravity | Codex |
|--|-------------|-------|
| URL fetch tool | `read_url_content` (built-in) | `curl` / `wget` / web tool |
| URLs in system prompt | 5 (all skills upfront) | 5 (all skills upfront) |
| Sub-skill loading | Pre-fetched at task start | Pre-fetched at task start |

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Codex cannot access URLs | Enable internet access in Codex settings |
| `ModuleNotFoundError: aggeodata` | Run the pip install command above |
| Agent invents code instead of following the skill | Verify the system prompt was saved and the fetch succeeded |
