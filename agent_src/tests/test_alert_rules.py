from pathlib import Path


ALERT_RULES = Path(__file__).resolve().parents[2] / "ansible" / "config" / "alert_rules.yml"


def test_frontend_api_proxy_alert_requires_direct_payment_api_to_be_healthy() -> None:
    rules = ALERT_RULES.read_text(encoding="utf-8")

    proxy_rule = rules.split("- alert: FrontendAPIProxyDown", 1)[1].split(
        "- alert: PaymentAPIEndpointDown", 1
    )[0]

    assert 'probe_success{runbook="api-proxy"' in proxy_rule
    assert 'probe_success{runbook="payment-api"' in proxy_rule
    assert "and on()" in proxy_rule
    assert "== 1" in proxy_rule


def test_docker_container_alerts_use_latest_cadvisor_series() -> None:
    rules = ALERT_RULES.read_text(encoding="utf-8")
    docker_rules = rules.split("- alert: DockerContainerDown")[1:]

    assert len(docker_rules) == 5
    for rule in docker_rules:
        assert "max by (instance) (container_last_seen" in rule
