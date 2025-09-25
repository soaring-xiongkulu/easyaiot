# WEB模块部署文档

## 项目概述
云边端一体化协同算法应用平台是一个基于 Vue 3 和 Vite 构建的现代化 Web 应用程序。该平台使用了多种技术栈，包括 Ant Design Vue、Pinia、Vue Router 等。

## 环境要求
- Node.js 版本: >=20.0.0
- pnpm 版本: >=9.0.4

## 部署步骤
### 1. 安装依赖
```
# 使用 pnpm 安装项目依赖
pnpm install
```
### 2. 构建生产版本
```
# 构建生产环境版本
pnpm build
```

### 3. 部署静态文件
构建完成后，生成的文件将位于 dist 目录中。将该目录中的所有文件部署到您的 Web 服务器或 CDN 上。

### 4. 预览部署结果
# 构建并预览部署结果
pnpm preview

# 或者仅预览已构建的 dist 目录
pnpm preview:dist

## 开发环境运行
如果需要在开发环境中运行项目:
```
# 启动开发服务器
pnpm dev
```
或者使用别名：
```
# 启动开发服务器
pnpm serve
```

## 其他有用命令
### 清理缓存
```
# 清理构建缓存
pnpm clean:cache

# 清理所有依赖
pnpm clean:lib

```
### 重新安装依赖
```
# 删除 lock 文件和 node_modules 并重新安装
pnpm reinstall

```

### 代码检查
```
# TypeScript 类型检查
pnpm type:check

# ESLint 代码检查
pnpm lint

# ESLint 代码修复
pnpm lint:fix

# Stylelint 样式检查
pnpm lint:stylelint

```

## 构建选项
项目支持多种构建模式：
```
pnpm build: 生产环境构建
pnpm build:test: 测试环境构建
pnpm build:static: 静态资源构建
pnpm build:no-cache: 清除缓存后构建
pnpm report: 构建并生成报告
```
## 注意事项
```
确保服务器环境满足 Node.js 和 pnpm 的版本要求
部署前务必执行 pnpm build 命令生成生产版本
部署后检查所有静态资源是否正确加载
根据实际需要配置服务器的反向代理规则（如果有 API 请求）
```

