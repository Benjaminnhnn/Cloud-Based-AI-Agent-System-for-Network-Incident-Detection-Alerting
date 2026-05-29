from unittest.mock import patch

from tools.prometheus_check import PrometheusChecker


def test_web_endpoint_down_resolves_when_probe_success_is_one() -> None:
    checker = PrometheusChecker("http://prometheus:9090")

    with patch.object(checker, "_first_value", return_value=1.0) as query:
        assert checker.is_alert_resolved("WebEndpointDown", "bank-web-01") is True

    query.assert_called_once_with(
        'probe_success{job="blackbox_http_web",instance="bank-web-01"}'
    )


def test_unknown_alert_does_not_default_to_resolved() -> None:
    checker = PrometheusChecker("http://prometheus:9090")

    with patch.object(checker, "_first_value", return_value=None):
        assert checker.is_alert_resolved("UnknownAlert", "bank-web-01") is False


def test_postgresql_down_resolves_when_pg_up_is_one() -> None:
    checker = PrometheusChecker("http://prometheus:9090")

    with patch.object(checker, "_first_value", return_value=1.0):
        assert checker.is_alert_resolved("PostgreSQLDown", "bank-core-01") is True


def test_redis_down_resolves_when_redis_up_is_one() -> None:
    checker = PrometheusChecker("http://prometheus:9090")

    with patch.object(checker, "_first_value", return_value=1.0):
        assert checker.is_alert_resolved("RedisDown", "monitor-ai-01") is True


def test_docker_container_down_requires_expected_containers_present() -> None:
    checker = PrometheusChecker("http://prometheus:9090")

    with patch.object(checker, "_first_value", return_value=1780068000.0):
        assert checker.is_alert_resolved("DockerContainerDown", "bank-core-01") is True
