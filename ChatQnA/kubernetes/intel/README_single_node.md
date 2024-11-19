# Deploy ChatQnA in Kubernetes Cluster on Single Node environment (Minikube)

The following instructions are to deploy the ChatQnA example on a single Node using Kubernetes for testing purposes.
## Minikube setup
1. Install [Minikube](https://minikube.sigs.k8s.io/docs/start/) following the quickstart guide
2. Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
3. Build the container images, following the steps under "Build Docker Images" section in the [docker-compose README](../../docker_compose/intel/cpu/xeon/README.md) to checkout [GenAIComps](https://github.com/opea-project/GenAIComps.git) and build other images with your changes for development.
```bash
# Example on building frontend Docker image
cd GenAIExamples/ChatQnA/ui
docker build --no-cache -t opea/chatqna-ui:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f ./docker/Dockerfile .
# etc...
```
The built images should be visible in the local Docker registry. Other images which have not been built with your changes (or not present in your local Docker registry) will be pulled from [docker hub](https://hub.docker.com/u/opea) by Minikube later in step 6.
```bash
docker images | grep opea
# REPOSITORY                    TAG         IMAGE ID       CREATED         SIZE
# opea/chatqna-ui               latest      8f2fa2523b85   6 days ago      1.56GB
# opea/chatqna                  latest      7f2602a7a266   6 days ago      821MB
# ...
```
4. The built images must be imported into the Minikube registry from the local Docker registry. This can be done using `minikube load `image.
```bash
minikube image load opea/chatqna
minikube image load opea/chatqna-ui
# etc...
```
5. Start the minikube cluster with `minikube start`, check that the minikube container (kicbase) is up with `docker ps`
```bash
docker ps
# CONTAINER ID   IMAGE                                 COMMAND                  CREATED      STATUS      PORTS                                                                                                                                  NAMES
# de088666cef2   gcr.io/k8s-minikube/kicbase:v0.0.45   "/usr/local/bin/entr…"   2 days ago   Up 2 days   127.0.0.1:49157->22/tcp...   minikube
```
6. Deploy the ChatQnA application with `kubectl apply -f chatqna.yaml`, check that the opea pods are in a running state with `kubectl get pods`
```bash
kubectl get pods
# NAME                                      READY   STATUS             RESTARTS   AGE
# chatqna-78b4f5865-qbzms                   1/1     Running            0          2d3h
# chatqna-chatqna-ui-54c8dfb6cf-fll5g       1/1     Running            0          2d3h
# etc...
```

7. Forward the port of the chatqna service from Minikube to the host, and test the service as you would a normal k8s cluster deployment
```bash
# port-forward to expose the chatqna endpoint from within the minikube cluster
kubectl port-forward svc/chatqna 8888:8888
curl http://localhost:8888/v1/chatqna \
    -H 'Content-Type: application/json' \
    -d '{"messages": "What is the revenue of Nike in 2023?"}'

# Similarly port-forward to expose the chatqna-ui endpoint and use the UI at <machine-external-ip>:5173 in your browser
kubectl port-forward svc/chatqna-chatqna-ui 5173:5173
```
