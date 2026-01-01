# Kubernetes Deployment for Cogniware IMS

This directory contains Kubernetes deployment configurations for the OPEA Cogniware Inventory Management System.

## Deployment Options

### Option 1: Helm Chart Deployment

> **Note:** Publish the chart to GHCR before running CI. See `helm/PUBLISH_CHART.md` for instructions.

#### Prerequisites

- Kubernetes cluster (v1.24+)
- Helm 3.0+
- kubectl configured

#### Installation

```bash
# Create namespace
kubectl create namespace opea

# Install Cogniware IMS
helm install cogniwareims ./helm \
  --namespace opea \
  --set global.HUGGINGFACEHUB_API_TOKEN=<your-token>

# Check deployment
kubectl get pods -n opea
kubectl get svc -n opea

# Access the application
kubectl port-forward -n opea svc/cogniwareims-ui 3000:3000
```

#### Configuration

Customize deployment by editing `helm/values.yaml` or using `--set`:

```bash
helm install cogniwareims ./helm \
  --namespace opea \
  --set global.HUGGINGFACEHUB_API_TOKEN=<your-token> \
  --set cogniwareims-ui.service.type=LoadBalancer
```

#### Upgrading

```bash
helm upgrade cogniwareims ./helm --namespace opea
```

#### Uninstalling

```bash
helm uninstall cogniwareims --namespace opea
```

### Option 2: GMC (GenAI Microservices Connector) Deployment

#### Prerequisites

- Kubernetes cluster with GMC installed
- kubectl configured

#### Installation

```bash
# Install GMC (if not installed)
kubectl apply -f https://github.com/opea-project/GenAIInfra/releases/download/v1.0/gmc.yaml

# Deploy Cogniware IMS
kubectl apply -f gmc/cogniwareims.yaml

# Verify
kubectl get gmconnector cogniwareims
kubectl get pods -l app=cogniwareims
```

## Architecture

The Kubernetes deployment includes:

1. **Frontend**: Next.js application (Port 3000)
2. **Backend**: FastAPI with megaservice orchestration (Port 8000)
3. **PostgreSQL**: Relational database (Port 5432)
4. **Redis**: Vector store and cache (Port 6379)
5. **OPEA Microservices**:
   - TGI Service (Port 80)
   - LLM Microservice (Port 9000)
   - Embedding Service (Port 6000)
   - Retriever Service (Port 7000)
   - Reranking Service (Port 8000)
   - DataPrep Service (Port 6007)

## Monitoring

### Health Checks

```bash
# Check backend
kubectl exec -it <backend-pod> -n opea -- curl http://localhost:8000/api/health

# Check services
kubectl get pods -n opea
kubectl describe pod <pod-name> -n opea
```

### Logs

```bash
# View backend logs
kubectl logs -f deployment/cogniwareims-backend -n opea

# View UI logs
kubectl logs -f deployment/cogniwareims-ui -n opea
```

## Scaling

### Horizontal Pod Autoscaling

```bash
kubectl autoscale deployment cogniwareims-backend \
  --namespace opea \
  --cpu-percent=70 \
  --min=2 \
  --max=10
```

### Manual Scaling

```bash
kubectl scale deployment cogniwareims-backend --replicas=3 -n opea
```

## Troubleshooting

### Pods Not Starting

```bash
kubectl describe pod <pod-name> -n opea
kubectl get events -n opea --sort-by='.lastTimestamp'
```

### Service Connectivity

```bash
kubectl get svc -n opea
kubectl exec -it <pod-name> -n opea -- curl http://service-name:port/health
```

## References

- [OPEA Documentation](https://opea-project.github.io)
- [Helm Documentation](https://helm.sh/docs/)
- [GMC Documentation](https://github.com/opea-project/GenAIInfra)
