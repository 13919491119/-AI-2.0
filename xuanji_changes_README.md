# xuanji_changes.patch 包使用说明

目的
---

本文件包含如何在本地将工作区生成的 patch 应用到一个新的分支并推送到远端以创建 PR 的最小步骤。

前提
---

- 在本地有对目标仓库的写权限（SSH key 或 HTTPS 凭据）。
- 你正在在本地仓库根目录执行命令。
- 推荐使用 SSH 方式：<git@github.com>:OWNER/REPO.git

快速步骤
---

1) 创建并切换到分支（在本地仓库根）

```bash
git checkout -b xuanji/safe-updates
```

2) 应用 patch（如果 patch 以 mbox/git format-patch 形式生成）

```bash
# 首选（如果 patch 是 git format-patch 生成的 mbox）
git am --signoff < xuanji_changes.patch

# 若 git am 失败（非 mbox），可用下面的方法
# git apply --index xuanji_changes.patch
# git commit -m "Apply xuanji_changes.patch (safe autonomous updates)"
```

3) 检查提交

```bash
git log -1 --stat
git show --name-only HEAD
```

4) 推送分支到远端（替换 <REMOTE_URL>）

```bash
# 仅在未添加远端时运行
git remote add target-origin <REMOTE_URL>

# 拉取远端引用并推送
git fetch target-origin
git push -u target-origin xuanji/safe-updates
```

5) 创建 PR（推荐 gh CLI）

```bash
gh pr create --title "feat: add safe autonomous workflow & api smoke tests" \
  --body "包含：safe self-upgrade dry-run/manual 模式，FastAPI smoke 服务，训练入口和监控守护。请在合并前审阅 upgrade_plan_pending.json。" \
  --base main --head xuanji/safe-updates
```

验证与故障排查
---

- 若 push 被拒绝：检查远端权限或分支保护策略。解决办法常为：向你的 fork 推送并从 fork 发起 PR，或请求仓库管理员允许创建分支。
- 若 gh CLI 无法创建 PR：请确保 gh 已登录 (`gh auth login`) 或使用浏览器手动创建 PR（打开 `https://github.com/OWNER/REPO/compare/main...your-username:xuanji/safe-updates?expand=1`）。

审计信息
---

- 我已在工作区生成 `xuanji_changes.patch` 及本说明文件。你可以下载/复制到本地并按上面步骤执行。

如需我把 patch 打包为 tar.gz 或生成一个包含校验和的 bundle，请在对话中回复 “打包 patch”。
