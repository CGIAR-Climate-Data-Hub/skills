---
name: datacube-temporal-aggregator
description: >
  Summarizes the time axis of a gridded xarray Dataset (daily, dekadal, or monthly climate data) into
  monthly, annual, meteorological-season (DJF/MAM/JJA/SON), custom season-window, or long-term monthly
  climatology values, per pixel, keeping the result gridded. Use this skill whenever the user wants
  values over time periods rather than over space: "monthly totals", "annual rainfall", "per season",
  "DJF / JJA", "seasonal mean temperature", "Jun–Sep accumulated rain", "long rains / short rains",
  "growing season", "Nov–Mar" (crossing the new year), "average month", "climatology", "typical year".
  Works on its own (gridded output for maps, COGs, or crop models) or before the zonal statistics in
  geospatial-cube-processor (temporal first, then spatial). Does not clip, stack, or summarize by
  region — that is geospatial-cube-processor.
---

# Datacube Temporal Aggregator

This skill teaches Claude how to write one generic function, `aggregate_time`, **directly into the
user's existing script or notebook** (or run it in-session when an orchestrator such as gcf-pipeline
calls for it). It uses only `xarray`, `pandas`, and `numpy` — already in the climate-data-download
environment. It reduces the `time` axis **per pixel** and returns a gridded `xr.Dataset`; it never
touches `lat`/`lon`.

---

## Before writing any code — confirm with the user

Ask only what is unknown:

- **Period**: `"month"`, `"year"`, `"season"` (DJF/MAM/JJA/SON), `"window"` (custom dates), or
  `"monthly_climatology"`?
- **Window dates** (only for `"window"`): start and end as `"MM-DD"`. If the user names a season
  without dates ("main season", "Meher", "long rains"), **ask for the dates** — seasons differ by
  country and crop; never guess them.
- **Aggregation**: `sum`, `mean`, `min`, or `max`? Infer from the variable and wording (table below)
  and state the choice.

| Variable / wording | `agg_method` |
|--------------------|--------------|
| "accumulated", "total"; precipitation, ET, radiation as a period total | `sum` |
| temperature, humidity, wind, soil moisture — states, not amounts | `mean` |
| "hottest", "maximum", "extreme" | `max` |
| "coldest", "minimum", "frost" | `min` |

---

## Periods

| `period` | Groups | `period` label |
|----------|--------|----------------|
| `"month"` | calendar months | `2020-01` |
| `"year"` | calendar years | `2020` |
| `"season"` | DJF, MAM, JJA, SON (DJF crosses the year) | `MAM 2020`, `DJF 2020-21` |
| `"window"` | user dates `{"name": ("MM-DD", "MM-DD")}`; end before start crosses the year | `JJAS 2020`, `Nov-Mar 2020-21` |
| `"monthly_climatology"` | each calendar month across all years | dim `month` = 1–12 |

---

## Function — `aggregate_time`

```python
import calendar
import numpy as np
import pandas as pd
import xarray as xr

MET_SEASONS = {
    "DJF": ("12-01", "02-29"), "MAM": ("03-01", "05-31"),
    "JJA": ("06-01", "08-31"), "SON": ("09-01", "11-30"),
}


def _clamp(year, month, day):
    return pd.Timestamp(year, month, min(day, calendar.monthrange(year, month)[1]))


def aggregate_time(
    ds: xr.Dataset,
    period: str = "year",
    agg_method: str = "mean",
    windows: dict = None,
    min_coverage: float = 0.9,
) -> xr.Dataset:
    t = pd.DatetimeIndex(ds["time"].values)
    step_days = float(np.median(np.diff(t.values)) / np.timedelta64(1, "D")) if len(t) > 1 else 1.0

    if period == "monthly_climatology":
        monthly = aggregate_time(ds, "month", agg_method, min_coverage=min_coverage)
        return monthly.groupby("time.month").mean("time")

    if period in ("month", "year"):
        p = t.to_period("M" if period == "month" else "Y")
        groups = [(p.start_time, p.end_time.normalize(), p.strftime("%Y-%m" if period == "month" else "%Y"),
                   np.ones(len(t), bool))]
    elif period in ("season", "window"):
        wins = MET_SEASONS if period == "season" else windows
        if not wins:
            raise ValueError('period="window" needs windows={"name": ("MM-DD", "MM-DD")}')
        groups = []
        md = t.month * 100 + t.day
        for name, (s, e) in wins.items():
            sm, sd = map(int, s.split("-"))
            em, ed = map(int, e.split("-"))
            s_md, e_md = sm * 100 + sd, em * 100 + ed
            crosses = e_md < s_md
            if crosses:  # e.g. Nov-Mar: labelled by the year the window starts in
                inside = (md >= s_md) | (md <= e_md)
                y0 = np.where(md >= s_md, t.year, t.year - 1)
            else:
                inside = (md >= s_md) & (md <= e_md)
                y0 = t.year.values
            starts = pd.DatetimeIndex([_clamp(y, sm, sd) for y in y0])
            ends = pd.DatetimeIndex([_clamp(y + crosses, em, ed) for y in y0])
            labels = pd.Index([f"{name} {y}-{(y + 1) % 100:02d}" if crosses else f"{name} {y}" for y in y0])
            groups.append((starts, ends, labels, np.asarray(inside)))
    else:
        raise ValueError("period must be month | year | season | window | monthly_climatology")

    pieces = []
    for starts, ends, labels, inside in groups:
        if not inside.any():
            continue
        sub = ds.isel(time=np.flatnonzero(inside))
        key = xr.DataArray(pd.DatetimeIndex(starts[inside]), dims="time",
                           coords={"time": sub["time"]}, name="period_start")
        g = sub.groupby(key)
        out = g.sum("time", min_count=1) if agg_method == "sum" else getattr(g, agg_method)("time")

        info = pd.DataFrame({"start": starts[inside], "end": ends[inside], "label": labels[inside]})
        info = info.groupby("start").agg(end=("end", "first"), label=("label", "first"), n_steps=("label", "size"))
        info["coverage"] = (info["n_steps"] * step_days / ((info["end"] - info.index).dt.days + 1)).clip(upper=1)
        out = out.assign_coords(
            period=("period_start", info.loc[out.period_start.values, "label"].values),
            n_steps=("period_start", info.loc[out.period_start.values, "n_steps"].values),
            coverage=("period_start", info.loc[out.period_start.values, "coverage"].values),
        )
        pieces.append(out.where(out.coverage >= min_coverage, drop=True))

    result = xr.concat(pieces, dim="period_start").sortby("period_start").rename(period_start="time")
    result.attrs.update(ds.attrs)
    result.attrs.update({"temporal_aggregation": f"{agg_method} per {period}", "source_step_days": step_days})
    return result
```

### Example calls

```python
annual_rain   = aggregate_time(ds, "year", "sum")
monthly_tmax  = aggregate_time(ds, "month", "mean")
seasonal_tmax = aggregate_time(ds, "season", "mean")
crop_season   = aggregate_time(ds, "window", "sum", windows={"JJAS": ("06-01", "09-30")})
two_seasons   = aggregate_time(ds, "window", "sum",
                               windows={"long rains": ("03-01", "05-31"), "short rains": ("10-01", "12-31")})
austral       = aggregate_time(ds, "window", "sum", windows={"Nov-Mar": ("11-01", "03-31")})
clim          = aggregate_time(ds, "monthly_climatology", "sum")   # mean monthly total, 12 maps
```

After running, report which periods were kept and which were dropped as incomplete:

```python
print(dict(zip(out.period.values, out.coverage.values.round(2))))
```

---

## Output

- A gridded `xr.Dataset` with the same variables and `lat`/`lon`. `time` holds the **start date** of
  each period; the coordinates `period` (readable label), `n_steps`, and `coverage` describe it.
- `monthly_climatology` returns a `month` dimension (1–12) instead of `time`.
- Save gridded output with `out.to_netcdf("rain_JJAS.nc")`, or one COG per period:
  `out["pr"].sel(time=t).rio.write_crs("EPSG:4326").rio.to_raster(f"pr_{label}.tif", driver="COG")`
  (replace spaces in the label for the file name).
- **For a per-region table**, pass the result to `summarize_by_admin` in
  `.agents/skills/geospatial-cube-processor/SKILL.md`. It carries `period` and `month` through to the
  CSV.

---

## Key rules

- **Incomplete periods are dropped.** A period whose input covers less than `min_coverage` (default
  90 %) of its days is removed — e.g. DJF 2019-20 when the data starts on 1 Jan 2020, or a year cut
  off by the end date. A partial sum would look like a drought. Tell the user what was dropped; lower
  `min_coverage` only if they ask.
- `sum` uses `min_count=1`, so pixels outside a mask stay NaN instead of becoming 0. Never write
  `resample(...).sum()` on masked data — the zeros pull every later spatial mean down.
- `monthly_climatology` aggregates to months first, then averages across years — "average January
  rainfall" is the mean of the January totals, not the sum of all Januaries.
- Cross-year windows are labelled by the year they start in: `Nov-Mar 2020-21` is Nov 2020 – Mar 2021;
  `DJF 2020-21` is Dec 2020 – Feb 2021. Windows may overlap — each is computed on its own.
- A window ending on `"02-29"` ends on 28 Feb in non-leap years.
- Coverage counts time steps, not valid pixels: a pixel with gaps inside a kept period is still
  aggregated with `skipna`. Mention it if the source has known gaps.

---

## Common pitfalls

- **Time dimension name**: the function expects `time`. ERA5/AgERA5 files may use `valid_time` —
  `ds = ds.rename(valid_time="time")` first.
- **Non-standard calendars**: CMIP-style `cftime` axes (`noleap`, `360_day`) do not convert to
  `pd.DatetimeIndex`. Use `ds = ds.convert_calendar("standard", align_on="date")` first and say so.
- **Units after `sum`**: a daily rate becomes a period total (`mm d-1` → `mm`). Update
  `ds[var].attrs["units"]` so plots and metadata are right.
- **Temperature in Kelvin**: aggregation does not change units; convert before plotting if needed.
- **Memory**: for large cubes, `ds = ds.chunk({"time": 365})` before calling; the groupby stays lazy
  until `.compute()` or a write.

---

*Evaluation examples: [evals/evals.json](evals/evals.json)*
