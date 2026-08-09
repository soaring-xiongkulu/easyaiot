# Git 远程与上游政策

## 当前 remote（2026-08-09）

| 名称 | URL |
|------|-----|
| upstream | https://github.com/soaring-xiongkulu/easyaiot.git |

公司 origin 尚未配置；日后: git remote add origin <公司 URL>

## 政策

- 不长期跟踪 upstream，无自动同步。
- 选择性合并：人工 fetch / cherry-pick / 合并并回归。
- 默认分支 main，本阶段不建行业分支。
