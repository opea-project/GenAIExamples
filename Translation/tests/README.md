# Translation UT test scripts

1. Set the required environment variables

   ```bash
   # Example: host_ip="192.168.1.1"
   export host_ip="External_Public_IP"
   # Example: no_proxy="localhost, 127.0.0.1, 192.168.1.1"
   export no_proxy="Your_No_Proxy"
   export HUGGINGFACEHUB_API_TOKEN="Your_Huggingface_API_Token"
   ```

2. Run UT test

   On Xeon:

   ```bash
   bash test_compose_on_xeon.sh
   ```

   On Gaudi:

   ```bash
   bash test_compose_on_gaudi.sh
   ```

   On AMD GPU base on TGI:

   ```bash
   bash test_compose_on_rocm.sh
   ```

   On AMD GPU base on vllm:

   ```bash
   bash test_compose_vllm_on_rocm.sh
   ```
