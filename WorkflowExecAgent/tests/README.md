# Validate Workflow Agent Microservice

<!-- Microservice validation for Intel Data Insight Automation platform workflow serving. -->

Microservice validation for example workflow API with sample data and sample workflow.

## Usage

Configure necessary variables as listed below. Replace the variables according to your test case.

```sh
export SDK_BASE_URL=${SDK_BASE_URL}     # If unspecified, test script defaults to <ip_address>:<workflow_api_port>. Refer to api_server_url variable under GenAIExamples/WorkflowExecAgent/tests/test_compose_vllm_example_wf_on_xeon.sh.
export SERVING_TOKEN=${SERVING_TOKEN}   # For example workflow test, can be empty as no authentication required.
export HF_TOKEN=${HF_TOKEN}
export workflow_id=${workflow_id}       # workflow_id of the serving workflow. For example workflow can be left empty
export vllm_port=${vllm_port}           # vllm serving port
export ip_address=$(hostname -I | awk '{print $1}')
export VLLM_CPU_OMP_THREADS_BIND=${VLLM_CPU_OMP_THREADS_BIND}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
```

Launch test script by running the following command.

```sh
cd GenAIExamples/WorkflowExecAgent/tests
. /test_compose_vllm_example_wf_on_xeon.sh
```

`test_compose_vllm_example_wf_on_xeon.sh` will run the other `.sh` files under `tests/`. The validation script launches 1 docker container for the agent microservice, 1 for the vllm model serving on CPU, and 1 for the example workflow API. When validation is completed, all containers will be stopped.

The test script checks if the model reasoning output response matches a partial substring. Below is an expected output from running the test script:

![image](https://github.com/user-attachments/assets/88081bc8-7b73-470d-970e-92e0fe5f96ec)

## Note

- Currently the validation test is only designed with vllm model serving (CPU only).
