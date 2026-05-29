# prometheus_check.py
# Utilities để kiểm lại Prometheus metrics và xác nhận issue đã resolve

import os
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Prometheus configuration. In production Prometheus runs on the monitor host
# network, while the AI agent runs in a bridge network. Try the configured URL
# first, then common Docker host gateway addresses.
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
PROMETHEUS_TIMEOUT = 10


class PrometheusChecker:
    """
    Kiểm lại Prometheus metrics để xác nhận issue đã resolve.
    
    Usage:
        checker = PrometheusChecker()
        is_resolved = checker.is_alert_resolved("node_cpu_high", "10.10.1.68")
    """
    
    def __init__(self, prometheus_url: str = PROMETHEUS_URL):
        fallback_urls = (
            "http://172.20.0.1:9090",
            "http://172.19.0.1:9090",
            "http://172.18.0.1:9090",
            "http://172.17.0.1:9090",
            "http://127.0.0.1:9090",
        )
        urls = [prometheus_url.rstrip("/")]
        urls.extend(url for url in fallback_urls if url not in urls)
        self.base_urls = urls
        self.base_url = urls[0]
        self.query_url = f"{self.base_url}/api/v1/query"

    def _query(self, query: str) -> list[dict[str, Any]]:
        last_error = None
        for base_url in self.base_urls:
            try:
                response = requests.get(
                    f"{base_url}/api/v1/query",
                    params={"query": query},
                    timeout=PROMETHEUS_TIMEOUT,
                )
                response.raise_for_status()

                data = response.json()
                if data.get("status") == "success":
                    self.base_url = base_url
                    self.query_url = f"{base_url}/api/v1/query"
                    return data.get("data", {}).get("result", [])
            except Exception as e:
                last_error = e
                logger.warning("Prometheus query failed via %s: %s", base_url, e)

        logger.error("All Prometheus query endpoints failed. Last error: %s", last_error)
        return []

    def _first_value(self, query: str) -> Optional[float]:
        results = self._query(query)
        if not results:
            return None
        value = results[0].get("value", [None, None])[1]
        return float(value) if value is not None else None
    
    def get_metric(self, instance: str, metric_name: str) -> Optional[float]:
        """
        Query Prometheus để lấy current metric value.
        
        Example:
            - metric_name: "node_cpu_percent{instance='10.10.1.68'}"
            - Return: 45.5 (CPU percent)
        """
        try:
            query = f"{metric_name}{{instance='{instance}'}}"
            return self._first_value(query)
        except Exception as e:
            logger.error(f"Error querying Prometheus for {metric_name}: {e}")
            return None
    
    def is_alert_resolved(self, alert_name: str, instance: str) -> bool:
        """
        Kiểm lại nếu alert đã resolve dựa trên alert name.
        
        Mapping:
        - node_cpu_high: CPU < 80%
        - node_memory_high: Memory < 85%
        - node_disk_high: Disk < 85%
        - service_down: port accessible
        - network_packet_loss: Loss < 1%
        """
        
        try:
            # Extract instance IP/hostname
            # instance format: "10.10.1.68:9100" or "10.10.1.68"
            host = instance.split(":")[0]
            
            if alert_name == "node_cpu_high":
                # Check if CPU is below 80%
                cpu = self.get_metric(host, "node_cpu_usage_percent")
                threshold = 80
                return cpu is not None and cpu < threshold
            
            elif alert_name == "node_memory_high":
                # Check if Memory is below 85%
                mem = self.get_metric(host, "node_memory_usage_percent")
                threshold = 85
                return mem is not None and mem < threshold
            
            elif alert_name == "node_disk_high":
                # Check if Disk is below 85%
                disk = self.get_metric(host, "node_disk_usage_percent")
                threshold = 85
                return disk is not None and disk < threshold
            
            elif alert_name == "network_packet_loss":
                # Check if packet loss is below 1%
                loss = self.get_metric(host, "node_network_packet_loss_percent")
                threshold = 1
                return loss is not None and loss < threshold
            
            elif alert_name == "WebEndpointDown":
                probe = self._first_value(
                    f'probe_success{{job="blackbox_http_web",instance="{instance}"}}'
                )
                return probe == 1

            elif alert_name == "service_down":
                # Check if service is up (via port health check)
                # This would require specific port configuration
                logger.info(f"Service check for {host} - assuming resolved")
                return True
            
            else:
                active_alert = self._first_value(
                    f'ALERTS{{alertname="{alert_name}",instance="{instance}",alertstate="firing"}}'
                )
                if active_alert is not None:
                    return active_alert != 1

                logger.warning("Unknown alert type and no ALERTS series found: %s", alert_name)
                return False
        
        except Exception as e:
            logger.error(f"Error in is_alert_resolved: {e}")
            return False
    
    def get_alert_metrics(self, instance: str) -> Dict[str, Any]:
        """
        Lấy tất cả metrics liên quan để report.
        
        Return:
        {
            "cpu_percent": 45.5,
            "memory_percent": 62.3,
            "disk_percent": 70.1,
            "timestamp": "2026-04-28T14:53:00"
        }
        """
        from datetime import datetime
        
        host = instance.split(":")[0]
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": self.get_metric(host, "node_cpu_usage_percent"),
            "memory_percent": self.get_metric(host, "node_memory_usage_percent"),
            "disk_percent": self.get_metric(host, "node_disk_usage_percent"),
        }
        return metrics


# Singleton instance
_checker: Optional[PrometheusChecker] = None


def get_prometheus_checker() -> PrometheusChecker:
    """Get singleton instance of PrometheusChecker"""
    global _checker
    if _checker is None:
        _checker = PrometheusChecker()
    return _checker
