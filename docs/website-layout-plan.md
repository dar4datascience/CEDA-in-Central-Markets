# Website Layout Plan — CEDA Establishment Directory

**Goal:** a Quarto-generated static site that mirrors the structure of
<https://www.monitor.com.mx/>, populated from the pipeline outputs in
`data/outputs/` (currently `ceda_iztapalapa_denue.csv/.geojson`, ~7,278
establishments inside the CEDA Iztapalapa geofence).

---

## 1. What monitor.com.mx looks like

A three-level drill-down directory over DENUE data:

| Level | URL pattern | Content |
|---|---|---|
| Home | `/` | List of 32 states |
| State | `/{estado}/` | List of municipalities |
| Municipality | `/{estado}/{municipio}/` | List of establishments (name links only) |
| Establishment | `/{id}/{slug}/` | Detail record + "Empresas cercanas" |

Detail page fields: Nombre, Razón Social, **Actividad** (SCIAN
description), Calle, Número, Teléfono, Calles 2–4 (cross streets),
Colonia/Asentamiento, Código Postal, Localidad, Municipio, Estado,
**Personal** (employee range), Sitio Web — then 3 nearby companies.

Their "nearby" list is just sequential IDs, not real distance — we can do
better because every row has `latitud`/`longitud`.

## 2. Source data → site fields

`data/outputs/ceda_iztapalapa_denue.csv` columns map almost 1:1:

| CSV column | Site field | Notes |
|---|---|---|
| `id` | detail-page URL key `/{id}-{slug}/` | stable DENUE id |
| `nom_estab` | Nombre | slugify for URL |
| `codigo_act` / `nombre_act` | Actividad + link to SCIAN category page | already joined |
| `sector` / `sector_title` | sector browse path | our addition (monitor lacks it) |
| `per_ocu` | Personal | e.g. "0 a 5 personas" |
| `tipo_vial` `nom_vial` `numero_ext` `letra_ext` | Calle / Número | concat at build time |
| `tipo_asent` `nomb_asent` | Colonia/Asentamiento | also a browse path |
| `cod_postal` | Código Postal | float → cast to int |
| `entidad` `cve_mun` `municipio` | Estado / Municipio | hierarchy levels |
| `latitud` `longitud` | detail map + nearby calc | haversine, build-time |
| `fecha_alta` | year filter / timeline | longitudinal edge over monitor |

**Gaps vs. monitor's detail page:** `telefono`, `razon_social`, cross
streets, `localidad`, `sitio_web` are dropped by our processed output but
exist in raw `data/denue/conjunto_de_datos/denue_inegi_09_.csv`.
*Optional step:* re-join on `id` at site-build time to recover them.

## 3. Site architecture

Our data is one geofence (CEDA Iztapalapa), not the whole country, so the
top level becomes **mercado** instead of estado. Same drill-down shape:

```
/                                  Inicio: hero, headline stats, market card(s), map
/mercados/ceda-iztapalapa/         Market overview: stats, quality metrics,
                                   mini-map, links into all browse paths

Browse paths (parallel ways into the same establishments):
/mercados/ceda-iztapalapa/municipios/            list of municipalities in geofence
/mercados/ceda-iztapalapa/municipios/iztapalapa/   establishments in it
/sectores/                        SCIAN sector grid (11, 21, 43, 46, 72…)
/sectores/46/                     sector detail → its establishments
/colonias/                        colonias ranked by establishment count
/colonias/central-de-abasto/

/empresas/716678-frutas-casa-grandes/   establishment detail (monitor layout)
                                        + map + real "Empresas cercanas"

/metodologia/                     sources, geofence def, quality_metrics,
                                  DENUE/SCIAN versions + retrieval hashes
/descargas/                       CSV / GeoJSON / future parquet
/acerca-de/                       project about page
```

Rationale: municipality drill-down mirrors monitor 1:1; sector and
colonia paths are cheap additions that exploit `scian_title`/`nomb_asent`
we already carry; `fecha_alta` enables a "nuevos por año" view later.

### Detail page layout (mirrors monitor)

```
# {NOM_ESTAB}
Actividad: {nombre_act}  →  link to /sectores/{sector}/
[definitional table: Calle, Número, Colonia, CP, Localidad,
 Municipio, Estado, Personal, Teléfono*, Sitio Web*]   (* if re-joined)
[Leaflet map, single marker]
## Empresas cercanas
3 nearest by haversine distance (computed at build time)
```

## 4. Quarto project layout

> Sources live in `website/` (not `site/` — `/site` is gitignored as an
> mkdocs artifact by the Python .gitignore template).

```
website/
├── _quarto.yml                  # type: website, lang: es, navbar, theme
├── _brand.yml                   # optional brand colors/fonts
├── index.qmd                    # home
├── mercados/ceda-iztapalapa/
│   ├── index.qmd                # market overview
│   └── municipios/
│       ├── index.qmd            # listing of municipality pages
│       └── {mun}/index.qmd      # generated, one per municipality
├── sectores/index.qmd + sectores/{sector}/index.qmd   # generated
├── colonias/index.qmd + colonias/{col}/index.qmd      # generated
├── empresas/{id}-{slug}/index.qmd                   # ~7.3k generated
├── metodologia.qmd
├── descargas.qmd
└── acerca-de.qmd
```

`_quarto.yml` sketch:

```yaml
project:
  type: website
  output-dir: _site

website:
  title: "Monitor CEDA"
  lang: es
  site-url: https://<deploy-url>/
  navbar:
    left:
      - href: index.qmd            # Inicio
      - href: mercados/ceda-iztapalapa/index.qmd   # Mercado
      - href: sectores/index.qmd   # Sectores
      - href: colonias/index.qmd   # Colonias
      - href: descargas.qmd        # Datos
      - href: metodologia.qmd      # Metodología
  page-footer:
    center: "Datos: INEGI DENUE · SCIAN 2023"

format:
  html:
    theme: cosmo
    toc: false

execute:
  freeze: auto        # generated pages carry no executable code anyway
```

## 5. Build pipeline (data → site)

One Python script, run inside the existing `.venv`:

```
scripts/build_site.py
  1. read data/outputs/ceda_iztapalapa_denue.csv (+ optional raw-DENUE re-join)
  2. clean: cast cod_postal, build calle string, slugify names (unidecode)
  3. precompute per-establishment 3 nearest neighbors (scipy cKDTree /
     numpy haversine — 7.3k pts is trivial)
  4. emit .qmd files:
     - detail pages: pure markdown + `::: {=html}` blocks (no code cells,
       so Quarto renders them fast)
     - listing pages: Quarto `listing:` with `contents:` pointing at
       generated YAML metadata (fields: title, href, municipio, actividad)
     - overview pages: stats tables + embedded folium/leaflet map HTML
  5. `quarto render website/`
```

Key decision — **7.3k detail pages**: monitor has one URL per company, so
we generate one .qmd per establishment. Pure-markdown pages render
quickly; `freeze: auto` plus Quarto's incremental render keep rebuilds
cheap. If render time ever hurts, fall back to a single searchable table
(Observable JS + DataTables) for the listing level and keep detail pages.

**Maps:** folium (Python, already-`.venv`-friendly) with marker clusters
on overview pages; a single-marker leaflet embed on detail pages
(folium `save()` → include HTML).

**Search:** Quarto's built-in site search indexes every rendered page —
establishment names become findable for free.

## 6. Deployment

- `quarto publish gh-pages` (this repo) or Netlify; `_site/` is already
  covered by `.gitignore` conventions — add `site/_site/` explicitly.
- Deterministic rebuilds: same CSV in → same site out; the pipeline's
  provenance fields (retrieval hash, SCIAN version) get displayed on
  `/metodologia/` — a transparency feature monitor doesn't have.

## 7. Phases

1. **Skeleton** — `_quarto.yml`, index, metodologia, descargas stubs;
   render + deploy smoke test.
2. **Core mirror** — generator emits municipio drill-down + detail pages;
   verify against monitor.com.mx layout.
3. **Enrichment** — sector/colonia browse paths, real nearby companies,
   per-page maps.
4. **Polish** — `_brand.yml`, search tuning, `fecha_alta` year views,
   optional raw-DENUE re-join for teléfono/sitio web.

## 8. Open decisions

- **Scope:** site grows to other centrales de abasto later? The
  `/mercados/{slug}/` layer already anticipates that — home becomes a
  market grid (exactly like monitor's state grid).
- **Multi-year:** when a second DENUE year lands, decide between
  year-suffixed detail pages vs. a year switcher on each page.
- **URL scheme:** `/{id}-{slug}/` shown above; if you want literal parity
  with monitor (`/{id}/{slug}/`), emit nested dirs instead — trivial
  generator change.
