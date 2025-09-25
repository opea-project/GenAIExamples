# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import logging
import os
import pathlib
import random
import re
import shutil
import subprocess
import sys
import time

try:
    import ruamel.yaml

    YAML_HANDLER = ruamel.yaml.YAML()
    YAML_HANDLER.preserve_quotes = True
    YAML_HANDLER.indent(mapping=2, sequence=4, offset=2)
except ImportError:
    try:
        import yaml

        YAML_HANDLER = yaml
    except ImportError:
        YAML_HANDLER = None

from .config import LOG_FILE_PATH

COLOR_RESET = "\033[0m"
COLOR_OK = "\033[1;32m"
COLOR_ERROR = "\033[1;31m"
COLOR_WARN = "\033[1;33m"
COLOR_INFO_HEADER = "\033[1;34m"
COLOR_DEBUG_ICON = "\033[0;36m"


class DeploymentError(Exception):
    """Custom exception for deployment script failures."""

    pass


class LogMessagePrintFilter(logging.Filter):
    def filter(self, record):
        return not getattr(record, "skip_console_handler", False)


def setup_logging():
    file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_FILE_PATH)
    fh.setFormatter(file_formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    ch.setFormatter(console_formatter)
    ch.addFilter(LogMessagePrintFilter())
    logger.addHandler(ch)


def log_message(level, message, to_console=True):
    level_upper = level.upper()
    icon, color, log_lvl = {
        "ERROR": ("❌", COLOR_ERROR, logging.ERROR),
        "WARN": ("⚠️", COLOR_WARN, logging.WARNING),
        "OK": ("✅", COLOR_OK, logging.INFO),
        "INFO": ("📘", COLOR_RESET, logging.INFO),
        "DEBUG": ("🐞", COLOR_DEBUG_ICON, logging.DEBUG),
    }.get(level_upper, ("ℹ️", COLOR_RESET, logging.INFO))
    entry = f"{icon} {message}"
    if to_console:
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {color}{icon} [{level_upper}] {message}{COLOR_RESET}")
        logging.log(log_lvl, entry, extra={"skip_console_handler": True})
    else:
        logging.log(log_lvl, entry)


def section_header(title):
    border = "=" * 70
    header = f"\n{border}\n== {title.upper()} ==\n{border}"
    print(f"{COLOR_INFO_HEADER}{header}{COLOR_RESET}\n")
    logging.info(header, extra={"skip_console_handler": True})


def run_command(cmd_list, cwd=None, env=None, check=True, capture_output=False, display_cmd=True, stream_output=False):
    """Executes a shell command with logging and error handling.

    This function is secured by disallowing shell=True.
    - stream_output=True: Will print command output in real-time. In this mode,
                          the function does not return stdout/stderr.
    - capture_output=True: Will capture stdout/stderr and return them in the result object.
                           Cannot be used with stream_output=True.
    """
    if stream_output and capture_output:
        raise ValueError("stream_output and capture_output cannot be used together.")

    if not isinstance(cmd_list, list):
        log_message("ERROR", "Security: run_command requires commands to be a list.")
        raise TypeError("cmd_list must be a list of strings")

    if display_cmd:
        cmd_str = " ".join(map(str, cmd_list))
        log_message("INFO", f"Running command: {cmd_str}")

    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    if stream_output:
        try:
            process = subprocess.Popen(
                cmd_list,
                cwd=cwd,
                env=process_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Read and print output line by line
            with process.stdout:
                for line in iter(process.stdout.readline, ""):
                    # Print directly to console without log prefix for clean docker-compose output
                    print(line, end="")
                    # Also write to the main log file
                    logging.info(line.strip(), extra={"skip_console_handler": True})

            process.wait(timeout=1800)  # Wait for the process to finish

            if check and process.returncode != 0:
                # Create a CalledProcessError manually for consistent exception handling
                raise subprocess.CalledProcessError(process.returncode, cmd_list)

            return subprocess.CompletedProcess(cmd_list, process.returncode)

        except subprocess.TimeoutExpired as e:
            log_message("ERROR", f"Command timed out after 1800 seconds: {cmd_list}")
            process.kill()
            process.communicate()
            if check:
                raise
            return e
        except Exception as e:
            log_message("ERROR", f"An unexpected error occurred during command streaming: {e}")
            if check:
                raise
            return e

    try:
        result = subprocess.run(
            cmd_list,
            cwd=cwd,
            env=process_env,
            check=check,
            capture_output=capture_output,
            text=True,
            timeout=1800,
        )
        if capture_output:
            if result.stdout:
                log_message("DEBUG", f"Cmd stdout:\n{result.stdout.strip()}", to_console=False)
            if result.stderr:
                log_message("DEBUG", f"Cmd stderr:\n{result.stderr.strip()}", to_console=False)
        return result
    except subprocess.CalledProcessError as e:
        log_message("ERROR", f"Command failed with exit code {e.returncode}: {cmd_list}")
        if e.stdout:
            # When capture_output is True, this contains the output.
            log_message("ERROR", f"Stdout:\n{e.stdout.strip()}")
        if e.stderr:
            log_message("ERROR", f"Stderr:\n{e.stderr.strip()}")
        if check:
            raise
        return e
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        log_message("ERROR", f"Command execution failed: {e}")
        if check:
            raise
        return e


def command_exists(cmd):
    return shutil.which(cmd) is not None


def get_host_ip():
    """Tries to determine the host's primary IP address.

    Commands are now correctly passed as lists.
    """
    try:
        result = run_command(["hostname", "-I"], capture_output=True, check=True, display_cmd=False)
        return result.stdout.strip().split()[0]
    except Exception:
        log_message("WARN", "'hostname -I' failed, trying fallback 'ip route'.")
        try:
            result = run_command(["ip", "route", "get", "1.1.1.1"], capture_output=True, check=True, display_cmd=False)
            return result.stdout.split("src")[-1].strip().split()[0]
        except Exception as e:
            log_message("ERROR", f"Could not determine host IP using any method: {e}. Defaulting to 127.0.0.1")
            return "127.0.0.1"


def get_huggingface_token_from_file():
    token_file = pathlib.Path.home() / ".cache" / "huggingface" / "token"
    if token_file.exists():
        try:
            return token_file.read_text().strip()
        except Exception as e:
            log_message("WARN", f"Could not read HF token from {token_file}: {e}")
    return None


def update_or_create_set_env(source_path: pathlib.Path, dest_path: pathlib.Path, updates: dict):
    if not source_path or not source_path.exists():
        log_message("ERROR", f"Source environment file not found: {source_path}. Cannot create local config.")
        return False
    try:
        shutil.copy2(source_path, dest_path)
        log_message("INFO", f"Copied '{source_path.name}' to '{dest_path.name}' for local configuration.")
    except (IOError, shutil.SameFileError) as e:
        log_message("ERROR", f"Failed to copy '{source_path.name}' to '{dest_path.name}': {e}")
        return False
    lines = dest_path.read_text().splitlines()
    for var_name, new_value in updates.items():
        if new_value is None:
            continue
        escaped_value = str(new_value).replace('"', '\\"')
        safe_new_value = f'"{escaped_value}"'
        found = False
        # Match both uppercase and lowercase versions of the variable for robustness
        # The replacement will use the key from the `updates` dictionary
        for i, line in enumerate(lines):
            if re.match(rf"^\s*(export\s+)?{re.escape(var_name)}\s*=.*", line):
                lines[i] = f"export {var_name}={safe_new_value}"
                found = True
                break
        if not found:
            lines.append(f"export {var_name}={safe_new_value}")
    try:
        dest_path.write_text("\n".join(lines) + "\n")
        return True
    except IOError as e:
        log_message("ERROR", f"Failed to write updates to {dest_path}: {e}")
        return False


def update_helm_values_yaml(file_path: pathlib.Path, updates_map: dict):
    if not YAML_HANDLER:
        log_message("ERROR", "YAML library not available.")
        return False
    if not file_path.exists():
        log_message("ERROR", f"Helm values file not found: {file_path}")
        return False
    try:
        with open(file_path, "r") as f:
            # Using safe_load for ruamel.yaml as well for consistency
            data = YAML_HANDLER.safe_load(f) if hasattr(YAML_HANDLER, "safe_load") else YAML_HANDLER.load(f)
    except Exception as e:
        log_message("ERROR", f"Failed to load YAML file {file_path}: {e}")
        return False
    for key_path, value in updates_map.items():
        if value is None:
            continue

        keys, current_level = key_path, data

        try:
            for key in keys[:-1]:
                if key not in current_level or not isinstance(current_level.get(key), dict):
                    current_level[key] = {}
                current_level = current_level[key]
            current_level[keys[-1]] = value
        except (TypeError, KeyError) as e:
            log_message("ERROR", f"Failed to set '{key_path}': {e}")
            return False
    try:
        with open(file_path, "w") as f:
            YAML_HANDLER.dump(data, f)
    except Exception as e:
        log_message("ERROR", f"Failed to write YAML file {file_path}: {e}")
        return False
    return True


KUBECTL_PORT_FORWARD_PIDS = {}


def start_kubectl_port_forward(namespace, service_name, local_port, remote_port):
    """Starts a kubectl port-forward process with intelligent port selection.

    - If a specific `local_port` is provided, it checks for availability.
        - If available, it's used.
        - If occupied, it logs a warning and falls back to selecting a random port.
    - If `local_port` is 0 or None, it selects a random available port between 59000-59999.
    """
    key = f"{namespace}/{service_name}"

    process = KUBECTL_PORT_FORWARD_PIDS.pop(key, None)
    if process and process.poll() is None:
        log_message("INFO", f"Stopping existing port-forward for {key} to start a new one.")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    target_local_port = None

    if local_port and local_port > 0:
        log_message("INFO", f"Preferred local port {local_port} was provided. Checking availability...")
        if not is_port_in_use(local_port, "127.0.0.1"):
            log_message("OK", f"Port {local_port} is available and will be used.")
            target_local_port = local_port
        else:
            log_message(
                "WARN",
                f"Preferred port {local_port} is already in use. A random port in the range 59000-59999 will be selected instead.",
            )

    if target_local_port is None:
        log_message("INFO", "Finding a random available port in range 59000-59999.")
        found_port = False
        for _ in range(5):
            candidate_port = random.randint(59000, 59999)
            if not is_port_in_use(candidate_port, "127.0.0.1"):
                target_local_port = candidate_port
                found_port = True
                log_message("INFO", f"Found available random port: {target_local_port}")
                break
        if not found_port:
            log_message("ERROR", "Could not find an available port in the range 59000-59999 after 100 attempts.")
            return None

    cmd = ["kubectl", "port-forward", "-n", namespace, f"svc/{service_name}", f"{target_local_port}:{remote_port}"]
    log_message("INFO", f"Starting port-forward: {' '.join(cmd)}")
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        KUBECTL_PORT_FORWARD_PIDS[key] = process
        time.sleep(2)

        if process.poll() is not None:
            stdout, stderr = process.communicate()
            log_message(
                "ERROR",
                f"Port-forward failed to start for {key} on port {target_local_port}. Error: {stderr.strip()}",
            )
            return None

        log_message("OK", f"Port-forward started for {key} on localhost:{target_local_port} (PID: {process.pid}).")
        return target_local_port
    except Exception as e:
        log_message("ERROR", f"Exception starting port-forward for {key}: {e}")
        return None


def stop_all_kubectl_port_forwards():
    if not KUBECTL_PORT_FORWARD_PIDS:
        return
    log_message("INFO", "Stopping all managed port-forwards...")
    for key in list(KUBECTL_PORT_FORWARD_PIDS.keys()):
        ns, svc = key.split("/")
        process = KUBECTL_PORT_FORWARD_PIDS.get(f"{ns}/{svc}")
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            del KUBECTL_PORT_FORWARD_PIDS[f"{ns}/{svc}"]


def get_var_from_shell_script(script_path: pathlib.Path, var_name: str) -> str | None:
    """Gets the value of an environment variable by executing a shell script.

    This method is robust as it handles scripts with functions, sourcing other files,
    and conditional logic. It executes the script in a non-interactive mode.

    Args:
        script_path: The absolute path to the shell script.
        var_name: The name of the environment variable to retrieve.

    Returns:
        The value of the variable as a string, or None if not found or on error.
    """
    if not script_path or not script_path.exists():
        log_message("DEBUG", f"Source script for variable extraction not found: {script_path}")
        return None

    command_string = f"NON_INTERACTIVE=true; " f'source "{script_path.resolve()}" > /dev/null; ' f'echo "${var_name}"'
    try:
        result = run_command(
            ["bash", "-c", command_string],
            cwd=script_path.parent,
            capture_output=True,
            check=False,
            display_cmd=False,
        )

        if result.returncode != 0:
            log_message(
                "WARN",
                f"Execution of '{script_path.name}' failed when trying to get var '{var_name}'. Stderr: {result.stderr.strip()}",
            )
            return None

        value = result.stdout.strip()

        if value:
            log_message("DEBUG", f"Extracted value for '{var_name}' from '{script_path.name}': {value}")
            return value
        else:
            log_message("DEBUG", f"Variable '{var_name}' was not set or is empty in '{script_path.name}'.")
            return None

    except Exception as e:
        log_message(
            "WARN", f"An unexpected error occurred while executing {script_path.name} to get var '{var_name}': {e}"
        )
        return None


def check_install_python_pkg(package, import_name=None):
    import_name = import_name or package
    if importlib.util.find_spec(import_name) is None:
        log_message("INFO", f"Package '{package}' not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    else:
        log_message("DEBUG", f"Package '{package}' is already installed.")


def parse_shell_env_file(file_path: pathlib.Path) -> dict:
    env_vars = {}
    if not file_path or not file_path.exists():
        return env_vars
    pattern = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)")
    try:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = pattern.match(line)
                if match:
                    key, value = match.groups()
                    value = value.split("#", 1)[0].strip()
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]
                    env_vars[key] = value
    except Exception as e:
        log_message("WARN", f"Could not parse environment file {file_path}: {e}")
    return env_vars


def is_port_in_use(port: int, host: str = "0.0.0.0") -> bool:
    """Checks if a given TCP port is already in use on the host."""
    import errno
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError as e:

            if e.errno == errno.EADDRINUSE or e.errno == getattr(errno, "WSAEADDRINUSE", None):
                return True

            if e.errno == errno.EACCES:
                log_message(
                    "WARN",
                    f"Permission denied to check port {port}. This port is likely privileged. Run as root if you need to bind to it.",
                )
                return False

            raise


def _substitute_env_vars(content: str, env_vars: dict) -> str:
    """Mimics Docker Compose's environment variable substitution in a string.

    Handles ${VAR}, $VAR, and ${VAR:-default}.
    """
    # Regex to find all forms of variables: ${VAR}, $VAR, ${VAR:-default}, ${VAR-default}
    pattern = re.compile(r"\$(?:\{(\w+)(?:[:-](.*?))?\}|(\w+))")

    def replacer(match):
        # Determine the variable name and default value from the match groups
        var_name = match.group(1) or match.group(3)
        default_value = match.group(2)

        # Get the value from the provided environment, or the default, or an empty string
        value = env_vars.get(var_name)
        if value is not None:
            return str(value)
        if default_value is not None:
            return str(default_value)
        # Docker compose substitutes with an empty string if var is not set and no default
        return ""

    return pattern.sub(replacer, content)


def get_conflicting_ports_from_compose(compose_files: list[pathlib.Path], env_vars: dict) -> list[int]:
    """Parses Docker Compose files using the "substitute first, then parse" method,
    and checks for port conflicts on the host.

    This is the robust way.
    """
    if not YAML_HANDLER:
        log_message("WARN", "YAML library not available, skipping port check.")
        return []

    all_host_ports = set()

    for file_path in compose_files:
        if not file_path.exists():
            log_message("WARN", f"Compose file for port check not found: {file_path}")
            continue
        try:
            # 1. Read the raw file content
            raw_content = file_path.read_text()

            # 2. Substitute environment variables in the raw text
            substituted_content = _substitute_env_vars(raw_content, env_vars)

            # 3. Parse the substituted (clean) YAML content
            data = (
                YAML_HANDLER.safe_load(substituted_content)
                if hasattr(YAML_HANDLER, "safe_load")
                else YAML_HANDLER.load(substituted_content)
            )

            if not data or "services" not in data:
                continue

            for service_config in data.get("services", {}).values():
                if not isinstance(service_config, dict) or "ports" not in service_config:
                    continue

                for port_mapping in service_config["ports"]:
                    # After substitution, the mapping should be a clean string like "8080:80"
                    # We only care about mappings that expose a host port
                    mapping_str = str(port_mapping)
                    if ":" in mapping_str:
                        host_port_str = mapping_str.split(":", 1)[0]
                        # The host port should now be a simple number
                        if host_port_str.isdigit():
                            all_host_ports.add(int(host_port_str))
                        else:
                            # This case might occur if a variable was not resolved to a number
                            log_message(
                                "WARN",
                                f"Could not resolve host port '{host_port_str}' to a number in file '{file_path.name}'. Skipping.",
                            )

        except Exception as e:
            log_message("ERROR", f"Failed to process compose file {file_path} for port check: {e}")

    if not all_host_ports:
        return []

    log_message("INFO", f"Checking for availability of required ports: {sorted(list(all_host_ports))}")

    conflicting_ports = []
    for port in all_host_ports:
        if is_port_in_use(port):
            conflicting_ports.append(port)

    return conflicting_ports


def find_all_values_for_key(data_structure, key_to_find):
    """Recursively finds all values for a specific key in a nested data structure."""
    found_values = []
    if isinstance(data_structure, dict):
        for key, value in data_structure.items():
            if key == key_to_find:
                if isinstance(value, str):
                    found_values.append(value)
            else:
                found_values.extend(find_all_values_for_key(value, key_to_find))
    elif isinstance(data_structure, list):
        for item in data_structure:
            found_values.extend(find_all_values_for_key(item, key_to_find))
    return found_values
