# ProductivitySuite E2E test scripts

## Set the required environment variable

```bash
export HF_TOKEN="Your_Huggingface_API_Token"
```

## Run test

On Intel Xeon with TGI:

```bash
bash test_compose_on_xeon.sh
```

On AMD EPYC with TGI:

```bash
bash test_compose_on_epyc.sh
```
