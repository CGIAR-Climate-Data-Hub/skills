# Running DSSAT for Maize in Honduras (without skill)

## Config File

```yaml
GENERAL_INFO:
  country: 'Honduras'
  country_code: 'HND'
  model: 'dssat'
  working_path: 'D:/dssat_runs/hnd_2021'
  dssat_path: null
  ncores: 4

SPATIAL_INFO:
  feature_name: 'shapeName'
  adm_level: 2
  feature: null
  soil_path: 'D:/cubes/soil_hnd.nc'
  weather_path: 'D:/cubes/climate_hnd_2021.nc'
  output_path: 'D:/results/yield_hnd.nc'
  dem_path: null

CROP:
  name: 'Maize'
  cultivar: 'IB1072'

MANAGEMENT:
  planting_date: '2021-05-15'
  n_planting_windows: 1
  planting_window_days: 7
```

**Important:** `working_path` must have no spaces -- DSSAT is a Fortran program.

## Running the Simulation

```python
import json
from ag_cube_cm.mcp_server import run_simulation

CONFIG_PATH = "path/to/config.yaml"

result = json.loads(run_simulation(config_path=CONFIG_PATH))

if result["status"] != "ok":
    print("ERROR:", result["message"])
else:
    print(f"Status      : {result['status']}")
    print(f"Output      : {result['output_path']}")
    print(f"Pixels OK   : {result['pixels_ok']}")
    print(f"Pixels skip : {result['pixels_skipped']}")
    print(f"Pixels fail : {result['pixels_failed']}")
    print(f"Mean HWAM   : {result['mean_hwam_kg_ha']} kg/ha")
```

Or use generate_config + run_simulation via MCP server.

## Notes

- `working_path` (`D:/dssat_runs/hnd_2021`) must have no spaces
- Output NetCDF has dimensions `(planting_window, year, y, x)` with `HWAM` variable
- Cultivar IB1072 is a standard tropical maize cultivar in DSSAT's bundled database
