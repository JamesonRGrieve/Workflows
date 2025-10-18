# Meta-testing Harness

This directory contains isolated sample projects and helper scripts that exercise the reusable workflows in this repository without depending on downstream consumers. Everything under `meta_testing/` is safe to modify when rehearsing workflow changes and is not used by production triggers.

## Projects

- `projects/python/sample_app/` – Minimal Python application with deterministic pytest coverage.
- `projects/typescript/sample_app/` – ESLint-ready TypeScript project with strict linting rules.
- `projects/dotnet/` – .NET solution with xUnit tests that mirror the structure expected by the reusable workflow.

Each project is intentionally small so that workflow iterations are fast. The surrounding scripts can inject failures to validate regression detection logic.

## Scripts

Scripts live under `meta_testing/scripts/` and are grouped by language. They provide idempotent helpers that introduce predictable failures (for example, appending a failing test) so that regression gates can be rehearsed.

## Workflows

Dedicated `meta-*` workflows in `.github/workflows/` call into the reusable workflow definitions with `project_path` overrides, ensuring the meta assets stay isolated from the rest of the repository. The available entry points are:

- `meta-python-harness.yml` – Runs the pytest reusable workflow against `projects/python/sample_app` and can optionally inject a failing test before re-running.
- `meta-typescript-harness.yml` – Rehearses the TypeScript lint workflow, bootstrapping dependencies inside `projects/typescript/sample_app` before optionally adding a lint violation.
- `meta-dotnet-harness.yml` – Executes the .NET test workflow on `projects/dotnet` and can append a failing xUnit test to verify regression detection.

Each harness exposes a `simulate_regression` input so you can validate both the healthy and failing paths in a single manual dispatch run.
