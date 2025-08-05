# ChatQnA E2E test scripts

## Set the required environment variable

```bash
export HF_TOKEN="Your_Huggingface_API_Token"
```

## Run test

On Intel Xeon with TGI:

```bash
bash test_compose_tgi_on_xeon.sh
```

On Intel Xeon with vLLM:

```bash
bash test_compose_on_xeon.sh
```

On Intel Xeon with MariaDB Vector:

```bash
bash test_compose_mariadb_on_xeon.sh
```

On Intel Xeon with Pinecone:

```bash
bash test_compose_pinecone_on_xeon.sh
```

On Intel Xeon with Milvus

```bash
bash test_compose_milvus_on_xeon.sh
```

On Intel Xeon with Qdrant

```bash
bash test_compose_qdrant_on_xeon.sh
```

On Intel Xeon without Rerank:

```bash
bash test_compose_without_rerank_on_xeon.sh
```

On Intel Gaudi with TGI:

```bash
bash test_compose_tgi_on_gaudi.sh
```

On Intel Gaudi with vLLM:

```bash
bash test_compose_on_gaudi.sh
```

On Intel Gaudi with Guardrails:

```bash
bash test_compose_guardrails_on_gaudi.sh
```

On Intel Gaudi without Rerank:

```bash
bash test_compose_without_rerank_on_gaudi.sh
```

On AMD EPYC with TGI:

```bash
bash test_compose_tgi_on_epyc.sh
```

On AMD EPYC with vLLM:

```bash
bash test_compose_on_epyc.sh
```

On AMD EPYC with Pinecone:

```bash
export PINECONE_KEY_LANGCHAIN_TEST="Pinecone_API_Key"

bash test_compose_pinecone_on_epyc.sh
```

On AMD EPYC with Milvus

```bash
bash test_compose_milvus_on_epyc.sh
```

On AMD EPYC with Qdrant

```bash
bash test_compose_qdrant_on_epyc.sh
```

On AMD EPYC without Rerank:

```bash
bash test_compose_without_rerank_on_epyc.sh
```

On AMD ROCm with TGI:

```bash
bash test_compose_on_rocm.sh
```

On AMD ROCm with vLLM:

```bash
bash test_compose_vllm_on_rocm.sh
```

Test FAQ Generation On Intel Xeon with TGI:

```bash
bash test_compose_faqgen_tgi_on_xeon.sh
```

Test FAQ Generation On Intel Xeon with vLLM:

```bash
bash test_compose_faqgen_on_xeon.sh
```

Test FAQ Generation On Intel Gaudi with TGI:

```bash
bash test_compose_faqgen_tgi_on_gaudi.sh
```

Test FAQ Generation On Intel Gaudi with vLLM:

```bash
bash test_compose_faqgen_on_gaudi.sh
```

Test FAQ Generation On AMD ROCm with TGI:

```bash
bash test_compose_faqgen_on_rocm.sh
```

Test FAQ Generation On AMD ROCm with vLLM:

```bash
bash test_compose_faqgen_vllm_on_rocm.sh
```
