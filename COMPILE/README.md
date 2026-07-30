# EasyAIoT COMPILE

把 `PANEL`（及其他模块，后续扩展）编译打包为各平台可执行文件 / 安装包。

当前已实现：
- **Ubuntu 单文件** `easyaiot-panel` + **内置 runtime** `.deb`（`install_linux*.sh`）
- **交互式打包菜单** `COMPILE/install_linux.sh`
- **Windows** `easyaiot-panel.exe` + **内置 runtime**（`install_windows.sh` 仅镜像部署）+ 可选 NSIS
- **macOS** `easyaiot-panel` + **内置 runtime**（`install_mac.sh` 仅镜像部署）+ 可选 `.app` / `.dmg`
- **CentOS/RHEL** `easyaiot-panel` + `.rpm`

## 快速开始

> **Ubuntu Docker 打包已加速：** 默认先在宿主机 `npm run build`，容器内只做 PyInstaller；
> 构建上下文只含 PANEL 必要文件（约数 MB），不再把整个仓库塞进 dockerd，也不再在容器里跑 `npm install`（以前常卡 400s+）。

```bash
# 统一入口（交互菜单：部署操作 / 安装操作）
bash COMPILE/install_linux.sh

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

# Windows（需在 Windows 主机执行；产物含 runtime/ + install_windows.sh）
bash COMPILE/build.sh windows
ls -lh COMPILE/dist/windows/easyaiot-panel.exe
ls -ld COMPILE/dist/windows/runtime
ls -lh COMPILE/dist/windows/panel.env COMPILE/dist/windows/run.bat
# 可选安装包（需 NSIS / makensis；会打入 runtime）
bash COMPILE/build.sh windows --installer
# 运行：
# COMPILE\dist\windows\run.bat
# 然后在 PANEL「应用部署」执行 install（仅拉取预构建镜像）

# macOS（需在 macOS 主机执行；产物含 runtime/ + install_mac.sh）
bash COMPILE/build.sh macos
ls -lh COMPILE/dist/macos/easyaiot-panel
ls -ld COMPILE/dist/macos/runtime
ls -lh COMPILE/dist/macos/panel.env COMPILE/dist/macos/run.command
# 可选 .app / .dmg（.app 内含 Resources/runtime）
bash COMPILE/build.sh macos --app
bash COMPILE/build.sh macos --dmg
# 运行：
# ./COMPILE/dist/macos/run.command

# CentOS/RHEL（需在对应主机执行）
bash COMPILE/build.sh centos
ls -lh COMPILE/dist/centos/easyaiot-panel COMPILE/dist/centos/*.rpm
# 安装 RPM：
# sudo rpm -ivh COMPILE/dist/centos/easyaiot-panel-*.rpm
# sudo systemctl daemon-reload
# sudo systemctl enable --now easyaiot-panel
#
# 配置仓库根路径：
# sudoedit /etc/easyaiot-panel/panel.env
# EASYAIOT_ROOT=/path/to/easyaiot

# 安装/卸载管理（自动识别 deb/rpm）
bash COMPILE/install_linux.sh install auto
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
chmod +x COMPILE/build.sh COMPILE/platforms/ubuntu/build.sh COMPILE/platforms/ubuntu/pack_deb.sh

# 版本号在每次打包时自动递增（也可 PANEL_VERSION=105 固定指定）
# 状态文件：COMPILE/.panel-version（gitignore，也可由 dist 已有包推断）
```

如果要打 `.deb`：请确保“当前 shell 的 `python3`”能导入 `Pillow`（模块名 `PIL`）。
`pack_deb.sh` 生成桌面图标时会用到这一点；若你在 `conda(base)` 里打包，可能需要 `deactivate` 或在当前 conda 环境安装 `pillow`（`python3 -m pip install pillow`）。

## 前置依赖提示（按目标）
- Windows/macOS：建议在对应 OS 本机执行，需本机具备 `Node.js + npm`、Python 3.11+。
- CentOS/RHEL：需 `rpm-build`（提供 `rpmbuild`），同样需要 `Node.js + npm`、Python 3.11+。

如果要走 Docker 构建（默认方式），还需要确认 Docker 可用：

```bash
docker --version
docker compose version
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
```

预期产物示例（`<VERSION>` 为自动递增的数字版本）：

- x86/amd64：`COMPILE/dist/ubuntu/easyaiot-panel_<VERSION>_amd64.deb`
- ARM64：`COMPILE/dist/ubuntu-arm/easyaiot-panel_<VERSION>_arm_arm64.deb`
- 麒麟：`COMPILE/dist/ubuntu-kylin/easyaiot-panel_<VERSION>_kylin_arm64.deb`

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

## 目录

```
COMPILE/
  build.sh                      # 统一入口
  lib/
    resolve_panel_version.sh    # 打包版本自动递增
  assets/
    panel-logo.png              # 各平台共享图标源文件
  requirements-build.txt
  platforms/                     # 指向原 targets（构建平台脚本）
    ubuntu/
      Dockerfile
      panel.spec
      build.sh                  # --docker / --local / --deb
      pack_deb.sh               # 打 .deb
      deb/                      # control、systemd、postinst…
    windows/
      panel.spec
      build.sh                  # Windows：.exe + runtime + 可选 NSIS
      panel.env                 # INSTALL_SCRIPT=install_windows.sh
      installer.nsi
    macos/
      panel.spec
      build.sh                  # macOS：二进制 + runtime + 可选 .app/.dmg
      panel.env                 # INSTALL_SCRIPT=install_mac.sh
    centos/
      build.sh                  # CentOS/RHEL 本地构建二进制
      pack_rpm.sh               # 生成 .rpm
      rpm/                      # systemd/desktop/env 模板
  dist/ubuntu/                  # x86/amd64 产物（gitignore）
  dist/ubuntu-arm/              # arm64 产物（gitignore）
  dist/ubuntu-kylin/            # 麒麟 产物（gitignore）
```

## 版本号

每次执行 deb / rpm / Windows 安装包 / macOS dmg 打包时，版本号会自动 +1：
- 状态文件：`COMPILE/.panel-version`（gitignore）
- 也可扫描 `COMPILE/dist/**` 已有包名推断当前最大值
- 固定版本：`PANEL_VERSION=105 bash COMPILE/build.sh ubuntu-x86 --deb`
- 起始基数：`PANEL_VERSION_BASE`（默认 `100`）

## 构建方式

| 模式 | 命令 | 说明 |
|------|------|------|
| Docker（默认） | `bash COMPILE/build.sh ubuntu-x86 / ubuntu-arm / ubuntu-kylin` | 输出对应架构 Linux 可执行文件（ARM/Kylin 使用 `linux/arm64` 构建） |
| 本地 | `bash COMPILE/build.sh <target> --local` | 需在对应架构机器上执行（本机 Node + Python3） |
| deb | `bash COMPILE/build.sh <target> --deb` | 产出对应 variant 的 `.deb`（x86/amd64、arm_arm64、kylin_arm64） |
| windows | `bash COMPILE/build.sh windows` | 需在 Windows 主机执行，产出 `.exe` |
| macos | `bash COMPILE/build.sh macos` | 需在 macOS 主机执行，产出 macOS 可执行文件 |
| centos | `bash COMPILE/build.sh centos [--docker|--local] [--no-rpm]` | CentOS/RHEL 本地或容器标准化构建；默认产出二进制 + `.rpm` |

## 运行时依赖

可执行文件已内嵌 Python 运行时、Flask 依赖与 `ui/dist` 前端，但业务能力仍依赖宿主机：

- **Docker CLI**（`docker` / `docker compose`）与 Docker Engine（Linux sock / Desktop）
- **EasyAIoT runtime 根**（`EASYAIOT_ROOT`）
  - Ubuntu deb 默认：`/opt/easyaiot-panel/runtime` → `install_linux*.sh`
  - Windows / macOS 安装包：与二进制同级的 `runtime/` → `install_windows.sh` / `install_mac.sh`
  - 也可指向本机 clone 的仓库根

| 平台 | `INSTALL_SCRIPT` | 本地 build |
|------|------------------|------------|
| Linux | `install_linux.sh`（arm/kylin 变体） | 支持 |
| macOS | `install_mac.sh` | **禁止**（仅镜像） |
| Windows | `install_windows.sh` | **禁止**（仅镜像；需 Git Bash） |

deb 安装后配置在 `/etc/easyaiot-panel/panel.env`；Windows/macOS 配置为安装目录下的 `panel.env`。

## 说明

- Windows/macOS 建议在对应系统本机或对应 CI Runner 执行；CentOS 已支持容器标准化构建。
- 已提供 GitHub Actions 模板：`.github/workflows/compile-packaging.yml`（支持多平台与可选开关）。
