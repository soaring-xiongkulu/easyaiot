# EasyAIoT COMPILE

把 `PANEL`（及其他模块，后续扩展）编译打包为各平台可执行文件 / 安装包。

当前已实现：
- **Ubuntu 单文件** `easyaiot-panel` + **内置 runtime** `.deb`（按架构绑定 `install_linux.sh` / `install_linux_arm.sh` / `install_linux_kylin.sh`）
- **交互式打包菜单** `COMPILE/install_linux.sh`（Ubuntu / CentOS / **麒麟(Kylin) / 欧拉(openEuler)** / Windows / macOS / 全量 Linux）
- **Windows** `easyaiot-panel.exe` + **内置 runtime**（`install_windows.sh` 仅镜像部署）+ 可选 NSIS
- **macOS** `easyaiot-panel` + **内置 runtime**（`install_mac.sh` 仅镜像部署）+ 可选 `.app` / `.dmg`（圆形白底图标，与 Linux 一致）
- **CentOS/RHEL x86** `easyaiot-panel` + `.rpm`，按 **el7 / el8 / el9** 分别构建（默认 el9；**不含**内置 runtime，需配置 `EASYAIOT_ROOT`；部署用 `install_linux_centos.sh`）
- **CentOS/RHEL ARM** `easyaiot-panel` + `.rpm`，同样区分 **el7 / el8 / el9**（默认 el9；Docker `linux/arm64` 交叉构建；部署用 `install_linux_centos_arm.sh`）
- **欧拉(openEuler)** `easyaiot-panel` + `.rpm`（同上；部署用仓库内 `install_linux_openeuler.sh`）

## 快速开始

> **Ubuntu Docker 打包已加速：** 默认先在宿主机 `npm run build`，容器内只做 PyInstaller；
> 构建上下文只含 PANEL 必要文件（约数 MB），不再把整个仓库塞进 dockerd，也不再在容器里跑 `npm install`（以前常卡 400s+）。
>
> **CentOS 默认也走 Docker**，并按 EL 大版本分开打包（**包源默认华为云**，`COMPILE_CN_MIRROR=aliyun|tuna` 可切换）：
> - el9：`rockylinux:9` → `COMPILE/dist/centos-el9/`（`centos` 同义）
> - el8：`rockylinux:8` → `COMPILE/dist/centos-el8/`
> - el7：`centos:7` → `COMPILE/dist/centos-el7/`（SCL rh-python38）
>
> **CentOS ARM** 同样区分 el7/el8/el9（`--platform linux/arm64`），产物在 `COMPILE/dist/centos-arm-el{7,8,9}/`。
>
> **欧拉(openEuler)** 默认 Docker（`openeuler/openeuler:24.03`），dnf 默认华为云，**不做全量 `dnf update`**。

```bash
# 统一入口（交互菜单：部署操作 / 安装操作）
bash COMPILE/install_linux.sh
# 非交互改为本机构建：COMPILE_BUILD_MODE=local bash COMPILE/install_linux.sh
# 非交互全量 Linux 包：bash COMPILE/install_linux.sh pack-all
# Windows（须在 Windows 主机）：bash COMPILE/install_linux.sh windows [--installer]

# x86/amd64 单文件
bash COMPILE/build.sh ubuntu-x86
ls -lh COMPILE/dist/ubuntu/easyaiot-panel

# ARM64 单文件（deploy 调用 install_linux_arm.sh）
bash COMPILE/build.sh ubuntu-arm
ls -lh COMPILE/dist/ubuntu-arm/easyaiot-panel

# 麒麟 ARM64 单文件（deploy 调用 install_linux_kylin.sh）
bash COMPILE/build.sh ubuntu-kylin
ls -lh COMPILE/dist/ubuntu-kylin/easyaiot-panel

# .deb 安装包（示例：打 x86）
bash COMPILE/build.sh ubuntu-x86 --deb
ls -lh COMPILE/dist/ubuntu/easyaiot-panel_*_amd64.deb

# 或：打 ARM / 麒麟
bash COMPILE/build.sh ubuntu-arm --deb
ls -lh COMPILE/dist/ubuntu-arm/easyaiot-panel_*_arm_arm64.deb

bash COMPILE/build.sh ubuntu-kylin --deb
ls -lh COMPILE/dist/ubuntu-kylin/easyaiot-panel_*_kylin_arm64.deb

# Windows（须在 Windows 主机；也可经统一入口）
bash COMPILE/install_linux.sh windows
bash COMPILE/install_linux.sh windows --installer   # 需 NSIS / makensis
# 等价：bash COMPILE/build.sh windows [--installer]
ls -lh COMPILE/dist/windows/easyaiot-panel.exe
ls -ld COMPILE/dist/windows/runtime
ls -lh COMPILE/dist/windows/panel.env COMPILE/dist/windows/run.bat
# 运行：
# COMPILE\dist\windows\run.bat
# 然后在 PANEL「应用部署」执行 install（仅拉取预构建镜像）

# macOS（需在 macOS 主机执行；产物含 runtime/ + install_mac.sh）
# 图标源：COMPILE/assets/panel-logo.png → 圆形白底（与 Ubuntu/Windows 一致）
bash COMPILE/build.sh macos
ls -lh COMPILE/dist/macos/easyaiot-panel
ls -ld COMPILE/dist/macos/runtime
ls -lh COMPILE/dist/macos/panel.env COMPILE/dist/macos/run.command
# 安装包：.app + .dmg（含 Applications 快捷方式）
bash COMPILE/build.sh macos --dmg
# Apple Silicon → easyaiot-panel-<VERSION>-arm64.dmg
# Intel         → easyaiot-panel-<VERSION>-amd64.dmg
ls -lh COMPILE/dist/macos/easyaiot-panel-*-{arm64,amd64}.dmg
# 运行：打开 dmg 拖到 Applications，或 ./COMPILE/dist/macos/run.command

# CentOS/RHEL x86 — 按 EL 版本分别打包（默认 el9）
bash COMPILE/build.sh centos-el9          # 同: centos
bash COMPILE/build.sh centos-el8
bash COMPILE/build.sh centos-el7
ls -lh COMPILE/dist/centos-el9/*.rpm COMPILE/dist/centos-el8/*.rpm COMPILE/dist/centos-el7/*.rpm

# CentOS/RHEL ARM64 — 按 EL 版本交叉构建
bash COMPILE/build.sh centos-arm-el9      # 同: centos-arm
bash COMPILE/build.sh centos-arm-el8
bash COMPILE/build.sh centos-arm-el7
ls -lh COMPILE/dist/centos-arm-el9/*aarch64.rpm

# openEuler（默认 Docker；基础镜像 openeuler/openeuler:24.03）
bash COMPILE/build.sh openeuler
# 仅二进制：bash COMPILE/build.sh openeuler --no-rpm
# 本机构建：bash COMPILE/build.sh openeuler --local
ls -lh COMPILE/dist/openeuler/easyaiot-panel COMPILE/dist/openeuler/easyaiot-panel-*-*.oe2403.*.rpm
# 安装后改 EASYAIOT_ROOT，部署用：.scripts/docker/install_linux_openeuler.sh

# 一次打全量 Linux 包（Ubuntu×3 deb + CentOS el7/el8/el9 x86+arm + openEuler；每包版本号 +1）
bash COMPILE/install_linux.sh pack-all
# 或：bash COMPILE/build.sh all-linux

# 安装/卸载管理
bash COMPILE/install_linux.sh install auto
bash COMPILE/install_linux.sh install centos-el9   # 或 centos-el8 / centos-el7 / centos-arm-el9
bash COMPILE/install_linux.sh uninstall
bash COMPILE/install_linux.sh status
```

## 打包操作详细步骤

以下步骤默认在**仓库根目录**执行：`/path/to/easyaiot`。

### 1) 构建前检查

```bash
# 进入仓库根目录
cd /path/to/easyaiot

# 检查脚本权限（如无执行权限可补上）
ls -l COMPILE/build.sh
chmod +x COMPILE/build.sh \
  COMPILE/platforms/ubuntu/build.sh COMPILE/platforms/ubuntu/pack_deb.sh \
  COMPILE/platforms/centos/el_common.sh \
  COMPILE/platforms/centos/build.sh COMPILE/platforms/centos/pack_rpm.sh \
  COMPILE/platforms/centos-arm/build.sh COMPILE/platforms/centos-arm/pack_rpm.sh \
  COMPILE/platforms/openeuler/build.sh COMPILE/platforms/openeuler/pack_rpm.sh

# 版本号在每次打包时自动递增（也可 PANEL_VERSION=105 固定指定）
# 状态文件：COMPILE/.panel-version（gitignore，也可由 dist 已有包推断）
```

如果要打 `.deb` / `.rpm`：请确保“当前 shell 的 `python3`”能导入 `Pillow`（模块名 `PIL`）。
`pack_deb.sh` / `pack_rpm.sh` 生成桌面图标时会用到；若在 `conda(base)` 里打包，可能需要 `deactivate` 或 `python3 -m pip install pillow`。

## 前置依赖提示（按目标）
- **Ubuntu deb（Docker 默认）**：本机 `npm`（先编前端）、`docker`（含 buildx）、`dpkg-deb`（`apt install dpkg-dev`）、`python3`+Pillow。
- Ubuntu ARM / **麒麟(Kylin)**：同上；Docker 使用 `--platform linux/arm64`，宿主机需已注册 QEMU/binfmt（`docker buildx ls` 能看到 `linux/arm64`）。
- **CentOS/RHEL（Docker 默认）**：只需本机 `docker`；容器内安装 `rpm-build` 并完成 PyInstaller。`--local` 时才需要本机 `rpm-build` + Node + Python 3.11+。
- **欧拉(openEuler)**（Docker 默认）：只需本机 `docker`；基础镜像 `openeuler/openeuler:24.03`（可用 `COMPILE_OPENEULER_BASE_IMAGE` 覆盖）。`--local` 时需本机 `rpm-build` + Node + Python。
- **Windows/macOS**：必须在对应 OS 本机（或对应 CI Runner）执行，需 `Node.js + npm`、Python 3.11+、Pillow（`requirements-build.txt`）；Windows 可选 NSIS（`makensis`）；macOS 打包 `.app`/`.dmg` 另需系统自带 `sips` / `iconutil` / `hdiutil`。

如果要走 Docker 构建（默认方式），还需要确认 Docker 可用：

```bash
docker --version
docker compose version
docker buildx ls    # ARM/麒麟打包前确认有 linux/arm64
```

### 2) 生成 Ubuntu 单文件二进制（推荐先执行）

```bash
# 默认使用 Docker，输出 Linux 可执行文件
bash COMPILE/build.sh ubuntu-x86
ls -lh COMPILE/dist/ubuntu/easyaiot-panel

bash COMPILE/build.sh ubuntu-arm
ls -lh COMPILE/dist/ubuntu-arm/easyaiot-panel

bash COMPILE/build.sh ubuntu-kylin
ls -lh COMPILE/dist/ubuntu-kylin/easyaiot-panel
```

本地构建（不走 Docker）：

```bash
# x86/amd64（本机）
bash COMPILE/build.sh ubuntu-x86 --local

# ARM / 麒麟：建议在对应架构机器上执行
bash COMPILE/build.sh ubuntu-arm --local
bash COMPILE/build.sh ubuntu-kylin --local
```

### 3) 基于二进制打 .deb 安装包

```bash
# x86/amd64（deploy 调用 install_linux.sh）
bash COMPILE/build.sh ubuntu-x86 --deb

# ARM64（deploy 调用 install_linux_arm.sh）
bash COMPILE/build.sh ubuntu-arm --deb

# 麒麟 ARM64（deploy 调用 install_linux_kylin.sh）
bash COMPILE/build.sh ubuntu-kylin --deb

# 兼容别名：deb 等价于 ubuntu-x86 --deb
bash COMPILE/build.sh deb
```

打包完成后检查：

```bash
ls -lh COMPILE/dist/ubuntu/*.deb
ls -lh COMPILE/dist/ubuntu-arm/*.deb
ls -lh COMPILE/dist/ubuntu-kylin/*.deb
```

预期产物示例（`<VERSION>` 为自动递增的数字版本）：

- x86/amd64：`COMPILE/dist/ubuntu/easyaiot-panel_<VERSION>_amd64.deb`
- ARM64：`COMPILE/dist/ubuntu-arm/easyaiot-panel_<VERSION>_arm_arm64.deb`
- **麒麟(Kylin)**：`COMPILE/dist/ubuntu-kylin/easyaiot-panel_<VERSION>_kylin_arm64.deb`
- CentOS/RHEL x86 el9：`COMPILE/dist/centos-el9/easyaiot-panel-<VERSION>-1.el9.<arch>.rpm`（构建目标 `centos` 同义指向 el9）
- CentOS/RHEL x86 el8 / el7：`COMPILE/dist/centos-el8/...el8...rpm`、`COMPILE/dist/centos-el7/...el7...rpm`
- CentOS/RHEL ARM el9：`COMPILE/dist/centos-arm-el9/easyaiot-panel-<VERSION>-1.el9.aarch64.rpm`（构建目标 `centos-arm` 同义指向 el9）
- CentOS/RHEL ARM el8 / el7：`COMPILE/dist/centos-arm-el8/`、`COMPILE/dist/centos-arm-el7/`
- **欧拉(openEuler)**：`COMPILE/dist/openeuler/easyaiot-panel-<VERSION>-1.oe2403.<arch>.rpm`（与包内 NEVRA 一致；oe2403 = openEuler 24.03）

### 4) 安装并验证 .deb

```bash
# 安装
sudo apt install ./COMPILE/dist/ubuntu/easyaiot-panel_*_amd64.deb
# 或 ARM / 麒麟：
# sudo apt install ./COMPILE/dist/ubuntu-arm/easyaiot-panel_*_arm_arm64.deb
# sudo apt install ./COMPILE/dist/ubuntu-kylin/easyaiot-panel_*_kylin_arm64.deb

# 配置 EasyAIoT 仓库根目录（非常关键）
sudoedit /etc/easyaiot-panel/panel.env
# 设置：
# EASYAIOT_ROOT=/path/to/easyaiot

# 启动服务并检查状态
sudo systemctl daemon-reload
sudo systemctl enable easyaiot-panel
sudo systemctl restart easyaiot-panel
sudo systemctl status easyaiot-panel --no-pager
```

访问验证：

```bash
# 浏览器访问
http://127.0.0.1:9200/
```

### 4.1) Ubuntu 下重新安装/升级（覆盖安装）.deb

> 说明：`.deb` 安装时会写入 systemd 服务 `easyaiot-panel.service`，配置文件在 `/etc/easyaiot-panel/panel.env`，二进制默认在 `/opt/easyaiot-panel/bin/easyaiot-panel`。
> `postinst` 里默认会 `enable` 服务，但不会强制拉起（因此你通常仍需要下面的 `restart`）。

```bash
# 1) 停止当前服务（可选，但建议）
sudo systemctl stop easyaiot-panel || true

# 2) 先备份配置（强烈建议，尤其是你改过 EASYAIOT_ROOT / PANEL_TOKEN）
sudo cp -a /etc/easyaiot-panel/panel.env "/etc/easyaiot-panel/panel.env.bak.$(date +%F_%H%M%S)" 2>/dev/null || true

# 3) 安装/覆盖安装（二选一）
# x86/amd64：
sudo apt install -y ./COMPILE/dist/ubuntu/easyaiot-panel_*_amd64.deb
# 或 ARM / 麒麟：
# sudo apt install -y ./COMPILE/dist/ubuntu-arm/easyaiot-panel_*_arm_arm64.deb
# sudo apt install -y ./COMPILE/dist/ubuntu-kylin/easyaiot-panel_*_kylin_arm64.deb

# 如果你确实需要“强制重装同版本”（上面没生效/版本未变化时可用 dpkg 强制覆盖）：
# sudo dpkg -i ./COMPILE/dist/ubuntu/easyaiot-panel_*_amd64.deb
# sudo apt -f install

# 4) 重新检查关键配置（非常关键）
sudoedit /etc/easyaiot-panel/panel.env

# 设置示例：
# EASYAIOT_ROOT=/path/to/easyaiot
# 如果你使用 deb 包内置 runtime，则可保持默认：/opt/easyaiot-panel/runtime

# 5) 重载并启动（建议每次都执行）
sudo systemctl daemon-reload
sudo systemctl enable easyaiot-panel
sudo systemctl restart easyaiot-panel
sudo systemctl status easyaiot-panel --no-pager
```

访问验证：

```bash
http://127.0.0.1:9200/
```

### 4.2) Ubuntu 卸载（remove）与彻底卸载（purge）

`.deb` 卸载时：
- `prerm`：会先 `stop` 服务（在 `remove/upgrade/deconfigure` 场景）
- `postrm`：在 `remove/purge` 场景会 `disable` 服务，并更新桌面条目/图标缓存（如果命令存在）

```bash
# 1) 普通卸载（保留 /etc/easyaiot-panel/panel.env 等配置）
sudo apt remove -y easyaiot-panel

# 2) 检查服务是否已停止/卸载
sudo systemctl status easyaiot-panel --no-pager || true

# 3) 如需彻底清理配置：用 purge（会移除包内置/注册的配置文件）
sudo apt purge -y easyaiot-panel

# 4) 清理残留目录（如果 purge 后你仍看到目录存在）
sudo rm -rf /etc/easyaiot-panel 2>/dev/null || true

# 5) 重载 systemd 元数据
sudo systemctl daemon-reload
```

### 5) 常用排查命令

```bash
# 查看服务日志
journalctl -u easyaiot-panel -f

# 检查安装文件
dpkg -L easyaiot-panel

# 检查配置文件
cat /etc/easyaiot-panel/panel.env
```

### 安装 .deb（快速版）

完整安装与验证请参考上方“**4) 安装并验证 .deb**”。如只需快速安装，可执行：

```bash
sudo apt install ./COMPILE/dist/ubuntu/easyaiot-panel_*_amd64.deb
# 或 ARM / 麒麟：
# sudo apt install ./COMPILE/dist/ubuntu-arm/easyaiot-panel_*_arm_arm64.deb
# sudo apt install ./COMPILE/dist/ubuntu-kylin/easyaiot-panel_*_kylin_arm64.deb
sudo systemctl restart easyaiot-panel
```

安装后会在应用菜单出现 `EasyAIoT Panel`，点击会尝试启动服务并打开浏览器。

### 直接跑二进制

```bash
# x86/amd64：
bash COMPILE/dist/ubuntu/run.sh

# ARM64：
bash COMPILE/dist/ubuntu-arm/run.sh

# 麒麟：
bash COMPILE/dist/ubuntu-kylin/run.sh

# 或（直接运行二进制）：
export EASYAIOT_ROOT=/path/to/easyaiot

# x86/amd64：
./COMPILE/dist/ubuntu/easyaiot-panel
# ARM64：
./COMPILE/dist/ubuntu-arm/easyaiot-panel
# 麒麟：
./COMPILE/dist/ubuntu-kylin/easyaiot-panel
```

### 6) CentOS/RHEL 打包与安装（el7 / el8 / el9）

> 按 **EL 大版本分别构建**，产物目录与 RPM dist 标签一一对应：
>
> | 目标 | 基础镜像 | 产物目录 | RPM 示例 |
> |------|----------|----------|----------|
> | `centos-el9`（`centos` 同义） | `rockylinux:9` + 国内 dnf | `dist/centos-el9/` | `*-1.el9.x86_64.rpm` |
> | `centos-el8` | `rockylinux:8` + 国内 dnf | `dist/centos-el8/` | `*-1.el8.x86_64.rpm` |
> | `centos-el7` | `centos:7` + 国内 vault/SCL | `dist/centos-el7/` | `*-1.el7.x86_64.rpm` |
>
> 国内源：`COMPILE_CN_MIRROR=huawei`（默认）/`aliyun`/`tuna`。可选 `COMPILE_CN_REGISTRY=docker.1panel.live` 加速拉基础镜像。
>
> RPM **不打入**内置 runtime：安装后必须把 `EASYAIOT_ROOT` 指到本机仓库根，部署用 `.scripts/docker/install_linux_centos.sh`。

```bash
bash COMPILE/build.sh centos-el9    # 同 centos
bash COMPILE/build.sh centos-el8
bash COMPILE/build.sh centos-el7
ls -lh COMPILE/dist/centos-el9/easyaiot-panel-*-*.el9.*.rpm
```

安装示例（el9）：

```bash
sudo rpm -Uvh ./COMPILE/dist/centos-el9/easyaiot-panel-*-*.el9.*.rpm
sudoedit /etc/easyaiot-panel/panel.env   # 改 EASYAIOT_ROOT
sudo systemctl enable --now easyaiot-panel
```

```bash
bash COMPILE/install_linux.sh install centos-el9
# 或 centos-el8 / centos-el7
```

### 6.0) CentOS/RHEL ARM 打包与安装（el7 / el8 / el9）

> 与 x86 相同按 EL 区分；默认 Docker `--platform linux/arm64` 交叉构建。  
> `panel.env` 默认 `INSTALL_SCRIPT=.scripts/docker/install_linux_centos_arm.sh`。

```bash
bash COMPILE/build.sh centos-arm-el9    # 同 centos-arm
bash COMPILE/build.sh centos-arm-el8
bash COMPILE/build.sh centos-arm-el7
ls -lh COMPILE/dist/centos-arm-el9/easyaiot-panel-*-*.el9.aarch64.rpm
bash COMPILE/install_linux.sh install centos-arm-el9
```

### 6.1) **欧拉(openEuler)** 打包与安装

> **欧拉(openEuler)** 默认 Docker 构建（`platforms/openeuler/Dockerfile`，基础镜像 `openeuler/openeuler:24.03`）。
> dnf 默认走华为云国内源（`COMPILE_CN_MIRROR`），不再执行全量 `dnf update`。
> 与 CentOS 相同：**不含**内置 runtime；安装后改 `EASYAIOT_ROOT`，平台部署用 `.scripts/docker/install_linux_openeuler.sh`。

```bash
# 默认：Docker 产出二进制 + rpm
bash COMPILE/build.sh openeuler
ls -lh COMPILE/dist/openeuler/easyaiot-panel COMPILE/dist/openeuler/easyaiot-panel-*-*.oe2403.*.rpm

# 仅二进制 / 本机构建 / 换基础镜像
bash COMPILE/build.sh openeuler --no-rpm
bash COMPILE/build.sh openeuler --local
COMPILE_OPENEULER_BASE_IMAGE=openeuler/openeuler:24.03-lts-sp3 bash COMPILE/build.sh openeuler
```

安装与配置：

```bash
sudo rpm -Uvh ./COMPILE/dist/openeuler/easyaiot-panel-*-*.oe2403.*.rpm
sudoedit /etc/easyaiot-panel/panel.env
# EASYAIOT_ROOT=/path/to/easyaiot

sudo systemctl daemon-reload
sudo systemctl enable --now easyaiot-panel
# 浏览器：http://127.0.0.1:9200/
# 平台部署：sudo .scripts/docker/install_linux_openeuler.sh install
```

也可用统一入口：

```bash
bash COMPILE/install_linux.sh install openeuler
```

### 7) 已安装 deb 的热修 / 强制升级（可选）

部署脚本（如 `deploy_profile.sh`）修好后若不想整包重装，可把仓库改动同步进已装 runtime：

```bash
# 需 root；默认目标 /opt/easyaiot-panel/runtime
sudo bash COMPILE/hotfix_panel_runtime_deploy.sh
```

强制用最新 x86 deb 覆盖安装并重启：

```bash
sudo bash COMPILE/force_upgrade_panel.sh
```

### 8) 常见打包问题

| 现象 | 处理 |
|------|------|
| `EACCES` / `权限不够` 清理 `PANEL/ui/dist` 或 `COMPILE/work/ubuntu-docker-ctx` | 上次 Docker/`--output` 产物属主为 root。可用：`docker run --rm -v "$PWD/COMPILE/work:/w" -v "$PWD/PANEL/ui:/ui" alpine chown -R "$(id -u):$(id -g)" /w /ui/dist` |
| ARM/**麒麟(Kylin)** `docker build` 报 platform 不支持 | 确认 `docker buildx ls` 含 `linux/arm64`，并已安装 qemu-user-static / binfmt |
| `pack_deb.sh` 报缺 `dpkg-deb` | `sudo apt install -y dpkg-dev` |
| 图标阶段报缺 `PIL` | `python3 -m pip install pillow`（或退出会遮蔽系统 python 的 conda env） |
| 连续打多包版本号跳很多 | 正常：每个 deb/rpm 都会 `+1`；可用 `PANEL_VERSION=130` 固定某一包版本 |
| macOS 图标发白/方块 | 确认使用 `COMPILE/assets/panel-logo.png`；打包脚本会生成圆形白底再转 icns（`lib/make_circle_icon.py`） |
| macOS `hdiutil` / `iconutil` 失败 | 在本机 Terminal 执行（勿在沙箱/无 GUI 环境）；确认 Xcode CLT 可用 |

---

## macOS 打包（.dmg）

> 须在 **macOS 主机**执行。产物内置 `runtime/` + `install_mac.sh`（**仅镜像部署**，与桌面部署文档一致）。  
> 部署侧说明见 [.doc/部署文档/平台macOS部署文档_zh.md](../.doc/部署文档/平台macOS部署文档_zh.md)。

### 图标（与 Linux / Windows 一致）

| 项 | 说明 |
|----|------|
| 源文件 | `COMPILE/assets/panel-logo.png`（可用 `COMPILE_PANEL_LOGO=` 覆盖） |
| 算法 | `COMPILE/lib/make_circle_icon.py`：**圆形白底、外圈透明**（与 Ubuntu `pack_deb.sh` / Windows `build.sh` 同源） |
| 中间产物 | `COMPILE/dist/macos/panel-icon-circle.png` |
| App 图标 | `EasyAIoT Panel.app/Contents/Resources/panel.icns`（由圆形 PNG 经 `sips` + `iconutil` 生成） |

```bash
# 仅预览圆形图标
python3 COMPILE/lib/make_circle_icon.py \
  COMPILE/assets/panel-logo.png /tmp/panel-circle.png --size 512
open /tmp/panel-circle.png
```

### 构建命令

```bash
# 交互菜单也可选 macos → .app+.dmg
bash COMPILE/install_linux.sh

# 仅二进制 + runtime + run.command
bash COMPILE/build.sh macos

# .app（含 Resources/runtime + 圆形图标）
bash COMPILE/build.sh macos --app

# 安装包：.app + .dmg（含 Applications 快捷方式与 README）
bash COMPILE/build.sh macos --dmg
```

### 产物清单

| 路径 | 说明 |
|------|------|
| `COMPILE/dist/macos/easyaiot-panel` | 可执行文件 |
| `COMPILE/dist/macos/runtime/` | 内置部署树（含 `.scripts/docker/install_mac.sh`） |
| `COMPILE/dist/macos/panel.env` | 面板配置（`INSTALL_SCRIPT=install_mac.sh`） |
| `COMPILE/dist/macos/run.command` | 双击启动包装 |
| `COMPILE/dist/macos/EasyAIoT Panel.app` | macOS 应用包 |
| `COMPILE/dist/macos/easyaiot-panel-<VERSION>-arm64.dmg` | Apple Silicon（M 系列）安装包 |
| `COMPILE/dist/macos/easyaiot-panel-<VERSION>-amd64.dmg` | Intel Mac 安装包 |

安装：打开 dmg → 将 **EasyAIoT Panel** 拖到 **Applications** → 启动后访问 `http://127.0.0.1:9200/`，在面板「应用部署」中执行 `install`（需本机 Docker Desktop 已就绪）。

### 前置（macOS）

- Node.js + npm（编 `PANEL/ui`）
- Python 3.9+（建议 3.11+）与 venv；`pip install -r COMPILE/requirements-build.txt`（含 PyInstaller、Pillow）
- 系统工具：`sips`、`iconutil`、`hdiutil`（随 macOS / CLT）

---

## 目录

```
COMPILE/
  build.sh                      # 统一入口（含 centos-el{7,8,9} / centos-arm-el{7,8,9}）
  install_linux.sh              # 交互打包 + pack-all + windows/macos + install/uninstall/status
  interactive_pack.sh           # 被 install_linux.sh 默认调用的交互菜单
  hotfix_panel_runtime_deploy.sh
  force_upgrade_panel.sh
  lib/
    resolve_panel_version.sh    # 打包版本自动递增
    pack_desktop_runtime.sh     # deb / Windows / macOS 共用的 source-free runtime 打包
    make_circle_icon.py         # 圆形白底图标（Ubuntu/Windows/macOS 共用算法）
  assets/
    panel-logo.png              # 各平台共享图标源文件
  requirements-build.txt
  platforms/
    pack_all_linux.sh           # Ubuntu×3 deb + centos-el9 + centos-arm-el9 + openEuler
    ubuntu/
      Dockerfile
      panel.spec
      build.sh                  # --docker / --local / --deb / --arm / --kylin
      pack_deb.sh               # 打 .deb（内置 runtime）
      deb/                      # control、systemd、postinst、panel.env*
    windows/
      panel.spec
      build.sh                  # Windows：.exe + runtime + 可选 NSIS
      panel.env                 # INSTALL_SCRIPT=install_windows.sh
      installer.nsi
    macos/
      panel.spec
      build.sh                  # macOS：二进制 + runtime + 可选 .app/.dmg（圆形图标）
      panel.env                 # INSTALL_SCRIPT=install_mac.sh
    centos/
      el_common.sh              # el7/el8/el9 解析（centos 与 centos-arm 共用）
      Dockerfile                # ARG EL_RELEASE=7|8|9
      build.sh                  # --el7|--el8|--el9 [--docker|--local] [--rpm|--no-rpm]
      pack_rpm.sh               # 生成 *.elN.*.rpm（不含内置 runtime）
      rpm/                      # systemd/desktop/env 模板
    centos-arm/
      Dockerfile                # linux/arm64 + EL_RELEASE
      build.sh                  # --el7|--el8|--el9 [--docker|--local] [--rpm|--no-rpm]
      pack_rpm.sh               # 生成 aarch64 *.elN.*.rpm
      rpm/                      # INSTALL_SCRIPT=install_linux_centos_arm.sh
    openeuler/
      Dockerfile                # openEuler 24.03 容器标准化构建（默认）
      build.sh                  # --docker / --local / --rpm / --no-rpm
      pack_rpm.sh               # 生成 .rpm（不含内置 runtime）
      rpm/                      # systemd/desktop/env 模板
  dist/ubuntu/                  # x86/amd64 产物（gitignore）
  dist/ubuntu-arm/              # arm64 产物（gitignore）
  dist/ubuntu-kylin/            # 麒麟 产物（gitignore）
  dist/centos-el{7,8,9}/        # CentOS x86 按 EL 分目录
  dist/centos-arm-el{7,8,9}/    # CentOS ARM 按 EL 分目录
  dist/openeuler/               # openEuler 二进制 + rpm（gitignore）
  dist/windows/                 # Windows 产物（gitignore）
  dist/macos/                   # macOS 产物（gitignore）
```

## 版本号

每次执行 deb / rpm / Windows 安装包 / macOS dmg 打包时，版本号会自动 +1：
- 状态文件：`COMPILE/.panel-version`（gitignore）
- 也可扫描 `COMPILE/dist/**` 已有包名推断当前最大值
- 固定版本：`PANEL_VERSION=105 bash COMPILE/build.sh ubuntu-x86 --deb`
- 起始基数：`PANEL_VERSION_BASE`（默认 `100`）
- 一次打完 Ubuntu 三架构 + centos-el9 + centos-arm-el9 + **欧拉(openEuler)** 会连续占用多个版本号；单独打 el7/el8 也会各占一个版本号

## 构建方式

| 模式 | 命令 | 说明 |
|------|------|------|
| Docker（默认） | `bash COMPILE/build.sh ubuntu-x86 / ubuntu-arm / ubuntu-kylin` | 输出对应架构 Linux 可执行文件（ARM/Kylin 使用 `linux/arm64` 构建） |
| 本地 | `bash COMPILE/build.sh <target> --local` | 需在对应架构机器上执行（本机 Node + Python3） |
| deb | `bash COMPILE/build.sh <target> --deb` | 产出对应 variant 的 `.deb`（含内置 runtime；x86/amd64、arm_arm64、kylin_arm64） |
| windows | `bash COMPILE/build.sh windows [--installer]` | 需在 Windows 主机执行；默认 `.exe`+`runtime/`，可选 NSIS |
| macos | `bash COMPILE/build.sh macos [--app|--dmg]` | 需在 macOS 主机执行；默认二进制+`runtime/`，可选 `.app`/`.dmg` |
| centos-el9 | `bash COMPILE/build.sh centos-el9`（`centos` 同义） | Docker / stream9 → `dist/centos-el9/*.el9.*.rpm` |
| centos-el8 | `bash COMPILE/build.sh centos-el8` | Docker / stream8 → `dist/centos-el8/*.el8.*.rpm` |
| centos-el7 | `bash COMPILE/build.sh centos-el7` | Docker / centos:7 + Python3.8 → `dist/centos-el7/*.el7.*.rpm` |
| centos-arm-el9 | `bash COMPILE/build.sh centos-arm-el9`（`centos-arm` 同义） | Docker `linux/arm64` → `dist/centos-arm-el9/*.el9.aarch64.rpm` |
| centos-arm-el8/el7 | `bash COMPILE/build.sh centos-arm-el8` / `centos-arm-el7` | 同上交叉构建，产物分目录 |
| openeuler | `bash COMPILE/build.sh openeuler [--docker|--local] [--no-rpm]` | 默认 Docker 产出二进制 + `.rpm`（无内置 runtime；基础镜像 `openeuler/openeuler:24.03`） |
| all-linux | `bash COMPILE/build.sh all-linux` / `bash COMPILE/install_linux.sh pack-all` | Ubuntu×3 deb + centos-el{7,8,9} x86/arm + openEuler |

## 运行时依赖

可执行文件已内嵌 Python 运行时、Flask 依赖与 `ui/dist` 前端，但业务能力仍依赖宿主机：

- **Docker CLI**（`docker` / `docker compose`）与 Docker Engine（Linux sock / Desktop）
- **EasyAIoT runtime 根**（`EASYAIOT_ROOT`）
  - Ubuntu deb 默认：`/opt/easyaiot-panel/runtime` → 按包变体使用 `install_linux.sh` / `install_linux_arm.sh` / `install_linux_kylin.sh`
  - Windows / macOS 安装包：与二进制同级的 `runtime/` → `install_windows.sh` / `install_mac.sh`
  - CentOS rpm：默认 `/opt/easyaiot`（占位），**须改为**本机仓库根 → 使用 `.scripts/docker/install_linux_centos.sh`
  - CentOS ARM rpm：同上 → 使用 `.scripts/docker/install_linux_centos_arm.sh`（panel.env 已默认写入）
  - **欧拉(openEuler)** rpm：同上 → 使用 `.scripts/docker/install_linux_openeuler.sh`
  - 也可把任意平台的 `EASYAIOT_ROOT` 指到本机 clone 的仓库根

| 平台 | `INSTALL_SCRIPT` | 本地 build（源码编译业务镜像） |
|------|------------------|-------------------------------|
| Ubuntu x86 | `install_linux.sh` | 支持 |
| Ubuntu ARM | `install_linux_arm.sh` | 支持 |
| **麒麟(Kylin)** ARM | `install_linux_kylin.sh` | 支持 |
| **欧拉(openEuler)** | `install_linux_openeuler.sh`（需仓库根） | 支持 |
| CentOS/RHEL x86 | `install_linux_centos.sh`（需仓库根） | 支持 |
| CentOS/RHEL ARM | `install_linux_centos_arm.sh`（需仓库根） | 支持 |
| macOS | `install_mac.sh` | **禁止**（仅镜像） |
| Windows | `install_windows.sh` | **禁止**（仅镜像；需 Git Bash） |

deb / rpm 安装后配置在 `/etc/easyaiot-panel/panel.env`；Windows/macOS 配置为安装目录下的 `panel.env`。

## 说明

- Windows/macOS 须在对应系统本机或对应 CI Runner 执行；Ubuntu / CentOS / **麒麟(Kylin) / 欧拉(openEuler)** 均可在任意已装 Docker 的 Linux 上交叉/标准化构建（ARM 需 qemu）。
- 已提供 GitHub Actions 模板：`.github/workflows/compile-packaging.yml`（Ubuntu deb、Windows、macOS；CentOS / **欧拉(openEuler)** 为可选开关）。
