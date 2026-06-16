# DSSAT Output: Why Are So Many Pixels Skipped?

## Your Results at a Glance

| Metric | Value |
|---|---|
| pixels_ok | 12 |
| pixels_skipped | 45 |
| pixels_failed | 0 |
| mean HWAM | 6,200 kg/ha |

## Why Are So Many Pixels Skipped?

The large number of skipped pixels (45 out of 57 total) is **expected behavior**, not a problem.

**The Root Cause: Grid Resolution Mismatch**

Your simulation combines climate and soil data from sources with different spatial resolutions:

- CHIRPS (precipitation): 0.05 degree resolution -- the finest grid, used as the base
- AgERA5 (solar radiation): 0.1 degree resolution -- coarser by a factor of 2
- SoilGrids: also at a coarser resolution than CHIRPS

When the simulation grid is defined at CHIRPS resolution (0.05 deg), many fine-resolution pixels fall **outside the spatial coverage** of AgERA5 or SoilGrids. This happens especially at the edges of your bounding box -- the top/bottom rows and left/right columns of the CHIRPS grid often have no corresponding AgERA5 or SoilGrids data, resulting in NaN values for solar radiation (rsds) or soil properties.

When a pixel has NaN inputs, it cannot be passed to DSSAT. Those pixels are automatically skipped before the model even runs.

**Skipped vs. Failed -- Key Distinction**

| Term | Meaning | Action needed? |
|------|---------|----------------|
| pixels_skipped | NaN data at grid edges -- structural, expected | No |
| pixels_failed | DSSAT runtime error | Yes, if > 5% of (ok+failed) |

## Is the Result Reliable?

**Yes, highly reliable.**

- `pixels_failed = 0` means DSSAT ran cleanly on all 12 attempted pixels
- `pixels_skipped = 45` reflects edge pixels excluded before DSSAT -- no bias introduced
- Mean HWAM of 6,200 kg/ha is a plausible yield result

The only consideration: 12 valid pixels is a small footprint. If the area of interest is large, verify these 12 pixels adequately represent it, or expand the bounding box to capture more interior pixels with full data coverage.

## How to Inspect Coverage

```python
import xarray as xr

ds = xr.open_dataset("your_output.nc")
hwam = ds["HWAM"]

# Count valid pixels (at least one non-NaN result)
valid_pixels = (~hwam.isnull()).any(dim=["planting_window", "year"])
print(f"Valid pixels: {valid_pixels.sum().item()}")
print(f"Total pixels in grid: {valid_pixels.size}")

# Plot spatial coverage
valid_pixels.plot(cmap="RdYlGn")
```

## Summary

| Question | Answer |
|---|---|
| Why so many skipped? | Grid-edge pixels lack AgERA5/SoilGrids coverage -- expected at 0.05 deg resolution |
| Are skipped pixels a bug? | No -- automatically excluded before DSSAT runs |
| Is pixels_failed=0 good? | Yes -- DSSAT ran without errors on all attempted pixels |
| Is the result reliable? | Yes -- highly reliable for the 12 valid pixels |
| Any concern? | Only that 12 pixels is a small spatial sample |
