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


def test_frontend_api_proxy_resolved_matches_correlated_alert_rule() -> None:
    checker = _checker()
    labels = {
        "alertname": "FrontendAPIProxyDown",
        "component": "frontend-web-staging",
        "instance": "bank-web-01",
        "runbook": "api-proxy",
        "dependency": "payment-api-staging",
        "dependency_instance": "bank-core-01",
    }

    with patch.object(checker, "query", return_value=[{"value": [1, "0"]}]) as query:
        assert checker.is_alert_resolved("FrontendAPIProxyDown", "bank-web-01", labels) is False

    condition_query = query.call_args.args[0]
    assert 'runbook="api-proxy"' in condition_query
    assert 'runbook="payment-api"' in condition_query
    assert "and on()" in condition_query

    with patch.object(checker, "query", return_value=[]):
        assert checker.is_alert_resolved("FrontendAPIProxyDown", "bank-web-01", labels) is True


def test_docker_container_resolved_requires_fresh_container_metric() -> None:
    checker = _checker()
    labels = {
        "alertname": "DockerContainerDown",
        "component": "frontend-web-staging",
        "instance": "bank-web-01",
    }

    with patch.object(checker, "query", return_value=[]):
        assert checker.is_alert_resolved("DockerContainerDown", "bank-web-01", labels) is False

    with patch.object(
        checker,
        "query",
        side_effect=[[{"value": [1, "123"]}], [{"value": [1, "10"]}]],
    ):
        assert checker.is_alert_resolved("DockerContainerDown", "bank-web-01", labels) is True

    with patch.object(
        checker,
        "query",
        side_effect=[[{"value": [1, "123"]}], [{"value": [1, "45"]}]],
    ):
        assert checker.is_alert_resolved("DockerContainerDown", "bank-web-01", labels) is False


def test_high_cpu_resolved_uses_prometheus_rule_threshold() -> None:
    checker = _checker()
    labels = {"instance": "bank-core-01"}

    with patch.object(checker, "query", return_value=[{"value": [1, "25"]}]) as query:
        assert checker.is_alert_resolved("HighCPUUsage", "bank-core-01", labels) is True

    assert "node_cpu_seconds_total" in query.call_args.args[0]
