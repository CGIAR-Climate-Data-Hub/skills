---
name: notebook-plots
description: >
  Writes interactive Plotly visualization cells into a Jupyter notebook or Google Colab.
  Use whenever the user wants to plot, visualize, chart, or map climate or geospatial data.
  Trigger phrases: "plot", "visualize", "show me", "make a chart", "graph this", "map this",
  "dashboard", "seasonal pattern", "monthly chart", "compare regions", "time series".
  Also triggers automatically when the user has a CSV from summarize_by_admin (columns:
  variable, time, value — optionally admin_unit) and wants to see the results, even if
  they don't say "plot" explicitly. Handles: seasonal bar charts, multi-year time series,
  admin-unit comparisons, spatial raster maps, and multi-variable dashboards.
  IMPORTANT: invoke this skill any time the user wants to see data — even if their phrasing
  is casual ("can you show me the rainfall?", "what does the temperature look like?").
---

# Notebook Plots

Writes exactly **three notebook cells** per visualization — no more, no less:
1. Markdown header (title, source, data path)
2. Imports + load data
3. Plot function + call

Never write download or processing code into the notebook. The notebook loads a
pre-existing CSV or NetCDF and renders a chart.

---

## Step 1 — Understand the data

Extract from context first. Ask only for what is genuinely unknown.

| Input | Where it comes from |
|-------|-------------------|
| CSV path | User provides, or output of `summarize_by_admin` |
| NetCDF path | Only needed for `spatial_map` (user provides or downloaded file) |
| Variable name | Exact string from `df["variable"].unique()` |
| Country / period | For the chart title |
| Plot type | Auto-detect (see below), or user specifies |

**Auto-detect plot type from data shape:**

| Condition | Plot type |
|-----------|-----------|
| Monthly frequency data | `seasonal_pattern` — bar chart by month |
| `admin_unit` column + multi-year | `time_series` — one line per region |
| `admin_unit` column + single time step | `admin_comparison` — sorted bar chart |
| No `admin_unit`, no time variation | `spatial_map` — raster heatmap from NetCDF |
| Multiple distinct variables in CSV | `dashboard` — one panel per variable |

---

## Step 2 — Write the three cells

### Cell 1 — Markdown header

```markdown
# {Country} — {Variable} {Period}

**Source:** {Source} | **Aggregation:** {agg_method} per {freq}
**Data:** `{csv_or_nc_path}`
```

### Cell 2 — Imports + load data

```python
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings; warnings.filterwarnings("ignore")

df = pd.read_csv("{CSV_PATH}")
df["time"] = pd.to_datetime(df["time"], errors="coerce")
df["month"] = df["time"].dt.month
print(df.head())
```

### Cell 3 — Plot function matching the detected type

Write **only** the function that matches. Fill all `{PLACEHOLDERS}` with real values.

---

#### `seasonal_pattern` — monthly bar chart

```python
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
var = "{ACTUAL_VAR_NAME}"

df_var = df[df["variable"] == var].sort_values("month")
monthly_vals = df_var.set_index("month")["value"].reindex(range(1, 13))

fig = go.Figure(go.Bar(
    x=MONTHS,
    y=monthly_vals.values,
    marker=dict(color=monthly_vals.values, colorscale="{COLORSCALE}",
                showscale=True, colorbar=dict(title="{UNITS}")),
    hovertemplate="%{x}: %{y:.2f} {UNITS}<extra></extra>",
))
fig.update_layout(
    title="{VARIABLE} — Monthly {AGG_LABEL} ({COUNTRY} {YEAR})",
    xaxis_title="Month", yaxis_title="{VARIABLE} ({UNITS})",
    template="plotly_white", width=800, height=460,
)
fig.show()
```

---

#### `time_series` — one line per admin unit

```python
fig = px.line(
    df[df["variable"] == "{VAR}"],
    x="time", y="value", color="admin_unit",
    title="{VARIABLE} — Time Series ({COUNTRY})",
    labels={"value": "{VARIABLE} ({UNITS})", "time": "Date", "admin_unit": "Region"},
    markers=True,
)
fig.update_layout(hovermode="x unified", template="plotly_white")
fig.show()
```

---

#### `admin_comparison` — sorted bar chart per region

```python
summary = (
    df[df["variable"] == "{VAR}"]
    .groupby("admin_unit")["value"].mean()
    .reset_index()
    .sort_values("value", ascending=False)
)
fig = px.bar(
    summary, x="admin_unit", y="value",
    title="{VARIABLE} by Admin Unit ({COUNTRY} {PERIOD})",
    labels={"value": "{VARIABLE} ({UNITS})", "admin_unit": "Admin Unit"},
    color="value", color_continuous_scale="{COLORSCALE}",
)
fig.update_layout(xaxis_tickangle=-30, template="plotly_white")
fig.show()
```

---

#### `spatial_map` — raster heatmap from NetCDF

```python
import xarray as xr

ds = xr.open_dataset("{NC_PATH}")
var = "{ACTUAL_VAR_NAME}"
da = ds[var].mean(dim="time") if "time" in ds[var].dims else ds[var]

fig = px.imshow(
    da.values, x=da.lon.values, y=da.lat.values,
    color_continuous_scale="{COLORSCALE}",
    title="{VARIABLE} — {AGG_LABEL} ({COUNTRY} {PERIOD})",
    labels={"color": "{UNITS}", "x": "Longitude", "y": "Latitude"},
    origin="lower", aspect="auto",
)
fig.update_coloraxes(colorbar_title="{UNITS}")
fig.show()
```

---

#### `dashboard` — one panel per variable

```python
variables = df["variable"].unique().tolist()
fig = make_subplots(rows=1, cols=len(variables),
                    subplot_titles=[v.upper() for v in variables])

for i, var in enumerate(variables, start=1):
    df_v = df[df["variable"] == var].sort_values("time")
    fig.add_trace(
        go.Scatter(x=df_v["time"], y=df_v["value"],
                   mode="lines+markers", name=var),
        row=1, col=i,
    )
    fig.update_yaxes(title_text="{UNITS}", row=1, col=i)

fig.update_layout(
    title="{COUNTRY} — Climate Overview {PERIOD}",
    template="plotly_white", height=420, showlegend=False,
)
fig.show()
```

---

## Colorscale + units reference

| Variable | Colorscale | Units |
|----------|-----------|-------|
| Solar radiation (`rsds`, `ALLSKY_SFC_SW_DWN`) | `YlOrRd` | MJ/m²/month |
| Precipitation (`pr`, `precipitation`) | `Blues` | mm |
| Tmax / Tmin (`tmax`, `tmin`) | `RdYlBu_r` | °C |
| Relative humidity (`RH2M`, `rh`) | `BuGn` | % |
| Wind speed (`WS2M`, `ws`) | `PuBu` | m/s |
| Reference ET (`etr`) | `YlGn` | mm/day |

---

## Response style

- Create the notebook at `{OUTPUT_FOLDER}/{country}_{variable}_{year}.ipynb` using `nbformat`
- After writing say: *"Open `{notebook_path}` and run all cells — the chart renders inline."*
- Multiple variables → default to `dashboard`; offer individual charts if user prefers
