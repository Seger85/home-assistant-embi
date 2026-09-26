# Repository automation

Seven maintained workflows cover development and releases:

| Workflow | Responsibility |
|---|---|
| `quality.yml` | Unit tests, Ruff, MyPy, repository contracts and real Home Assistant tests |
| `test-artifact.yml` | Build and verify an installable test package |
| `hacs.yml` | HACS validation |
| `hassfest.yml` | Home Assistant integration validation |
| `dependabot-automerge.yml` | Validate dependency updates before merging |
| `release.yml` | Prepare, publish and verify versioned releases; resume incomplete releases |
| `repository-hygiene.yml` | Remove completed run history for retired workflows |

GitHub also manages Dependabot update and dependency-graph workflows. These dynamic workflows are retained.

## Retired workflow history

The repository-maintenance workflow runs weekly. It only removes completed runs when the associated workflow is **manually disabled** and its YAML file is **absent from the current checkout**. It checks workflow and run state again immediately before deletion. Active workflows, remaining YAML files and unfinished runs are protected. Commits, tags, releases and Home Assistant registries are outside its scope.

For a preview, run **Repository maintenance** manually with `apply` disabled. Set `apply` to true to delete matching historical runs. Deletion also removes their logs and artifacts and cannot be undone. GitHub may retain internal workflow metadata after its visible run history is gone; there is no separate supported workflow-registration deletion endpoint.

The workflow uses the short-lived repository `GITHUB_TOKEN` with `actions: write`; it does not require another personal token. Actions are pinned to commit IDs. Production CI and release history are retained.
