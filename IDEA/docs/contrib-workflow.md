# 社区贡献工作流（IDEA 工作区内）

## 目标

在浏览器 IDE 中改 EasyAIoT，推送到**个人 fork**，再向官方仓提 PR。

## 首次准备

1. 网页 Fork 官方仓（Gitee / GitHub）
2. 打开终端：

```bash
bash scripts/idea/setup-fork.sh
bash scripts/idea/setup-git-auth.sh   # 个人 HTTPS Token，仅存工作区数据卷
```

效果：

- `upstream` → 官方只读仓  
- `origin` → 你的 fork（可写）
- Git credential helper → `~/project-data/.git-credentials`（不上传门户）

3. 确认：

```bash
bash scripts/idea/contrib-status.sh
```

若 OAuth 登录过，工作区会预填 `user.name` / 建议 fork 地址（见 `IDEA-CONTRIB.md`）。

## 日常开发

```bash
git fetch upstream
git checkout -b feat/xxx
# 编辑代码…
git add -A
git commit -m "feat: xxx"
bash scripts/idea/push-pr.sh
```

按提示打开官方仓创建 PR，并参考 `IDEA-PR-CHECKLIST.md` / 仓库内 PR 模板。

## 同步官方更新

```bash
git fetch upstream
git checkout master   # 或 main
git merge upstream/master
# 或: git rebase upstream/master
git push origin master
```

也可把 origin 改成自建 GitLab：门户「贡献代码」里保存 HTTPS 地址，或

```bash
bash scripts/idea/setup-fork.sh . https://gitlab.example.com/you/easyaiot.git
bash scripts/idea/setup-git-auth.sh gitlab
```

看效果（不经过 WEB 按钮）：打开门户 → **发布到本机**。

## VS Code 任务

`Terminal → Run Task…`：

- **IDEA: 发布到本机（打开门户说明）**
- **IDEA: 推送并提示 PR**
- **IDEA: 贡献状态**

## 注意

- 平台**不代持**你的 Git 密码；Token 只在本工作区磁盘
- 清除凭据：`bash scripts/idea/clear-git-auth.sh`
- 大模块编译优先走 CI，不必强求在 IDEA 容器内编过 RUNTIME/VIDEO
