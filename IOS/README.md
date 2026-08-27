# IOS 模块 —— EasyAIoT 移动端 iOS 壳工程

把 [APP](../APP)（uni-app / unibest）前端工程编译出的 **H5 资源**，装进一个内置系统 WebView 的 Xcode 壳工程，用 xcodebuild 出可安装的 .app / .ipa。

本模块不包含业务代码：界面全部来自 APP 模块的 H5 构建产物，壳工程只负责加载、图标、签名与打包。

```
APP (uni-app 工程)
   │  pnpm build:h5[:prod|:test]          ← 第 1 步：编译前端 H5
   ▼
APP/dist/build/h5 （index.html + assets/static）
   │  同步到壳工程 www/                     ← 第 2 步：脚本自动完成
   ▼
IOS/EasyAIoT/www
   │  xcodebuild                           ← 第 3 步：出包
   ▼
EasyAIoT.app（模拟器，免签名）/ EasyAIoT.ipa（真机分发）
```

> **与 ANDROID 模块的技术差异**：ANDROID 使用 DCloud uni-app 离线运行时（依赖其受控下载的 AAR 二进制）；iOS 侧壳工程直接用系统 WKWebView 加载纯网页产物。前端全项目仅 1 处 `plus.*` API 且被 `#ifdef APP` 条件编译隔离，H5 形态功能不受影响；后端网关已全量放开 CORS，登录/接口调用照常工作。

日常打包只需一个命令：

```bash
./make-ipa.sh              # 模拟器 .app（免签名，默认）
./make-ipa.sh --device     # 真机/分发 ipa（需签名配置）
./make-ipa.sh test         # 测试环境
./make-ipa.sh dev          # 开发环境
```

---

## 一、关键信息速查

| 项 | 值 |
|---|---|
| Bundle ID | `com.basiclab.iot.app`（与 ANDROID 包名一致） |
| 应用名 | EasyAIoT（`EasyAIoT/Info.plist`） |
| 版本号 | `MARKETING_VERSION 1.0.0` / `CURRENT_PROJECT_VERSION 100`（`EasyAIoT.xcodeproj/project.pbxproj`） |
| 部署目标 | iOS 15.0+（iPhone / iPad） |
| 工程格式 | objectVersion 77（需 **Xcode 16+**） |
| 签名方式 | 自动签名；真机出包前需把 `ExportOptions.plist` 的 `teamID` 从占位值改掉 |

## 二、目录结构

```
IOS/
├── make-ipa.sh                    # 一键打包脚本（校验版本→构建前端→同步资源→xcodebuild）
├── ExportOptions.plist            # 导出配置（method/teamID，--device 时使用）
├── EasyAIoT.xcodeproj/
│   └── project.pbxproj            # 版本号在此维护（synchronized group 极简工程）
└── EasyAIoT/
    ├── EasyAIoTApp.swift          # SwiftUI 入口
    ├── WebViewScreen.swift        # WKWebView + easyiot:// 协议本地资源服务
    ├── Info.plist                 # 显示名/ATS 放行 http/启动屏/屏幕方向
    ├── Assets.xcassets/           # AppIcon（源自 APP/src/static/app/icons）
    └── www/                       # APP 构建产物（脚本生成，不入库）
```

**WebView 加载原理**：H5 产物通过自定义协议 `easyiot://localhost/index.html` 提供（`WKURLSchemeHandler` 直接从 bundle 内 `www/` 读文件）。页面以"正常网页"身份运行——ES Module、localStorage、对后端 admin-api 的跨域请求均与真实站点部署一致，规避了 `file://` 直载在 WebKit/Chromium 内核下的种种限制。

## 三、环境准备（新电脑）

### 3.1 Node + pnpm（构建前端用）

- Node ≥ 20，pnpm ≥ 9（APP 工程有 `only-allow pnpm` 钩子）。
- 安装依赖：`cd APP && pnpm install`

### 3.2 Xcode 16 及以上

壳工程使用了 Xcode 16 的 fileSystemSynchronized 工程格式（objectVersion 77），旧版 Xcode 无法打开。模拟器流程无任何账号要求：

```bash
# 第一次验证推荐先跑模拟器版，全程免签名
xcrun simctl list devices available      # 确认已有可用模拟器
./make-ipa.sh && open easyaiot-1.0.0-prod-ios-sim.app
```

### 3.3 真机调试 / 分发

1. Xcode → Settings → Accounts 登录 Apple ID（免费账号可真机调试）。
2. 把 `ExportOptions.plist` 中 `YOUR_TEAM_ID` 替换为你的 Team ID。
3. `./make-ipa.sh --device`；首次真机运行需在 设置 → 通用 → VPN 与设备管理 中信任开发者证书。

> App Store 上架：将 `ExportOptions.plist` 的 `method` 改为 `app-store-connect` 后重新出包，再用 Transporter/Xcode Organizer 上传。

## 四、日常打包

### 方式一：一键脚本（推荐）

```bash
cd IOS
./make-ipa.sh [--device] [--skip-native] [prod|test|dev]
```

脚本依次完成：版本一致性校验 → 前端按指定模式构建 H5 → 清空并同步 www 资源（含绝对路径归一化安全网）→ xcodebuild 打包 → 复制为带环境后缀的成品。不同环境的包不会互相覆盖。

Linux / CI 环境可执行 `./make-ipa.sh --skip-native`，完成前三步并就绪 `EasyAIoT/www/`，把源码交给任何一台 Mac 继续出包。

### 方式二：分步执行（理解原理用）

```bash
# 1. 构建前端（产出 APP/dist/build/h5；相对路径是本模块的硬性要求）
cd ../APP && VITE_APP_PUBLIC_BASE=./ pnpm build:h5:prod

# 2. 同步 www 资源（先清空再拷贝）
rm -rf  EasyAIoT/www && mkdir -p EasyAIoT/www
cp -a ../APP/dist/build/h5/. EasyAIoT/www/

# 3. 模拟器出包（免签名）
xcodebuild build -project EasyAIoT.xcodeproj -scheme EasyAIoT \
  -configuration Release -sdk iphonesimulator -derivedDataPath build \
  CODE_SIGNING_ALLOWED=NO
# 产物: build/Build/Products/Release-iphonesimulator/EasyAIoT.app

# 4. 真机/分发（需 teamID 已配置）
xcodebuild archive -project EasyAIoT.xcodeproj -scheme EasyAIoT \
  -configuration Release -sdk iphoneos -archivePath build/EasyAIoT.xcarchive
xcodebuild -exportArchive -archivePath build/EasyAIoT.xcarchive \
  -exportOptionsPlist ExportOptions.plist -exportPath build/export
```

### 多环境与后端地址

| 命令 | mode | env 文件 | 说明 |
|---|---|---|---|
| `make-ipa.sh` / `pnpm build:h5:prod` | production | `APP/env/.env.production` | 默认走 `.env` 的正式后端地址 |
| `make-ipa.sh test` / `pnpm build:h5:test` | test | `APP/env/.env.test` | 测试后端地址 |
| `make-ipa.sh dev` / `pnpm build:h5` | development | `APP/env/.env.development` | 开发联调 |

后端地址在各 env 文件的 `VITE_SERVER_BASEURL` 配置，**编译期写死进 JS 包**；部署时改成实际网关地址即可。Info.plist 已开启 ATS 全放行（对应 ANDROID 壳的 `usesCleartextTraffic`），允许 http 后端调试。

## 五、版本号管理

发新版本只改两处（保持一致）：

1. `IOS/EasyAIoT.xcodeproj/project.pbxproj`（Debug 与 Release 两段都要改）
   ```
   CURRENT_PROJECT_VERSION = 101;      // 整数递增
   MARKETING_VERSION = 1.0.1;
   ```
2. `APP/manifest.config.ts`
   ```ts
   'versionName': '1.0.1',
   'versionCode': '101',
   ```

`make-ipa` 脚本会在打包前对这两处做一致性校验，不一致直接终止，避免打出资源错乱的包。同时建议同步更新 `HARMONYOS/AppScope/app.json5`，让三端版本齐平。

## 六、图标与名称

- 图标唯一来源：`APP/src/static/app/icons/1024x1024.png`。当前已复制为 `EasyAIoT/Assets.xcassets/AppIcon.appiconset/AppIcon1024.png`（Xcode 支持 iOS 12+ 单尺寸 1024 图标，各尺寸由系统缩放）。前端更换图标后重跑一次拷贝即可。
- 应用显示名改 `EasyAIoT/Info.plist` 的 `CFBundleDisplayName`；内部分组名等改 pbxproj 的 target 名（一般不动）。

## 七、常见问题排查

| # | 报错 / 现象 | 原因 | 解决 |
|---|---|---|---|
| 1 | Xcode 打开报「项目格式太新」 | Xcode < 16 不支持 objectVersion 77 | 升级 Xcode ≥ 16 |
| 2 | 启动白屏，控制台全是 failed to load module | `www/` 为空或同步了旧缓存 | 用 `make-ipa.sh` 全流程，不要手动只跑 xcodebuild |
| 3 | 页面能开但接口全部失败 | 后端地址写的是 localhost 或网关未启动 | 改 `VITE_SERVER_BASEURL` 为真实网关后重新出包 |
| 4 | 接口跨域报错 | 走了未经网关的直连端口 | 该项目 CORS 由 `DEVICE/iot-gateway` 的 CorsFilter 统一放行，请确认请求经网关（48080/admin-api） |
| 5 | `make-ipa.sh --device` 提示 teamID 占位 | 未替换 `ExportOptions.plist` | 按第三节 3.3 配置 |
| 6 | 真机安装提示不受信任 | 免费签名的常规现象 | 设置 → 通用 → VPN 与设备管理 → 信任 |
| 7 | `preinstall: npx only-allow pnpm` 报错 | APP 工程只允许 pnpm | 不要用 npm/yarn 装 APP 依赖 |
| 8 | 改了前端代码 App 里没生效 | 只跑了 xcodebuild，没有重新构建/同步 www | 用 `make-ipa.sh` 全流程 |

## 八、命令速查

```bash
# 一键打包
cd IOS && ./make-ipa.sh                # 模拟器 .app
cd IOS && ./make-ipa.sh --device       # 分发 .ipa

# 列出目标/模拟器
xcodebuild -project EasyAIoT.xcodeproj -list
xcrun simctl list devices available

# 安装并启动到指定模拟器
xcrun simctl install booted easyaiot-1.0.0-prod-ios-sim.app
xcrun simctl launch booted com.basiclab.iot.app

# 查看 ipa 内信息（解压 Payload/*.app 后）
plutil -p EasyAIoT.app/Info.plist | grep -E "Version|Bundle"
codesign -dv EasyAIoT.app
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
