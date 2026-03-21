# End-to-End Testing with Venom

This project uses [Venom](https://github.com/ovh/venom) for API-focused E2E tests.

## Scope

The first E2E iteration covers two critical workflows:

- Temperature retrieval workflow (`GET /temperature`)
- Store flush workflow (`POST /store`)

These tests run against deployed environments (KinD, local, or staging) using the same suites and profile-specific variables.

## Directory Layout

```text
tests/
  e2e/
    suites/
      01_temperature_workflow.yml
      02_store_workflow.yml
    vars/
      kind.yaml
      local.yaml
      staging.example.yaml
    results/
```

## Install Venom

### Linux/macOS

```bash
curl -L https://github.com/ovh/venom/releases/download/v1.3.0/venom.linux-amd64 -o ./venom
chmod +x ./venom
sudo mv ./venom /usr/local/bin/venom
venom version
```

### Windows (PowerShell)

```powershell
Invoke-WebRequest https://github.com/ovh/venom/releases/download/v1.3.0/venom.windows-amd64.exe -OutFile venom.exe
Move-Item venom.exe "$env:USERPROFILE\\bin\\venom.exe"
$env:Path += ";$env:USERPROFILE\\bin"
venom version
```

## Run E2E Tests

### KinD deployment (recommended)

```bash
task kind:create
task kind:deploy
task test:e2e:venom:kind
```

### Local Flask deployment

```bash
task run
task test:e2e:venom:local
```

### Staging deployment

Set the target endpoint and run:

```bash
VENOM_BASE_URL=https://your-staging-hivebox.example.com task test:e2e:venom:staging
```

## Assertions and Validation Strategy

The Venom suites validate:

- HTTP status code contract for each endpoint
- JSON payload shape and required keys
- Allowed business values for status fields
- Response-time guardrails (`< 5s` on key calls)

`/temperature` intentionally accepts either:

- `200` with `average_temperature` + status (`Too Cold`, `Good`, `Too Hot`)
- `503` with documented `No temperature data available` payload

This dual contract keeps E2E stable even when upstream SenseBox data is temporarily unavailable.

## CI/CD Integration

PR workflow runs E2E in KinD via `.github/workflows/development.yml`:

1. Build/deploy stack in KinD
2. Wait until ingress endpoint is reachable
3. Run Venom suites with `tests/e2e/vars/kind.yaml`
4. Upload test results and Kubernetes diagnostics artifacts

## Maintenance Guide

When adding a new E2E workflow:

1. Add a new suite file under `tests/e2e/suites/` with numeric prefix.
2. Keep assertions aligned with route contracts in `src/routes/`.
3. Reuse profile variables (`base_url`, timeout/retry) for portability.
4. Keep tests deterministic: avoid fragile timing assumptions and prefer contract checks.
5. Run local + KinD profiles before opening PR.

When endpoint contracts change:

1. Update route-level tests (unit/integration) first.
2. Update Venom assertions in matching E2E suite.
3. Re-run PR workflow to verify end-to-end compatibility.
