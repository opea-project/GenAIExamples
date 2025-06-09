import requests
import time
import json

from .utils import log_message, get_host_ip, run_command, start_kubectl_port_forward, stop_all_kubectl_port_forwards
from .config import EXAMPLE_CONFIGS


class ConnectionTester:
    """
    Handles testing connections to the deployed services.
    """

    def __init__(self, example_name, deploy_mode, device, args_namespace):
        self.example_name = example_name
        self.deploy_mode = deploy_mode
        self.device = device
        self.args = args_namespace
        self.config = EXAMPLE_CONFIGS[example_name]
        self.test_suite_config = self.config.get("test_connections", {})
        self.port_config = self.config.get("ports", {})
        self.k8s_namespace = self.config.get("kubernetes", {}).get("namespace")
        self.host_ip = get_host_ip() if self.deploy_mode == "docker" else "localhost"
        self.session = requests.Session()
        if self.args.http_proxy or self.args.https_proxy:
            self.session.proxies = {'http': self.args.http_proxy, 'https': self.args.https_proxy}
        self.results = {"passed": 0, "failed": 0, "skipped": 0}

    def _get_service_url_and_port(self, service_key):
        """Determines the URL for a service, handling Docker ports and K8s port-forwarding."""
        if self.deploy_mode == "docker":
            port = self.port_config.get("docker", {}).get(service_key)
            if not port: return None, None
            return f"http://{self.host_ip}:{port}", port

        elif self.deploy_mode == "k8s":
            service_name = self.port_config.get("k8s_services", {}).get(service_key)
            if not service_name: return None, None
            try:
                cmd = ["kubectl", "get", "svc", service_name, "-n", self.k8s_namespace, "-o",
                       "jsonpath={.spec.ports[0].port}"]
                result = run_command(cmd, capture_output=True, check=True, display_cmd=False)
                remote_port = result.stdout.strip()
            except Exception as e:
                log_message("ERROR", f"Failed to get remote port for {service_name}: {e}")
                return None, None

            # Use defined local port for main service, generate for others
            local_port = self.args.k8s_test_local_port if service_key == self.test_suite_config.get("main_service",
                                                                                                    {}).get(
                "service_key") else (8081 + hash(service_key) % 100)

            if not start_kubectl_port_forward(self.k8s_namespace, service_name, local_port, remote_port):
                return None, None

            return f"http://localhost:{local_port}", local_port
        return None, None

    def _make_request(self, service_key, test_case_config):
        """Makes a single HTTP request to a service endpoint."""
        base_url, _ = self._get_service_url_and_port(service_key)
        if not base_url:
            return {"status": "SKIPPED", "reason": f"Could not determine URL for '{service_key}'"}

        full_url = base_url + test_case_config["path"]
        method = test_case_config.get("method", "GET").upper()
        log_message("INFO", f"Testing {method} {full_url}")

        try:
            response = self.session.request(
                method, full_url,
                json=test_case_config.get("payload"),
                headers=test_case_config.get("headers", {}),
                timeout=test_case_config.get("timeout", 120)
            )
            return {
                "status_code": response.status_code,
                "content": response.text,
                "url": full_url
            }
        except requests.exceptions.RequestException as e:
            return {"status": "ERROR", "reason": str(e), "url": full_url}

    def _validate_response(self, response_data, test_case_config):
        """Validates the HTTP response against expected outcomes."""
        test_name = test_case_config.get("name", test_case_config["path"])
        if response_data.get("status") in ["SKIPPED", "ERROR"]:
            log_message("WARN", f"Test '{test_name}': Skipped or Errored - {response_data.get('reason')}")
            self.results["skipped"] += 1
            return False

        passed = True
        expect_code = test_case_config.get("expect_code")
        if expect_code and response_data["status_code"] != expect_code:
            passed = False
            log_message("ERROR",
                        f"Test '{test_name}': Expected status {expect_code}, got {response_data['status_code']}")

        expect_contains = test_case_config.get("expect_response_contains")
        if expect_contains and expect_contains not in response_data["content"]:
            passed = False
            log_message("ERROR", f"Test '{test_name}': Expected response to contain '{expect_contains}'")

        if passed:
            log_message("OK", f"Test '{test_name}' PASSED.")
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
        return passed

    def run_all_tests(self):
        """Runs all configured tests for the example."""
        if not self.test_suite_config:
            log_message("WARN", "No connection tests configured. Skipping.")
            return True  # Not a failure

        all_passed = True

        # Test main service
        main_test = self.test_suite_config.get("main_service")
        if main_test:
            response = self._make_request(main_test["service_key"], main_test)
            if not self._validate_response(response, main_test):
                all_passed = False

        # Test sub-services
        for sub_test in self.test_suite_config.get("sub_services", []):
            response = self._make_request(sub_test["service_key"], sub_test)
            if not self._validate_response(response, sub_test):
                all_passed = False

        if self.deploy_mode == "k8s":
            stop_all_kubectl_port_forwards()

        log_message("INFO",
                    f"Test Summary: Passed: {self.results['passed']}, Failed: {self.results['failed']}, Skipped: {self.results['skipped']}")
        return all_passed