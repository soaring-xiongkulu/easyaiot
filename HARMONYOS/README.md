# HARMONYOS 模块 —— EasyAIoT 移动端 HarmonyOS 壳工程

把 [APP](../APP)（uni-app / unibest）前端工程编译出的 **H5 资源**，装进一个内置 ArkWeb（系统 WebView）的 DevEco Studio 工程，用 hvigor 出可安装的 HAP。

本模块不包含业务代码：界面全部来自 APP 模块的 H5 构建产物，壳工程只负责加载、图标、签名与打包。

```
APP (uni-app 工程)
   │  pnpm build:h5[:prod|:test]          ← 第 1 步：编译前端 H5
   ▼
APP/dist/build/h5 （index.html + assets/static）
   │  同步到壳工程 rawfile/www             ← 第 2 步：脚本自动完成
   ▼
HARMONYOS/entry/src/main/resources/rawfile/www
   │  ./hvigorw assembleHap               ← 第 3 步：出包
   ▼
entry/build/**/outputs/**/*.hap
   →  easyaiot-<版本>-<模式>-harmonyos.hap
```

> **与 ANDROID 模块的技术差异**：ANDROID 使用 DCloud uni-app 离线运行时（依赖其受控下载的 AAR 二进制）；HarmonyOS 侧壳工程直接用系统 ArkWeb 加载纯网页产物。前端全项目仅 1 处 `plus.*` API 且被 `#ifdef APP` 条件编译隔离，H5 形态功能不受影响；后端网关已全量放开 CORS，登录/接口调用照常工作。
>
> **为什么不直接 `file://` 加载**：ArkWeb 基于 Chromium，会拦截 file 源的 ES Module 与部分存储 API。壳页面把资源统一映射为虚拟主机 `http://appassets.local/`，由 `onInterceptRequest` 从 rawfile 取字节回填（见 `entry/src/main/ets/pages/Index.ets`），页面以"正常网页"身份运行。

日常打包只需一个命令：

```bash
./make-hap.sh            # 生产环境
./make-hap.sh test       # 测试环境
./make-hap.sh dev        # 开发环境
```

---

## 一、关键信息速查

| 项 | 值 |
|---|---|
| Bundle 名 | `com.basiclab.iot.app`（与 ANDROID 包名 / iOS Bundle ID 一致） |
| 应用名 | EasyAIoT（`AppScope/resources/base/element/string.json`） |
| 版本号 | `versionCode 100` / `versionName "1.0.0"`（`AppScope/app.json5`） |
| 目标平台 | phone / tablet；compatibleSdkVersion `5.0.5(17)` |
| 构建工具 | hvigor（modelVersion 5.0.0，DevEco Studio 自带或 npm `@ohos/hvigor`） |

## 二、目录结构

```
HARMONYOS/
├── make-hap.sh                    # 一键打包脚本（校验版本→构建前端→同步资源→hvigor）
├── hvigorw / hvigorw.bat          # hvigor 启动器（优先用 DevEco 自带工具链）
├── hvigor/hvigor-config.json5     # hvigor 版本锚定
├── build-profile.json5            # 签名配置/产品默认产物/模块列表
├── oh-package.json5
├── AppScope/
│   ├── app.json5                  # bundleName/versionName/versionCode（版本号在这里维护）
│   └── resources/base/
│       ├── media/                 # 分层图标（layered_background/foreground）
│       └── element/string.json    # app_name
└── entry/
    ├── build-profile.json5 / oh-package.json5 / obfuscation-rules.txt
    └── src/main/
        ├── module.json5           # UIAbility + INTERNET 权限 + 页面注册
        ├── resources/base/
        │   ├── media/start_icon.png      # 启动窗口图标
        │   ├── profile/main_pages.json
        │   └── element/{string,color}.json
        ├── ets/
        │   ├── entryability/EntryAbility.ets
        │   └── pages/Index.ets    # ArkWeb 壳页面（onInterceptRequest 服务本地资源）
        └── resources/rawfile/www/ # APP 构建产物（脚本生成，不入库）
```

## 三、环境准备（新电脑）

### 3.1 Node + pnpm（构建前端用）

- Node ≥ 20，pnpm ≥ 9（APP 工程有 `only-allow pnpm` 钩子）。
- 安装依赖：`cd APP && pnpm install`

### 3.2 DevEco Studio / 命令行工具链

推荐安装 [DevEco Studio](https://developer.huawei.com/consumer/cn/deveco-studio/)（macOS/Windows）。命令行构建所需的一切都在其中：

- **hvigor**：`<DevEco 安装目录>/tools/hvigor`。仓库里的 `hvigorw` 启动器会自动探测该路径；也可设环境变量 `HVIGOR_HOME` 显式指定（例如指向团队内共享的 DevEco 安装）。注意 hvigor 随 DevEco Studio 分发、不在公开 npm 源，没有"装个 npm 包就能构建"的路径。
- **SDK**：DevEco 首次启动时按提示下载 HarmonyOS SDK；命令行构建时通过环境变量指定：
  ```bash
  export DEVECO_SDK_HOME=$HOME/Library/OpenHarmony/Sdk   # macOS 默认位置示例
  ```

无 SDK 时仍可执行 `./make-hap.sh --skip-native` 完成前三步（前端构建与资源同步），把源码交给任何装有 DevEco Studio 的机器继续出包。

首次用 DevEco Studio 打开本项目若提示升级 hvigor / SDK 版本，点击 Sync 同意即可（`build-profile.json5` 的 `compatibleSdkVersion` 与 `hvigor-config.json5` 的 `modelVersion` 是配套的）。

## 四、日常打包

### 方式一：一键脚本（推荐）

```bash
cd HARMONYOS
./make-hap.sh [--skip-native] [prod|test|dev]
```

脚本依次完成：版本一致性校验 → 前端按指定模式构建 H5 → 清空并同步 rawfile/www 资源（含绝对路径归一化安全网）→ `hvigor assembleHap` → 复制为带环境后缀的成品。

### 方式二：分步执行（理解原理用）

```bash
# 1. 构建前端（产出 APP/dist/build/h5；相对路径是本模块的硬性要求）
cd ../APP && VITE_APP_PUBLIC_BASE=./ pnpm build:h5:prod

# 2. 同步 www 资源（先清空再拷贝）
rm -rf  entry/src/main/resources/rawfile/www
mkdir -p entry/src/main/resources/rawfile/www
cp -a ../APP/dist/build/h5/. entry/src/main/resources/rawfile/www/

# 3. 打包
./hvigorw assembleHap --mode module -p product=default -p buildMode=release
# 产物: entry/build/default/outputs/default/*.hap
```

### 多环境与后端地址

| 命令 | mode | env 文件 | 说明 |
|---|---|---|---|
| `make-hap.sh` / `pnpm build:h5:prod` | production | `APP/env/.env.production` | 默认走 `.env` 的正式后端地址 |
| `make-hap.sh test` / `pnpm build:h5:test` | test | `APP/env/.env.test` | 测试后端地址 |
| `make-hap.sh dev` / `pnpm build:h5` | development | `APP/env/.env.development` | 开发联调 |

后端地址在各 env 文件的 `VITE_SERVER_BASEURL` 配置，**编译期写死进 JS 包**；部署时改成实际网关地址即可。module.json5 已申请 `ohos.permission.INTERNET`，允许 http 后端调试。

## 五、签名与真机安装

HarmonyOS 应用上架/真机运行都需要华为签发的签名材料：

1. **调试签名（最常用）**：DevEco Studio 中 `File → Project Structure → Signing Configs` 勾选 *Automatically generate signature*，登录华为账号后会自动在 `build-profile.json5` 补全调试证书与 Profile；随后可直接 Run 到已授权的真机/模拟器。
2. **发行签名**：在 AppGallery Connect 创建应用（包名 `com.basiclab.iot.app`）→ 申请发布证书与 Profile → 把材料登记进 `signingConfigs` 后打 release 包。
3. 命令行打的包若未配置签名，产物为 `-unsigned.hap`，仅供结构验证，不能直装真机。

## 六、版本号管理

发新版本只改两处（保持一致）：

1. `HARMONYOS/AppScope/app.json5`
   ```json5
   "versionCode": 101,      // 整数递增
   "versionName": "1.0.1",  // 显示版本
   ```
2. `APP/manifest.config.ts`
   ```ts
   'versionName': '1.0.1',
   'versionCode': '101',
   ```

`make-hap` 脚本会在打包前对这两处做一致性校验，不一致直接终止，避免打出资源错乱的包。同时建议同步更新 `IOS/EasyAIoT.xcodeproj/project.pbxproj`，让三端版本齐平。

## 七、图标

- 分层图标：`AppScope/resources/base/media/layered_background.png`（当前为品牌深蓝纯色底）+ `layered_foreground.png`（居中缩放的应用图标），由 `layered_image.json` 组合声明——设计侧可分别替换这两张图。
- 启动窗口图标：`entry/src/main/resources/base/media/start_icon.png`。
- 图片唯一来源同 iOS：`APP/src/static/app/icons/1024x1024.png`。

## 八、常见问题排查

| # | 报错 / 现象 | 原因 | 解决 |
|---|---|---|---|
| 1 | `hvigorw: command not found` 或脚本报未找到 hvigor | 未装 DevEco Studio 且 PATH 里没有 hvigor | 见第三节 3.2，设置 `HVIGOR_HOME` 或安装 DevEco Studio |
| 2 | hvigor 报 SDK not found | 未下载 HarmonyOS SDK 或未设环境变量 | DevEco 内下载 SDK；导出 `DEVECO_SDK_HOME` 后重试 |
| 3 | 启动白屏 | `rawfile/www/` 为空或同步了旧缓存 | 用 `make-hap.sh` 全流程，不要手动只跑 hvigorw |
| 4 | 页面能开但接口全部失败 | 后端地址是 localhost 或网关未启动 | 改 `VITE_SERVER_BASEURL` 为真实网关后重新出包 |
| 5 | 接口跨域报错 | 走了未经网关的直连端口 | 项目 CORS 由 `DEVICE/iot-gateway` 的 CorsFilter 统一放行，请确认请求经网关（48080/admin-api） |
| 6 | hap 无法安装到真机 | 未签名（unsigned 包） | 按第五节配置自动调试签名 |
| 7 | 首次打开提示 modelVersion 不匹配 | 本地 hvigor 版本与 `hvigor-config.json5` 不同代 | 按 IDE 提示一键升级同步 |
| 8 | `preinstall: npx only-allow pnpm` 报错 | APP 工程只允许 pnpm | 不要用 npm/yarn 装 APP 依赖 |
| 9 | 改了前端代码 App 里没生效 | 只跑了 hvigorw，没有重新构建/同步 www | 用 `make-hap.sh` 全流程 |

## 九、命令速查

```bash
# 一键打包
cd HARMONYOS && ./make-hap.sh
cd HARMONYOS && ./make-hap.sh --skip-native   # 只做前端构建+同步（CI/无 DevEco 环境）

# 手动 hvigor
cd HARMONYOS && ./hvigorw assembleHap --mode module -p product=default -p buildMode=release

# 清理构建
cd HARMONYOS && ./hvigorw clean

# 安装到已连接设备（需 hdc，随 DevEco 分发）
hdc install -r entry/build/default/outputs/default/*.hap
hdc shell aa start -a EntryAbility -b com.basiclab.iot.app
```

---

## 统一管理（推荐）

统一脚本目录提供三端统一管理入口 `.scripts/docker/mobile.sh`（等价入口：`./install_linux.sh mobile <子命令>`），日常操作不必分别进入各模块：

```bash
.scripts/docker/mobile.sh status                # 三端版本一致性 / 工具链就绪度 / 已有成品 概览
.scripts/docker/mobile.sh build android prod    # 单端打包（android|ios|harmonyos|all）
.scripts/docker/mobile.sh bump 1.0.1 101        # 发版：APP manifest 与三端壳共 5 处版本号一次改齐
.scripts/docker/mobile.sh artifacts             # 列出所有已产出安装包
.scripts/docker/mobile.sh clean android         # 清理指定端的打包成品
```

完整说明见 [MOBILE.md](../MOBILE.md)；三端安装包统一命名为全小写 `easyaiot-<版本>-<环境>-<平台>.<格式>`。
