# One-Click Deployment for GenAI Examples

This document provides a comprehensive guide to deploying, managing, and testing the GenAI Examples using the unified one-click interactive Python script. This script simplifies the entire workflow, from environment validation to service deployment on both Docker and Kubernetes.

## Prerequisites

Before you begin, ensure your system meets the following requirements.

### 1. System Requirements

Hardware requirements can vary significantly depending on the example and models being used. The following are general guidelines, with more demanding examples like ChatQnA requiring more resources.

- **CPU:** For optimal performance with larger models in production (e.g., on Xeon), use CPUs with more cores.
- **Memory:** A minimum of **64GB RAM**. For larger models, **128GB or more** is recommended.
- **HPU (for Gaudi deployments):** At least **2 HPU cards** are recommended for ChatQnA deployment.
- **Disk Space:** A minimum of **50GB** of free disk space is required for Docker images, models, and data.

### 2. Software Requirements

The deployment script and its underlying tools require the following software to be installed:

- **Python:** Python 3.9+ is required.
- **Python Packages:** The script depends on several Python packages. Install them using the provided `requirements.txt` file.
  ```bash
  cd one_click_deploy
  pip install -r requirements.txt
  ```
- **Docker Engine:** Required for Docker-based deployments and for building container images.
  - Install Docker by following the [official documentation](https://docs.docker.com/engine/install/).
  - Ensure the Docker daemon is running.
- **Docker Compose:** The script uses the `docker compose` command. This is typically included with modern Docker installations or can be installed as a plugin.
- **Kubernetes Tools (for K8s deployments):**
  - `kubectl`: The Kubernetes command-line tool.
  - `helm`: The package manager for Kubernetes.
- **Git:** Required for cloning repositories during the image build process for some examples.

> [!IMPORTANT]
> The `check_env.sh` script, which can be run as part of the one-click deployment, may require `sudo` privileges to perform actions like installing missing packages or configuring the CPU governor.

### 3. Environment Requirements

- **Hugging Face Hub Token:** A Hugging Face token is required to download models from the Hub.
  - You can create a token from your [Hugging Face account settings](https://huggingface.co/settings/tokens).
  - The script will prompt you for this token and can read it from the default cache location (`~/.cache/huggingface/token`) if available.
- **Network & Proxy Settings:** If you are behind a corporate firewall, you will need to provide proxy settings. The script will interactively ask for:
  - `HTTP_PROXY`
  - `HTTPS_PROXY`
  - `NO_PROXY` (The script will automatically add the host IP and localhost to this list).

---

## Getting Started: The One-Click Script

The `one_click_deploy.py` script is the central entry point for all management tasks. It provides an interactive command-line interface to guide you through deployment, testing, and cleanup.

### Running the Script

To start the interactive deployment process, run the following command from the `one_click_deploy` directory:

```bash
python3 one_click_deploy.py
```

The script will present you with a series of choices to configure your deployment.

### Interactive Walkthrough: Deploying an Example

This section walks you through a typical deployment session for the `ChatQnA` example using Docker.

1.  **Launch the script:**

    ```bash
    python3 one_click_deploy.py
    ```

2.  **Choose an Example:** The script will list all available examples from the configuration.

    ```text
    Please choose an example to manage:
      [1] ChatQnA
      [2] CodeTrans
      [3] DocSum
      [4] CodeGen
      [5] AudioQnA
    [1-5] (1): 1
    ```

3.  **Choose an Action:** Select `Deploy` to start the installation process.

    ```text
    Please choose an action:
      [1] Deploy
      [2] Clear
      [3] Test Connection
    [1-3] (1): 1
    ```

4.  **Configure Deployment:** The script will now ask for deployment-specific parameters.

    ```text
    Deployment Mode [docker/k8s] (docker): docker
    Target Device [xeon/gaudi] (xeon): xeon
    Hugging Face Token (cached found): ****************
    HTTP Proxy []: http://your-proxy.com:8080
    HTTPS Proxy []: http://your-proxy.com:8080
    No Proxy hosts [localhost,127.0.0.1,10.0.1.5]:
    ```

5.  **Configure Example Parameters:** Provide the model IDs and other parameters specific to the chosen example. Defaults are provided.

    ```text
    LLM Model ID (e.g., meta-llama/Meta-Llama-3-8B-Instruct) [meta-llama/Meta-Llama-3-8B-Instruct]:
    Embedding Model ID (e.g., BAAI/bge-base-en-v1.5) [BAAI/bge-base-en-v1.5]:
    Reranking Model ID (e.g., BAAI/bge-reranker-base) [BAAI/bge-reranker-base]:
    Data Mount Directory (for Docker) [./data]:
    ```

6.  **Select Optional Steps:** Choose whether to run pre-flight checks, build images, or run post-deployment tests.

    ```text
    Run environment check? [y/N]: y
    Update images (build/push)?: n
    Run connection tests after deployment? [y/N]: y
    ```

7.  **Confirm and Deploy:** Review the summary and confirm to start the deployment.

    ````text
    ======================================================================
    == CONFIGURATION SUMMARY ==
    ======================================================================

        📘   Deploy Mode: docker
        📘   Target Device: xeon
        ...
        Proceed with deployment? [Y/n]: y
        ```

    The script will now execute all the selected steps: check the environment, configure services, and deploy using Docker Compose.
    ````

### Testing a Deployed Service

You can test a running deployment at any time by selecting the `Test Connection` action.

1.  Choose the `Test Connection` action.
2.  Specify how the service was deployed (`docker` or `k8s`) and on which device.
3.  If testing a Kubernetes service, provide a local port for port-forwarding (e.g., `8080`).
4.  The script will then establish a connection and run a pre-defined test against the main service endpoint, reporting whether it passed or failed.

```bash
# Example test run for a Docker deployment
$ python3 one_click_deploy.py
# ... choose example and 'Test Connection' action ...
Deployment Mode [docker/k8s] (docker): docker
Target Device [xeon/gaudi] (xeon): xeon
...
======================================================================
== TESTING CONNECTION FOR CHATQNA ==
======================================================================

📘 [INFO] Testing POST http://10.0.1.5:8888/v1/chatqna
✅ [OK] Test '/v1/chatqna' PASSED.
📘 [INFO] Test Summary: Passed: 1, Failed: 0, Skipped: 0
```

### Clearing a Deployment

To stop and remove a deployed example, use the `Clear` action. This is crucial for releasing resources and avoiding conflicts.

1.  Choose the `Clear` action.
2.  Select the deployment mode (`docker` or `k8s`) that you want to clear.
3.  If clearing a Docker deployment, specify the device it was deployed on.
4.  If clearing a Kubernetes deployment, you will be asked if you also want to delete the entire namespace.

The script will then run the appropriate commands (`docker compose down -v` or `helm uninstall`) to tear down the services.

---

## Verifying the Deployment

After the script finishes, you can manually verify that all services are running correctly.

**For Docker Compose deployments:**
Run `docker ps` to see all running containers. All service containers for the example should be in the `Up` state.

```shell
docker ps
```

To check the logs of a specific service (e.g., the backend):

```shell
# Find the container name with 'docker ps' first
docker logs chatqna-xeon-backend-server
```

**For Kubernetes deployments:**
Run `kubectl get pods -n <namespace>` to verify that all pods are in the `Running` or `Completed` state. The default namespace is typically the name of the example (e.g., `chatqna`).

```shell
# Check pods and services in the 'chatqna' namespace
kubectl get pods -n chatqna
kubectl get svc -n chatqna
```

To check the logs of a specific pod:

```shell
# Find the pod name with 'kubectl get pods' first
kubectl logs chatqna-backend-server-svc-xxxxxxxx-yyyyy -n chatqna
```

---

## Troubleshooting

If you encounter issues, refer to the following common problems and solutions.

- **Environment Check Fails:**

  - **Problem:** The script reports that required commands like `docker` or `helm` are missing.
  - **Solution:** Manually install the missing software using your system's package manager. Review the output of the environment check and the log file (`one_click_deploy/deployment.log`) for details.

- **Docker Image Pull Errors:**

  - **Problem:** Docker fails to pull images, often with an `authentication required` or `timeout` error.
  - **Solution:**
    1.  **Check HF Token:** Ensure the Hugging Face token you provided is correct and has the necessary permissions.
    2.  **Check Proxy Settings:** If you are behind a firewall, ensure your `http_proxy` and `https_proxy` settings are correct.
    3.  **Check Disk Space:** A `no space left on device` error indicates you need to free up disk space.

- **Kubernetes Pods Stuck in `Pending` or `ImagePullBackOff`:**

  - **Problem:** Pods fail to start.
  - **Solution:**
    1.  Use `kubectl describe pod <pod-name> -n <namespace>` to get detailed events.
    2.  **`ImagePullBackOff`:** This often means the Kubernetes cluster cannot access the container image. Check that the image registry and tag are correct and that your cluster has credentials to pull from it (the Helm chart should handle this if using a public registry, but the HF token is still crucial for models).
    3.  **`Pending`:** This can be due to insufficient resources (CPU/memory/HPU) on your cluster nodes. Check the pod description for messages about resource constraints.

- **Connection Test Fails:**
  - **Problem:** The script reports that it cannot connect to the service endpoint.
  - **Solution:**
    1.  Verify that all containers/pods are running correctly using the steps in the [Verifying the Deployment](#verifying-the-deployment) section.
    2.  Check the logs of the main service container/pod for any startup errors.
    3.  Ensure no firewalls are blocking the connection between your machine and the service port (for Docker) or the `kubectl port-forward` connection (for K8s).
