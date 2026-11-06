"""Election outcomes must not be inferred from platforms, polls or advisory votes."""

from copy import deepcopy
from datetime import date

import pytest
from pydantic import ValidationError

from schema import ElectionMeasure, ElectionRace, ElectionsPayload


def evidence(statement: str = "Jordan wins the governor election.") -> dict:
    return {"statement": statement, "source_url": "https://elections.example.org/results",
            "source_title": "Election results", "captured_at": "2026-11-04"}


def race() -> dict:
    return {"id": "tx-governor-2026", "state_code": "TX", "jurisdiction": "Texas",
            "office": "Governor", "level": "governor", "election_date": "2026-11-03",
            "captured_at": "2026-11-04", "candidates": [{"name": "Jordan", "party": "Independent"}],
            "result": {"status": "reported", "winner": "Jordan", "source_type": "official",
                       "evidence": evidence()}}


def test_reported_result_is_not_certification() -> None:
    result = ElectionRace.model_validate(race()).result
    assert result.status == "reported" and result.certified_on is None


@pytest.mark.parametrize("change", [
    {"status": "unverified", "winner": "Jordan"},
    {"status": "reported", "winner": "Someone else", "evidence": evidence(), "source_type": "news"},
    {"status": "reported", "winner": "Jordan"},
    {"status": "certified", "winner": "Jordan", "evidence": evidence(), "source_type": "news", "certified_on": "2026-11-04"},
    {"status": "certified", "winner": "Jordan", "evidence": evidence(), "source_type": "official"},
])
def test_rejects_unsupported_outcomes(change: dict) -> None:
    data = race()
    data["result"] = change
    with pytest.raises(ValidationError):
        ElectionRace.model_validate(data)


def test_a_poll_cannot_be_used_as_result_evidence() -> None:
    data = race()
    data["result"]["evidence"]["published_at"] = "2026-11-02"
    with pytest.raises(ValidationError, match="Pre-election"):
        ElectionRace.model_validate(data)


def test_certified_result_needs_official_evidence_and_date() -> None:
    data = race()
    data["result"].update(status="certified", certified_on="2026-11-04")
    assert ElectionRace.model_validate(data).result.certified_on == date(2026, 11, 4)


def test_candidate_quote_needs_its_own_speaker() -> None:
    data = race()
    data["candidates"][0]["statements"] = [{**evidence("I support a pause."), "speaker": "Opponent"}]
    with pytest.raises(ValidationError, match="speaker"):
        ElectionRace.model_validate(data)


def test_unverified_race_preserves_unknown_result() -> None:
    data = race()
    data["result"] = {"status": "unverified"}
    assert ElectionRace.model_validate(data).result.winner is None


def test_comparison_uses_actual_prior_not_losing_challenger() -> None:
    data = race()
    prior = {**evidence("The current administration requires an audit."),
             "source_url": "https://example.org/prior-action"}
    data["outgoing"] = {"name": "Actual prior", "party": "Republican",
                        "evidence": evidence("Actual prior holds the office."), "statements": [prior]}
    data["candidates"].append({"name": "Losing challenger", "party": "Republican", "statements": [
        {**evidence("Approve everything."), "source_url": "https://example.org/opponent", "speaker": "Losing challenger"}]})
    data["proposed_changes"] = [{"topic": "Approval process", "summary": "Prior administration required an audit.",
                                 "source_urls": [prior["source_url"]]}]
    assert ElectionRace.model_validate(data).outgoing.statements[0].speaker is None
    data["proposed_changes"][0]["source_urls"] = ["https://example.org/opponent"]
    with pytest.raises(ValidationError, match="prior officeholder evidence"):
        ElectionRace.model_validate(data)


def test_prior_personal_statement_cannot_be_attributed_to_someone_else() -> None:
    data = race()
    data["outgoing"] = {"name": "Prior", "party": "Independent", "evidence": evidence(),
                        "statements": [{**evidence("My policy."), "speaker": "Someone else"}]}
    with pytest.raises(ValidationError, match="Officeholder statements"):
        ElectionRace.model_validate(data)


def test_unresolved_winner_cannot_have_proposed_changes() -> None:
    data = race()
    data["result"] = {"status": "unverified"}
    data["proposed_changes"] = [{"topic": "Permits", "summary": "Pause approvals.",
                                 "source_urls": ["https://example.org/source"]}]
    with pytest.raises(ValidationError, match="known winner"):
        ElectionRace.model_validate(data)


def measure() -> dict:
    data = race()
    for key in ("office", "level", "candidates"):
        data.pop(key)
    data.update(id="oh-advisory-2026", title="Advisory question", effect="advisory",
                ballot_evidence=evidence("Should the council consider a moratorium?"),
                legal_effect="Advises the council; does not change local law.",
                result={"status": "reported", "outcome": "passed", "evidence": evidence("Yes won."), "source_type": "official"})
    return data


def test_passed_advisory_vote_does_not_create_a_moratorium() -> None:
    data = measure()
    assert ElectionMeasure.model_validate(data).effect == "advisory"
    data["related_moratorium_ids"] = ["a-new-enacted-pause"]
    with pytest.raises(ValidationError, match="advisory"):
        ElectionMeasure.model_validate(data)


def test_mixed_race_and_measure_ids_must_be_unique() -> None:
    data = {"generated_at": "2026-11-04", "election_date": "2026-11-03", "calendar": evidence(),
            "races": [race()], "measures": [measure()]}
    assert len(ElectionsPayload.model_validate(data).races) == 1
    data["measures"][0]["id"] = data["races"][0]["id"]
    with pytest.raises(ValidationError, match="Duplicate"):
        ElectionsPayload.model_validate(data)


def test_cannot_duplicate_governor_contest_under_another_id() -> None:
    other = deepcopy(race())
    other["id"] = "tx-other-2026"
    with pytest.raises(ValidationError, match="one governor"):
        ElectionsPayload.model_validate({"generated_at": "2026-11-04", "election_date": "2026-11-03",
                                        "calendar": evidence(), "races": [race(), other]})


def test_related_legal_record_must_exist() -> None:
    import refresh

    payloads = {name: refresh._load_payload(name, model) for name, model in refresh.PAYLOAD_FILES.items()}
    item = race()
    item["related_moratorium_ids"] = ["missing-legal-record"]
    payloads["elections"].races = [ElectionRace.model_validate(item)]
    errors = refresh._check_cross_refs(
        payloads["companies"], payloads["claims"], payloads["projects"], payloads["responses"],
        policies=payloads["policies"], moratoriums=payloads["moratoriums"], elections=payloads["elections"],
    )
    assert any("missing-legal-record" in error for error in errors)
