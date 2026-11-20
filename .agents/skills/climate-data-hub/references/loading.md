# Loading Hub data

Replace `URL` with an `https://` location from the record. Read a subset first.

## Zarr (`application/vnd.zarr`)

Needs `xarray`, `zarr`, `fsspec`, `aiohttp`.

```python
import xarray as xr

# trust_env: use the sandbox's proxy settings if it has any (no-op otherwise)
ds = xr.open_zarr(URL, storage_options={"client_kwargs": {"trust_env": True}})

# Check coordinate names first (x/y or lon/lat). Latitude often runs north to south.
window = ds.sel(x=slice(28, 52), y=slice(18, -12))
point = ds.sel(x=36.8, y=-1.3, method="nearest")
```

## GeoTIFF (`image/tiff`)

Needs `rioxarray`.

```python
import rioxarray

da = rioxarray.open_rasterio(URL, masked=True)
window = da.rio.clip_box(minx=28, miny=-12, maxx=52, maxy=18)
```

For many files, pick from the record's file list:

```python
import pandas as pd

files = pd.read_csv("https://cgiar-climate-data-hub.github.io/catalog/<id>/<asset>-files.csv")
url = files.loc[files["species"] == "cattle", "href"].iloc[0]
```

## Parquet (`application/vnd.apache.parquet`)

Needs `pandas`, `pyarrow`.

```python
import pandas as pd

df = pd.read_parquet(URL)
```

## Plain text (`text/plain`)

Fetch it and parse the text.

## If reading fails

- **Hangs or connection errors behind a proxy:** keep `trust_env` on Zarr
  reads. For GeoTIFFs, set the `GDAL_HTTP_PROXY` env var to the proxy URL.
- **Missing packages and no `pip`:** download one file with the standard
  library, then open it locally. Check the record's `file_size` first. This
  doesn't work for Zarr, which is many files.

  ```python
  import urllib.request

  urllib.request.urlretrieve(URL, "data.tif")
  ```
