# EdgeCraft RAG CLI

A command-line interface tool for managing EdgeCraft RAG system components including pipelines, models, knowledge bases, agents, and more.

## Implementation Notes

The CLI package is organized as follows:

- `main.py`: Click command groups and subcommands
- `client.py`: `EcragApiClient` REST wrapper
- `config.py`: environment-based connection config
- `quickstart.py`: quick start and connectivity check helper
- `setup.py`: package metadata and `ecrag` console entry point

## Installation

Requires Python 3.8+.

### Recommended

```bash
# From EdgeCraftRAG/cli/
pip install -e .

# Verify
ecrag --help
```

If your OS uses externally-managed Python (PEP 668), use:

```bash
pip install --break-system-packages -e .
ecrag --help
```

### Optional (non-editable install)

```bash
pip install .
ecrag --help
```

## Usage

The CLI is organized into logical command groups for different system components.

### Basic Syntax

```bash
ecrag [--host HOST] [--port PORT] [--mega-port MEGA_PORT] COMMAND [OPTIONS]
```

```bash
# Default top-level query uses ChatQnA (/v1/chatqna)
ecrag query "Your question"
```

### Global Options

- `--host`: Server host URL (default: `http://localhost`)
- `--port`: Server port (default: `16010`)
- `--mega-port`: Mega service port (default: `16011`)

## Commands

### Pipeline Management

```bash
# List all pipelines
ecrag pipeline list

# Create a pipeline
ecrag pipeline create --name my_pipeline --file pipeline.json

# Get pipeline details
ecrag pipeline get --name my_pipeline

# Get pipeline JSON
ecrag pipeline get-json --name my_pipeline

# Activate/Deactivate pipeline
ecrag pipeline activate --name my_pipeline
ecrag pipeline deactivate --name my_pipeline

# Delete pipeline
ecrag pipeline delete --name my_pipeline

# Get benchmark data
ecrag pipeline benchmark --name my_pipeline

# Import pipeline from file
ecrag pipeline import-pipeline --file pipeline.json
```

### Model Management

```bash
# Load a model
ecrag model load --type LLM --id model-id --path /path/to/model --device cpu

# List all models
ecrag model list

# Get model info
ecrag model get --id model-id

# Update model
ecrag model update --id model-id --device gpu

# Delete model
ecrag model delete --id model-id

# Get available weights
ecrag model weights --id model-id

# List available models by type
ecrag model available --type LLM
ecrag model available --type embedding
```

### Knowledge Base Management

```bash
# Create knowledge base
ecrag kb create --name my_kb --description "My knowledge base"

# List knowledge bases
ecrag kb list

# Get knowledge base details
ecrag kb get --name my_kb

# Get knowledge base JSON
ecrag kb get-json --name my_kb

# Get file map (pagination)
ecrag kb filemap --name my_kb --page 1 --size 20

# Update knowledge base
ecrag kb update --name my_kb --description "Updated" --active true

# Delete knowledge base
ecrag kb delete --name my_kb

# Add files to knowledge base
ecrag kb add-files --name my_kb --paths /path/to/file1 /path/to/file2

# Delete files from knowledge base
ecrag kb delete-files --name my_kb --paths /path/to/file1
```

### Experience Management

```bash
# List all experiences
ecrag experience list

# Get experience
ecrag experience get --id exp-id

# Create/Update experience
ecrag experience create --id exp-id --question "What is X?" --content "Answer"

# Delete experience
ecrag experience delete --id exp-id

# Load experiences from file
ecrag experience load-file --file experiences.json
```

### Agent Management

```bash
# List all agents
ecrag agent list

# Get agent details
ecrag agent get --name my_agent

# Get agent type configs
ecrag agent configs --type react_llm

# Create agent
ecrag agent create --name my_agent --type react_llm --pipeline pipeline-idx

# Update agent
ecrag agent update --name my_agent --active true

# Delete agent
ecrag agent delete --name my_agent
```

### Prompt Management

```bash
# Get current prompt
ecrag prompt get

# Get tagged prompt
ecrag prompt get-tagged

# Get default prompt
ecrag prompt get-default

# Set prompt from text
ecrag prompt set --text "Your prompt text here"

# Set prompt from file
ecrag prompt set --file prompt.txt

# Reset to default prompt
ecrag prompt reset
```

### Data Management

```bash
# Get all nodes
ecrag data nodes

# Get nodes by document
ecrag data nodes-by-doc --name document_name

# List all documents
ecrag data documents

# List all files
ecrag data files

# Get specific file
ecrag data get-file --name filename

# Upload file
ecrag data upload --name filename --path /path/to/file
```

### Session Management

```bash
# List all sessions
ecrag session list

# Get session details
ecrag session get --id session-id
```

### System Information

```bash
# Get system info (CPU, memory, disk, etc.)
ecrag system info

# Get available devices
ecrag system devices
```

### Chat and Query

```bash
# Shortcut for ChatQnA
ecrag query "Your question"

# Retrieve relevant chunks
ecrag chat retrieve --query "Your question" --top-n 5

# Run RAG pipeline
ecrag chat rag --query "Your question" --top-n 5

# Run mega service (full pipeline)
ecrag chat mega --query "Your question" --top-n 5

# Check vLLM connection
ecrag chat check-vllm --server http://localhost:8086 --model "Qwen/Qwen3-8B"
```

## Examples

### Create a Knowledge Base and Add Files

```bash
# Create KB
ecrag kb create --name research_kb --description "Research papers"

# Add files
ecrag kb add-files --name research_kb --paths /data/paper1.pdf /data/paper2.pdf
```

### Load a Model and Create Pipeline

```bash
# Load embedding model
ecrag model load --type embedding --id BAAI/bge-base-en --device cpu

# Create pipeline with the model
ecrag pipeline create --name my_pipeline --file pipeline_config.json

# Activate pipeline
ecrag pipeline activate --name my_pipeline
```

### Query the System

```bash
# Run the default ChatQnA shortcut
ecrag query "What is RAG?"

# Equivalent explicit subcommand
ecrag chat mega --query "What is RAG?" --top-n 5

# RAG pipeline only
ecrag chat rag --query "What is RAG?" --top-n 5

# Retrieval only
ecrag chat retrieve --query "What is RAG?" --top-n 5
```

## Configuration

The CLI reads the following environment variables (optional):

- `ECRAG_HOST`: Server host (default: `http://localhost`)
- `ECRAG_PORT`: Server port (default: `16010`)
- `ECRAG_MEGA_PORT`: Mega service port (default: `16011`)

## Error Handling

The CLI will display error messages from the API in JSON format. Network errors and other issues will be reported with descriptive error messages.

## Tips

- Use `--help` with any command to see detailed help:
  ```bash
  ecrag pipeline --help
  ecrag pipeline create --help
  ```

- Pipe JSON output to other tools:
  ```bash
  ecrag kb list | jq '.[]' | head -n 20
  ```

- Use confirmation prompts for destructive operations:
  ```bash
  # Will ask before deleting
  ecrag pipeline delete --name old_pipeline
  ```

## API Reference

The CLI wraps the following API endpoints:

- **Pipelines**: `/v1/settings/pipelines`
- **Models**: `/v1/settings/models`
- **Knowledge Bases**: `/v1/knowledge`
- **Experiences**: `/v1/experiences`
- **Agents**: `/v1/agents`
- **Prompts**: `/v1/chatqna/prompt`
- **Data**: `/v1/data/*`
- **Sessions**: `/v1/sessions`
- **System**: `/v1/system/*`
- **Chat/Query**: `/v1/retrieval`, `/v1/ragqna`, `/v1/chatqna`

For more details, see the main [API_Guide.md](../docs/API_Guide.md).

## Endpoint Mapping Details

The CLI maps command groups to REST endpoints as follows:

- `pipeline`: `GET/POST /v1/settings/pipelines`, `GET/PATCH/DELETE /v1/settings/pipelines/{name}`
- `model`: `GET/POST /v1/settings/models`, `GET/PATCH/DELETE /v1/settings/models/{id}`
- `kb`: `GET/POST /v1/knowledge`, `GET/DELETE /v1/knowledge/{name}`, `PATCH /v1/knowledge/patch`, `POST/DELETE /v1/knowledge/{name}/files`
- `experience`: `GET /v1/experiences`, `POST /v1/experience`, `PATCH/DELETE /v1/experiences`
- `agent`: `GET/POST /v1/agents`, `GET/PATCH/DELETE /v1/agents/{name}`
- `prompt`: `GET/POST /v1/chatqna/prompt`, `POST /v1/chatqna/prompt/reset`
- `data`: `GET /v1/data/nodes`, `GET /v1/data/documents`, `GET /v1/data/files`, `POST /v1/data/file/{name}`
- `chat`: `POST /v1/retrieval`, `POST /v1/ragqna`, `POST /v1/chatqna`
