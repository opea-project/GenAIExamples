import click
import os
import time

from .utils import log_message, section_header, run_command, command_exists, \
    update_or_create_set_env, update_helm_values_yaml, get_huggingface_token_from_file, get_host_ip
from .config import EXAMPLE_CONFIGS, EXAMPLES_ROOT_DIR, COMMON_SCRIPTS_DIR
from .tester import ConnectionTester


class Deployer:
    """
    Manages the interactive deployment and clearing of a GenAIExample.
    """

    def __init__(self, args_namespace):
        self.args = args_namespace
        self.example_name = self.args.example
        self.config = EXAMPLE_CONFIGS[self.example_name]
        self.example_root = EXAMPLES_ROOT_DIR / self.config["base_dir"]
        self.compose_command = "docker compose"

    def _get_path_from_config(self, config_keys, device_specific_key=None):
        current_level = self.config
        for key in config_keys:
            if not isinstance(current_level, dict) or key not in current_level: return None
            current_level = current_level[key]
        path_str = current_level.get(device_specific_key) if device_specific_key and isinstance(current_level,
                                                                                                dict) else (
            current_level if isinstance(current_level, str) else None)
        return self.example_root / path_str if path_str else None

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
        return self._get_path_from_config(["kubernetes", "helm", "values_files"], self.args.device)

    def run_interactive_deployment(self):
        """
        Orchestrates the deployment flow with automatic cleanup on failure.
        """
        if not self._interactive_setup_for_deploy():
            return  # User aborted setup

        all_steps_succeeded = False
        try:
            # Chain the deployment steps. If any step returns False, the chain stops.
            success = self.check_environment()
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
                    self.clear_deployment()
                    log_message("OK", "Automatic cleanup has finished.")
                except Exception as cleanup_e:
                    log_message("ERROR",
                                f"Automatic cleanup ALSO FAILED: {cleanup_e}. Please check your environment manually.")
            else:
                log_message("OK", "Deployment process completed successfully.")

    def run_interactive_deployment(self):
        """
        Orchestrates the deployment flow with automatic cleanup on failure.
        """
        if not self._interactive_setup_for_deploy():
            return  # User aborted setup

        all_steps_succeeded = False
        try:
            success = True

            if self.args.do_check_env:
                success = self.check_environment()

            if success:
                success = self.configure_services()

            if success:
                success = self.deploy()

            # Correctly check the flag for testing
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
                    self.clear_deployment()
                    log_message("OK", "Automatic cleanup has finished.")
                except Exception as cleanup_e:
                    log_message("ERROR",
                                f"Automatic cleanup ALSO FAILED: {cleanup_e}. Please check your environment manually.")
            else:
                log_message("OK", "Deployment process completed successfully.")

    def _interactive_setup_for_deploy(self):
        section_header(f"{self.example_name} Interactive Deployment Setup")
        self.args.deploy_mode = click.prompt("Deployment Mode", type=click.Choice(["docker", "k8s"]), default="docker")
        self.args.device = click.prompt("Target Device", type=click.Choice(self.config.get("supported_devices")),
                                        default=self.config.get("default_device"))
        cached_token = get_huggingface_token_from_file()
        self.args.hf_token = click.prompt(f"Hugging Face Token{' (cached found)' if cached_token else ''}",
                                          default=cached_token or "", show_default=False)
        self.args.http_proxy = click.prompt("HTTP Proxy", default=os.environ.get("http_proxy", ""))
        self.args.https_proxy = click.prompt("HTTPS Proxy", default=os.environ.get("https_proxy", ""))
        env_no_proxy, host_ip = os.environ.get("no_proxy", ""), get_host_ip()
        user_no_proxy = click.prompt("No Proxy hosts", default=env_no_proxy)
        no_proxy_set = {"$no_proxy", "localhost", "127.0.0.1", host_ip}
        no_proxy_set.update(p.strip() for p in env_no_proxy.split(',') if p.strip())
        no_proxy_set.update(p.strip() for p in user_no_proxy.split(',') if p.strip())
        self.args.no_proxy = ",".join(sorted(list(no_proxy_set)))
        for param in self.config.get("interactive_params", []):
            if "modes" in param and self.args.deploy_mode not in param["modes"]:
                setattr(self.args, param["name"], None)
                continue
            setattr(self.args, param["name"],
                    click.prompt(param["prompt"], default=param.get("default"), type=param.get("type", str)))
        self.args.do_check_env = click.confirm("Run environment check?", default=False)
        self.args.do_update_images = click.confirm("Build/Push images?", default=False)
        if self.args.do_update_images:
            self.args.build_images = click.confirm("  -> Build images?", default=True)
            self.args.push_images = click.confirm("  -> Push images?", default=False)
            if self.args.push_images: self.args.registry = click.prompt("     Enter container registry URL", default="")
        self.args.do_test_connection = click.confirm("Run connection tests?", default=False)
        if self.args.deploy_mode == 'k8s' and self.args.do_test_connection:
            self.args.k8s_test_local_port = click.prompt("  -> Local port for K8s test", type=int, default=8080)
        section_header("Configuration Summary")
        for k, v in vars(self.args).items():
            # if v is not None and v != '' and not k.startswith('do_'):
            if v is not None and v != '':
                log_message("INFO",
                            f"  {k.replace('_', ' ').title()}: {'....' + v[-4:] if k == 'hf_token' and v else v}")
        return click.confirm("Proceed?", default=True)

    def check_environment(self):
        script_path = COMMON_SCRIPTS_DIR / "check_env.sh"
        if not script_path.exists(): log_message("WARN", f"{script_path} not found. Skipping check."); return True
        try:
            run_command(["bash", str(script_path), "--device", self.args.device], check=True);
            log_message("OK",
                        "Env check passed.");
            return True
        except Exception as e:
            log_message("ERROR", f"Env check failed: {e}");
            return False

    def update_images(self):
        log_message("INFO", "Image update step needs implementation in common/update_images.sh");
        return True

    def configure_services(self):
        section_header(f"Configuring Services for {self.example_name} ({self.args.deploy_mode})")

        if self.args.deploy_mode == "docker":
            source_env_file = self._get_docker_set_env_script()
            local_env_file = self._get_local_env_file_path()

            updates = {
                env_var: getattr(self.args, arg_name)
                for arg_name, env_var in self.config["docker_compose"]["params_to_set_env"].items()
                if hasattr(self.args, arg_name)
            }
            updates.update({
                "HTTP_PROXY": self.args.http_proxy, "HTTPS_PROXY": self.args.https_proxy,
                "NO_PROXY": self.args.no_proxy, "HOST_IP": get_host_ip()
            })

            if update_or_create_set_env(source_env_file, local_env_file, updates):
                log_message("OK", f"Successfully generated local config '{local_env_file.name}'.")
                return True
            else:
                # The function now logs errors internally.
                return False

        elif self.args.deploy_mode == "k8s":
            values_file = self._get_helm_values_file()
            if not values_file or not values_file.exists():
                log_message("ERROR", "Helm values file not found. Cannot configure.");
                return False
            updates = {
                path: getattr(self.args, name)
                for name, path in self.config["kubernetes"]["helm"]["params_to_values"].items() if
                hasattr(self.args, name)
            }
            if self.example_name == "CodeTrans": updates.update(
                {"tgi.enabled": False, "vllm.enabled": True, "llm-uservice.TEXTGEN_BACKEND": "vLLM"})
            if update_helm_values_yaml(values_file, updates):
                log_message("OK", f"Successfully updated Helm values in {values_file.name}.");
                return True
            else:
                log_message("ERROR", f"Failed to update Helm values in {values_file.name}.");
                return False
        return True

    def deploy(self):
        section_header(f"Deploying {self.example_name} ({self.args.deploy_mode})")

        if self.args.deploy_mode == "docker":
            compose_file = self._get_docker_compose_file()
            if not compose_file:
                log_message("ERROR", "Docker Compose file not found.");
                return False

            compose_dir = compose_file.parent
            local_env_filename = self._get_local_env_file_path().name
            compose_filename = compose_file.name

            # Use POSIX-compliant '.' which works in bash too.
            cmd_string = (
                f"cd '{compose_dir}' && "
                f". ./{local_env_filename} && "
                f"{self.compose_command} -f {compose_filename} up -d --remove-orphans"
            )

            log_message("INFO", "Executing deployment command in a bash subshell...")
            try:
                # Specify '/bin/bash' as the executable for the shell
                run_command(cmd_string, check=True, shell=True, executable='/bin/bash')
                log_message("OK", f"{self.example_name} deployed successfully.")
                return True
            except Exception as e:
                log_message("ERROR", f"Docker Compose deployment failed: {e}")
                return False

        elif self.args.deploy_mode == "k8s":
            cfg = self.config["kubernetes"]
            cmd = ["helm", "install", cfg["release_name"], cfg["helm"]["chart_oci"], "--namespace", cfg["namespace"],
                   "--create-namespace", "-f", str(self._get_helm_values_file())]
            try:
                run_command(cmd, check=True);
                log_message("OK", f"{self.example_name} deployed.");
                time.sleep(30);
                return True
            except Exception as e:
                log_message("ERROR", f"Helm deployment failed: {e}");
                return False
        return False

    def clear_deployment(self):
        section_header(f"Clearing Deployment for {self.example_name} ({self.args.deploy_mode})")

        if self.args.deploy_mode == "docker":
            compose_file = self._get_docker_compose_file()
            if not compose_file:
                log_message("WARN", "Docker Compose file not found.");
                return True

            compose_dir = compose_file.parent
            local_env_file = self._get_local_env_file_path()
            local_env_filename = local_env_file.name
            compose_filename = compose_file.name

            if not local_env_file.exists():
                log_message("WARN", f"Local env file '{local_env_filename}' not found, but proceeding.")

            cmd_string = (
                f"cd '{compose_dir}' && "
                f". ./{local_env_filename} && "
                f"{self.compose_command} -f {compose_filename} down -v --remove-orphans"
            )

            log_message("INFO", "Executing cleanup command in a bash subshell...")
            try:
                # Also specify '/bin/bash' for the cleanup command
                run_command(cmd_string, check=False, shell=True, executable='/bin/bash')
                if local_env_file.exists():
                    local_env_file.unlink()
                    log_message("INFO", f"Removed generated config file: {local_env_filename}")
                log_message("OK", "Docker Compose deployment cleared.")
                return True
            except Exception as e:
                log_message("ERROR", f"Failed to clear Docker Compose deployment: {e}");
                return False

        elif self.args.deploy_mode == "k8s":
            cfg = self.config["kubernetes"]
            try:
                run_command(["helm", "uninstall", cfg["release_name"], "--namespace", cfg["namespace"]], check=False)
                log_message("OK", f"Helm release '{cfg['release_name']}' uninstalled.")
            except Exception as e:
                log_message("WARN", f"Helm uninstall may have failed: {e}")
            if getattr(self.args, 'delete_namespace_on_clear', False):
                try:
                    run_command(["kubectl", "delete", "namespace", cfg["namespace"], "--ignore-not-found=true"],
                                check=True); log_message("OK", f"Namespace '{cfg['namespace']}' deleted.")
                except Exception as e:
                    log_message("ERROR", f"Failed to delete namespace: {e}"); return False
            return True
        return False

    def test_connection(self):
        section_header(f"Testing Connection for {self.example_name}")
        tester = ConnectionTester(self.example_name, self.args.deploy_mode, self.args.device, self.args)
        return tester.run_all_tests()