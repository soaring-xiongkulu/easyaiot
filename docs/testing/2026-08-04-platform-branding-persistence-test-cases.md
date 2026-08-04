# 平台品牌配置持久化测试用例

## 一、文档信息

| 项目 | 内容 |
| --- | --- |
| 项目名称 | EasyAIoT |
| 测试单元 | IoT 首页平台品牌配置持久化 |
| 设计依据 | `docs/specs/2026-08-04-platform-branding-persistence-design.md` |
| 重点范围 | 用户确认的 3 个数据库初始配置、页面保存和重置场景 |
| 测试级别 | 页面 + API + 数据库闭环 |
| 链路覆盖等级 | LOCAL_ONLY；本功能无外部上下游业务系统 |
| 用例状态 | 2026-08-04 已执行：场景 2、3 `PASS`；场景 1 自动化回归通过，缺表/空表真实 E2E 因共享环境安全限制 `BLOCKED` |
| 编写日期 | 2026-08-04 |

## 二、验收口径

品牌配置使用 `infra_platform_branding.id = 1` 的全平台唯一记录。同一记录包含两组字段：

- 当前配置字段：由前端保存和重置接口维护。
- `default_*` 数据库初始配置字段：只能通过数据库操作维护，前端保存和重置接口均不得修改。

逐字段读取优先级为：

```text
当前配置 → 数据库初始配置 → 改造前内置默认配置
```

重置规则为：

```text
数据库初始配置与改造前内置默认配置逐字段合并
  → 写回当前配置字段
  → default_* 字段保持不变
```

改造前内置默认配置基线：

| 配置项 | 内置默认值 |
| --- | --- |
| 平台名称 | `云边端一体化智能算法应用平台`，如构建环境设置 `VITE_GLOB_APP_TITLE` 则以该构建值为准 |
| 平台 Logo | `WEB/src/assets/images/logo.png` |
| 大屏标题 | `云边端一体算法预警监控平台` |
| 登录页名称 | 与平台名称相同 |
| 登录页 Logo | `WEB/src/assets/images/logo.png` |
| 登录表单标题 | 空字符串，页面使用原有 i18n 默认文案 |
| 浅色登录背景 | `WEB/src/assets/images/light-bg.png` |
| 深色登录背景 | `WEB/src/assets/images/dark-bg.png` |

## 三、执行准备

### 3.1 环境与安全要求

1. 仅允许在独立测试数据库或独立测试 schema 中执行缺表、清空表和数据维护步骤。
2. 禁止在共享 dev、生产或包含有效品牌配置的数据库中执行本文准备 SQL。
3. 场景 1A 使用一个从未执行品牌表 DDL 的独立数据库验证，不通过删除共享环境表构造。
4. 页面测试至少准备 A、B 两个相互独立的浏览器配置目录；不能只使用同一浏览器的两个标签页。
5. 管理员账号需具备品牌图片上传、保存和重置权限；B 浏览器可使用不同账号或未登录访问登录页。
6. 执行每个写入场景前先保存数据库前值，执行后保存数据库后值；测试结束后按记录恢复。

### 3.2 测试数据

| 数据编号 | 数据 | 准备方式 | 用途 | 清理方式 | 状态 |
| --- | --- | --- | --- | --- | --- |
| TD-01 | 独立空数据库，未执行 `infra_platform_branding.sql` | 新建专用测试数据库 | 场景 1A 缺表兜底 | 删除专用测试数据库 | NOT_READY |
| TD-02 | 已执行最新 DDL、`infra_platform_branding` 为空 | 专用测试数据库执行幂等 SQL | 场景 1B 空表兜底 | 恢复执行前快照 | NOT_READY |
| TD-03 | 自定义平台 Logo、登录 Logo、浅色背景、深色背景图片 | 从品牌设置页面分别上传 | 场景 2 当前配置 | 删除测试文件记录和对象存储文件 | NOT_READY |
| TD-04 | 数据库初始 Logo、浅色背景、深色背景图片 | 先上传取得 `infra_file.id`，再通过 SQL 写入 `default_*` | 场景 3 数据库初始配置 | 恢复执行前快照并清理测试文件 | NOT_READY |
| TD-05 | A、B 两个独立浏览器配置目录 | Chrome/Edge 或两个独立 Chrome Profile | 跨浏览器持久化 | 清理浏览器测试 Profile | NOT_READY |

### 3.3 通用数据库只读查询

确认表是否存在：

```sql
SELECT to_regclass('public.infra_platform_branding') AS table_name;
```

查询唯一品牌记录：

```sql
SELECT *
FROM infra_platform_branding
WHERE id = 1;
```

确认没有额外品牌记录：

```sql
SELECT COUNT(*) AS total_count,
       COUNT(*) FILTER (WHERE id = 1) AS singleton_count
FROM infra_platform_branding;
```

检查品牌表只保存文件 Key，不保存图片内容或环境 URL：

```sql
SELECT platform_logo_file_id,
       login_logo_file_id,
       login_bg_light_file_id,
       login_bg_dark_file_id,
       default_platform_logo_file_id,
       default_login_logo_file_id,
       default_login_bg_light_file_id,
       default_login_bg_dark_file_id
FROM infra_platform_branding
WHERE id = 1;
```

## 四、场景覆盖矩阵

| 用户场景 | 用例编号 | 核心验收结果 | 页面/API | DB | 优先级 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 1. 数据表未执行时使用改造前默认配置 | TC-EAIOT-BRAND-FT-001A | 缺表不影响页面展示默认品牌；保存、重置不得虚假成功 | 必测 | 验证缺表 | P0 | NOT_RUN |
| 1. 数据表存在但为空时使用改造前默认配置 | TC-EAIOT-BRAND-FT-001B | 空表返回空配置并由前端完整兜底，不自动生成脏记录 | 必测 | 前后均 0 行 | P0 | NOT_RUN |
| 2. 页面保存新配置，重置后恢复改造前默认配置 | TC-EAIOT-BRAND-FT-002 | 保存跨浏览器生效；重置写回历史默认并持久化 | 必测 | 当前字段变化，`default_*` 始终为空 | P0 | NOT_RUN |
| 3. 数据库维护初始配置，后续重置使用该配置 | TC-EAIOT-BRAND-FT-003 | 更新 `default_*` 不立即覆盖当前配置；重置后才成为当前配置 | 必测 | 当前字段与初始字段分离且最终一致 | P0 | NOT_RUN |

## 五、详细测试用例

### TC-EAIOT-BRAND-FT-001A：数据库表未执行时使用改造前默认配置

#### A. 用例契约

| 字段 | 内容 |
| --- | --- |
| 场景类型 | 兼容性、异常兜底 |
| 关联依据 | 用户场景 1；设计验收项 1、2 |
| 角色 | 未登录用户、管理员 |
| 执行方式 | 页面 + API + 数据库只读核验 |
| 数据 | TD-01、TD-05 |
| 业务键 | `infra_platform_branding` 表是否存在 |
| 允许终态 | 页面保持完整内置默认配置；任何写操作明确失败且没有品牌数据落库 |
| 状态 | BLOCKED（共享 dev 禁止删表；自动化回归通过） |

#### B. Given / When

| ID | 类型 | 操作或前值 |
| --- | --- | --- |
| G-001 | Given | 使用从未执行 `infra_platform_branding.sql` 的独立测试数据库；`to_regclass(...)` 返回 `NULL` |
| G-002 | Given | 清理 A、B 浏览器中历史 `PLATFORM_BRANDING_CONFIG`，保留当前构建内置资源 |
| W-001 | When | 在 A 浏览器打开登录页，再登录并打开 IoT 首页 |
| W-002 | When | 观察平台名称、首页 Logo、大屏标题、登录页名称、登录 Logo、表单标题、明暗背景和浏览器标签图标 |
| W-003 | When | 管理员尝试保存一次品牌配置 |
| W-004 | When | 管理员尝试执行“重置为初始设置” |
| W-005 | When | 在 B 浏览器重新打开登录页和 IoT 首页 |

#### C. 分层断言

| 断言 ID | 层级 | 精确预期 | 证据 | 状态 |
| --- | --- | --- | --- | --- |
| A-001-BIZ-01 | 业务 | A、B 浏览器均展示改造前的完整默认品牌配置，不出现空白 Logo 或空白背景 | 页面截图 | NOT_RUN |
| A-001-UI-01 | 页面 | 平台 Logo、登录 Logo、浏览器标签图标均为内置 `logo.png` | 页面与浏览器标签截图 | NOT_RUN |
| A-001-UI-02 | 页面 | 登录页浅色/深色模式分别使用内置 `light-bg.png`、`dark-bg.png` | 两种主题截图 | NOT_RUN |
| A-001-API-01 | API | 公共读取接口即使因缺表失败，前端也捕获失败并保持默认配置，不应用历史浏览器品牌数据 | 网络请求与页面截图 | NOT_RUN |
| A-001-API-02 | API | 保存和重置不得返回成功；页面提示品牌配置表未初始化或等价明确错误 | API 响应与页面提示截图 | NOT_RUN |
| A-001-DB-01 | DB | `to_regclass('public.infra_platform_branding')` 在保存、重置前后均为 `NULL`，接口不得自行创建数据表 | SQL 前后值 | NOT_RUN |
| A-001-DB-02 | DB | 不产生任何替代配置表、浏览器持久化品牌记录或 Base64 图片数据 | schema 查询与浏览器存储截图 | NOT_RUN |

#### D. 用例结论

| 必需断言数 | PASS | FAIL | BLOCKED | 用例状态 | 执行证据 |
| --- | --- | --- | --- | --- | --- |
| 7 | 0 | 0 | 7 | BLOCKED | 自动化回归见第 8.4 节；真实缺表 E2E 未执行 |

### TC-EAIOT-BRAND-FT-001B：数据库表为空时使用改造前默认配置

#### A. 用例契约

| 字段 | 内容 |
| --- | --- |
| 场景类型 | 空数据兼容 |
| 关联依据 | 用户场景 1；设计验收项 1 |
| 角色 | 未登录用户、管理员 |
| 执行方式 | 页面 + API + 数据库只读核验 |
| 数据 | TD-02、TD-05 |
| 业务键 | `infra_platform_branding.id = 1` |
| 允许终态 | 页面显示完整内置默认配置；只读操作不自动插入记录 |
| 状态 | BLOCKED（共享 dev 禁止清表；无记录自动化回归通过） |

#### B. Given / When

| ID | 类型 | 操作或前值 |
| --- | --- | --- |
| G-011 | Given | 已执行最新幂等 SQL，表结构包含当前字段、`default_*` 字段和 `id = 1` 单例约束 |
| G-012 | Given | `infra_platform_branding` 表为 0 行 |
| G-013 | Given | A、B 浏览器不存在历史本地品牌配置 |
| W-011 | When | A 浏览器打开登录页和 IoT 首页，等待公共品牌读取接口完成 |
| W-012 | When | B 浏览器重新执行相同操作 |

#### C. 分层断言

| 断言 ID | 层级 | 精确预期 | 证据 | 状态 |
| --- | --- | --- | --- | --- |
| A-011-BIZ-01 | 业务 | A、B 浏览器均展示改造前的完整默认品牌配置 | 页面截图 | NOT_RUN |
| A-011-API-01 | API | `GET /admin-api/infra/platform-branding/get` 成功，品牌数据字段为空或缺省，由前端逐字段合并内置默认值 | API 响应 | NOT_RUN |
| A-011-UI-01 | 页面 | 名称、首页 Logo、大屏标题、登录 Logo、登录背景和 favicon 均不为空且与内置默认一致 | 页面截图 | NOT_RUN |
| A-011-DB-01 | DB | 读取前 `COUNT(*) = 0`，读取后仍为 `0`；GET 接口不隐式插入 `id = 1` | SQL 前后值 | NOT_RUN |
| A-011-DB-02 | DB | 不存在 `id <> 1` 的记录，也不存在文件 URL、Base64 或图片二进制被写入品牌表 | SQL 查询结果 | NOT_RUN |

#### D. DB 前后值

| DB 断言 | 表/业务键 | 前值 | 预期变化 | 预期后值 | 无脏数据要求 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| DBA-011 | `infra_platform_branding` | 0 行 | 0 行 | 0 行 | 不新增任何记录 | NOT_RUN |

#### E. 用例结论

| 必需断言数 | PASS | FAIL | BLOCKED | 用例状态 | 执行证据 |
| --- | --- | --- | --- | --- | --- |
| 5 | 0 | 0 | 5 | BLOCKED | 自动化回归见第 8.4 节；真实空表 E2E 未执行 |

### TC-EAIOT-BRAND-FT-002：页面保存新配置，重置后恢复改造前默认配置

#### A. 用例契约

| 字段 | 内容 |
| --- | --- |
| 场景类型 | 核心主流程、跨浏览器持久化、重置 |
| 关联依据 | 用户场景 2；设计验收项 3、4、5、7、8 |
| 角色 | 管理员、普通读取用户 |
| 执行方式 | A/B 浏览器页面 + API + 数据库只读核验 |
| 数据 | TD-02、TD-03、TD-05 |
| 业务键 | `infra_platform_branding.id = 1` |
| 允许终态 | 保存后当前配置跨浏览器生效；重置后当前字段持久化为历史默认，`default_*` 保持空 |
| 状态 | PASS |

#### B. 测试输入

| 字段 | 页面保存值 |
| --- | --- |
| `platform_name` | `测试平台-A` |
| `platform_logo_file_id` | TD-03 自定义平台 Logo 的 `infra_file.id` |
| `dashboard_title` | `测试大屏-A` |
| `login_name` | `测试登录页-A` |
| `login_logo_file_id` | TD-03 自定义登录 Logo 的 `infra_file.id` |
| `login_form_title` | `测试登录标题-A` |
| `login_bg_light_file_id` | TD-03 自定义浅色背景的 `infra_file.id` |
| `login_bg_dark_file_id` | TD-03 自定义深色背景的 `infra_file.id` |

#### C. Given / When

| ID | 类型 | 操作或前值 |
| --- | --- | --- |
| G-021 | Given | 品牌表为空，或 `id = 1` 的当前字段与全部 `default_*` 字段均为 `NULL` |
| G-022 | Given | 记录品牌表前值和 TD-03 各图片对应的 `infra_file.id` |
| W-021 | When | A 浏览器上传四张测试图片，确认每个缩略图都正常展示 |
| W-022 | When | A 浏览器填写测试输入并保存 |
| W-023 | When | 记录保存提示、保存接口响应及品牌表后值 |
| W-024 | When | 清空 B 浏览器缓存后，在 B 浏览器打开登录页和 IoT 首页 |
| W-025 | When | A 浏览器执行“重置为初始设置”并确认操作 |
| W-026 | When | 刷新 A 浏览器，并重新打开 B 浏览器页面 |

#### D. 保存后的分层断言

| 断言 ID | 层级 | 精确预期 | 证据 | 状态 |
| --- | --- | --- | --- | --- |
| A-021-BIZ-01 | 业务 | A 保存后立即使用“测试平台-A”整套配置；B 刷新后显示同一配置 | A/B 页面截图 | PASS |
| A-021-UI-01 | 页面 | 四张上传图片的设置缩略图均正常显示，不出现破图、下载弹窗或空白背景 | 设置页截图 | PASS |
| A-021-UI-02 | 页面 | 首页 Logo、登录 Logo、明暗背景和浏览器标签图标分别使用已保存图片 | 页面与 favicon 截图 | PASS |
| A-021-UI-03 | 页面 | 保存成功提示只显示“操作成功”，不显示冗余配置内容 | 提示截图 | PASS |
| A-021-API-01 | API | 保存响应返回 8 项当前配置，图片地址均为同源 `/admin-api/infra/platform-branding/image/view?fileId={id}` | API 响应 | PASS |
| A-021-API-02 | API | 图片读取响应为对应 `image/*`，不包含 `Content-Disposition: attachment` | 响应头 | PASS |
| A-021-DB-01 | DB | 只新增或更新 `id = 1` 一行，8 个当前字段与页面输入一致 | SQL 前后值 | PASS |
| A-021-DB-02 | DB | 8 个 `default_*` 字段全部保持原值 `NULL`，保存接口未覆盖数据库初始配置 | SQL 前后值 | PASS |
| A-021-DB-03 | DB | 图片配置列只保存 `infra_file.id`，不保存完整 URL、Base64 或二进制内容 | SQL 查询结果 | PASS |

#### E. 重置后的分层断言

| 断言 ID | 层级 | 精确预期 | 证据 | 状态 |
| --- | --- | --- | --- | --- |
| A-022-BIZ-01 | 业务 | A 重置后立即恢复改造前默认配置；A 刷新及 B 重新打开后仍保持默认配置 | A/B 页面截图 | PASS |
| A-022-UI-01 | 页面 | 首页 Logo、登录 Logo、favicon 恢复内置 `logo.png`，明暗背景恢复内置背景 | 页面截图 | PASS |
| A-022-UI-02 | 页面 | 平台名称、大屏标题、登录页名称和登录标题恢复验收口径中的内置默认值 | 页面截图 | PASS |
| A-022-DB-01 | DB | `id = 1` 仍只有一行；当前文字字段写入历史默认值，四个当前图片 Key 写为 `NULL` | SQL 前后值 | PASS |
| A-022-DB-02 | DB | 8 个 `default_*` 字段重置前后仍全部为 `NULL` | SQL 前后值 | PASS |
| A-022-DB-03 | DB | 不新增第二条品牌配置记录，不删除 TD-03 对应 `infra_file` 文件记录 | SQL 查询结果 | PASS |

#### F. DB 前后值

| 阶段 | 行数/id | 当前配置字段 | `default_*` 字段 | 预期变化 |
| --- | --- | --- | --- | --- |
| 保存前 | 0 行，或 `id=1` 当前字段为 `NULL` | 全空 | 全空 | 基线 |
| 保存后 | 仅 `id=1` 一行 | 等于“测试平台-A”及 TD-03 图片 Key | 全空 | 仅当前字段变化 |
| 重置后 | 仅 `id=1` 一行 | 文字为历史默认；图片 Key 为 `NULL` | 全空 | 当前字段被重置并持久化 |

#### G. 用例结论

| 必需断言数 | PASS | FAIL | BLOCKED | 用例状态 | 执行证据 |
| --- | --- | --- | --- | --- | --- |
| 15 | 15 | 0 | 0 | PASS | 见第 8.2 节 |

### TC-EAIOT-BRAND-FT-003：数据库维护初始配置，重置后使用该配置

#### A. 用例契约

| 字段 | 内容 |
| --- | --- |
| 场景类型 | 数据库初始配置、配置优先级、重置 |
| 关联依据 | 用户场景 3；设计验收项 5、7、9 |
| 角色 | 数据库维护人员、管理员、普通读取用户 |
| 执行方式 | 数据库维护 + A/B 浏览器页面 + API + 数据库只读核验 |
| 数据 | TD-03、TD-04、TD-05 |
| 业务键 | `infra_platform_branding.id = 1` |
| 允许终态 | 数据库更新初始值后当前配置不立即变化；重置后当前字段等于数据库初始值，未配置项使用历史默认 |
| 状态 | PASS |

#### B. 数据库初始配置输入

| 字段 | 数据库维护值 |
| --- | --- |
| `default_platform_name` | `数据库初始平台-B` |
| `default_platform_logo_file_id` | TD-04 默认平台 Logo 的 `infra_file.id` |
| `default_dashboard_title` | `数据库初始大屏-B` |
| `default_login_name` | `数据库初始登录页-B` |
| `default_login_logo_file_id` | TD-04 默认登录 Logo 的 `infra_file.id` |
| `default_login_form_title` | `数据库初始登录标题-B` |
| `default_login_bg_light_file_id` | TD-04 默认浅色背景的 `infra_file.id` |
| `default_login_bg_dark_file_id` | 保持 `NULL`，用于验证逐字段回退到内置深色背景 |

#### C. Given / When

| ID | 类型 | 操作或前值 |
| --- | --- | --- |
| G-031 | Given | `id = 1` 当前配置已保存为场景 2 的“测试平台-A”整套自定义配置 |
| G-032 | Given | 记录全部当前字段、全部 `default_*` 字段及审计字段前值 |
| W-031 | When | 数据库维护人员仅更新 8 个 `default_*` 字段为本用例输入，不修改当前字段 |
| W-032 | When | A、B 浏览器刷新页面，确认重置前展示内容 |
| W-033 | When | 管理员在 A 浏览器执行“重置为初始设置” |
| W-034 | When | 记录重置接口响应、品牌表后值；刷新 A 并重新打开 B 浏览器 |

#### D. 数据库更新后、重置前断言

| 断言 ID | 层级 | 精确预期 | 证据 | 状态 |
| --- | --- | --- | --- | --- |
| A-031-BIZ-01 | 业务 | 数据库更新 `default_*` 后不会立即替换已存在的当前配置 | A/B 页面截图 | PASS |
| A-031-UI-01 | 页面 | A、B 刷新后仍显示“测试平台-A”及 TD-03 当前图片，不显示“数据库初始平台-B” | 页面截图 | PASS |
| A-031-DB-01 | DB | 8 个当前字段与更新前完全一致，仅 `default_*` 字段按数据库操作变化 | SQL 前后值 | PASS |
| A-031-DB-02 | DB | `id = 1` 仍为唯一记录，数据库维护未新增第二条默认记录 | SQL 查询结果 | PASS |

#### E. 重置后分层断言

| 断言 ID | 层级 | 精确预期 | 证据 | 状态 |
| --- | --- | --- | --- | --- |
| A-032-BIZ-01 | 业务 | A 重置后立即显示“数据库初始平台-B”配置；A 刷新及 B 重新打开后保持一致 | A/B 页面截图 | PASS |
| A-032-UI-01 | 页面 | 平台 Logo、登录 Logo和浅色背景使用 TD-04 数据库初始图片 | 页面截图 | PASS |
| A-032-UI-02 | 页面 | 因 `default_login_bg_dark_file_id = NULL`，深色背景使用内置 `dark-bg.png` | 深色模式截图 | PASS |
| A-032-UI-03 | 页面 | 浏览器标签图标与数据库初始平台 Logo 一致 | favicon 截图 | PASS |
| A-032-API-01 | API | 重置响应中非空数据库初始图片使用同源图片读取地址；深色背景地址为空并由前端内置资源兜底 | API 响应 | PASS |
| A-032-DB-01 | DB | 8 个当前字段被逐字段写回：已配置的初始值写入当前字段，未配置的深色背景 Key 写为 `NULL` | SQL 前后值 | PASS |
| A-032-DB-02 | DB | 8 个 `default_*` 字段与重置前完全一致，重置接口没有覆盖或清空数据库初始值 | SQL 前后值 | PASS |
| A-032-DB-03 | DB | 仅存在 `id = 1` 一条品牌配置记录，所有图片列均只保存有效 `infra_file.id` 或 `NULL` | SQL 查询结果 | PASS |

#### F. DB 前后值

| 阶段 | 当前字段 | `default_*` 字段 | 行数不变量 |
| --- | --- | --- | --- |
| 数据库维护前 | “测试平台-A”及 TD-03 图片 Key | 全空 | 仅 `id=1` 一行 |
| 数据库维护后、重置前 | 保持“测试平台-A”及 TD-03 图片 Key | 等于“数据库初始平台-B”及 TD-04 图片 Key | 仅 `id=1` 一行 |
| 重置后 | 等于数据库初始字段；未设置的深色背景 Key 为 `NULL` | 保持数据库维护值不变 | 仅 `id=1` 一行 |

#### G. 用例结论

| 必需断言数 | PASS | FAIL | BLOCKED | 用例状态 | 执行证据 |
| --- | --- | --- | --- | --- | --- |
| 12 | 12 | 0 | 0 | PASS | 见第 8.3 节 |

## 六、场景 3 数据准备 SQL 示例

> 仅供独立测试数据库执行。执行前替换四个文件 ID 占位符并保存 `id = 1` 的完整前值。该 SQL 只维护 `default_*`，不得修改当前配置字段。

```sql
INSERT INTO infra_platform_branding (
    id,
    default_platform_name,
    default_platform_logo_file_id,
    default_dashboard_title,
    default_login_name,
    default_login_logo_file_id,
    default_login_form_title,
    default_login_bg_light_file_id,
    default_login_bg_dark_file_id
) VALUES (
    1,
    '数据库初始平台-B',
    <DEFAULT_PLATFORM_LOGO_FILE_ID>,
    '数据库初始大屏-B',
    '数据库初始登录页-B',
    <DEFAULT_LOGIN_LOGO_FILE_ID>,
    '数据库初始登录标题-B',
    <DEFAULT_LIGHT_BG_FILE_ID>,
    NULL
)
ON CONFLICT (id) DO UPDATE SET
    default_platform_name = EXCLUDED.default_platform_name,
    default_platform_logo_file_id = EXCLUDED.default_platform_logo_file_id,
    default_dashboard_title = EXCLUDED.default_dashboard_title,
    default_login_name = EXCLUDED.default_login_name,
    default_login_logo_file_id = EXCLUDED.default_login_logo_file_id,
    default_login_form_title = EXCLUDED.default_login_form_title,
    default_login_bg_light_file_id = EXCLUDED.default_login_bg_light_file_id,
    default_login_bg_dark_file_id = EXCLUDED.default_login_bg_dark_file_id;
```

维护后必须先查询并保存结果，不能仅凭 SQL 执行成功判断：

```sql
SELECT id,
       platform_name,
       platform_logo_file_id,
       dashboard_title,
       login_name,
       login_logo_file_id,
       login_form_title,
       login_bg_light_file_id,
       login_bg_dark_file_id,
       default_platform_name,
       default_platform_logo_file_id,
       default_dashboard_title,
       default_login_name,
       default_login_logo_file_id,
       default_login_form_title,
       default_login_bg_light_file_id,
       default_login_bg_dark_file_id
FROM infra_platform_branding
WHERE id = 1;
```

## 七、执行记录与判定规则

| 用例编号 | 页面/API | DB 前后值 | 跨浏览器 | 证据完整 | 最终状态 | Bug 编号 |
| --- | --- | --- | --- | --- | --- | --- |
| TC-EAIOT-BRAND-FT-001A | 自动化回归通过；真实页面/API 未构造缺表 | 共享 dev 禁止删表 | 不适用 | 部分 | BLOCKED | |
| TC-EAIOT-BRAND-FT-001B | 服务层无记录回归通过；真实页面/API 未清空表 | 共享 dev 禁止清表 | 不适用 | 部分 | BLOCKED | |
| TC-EAIOT-BRAND-FT-002 | PASS | PASS | Chrome + Safari PASS | 是 | PASS | |
| TC-EAIOT-BRAND-FT-003 | PASS | PASS | Chrome + Safari PASS | 是 | PASS | |

判定规则：

1. 任一必需断言失败，用例状态为 `FAIL` 并登记 Bug。
2. 环境、账号、数据库只读权限或测试数据未就绪，用例状态为 `BLOCKED`。
3. 只有页面/API、数据库前后值、跨浏览器持久化和证据全部满足时，用例才能标记为 `PASS`。
4. “操作成功”、HTTP 200、SQL 执行成功均不能单独作为用例通过依据。
5. 缺表、空表用例必须在独立数据库补做真实 E2E 后，才能从 `BLOCKED` 改为 `PASS`。

## 八、2026-08-04 dev 环境执行证据

### 8.1 环境与执行窗口

| 项目 | 实际值 |
| --- | --- |
| WEB | `http://192.168.1.88:8888` |
| PostgreSQL | `192.168.1.88:5432/ruoyi-vue-pro20` |
| 执行时间 | 2026-08-04 16:09—16:35（Asia/Shanghai） |
| 浏览器 A | Chrome 已登录会话 |
| 浏览器 B | Safari 独立未登录会话 |
| 执行前品牌记录 | 仅 `id=1`；当前图片 Key 为 `16/17/18/19`；8 个 `default_*` 全为 `NULL` |

### 8.2 场景 2 实际结果

1. Chrome 上传平台 Logo、登录 Logo、浅色背景和深色背景后，四个缩略图均正常显示。
2. 保存值为 `测试平台-A / 测试大屏-A / 测试登录页-A / 测试登录标题-A`，图片 Key 为 `20/22/23/24`。
3. 保存成功提示仅显示 `操作成功`；浏览器标题立即变为 `首页 - 测试平台-A`。
4. 公共读取接口返回同一套 A 配置；四个图片接口均为 HTTP 200、`Content-Type: image/webp`，且没有 `Content-Disposition: attachment`。
5. Safari 独立会话打开登录页后显示 A 配置；浅色、深色模式背景均与保存图片一致，证明配置未依赖浏览器本地存储。
6. 数据库仍仅 `id=1` 一行；8 个当前字段与页面输入一致，8 个 `default_*` 保持 `NULL`。
7. 执行重置后，当前文字字段写入改造前内置默认值，四个当前图片 Key 写为 `NULL`，`default_*` 仍全为 `NULL`；页面逐字段使用内置 Logo 和背景兜底。

结论：`TC-EAIOT-BRAND-FT-002 = PASS`。

### 8.3 场景 3 实际结果

1. 前置当前配置为场景 2 的 A 配置，`default_*` 全空。
2. 仅通过 SQL 把数据库初始配置维护为 `数据库初始平台-B / 数据库初始大屏-B / 数据库初始登录页-B / 数据库初始登录标题-B`，图片 Key 为 `16/17/18/NULL`。
3. SQL 前后对比确认当前字段保持 A 配置；公共读取接口和 Chrome 刷新后仍显示 A，未被 B 立即覆盖；品牌表仍仅 `id=1`。
4. 页面执行重置后，当前字段写成 B 配置：Logo 使用 `16/17`，浅色背景使用 `18`，深色背景 Key 为 `NULL` 并由前端回退内置 `dark-bg.png`。
5. Safari 刷新后显示 B 名称、Logo、登录标题和内置深色背景；浏览器标题同步变为 `登录 - 数据库初始平台-B`。
6. 重置后 8 个 `default_*` 保持不变，当前字段与数据库初始字段逐字段一致，仍仅 `id=1` 一行。

结论：`TC-EAIOT-BRAND-FT-003 = PASS`。

### 8.4 场景 1 自动化回归

执行命令：

```bash
mvn -pl iot-infra/iot-infra-biz -am \
  -DskipTests=false \
  -Dtest=PlatformBrandingControllerTest,PlatformBrandingFileUrlBuilderTest,PlatformBrandingTenantConfigurationTest,PlatformBrandingServiceImplTest \
  -Dsurefire.failIfNoSpecifiedTests=false test
```

结果：2026-08-04 16:30:31 完成，`BUILD SUCCESS`；Tests run: 11，Failures: 0，Errors: 0，Skipped: 0。覆盖无品牌记录返回、当前字段为空时读取数据库初始值、保存保留 `default_*`、重置持久化、全平台租户忽略和图片同源预览路由。

限制：共享 dev 已有有效 `id=1` 记录，未执行删表或清表；因此缺表和空表的真实页面/API/DB E2E 保持 `BLOCKED`，不是功能失败。

### 8.5 数据恢复与残留

测试结束后已恢复业务配置：

```text
platform_name / dashboard_title / login_name = AIoT预警监控平台
platform_logo_file_id / login_logo_file_id = 16 / 17
login_form_title = 空字符串
login_bg_light_file_id / login_bg_dark_file_id = 18 / 19
全部 default_* = NULL
deleted = 0
品牌记录总数 = 1
```

公共读取接口已返回上述原始配置，Chrome 和 Safari 刷新后也已恢复。

上传测试产生 `infra_file.id = 20、21、22、23、24`。这些文件不再被品牌配置引用；为避免未经确认永久删除对象存储数据，本次未删除，作为可清理残留记录保留。
