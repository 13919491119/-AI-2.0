#!/usr/bin/env bash
# One-shot script to push branch, create PR, optionally auto-merge and deploy to canary.
# Intended to be run on a trusted host where credentials (SSH key, GH_TOKEN, KUBECONFIG) are configured.
# Safety: dry-run mode is default. To execute actions, pass --dry-run=false explicitly.

set -euo pipefail

SCRIPT_NAME=$(basename "$0")

REMOTE_URL=""
BRANCH="xuanji/safe-updates"
PR_TITLE="feat: add safe autonomous workflow, FastAPI smoke service, and monitoring"
PR_BODY_FILE="PR_BODY.md"
DRY_RUN=true
AUTO_MERGE=false
DEPLOY=false
ARTIFACT_DIR="artifacts"

usage(){
  cat <<EOF
Usage: $SCRIPT_NAME [--remote-url <git@github.com:OWNER/REPO.git>] [--branch <branch>] [--dry-run=(true|false)] [--auto-merge=(true|false)] [--deploy=(true|false)]

This script will:
  - ensure branch exists locally
  - add remote if provided and not present
  - push branch to remote
  - create a PR via gh
  - optionally auto-merge the PR and trigger canary deploy

Defaults: branch=$BRANCH, dry-run=$DRY_RUN

IMPORTANT: By default this is a dry-run which only prints commands. To perform actions set --dry-run=false.
EOF
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote-url) REMOTE_URL=$2; shift 2;;
    --branch) BRANCH=$2; shift 2;;
    --dry-run=*) DRY_RUN=${1#*=}; shift;;
    --dry-run) DRY_RUN=$2; shift 2;;
    --auto-merge=*) AUTO_MERGE=${1#*=}; shift;;
    --auto-merge) AUTO_MERGE=$2; shift 2;;
    --deploy=*) DEPLOY=${1#*=}; shift;;
    --deploy) DEPLOY=$2; shift 2;;
    --artifact-dir) ARTIFACT_DIR=$2; shift 2;;
    -h|--help) usage;;
    *) echo "Unknown arg: $1"; usage;;
  esac
done

echo "Run configuration: branch=$BRANCH, remote=$REMOTE_URL, dry-run=$DRY_RUN, auto-merge=$AUTO_MERGE, deploy=$DEPLOY"

cmd(){
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY RUN: $*"
  else
    echo "+ $*"
    eval "$@"
  fi
}

# Preconditions
if ! command -v git >/dev/null 2>&1; then
  echo "git not found on PATH" >&2; exit 2
fi
if ! command -v gh >/dev/null 2>&1; then
  echo "gh (GitHub CLI) not found on PATH" >&2; exit 2
fi

if [[ -n "$REMOTE_URL" ]]; then
  # Add remote if not present
  if ! git remote | grep -q '^target-origin$'; then
    cmd git remote add target-origin "$REMOTE_URL"
  else
    echo "remote 'target-origin' already exists locally"
  fi
fi

# Ensure working tree is clean
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is not clean; please commit or stash changes before running this script." >&2
  git status --porcelain
  exit 3
fi

# Ensure branch exists
if git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
  echo "Branch $BRANCH exists locally"
else
  echo "Branch $BRANCH does not exist locally. Creating from current HEAD"
  cmd git checkout -b "$BRANCH"
fi

# Push branch
if [[ -n "$REMOTE_URL" ]]; then
  cmd git push -u target-origin "$BRANCH"
else
  echo "No remote URL provided; cannot push. Use --remote-url to set remote." >&2
fi

# Create PR
PR_NUMBER=""
if [[ -f "$PR_BODY_FILE" ]]; then
  # Use gh to create PR
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY RUN: gh pr create --title \"$PR_TITLE\" --body-file $PR_BODY_FILE --base main --head $BRANCH"
  else
    PR_JSON=$(gh pr create --title "$PR_TITLE" --body-file "$PR_BODY_FILE" --base main --head "$BRANCH" --json number,url 2>/dev/null)
    PR_NUMBER=$(echo "$PR_JSON" | jq -r .number)
    PR_URL=$(echo "$PR_JSON" | jq -r .url)
    echo "Created PR #$PR_NUMBER -> $PR_URL"
  fi
else
  echo "PR body file $PR_BODY_FILE not found; creating PR with inline body"
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY RUN: gh pr create --title \"$PR_TITLE\" --body \"Automated PR\" --base main --head $BRANCH"
  else
    PR_JSON=$(gh pr create --title "$PR_TITLE" --body "Automated PR" --base main --head "$BRANCH" --json number,url)
    PR_NUMBER=$(echo "$PR_JSON" | jq -r .number)
    PR_URL=$(echo "$PR_JSON" | jq -r .url)
    echo "Created PR #$PR_NUMBER -> $PR_URL"
  fi
fi

# Optionally auto-merge
if [[ "$AUTO_MERGE" == "true" ]]; then
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY RUN: gh pr merge $PR_NUMBER --squash --delete-branch"
  else
    if [[ -z "$PR_NUMBER" || "$PR_NUMBER" == "null" ]]; then
      echo "PR number unknown; attempting to find by branch"
      PR_NUMBER=$(gh pr list --head "$BRANCH" --state open --json number --jq '.[0].number') || true
    fi
    if [[ -n "$PR_NUMBER" && "$PR_NUMBER" != "null" ]]; then
      gh pr merge "$PR_NUMBER" --squash --delete-branch
      echo "Merged PR #$PR_NUMBER"
    else
      echo "No PR found to merge" >&2
    fi
  fi
fi

# Optionally deploy
if [[ "$DEPLOY" == "true" ]]; then
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY RUN: ./tools/auto_merge_and_deploy.sh --pr-title \"$PR_TITLE\" --dry-run=false"
  else
    ./tools/auto_merge_and_deploy.sh --pr-title "$PR_TITLE" --dry-run=false
  fi
fi

echo "Script finished. Check PR and CI status on GitHub."
