from pathlib import Path

import pytest


from f1_llm.contracts import EXPLANATION_SESSION_TOP_DRIVERS_COLUMNS  # noqa: E402


@pytest.mark.unit
def test_explanation_contract_columns() -> None:
    assert EXPLANATION_SESSION_TOP_DRIVERS_COLUMNS == [
        "season",
        "round",
        "session",
        "explanation_type",
        "explanation_text",
        "explanation_generated_at",
    ]
