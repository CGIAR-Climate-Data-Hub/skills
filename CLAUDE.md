# GeoAgri Skills — Claude Code Project Instructions

## Custom skills

This project contains domain-specific skill files in `skills/`. Before responding to any climate
or geospatial data request, read the relevant skill file and follow its instructions exactly.
Do NOT inspect the aggeodata package with `inspect` or `dir` — all required API patterns are
in the skill files.

### Skill routing

| User intent | Skill file to read |
|-------------|-------------------|
| Download **and** visualize / "show me" / "I want to see" / "full pipeline" | `skills/gcf-pipeline/SKILL.md` |
| Download only (no visualization requested) | `skills/climate-data-download/SKILL.md` |
| Process / clip / aggregate already-downloaded data | `skills/geospatial-cube-processor/SKILL.md` |
| Plot / chart / notebook from existing data | `skills/notebook-plots/SKILL.md` |

### gcf-pipeline trigger phrases (read `skills/gcf-pipeline/SKILL.md` when any of these appear)

- "download and visualize", "get and show", "download and plot"
- "show me [variable] for [country/year]"
- "I want to see [variable]"
- "map [variable] over [country]"
- "accumulated [variable] in [country]"
- "full pipeline"
- "per department / per region / per province / per district" combined with a variable name
- any prompt that clearly implies **all three steps**: fetch data + spatial aggregation + plot

### How to invoke a skill

1. Read the skill file (`skills/<skill-name>/SKILL.md`) with the Read tool.
2. Follow its stages exactly — collect parameters, show the plan, wait for confirmation, then execute.
3. When a skill instructs you to read a sub-skill file, read it before continuing that stage.

## MCP server

The `aggeodata` MCP server is registered in `.mcp.json` (project root). The MCP tools are a
**fallback only** — the skills above specify which aggeodata classes and methods to call via
Python (Bash), not via MCP tools directly. Use MCP tools only when a skill explicitly calls for them.
