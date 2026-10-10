# Data directory

Git tracks **small, curated, hard-to-regenerate files only**. Bulk downloads and
generated artifacts are gitignored — reproduce them via the source manifests or
by re-running the pipeline/notebooks.

## Layout

| Path | Tracked? | Contents |
|---|---|---|
| `ceda_iztapalapa_osm.geojson` | yes | CEDA boundary polygon (hand-curated, ~8 KB) |
| `censo_2012/` | yes | 2012 central-market directory extract (small) |
| `sources_live_check/` | yes | Reference documents used to verify sources |
| `scian/scian_source_manifest.json` | yes | Provenance for the SCIAN catalog download |
| `scian/*.xlsx` | **no** | Raw SCIAN catalog — re-download via manifest URL |
| `scian/scian_2023_processed.csv` | **no** | Processed SCIAN extract — regenerate via notebooks |
| `denue/` | **no** | Bulk DENUE extracts (~800 MB) — see `notebooks/centrales_abasto_nacional.ipynb` |
| `outputs/` | **no** | Generated CSVs, GeoJSON, HTML maps and reports |
| `sources/` | **no** | Pipeline auto-download cache (`--data-dir` default) |

## Rules of thumb

- **Commit**: manifests, codebooks, hand-edited reference data, anything under
  ~1 MB that can't be regenerated.
- **Never commit**: raw downloads, generated artifacts, caches — if a script or
  manifest can recreate it, it doesn't belong in Git.
- To force-commit a small file inside an ignored directory:
  `git add -f data/path/to/file`.
- For large files that genuinely need versioning, prefer Git LFS or GitHub
  release assets over plain commits — once a blob enters history it stays there.
