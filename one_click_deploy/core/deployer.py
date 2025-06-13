# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import time

import click

from .config import COMMON_SCRIPTS_DIR, EXAMPLE_CONFIGS, EXAMPLES_ROOT_DIR
from .tester import ConnectionTester
from .utils import (
    get_host_ip,
    get_huggingface_token_from_file,
    log_message,
    run_command,
    section_header,
    update_helm_values_yaml,
    update_or_create_set_env,
    get_var_from_shell_script,
)


class Deployer:
    """Manages the interactive deployment and clearing of a GenAIExample."""

    def __init__(self, args_namespace):
        self.args = args_namespace
        self.example_name = self.args.example
        self.config = EXAMPLE_CONFIGS[self.example_name]
        self.example_root = EXAMPLES_ROOT_DIR / self.config["base_dir"]
        self.compose_command = "docker compose"

    def _get_path_from_config(self, config_keys, device_specific_key=None):
        current_level = self.config
        for key in config_keys:
            if not isinstance(current_level, dict) or key not in current_level:
                return None
            current_level = current_level[key]
        path_str = (
            current_level.get(device_specific_key)
            if device_specific_key and isinstance(current_level, dict)
            else (current_level if isinstance(current_level, str) else None)
        )
        return self.example_root / path_str if path_str else None

    # Docker helpers
    def _get_docker_compose_file(self):
        return self._get_path_from_config(["docker_compose", "paths"], self.args.device)

    def _get_docker_set_env_script(self):
        return self._get_path_from_config(["docker_compose", "set_env_scripts"], self.args.device)

    def _get_local_env_file_path(self):
        base_script_path = self._get_docker_set_env_script()
        if not base_script_path:
            compose_dir = self._get_docker_compose_file().parent
            return compose_dir / "set_env.local.sh"
        return base_script_path.with_name(f"{base_script_path.stem}.local{base_script_path.suffix}")

    def _get_helm_values_file(self):
        """Gets the original Helm values file path."""
        return self._get_path_from_config(["kubernetes", "helm", "values_files"], self.args.device)

    def _get_local_helm_values_file_path(self):
        """Constructs the path for the local (temporary) Helm values file."""
        base_values_path = self._get_helm_values_file()
        if not base_values_path:
            return None
        return base_values_path.with_name(f"{base_values_path.stem}.local{base_values_path.suffix}")

    def run_interactive_deployment(self):
        """Orchestrates the deployment flow with automatic cleanup on failure."""
        if not self._interactive_setup_for_deploy():
            log_message("INFO", "Deployment setup aborted by user.")
            return

        all_steps_succeeded = False
        try:
            success = True

            if self.args.do_check_env:
                success = self.check_environment()

            if success and self.args.do_update_images:
                success = self.update_images()

            if success:
                success = self.configure_services()

            if success:
                success = self.deploy()

            if success and self.args.do_test_connection:
                success = self.test_connection()

            all_steps_succeeded = success

        except Exception as e:
            log_message("ERROR", f"An unexpected error occurred during deployment: {e}")
            all_steps_succeeded = False

        finally:
            if not all_steps_succeeded:
                log_message("ERROR", "Deployment failed. Triggering automatic cleanup.")
                try:
                    # We need self.args.deploy_mode and self.args.device to be set for cleanup
                    if hasattr(self, "args") and hasattr(self.args, "deploy_mode") and self.args.deploy_mode:
                        self.clear_deployment()
                        log_message("OK", "Automatic cleanup has finished.")
                    else:
                        log_message("WARN", "Cannot run automatic cleanup: deployment mode not set.")
                except Exception as cleanup_e:
                    log_message(
                        "ERROR", f"Automatic cleanup ALSO FAILED: {cleanup_e}. Please check your environment manually."
                    )
            else:
                log_message("OK", "Deployment process completed successfully.")

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

        for param in self.config.get("interactive_params", []):
            # Skip parameters not relevant for the chosen deployment mode
            if "modes" in param and self.args.deploy_mode not in param["modes"]:
                setattr(self.args, param["name"], None)
                continue

            prompt_text = param["prompt"]
            help_text = param.get("help")
            if help_text:
                prompt_text = f"{prompt_text} ({help_text})"

            user_input = click.prompt(prompt_text, default=param.get("default"), type=param.get("type", str))
            setattr(self.args, param["name"], user_input)

        self.args.do_check_env = click.confirm("Run environment check?", default=False, show_default=True)
        self.args.do_update_images = click.confirm("Build or Push images?", default=False, show_default=True)
        if self.args.do_update_images:
            self.args.setup_local_registry = click.confirm(
                "  -> Set up a local registry for this run? (creates 'localhost:5000' registry)",
                default=False,
                show_default=True,
            )
            self.args.build_images = click.confirm("  -> Build images?", default=False, show_default=True)
            self.args.push_images = click.confirm("  -> Push images?", default=False, show_default=True)

            if self.args.push_images and not self.args.setup_local_registry:
                self.args.registry = click.prompt(
                    "     Enter container registry URL (e.g., docker.io/myuser)", default="", show_default=False
                )
            else:
                self.args.registry = ""

        self.args.do_test_connection = click.confirm(
            "Run connection tests after deployment?", default=False, show_default=True
        )
        if self.args.deploy_mode == "k8s" and self.args.do_test_connection:
            self.args.k8s_test_local_port = click.prompt("  -> Local port for K8s test access", type=int, default=8080)

        section_header("Configuration Summary")
        for k, v in vars(self.args).items():
            if v is not None and v != "":
                log_message("INFO", f"  {k.replace('_', ' ').title()}: {'**********' if k == 'hf_token' and v else v}")
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
        # Step 1: Gather all necessary parameters interactively.
        if not self._interactive_setup_for_test():
            log_message("INFO", "Test operation aborted by user.")
            return

        try:
            # Step 2: With the updated self.args, call the actual test method.
            self.test_connection()
            log_message("OK", "Testing process completed.")
        except Exception as e:
            log_message("ERROR", f"An unexpected error occurred during testing: {e}")

    def _interactive_setup_for_test(self):
        """Gathers necessary information for testing and updates self.args. Returns False if aborted."""
        section_header(f"{self.example_name} Interactive Connection Test Setup")

        self.args.deploy_mode = click.prompt(
            "How is the service deployed?", type=click.Choice(["docker", "k8s"]), default="docker"
        )
        self.args.device = click.prompt(
            "On which target device is it running?",
            type=click.Choice(self.config.get("supported_devices")),
            default=self.config.get("default_device"),
        )

        # The following prompts populate self.args with proxy information.
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

        cmd = ["bash", str(script_path)]
        cmd.extend(["--example", self.example_name])
        cmd.extend(["--device", self.args.device])

        if hasattr(self.args, "setup_local_registry") and self.args.setup_local_registry:
            cmd.append("--setup-registry")

        if hasattr(self.args, "build_images") and self.args.build_images:
            cmd.append("--build")

        if hasattr(self.args, "push_images") and self.args.push_images:
            cmd.append("--push")
            if hasattr(self.args, "registry") and self.args.registry and self.args.registry.strip():
                cmd.extend(["--registry", self.args.registry])
            elif not (hasattr(self.args, "setup_local_registry") and self.args.setup_local_registry):
                log_message(
                    "WARN",
                    "Push selected but no registry provided. Push may fail or use shell script's default.",
                )

        if not (hasattr(self.args, "build_images") and self.args.build_images) and \
                not (hasattr(self.args, "push_images") and self.args.push_images) and \
                not (hasattr(self.args, "setup_local_registry") and self.args.setup_local_registry):
            log_message("INFO", "No image action ('build', 'push', 'setup-registry') confirmed. Skipping.")
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
            source_env_file = self._get_docker_set_env_script()
            local_env_file = self._get_local_env_file_path()

            # Base updates from interactive parameters
            updates = {
                env_var: getattr(self.args, arg_name)
                for arg_name, env_var in self.config["docker_compose"]["params_to_set_env"].items()
                if hasattr(self.args, arg_name) and getattr(self.args, arg_name) is not None
            }

            # 1. Get no_proxy values from the user/environment (already in self.args.no_proxy)
            user_proxies = {p.strip() for p in self.args.no_proxy.split(",") if p.strip()}

            # 2. Get no_proxy values from the original set_env.sh script
            script_no_proxy_str = get_var_from_shell_script(source_env_file, "no_proxy")
            script_proxies = set()
            if script_no_proxy_str:
                script_proxies = {p.strip() for p in script_no_proxy_str.split(",") if p.strip()}
                log_message("INFO", f"Found no_proxy from '{source_env_file.name}': {script_no_proxy_str}")

            # 3. Merge the two sets for a de-duplicated list
            merged_proxies = user_proxies.union(script_proxies)
            final_no_proxy = ",".join(sorted(list(merged_proxies)))
            log_message("INFO", f"Final combined no_proxy list: {final_no_proxy}")

            updates.update(
                {
                    "http_proxy": self.args.http_proxy,
                    "https_proxy": self.args.https_proxy,
                    "no_proxy": final_no_proxy,
                    "HOST_IP": get_host_ip(),
                }
            )

            if update_or_create_set_env(source_env_file, local_env_file, updates):
                log_message("OK", f"Successfully generated local config '{local_env_file.name}'.")
                return True
            else:
                return False

        elif self.args.deploy_mode == "k8s":
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

            if update_helm_values_yaml(local_values_file, updates):
                log_message("OK", f"Successfully updated local Helm values in {local_values_file.name}.")
                return True
            else:
                log_message("ERROR", f"Failed to update Helm values in {local_values_file.name}.")
                return False
        return True

    def deploy(self):
        section_header(f"Deploying {self.example_name} ({self.args.deploy_mode})")

        if self.args.deploy_mode == "docker":
            compose_file = self._get_docker_compose_file()
            if not compose_file:
                log_message("ERROR", "Docker Compose file not found.")
                return False

            compose_filename = compose_file.name
            compose_dir = compose_file.parent
            local_env_file = self._get_local_env_file_path()

            # Ensure the command sources the env file from its own directory
            cmd_string = (
                f"cd '{local_env_file.parent}' && "
                f"source ./{local_env_file.name} && "
                f"cd '{compose_dir}' && "
                f"{self.compose_command} -f {compose_filename} up -d --remove-orphans"
            )

            log_message("INFO", "Executing deployment command in a bash subshell...")
            try:
                run_command(cmd_string, check=True, shell=True, executable="/bin/bash")
                log_message("OK", f"{self.example_name} deployed successfully via Docker Compose.")
                return True
            except Exception as e:
                log_message("ERROR", f"Docker Compose deployment failed: {e}")
                return False

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
                time.sleep(30)  # Give some time for pods to start
                return True
            except Exception as e:
                log_message("ERROR", f"Helm deployment failed: {e}")
                return False
        return False

    def clear_deployment(self):
        section_header(f"Clearing Deployment for {self.example_name} ({self.args.deploy_mode})")

        if self.args.deploy_mode == "docker":
            compose_file = self._get_docker_compose_file()
            if not compose_file:
                log_message("WARN", "Docker Compose file not found. Cannot clear.")
                return True

            compose_dir = compose_file.parent
            local_env_file = self._get_local_env_file_path()
            compose_filename = compose_file.name

            cmd_string = f"cd '{compose_dir}' && {self.compose_command} -f {compose_filename} down -v --remove-orphans"

            log_message("INFO", "Executing cleanup command in a bash subshell...")
            try:
                run_command(cmd_string, check=False, shell=True, executable="/bin/bash")
                if local_env_file.exists():
                    local_env_file.unlink()
                    log_message("INFO", f"Removed generated config file: {local_env_file.name}")
                log_message("OK", "Docker Compose deployment cleared.")
                return True
            except Exception as e:
                log_message("ERROR", f"Failed to clear Docker Compose deployment: {e}")
                return False

        elif self.args.deploy_mode == "k8s":
            cfg = self.config["kubernetes"]
            try:
                run_command(["helm", "uninstall", cfg["release_name"], "--namespace", cfg["namespace"]], check=False)
                log_message("OK", f"Helm release '{cfg['release_name']}' uninstalled.")
            except Exception as e:
                log_message("WARN", f"Helm uninstall may have failed (this is often ok if it was already gone): {e}")

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
        """
        Creates a ConnectionTester and runs all tests.
        It uses self.args, which has been populated by the interactive setup methods.
        """
        section_header(f"Testing Connection for {self.example_name}")
        tester = ConnectionTester(self.example_name, self.args.deploy_mode, self.args.device, self.args)
        return tester.run_all_tests()
