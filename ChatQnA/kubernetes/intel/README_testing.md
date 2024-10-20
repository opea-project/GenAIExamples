# Deploy ChatQnA in Kubernetes Cluster on Single Node environment

The following instructions are to deploy the ChatQnA example on a single Node using Kubernetes for testing purposes. 
It requires [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/) to be installed on the target environmenet whether it is using Xeon or Gaudi.

## Steps

1. Install [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/) following the quickstart guide
2. Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
2. Do `docker ps` and check that the `kind-control-plane` container is up
3. 