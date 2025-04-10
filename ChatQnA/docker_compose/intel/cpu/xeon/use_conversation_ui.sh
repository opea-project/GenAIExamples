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
source ./set_env.sh[[3](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAQXblrzJdVR5EXosjXbjSi13_w8_AjDsxY1z8tpwlX2Ht4FdLy1NFE8mDnpUWrLd1KeksZBRzGExdccSmovlOVd5GIk44_Ibde4YqSvt0wI6BvhM3TOJUVyxcWF7BH0XBGtNMn3rQueGW5X0aAetveHZAe6Q6d_fzeFIwluKFo_DQe-i)]

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


# 3. Set/Update environment variables.[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAQXblrwgB6_YzDOTrTgyLG3NtwEG15FrZHMecr3XB8K2P25wkEejiD4vju6T4kZXRPfD04MDBipmSplTw5Un2PE0JOmfhjGg8RZh8mvDlbG5DNgqFpV0UJDYEk5h5GJqKf7mPdHHbuG0rUE8xzH-dSdWt3tWZIowiL1Atg%3D%3D)][[3](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAQXblrzJdVR5EXosjXbjSi13_w8_AjDsxY1z8tpwlX2Ht4FdLy1NFE8mDnpUWrLd1KeksZBRzGExdccSmovlOVd5GIk44_Ibde4YqSvt0wI6BvhM3TOJUVyxcWF7BH0XBGtNMn3rQueGW5X0aAetveHZAe6Q6d_fzeFIwluKFo_DQe-i)][[4](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAQXblrz98WVP-aqDwR0GmOl-zwhQqj4VN6J7_FW4BIPLfYfOGmlIsagBsD6r9wmEAHpUG0kCx5ylsMFtWWdchucxJFxid4qk8F6vAIAeDnRx34CigKDkn7xrxF5CkGBxLfHvw1iaD8B97YkpDl1T1qsYuomNEuOROXzdOKYAFEhHWU5uS3LL68mhLRKzMyKPhEe3vzIRe70gmt9aedCQQ0SbJZlt3roK7jHA__tTZ0s%3D)][[5](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAQXblry_dQaxUGNibABkk3NezjT1i3K9C7qAUDw-8AZfkFBmNth5Y70HVR8yPMp5ZBnGqvVZKQFt9Ydp9m1jgKEH1JOqxLNaOU3l5tMErwVnYsozL9dC1Z_VwW02Dw9c4vgAd9yK7W1lAwaUdxmHKWFSzc65VQ8i7HO1s4PG3leeXbSJz74xajRuyDJUkrxkjMgMsj1ozTPVNzBJQz_AhzjIbOMkIJO0qZbl44xqsQ2w)][[6](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAQXblryJfN6Pys1D4un81GYQvY33Yth_PGQFA2-FrzGwRtE-Iv1KKGEKlKB5l9uy8tT7WypRwGpN_ukIBhpqth33VyRuLVmOg2pZkVZETVY3u0KFxldRVG16axEN-fgN5fsiC5gHrMtiV5bFuWj05wP0iw%3D%3D)]
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

echo "Conversational UI setup complete.  Run 'docker compose up -d' to start."[[1](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAQXblrwgB6_YzDOTrTgyLG3NtwEG15FrZHMecr3XB8K2P25wkEejiD4vju6T4kZXRPfD04MDBipmSplTw5Un2PE0JOmfhjGg8RZh8mvDlbG5DNgqFpV0UJDYEk5h5GJqKf7mPdHHbuG0rUE8xzH-dSdWt3tWZIowiL1Atg%3D%3D)][[3](https://www.google.com/url?sa=E&q=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fgrounding-api-redirect%2FAQXblrzJdVR5EXosjXbjSi13_w8_AjDsxY1z8tpwlX2Ht4FdLy1NFE8mDnpUWrLd1KeksZBRzGExdccSmovlOVd5GIk44_Ibde4YqSvt0wI6BvhM3TOJUVyxcWF7BH0XBGtNMn3rQueGW5X0aAetveHZAe6Q6d_fzeFIwluKFo_DQe-i)]

# Make the script executable
#chmod +x use_conversation_ui.sh

# Run the script
#./use_conversation_ui.sh

#Start the Services
#docker compose up -d
