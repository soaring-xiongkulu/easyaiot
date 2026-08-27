# ANDROID 模块 —— EasyAIoT 移动端 APK 打包壳工程

把 [APP](../APP)（uni-app / unibest）前端工程编译出的资源，塞进一个内置原生运行时的 Android 壳工程，用 Gradle 打出可直接安装的 APK。

本模块不包含业务代码：界面全部来自 APP 模块的 www 资源，壳工程只负责运行时、签名与打包。

```
APP (uni-app 工程)
   │  pnpm build:app[:prod|:test]        ← 第 1 步：编译前端
   ▼
APP/dist/build/app （www 资源）
   │  同步到壳工程 assets                  ← 第 2 步：脚本自动完成
   ▼
ANDROID/app/src/main/assets/apps/__UNI__8A5A71D/www
   │  ./gradlew assembleRelease           ← 第 3 步：打出 APK
   ▼
app/build/outputs/apk/release/app-release.apk
   →  easyaiot-<版本>-<模式>-android.apk
```

日常打包只需一个命令：

```bash
# Linux / macOS
./make-apk.sh            # 生产环境
./make-apk.sh test       # 测试环境
./make-apk.sh dev        # 开发环境

# Windows
make-apk.bat             # 生产环境
make-apk.bat test
```

---

## 一、关键信息速查

| 项 | 值 |
|---|---|
| 包名 (applicationId) | `com.basiclab.iot.app` |
| 应用名 | EasyAIoT（`app/src/main/res/values/strings.xml`） |
| DCloud AppID | `__UNI__8A5A71D`（由 `APP/env/.env` 的 `VITE_UNI_APPID` 决定） |
| 签名证书 | `app/iot.jks`，alias=`iot`，密码=`easyaiot@2026`（store 与 key 相同） |
| 版本号 | `versionCode 100` / `versionName "1.0.0"`（`app/build.gradle`） |
| 目标平台 | minSdk 21 / targetSdk 33 / compileSdk 35 |

## 二、目录结构

```
ANDROID/
├── make-apk.sh / make-apk.bat     # 一键打包脚本（校验版本→构建前端→同步资源→Gradle 打包）
├── settings.gradle                # 仅 include ':app'
├── build.gradle                   # AGP 8.7.3 + 阿里云镜像
├── gradle.properties              # AndroidX 开关等全局配置
├── gradle/wrapper/                # Gradle 8.11.1（腾讯镜像下载）
├── local.properties.example       # 本机 SDK 路径模板（local.properties 不入库）
└── app/
    ├── build.gradle               # 包名/版本/签名/lint 关闭等
    ├── iot.jks                    # 签名证书
    ├── libs/                      # uni-app 离线运行时 AAR（见下节）
    └── src/main/
        ├── AndroidManifest.xml    # 权限 + 入口 Activity + dcloud_appkey
        ├── assets/
        │   ├── data/              # dcloud_control.xml（appid/appver）、features 声明等
        │   └── apps/__UNI__8A5A71D/www/   # APP 模块构建产物（脚本生成，不入库）
        └── res/                   # 图标、启动图、应用名、主题补充
```

## 三、环境准备（新电脑）

### 3.1 Node + pnpm

- Node ≥ 20，pnpm ≥ 9（APP 工程有 `only-allow pnpm` 钩子，不要用 npm/yarn）。
- 安装依赖：`cd APP && pnpm install`

### 3.2 JDK 17 及以上

Gradle 构建需要 JDK 17+（推荐 17 或 21）。注意 Android Studio 自带的 JBR 新版可能超出 Gradle 支持范围，若在 AS 里构建报 class version 错误，把 Gradle JDK 指向独立安装的 JDK 17/21。

### 3.3 Android SDK

需要的组件：`platforms;android-35`、`build-tools;35.0.0`、`platform-tools`。首次执行 Gradle 会自动补装缺失组件（前提是 licenses 已接受），也可手动：

```bash
cmdline-tools/latest/bin/sdkmanager --install "platforms;android-35" "build-tools;35.0.0" "platform-tools"
yes | cmdline-tools/latest/bin/sdkmanager --licenses
```

然后复制 `local.properties.example` 为 `local.properties`，填入本机 SDK 路径。

> ⚠️ **必须用正斜杠**，Windows 下同样如此，否则属性转义会把路径吞坏：
> ```properties
> sdk.dir=C:/Users/you/AppData/Local/Android/Sdk
> ```

### 3.4 uni-app 离线运行时（libs/ 已就位）

`app/libs/` 内置了五组离线运行时库（uni-app v8 核心、5+ 基座等）。**版本必须与 APP 前端编译器配套**：当前 APP 的编译器为 `3.0.0-4070620250821001`（2025-08 版），与本目录内置库兼容。日后如果升级前端依赖（`pnpm uvm`），编译器随之更新，届时请到 DCloud 官网「App 离线 SDK」下载页换用同版本号的库文件替换 `libs/*.aar`。

## 四、日常打包

### 方式一：一键脚本（推荐）

```bash
cd ANDROID
./make-apk.sh [prod|test|dev]
```

脚本依次完成：版本一致性校验 → 前端按指定模式构建 → 清空并同步 www 资源 → Gradle assembleRelease → 复制为 `easyaiot-<版本>-<模式>-android.apk`。文件名带环境后缀，不同环境的包不会互相覆盖。

### 方式二：分步执行（理解原理用）

```bash
# 1. 构建前端（产出 APP/dist/build/app）
cd ../APP && pnpm build:app:prod

# 2. 同步 www 资源（先清空再拷贝；appid 三处必须一致）
rm -rf app/src/main/assets/apps/__UNI__8A5A71D/www
mkdir -p  app/src/main/assets/apps/__UNI__8A5A71D/www
cp -a ../APP/dist/build/app/. app/src/main/assets/apps/__UNI__8A5A71D/www/

# 3. Gradle 打包
./gradlew assembleRelease --no-daemon
# 产物: app/build/outputs/apk/release/app-release.apk
```

### 多环境与后端地址

| 命令 | mode | env 文件 | 说明 |
|---|---|---|---|
| `make-apk.sh` / `pnpm build:app:prod` | production | `APP/env/.env.production` | 默认走 `.env` 的正式后端地址 |
| `make-apk.sh test` / `pnpm build:app:test` | test | `APP/env/.env.test` | 测试后端地址 |
| `make-apk.sh dev` / `pnpm build:app` | development | `APP/env/.env.development` | 开发联调 |

后端地址在各 env 文件的 `VITE_SERVER_BASEURL` 配置；默认 `http://localhost:48080/admin-api`，部署时改成实际网关地址即可。Manifest 里已开启 `usesCleartextTraffic`，允许 http 后端调试。

## 五、版本号管理

发新版本只改两处（保持一致）：

1. `ANDROID/app/build.gradle`
   ```gradle
   versionCode 101      // 整数递增
   versionName "1.0.1"  // 显示版本
   ```
2. `APP/manifest.config.ts`
   ```ts
   'versionName': '1.0.1',
   'versionCode': '101',
   ```

`dcloud_control.xml` 的 `appver` 也要同步成同样的 versionName——`make-apk` 脚本会在打包前对这三处做一致性校验，不一致直接终止，避免打出资源错乱的包。

## 六、签名证书

当前证书信息（`app/iot.jks`）：

| 项 | 值 |
|---|---|
| 别名 | `iot` |
| 密码 | `easyaiot@2026`（store 与 key 相同） |
| 有效期 | 25 年（2026 → 2051） |
| SHA1（申请 AppKey 用，去冒号小写） | `a9ad5ef3990d1f045ae6d524637333f468d14fc1` |
| SHA256 | `1533a8b1dbb9b420f6e706136fa649d4e5f13b0ba45163a59cf4e378695afde3` |

查看指纹：

```bash
keytool -list -v -keystore app/iot.jks -storepass easyaiot@2026
```

生成新证书（如需更换为自己的发布证书）：

```bash
keytool -genkeypair -v -keystore new.jks -alias iot -keyalg RSA -keysize 2048 \
  -validity 9125 -dname "CN=EasyAIoT, OU=Mobile, O=EasyAIoT, L=Shenzhen, ST=Guangdong, C=CN"
```

然后同步修改 `app/build.gradle` 的 `signingConfigs`，并重新申请/登记 AppKey（见下节）。**换证书 = 换指纹 = 必须重新配置 AppKey**，且老 APK 无法覆盖安装（签名不同需先卸载）。

> 提示：仓库内的 jks 与密码便于内部开发联调直接出包；对外正式发布前建议换成自行保管、不入库的私有证书。

## 七、AppKey

Manifest 中的 `dcloud_appkey` 已配置当前证书对应的 key（应用 `__UNI__8A5A71D`，包名 `com.basiclab.iot.app`）。**若更换包名或签名证书（SHA1 变化），原 key 会失效，启动会提示「未配置 appkey 或配置错误」**，此时按下述步骤重新申请并回填。

申请/更新步骤：

1. 登录 DCloud 开发者中心（dev.dcloud.net.cn，需 DCloud 账号）。
2. 应用管理中确认 `__UNI__8A5A71D` 这个应用在你自己的账号名下（该 appid 来自 `APP/env/.env` 的 `VITE_UNI_APPID`；若不属于你，请在自己账号下新建应用，用新的 appid 替换 `.env`、`assets/apps/` 目录名和 `dcloud_control.xml`，并重新构建前端）。
3. 「各平台信息」新增 Android 平台：
   - 包名：`com.basiclab.iot.app`
   - SHA1：`A9AD5EF3990D1F045AE6D524637333F468D14FC1`（即上文指纹的去冒号形式）
4. 把拿到的 AppKey 填入 `app/src/main/AndroidManifest.xml`：
   ```xml
   <meta-data android:name="dcloud_appkey" android:value="申请到的 key"/>
   ```
5. 重跑 `./make-apk.sh` 完成最终打包。

## 八、在 Android Studio 中使用（可选）

`File → Open` 打开 `ANDROID` 目录即可（首次会索引 Gradle）。检查 `Settings → Build Tools → Gradle → Gradle JDK` 使用 JDK 17/21。之后可用 AS 菜单 `Build → Generate Signed APK` 或终端 `gradlew assembleRelease` 出包。

注意：仓库不含 www 资源（已 gitignore），克隆后请先跑一次 `./make-apk.sh` 或分步流程第 1~2 步同步资源，否则缺 `assets/apps/**` 无法编译。

## 九、常见问题排查

| # | 报错 / 现象 | 原因 | 解决 |
|---|---|---|---|
| 1 | `文件名、目录名或卷标语法不正确` 或 IO 异常发生在 lintVital / dexBuilder | `local.properties` 里 `sdk.dir` 用了反斜杠转义，路径被吞变非法 | 改用正斜杠 |
| 2 | release 构建卡在 lintVitalReport 失败 | AGP 强制 lint 对壳资源误报 | `app/build.gradle` 已配 `lint { checkReleaseBuilds false }`；如自定义改动后再遇到同样问题检查此项 |
| 3 | Gradle 报 Unsupported class file major version | JAVA_HOME 指向的 JDK 过新或过旧 | 用 JDK 17 或 21 |
| 4 | 首次构建长时间停在下载组件 | 正在下载 SDK 组件 / Gradle 发行版 / 依赖 | 保持网络畅通，均走国内镜像或官方源，装完不再重复 |
| 5 | `preinstall: npx only-allow pnpm` 报错 | APP 工程只允许 pnpm | 不要用 npm/yarn 装 APP 依赖 |
| 6 | 改了前端代码，APK 里没生效 | 只跑了 gradlew，没有重新构建/同步 www | 用 `make-apk.sh` 全流程 |
| 7 | 启动白屏或提示 appid 不匹配 | 前端 appid 与 assets 目录名 / dcloud_control.xml 不一致 | 三处一致：`.env` 的 appid、`assets/apps/<appid>/www`、`dcloud_control.xml` |
| 8 | 启动弹「未配置 appkey 或配置错误」 | 包名/SHA1/appid 与 AppKey 申请信息不符（换过证书、改过包名或 appid） | 按第七节重新申请并回填，重新打包 |
| 9 | Windows 上 bat 中文乱码报「不是内部或外部命令」 | zh-CN 的 cmd 按 GBK 解析 bat | `make-apk.bat` 全文只用 ASCII 字符，修改时保持该约定 |
| 10 | 无法覆盖安装新 APK | 签名不同（换过证书）或 versionCode 未递增 | 先卸载旧包；发版记得递增 versionCode |

## 十、命令速查

```bash
# 一键打包
cd ANDROID && ./make-apk.sh

# 手动 Gradle
cd ANDROID && ./gradlew assembleRelease --no-daemon

# 校验 APK 签名（需 build-tools 35.0.0）
$SDK/build-tools/35.0.0/apksigner verify --print-certs app/build/outputs/apk/release/app-release.apk

# 查看 APK 信息（包名/版本/权限）
$SDK/build-tools/35.0.0/aapt dump badging app/build/outputs/apk/release/app-release.apk

# 安装到已连接设备
adb install -r app/build/outputs/apk/release/app-release.apk
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
