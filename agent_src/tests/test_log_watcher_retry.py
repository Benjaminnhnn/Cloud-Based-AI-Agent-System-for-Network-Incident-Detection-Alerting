from unittest.mock import Mock, patch

import log_watcher


def test_log_watcher_retries_temporary_webhook_error() -> None:
    temporary_error = Mock(status_code=503)
    success = Mock(status_code=200)

    with (
        patch.object(log_watcher, "WEBHOOK_MAX_ATTEMPTS", 3),
        patch.object(log_watcher.requests, "post", side_effect=[temporary_error, success]) as post,
        patch.object(log_watcher.time, "sleep") as sleep,
    ):
        log_watcher.send_alert_to_ai_agent("ERROR demo", "/tmp/test.log")

    assert post.call_count == 2
    sleep.assert_called_once_with(1.0)
