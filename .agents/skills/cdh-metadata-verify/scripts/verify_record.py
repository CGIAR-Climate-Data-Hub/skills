#!/usr/bin/env python3
"""verify_record.py — adversarial, evidence-based checks of a CDH metadata record against reality.

The schema validator says a record is well-formed. This script asks whether it is TRUE: it opens
every data asset the record points at and diffs what is stored against what the record claims
(bbox, CRS, grid step, variables, dtypes, fill values, categories, time axis, file sizes, template
expansions, foreign keys), resolves every URL, checks the DOI against Crossref, the licence
against SPDX, the geography ids against the Hub vocabulary, and the dates/ids for consistency.

Nothing is auto-fixed (standard §4.6: an authored value always wins; a disagreement is reported).
Output is a severity-ranked findings table (Markdown) and JSON. Exit code 1 when any HIGH finding
exists, 2 when the record cannot be read.

    python verify_record.py records/glw4-2020/glw4-2020.yaml
    python verify_record.py record.yaml --json out.json --md out.md --no-remote     # offline checks only
    python verify_record.py record.yaml --catalog-ids glw4-2020,mapspam2020          # known catalog ids
    python verify_record.py record.yaml --standard-dir ../cdh-metadata-standard      # also run validate-yaml.js

Required: pyyaml, requests. Optional (each unlocks checks; absence is reported as INFO, never as
a pass): rasterio (GeoTIFF/COG), xarray + zarr>=3 (Zarr), duckdb (Parquet/CSV over HTTP).
Accepts v0.4.x records and normalises v0.3.0 records (root dimensions/variables, joins,
spatial.resolution) so the same checks run on the live catalog.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import math
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import requests
import yaml

UA = "cdh-metadata-verify/0.1 (+https://github.com/CGIAR-Climate-Data-Hub/skills)"
TIMEOUT = 40
SEV_ORDER = {"HIGH": 0, "MED": 1, "LOW": 2, "INFO": 3}
STD_RAW = "https://raw.githubusercontent.com/CGIAR-Climate-Data-Hub/cdh-metadata-standard/main"
CATALOG_API = "https://api.github.com/repos/CGIAR-Climate-Data-Hub/cdh-catalog/contents/records"
NUMERIC = {"int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float16", "float32", "float64",
           "decimal", "integer", "number"}


@dataclass
class Finding:
    severity: str
    path: str
    check: str
    message: str
    record_value: Any = None
    observed: Any = None
    hint: str = ""


@dataclass
class Report:
    record: str
    id: str | None
    version: str | None
    schema_version: str | None
    findings: list[Finding] = field(default_factory=list)
    checked_urls: int = 0
    assets_inspected: int = 0

    def add(self, sev, path, check, message, record_value=None, observed=None, hint=""):
        self.findings.append(Finding(sev, path, check, message, _short(record_value), _short(observed), hint))

    def sorted(self):
        return sorted(self.findings, key=lambda f: (SEV_ORDER.get(f.severity, 9), f.path))


def _short(v, n=160):
    if v is None:
        return None
    s = v if isinstance(v, str) else json.dumps(v, default=str)
    return s if len(s) <= n else s[: n - 1] + "…"


# ----------------------------------------------------------------------------- helpers
def http_url(url: str) -> str:
    """s3://bucket/key → https://bucket.s3.amazonaws.com/key (public buckets); gs:// left alone."""
    if url.startswith("s3://"):
        b, _, k = url[5:].partition("/")
        return f"https://{b}.s3.amazonaws.com/{k}"
    return url


def probe(url: str, session: requests.Session) -> dict:
    """HEAD, then ranged GET on 403/405/501. Returns status, content-type, length, final url.
    A Zarr root is a prefix, not an object: probe its zarr.json (v3) / .zmetadata / .zgroup (v2) instead."""
    u = http_url(url)
    out = {"url": url, "status": None, "content_type": None, "length": None, "error": None}
    if u.rstrip("/").endswith(".zarr"):
        for marker in ("zarr.json", ".zmetadata", ".zgroup"):
            r = probe(u.rstrip("/") + "/" + marker, session)
            if r["status"] and r["status"] < 400:
                return {**r, "url": url, "length": None, "zarr_marker": marker}
        return {**r, "url": url}
    try:
        r = session.head(u, allow_redirects=True, timeout=TIMEOUT)
        if r.status_code in (403, 405, 501, 400):
            r = session.get(u, headers={"Range": "bytes=0-0"}, allow_redirects=True, timeout=TIMEOUT, stream=True)
        out.update(status=r.status_code, content_type=(r.headers.get("content-type") or "").split(";")[0].strip(),
                   length=int(r.headers.get("content-range", "").split("/")[-1]) if r.headers.get("content-range", "").split("/")[-1].isdigit()
                   else (int(r.headers["content-length"]) if r.headers.get("content-length", "").isdigit() else None))
        r.close()
    except requests.RequestException as e:
        out["error"] = e.__class__.__name__
    return out


def s3_list(url: str, session: requests.Session, max_keys: int = 50) -> list[str] | None:
    """List objects under an s3:// or https://bucket.s3.amazonaws.com/prefix (public, anonymous)."""
    u = http_url(url)
    m = re.match(r"https://([^/.]+)\.s3[.-][^/]*amazonaws\.com/(.*)$", u) or re.match(r"https://([^/.]+)\.s3\.amazonaws\.com/(.*)$", u)
    if not m:
        return None
    bucket, prefix = m.group(1), m.group(2)
    try:
        r = session.get(f"https://{bucket}.s3.amazonaws.com/?list-type=2&prefix={prefix}&max-keys={max_keys}", timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        root = ET.fromstring(r.text)
        ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
        return [c.find(f"{ns}Key").text for c in root.iter(f"{ns}Contents")]
    except Exception:  # noqa: BLE001
        return None


def parse_size(s) -> int | None:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return int(s)
    m = re.match(r"^\s*([\d.]+)\s*([KMGTP]?B)\s*$", str(s), re.I)
    if not m:
        return None
    mult = {"B": 1, "KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12, "PB": 1e15}[m.group(2).upper()]
    return int(float(m.group(1)) * mult)


def walk_urls(obj, path="") -> list[tuple[str, str]]:
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}/{k}"
            if k in ("url", "href") and isinstance(v, str) and re.match(r"^(https?|s3|gs)://", v):
                out.append((p, v))
            else:
                out.extend(walk_urls(v, p))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(walk_urls(v, f"{path}/{i}"))
    elif isinstance(obj, str) and path.endswith("/doi") and obj.startswith("http"):
        out.append((path, obj))
    return out


def norm_dtype(d) -> str | None:
    if d is None:
        return None
    s = str(d).lower()
    s = {"float": "float32", "double": "float64", "bool": "boolean", "str": "string", "utf8": "string", "int": "int64",
         "integer": "int64", "number": "float64", "bigint": "int64", "varchar": "string", "date32[day]": "date"}.get(s, s)
    return s


def dtype_compatible(record: str | None, observed: str | None) -> bool:
    r, o = norm_dtype(record), norm_dtype(observed)
    if r is None or o is None:
        return True
    if r == o:
        return True
    fam = lambda x: "int" if ("int" in x) else ("float" if "float" in x or x == "decimal" else x)
    return fam(r) == fam(o) and r in ("integer", "number", "int64", "float64")


def nan_eq(a, b) -> bool:
    try:
        fa, fb = float(a), float(b)
        if math.isnan(fa) and math.isnan(fb):
            return True
        return math.isclose(fa, fb, rel_tol=1e-6)
    except (TypeError, ValueError):
        return str(a).lower() == str(b).lower()


# ----------------------------------------------------------------------------- normalisation
def normalise(rec: dict) -> dict:
    """Give v0.3.0 records the v0.4 shape so the checks are uniform. Returns a shallow copy."""
    r = dict(rec)
    ver = str(r.get("cdh_schema_version", ""))
    if "structures" not in r and ("variables" in r or "dimensions" in r):
        st = {"name": "main", "dimensions": r.get("dimensions", []) or [], "variables": r.get("variables", []) or []}
        if r.get("joins"):
            st["foreign_keys"] = [{"fields": j.get("left_fields", []), "reference": {"resource": j.get("target"), "fields": j.get("right_fields", [])}}
                                  for j in r["joins"]]
        if isinstance(r.get("spatial"), dict) and r["spatial"].get("geometry_column"):
            st["geometry_column"] = r["spatial"]["geometry_column"]
        res = (r.get("spatial") or {}).get("resolution") or []
        for x in res:
            if x.get("type") in ("xy", "x", "y") and x.get("value") is not None:
                st["dimensions"] = [{"name": "cell", "type": x["type"], "step": x["value"], "unit": x.get("unit"), "_from_resolution": True}] + st["dimensions"]
        for v in st["variables"]:
            v.pop("dimensions", None)
        r["structures"] = [st]
        r["_normalised_from"] = ver or "v0.3.x"
    # v0.3.0 kept nodata per asset (data[].nodata); it is read per asset in the comparisons below.
    return r


def asset_nodata(d: dict, v: dict):
    """v0.3.0: the asset's own nodata wins (one record described Zarr NaN and COG -3.4e38 that way);
    v0.4: nodata lives on the variable in the structure the asset holds."""
    return d["nodata"] if "nodata" in d else v.get("nodata")


CRS_VARS = {"spatial_ref", "crs", "grid_mapping", "lambert_conformal_conic", "transverse_mercator"}


# ----------------------------------------------------------------------------- inspectors
def inspect_raster(url: str) -> dict:
    import rasterio  # noqa: PLC0415
    u = url
    if u.startswith("s3://"):
        u = "/vsis3/" + u[5:]
    with rasterio.Env(AWS_NO_SIGN_REQUEST="YES", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="3"):
        with rasterio.open(u) as src:
            b = src.bounds
            info = {"kind": "raster", "bbox": [b.left, b.bottom, b.right, b.top], "crs": src.crs.to_string() if src.crs else None,
                    "res": [abs(src.res[0]), abs(src.res[1])], "dtypes": list(src.dtypes), "nodata": src.nodata, "count": src.count,
                    "band_names": [d for d in src.descriptions], "driver": src.driver, "layout": src.tags(ns="IMAGE_STRUCTURE").get("LAYOUT"),
                    "overviews": src.overviews(1) if src.count else []}
            # category sample from the coarsest overview (cheap) for small-int rasters
            if src.dtypes[0] in ("uint8", "int8", "uint16", "int16") and src.overviews(1):
                ov = src.overviews(1)[-1]
                arr = src.read(1, out_shape=(1, max(1, src.height // ov), max(1, src.width // ov)))
                import numpy as np  # noqa: PLC0415
                vals, counts = np.unique(arr, return_counts=True)
                info["observed_values"] = [int(v) for v in vals][:200]
            return info


def inspect_zarr(url: str) -> dict:
    import xarray as xr  # noqa: PLC0415
    u = http_url(url)
    ds = None
    for cons in (True, False):
        try:
            ds = xr.open_zarr(u, consolidated=cons, chunks=None)
            break
        except Exception:  # noqa: BLE001
            continue
    if ds is None:
        raise RuntimeError("could not open zarr store")
    info = {"kind": "zarr", "variables": {}, "dims": {k: int(v) for k, v in ds.sizes.items()}, "coords": {}}
    for name, da in ds.data_vars.items():
        info["variables"][name] = {"dtype": str(da.dtype), "dims": list(da.dims), "nodata": da.encoding.get("_FillValue", da.attrs.get("_FillValue")),
                                   "units": da.attrs.get("units"), "attrs": {k: str(v)[:60] for k, v in list(da.attrs.items())[:8]}}
    for c in ds.coords:
        v = ds[c].values
        if v.size:
            try:
                info["coords"][c] = {"min": str(v.min()), "max": str(v.max()), "n": int(v.size),
                                     "values": [str(x) for x in v] if v.size <= 500 else None}
            except Exception:  # noqa: BLE001
                info["coords"][c] = {"n": int(v.size)}
    lat = next((c for c in ds.coords if c.lower() in ("lat", "latitude", "y")), None)
    lon = next((c for c in ds.coords if c.lower() in ("lon", "longitude", "x")), None)
    if lat and lon and ds[lat].size > 1 and ds[lon].size > 1:
        la, lo = ds[lat].values, ds[lon].values
        dy, dx = abs(float(la[1] - la[0])), abs(float(lo[1] - lo[0]))
        info["bbox"] = [float(lo.min()) - dx / 2, float(la.min()) - dy / 2, float(lo.max()) + dx / 2, float(la.max()) + dy / 2]
        info["res"] = [dx, dy]
    tcoord = next((c for c in ds.coords if c.lower() in ("time", "date")), None)
    if tcoord:
        t = ds[tcoord].values
        info["time"] = {"start": str(t.min())[:10], "end": str(t.max())[:10], "n": int(t.size)}
    ds.close()
    return info


def inspect_parquet(url: str, sample_cols: list[str] | None = None) -> dict:
    import duckdb  # noqa: PLC0415
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    u = http_url(url)
    cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{u}', hive_partitioning=false)").fetchall()
    info = {"kind": "parquet", "columns": {c[0]: c[1] for c in cols}}
    try:
        info["rows"] = con.execute(f"SELECT count(*) FROM read_parquet('{u}', hive_partitioning=false)").fetchone()[0]
    except Exception:  # noqa: BLE001
        pass
    info["samples"] = {}
    for c in sample_cols or []:
        if c in info["columns"]:
            try:
                vals = con.execute(f"SELECT DISTINCT \"{c}\" FROM read_parquet('{u}', hive_partitioning=false) LIMIT 500").fetchall()
                info["samples"][c] = [v[0] for v in vals]
            except Exception:  # noqa: BLE001
                pass
    return info


def inspect_api(url: str, session: requests.Session) -> dict:
    r = session.get(http_url(url), timeout=TIMEOUT, stream=True)
    ct = (r.headers.get("content-type") or "").split(";")[0].strip()
    body = r.raw.read(400, decode_content=True)
    r.close()
    return {"kind": "api", "status": r.status_code, "content_type": ct, "head": body[:200].decode("utf-8", "replace")}


# ----------------------------------------------------------------------------- the verifier
class Verifier:
    def __init__(self, path: Path, *, remote: bool = True, catalog_ids: set[str] | None = None, standard_dir: Path | None = None,
                 max_template: int = 6):
        self.path = path
        self.remote = remote
        self.standard_dir = standard_dir
        self.max_template = max_template
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA, "Accept": "*/*"})
        self.raw = yaml.safe_load(path.read_text()) or {}
        self.rec = normalise(self.raw)
        self.rep = Report(str(path), self.raw.get("id"), str(self.raw.get("version", "")) or None, self.raw.get("cdh_schema_version"))
        self.catalog_ids = catalog_ids
        self.observed: dict[str, dict] = {}

    # ---------- orchestration
    def run(self) -> Report:
        for name in ("check_schema", "check_identity", "check_dates", "check_license", "check_contacts", "check_citation",
                     "check_geography", "check_links", "check_assets", "check_structures_vs_assets", "check_spatial",
                     "check_temporal", "check_foreign_keys", "check_provenance", "check_prose"):
            try:
                getattr(self, name)()
            except Exception as e:  # noqa: BLE001
                self.rep.add("INFO", "/", name, f"check crashed: {e.__class__.__name__}: {e}", hint="fix the verifier or run with -v")
        return self.rep

    # ---------- schema (delegated)
    def check_schema(self):
        if not self.standard_dir:
            self.rep.add("INFO", "/", "schema", "schema/cross-field validation not run (pass --standard-dir to run validate-yaml.js)")
            return
        js = Path(self.standard_dir) / "scripts" / "validate-yaml.js"
        if not js.exists():
            self.rep.add("INFO", "/", "schema", f"{js} not found")
            return
        tooling = None
        try:
            tooling = "v" + json.loads((Path(self.standard_dir) / "package.json").read_text())["version"]
        except Exception:  # noqa: BLE001
            pass
        p = subprocess.run(["node", str(js), str(self.path.resolve())], capture_output=True, text=True, cwd=self.standard_dir)
        msg = (p.stdout + p.stderr).strip().splitlines()
        msg = " ".join(l.strip() for l in msg if not l.strip().startswith("at "))[-500:]
        if p.returncode != 0:
            rv = str(self.raw.get("cdh_schema_version") or "")
            if tooling and rv and rv != tooling:
                self.rep.add("INFO", "/", "schema", f"record is {rv}; validate-yaml.js is {tooling} — schema check not applicable until the record is migrated",
                             rv, tooling, hint="see 'Moving a v0.3.0 record to v0.4.1' in the cdh-metadata skill")
            else:
                self.rep.add("HIGH", "/", "schema", "validate-yaml.js failed", observed=msg, hint="fix schema errors first")
        else:
            self.rep.add("INFO", "/", "schema", f"validate-yaml.js ({tooling or '?'}): ok")

    # ---------- identity / dates
    def check_identity(self):
        rid = self.raw.get("id")
        if not rid or not re.match(r"^[a-z0-9][a-z0-9-]*$", str(rid)):
            self.rep.add("HIGH", "/id", "id", "id missing or not a lowercase-kebab slug", rid)
        if rid and self.path.stem not in (rid, f"{rid}-{self.raw.get('version')}"):
            self.rep.add("LOW", "/id", "id-filename", "file name does not match id", rid, self.path.name)
        if not self.raw.get("version"):
            self.rep.add("HIGH" if str(self.raw.get("cdh_schema_version", "")).startswith("v0.4") else "LOW", "/version", "version",
                         "version missing (required from v0.4.0)")
        if not self.raw.get("cdh_schema_version"):
            self.rep.add("HIGH", "/cdh_schema_version", "schema-version", "cdh_schema_version missing")

    def check_dates(self):
        today = dt.date.today().isoformat()
        c, u = self.raw.get("created"), self.raw.get("updated")
        for k, v in (("created", c), ("updated", u)):
            if v is None:
                self.rep.add("MED" if str(self.raw.get("cdh_schema_version", "")).startswith("v0.4") else "LOW", f"/{k}", "dates", f"{k} missing")
            elif str(v) > today:
                self.rep.add("HIGH", f"/{k}", "dates", f"{k} is in the future", str(v), today)
        if c and u and str(u) < str(c):
            self.rep.add("HIGH", "/updated", "dates", "updated earlier than created", str(u), str(c))
        for i, st in enumerate(self.raw.get("processing", []) or []):
            if st.get("date") and u and str(st["date"]) > str(u):
                self.rep.add("MED", f"/processing/{i}/date", "dates", "processing step dated after `updated`", st["date"], u)

    # ---------- licence
    def check_license(self):
        lic = self.raw.get("license")
        if not lic:
            self.rep.add("HIGH", "/license", "license", "license missing")
            return
        ids = [t for t in re.split(r"\s+(?:AND|OR|WITH)\s+|[()]", str(lic)) if t]
        spdx = self._spdx()
        if spdx:
            for t in ids:
                if t not in spdx and not t.startswith("LicenseRef-"):
                    self.rep.add("HIGH", "/license", "license-spdx", "not a known SPDX id (or LicenseRef-)", t, hint="e.g. CC-BY-4.0, CC0-1.0, CC-BY-NC-SA-3.0-IGO")
        # licence vs provider page: look for CC tokens in the citation/landing page
        urls = [self.raw.get("citation", {}).get("url")] + [l.get("url") for l in self.raw.get("additional_links", []) or []]
        urls = [x for x in urls if x and self.remote]
        if urls:
            page = self._get_text(urls[0])
            if page:
                found = set(re.findall(r"\b(CC[- ]?BY(?:[- ]?(?:NC|SA|ND))*(?:[- ]?\d\.\d)?(?:[- ]?IGO)?|CC0(?:[- ]?1\.0)?|public domain|ODbL|MIT License|Apache(?: License)? 2\.0|AGPL|GPL)\b", page, re.I))
                if found:
                    norm = {f.upper().replace(" ", "-") for f in found}
                    lic_u = str(lic).upper()
                    tag = lic_u.replace("-4.0", "").replace("-3.0", "").replace("-1.0", "")
                    if not any(tag.split("-IGO")[0] in n for n in norm) and "LICENSEREF" not in lic_u:
                        self.rep.add("MED", "/license", "license-vs-page", "licence strings on the provider page do not mention the declared licence — verify",
                                     lic, sorted(norm)[:6], hint=f"read {urls[0]}")
        access = self.raw.get("access", "public")
        if access != "public" and not self.raw.get("access_note"):
            self.rep.add("HIGH", "/access_note", "access", "access is restricted/non-public but access_note is missing", access)

    def _spdx(self) -> set[str] | None:
        if not self.remote:
            return None
        if not hasattr(self, "_spdx_cache"):
            try:
                r = self.s.get("https://spdx.org/licenses/licenses.json", timeout=TIMEOUT)
                self._spdx_cache = {x["licenseId"] for x in r.json()["licenses"]}
            except Exception:  # noqa: BLE001
                self._spdx_cache = None
        return self._spdx_cache

    def _get_text(self, url: str) -> str | None:
        try:
            r = self.s.get(http_url(url), timeout=TIMEOUT)
            if r.status_code != 200:
                return None
            t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", r.text, flags=re.S)
            return re.sub(r"<[^>]+>", " ", t)[:400_000]
        except requests.RequestException:
            return None

    # ---------- contacts
    def check_contacts(self):
        cs = self.raw.get("contact", []) or []
        roles = {r for c in cs for r in (c.get("roles") or [])}
        v04 = str(self.raw.get("cdh_schema_version", "")).startswith("v0.4")
        if "licensor" not in roles:
            self.rep.add("HIGH", "/contact", "contacts", "no contact with role licensor")
        if v04 and "maintainer" not in roles:
            self.rep.add("HIGH", "/contact", "contacts", "no contact with role maintainer (required from v0.4.0)")
        if "custodian" in roles and v04:
            self.rep.add("MED", "/contact", "contacts", "role custodian was renamed maintainer in v0.4.0")
        for i, c in enumerate(cs):
            if c.get("name") and not c.get("organization"):
                self.rep.add("MED", f"/contact/{i}", "contacts", "person-level contact without organization", c.get("name"))
            em = c.get("email")
            if em and not re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", str(em), re.I):
                self.rep.add("MED", f"/contact/{i}/email", "contacts", "email does not look valid", em)
            for k in ("orcid", "ror"):
                if c.get(k) and not str(c[k]).startswith(f"https://{k}.org/"):
                    self.rep.add("LOW", f"/contact/{i}/{k}", "contacts", f"{k} must be a full https://{k}.org/ URL", c[k])

    # ---------- citation / DOI
    def check_citation(self):
        doi = self.raw.get("doi")
        cit = self.raw.get("citation") or {}
        if not doi and not cit:
            self.rep.add("HIGH", "/citation", "citation", "neither doi nor citation present")
            return
        if cit and str(self.raw.get("cdh_schema_version", "")).startswith("v0.4"):
            for i, a in enumerate(cit.get("authors", []) or []):
                if isinstance(a, str):
                    self.rep.add("HIGH", f"/citation/authors/{i}", "citation", "author must be an object {family, given?} or {organization} in v0.4", a)
        if doi and self.remote:
            d = str(doi).replace("https://doi.org/", "")
            try:
                r = self.s.get(f"https://api.crossref.org/works/{d}", timeout=TIMEOUT)
                if r.status_code == 404:
                    r2 = self.s.head(f"https://doi.org/{d}", allow_redirects=True, timeout=TIMEOUT)
                    if r2.status_code >= 400:
                        self.rep.add("HIGH", "/doi", "doi", "DOI does not resolve", d, r2.status_code)
                    else:
                        self.rep.add("INFO", "/doi", "doi", "DOI resolves but is not in Crossref (DataCite?) — title not cross-checked", d)
                    return
                if r.status_code != 200:
                    self.rep.add("INFO", "/doi", "doi", f"Crossref returned {r.status_code}", d)
                    return
                m = r.json()["message"]
                xt = (m.get("title") or [""])[0]
                rt = cit.get("title") or self.raw.get("title") or ""
                ratio = difflib.SequenceMatcher(None, xt.lower(), rt.lower()).ratio()
                if xt and ratio < 0.55:
                    self.rep.add("HIGH", "/doi", "doi-title", "Crossref title for this DOI does not match the citation/record title", rt, xt,
                                 hint="the DOI may point at a different work (e.g. a paper about the data, not the data)")
                xy = str((m.get("issued") or {}).get("date-parts", [[None]])[0][0])
                if cit.get("date") and xy and xy not in str(cit["date"]):
                    self.rep.add("MED", "/citation/date", "doi-year", "citation year differs from Crossref issued year", cit["date"], xy)
                xa = [a.get("family", "") for a in m.get("author", [])][:3]
                ra = [a.get("family") if isinstance(a, dict) else str(a).split(",")[0] for a in (cit.get("authors") or [])][:3]
                if xa and ra and not any(a and a.lower() in " ".join(ra).lower() for a in xa):
                    self.rep.add("MED", "/citation/authors", "doi-authors", "none of the first Crossref authors appear in the citation", ra, xa)
            except requests.RequestException as e:
                self.rep.add("INFO", "/doi", "doi", f"Crossref unreachable: {e.__class__.__name__}")

    # ---------- geography vocab
    def check_geography(self):
        geo = (self.raw.get("spatial") or {}).get("geography") or []
        if not geo:
            return
        if not self.remote:
            self.rep.add("INFO", "/spatial/geography", "geography", "vocab not checked (offline)")
            return
        try:
            v = self.s.get(f"{STD_RAW}/vocab/geography.json", timeout=TIMEOUT).json()
            ids = {c["id"] for c in v["concepts"]}
            parents = {c["id"]: set(c.get("parents", [])) for c in v["concepts"]}
        except Exception as e:  # noqa: BLE001
            self.rep.add("INFO", "/spatial/geography", "geography", f"vocab fetch failed: {e.__class__.__name__}")
            return
        for g in geo:
            if g not in ids:
                self.rep.add("HIGH", "/spatial/geography", "geography-vocab", "id not in vocab/geography.json", g)
        for g in geo:
            for h in geo:
                if g != h and h in parents.get(g, set()):
                    self.rep.add("LOW", "/spatial/geography", "geography-redundant", f"{g} is already covered by {h}", g, h)

    # ---------- links
    def check_links(self):
        if not self.remote:
            self.rep.add("INFO", "/", "links", "links not checked (offline)")
            return
        seen = {}
        for path, url in walk_urls(self.raw):
            blocking = any(path.startswith(p) for p in ("/data", "/citation/url", "/doi", "/processing", "/extensions", "/file_index")) or "/derived_from" in path or "/code/" in path
            if url.endswith("/") and path.startswith("/data"):
                continue  # prefixes are checked by check_assets
            if url not in seen:
                seen[url] = probe(url, self.s)
                self.rep.checked_urls += 1
            p = seen[url]
            if p["error"] or (p["status"] or 0) >= 400:
                sev = "HIGH" if blocking else "MED"
                if p["status"] in (401, 403) and not blocking:
                    sev = "LOW"
                self.rep.add(sev, path, "link", f"URL unreachable ({p['error'] or p['status']})", url,
                             hint="bot-blocked hosts (403) need a browser check; drop URLs you cannot source")
        for i, ext in enumerate(self.raw.get("extensions", []) or []):
            m = re.search(r"/v(\d+\.\d+\.\d+)/", ext)
            if m and self.raw.get("cdh_schema_version") and m.group(1) != str(self.raw["cdh_schema_version"]).lstrip("v"):
                self.rep.add("HIGH", f"/extensions/{i}", "extensions-version", "extension URL version differs from cdh_schema_version", ext, self.raw["cdh_schema_version"])

    # ---------- assets
    def check_assets(self):
        data = self.raw.get("data", []) or []
        if not data:
            self.rep.add("HIGH", "/data", "assets", "no data assets")
            return
        names = [d.get("name") for d in data] + [a.get("name") for a in self.raw.get("additional_assets", []) or []]
        dups = {n for n in names if names.count(n) > 1}
        if dups:
            self.rep.add("HIGH", "/data", "assets-names", "duplicate asset names", sorted(dups))
        for i, d in enumerate(data):
            p = f"/data/{i}"
            locs = [l.get("url") for l in d.get("locations", []) or [] if l.get("url")]
            if not locs and not d.get("file_index"):
                self.rep.add("HIGH" if self.raw.get("access", "public") == "public" else "LOW", p, "assets", "asset has no location url", d.get("name"))
                continue
            if not d.get("media_type"):
                self.rep.add("LOW", f"{p}/media_type", "assets", "media_type missing")
            if not self.remote:
                continue
            url = locs[0] if locs else None
            mt = (d.get("media_type") or "").lower()
            # 1) existence / size
            if url and (not url.endswith("/") or url.rstrip("/").endswith(".zarr")) and not d.get("href_template"):
                pr = probe(url, self.s)
                self.rep.checked_urls += 1
                if pr["error"] or (pr["status"] or 0) >= 400:
                    self.rep.add("HIGH", f"{p}/locations/0", "asset-url", f"primary data location unreachable ({pr['error'] or pr['status']})", url)
                    continue
                want = parse_size(d.get("file_size"))
                if want and pr["length"] and abs(pr["length"] - want) / max(want, 1) > 0.05:
                    self.rep.add("MED", f"{p}/file_size", "asset-size", "file_size differs from Content-Length by >5%", d.get("file_size"), f"{pr['length']} B")
                if mt and pr["content_type"] and mt.split(";")[0] not in pr["content_type"] and pr["content_type"] not in ("application/octet-stream", "binary/octet-stream", ""):
                    self.rep.add("LOW", f"{p}/media_type", "asset-media-type", "declared media_type differs from served Content-Type", mt, pr["content_type"])
            # 2) prefix + template / index
            if url and url.endswith("/") and not d.get("href_template") and not d.get("file_index"):
                keys = s3_list(url, self.s, 5)
                if keys is None:
                    self.rep.add("MED", f"{p}/locations/0", "asset-prefix", "prefix location without href_template or file_index — cannot verify contents", url)
                elif not keys:
                    self.rep.add("HIGH", f"{p}/locations/0", "asset-prefix", "prefix is empty", url)
            if d.get("href_template") and url:
                self._check_template(p, d, url)
            for j, fi in enumerate(d.get("file_index", []) or []):
                self._check_file_index(f"{p}/file_index/{j}", fi)
            # 3) open the asset
            self._inspect(p, d, url, mt)

    def _expand_template(self, template: str, d: dict) -> list[str]:
        st = self._structures_for(d)
        dims = {}
        for s in st:
            for dim in s.get("dimensions", []) or []:
                vals = dim.get("values") or [c.get("value") for c in dim.get("categories", []) or []]
                if not vals and dim.get("extent") and dim.get("type") == "temporal":
                    vals = list(dim["extent"])
                if vals:
                    dims[dim["name"]] = [str(v) for v in vals]
            if "{variable}" in template:
                dims["variable"] = [v["name"] for v in s.get("variables", []) or []]
        tokens = re.findall(r"\{([a-zA-Z0-9_]+)(?::[^}]*)?\}", template)
        if any(t not in dims for t in tokens):
            return []
        out = [template]
        for t in tokens:
            vals = dims[t]
            pick = sorted({vals[0], vals[-1]} | ({vals[len(vals) // 2]} if len(vals) > 2 else set()), key=vals.index)
            out = [re.sub(r"\{%s(?::[^}]*)?\}" % t, v, o) for o in out for v in pick]
        return out[: self.max_template]

    def _check_template(self, p, d, base):
        urls = self._expand_template(d["href_template"], d)
        if not urls:
            self.rep.add("MED", f"{p}/href_template", "template", "could not expand href_template from the structure's dimension values/categories", d["href_template"])
            return
        bad = []
        for u in urls:
            full = base.rstrip("/") + "/" + u if not u.startswith(("http", "s3://")) else u
            pr = probe(full, self.s)
            self.rep.checked_urls += 1
            if pr["error"] or (pr["status"] or 0) >= 400:
                bad.append((u, pr["error"] or pr["status"]))
        if bad:
            self.rep.add("HIGH", f"{p}/href_template", "template-expansion", f"{len(bad)}/{len(urls)} sampled template expansions do not exist", d["href_template"], bad[:4],
                         hint="dimension values and file names disagree (case, spelling, order)")
        else:
            self.rep.add("INFO", f"{p}/href_template", "template-expansion", f"{len(urls)} sampled expansions exist")

    def _check_file_index(self, p, fi):
        loc = next((l.get("url") for l in fi.get("locations", []) or [] if l.get("url")), None)
        if not loc:
            return
        if fi.get("format") == "cdh-inventory":
            try:
                url = loc if re.match(r"^(https?|s3)://", loc) else str(self.path.parent / loc)
                txt = self.s.get(http_url(url), timeout=TIMEOUT).text if url.startswith("http") else Path(url).read_text()
                lines = [l for l in txt.splitlines() if l.strip()]
                head = lines[0].split(",") if lines else []
                if "url" not in [h.strip().lower() for h in head]:
                    self.rep.add("HIGH", p, "file-index", "cdh-inventory has no `url` column", head)
                for row in lines[1:4]:
                    u = row.split(",")[[h.strip().lower() for h in head].index("url")].strip()
                    pr = probe(u, self.s)
                    if pr["error"] or (pr["status"] or 0) >= 400:
                        self.rep.add("HIGH", p, "file-index", "inventory row URL unreachable", u, pr["error"] or pr["status"])
            except Exception as e:  # noqa: BLE001
                self.rep.add("MED", p, "file-index", f"could not read inventory: {e.__class__.__name__}", loc)
        else:
            pr = probe(loc, self.s)
            if pr["error"] or (pr["status"] or 0) >= 400:
                self.rep.add("HIGH", p, "file-index", "index file unreachable", loc, pr["error"] or pr["status"])

    def _inspect(self, p, d, url, mt):
        if not url:
            return
        try:
            if "zarr" in mt or url.rstrip("/").endswith(".zarr"):
                info = inspect_zarr(url)
            elif "tiff" in mt or url.lower().endswith((".tif", ".tiff")) or d.get("href_template", "").lower().endswith((".tif", ".tiff")):
                target = url
                if d.get("href_template"):
                    ex = self._expand_template(d["href_template"], d)
                    if not ex:
                        return
                    target = url.rstrip("/") + "/" + ex[0]
                info = inspect_raster(target)
                info["sample_url"] = target
            elif "parquet" in mt or url.lower().endswith(".parquet"):
                want = []
                for s in self._structures_for(d):
                    want += [x["name"] for x in s.get("dimensions", []) or []]
                    want += [v["name"] for v in s.get("variables", []) or [] if v.get("categories")]
                info = inspect_parquet(url, want)
            elif "json" in mt or "csv" in mt or url.startswith("http") and ("api" in url or "?" in url):
                info = inspect_api(url, self.s)
                if info["status"] >= 400:
                    self.rep.add("HIGH", f"{p}/locations/0", "api", f"endpoint returned {info['status']}", url)
                elif mt and mt.split(";")[0] not in info["content_type"]:
                    self.rep.add("MED", f"{p}/media_type", "api-media-type", "endpoint Content-Type differs from media_type", mt, info["content_type"])
            else:
                self.rep.add("INFO", p, "inspect", f"no inspector for media_type '{mt}' — contents not verified", url)
                return
            self.observed[d.get("name") or p] = info
            self.rep.assets_inspected += 1
        except ImportError as e:
            self.rep.add("INFO", p, "inspect", f"library missing, asset not opened: {e}", url, hint="pip install rasterio / zarr xarray / duckdb")
        except Exception as e:  # noqa: BLE001
            self.rep.add("MED", p, "inspect", f"could not open asset: {e.__class__.__name__}: {str(e)[:120]}", url)

    def _structures_for(self, d: dict) -> list[dict]:
        sts = self.rec.get("structures", []) or []
        if d.get("structures"):
            return [s for s in sts if s.get("name") in d["structures"]]
        return sts

    # ---------- structures vs observed
    def check_structures_vs_assets(self):
        for i, d in enumerate(self.raw.get("data", []) or []):
            info = self.observed.get(d.get("name") or f"/data/{i}")
            if not info:
                continue
            p = f"/data/{i}"
            for s in self._structures_for(d):
                sp = f"/structures[{s.get('name')}]"
                vars_ = s.get("variables", []) or []
                dims = s.get("dimensions", []) or []
                if info["kind"] == "zarr":
                    obs = info["variables"]
                    decl = {v["name"] for v in vars_}
                    tmpl_vars = "{variable}" in (d.get("href_template") or "")
                    for v in vars_:
                        if v["name"] not in obs:
                            self.rep.add("HIGH", f"{sp}/variables/{v['name']}", "variable-missing", "declared variable is not an array in the Zarr store", v["name"], sorted(obs)[:12],
                                         hint="names must be the stored array names; a per-species store has one array per species")
                        else:
                            o = obs[v["name"]]
                            if not dtype_compatible(v.get("data_type"), o["dtype"]):
                                self.rep.add("MED", f"{sp}/variables/{v['name']}/data_type", "variable-dtype", "declared dtype differs from stored", v.get("data_type"), o["dtype"])
                            nd = asset_nodata(d, v)
                            if nd is not None and o.get("nodata") is not None and not nan_eq(nd, o["nodata"]):
                                self.rep.add("MED", f"{sp}/variables/{v['name']}/nodata", "variable-nodata", "declared nodata differs from stored _FillValue", nd, o["nodata"])
                            if v.get("unit") and o.get("units") and str(v["unit"]).replace(" ", "") != str(o["units"]).replace(" ", ""):
                                self.rep.add("LOW", f"{sp}/variables/{v['name']}/unit", "variable-unit", "declared unit differs from stored units attr", v["unit"], o["units"])
                    undeclared = [n for n in obs if n not in decl and n not in CRS_VARS]
                    if undeclared and not tmpl_vars:
                        self.rep.add("MED", f"{sp}/variables", "variable-undeclared", f"{len(undeclared)} array(s) in the store are not described by any variable", None, undeclared,
                                     hint="one variable per stored array (e.g. per species), or a {variable} template")
                    for dim in dims:
                        if dim.get("type") in ("xy", "x", "y"):
                            continue
                        if dim["name"] not in info["dims"] and dim["name"] not in info["coords"]:
                            self.rep.add("MED", f"{sp}/dimensions/{dim['name']}", "dimension-missing", "declared dimension is not a dimension/coordinate of the store", dim["name"], sorted(info["dims"]))
                        elif dim.get("values") and info["coords"].get(dim["name"], {}).get("values") is not None:
                            ov = info["coords"][dim["name"]]["values"]
                            miss = [v for v in map(str, dim["values"]) if v not in ov]
                            extra = [v for v in ov if v not in map(str, dim["values"])]
                            if miss or extra:
                                self.rep.add("HIGH", f"{sp}/dimensions/{dim['name']}/values", "dimension-values", "declared values differ from stored coordinate values",
                                             dim["values"], {"missing_in_store": miss, "not_declared": extra})
                elif info["kind"] == "raster":
                    if vars_ and info["count"] == 1 and len(vars_) > 1 and not d.get("href_template"):
                        self.rep.add("MED", f"{sp}/variables", "variable-count", f"{len(vars_)} variables declared but the file has one band and no href_template", [v["name"] for v in vars_])
                    for v in vars_[:1] if info["count"] == 1 else vars_:
                        if not dtype_compatible(v.get("data_type"), info["dtypes"][0]):
                            self.rep.add("MED", f"{sp}/variables/{v['name']}/data_type", "variable-dtype", "declared dtype differs from raster dtype", v.get("data_type"), info["dtypes"][0])
                        nd = asset_nodata(d, v)
                        if nd is not None and info.get("nodata") is not None and not nan_eq(nd, info["nodata"]):
                            self.rep.add("MED", f"{sp}/variables/{v['name']}/nodata", "variable-nodata", "declared nodata differs from raster nodata", nd, info["nodata"])
                        cats = v.get("categories")
                        if cats and info.get("observed_values") is not None:
                            declared = {int(c["value"]) for c in cats if str(c.get("value", "")).lstrip("-").isdigit()}
                            nod = info.get("nodata")
                            obs = {x for x in info["observed_values"] if nod is None or not nan_eq(x, nod)}
                            undeclared = sorted(obs - declared)
                            if undeclared:
                                self.rep.add("HIGH", f"{sp}/variables/{v['name']}/categories", "categories-coverage", "values present in the raster have no category", sorted(declared), undeclared)
                    if "cloud-optimized" in (d.get("media_type") or "") and info.get("layout") != "COG":
                        self.rep.add("MED", f"{p}/media_type", "cog-layout", "media_type claims cloud-optimized but GDAL reports no COG layout", d.get("media_type"), info.get("layout"))
                    for dim in dims:
                        if dim.get("type") in ("xy", "x", "y") and dim.get("step") is not None:
                            o = info["res"][0] if dim["type"] in ("xy", "x") else info["res"][1]
                            if not math.isclose(float(dim["step"]), o, rel_tol=2e-3):
                                self.rep.add("HIGH", f"{sp}/dimensions/{dim['name']}/step", "grid-step", "declared grid step differs from raster pixel size", dim["step"], o)
                elif info["kind"] == "parquet":
                    cols = info["columns"]
                    for v in vars_:
                        if v["name"] not in cols:
                            self.rep.add("HIGH", f"{sp}/variables/{v['name']}", "variable-missing", "declared variable is not a column", v["name"], sorted(cols)[:20])
                        elif not dtype_compatible(v.get("data_type"), cols[v["name"]]):
                            self.rep.add("MED", f"{sp}/variables/{v['name']}/data_type", "variable-dtype", "declared dtype differs from column type", v.get("data_type"), cols[v["name"]])
                        cats = v.get("categories")
                        if cats and v["name"] in info["samples"]:
                            declared = {str(c.get("value")) for c in cats}
                            undeclared = sorted({str(x) for x in info["samples"][v["name"]] if x is not None} - declared)
                            if undeclared:
                                self.rep.add("HIGH", f"{sp}/variables/{v['name']}/categories", "categories-coverage", "column holds values with no category", sorted(declared)[:12], undeclared[:12])
                    for dim in dims:
                        if dim.get("type") in ("xy", "x", "y") and dim.get("_from_resolution"):
                            continue
                        if dim["name"] not in cols:
                            self.rep.add("HIGH", f"{sp}/dimensions/{dim['name']}", "dimension-missing", "declared dimension is not a column", dim["name"], sorted(cols)[:20])
                        elif dim.get("values") and dim["name"] in info["samples"]:
                            obs = {str(x) for x in info["samples"][dim["name"]] if x is not None}
                            miss = [v for v in map(str, dim["values"]) if v not in obs]
                            extra = sorted(obs - set(map(str, dim["values"])))
                            if miss or extra:
                                self.rep.add("HIGH", f"{sp}/dimensions/{dim['name']}/values", "dimension-values", "declared values differ from the column's distinct values", dim["values"], {"missing": miss[:10], "not_declared": extra[:10]})
                    gc = s.get("geometry_column")
                    if gc and gc not in cols:
                        self.rep.add("HIGH", f"{sp}/geometry_column", "geometry-column", "geometry_column is not a column", gc, sorted(cols)[:20])
                    declared = {v["name"] for v in vars_} | {x["name"] for x in dims} | ({gc} if gc else set())
                    extra_cols = [c for c in cols if c not in declared and c not in ("geometry", "bbox")]
                    if extra_cols and (vars_ or dims):
                        self.rep.add("LOW", f"{sp}", "columns-undeclared", "columns in the table not described in the structure", None, extra_cols[:15])
                # unit presence
                for v in vars_:
                    if norm_dtype(v.get("data_type")) in NUMERIC and not v.get("unit") and not v.get("categories"):
                        self.rep.add("LOW", f"{sp}/variables/{v['name']}/unit", "variable-unit", "numeric variable without a unit (use '1' for dimensionless)", v["name"])

    # ---------- spatial / temporal vs observed
    def check_spatial(self):
        sp = self.raw.get("spatial") or {}
        bbox = sp.get("bbox")
        if bbox and isinstance(bbox[0], (int, float)):
            w, s_, e, n = bbox
            if not (-180 <= w <= 180 and -180 <= e <= 180 and -90 <= s_ <= 90 and -90 <= n <= 90 and w < e and s_ < n):
                self.rep.add("HIGH", "/spatial/bbox", "bbox", "bbox is not [west, south, east, north] in WGS84 or is inverted", bbox)
        for name, info in self.observed.items():
            if "bbox" in info and bbox and isinstance(bbox[0], (int, float)):
                ob = info["bbox"]
                tol = max(0.05, 0.02 * max(abs(bbox[2] - bbox[0]), abs(bbox[3] - bbox[1])))
                if any(abs(a - b) > tol for a, b in zip(bbox, ob)):
                    inside = ob[0] >= bbox[0] - tol and ob[1] >= bbox[1] - tol and ob[2] <= bbox[2] + tol and ob[3] <= bbox[3] + tol
                    self.rep.add("MED" if inside else "HIGH", "/spatial/bbox", "bbox-vs-asset",
                                 "record bbox differs from the asset's extent" + (" (asset lies inside the declared box)" if inside else ""), bbox, [round(x, 4) for x in ob])
            if info.get("crs") and sp.get("crs") and info["crs"].replace(" ", "").upper() != str(sp["crs"]).replace(" ", "").upper():
                self.rep.add("HIGH", "/spatial/crs", "crs-vs-asset", "record crs differs from the asset's CRS", sp["crs"], info["crs"])
        if sp and not sp.get("crs") and any(k in self.observed for k in self.observed):
            self.rep.add("MED", "/spatial/crs", "crs", "spatial.crs missing for a geospatial record")

    def check_temporal(self):
        t = self.raw.get("temporal") or {}
        if not t:
            return
        start, end = t.get("start_date"), t.get("end_date")
        single = t.get("date")
        if single and (start or end):
            self.rep.add("HIGH", "/temporal", "temporal", "`date` and `start_date/end_date` are mutually exclusive")
        if start and end and str(end) < str(start):
            self.rep.add("HIGH", "/temporal", "temporal", "end_date before start_date", start, end)
        for name, info in self.observed.items():
            tm = info.get("time")
            if not tm:
                continue
            lo, hi = str(start or single or ""), str(end or single or "")
            if lo and tm["start"][: len(lo)] < lo[: len(tm["start"])] and tm["start"][:4] != lo[:4]:
                self.rep.add("HIGH", "/temporal/start_date", "temporal-vs-asset", "asset time axis starts before the declared start", lo, tm["start"])
            if hi and end is not None and tm["end"][:4] > str(hi)[:4]:
                self.rep.add("HIGH", "/temporal/end_date", "temporal-vs-asset", "asset time axis ends after the declared end", hi, tm["end"])
            if hi and end is not None and int(tm["end"][:4]) < int(str(hi)[:4]) - 1:
                self.rep.add("MED", "/temporal/end_date", "temporal-vs-asset", "declared end is later than the asset's last time step", hi, tm["end"])

    # ---------- foreign keys
    def check_foreign_keys(self):
        ids = self._catalog_ids()
        for s in self.rec.get("structures", []) or []:
            cols = {x["name"] for x in (s.get("dimensions", []) or [])} | {v["name"] for v in (s.get("variables", []) or [])}
            for k, fk in enumerate(s.get("foreign_keys", []) or []):
                p = f"/structures[{s.get('name')}]/foreign_keys/{k}"
                for f in fk.get("fields", []) or []:
                    if f not in cols:
                        self.rep.add("HIGH", f"{p}/fields", "fk-fields", "foreign-key field is not a dimension/variable of this structure", f, sorted(cols)[:15])
                ref = (fk.get("reference") or {})
                res = ref.get("resource")
                if not res:
                    self.rep.add("HIGH", p, "fk-reference", "foreign key has no reference.resource")
                    continue
                if not re.match(r"^(https?|s3)://", str(res)):
                    if ids is not None and res not in ids:
                        self.rep.add("HIGH", f"{p}/reference/resource", "fk-target", "referenced catalog record id does not exist in cdh-catalog", res,
                                     hint="the boundary set must be catalogued first (or reference it by absolute URL)")
                else:
                    pr = probe(res, self.s) if self.remote else {"status": None, "error": "offline"}
                    if pr["error"] or (pr["status"] or 0) >= 400:
                        self.rep.add("HIGH", f"{p}/reference/resource", "fk-target", f"referenced resource unreachable ({pr['error'] or pr['status']})", res)
                    elif str(res).lower().endswith(".parquet") and self.remote:
                        try:
                            tinfo = inspect_parquet(res)
                            for f in ref.get("fields", []) or []:
                                if f not in tinfo["columns"]:
                                    self.rep.add("HIGH", f"{p}/reference/fields", "fk-target-fields", "referenced field is not a column of the target", f, sorted(tinfo["columns"])[:15])
                        except Exception as e:  # noqa: BLE001
                            self.rep.add("INFO", p, "fk-target-fields", f"target not inspected: {e.__class__.__name__}")

    def _catalog_ids(self) -> set[str] | None:
        if self.catalog_ids is not None:
            return self.catalog_ids
        if not self.remote:
            return None
        try:
            r = self.s.get(CATALOG_API, timeout=TIMEOUT)
            self.catalog_ids = {e["name"] for e in r.json() if e.get("type") == "dir"}
        except Exception:  # noqa: BLE001
            self.catalog_ids = None
        return self.catalog_ids

    # ---------- provenance
    def check_provenance(self):
        proc = self.raw.get("processing", []) or []
        derived = any(k in (self.raw.get("title", "") + self.raw.get("description", "")).lower() for k in ("derived", "aggregat", "zonal", "redistribut", "cloud-optimi"))
        if derived and not proc:
            self.rep.add("MED", "/processing", "provenance", "record reads as a derived product but has no processing[]")
        ids = self._catalog_ids()
        for i, st in enumerate(proc):
            for j, src in enumerate(st.get("derived_from", []) or []):
                p = f"/processing/{i}/derived_from/{j}"
                if src.get("id") and src.get("url"):
                    self.rep.add("HIGH", p, "provenance", "derived_from entry has both id and url")
                if src.get("id") and ids is not None and src["id"] not in ids:
                    self.rep.add("HIGH", f"{p}/id", "provenance", "derived_from.id is not a catalog record", src["id"])
                if not src.get("version"):
                    self.rep.add("LOW", f"{p}/version", "provenance", "source version not pinned", src.get("title") or src.get("id") or src.get("url"))
            code = st.get("code") or {}
            if code.get("url") and re.search(r"<[^>]+>|example\.org|your-org", str(code["url"])):
                self.rep.add("HIGH", f"/processing/{i}/code/url", "provenance", "placeholder code URL", code["url"])
            if code.get("url") and not code.get("version"):
                self.rep.add("LOW", f"/processing/{i}/code/version", "provenance", "code version/commit not pinned", code["url"])
        if self.raw.get("parent") and ids is not None and self.raw["parent"] not in ids:
            self.rep.add("HIGH", "/parent", "parent", "parent is not a catalog record", self.raw["parent"])
        if self.raw.get("previous_version") and not self.raw.get("version"):
            self.rep.add("MED", "/previous_version", "version", "previous_version without version")

    # ---------- prose sanity
    def check_prose(self):
        desc = str(self.raw.get("description") or "")
        if len(desc) < 80:
            self.rep.add("MED", "/description", "prose", "description is very short (<80 chars)", desc)
        if re.search(r"\b(TODO|TBD|lorem|placeholder|FIXME|xxx)\b", desc, re.I) or re.search(r"<[^>]+>", desc):
            self.rep.add("HIGH", "/description", "prose", "description contains a placeholder marker")
        if re.search(r"\b(SAMPLE|FICTIONAL|NOT REAL DATA)\b", (self.raw.get("title") or "") + desc, re.I):
            self.rep.add("HIGH", "/title", "prose", "record is marked as sample/fictional")
        # numbers in prose that do not appear anywhere structured (weak heuristic → LOW)
        for n in re.findall(r"\b\d{2,}(?:\.\d+)?\b", desc)[:20]:
            if n not in json.dumps({k: v for k, v in self.raw.items() if k != "description"}, default=str) and float(n) > 1900 and float(n) < 2100 and self.raw.get("temporal"):
                t = json.dumps(self.raw.get("temporal"))
                if n not in t:
                    self.rep.add("LOW", "/description", "prose-year", "a year in the description is not in `temporal`", n, t)
                    break
        usage = (self.raw.get("cdh") or {}).get("usage") or {}
        if not usage.get("not_recommended_for"):
            self.rep.add("LOW", "/cdh/usage", "usage", "no not_recommended_for guidance — every dataset has misuse cases")


# ----------------------------------------------------------------------------- output
def to_markdown(rep: Report) -> str:
    rows = rep.sorted()
    counts = {k: sum(f.severity == k for f in rows) for k in SEV_ORDER}
    out = [f"# Verification — `{rep.id}` (v{rep.version or '?'}, schema {rep.schema_version or '?'})", "",
           f"File `{rep.record}` · {rep.checked_urls} URLs probed · {rep.assets_inspected} assets opened · "
           + " · ".join(f"**{k} {v}**" if k == "HIGH" and v else f"{k} {v}" for k, v in counts.items()), "",
           "| Sev | Path | Check | Finding | Record says | Observed | Hint |", "|---|---|---|---|---|---|---|"]
    esc = lambda x: ("" if x is None else str(x)).replace("|", "\\|").replace("\n", " ")
    for f in rows:
        out.append(f"| {f.severity} | `{esc(f.path)}` | {f.check} | {esc(f.message)} | {esc(f.record_value)} | {esc(f.observed)} | {esc(f.hint)} |")
    out += ["", "Rule (standard §4.6): nothing above is auto-fixed; an authored value wins until a person decides which side is wrong.", ""]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("record", nargs="+", help="record YAML file(s)")
    ap.add_argument("--json", help="write JSON findings here (one file → object; many → list)")
    ap.add_argument("--md", help="write Markdown report here")
    ap.add_argument("--no-remote", action="store_true", help="skip every network check")
    ap.add_argument("--catalog-ids", help="comma-separated known catalog record ids (else fetched from cdh-catalog)")
    ap.add_argument("--standard-dir", help="local clone of cdh-metadata-standard → also runs scripts/validate-yaml.js")
    ap.add_argument("--max-template", type=int, default=6)
    ap.add_argument("-q", "--quiet", action="store_true")
    a = ap.parse_args(argv)
    reports = []
    worst = 0
    for rp in a.record:
        p = Path(rp)
        try:
            v = Verifier(p, remote=not a.no_remote, catalog_ids=set(a.catalog_ids.split(",")) if a.catalog_ids else None,
                         standard_dir=Path(a.standard_dir) if a.standard_dir else None, max_template=a.max_template)
        except Exception as e:  # noqa: BLE001
            print(f"cannot read {rp}: {e}", file=sys.stderr)
            return 2
        rep = v.run()
        reports.append(rep)
        if any(f.severity == "HIGH" for f in rep.findings):
            worst = 1
        if not a.quiet:
            print(to_markdown(rep))
    if a.md:
        Path(a.md).write_text("\n\n".join(to_markdown(r) for r in reports))
    if a.json:
        payload = [{**asdict(r), "findings": [asdict(f) for f in r.sorted()]} for r in reports]
        Path(a.json).write_text(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, default=str))
    return worst


if __name__ == "__main__":
    sys.exit(main())
