# 平台品牌配置持久化开发设计

## 状态

- 设计状态：已批准
- 批准日期：2026-08-04
- 工程基线：现有 EasyAIoT `WEB` Vue3 前端、`DEVICE/iot-infra` Spring Boot + MyBatis-Plus 后端、PostgreSQL

## 目标与范围

平台名称、平台 Logo、大屏标题、登录页名称、登录页 Logo、登录表单标题及明暗登录背景使用全平台唯一配置。数据库是品牌配置的唯一可信来源，跨浏览器、跨账号读取同一份配置。

不包含实时推送；其他浏览器在刷新或重新打开后读取最新配置。悬浮球隐藏状态属于浏览器个人偏好，继续使用本地存储。

## 数据模型

新增 `infra_platform_branding` 单例表，固定主键 `id = 1`。同一行同时保存“当前配置”和“数据库初始配置”。当前字段由前端界面保存，`default_*` 初始字段只能通过数据库维护，前端接口不得修改。

当前配置字段：

- `platform_name`
- `platform_logo_file_id`
- `dashboard_title`
- `login_name`
- `login_logo_file_id`
- `login_form_title`
- `login_bg_light_file_id`
- `login_bg_dark_file_id`

数据库初始配置字段：

- `default_platform_name`
- `default_platform_logo_file_id`
- `default_dashboard_title`
- `default_login_name`
- `default_login_logo_file_id`
- `default_login_form_title`
- `default_login_bg_light_file_id`
- `default_login_bg_dark_file_id`
- 通用创建、更新、逻辑删除审计字段

读取优先级按字段执行：当前配置 → 数据库初始配置 → 改造前的前端内置默认配置。图片文件 ID 为 `NULL` 表示继续进入下一层兜底。数据库无表或无记录时使用改造前的完整默认配置；缺表时写入和重置必须失败并明确提示，不能虚假成功。

## 接口与权限

- 公共读取：未登录可调用，返回数据库值与可访问图片 URL；品牌图片统一返回同源且不含文件扩展名的
  `/admin-api/infra/platform-branding/image/view?fileId={fileId}`，不直接返回包含存储环境域名的
  `infra_file.url`，也不依赖 WEB Nginx 对 `.png`、`.jpg`、`.svg` 等静态资源正则的匹配顺序；
  图片读取响应使用 `image/*` 内联内容，不携带 `Content-Disposition: attachment` 下载响应头，确保缩略图、
  Logo、登录背景和浏览器标签图标均可直接加载；
  WEB Nginx 的 `/admin-api/` 与 `/dev-api/` 代理继续使用 `^~` 前缀匹配作为通用文件 API 的防护；
  无记录时返回空字段，由前端合并默认值。
- 管理员保存：整套当前配置一次事务新增或更新固定记录，不修改任何 `default_*` 字段。
- 管理员重置：按“数据库初始配置 → 改造前内置默认配置”解析初始值并写回当前配置字段，不修改任何 `default_*` 字段。
- 管理员图片上传：复用文件存储服务，返回 `fileId` 与 URL；配置表只保存 `fileId`。

读取接口允许匿名访问；保存、重置、上传要求管理员权限。写命令失败时不改变前端已生效配置。
`infra_platform_branding` 是全平台单例表，必须加入租户忽略表；公共读取 URL 同时加入租户请求过滤白名单，
避免多租户拦截器注入不存在的 `tenant_id` 条件，或要求未登录页面携带租户标识。

## 前端数据流

应用先使用当前内置默认值渲染，再异步读取服务端配置并合并非空字段。读取失败继续使用默认值。服务端读取成功后清除历史 `PLATFORM_BRANDING_CONFIG`，旧本地品牌配置不迁移、不参与全局配置。

保存成功后使用服务端返回结果更新当前页面；重置成功后同样使用服务端结果更新。浏览器标签图标、首页 Logo、登录页背景与标题全部消费同一响应式配置。
保存成功的动作反馈统一显示“操作成功”。

## 验收

1. 数据库无表、无记录或接口不可用时，前端显示当前默认品牌信息。
2. 无表时保存和重置失败并提示数据表未初始化。
3. A 浏览器保存后，B 浏览器刷新可读取相同配置。
4. 清理浏览器缓存、退出登录或更换账号不丢失配置。
5. 重置后数据库保留单例记录，当前配置恢复为数据库初始配置；未维护的初始字段显示改造前内置默认配置。
6. 普通用户仅可读取，管理员可上传、保存和重置。
7. 数据表只保存文件 ID，不保存 Base64 或环境相关完整 URL。
8. 文件存储配置使用容器或内网域名时，上传后的缩略图及刷新后的品牌图片仍可通过当前站点同源地址访问。
9. 通过数据库修改 `default_*` 字段后，当前页面配置不被立即覆盖；下一次执行重置后使用新的数据库初始配置。
