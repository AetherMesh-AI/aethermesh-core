# AetherMesh Core Agent Notes

This repository keeps a Graphify knowledge graph under `graphify-out/`.

When answering architecture questions, planning the next implementation step, or making non-trivial code changes:

1. Prefer querying the graph before reading many files:
   ```bash
   graphify query "<question>"
   ```
2. Use focused graph commands when useful:
   ```bash
   graphify explain "<symbol-or-concept>"
   graphify path "<A>" "<B>"
   ```
3. After code changes land on `main`, refresh the graph with:
   ```bash
   graphify update .
   ```

The automation loop normally handles the post-merge graph refresh. Keep generated Graphify artifacts inside `graphify-out/`.

## PR validation gates

Before opening, updating, or marking a PR as ready, run the repo-native validation gates from the repository root.

Fast local gate for ordinary code/CI edits:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/full_test.py --mode fast --base origin/main --keep-going
```

This must pass before a PR can be considered locally validated. It covers the cheap required checks: tests, 100% branch coverage, ruff, ruff format, strict mypy, test-integrity, dependency-review, workflow-security, and PR-size.

Full PR gate when validating merge readiness or changes that can affect mutation/security/build/install checks:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/full_test.py --mode full --base origin/main --keep-going
```

If debugging mutation score directly, run:

```bash
python3 scripts/mutmut_early_fail.py --minimum 95 --max-children "$(sysctl -n hw.ncpu)"
python3 scripts/ci_quality_gates.py mutation-score --minimum 95
```

On Linux CI, use `$(nproc)` instead of `$(sysctl -n hw.ncpu)`. `mutants/` is mutmut's disposable local cache/state: keep it only during an active mutation-debugging loop, never commit it, and remove it before reporting a clean workspace or committing.

Do not push a PR update after code changes unless the relevant local gate passes, or the blocker is explicitly reported. Before committing, run `git diff --check`, stage only intentional files, and keep generated/local artifacts out of the commit.
