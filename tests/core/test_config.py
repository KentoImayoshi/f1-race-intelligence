from f1_core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "F1 Race Intelligence AI"
    assert settings.env == "local"
    assert settings.debug is False
    assert settings.api_v1_prefix == "/api/v1"
