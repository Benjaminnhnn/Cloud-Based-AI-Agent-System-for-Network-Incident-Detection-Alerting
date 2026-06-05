import asyncio
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


def _runbook_alert(alertname: str, component: str, instance: str) -> dict:
    return {
        "status": "firing",
        "labels": {
            "alertname": alertname,
            "instance": instance,
            "job": "demo",
            "service": "demo",
            "component": component,
            "environment": "staging",
        },
        "annotations": {"summary": f"{component} is down"},
    }


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


def test_web_endpoint_alert_context_includes_probe_target() -> None:
    details = tasks.build_incident_details(_alert("web-down"))

    assert "Alert: WebEndpointDown" in details
    assert "Instance: bank-web-01" in details
    assert "Job: blackbox_http_web" in details
    assert "Target: http://52.220.34.44/health" in details


def test_web_endpoint_diagnosis_has_actionable_checks() -> None:
    analysis, proposal = tasks.deterministic_diagnosis(_alert("web-down"))

    assert "frontend-web-prod" in analysis
    assert "docker ps -a --filter name=frontend-web-prod" in analysis
    assert proposal == {
        "action": "check_or_start_frontend_web_prod",
        "host": "bank-web-01",
    }


def test_staging_web_endpoint_diagnosis_uses_staging_container_and_port() -> None:
    alert = _runbook_alert("WebEndpointDown", "frontend-web-staging", "bank-web-01")
    alert["labels"]["target"] = "http://13.228.171.39:18081/health"

    analysis, proposal = tasks.deterministic_diagnosis(alert)

    assert "frontend-web-staging" in analysis
    assert "http://127.0.0.1:18081/health" in analysis
    assert proposal == {
        "action": "check_or_start_frontend_web_staging",
        "host": "bank-web-01",
    }


def test_postgresql_diagnosis_has_core_redeploy_steps() -> None:
    analysis, proposal = tasks.deterministic_diagnosis(
        _runbook_alert("PostgreSQLDown", "postgres-staging", "bank-core-01")
    )

    assert "postgres-staging" in analysis
    assert "pg_isready -U aiops_user -d aiops_db" in analysis
    assert "./automation/app-release-deploy.sh staging \"$TAG\" core" in analysis
    assert proposal == {
        "action": "check_or_start_postgres_staging",
        "host": "bank-core-01",
    }


def test_redis_diagnosis_has_monitor_redeploy_steps() -> None:
    analysis, proposal = tasks.deterministic_diagnosis(
        _runbook_alert("RedisDown", "redis-cache-staging", "monitor-ai-01")
    )

    assert "redis-cache-staging" in analysis
    assert "redis-cli ping" in analysis
    assert "./automation/app-release-deploy.sh staging \"$TAG\" monitor" in analysis
    assert proposal == {
        "action": "check_or_start_redis_cache_staging",
        "host": "monitor-ai-01",
    }


def test_docker_container_diagnosis_maps_component_to_role() -> None:
    analysis, proposal = tasks.deterministic_diagnosis(
        _runbook_alert("DockerContainerDown", "payment-api-staging", "bank-core-01")
    )

    assert "payment-api-staging" in analysis
    assert "Deploy role: core" in analysis
    assert "./automation/app-release-deploy.sh staging \"$TAG\" core" in analysis
    assert proposal == {
        "action": "redeploy_core_staging",
        "host": "bank-core-01",
    }


def test_known_runbook_alert_does_not_call_gemini() -> None:
    alert = _runbook_alert("RedisDown", "redis-cache-staging", "monitor-ai-01")

    with (
        patch.object(tasks, "redis_client", None),
        patch.object(tasks, "ALERT_DEDUP_ENABLED", False),
        patch.object(tasks, "run_agent_workflow") as run_agent_workflow,
        patch.object(tasks, "send_telegram_message") as send_telegram_message,
        patch.object(tasks, "save_incident_to_redis"),
        patch.object(tasks.verify_resolution_task, "apply_async"),
    ):
        asyncio.run(tasks.process_single_alert(alert))

    run_agent_workflow.assert_not_called()
    assert send_telegram_message.called
    assert "redis-cache-staging" in send_telegram_message.call_args.args[0]


def test_alert_batch_concurrency_is_bounded() -> None:
    active = 0
    peak = 0

    async def fake_process_single_alert(alert: dict) -> None:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1

    with (
        patch.object(tasks, "ALERT_BATCH_CONCURRENCY", 2),
        patch.object(tasks, "process_single_alert", side_effect=fake_process_single_alert),
    ):
        tasks.process_alerts_task.run({"alerts": [{"id": i} for i in range(6)]})

    assert peak == 2
