#!/usr/bin/env bash
# Auto-merge and deploy script (requires gh CLI and kubectl in PATH and proper secrets/config)

set -euo pipefail

PR_TITLE=""
DRY_RUN=true

while [[ $# -gt 0 ]]; do
  case $1 in
    --pr-title) PR_TITLE=$2; shift 2;;
    --dry-run=*) DRY_RUN=${1#*=}; shift;;
    --dry-run) DRY_RUN=$2; shift 2;;
    *) echo "Unknown arg $1"; exit 1;;
  esac
done

if [[ -z "$PR_TITLE" ]]; then
  echo "--pr-title required" >&2
  exit 2
fi

echo "Auto-merge and deploy (dry-run=$DRY_RUN) for PR title contains: $PR_TITLE"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "DRY RUN: Would find PR via gh, merge it, then run deploy_canary.sh"
  echo "Example commands (when enabled):"
  echo "  gh pr list --search \"$PR_TITLE\""
  echo "  gh pr merge <pr-number> --squash --admin"
  echo "  ./tools/deploy_canary.sh --artifact artifacts --namespace canary --dry-run=false"
  exit 0
fi

PR_NUM=$(gh pr list --search "$PR_TITLE" --json number --jq '.[0].number')
if [[ -z "$PR_NUM" || "$PR_NUM" == "null" ]]; then
  echo "PR not found" >&2
  exit 3
fi

echo "Merging PR #$PR_NUM"
gh pr merge "$PR_NUM" --squash --admin

echo "Triggering deploy"
./tools/deploy_canary.sh --artifact artifacts --namespace canary --dry-run=false
