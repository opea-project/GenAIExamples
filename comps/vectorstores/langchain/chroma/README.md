# Introduction

Chroma is a AI-native open-source vector database focused on developer productivity and happiness. Chroma is licensed under Apache 2.0. Chroma runs in various modes, we can deploy it as a server running your local machine or in the cloud.

# Getting Started

## Start Chroma Server

To start the Chroma server on your local machine, follow these steps:

```bash
git clone https://github.com/chroma-core/chroma.git
cd chroma
docker compose up -d
```

## Start Log Output

Upon starting the server, you should see log outputs similar to the following:

```
server-1  | Starting 'uvicorn chromadb.app:app' with args: --workers 1 --host 0.0.0.0 --port 8000 --proxy-headers --log-config chromadb/log_config.yml --timeout-keep-alive 30
server-1  | INFO:     [02-08-2024 07:03:19] Set chroma_server_nofile to 65536
server-1  | INFO:     [02-08-2024 07:03:19] Anonymized telemetry enabled. See                     https://docs.trychroma.com/telemetry for more information.
server-1  | DEBUG:    [02-08-2024 07:03:19] Starting component System
server-1  | DEBUG:    [02-08-2024 07:03:19] Starting component OpenTelemetryClient
server-1  | DEBUG:    [02-08-2024 07:03:19] Starting component SqliteDB
server-1  | DEBUG:    [02-08-2024 07:03:19] Starting component QuotaEnforcer
server-1  | DEBUG:    [02-08-2024 07:03:19] Starting component Posthog
server-1  | DEBUG:    [02-08-2024 07:03:19] Starting component LocalSegmentManager
server-1  | DEBUG:    [02-08-2024 07:03:19] Starting component SegmentAPI
server-1  | INFO:     [02-08-2024 07:03:19] Started server process [1]
server-1  | INFO:     [02-08-2024 07:03:19] Waiting for application startup.
server-1  | INFO:     [02-08-2024 07:03:19] Application startup complete.
server-1  | INFO:     [02-08-2024 07:03:19] Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```
