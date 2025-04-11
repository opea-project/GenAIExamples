export LLM_MODEL_ID="meta-llama/Llama-3.3-70B-Instruct"
export MAX_LEN=16384

docker compose -f vllm_compose.yaml up -d