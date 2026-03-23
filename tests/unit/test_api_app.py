import pytest
from f1_api.main import create_app


@pytest.mark.unit
def test_app_routes_include_health() -> None:
    app = create_app()

    paths = {route.path for route in app.routes}

    assert "/health" in paths
    assert "/" in paths
    assert "/api/v1/meta/last-run" in paths
