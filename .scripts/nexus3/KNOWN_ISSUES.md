# Nexus3 已知问题说明

## Azure Blob Store 用户已知问题

### 问题描述

在 Nexus3 管理平台中，您可能会看到以下提示：

> **Known Issue for Azure Blob Store Users**
> 
> Running the Repair - reconcile component database from blob store task with integrity check enabled may incorrectly remove content from repositories using an Azure blob store. Avoid using this task with integrity check selected.

### 问题详情

- **影响范围**: 使用 Azure Blob Store 作为存储后端的仓库
- **触发条件**: 运行修复任务 "Repair - reconcile component database from blob store" 时启用了完整性检查（integrity check）
- **潜在风险**: 可能会错误地删除仓库中的内容

### 解决方案

#### 1. 避免使用完整性检查

如果您使用 Azure Blob Store，**请勿**在运行以下任务时启用完整性检查：
- **Repair - reconcile component database from blob store**

**操作建议**:
- 如果必须运行此修复任务，请确保**取消勾选** "Integrity check" 选项
- 或者使用其他修复任务来维护仓库

#### 2. 使用其他存储后端（可选）

如果您尚未配置存储，可以考虑使用：
- **File System Storage**（默认，本地文件系统）
- **S3 Blob Store**（Amazon S3）
- **Google Cloud Storage**

这些存储后端不受此问题影响。

#### 3. 备份数据

在运行任何修复任务之前，**强烈建议**：
1. 备份 Nexus3 数据目录
2. 导出重要仓库的配置
3. 记录当前仓库状态

### 如何检查是否使用 Azure Blob Store

1. 登录 Nexus3 管理平台
2. 进入 **Administration** → **Repository** → **Blob Stores**
3. 查看已配置的 Blob Store 类型
4. 如果看到 "Azure Blob Store" 类型的存储，则需要注意此问题

### 相关链接

- [Nexus3 官方文档](https://help.sonatype.com/repomanager3)
- [Nexus3 已知问题](https://help.sonatype.com/repomanager3/product-information/release-notes)

### 注意事项

- 此问题仅影响使用 Azure Blob Store 的仓库
- 如果您的 Nexus3 使用默认的文件系统存储，则不受此问题影响
- 此问题已在后续版本中修复，建议定期更新 Nexus3 到最新版本

---

**最后更新**: 2024年

