# EasyAIoT TWIN

通用工业园区数字孪生 MVP。当前版本使用 Three.js 程序化构建园区，包含三维漫游、设备状态、告警定位、实时模拟数据、视角切换和设备详情。

## 启动

```bash
cd TWIN
pnpm install
pnpm dev
```

默认访问 `http://localhost:5173`。

项目入口：`?project=industrial`、`?project=campus`、`?project=port`、`?project=energy`。

## 构建

```bash
pnpm build
pnpm preview
```

生产容器默认映射到 `http://localhost:8003`：

```bash
docker compose up -d --build
```

## 设备数据约定

每个三维设备使用稳定的 `id` 与平台设备 ID 对应。当前数据在 `src/main.ts` 中模拟，后续可将定时器替换为 MQTT over WebSocket 或后端 WebSocket 数据源，并保持 UI 与模型代码不变。

## 后续接入

1. Blender 导出园区 `GLB`，通过 `GLTFLoader` 替换程序化建筑。
2. 保留模型对象的 `device_id` 自定义属性。
3. 接入 EasyAIoT 设备 API、实时遥测和告警流。
4. 增加时序数据库、历史回放和能耗分析。

## Blender 资产

已提供 `blender/generate_park.py`。安装 Blender 后可在 `TWIN` 目录执行：

```bash
blender --background --python blender/generate_park.py
```

脚本会生成 `industrial_park.blend` 与 `industrial_park.glb`，并把 `device_id` 写入设备标记的 glTF extras。
