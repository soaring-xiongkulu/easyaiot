# App 控制面板模板（产品级动态控制页）设计

## 目标

在云端为每个产品设计 App 控制页面模板并绑定到产品，发布后自动下发；App 打开设备控制台时按设备所属产品的已发布模板动态渲染控制页。不同产品 → 不同控制页，新增或调整页面无需发版。

## 总体链路

1. WEB 管理端「App 面板模板」创建/设计模板（组件库 + 手机实时预览 + JSON 源码双模式），保存为草稿。
2. 发布模板：状态置为 `PUBLISHED`、版本号自增，同一产品的其他已发布模板自动停用（一个产品仅一个生效模板）。
3. App 设备控制台（工作台菜单「设备控制台」或设备列表页右上角「控制台」）打开某 IoT 设备时，按 `productIdentification` 调用下发接口拉取模板，`PanelRenderer` 按 JSON 渲染组件。
4. 数据读写：属性值经设备影子轮询展示；开关/滑条/步进器通过命令下发写入，按钮直接下发服务命令。

## 后端（DEVICE/iot-device-biz）

- 新表 `app_panel_template`：DDL 见 `iot-device-biz/src/main/resources/sql/app_panel_template.sql`，并已同步至 `.scripts/postgresql/iot-device10.sql`。
  - 关键列：`template_code`（唯一）、`template_name`、`product_identification`（绑定产品）、`status`（DRAFT/PUBLISHED/DISABLED）、`version`、`panel_schema`（模板 JSON）、`tenant_id`、`deleted`。
- DO/Mapper/Service/Controller 沿用 `app` 模块现代风格：
  - `dal/dataobject/AppPanelTemplateDO.java`
  - `dal/pgsql/apppanel/AppPanelTemplateMapper.java` + `mapper/apppanel/AppPanelTemplateMapper.xml`
  - `service/apppanel/AppPanelTemplateService(Impl).java`
  - `controller/apppanel/AppPanelTemplateController.java`
- 接口（经网关 `/admin-api/appPanelTemplate/**`，路由已在 `iot-gateway/src/main/resources/application.yaml` 增加）：
  - 管理端：`create` / `update` / `delete` / `get` / `page` / `list` / `publish` / `unpublish`
  - APP 下发入口：`GET /admin-api/appPanelTemplate/get-by-product?productIdentification=...`，返回当前生效模板；未配置返回 null。
- 业务约束：模板编码唯一；同一产品同时只允许一个非停用模板绑定；发布时校验 `panel_schema` 为合法 JSON。
- 复用的既有能力：
  - 影子读：`GET /admin-api/shadow/{deviceId}`（取 `reported` 属性值与 `connectStatus`）
  - 命令下发：`POST /admin-api/deviceCommand/issueCommands`（`msgType=SERVICE_INVOKE`，topic 规则 `/iot/{product}/{device}/service/downstream/invoke/{serviceCode}`）
  - 视频联动：`GET /admin-api/device/cameraLinks?iotDeviceId=` 取关联摄像头后走既有拉流逻辑

## 模板 JSON 结构

```json
{
  "version": 1,
  "pages": [
    {
      "name": "控制台",
      "layout": "grid",
      "widgets": [
        { "id": "switch_0", "type": "switch", "title": "电源开关", "span": "half",
          "propertyCode": "power", "config": { "options": [ {"label":"开启","value":"1"}, {"label":"关闭","value":"0"} ] } },
        { "id": "slider_0", "type": "slider", "title": "亮度", "span": "half",
          "propertyCode": "brightness", "config": { "min": 0, "max": 100, "step": 1, "unit": "%" } },
        { "id": "status_0", "type": "status", "title": "工作模式",
          "propertyCode": "mode", "config": { "options": [ {"label":"制冷","value":"COOL","color":"#1890ff"} ] } },
        { "id": "text_0",   "type": "text",   "title": "实时功率", "propertyCode": "power_consumption", "config": { "unit": "W" } },
        { "id": "button_0", "type": "button", "title": "重启设备", "serviceId": "reboot", "config": { "confirm": true } },
        { "id": "video_0",  "type": "video",  "title": "实时画面" }
      ]
    }
  ]
}
```

组件类型 v1：`switch` 开关 / `slider` 滑条 / `number` 步进器 / `status` 状态标签 / `text` 数值文本 / `button` 命令按钮 / `video` 实时画面。可写属性组件可选配置 `serviceId`，缺省走平台约定的 `setProperty` 属性写服务，参数形如 `{ "<propertyCode>": <value> }`。

## WEB 管理端

- API：`src/api/device/appPanelTemplate.ts`
- 页面：`src/views/apppanel/index.vue` + `components/TemplateEditor.vue`（左：组件库/组件清单，中：手机预览或 JSON 源码，右：选中组件的属性配置）
- 菜单为数据库驱动，执行 `iot-system-biz/src/main/resources/sql/app_panel_template_menu.sql` 插入菜单（或在「系统管理→菜单管理」等价添加，组件路径 `apppanel/index`），并按需为角色分配。

## APP 端

- API 与类型：`src/api/device/panel.ts`
- 动态渲染器：`src/components/panel/PanelRenderer.vue`（卡片栅格布局、影子 10s 轮询、乐观更新失败回滚）+ `src/components/panel/widgets/*`
- 页面：`pages/device/console/index.vue`（IoT 设备列表）→ `pages/device/control/index.vue`（按产品模板渲染的控制台）
- 入口：工作台「设备控制台」菜单 + 设备列表页导航栏「控制台」
- 未配置模板的产品显示引导空态（提示到 WEB 端为产品绑定并发布模板）

## 部署步骤

1. 执行 `DEVICE/iot-device/iot-device-biz/src/main/resources/sql/app_panel_template.sql` 建表（新库可直接使用 `.scripts/postgresql/iot-device10.sql` 全量脚本）。
2. 重启 device-server 与网关（网关路由已含 `/admin-api/appPanelTemplate/**`）。
3. 执行系统库菜单脚本并给角色授权后重启/重新登录 WEB 管理端。
4. WEB「App 面板模板」新建模板 → 绑定产品 → 设计组件 → 保存草稿 → 发布。
5. App 端进入设备控制台验证面板生效；修改模板后再次发布即可热更新（版本号自增）。
