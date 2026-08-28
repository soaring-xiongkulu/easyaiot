# EasyAIoT（云边端一体化智能算法应用平台）

[![Gitee star](https://gitee.com/volara/easyaiot/badge/star.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/stargazers)
[![Gitee fork](https://gitee.com/volara/easyaiot/badge/fork.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/members)

<p style="font-size: 16px; line-height: 1.8; color: #555; font-weight: 400; margin: 20px 0;">
我希望全世界都能使用这个系统，实现AI的真正0门槛，人人都能体验到AI带来的好处，而并不只是掌握在少数人手里。
</p>

<div align="center">
    <img src=".image/logo.png" width="30%" height="30%" alt="EasyAIoT">
</div>

<h4 align="center" style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; padding: 20px; font-weight: bold;">
  <a href="./README.md">English</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_zh.md">简体中文</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_zh_tw.md">繁體中文</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_ru.md">Русский</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_fr.md">Français</a>
  <span style="display: flex; align-items: center; color: #666; font-weight: bold;">|</span>
  <a href="./README_ko.md">한국어</a>
</h4>

## 🌐 官方网站

EasyAIoT 官方网站：[http://36.111.47.113:8090/](http://36.111.47.113:8090/)

提供产品介绍、特性说明、四档硬件选型、安装包下载与文档入口，便于快速了解平台价值并开始落地。

## 📖 项目介绍

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
<strong>EasyAIoT</strong>（Easy AI Internet of Things）是一款<strong>云边端一体化的智能算法应用平台</strong>，专注于将人工智能与物联网深度融合，让摄像头、传感器与边缘算力在现场即可协同运转——从设备接入、数据采集，到实时视觉分析、智能研判与告警联动，全链路在一套软件中贯通完成。
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
许多智能物联网项目落地时面临同一困境：视频系统、设备平台、算法服务各自为政，集成成本高、运维割裂、扩容困难。<strong>EasyAIoT 用一套平台化解这一矛盾</strong>——同一套软件既可部署在 <strong>2 GB</strong> 边缘单机（edge）上先跑通智能闭环，也可落在 4～8 GB 边缘盒子（mini）实现单点智能，还可搭载于 AI 一体摄像头完成楼面级覆盖，或装进企业级全栈一体机，一箱配齐 IoT 纳管、海量视频接入与 AI 分析研判，不必维护多套版本、不必反复对接异构系统。
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
平台由 <strong>WEB、APP、DEVICE、EDGE、SENTINEL、VIDEO、RTC、AI、RUNTIME、POST、VISUALIZE、TRANSFORM、PANEL、IDEA、HARNESS、SITE</strong> 等核心模块组成，并以 <strong>COMPILE</strong> 承接多平台打包交付（含 Ubuntu / CentOS·RHEL <strong>7～9</strong>（x86 + <strong>CentOS ARM</strong>，按 el7/el8/el9 分包） / <strong>麒麟(Kylin) / 欧拉(openEuler)</strong> / Windows / macOS / ARM）。在能力侧，平台覆盖 GB28181 / ONVIF 多协议摄像头接入、<strong>RTC 消费级摄像头 P2P 桥接</strong>（基于 go2rtc，覆盖 <strong>Tapo、Tuya、Ring、Nest、小米、Wyze、DoorBird、GoPro、Roborock</strong> 九大品牌——门店 Tapo 补盲、涂鸦白牌纳管、海外 Ring/Nest 门铃、米家存量利旧、Wyze 低成本扩点、DoorBird 门口对讲、GoPro 机动机位、石头扫地机移动视角等场景，Web 一键接入并纳入统一视频与 AI 研判闭环）、<strong>大疆机场与无人机空中视角接入</strong>、实时 / 抓拍 / 巡检算法任务、<strong>RUNTIME 原生高速执行层</strong>（编译型二进制承接拉流解码、YOLO 推理、带框推流与多路原画转发——相对解释型链路更低 CPU/内存、更稳时延；同一二进制覆盖实时 / 抓拍 / 巡检 / 转发）、YOLO 目标检测与 SAM 零样本自动标注、人脸/车牌识别、<strong>POST 定制研判</strong>（检出之后按现场规则过滤、复合判断再告警，改规则不必重训模型）、联邦算力集群调度、<strong>SENTINEL 集群节点哨兵</strong>（按业务摸清节点就绪与可调度能力，缺件可自助补齐，任务按真能力下发），以及 <strong>无限联邦边缘集群模式</strong>（普通开发板可即开即用、现场智能就地决策、告警与证据自动汇聚上云，算力随业务任意铺开），还有 MQTT / TCP / HTTP / Modbus-TCP / Modbus-RTU / OPC UA 物联网设备全生命周期管理，并由 <strong>EDGE C# 边缘采集运行时</strong>在现场以插件化采集器承接 Modbus RTU/TCP、OPC UA 等工业协议采集、本地调度与 MQTT 云边对接，以及<strong>可视化大屏与 Web 工艺组态</strong>，让设备数据既能展成指挥态势、也能落回工艺画面；并新增 <strong>POST 定制研判服务</strong>，把检测结果锻造成可贴现场的业务事件，误报少、规则可配、上线可先试跑；配套 <strong>TRANSFORM 多向数据流转引擎</strong>，把平台侧业务事件按约定投递到 MES / ERP / CRM / WMS 等外部系统，多方对接可配、可追、可复用；配套 <strong>PANEL 交付与值守入口</strong>，让一体机到场当天可装可验，值守与排障不必事事等开发远程敲命令；另以 <strong>SITE 官方网站</strong>对外呈现产品价值、四档硬件选型与安装包入口，让访客先看懂再下载、先选型再落地；并以 <strong>IDEA 社区贡献在线 IDE</strong> 让贡献者浏览器即可打开全仓、用 GitHub Copilot 共创、按改动发布到本机并提交 PR，把开源共建从「先配环境」变成「打开即改」。在体验侧，Web 管控台与移动 App / 小程序能力对齐，让指挥中心与现场巡检同一套业务逻辑、随时随地处置；并新增 <strong>ANDROID / IOS / HARMONYOS 三端壳打包工程</strong>，把这一移动体验以 APK / IPA / HAP 安装包形态覆盖到主流手机系统，一套前端、一键出包、版本统一管理。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>一句话概括：</strong>EasyAIoT = AI + IoT，让万物互联的同时实现万物智视、万物智控。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
📄 如需更完整的图文介绍，请参阅 <a href=".doc/项目介绍/EasyAIoT项目介绍 V2.0.pptx" style="color: #3498db; text-decoration: none; font-weight: 600;">EasyAIoT项目介绍 V2.0（PPT）</a>，以及 <a href=".doc/项目介绍/AI视频监控分析平台.pdf" style="color: #3498db; text-decoration: none; font-weight: 600;">AI视频监控分析平台（PDF）</a>。部署完成后的业务操作见 <a href=".doc/操作手册/README.md" style="color: #3498db; text-decoration: none; font-weight: 600;">平台操作手册</a>。
</p>

### 🏆 资质证书

| | | | |
|:---:|:---:|:---:|:---:|
| <img src=".image/certificates/gitee-oss-award-2025-top1.jpg" width="200" alt="Gitee 2025年度开源项目 · 工业软件赛道 Top1"> | <img src=".image/certificates/gitee-2000-stars.jpg" width="200" alt="Gitee 2000+ Stars"> | <img src=".image/certificates/gitee-gvp-2025.jpg" width="200" alt="Gitee GVP 2025 · 最有价值开源项目"> | <img src=".image/certificates/csdn-blog-expert.jpg" width="200" alt="CSDN 博客专家"> |

## 🚀 快速开始

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
打开 README 心里嘀咕：「我这破机器……装得动吗？」——<strong>能。先别怂。</strong>
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
最轻一档，容器总占用大约就 <strong>1 GB</strong>。摄像头接入、实时分析、智能告警，小机器也能闭环——旧笔记本先爽一把，上瘾了再升档也不迟。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>三步上车（Linux 示例）：</strong>
</p>

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# 方式 A（推荐）
EASYAIOT_DEPLOY_PROFILE=edge sudo bash .scripts/docker/install_linux.sh install

# 方式 B
# sudo bash .scripts/docker/install_linux.sh edge install
```

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0;">
装完浏览器打开 <code>https://&lt;服务器IP&gt;:8888</code>，默认账号 <code>admin</code> / <code>admin123</code>。验证一把：
</p>

```bash
.scripts/docker/install_linux.sh verify
# 可选：再瞄一眼内存是否还在规格内
.scripts/docker/install_linux.sh resources
```

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0;">
绿灯齐了就收工——比你想的轻松，今天可以提前喝杯咖啡了。
</p>

## 🌟 关于项目的一些思考

### 📍 项目定位

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT是一个云边端一体化的智能物联网平台，专注于AI与IoT的深度融合。平台通过算法任务管理、实时流分析、模型服务集群推理等核心能力，实现从设备接入到数据采集、AI分析、智能决策的全链路闭环，真正实现万物互联、万物智控。
</p>

### 🎛️ PANEL：一体机到场当天可装可验，值守不必等开发远程

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
智能物联网项目最容易卡在「最后一公里」：机器到了现场，却<strong>装不起来、验不出去、出了故障只能等开发远程敲命令</strong>，驻场成本与验收周期都被人拖住。PANEL 是面向集成商与现场运维的<strong>独立交付与值守入口</strong>——按档位一键装机、看清整机健康与依赖、启停服务与查日志当场办完；<strong>业务管控台尚未就绪时，也能先把整机拉起来、守住、交出去</strong>，把「机器到场 → 平台可用 → 可验收」从等人变成当天可闭环。
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>缩短验收周期</strong>：到场按 edge / mini / standard / full 选一档即可装机，进度与结果当场可见，少因命令记不全、步骤漏一步导致「装一半不知卡在哪」，PoC 与正式交付都能更快过验收</li>
  <li><strong>降低驻场与远程成本</strong>：容器是否在跑、资源是否吃紧、日志卡在哪一目了然，重启、清缓存、拉镜像不必先翻文档再等开发支援，值守人员可自助处置常见故障</li>
  <li><strong>多项目一套口径</strong>：同一套装机与运维入口可复用到多台一体机、多处机房，交付、值守、交接口径一致，避免「每台现场各一套口口相传」</li>
</ul>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
📦 <strong>安装包下载</strong>：Ubuntu / Debian、CentOS / RHEL <strong>7～9</strong>（x86 + <strong>CentOS ARM</strong>，对应 el7/el8/el9 RPM）、Windows、macOS 及 ARM / <strong>麒麟(Kylin) / 欧拉(openEuler)</strong>等目标安装包见 <a href="https://gitee.com/volara/easyaiot/releases" style="color: #3498db; text-decoration: none; font-weight: 600;">Gitee Releases</a>。
</p>

| | | |
|:---:|:---:|:---:|
| ![系统概览](.image/banner/panel/panel_1000.png) | ![容器管理](.image/banner/panel/panel_1001.png) | ![容器日志](.image/banner/panel/panel_1002.png) |
| ![一键部署](.image/banner/panel/panel_1003.png) | ![镜像就绪](.image/banner/panel/panel_1004.png) | ![镜像拉取](.image/banner/panel/panel_1005.png) |
| ![系统诊断](.image/banner/panel/panel_1006.png) | ![系统维护](.image/banner/panel/panel_1007.png) | ![服务拓扑](.image/banner/panel/panel_1008.png) |

### 📡 RTC：消费级摄像头 P2P 桥接，让「没有 RTSP」的设备也能进平台

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
家庭、门店与轻量安防场景里，大量已在用的设备来自 <strong>Tapo、涂鸦、Ring、Nest、小米、Wyze、DoorBird、GoPro、Roborock</strong> 等品牌——它们普遍走厂商私有 P2P 协议，<strong>原生不提供标准 RTSP</strong>，传统视频监控平台往往只能劝用户另搭 Micam、Home Assistant 等中间件，接入链路长、运维割裂、AI 研判接不进来。EasyAIoT 新增独立 <strong>RTC 模块</strong>，基于开源项目 <a href="https://github.com/AlexxIT/go2rtc" style="color: #3498db; text-decoration: none; font-weight: 600;">go2rtc</a>，<strong>一次打通上述九大品牌的取流与对讲能力</strong>，把 P2P 桥接与平台编排收成一体——消费级设备也能像国标/ONVIF 摄像头一样，<strong>注册、预览、推流转发、挂 AI 任务、告警联动</strong>全链路打通。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
<strong>已覆盖品牌与典型价值场景：</strong>
</p>

<table style="width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px;">
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 14%;">品牌</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 18%;">厂商 / 生态</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 28%;">典型设备</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">落地价值</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Tapo</strong></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;">TP-Link</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;">家用 IPC、室内/室外枪机、球机</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">门店、出租屋、小微店铺<strong>低成本补盲</strong>；云密码直连，支持<strong>双向对讲</strong>，无需折腾 RTSP 密码</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Tuya</strong></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;">涂鸦智能</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;">涂鸦生态 IPC、门铃、室内机</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;"><strong>海量白牌/OEM 摄像头</strong>一次纳管；出海与国内涂鸦系设备统一接入，减少「一品牌一套对接」</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Ring</strong></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;">Amazon</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;">门铃、室外机、Spotlight Cam</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">海外社区、跨境电商仓<strong>门铃监控入平台</strong>；账号绑定后本地 P2P 取流，支持<strong>远程对讲</strong></td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Nest</strong></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;">Google</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;">Nest Cam、Doorbell</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">高端住宅、涉外项目<strong>Google 生态门铃/摄像头</strong>纳入统一值守，与专业摄像机同屏研判</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>小米</strong></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;">米家 / Mi Home</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;">米家摄像机、智能门铃、室外机</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">国内家庭与连锁门店<strong>存量米家设备利旧</strong>；免 Micam 中间件，直连平台挂 AI 分析</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Wyze</strong></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;">Wyze</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;">Wyze Cam v3/v4、门铃、室外机</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;"><strong>极致性价比摄像头</strong>批量入平台；本地 P2P、支持<strong>双向对讲</strong>，适合试点与广域补点</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>DoorBird</strong></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;">DoorBird</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;">智能门铃、门口机</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">别墅、高端社区<strong>门口可视对讲</strong>与平台告警联动；MJPEG/音频/对讲一体桥接</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>GoPro</strong></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;">GoPro</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;">HERO9–12（USB / Wi-Fi）</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">巡检、应急、运动视角<strong>机动机位</strong>；临时机位快速入流，适合勘察与现场记录</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>Roborock</strong></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top;">石头科技</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;">S6/S7/Qrevo MaxV 等带摄像头扫地机</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;"><strong>移动视角补盲</strong>——家具底部、床底等固定摄像头看不到的区域；部分型号支持<strong>双向对讲</strong></td>
</tr>
</table>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Web 一键接入</strong>：管控台「接入 RTC 摄像头」入口，按品牌动态表单填参；Ring / Nest / 小米 / Wyze / Roborock 等 OAuth 类平台经 go2rtc WebUI 完成账号绑定后，复制源流 URL 即可登记</li>
  <li><strong>全链路已打通</strong>：WEB 注册 → VIDEO <code>/register/device/rtc-live</code> → RTC 管理 API → go2rtc P2P 取流 → 标准 RTSP 输出 → SRS 推流转发 → Jessibuca 播放与 AI 分析，<strong>九大品牌同一套流程</strong>，无需额外中间件</li>
  <li><strong>双向对讲</strong>：Tapo、Tuya、Ring、Wyze、DoorBird、Roborock 支持 go2rtc 双向音频，门铃对讲、远程喊话与告警联动可扩展</li>
  <li><strong>生命周期联动</strong>：设备删除时自动清理 go2rtc 流配置；与设备目录、地图布点、算法任务体系无缝衔接</li>
  <li><strong>Docker 一体化部署</strong>：<code>bash RTC/install_linux.sh start</code> 即可启动 go2rtc + Python 管理服务，默认 host 网络适配 P2P 局域网直连</li>
</ul>

### 🔌 EDGE：C# 边缘采集运行时，让工业现场「采得准、上得去」

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
工控与楼宇现场常见「PLC、电表、传感器挂在 RS-485 或以太网侧，云平台却要另配一套数采软件、协议各写各的、配置改一次要派人到现场」——接入链路长、运维割裂、云边对不上口径。EasyAIoT 新增独立 <strong>EDGE 模块</strong>（C#），作为<strong>可独立部署的边缘采集运行时</strong>：多协议采集器插件、本地调度、配置驱动解析、MQTT 对接 EasyAIoT 云平台，把 Modbus RTU/TCP、OPC UA 等现场测点收成统一物模型上行，云端配置下发与属性写值也能直达边缘执行。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0;">
<strong>与设备管理「网关」的区别：</strong>设备管理里的网关是云上的产品/设备类型（GATEWAY + 子设备 SUBSET 拓扑），负责建档、影子、绑定与下发；EDGE 没有单独设备页面，而是现场去<strong>当这台网关</strong>的采集进程——采上来的数落在同一套设备管理里。另有一条路径是 iot-sink <strong>在云端直接轮询</strong> Modbus/OPC UA（平台须能访问现场设备）；EDGE 则在现场采完只走 MQTT 上云，适合 OT 隔离与 RS-485。当前已对齐网关属性上下行、子设备属性代报与配置下发，可作为现场工业网关使用；拓扑主动申报、子设备事件/服务透传、OTA 等完整网关协议面仍在演进。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
<strong>为何选用 C# 做边缘物联网采集？</strong>
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>工业现场亲和</strong>：C# 在工控、SCADA、上位机领域生态成熟，Modbus、OPC UA、串口通信等协议库与工程实践丰富，集成商与自动化工程师上手成本低</li>
  <li><strong>强类型 + 结构化工程</strong>：测点映射、寄存器解析、配置校验在编译期即可发现错误，长期维护多协议采集器时比脚本语言更稳、更可测</li>
  <li><strong>异步并发不阻塞</strong>：<code>async/await</code> 天然适合多设备轮询、串口/网络 I/O 并发——同一网关可同时调度数十路子设备采集，避免 Python GIL 等解释型链路在高频轮询下的吞吐瓶颈</li>
  <li><strong>长驻服务稳定</strong>：.NET 运行时适合边缘网关 7×24 常驻进程，内存与 GC 行为可预期，配合依赖注入与插件化架构，采集器热插拔、版本迭代不必重启整站</li>
  <li><strong>跨平台可交付</strong>：同一套 C# 源码可发布至 Linux x86_64 / ARM64 工控机与边缘盒子，单文件/自包含部署，现场装机不必再配 Python 虚拟环境或 JVM</li>
  <li><strong>与云平台分工清晰</strong>：边缘侧专注「采、解、发」，DEVICE 侧专注物模型与设备生命周期——C# 不承担平台重业务与 AI 推理，资源占用更轻，适合挂在 RS-485 总线侧或弱算力网关上独立运行</li>
</ul>

<table style="width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px;">
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 18%;">采集器</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">协议 / 场景</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;"><code>modbus-rtu</code></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">Modbus RTU（RS485/串口）——电表、仪表、PLC 等总线侧设备</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;"><code>modbus-tcp</code></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">Modbus TCP——以太网侧工控设备、变频器、网关</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;"><code>opc-ua</code></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">OPC UA——现代化工控与上位系统互联</td>
</tr>
</table>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>插件化采集架构</strong>：实现 <code>ICollector</code> 即可扩展新协议；Host 统一注册、调度与结果上报，采集逻辑与运行时解耦</li>
  <li><strong>配置双通道</strong>：本地 <code>device-jobs.json</code> 可离线运行；云端 MQTT <code>config/downstream/push</code> 可远程覆盖采集任务，现场改配置不必再派人</li>
  <li><strong>MQTT 云边一体</strong>：以平台 GATEWAY 身份接入——网关属性上报、子设备属性代报、云端属性写值下行，经 EMQX 对接 DEVICE/<strong>iot-sink</strong>，子设备自动创建与影子入库，数据在「设备管理」展现</li>
  <li><strong>独立打包交付</strong>：<code>pack_linux.sh</code> 产出 x86_64 / ARM64 Linux 部署包，可装于工控机、边缘网关，与平台主栈解耦部署</li>
  <li><strong>E2E 联调开箱即用</strong>：<code>bash EDGE/demo/run_e2e.sh</code> 一键验证采集 → MQTT 上行 → 云端入库全链路</li>
</ul>

### 🛰️ SENTINEL：集群节点哨兵，让「纳管即就绪、调度按真能力」

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
联邦扩容最怕「机器加进来了，却不知道能不能接活」——视频分析、推流转发、模型训练各要不同就绪条件，任务派下去才发现环境缺件，现场反复登机装依赖，验收卡在「装完跑不起来」。EasyAIoT 新增独立 <strong>SENTINEL 模块</strong>，作为跟着每台调度节点走的<strong>业务就绪哨兵</strong>：按勾选业务持续摸清本机是否真正可接活，把可调度能力汇聚到管控台；缺件时可自动请求环境补齐，让运维少登机、任务少踩坑、扩容交付当天就能验收。
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>按业务认能力</strong>：视频分析、推流转发、直播接入、模型训练、大模型、智能标注等——勾什么业务，就盯什么就绪度，不再按角色猜「这台机器大概能干啥」</li>
  <li><strong>纳管即监测</strong>：节点纳入平台后自动拉起哨兵巡检，扩容当天就能看见「能不能接活」，缩短「加机器—等联调—才发现不能用」的空窗</li>
  <li><strong>真能力驱动调度</strong>：只有环境真正就绪的节点进入可调度池，减少「派了跑不起来」的返工与客诉</li>
  <li><strong>缺件自助补齐</strong>：期望环境缺失时可自动请求平台补齐，把现场手工装机压缩成平台侧闭环，值守少登服务器</li>
  <li><strong>断网也能扩</strong>：无公网或受限网络现场可离线纳管与环境同步，边端扩容不被外网卡住</li>
  <li><strong>管控台一眼可验</strong>：组件健康与可调度功能同屏可见，验收与排障少猜、少翻机器，交付口径统一</li>
</ul>

### 🧭 POST：定制研判，让「检出」变成可运营的业务事件

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
视觉项目最容易卡在「模型已经框出人/车/物，告警却用不起来」——区域外路过也报、正常作业也报、客户要的是越线、滞留、人数超限，却只能反复改模型、停任务、等开发改代码。EasyAIoT 新增独立 <strong>POST 定制研判服务</strong>，把<strong>画面感知</strong>与<strong>业务判断</strong>拆开：检测继续专心「看见」，研判按任务编排「该不该报、报什么」——规则改了不必重训模型，分析画面也不必跟着停，让告警真正贴工地、园区、交通与厂区的管理口径。
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>按任务编排研判</strong>：每个算法任务可独立配置后处理步骤，默认先按检测区域过滤、再进入标准告警；也可插入业务脚本或行业插件，把人数统计、越线通行、停留超时、区域滞留、多条件复合告警配成可贴现场的规则链，同类场景一次配好、多任务复用</li>
  <li><strong>只报业务关心的范围</strong>：与设备「区域检测」联动，区域外目标自动滤掉、不会刷屏；未划区域时不挡告警，避免「没配区域就全哑火」。值守精力打在禁区、通道、工位等真正要管的地方，误报与人工复核成本明显下降</li>
  <li><strong>业务脚本与规则链可并存</strong>：基础配置里的业务脚本负责「用现场语言写判断」；规则页负责过滤与步骤顺序。两条能力相互独立、可同时启用，交付时不必在「写脚本」和「配步骤」里二选一，复杂现场也能把口径一次说清</li>
  <li><strong>行业逻辑可插拔</strong>：园区、工地、交通等差异化研判不必改平台内核。集成商与方案商可登记、启停自己的研判能力，并按任务挂上——同一套检测模型服务多个客户项目，把「每个现场改一版分析程序」变成「配规则、挂能力、验收口径」</li>
  <li><strong>上线前可试跑</strong>：用样例或真实检测事件在线回放当前规则，逐步看清「通过还是丢弃、会不会产生告警」，联调与验收能回答「这条规则到底拦了什么」，少靠上线后再靠客诉调参</li>
  <li><strong>改规则即时生效</strong>：运行中的任务保存规则即可跟上新口径，不必停分析、不必重推画面。现场临时改禁区、加一道判断，值守当天就能按新标准管，缩短「等窗口停机—再改—再验」的空窗</li>
  <li><strong>感知与研判互不拖垮</strong>：监控画面继续流畅分析，业务判断按需扩展；研判失败可选择「本步跳过继续告警」或「宁可不报以免错告」，在漏报与误报之间按现场风险偏好取值。楼面级（standard）与全栈一体机（full）默认具备该能力，轻量单机仍可先跑通检测告警，需要深度运营时再升档</li>
  <li><strong>四类内置研判插件（免登记）</strong>：<strong><code>line_cross</code></strong>（越线检测，配合 <code>line</code> 检测线与追踪）、<strong><code>region_enter_exit</code></strong>（区域进出）、<strong><code>dwell_timer</code></strong>（停留/滞留超时）、<strong><code>headcount_gate</code></strong>（人数阈值）——可与区域闸门、放行、业务脚本及行业插件编排成贴现场的规则链</li>
</ul>

### 🤖 AI助手：IDEA 分屏共创，边改代码边问架构查健康

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
开源共建与现场 PoC 常卡在同一处：模块多、链路长，改代码要先配环境，查健康要登服务器，问架构要翻文档、找人。EasyAIoT 把 <strong>HARNESS 对话式助手</strong>嵌进 <strong>IDEA 在线 IDE</strong>——左侧完整 VS Code 工作区，右侧 AI 助手分屏；从资源管理器拖文件即可自动 <code>@</code> 引用进对话，边读源码边问端口、配置与服务健康，缩短「不懂—找人—再改」的闭环。
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>IDEA 分屏共创</strong>：工具栏一键打开右侧 AI 助手，编辑器与 Agent 同屏；亦可 <code>?file=路径&harness=1</code> 深链打开指定文件并分屏</li>
  <li><strong>拖入自动 @</strong>：资源管理器文件拖到助手面板，自动关联为对话上下文，少打路径、少丢上下文</li>
  <li><strong>问即查</strong>：Agent 调平台 Tool 探测 Gateway / 视频 / 算法等服务健康，并指向相关配置与源码——把 SSH + 翻 compose 压缩成一次对话</li>
  <li><strong>懂本体</strong>：内置 <code>HARNESS/ontology/AGENTS.md</code> 与全仓工作区，架构、端口、API、安装约定有统一答案</li>
  <li><strong>管控台同口径</strong>：业务页悬浮抽屉 / 全屏「AI 助手」与 IDEA 侧同一套能力；MCP + Cursor Skill 可跨环境复用</li>
  <li><strong>双向跳转</strong>：助手可通过 <code>easyaiot_open_in_idea</code> 生成门户链接，从问答回到可改可发的完整 IDE</li>
</ul>

| | | |
|:---:|:---:|:---:|
| ![IDEA登录](.image/banner/banner1203.png) | ![IDEA工作区](.image/banner/banner1204.png) | ![IDEA开发](.image/banner/banner1205.png) |
| ![AI助手对话](.image/banner/banner1210.png) | ![AI助手分析](.image/banner/banner1211.png) | ![AI助手协作](.image/banner/banner1212.png) |

### 📱 ANDROID / IOS / HARMONYOS：一套前端三端壳，人手一部手机都能用

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
移动端交付常卡在「平台覆盖」上：只支持一个系统的 App，把现场人员锁死在单位配发的手机上；而每多维护一套原生代码，成本翻倍、功能还容易漂移。EasyAIoT 的移动端是 <strong>一套 uni-app 前端 + 三套原生壳工程</strong>：同一套 <strong>APP</strong> 页面分别编译成 <strong>ANDROID</strong>（DCloud 离线运行时 + Gradle → APK）、<strong>IOS</strong>（WKWebView 壳 + xcodebuild → .app / .ipa）、<strong>HARMONYOS</strong>（ArkWeb 壳 + hvigor → HAP）三端可安装应用——一套业务逻辑，主流手机系统全部有原生安装包，不必维护三套代码。
</p>

<table style="width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px;">
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 14%;">平台</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 34%;">壳技术</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 30%;">打包产物</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600;">一键脚本</td>
</tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>ANDROID</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">DCloud uni-app 离线运行时 + Gradle</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>easyaiot-&lt;版本&gt;-&lt;环境&gt;-android.apk</code></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>ANDROID/make-apk.sh</code> / <code>make-apk.bat</code></td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>IOS</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">WKWebView 壳 + xcodebuild（需 Xcode 16+）</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>.app</code>（模拟器免签名）/ <code>.ipa</code>（真机分发）</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>IOS/make-ipa.sh</code></td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>HARMONYOS</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">ArkWeb 壳 + hvigor（DevEco Studio）</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>easyaiot-&lt;版本&gt;-&lt;环境&gt;-harmonyos.hap</code></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>HARMONYOS/make-hap.sh</code></td></tr>
</table>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>一套代码，零分叉</strong>：三端壳共用同一套 APP 页面与 admin-api——设备管理、实时预览、推流转发、算法任务、告警中心、模型推理/训练，在 Android、iOS、鸿蒙三端与 PC 管控台能力对齐；前端原生能力差异全部由条件编译隔离，一处改动三端生效</li>
  <li><strong>每端都用系统原生渲染</strong>：Android 跑 uni-app 离线运行时，获得原生 App 体验；iOS 通过自定义协议 <code>easyiot://</code> 加载 H5 产物，页面以「正常网页」身份运行（ES Module、localStorage、对 admin-api 的跨域请求都与真实站点部署一致）；鸿蒙把 rawfile 资源映射为 <code>http://appassets.local/</code> 虚拟主机交给 ArkWeb——无第三方引擎、无 file:// 各种限制、无行为分叉</li>
  <li><strong>每端一条命令出包</strong>：<code>make-apk.sh</code> / <code>make-ipa.sh</code>（模拟器 .app 或真机 .ipa）/ <code>make-hap.sh</code> 依次完成版本一致性校验 → 前端构建 → 资源同步 → 原生打包 → 命名成品；prod / test / dev 多环境各自出包互不覆盖</li>
  <li><strong>统一管理入口</strong>：<code>.scripts/docker/mobile.sh</code> 一入口管三端——<code>status</code>（三端版本一致性 / 工具链就绪度 / 已有成品）、<code>build android|ios|harmonyos|all</code>、<code>bump</code>、<code>artifacts</code>、<code>clean</code>，日常操作不必分别进入各模块</li>
  <li><strong>一条命令改齐五处版本号</strong>：APP manifest + Android build.gradle + <code>dcloud_control.xml</code> + iOS pbxproj（Debug/Release）+ 鸿蒙 <code>app.json5</code>——<code>.scripts/docker/mobile.sh bump 1.0.1 101</code> 一次改齐并回读校验；各端打包脚本在五处不一致时直接拒绝出包，宁可不出包也不出错包</li>
  <li><strong>成品命名即规范</strong>：全小写 kebab-case <code>easyaiot-&lt;版本&gt;-&lt;环境&gt;-&lt;平台&gt;.&lt;格式&gt;</code>，排序稳定便于归档，对对象存储 / CDN 与 CI 制品归集最友好；<code>mobile.sh artifacts/clean/status</code> 同时兼容新旧两种命名</li>
  <li><strong>CI 友好的流水线拆分</strong>：任何 Linux runner 都能先跑 <code>--skip-native</code> 完成前端构建与资源同步，再把同步好的工程交给 macOS runner（iOS）或自托管 DevEco runner（鸿蒙）做最后原生编译——一条流水线三端出包，不必每台机器都装平台工具链</li>
  <li><strong>签名与分发齐备</strong>：Android 用内置 <code>iot.jks</code> 签名（DCloud AppKey 已登记）；iOS 模拟器包免账号，真机 / App Store 包自动签名 + Team ID；鸿蒙 DevEco 内可自动生成调试签名，发行签名走 AppGallery Connect</li>
  <li><strong>每端文档与排查齐全</strong>：各模块自带 README，覆盖环境准备（JDK / Xcode 16+ / DevEco）、版本管理、签名与 FAQ 排查表；三端统一指南见 <a href="MOBILE.md" style="color: #3498db; text-decoration: none; font-weight: 600;">MOBILE.md</a></li>
</ul>

### 🎯 四档硬件，一套平台

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
很多智能物联网项目走到落地时都会卡住：<strong>功能做全了，小机器装不下；为了装得下，又得砍能力、拆版本、维护多套部署包。</strong> EasyAIoT 用同一套平台化解这一矛盾——从 <strong>edge 极简单机合装</strong>，到 <strong>边缘盒子点上智能、AI 一体摄像头上墙即分析、AIoT 智能全栈一体机一箱配齐全链路</strong>，四类最常见的现场硬件各选一档即可，同一套软件贯穿从「先跑起来」到单点试点、楼面覆盖再到全栈交付，不必拆版本。
</p>

| 选型 | 典型硬件（举例） | 推荐内存 | 你能做到什么 | 实测验证 |
| :-- | :-- | :--: | :-- | :--: |
| **edge** 边缘单机版 | <strong>轻量边缘单机</strong>（2 GB 工控机、旧笔记本、云上最小机型、门店试装机） | ≥ 2 GB | <strong>一台机器闭环先跑通</strong>：WEB + VIDEO + RUNTIME；摄像头接入、实时分析、智能告警；零 DEVICE，登录由 VIDEO 主导 | 约 **1.02 GB**，余量近 1 GB |
| **mini** 边缘精简版 | <strong>边缘盒子</strong>（8 GB 工控机、门店安防一体机、工地现场网关） | ≥ 8 GB | <strong>一个点位装上就有智能</strong>：摄像头接入、实时分析、智能告警、模型推理；事件面与 standard/full 一致（Gateway + iot-sink + EMQX） | 约 4–6 GB，余量充足 |
| **standard** 标准版 | <strong>AI 一体摄像头</strong>（智能摄像终端、带算力 AI 监控摄像头、多目 AI 分析一体机） | ≥ 16 GB | <strong>每路摄像头即智能节点</strong>：多路摄像头上墙即可楼面/园区级覆盖，设备、规则、算力统一编排，多场景并行运营；<strong>POST 定制研判</strong>让告警贴现场口径 | 约 10 GB，运行平稳有余量 |
| **full** 完整版（默认） | <strong>AIoT 智能全栈一体机</strong>（企业级全栈智控一体机、行业物联网全栈主机、云边端一体智能平台一体机） | ≥ 20 GB | <strong>一箱配齐 IoT + 视频 + AI</strong>：设备纳管、海量接入、智能分析、指挥研判一体化，全量能力长期稳跑；含 <strong>POST 定制研判</strong>与对外业务流转 | 约 14 GB，全能力开启仍留足余量 |

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
<strong>edge 怎么装：</strong><code>EASYAIOT_DEPLOY_PROFILE=edge sudo bash .scripts/docker/install_linux.sh install</code>（或 <code>... install_linux.sh edge install</code>）。首次安装交互菜单亦可选档；详情见上方 <a href="#-快速开始">快速开始</a>。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>安装选型与资源符合性（实测）：</strong>
</p>

| | |
|:---:|:---:|
| ![边缘单机 edge](.image/deploy-profile-edge.png) | ![边缘盒子 mini](.image/deploy-profile-mini.png) |
| ![AI 一体摄像头 standard](.image/deploy-profile-standard.png) | ![全栈一体机 full](.image/deploy-profile-full.png) |

#### 🧠 AI能力

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>平台名称与 Logo 全触点自定义</strong>：同一套 EasyAIoT 部署到现场后，用户看到的应是「自己的平台」，而不是通用产品名。监控大屏内置可视化「平台标识设置」，管理员在界面中即可完成品牌替换——管理后台可改平台名称与 Logo（同步侧边栏、浏览器标题）；监控大屏可独立设置指挥标题；登录页可自定义名称、Logo、表单标题及浅色/深色背景图，三处视觉统一、即时生效，并支持保存与一键重置。
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>对系统集成商与方案商</strong>：省去前端改肤、二次开发与发版成本；PoC 演示与正式交付可快速切换为客户品牌，同一套代码支撑多客户项目，缩短回款周期、提高方案复用率</li>
      <li><strong>对政府、园区、医院等行业终端用户</strong>：登录页、指挥大屏与日常管理后台均呈现本单位名称与标识，领导视察与对内推广更有归属感与公信力，符合机关、事业单位及大型企业的信息化品牌展示要求</li>
      <li><strong>对私有化部署与运维团队</strong>：现场安装后当场配置即可验收，无需等待开发排期；多客户演示或阶段性试点结束后可一键恢复初始设置，降低运维切换与重复部署成本</li>
    </ul>
  </li>
  <li><strong>YOLO26 新一代目标检测能力</strong>：平台内置最新一代目标检测能力，开箱即可用于实时画面分析与抓拍识别，在相同硬件条件下可接入更多路摄像头、响应更快、误报更少。支持从数据采集、标注、训练到上线推理的完整闭环，帮助用户以更低成本持续迭代专属检测模型，快速覆盖安全帽佩戴、人员闯入、烟火隐患等各类常见安防与工业场景，让「看得准、算得快、扩得动」成为默认可用能力</li>
  <li><strong>RUNTIME 高速执行层</strong>：把「看图、算图、推图」从解释型语言链路里抽出来，用 <strong>原生二进制</strong>贯通<strong>拉流 → 解码 → 推理 → 告警回传 → 带框推流</strong>。相对 Python 执行路径，避开 GIL 与多进程编排开销，同等硬件上<strong>同机路数更高、端到端时延更低、CPU/内存更省</strong>；实时 / 抓拍 / 巡检与多路原画转发共用同一套执行能力，默认 <code>executor=cpp</code>。业务上可做到：园区 NVR 数十路先保证「看得清、不卡顿」，再按需只对重点通道开 AI；原画预览与带框研判同屏切换、互不拖垮；平台（VIDEO/WEB）继续管设备编排、告警归档与权限，执行层专注吞吐与时延——扩路、加场景不必先换整机</li>
  <li><strong>高性能推流转发</strong>：面向「要先把画面铺满大屏 / 分屏，不必每路都开算法」的真实交付——NVR 批量通道、楼宇多点位可一键建转发任务，默认走 <strong>RUNTIME</strong> 高性能路径（亦可切兼容模式），让多路原画以更低资源开销稳定上墙。原画观看与 AI 研判可同设备并行：值守既能看未标注实况，也能切到带框结果；算法启停后转发策略自动跟进，少一次手工改配置、少一轮联调返工。配套并排预览能力，验收时直接对比延时与标注效果，缩短「装完还要对半天画面」的周期</li>
  <li><strong>YOLO26 人体姿态分析</strong>：在目标检测能力之上新增人体关键点与骨架姿态分析，开箱即用，支持图片、视频与摄像头实时流三种输入方式。图片模式可同步输出骨架标注与人数统计；视频模式支持进度跟踪与结果下载；摄像头模式可对接 RTSP/RTMP 实时取流，将姿态识别结果叠加推流回显，便于远程盯防与行为研判。模型推理页提供「姿态分析」与「目标检测」一键切换，适用于工地作业规范、健身动作评估、人群聚集态势感知等需要「看清人体结构与动作形态」的场景，让平台从「框出目标」进一步走向「理解姿态」</li>
  <li><strong>多协议摄像头接入支持</strong>：全面支持 GB28181 和 ONVIF 两大主流视频监控协议，实现标准化设备接入与管理。GB28181 作为中国国家标准，完美适配国内主流监控设备；ONVIF 作为国际通用标准，广泛兼容全球主流品牌摄像头。通过双协议支持，平台能够无缝对接现有监控系统，实现设备的即插即用、自动发现与统一管理，大幅降低设备接入门槛，提升系统兼容性与扩展性，为大规模摄像头部署提供坚实的技术基础。此外，新增 NVR 同网段/跨网段批量扫描、注册与统一管控能力，覆盖海康、大华、华为、萤石、小米等主流品牌，支持基于设备原生协议的网段发现、一键登记及通道批量导入；对于米家等原生不支持 RTSP 的消费级摄像头，可通过 <strong>RTC 模块（go2rtc 桥接）</strong>纳入同一平台，进一步降低大规模监控设备的接入与运维成本</li>
  <li><strong>大疆机场 / 无人机空中视角接入</strong>：突破固定摄像头「只能看地面、难覆盖广域」的布控局限，将大疆司空体系下的机场与无人机高空画面纳入平台统一视频与 AI 研判闭环。流媒体模块提供「接入大疆直播」能力：支持<strong>司空 API 开启直播</strong>与<strong>手动直播源</strong>两种接入方式——API 模式一键拉起厂家直播流并自动登记设备；手动模式则支持直接填入 RTSP / RTMP / HTTP-FLV / HLS 等直播源。接入后空中画面可与国标/ONVIF 固定点位同屏共管，管理者可像管理固定摄像头一样调阅机场与飞行器实况，并进一步挂接实时 AI 分析、告警联动与证据留存，快速覆盖广域巡查、应急勘察、周界补盲等传统固定点位难以触及的场景，显著缩短「发现异常—锁定现场—联动处置」的响应链条，让智慧安防从平面布控升级到天地一体协同感知</li>
  <li><strong>RTC 消费级摄像头 P2P 桥接</strong>：一次打通 <strong>Tapo（TP-Link 家用/门店 IPC）、Tuya（涂鸦系白牌海量设备）、Ring / Nest（海外门铃生态）、小米米家（国内家庭存量利旧）、Wyze（高性价比补点）、DoorBird（高端门口对讲）、GoPro（机动巡检机位）、Roborock（扫地机移动视角）</strong> 九大品牌——它们原生均不支持标准 RTSP，RTC 模块基于 go2rtc 提供 P2P 桥接与统一管理 API。Web 管控台「接入 RTC 摄像头」按品牌动态引导填参或 OAuth 绑定，一键完成 go2rtc 流注册、VIDEO 设备登记与 SRS 推流转发；桥接后与国标/ONVIF 专业摄像机<strong>同屏共管、同挂 AI 任务、同走告警联动</strong>，把「家里/门店已在用的摄像头」和「项目里的专业摄像机」纳入同一套视频研判体系，显著降低消费级设备入平台的集成与利旧成本</li>
  <li><strong>实时对讲与云台远控</strong>：打破「只能看、不能管」的传统监控局限，值守人员在实时预览同屏即可完成语音喊话与云台操控——无需切换系统、不必亲临现场，即可远程沟通、引导疏散或制止违规行为，把响应从「派人到场」压缩到「开口即达」。云台操控让摄像头随心转向、变焦聚焦，突发情况可迅速对准事发区域、放大细节，形成「看得清、指得准、喊得到」的一体化现场处置闭环。全面兼容 GB28181 与 ONVIF 设备，利旧现有监控资产，无需额外购置对讲主机或第三方软件，让存量摄像头即刻具备远程沟通与灵活调度能力，显著降低系统孤岛与值守成本</li>
  <li><strong>POST 定制研判（可编排后处理）</strong>：突破「只能检出、难以研判」的能力瓶颈，由独立 <strong>POST</strong> 服务承接业务研判层，将画面感知结果转化为可运营、可追责、可统计的业务事件。算法任务内即可编排规则链：默认按检测区域过滤后再告警，并可叠加业务脚本与行业插件，灵活定义人数统计、越线通行、停留超时、区域滞留、多条件复合告警等场景，无需反复调整模型即可适配工地安监、园区安防、交通管控等差异化需求。上线前可用样例事件试跑规则、看清拦什么、会不会告警；运行中改规则即时生效，不必停分析。感知与研判彼此独立、并行运转——画面持续流畅分析，业务逻辑按需扩展，研判结果自动沉淀并驱动精准告警，显著降低误报漏报与人工复核成本。业务人员专注规则表达，集成商可插拔行业能力，平台负责分发执行与规模承载，让「看得见」真正走向「判得清、管得住、用得起来」</li>
  <li><strong>多中心节点 × 多工作节点联邦集群</strong>：面向跨区域、多机房与云边协同部署，平台采用「N 个中心节点 + N 个工作节点」联邦架构——中心节点统一编排，工作节点承载算力与媒体执行，可横向扩展。每个中心节点纳管本域工作节点，支持流媒体、音视频转码、视频分析、模型推理与训练等能力的远程分发与一键部署；多中心可互联同步，集群泳道视图直观呈现「中心—工作」拓扑与资源水位。算法任务、自动标注流水线、推流转发等工作负载按节点角色与 GPU 能力智能调度，让海量路数接入、高并发推理与分布式训练在同一集群中协同运转，真正做到「纳得进、分得清、扩得开、管得全」</li>
  <li><strong>SENTINEL 集群节点哨兵</strong>：面向联邦扩容与跨机房算力池，解决「机器加进来了、却不知道能不能接活」的交付痛点——按业务功能持续摸清每台节点的就绪度与可调度能力，任务只派到真正就绪的机器；缺件时可自动请求环境补齐，无公网现场也能离线纳管扩容，让集群真正做到「纳得进、认得清、派得准、少登机」</li>

  <li><strong>SAM 零启动自动标注编排流水线</strong>：面向「尚无标注样本、尚无可用检测模型」的冷启动场景，平台集成 SAM 开放词汇分割能力，提供一键无人值守标注流水线。系统按策略自动串联摄像头抽帧采集、文本提示首批标注、达标后自动触发 YOLO 微调训练、量产阶段以 YOLO 高速推理为主并对漏检样本智能切换 SAM 回补、按进度周期性迭代训练及数据集自动打包导出，完整贯通「采—标—训—导」闭环。支持任务暂停恢复与本地/集群算力弹性调度，配合可视化策略配置与运行日志，帮助用户从零样本、零模型起步快速沉淀专属检测能力，让「开口定义类别、坐等模型成型」成为数据集建设的默认可用路径</li>
  <li><strong>万级弹性算力集群与横向扩容池</strong>：面向超大规模 AI 与视频业务，构建云边端一体的分布式算力底座，将算法任务、推流转发、算法服务、模型训练与推理统一纳入横向负载均衡与弹性伸缩体系。新增服务器一键纳管入网即可成为可调度算力单元，调度中枢按资源水位与业务压力自动分发任务、平衡负载，实现从百路到万路摄像头、从单机到万级节点的线性扩容——无需重复部署与手工调参，让海量路数接入、高并发推理与分布式训练在同一算力池中协同运行，真正做到「扩得动、跑得稳、管得住」</li>
  <li><strong>分布式存储驱动（计算 + 存储双集群解耦）</strong>：突破传统「每台节点本地目录挂载、路径写死、扩容必改配置」的存储瓶颈，平台以<strong>集群事件驱动</strong>替代原始本地目录驱动——Export 就绪、客户端挂载、主从切换、多集群桥接等存储状态变更以事件自动感知与联动，抓拍、录像、告警证据与模型资产统一写入分布式 NFS 集群，业务层无需关心底层挂载细节。计算与存储<strong>双集群分离解耦</strong>：算力侧全面拥抱 <strong>C++ RUNTIME</strong> 高速执行链路，存储侧独立构建可横向无限扩容的 NFS 集群池，算力扩容与存储扩容互不绑死、各按水位独立伸缩。配套集群泳道、拓扑视图与多集群桥接同步能力，新增节点一键纳管即可加入存储域，让海量路数接入下的「算得动」与「存得下」同步成立，真正做到「算存分离、各自扩容、事件联动、管得齐、扩得开」</li>
  <li><strong>天地图空间可视化与以图研判</strong>：接入国家天地图，将摄像头、告警与人车识别能力汇聚到一张地图，让监控从「看画面」升级为「看全局」。流媒体与告警模块均提供「地图分布」视图，配合设备目录树按区域聚焦，一眼掌握卡口布局与在线状态；支持地图点选、地点搜索与批量导入坐标，国标通道、NVR 通道与直连摄像头均可快速完成布点，让每路画面都有清晰的空间归属。告警事件自动关联摄像头坐标上图展示，可按时间、事件类型、任务与业务标签筛选，选中即可查看抓拍与录像，帮助值守人员从「哪里出事」快速切入处置。结合人脸库与车牌库识别能力，可将同一目标在多个点位上的命中记录串联成空间脉络——<strong>以人寻迹</strong>，还原重点人员在布控范围内的出现路线与活动范围；<strong>以车寻迹</strong>，串联过车记录，快速定位车辆行经路径与停留区域，为寻人找车、巡防布控与事后复盘提供直观线索。移动类设备还支持轨迹回放，按时间轴重现巡逻与行进路线；矢量地图与卫星影像随心切换，自动适应视野，让管理者以地图为纲、以图为媒，更快发现异常、锁定目标、指挥调度</li>
  <li><strong>Qwen / DeepSeek 多卡部署</strong>：支持将 Qwen、DeepSeek 等大语言模型以多卡并行方式部署上线，可按集群灵活调度 GPU 算力，实现模型实例的弹性扩缩与负载均衡，满足高并发推理与长上下文场景下的稳定服务能力</li>
  <li><strong>视觉大模型智能理解</strong>：集成QwenVL3视觉大模型，支持对实时视频画面进行深度视觉推理与语义理解，能够对画面内容进行智能分析与场景理解，提供更丰富的视觉认知能力，实现从像素级感知到语义级理解的跨越</li>
  <li><strong>摄像头实时画面 AI 分析</strong>：面向 RTSP/RTMP 实时视频流提供从拉流、解码、模型推理到结构化出数与告警联动的全链路分析能力；默认可由 <strong>RUNTIME</strong> 承接（与抓拍、巡检共用同一执行器体系），以毫秒级响应将画面变化即时转化为可检索、可研判的结构化检测事件，并<strong>默认推送带框检测流</strong>供值守切换研判。观看（原画）与算法（检测画）链路相互独立，兼顾预览清晰度与高路数并发吞吐；分析结果可无缝衔接检测区域、布防时段、人脸/车牌识别及可编排后处理规则，将传统「人盯屏、事后翻」的值守模式升级为「机器全时盯、异常秒推送、证据自动留」，让实时视频从被动观看真正变为主动感知与智能研判的基础设施</li>
  <li><strong>摄像头智能巡检</strong>：面向路数多、值守人力有限的监控场景，提供分屏巡检与设备目录批量巡检能力，对大规模摄像头进行轮巡式 AI 分析；默认可由 <strong>RUNTIME</strong> 以 <code>task_type=patrol</code> 在计算节点执行。支持轮询、连接池、混合三种调度模式——可按设定间隔自动抓拍、运行检测模型并联动告警与人脸/车牌识别；混合模式下焦点路常驻盯防、背景路轮巡，兼顾重点布控与全域覆盖。巡检进度实时可见，抓拍自动留存，支持从分屏画面或设备目录一键拉起数百路巡检，以「少连接、广覆盖、快发现」的方式，将传统人工逐屏翻看的值守模式升级为智能化自动巡检</li>
  <li><strong>云边端一体算法预警监控大屏</strong>：提供统一的云边端一体化算法预警监控大屏，实时展示设备状态、算法任务运行情况、告警事件统计、视频流分析结果等关键信息，支持多维度数据可视化展示，实现云端、边缘端、设备端的统一监控与管理，为决策者提供全局视角的智能监控指挥中心</li>
  <li><strong>人脸识别与人脸库管理能力</strong>：支持在摄像头任务中灵活开启人脸识别能力，提供人脸库与人脸特征管理体系，支持样本/特征的新增、查询、更新、删除与高效检索。支持对抓拍画面进行人脸比对与身份检索，完整记录匹配结果、抓拍图片、摄像头位置信息与设备上下文，便于后续人员轨迹追溯、安防取证与多维度统计分析</li>
  <li><strong>车牌识别与车牌库管理能力</strong>：支持在监控任务中一键启用车牌识别，自动从过车画面中识别车牌信息，并与自建车牌库实时比对。可灵活维护白名单、黑名单及业务标签，车辆命中规则时即时告警联动，帮助实现出入口通行管控、重点车辆布控、访客与固定车辆分类管理等需求。支持自动收录新出现车牌、完整留存抓拍与匹配记录，便于事后查车、轨迹核对与证据留存；识别过程与原有视频分析并行运行，不影响监控与告警主流程的稳定性和实时性</li>
  <li><strong>设备检测区域绘制</strong>：提供可视化的设备检测区域绘制工具，支持在设备抓拍图片上绘制四边形和多边形检测区域，支持区域与算法模型灵活关联配置，支持区域的可视化管理、编辑、删除等操作，支持快捷键操作提升绘制效率，实现精准的区域检测配置，为算法任务提供精确的检测范围定义</li>
  <li><strong>智能联动告警机制</strong>：支持检测区域、布防时段和事件告警的三重联动机制，系统会智能判断检测到的事件是否同时满足指定的检测区域范围、处于布防时段内且匹配告警事件类型，只有同时满足这三个条件时才会触发告警，实现精准的时空条件过滤，大幅降低误报率，提升告警系统的准确性和实用性</li>
  <li><strong>告警工单（AI 告警责任闭环）</strong>：让「AI 报出告警」真正落到「有人负责、有流程跟进、有结果可查」。告警落库后按<strong>路由规则</strong>自动匹配（告警对象/事件/任务/设备/边缘节点多条件组合），命中即自动生成<strong>告警工单</strong>并发起处理流程——无需人工盯屏派单，责任直接到人。工单依托平台内置的<strong>流程编排能力</strong>（可视化流程设计器：审批、会签、抄送、条件分支、并行分支、超时提醒等节点自由组合），支持通过/拒绝/退回/委派/转办/加签等审批动作与站内信/APP 待办提醒（deepLink 一键直达审批详情），每条告警的处置状态、当前责任人、耗时全程留痕，形成「告警—工单—处置—复核」完整闭环；存量告警也可手动补发起工单兜底，避免漏处置</li>
  <li><strong>大规模摄像头管理</strong>：支持百级摄像头接入，提供采集、标注、训练、推理、导出、分析、告警、录像、存储、部署等全流程服务</li>
  <li><strong>算法任务管理</strong>：支持创建和管理实时、抓拍、巡检等类型的算法任务，每个算法任务可灵活绑定抽帧器和排序器，实现精准的视频帧提取与结果排序
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>实时算法任务</strong>：用于实时画面分析，支持 RTSP/RTMP 流处理；执行后端默认 <code>executor=cpp</code>（拉起 <strong>RUNTIME</strong>，默认推带框 AI 流并回传告警/心跳），亦可选 <code>python</code> 兼容路径</li>
      <li><strong>抓拍算法任务</strong>：用于抓拍图像分析；默认亦可走 <code>executor=cpp</code>（RUNTIME SnapScheduler / Cron），对抓拍画面智能识别</li>
      <li><strong>巡检算法任务</strong>：面向多路轮巡与连接池调度；默认亦可走 <code>executor=cpp</code>（RUNTIME PatrolScheduler），以「少连接、广覆盖」完成批量 AI 巡检</li>
    </ul>
  </li>
  <li><strong>数据集标注与多格式数据集管理</strong>：内置可视化图像标注工作台，支持矩形框、多边形等标注形态，以及标注类别管理与进度跟踪；全面兼容 YOLO、COCO、ImageFolder 等主流数据集格式的灵活导入与导出，并打通云平台数据集通道，支持云端数据集的一键导入与同步导出，贯通「数据采集—人工标注—模型训练—部署推理」全流程闭环</li>
  <li><strong>多卡训练、断点续训与节点侧部署</strong>：突破「有卡用不上、任务控不住、中断成果丢」的训练瓶颈，打通多卡算力利用、任务可控调度与节点侧部署，让现场 GPU 真正用得上、训练任务真正控得住。平台可自动识别并调度服务器全部 GPU，用户可在训练页按需选择单卡或多卡；兼容多种常见数据集格式，支持大容量本地数据集上传，训练失败后仍可保留原始数据快速重试。训练进度全程可见，任务可停可续，本地与远程训练失败时也能及时回退并给出清晰反馈，让「训练—发布—使用」闭环更顺畅可靠</li>
  <li><strong>推流转发</strong>：支持在不启算法的情况下直接观看摄像头实时画面；多路批量推送、NVR 通道自动建任务开箱可用。默认走 <strong>RUNTIME</strong> 高性能路径，多路原画更省资源、更易上墙，适合「大屏先铺满、重点通道再开 AI」；特殊环境可切 Python/FFmpeg 兼容模式</li>
  <li><strong>GPU 探测、负载分配与多卡协同</strong>：平台具备 GPU 资源探测与智能分配能力，可自动识别可用 GPU 数量，并依据各卡实时负载将视频编解码与算法推理任务动态调度到多卡并行执行，在保障稳定性的前提下提升多路流处理吞吐与算力利用率，实现多卡场景下的画面编解码与模型推理协同</li>
  <li><strong>智能传输协议与拉流高可靠</strong>：在 RTSP 等拉流链路上，系统可按场景自动选择合适的传输方式以兼顾时延与稳定性。当出现灰屏、解码异常或画面停滞时，自动触发重连与链路恢复，降低长时间花屏、卡死对业务的影响</li>
  <li><strong>观看与研判双通路</strong>：把「大屏/分屏看原画」与「算法看结果」拆开调度——值守侧优先保证画面清晰、流畅；研判侧独立输出带框结果，两边互不抢路、互不拖垮。同一摄像头可同时保留实况与分析画面，值班切换更自然，扩路时也不必在「看得清」和「算得动」之间二选一</li>
  <li><strong>模型服务集群推理</strong>：支持分布式模型推理服务集群，实现智能负载均衡、故障自动切换与高可用保障，大幅提升推理吞吐量与系统稳定性</li>
  <li><strong>布防时段管理</strong>：支持全防模式和半防模式两种布防策略，可灵活配置不同时段的布防规则，实现精准的时段化智能监控与告警</li>
  <li><strong>OCR与语音识别</strong>：提供高精度文字识别与语音转文本能力，支持多语言识别</li>
  <li><strong>多模态视觉大模型</strong>：支持物体识别、文字识别等多种视觉任务，提供强大的图像理解与场景分析能力</li>
  <li><strong>LLM大语言模型</strong>：支持RTSP流、视频、图像、语音、文本等多种输入格式的智能分析与理解，实现多模态内容理解</li>
  <li><strong>模型部署与版本管理</strong>：支持AI模型的快速部署与版本管理，实现模型一键上线、版本回滚与灰度发布</li>
  <li><strong>多实例管理</strong>：支持多个模型实例的并发运行与资源调度，提高系统利用率与资源利用效率</li>
  <li><strong>摄像头抓拍</strong>：支持摄像头实时抓拍功能，可配置抓拍规则与触发条件，实现智能抓拍与事件记录</li>
  <li><strong>抓拍空间管理</strong>：提供抓拍图片的存储空间管理，支持空间配额与清理策略，确保存储资源合理利用</li>
  <li><strong>录像空间管理</strong>：提供录像文件的存储空间管理，支持自动清理与归档，实现存储资源的智能管理</li>
  <li><strong>抓拍图片管理</strong>：支持抓拍图片的查看、检索、下载、删除等全生命周期管理，提供便捷的图片管理功能</li>
  <li><strong>设备目录管理</strong>：提供设备树形目录管理，支持设备分组、层级管理与权限控制，实现设备的有序组织与精细化管理</li>
  <li><strong>告警录像</strong>：支持告警事件自动触发录像功能，当检测到异常事件时自动录制相关视频片段，提供完整的告警证据链，支持告警录像的查看、下载和管理</li>
  <li><strong>告警事件</strong>：提供完整的告警事件管理功能，支持告警事件的实时推送、历史查询、统计分析、事件处理与状态跟踪，实现告警全生命周期管理</li>
  <li><strong>录像回放</strong>：支持历史录像的快速检索与回放功能，提供时间轴定位、倍速播放、关键帧跳转等便捷操作，支持多路视频同步回放，满足事件回溯与分析需求</li>
</ul>

#### 🌐 IoT能力

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
许多项目把 IoT 做成「设备台账 + 报文中转」，结果是：能连上，却管不住；能上报，却推不动；能告警，却看不清现场；有数了，却展不成屏、对不上工艺。EasyAIoT 把 IoT 定位为<strong>感知—理解—决策—执行</strong>闭环里的执行神经：传感器与执行器提供「数」，摄像头与 AI 提供「图」，可视化大屏与工艺组态把「数」变成可指挥的态势，规则与影子把两者拧成可运营的业务动作——让平台不只「看得见」，更能「展得成屏、看得懂工艺、管得住、控得准、扩得开」。
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>可视化管理</strong>：设备测点、告警与业务指标若只停在列表与报文里，领导看不全、值班看不清、汇报还得另做 PPT——数据价值卡在「能采不能展」。平台将可视化项目、模板中心、素材库、数据源与服务部署收拢为一套能力：把物联网数据拖拽拼成园区态势、产线 KPI、设备运行等可运营大屏，草稿可改、成熟可发、发布可投——让 IoT 从「后台有数」升级为「前台有屏」，指挥研判与对外展示不必再外挂一套大屏工具</li>
  <li><strong>可视化项目全生命周期</strong>：大屏工程若散落在个人电脑与临时链接里，交接必乱、版本必丢、上线必扯皮。平台统一管理大屏项目的创建、编辑、预览、发布与下线，表格/卡片双视图随手盘点，已发布与未发布一眼可分——谁在做、做到哪、能不能投屏，项目状态可盘、可交、可验收，把「做一张屏」变成可运营的交付资产</li>
  <li><strong>可视化模板中心</strong>：每个项目都从空白画布重做，交付周期必然被设计与联调拖长。成熟的园区总览、工厂态势、设备看板等模板可沉淀复用，新建项目一键套用再微调——同类场景少从零画起，PoC 与多项目复制更快、口径更统一，把「会做一次」沉淀成「能交付多次」</li>
  <li><strong>可视化素材与数据源治理</strong>：图标、背景、视频素材各项目私藏一份，数据接口各屏各写一套，后期必出现风格打架、字段对不上。素材库集中归档可复用视觉资产，数据源统一挂接设备与业务接口——同一套素材风格、同一套数据口径服务多张大屏，改一处多处受益，少重复建设、少口径扯皮</li>
  <li><strong>可视化发布与服务部署</strong>：大屏做好却投不出去，等于白做。项目确认发布后可关联服务部署，按场景投放到指挥中心、值班室或对外展示入口，预览与正式投放同一套工程——从「编辑态」到「值班态」有明确出口，验收与日常值守不再靠临时链接与口头约定</li>
  <li><strong>组态管理</strong>：工业与楼宇现场最怕「表盘一堆、工艺看不懂」——电表、阀门、罐体液位有读数，值班却对不上管线与工序，异常只能口头对图、靠经验猜。平台提供 Web 组态能力，将设备测点绑定到水厂工艺总貌、产线运行看板、厂区管网拓扑、配电室电力监视等工艺画面，编辑与预览同入口、发布即可值班——让「数」落回「图」，工艺状态一目了然，值守从翻表猜事变为对着工艺图研判与处置</li>
  <li><strong>组态画面实时监视与有限控制</strong>：纯列表监控「看得见点位却看不见流程」，异常定位慢、跨班交接难、现场培训靠师傅带。组态运行态把关键测点动画到罐体、阀组、电机与开关上，趋势与状态同屏刷新，必要时可在画面侧完成启停、复位等有限操作——新人也能对着图上手，班组交接看同一套画面，异常从「找点位」压缩到「看工艺」，把工控现场真正纳入可值守、可交代、可扩展的日常运营</li>
  <li><strong>产品模型管理</strong>：物联网落地最贵的往往不是买设备，而是每接一类设备就重配一遍档案。平台以产品为同类设备模板，支持创建、启停、检索与表格/卡片双视图，应用场景、厂商、型号一次配好——后续扩容直接套用产品模板，不用再逐台从零填写，同类设备一次建档、多台复用，把「设备接入成本」从线性增长压成可复制资产</li>
  <li><strong>多类型产品建模</strong>：现场同时存在直连终端、边缘网关、网关子设备与视频设备时，若用同一套接入路径硬套，拓扑必乱、协议必错。平台按直连、网关、网关子设备、视频四类形态分开建产品，边缘汇聚、直连终端与视频设备各走各的接入路径——拓扑不会混、协议不会配错，为后续规模化纳管打好正确的产品骨架</li>
  <li><strong>产品接入协议与认证配置</strong>：每台设备单独约定协议与鉴权，是联调返工的重灾区。平台在产品级一次定稿接入协议（MQTT / TCP / HTTP / Modbus-TCP / Modbus-RTU / OPC UA）、数据格式、认证方式与加解密策略，下属设备自动继承同一套规范——联调时不再逐台约定鉴权与报文格式，接入规范从「人口口相传」变成「产品级可继承契约」</li>
  <li><strong>Modbus-TCP 工业以太网接入</strong>：面向电表、PLC、变频器等以太网侧工控设备，平台内置 Modbus-TCP 主站采集能力，按产品/设备配置接入参数与测点即可上线——读数自动汇入设备影子与在线状态，写值与属性下发贯通，让工业测点与物联网物模型、规则引擎、告警联动同一套闭环，不必再外挂独立数采软件</li>
  <li><strong>Modbus-RTU 串口现场接入</strong>：大量现场仪表仍挂在 RS-485 总线，若只能走 TCP 网关转换，接入成本与故障点都会翻倍。平台支持 Modbus-RTU 串口主站采集，适配虚拟串口与真实串口场景——总线侧设备同样纳入统一纳管与上下行控制，补齐「以太网进不了、串口又管不住」的现场空白</li>
  <li><strong>OPC UA 工业互联接入</strong>：面向现代化工控与上位系统互联场景，平台支持 OPC UA 客户端接入，完成订阅/读写配置——复杂设备模型可映射为平台物模型属性，上行采集与下行写点与现有设备影子、规则链、消息推送无缝衔接，让 OPC UA 现场资产真正进入「看得见、控得住、可联动」的 AIoT 运营体系</li>
  <li><strong>EDGE C# 边缘采集运行时</strong>：面向工控现场可独立部署的边缘采集模块——以 C# 插件化采集器承接 Modbus RTU、Modbus TCP、OPC UA 等协议，本地调度采集、配置驱动解析，经 MQTT 与 DEVICE/<strong>iot-sink</strong> 云平台对接。它对应设备管理中的 GATEWAY 角色（而非另开一套设备页）：现场汇聚、云上纳管；已覆盖网关/子设备属性上下行与配置下发，拓扑与子设备事件/服务透传等仍在演进。可打包发布至 x86_64 / ARM64 Linux 工控机与边缘网关，实现「现场采得准、云端管得住」的云边协同闭环</li>
  <li><strong>物模型属性定义</strong>：大屏、规则、告警若各写一套测点名，后期必然互相听不懂。平台先把设备能上报、能读写的测点定清楚，支持标准模板与自定义，草稿改完再发布——大屏、规则、告警从此认同一套字段，「能看哪些量」有统一语义，测点名各说各话的返工从根上被掐掉</li>
  <li><strong>物模型服务定义</strong>：远程启停、复位若每做一个动作就写一次性接口，控制面必然碎片化。平台把设备可被远程调用的服务及入参出参写成契约，草稿编辑、发布后生效——「能远程做什么」按契约填参即可，不必再为每个动作堆一次性接口，控制能力可复用、可审计</li>
  <li><strong>物模型事件定义</strong>：设备会上报哪些业务事件若不事先约定，告警口径必然前后打架。平台先约定事件类型，草稿发布后统一生效——事件日志与规则触发共用同一语义，「会发生哪些事」有统一口径，告警不会各说各话</li>
  <li><strong>物模型发布管控</strong>：模型改动若直接打到在线设备，一次误操作就可能冲击整批终端。平台让模型改动先落草稿，确认发布才推到设备侧——改模型有缓冲，未验证改动不会直接打中现场在线设备，显著降低误操作风险</li>
  <li><strong>协议脚本适配</strong>：现场最难啃的不是标准 MQTT，而是各厂家私有报文与「只能本地工具调试」的黑盒设备。标准报文开箱即用；遇私有协议，可在平台编写上下行编解码，支持模板套用、校验、即时调试与保存热加载——对接从「改设备固件、等厂家排期」变为「配脚本、热生效」，异厂家存量设备不用改固件就能纳入统一物模型</li>
  <li><strong>产品接入指引</strong>：新人联调若全靠驻场专家口头传，交付节奏必然卡在人身上。产品详情内置联调参数、鉴权、报文与验收说明，按页操作即可把设备验过——按产品交付时自带标准联调手册，少依赖驻场专家口述，PoC 与验收节奏更快、更稳</li>
  <li><strong>产品关联设备一览</strong>：运维与验收常因「这批设备到底覆盖了多少、在线率怎样」扯皮。打开产品即可看到旗下设备清单与在线状态——在线率、覆盖规模一眼盘清，运维与验收各管一段、责任边界清楚</li>
  <li><strong>设备档案纳管</strong>：散落在表格、聊天记录与现场记忆里的设备，盘点与移交必然失控。平台提供设备增删改查、按产品/标识/在线状态检索，表格与卡片双视图随手切换——散落终端收成可检索台账，盘点、移交、扩容都从一个入口进</li>
  <li><strong>设备在线与激活状态</strong>：问题机埋在「全部设备」里，值班只能盲翻。列表与详情直接亮出连接状态、激活状态、激活时间与最后上线时间——离线机、未激活机优先浮出，运维精力先打在真正异常的设备上</li>
  <li><strong>按产品登记设备</strong>：扩容时每台重选协议、重填鉴权，是规模化上线最大的摩擦。新建设备时绑定所属产品，协议与场景一并继承——登记即挂上正确产品模板，扩容复制产品即可，少了反复选协议、填鉴权的步骤</li>
  <li><strong>工业采集接入配置</strong>：电表、传感等测点若还要另开数采工具配置，现场必然双系统并行。登记工业采集类设备时可顺带配好主机、测点与采集周期——现场测点一次落档，不必再切到别的数采工具，工业采集与平台纳管一体完成</li>
  <li><strong>设备基础信息档案</strong>：换机、追责、对账时若靠口头确认「这是谁」，责任链必然断。名称、标识、SN、产品、版本、IP 等一机一档沉下来——打开档案即可确认设备身份，减少口头确认与现场翻找</li>
  <li><strong>设备接入指引</strong>：现场联调若仍靠翻厚文档、问专家，上线周期必然被拉长。按设备类型给出推荐命令、联调参数、鉴权、报文与验收说明，参数改完命令可直接复制——联调从翻文档变成抄命令验收，上线与 PoC 节奏更紧</li>
  <li><strong>运行状态实时查看</strong>：值班若每次都要登设备、啃原始报文才能判断测点是否正常，值守成本必然居高不下。按物模型把当前属性实况摊开，表格/卡片可切换、可刷新——不登设备、不看原始报文，也能一眼判断关键测点此刻正不正常</li>
  <li><strong>传感器浮点数据预测</strong>：关键测点若只能事后翻历史曲线，异常往往等「已经越界」才被看见。平台对传感器浮点属性提供趋势预测，把历史读数推演为可前瞻的走势——运维从「事后看数」升级为「事前洞察」，为处置争取窗口</li>
  <li><strong>运行状态属性阈值配置</strong>：健康边界若写死在代码或口头约定里，换型号、换场景就要返工。可按物模型为运行状态属性配置上下阈值，边界可定义、可复用、可精细化——设备「正常区间」成为可治理资产，而不是散落各处的经验值</li>
  <li><strong>阈值告警与阈值规则</strong>：超限若无人知、知了却无法联动，阈值配置只是摆设。测点越界自动告警，并可纳入规则联动处置——「越界即知、知则能管」，把健康边界真正落到可运营闭环</li>
  <li><strong>中心设备关联子设备一屏掌控</strong>：下属设备健康态势若要逐台翻看，巡检与异常响应必然慢半拍。中心设备视角一屏纵览关联子设备运行状态——不用逐台切换，现场巡检与异常定位效率显著提升，让设备侧真正具备「看得见数、管得住界、告得出警、看得清全局」的能力闭环</li>
  <li><strong>设备影子对照</strong>：传统排障最痛苦的是分不清「想让它怎样」和「实际怎样」。上报态、期望态与差异同屏对照，完整 JSON 可留底——排障从猜测变成对照，期望与实况是否一致一目了然</li>
  <li><strong>属性期望下发</strong>：为改一个参数专程出车，是规模化运维的典型浪费。可写属性批量改期望值后一键下发，处理中/成功/失败全程可跟——远程调参有回执，不必再为改参数派人到场，少无效出车</li>
  <li><strong>物模型服务调用</strong>：启停、复位若下达后无法确认是否执行到位，处置只能靠口头对账。按已发布服务填参发起调用，指令回执可跟踪——动作下达后能确认是否执行到位，处置过程可审计，把「口头说控过了」升级为「有回执的闭环」</li>
  <li><strong>离线指令排队</strong>：弱网或短暂离线时指令直接丢，回来还得重做一遍。设备暂时离线时，指令先写入期望影子，上线后按协议自动拉取或接收——弱网抖动不丢控制意图，回来即补齐，少做一遍重复操作</li>
  <li><strong>子设备网关代理控制</strong>：边缘大量终端若都要求直连平台，接入复杂度与证书管理成本会指数上升。子设备控制经所属网关代理下发——边缘终端不必直连平台也能被统一遥控，降低终端接入复杂度，让网关真正成为可运营的汇聚面</li>
  <li><strong>关联摄像头</strong>：传感器告警若看不到现场，值守只能「听数猜事」。物联设备可绑定设备目录中的摄像头，测点与画面点位挂上对应关系——异常一出就知道该翻哪路视频，把「报个数」升级为「找得到画面」</li>
  <li><strong>分屏监控与 AI 联动</strong>：这是 EasyAIoT 相对纯 IoT 平台的关键差异——纯物联「看得见数却看不见场」，纯视频「看得见场却控不住设备」。功能调用页可切 1/4/9 分屏预览关联摄像头，并可顺手拉起 AI 分析——改参数、下指令的同时盯着现场，「数」与「图」在同一屏里核实与处置，少切系统、少漏判，真正体现 AI + IoT 融合价值</li>
  <li><strong>事件日志</strong>：告警弹窗一闪而过，事后复盘只能靠记忆与扯皮。设备上报的信息/警告/错误事件集中汇聚，可按类型、名称、时间筛选——复盘翻的是原始事件流，回答「现场发生过什么」有据可依，不只靠瞬时弹窗</li>
  <li><strong>指令日志</strong>：联调排障最怕双方各执一词：指令到底下没下到、设备认没认。属性设置与服务调用的处理中/成功/失败全程留痕——联调与排障告别口头对账，指令链路可核对、可追责</li>
  <li><strong>设备日志</strong>：定位固件与业务异常若还要登设备翻本地文件，排障效率必然被现场网络与权限卡住。设备侧多级别日志汇到云端，关键字与时间可检索——云端即可定位异常，不必再登设备翻本地日志</li>
  <li><strong>网关子设备绑定</strong>：工业与楼宇现场常见「一台网关挂几十上百子设备」，拓扑若靠口口相传，扩点与故障隔离必然失控。网关可批量绑定/解绑子设备——谁挂谁一清二楚，扩点、换网关、故障隔离时责任边界不会糊</li>
  <li><strong>Topic 能力清单</strong>：研发与集成若各拿一份通道约定，联调必因不一致返工。按设备列出配置、影子、属性、服务、事件、OTA、时钟同步等上下行通道说明——对着同一份目录对接，通道约定不一致的返工少了</li>
  <li><strong>OTA 升级包管理</strong>：补丁与固件若靠 U 盘逐台拷贝，规模化升级几乎不可能。软件包/固件包统一上传归档，版本号、下载、编辑、删除与双视图齐全——补丁与固件放在一处可复用，不用再逐台拷贝介质，固件成为可管控的交付资产</li>
  <li><strong>OTA 升级策略</strong>：漏升有安全漏洞，乱升有兼容风险，是规模化设备运维的两难。关键版本可打标记，升级方式可选强制或非强制——紧急修复能推到位，日常版本也不乱升，漏升与兼容风险可控</li>
  <li><strong>规则链管理</strong>：业务联动规则散落各处、无法集中启停，误触发与闲置链路必然增多。规则新增、启停、批量删除与列表/卡片管理齐全——业务联动链路集中开关，闲置规则随时关掉，误触发少一截</li>
  <li><strong>规则链可视化编排</strong>：现场业务天天在变——阈值要调、联动要加——若每次都等开发写死，响应永远慢半拍。链式画布上按意图串联数据流转、条件判断与下游动作——场景改动拖拽即可落地，不必再等开发排期，把「设备数据进来之后怎么办」交给业务人员配置</li>
  <li><strong>规则导入导出</strong>：成熟规则若不能带走，每个项目都要从零重写。规则支持导入导出——跨环境迁移、多项目复用直接带走，成熟规则沉淀为可复制的交付资产</li>
  <li><strong>消息配置</strong>：换通知通道、改账号若还要动业务代码，运维必然被开发卡住。通知通道与消息基础设置集中维护——换通道、改账号只动配置，不动业务代码</li>
  <li><strong>消息模板</strong>：告警话术临时拼写，既易出错也难统一口径。邮件、短信、企业微信、钉钉、飞书、Webhook 等渠道各自维护模板——文案一次定稿多处复用，告警话术统一，少临时拼文案出错</li>
  <li><strong>消息推送</strong>：再准的检测、再完整的设备事件，若堵在系统里等人翻，价值等于零。按渠道创建推送任务，可先测试再正式启动——告警与业务事件直接落到责任人日常办公入口，不堵在系统里</li>
  <li><strong>推送历史</strong>：通知是否发出、是否触达若无记录，审计与优化只能靠猜。各渠道推送记录可回看——发出没有、触达没有有据可查，审计与触达策略优化都有底</li>
  <li><strong>通知用户与分组</strong>：关键告警全员刷屏会造成告警疲劳，该到的人收不到又会漏报。维护通知用户与分组，按角色、班次精准触达——该到的人收得到，全员刷屏的告警疲劳也少了，让「感知—研判—通知—处置」真正闭环到人</li>
  <li><strong>TRANSFORM 多向业务流转</strong>：平台侧告警、设备事件与业务结果若只能停在 EasyAIoT 内部，对接 MES / ERP / CRM / WMS 等系统仍要按项目定制接口，交付周期与返工成本都会被放大。TRANSFORM 把「转给谁、按什么规则转、字段怎么对上、投没投到」收成可配置能力：数据目的、转发规则与映射模板一次配好即可复用，投递过程可监控、可回看——多方系统对接从「每家写一次定制接口」变成「按约定配通、按轨迹验收」，让平台数据真正进入客户既有业务闭环</li>
</ul>

#### 📱 移动端APP

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>跨端覆盖</strong>：手机、小程序与 App 多端可用，运维与管理不必绑在工位前，现场也能即时查看与处置</li>
  <li><strong>能力对齐</strong>：移动端与 PC 管控台业务能力一致，换端不换功，管控体验无缝衔接</li>
  <li><strong>设备管理</strong>：多种接入方式统一纳管，列表与通道一目了然，点开即可实时看图，外出巡检同样心中有数</li>
  <li><strong>推流转发</strong>：随时创建与启停转发任务，掌握节点与各路画面状态；多路原画可高效上屏，外出也能调度视频资源</li>
  <li><strong>算法任务</strong>：实时、抓拍与巡检任务随手启停，检测成效随时掌握，异常发现不必等回办公室</li>
  <li><strong>告警中心</strong>：告警随手检索，抓拍与录像即点即看，移动值守也能快速核实与跟进</li>
  <li><strong>模型管理</strong>：模型上线状态一眼可查，部署进展心中有数</li>
  <li><strong>模型推理</strong>：现场传图即得识别结果，临时核验与抽检不必回 PC</li>
  <li><strong>模型训练</strong>：训练进度随时盯，必要时远程一键叫停，避免无效算力空转</li>
  <li><strong>个人中心</strong>：账号、租户与应用偏好集中管理，多端使用各得其便</li>
  <li><strong>流畅观看</strong>：实时画面与告警录像在移动端流畅回放，低延时、不卡顿，移动值守体验不打折</li>
  <li><strong>持续在线</strong>：登录状态自动保持，少被打断、少重复登录，让「云边端智能管控」真正触达手机与小程序</li>
</ul>

#### 💻 IDEA 在线 IDE

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>浏览器即开发</strong>：基于 code-server 提供 VS Code 风格在线 IDE，默认 clone 完整 EasyAIoT 仓库，贡献者不必先配本机环境即可改代码、跑模块级验证、提交 PR</li>
  <li><strong>独立门户与多人在线</strong>：操作台独立运行于 <code>:9300</code>，与 WEB 管控台解耦；一人一 Docker 工作区，端口池 13338–13437 支持多人同时在线；管控台悬浮球一键跳转门户</li>
  <li><strong>六语言工具链对齐本机</strong>：预装 <strong>JDK 21</strong>、Node 22、Python、Go、CMake/C++、.NET 8，覆盖 WEB / DEVICE / AI / RUNTIME / EDGE 的阅读、轻改与模块级验证</li>
  <li><strong>AI 共创</strong>：预装 GitHub Copilot（用自己的 GitHub 账号登录，平台不代持密钥）；无 Copilot 订阅时可自备 OpenAI 兼容 API Key，经 Continue 辅助改代码；工具栏可分屏打开 HARNESS AI 助手，拖文件自动 <code>@</code> 引用，边改边问</li>
  <li><strong>本机发布</strong>：按工作区改动路径建议待发模块，一键执行构建并替换本机正在跑的同名容器，刷新现网即可验收，缩短「改完—看到效果」的闭环</li>
  <li><strong>OAuth 与闲置回收</strong>：支持 Gitee / GitHub 登录（可强制），一人一区绑定账号；闲置默认 8 小时自动停机，心跳与打开 IDE 会刷新活跃时间，避免算力空转</li>
  <li><strong>贡献闭环</strong>：绑定个人 fork → 开分支改代码 → 推送到 fork → 向官方仓提交 PR</li>
</ul>

#### 🤖 HARNESS AI 助手

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0 12px;">
模块多、链路长，查健康、问架构、找配置常要翻文档、登服务器。HARNESS 把平台知识与实时探测收成<strong>对话式助手</strong>——业务页右下角即问即查，缩短排障与 PoC 周期，少依赖原厂与口口相传的经验。
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>问即查</strong>：Agent 调平台 Tool 探测 Gateway / 视频 / 算法等服务健康，并指向相关配置与源码——把 SSH + 翻 compose 压缩成一次对话</li>
  <li><strong>懂本体</strong>：内置 <code>HARNESS/ontology/AGENTS.md</code> 与全仓工作区，架构、端口、API、安装约定有统一答案</li>
  <li><strong>页内即聊</strong>：悬浮抽屉 iframe 嵌入，看告警/设备时不跳转、不丢上下文；亦可全屏「AI 助手」或新窗口</li>
  <li><strong>IDEA 分屏共创</strong>：工具栏一键打开右侧 AI 助手，编辑器与 Agent 同屏；亦可 <code>?file=路径&harness=1</code> 深链打开指定文件并分屏</li>
  <li><strong>拖入自动 @</strong>：从资源管理器拖文件到助手面板，自动关联为对话上下文</li>
  <li><strong>双向跳转</strong>：Agent 可通过 <code>easyaiot_open_in_idea</code> 生成门户链接，从问答回到可改可发的完整 IDE；IDEA 改代码提 PR，HARNESS 问架构查健康</li>
  <li><strong>MCP + Cursor Skill</strong>：同一套 <code>easyaiot_*</code> 能力经 MCP 暴露给 Cursor 等 IDE——管控台能问能查的，开发环境里同样能调，Skill 可跨项目复用</li>
  <li><strong>全形态开箱</strong>：基于 <a href="https://github.com/deepseek-ai/deepseek-harness" style="color: #3498db; text-decoration: none; font-weight: 600;">DeepSeek Harness</a> Sidecar（<code>:3080</code>），<code>mini / standard / full</code> 默认部署即带（<code>EASYAIOT_ENABLE_HARNESS=0</code> 可关）；DeepSeek / OpenAI 兼容端点，Key 在 <code>harness.env</code> 或 UI 自备</li>
  <li><strong>安全提示</strong>：实验模块，上游 <code>dsh</code> 处于 Developer Preview；生产请限制访问并配置写操作 / Shell 审批；API Key 勿提交 Git</li>
</ul>

### 📦 内置 AI 模型

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
平台开箱即用，内置多种面向安防监控、工业现场、智慧交通等场景的预训练模型，可在算法任务中直接选用，快速完成部署与推理，无需从零训练即可覆盖常见视觉检测需求。
</p>

| 模型名称 | 推理格式 | 基础模型 | 能力说明 |
| :-- | :--: | :--: | :-- |
| 安全帽模型 | ONNX | YOLOv8 | 检测作业人员是否佩戴安全帽 |
| 睡岗模型 | PyTorch | YOLOv8 | 识别岗位人员睡岗、脱岗等异常行为 |
| 人模型 | PyTorch | YOLOv8 | 通用人体检测，用于画面中人员的识别与定位 |
| 车牌模型 | ONNX | YOLOv8 | 识别车辆号牌信息 |
| 反光衣模型 | PyTorch | YOLOv8 | 检测作业人员是否穿着反光衣 |
| 火焰模型 | PyTorch | YOLOv8 | 识别明火、火焰等火灾隐患 |
| 吸烟模型 | PyTorch | YOLOv8 | 识别人员吸烟行为 |
| 打电话模型 | ONNX | YOLOv8 | 识别人员打电话、使用手机等行为 |
| 道路积水模型 | ONNX | YOLOv8 | 识别道路积水、路面积水等异常状况 |
| 口罩模型 | ONNX | YOLOv8 | 检测人员是否正确佩戴口罩 |
| 跌倒检测模型 | ONNX | YOLOv8 | 识别人员跌倒等异常姿态 |
| 人脸检测模型 | ONNX | YOLOv8 | 检测画面中人脸位置，支撑人脸识别链路 |

### 💡 技术理念

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
我们认为没有任何一个编程语言能够擅长所有事情。EasyAIoT 用六种编程语言混编，按场景分工：Java 负责平台架构、Python 负责 AI 算法、C++ 负责视频执行、Go 负责协议网关、TypeScript 负责管控界面、C# 负责边缘工业数采，云管、算法、执行、协议、界面与现场采集各归其位，构成完整的云边端技术闭环。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Java擅长构建稳定可靠的平台架构，却不适合网络编程与AI开发；Python擅长网络编程与AI算法，却在高路数、低时延的帧级执行上容易碰到 GIL 与进程开销瓶颈；C++擅长高性能任务执行，却不宜承担平台架构与算法编排；Go擅长高并发网络编程与协议实现，却不宜承担平台管控与AI算法；TypeScript擅长复杂前端交互与类型安全的工程化界面，却不宜承担后端高性能计算与AI推理；C#擅长工业协议采集与边缘运行时编排，强类型保障测点映射与协议解析可靠，<code>async/await</code> 支撑多设备并发轮询，.NET 跨平台发布适配 x86/ARM 工控现场，工控/SCADA 生态成熟、集成商上手快，却不适合承担云平台核心业务与AI算法。六种语言各司其职、扬长避短，实现颇具挑战，使用却极其便捷。
</p>

![EasyAIoT平台架构.jpg](.image/iframe2.jpg)

### 🔄 模块数据流转

<img src=".image/iframe3.jpg" alt="EasyAIoT平台架构" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🤖 零样本标注技术

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
创新性地依托大模型构建零样本标注技术体系（理想状态下完全去除人工标注环节，实现标注流程的自动化），该技术通过大模型生成初始数据并借助提示词技术完成自动标注，再经人机协同校验确保数据质量（可选），进而训练出初始小模型。该小模型通过持续迭代、自我优化，实现标注效率与模型精度的协同进化，最终推动系统性能不断攀升。
</p>

<img src=".image/iframe4.jpg" alt="EasyAIoT平台架构" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🏗️ 项目架构特点

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
EasyAIoT其实不是一个项目，而是多个可独立部署的子项目（含 WEB、DEVICE、EDGE、VIDEO、RTC、AI 等）。
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
好处是什么呢？假如说你在一个受限的设备上（比如RK3588），你只需要拿出其中某个项目就可以独立部署，所以看似这个项目是云平台，其实他也可以是边缘平台。
</p>

<div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">

<p style="font-size: 16px; line-height: 1.8; margin: 0; font-weight: 500;">
🌟 真开源不易，如果这个项目对您有帮助，请您点亮一颗Star再离开，这将是对我最大的支持！<br>
<small style="font-size: 14px; opacity: 0.9;">（在这个假开源横行的时代，这个项目就是一个异类，纯靠爱来发电）</small>
</p>

</div>

### 🌍 本土化支持

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT积极响应本土化战略，全面支持本土化硬件和操作系统，为用户提供安全可控的AIoT解决方案。已覆盖 <strong>麒麟(Kylin) / 欧拉(openEuler)</strong> 等国产操作系统的部署与 PANEL 安装包交付。
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖥️ 服务器端支持</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>完美兼容海光（Hygon）x86架构处理器</li>
  <li>支持本土化服务器硬件平台</li>
  <li>提供针对性的性能优化方案</li>
  <li>确保企业级应用的稳定运行</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📱 边缘端支持</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>普通开发板也可就地承担智能值守</li>
  <li><strong>EDGE</strong> C# 边缘采集可独立部署于工控机与 RS485 现场</li>
  <li>现场轻装上阵，无需为每处网点堆叠重存储</li>
  <li>开箱即可智能化，缩短边缘上线周期</li>
  <li>算力随点位铺开，告警与证据自动汇聚上云</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖱️ 操作系统支持</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>兼容<strong>麒麟(Kylin) / 欧拉(openEuler)</strong></li>
  <li>支持方德（Founder）等本土化Linux发行版</li>
  <li>适配统信UOS等主流本土化操作系统</li>
  <li>提供完整的本土化部署方案</li>
</ul>
</div>

</div>

## 🎯 适用场景

<img src=".image/适用场景.png" alt="适用场景" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

## 🧩 项目结构

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT 由 WEB、APP、DEVICE、EDGE、SENTINEL、VIDEO、RTC、AI、RUNTIME、POST、VISUALIZE、TRANSFORM、PANEL、IDEA、HARNESS、SITE 等核心模块组成，并配套 COMPILE 多平台打包交付能力：
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 20%;">模块</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">描述</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>SITE模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>官方价值入口</strong>：面向访客、集成商与终端客户的独立官方网站，把「云边端一体化」讲清楚——先理解价值，再进入下载与部署</li>
    <li><strong>缩短认知路径</strong>：产品特性、四档硬件选型、安装包入口与文档导览同站完成，减少「翻仓库、问人、找包」的沟通成本</li>
    <li><strong>支撑选型决策</strong>：按 edge / mini / standard / full 呈现轻量单机、边缘盒子、AI 一体摄像头与全栈一体机适用场景，帮助现场按硬件能力一次选对档位</li>
    <li><strong>引流到落地</strong>：官网与演示环境、开源仓库、Releases 安装包形成闭环，让「看懂 → 试用 → 下载 → 装机」可连续完成</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>WEB模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>统一管控界面</strong>：前端管理界面，提供统一的用户交互体验</li>
    <li><strong>多协议设备接入向导</strong>：IPC / NVR / 国标 / RTC 平台分 Tab 引导，支持 ONVIF 扫描、跨网段扫描、手动 RTSP、大疆直播与消费级摄像头 P2P 接入</li>
    <li><strong>RTC 平台接入</strong>：「接入 RTC 摄像头」快捷入口，按 <strong>Tapo / Tuya / Ring / Nest / 小米 / Wyze / DoorBird / GoPro / Roborock</strong> 九大品牌动态表单填参，OAuth 平台引导至 go2rtc WebUI 完成绑定</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>APP模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>跨端覆盖</strong>：一套建设、多端触达，手机、小程序与 App 均可使用</li>
    <li><strong>能力对齐</strong>：与 PC 管控台业务能力一致，支持多租户切换</li>
    <li><strong>设备管理</strong>：直连摄像头、GB28181、NVR、RTC 消费级摄像头等多协议统一纳管，在线状态与通道浏览，设备详情内一键实时预览</li>
    <li><strong>推流转发</strong>：推流任务创建、启停、节点状态与多路画面查看；支持高性能 / 兼容模式按现场切换</li>
    <li><strong>算法任务</strong>：实时 / 抓拍 / 巡检任务列表、启停控制与检测/帧数统计（默认可走 RUNTIME）</li>
    <li><strong>告警中心</strong>：告警事件检索、抓拍图预览、告警录像点播回放</li>
    <li><strong>模型与 AI</strong>：模型列表与部署状态、移动端图片推理工作台、训练任务进度监控与停止</li>
    <li><strong>个人中心</strong>：个人资料、账号安全、常见问题、意见反馈与应用设置</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>ANDROID / IOS / HARMONYOS模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>一套前端三端壳</strong>：APP uni-app 页面分别打成 Android（DCloud 离线运行时 + Gradle → APK）、iOS（WKWebView 壳 + xcodebuild → .app / .ipa）、鸿蒙（ArkWeb 壳 + hvigor → HAP）可安装应用，主流手机系统同一套业务逻辑</li>
    <li><strong>一键出包</strong>：<code>make-apk.sh</code> / <code>make-ipa.sh</code> / <code>make-hap.sh</code> 带版本一致性校验；prod / test / dev 多环境各自出包</li>
    <li><strong>统一管理</strong>：<code>.scripts/docker/mobile.sh</code> 承担 status / build / bump / artifacts / clean；<code>bump</code> 一次改齐五处版本号，版本不一致拒绝打包</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>DEVICE模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>设备管理</strong>：设备注册、认证、状态监控、生命周期管理</li>
    <li><strong>产品管理</strong>：产品定义、物模型管理、产品配置</li>
    <li><strong>协议支持</strong>：MQTT、TCP、HTTP、Modbus-TCP、Modbus-RTU、OPC UA 等多种物联网与工业协议</li>
    <li><strong>设备认证</strong>：设备动态注册、身份认证、安全接入</li>
    <li><strong>规则引擎</strong>：数据流转规则、消息路由、数据转换</li>
    <li><strong>数据采集</strong>：设备数据采集、存储、查询与分析</li>
    <li><strong>节点编排</strong>：计算/媒体节点纳管、连通检测、工作负载调度与媒体节点池分配</li>
    <li><strong>可视化后台</strong>：统一管理大屏/组态项目、模板、素材、数据源与服务部署，为可视化编辑器与工艺组态提供工程管理与发布能力</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>EDGE模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>为何选用 C#</strong>：强类型测点映射、异步多设备并发轮询、7×24 长驻稳定、Linux x86/ARM 跨平台自包含发布，工控生态成熟、集成商上手快</li>
    <li><strong>C# 边缘采集运行时</strong>：独立部署的边缘侧采集服务，插件化采集器 + 本地调度 + 配置驱动解析</li>
    <li><strong>多协议采集器</strong>：内置 Modbus RTU（RS485/串口）、Modbus TCP、OPC UA 采集器，可按任务扩展 <code>ICollector</code> 插件</li>
    <li><strong>MQTT 云边对接</strong>：以设备管理 GATEWAY 身份接入，属性上报、子设备属性代报、云端配置下发（<code>config/downstream/push</code>）与属性写值下行，对接 DEVICE/<strong>iot-sink</strong>；数据在同一套设备管理展现，与云端工业轮询（平台直连现场设备）互补——EDGE 适合 OT 隔离与 RS-485 现场</li>
    <li><strong>配置双通道</strong>：本地 <code>device-jobs.json</code> 与云端 MQTT 配置推送均可驱动采集任务</li>
    <li><strong>Linux 打包发布</strong>：<code>pack_linux.sh</code> 产出 x86_64 / ARM64 独立部署包，适配工控机与边缘网关</li>
    <li><strong>联调开箱</strong>：内置 E2E Demo，一键验证采集 → MQTT 上行 → 云端入库；配套云平台对接能力</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>SENTINEL模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>业务就绪哨兵</strong>：跟着每台调度节点走，按勾选业务持续摸清本机是否真正可接活</li>
    <li><strong>纳管即监测</strong>：节点纳入平台后自动开始巡检，扩容当天即可验收就绪度</li>
    <li><strong>可调度能力汇聚</strong>：把「能不能跑某类业务」汇总到管控台，调度按真能力下发</li>
    <li><strong>缺件自助补齐</strong>：期望环境缺失时可自动请求平台补齐，减少现场登机装机</li>
    <li><strong>断网友好扩容</strong>：无公网或受限网络现场可离线纳管与环境同步</li>
    <li><strong>交付口径统一</strong>：组件健康与可调度功能同屏可见，验收与排障少猜</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VIDEO模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>流媒体处理</strong>：支持 RTSP/RTMP 流实时处理与传输</li>
    <li><strong>多协议摄像头接入</strong>：GB28181、ONVIF、NVR 批量扫描、大疆司空直播与 RTC 消费级摄像头统一纳管</li>
    <li><strong>RTC 联动 API</strong>：<code>/register/device/rtc-live</code> 一键完成 go2rtc 流注册与设备入库，删除设备时自动清理 RTC 流</li>
    <li><strong>算法任务管理</strong>：支持实时 / 抓拍 / 巡检；默认可走高性能执行路径并输出带框研判画面，亦可按现场切兼容模式</li>
    <li><strong>推流转发编排</strong>：多路原画批量上屏默认高性能；特殊环境可切兼容模式；任务启停与策略变更可自动跟进，减少手工返工</li>
    <li><strong>抽帧器与排序器</strong>：支持灵活的抽帧策略与结果排序机制，每个算法任务可绑定独立的抽帧器和排序器</li>
    <li><strong>布防时段</strong>：支持全防模式和半防模式的时段化配置</li>
    <li><strong>编排与执行分工</strong>：VIDEO 管设备编排、原画预览、告警归档与启停；重活交给 <strong>RUNTIME</strong>（推理与高性能转发）——「管得住」与「跑得动」分开，路数与时延不再被 Python 编排拖住</li>
    <li><strong>与 POST 研判衔接</strong>：算法任务可配置后处理规则，检测结果经定制研判后再进入标准告警，改规则不必停分析</li>
    <li><strong>验收预览</strong>：支持原画与研判画面并排对照，便于现场快速验收延时与标注效果</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>RTC模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>go2rtc</strong>：基于 <a href="https://github.com/AlexxIT/go2rtc">go2rtc</a> 源码，vendor 随 install 脚本拉取</li>
    <li><strong>九大品牌 P2P 桥接</strong>：
      <ul style="margin: 4px 0; padding-left: 18px; line-height: 1.7;">
        <li><strong>Tapo</strong>（TP-Link）— 家用/门店 IPC，云密码直连 + 双向对讲</li>
        <li><strong>Tuya</strong>（涂鸦）— 白牌/OEM 摄像头海量纳管</li>
        <li><strong>Ring</strong>（Amazon）— 门铃/室外机，海外社区与仓储</li>
        <li><strong>Nest</strong>（Google）— Nest Cam / Doorbell 涉外高端场景</li>
        <li><strong>小米</strong>（米家）— 国内家庭存量设备利旧，免 Micam</li>
        <li><strong>Wyze</strong> — 高性价比 IPC，试点与广域补点</li>
        <li><strong>DoorBird</strong> — 智能门铃门口对讲 + 视频</li>
        <li><strong>GoPro</strong> — HERO9–12 机动机位 / 应急巡检</li>
        <li><strong>Roborock</strong>（石头）— 带摄像头扫地机移动视角补盲</li>
      </ul>
    </li>
    <li><strong>统一管理 API</strong>：平台注册表、流 URL 构建、go2rtc REST 代理，默认端口 6100（管理）/ 1984（WebUI）/ 8554（RTSP）</li>
    <li><strong>与 VIDEO 全链路打通</strong>：P2P 取流 → 标准 RTSP → SRS 推流 → Web 播放与 AI 分析，消费级设备与专业摄像机同一套运维体系</li>
    <li><strong>Docker 一体化</strong>：单容器运行 go2rtc 核心 + Python 管理服务，host 网络适配 P2P 局域网直连</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>AI模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>智能分析</strong>：负责视频分析和AI算法执行</li>
    <li><strong>模型服务集群</strong>：支持分布式模型推理服务，实现负载均衡与高可用</li>
    <li><strong>实时推理</strong>：提供毫秒级响应的实时智能分析能力</li>
    <li><strong>模型管理</strong>：支持模型部署、版本管理与多实例调度</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>RUNTIME模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>高性能原生执行</strong>：单二进制贯通拉流、解码、ONNX 推理、告警/心跳回传与带框推流；默认 <code>executor=cpp</code>，相对 Python 路径同机路数更高、时延更低、资源更省</li>
    <li><strong>四类现场形态</strong>：实时盯防、定时抓拍、轮巡巡检、纯原画转发——按业务选形态，不必为「只想看图」也付满额算力成本</li>
    <li><strong>原画与研判双画面</strong>：实时任务默认同步输出带框检测流，与 VIDEO 原画预览分离呈现，互不抢路</li>
    <li><strong>多路原画省资源上墙</strong>：推流转发默认走高性能路径，NVR 多通道场景下「多路看原画、少路跑 AI」同时成立</li>
    <li><strong>告警与状态回传中心</strong>：分析与转发过程的告警、运行状态汇聚回 VIDEO 统一落库与通知，节点本地不堆业务数据</li>
    <li><strong>过载时保实时</strong>：算力吃紧时优先保障当前画面与告警时效，避免「越忙越卡、越卡越漏」</li>
    <li><strong>GPU 优先、失败可续跑</strong>：有加速卡则优先用，不可用时自动降级继续跑，任务不中断</li>
    <li><strong>一键分发</strong>：WEB「业务运行时分发」或安装脚本批量下发；中心机随 VIDEO 安装自动挂载本机执行器</li>
    <li><strong>事件面 MQTT</strong>：告警/抓拍/后处理发往 EMQX 算法总线，由 <strong>iot-sink</strong> 落库、归档与通知 enrichment</li>
    <li><strong>管理面 HTTP 心跳</strong>：任务存活回 VIDEO，启停与任务表由 VIDEO 管理</li>
    <li><strong>NFS 媒体根</strong>：告警图、SRS 录像统一写入 <strong>NFS 共享媒体根</strong>（`EASYAIOT_MEDIA_ROOT`，默认 `/mnt/easyaiot-media`；无 sudo 时 fallback 至 `$HOME/easyaiot/media`）；MQTT 只带路径，由 <strong>iot-sink</strong> 读盘归档 MinIO</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>POST模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>定制研判</strong>：在目标检测之上独立做业务判断，把「框出目标」变成「该不该告警、按什么口径告警」</li>
    <li><strong>按任务配规则</strong>：区域过滤、放行、业务脚本与行业插件可编排成规则链，贴工地、园区、交通等现场管理抓手</li>
    <li><strong>少误报、可验收</strong>：区域外不刷屏；上线前可试跑规则，看清拦什么、会不会产生告警</li>
    <li><strong>改口径不停分析</strong>：运行中保存规则即时生效，不必为改禁区或加判断而停任务</li>
    <li><strong>感知与研判解耦</strong>：画面分析继续跑，业务逻辑按需扩展；行业能力可插拔，多项目复用同一套检测</li>
    <li><strong>内置插件</strong>：<code>line_cross</code> 越线检测、<code>region_enter_exit</code> 区域进出、<code>dwell_timer</code> 停留超时、<code>headcount_gate</code> 人数阈值——算法任务「后处理规则」中直接选用，无需登记；越线/进出/停留需开启目标追踪（<code>track_id</code>）</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VISUALIZE模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>拖拽式大屏编辑器</strong>：高性能低代码可视化编辑器，专注画布编辑与预览</li>
    <li><strong>与 WEB 一体联动</strong>：项目创建、模板、素材、数据源、发布与投放在管理后台「可视化」菜单完成；点击「打开编辑器」即可进入画布</li>
    <li><strong>大屏交付能力</strong>：图表、指标与布局拖拽配置，组件可挂接平台数据源与 IoT 测点，支撑园区态势、产线 KPI、设备运维、能源能耗等指挥大屏快速成屏</li>
    <li><strong>与组态分工清晰</strong>：指挥大屏走本模块编辑；工艺组态走 Web 组态能力；工程元数据统一由 DEVICE 侧可视化后台管理</li>
    <li><strong>部署形态</strong>：与 APP 同属 full 完整版能力，mini / standard 可按现场硬件跳过，降低边缘精简部署体积</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>TRANSFORM模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>多向业务流转</strong>：把平台侧告警、设备事件与业务结果按约定投递到 MES / ERP / CRM / WMS 等外部系统，打通「平台有数 → 业务系统用得上」的最后一公里</li>
    <li><strong>可配置对接</strong>：数据目的、转发规则与字段映射一次配好即可复用，减少「每接一家客户系统就定制一套接口」的交付成本</li>
    <li><strong>投递可验收</strong>：运行集群与投递轨迹可监控、可回看，联调与验收能回答「转没转到、卡在哪一步」，少靠口头对账</li>
    <li><strong>横向扩展</strong>：流量上来后可按业务约定扩容消费与投递能力，支撑多产线、多工厂、多系统并行对接</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>PANEL模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>交付与值守入口</strong>：独立于业务管控台——到场可装、可验、可守，缩短验收周期，降低驻场与远程支援成本</li>
    <li><strong>当天可闭环</strong>：按档位界面化装机，进度与结果当场可见，业务管控台未就绪也能先把整机拉起来并交出去</li>
    <li><strong>自助排障</strong>：容器健康、资源水位、任务日志与镜像就绪度一目了然，常见启停、拉镜像、清缓存不必等开发敲命令</li>
    <li><strong>多现场复用</strong>：同一套入口贯穿多台一体机与多处机房，PoC 与量产交付口径一致</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>IDEA模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>社区贡献在线 IDE</strong>：浏览器打开 VS Code 风格工作区，默认 clone 全仓；一人一 Docker 区，支持本机发布与闲置回收，把开源共建从「先配环境」变成「打开即改」</li>
    <li><strong>分屏 AI 助手</strong>：工具栏打开右侧 HARNESS，拖文件自动 <code>@</code> 引用；支持 <code>?file=&harness=1</code> 深链定位</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>HARNESS模块</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>对话式助手</strong>：问健康、问架构、定位问题，缩短排障与 PoC，少依赖原厂</li>
    <li><strong>页内悬浮抽屉</strong>：业务页不跳转即聊；<code>mini / standard / full</code> 默认自带</li>
    <li><strong>IDEA 分屏联动</strong>：编辑器右侧嵌助手，拖入 <code>@</code>、深链定位与双向跳转</li>
    <li><strong>MCP / Skill</strong>：管控台与 IDE 共用平台语义，Skill 可跨项目复用</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>COMPILE打包</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>多平台交付物</strong>：把 PANEL 等能力打成 Ubuntu / Debian、CentOS / RHEL <strong>7～9</strong>（x86 + <strong>CentOS ARM</strong>，按 el7/el8/el9 分包）、Windows、macOS 及 ARM / <strong>麒麟(Kylin) / 欧拉(openEuler)</strong>等目标安装包或可执行文件，方便给客户装机，不必现场从源码编译</li>
    <li><strong>缩短交付链路</strong>：集成商可按目标环境取对应安装包完成部署与升级，安装、启停与卸载路径统一，降低跨系统交付差异</li>
    <li><strong>与 PANEL 配套</strong>：打包产物可直接用于现场运维入口落地，让「能打包出去」和「到场能装能守」同一条交付链打通</li>
  </ul>
</td>
</tr>
</table>

## 🖥️ 跨平台部署优势

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT支持在Linux、Mac、Windows三大主流操作系统上部署，为不同环境下的用户提供灵活便捷的部署方案；配套 <strong>COMPILE</strong> 可按目标系统产出安装包与可执行文件，配合 <strong>PANEL</strong> 完成到场装机与日常值守：
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🐧 Linux部署优势</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>适合生产环境，稳定可靠，资源占用低</li>
  <li>支持Docker容器化部署，一键启动所有服务</li>
  <li>完美适配服务器、边缘计算设备（如RK3588等ARM架构设备）</li>
  <li>提供完整的自动化安装脚本，简化部署流程</li>
  <li>覆盖 Ubuntu、CentOS/RHEL <strong>7～9</strong>（含 <strong>CentOS ARM</strong>）、<strong>麒麟(Kylin) / 欧拉(openEuler)</strong>等主流服务器发行版</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🍎 Mac部署优势</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>适合开发测试环境，与macOS系统深度集成</li>
  <li>支持本地开发和调试，快速验证功能</li>
  <li>提供便捷的安装脚本，支持Homebrew等包管理器</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🪟 Windows部署优势</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>适合Windows服务器环境，降低学习成本</li>
  <li>支持PowerShell自动化脚本，简化部署操作</li>
  <li>兼容Windows Server和桌面版Windows系统</li>
  <li>提供图形化安装向导，用户友好</li>
</ul>
</div>

</div>


<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>统一体验</strong>：无论选择哪种操作系统，EasyAIoT都提供一致的安装脚本和部署文档，确保跨平台部署体验的一致性。
</p>

## ☁️ EasyAIoT = AI + IoT = 云边端一体化解决方案

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
支持上千种垂直场景，支持AI模型定制化和AI算法定制化开发，深度融合。
</p>

<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
<h3 style="color: #2c3e50; margin-top: 0;">赋能万物智视：EasyAIoT</h3>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
构筑了物联网设备（尤其是海量摄像头）的高效接入与管控网络。我们深度融合流媒体实时传输技术与前沿人工智能（AI），打造一体化服务核心。这套方案不仅打通了异构设备的互联互通，更将高清视频流与强大的AI解析引擎深度集成，赋予监控系统"智能之眼"——精准实现人脸识别、异常行为分析、风险人员布控及周界入侵检测。
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
平台支持实时、抓拍与巡检等类型的算法任务：三类任务均可默认走 <strong>RUNTIME 高速执行层</strong>（<code>executor=cpp</code>）——以原生二进制完成长连接拉流、解码、YOLO 推理与结果回传，实时任务<strong>默认推带框 AI 检测流</strong>；抓拍按 Cron 采帧识别；巡检多路轮巡覆盖；推流转发亦可走同一高性能路径把多路原画省资源上墙。相对 Python 兼容后端，高性能路径更吃得住高路数与低时延。告警与心跳统一回 VIDEO。通过算法任务管理实现灵活的抽帧与排序策略，结合模型服务集群推理，确保毫秒级响应与高可用。同时提供全防 / 半防两种布防策略，按时段精准监控与告警。
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
在物联网设备管理方面，EasyAIoT提供完整的设备生命周期管理能力，支持多种物联网与工业协议（MQTT、TCP、HTTP、Modbus-TCP、Modbus-RTU、OPC UA）。设备管理中的网关是云上的 GATEWAY / 子设备拓扑；<strong>EDGE</strong> C# 边缘采集运行时在现场扮演该网关，承接工业协议采集与 MQTT 云边对接，数据回落到同一套设备管理，实现设备的快速接入、安全认证、实时监控和智能控制。通过规则引擎实现设备数据的智能流转与处理，结合AI能力对设备数据进行深度分析，实现从设备接入、数据采集、智能分析到决策执行的全流程自动化，真正实现万物互联、万物智控。
</p>
</div>

<img src=".image/iframe1.jpg" alt="EasyAIoT平台架构" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

## ⚠️ 免责声明

EasyAIoT是一个开源学习项目，与商业行为无关。用户在使用该项目时，应遵循法律法规，不得进行非法活动。如果EasyAIoT发现用户有违法行为，将会配合相关机关进行调查并向政府部门举报。用户因非法行为造成的任何法律责任均由用户自行承担，如因用户使用造成第三方损害的，用户应当依法予以赔偿。使用EasyAIoT所有相关资源均由用户自行承担风险.

## 📚 部署文档

- [平台部署文档](.doc/部署文档/平台部署文档_zh.md) — Linux（含 Ubuntu / CentOS·RHEL **7～9** / **CentOS ARM** / ARM / **麒麟(Kylin) / 欧拉(openEuler)**）/ Mac / Windows 分步部署指南
- [macOS 镜像部署](.doc/部署文档/平台macOS部署文档_zh.md) — Docker Desktop 一键拉取预构建镜像
- [Windows 镜像部署](.doc/部署文档/平台Windows部署文档_zh.md) — `install_windows.ps1` 推荐入口（第 0 章）
- [部署最佳实践](.doc/部署文档/部署最佳实践.md) — 规格选型、环境要求、一键部署（含 CentOS **7～9** / **CentOS ARM** / **麒麟(Kylin) / 欧拉(openEuler)**）、预构建镜像、运维排障与生产环境建议

## 📘 操作手册

面向交付、值守与业务操作：按**操作链**组织（目标 → 前置 → 步骤 → 验收），默认平台已部署可用。

- [平台操作手册（目录）](.doc/操作手册/README.md) — 怎么读、最短闭环与文档索引
- [操作链总览](.doc/操作手册/00-操作链总览.md) — 全局地图、菜单速查、PoC 当天验收清单
- [登录与基础准备](.doc/操作手册/01-登录与基础准备.md) — 账号、组织、权限、通知渠道底座
- [视频设备接入](.doc/操作手册/02-视频设备接入.md) — ONVIF / NVR / 国标 / RTC / 大疆 → 预览与推流
- [AI 算法任务闭环](.doc/操作手册/03-AI算法任务闭环.md) — 标注/模型 → 任务 → 告警
- [物联网设备接入](.doc/操作手册/04-物联网设备接入.md) — 产品物模型 → 设备 → EDGE / 工业采集
- [告警通知与对外联动](.doc/操作手册/05-告警通知与对外联动.md) — 告警处置、通知、TRANSFORM
- [可视化大屏](.doc/操作手册/06-可视化大屏.md) — 大屏/组态编辑、发布与投放
- [APP 移动值守](.doc/操作手册/07-APP移动值守.md) — 移动端与 WEB 能力对照

## 🎮 演示环境

- 演示地址：http://36.111.47.113:8888/
- 账号：admin
- 密码：admin123

## 🎬 演示视频

- Bilibili：https://www.bilibili.com/video/BV1d3846yEQz/?vd_source=5d3350c0182a2cf35c2739f3d16c1161

## ⚙️ 项目地址

- Gitee: https://gitee.com/soaring-xiongkulu/easyaiot
- Github: https://github.com/soaring-xiongkulu/easyaiot

## 📸 截图

<div>
  <img src=".image/banner/banner-video1000.gif" alt="演示" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner-video1001.gif" alt="演示" width="49%">
</div>

#### 🖥️ 监控大屏

| | | |
|:---:|:---:|:---:|
| ![态势](.image/banner/banner1001.png) | ![总览](.image/banner/banner1076.jpg) | ![告警](.image/banner/banner1074.jpg) |
| ![看板](.image/banner/banner1075.jpg) | ![多维](.image/banner/banner1095.jpg) | ![综合](.image/banner/banner1096.jpg) |
| ![监控](.image/banner/banner1078.jpg) | ![实时](.image/banner/banner1077.jpg) |  |

#### 📺 可视化组态

| | | |
|:---:|:---:|:---:|
| ![项目](.image/banner/banner1185.png) | ![组态](.image/banner/banner1186.png) | ![编辑](.image/banner/banner1187.png) |
| ![预览](.image/banner/banner1188.png) | ![组件](.image/banner/banner1189.png) | ![数据源](.image/banner/banner1190.png) |
| ![发布](.image/banner/banner1191.png) | ![运行](.image/banner/banner1192.png) | ![模板](.image/banner/banner1193.png) |
| ![资产](.image/banner/banner1194.png) | ![大屏](.image/banner/banner1195.png) | ![展示](.image/banner/banner1196.png) |

#### 📹 视频监控

| | | |
|:---:|:---:|:---:|
| ![视频监控](.image/banner/banner1225.png) | ![视频监控](.image/banner/banner1226.png) | ![视频监控](.image/banner/banner1227.png) |
| ![视频监控](.image/banner/banner1228.png) | ![视频监控](.image/banner/banner1229.png) | ![视频监控](.image/banner/banner1230.png) |
| ![视频监控](.image/banner/banner1219.png) | ![视频监控](.image/banner/banner1220.png) | ![视频监控](.image/banner/banner1221.png) |
| ![视频监控](.image/banner/banner1222.png) | ![视频监控](.image/banner/banner1223.png) | ![视频监控](.image/banner/banner1224.png) |
| ![区域检测](.image/banner/banner1213.png) | ![区域检测](.image/banner/banner1214.png) | ![区域检测](.image/banner/banner1218.png) |
| ![后处理规则链](.image/banner/banner1216.png) | ![后处理规则链](.image/banner/banner1217.png) | ![后处理规则链](.image/banner/banner1215.png) |
| ![直播](.image/banner/banner1145.jpg) | ![预览](.image/banner/banner1146.jpg) | ![摄像头](.image/banner/banner1051.jpg) |
| ![列表](.image/banner/banner1053.jpg) | ![推流](.image/banner/banner1083.jpg) | ![转发](.image/banner/banner1084.jpg) |
| ![存储](.image/banner/banner1121.png) | ![抓拍](.image/banner/banner1122.png) | ![录像](.image/banner/banner1123.png) |
| ![配置](.image/banner/banner1124.png) | ![容量](.image/banner/banner1125.png) | ![回放](.image/banner/banner1126.png) |
| ![抓拍](.image/banner/banner1117.png) | ![文件](.image/banner/banner1118.png) | ![策略](.image/banner/banner1119.png) |
| ![配额](.image/banner/banner1120.png) | ![图库](.image/banner/banner1057.jpg) | ![归档](.image/banner/banner1058.jpg) |
| ![监控](.image/banner/banner1068.jpg) | ![统计](.image/banner/banner1069.jpg) | ![地图](.image/banner/banner1113.png) |
| ![定位](.image/banner/banner1114.png) | ![分布](.image/banner/banner1115.png) | ![点位](.image/banner/banner1116.png) |
| ![实况](.image/banner/banner1026.jpg) | ![多路](.image/banner/banner1028.jpg) | ![推流](.image/banner/banner1103.png) |
| ![预览](.image/banner/banner1104.png) | ![接入](.image/banner/banner1105.png) | ![NVR](.image/banner/banner1106.png) |
| ![实况](.image/banner/banner1183.jpg) | ![地图](.image/banner/banner1184.jpg) |  |

#### 🤖 AI助手

| | | |
|:---:|:---:|:---:|
| ![IDEA登录](.image/banner/banner1203.png) | ![IDEA工作区](.image/banner/banner1204.png) | ![IDEA开发](.image/banner/banner1205.png) |
| ![AI助手对话](.image/banner/banner1210.png) | ![AI助手分析](.image/banner/banner1211.png) | ![AI助手协作](.image/banner/banner1212.png) |

#### 🧠 AI模型

| | | |
|:---:|:---:|:---:|
| ![多集群同步](.image/banner/banner1200.png) | ![NFS集群拓扑](.image/banner/banner1198.png) | ![NFS集群管理](.image/banner/banner1197.png) |
| ![节点管理](.image/banner/banner1199.png) | ![NFS文件目录](.image/banner/banner1201.png) | ![NFS目录浏览](.image/banner/banner1202.png) |
| ![Qwen](.image/banner/banner1093.jpg) | ![视觉模型](.image/banner/banner1094.jpg) | ![列表](.image/banner/banner1099.png) |
| ![配置](.image/banner/banner1100.png) | ![详情](.image/banner/banner1101.png) | ![调用](.image/banner/banner1102.png) |
| ![训练](.image/banner/banner1019.jpg) | ![任务](.image/banner/banner1020.jpg) | ![列表](.image/banner/banner1023.jpg) |
| ![进度](.image/banner/banner1024.jpg) | ![参数](.image/banner/banner1017.jpg) | ![评估](.image/banner/banner1018.jpg) |
| ![详情](.image/banner/banner1021.png) | ![日志](.image/banner/banner1022.jpg) | ![管理](.image/banner/banner1097.png) |
| ![仓库](.image/banner/banner1098.png) | ![版本](.image/banner/banner1039.jpg) | ![资产](.image/banner/banner1061.jpg) |
| ![推理](.image/banner/banner1040.jpg) | ![配置](.image/banner/banner1042.jpg) | ![结果](.image/banner/banner1043.jpg) |
| ![在线](.image/banner/banner1044.jpg) | ![批量](.image/banner/banner1047.jpg) | ![监控](.image/banner/banner1048.jpg) |
| ![服务](.image/banner/banner1045.jpg) | ![部署](.image/banner/banner1046.jpg) | ![集群](.image/banner/banner1049.jpg) |
| ![调用](.image/banner/banner1050.jpg) | ![权重](.image/banner/banner1111.png) | ![下载](.image/banner/banner1112.png) |
| ![姿态](.image/banner/banner1147.jpg) | ![识别](.image/banner/banner1148.jpg) | ![任务](.image/banner/banner1085.jpg) |
| ![配置](.image/banner/banner1086.jpg) | ![详情](.image/banner/banner1087.jpg) | ![运行](.image/banner/banner1088.jpg) |
| ![区域](.image/banner/banner1079.jpg) | ![检测框](.image/banner/banner1080.jpg) | ![布防](.image/banner/banner1081.jpg) |
| ![预览](.image/banner/banner1082.jpg) | ![算法](.image/banner/banner1062.jpg) | ![创建](.image/banner/banner1063.png) |
| ![画面](.image/banner/banner1064.jpg) | ![分析](.image/banner/banner1065.jpg) | ![结果](.image/banner/banner1066.jpg) |
| ![回看](.image/banner/banner1067.jpg) | ![实况](.image/banner/banner1052.jpg) | ![智能](.image/banner/banner1054.jpg) |

#### 📋 告警工单

| | | |
|:---:|:---:|:---:|
| ![流程设计](.image/banner/banner1231.png) | ![节点配置](.image/banner/banner1232.png) | ![选择审批人](.image/banner/banner1233.png) |
| ![条件分支](.image/banner/banner1234.png) | ![条件规则](.image/banner/banner1235.png) | ![并行分支](.image/banner/banner1236.png) |

#### 📦 数据集

| | | |
|:---:|:---:|:---:|
| ![管理](.image/banner/banner1015.png) | ![列表](.image/banner/banner1010.jpg) | ![标注](.image/banner/banner1027.png) |
| ![任务](.image/banner/banner1016.jpg) | ![工具](.image/banner/banner1059.jpg) | ![预览](.image/banner/banner1060.jpg) |
| ![详情](.image/banner/banner1107.png) | ![导入](.image/banner/banner1108.png) | ![项目](.image/banner/banner1109.png) |
| ![审核](.image/banner/banner1110.png) | ![创建](.image/banner/banner1007.jpg) | ![样本](.image/banner/banner1008.jpg) |

#### 🔌 物联网

| | | |
|:---:|:---:|:---:|
| ![物模型](.image/banner/banner1149.jpg) | ![定义](.image/banner/banner1150.jpg) | ![产品](.image/banner/banner1151.jpg) |
| ![详情](.image/banner/banner1152.jpg) | ![设备](.image/banner/banner1153.jpg) | ![详情](.image/banner/banner1154.jpg) |
| ![状态](.image/banner/banner1155.jpg) | ![属性](.image/banner/banner1156.jpg) | ![服务](.image/banner/banner1157.jpg) |
| ![事件](.image/banner/banner1158.jpg) | ![影子](.image/banner/banner1159.jpg) | ![拓扑](.image/banner/banner1160.jpg) |
| ![子设备](.image/banner/banner1161.jpg) | ![分组](.image/banner/banner1162.jpg) | ![控制](.image/banner/banner1163.jpg) |
| ![遥测](.image/banner/banner1164.jpg) | ![历史](.image/banner/banner1165.jpg) | ![协议](.image/banner/banner1166.jpg) |
| ![连接](.image/banner/banner1167.jpg) | ![认证](.image/banner/banner1168.jpg) | ![调试](.image/banner/banner1169.jpg) |
| ![功能](.image/banner/banner1170.jpg) | ![读写](.image/banner/banner1171.jpg) | ![服务](.image/banner/banner1172.jpg) |
| ![订阅](.image/banner/banner1173.jpg) | ![日志](.image/banner/banner1174.jpg) | ![在线](.image/banner/banner1175.jpg) |
| ![统计](.image/banner/banner1176.jpg) | ![总览](.image/banner/banner1177.jpg) | ![看板](.image/banner/banner1178.jpg) |
| ![产品](.image/banner/banner1006.jpg) | ![设备](.image/banner/banner1009.jpg) | ![OTA](.image/banner/banner1179.jpg) |
| ![固件](.image/banner/banner1180.jpg) | ![任务](.image/banner/banner1181.jpg) | ![进度](.image/banner/banner1182.jpg) |
| ![规则](.image/banner/banner1013.jpg) | ![编排](.image/banner/banner1014.png) | ![转发](.image/banner/banner1206.png) |
| ![运行](.image/banner/banner1209.png) | ![目的](.image/banner/banner1207.png) | ![投递](.image/banner/banner1208.png) |

#### 🖥️ 集群

| | | |
|:---:|:---:|:---:|
| ![概览](.image/banner/banner1127.jpg) | ![算力](.image/banner/banner1128.jpg) | ![节点](.image/banner/banner1129.jpg) |
| ![详情](.image/banner/banner1130.jpg) | ![监控](.image/banner/banner1131.jpg) | ![调度](.image/banner/banner1132.jpg) |
| ![列表](.image/banner/banner1133.jpg) | ![状态](.image/banner/banner1134.jpg) | ![配置](.image/banner/banner1135.jpg) |
| ![分配](.image/banner/banner1136.jpg) |  |  |

#### 🔔 告警

| | | |
|:---:|:---:|:---:|
| ![事件](.image/banner/banner1089.jpg) | ![处理](.image/banner/banner1090.jpg) | ![通知](.image/banner/banner1029.jpg) |
| ![配置](.image/banner/banner1030.jpg) | ![列表](.image/banner/banner1072.jpg) | ![详情](.image/banner/banner1031.jpg) |
| ![处置](.image/banner/banner1070.jpg) | ![统计](.image/banner/banner1071.jpg) |  |

#### ⚙️ 系统

| | | |
|:---:|:---:|:---:|
| ![标识](.image/banner/banner1143.jpg) | ![重置](.image/banner/banner1144.jpg) | ![用户](.image/banner/banner1003.png) |
| ![权限](.image/banner/banner1004.png) | ![菜单](.image/banner/banner1005.png) | ![配置](.image/banner/banner1002.png) |

#### 📱 APP

| | | |
|:---:|:---:|:---:|
| ![APP截图](.image/banner/app/app_1008.jpg) | ![APP截图](.image/banner/app/app_1009.jpg) | ![APP截图](.image/banner/app/app_1010.jpg) |
| ![APP截图](.image/banner/app/app_1011.jpg) | ![APP截图](.image/banner/app/app_1012.jpg) | ![APP截图](.image/banner/app/app_1013.jpg) |
| ![APP截图](.image/banner/app/app_2023.png) | ![APP截图](.image/banner/app/app_2024.png) | ![APP截图](.image/banner/app/app_2025.png) |
| ![APP截图](.image/banner/app/app_2026.png) | ![APP截图](.image/banner/app/app_2027.png) | ![APP截图](.image/banner/app/app_2028.png) |
| ![APP截图](.image/banner/app/app_1014.jpg) | ![APP截图](.image/banner/app/app_1015.jpg) | ![APP截图](.image/banner/app/app_1016.jpg) |
| ![APP截图](.image/banner/app/app_1017.jpg) | ![APP截图](.image/banner/app/app_1018.jpg) | ![APP截图](.image/banner/app/app_1019.jpg) |
| ![APP截图](.image/banner/app/app_1020.jpg) | ![APP截图](.image/banner/app/app_1021.jpg) | ![APP截图](.image/banner/app/app_1022.jpg) |
| ![APP截图](.image/banner/app/app_2029.jpg) | ![APP截图](.image/banner/app/app_2030.jpg) | ![APP截图](.image/banner/app/app_2031.jpg) |

## 📞 联系方式

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
请先关注下方公众号，再通过技术交流群或微信号与我们联系。
</p>

## 👥 公众号

<div>
  <img src=".image/公众号.jpg" alt="公众号" width="30%">
</div>

## 💬 技术交流群

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
关注公众号后，使用微信扫描下方二维码加入 EasyAIoT 技术交流群。
</p>

<div>
  <img src=".image/交流群3群.jpg" alt="EasyAIoT技术交流3群" width="30%">
</div>

## 💬 微信号联系

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
关注公众号后，如需一对一沟通，可扫描下方二维码添加微信好友。
</p>

<div>
  <img src=".image/微信联系方式.jpg" alt="微信号联系方式" width="200">
</div>

## 🪐 知识星球：

<p>
  <img src=".image/知识星球.jpg" alt="知识星球" width="30%">
</p>

## 💰 打赏赞助

<div>
    <img src=".image/微信支付.jpg" alt="微信支付" width="30%" height="30%">
    <img src=".image/支付宝支付.jpg" alt="支付宝支付" width="30%" height="10%">
</div>

## 🤝 贡献指南

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
我们欢迎所有形式的贡献！无论您是代码开发者、文档编写者，还是问题反馈者，您的贡献都将帮助 EasyAIoT 变得更好。以下是几种主要的贡献方式：
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">💻 代码贡献</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Fork 项目到您的 GitHub/Gitee 账号</li>
  <li>创建特性分支 (git checkout -b feature/AmazingFeature)</li>
  <li>提交更改 (git commit -m 'Add some AmazingFeature')</li>
  <li>推送到分支 (git push origin feature/AmazingFeature)</li>
  <li>提交 Pull Request</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📚 文档贡献</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>完善现有文档内容</li>
  <li>补充使用示例和最佳实践</li>
  <li>提供多语言翻译</li>
  <li>修正文档错误</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🌟 其他贡献方式</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>报告并修复 Bug</li>
  <li>提出功能改进建议</li>
  <li>参与社区讨论，帮助其他开发者</li>
  <li>分享使用经验和案例</li>
</ul>
</div>

</div>

## 🌟 重大贡献者

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
以下是对EasyAIoT项目做出重大贡献的杰出贡献者，他们的贡献对项目的发展起到了关键推动作用，我们表示最诚挚的感谢！
</p>

<table style="width: 100%; table-layout: fixed; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0; width: 32%; min-width: 9rem;">贡献者</th>
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0;">贡献内容</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>℡夏别</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动EasyAIoT项目贡献Windows部署文档，为Windows平台用户提供了完整的部署指南，大大降低了Windows环境下的部署难度，让更多用户能够便捷地使用EasyAIoT平台。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>YiYaYiYaho</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动EasyAIoT项目贡献Mac容器一键部署脚本，为Mac平台用户提供了自动化部署解决方案，显著简化了Mac环境下的部署流程，提升了开发者和用户的部署体验。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>山寒</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动EasyAIoT项目贡献Linux容器部署脚本，为Linux平台用户提供了容器化部署方案，实现了快速、可靠的容器部署，为生产环境的稳定运行提供了重要保障。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>玖零。</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动EasyAIoT项目贡献Linux容器部署脚本，进一步完善了Linux平台的容器化部署方案，为不同Linux发行版用户提供了更多选择，推动了项目的跨平台部署能力。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>爱吃小柚子</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在「训得动、训得稳、训得省心」方向的发展，系统性打通多卡训练、断点续训与节点侧部署能力，让现场算力真正用得上、训练任务真正控得住：支持自动识别并使用服务器全部 GPU，用户可在训练页按需选择单卡或多卡，不再受限于只能看到一张卡；兼容多种常见数据集格式与目录结构，支持大容量本地数据集上传，训练失败后仍可保留原始数据快速重试，显著降低数据准备与反复折腾的成本；完善训练进度可见、任务可停可续，避免中断后成果丢失、点击停止却仍在后台空转等痛点，使本地与远程训练调度在失败时也能及时回退、给出清晰反馈；同步优化前端训练任务的 GPU 选择、继续训练与停止状态展示，并修复模型发布误判失败、自定义预览图被覆盖、按名称/版本查不到模型以及数据集同步易超时、易冲突等问题，让「训练—发布—使用」闭环更顺畅可靠。此前亦主导国标 GB28181 与 AI 业务流程的端到端联调验证及画面清晰度专项评估，为国标接入可靠性与视频观感优化提供了重要依据。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>Dark</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动EasyAIoT项目在国标视频监控方向的发展，贡献 GB28181 能力的端到端打通，实现视频播放与云台控制，使国标设备接入具备可用的实况预览与远程操控能力。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>machh</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT-Edge 项目的发展，完成摄像头接入与 AI 能力的端到端跑通，并实现功能串联，使边缘侧「接入—智能分析」链路可用、可闭环。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>遗忘的星空</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在设备直连接入方向的发展，贡献多品牌 IP 摄像头资产盘点与网段扫描能力，支持海康 IPC、NVR 等设备的批量发现与识别；完善直连设备在同网段、跨网段场景下的批量搜索与一键注册流程，基于设备原生协议实现接入，可绕过海康 SDK、摆脱对海康平台的强依赖，为开放、可控的摄像头规模化接入奠定了基础。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>阿龙</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在地图可视化与空间研判方向的发展，独立贡献天地图空间可视化能力的完整代码实现，涵盖国家天地图底图接入、摄像头与告警设备布点、地图分布视图、地点搜索与坐标批量导入、告警事件自动上图、以人/以车寻迹及移动设备轨迹回放等核心链路，使平台「天地图空间可视化与以图研判」能力从方案设计真正走向可落地、可使用的生产形态。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>雨落流殇</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在超大规模流媒体承载方向的发展，贡献异构流媒体服务器集群的部署与调度思路，提出多节点池协同、流媒体与业务层解耦及节点注册调度等可扩展方案，为平台支撑万级路摄像头并发接入、稳定分发与弹性扩容奠定了重要的架构基础。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>常康</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在智能交通与车辆管控方向的发展，独立贡献车牌识别算法与完整代码实现，涵盖车牌定位检测、号码与颜色识别、双层牌拼接与倾斜透视校正、车牌库管理与多库顺序匹配、算法任务一键联动及异步比对等核心链路，全面支持蓝/黄/绿/白牌及新能源车牌等主流类型，使平台「车牌识别与车牌库管理能力」从能力规划真正走向可落地、可闭环的生产应用。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>Li</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在青年开发者社群与协作生态方向的发展，以卓越的组织领导力与感召力，带领全校同学深度参与项目共建，汇聚青春才智、凝聚团队合力，为 EasyAIoT 注入了源源不断、绵延不绝的发展动能；在项目传播推广、实践落地与后续人才梯队培育等方面，亦作出了举足轻重、不可替代的重要贡献。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>陈家林</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在物联网设备互通、工业协议接入与空天视频融合方向的发展，打通设备指令与状态数据的上下行闭环，使平台真正实现「下得去、看得见、控得住」；系统性贡献 Modbus-TCP、Modbus-RTU、OPC UA 工业协议接入能力，完成以太网侧与串口侧工控设备及 OPC UA 节点的统一采集、测点读写与物模型映射，使电表、传感器、PLC、控制器等海量工业设备数据可被平台统一汇聚、监测与联动，补齐「看得见现场、也听得到设备」的关键拼图；同时贡献大疆司空机场与无人机画面接入能力，把空中巡检视角纳入统一视频与告警体系，显著拓展平台在工控数采、产线智控、广域巡查、应急勘察与天地一体协同感知中的落地价值。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>空空</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在摄像头直连「从能发现走向能落地」方向的发展，补齐直连接入在认证、通道同步、配置变更与多品牌出流等关键短板，使平台在真实 NVR / 多厂商现场具备可交付的可用性：打通设备登录认证，让直连设备真正「登得进、管得住」；完善 NVR 同步通道后的取流模型，让批量同步出来的流可播、可用，显著提升 NVR 规模化接入效率；保障接入参数可持续维护；同步建设国内常用监控品牌出流规则库，并开放自定义品牌规则，使异厂商、异型号设备可一键出流，不必依赖人工试地址，把直连能力从「扫得到设备」推进到「登得进、同步准、改得了、多品牌都能出流」的生产可用形态，为后续云台与变焦等操控能力完善奠定坚实基础。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>狗娃</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在「物联网数据可展成屏」方向的发展，前瞻提出可视化 Board（拖拽看板）模块的产品构想：传统大屏往往每张屏、每个组件都要独立手写查询，交付慢、改一次动全身、业务人员几乎无法自助做屏。Board 方案把图表、指标与布局交给拖拽画布配置，并把组件直接挂接平台 IoT 物模型测点——实时值与历史值从设备侧一键取用；让园区态势、产线 KPI、设备运维等大屏从「开发写查询才能出屏」升级为「选测点、拖组件即可成屏」，显著缩短可视化交付周期，把 IoT「后台有数」真正变成「前台有屏」的可运营能力。此前亦贡献传感器浮点数据预测、运行状态属性上下阈值配置、阈值告警与规则联动，以及中心设备关联子设备运行状态一屏展示，打通「预测—定界—告警—规则—一屏掌控」设备运行闭环，使平台设备侧具备「看得见数、管得住界、告得出警、看得清全局」的能力。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>大老刘</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在对外宣介与方案表达方向的发展，贡献《AI视频监控分析平台》图文介绍材料，系统梳理平台在 AI 视频监控分析场景下的能力全貌与落地价值，让更多用户、集成商与合作伙伴能快速理解平台定位与核心亮点，显著提升项目对外传播与商务沟通效率。</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>刘兆中ᯤ⁵ᴳ</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在 macOS 一键部署方向的发展，率先贡献部分 Mac 一键部署脚本，把镜像拉取、容器编排与环境前置检查等主干路径基本打通，使后续完善只需补齐「最后一公里」；其探索与实践为团队厘清了 Mac 侧部署链路的关键节点与风险点，显著缩短了后续工程化收尾的路径，是 macOS 部署能力从零到可用过程中不可或缺的奠基性贡献。</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>添旺</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">为推动 EasyAIoT 项目在云边协同视频接入与智能研判方向的发展，独立贡献多项关键能力，直面边缘落地中「接不进、调不准、跑不实、查不回」的核心痛点：其一，支持边缘摄像头接入与算法节点亲和——IPC / NVR 可选择在线边缘节点作为「接入节点」，设备发现、网段扫描、ONVIF 探测与 NVR 通道枚举全部下沉至边缘节点就近执行，源流经边缘节点回推主节点媒体服务统一分发播放，使分支机构、跨网段/私网中的摄像头无需与中心平台网络直通即可纳管出流；算法任务创建时按摄像头登记的接入节点自动锁定执行节点，从调度机制上杜绝任务被派往无法访问摄像头的节点而空转失效，让算力真正围绕摄像头就近编排。其二，定位并修复同摄像头多任务及多模型仅单路生效的核心缺陷——以任务级流标识隔离各任务的推理链路，通过共享解码复用单路取流支撑多任务并发分析，并让告警与运行状态全链路携带任务身份，使同一摄像头可稳定并行承载多个算法任务与多模型检测（如人脸+车辆同框识别），且以独立取流服务与回归测试长期守护该行为。其三，支持边缘录像分层存储与统一事件回放——边缘侧录像按层级就地留存，告警事件与录像证据可在云边统一入口检索回放，补齐「事件有据可查、证据可信可回放」的证据闭环。上述工作显著增强了平台在真实复杂网络环境下的交付确定性与智能分析结果的可信度。</td>
</tr>
</tbody>
</table>

<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>特别致谢</strong>：以上贡献者在跨平台部署文档与脚本、macOS 一键部署脚本奠基与链路探索、国标视频能力与 AI 联调验证、多卡训练与断点续训、多品牌摄像头直连发现与批量接入、天地图空间可视化、异构流媒体集群部署与调度、车牌识别算法与完整代码、EasyAIoT-Edge 边缘侧端到端串联、校园开发者社群组织与青年协作生态构建、物联网设备上下行闭环与大疆司空空中视角接入、Modbus-TCP / Modbus-RTU / OPC UA 工业协议接入、摄像头直连从发现到登录/同步/配置/多品牌出流的闭环、拖拽看板（Board）构想与 IoT 测点实时/历史值直取集成、传感器浮点数据预测与阈值告警规则及中心设备关联子设备运行状态一屏展示、AI 视频监控分析平台图文介绍材料、边缘摄像头接入与算法节点亲和调度、同摄像头多任务及多模型仅单路生效的隔离修复、边缘录像分层存储与统一事件回放等不同方面推动了 EasyAIoT 的发展，他们的专业精神与无私奉献值得我们学习与尊敬。再次向这些杰出的贡献者表示最诚挚的感谢！🙏
</p>

## 💝 开源守望者

开源项目的持续推进，从来不只依赖代码与文档。在 EasyAIoT 算力资源最吃紧、项目几近难以为继的那些日子里，正是以下各位以真金白银的支持，为项目注入了最关键的续航——你们或许未曾提交一行代码，但每一份信任与托举，都让这个项目得以跨过最难的槛、继续向前迭代。只要有人在用、有人在撑，开源生态便值得走得更远；EasyAIoT 今日所能抵达的高度，离不开这些在关键时刻雪中送炭的同行者。我们向每一位给予援手的朋友致以最诚挚的敬意与感谢！以下排名不分先后：

<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/lysss.jpg" width="80px;" alt="lysss"/><br /><sub><b>lysss</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Sean-宋阳.jpg" width="80px;" alt="Sean-宋阳"/><br /><sub><b>Sean-宋阳</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/XYZ.jpg" width="80px;" alt="XYZ"/><br /><sub><b>XYZ</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/大虚子民🎼.jpg" width="80px;" alt="大虚子民🎼"/><br /><sub><b>大虚子民🎼</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/哈兰葱.jpg" width="80px;" alt="哈兰葱"/><br /><sub><b>哈兰葱</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/曲超.jpg" width="80px;" alt="曲超"/><br /><sub><b>曲超</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/李雪汉.jpg" width="80px;" alt="李雪汉"/><br /><sub><b>李雪汉</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/梦影·清之韵.jpg" width="80px;" alt="梦影·清之韵"/><br /><sub><b>梦影·清之韵</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/dasic.png" width="80px;" alt="dasic"/><br /><sub><b>dasic</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/战刀.jpg" width="80px;" alt="战刀"/><br /><sub><b>战刀</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/禾一虫.jpg" width="80px;" alt="禾一虫"/><br /><sub><b>禾一虫</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/钟意月月🍹.jpg" width="80px;" alt="钟意月月🍹"/><br /><sub><b>钟意月月🍹</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/山人.jpg" width="80px;" alt="山人"/><br /><sub><b>山人</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/林大侠.jpg" width="80px;" alt="林大侠"/><br /><sub><b>林大侠</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/core.jpg" width="80px;" alt="core"/><br /><sub><b>core</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/王亚鹏.jpg" width="80px;" alt="王亚鹏"/><br /><sub><b>王亚鹏</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/今早好大雾.jpg" width="80px;" alt="今早好大雾"/><br /><sub><b>今早好大雾</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/头像飞鱼.jpg" width="80px;" alt="头像飞鱼"/><br /><sub><b>头像飞鱼</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/simon.jpg" width="80px;" alt="simon"/><br /><sub><b>simon</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/万博览.jpg" width="80px;" alt="万博览"/><br /><sub><b>万博览</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/董永乐.jpg" width="80px;" alt="董永乐"/><br /><sub><b>董永乐</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/℡夏别.jpg" width="80px;" alt="℡夏别"/><br /><sub><b>℡夏别</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/wangqiqi" target="_blank"><img src="./.image/open-source-guardian/周金旺.jpg" width="80px;" alt="周金旺"/><br /><sub><b>周金旺</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/无忧.jpg" width="80px;" alt="无忧"/><br /><sub><b>无忧</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/许多.jpg" width="80px;" alt="许多"/><br /><sub><b>许多</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/王军.jpg" width="80px;" alt="王军"/><br /><sub><b>王军</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/子非鱼.png" width="80px;" alt="子非鱼"/><br /><sub><b>子非鱼</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/苏州小朱.jpg" width="80px;" alt="苏州小朱"/><br /><sub><b>苏州小朱</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/空白.jpg" width="80px;" alt=""/><br /><sub><b></b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/HuaZy.jpg" width="80px;" alt="HuaZy"/><br /><sub><b>HuaZy</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/越南打印机网络监控电脑门禁何工.jpg" width="80px;" alt="越南打印机网络监控电脑门禁何工"/><br /><sub><b>越南打印机网络监控电脑门禁何工</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/熊勇辉.jpg" width="80px;" alt="熊勇辉"/><br /><sub><b>熊勇辉</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/旭.jpg" width="80px;" alt="旭"/><br /><sub><b>旭</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/心远.jpg" width="80px;" alt="心远"/><br /><sub><b>心远</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Mr.Peng.jpg" width="80px;" alt="Mr.Peng"/><br /><sub><b>Mr.Peng</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/舒韩春💭成都云速广告💭.jpg" width="80px;" alt="舒韩春💭成都云速广告💭"/><br /><sub><b>舒韩春💭成都云速广告💭</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/前进!.png" width="80px;" alt="前进!"/><br /><sub><b>前进!</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/永恒.png" width="80px;" alt="永恒"/><br /><sub><b>永恒</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Catwings.png" width="80px;" alt="Catwings"/><br /><sub><b>Catwings</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/刘振达.png" width="80px;" alt="刘振达"/><br /><sub><b>刘振达</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/雷沛奇.png" width="80px;" alt="雷沛奇"/><br /><sub><b>雷沛奇</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/CSL.png" width="80px;" alt="CSL"/><br /><sub><b>CSL</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/自胜.png" width="80px;" alt="自胜"/><br /><sub><b>自胜</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/朱江山.png" width="80px;" alt="朱江山"/><br /><sub><b>朱江山</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/安.png" width="80px;" alt="安"/><br /><sub><b>安</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/简单.png" width="80px;" alt="简单"/><br /><sub><b>简单</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/郝艳军.png" width="80px;" alt="郝艳军"/><br /><sub><b>郝艳军</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Star&Li.png" width="80px;" alt="Star&Li"/><br /><sub><b>Star&Li</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/工体东路.png" width="80px;" alt="工体东路"/><br /><sub><b>工体东路</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Sunder..png" width="80px;" alt="Sunder."/><br /><sub><b>Sunder.</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/程亮🌟.png" width="80px;" alt="程亮🌟"/><br /><sub><b>程亮🌟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/should.png" width="80px;" alt="should"/><br /><sub><b>should</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/黄国洪.png" width="80px;" alt="黄国洪"/><br /><sub><b>黄国洪</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Holmesian.png" width="80px;" alt="Holmesian"/><br /><sub><b>Holmesian</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Issac.png" width="80px;" alt="Issac"/><br /><sub><b>Issac</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/习惯.png" width="80px;" alt="习惯"/><br /><sub><b>习惯</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/黄杰.png" width="80px;" alt="黄杰"/><br /><sub><b>黄杰</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/唐智灵.png" width="80px;" alt="唐智灵"/><br /><sub><b>唐智灵</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/巴波儿奔🇨🇳.png" width="80px;" alt="巴波儿奔🇨🇳"/><br /><sub><b>巴波儿奔🇨🇳</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/冯振华.png" width="80px;" alt="冯振华"/><br /><sub><b>冯振华</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/风清扬.png" width="80px;" alt="风清扬"/><br /><sub><b>风清扬</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/take your time or.png" width="80px;" alt="take your time or"/><br /><sub><b>take your time or</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Rising徐.png" width="80px;" alt="Rising徐"/><br /><sub><b>Rising徐</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Mr.G.png" width="80px;" alt="Mr.G"/><br /><sub><b>Mr.G</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/吴翕然.png" width="80px;" alt="吴翕然"/><br /><sub><b>吴翕然</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/蓝天白云.png" width="80px;" alt="蓝天白云"/><br /><sub><b>蓝天白云</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Charlie.png" width="80px;" alt="Charlie"/><br /><sub><b>Charlie</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/胖哥.png" width="80px;" alt="胖哥"/><br /><sub><b>胖哥</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/王宪芳.png" width="80px;" alt="王宪芳"/><br /><sub><b>王宪芳</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/lk.png" width="80px;" alt="lk"/><br /><sub><b>lk</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/阿旺.png" width="80px;" alt="阿旺*"/><br /><sub><b>阿旺*</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/🍃一笑奈何🍃.png" width="80px;" alt="🍃一笑奈何🍃"/><br /><sub><b>🍃一笑奈何🍃</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/刘召.png" width="80px;" alt="刘召"/><br /><sub><b>刘召</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/🍻Jamie.png" width="80px;" alt="🍻Jamie"/><br /><sub><b>🍻Jamie</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/薛磊.png" width="80px;" alt="薛磊"/><br /><sub><b>薛磊</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Jack.png" width="80px;" alt="Jack"/><br /><sub><b>Jack</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/啊这.png" width="80px;" alt="啊这"/><br /><sub><b>啊这</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/在希望德田野上.png" width="80px;" alt="在希望德田野上"/><br /><sub><b>在希望德田野上</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/莫建民.png" width="80px;" alt="莫建民"/><br /><sub><b>莫建民</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/马景祥.png" width="80px;" alt="马景祥"/><br /><sub><b>马景祥</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/谭远彪.png" width="80px;" alt="谭远彪"/><br /><sub><b>谭远彪</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/一杯陈豆浆🥲🥲.png" width="80px;" alt="一杯陈豆浆🥲🥲"/><br /><sub><b>一杯陈豆浆🥲🥲</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/chen.png" width="80px;" alt="chen"/><br /><sub><b>chen</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/xingzhedu2030.png" width="80px;" alt="xingzhedu2030"/><br /><sub><b>xingzhedu2030</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/machh.png" width="80px;" alt="machh"/><br /><sub><b>machh</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/开炫🍊🍊🍊.png" width="80px;" alt="开炫🍊🍊🍊"/><br /><sub><b>开炫🍊🍊🍊</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Dark.png" width="80px;" alt="Dark"/><br /><sub><b>Dark</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/A-Tree.png" width="80px;" alt="A-Tree"/><br /><sub><b>A-Tree</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/陈.png" width="80px;" alt="陈"/><br /><sub><b>陈</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/月半.png" width="80px;" alt="月半"/><br /><sub><b>月半</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/吴军.png" width="80px;" alt="吴军"/><br /><sub><b>吴军</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/青衫.png" width="80px;" alt="青衫"/><br /><sub><b>青衫</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/梓淇東來.png" width="80px;" alt="梓淇東來"/><br /><sub><b>梓淇東來</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/潇潇.png" width="80px;" alt="潇潇"/><br /><sub><b>潇潇</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/依依.png" width="80px;" alt="依依"/><br /><sub><b>依依</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/金·郁金香.png" width="80px;" alt="金·郁金香"/><br /><sub><b>金·郁金香</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/David.png" width="80px;" alt="David"/><br /><sub><b>David</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/榕德天锐-邱国城.png" width="80px;" alt="榕德天锐-邱国城"/><br /><sub><b>榕德天锐-邱国城</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Wzs.png" width="80px;" alt="Wzs"/><br /><sub><b>Wzs</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/张军伟.png" width="80px;" alt="张军伟"/><br /><sub><b>张军伟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/菜rainbow狗.png" width="80px;" alt="菜rainbow狗"/><br /><sub><b>菜rainbow狗</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/闻达.png" width="80px;" alt="闻达"/><br /><sub><b>闻达</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/银之匙.png" width="80px;" alt="银之匙"/><br /><sub><b>银之匙</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/命中注定.png" width="80px;" alt="命中注定"/><br /><sub><b>命中注定</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/..png" width="80px;" alt="..."/><br /><sub><b>...</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/爱吃小柚子.png" width="80px;" alt="爱吃小柚子"/><br /><sub><b>爱吃小柚子</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/草原雄鹰.png" width="80px;" alt="草原雄鹰"/><br /><sub><b>草原雄鹰</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/顺流致远.png" width="80px;" alt="顺流致远"/><br /><sub><b>顺流致远</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/香草口味.png" width="80px;" alt="香草口味"/><br /><sub><b>香草口味</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/雨落流殇.png" width="80px;" alt="雨落流殇"/><br /><sub><b>雨落流殇</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/弱电安防.png" width="80px;" alt="弱电安防"/><br /><sub><b>弱电安防</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/山里人.png" width="80px;" alt="山里人"/><br /><sub><b>山里人</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/诗如画.png" width="80px;" alt="诗如画"/><br /><sub><b>诗如画</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/星空🌃.png" width="80px;" alt="星空🌃"/><br /><sub><b>星空🌃</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/楠哥.png" width="80px;" alt="楠哥"/><br /><sub><b>楠哥</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/蜗牛.png" width="80px;" alt="蜗牛"/><br /><sub><b>蜗牛</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/大周.png" width="80px;" alt="大周"/><br /><sub><b>大周</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/歌德de花烛.png" width="80px;" alt="歌德de花烛"/><br /><sub><b>歌德de花烛</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/noname.png" width="80px;" alt="noname"/><br /><sub><b>noname</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/兔子.png" width="80px;" alt="兔子"/><br /><sub><b>兔子</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/ThinkInStack.png" width="80px;" alt="ThinkInStack"/><br /><sub><b>ThinkInStack</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/Louis.png" width="80px;" alt="Louis"/><br /><sub><b>Louis</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/胡首凡 梯控门禁五方对讲.png" width="80px;" alt="胡首凡 梯控门禁五方对讲"/><br /><sub><b>胡首凡 梯控门禁五方对讲</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/袁建华.png" width="80px;" alt="袁建华"/><br /><sub><b>袁建华</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/空空.png" width="80px;" alt="空空"/><br /><sub><b>空空</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/阿涛.png" width="80px;" alt="阿涛"/><br /><sub><b>阿涛</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/NULL.png" width="80px;" alt="NULL"/><br /><sub><b>NULL</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/一片天.png" width="80px;" alt="一片天"/><br /><sub><b>一片天</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/小满藏舟.png" width="80px;" alt="小满藏舟"/><br /><sub><b>小满藏舟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/M.png" width="80px;" alt="M"/><br /><sub><b>M</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/舍得.png" width="80px;" alt="舍得"/><br /><sub><b>舍得</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/默者.png" width="80px;" alt="默者"/><br /><sub><b>默者</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/火车叨位去、.png" width="80px;" alt="火车叨位去、"/><br /><sub><b>火车叨位去、</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/payne.png" width="80px;" alt="payne"/><br /><sub><b>payne</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/滕虎.png" width="80px;" alt="滕虎"/><br /><sub><b>滕虎</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/天天.png" width="80px;" alt="天天"/><br /><sub><b>天天</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/王超.png" width="80px;" alt="王超"/><br /><sub><b>王超</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/南北.png" width="80px;" alt="南北"/><br /><sub><b>南北</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/最后的轻语.png" width="80px;" alt="最后的轻语"/><br /><sub><b>最后的轻语</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/西乡一粒沙.png" width="80px;" alt="西乡一粒沙"/><br /><sub><b>西乡一粒沙</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/yang.png" width="80px;" alt="yang"/><br /><sub><b>yang</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/何行者.png" width="80px;" alt="何行者"/><br /><sub><b>何行者</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/在路上.png" width="80px;" alt="在路上"/><br /><sub><b>在路上</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/ANDY.png" width="80px;" alt="ANDY"/><br /><sub><b>ANDY</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/冯.png" width="80px;" alt="冯"/><br /><sub><b>冯</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/忘记时间.png" width="80px;" alt="忘记时间"/><br /><sub><b>忘记时间</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/A许庆.png" width="80px;" alt="A许庆"/><br /><sub><b>A许庆</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/刘兆中📶⁵ᴳ.png" width="80px;" alt="刘兆中📶⁵ᴳ"/><br /><sub><b>刘兆中📶⁵ᴳ</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/莫斯克.png" width="80px;" alt="莫斯克"/><br /><sub><b>莫斯克</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/赵欢.png" width="80px;" alt="赵欢"/><br /><sub><b>赵欢</b></sub></a></td>
    </tr>
  </tbody>
</table>

## 🏆 最佳实践者

他们是将 EasyAIoT 从「可用」推向「好用、用好」的先行者——以下各位已完成 EasyAIoT 项目部署或业务场景落地，其探索与成果为社区树立了可复制、可参考的标杆，我们向这些卓越践行者致以崇高敬意与衷心祝贺！以下排名不分先后：

<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/℡夏别.jpg" width="80px;" alt="℡夏别"/><br /><sub><b>℡夏别</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/YiYaYiYaho.jpg" width="80px;" alt="YiYaYiYaho"/><br /><sub><b>YiYaYiYaho</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/冯.jpg" width="80px;" alt="冯"/><br /><sub><b>冯</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/在希望德田野上.jpg" width="80px;" alt="在希望德田野上"/><br /><sub><b>在希望德田野上</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/漠然.png" width="80px;" alt="漠然"/><br /><sub><b>漠然</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/爱吃小柚子.jpg" width="80px;" alt="爱吃小柚子"/><br /><sub><b>爱吃小柚子</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/Wzs.jpg" width="80px;" alt="Wzs"/><br /><sub><b>Wzs</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/Dark.jpg" width="80px;" alt="Dark"/><br /><sub><b>Dark</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/best-practitioner/刘延波.jpg" width="80px;" alt="刘延波"/><br /><sub><b>刘延波</b></sub></a></td>
    </tr>
  </tbody>
</table>

## 🙏 致谢

感谢以下各位对本项目包括但不限于代码贡献、问题反馈、资金捐赠等各种方式的支持！以下排名不分先后：
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/默者.png" width="80px;" alt="默者"/><br /><sub><b>默者</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/小满藏舟.png" width="80px;" alt="小满藏舟"/><br /><sub><b>小满藏舟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/空空.png" width="80px;" alt="空空"/><br /><sub><b>空空</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/chen_jialin123" target="_blank"><img src="./.image/sponsor/陈家林.png" width="80px;" alt="陈家林"/><br /><sub><b>陈家林</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/NULL.png" width="80px;" alt="NULL"/><br /><sub><b>NULL</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/陈勇至.jpg" width="80px;" alt="陈勇至"/><br /><sub><b>陈勇至</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Dark.jpg" width="80px;" alt="Dark"/><br /><sub><b>Dark</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/machh" target="_blank"><img src="./.image/sponsor/machh.jpg" width="80px;" alt="machh"/><br /><sub><b>machh</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/三块两毛四.jpg" width="80px;" alt="三块两毛四"/><br /><sub><b>三块两毛四</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/物语晨水²⁰²⁶.jpg" width="80px;" alt="物语晨水²⁰²⁶"/><br /><sub><b>物语晨水²⁰²⁶</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/L_Z_M" target="_blank"><img src=".image/sponsor/玖零。.jpg" width="80px;" alt="玖零。"/><br /><sub><b>玖零。</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/36436022" target="_blank"><img src=".image/sponsor/金鸿伟.jpg" width="80px;" alt="金鸿伟"/><br /><sub><b>金鸿伟</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/cnlijf" target="_blank"><img src="./.image/sponsor/李江峰.jpg" width="80px;" alt="李江峰"/><br /><sub><b>李江峰</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src=".image/sponsor/Best%20Yao.jpg" width="80px;" alt="Best Yao"/><br /><sub><b>Best Yao</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/weiloser" target="_blank"><img src=".image/sponsor/无为而治.jpg" width="80px;" alt="无为而治"/><br /><sub><b>无为而治</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/shup092_admin" target="_blank"><img src="./.image/sponsor/shup.jpg" width="80px;" alt="shup"/><br /><sub><b>shup</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/gampa" target="_blank"><img src="./.image/sponsor/也许.jpg" width="80px;" alt="也许"/><br /><sub><b>也许</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/leishaozhuanshudi" target="_blank"><img src="./.image/sponsor/⁰ʚᦔrꫀꪖꪑ⁰ɞ%20..jpg" width="80px;" alt="⁰ʚᦔrꫀꪖꪑ⁰ɞ ."/><br /><sub><b>⁰ʚᦔrꫀꪖꪑ⁰ɞ .</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/fateson" target="_blank"><img src="./.image/sponsor/逆.jpg" width="80px;" alt="逆"/><br /><sub><b>逆</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/dongGezzz_admin" target="_blank"><img src="./.image/sponsor/廖东旺.jpg" width="80px;" alt="廖东旺"/><br /><sub><b>廖东旺</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/huangzhen1993" target="_blank"><img src="./.image/sponsor/黄振.jpg" width="80px;" alt="黄振"/><br /><sub><b>黄振</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/fengchunshen" target="_blank"><img src="./.image/sponsor/春生.jpg" width="80px;" alt="春生"/><br /><sub><b>春生</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mrfox_wang" target="_blank"><img src="./.image/sponsor/贵阳王老板.jpg" width="80px;" alt="贵阳王老板"/><br /><sub><b>贵阳王老板</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/haobaby" target="_blank"><img src="./.image/sponsor/hao_chen.jpg" width="80px;" alt="hao_chen"/><br /><sub><b>hao_chen</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/finalice" target="_blank"><img src="./.image/sponsor/尽千.jpg" width="80px;" alt="尽千"/><br /><sub><b>尽千</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/yuer629" target="_blank"><img src="./.image/sponsor/yuer629.jpg" width="80px;" alt="yuer629"/><br /><sub><b>yuer629</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/cai-peikai/ai-project" target="_blank"><img src="./.image/sponsor/kong.jpg" width="80px;" alt="kong"/><br /><sub><b>kong</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/HB1731276584" target="_blank"><img src="./.image/sponsor/岁月静好.jpg" width="80px;" alt="岁月静好"/><br /><sub><b>岁月静好</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/hy5128" target="_blank"><img src="./.image/sponsor/Kunkka.jpg" width="80px;" alt="Kunkka"/><br /><sub><b>Kunkka</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/guo-dida" target="_blank"><img src="./.image/sponsor/灬.jpg" width="80px;" alt="灬"/><br /><sub><b>灬</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/XyhBill" target="_blank"><img src="./.image/sponsor/Mr.LuCkY.jpg" width="80px;" alt="Mr.LuCkY"/><br /><sub><b>Mr.LuCkY</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/timeforeverz" target="_blank"><img src="./.image/sponsor/泓.jpg" width="80px;" alt="泓"/><br /><sub><b>泓</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mySia" target="_blank"><img src="./.image/sponsor/i.jpg" width="80px;" alt="i"/><br /><sub><b>i</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/依依.jpg" width="80px;" alt="依依"/><br /><sub><b>依依</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/sunbirder" target="_blank"><img src="./.image/sponsor/小菜鸟先飞.jpg" width="80px;" alt="小菜鸟先飞"/><br /><sub><b>小菜鸟先飞</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/mmy0" target="_blank"><img src="./.image/sponsor/追溯未来-_-.jpg" width="80px;" alt="追溯未来"/><br /><sub><b>追溯未来</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/ccqingshan" target="_blank"><img src="./.image/sponsor/青衫.jpg" width="80px;" alt="青衫"/><br /><sub><b>青衫</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/jiangchunJava" target="_blank"><img src="./.image/sponsor/Fae.jpg" width="80px;" alt="Fae"/><br /><sub><b>Fae</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/huang-xiangtai" target="_blank"><img src="./.image/sponsor/憨憨.jpg" width="80px;" alt="憨憨"/><br /><sub><b>憨憨</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/gu-beichen-starlight" target="_blank"><img src="./.image/sponsor/文艺小青年.jpg" width="80px;" alt="文艺小青年"/><br /><sub><b>文艺小青年</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/zhangnanchao" target="_blank"><img src="./.image/sponsor/lion.jpg" width="80px;" alt="lion"/><br /><sub><b>lion</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/yupccc" target="_blank"><img src="./.image/sponsor/汪汪队立大功.jpg" width="80px;" alt="汪汪队立大功"/><br /><sub><b>汪汪队立大功</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/wcjjjjjjj" target="_blank"><img src="./.image/sponsor/wcj.jpg" width="80px;" alt="wcj"/><br /><sub><b>wcj</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/hufanglei" target="_blank"><img src="./.image/sponsor/🌹怒放de生命😋.jpg" width="80px;" alt="怒放de生命"/><br /><sub><b>怒放de生命</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/juyunsuan" target="_blank"><img src="./.image/sponsor/蓝速传媒.jpg" width="80px;" alt="蓝速传媒"/><br /><sub><b>蓝速传媒</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/ADVISORYZ" target="_blank"><img src=".image/sponsor/ADVISORYZ.jpg" width="80px;" alt="ADVISORYZ"/><br /><sub><b>ADVISORYZ</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/dongxinji" target="_blank"><img src="./.image/sponsor/take%20your%20time%20or.jpg" width="80px;" alt="take your time or"/><br /><sub><b>take your time or</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/xu756" target="_blank"><img src="./.image/sponsor/碎碎念..jpg" width="80px;" alt="碎碎念."/><br /><sub><b>碎碎念.</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/lwisme" target="_blank"><img src="./.image/sponsor/北街.jpg" width="80px;" alt="北街"/><br /><sub><b>北街</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/yu-xinyan71" target="_blank"><img src="./.image/sponsor/Dorky%20TAT.jpg" width="80px;" alt="Dorky TAT"/><br /><sub><b>Dorky TAT</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/chenxiaohong" target="_blank"><img src=".image/sponsor/右耳向西.jpg" width="80px;" alt="右耳向西"/><br /><sub><b>右耳向西</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/派大星" target="_blank"><img src="./.image/sponsor/派大星.jpg" width="80px;" alt="派大星"/><br /><sub><b>派大星</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/wz_vue_gitee_181" target="_blank"><img src="./.image/sponsor/棒槌🧿🍹🍹🧿.jpg" width="80px;" alt="棒槌🧿🍹🍹🧿"/><br /><sub><b>棒槌</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/nctwo" target="_blank"><img src=".image/sponsor/信微输传助手.jpg" width="80px;" alt="信微输传助手"/><br /><sub><b>信微输传助手</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/l9999_admin" target="_blank"><img src=".image/sponsor/一往无前.jpg" width="80px;" alt="一往无前"/><br /><sub><benen>一往无前</benen></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/stenin" target="_blank"><img src="./.image/sponsor/Charon.jpg" width="80px;" alt="Charon"/><br /><sub><b>Charon</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/zhao-yihuiwifi" target="_blank"><img src="./.image/sponsor/赵WIFI..jpg" width="80px;" alt="赵WIFI."/><br /><sub><b>赵WIFI.</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/Yang619" target="_blank"><img src="./.image/sponsor/Chao..jpg" width="80px;" alt="Chao."/><br /><sub><b>Chao.</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/lcrsd123" target="_blank"><img src=".image/sponsor/城市稻草人.jpg" width="80px;" alt="城市稻草人"/><br /><sub><b>城市稻草人</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/Mo_bai1016" target="_blank"><img src=".image/sponsor/Bug写手墨白.jpg" width="80px;" alt="Bug写手墨白"/><br /><sub><b>Bug写手墨白</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/kevinosc_admin" target="_blank"><img src=".image/sponsor/kevin.jpg" width="80px;" alt="kevin"/><br /><sub><b>kevin</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/lhyicn" target="_blank"><img src=".image/sponsor/童年.jpg" width="80px;" alt="童年"/><br /><sub><b>童年</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/dubai100" target="_blank"><img src="./.image/sponsor/sherry金.jpg" width="80px;" alt="sherry金"/><br /><sub><b>sherry金</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/℡夏别.jpg" width="80px;" alt="℡夏别"/><br /><sub><b>℡夏别</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/翠翠草原.jpg" width="80px;" alt="翠翠草原"/><br /><sub><b>翠翠草原</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/慕容曦.jpg" width="80px;" alt="慕容曦"/><br /><sub><b>慕容曦</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Tyrion.jpg" width="80px;" alt="Tyrion"/><br /><sub><b>Tyrion</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/大漠孤烟.jpg" width="80px;" alt="大漠孤烟"/><br /><sub><b>大漠孤烟</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Return.jpg" width="80px;" alt="Return"/><br /><sub><b>Return</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/一杯拿铁.jpg" width="80px;" alt="一杯拿铁"/><br /><sub><b>一杯拿铁</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Thuri.jpg" width="80px;" alt="Thuri"/><br /><sub><b>Thuri</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Liu.jpg" width="80px;" alt="Liu"/><br /><sub><b>Liu</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/三金.jpg" width="80px;" alt="三金"/><br /><sub><b>三金</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/ZPort.jpg" width="80px;" alt="ZPort"/><br /><sub><b>ZPort</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Li.jpg" width="80px;" alt="Li"/><br /><sub><b>Li</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/嘉树.jpg" width="80px;" alt="嘉树"/><br /><sub><b>嘉树</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/俊采星驰.jpg" width="80px;" alt="俊采星驰"/><br /><sub><b>俊采星驰</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/oi.jpg" width="80px;" alt="oi"/><br /><sub><b>oi</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/ZhangY_000.jpg" width="80px;" alt="ZhangY_000"/><br /><sub><b>ZhangY_000</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/℡夏别.jpg" width="80px;" alt="℡夏别"/><br /><sub><b>℡夏别</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/张瑞麟.jpg" width="80px;" alt="张瑞麟"/><br /><sub><b>张瑞麟</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Lion King.jpg" width="80px;" alt="Lion King"/><br /><sub><b>Lion King</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Frank.jpg" width="80px;" alt="Frank"/><br /><sub><b>Frank</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/徐梦阳.jpg" width="80px;" alt="徐梦阳"/><br /><sub><b>徐梦阳</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/九月.jpg" width="80px;" alt="九月"/><br /><sub><b>九月</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/tangl伟.jpg" width="80px;" alt="tangl伟"/><br /><sub><b>tangl伟</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/冯瑞伦.jpg" width="80px;" alt="冯瑞伦"/><br /><sub><b>冯瑞伦</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/杨林.jpg" width="80px;" alt="杨林"/><br /><sub><b>杨林</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/梧桐有语。.jpg" width="80px;" alt="梧桐有语。"/><br /><sub><b>梧桐有语。</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/歌德de花烛.jpg" width="80px;" alt="歌德de花烛"/><br /><sub><b>歌德de花烛</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/泥嚎.jpg" width="80px;" alt="泥嚎"/><br /><sub><b>泥嚎</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/翠翠草原.jpg" width="80px;" alt="翠翠草原"/><br /><sub><b>翠翠草原</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/胡泽龙.jpg" width="80px;" alt="胡泽龙"/><br /><sub><b>胡泽龙</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/苏叶.jpg" width="80px;" alt="苏叶"/><br /><sub><b>苏叶</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/裴先生.jpg" width="80px;" alt="裴先生"/><br /><sub><b>裴先生</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/谭远彪.jpg" width="80px;" alt="谭远彪"/><br /><sub><b>谭远彪</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/陈祺.jpg" width="80px;" alt="陈祺"/><br /><sub><b>陈祺</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/零点就睡.jpg" width="80px;" alt="零点就睡"/><br /><sub><b>零点就睡</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/风之羽.jpg" width="80px;" alt="风之羽"/><br /><sub><b>风之羽</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/fufeng1908" target="_blank"><img src="./.image/sponsor/王守仁.jpg" width="80px;" alt="王守仁"/><br /><sub><b>王守仁</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/kaigejava" target="_blank"><img src="./.image/sponsor/狼ྂ图ྂ腾ྂ.jpg" width="80px;" alt="狼图腾"/><br /><sub><b>狼图腾</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/马到成功.jpg" width="80px;" alt="马到成功"/><br /><sub><b>马到成功</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/做生活的高手.jpg" width="80px;" alt="做生活的高手"/><br /><sub><b>做生活的高手</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/清欢之恋.jpg" width="80px;" alt="清欢之恋"/><br /><sub><b>清欢之恋</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/绝域时空.jpg" width="80px;" alt="绝域时空"/><br /><sub><b>绝域时空</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/风雨.jpg" width="80px;" alt="风雨"/><br /><sub><b>风雨</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Nicola.jpg" width="80px;" alt="Nicola"/><br /><sub><b>Nicola</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/云住.jpg" width="80px;" alt="云住"/><br /><sub><b>云住</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Mr.Zhang.jpg" width="80px;" alt="Mr.Zhang"/><br /><sub><b>Mr.Zhang</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/剑.jpg" width="80px;" alt="剑"/><br /><sub><b>剑</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/shen.jpg" width="80px;" alt="shen"/><br /><sub><b>shen</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/嗯.jpg" width="80px;" alt="嗯"/><br /><sub><b>嗯</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/周华.jpg" width="80px;" alt="周华"/><br /><sub><b>周华</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/太阳鸟.jpg" width="80px;" alt="太阳鸟"/><br /><sub><b>太阳鸟</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/了了.jpg" width="80px;" alt="了了"/><br /><sub><b>了了</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/第七次日落.jpg" width="80px;" alt="第七次日落"/><br /><sub><b>第七次日落</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/npc.jpg" width="80px;" alt="npc"/><br /><sub><b>npc</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/承担不一样的天空.jpg" width="80px;" alt="承担不一样的天空"/><br /><sub><b>承担不一样的天空</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/铁木.jpg" width="80px;" alt="铁木"/><br /><sub><b>铁木</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Orion.jpg" width="80px;" alt="Orion"/><br /><sub><b>Orion</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/森源-金福洪.jpg" width="80px;" alt="森源-金福洪"/><br /><sub><b>森源-金福洪</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/薛继超.jpg" width="80px;" alt="薛继超"/><br /><sub><b>薛继超</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/虎虎虎.jpg" width="80px;" alt="虎虎虎"/><br /><sub><b>虎虎虎</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Everyman.jpg" width="80px;" alt="Everyman"/><br /><sub><b>Everyman</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/NXL.jpg" width="80px;" alt="NXL"/><br /><sub><b>NXL</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/孙涛.jpg" width="80px;" alt="孙涛"/><br /><sub><b>孙涛</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/bcake" target="_blank"><img src=".image/sponsor/大饼.jpg" width="80px;" alt="大饼"/><br /><sub><b>大饼</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/hrsjw1.jpg" width="80px;" alt="hrsjw1"/><br /><sub><b>hrsjw1</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/linguanghuan.jpg" width="80px;" alt="linguanghuan"/><br /><sub><b>linguanghuan</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/YiYaYiYaho.jpg" width="80px;" alt="YiYaYiYaho"/><br /><sub><b>YiYaYiYaho</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/慢慢慢.jpg" width="80px;" alt="慢慢慢"/><br /><sub><b>慢慢慢</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/lilOne.jpg" width="80px;" alt="lilOne"/><br /><sub><b>lilOne</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src=".image/sponsor/icon.jpg" width="80px;" alt="icon"/><br /><sub><b>icon</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/jiang4yu" target="_blank"><img src=".image/sponsor/山寒.jpg" width="80px;" alt="山寒"/><br /><sub><b>山寒</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/baobaomo" target="_blank"><img src="./.image/sponsor/放学丶别走.jpg" width="80px;" alt="放学丶别走"/><br /><sub><b>放学丶别走</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/wagger" target="_blank"><img src="./.image/sponsor/春和.jpg" width="80px;" alt="春和"/><br /><sub><b>春和</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/longbinwu" target="_blank"><img src="./.image/sponsor/章鱼小丸子.jpg" width="80px;" alt="章鱼小丸子"/><br /><sub><b>章鱼小丸子</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/Catwings.jpg" width="80px;" alt="Catwings"/><br /><sub><b>Catwings</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/小工头.jpg" width="80px;" alt="小工头"/><br /><sub><b>小工头</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/西乡一粒沙.jpg" width="80px;" alt="西乡一粒沙"/><br /><sub><b>西乡一粒沙</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/爱吃小柚子.jpg" width="80px;" alt="爱吃小柚子"/><br /><sub><b>爱吃小柚子</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/阿龙.jpg" width="80px;" alt="阿龙"/><br /><sub><b>阿龙</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/雨落流殇.jpg" width="80px;" alt="雨落流殇"/><br /><sub><b>雨落流殇</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/遗忘的星空.jpg" width="80px;" alt="遗忘的星空"/><br /><sub><b>遗忘的星空</b></sub></a></td>
    </tr>
    <tr>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/achieve275" target="_blank"><img src="./.image/sponsor/Achieve_Xu.jpg" width="80px;" alt="Achieve_Xu"/><br /><sub><b>Achieve_Xu</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/nicholasld" target="_blank"><img src="./.image/sponsor/NicholasLD.jpg" width="80px;" alt="NicholasLD"/><br /><sub><b>NicholasLD</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/常康.jpg" width="80px;" alt="常康"/><br /><sub><b>常康</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/嘎嗝.jpg" width="80px;" alt="嘎嗝"/><br /><sub><b>嘎嗝</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/曹.jpg" width="80px;" alt="曹"/><br /><sub><b>曹</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/滔滔.jpg" width="80px;" alt="滔滔"/><br /><sub><b>滔滔</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/狗娃.jpg" width="80px;" alt="狗娃"/><br /><sub><b>狗娃</b></sub></a></td>
    </tr>
  </tbody>
</table>

## 💡 期望

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
欢迎提出更好的意见，帮助完善 easyaiot
</p>

## 📄 版权

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
翱翔的雄库鲁/easyaiot 采用 <a href="https://gitee.com/soaring-xiongkulu/easyaiot/blob/main/LICENSE" style="color: #3498db; text-decoration: none; font-weight: 600;">MIT LICENSE</a> 开源协议。我们致力于推动 AI 技术的普及与发展，让更多人能够自由使用和受益于这项技术。
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
<strong>使用许可</strong>：个人与企业可 100% 免费使用，无需保留作者、Copyright 信息。我们相信技术的价值在于被广泛使用和持续创新，而非被版权束缚。希望您能够自由地使用、修改、分发本项目，让 AI 技术真正惠及每一个人。
</p>
