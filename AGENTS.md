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
