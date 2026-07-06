"""Tests for the refresh.py driver — validation, cross-ref checking, output write."""

from __future__ import annotations

import json
import shutil
from datetime import date, timedelta
from pathlib import Path

import pytest

import refresh
from schema import Moratorium, MoratoriumsPayload, Tariff, TariffsPayload

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed"


def _copy_seed(tmp_path: Path) -> Path:
    """Copy the real seed into a tmp dir so we can mutate it without affecting the repo.

    Must mirror every payload refresh.py validates (refresh.PAYLOAD_FILES) — the
    driver iterates all of them and raises FileNotFoundError on any missing seed.
    Kept in sync as new payloads land (moratoriums v1.16, tariffs v1.17)."""
    dst = tmp_path / "data" / "seed"
    dst.mkdir(parents=True)
    for name in (
        "companies.json",
        "claims.json",
        "projects.json",
        "responses.json",
        "moratoriums.json",
        "tariffs.json",
    ):
        shutil.copyfile(SEED / name, dst / name)
    return dst


def _redirect_paths(monkeypatch, seed_dir: Path, out_dir: Path) -> None:
    monkeypatch.setattr(refresh, "SEED_DIR", seed_dir)
    monkeypatch.setattr(refresh, "OUT_DIR", out_dir)


class TestRefreshHappyPath:
    def test_check_only_returns_zero(self, tmp_path, monkeypatch):
        seed = _copy_seed(tmp_path)
        out = tmp_path / "docs" / "data"
        _redirect_paths(monkeypatch, seed, out)
        rc = refresh.refresh(check_only=True)
        assert rc == 0
        assert not out.exists() or not any(out.iterdir())

    def test_writes_four_payloads(self, tmp_path, monkeypatch):
        seed = _copy_seed(tmp_path)
        out = tmp_path / "docs" / "data"
        _redirect_paths(monkeypatch, seed, out)
        rc = refresh.refresh(pretty=True)
        assert rc == 0
        for name in ("companies", "claims", "projects", "responses"):
            assert (out / f"{name}.json").exists()

    def test_pretty_flag_indents(self, tmp_path, monkeypatch):
        seed = _copy_seed(tmp_path)
        out = tmp_path / "docs" / "data"
        _redirect_paths(monkeypatch, seed, out)
        refresh.refresh(pretty=True)
        text = (out / "companies.json").read_text()
        assert "\n  " in text, "pretty mode should produce indented JSON"

    def test_minified_flag_default(self, tmp_path, monkeypatch):
        seed = _copy_seed(tmp_path)
        out = tmp_path / "docs" / "data"
        _redirect_paths(monkeypatch, seed, out)
        refresh.refresh(pretty=False)
        text = (out / "companies.json").read_text()
        assert "\n  " not in text


class TestCrossRefDetection:
    def test_unknown_company_in_claim_fails(self, tmp_path, monkeypatch):
        seed = _copy_seed(tmp_path)
        path = seed / "claims.json"
        data = json.loads(path.read_text())
        # Mutate the first claim's company_slug to a non-existent slug — but
        # one that's still in the COMPANY_SLUGS Literal so Pydantic accepts it,
        # then we delete that company from companies.json.
        data["claims"][0]["company_slug"] = "anthropic"
        path.write_text(json.dumps(data))
        co_path = seed / "companies.json"
        co = json.loads(co_path.read_text())
        co["companies"] = [c for c in co["companies"] if c["slug"] != "anthropic"]
        co_path.write_text(json.dumps(co))

        out = tmp_path / "docs" / "data"
        _redirect_paths(monkeypatch, seed, out)
        rc = refresh.refresh(check_only=True)
        assert rc == 1, "Should fail when claim references missing company"

    def test_unknown_project_in_response_fails(self, tmp_path, monkeypatch):
        seed = _copy_seed(tmp_path)
        path = seed / "responses.json"
        data = json.loads(path.read_text())
        data["responses"][0]["project_id"] = "ghost-project-not-exist"
        path.write_text(json.dumps(data))

        out = tmp_path / "docs" / "data"
        _redirect_paths(monkeypatch, seed, out)
        rc = refresh.refresh(check_only=True)
        assert rc == 1


class TestValidationErrors:
    def test_invalid_seed_raises(self, tmp_path, monkeypatch):
        seed = _copy_seed(tmp_path)
        # Inject an invalid theme into a claim — Pydantic should reject.
        path = seed / "claims.json"
        data = json.loads(path.read_text())
        data["claims"][0]["theme"] = "bogus"
        path.write_text(json.dumps(data))

        out = tmp_path / "docs" / "data"
        _redirect_paths(monkeypatch, seed, out)
        with pytest.raises(Exception):
            refresh.refresh(check_only=True)

    def test_missing_seed_file_raises(self, tmp_path, monkeypatch):
        seed = tmp_path / "data" / "seed"
        seed.mkdir(parents=True)
        # No JSON files in seed dir.
        _redirect_paths(monkeypatch, seed, tmp_path / "out")
        with pytest.raises(FileNotFoundError):
            refresh.refresh(check_only=True)


def _moratorium(id_: str, status: str, captured_at: date) -> Moratorium:
    return Moratorium(
        id=id_,
        jurisdiction="Test Jurisdiction",
        jurisdiction_type="state",
        status=status,
        duration_description="1 year",
        summary="Test summary.",
        source_url="https://example.com/bill",
        source_title="Test Source",
        captured_at=captured_at,
    )


def _tariff(id_: str, status: str, captured_at: date) -> Tariff:
    return Tariff(
        id=id_,
        utility="Test Utility",
        state="OH",
        tariff_name="Test Tariff",
        status=status,
        regulator="Test PUC",
        summary="Test summary.",
        source_url="https://example.com/docket",
        source_title="Test Source",
        captured_at=captured_at,
    )


class TestStalePendingAudit:
    """`--audit` should flag `proposed` moratoriums/tariffs that have gone stale.

    A pending bill/docket is a moving target; `enacted`/`approved`/`rejected`/
    `failed` records are stable once captured and must never be flagged.
    """

    def test_stale_proposed_moratorium_flagged(self):
        old = date.today() - timedelta(days=refresh.STALE_PENDING_DAYS + 1)
        moratoriums = MoratoriumsPayload(
            generated_at=date.today(),
            moratoriums=[_moratorium("stale-mor", "proposed", old)],
        )
        tariffs = TariffsPayload(generated_at=date.today(), tariffs=[])
        stale = refresh._audit_stale_pending(moratoriums, tariffs)
        assert [r["id"] for r in stale] == ["stale-mor"]
        assert stale[0]["kind"] == "moratorium"
        assert stale[0]["age_days"] == refresh.STALE_PENDING_DAYS + 1

    def test_stale_proposed_tariff_flagged(self):
        old = date.today() - timedelta(days=refresh.STALE_PENDING_DAYS + 5)
        moratoriums = MoratoriumsPayload(generated_at=date.today(), moratoriums=[])
        tariffs = TariffsPayload(
            generated_at=date.today(), tariffs=[_tariff("stale-tar", "proposed", old)]
        )
        stale = refresh._audit_stale_pending(moratoriums, tariffs)
        assert [r["id"] for r in stale] == ["stale-tar"]
        assert stale[0]["kind"] == "tariff"

    def test_recent_proposed_not_flagged(self):
        recent = date.today() - timedelta(days=refresh.STALE_PENDING_DAYS - 1)
        moratoriums = MoratoriumsPayload(
            generated_at=date.today(),
            moratoriums=[_moratorium("fresh-mor", "proposed", recent)],
        )
        tariffs = TariffsPayload(generated_at=date.today(), tariffs=[])
        assert refresh._audit_stale_pending(moratoriums, tariffs) == []

    def test_stale_enacted_not_flagged(self):
        """Enacted/approved records are stable — never flagged, no matter how old."""
        ancient = date.today() - timedelta(days=999)
        moratoriums = MoratoriumsPayload(
            generated_at=date.today(),
            moratoriums=[_moratorium("old-enacted", "enacted", ancient)],
        )
        tariffs = TariffsPayload(
            generated_at=date.today(), tariffs=[_tariff("old-approved", "approved", ancient)]
        )
        assert refresh._audit_stale_pending(moratoriums, tariffs) == []
