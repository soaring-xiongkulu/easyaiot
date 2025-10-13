# 多人协作 Git 操作规范指南

为了保证团队在多人协作开发过程中的代码一致性、可追溯性和稳定性，特制定以下 Git 分支管理规范。

---

## 1. 主分支 [master](file:///projects/easyaiot/WEB/src/api/infra/fileConfig/index.ts#L19-L19)

- **用途**：用于发布提供给用户使用的正式版本。
- **特点**：
    - 稳定、经过测试的代码才能合并到该分支。
    - 所有正式对外发布的版本均基于此分支构建。

---

## 2. 开发分支 `dev`

- **用途**：日常功能开发和集成使用。
- **操作规范**：
    - 所有新功能和改进应在此分支上进行开发或合并。
    - 当准备对外发布时，需将 `dev` 分支合并至 [master](file:///projects/easyaiot/WEB/src/api/infra/fileConfig/index.ts#L19-L19) 分支。

---

## 3. 临时分支

> 所有临时分支均应从最新的 `origin/master` 拉取创建，确保代码同步最新状态。使用完毕后应及时删除。

### 3.1 功能分支（Feature Branch）

- **用途**：开发特定功能。
- **来源分支**：`dev`
- **目标分支**：开发完成后合入 `dev`
- **命名规范**：`feature-{功能名称}-{姓名缩写}`  
  示例：`feature-user-login-ljl`

### 3.2 Bug 修复分支（Hotfix Branch）

- **用途**：紧急修复线上问题。
- **来源分支**：[master](file:///projects/easyaiot/WEB/src/api/infra/fileConfig/index.ts#L19-L19)
- **目标分支**：修复完成后需同时合入 [master](file:///projects/easyaiot/WEB/src/api/infra/fileConfig/index.ts#L19-L19) 和 `dev`
- **命名规范**：`hotfix-{功能名称}-{姓名缩写}`  
  示例：`hotfix-payment-fail-tj`

> ⚠️ 注意事项：
>
> - 在修复过程中，应先 `merge origin master` 获取最新修改，避免冲突。
> - 该类型分支**仅允许合并到 [master](file:///projects/easyaiot/WEB/src/api/infra/fileConfig/index.ts#L19-L19) 和 `dev`**，不可主动合并其他非主干分支，以防引入无关变更。