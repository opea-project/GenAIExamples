# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Backup the original compose file (if not already backed up)
if [ ! -f compose.yaml.bak ]; then
  echo "Backing up compose.yaml to compose.yaml.bak"
  cp compose.yaml compose.yaml.bak
fi

# Check if set_env.sh exists
if [ ! -f set_env.sh ]; then
  echo "Error: set_env.sh not found.  Make sure you are in the correct directory."
  exit 1
fi

# Source environment variables
source ./set_env.sh

# Check if required environment variables are set
if [ -z "$BACKEND_SERVICE_ENDPOINT" ] || [ -z "$DATAPREP_SERVICE_ENDPOINT" ]; then
  echo "Error: BACKEND_SERVICE_ENDPOINT or DATAPREP_SERVICE_ENDPOINT not set. Run set_env.sh first."
  exit 1
fi

# 1. Replace the service name, image, and ports.  Use sed for in-place editing.
sed -i 's/chaqna-xeon-ui-server/chatqna-xeon-conversation-ui-server/g' compose.yaml
sed -i 's/opea\/chatqna-ui:latest/opea\/chatqna-conversation-ui:latest/g' compose.yaml
sed -i 's/5173:5173/5174:80/g' compose.yaml  # Corrected port mapping

# 2. Ensure the depends_on field is correct.
sed -i 's/depends_on:/&\n    - chatqna-xeon-backend-server/' compose.yaml
 # Check if depends_on already has chatqna-xeon-backend-server, and fix it using awk if there is different setting
if ! grep -q "chatqna-xeon-backend-server" compose.yaml; then
  awk '/depends_on:/ {print; print "    - chatqna-xeon-backend-server"; next} 1' compose.yaml > temp.yaml && mv temp.yaml compose.yaml
fi


# 3. Set/Update environment variables.
sed -i "/APP_BACKEND_SERVICE_ENDPOINT/d" compose.yaml  # Remove any existing lines
sed -i "/APP_DATA_PREP_SERVICE_URL/d" compose.yaml     # Remove any existing lines
sed -i "/chatqna-xeon-conversation-ui-server:/a \ \ environment:" compose.yaml
sed -i "/environment:/a \ \ \ \ - APP_BACKEND_SERVICE_ENDPOINT=\${BACKEND_SERVICE_ENDPOINT}" compose.yaml
sed -i "/APP_BACKEND_SERVICE_ENDPOINT/a \ \ \ \ - APP_DATA_PREP_SERVICE_URL=\${DATAPREP_SERVICE_ENDPOINT}" compose.yaml
sed -i '/ipc: host/d' compose.yaml
sed -i "/chatqna-xeon-conversation-ui-server:/a \ \ ipc: host" compose.yaml
sed -i "/chatqna-xeon-conversation-ui-server:/a \ \ restart: always" compose.yaml
# Check if conversation-ui service is already in the compose file, if not add it based on original ui service.
if ! grep -q "chatqna-xeon-conversation-ui-server" compose.yaml; then
    sed -e '/chaqna-xeon-ui-server/,/restart: always/ {
        s/chaqna-xeon-ui-server/chatqna-xeon-conversation-ui-server/
        s/opea\/chatqna-ui:latest/opea\/chatqna-conversation-ui:latest/
        s/5173:5173/5174:80/
        /environment:/a \      - APP_BACKEND_SERVICE_ENDPOINT=${BACKEND_SERVICE_ENDPOINT}\
        /environment:/a \      - APP_DATA_PREP_SERVICE_URL=${DATAPREP_SERVICE_ENDPOINT}

    }' compose.yaml > temp_compose.yaml
    mv temp_compose.yaml compose.yaml
fi

echo "Conversational UI setup complete.  Run 'docker compose up -d' to start.

# Make the script executable
#chmod +x use_conversation_ui.sh

# Run the script
#./use_conversation_ui.sh

#Start the Services
#docker compose up -d
