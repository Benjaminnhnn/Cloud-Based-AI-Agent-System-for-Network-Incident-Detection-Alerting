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
