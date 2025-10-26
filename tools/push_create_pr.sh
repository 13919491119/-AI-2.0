#!/usr/bin/env bash
set -euo pipefail

# push_create_pr.sh
# 用途：在本地自动化应用 patch（若需要）、创建分支、推送到远端并用 gh 创建 PR。
# 安全说明：脚本不会请求或存储任何秘密。请在具有写权限的本地环境运行（SSH key 或 gh 登录）。

usage() {
  cat <<'USAGE'
Usage: ./tools/push_create_pr.sh <REMOTE_URL> [BRANCH_NAME]

Arguments:
  REMOTE_URL   e.g. git@github.com:OWNER/REPO.git (推荐 SSH) 或 https://github.com/OWNER/REPO.git
  BRANCH_NAME  可选（默认 xuanji/safe-updates）

示例：
  ./tools/push_create_pr.sh git@github.com:owner/repo.git
  ./tools/push_create_pr.sh https://github.com/owner/repo.git my-branch-name

脚本步骤：
  - 在当前仓库基于 HEAD 创建分支（如果不存在）
  - 若 xuanji_changes.patch 存在且未应用，可尝试用 git am 应用
  - 将分支推送到远端（添加 remote 名称 target-origin，如果已存在则复用）
  - 用 gh 创建 PR（若 gh 未登录，将提示登录）

注意：如果仓库受保护分支限制或权限不足，push 会失败；在此情况下请考虑推送到 fork 并从 fork 发起 PR。
USAGE
}

if [ "$#" -lt 1 ]; then
  usage
  exit 1
fi

REMOTE_URL=$1
BRANCH=${2:-xuanji/safe-updates}
PATCH_FILE="xuanji_changes.patch"

echo "REMOTE_URL=${REMOTE_URL}"
echo "BRANCH=${BRANCH}"

echo "-- ensure working tree is clean --"
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
  # crude check: see if top commit message matches patch subject
  PATCH_SUMMARY=$(sed -n '1,5p' "$PATCH_FILE" | tr -d '\r') || true
  TOP_SUBJECT=$(git log -1 --pretty=%B | sed -n '1p' || true)
  if echo "$TOP_SUBJECT" | grep -Fq "$PATCH_SUMMARY"; then
    echo "Patch appears to already be applied (top commit subject matches). Skipping git am."
  else
    set +e
    git am --signoff < "$PATCH_FILE"
    AM_EXIT=$?
    set -e
    if [ $AM_EXIT -ne 0 ]; then
      echo "git am 失败，尝试用 git apply..."
      git am --abort || true
      git apply --index "$PATCH_FILE"
      git commit -m "Apply xuanji_changes.patch (safe autonomous updates)"
    else
      echo "git am 成功。"
    fi
  fi
else
  echo "No patch file $PATCH_FILE found—skipping apply." 
fi

# ensure remote
REMOTE_NAME=target-origin
if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  EXIST_URL=$(git remote get-url "$REMOTE_NAME")
  if [ "$EXIST_URL" != "$REMOTE_URL" ]; then
    echo "远端 $REMOTE_NAME 已存在且 URL 不匹配： $EXIST_URL"
    echo "将使用已存在远端的名称（$REMOTE_NAME）并尝试推送。若需改用给定 URL，请先删除或改名远端。"
  fi
else
  git remote add "$REMOTE_NAME" "$REMOTE_URL"
fi

# push
echo "Pushing branch $BRANCH to $REMOTE_NAME..."
git fetch "$REMOTE_NAME"
git push -u "$REMOTE_NAME" "$BRANCH"

# create PR using gh
if which gh >/dev/null 2>&1; then
  echo "Creating PR with gh..."
  gh pr create --title "feat: add safe autonomous workflow & api smoke tests" \
    --body-file PR_BODY.md --base main --head "$BRANCH" || {
      echo "gh pr create failed or interactive; you may create PR manually."
    }
else
  echo "gh CLI not found—please create PR manually using the GitHub UI."
  echo "Compare URL template: https://github.com/OWNER/REPO/compare/main...your-username:$BRANCH?expand=1"
fi

echo "Done. Please verify the PR in your GitHub repository."
