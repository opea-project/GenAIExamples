# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import copy
import json
import os
import time
from abc import ABC

import requests

from .config import EXAMPLE_CONFIGS, TEST_RETRY_ATTEMPTS, TEST_RETRY_DELAY_S
from .utils import (
    check_install_python_pkg,
    get_host_ip,
    log_message,
    run_command,
    start_kubectl_port_forward,
    stop_all_kubectl_port_forwards,
)


class BaseConnectionTester(ABC):
    """Handles testing connections to the deployed services."""

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
        # if self.args.http_proxy or self.args.https_proxy:
        #     self.session.proxies = {"http": self.args.http_proxy, "https": self.args.https_proxy}
        self.results = {"passed": 0, "failed": 0, "skipped": 0}

        self.session = requests.Session()

        # proxies = {}
        # if self.args.http_proxy:
        #     proxies["http"] = self.args.http_proxy
        # if self.args.https_proxy:
        #     proxies["https"] = self.args.https_proxy

        # if proxies:
        #     self.session.proxies = proxies

        # # Set NO_PROXY environment variable for the requests session to respect it
        # # This is the standard way to make requests bypass proxies for certain hosts
        # if self.args.no_proxy:
        #     os.environ["NO_PROXY"] = self.args.no_proxy
        #     log_message("DEBUG", f"Set NO_PROXY for this session: {self.args.no_proxy}")

    def _get_service_url_and_port(self, service_key):
        """Determines the URL for a service, handling Docker ports and K8s port-forwarding."""
        if self.deploy_mode == "docker":
            port = self.port_config.get("docker", {}).get(service_key)
            if not port:
                return None, None
            return f"http://{self.host_ip}:{port}", port

        elif self.deploy_mode == "k8s":
            service_name = self.port_config.get("k8s_services", {}).get(service_key)
            if not service_name:
                return None, None
            try:
                cmd = [
                    "kubectl",
                    "get",
                    "svc",
                    service_name,
                    "-n",
                    self.k8s_namespace,
                    "-o",
                    "jsonpath={.spec.ports[0].port}",
                ]
                result = run_command(cmd, capture_output=True, check=True, display_cmd=False)
                remote_port = result.stdout.strip()
            except Exception as e:
                log_message("ERROR", f"Failed to get remote port for {service_name}: {e}")
                return None, None

            # Use defined local port for main service, generate for others
            local_port = (
                self.args.k8s_test_local_port
                if service_key == self.test_suite_config.get("main_service", {}).get("service_key")
                else (8081 + hash(service_key) % 100)
            )

            # Capture the actual port returned by the port-forward function
            actual_local_port = start_kubectl_port_forward(self.k8s_namespace, service_name, local_port, remote_port)
            if not actual_local_port:
                return None, None

            # Use the actual_local_port to build the URL
            return f"http://localhost:{actual_local_port}", actual_local_port
        return None, None

    def _gen_payload(self, test_case_config):
        """Generates the payload for the request based on the test case configuration.

        This method can be overridden by subclasses to generate dynamic payloads
        based on the test case configuration. For example, adding timestamps,
        generating random data, or substituting variables from the environment.

        Args:
            test_case_config: Dictionary containing the test case configuration

        Returns:
            Dictionary containing the payload for the request

        Raises:
            ValueError: If payload is not specified or is empty
        """
        if "payload" not in test_case_config:
            raise ValueError(f"Payload is required. Please check config.py for '{self.example_name}' example.")

        payload = test_case_config["payload"]
        if payload is None or not payload:
            raise ValueError(
                f"Payload cannot be None or empty. Please check config.py for '{self.example_name}' example."
            )

        # Return the payload as is (subclasses can override for dynamic payloads)
        return payload

    def _make_request(self, service_key, test_case_config):
        """Makes a single HTTP request to a service endpoint."""
        base_url, _ = self._get_service_url_and_port(service_key)
        if not base_url:
            return {"status": "SKIPPED", "reason": f"Could not determine URL for '{service_key}'"}

        full_url = base_url + test_case_config["path"]
        method = test_case_config.get("method", "GET").upper()
        log_message("INFO", f"Testing {method} {full_url}")

        try:
            payload = self._gen_payload(test_case_config)
            response = self.session.request(
                method,
                full_url,
                json=payload,
                headers=test_case_config.get("headers", {}),
                timeout=test_case_config.get("timeout", 120),
            )
            return {"status_code": response.status_code, "content": response.text, "url": full_url}
        except Exception as e:
            log_message("ERROR", f"An error occurred during the test request for '{full_url}': {e}")
            return {"status": "ERROR", "reason": str(e), "url": full_url}

    def _validate_response(self, response_data, test_case_config):
        """Validates the HTTP response against expected outcomes."""
        test_name = test_case_config.get("name", test_case_config["path"])
        if response_data.get("status") in ["SKIPPED", "ERROR"]:
            log_message("WARN", f"Test '{test_name}': Skipped or Errored - {response_data.get('reason')}")
            self.results["skipped"] += 1
            return False

        passed = True
        error_messages = []

        expect_code = test_case_config.get("expect_code")
        if expect_code and response_data["status_code"] != expect_code:
            passed = False
            error_messages.append(
                f"Test '{test_name}': Expected status {expect_code}, got {response_data['status_code']}"
            )
        # print(response_data["content"])
        expect_contains = test_case_config.get("expect_response_contains")
        if expect_contains and expect_contains not in response_data["content"]:
            passed = False
            error_messages.append(f"Test '{test_name}': Expected response to contain '{expect_contains}'")

        if passed:
            log_message("OK", f"Test '{test_name}' PASSED.")
            self.results["passed"] += 1
        else:
            # Log all validation errors first
            for msg in error_messages:
                log_message("ERROR", msg)
            # Then log the response content for debugging
            log_message("ERROR", f"  -> Failing Response Content: {response_data.get('content', 'N/A')}")
            self.results["failed"] += 1

        return passed

    def run_all_tests(self):
        """Runs connection tests with a retry mechanism for the main service."""
        if not self.test_suite_config:
            log_message("WARN", "No connection tests configured. Skipping.")
            return True

        main_service_passed = False
        main_test = self.test_suite_config.get("main_service")

        if main_test:
            for attempt in range(1, TEST_RETRY_ATTEMPTS + 1):
                log_message("INFO", f"Running main service test (Attempt {attempt}/{TEST_RETRY_ATTEMPTS})...")
                response = self._make_request(main_test["service_key"], main_test)
                # The _validate_response function updates the internal pass/fail counters
                if self._validate_response(response, main_test):
                    main_service_passed = True
                    break

                if attempt < TEST_RETRY_ATTEMPTS:
                    log_message("WARN", f"Test failed. Retrying in {TEST_RETRY_DELAY_S} seconds...")
                    time.sleep(TEST_RETRY_DELAY_S)
                else:
                    log_message("ERROR", f"Main service test failed after {TEST_RETRY_ATTEMPTS} attempts.")

        else:
            log_message("WARN", "No 'main_service' test is configured. Skipping test.")
            self.results["skipped"] += 1
            main_service_passed = True  # Consider it passed if no test is defined.

        # NOTE: The following block is preserved for future diagnostic use.
        # If the main service test fails (main_service_passed is False), this block can be
        # uncommented to automatically run checks on sub-services to help pinpoint the failure.
        # The results of these sub-tests are for logging only and do not alter the overall outcome.
        """
        if not main_service_passed:
            log_message("INFO", "Main service test failed. Running sub-service diagnostics...")
            sub_services_tests = self.test_suite_config.get("sub_services", [])
            if not sub_services_tests:
                log_message("INFO", "No sub-service tests configured for diagnostics.")
            else:
                for sub_test in sub_services_tests:
                    # Run the test and validation, but the result doesn't change the overall 'main_service_passed'
                    response = self._make_request(sub_test["service_key"], sub_test)
                    self._validate_response(response, sub_test) # This will log pass/fail for the sub-service
        """

        if self.deploy_mode == "k8s":
            stop_all_kubectl_port_forwards()

        log_message(
            "INFO",
            f"Test Summary: Passed: {self.results['passed']}, Failed: {self.results['failed']}, Skipped: {self.results['skipped']}",
        )

        return main_service_passed


class AudioQnAConnectionTester(BaseConnectionTester):
    """Specialized ConnectionTester for AudioQnA example."""

    def _gen_payload(self, test_case_config):
        """Generates a dynamic payload for AudioQnA test cases.

        It handles the base64 encoding of audio files if an audio URL is provided.

        Args:
            test_case_config: Dictionary containing the test case configuration

        Returns:
            Dictionary containing the payload for the request
        """

        # Ensure the required Python package is installed
        check_install_python_pkg("pybase64")
        check_install_python_pkg("urllib3")

        import base64
        from urllib.parse import urlparse

        payload = copy.deepcopy(super()._gen_payload(test_case_config))

        # Read audio from URL + base64 encoding if present
        if "audio" in payload and payload["audio"]:
            audio_value = payload["audio"]

            # Check if the value is a valid URL
            parsed_url = urlparse(audio_value)
            is_url = all([parsed_url.scheme in ("http", "https"), parsed_url.netloc])

            if is_url:
                log_message("INFO", f"Converting audio from URL: {audio_value}")

                # Download the audio file content
                audio_response = requests.get(audio_value, stream=True, timeout=60)
                audio_response.raise_for_status()  # Ensure successful download

                # Base64 encoding
                audio_content = audio_response.content
                audio_base64 = base64.b64encode(audio_content).decode("utf-8")

                # Replace the URL with the encoded audio
                payload["audio"] = audio_base64
                log_message("INFO", "Successfully completed base64 encoding.")

            else:
                is_base64 = True
                try:
                    base64.b64decode(audio_value)
                except (ValueError, TypeError):
                    is_base64 = False

                if not is_base64:
                    raise ValueError("Audio value is not a valid URL or a Base64 string.")

        else:
            raise ValueError("Audio key not found or empty in payload. Please check config.py for 'AudioQnA' example.")
        return payload


class ConnectionTesterFactory:
    """Factory class to create ConnectionTester instances based on example name."""

    @staticmethod
    def create_tester(example_name, deploy_mode, device, args_namespace):
        """Creates a ConnectionTester instance based on the example name.

        Args:
            example_name: Name of the example to create tester for
            deploy_mode: Deployment mode (docker, k8s)
            device: Target device
            args_namespace: Command line arguments

        Returns:
            An appropriate ConnectionTester instance for the example
        """
        if example_name == "AudioQnA":
            return AudioQnAConnectionTester(example_name, deploy_mode, device, args_namespace)
        # Add additional specialized testers here as needed
        return BaseConnectionTester(example_name, deploy_mode, device, args_namespace)
