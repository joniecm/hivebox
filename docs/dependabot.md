# Dependabot Configuration

This project uses [GitHub Dependabot](https://docs.github.com/en/code-security/dependabot) to automatically monitor and create pull requests for dependency updates.

## Configuration

The Dependabot configuration lives in [`.github/dependabot.yml`](../.github/dependabot.yml).

### Monitored Ecosystems

| Ecosystem | Directory | Schedule |
|-----------|-----------|----------|
| Python (`pip`) | `/` | Weekly |
| GitHub Actions | `/` | Weekly |
| Docker | `/` | Weekly |
| Terraform | `/infra/terraform` | Weekly |

## How It Works

1. Dependabot scans the configured directories for outdated dependencies on the defined schedule (weekly).
2. When an update is available, Dependabot automatically opens a pull request targeting the `main` branch.
3. Each pull request triggers the full CI/CD pipeline (lint, unit tests, integration tests, API tests, E2E tests).
4. Review and merge the pull request once all checks pass.

## Pull Request Limits

| Ecosystem | Max open PRs |
|-----------|-------------|
| Python (`pip`) | 10 |
| GitHub Actions | 10 |
| Docker | 5 |
| Terraform | 5 |

## References

- [Dependabot documentation](https://docs.github.com/en/code-security/dependabot)
- [Dependabot configuration options](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file)
