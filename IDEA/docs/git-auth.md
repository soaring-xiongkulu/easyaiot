# Git HTTPS Token（工作区内自助）

EasyAIoT IDEA **不代持、不上传** 你的 Git 凭据。Token 仅写入个人工作区数据卷。

## 配置

```bash
bash scripts/idea/setup-git-auth.sh
# 或
bash scripts/idea/setup-git-auth.sh gitee <login>
```

将使用：

```text
~/project-data/.git-credentials
credential.helper = store --file=...
```

该目录随工作区卷持久化；删除工作区容器一般仍保留数据（除非运维清理卷）。

## 获取 Token

- Gitee：设置 → 私人令牌（至少 projects 相关权限）
- GitHub：Settings → Developer settings → Personal access tokens

## 推送

```bash
bash scripts/idea/push-pr.sh
```

## 清除

```bash
bash scripts/idea/clear-git-auth.sh
bash scripts/idea/clear-git-auth.sh gitee   # 只清某一平台
```

## 安全建议

- 不要把 Token 写进代码、Issue、PR 或镜像
- 不要用 `echo $TOKEN` 打日志
- 公用机器用完请执行 `clear-git-auth.sh`
