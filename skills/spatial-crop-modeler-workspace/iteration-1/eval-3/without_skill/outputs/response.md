# DSSAT Output: Why Are So Many Pixels Skipped? (without skill)

## What "pixels_skipped" actually means

A pixel gets skipped when, before DSSAT even starts, the code checks whether the weather
or soil data slice for that location is entirely NaN/empty. If either input is empty,
the pixel is flagged as "no-data" and DSSAT is never called.

So **skipped pixels are not simulation failures** -- they are grid cells where valid
input data simply does not exist.

## Common reasons 45 pixels were skipped

**1. Ocean / water bodies / outside country boundary**
The bounding box almost certainly includes grid cells over water or outside the land mask.
These cells have NaN values by design.

**2. Spatial mismatch between weather and soil grids**
Weather data (AgERA5/CHIRPS) and soil data (SoilGrids) may be at different resolutions.
Pixels at the edges may have valid weather but missing soil, or vice versa.

**3. Administrative boundary clipping**
If a `feature` polygon was specified, cells inside the bbox but outside the polygon get masked.

## Is your result reliable?

**Yes, with a caveat.**

- `pixels_failed = 0` -- every pixel that had data also produced output. Strong positive signal.
- `mean_hwam = 6,200 kg/ha` is computed only from the 12 successful pixels.
- Ask: are those 12 pixels representative of your study area's cropland?

If the 45 skipped cells are mostly ocean/lakes/forest (non-agricultural), 12 valid
cropland pixels is perfectly reasonable. If they cover areas that should be farmland,
the mean could be biased.

## How to verify

```python
import xarray as xr
import matplotlib.pyplot as plt

ds = xr.open_dataset("your_output.nc")

# Visualize the flag layer
ds["flag"].isel(planting_window=0, year=0).plot()
plt.title("Pixel flags: 0=ok, 1=failed, 2=skipped")
plt.show()

# Check input coverage
weather = xr.open_dataset("weather_cube.nc")
soil = xr.open_dataset("soil_cube.nc")
w_var = list(weather.data_vars)[0]
s_var = list(soil.data_vars)[0]
print("Weather valid pixels:", weather[w_var].isel(time=0).notnull().sum().item())
print("Soil valid pixels:", soil[s_var].isel(depth=0).notnull().sum().item())
```

## Summary

| Question | Answer |
|---|---|
| Why so many skips? | 45 cells had no weather or soil data -- likely ocean/lakes/outside land mask |
| Does skipped mean failed? | No. Skipped = no input data. Failed = simulation crashed. |
| Is mean HWAM reliable? | Yes, for the 12 pixels that ran. Verify they cover target cropland. |
| What to do next? | Plot the flag layer from the output NetCDF. |
