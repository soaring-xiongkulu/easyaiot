# 容器

终端 内置容器管理界面，支持 **Kubernetes** 集群管理，以及 **Docker / Podman / nerdctl / WSLC** 容器运行时，可管理本机或 SSH 远程主机上的集群资源与容器镜像。

## Kubernetes

![Kubernetes](/imgs/kubernetes_light.webp)

### 连接参数

| 参数 | 说明 |
|------|------|
| 配置来源 | **本地文件**（指定 kubeconfig 路径，带文件选择按钮）或 **kubeconfig 文本**（默认收起，点击「显示配置」展开后粘贴内容，可「从文件导入」） |
| Context | 从 kubeconfig 中选择上下文，可点击「重新加载」刷新列表 |
| 命名空间 | 默认查看的命名空间，可勾选「全部命名空间」浏览整个集群 |
| 跳过 TLS 验证 | 跳过 API Server 证书校验（不安全，仅用于自签名测试环境） |
| SSH 隧道 | 可选，通过 SSH 跳板机访问内网集群 API |

填写后可点击「测试连接」验证 kubeconfig 与网络是否可达。

### 资源浏览

左侧树形面板按类别分组展示集群资源，实时监听（watch）变更并自动刷新：

| 分组 | 资源 |
|------|------|
| Workloads | Pods、Deployments、StatefulSets、DaemonSets、ReplicaSets、Jobs、CronJobs、HPAs |
| Network | Services、Ingresses、Endpoints、NetworkPolicies |
| Config | ConfigMaps、Secrets、ResourceQuotas、LimitRanges |
| Storage | PVCs、PVs、StorageClasses |
| RBAC | ServiceAccounts、Roles、RoleBindings、ClusterRoles、ClusterRoleBindings |
| Cluster | Nodes、Namespaces、Events、CRDs |

- **顶部筛选** — 按名称、状态、命名空间等列实时过滤
- **健康高亮** — 未就绪的 Pod、副本不足的工作负载、NotReady 节点整行着色提示
- **实时指标** — Pods 和 Nodes 列表显示 CPU / 内存用量及占 requests/limits 的百分比（需集群安装 metrics-server）

### 资源操作

选中资源后，右键或行内操作按钮提供以下功能（按资源类型不同）：

- **详情** — 侧边抽屉展示元数据、Spec、Status 等完整字段
- **编辑** — 直接编辑资源 YAML 并应用
- **新建** — 通过内置 YAML 模板创建资源
- **伸缩** — 修改 Deployment / StatefulSet / ReplicaSet 副本数
- **重启** — 滚动重启工作负载
- **查看 Pods** — 跳转到该工作负载/节点关联的 Pod 列表
- **Cordon / Drain** — 标记节点不可调度或驱逐其上 Pod
- **删除** — 确认后删除，支持强制删除（跳过优雅终止）

### Pod 日志与终端

- **日志** — 实时跟随 Pod 日志，支持暂停/恢复、时间戳、上一个容器（previous）、自动滚动、换行、清屏
- **终端** — 直接 exec 进入 Pod 容器，获得交互式 Shell

## 容器引擎

![容器管理](/imgs/container_light.webp)

支持 **Docker**、**Podman**、**nerdctl(containerd)** 和 **WSLC**（Windows WSL2 Container，仅 Windows）四种运行时，新建连接时选择子类型。

### 连接参数

| 参数 | 说明 |
|------|------|
| 传输方式 | **远程主机 (SSH)**（默认）引用已有 SSH 连接，继承其凭证与跳板机配置管理远程主机上的容器；**本机** 使用本机安装的容器运行时 |
| SSH 连接 | 传输方式为远程主机时，选择一个已保存的 SSH 连接作为通道 |

> nerdctl 支持在顶部切换 containerd 的 namespace。WSLC 运行时不提供「重启」「重命名」操作。

### 容器管理

顶部标签切换「容器」与「镜像」两个视图。

**容器列表** 显示名称、镜像、状态、端口映射、创建时间，提供以下操作：

- **生命周期** — 启动、停止、重启、暂停、恢复
- **Exec** — 进入容器交互式终端
- **日志** — 查看容器日志输出
- **重命名** — 修改容器名称
- **删除** — 确认后移除容器
- **详情** — 查看概要、命令、网络、挂载、环境变量、状态等信息
- **新建容器** — 指定镜像、名称、端口映射、数据卷、环境变量、重启策略、启动命令后创建

### 镜像管理

**镜像列表** 显示仓库、标签、ID、大小，支持：

- **拉取** — 输入镜像名（如 `nginx:latest`）从仓库拉取
- **删除** — 确认后移除镜像

::: tip 相关内容
- [远程终端](/zh/connections/remote-terminal) —— SSH 连接与跳板机配置
- [支持协议](/zh/protocols) —— 完整协议与端口列表
:::
