import pytest

from f1_ingestion.ingestion import _records_from_results


@pytest.mark.unit
def test_records_from_results_rejects_unknown_type() -> None:
    with pytest.raises(
        TypeError,
        match="FastF1 results object must be a list of dicts or a pandas DataFrame",
    ):
        _records_from_results(object())
