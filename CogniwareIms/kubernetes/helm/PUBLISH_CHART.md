# Publish Cogniware IMS Helm Chart

The OPEA CI pipeline installs the chart from `oci://ghcr.io/opea-project/charts/cogniwareims:0-latest`. Before CI can succeed, make sure this tag exists in GitHub Container Registry.

## 1. Package the Chart

```bash
cd CogniwareIms/kubernetes/helm
helm package . \
  --destination ./dist \
  --version 0-latest \
  --app-version 0-latest
```

## 2. Login to GHCR

```bash
export GHCR_USER=<github-username>
export GHCR_TOKEN=<token with write:packages>
helm registry login ghcr.io \
  --username "$GHCR_USER" \
  --password "$GHCR_TOKEN"
```

## 3. Push the Chart as OCI Artifact

```bash
helm push ./dist/cogniwareims-0-latest.tgz \
  oci://ghcr.io/opea-project/charts
```

Once pushed, rerun CI to verify the helm install stage can pull the chart successfully.
