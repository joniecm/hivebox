# Deployment Guide

## Local Kubernetes with kind

Create the cluster using the provided config (port 4080 is mapped for ingress):

```bash
kind create cluster --config ./infra/kind-config.yaml
```

Get the kubeconfig for the cluster:

```bash
kind get kubeconfig --name hivebox
```

Install Ingress-NGINX:

```bash
kubectl apply -k ./infra/ingress-nginx
```

Load the locally built image into kind:

```bash
kind load docker-image hivebox:v0.1.0 --name hivebox
```

Note: If you're using a locally built image with tag `hivebox:latest`, you'll need to tag your image as `v0.1.0`:

```bash
docker tag hivebox:latest hivebox:v0.1.0
kind load docker-image hivebox:v0.1.0 --name hivebox
```

Deploy all resources (app, MinIO, Valkey) using Helm:

```bash
helm install hivebox ./infra/app-chart
```

Verify the deployment:

```bash
kubectl get all
```

Wait until deployment is done (use kubectl to check) and access:

```bash
curl http://localhost:4080/version
```

Delete the cluster when finished:

```bash
kind delete cluster --name hivebox
```

---

## Helm Deployment

**About Helm:** Helm is a package manager for Kubernetes that simplifies deploying and managing applications. It uses templates to generate Kubernetes manifests and allows you to configure applications through a `values.yaml` file.

This project uses Helm exclusively for all Kubernetes deployments. The chart at `infra/app-chart/` manages all resources: the HiveBox app, MinIO, Valkey, Ingress, NetworkPolicy, and optionally the Grafana Agent.

**Install from local directory:**

```bash
# Install with default values
helm install hivebox ./infra/app-chart

# Install with custom release name
helm install my-hivebox ./infra/app-chart

# Install in specific namespace
helm install hivebox ./infra/app-chart --namespace hivebox --create-namespace

# Install with custom values file
helm install hivebox ./infra/app-chart --values custom-values.yaml

# Create a full template values file, then edit it with your settings
cp infra/app-chart/values.example.yaml infra/app-chart/values.local.yaml

# Install using the template-based local values file
helm install hivebox ./infra/app-chart --values infra/app-chart/values.local.yaml

# Override specific values via command line
helm install hivebox ./infra/app-chart \
  --set replicaCount=3 \
  --set image.tag=v0.2.0
```

Use `infra/app-chart/values.example.yaml` as the full template for local configuration (including Grafana Agent values).

**Upgrade or uninstall:**

```bash
# Upgrade existing release
helm upgrade hivebox ./infra/app-chart

# Uninstall
helm uninstall hivebox
```

---

## Grafana Agent (App-only)

This project includes a Grafana Agent setup for both metrics scraping and log collection, scoped to the app only.

- Metrics: scrapes only the HiveBox `/metrics` endpoint.
- Logs: keeps only pod logs for the HiveBox app.

The Grafana Agent is configurable via the Helm chart using `infra/app-chart/values.example.yaml` (copy it locally and set `grafanaAgent` values):

- `grafanaAgent.enabled`
- `grafanaAgent.remoteWrite.prometheus.*`
- `grafanaAgent.remoteWrite.loki.*`

Replace the placeholder remote-write URLs and credentials with your Grafana Cloud values before deploying.

---

## Security Scanning with Checkov

This project uses **Checkov** to scan Kubernetes manifests for security misconfigurations.

**Install Checkov:**

```bash
pip install checkov
```

**Run security scan:**

```bash
# Scan Helm chart templates
checkov --directory infra/app-chart/templates/ --framework kubernetes

# Compact output
checkov --directory infra/app-chart/templates/ --framework kubernetes --compact
```

**Automated scanning:** Checkov runs automatically on pull requests and pushes to main when Helm chart files change. Results are available in the GitHub Security tab.

For detailed security scan results, remediation actions, and security best practices, see [SECURITY.md](../SECURITY.md).

