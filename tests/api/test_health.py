from f1_api.api.routes import health


def test_health_endpoint() -> None:
    assert health.health() == {"status": "ok"}


def test_root_endpoint() -> None:
    assert health.root() == {"service": "f1-api"}
