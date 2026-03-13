import pytest

import f1_ingestion.ingestion as ingestion


class _FakeSession:
    def __init__(self, *, results, round_number=1):
        self.results = results
        self.event = {"RoundNumber": round_number}

    def load(self) -> None:
        return None


class _FakeFastF1:
    def __init__(self, session: _FakeSession):
        self._session = session

    def get_session(self, year, grand_prix, session):
        return self._session


@pytest.mark.unit
def test_fastf1_missing_results_raises_actionable_error(monkeypatch, tmp_path) -> None:
    fake = _FakeFastF1(_FakeSession(results=None))
    monkeypatch.setitem(ingestion.__dict__, "fastf1", fake)

    with pytest.raises(RuntimeError, match="FastF1 session results are unavailable"):
        ingestion.ingest_raw_session_results(
            output_dir=tmp_path,
            source="fastf1",
            year=2024,
            grand_prix=1,
            session="R",
        )


@pytest.mark.unit
def test_fastf1_invalid_session_error(monkeypatch, tmp_path) -> None:
    class FakeInvalidSession(Exception):
        pass

    class FakeFastF1Invalid:
        def get_session(self, year, grand_prix, session):
            raise FakeInvalidSession("bad session")

    monkeypatch.setitem(ingestion.__dict__, "fastf1", FakeFastF1Invalid())

    with pytest.raises(RuntimeError, match="FastF1 session load failed"):
        ingestion.ingest_raw_session_results(
            output_dir=tmp_path,
            source="fastf1",
            year=2024,
            grand_prix=1,
            session="INVALID",
        )
