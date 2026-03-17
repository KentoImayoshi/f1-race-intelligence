from pathlib import Path

import pytest

from f1_models.contracts import BASELINE_SESSION_DRIVER_SCORES_COLUMNS


@pytest.mark.unit
def test_baseline_contract_columns() -> None:
    assert BASELINE_SESSION_DRIVER_SCORES_COLUMNS == [
        "season",
        "round",
        "session",
        "driver_code",
        "position_numeric",
        "score",
        "model_generated_at",
    ]
