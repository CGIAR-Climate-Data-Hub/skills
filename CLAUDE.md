# Climate Data Hub Skills — Claude Code Project Instructions

## Custom skills

This project contains domain-specific skill files in `.agents/skills/`. Before responding to any climate
or geospatial data request, read the relevant skill file and follow its instructions exactly.
Do NOT inspect the aggeodata package with `inspect` or `dir` — all required API patterns are
in the skill files.

### Skill routing

| User intent | Skill file to read |
|-------------|-------------------|
| Download **and** visualize / "show me" / "I want to see" / "full pipeline" | `.agents/skills/gcf-pipeline/SKILL.md` |
| Download climate data only (no visualization requested) | `.agents/skills/climate-data-download/SKILL.md` |
| Download soil data (SoilGrids) / build soil cube | `.agents/skills/soil-data-download/SKILL.md` |
| Process / clip / aggregate already-downloaded data | `.agents/skills/geospatial-cube-processor/SKILL.md` |
| Plot / chart / notebook from existing data | `.agents/skills/notebook-plots/SKILL.md` |
| Spatial crop modeling / run crop model over a region | `.agents/skills/spatial-crop-modeler/SKILL.md` |
| Create / generate CDH metadata YAML for a dataset | `.agents/skills/cdh-metadata/SKILL.md` |

### gcf-pipeline trigger phrases (read `.agents/skills/gcf-pipeline/SKILL.md` when any of these appear)

- "download and visualize", "get and show", "download and plot"
- "show me [variable] for [country/year]"
- "I want to see [variable]"
- "map [variable] over [country]"
- "accumulated [variable] in [country]"
- "full pipeline"
- "per department / per region / per province / per district" combined with a variable name
- any prompt that clearly implies **all three steps**: fetch data + spatial aggregation + plot

### climate-data-download trigger phrases (read `.agents/skills/climate-data-download/SKILL.md` when any of these appear)

- "download data for", "get data for", "fetch data for"
- "download [variable] for [country/year]"
- "get [variable] data for [region]"
- "fetch climate data", "retrieve weather data"
- "I need [variable] data for"
- any prompt that implies **fetching/downloading only** with no visualization or modeling requested
- **Not** soil — for soil variables route to `soil-data-download` instead

### soil-data-download trigger phrases (read `.agents/skills/soil-data-download/SKILL.md` when any of these appear)

- "SoilGrids", "soil grids", "soil data for [country]"
- "download soil", "get soil [variable] for"
- "clay/sand/silt for [region]"
- "soil organic carbon", "soil pH", "soil texture"
- "soil cube", "build a soil datacube"
- "soil water content", "wv0010 / wv0033 / wv1500"
- any prompt mentioning the depths `0-5`, `5-15`, `15-30`, `30-60`, `60-100` (cm)
- the schema error `reference_variable: non-null string required` while attempting soil downloads

### spatial-crop-modeler trigger phrases (read `.agents/skills/spatial-crop-modeler/SKILL.md` when any of these appear)

- "yield prediction for", "predict yield for", "crop yield for"
- "run crop model for", "simulate crop for"
- "spatial crop modeling", "crop simulation over"
- "model [crop] in [country/region]"
- "estimate production for", "forecast harvest for"
- any prompt that implies **running a crop model spatially** over a region or country

### cdh-metadata trigger phrases (read `.agents/skills/cdh-metadata/SKILL.md` when any of these appear)

- "create metadata for", "generate metadata for", "write CDH metadata", "generate YAML metadata"
- "document this dataset", "document my raster", "document my NetCDF"
- "add my data to the Climate Data Hub", "prepare dataset for CDH", "catalog this dataset"
- "fill in the metadata fields", "help me describe my dataset"
- "create a YAML for CDH", "write a metadata record"
- any prompt that combines a geospatial file path with a documentation or cataloging intent

### How to invoke a skill

1. Read the skill file (`.agents/skills/<skill-name>/SKILL.md`) with the Read tool.
2. Follow its stages exactly — collect parameters, show the plan, wait for confirmation, then execute.
3. When a skill instructs you to read a sub-skill file, read it before continuing that stage.

## MCP server

The `aggeodata` MCP server is registered in `.mcp.json` (project root). The MCP tools are a
**fallback only** — the skills above specify which aggeodata classes and methods to call via
Python (Bash), not via MCP tools directly. Use MCP tools only when a skill explicitly calls for them.
