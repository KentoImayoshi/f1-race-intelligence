from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/models/src"))

from f1_models.contracts import BASELINE_SESSION_DRIVER_SCORES_COLUMNS  # noqa: E402


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
