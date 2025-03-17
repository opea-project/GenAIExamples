#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e  # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
COMPOSE_FILE="../docker_compose/intel/cpu/xeon/compose.yaml"
SET_ENV_FILE="../docker_compose/intel/cpu/xeon/set_env.sh"
SCRIPT_FILE="../docker_compose/intel/cpu/xeon/use_conversation_ui.sh"

# --- Helper Functions ---

# Check if a command exists
command_exists() {
  command -v "$1" &> /dev/null
}

# Check if a file exists and is readable
file_exists_and_readable() {
  [[ -r "$1" ]]
}

# Get an environment variable, handling sourcing of set_env.sh
get_env_var() {
  local var_name="$1"
  # Source set_env.sh and then print the variable.  This ensures
  # we get the variable as it would be set by the script.
  source "$SET_ENV_FILE" && echo "${!var_name}"
}
# --- Setup ---
# Check prerequisites
if ! command_exists yq; then
  echo "Error: yq is required. Please install it (e.g., apt install yq)." >&2
  exit 1
fi

if ! file_exists_and_readable "$COMPOSE_FILE"; then
  echo "Error: Compose file not found: $COMPOSE_FILE" >&2
  exit 1
fi

if ! file_exists_and_readable "$SET_ENV_FILE"; then
  echo "Error: set_env.sh not found: $SET_ENV_FILE" >&2
  exit 1
fi
 if ! file_exists_and_readable "$SCRIPT_FILE"; then
  echo "Error: use_conversation_ui.sh not found: $SCRIPT_FILE" >&2
  exit 1
fi
# --- Tests ---

# Test 1: Check environment variables
test_environment_variables() {
  echo "Running environment variable tests..."
  local required_vars=("BACKEND_SERVICE_ENDPOINT" "DATAPREP_SERVICE_ENDPOINT" "HOST_IP" "NGINX_PORT")
  local var_value
  for var in "${required_vars[@]}"; do
    var_value=$(get_env_var "$var")
    if [[ -z "$var_value" ]]; then
      echo "  Error: Environment variable $var is not set or is empty." >&2
      return 1
    fi
    echo "  $var: $var_value"
  done
  echo "Environment variable tests passed."
  return 0
}

# Test 2: Check compose file changes
test_compose_file_changes() {
  echo "Running compose file tests..."

  # 1. Check service name
  local service_name=$(yq e '.services."chatqna-xeon-conversation-ui-server"' "$COMPOSE_FILE" 2>/dev/null)
  if [[ -z "$service_name" ]]; then
    echo "  Error: chatqna-xeon-conversation-ui-server service not found." >&2
    return 1
  fi

  # 2. Check image name
  local image_name=$(yq e '.services."chatqna-xeon-conversation-ui-server".image' "$COMPOSE_FILE")
  if [[ "$image_name" != "opea/chatqna-conversation-ui:latest" ]]; then
    echo "  Error: Incorrect image name.  Expected: opea/chatqna-conversation-ui:latest, Got: $image_name" >&2
    return 1
  fi

  # 3. Check port mapping
  local port_mapping=$(yq e '.services."chatqna-xeon-conversation-ui-server".ports[0]' "$COMPOSE_FILE")
  if [[ "$port_mapping" != "5174:80" ]]; then
    echo "  Error: Incorrect port mapping. Expected: 5174:80, Got: $port_mapping" >&2
    return 1
  fi

  # 4. Check depends_on
  local depends_on=$(yq e '.services."chatqna-xeon-conversation-ui-server".depends_on[0]' "$COMPOSE_FILE")
  if [[ "$depends_on" != "chatqna-xeon-backend-server" ]]; then
    echo "  Error: Incorrect depends_on. Expected: chatqna-xeon-backend-server, Got: $depends_on" >&2
    return 1
  fi

  # 5. Check environment variables
   local backend_endpoint=$(yq e '.services."chatqna-xeon-conversation-ui-server".environment.APP_BACKEND_SERVICE_ENDPOINT' "$COMPOSE_FILE" 2>/dev/null)
  local dataprep_endpoint=$(yq e '.services."chatqna-xeon-conversation-ui-server".environment.APP_DATA_PREP_SERVICE_URL' "$COMPOSE_FILE" 2>/dev/null)
  #If it is list
  if [[ -z "$backend_endpoint" ]] || [[ -z "$dataprep_endpoint" ]]; then
      backend_endpoint=$(yq e '.services."chatqna-xeon-conversation-ui-server".environment[0]' "$COMPOSE_FILE" 2>/dev/null)
      dataprep_endpoint=$(yq e '.services."chatqna-xeon-conversation-ui-server".environment[1]' "$COMPOSE_FILE" 2>/dev/null)
  fi

  local expected_backend_endpoint="\${BACKEND_SERVICE_ENDPOINT}"
  local expected_dataprep_endpoint="\${DATAPREP_SERVICE_ENDPOINT}"


  if [[ "$backend_endpoint" != "$expected_backend_endpoint" ]]; then
    echo "  Error: Incorrect APP_BACKEND_SERVICE_ENDPOINT. Expected: $expected_backend_endpoint, Got: $backend_endpoint" >&2
    return 1
  fi

  if [[ "$dataprep_endpoint" != "$expected_dataprep_endpoint" ]]; then
    echo "  Error: Incorrect APP_DATA_PREP_SERVICE_URL. Expected: $expected_dataprep_endpoint, Got: $dataprep_endpoint" >&2
    return 1
  fi

  echo "Compose file tests passed."
  return 0
}

#Test Script Execution
test_script_execution(){
  echo "Running script execution test"

  # Run the script and check for the success message.
  "$SCRIPT_FILE" &> script_output.log
   if ! grep -q "Conversational UI setup complete" script_output.log; then
    echo " Script execution failed.  See script_output.log for details." >&2
    return 1
  fi
    echo "Script execution test passed."
    return 0
}
# --- Main Execution ---

test_environment_variables &&
test_compose_file_changes &&
test_script_execution

# --- Exit ---
echo "All tests passed!"
exit 0
