# EdgeCraftRAG E2E test scripts

## Set the required environment variable

```bash
export HF_TOKEN="Your_Huggingface_API_Token"
```

## Run test

On Intel ARC with TGI:

```bash
bash test_compose_on_arc.sh
```

On Intel ARC with vLLM:

```bash
bash test_compose_vllm_on_arc.sh
```
