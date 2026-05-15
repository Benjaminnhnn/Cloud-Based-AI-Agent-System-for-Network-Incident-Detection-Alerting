from unittest.mock import patch

from core import tasks


def _alert(fingerprint: str | None = None) -> dict:
    alert = {
        "status": "firing",
        "labels": {
            "alertname": "WebEndpointDown",
            "instance": "bank-web-01",
            "job": "blackbox_http_web",
            "service": "availability",
            "target": "http://52.220.34.44/health",
        },
        "annotations": {},
    }
    if fingerprint:
        alert["fingerprint"] = fingerprint
    return alert


def test_alert_identity_prefers_alertmanager_fingerprint() -> None:
    assert tasks._alert_identity(_alert("abc123")) == "abc123"


def test_alert_processing_uses_local_cooldown_when_redis_unavailable() -> None:
    tasks._local_alert_cooldowns.clear()

    alert = _alert("same-alert")

    with (
        patch.object(tasks, "redis_client", None),
        patch.object(tasks, "ALERT_DEDUP_ENABLED", True),
        patch.object(tasks, "ALERT_AI_COOLDOWN_SECONDS", 60),
    ):
        assert tasks._reserve_alert_processing(alert) is True
        assert tasks._reserve_alert_processing(alert) is False

        tasks._clear_alert_cooldown(alert)
        assert tasks._reserve_alert_processing(alert) is True
