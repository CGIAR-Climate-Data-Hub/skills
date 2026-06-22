# CGIAR Climate Data Hub — Agent Instructions

These rules apply automatically to all tasks executed in this workspace.

## 0. Environment Setup

Before fetching skill files or executing any task, run this once per session and wait for it to finish:

```bash
pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git" s3fs zarr
```

This installs `aggeodata` into the sandbox so MCP tools and Python fallback both work.

## 1. Skill Discovery & Execution

All skills are under `.agents/skills/`. Before responding to any climate or geospatial data request,
read the relevant skill file and follow its instructions exactly.

Do NOT run exploratory introspection (`dir()`, `help()`, `inspect`) on `aggeodata` or `ag_cube_cm`.
All required API patterns are in the skill files.

### Skill routing

| User intent | Skill file |
|-------------|-----------|
| Download **and** visualize / "show me" / "full pipeline" | `.agents/skills/gcf-pipeline/SKILL.md` |
| Download climate data only (no visualization) | `.agents/skills/climate-data-download/SKILL.md` |
| Download soil data (SoilGrids) / build soil cube | `.agents/skills/soil-data-download/SKILL.md` |
| Process / clip / aggregate already-downloaded data | `.agents/skills/geospatial-cube-processor/SKILL.md` |
| Plot / chart / notebook from existing data | `.agents/skills/notebook-plots/SKILL.md` |
| Spatial crop modeling / run crop model over a region | `.agents/skills/spatial-crop-modeler/SKILL.md` |
| Build interactive climate dashboard | `.agents/skills/climate-dashboard/SKILL.md` |

### Trigger phrases

**gcf-pipeline**: "download and visualize", "show me [variable] for [country]", "map [variable] over [country]",
"accumulated [variable] in [country]", "full pipeline", "per department/region/province + variable name",
any prompt implying all three steps: fetch + aggregate + plot.

**climate-data-download**: "download data for", "get data for", "fetch climate data", "I need [variable] data for",
any prompt implying fetching climate-only with no visualization or modeling. **Not** soil — route soil to
`soil-data-download`.

**soil-data-download**: "SoilGrids", "download soil [variable] for", "clay/sand/silt for", "soil organic carbon",
"soil pH", "soil texture", "soil cube", any prompt referencing the soil depth layers (`0-5`, `5-15`, `15-30`,
`30-60`, `60-100`), or the schema error `reference_variable: non-null string required` while attempting soil downloads.

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

## 3. Troubleshooting & Friction Resolution

- **MCP Fallback**: If the MCP tools are not registered in your active schema (e.g. tools like `aggeodata/download_chirps` return a parser error), fall back to writing and executing a Python script using the classes and methods documented in [.agents/skills/climate-data-download/references/python_api.md](file:///D:/OneDrive%20-%20CGIAR/scripts/skills/.agents/skills/climate-data-download/references/python_api.md).
- **Dashboard Template**: To avoid token limits and truncation issues when generating the HTML dashboard, load the raw template from [.agents/skills/climate-dashboard/assets/template.html](file:///D:/OneDrive%20-%20CGIAR/scripts/skills/.agents/skills/climate-dashboard/assets/template.html) and use python code to inject the data into placeholders (`/* DATA_PLACEHOLDER */`, `{{title}}`, etc.).
- **Swapped Dimensions**: AgERA5 NetCDFs downloaded via the Copernicus API may swap the latitude/longitude variables. Proactively check dataset dimensions before spatial clipping or zonal stats, and rename if necessary: `ds = ds.rename({'longitude': 'lon', 'latitude': 'lat'})`.

