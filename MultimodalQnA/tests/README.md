# MultimodalQnA E2E test scripts

## Set the required environment variable

```bash
export HF_TOKEN="Your_Huggingface_API_Token"
```

## Run test

On Intel Xeon with vLLM:

```bash
bash test_compose_on_xeon.sh
```

On Intel Xeon with TGI:

```bash
bash test_compose_tgi_on_xeon.sh
```

On Intel Gaudi with vLLM:

```bash
bash test_compose_on_gaudi.sh
```

On Intel Gaudi with TGI:

```bash
bash test_compose_tgi_on_gaudi.sh
```

On AMD EPYC with vLLM:

```bash
bash test_compose_on_epyc.sh
```

On AMD EPYC with Milvus:

```bash
bash test_compose_milvus_on_epyc.sh
```

On AMD ROCm with TGI:

```bash
bash test_compose_on_rocm.sh
```

On AMD ROCm with vLLM:

```bash
bash test_compose_vllm_on_rocm.sh
```
