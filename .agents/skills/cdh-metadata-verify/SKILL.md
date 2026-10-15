---
name: cdh-metadata-verify
description: >
  Adversarial verification of a Climate Data Hub (CDH) metadata record against the data it
  describes and the sources it cites. Use this skill whenever a CDH YAML record exists and someone
  wants to know whether it is TRUE — not just schema-valid: "check this record", "verify the
  metadata", "review this submission", "is this catalog entry correct", "QA the YAML before I
  submit it", "what's wrong with this record", or as the last step after the cdh-metadata skill
  has generated a record. Also use it to review a cdh-catalog pull request. It runs a deterministic
  script that opens every data asset and diffs it against the record, then guides a hostile
  human-style review of the fields no script can settle. It never edits the record.
---

# CDH Metadata Verify — assume every field is wrong until the data or a primary source proves it

The schema validator in `cdh-metadata-standard` answers "is this well-formed?". This skill answers
"is this **correct**?". A record can pass the schema with the wrong bounding box, a variable that
does not exist in the store, a licence the provider never granted, a DOI that points at a different
paper, or a template whose files are named the other way round. Each of those was found in the live
catalog the first time this ran.

Two halves. Run both. Report findings; **never fix the record silently** (standard §4.6: an
authored value always wins; a disagreement is reported for a person to decide).

---

## Part 1 — the deterministic script

```bash
python scripts/verify_record.py <record.yaml> [--standard-dir <clone of cdh-metadata-standard>] [--md report.md] [--json report.json]
python scripts/verify_record.py records/*/*.yaml --md catalog-review.md          # a whole catalog
python scripts/verify_record.py record.yaml --no-remote                           # offline consistency only
```

Requires `pyyaml` and `requests`. Each optional library unlocks a class of checks and its absence
is reported as `INFO`, never counted as a pass: `rasterio` (GeoTIFF/COG), `xarray` + `zarr>=3`
(Zarr v2/v3), `duckdb` (Parquet/CSV over HTTP). `--standard-dir` adds `validate-yaml.js`
(schema + cross-field rules); v0.3.0 records are reported as *not applicable* against v0.4.x
tooling rather than failed. Exit code 1 = at least one HIGH finding.

What it checks, by evidence source — full list in [references/checks.md](references/checks.md):

| Evidence | Checks |
| --- | --- |
| **The asset itself** (opened over HTTP/S3) | bbox, CRS and grid step vs `spatial` / `xy` dimension; every declared variable exists as an array/band/column; dtype, fill value, units attrs; coordinate values vs `dimensions[].values`; raster category codes present but undeclared; Parquet column holds values with no `categories`; time axis vs `temporal`; COG layout when the media type claims it; `file_size` vs Content-Length; prefix non-empty |
| **Templates and indexes** | `href_template` expanded from the structure's dimension values — first/middle/last of each axis — and each file HEAD-probed; `cdh-inventory` CSV has a `url` column and its rows resolve |
| **Every URL** | HEAD/ranged GET with retries; `s3://` converted to the public HTTPS form; a Zarr root probed via `zarr.json`/`.zmetadata`; blocking paths (`data`, `doi`, `citation.url`, `processing`, `extensions`) → HIGH, others MED/LOW (403 from bot-blocking hosts → LOW, "check in a browser") |
| **Crossref** | DOI resolves; Crossref title vs `citation.title`/`title` (similarity < 0.55 → HIGH: the DOI may describe a paper, not the data); issued year vs `citation.date`; first authors vs `citation.authors` |
| **SPDX + provider page** | every id in the `license` expression is an SPDX id or `LicenseRef-`; licence tokens found on the citation/landing page are compared with the declared licence (mismatch → MED "verify") |
| **Hub vocab + catalog** | `spatial.geography` ids exist in `vocab/geography.json`, no parent/child redundancy; `foreign_keys[].reference.resource`, `parent`, `derived_from[].id` exist in `cdh-catalog`; FK fields exist on both sides (target Parquet opened) |
| **Internal consistency** | id slug and file name; `version`/`created`/`updated` present (v0.4), ordered, not in the future; processing dates ≤ `updated`; licensor + maintainer contacts; author objects (v0.4); `date` vs `start/end` exclusive; `access_note` when not public; placeholder code URLs (`<your-org>`, `example.org`); duplicate asset names; extension URL version = `cdh_schema_version` |
| **Prose** | placeholder markers, SAMPLE/FICTIONAL flags, years in the description absent from `temporal`, missing `not_recommended_for` |

Severity: **HIGH** = a user would be misled or the asset is unusable as described (wrong extent,
missing variable, dead data URL, wrong DOI, uncatalogued codes, bad FK target). **MED** = very
likely wrong, low harm (size, dtype, fill value, undeclared column, dead secondary link). **LOW**
= polish. **INFO** = could not be checked — say so in the review; it is not a pass.

---

## Part 2 — the adversarial pass (what no script can settle)

Work through the record as a hostile reviewer with the script's report beside you. For each
item: fetch the primary source. If you cannot verify it, write **unverifiable → NEEDS REVIEW**;
never "correct" a value from memory.

**HIGH — misleads a user or the Hub takes on a liability**

- `license` is the **data** licence from the provider's terms page, not the licence of a code repo,
  a paper, or a website footer. CC-BY vs CC0 vs "public domain" are different claims; NC/ND/SA
  terms must be carried exactly (`CC-BY-NC-SA-3.0-IGO`, not `CC-BY-4.0`). For a redistribution,
  the licence of the *redistribution* must be compatible with the source's.
- `contact` roles are real: the `licensor` is the party that actually holds the rights (often the
  producer's institution, not the person who converted it); the `maintainer` has agreed to be
  accountable for the record; emails are published addresses (watch the fabrication signature:
  one author's initials + another's surname; a personal gmail with no corroboration).
- `citation` / `doi` point at the **dataset** (or its data paper), not a paper that merely used it.
  Authors, year and publisher match the landing page. `related_publications` is where the paper
  about the method goes.
- `description` makes no claim the source does not make: no invented resolutions, dates, counts,
  accuracies, coverage ("global" when it is 60°S–60°N), or method words ("bias-corrected",
  "validated") that the provider does not use.
- `processing[].derived_from` names the real inputs, with the version actually used; `code.url`
  resolves to the code that produced *these* files (commit pinned), not a placeholder.
- `structures[].variables[]` mean what they say: units are physical and correct (a density is per
  km², a total is a sum, a fraction is 0–1), direction-of-reading is stated, and a per-species /
  per-crop store is declared per array, not as one umbrella variable.
- `cdh.usage.not_recommended_for` names the real misuse cases (trend claims on a product whose
  inputs changed; station-level use of a satellite product; comparing incompatible flavours).
- Duplicate: is this the same resource as an existing record under another id or version?

**MED — wrong but low-harm**

- `title` verbatim from the provider; `version` is the provider's label (`v2r2`), not ours.
- `spatial.geography` is the coverage the data has, not the project's ambition.
- `temporal.update_frequency` and `end_date: null` only when the resource really grows.
- `keywords` are topical; controlled terms carry `scheme`+`uri` that resolve.
- `attribution` present when the provider mandates wording (Copernicus, OSM, JMP).
- `file_size` and `media_type` on every asset.

**LOW — polish**

- Names follow the data lake conventions (lowercase kebab ids, snake_case variables).
- Sidecars (`AGENTS.md`, code lists, examples) exist and are referenced with roles.

---

## Output

One severity-ranked table, script findings and adversarial findings merged, then a verdict:

```
| Sev | Path | Check | Finding | Record says | Observed / source | Fix |
```

Verdict is one of **ready to submit** (no HIGH, every MED either fixed or consciously accepted
with a reason), **needs changes** (list the HIGH items), or **cannot verify** (list what was
unreachable and who can check it). Mark anything the script reported as INFO/unchecked explicitly
as **UNVERIFIED** — silence is not a pass.

Hand the table to the author or reviewer. Do not rewrite the record; if asked to, apply only the
fixes a person has approved, one field at a time, and re-run the script.

## Reference

- Standard §4.6 (authored vs machine-derived values; disagreements are review findings) and the
  authoring guide's *What review cannot decide*:
  <https://github.com/CGIAR-Climate-Data-Hub/cdh-metadata-standard/blob/main/spec/authoring-guide.md>
- Generating a record: the `cdh-metadata` skill. Run this skill after it, before submission.
- Submission: CDH Metadata Generator → `cdh-catalog` "Submit metadata record" issue → bot PR → CODEOWNER review.
