from ceda_pipeline.pipeline import run_pipeline
from ceda_pipeline.scian import load_scian_catalog


def test_run_pipeline_filters_by_year_and_geofence_and_maps_scian():
    market_rows = [
        {
            "market_id": "m1",
            "market_name": "Central",
            "address_raw": "Calle 1",
            "state": "CDMX",
            "municipality": "Iztapalapa",
            "source_page": 1,
            "source_text": "row",
        }
    ]
    denue_rows = [
        {
            "id": "1",
            "name": "Inside",
            "address": "Addr 1",
            "lat": 19.5,
            "lon": -99.5,
            "scian": "461110",
        },
        {
            "id": "2",
            "name": "Outside",
            "address": "Addr 2",
            "lat": 21.0,
            "lon": -99.5,
            "scian": "461110",
        },
    ]
    catalog = load_scian_catalog(
        [
            {"code": "46", "title": "Comercio", "level": 2, "parent_code": None},
            {"code": "461", "title": "Menor", "level": 3, "parent_code": "46"},
            {"code": "461110", "title": "Abarrotes", "level": 6, "parent_code": "461"},
        ],
        version="2023",
        version_date="2023-01-01",
    )

    result = run_pipeline(
        market_address_or_id="m1",
        year=2022,
        geofence_input={"type": "bbox", "min_lat": 19.0, "max_lat": 20.0, "min_lon": -100.0, "max_lon": -99.0},
        market_rows=market_rows,
        denue_rows=denue_rows,
        scian_catalog=catalog,
    )

    assert len(result["results"]) == 1
    assert result["results"][0]["establishment_id"] == "1"
    assert result["results"][0]["scian"]["title"] == "Abarrotes"
    assert result["quality_metrics"]["scian_mapping_coverage"] == 1.0


def test_run_pipeline_stable_schema_across_years():
    market_rows = [
        {
            "market_id": "m1",
            "market_name": "Central",
            "address_raw": "Calle 1",
            "state": "CDMX",
            "municipality": "Iztapalapa",
            "source_page": 1,
            "source_text": "row",
        }
    ]
    denue_2021 = [
        {
            "id": "1",
            "name": "Inside 2021",
            "address": "Addr 1",
            "lat": 19.5,
            "lon": -99.5,
            "scian": "461110",
        }
    ]
    denue_2022 = [
        {
            "id": "2",
            "name": "Inside 2022",
            "address": "Addr 2",
            "lat": 19.6,
            "lon": -99.6,
            "scian": "461110",
        }
    ]
    catalog = load_scian_catalog(
        [
            {"code": "46", "title": "Comercio", "level": 2, "parent_code": None},
            {"code": "461", "title": "Menor", "level": 3, "parent_code": "46"},
            {"code": "461110", "title": "Abarrotes", "level": 6, "parent_code": "461"},
        ],
        version="2023",
        version_date="2023-01-01",
    )

    base_kwargs = {
        "market_address_or_id": "m1",
        "geofence_input": {
            "type": "bbox",
            "min_lat": 19.0,
            "max_lat": 20.0,
            "min_lon": -100.0,
            "max_lon": -99.0,
        },
        "market_rows": market_rows,
        "scian_catalog": catalog,
    }
    result_2021 = run_pipeline(year=2021, denue_rows=denue_2021, **base_kwargs)
    result_2022 = run_pipeline(year=2022, denue_rows=denue_2022, **base_kwargs)

    keys_2021 = set(result_2021["results"][0].keys())
    keys_2022 = set(result_2022["results"][0].keys())
    assert keys_2021 == keys_2022
    assert result_2021["results"][0]["year"] == 2021
    assert result_2022["results"][0]["year"] == 2022
