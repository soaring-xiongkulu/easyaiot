# 移动端三端打包管理（Android / iOS / HarmonyOS）

EasyAIoT 的移动端由一个 uni-app 前端工程 + 三个原生壳工程组成。本文是**三端统一管理**的总入口：命令速查、产物命名规范、发版流程；各平台的环境准备、签名、疑难排查见各模块自己的 README。

```
                 APP（uni-app/unibest 前端）
                        │ pnpm build:app │ build:h5
          ┌─────────────┼─────────────────┐
          ▼             ▼                 ▼
     ANDROID/        IOS/            HARMONYOS/
   DCloud 离线运行时  WKWebView 壳      ArkWeb 壳
   Gradle → apk     xcodebuild → ipa  hvigor → hap
```

| 模块 | 一键脚本 | 技术形态 | 平台 README |
|---|---|---|---|
| ANDROID | `ANDROID/make-apk.sh[.bat]` | DCloud 离线 SDK + Gradle | [ANDROID/README.md](../../ANDROID/README.md) |
| IOS | `IOS/make-ipa.sh` | WKWebView 壳 + xcodebuild（需 Xcode 16+） | [IOS/README.md](../../IOS/README.md) |
| HARMONYOS | `HARMONYOS/make-hap.sh` | ArkWeb 壳 + hvigor（需 DevEco 工具链） | [HARMONYOS/README.md](../../HARMONYOS/README.md) |

> iOS 与 HarmonyOS 模块承载的是 H5 构建产物（`build:h5`），与 Android 承载的 App 运行时产物并行不悖：前端代码已把原生能力差异全部隔离在条件编译里，三种形态共用同一套页面与接口层。为什么 iOS/鸿蒙不用 DCloud 离线 SDK，见两模块 README 开头的「技术差异」说明。

---

## 一、统一管理命令

在仓库根目录执行（脚本位于 `.scripts/docker/mobile.sh`）：

```bash
.scripts/docker/mobile.sh status                  # 三端版本一致性 / 工具链就绪度 / 成品数量 概览
.scripts/docker/mobile.sh build all prod          # 三端依次出包（缺哪个平台工具链会明确报错，不影响其余端）
.scripts/docker/mobile.sh build android           # 只打 Android 生产包（默认 prod）
.scripts/docker/mobile.sh build ios test --skip-native   # 无 Mac 环境：只做前端构建+资源同步，产出可交接的壳源码状态
.scripts/docker/mobile.sh bump 1.0.1 101          # 发版号一次改齐 5 处（见第三节）
.scripts/docker/mobile.sh artifacts               # 列出所有安装包成品
.scripts/docker/mobile.sh clean all               # 清理成品（不含中间构建目录）
```

也可通过统一安装脚本调用：`./install_linux.sh mobile <同上子命令>`；交互菜单里选「移动端」可获得同样的引导。

Windows 用户请用 Git Bash 执行 `mobile.sh`（Android 打包另有原生的 `make-apk.bat`）。

### 中间构建产物的深度清理

`clean` 只删仓库里的安装包成品；如需清理编译中间物，进对应模块手动执行：

```bash
cd ANDROID  && ./gradlew clean && rm -rf .gradle
cd IOS      && rm -rf build
cd HARMONYOS && ./hvigorw clean && rm -rf entry/build **/oh_modules .hvigor
```

## 二、安装包命名规范

三端统一为全小写 kebab-case：`easyaiot-<版本>-<环境>-<平台>.<格式>`

| 端 | 成品名示例 | 说明 |
|---|---|---|
| Android | `easyaiot-1.0.0-prod-android.apk` | 签名 release 包 |
| iOS 真机/分发 | `easyaiot-1.0.0-prod-ios.ipa` | 需签名配置 |
| iOS 模拟器 | `easyaiot-1.0.0-prod-ios-sim.app` | 免签名目录束，双击即跑 |
| HarmonyOS | `easyaiot-1.0.0-prod-harmonyos.hap` | 未签名包为 `-unsigned.hap` |

规则要点：

- 字段顺序 = 产品 → 版本 → 环境(`prod|test|dev`) → 平台 → 格式；排序稳定便于按名归档与 CI 归集。
- 全小写、连字符分隔——对对象存储/CDN、Linux CI 工件归档、以及跨平台脚本均最友好。
- 同一版本不同环境的文件天然不重名，历史命名（`EasyAIoT-*-release.apk` 等）已被替代；`mobile.sh artifacts/clean/status` 同时兼容识别新旧两种。

## 三、版本号管理（发版流程）

版本基准只有一处认知来源：`APP/manifest.config.ts` 的 `'versionName'` / `'versionCode'`。三端壳工程各自留有副本用于系统商店元数据，共 5 个物理位置：

| # | 文件 | 字段 |
|---|---|---|
| 1 | `APP/manifest.config.ts` | `'versionName': 'x.y.z'` / `'versionCode': 'N'` |
| 2 | `ANDROID/app/build.gradle` | `versionName "x.y.z"` / `versionCode N` |
| 3 | `ANDROID/app/src/main/assets/data/dcloud_control.xml` | `appver="x.y.z"` |
| 4 | `IOS/EasyAIoT.xcodeproj/project.pbxproj` | Debug + Release 各一份 `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` |
| 5 | `HARMONYOS/AppScope/app.json5` | `versionName` / `versionCode` |

不要手改这 5 处，用一条命令改齐并自动回读校验：

```bash
$ .scripts/docker/mobile.sh bump 1.0.1 101
版本号升级: versionName=1.0.1  versionCode=101（共 5 处）

SUCCESS: 五处版本号已统一为 1.0.1/101
  1. APP/manifest.config.ts                 ('versionName'/'versionCode')
  ...
```

任何一处不一致时，`.scripts/docker/mobile.sh status` 会标红（不一致），且各端的 make 脚本会在打包前拒绝继续——宁可不出包，也不出错包。

## 四、CI / 团队协作建议

- **前后端流水线分离**：前端资源步骤与原生工具链无关，任何 Linux runner 都能跑 `.scripts/docker/mobile.sh build <端> <env> --skip-native`，把同步好的仓库工件交给 macOS runner（iOS）或自托管 DevEco runner（鸿蒙）做最后的原生编译。
- **工件命名即协议**：CI 按 `easyaiot-*-{android,ios,harmonyos}.*` 归档到制品库后，测试分发可以纯按文件名路由，无需额外清单。
- **发版原子性**：`bump` 是唯一合法的版本变更通道；review 时 diff 里应且只应出现上述 5 个文件的版本字段变化，多一行都值得追问。
