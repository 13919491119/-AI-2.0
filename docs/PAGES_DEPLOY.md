# GitHub Pages publish for visualizations

This file documents the safe CI-based process to publish the generated visualizations under `reports/visualization` to GitHub Pages, and summarizes recent recovery steps.

Why use Actions
- The environment used earlier lacked permission to call the Pages REST API (HTTP 403). Using the official Actions (`upload-pages-artifact` + `deploy-pages`) executes in CI with repository permissions and is safer.

How the workflow works
- Workflow file: `.github/workflows/publish-visualizations.yml`.
- It uploads `reports/visualization` as a Pages artifact and uses `actions/deploy-pages` to publish the artifact.
- Trigger: manual (`workflow_dispatch`) or `push` to `main`.

Manual trigger
1. On GitHub, go to Actions → "Publish visualizations to GitHub Pages" workflow.
2. Click "Run workflow" and choose the `main` branch.

Notes about recent recovery
- A previous attempt to create a pages branch and call the Pages REST API failed with 403 and an unintended push was made. Remote `main` was force-reset to a known-good merge commit (commit id `1ac658a4`).
- A fresh workspace clone was restored during recovery. The workflow file in this repository was corrected (duplicate definitions removed) and validated.

Next steps (automated)
1. Merge this docs PR after review.
2. Trigger the workflow manually once via Actions UI or run `gh workflow run 'publish-visualizations.yml' --ref main`.

If you need me to trigger the workflow now, I can attempt to run it and report the run status and Pages URL.
