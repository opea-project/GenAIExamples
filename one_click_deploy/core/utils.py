import logging
import os
import pathlib
import subprocess
import shutil
import re
import time
import sys

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


class LogMessagePrintFilter(logging.Filter):
    def filter(self, record):
        return not getattr(record, 'skip_console_handler', False)


def setup_logging():
    file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger()
    if logger.hasHandlers(): logger.handlers.clear()
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(LOG_FILE_PATH)
    fh.setFormatter(file_formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(f"%(asctime)s [%(levelname)s] %(message)s")
    ch.setFormatter(console_formatter)
    ch.addFilter(LogMessagePrintFilter())
    logger.addHandler(ch)


def log_message(level, message, to_console=True):
    level_upper = level.upper()
    icon, color, log_lvl = {"ERROR": ("❌", COLOR_ERROR, logging.ERROR), "WARN": ("⚠️", COLOR_WARN, logging.WARNING),
                            "OK": ("✅", COLOR_OK, logging.INFO), "INFO": ("📘", COLOR_RESET, logging.INFO),
                            "DEBUG": ("🐞", COLOR_DEBUG_ICON, logging.DEBUG)}.get(level_upper,
                                                                                 ("ℹ️", COLOR_RESET, logging.INFO))
    entry = f"{icon} {message}"
    if to_console:
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {color}{icon} [{level_upper}] {message}{COLOR_RESET}")
        logging.log(log_lvl, entry, extra={'skip_console_handler': True})
    else:
        logging.log(log_lvl, entry)


def section_header(title):
    border = "=" * 70
    header = f"\n{border}\n== {title.upper()} ==\n{border}"
    print(f"{COLOR_INFO_HEADER}{header}{COLOR_RESET}\n")
    logging.info(header, extra={'skip_console_handler': True})


def run_command(cmd_list, cwd=None, env=None, check=True, capture_output=False, shell=False, executable=None,
                display_cmd=True):
    """
    Executes a shell command with logging and error handling.
    Accepts an 'executable' argument to specify the shell (e.g., '/bin/bash').
    """
    if display_cmd:
        cmd_str = ' '.join(cmd_list) if isinstance(cmd_list, list) else cmd_list
        log_message("INFO", f"Running command: {cmd_str}")

    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    try:
        result = subprocess.run(
            cmd_list, cwd=cwd, env=process_env, check=check,
            capture_output=capture_output, text=True, shell=shell,
            executable=executable,
            timeout=1800
        )
        if capture_output:
            if result.stdout: log_message("DEBUG", f"Cmd stdout:\n{result.stdout.strip()}", to_console=False)
            if result.stderr: log_message("DEBUG", f"Cmd stderr:\n{result.stderr.strip()}", to_console=False)
        return result
    except subprocess.CalledProcessError as e:
        log_message("ERROR", f"Command failed with exit code {e.returncode}: {cmd_list}")
        if e.stdout: log_message("ERROR", f"Stdout: {e.stdout.strip()}")
        if e.stderr: log_message("ERROR", f"Stderr: {e.stderr.strip()}")
        if check: raise
        return e
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        log_message("ERROR", f"Command execution failed: {e}")
        if check: raise
        return e


def command_exists(cmd): return shutil.which(cmd) is not None


def get_host_ip():
    """
    Tries to determine the host's primary IP address.
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
        if new_value is None: continue
        escaped_value = str(new_value).replace('"', '\\"')
        safe_new_value = f'"{escaped_value}"'
        found = False
        for i, line in enumerate(lines):
            if re.match(rf'^\s*(export\s+)?{re.escape(var_name)}\s*=.*', line):
                lines[i] = f"export {var_name}={safe_new_value}";
                found = True;
                break
        if not found: lines.append(f"export {var_name}={safe_new_value}")
    try:
        dest_path.write_text("\n".join(lines) + "\n");
        return True
    except IOError as e:
        log_message("ERROR", f"Failed to write updates to {dest_path}: {e}");
        return False


def update_helm_values_yaml(file_path: pathlib.Path, updates_map: dict):
    if not YAML_HANDLER:
        log_message("ERROR", "YAML library not available.");
        return False
    if not file_path.exists():
        log_message("ERROR", f"Helm values file not found: {file_path}");
        return False
    try:
        with open(file_path, 'r') as f:
            data = YAML_HANDLER.load(f)
    except Exception as e:
        log_message("ERROR", f"Failed to load YAML file {file_path}: {e}");
        return False
    for key_path, value in updates_map.items():
        if value is None: continue
        keys, current_level = key_path.split('.'), data
        try:
            for key in keys[:-1]:
                if key not in current_level: current_level[key] = {}
                current_level = current_level[key]
            current_level[keys[-1]] = value
        except (TypeError, KeyError) as e:
            log_message("ERROR", f"Failed to set '{key_path}': {e}");
            return False
    try:
        with open(file_path, 'w') as f:
            YAML_HANDLER.dump(data, f)
    except Exception as e:
        log_message("ERROR", f"Failed to write YAML file {file_path}: {e}");
        return False
    return True


KUBECTL_PORT_FORWARD_PIDS = {}


def start_kubectl_port_forward(namespace, service_name, local_port, remote_port):
    key = f"{namespace}/{service_name}"
    if key in KUBECTL_PORT_FORWARD_PIDS and KUBECTL_PORT_FORWARD_PIDS[key].poll() is None: return local_port
    cmd = ["kubectl", "port-forward", "-n", namespace, f"svc/{service_name}", f"{local_port}:{remote_port}"]
    log_message("INFO", f"Starting port-forward: {' '.join(cmd)}")
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        KUBECTL_PORT_FORWARD_PIDS[key] = process
        time.sleep(2)
        if process.poll() is not None:
            _, stderr = process.communicate()
            log_message("ERROR", f"Port-forward failed: {stderr.decode().strip()}");
            del KUBECTL_PORT_FORWARD_PIDS[key];
            return None
        log_message("OK", f"Port-forward started (PID: {process.pid}).");
        return local_port
    except Exception as e:
        log_message("ERROR", f"Exception starting port-forward: {e}");
        return None


def stop_all_kubectl_port_forwards():
    if not KUBECTL_PORT_FORWARD_PIDS: return
    log_message("INFO", "Stopping all managed port-forwards...")
    for key in list(KUBECTL_PORT_FORWARD_PIDS.keys()):
        ns, svc = key.split('/')
        process = KUBECTL_PORT_FORWARD_PIDS.get(f"{ns}/{svc}")
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            del KUBECTL_PORT_FORWARD_PIDS[f"{ns}/{svc}"]