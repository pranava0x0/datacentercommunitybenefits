"""Public map geometry, point provenance and legal-record references."""
import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

import refresh
from schema import DOESitesPayload, MapPolygon

ROOT = Path(__file__).resolve().parents[1]


def test_geometry_rejects_unclosed_out_of_range_and_non_numeric_positions() -> None:
    ring = [[-100, 35], [-99, 35], [-99, 36], [-100, 35]]
    assert MapPolygon(type="Polygon", coordinates=[ring]).coordinates == [ring]
    for bad in (ring[:-1], [[200, 35], *ring[1:]], [["-100", 35], *ring[1:]], []):
        with pytest.raises(ValidationError):
            MapPolygon(type="Polygon", coordinates=[bad])


def test_seed_geography_covers_each_eligible_record_or_names_a_gap() -> None:
    payloads = {name: refresh._load_payload(name, model) for name, model in refresh.PAYLOAD_FILES.items()}
    geography = payloads["map_geography"]
    assert not refresh._check_map_refs(geography, payloads["moratoriums"], payloads["policies"])
    mapped = {("moratorium", key) for item in geography.jurisdictions for key in item.moratorium_ids}
    mapped |= {("policy", key) for item in geography.jurisdictions for key in item.policy_ids}
    mapped |= {(item.record_kind, item.record_id) for item in geography.unmatched}
    expected = {("moratorium", item.id) for item in payloads["moratoriums"].moratoriums if item.jurisdiction_type in {"state", "county", "city"}}
    expected |= {("policy", item.id) for item in payloads["policies"].policies if item.scope in {"state", "county", "city"} and item.instrument not in {"benefit_agreement", "company_plan"}}
    assert mapped == expected
    baltimore = next(item for item in geography.jurisdictions if "baltimore-county-md-2026-09" in item.moratorium_ids)
    assert baltimore.census_geoid == "24005"  # Baltimore County, distinct from Baltimore city.
    augusta = next(item for item in geography.jurisdictions if "augusta-ga-2026-06" in item.moratorium_ids)
    assert augusta.census_geoid == "1304204"  # Municipal government, not statistical Augusta CCD.
    oneonta = next(item for item in geography.jurisdictions if "oneonta-ny-2026-05" in item.moratorium_ids)
    assert oneonta.census_geoid == "3607754892"  # Town government, not the separately incorporated city.
    highland = next(item for item in geography.jurisdictions if "highland-ny-2026" in item.moratorium_ids)
    assert highland.census_geoid.startswith("36105")  # Sullivan County, not the Ulster County hamlet.
    assert not any(" CCD" in item.name for item in geography.jurisdictions)


def test_boundary_reference_cannot_change_state_or_expand_a_project_agreement() -> None:
    payloads = {name: refresh._load_payload(name, model) for name, model in refresh.PAYLOAD_FILES.items()}
    geography = payloads["map_geography"].model_copy(deep=True)
    jurisdiction = next(item for item in geography.jurisdictions if item.policy_ids)
    jurisdiction.state_code = "ZZ"
    assert any("state/level mismatch" in error for error in refresh._check_map_refs(geography, payloads["moratoriums"], payloads["policies"]))
    agreement = next(item for item in payloads["policies"].policies if item.instrument == "benefit_agreement")
    jurisdiction.policy_ids = [agreement.id]
    assert any("not a jurisdiction-wide framework" in error for error in refresh._check_map_refs(geography, payloads["moratoriums"], payloads["policies"]))


def test_doe_roster_and_announcements_preserve_source_precision_and_status() -> None:
    raw = json.loads((ROOT / "data/seed/doe_sites.json").read_text())
    payload = DOESitesPayload.model_validate(raw)
    labs = [item for item in payload.sites if "national_lab" in item.site_types]
    assert len({item.name.split("—")[0].strip() for item in labs}) == 17
    assert sum("em_site" in item.site_types for item in payload.sites) == 16
    assert all(item.coordinate_source_url and item.location_kind for item in payload.sites)
    event = next(item for item in payload.announcements if item.id == "doe-srs-amentum-negotiations-2026")
    assert "negotiations" in event.status_text
    national = next(item for item in payload.announcements if item.id == "doe-backup-generation-fern-2026")
    assert national.site_ids == []
    invalid = deepcopy(raw)
    invalid["announcements"][0]["site_ids"] = ["invented-project-parcel"]
    with pytest.raises(ValidationError, match="unknown site"):
        DOESitesPayload.model_validate(invalid)
    invalid = deepcopy(raw)
    invalid["announcements"][0]["published_at"] = "2099-01-01"
    with pytest.raises(ValidationError, match="published after capture"):
        DOESitesPayload.model_validate(invalid)


def test_preview_data_adapter_contains_exact_emitted_json() -> None:
    for path in (ROOT / "docs/data").glob("*.json"):
        adapter = path.with_suffix(".preview.js").read_text()
        value = adapter.split('] = ', 1)[1].rstrip(';\n')
        assert json.loads(value) == path.read_text()


def test_preview_module_adapters_include_current_module_source() -> None:
    adapters = list((ROOT / "docs").glob("*.preview.js"))
    assert adapters
    for adapter in adapters:
        source = adapter.with_name(adapter.name.replace(".preview.js", ".js")).read_text()
        assert "\n" + source.replace("export function ", "function ") + "\n" in adapter.read_text(), adapter.name
