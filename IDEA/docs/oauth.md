# IDEA OAuth 配置

社区贡献者可用 **Gitee / GitHub** 登录，再创建个人工作区。

## 1. 创建应用

### Gitee

1. 打开 https://gitee.com/oauth/applications
2. 回调地址填：`{IDEA_OAUTH_REDIRECT_BASE}/api/auth/callback/gitee`  
   例：`http://192.168.1.10:9300/api/auth/callback/gitee`
3. 将 Client ID / Secret 写入 `idea.env`

### GitHub

1. 打开 https://github.com/settings/developers → OAuth Apps
2. Authorization callback URL：`{IDEA_OAUTH_REDIRECT_BASE}/api/auth/callback/github`
3. 写入 `IDEA_GITHUB_CLIENT_ID` / `IDEA_GITHUB_CLIENT_SECRET`

## 2. idea.env 关键项

```bash
IDEA_OAUTH_REDIRECT_BASE=http://192.168.1.10:9300
# 登录后回到 IDEA 门户（与 WEB 解耦）。若仍想跳 WEB 可改成 :8888/idea/index
IDEA_WEB_CALLBACK=http://192.168.1.10:9300/
IDEA_SESSION_SECRET=please-change-me
IDEA_OAUTH_REQUIRED=1   # 生产建议开启：必须登录

IDEA_GITEE_CLIENT_ID=...
IDEA_GITEE_CLIENT_SECRET=...
# 和/或
IDEA_GITHUB_CLIENT_ID=...
IDEA_GITHUB_CLIENT_SECRET=...
```

WEB 侧不再承载操作台。可选：`VITE_IDEA_URL` 仅用于管控台跳转到门户。

## 3. 流程

1. 打开 IDEA 门户 `http://<host>:9300` 点击「Gitee 登录」→ `/api/auth/login/gitee`
2. 授权后回调 `/api/auth/callback/gitee` → 写会话 → 回到门户 `/?idea_token=...`
3. 门户页面保存 `idea_token` 为 `X-IDEA-Session`，之后创建工作区使用 `gitee-<login>` 作为用户名

## 4. API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/auth/providers` | 可用登录方式 |
| GET | `/api/auth/login/:provider` | 开始 OAuth |
| GET | `/api/auth/callback/:provider` | 回调 |
| GET | `/api/auth/me` | 当前用户（需 `X-IDEA-Session`） |
| POST | `/api/auth/logout` | 退出 |
