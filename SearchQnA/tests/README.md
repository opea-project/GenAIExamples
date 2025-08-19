# SearchQnA E2E test scripts

## Set the required environment variable

```bash
export HF_TOKEN="Your_Huggingface_API_Token"
export GOOGLE_API_KEY="your google api key"
export GOOGLE_CSE_ID="your cse id"
```

## Run test

On Intel Xeon with TGI:

```bash
bash test_compose_on_xeon.sh
```

On Intel Gaudi with TGI:

```bash
bash test_compose_on_gaudi.sh
```

On AMD EPYC with TGI:

```bash
bash test_compose_on_epyc.sh
```

On AMD ROCm with TGI:

```bash
bash test_compose_on_rocm.sh
```

On AMD ROCm with vLLM:

```bash
bash test_compose_vllm_on_rocm.sh
```
