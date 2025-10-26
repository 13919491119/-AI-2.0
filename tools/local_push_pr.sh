#!/usr/bin/env bash
set -euo pipefail

# local_push_pr.sh
# One-shot helper to apply the generated patch, create a branch, push to a remote
# and open a PR using gh. Intended to be run in your local clone (not in a shared
# environment) where you have your SSH keys or GitHub credentials configured.

PATCH_FILE="xuanji_changes.patch"
BRANCH=${1:-xuanji/safe-updates}
REMOTE_URL=${2:-}
REMOTE_NAME=${3:-target-origin}

usage() {
  cat <<USAGE
Usage: $0 [BRANCH] <REMOTE_URL> [REMOTE_NAME]

Example:
  $0 xuanji/safe-updates git@github.com:OWNER/REPO.git target-origin

Notes:
 - Run this locally in your cloned repository root where you have push access.
 - Script will not send credentials over chat. It expects your local git/gh
   to be authenticated.
USAGE
}

if [ "$#" -lt 1 ]; then
  echo "No REMOTE_URL provided." >&2
  usage
  exit 1
fi

if [ -n "$REMOTE_URL" ]; then
  :
fi

echo "Branch: $BRANCH"
echo "Patch file: $PATCH_FILE"
echo "Remote URL: $REMOTE_URL"
echo "Remote name: $REMOTE_NAME"

echo "-- ensure working tree is clean for tracked files --"
if [ -n "$(git status --porcelain)" ]; then
  echo "警告: 工作区存在未提交或未跟踪的改动。建议先 stash 或 commit。输出为："
  git status --porcelain
  echo "继续将基于当前 HEAD 创建分支并只提交已跟踪的变更。按 Ctrl+C 取消。"
  sleep 2
fi

# create or switch branch
if git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
  git checkout "$BRANCH"
else
  git checkout -b "$BRANCH"
fi

# Try to apply patch if exists and not already applied
if [ -f "$PATCH_FILE" ]; then
  echo "Found $PATCH_FILE. Attempting to apply if not applied..."
  PATCH_SUMMARY=$(sed -n '1,5p' "$PATCH_FILE" | tr -d '\r') || true
  TOP_SUBJECT=$(git log -1 --pretty=%B | sed -n '1p' || true)
  if echo "$TOP_SUBJECT" | grep -Fq "$PATCH_SUMMARY"; then
    echo "Patch appears applied already (top commit matches). Skipping git am." 
  else
    set +e
    git am --signoff < "$PATCH_FILE"
    AM_EXIT=$?
    set -e
    if [ $AM_EXIT -ne 0 ]; then
      echo "git am failed, aborting and trying git apply..."
      git am --abort || true
      git apply --index "$PATCH_FILE"
      git commit -m "Apply xuanji_changes.patch (safe autonomous updates)"
    else
      echo "git am success."
    fi
  fi
else
  echo "No patch file $PATCH_FILE found—skipping apply." 
fi

# add remote if not present
if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  EXIST_URL=$(git remote get-url "$REMOTE_NAME")
  if [ "$EXIST_URL" != "$REMOTE_URL" ]; then
    echo "Remote $REMOTE_NAME exists and URL differs: $EXIST_URL"
    echo "Using existing remote name. If you want to replace it, run: git remote remove $REMOTE_NAME; git remote add $REMOTE_NAME $REMOTE_URL"
  fi
else
  git remote add "$REMOTE_NAME" "$REMOTE_URL"
fi

echo "Pushing branch $BRANCH to $REMOTE_NAME..."
git fetch "$REMOTE_NAME"
git push -u "$REMOTE_NAME" "$BRANCH"

if which gh >/dev/null 2>&1; then
  echo "Creating PR with gh..."
  gh pr create --title "feat: add safe autonomous workflow & api smoke tests" --body-file PR_BODY.md --base main --head "$BRANCH" || {
    echo "gh pr create failed or interactive; you may create PR manually."
  }
else
  echo "gh not found—please create PR manually using GitHub UI."
  echo "Compare URL template: https://github.com/OWNER/REPO/compare/main...your-username:$BRANCH?expand=1"
fi

echo "Done. Verify the PR on GitHub." 
