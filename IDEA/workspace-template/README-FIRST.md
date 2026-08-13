# EasyAIoT IDEA — 欢迎

默认已打开完整仓库。操作台在 **IDEA 门户**（浏览器打开 `:9300`），与 WEB 管控台解耦。

## 建议流程

1. 门户点 **进入 IDE**
2. 改代码（Copilot 登录可选）
3. 回到门户 **发布到本机**（按 git 改动勾选模块）→ **打开现网** 看效果
4. 满意后填自己的 origin（Gitee / GitHub / GitLab），IDE 里配置 Token，再 `bash scripts/idea/push-pr.sh`

```bash
bash scripts/idea/setup-fork.sh . <你的仓库.git>
bash scripts/idea/setup-git-auth.sh
bash scripts/idea/setup-copilot.sh
bash scripts/idea/push-pr.sh
```

发布说明：`bash scripts/idea/publish-local.sh`

## 注意

- 发布替换的是本机正在跑的业务容器，不是预览网址
- 不会重启 IDEA 门户或本工作区
- 不要把 Token 写进仓库
