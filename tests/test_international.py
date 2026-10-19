"""International layer (v6, notes/specs/SPEC_INTERNATIONAL.md).

Parity between the schema registries and their app.js mirrors, the
US/international partition, and the editorial rules the validators carry
(verbatim original + labelled translation, no money conversion stored,
`federal` reserved for the US). Everything derives from the registries.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import schema
from tests.test_themes_match_frontend import _extract_array, _extract_quoted_or_bare_keys

ROOT = Path(__file__).resolve().parent.parent
APP_JS = (ROOT / "docs" / "app.js").read_text(encoding="utf-8")
SEED = json.loads((ROOT / "data" / "seed" / "international.json").read_text(encoding="utf-8"))


def _js_object(name: str) -> dict[str, str]:
    m = re.search(rf"const\s+{name}\s*=\s*\{{(.*?)\}};", APP_JS, re.DOTALL)
    assert m, f"const {name} not found in app.js"
    pairs = re.findall(r'"?([A-Za-z0-9_-]+)"?\s*:\s*"((?:[^"\\]|\\.)*)"', m.group(1))
    return dict(pairs)


@pytest.mark.parametrize(
    "js_name, py",
    [
        ("COUNTRY_NAMES", schema.COUNTRIES),
        ("SUPRANATIONAL_NAMES", schema.SUPRANATIONAL),
        ("SUBDIVISION_NAMES", schema.SUBDIVISIONS),
        ("LANGUAGE_NAMES", schema.LANGUAGES),
        ("TRANSLATION_SOURCE_LABELS", schema.TRANSLATION_SOURCE_LABELS),
        ("MORATORIUM_FORMALITY_LABELS", schema.MORATORIUM_FORMALITY_LABELS),
    ],
)
def test_registry_mirrors_match(js_name: str, py: dict) -> None:
    assert _js_object(js_name) == py


@pytest.mark.parametrize(
    "js_name, py",
    [
        ("CURRENCIES", schema.CURRENCIES),
        ("EU_MEMBERS", schema.EU_MEMBERS),
        ("MORATORIUM_FORMALITIES", schema.MORATORIUM_FORMALITIES),
    ],
)
def test_vocab_arrays_match(js_name: str, py: tuple) -> None:
    assert tuple(_extract_array(APP_JS, js_name)) == py


def test_every_fx_rate_is_a_registered_currency() -> None:
    # Display-only rates; a currency may lack one (CLP/ARS aren't in G.5A).
    assert _extract_quoted_or_bare_keys(APP_JS, "FX_USD_PER_UNIT") <= set(schema.CURRENCIES)


def test_international_payload_validates() -> None:
    schema.InternationalPayload.model_validate(SEED)


def test_every_registered_country_has_a_country_record() -> None:
    """A registry entry with no Country record would be a dead filter option."""
    codes = {c["code"] for c in SEED["countries"]}
    assert codes == (set(schema.COUNTRIES) - {"US"}) | set(schema.SUPRANATIONAL)


def test_every_country_has_at_least_one_record() -> None:
    """Honest absence is fine on a page, but a wave-1 country with nothing
    verified shouldn't be advertised as covered."""
    used = {r["country"] for k in ("policies", "moratoriums", "projects", "rate_cases") for r in SEED[k]}
    empty = {c["code"] for c in SEED["countries"]} - used
    assert not empty, f"countries with no records: {sorted(empty)}"


def test_non_english_quotes_carry_a_labelled_translation() -> None:
    for c in SEED["claims"]:
        if c.get("statement_lang", "en") != "en":
            assert c["statement_translation"]["by"] in schema.TRANSLATION_SOURCES
    for p in SEED["policies"]:
        if p.get("source_lang", "en") != "en":
            assert len(p["key_terms_translation"]["items"]) == len(p["key_terms"])


def test_no_converted_money_is_stored() -> None:
    for p in SEED["projects"]:
        assert p.get("claimed_investment_usd") is None, p["id"]
    for p in SEED["policies"]:
        assert p.get("value_usd") is None, p["id"]


def _project(**over):
    base = dict(
        id="x", company_slug="google", name="X", city="Dublin", country="IE",
        status="announced", announced_year=2026, source_url="https://example.org/x",
        source_title="X", captured_at="2026-10-19",
    )
    base.update(over)
    return schema.Project.model_validate(base)


def test_partition_rejects_crossovers() -> None:
    with pytest.raises(ValidationError):
        _project(state="TX")  # non-US site with a US state
    with pytest.raises(ValidationError):
        _project(country="US")  # US site without a state
    with pytest.raises(ValidationError):
        _project(claimed_investment_usd=1)  # converted money on a non-US site
    with pytest.raises(ValidationError):
        schema.ProjectsPayload.model_validate(
            {"generated_at": "2026-10-19", "projects": [_project().model_dump(mode="json")]}
        )


def test_federal_is_us_only_and_national_is_not() -> None:
    base = dict(
        id="m", jurisdiction="Ireland", status="enacted", duration_description="1 year",
        summary="s", source_url="https://example.org/m", source_title="M", captured_at="2026-10-19",
        country="IE",
    )
    with pytest.raises(ValidationError):
        schema.Moratorium.model_validate({**base, "jurisdiction_type": "federal"})
    schema.Moratorium.model_validate({**base, "jurisdiction_type": "national"})


def test_unofficial_pause_needs_a_second_source() -> None:
    base = dict(
        id="m", jurisdiction="Singapore", jurisdiction_type="national", status="enacted",
        duration_description="2019-2022", summary="s", source_url="https://example.org/m",
        source_title="M", captured_at="2026-10-19", country="SG", formality="de_facto",
    )
    with pytest.raises(ValidationError):
        schema.Moratorium.model_validate(base)
    schema.Moratorium.model_validate(
        {**base, "resources": [{"url": "https://example.org/2", "title": "Second"}]}
    )


def test_non_english_claim_requires_translation() -> None:
    base = dict(
        id="c", company_slug="google", theme="water", statement="Hola",
        source_url="https://example.org/c", source_title="C", captured_at="2026-10-19",
        country="CL", statement_lang="es",
    )
    with pytest.raises(ValidationError):
        schema.Claim.model_validate(base)
    schema.Claim.model_validate(
        {**base, "statement_translation": {"text": "Hello", "by": "machine", "reviewed_at": "2026-10-19"}}
    )


def test_home_digest_counts_match_their_tabs() -> None:
    """Home's Companies card opens the US Companies tab, and the International
    card counts countries without double-counting the EU."""
    home = json.loads((ROOT / "docs" / "data" / "home.json").read_text())["totals"]
    companies = json.loads((ROOT / "data" / "seed" / "companies.json").read_text())["companies"]
    assert home["companies"] == sum(not c.get("international_only") for c in companies)
    assert home["international_countries"] == sum(c["code"] in schema.COUNTRIES for c in SEED["countries"])


def test_app_js_has_no_regex_lookbehind() -> None:
    """Safari < 16.4 rejects `(?<=` / `(?<!` at parse time, so one lookbehind
    anywhere takes down every tab (Sonnet review of #83)."""
    assert "(?<=" not in APP_JS and "(?<!" not in APP_JS


def _policy(**over):
    base = dict(
        id="p", title="T", instrument="regulation", status="in_effect", scope="national",
        jurisdiction="Ireland", benefit_themes=["energy"], principles=["pay_own_way"],
        key_terms=["term"], summary="s", source_url="https://example.org/p", source_title="P",
        captured_at="2026-10-19", country="IE",
    )
    base.update(over)
    return schema.Policy.model_validate(base)


def test_policy_scope_branches() -> None:
    _policy()
    with pytest.raises(ValidationError):
        _policy(scope="federal")  # federal is the US government only
    with pytest.raises(ValidationError):
        _policy(scope="state")  # sub-national abroad needs a subdivision
    _policy(scope="state", country="AU", subdivision="AU-NSW", jurisdiction="NSW")
    with pytest.raises(ValidationError):
        _policy(country="US", scope="national", state_code=None)
    with pytest.raises(ValidationError):
        _policy(country="EU", scope="national")  # EU goes with supranational
    _policy(country="EU", scope="supranational", applies_to=["IE", "FR"])
    with pytest.raises(ValidationError):
        _policy(country="EU", scope="supranational", applies_to=["US"])
    with pytest.raises(ValidationError):
        _policy(source_lang="fr")  # needs a parallel translation
    with pytest.raises(ValidationError):
        _policy(source_lang="fr", key_terms_translation={"items": ["a", "b"], "by": "machine", "reviewed_at": "2026-10-19"})
    _policy(source_lang="fr", key_terms_translation={"items": ["a"], "by": "machine", "reviewed_at": "2026-10-19"})


def test_translation_provenance() -> None:
    with pytest.raises(ValidationError):
        schema.Translation.model_validate({"text": "x", "by": "official", "reviewed_at": "2026-10-19"})
    with pytest.raises(ValidationError):
        schema.Translation.model_validate({"text": "x", "by": "human", "reviewed_at": "2026-10-19"})



def test_every_used_currency_has_a_rate_or_is_documented_rateless() -> None:
    rates = _extract_quoted_or_bare_keys(APP_JS, "FX_USD_PER_UNIT")
    rateless = {"CLP", "ARS"}  # not in Fed G.5A; shown as stated only (CLAUDE.md)
    used = {m["currency"] for k in ("projects", "policies") for r in SEED[k]
            for m in [r.get("claimed_investment") or r.get("value")] if m}
    assert used <= rates | rateless, used - rates - rateless
