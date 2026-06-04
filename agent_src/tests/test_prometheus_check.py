from unittest.mock import patch

from tools.prometheus_check import PrometheusChecker


def _checker() -> PrometheusChecker:
    return PrometheusChecker("http://prometheus:9090")


def test_unknown_alert_is_not_assumed_resolved() -> None:
    assert _checker().is_alert_resolved("UnknownAlert", "bank-web-01", {}) is False


def test_web_endpoint_resolved_requires_probe_success() -> None:
    checker = _checker()
    labels = {
        "alertname": "WebEndpointDown",
        "component": "frontend-web-staging",
        "instance": "bank-web-01",
        "runbook": "nginx",
    }

    with patch.object(checker, "query", return_value=[{"value": [1, "1"]}]):
        assert checker.is_alert_resolved("WebEndpointDown", "bank-web-01", labels) is True

    with patch.object(checker, "query", return_value=[{"value": [1, "0"]}]):
        assert checker.is_alert_resolved("WebEndpointDown", "bank-web-01", labels) is False


def test_docker_container_resolved_requires_container_metric() -> None:
    checker = _checker()
    labels = {
        "alertname": "DockerContainerDown",
        "component": "frontend-web-staging",
        "instance": "bank-web-01",
    }

    with patch.object(checker, "query", return_value=[]):
        assert checker.is_alert_resolved("DockerContainerDown", "bank-web-01", labels) is False

    with patch.object(checker, "query", return_value=[{"value": [1, "123"]}]):
        assert checker.is_alert_resolved("DockerContainerDown", "bank-web-01", labels) is True
