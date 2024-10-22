# Validate Workflow Agent Microservice

Microservice validation for Intel Data Insight Automation platform workflow serving.

## Usage

Configure necessary variables as listed below. Replace the variables according to your usecase.

```sh
export SDK_BASE_URL=${SDK_BASE_URL}
export SERVING_TOKEN=${SERVING_TOKEN}
export HUGGINGFACEHUB_API_TOKEN=${HF_TOKEN}
export workflow_id=${workflow_id}       # workflow_id of the serving workflow
export vllm_port=${vllm_port}           # vllm serving port
export ip_address=$(hostname -I | awk '{print $1}')
export VLLM_CPU_OMP_THREADS_BIND=${VLLM_CPU_OMP_THREADS_BIND}
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
```

Note: `SDK_BASE_URL` and `SERVING_TOKEN` can be obtained from Intel Data Insight Automation platform.

Launch validation by running the following command.

```sh
cd GenAIExamples/WorkflowExecAgent/tests
. /test_compose_on_xeon.sh
```

`test_compose_on_xeon.sh` will run the other `.sh` files under `tests/`. The validation script launches 1 docker container for the agent microservice, and another for the vllm model serving on CPU. When validation is completed, all containers will be stopped.

The validation is tested by checking if the model reasoning output response matches a partial substring. The expected output is shown below:

![image](https://github.com/user-attachments/assets/88081bc8-7b73-470d-970e-92e0fe5f96ec)

## Note

- Currently the validation test is only designed with vllm model serving (CPU only).
