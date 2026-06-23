# Spatial Crop Modeler — Troubleshooting

This file collects diagnostic detail for failures of `ag-cube-cm` runs.
Sections:

- [Manual datacube fixes](#manual-datacube-fixes) — workarounds when the
  aggeodata auto-builder fails. Most users should reach for the
  `geospatial-cube-processor` skill **first** — its `stack_datasets`
  function uses a pure xarray + rioxarray path with configurable
  `target_resolution` and `resampling_method` and avoids every issue
  documented below. The fixes here are only needed when you want to keep
  using the aggeodata internal stacker.
- [DSSAT rc=99 diagnosis](#dssat-returned-rc99--diagnose-in-this-order)
- [Other failure modes](#other-failure-modes)

---

## Manual datacube fixes

The `ag-cube-cm` auto-builder is robust for typical small-area runs but a few
failure modes show up at country scale or with mixed-resolution sources. If
you hit one of these between Step 5 and Step 6, fix the intermediate cube then
re-run `ag-cube-cm` in `with_cubes` mode.

**Boundary NaN after `xr.interp`** — when the reference grid extends slightly
beyond the source grid, `xr.interp` returns NaN on edge pixels (`bounds_error=False`
only suppresses scipy errors; the NaNs come from the linear interpolant having no
neighbors). Fill with the nearest valid value along both axes:

```python
resampled = da.interp(y=ref_y, x=ref_x, method="linear")
resampled = resampled.ffill("y").bfill("y").ffill("x").bfill("x")
```

**Stacker SIGABRT on large file counts** — at ~1000+ input GeoTIFFs the
rasterio warp path can hit a heap corruption ("unaligned tcache chunk") and the
process dies with SIGABRT. Bypass it with a pure-xarray stack:

```python
import xarray as xr
import rioxarray  # registers the .rio accessor

ds = xr.open_mfdataset(file_paths, combine="by_coords", parallel=True)
ds = ds.rio.write_crs("EPSG:4326")   # mfdataset drops CRS metadata — re-attach
ds.to_netcdf(out_path, engine="netcdf4")
```

The `write_crs` call is mandatory — without it, downstream tools see
`ds.rio.crs == None` and silently misalign.

**Time coordinate is all zeros after manual stack** — when input files lack CF
time metadata, the time index is zero-valued and slices wrong silently. Rebuild:

```python
assert ds.time.dtype.kind == "M", "time coord is not datetime — reassign via cftime_range"

ds = ds.assign_coords(
    time=xr.cftime_range("2021-01-01", periods=ds.sizes["time"], freq="D")
              .to_datetimeindex()
)
```

For monthly cubes use `freq="MS"`, annual `freq="YS"`.

---

## `DSSAT returned rc=99` — diagnose in this order

`rc=99` is DSSAT's generic "something went wrong" exit code. The accompanying
message ("Crop code incompatible") is often misleading — the real cause can be
any of the four below. Work through them from cheapest to most expensive; most
rc=99 cases are caught in the first two.

1. **Empty weather DataFrame** — the pixel had NaN weather (common at grid
   edges where the climate cube doesn't cover the soil cube extent). DSSAT
   reads zero rows and bails out.
   **Test:** `df_wth.dropna()` returns 0 rows. Expected at the edges; suspicious
   in the interior — check climate-cube extent vs soil-cube extent.
2. **Working path contains a space** — DSSATPRO's whitespace-delimited parser
   corrupts the M-line and reports a fake "crop code incompatible".
   **Test:** `print(working_path)`. If it contains a space (`OneDrive - CGIAR`,
   `Program Files`, …), move to a space-free path like `D:/dssat_work` or
   `/tmp/dssat_runs`.
3. **Wrong cultivar module** — e.g. WHCER cultivars (`IB1487`) under the
   bundled WHAPS048 binary, or a maize cultivar passed to a wheat run.
   **Test:** open the generated X-file, check the `SMODEL` line matches the
   cultivar's expected module (`WHAPS048` for wheat WHAPS, `MZCER048` for maize,
   `CRGRO048` for legumes). For wheat, use `IB1015`, `IB0001`, `IB0002`, or
   `IB1500`.
4. **DSSAT binary missing or not on PATH** — `dssat_path` in config is wrong,
   or DSSAT isn't installed.
   **Test:** `which dscsm048` (Linux/Mac) or check the binary at the configured
   `dssat_path`/`bin_path`.

---

## Other failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| All pixels skipped | Grid edges have NaN from coarser AgERA5/SoilGrids | Expected — increase `max_pixels` or check interior pixels |
| All pixels skipped: soil slice is all NaN | Soil cube coordinates are in projected metres, not degrees — `sel(y,x)` lands outside the data | Rebuild soil cube with `crs='+proj=igh ...'` and `target_crs='EPSG:4326'` (see `soil-data-download` skill) |
| All pixels skipped: `no valid index for a 0-dimensional object` | Soil cube is in flat format (`clay_0-5cm_mean`) — needs reshaping | Run `reshape_flat_soil_cube(ds).to_netcdf(...)` then re-run simulation |
| `UnicodeEncodeError` | Non-ASCII chars in output path on Windows | Use ASCII-only paths |
| `ModuleNotFoundError: mcp` | mcp package not installed | `pip install mcp` |
| Slow simulation | `ncores` too low | Set `ncores` to number of physical CPU cores |
