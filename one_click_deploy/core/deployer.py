# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import time

import click

from .config import (
    CLEANUP_ON_DEPLOY_FAILURE,
    COMMON_SCRIPTS_DIR,
    EXAMPLE_CONFIGS,
    EXAMPLES_ROOT_DIR,
    K8S_VLLM_SKIP_WARMUP,
    POST_DEPLOY_WAIT_S,
)
from .tester import ConnectionTesterFactory
from .utils import (
    get_conflicting_ports_from_compose,
    get_host_ip,
    get_huggingface_token_from_file,
    get_var_from_shell_script,
    log_message,
    parse_shell_env_file,
    run_command,
    section_header,
    update_helm_values_yaml,
    update_or_create_set_env,
)


class Deployer:
    """Manages the interactive deployment and clearing of a GenAIExample."""

    def __init__(self, args_namespace):
        self.args = args_namespace
        self.example_name = self.args.example
        self.config = EXAMPLE_CONFIGS[self.example_name]
        self.example_root = EXAMPLES_ROOT_DIR / self.config["base_dir"]
        self.compose_command = "docker compose"
        self.project_name = None

    def _capture_docker_logs_on_failure(self):
        """Captures logs from all services in a Docker Compose project on failure."""
        if not self.project_name:
            log_message("WARN", "Docker project name not set, cannot capture logs.")
            return

        log_message("INFO", f"Capturing Docker logs for project '{self.project_name}'...")
        compose_base_cmd = self._get_compose_command_base()
        if not compose_base_cmd:
            log_message("ERROR", "Could not construct base command for Docker logs.")
            return

        log_cmd = compose_base_cmd + ["logs", "--no-color", "--tail=200"]

        try:
            result = run_command(log_cmd, capture_output=True, check=False, display_cmd=True)
            log_header = f"\n\n{'='*20} DOCKER LOGS ON FAILURE ({self.project_name}) {'='*20}\n"
            log_footer = f"\n{'='*20} END OF DOCKER LOGS {'='*20}\n\n"

            log_message("INFO", log_header, to_console=False)
            if result.stdout:
                log_message("INFO", result.stdout, to_console=False)
            if result.stderr:
                log_message("WARN", result.stderr, to_console=False)
            log_message("INFO", log_footer, to_console=False)

            log_message("OK", f"Diagnostic logs for Docker project '{self.project_name}' saved to deployment.log")

        except Exception as e:
            log_message("ERROR", f"An exception occurred while trying to capture Docker logs: {e}")

    def _capture_k8s_logs_on_failure(self):
        """Captures pod descriptions and logs from a Kubernetes namespace on failure."""
        ns = self.config.get("kubernetes", {}).get("namespace")
        if not ns:
            log_message("WARN", "Kubernetes namespace not configured, cannot capture logs.")
            return

        log_message("INFO", f"Capturing Kubernetes diagnostic info from namespace '{ns}'...")
        log_header = f"\n\n{'='*20} KUBERNETES DIAGNOSTICS ON FAILURE ({ns}) {'='*20}\n"
        log_footer = f"\n{'='*20} END OF K8S DIAGNOSTICS {'='*20}\n\n"

        log_message("INFO", log_header, to_console=False)

        try:
            # 1. Get all pods status
            log_message("INFO", "\n--- Pod Status ---\n", to_console=False)
            get_pods_cmd = ["kubectl", "get", "pods", "-n", ns, "-o", "wide"]
            pods_status = run_command(get_pods_cmd, capture_output=True, check=False, display_cmd=True)
            if pods_status.stdout:
                log_message("INFO", pods_status.stdout, to_console=False)
            if pods_status.stderr:
                log_message("WARN", pods_status.stderr, to_console=False)

            # 2. Get pod names
            get_pod_names_cmd = ["kubectl", "get", "pods", "-n", ns, "-o", "jsonpath={.items[*].metadata.name}"]
            pod_names_result = run_command(get_pod_names_cmd, capture_output=True, check=False, display_cmd=False)
            pod_names = pod_names_result.stdout.strip().split()

            if not pod_names:
                log_message("WARN", "No pods found in the namespace.", to_console=False)
                return

            # 3. For each pod, get description and logs
            for pod_name in pod_names:
                log_message("INFO", f"\n--- Description for pod: {pod_name} ---\n", to_console=False)
                describe_cmd = ["kubectl", "describe", "pod", pod_name, "-n", ns]
                describe_result = run_command(describe_cmd, capture_output=True, check=False, display_cmd=True)
                if describe_result.stdout:
                    log_message("INFO", describe_result.stdout, to_console=False)

                log_message("INFO", f"\n--- Logs for pod: {pod_name} ---\n", to_console=False)
                logs_cmd = ["kubectl", "logs", pod_name, "-n", ns, "--all-containers=true", "--tail=200"]
                logs_result = run_command(logs_cmd, capture_output=True, check=False, display_cmd=True)
                if logs_result.stdout:
                    log_message("INFO", logs_result.stdout, to_console=False)
                if logs_result.stderr:
                    log_message("WARN", logs_result.stderr, to_console=False)

        except Exception as e:
            log_message("ERROR", f"An exception occurred while trying to capture K8s logs: {e}")
        finally:
            log_message("INFO", log_footer, to_console=False)
            log_message("OK", f"Diagnostic logs for K8s namespace '{ns}' saved to deployment.log")

    def _get_compose_command_base(self):
        """Constructs the base docker compose command with project and compose files."""
        if not self.project_name:
            self.project_name = f"{self.example_name.lower().replace(' ', '')}-{self.args.device}"
        compose_files = self._get_docker_compose_files()
        if not compose_files:
            return None
        cmd = self.compose_command.split()
        cmd.extend(["-p", self.project_name])
        for f in compose_files:
            cmd.extend(["-f", str(f.resolve())])
        return cmd

    def _get_path_from_config(self, config_keys, device_specific_key=None):
        """Helper to safely retrieve a path or list of paths from the configuration."""
        current_level = self.config
        for key in config_keys:
            if not isinstance(current_level, dict) or key not in current_level:
                return None
            current_level = current_level[key]
        path_or_paths = (
            current_level.get(device_specific_key)
            if device_specific_key and isinstance(current_level, dict)
            else (current_level if isinstance(current_level, (str, list)) else None)
        )
        if not path_or_paths:
            return None
        if isinstance(path_or_paths, str):
            path_or_paths = [path_or_paths]
        resolved_paths = []
        for p in path_or_paths:
            if os.path.isabs(p):
                resolved_paths.append(pathlib.Path(p))
            else:
                resolved_paths.append(self.example_root / p)
        return resolved_paths

    def _get_device_specific_or_common_config(self, key_path):
        """Retrieves a configuration value, handling device-specific overrides."""
        current_level = self.config
        try:
            for key in key_path:
                current_level = current_level[key]
        except (KeyError, TypeError):
            return None
        if isinstance(current_level, dict) and self.args.device in current_level:
            return current_level[self.args.device]
        return current_level

    def _get_docker_compose_files(self):
        """Returns a list of Docker Compose file paths."""
        return self._get_path_from_config(["docker_compose", "paths"], self.args.device)

    def _get_docker_set_env_script(self):
        """Returns the path to the set_env script."""
        path_or_paths = self._get_path_from_config(["docker_compose", "set_env_scripts"], self.args.device)
        return path_or_paths[0] if path_or_paths else None

    def _get_local_env_file_path(self):
        """Determines the path for the local 'set_env.local.sh' file."""
        base_script_path = self._get_docker_set_env_script()
        if base_script_path:
            return base_script_path.with_name(f"{base_script_path.stem}.local{base_script_path.suffix}")
        else:
            compose_files = self._get_docker_compose_files()
            if compose_files:
                compose_dir = compose_files[0].parent
                return compose_dir / "set_env.local.sh"
        return None

    def _get_helm_values_file(self):
        """Gets the original Helm values file path."""
        paths = self._get_path_from_config(["kubernetes", "helm", "values_files"], self.args.device)
        return paths[0] if paths else None

    def _get_local_helm_values_file_path(self):
        """Constructs the path for the local (temporary) Helm values file."""
        base_values_path = self._get_helm_values_file()
        if not base_values_path:
            return None
        return base_values_path.with_name(f"{base_values_path.stem}.local{base_values_path.suffix}")

    def run_interactive_deployment(self):
        """Orchestrates the deployment flow with intelligent pre-flight checks."""
        if not self._interactive_setup_for_deploy():
            log_message("INFO", "Deployment setup aborted by user.")
            return

        if self.args.do_check_env and not self.check_environment():
            log_message("ERROR", "Environment check failed. Aborting deployment.")
            return
        if self.args.do_update_images and not self.update_images():
            log_message("ERROR", "Image update failed. Aborting deployment.")
            return
        if not self.configure_services():
            log_message("ERROR", "Service configuration failed. Aborting deployment.")
            return

        if self.args.deploy_mode == "docker":
            self.project_name = f"{self.example_name.lower().replace(' ', '')}-{self.args.device}"
            log_message("INFO", f"Using Docker Compose project name: '{self.project_name}'")
            compose_base_cmd = self._get_compose_command_base()
            if not compose_base_cmd:
                log_message("ERROR", "Could not construct Docker Compose command. Check config.")
                return
            try:
                result = run_command(
                    compose_base_cmd + ["ps", "-q"], capture_output=True, check=False, display_cmd=False
                )
                is_running = result.stdout.strip() != ""
                if is_running:
                    log_message("WARN", f"An instance of '{self.example_name}' appears to be already running.")
                    if click.confirm("Do you want to stop the current instance and redeploy/update it?", default=True):
                        log_message("INFO", "Stopping existing services...")
                        self.clear_deployment(clear_local_config=False)
                    else:
                        log_message("INFO", "Deployment aborted by user.")
                        return
                else:
                    local_env_file = self._get_local_env_file_path()
                    env_vars = parse_shell_env_file(local_env_file)
                    conflicting_ports = get_conflicting_ports_from_compose(self._get_docker_compose_files(), env_vars)
                    if conflicting_ports:
                        log_message(
                            "ERROR",
                            f"Deployment aborted. Ports are in use by other applications: {sorted(conflicting_ports)}",
                        )
                        return
            except Exception as e:
                log_message("ERROR", f"Failed during pre-deployment check: {e}")
                return

        try:
            log_message("INFO", "Starting deployment...")
            if not self.deploy():
                raise RuntimeError("Deployment command failed to execute successfully.")
            log_message("OK", "Deployment process completed successfully.")
        except Exception as e:
            log_message("ERROR", f"Deployment failed: {e}")
            log_message("INFO", "Capturing diagnostic logs due to deployment failure...")
            if self.args.deploy_mode == "docker":
                self._capture_docker_logs_on_failure()
            elif self.args.deploy_mode == "k8s":
                self._capture_k8s_logs_on_failure()
            if CLEANUP_ON_DEPLOY_FAILURE:
                log_message("INFO", "Attempting automatic cleanup as configured...")
                try:
                    self.clear_deployment()
                    log_message("OK", "Automatic cleanup successful.")
                except Exception as cleanup_e:
                    log_message(
                        "ERROR", f"Automatic cleanup ALSO FAILED: {cleanup_e}. Please check your environment manually."
                    )
            else:
                log_message("WARN", "Automatic cleanup is disabled. The failed environment is preserved for debugging.")
                if self.args.deploy_mode == "docker":
                    log_message("INFO", f"You can inspect logs using: docker compose -p {self.project_name} logs")
                elif self.args.deploy_mode == "k8s":
                    ns = self.config["kubernetes"]["namespace"]
                    log_message("INFO", f"Inspect pods with 'kubectl get pods -n {ns}'.")
            return

        if self.args.do_test_connection:
            log_message("INFO", f"Waiting for {POST_DEPLOY_WAIT_S} seconds for services to stabilize before testing...")
            for i in range(POST_DEPLOY_WAIT_S, 0, -10):
                print(f"\r... {i} seconds remaining...  ", end="")
                time.sleep(min(10, i))
            print("\rWait complete. Starting tests.        ")

            if not self.test_connection():
                log_message("WARN", "Connection tests failed. The services are still running.")
                if self.args.deploy_mode == "docker":
                    self._capture_docker_logs_on_failure()
                elif self.args.deploy_mode == "k8s":
                    self._capture_k8s_logs_on_failure()

                if self.args.deploy_mode == "docker":
                    log_message("INFO", f"Please inspect logs using: docker compose -p {self.project_name} logs")
                elif self.args.deploy_mode == "k8s":
                    ns = self.config["kubernetes"]["namespace"]
                    log_message("INFO", f"Please inspect pod status with 'kubectl get pods -n {ns}'.")
            else:
                log_message("OK", "All connection tests passed.")

    def _interactive_setup_for_deploy(self):
        section_header(f"{self.example_name} Interactive Deployment Setup")
        self.args.deploy_mode = click.prompt("Deployment Mode", type=click.Choice(["docker", "k8s"]), default="docker")
        self.args.device = click.prompt(
            "Target Device",
            type=click.Choice(self.config.get("supported_devices")),
            default=self.config.get("default_device"),
        )
        cached_token = get_huggingface_token_from_file()
        self.args.hf_token = click.prompt(
            f"Hugging Face Token{' (cached found)' if cached_token else ''}",
            default=cached_token or "your-hf-token-here",
            show_default=False,
        )
        self.args.http_proxy = click.prompt("HTTP Proxy", default=os.environ.get("http_proxy", ""), show_default=True)
        self.args.https_proxy = click.prompt(
            "HTTPS Proxy", default=os.environ.get("https_proxy", ""), show_default=True
        )
        env_no_proxy, host_ip = os.environ.get("no_proxy", ""), get_host_ip()
        user_no_proxy = click.prompt("No Proxy hosts", default=env_no_proxy, show_default=True)
        no_proxy_set = {"localhost", "127.0.0.1", host_ip}
        if env_no_proxy:
            no_proxy_set.update(p.strip() for p in env_no_proxy.split(",") if p.strip())
        if user_no_proxy:
            no_proxy_set.update(p.strip() for p in user_no_proxy.split(",") if p.strip())
        self.args.no_proxy = ",".join(sorted(list(no_proxy_set)))

        interactive_params = self._get_device_specific_or_common_config(["interactive_params"]) or []

        for param in interactive_params:
            if "modes" in param and self.args.deploy_mode not in param["modes"]:
                setattr(self.args, param["name"], None)
                continue

            prompt_text = param["prompt"]
            help_text = param.get("help")
            if help_text:
                prompt_text = f"{prompt_text} ({help_text})"

            default_value = param.get("default")
            is_required = param.get("required", False)

            user_input = click.prompt(prompt_text, default=default_value, type=param.get("type", str))

            while is_required and (not user_input or user_input == default_value):
                log_message("WARN", f"A valid '{param['prompt']}' is required. Please provide a real value.")
                user_input = click.prompt(prompt_text, type=param.get("type", str), default=None)

            setattr(self.args, param["name"], user_input)

        self.args.do_check_env = click.confirm("Run environment check?", default=False, show_default=True)

        self.args.do_update_images = click.confirm("Update images (build/push)?", default=False, show_default=True)

        self.args.build_images = False
        self.args.push_images = False
        self.args.setup_local_registry = False
        self.args.registry = ""

        if self.args.do_update_images:
            self.args.build_images = click.confirm("  -> Build images locally?", default=True, show_default=True)

            self.args.push_images = click.confirm("  -> Push images to a registry?", default=False, show_default=True)

            if self.args.push_images:
                self.args.setup_local_registry = click.confirm(
                    "     -> Use a temporary local registry (localhost:5000) for this push?",
                    default=False,
                    show_default=True,
                )
                if not self.args.setup_local_registry:
                    self.args.registry = click.prompt(
                        "     -> Enter the target remote registry URL (e.g., docker.io/myuser)",
                        default="",
                        show_default=False,
                    )

        self.args.do_test_connection = click.confirm(
            "Run connection tests after deployment?", default=False, show_default=True
        )
        if self.args.deploy_mode == "k8s" and self.args.do_test_connection:
            self.args.k8s_test_local_port = click.prompt("  -> Local port for K8s test access", type=int, default=8080)

        section_header("Configuration Summary")
        for k, v in vars(self.args).items():
            if v is not None and v != "":
                log_message(
                    "INFO",
                    f"  {k.replace('_', ' ').title()}: {'**********' if k == 'hf_token' or k.endswith('_key') else v}",
                )
        return click.confirm("Proceed with deployment?", default=True)

    def run_interactive_clear(self):
        """Orchestrates the interactive clearing of a deployment."""
        if not self._interactive_setup_for_clear():
            log_message("INFO", "Clear operation aborted by user.")
            return

        try:
            self.clear_deployment()
            log_message("OK", "Cleanup process completed successfully.")
        except Exception as e:
            log_message("ERROR", f"An unexpected error occurred during cleanup: {e}")

    def _interactive_setup_for_clear(self):
        section_header(f"{self.example_name} Interactive Clear Setup")
        self.args.deploy_mode = click.prompt(
            "Which deployment mode to clear?", type=click.Choice(["docker", "k8s"]), default="docker"
        )

        if self.args.deploy_mode == "docker":
            self.args.device = click.prompt(
                "On which target device was it deployed?",
                type=click.Choice(self.config.get("supported_devices")),
                default=self.config.get("default_device"),
            )
            # Set project name for clearing
            self.project_name = f"{self.example_name.lower().replace(' ', '')}-{self.args.device}"
        else:
            self.args.device = self.config.get("default_device")

        if self.args.deploy_mode == "k8s":
            self.args.delete_namespace_on_clear = click.confirm(
                f"Also delete the '{self.config['kubernetes']['namespace']}' namespace entirely?", default=False
            )

        log_message("INFO", f"Will attempt to clear '{self.example_name}' deployed via {self.args.deploy_mode}.")
        return click.confirm("Proceed with clearing?", default=True)

    def run_interactive_test(self):
        """Orchestrates the interactive testing of an existing deployment."""
        if not self._interactive_setup_for_test():
            log_message("INFO", "Test operation aborted by user.")
            return

        try:
            self.test_connection()
            log_message("OK", "Testing process completed.")
        except Exception as e:
            log_message("ERROR", f"An unexpected error occurred during testing: {e}")

    def _interactive_setup_for_test(self):
        """Gathers necessary information for testing and updates self.args."""
        section_header(f"{self.example_name} Interactive Connection Test Setup")

        self.args.deploy_mode = click.prompt(
            "How is the service deployed?", type=click.Choice(["docker", "k8s"]), default="docker"
        )
        self.args.device = click.prompt(
            "On which target device is it running?",
            type=click.Choice(self.config.get("supported_devices")),
            default=self.config.get("default_device"),
        )
        if self.args.deploy_mode == "docker":
            self.project_name = f"{self.example_name.lower().replace(' ', '')}-{self.args.device}"

        self.args.http_proxy = click.prompt("HTTP Proxy", default=os.environ.get("http_proxy", ""), show_default=True)
        self.args.https_proxy = click.prompt(
            "HTTPS Proxy", default=os.environ.get("https_proxy", ""), show_default=True
        )

        env_no_proxy, host_ip = os.environ.get("no_proxy", ""), get_host_ip()
        user_no_proxy = click.prompt("No Proxy hosts", default=env_no_proxy, show_default=True)
        no_proxy_set = {"localhost", "127.0.0.1", host_ip}
        if env_no_proxy:
            no_proxy_set.update(p.strip() for p in env_no_proxy.split(",") if p.strip())
        if user_no_proxy:
            no_proxy_set.update(p.strip() for p in user_no_proxy.split(",") if p.strip())
        self.args.no_proxy = ",".join(sorted(list(no_proxy_set)))

        if self.args.deploy_mode == "k8s":
            self.args.k8s_test_local_port = click.prompt("  -> Local port for K8s test access", type=int, default=8080)

        section_header("Configuration Summary")
        log_message("INFO", f"  Test Target: {self.example_name}")
        log_message("INFO", f"  Deployment Mode: {self.args.deploy_mode}")
        log_message("INFO", f"  Device: {self.args.device}")
        log_message("INFO", f"  HTTP Proxy: {self.args.http_proxy or 'Not set'}")
        log_message("INFO", f"  HTTPS Proxy: {self.args.https_proxy or 'Not set'}")
        log_message("INFO", f"  No Proxy: {self.args.no_proxy or 'Not set'}")

        if self.args.deploy_mode == "k8s":
            log_message("INFO", f"  K8s Local Port: {self.args.k8s_test_local_port}")

        return click.confirm("Proceed with connection tests?", default=True)

    def check_environment(self):
        section_header("Checking Environment")
        script_path = COMMON_SCRIPTS_DIR / "check_env.sh"
        if not script_path.exists():
            log_message("WARN", f"{script_path} not found. Skipping environment check.")
            return True
        try:
            run_command(["bash", str(script_path), "--device", self.args.device], check=True)
            log_message("OK", "Environment check passed.")
            return True
        except Exception as e:
            log_message("ERROR", f"Environment check failed: {e}")
            return False

    def update_images(self):
        """Builds and/or pushes Docker images by calling the update_images.sh script."""
        section_header("Updating Container Images")

        script_path = COMMON_SCRIPTS_DIR / "update_images.sh"
        if not script_path.exists():
            log_message("WARN", f"Image update script '{script_path}' not found. Skipping this step.")
            return True

        cmd = ["bash", str(script_path), "--example", self.example_name, "--device", self.args.device]

        if getattr(self.args, "setup_local_registry", False):
            cmd.append("--setup-registry")
        if getattr(self.args, "build_images", False):
            cmd.append("--build")
        if getattr(self.args, "push_images", False):
            cmd.append("--push")
            if getattr(self.args, "registry", None):
                cmd.extend(["--registry", self.args.registry])

        if not any(
            [
                getattr(self.args, "setup_local_registry", False),
                getattr(self.args, "build_images", False),
                getattr(self.args, "push_images", False),
            ]
        ):
            log_message("INFO", "No image action selected. Skipping.")
            return True

        try:
            run_command(cmd, check=True)
            log_message("OK", "Image update process completed successfully.")
            return True
        except Exception as e:
            log_message("ERROR", f"The image update script failed. Check logs for details. Error: {e}")
            return False

    def configure_services(self):
        section_header(f"Configuring Services for {self.example_name} ({self.args.deploy_mode})")

        if self.args.deploy_mode == "docker":
            return self._configure_docker()
        elif self.args.deploy_mode == "k8s":
            return self._configure_kubernetes()
        return True

    def _configure_docker(self):
        source_env_file = self._get_docker_set_env_script()
        local_env_file = self._get_local_env_file_path()

        if not source_env_file:
            log_message("ERROR", "Source environment file not found in configuration.")
            return False

        params_to_env_map = self._get_device_specific_or_common_config(["docker_compose", "params_to_set_env"]) or {}

        updates = {
            env_var: getattr(self.args, arg_name)
            for arg_name, env_var in params_to_env_map.items()
            if hasattr(self.args, arg_name) and getattr(self.args, arg_name) is not None
        }

        user_proxies = {p.strip() for p in self.args.no_proxy.split(",") if p.strip()}
        script_no_proxy_str = get_var_from_shell_script(source_env_file, "no_proxy")
        script_proxies = (
            {p.strip() for p in script_no_proxy_str.split(",") if p.strip()} if script_no_proxy_str else set()
        )

        merged_proxies = user_proxies.union(script_proxies)
        final_no_proxy = ",".join(sorted(list(merged_proxies)))

        host_ip_value = get_host_ip()
        updates.update(
            {
                "http_proxy": self.args.http_proxy,
                "https_proxy": self.args.https_proxy,
                "no_proxy": final_no_proxy,
                "host_ip": host_ip_value,
                "HOST_IP": host_ip_value,
            }
        )
        return update_or_create_set_env(source_env_file, local_env_file, updates)

    def _configure_kubernetes(self):
        original_values_file = self._get_helm_values_file()
        local_values_file = self._get_local_helm_values_file_path()

        if not original_values_file or not original_values_file.exists():
            log_message("ERROR", f"Helm values file not found: {original_values_file}. Cannot configure.")
            return False

        try:
            shutil.copy2(original_values_file, local_values_file)
            log_message("INFO", f"Created local values file '{local_values_file.name}' for this deployment.")
        except Exception as e:
            log_message("ERROR", f"Failed to create local values file: {e}")
            return False

        params_to_values = self.config["kubernetes"]["helm"]["params_to_values"]
        updates = {}
        for name, path_or_paths in params_to_values.items():
            if hasattr(self.args, name):
                value = getattr(self.args, name)
                if value is None:
                    continue

                if isinstance(path_or_paths, list):
                    for path in path_or_paths:
                        updates[path] = value
                else:
                    updates[path_or_paths] = value

        if K8S_VLLM_SKIP_WARMUP:
            # Heuristic check: only add this setting if the values.yaml seems to be for vLLM.
            # This prevents adding it to examples that don't use vLLM.
            if "vllm:" in original_values_file.read_text():
                log_message(
                    "INFO",
                    "Global flag K8S_VLLM_SKIP_WARMUP is True. Adding 'vllm.VLLM_SKIP_WARMUP: True' to Helm values.",
                )
                updates["vllm.VLLM_SKIP_WARMUP"] = True
            else:
                log_message(
                    "DEBUG",
                    f"K8S_VLLM_SKIP_WARMUP is on, but 'vllm:' key not found in {original_values_file.name}. Skipping addition.",
                )

        if update_helm_values_yaml(local_values_file, updates):
            log_message("OK", f"Successfully updated local Helm values in {local_values_file.name}.")
            return True
        else:
            log_message("ERROR", f"Failed to update Helm values in {local_values_file.name}.")
            return False

    def deploy(self):
        section_header(f"Executing Deployment for {self.example_name} ({self.args.deploy_mode})")

        if self.args.deploy_mode == "docker":
            compose_base_cmd = self._get_compose_command_base()
            if not compose_base_cmd:
                return False

            local_env_file = self._get_local_env_file_path()
            if not local_env_file or not local_env_file.exists():
                log_message("ERROR", f"Local environment script '{local_env_file}' not found. Cannot deploy.")
                return False

            compose_up_cmd = " ".join(compose_base_cmd + ["up", "-d", "--remove-orphans"])
            if self.example_name == "ChatQnA" and self.args.device == "gaudi":
                compose_up_cmd = "source .env&&" + compose_up_cmd
            compose_dir = self._get_docker_compose_files()[0].parent
            local_env_dir = local_env_file.parent

            script_content = f"""#!/bin/bash
set -e
trap 'echo "ERROR: A command failed at line $LINENO. Exiting." >&2' ERR
cd "{local_env_dir.resolve()}"
source "{local_env_file.resolve()}"
cd "{compose_dir.resolve()}"
{compose_up_cmd}
"""
            temp_script_path = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh", dir=".") as f:
                    f.write(script_content)
                    temp_script_path = f.name
                os.chmod(temp_script_path, stat.S_IRWXU)
                run_command(["/bin/bash", temp_script_path], check=True, stream_output=True)
                return True
            except subprocess.CalledProcessError:
                log_message("ERROR", "Deployment script failed to execute. See detailed logs above.")
                return False
            except Exception as e:
                log_message("ERROR", f"An unexpected error occurred during Docker Compose deployment: {e}")
                return False
            finally:
                if temp_script_path and os.path.exists(temp_script_path):
                    os.remove(temp_script_path)

        elif self.args.deploy_mode == "k8s":
            cfg = self.config["kubernetes"]
            local_values_file = self._get_local_helm_values_file_path()

            if not local_values_file or not local_values_file.exists():
                log_message("ERROR", f"Local Helm values file '{local_values_file}' not found. Cannot deploy.")
                return False

            cmd = [
                "helm",
                "install",
                cfg["release_name"],
                cfg["helm"]["chart_oci"],
                "--namespace",
                cfg["namespace"],
                "--create-namespace",
                "-f",
                str(local_values_file),
            ]
            try:
                run_command(cmd, check=True)
                log_message("OK", f"Helm release '{cfg['release_name']}' deployed. Waiting for pods to stabilize...")
                time.sleep(30)
                return True
            except Exception as e:
                log_message("ERROR", f"Helm deployment failed during execution: {e}")
                return False
        return False

    def clear_deployment(self, clear_local_config=True):
        section_header(f"Clearing Deployment for {self.example_name} ({self.args.deploy_mode})")

        if self.args.deploy_mode == "docker":
            compose_base_cmd = self._get_compose_command_base()
            if not compose_base_cmd:
                log_message("WARN", "Could not construct Docker Compose command. Cannot clear.")
                return True
            cmd_list = compose_base_cmd + ["down", "-v", "--remove-orphans"]
            try:
                result = run_command(cmd_list, check=False, capture_output=True, display_cmd=True)
                if result.returncode != 0:
                    log_message("ERROR", f"Docker Compose down command failed with exit code {result.returncode}.")
                    if result.stdout:
                        log_message("ERROR", f"  STDOUT: {result.stdout.strip()}")
                    if result.stderr:
                        log_message("ERROR", f"  STDERR: {result.stderr.strip()}")
                else:
                    log_message("OK", "Docker Compose services stopped and removed.")
                if clear_local_config:
                    local_env_file = self._get_local_env_file_path()
                    if local_env_file and local_env_file.exists():
                        local_env_file.unlink()
                        log_message("INFO", f"Removed generated config file: {local_env_file.name}")
                return result.returncode == 0
            except Exception as e:
                log_message("ERROR", f"Failed to clear Docker Compose deployment: {e}")
                return False

        elif self.args.deploy_mode == "k8s":
            cfg = self.config["kubernetes"]
            try:
                run_command(["helm", "uninstall", cfg["release_name"], "--namespace", cfg["namespace"]], check=False)
                log_message("OK", f"Helm release '{cfg['release_name']}' uninstalled.")
            except Exception as e:
                log_message("WARN", f"Helm uninstall may have failed: {e}")
            local_values_file = self._get_local_helm_values_file_path()
            if local_values_file and local_values_file.exists():
                try:
                    local_values_file.unlink()
                    log_message("INFO", f"Removed local Helm values file: {local_values_file.name}")
                except OSError as e:
                    log_message("WARN", f"Could not remove local values file {local_values_file}: {e}")
            if getattr(self.args, "delete_namespace_on_clear", False):
                log_message("INFO", f"Deleting namespace '{cfg['namespace']}' as requested.")
                try:
                    run_command(
                        ["kubectl", "delete", "namespace", cfg["namespace"], "--ignore-not-found=true"], check=True
                    )
                    log_message("OK", f"Namespace '{cfg['namespace']}' deleted.")
                except Exception as e:
                    log_message("ERROR", f"Failed to delete namespace: {e}")
                    return False
            return True
        return False

    def test_connection(self):
        """Creates a ConnectionTester and runs all tests.

        It uses self.args, which has been populated by the interactive setup methods.
        """
        section_header(f"Testing Connection for {self.example_name}")
        tester = ConnectionTesterFactory.create_tester(
            self.example_name, self.args.deploy_mode, self.args.device, self.args
        )
        return tester.run_all_tests()
