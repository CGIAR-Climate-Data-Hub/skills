# spatial-crop-modeler

A managed agent for spatially-explicit process-based crop yield simulation.
Developed by Climate Data Hub — CGIAR.

## Trigger conditions

Load this agent when the user asks about any of:
- Running DSSAT, CAF2021, or any process-based crop model
- Simulating maize, wheat, bean, or soybean yield
- Downloading CHIRPS, CHIRTS, AgERA5, or SoilGrids data
- Building weather or soil datacubes for crop modeling
- Interpreting HWAM output, pixels_ok/skipped/failed summaries
- Spatial yield maps, planting date analysis, multi-year crop simulations

## Skill

Read and follow: SKILL.md

## Tools required

- `bash` — run ag-cube-cm CLI commands, validate configs
- `file_write` — save YAML config files to the user's output directory

## Agent behavior

1. Ask one clarifying question if mode (with_cubes vs full_pipeline) is not clear
2. Show a plan table and wait for user confirmation before writing any files
3. Generate a Pydantic-validated YAML config (ag-cube-cm schema)
4. Show validate → run commands
5. After simulation, report pixel summary and mean HWAM
6. Offer a matplotlib yield map

## Science bundle registration

This agent is eligible for the Antigravity Science Skills bundle.
Category: Agricultural Science / Crop Modeling
Data sources: CHIRPS, CHIRTS, AgERA5, SoilGrids, NASA POWER
Models: DSSAT (Maize, Wheat, Bean)
Output: spatially-explicit yield maps (NetCDF, kg/ha)

## Dependencies

User must have installed on their machine:
- Python >= 3.10
- ag-cube-cm: `pip install "ag-cube-cm[models] @ git+https://github.com/anaguilarar/ag-cube-cm.git"`
- aggeodata: `pip install "aggeodata[download,mcp] @ git+https://github.com/anaguilarar/aggeodata.git"`
- DSSAT (optional, auto-detected if on PATH)

## Repository

https://github.com/anaguilarar/spatial-crop-modeler-skill

## License

MIT — Climate Data Hub, CGIAR
