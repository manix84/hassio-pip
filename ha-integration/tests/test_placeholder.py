from custom_components.ha_tv_pip.const import DOMAIN


def test_domain_matches_integration_slug() -> None:
    assert DOMAIN == "ha_tv_pip"
