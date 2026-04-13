#!/usr/bin/env python3
"""
🔍 UNIFIED SERVICE MONITOR - Module 1 + Module 2 Integration

Combines metrics from Module 1 (Prometheus) and logs from Module 2 (Log Watcher)
to provide enriched context to AI Agent.

Architecture:
    Module 1 (Prometheus):  Generic metrics every 15s
    Module 2 (Log Watcher): Specific errors every <1s
            ↓
        service_monitor.py
            ├─ Consume Module 2 queue
            ├─ Fetch Module 1 metrics
            ├─ Merge context
            └─ Send to webhook
            
Usage:
    python3 service_monitor.py
    
Configuration:
    services_config.json - Configure which services to monitor
"""

import json
import time
import socket
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

import sys
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG_FILE = Path(__file__).parent / 'services_config.json'
PROMETHEUS_URL = 'http://localhost:9090'

# Dynamic webhook URL - find any port in range 8000-8010
def find_webhook_url():
    """Find running webhook endpoint on ports 8000-8010."""
    for port in range(8000, 8011):
        try:
            r = requests.get(f'http://localhost:{port}/health', timeout=1)
            if r.status_code == 200:
                return f'http://localhost:{port}/webhook'
        except:
            pass
    # Fallback to default
    return 'http://localhost:8000/webhook'

WEBHOOK_URL = find_webhook_url()
HOSTNAME = socket.gethostname()

# ============================================================================
# PORT CHECKER - Module 3 (Active Port Monitoring)
# ============================================================================

class PortChecker:
    """Check if services are listening on ports."""
    
    def __init__(self, config_file: Path = None):
        """Initialize port checker with config."""
        self.config_file = config_file or Path(__file__).parent / 'services_config.json'
        self.config = self._load_config()
        self.port_status = {}  # Track port status changes
        self.last_check_time = defaultdict(float)
        self.check_timeout = 3  # Seconds to wait for port response
        
        logger.debug("🔌 Port Checker initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration."""
        try:
            with open(self.config_file) as f:
                config = json.load(f)
                return config
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return {'services': {}}
    
    def _is_port_open(self, host: str, port: int, timeout: int = 3) -> bool:
        """
        Check if a port is open (service listening).
        
        Args:
            host: Hostname/IP to check
            port: Port number
            timeout: Timeout in seconds
            
        Returns:
            True if port is open, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            # Try to connect
            result = sock.connect_ex((host, port))
            sock.close()
            
            return result == 0
        except socket.timeout:
            logger.debug(f"⏱️ Timeout connecting to {host}:{port}")
            return False
        except socket.error as e:
            logger.debug(f"❌ Socket error for {host}:{port}: {e}")
            return False
        except Exception as e:
            logger.debug(f"❌ Error checking port {host}:{port}: {e}")
            return False
    
    def check_all_ports(self) -> tuple:
        """
        Check all configured services.
        
        Returns:
            Tuple of (results, alerts) lists
        """
        results = []
        alerts = []
        
        services = self.config.get('services', {})
        
        for service_name, service_config in services.items():
            # Skip disabled services
            if not service_config.get('enabled', True):
                continue
            
            # Skip services without ports
            port = service_config.get('port')
            if port is None:
                continue
            
            host = 'localhost'
            severity = service_config.get('severity', 'CRITICAL')
            
            # Check if port is open
            is_open = self._is_port_open(host, port, self.check_timeout)
            
            # Track status change
            service_key = f"{service_name}:{port}"
            previous_status = self.port_status.get(service_key)
            self.port_status[service_key] = is_open
            
            # Create result
            result = {
                'service': service_name,
                'host': host,
                'port': port,
                'severity': severity,
                'is_open': is_open,
                'timestamp': datetime.now().isoformat(),
                'status_changed': previous_status is not None and previous_status != is_open
            }
            results.append(result)
            
            # Log result
            if is_open:
                logger.debug(f"✅ {service_name:15} {host}:{port:5} - LISTENING")
            else:
                logger.warning(f"❌ {service_name:15} {host}:{port:5} - DOWN")
            
            # Generate alert if port down or just went down
            if not is_open:
                alerts.append({
                    'service': service_name,
                    'port': port,
                    'severity': severity,
                    'status_changed': result['status_changed'],
                    'message': f"🚨 {service_name} (port {port}) is DOWN"
                })
        
        return results, alerts

# ============================================================================
# UNIFIED MONITOR
# ============================================================================

class UnifiedServiceMonitor:
    """
    Combines Module 1 (Prometheus metrics) + Module 2 (Log errors)
    for enriched error context and faster detection.
    """
    
    def __init__(self, config_file: Path = CONFIG_FILE):
        """Initialize monitor with configuration."""
        self.config = self._load_config(config_file)
        self.check_interval = self.config.get('monitoring', {}).get('check_interval', 5)
        self.alert_cooldown = self.config.get('monitoring', {}).get('alert_cooldown', 60)
        self.last_alert_time = defaultdict(float)
        
        # Initialize port checker (Module 3)
        self.port_checker = PortChecker(config_file)
        
        logger.info(f"🚀 Unified Service Monitor Started")
        logger.info(f"   Check interval: {self.check_interval}s")
        logger.info(f"   Alert cooldown: {self.alert_cooldown}s")
        logger.info(f"   ✅ Module 3 (Port Checker) initialized")

    def _load_config(self, config_file: Path) -> Dict[str, Any]:
        """Load services configuration."""
        try:
            with open(config_file) as f:
                config = json.load(f)
                logger.info(f"✅ Configuration loaded from {config_file}")
                return config
        except FileNotFoundError:
            logger.warning(f"⚠️  Config file not found: {config_file}")
            logger.warning(f"   Using default configuration")
            return self._default_config()
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration."""
        return {
            'services': {
                'nginx': {'enabled': True, 'port': 80, 'severity': 'CRITICAL'},
                'postgresql': {'enabled': True, 'port': 5432, 'severity': 'CRITICAL'},
            },
            'monitoring': {
                'check_interval': 5,
                'alert_cooldown': 60
            }
        }

    # ========================================================================
    # MODULE 3: PORT MONITORING (Active, real-time)
    # ========================================================================

    def _check_services_ports(self) -> Optional[Dict[str, Any]]:
        """
        Check if services are listening on ports (Module 3).
        
        Returns:
            Alert for first down service, or None
        """
        try:
            results, alerts = self.port_checker.check_all_ports()
            
            # Only send alert if port status changed (not down before, now down)
            for alert in alerts:
                if alert['status_changed']:
                    logger.warning(f"🚨 PORT DOWN: {alert['service']} port {alert['port']} is DOWN!")
                    return {
                        'service': alert['service'],
                        'port': alert['port'],
                        'severity': alert['severity'],
                        'message': alert['message']
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking ports: {str(e)}")
            return None
    
    def _generate_port_down_alert(self, port_alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate alert payload for port down.
        
        Args:
            port_alert: Port check alert dict
            
        Returns:
            Alert payload for webhook
        """
        alert = {
            'receiver': 'port-checker',
            'status': 'firing',
            'alerts': [{
                'status': 'firing',
                'labels': {
                    'alertname': f"{port_alert['service']}_DOWN",
                    'severity': port_alert['severity'],
                    'instance': HOSTNAME,
                    'service': port_alert['service'],
                    'port': str(port_alert['port']),
                    'module': 'MODULE_3_PORT_CHECKER'
                },
                'annotations': {
                    'summary': f"🚨 {port_alert['severity']}: {port_alert['service']} port {port_alert['port']} DOWN",
                    'description': port_alert['message'],
                    'service': port_alert['service'],
                    'port': str(port_alert['port']),
                    'check_type': 'port_connectivity'
                },
                'startsAt': datetime.utcnow().isoformat() + 'Z',
                'generatorURL': f'http://{HOSTNAME}/monitor'
            }]
        }
        return alert

    # ========================================================================
    # MODULE 1: METRICS (Generic, 15s lag)
    # ========================================================================

    def _fetch_prometheus_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Fetch current metrics from Prometheus (Module 1).
        
        Returns:
            Metrics dict or None if unavailable
        """
        try:
            # Get current metrics from Prometheus
            query_url = f"{PROMETHEUS_URL}/api/v1/query"
            
            queries = {
                'cpu_usage': 'node_cpu_seconds_total',
                'memory_usage': 'node_memory_MemAvailable_bytes',
                'disk_usage': 'node_filesystem_avail_bytes'
            }
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'source': 'prometheus',
                'available': True
            }
            
            # Simple check - if Prometheus is reachable
            response = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=2)
            if response.status_code == 200:
                metrics['prometheus_healthy'] = True
                logger.info(f"✅ Module 1 (Prometheus) metrics available")
            else:
                metrics['prometheus_healthy'] = False
                logger.warning(f"⚠️  Prometheus not responding")
            
            return metrics
            
        except Exception as e:
            logger.warning(f"⚠️  Cannot fetch Module 1 metrics: {str(e)}")
            return None

    # ========================================================================
    # MERGE CONTEXT
    # ========================================================================

    def _merge_context(self, module2_event: Dict[str, Any], 
                       module1_metrics: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge Module 2 event + Module 1 metrics for enriched context.
        
        Args:
            module2_event: Event from log watcher
            module1_metrics: Metrics from Prometheus
            
        Returns:
            Merged alert payload
        """
        alert = {
            'receiver': 'unified-monitor',
            'status': 'firing',
            'alerts': [{
                'status': 'firing',
                'labels': {
                    'alertname': module2_event.get('file', 'UnknownService'),
                    'severity': module2_event.get('severity', 'ERROR'),
                    'instance': HOSTNAME,
                    'service': 'unified-monitor',
                    'source_file': module2_event.get('file', '-'),
                    'server': module2_event.get('server', HOSTNAME),
                    'module': 'MODULE_2_LOG_WATCHER'
                },
                'annotations': {
                    'summary': f"🚨 {module2_event.get('severity', 'ERROR')}: {module2_event.get('file', 'Unknown').split('/')[-1]}",
                    'description': module2_event.get('line', 'Unknown error'),
                    'log_context': json.dumps(module2_event.get('context', []), ensure_ascii=False),
                    'error_file': module2_event.get('file', '-'),
                    'server': module2_event.get('server', HOSTNAME)
                },
                'startsAt': module2_event.get('timestamp', datetime.utcnow().isoformat()) + 'Z',
                'generatorURL': f'http://{HOSTNAME}/monitor'
            }]
        }
        
        # Add Module 1 metrics if available
        if module1_metrics and module1_metrics.get('prometheus_healthy'):
            alert['alerts'][0]['annotations']['module1_metrics_available'] = 'true'
            alert['alerts'][0]['labels']['dual_layer'] = 'true'
            logger.info(f"✅ Merged Module 1 + Module 2 context")
        
        return alert

    # ========================================================================
    # SEND TO WEBHOOK
    # ========================================================================

    def _send_to_webhook(self, alert: Dict[str, Any]) -> bool:
        """
        Send merged alert to AI Agent webhook.
        
        Args:
            alert: Alert payload
            
        Returns:
            True if successful
        """
        try:
            response = requests.post(
                WEBHOOK_URL,
                json=alert,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Alert sent to webhook: {alert['alerts'][0]['labels']['alertname']}")
                return True
            else:
                logger.error(f"❌ Webhook returned {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Webhook timeout")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending to webhook: {str(e)}")
            return False

    # ========================================================================
    # MAIN LOOP
    # ========================================================================

    def monitor_services(self):
        """Main monitoring loop."""
        print("\n" + "="*80)
        print("🔄 UNIFIED SERVICE MONITOR (Module 1 + Module 2 + Module 3)")
        print("   Module 1: Prometheus metrics (15s)")
        print("   Module 2: Log watcher errors (<1s)")
        print("   Module 3: Port checker (real-time)")
        print("="*80 + "\n")
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                
                # Module 3: Check service ports (PRIORITY - immediate response)
                port_alert = self._check_services_ports()
                if port_alert:
                    alert = self._generate_port_down_alert(port_alert)
                    self._send_to_webhook(alert)
                    time.sleep(1)  # Wait before checking again
                    continue
                
                # log_watcher sends alerts directly via HTTP webhook
                # No queuing mechanism needed
                
                time.sleep(self.check_interval)
        
        except KeyboardInterrupt:
            print("\n" + "="*80)
            logger.info("⏹️  Monitor stopped by user")
            print("="*80)
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            raise


def main():
    """Entry point."""
    monitor = UnifiedServiceMonitor()
    monitor.monitor_services()


if __name__ == "__main__":
    main()
