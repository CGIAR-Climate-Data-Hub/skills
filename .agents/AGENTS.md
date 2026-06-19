# CGIAR Climate Data Hub — Agent Instructions

These rules apply automatically to all tasks executed in this workspace.

## 1. Skill Discovery & Execution

All skills are under `.agents/skills/`. Before responding to any climate or geospatial data request,
read the relevant skill file and follow its instructions exactly.

Do NOT run exploratory introspection (`dir()`, `help()`, `inspect`) on `aggeodata` or `ag_cube_cm`.
All required API patterns are in the skill files.

### Skill routing

| User intent | Skill file |
|-------------|-----------|
| Download **and** visualize / "show me" / "full pipeline" | `.agents/skills/gcf-pipeline/SKILL.md` |
| Download only (no visualization) | `.agents/skills/climate-data-download/SKILL.md` |
| Process / clip / aggregate already-downloaded data | `.agents/skills/geospatial-cube-processor/SKILL.md` |
| Plot / chart / notebook from existing data | `.agents/skills/notebook-plots/SKILL.md` |
| Spatial crop modeling / run crop model over a region | `.agents/skills/spatial-crop-modeler/SKILL.md` |
| Build interactive climate dashboard | `.agents/skills/climate-dashboard/SKILL.md` |

### Trigger phrases

**gcf-pipeline**: "download and visualize", "show me [variable] for [country]", "map [variable] over [country]",
"accumulated [variable] in [country]", "full pipeline", "per department/region/province + variable name",
any prompt implying all three steps: fetch + aggregate + plot.

**climate-data-download**: "download data for", "get data for", "fetch climate data", "I need [variable] data for",
any prompt implying fetching only with no visualization or modeling.

**spatial-crop-modeler**: "yield prediction", "run crop model", "simulate crop", "model [crop] in [country]",
"estimate production", any prompt implying running a crop model spatially.

### How to invoke a skill

1. Read the skill file with the appropriate file-read tool.
2. Follow its stages exactly — collect parameters, show the plan, wait for confirmation, then execute.
3. When a skill instructs you to read a sub-skill file, read it before continuing that stage.
4. Treat `gcf-pipeline` as the primary controlling workflow for multi-step tasks.

## 2. Code Execution & Tool Usage

- **Terminal Execution**: Run generated Python code using `run_command`.
- **File writes**: Use `write_to_file` for writing configuration or output files.
- **MCP tool names**: Prefix with the server name, e.g. `aggeodata/download_chirps`.
- **No redundant checks**: Do not check for directory existence, library installation, or environment
  variables unless a command fails. Assume the environment is configured.
