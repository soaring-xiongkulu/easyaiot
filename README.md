# EasyAIoT (Cloud-Edge-Device Integrated Intelligent Algorithm Application Platform)

[![Gitee star](https://gitee.com/volara/easyaiot/badge/star.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/stargazers)
[![Gitee fork](https://gitee.com/volara/easyaiot/badge/fork.svg?theme=gvp)](https://gitee.com/soaring-xiongkulu/easyaiot/members)

<p style="font-size: 16px; line-height: 1.8; color: #555; font-weight: 400; margin: 20px 0;">
My vision is for this system to be accessible worldwide, achieving truly zero barriers to AI. Everyone should experience the benefits of AI, not just a privileged few.
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

## 🌐 Official Website

EasyAIoT Official Website: [http://36.111.47.113:8090/](http://36.111.47.113:8090/)

Product introduction, feature overview, four hardware tiers, installer downloads, and documentation entry—so you can quickly understand the platform and start deploying.

## 📖 Project Overview

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
<strong>EasyAIoT</strong> (Easy AI Internet of Things) is a <strong>cloud-edge-device integrated intelligent algorithm application platform</strong> dedicated to deeply fusing artificial intelligence with the Internet of Things—enabling cameras, sensors, and edge compute to work together on site. From device onboarding and data collection to real-time visual analysis, intelligent assessment, and alert orchestration, the entire chain runs on a single software stack.
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Many smart IoT projects hit the same wall at deployment: video systems, device platforms, and algorithm services live in silos—integration is costly, operations are fragmented, and scaling is painful. <strong>EasyAIoT resolves this with one platform</strong>—the same software can run a closed smart loop on a <strong>2 GB</strong> edge standalone (edge), land on a 4–8 GB edge box (mini) for single-point intelligence, ride AI all-in-one cameras for floor-level coverage, or pack into an enterprise full-stack appliance with IoT management, massive video access, and AI analysis—no multiple versions to maintain, no repeated integration across heterogeneous systems.
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
The platform comprises core modules including <strong>WEB, APP, DEVICE, EDGE, SENTINEL, VIDEO, RTC, AI, RUNTIME, POST, VISUALIZE, TRANSFORM, PANEL, IDEA, HARNESS, and SITE</strong>, with <strong>COMPILE</strong> handling multi-platform packaging and delivery (including Ubuntu / CentOS·RHEL <strong>7–9</strong> (x86 + <strong>CentOS ARM</strong>, packages per el7/el8/el9) / <strong>Kylin (麒麟) / openEuler (欧拉)</strong> / Windows / macOS / ARM). On the capability side, the platform covers GB28181 / ONVIF multi-protocol camera access, <strong>RTC consumer-camera P2P bridging</strong> (based on go2rtc, covering <strong>Tapo, Tuya, Ring, Nest, Xiaomi, Wyze, DoorBird, GoPro, and Roborock</strong>—store Tapo fill-in, Tuya white-label onboarding, overseas Ring/Nest doorbells, Xiaomi reuse, Wyze low-cost scale-out, DoorBird intercom, GoPro mobile views, Roborock vacuum cameras—with one-click Web onboarding into unified video and AI judgment), <strong>DJI dock and drone aerial view access</strong>, real-time / snapshot / patrol algorithm tasks, <strong>RUNTIME native high-speed execution layer</strong> (compiled binary owns pull/decode, YOLO inference, boxed push, and multi-channel raw forward—lower CPU/memory and steadier latency than interpreted paths; one binary covers realtime / snap / patrol / forward), YOLO object detection and SAM zero-shot auto-annotation, face/plate recognition, <strong>POST custom judgment</strong> (after detection, filter and composite rules before alerting—change rules without retraining models), federated compute cluster scheduling, <strong>SENTINEL cluster-node sentinel</strong> (continuously reveals per-node readiness and schedulable business capacity, requests environment fill-in when gaps appear, and dispatches work by real capability), and <strong>Infinite Federated Edge Cluster mode</strong> (ordinary development boards ready out of the box, on-site intelligence for local decisions, alerts and evidence automatically aggregated to the cloud, compute scaling with business as needed), plus MQTT / TCP / HTTP / Modbus-TCP / Modbus-RTU / OPC UA IoT device lifecycle management, with the <strong>EDGE C# edge collection runtime</strong> handling Modbus RTU/TCP, OPC UA, and other on-site industrial protocols via pluggable collectors, local scheduling, and MQTT cloud-edge integration, plus <strong>visualization dashboards and Web SCADA configuration</strong>, so device data can be displayed as command-center situational awareness and mapped back to process screens; plus the new <strong>POST custom judgment service</strong>, which turns detections into field-ready business events—fewer false alarms, configurable rules, trial runs before go-live; plus the <strong>TRANSFORM multidirectional data-flow engine</strong>, which delivers platform-side business events to external systems such as MES / ERP / CRM / WMS by contract—multi-party integration that is configurable, traceable, and reusable; and the companion <strong>PANEL delivery & watch entry</strong>, so appliances can be installed and accepted on arrival day, and watch/troubleshooting no longer wait on developers running remote commands every time; plus the <strong>SITE official website</strong> to present product value, four hardware tiers, and installer entry—so visitors understand first, then download and deploy; and <strong>IDEA community cloud IDE</strong> so contributors can open the full repo in a browser, co-create with GitHub Copilot, publish local changes, and submit PRs—turning open-source collaboration from “set up the environment first” into “open and edit”. On the experience side, the Web console and mobile App / mini-program are capability-aligned, so command centers and field inspections share the same business logic—handle incidents anytime, anywhere; and the new <strong>ANDROID / IOS / HARMONYOS packaging shells</strong> ship that mobile experience as installable apps on every mainstream phone OS (APK / IPA / HAP) from one frontend codebase, with one-command builds and unified version management.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>In one sentence:</strong> EasyAIoT = AI + IoT—interconnect everything while enabling intelligent vision and intelligent control for everything.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
📄 For a more complete illustrated introduction, see <a href=".doc/项目介绍/EasyAIoT项目介绍 V2.0.pptx" style="color: #3498db; text-decoration: none; font-weight: 600;">EasyAIoT Project Introduction V2.0 (PPT)</a>, and <a href=".doc/项目介绍/AI视频监控分析平台.pdf" style="color: #3498db; text-decoration: none; font-weight: 600;">AI Video Surveillance Analytics Platform (PDF)</a>. For day-to-day platform operations after deployment, see the <a href=".doc/操作手册/README.md" style="color: #3498db; text-decoration: none; font-weight: 600;">Platform Operations Manual</a>.
</p>

### 🏆 Certificates

| | | | |
|:---:|:---:|:---:|:---:|
| <img src=".image/certificates/gitee-oss-award-2025-top1.jpg" width="200" alt="Gitee Annual OSS Award 2025 · Industrial Software Track Top 1"> | <img src=".image/certificates/gitee-2000-stars.jpg" width="200" alt="Gitee 2000+ Stars"> | <img src=".image/certificates/gitee-gvp-2025.jpg" width="200" alt="Gitee GVP 2025 · Most Valuable Open Source Project"> | <img src=".image/certificates/csdn-blog-expert.jpg" width="200" alt="CSDN Blog Expert"> |

## 🚀 Quick Start

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Open the README and mutter: “Can my little box even run this?” — <strong>Yes. Don’t panic.</strong>
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Lightest tier, containers use about <strong>1 GB</strong> total. Cameras, real-time analysis, smart alerts—small machines still close the loop. Spin up that old laptop first; upgrade later when you’re hooked.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>Three steps (Linux):</strong>
</p>

```bash
git clone https://gitee.com/volara/easyaiot.git
cd easyaiot

# Option A (recommended)
EASYAIOT_DEPLOY_PROFILE=edge sudo bash .scripts/docker/install_linux.sh install

# Option B
# sudo bash .scripts/docker/install_linux.sh edge install
```

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0;">
Then open <code>https://&lt;server-ip&gt;:8888</code> — default <code>admin</code> / <code>admin123</code>. Sanity-check:
</p>

```bash
.scripts/docker/install_linux.sh verify
# Optional: peek at memory vs the tier budget
.scripts/docker/install_linux.sh resources
```

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0;">
All green? You’re done—easier than you feared. Go grab that coffee early.
</p>

## 🌟 Some Thoughts on the Project

### 📍 Project Positioning

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT is a cloud-edge-device integrated intelligent IoT platform that focuses on the deep integration of AI and IoT. Through core capabilities such as algorithm task management, real-time stream analysis, and model service cluster inference, the platform achieves a complete closed-loop from device access to data collection, AI analysis, and intelligent decision-making, truly realizing interconnected everything and intelligent control of everything.
</p>

### 🎛️ PANEL: Install & Accept on Arrival Day—Watch Duty Without Waiting for Remote Devs

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Smart IoT projects most often stall at the last mile: the machine is on site, yet <strong>it won't install, won't pass acceptance, and when something breaks you can only wait for developers to run remote commands</strong>—on-site cost and acceptance cycles are held hostage by people. PANEL is an <strong>independent delivery and watch entry</strong> for integrators and field ops—one-click install by tier, see whole-machine health and dependencies, start/stop services and inspect logs on the spot; <strong>even before the business console is ready, you can bring up, hold, and hand over the appliance</strong>, turning “machine on site → platform usable → acceptance-ready” from waiting on people into a same-day closed loop.
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Shorter acceptance cycles</strong>: On arrival pick edge / mini / standard / full, install, and see progress and results on the spot—fewer “stuck halfway, unsure where” cases from incomplete commands or skipped steps; PoC and production delivery clear acceptance faster</li>
  <li><strong>Lower on-site and remote cost</strong>: Whether containers are running, resources are tight, and where logs stall is obvious at a glance—restart, clean cache, and pull images without first hunting docs or waiting for developer support; watch staff can self-serve common faults</li>
  <li><strong>One playbook across projects</strong>: The same install and ops entry reuses across appliances and rooms—delivery, watch, and handoff share one standard, avoiding “each site has its own oral tradition”</li>
</ul>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
📦 <strong>Installer download</strong>: Packages for Ubuntu / Debian, CentOS / RHEL <strong>7–9</strong> (x86 + <strong>CentOS ARM</strong>, el7/el8/el9 RPMs), Windows, macOS, and ARM / <strong>Kylin (麒麟) / openEuler (欧拉)</strong> targets are on <a href="https://gitee.com/volara/easyaiot/releases" style="color: #3498db; text-decoration: none; font-weight: 600;">Gitee Releases</a>.
</p>

| | | |
|:---:|:---:|:---:|
| ![Overview](.image/banner/panel/panel_1000.png) | ![Containers](.image/banner/panel/panel_1001.png) | ![Logs](.image/banner/panel/panel_1002.png) |
| ![Deploy](.image/banner/panel/panel_1003.png) | ![Images](.image/banner/panel/panel_1004.png) | ![Pull](.image/banner/panel/panel_1005.png) |
| ![Diagnose](.image/banner/panel/panel_1006.png) | ![Maintain](.image/banner/panel/panel_1007.png) | ![Topology](.image/banner/panel/panel_1008.png) |

### 📡 RTC: Consumer-Camera P2P Bridging—Bring "No RTSP" Devices Into the Platform

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
In homes, retail stores, and light-security deployments, many devices already in use come from <strong>Tapo, Tuya, Ring, Nest, Xiaomi, Wyze, DoorBird, GoPro, and Roborock</strong>—they rely on vendor-private P2P protocols and <strong>do not expose standard RTSP</strong>. Traditional VMS platforms often push users toward Micam, Home Assistant, or other middleware, leaving long integration chains, fragmented ops, and no path to AI judgment. EasyAIoT adds a dedicated <strong>RTC module</strong> built on <a href="https://github.com/AlexxIT/go2rtc" style="color: #3498db; text-decoration: none; font-weight: 600;">go2rtc</a>, that <strong>unifies streaming and two-way audio for all nine brands</strong>—consumer devices can register, preview, relay, run AI tasks, and trigger alerts just like GB28181/ONVIF cameras.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
<strong>Supported brands and typical value:</strong>
</p>

<table style="width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px;">
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 14%;">Brand</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 18%;">Vendor</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 28%;">Typical devices</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600;">Value</td>
</tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Tapo</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">TP-Link</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Home/store IPC, indoor/outdoor cams</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444; line-height: 1.7;"><strong>Low-cost blind-spot fill</strong> for shops; cloud-password connect; <strong>two-way audio</strong></td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Tuya</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Tuya Smart</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Tuya-ecosystem IPC, doorbells</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444; line-height: 1.7;"><strong>Mass white-label/OEM onboarding</strong>; one integration for countless rebranded cameras</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Ring</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Amazon</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Doorbells, outdoor cams</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444; line-height: 1.7;"><strong>Overseas doorbell monitoring</strong> in platform; local P2P after OAuth; remote talk</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Nest</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Google</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Nest Cam, Doorbell</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444; line-height: 1.7;"><strong>Google-ecosystem premium sites</strong> unified with pro cameras on one screen</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Xiaomi</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Mi Home</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Mi Home cams, doorbells</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444; line-height: 1.7;"><strong>Reuse installed Mi Home fleet</strong>; no Micam middleware; attach AI directly</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Wyze</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Wyze</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Wyze Cam v3/v4, doorbells</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444; line-height: 1.7;"><strong>Ultra-low-cost scale-out</strong>; local P2P; two-way audio for pilots</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>DoorBird</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">DoorBird</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">Smart doorbells, door stations</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444; line-height: 1.7;"><strong>Premium entry intercom</strong> + video; MJPEG/audio/talk in one bridge</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>GoPro</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">GoPro</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">HERO9–12 (USB / Wi-Fi)</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444; line-height: 1.7;"><strong>Mobile tactical views</strong> for patrol and emergency survey</td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>Roborock</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0;">Roborock</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">S6/S7/Qrevo MaxV vacuums with cameras</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444; line-height: 1.7;"><strong>Moving under-furniture views</strong> fixed cameras cannot reach; talk on supported models</td></tr>
</table>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>One-click Web onboarding</strong>: "Connect RTC camera" in the console with per-brand dynamic forms; OAuth brands (Ring/Nest/Xiaomi/Wyze/Roborock) bind via go2rtc WebUI then paste stream URL</li>
  <li><strong>Full pipeline wired</strong>: WEB → VIDEO <code>/register/device/rtc-live</code> → RTC API → go2rtc P2P → RTSP → SRS relay → Jessibuca + AI—<strong>same flow for all nine brands</strong></li>
  <li><strong>Two-way audio</strong>: Tapo, Tuya, Ring, Wyze, DoorBird, Roborock support go2rtc intercom for remote talk and doorbell scenarios</li>
  <li><strong>Lifecycle sync</strong>: Deleting a device cleans up go2rtc streams; works with device tree, map pins, and algorithm tasks</li>
  <li><strong>Docker all-in-one</strong>: <code>bash RTC/install_linux.sh start</code> runs go2rtc + management API; host network for P2P LAN</li>
</ul>

### 🔌 EDGE: C# Edge Collection Runtime

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
On industrial and building sites, PLCs, meters, and sensors often hang on RS-485 or Ethernet while the cloud platform still needs a separate data-acquisition stack—protocols written one-off, every config change requiring a site visit. Long access chains, fragmented ops, and cloud-edge metric drift are the norm. EasyAIoT adds a dedicated <strong>EDGE module</strong> (C#) as an <strong>independently deployable edge collection runtime</strong>: pluggable multi-protocol collectors, local scheduling, config-driven parsing, and MQTT integration with the EasyAIoT cloud platform—lifting on-site Modbus RTU/TCP, OPC UA, and other points into a unified thing model uplink, with cloud config push and property writes reaching the edge for execution.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0;">
<strong>Difference from Device Management "gateway":</strong> In device management, a gateway is a cloud-side product/device type (GATEWAY + SUBSET sub-device topology) for provisioning, shadow, binding, and downlink. EDGE has no separate device page—it is the on-site process that <strong>acts as that gateway</strong>; collected data appears in the same device management UI. Another path is <strong>iot-sink cloud-side polling</strong> of Modbus/OPC UA (the platform must reach field devices); EDGE collects on site and uplinks via MQTT only—suited to OT isolation and RS-485. Gateway property uplink/downlink, sub-device property proxy reporting, and config push are already aligned for use as an on-site industrial gateway; proactive topology reporting, sub-device event/service passthrough, OTA, and the full gateway protocol surface are still evolving.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
<strong>Why C# for edge IoT acquisition?</strong>
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Industrial site affinity</strong>: C# has a mature ecosystem in industrial control, SCADA, and HMI—rich protocol libraries and engineering practice for Modbus, OPC UA, serial communication, and more; low onboarding cost for integrators and automation engineers</li>
  <li><strong>Strong typing + structured engineering</strong>: Point mapping, register parsing, and config validation surface errors at compile time—more stable and testable than script languages when maintaining multi-protocol collectors long term</li>
  <li><strong>Async concurrency without blocking</strong>: <code>async/await</code> fits multi-device polling and concurrent serial/network I/O—a single gateway can schedule dozens of sub-device collection jobs without the throughput bottlenecks of interpreted paths like Python GIL under high-frequency polling</li>
  <li><strong>Long-running service stability</strong>: The .NET runtime suits 7×24 edge gateway daemons with predictable memory and GC behavior; dependency injection and plugin architecture let collectors hot-swap and version without restarting the whole site</li>
  <li><strong>Cross-platform deliverability</strong>: The same C# codebase publishes to Linux x86_64 / ARM64 industrial PCs and edge boxes—single-file/self-contained deployment without Python virtualenvs or JVM on site</li>
  <li><strong>Clear division with the cloud platform</strong>: The edge focuses on collect—parse—publish; DEVICE focuses on thing models and device lifecycle—C# does not carry heavy platform business or AI inference, stays lightweight, and runs independently on RS-485 bus sides or low-power gateways</li>
</ul>

<table style="width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px;">
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 18%;">Collector</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">Protocol / Scenario</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;"><code>modbus-rtu</code></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">Modbus RTU (RS485/serial)—meters, instruments, PLCs on the bus</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;"><code>modbus-tcp</code></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">Modbus TCP—Ethernet-side industrial devices, VFDs, gateways</td>
</tr>
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444;"><code>opc-ua</code></td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; vertical-align: top; color: #444; line-height: 1.7;">OPC UA—modern industrial control and upper-system interconnect</td>
</tr>
</table>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Plugin collection architecture</strong>: Implement <code>ICollector</code> to extend new protocols; the Host handles registration, scheduling, and result reporting—collection logic decoupled from the runtime</li>
  <li><strong>Dual config channels</strong>: Local <code>device-jobs.json</code> for offline operation; cloud MQTT <code>config/downstream/push</code> can remotely override collection jobs—no site visit to change config</li>
  <li><strong>MQTT cloud-edge integration</strong>: Joins as platform GATEWAY—gateway property reporting, sub-device property proxy reporting, cloud property write downlink via EMQX to DEVICE/<strong>iot-sink</strong>; sub-devices auto-created with shadow persistence; data shown in Device Management</li>
  <li><strong>Standalone packaging</strong>: <code>pack_linux.sh</code> produces x86_64 / ARM64 Linux deployment packages for industrial PCs and edge gateways—decoupled from the main platform stack</li>
  <li><strong>E2E integration out of the box</strong>: <code>bash EDGE/demo/run_e2e.sh</code> validates the full chain—collection → MQTT uplink → cloud persistence</li>
</ul>

### 🛰️ SENTINEL: Cluster-Node Sentinel—Onboard Ready, Schedule by Real Capability

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Federated scale-out often fails at “the machine joined, but nobody knows if it can take work”—video analytics, stream forwarding, and model training each need different readiness; jobs land only to discover missing environment pieces, and sites keep boarding servers to install dependencies until acceptance stalls on “installed but won’t run.” EasyAIoT adds a dedicated <strong>SENTINEL module</strong> as a <strong>business-readiness sentinel</strong> that travels with every schedulable node: it continuously checks whether the box can truly take the selected workloads, aggregates schedulable capacity into the console, and can request environment fill-in when gaps appear—so ops board fewer machines, jobs hit fewer dead ends, and scale-out can be accepted the same day.
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Capability by business choice</strong>: Video analytics, stream forwarding, live ingest, model training, LLMs, smart labeling—whatever business you select is what readiness tracks; no more guessing by role what a machine “probably” can do</li>
  <li><strong>Monitor on onboard</strong>: After a node joins the platform, sentinel inspection starts automatically—see “can it take work?” the same day, shortening the idle window of “add machine → wait for integration → discover it can’t run”</li>
  <li><strong>Schedule by real capability</strong>: Only truly ready nodes enter the schedulable pool, cutting rework and complaints from “dispatched but won’t start”</li>
  <li><strong>Self-serve gap fill-in</strong>: When expected environment is missing, the platform can be asked to fill it in—turning manual on-site installs into a closed loop and fewer server logins for duty staff</li>
  <li><strong>Scale without public internet</strong>: Air-gapped or restricted sites can still onboard offline and sync environments—edge expansion is not blocked by WAN access</li>
  <li><strong>Acceptance at a glance</strong>: Component health and schedulable functions share one console view—less guessing, less machine hopping, one delivery language</li>
</ul>

### 🧭 POST: Custom Judgment—Turn “Detections” into Operable Business Events

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Vision projects often stall at “the model already boxed people/vehicles/objects, but alerts are unusable”—passers-by outside the zone still alarm, normal work still alarms, and customers need line-crossing, loitering, or people-over-limit, yet teams keep retraining models, stopping tasks, and waiting on developers. EasyAIoT adds a dedicated <strong>POST custom judgment service</strong> that separates <strong>visual perception</strong> from <strong>business judgment</strong>: detection keeps focusing on “seeing,” while judgment orchestrates per task “whether to alert and what to report”—change rules without retraining, and analysis keeps running, so alerts finally match site, campus, traffic, and plant management standards.
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Orchestrate judgment per task</strong>: Each algorithm task can configure its own post-processing steps—default filter by detection regions, then enter standard alerting; insert business scripts or industry plugins to compose people counting, line-crossing, dwell timeout, area loitering, and multi-condition composite alerts into field-ready rule chains—configure once per scenario, reuse across tasks</li>
  <li><strong>Alert only where business cares</strong>: Linked with device “region detection,” targets outside regions are filtered out—no screen flood; with no regions drawn, alerts are not blocked—avoid “no regions configured, everything goes silent.” Duty attention stays on forbidden zones, passages, and workstations that truly matter; false alarms and manual review drop sharply</li>
  <li><strong>Business scripts and rule chains can coexist</strong>: Base-config scripts express judgment in field language; the rules page owns filtering and step order. Both capabilities are independent and can run together—delivery need not choose between “write a script” and “configure steps”; complex sites can state the standard once</li>
  <li><strong>Pluggable industry logic</strong>: Differentiated judgment for campuses, sites, and traffic need not change the platform core. Integrators and solution providers can register, start/stop their own judgment capabilities and attach them per task—one detection model serves many customer projects, turning “rewrite analysis per site” into “configure rules, attach capability, accept the standard”</li>
  <li><strong>Trial-run before go-live</strong>: Replay current rules online with sample or real detection events—step through pass vs drop and whether an alert will fire. Integration and acceptance can answer “what did this rule actually block,” instead of tuning after go-live from complaints</li>
  <li><strong>Rule changes take effect immediately</strong>: Saving rules on a running task adopts the new standard—no need to stop analysis or re-push video. Temporary forbidden-zone changes or an extra judgment step can be operated the same day, shortening the “wait for a maintenance window → change → re-accept” idle gap</li>
  <li><strong>Perception and judgment do not drag each other down</strong>: Monitoring keeps analyzing smoothly while business judgment scales on demand; on judgment failure choose “skip this step and keep alerting” or “prefer no alert over a wrong one,” matching field risk preference between misses and false alarms. Floor-level (standard) and full-stack appliances (full) include this capability by default; light standalones can first close the detection-alert loop and upgrade when deeper operations are needed</li>
  <li><strong>Four built-in judgment plugins (no registration)</strong>: <strong><code>line_cross</code></strong> (line crossing with <code>line</code> detection lines + tracking), <strong><code>region_enter_exit</code></strong> (enter/exit polygon zones), <strong><code>dwell_timer</code></strong> (dwell/loiter timeout in zone), <strong><code>headcount_gate</code></strong> (headcount threshold in zone)—compose with region gate, pass-through, business scripts, and industry plugins into field-ready rule chains</li>
</ul>

### 🤖 AI Assistant: IDEA split-pane co-creation—edit code while asking about architecture and health

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Open-source contribution and on-site PoCs often stall in the same place: many modules, long chains—editing needs a local setup, health checks need SSH, architecture questions mean digging docs and asking people. EasyAIoT embeds the <strong>HARNESS conversational assistant</strong> into the <strong>IDEA cloud IDE</strong>—full VS Code workspace on the left, AI assistant split on the right; drag files from the explorer to auto <code>@</code>-mention them in chat, read source while asking about ports, config, and service health, shortening the “don’t know → ask someone → edit again” loop.
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>IDEA split-pane co-creation</strong>: Toolbar opens the AI assistant on the right—editor and Agent side by side; or deep-link with <code>?file=path&harness=1</code> to open a file and split</li>
  <li><strong>Drag to auto @</strong>: Drop explorer files onto the assistant pane to attach them as chat context—fewer paths typed, less context lost</li>
  <li><strong>Ask and check</strong>: The Agent calls platform Tools to probe Gateway / video / AI health and points to related config and source—compressing SSH + compose digging into one conversation</li>
  <li><strong>Knows the ontology</strong>: Built-in <code>HARNESS/ontology/AGENTS.md</code> and full-repo workspace—architecture, ports, APIs, and install conventions in one place</li>
  <li><strong>Same semantics in the console</strong>: In-page floating drawer / full-screen “AI Assistant” share the same capabilities as IDEA; MCP + Cursor Skill reusable across environments</li>
  <li><strong>Two-way jump</strong>: The assistant can generate portal links via <code>easyaiot_open_in_idea</code>—from Q&amp;A back to a full IDE where you can edit and publish</li>
</ul>

| | | |
|:---:|:---:|:---:|
| ![IDEA Login](.image/banner/banner1203.png) | ![IDEA Workspace](.image/banner/banner1204.png) | ![IDEA Development](.image/banner/banner1205.png) |
| ![AI Assistant Chat](.image/banner/banner1210.png) | ![AI Assistant Analysis](.image/banner/banner1211.png) | ![AI Assistant Collaboration](.image/banner/banner1212.png) |

### 📱 ANDROID / IOS / HARMONYOS: One Frontend, Three Native Shells—Every Phone, One App

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Mobile delivery often stalls on platform coverage: an app that only runs on one OS chains field staff to company-issued devices, and maintaining a separate native codebase per platform triples cost while the feature sets drift apart. EasyAIoT's mobile side is <strong>one uni-app frontend + three native shells</strong>: the same <strong>APP</strong> pages compile into installable apps for <strong>ANDROID</strong> (DCloud offline runtime + Gradle → APK), <strong>IOS</strong> (WKWebView shell + xcodebuild → .app / .ipa), and <strong>HARMONYOS</strong> (ArkWeb shell + hvigor → HAP)—one set of business logic, native installers on every mainstream phone OS, without maintaining three codebases.
</p>

<table style="width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px;">
<tr>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 14%;">Platform</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 34%;">Shell technology</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; width: 30%;">Build output</td>
<td style="padding: 10px 12px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600;">One-command script</td>
</tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>ANDROID</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">DCloud uni-app offline runtime + Gradle</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>easyaiot-&lt;version&gt;-&lt;env&gt;-android.apk</code></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>ANDROID/make-apk.sh</code> / <code>make-apk.bat</code></td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>IOS</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">WKWebView shell + xcodebuild (Xcode 16+)</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>.app</code> (simulator, no signing) / <code>.ipa</code> (device)</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>IOS/make-ipa.sh</code></td></tr>
<tr><td style="padding: 10px 12px; border: 1px solid #e0e0e0;"><strong>HARMONYOS</strong></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;">ArkWeb shell + hvigor (DevEco Studio)</td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>easyaiot-&lt;version&gt;-&lt;env&gt;-harmonyos.hap</code></td><td style="padding: 10px 12px; border: 1px solid #e0e0e0; color: #444;"><code>HARMONYOS/make-hap.sh</code></td></tr>
</table>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>One codebase, zero divergence</strong>: All three shells share the same APP pages and admin-api—device management, live preview, stream forwarding, algorithm tasks, alert center, model inference/training—matching the PC console feature-for-feature on Android, iOS, and HarmonyOS alike; frontend capability differences are isolated in conditional compilation, so one change ships to every platform</li>
  <li><strong>System-native rendering on each platform</strong>: Android runs the uni-app offline runtime for a native App experience; iOS serves the H5 build through a custom <code>easyiot://</code> scheme so pages run as a normal website (ES Modules, localStorage, and cross-origin admin-api behave as on a real deployment); HarmonyOS maps rawfile resources to the <code>http://appassets.local/</code> virtual host in ArkWeb—no third-party engines, no file:// quirks, no behavior forks</li>
  <li><strong>One-command packaging per platform</strong>: <code>make-apk.sh</code> / <code>make-ipa.sh</code> (simulator .app or device .ipa) / <code>make-hap.sh</code> each run version-consistency check → frontend build → resource sync → native build → named artifact; prod / test / dev environments produce independent packages that never overwrite each other</li>
  <li><strong>Unified management entry</strong>: <code>.scripts/docker/mobile.sh</code> covers all three ends—<code>status</code> (version consistency + toolchain readiness + existing artifacts), <code>build android|ios|harmonyos|all</code>, <code>bump</code>, <code>artifacts</code>, and <code>clean</code>—daily operations never need to enter each module separately</li>
  <li><strong>One command to bump all five version fields</strong>: APP manifest + Android build.gradle + <code>dcloud_control.xml</code> + iOS pbxproj (Debug/Release) + HarmonyOS <code>app.json5</code>—<code>.scripts/docker/mobile.sh bump 1.0.1 101</code> updates every copy and re-reads to verify; each packaging script refuses to build when the copies disagree, so a mismatched version never ships</li>
  <li><strong>Standardized artifact naming</strong>: lowercase kebab-case <code>easyaiot-&lt;version&gt;-&lt;env&gt;-&lt;platform&gt;.&lt;ext&gt;</code>—sorted-stable for archiving, friendly to object storage / CDN and CI artifact collection; <code>mobile.sh artifacts/clean/status</code> recognize both new and legacy names</li>
  <li><strong>CI-friendly split pipeline</strong>: any Linux runner can run <code>--skip-native</code> to build and sync the frontend resources, then hand the prepared project to a macOS runner (iOS) or a self-hosted DevEco runner (HarmonyOS) for the native compile—one pipeline, three platforms, no platform toolchain on every machine</li>
  <li><strong>Signing and distribution ready</strong>: Android signs with the built-in <code>iot.jks</code> (DCloud AppKey registered); iOS simulator builds need no account while device / App Store builds use automatic signing with a Team ID; HarmonyOS auto-generates debug signatures in DevEco and supports release signing via AppGallery Connect</li>
  <li><strong>Per-module docs and troubleshooting</strong>: each module ships its own README covering environment prep (JDK / Xcode 16+ / DevEco), version management, signing, and a FAQ table; the unified three-end guide lives in <a href="MOBILE.md" style="color: #3498db; text-decoration: none; font-weight: 600;">MOBILE.md</a></li>
</ul>

### 🎯 Four Hardware Tiers, One Platform

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Many intelligent IoT projects stall at deployment: <strong>full features won't fit on small machines; to make them fit, you cut capabilities, split versions, and maintain multiple deployment packages.</strong> EasyAIoT resolves this with one platform—from <strong>edge ultra-light standalone</strong> to <strong>edge boxes for point intelligence, AI all-in-one cameras for on-wall analysis, AIoT full-stack all-in-ones for the complete stack in one box</strong>. Pick among the four common field hardware classes; the same software runs from “just get it running” through single-site pilots, floor coverage, and full-stack delivery—no split versions.
</p>

| Tier | Typical hardware (examples) | Recommended RAM | What you can do | Verified |
| :-- | :-- | :--: | :-- | :--: |
| **edge** Edge Standalone | <strong>Light edge standalone</strong> (2 GB industrial PC, old laptop, smallest cloud VM, store trial box) | ≥ 2 GB | <strong>One machine closes the loop first</strong>: WEB + VIDEO + RUNTIME; camera access, real-time analysis, smart alerts; zero DEVICE, login led by VIDEO | ~**1.02 GB**, nearly 1 GB headroom |
| **mini** Edge Lite | <strong>Edge box</strong> (8 GB industrial PC, store security all-in-one, site gateway) | ≥ 8 GB | <strong>Intelligence at one point</strong>: camera access, real-time analysis, smart alerts, model inference; event plane same as standard/full (Gateway + iot-sink + EMQX) | ~4–6 GB used, ample headroom |
| **standard** Standard | <strong>AI all-in-one camera</strong> (smart camera terminal, AI surveillance camera with compute, multi-sensor AI analyzer) | ≥ 16 GB | <strong>Each camera is a smart node</strong>: multiple cameras on the wall cover a floor/campus; devices, rules, and compute orchestrated together; <strong>POST custom judgment</strong> makes alerts match field standards | ~10 GB, stable with headroom |
| **full** Full (default) | <strong>AIoT full-stack all-in-one</strong> (enterprise full-stack control all-in-one, industry IoT full-stack host, cloud-edge-device smart platform all-in-one) | ≥ 20 GB | <strong>IoT + video + AI in one box</strong>: device management, massive access, intelligent analysis, command and judgment unified—full capabilities long-term; includes <strong>POST custom judgment</strong> and outbound business flow | ~14 GB, full features with headroom |

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
<strong>Install edge:</strong> <code>EASYAIOT_DEPLOY_PROFILE=edge sudo bash .scripts/docker/install_linux.sh install</code> (or <code>... install_linux.sh edge install</code>). First-time install can also pick the tier interactively; see <a href="#-quick-start">Quick Start</a> above.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>Install tier selection and resource compliance (verified):</strong>
</p>

| | |
|:---:|:---:|
| ![Edge standalone edge](.image/deploy-profile-edge.png) | ![Edge box mini](.image/deploy-profile-mini.png) |
| ![AI all-in-one camera standard](.image/deploy-profile-standard.png) | ![Full-stack all-in-one full](.image/deploy-profile-full.png) |

#### 🧠 AI Capabilities

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>RUNTIME High-Speed Execution Layer</strong>: Pulls “watch / compute / push” out of interpreted-language paths into a <strong>native binary</strong> that owns <strong>pull → decode → infer → alert callback → boxed push</strong>. Versus Python executors, it avoids GIL and multi-process orchestration overhead—on the same hardware you get <strong>more channels per box, lower end-to-end latency, and less CPU/memory</strong>. Realtime / snap / patrol and multi-channel raw forward share one execution stack; default <code>executor=cpp</code>. In practice: keep dozens of NVR channels clear first, then enable AI only on critical channels; switch raw preview and boxed judgment without either path dragging the other down; VIDEO/WEB keep orchestration, archiving, and access control while RUNTIME focuses on throughput and latency—scale channels without replacing the whole appliance</li>
  <li><strong>High-Performance Stream Forwarding</strong>: Built for the real delivery need to “fill the video wall / split view first, without turning AI on for every channel”—batch NVR channels and building endpoints can create forwarding tasks in one click. Default path is <strong>RUNTIME</strong> high-performance (compatibility mode still available) so multi-channel raw video stays on wall at lower resource cost. Raw viewing and AI judgment can run on the same device in parallel; when algorithm tasks start/stop, forwarding policy follows automatically. Side-by-side preview shortens acceptance by comparing latency and overlay quality directly</li>
  <li><strong>Custom Platform Name &amp; Logo Across All Touchpoints</strong>: After deploying EasyAIoT on site, users should see <em>their</em> platform—not a generic product name. The monitoring dashboard includes a visual "Platform Branding" panel where administrators can rebrand in the UI: update the admin console name and logo (synced to the sidebar and browser tab); set an independent command-center title on the big screen; and customize the login page name, logo, form title, plus light/dark background images—all three touchpoints stay visually consistent, take effect immediately, and can be saved or reset with one click.
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>For system integrators and solution providers</strong>: Eliminates front-end reskinning, custom development, and release cycles; switch branding quickly between PoC demos and production delivery, reuse one codebase across multiple customers, shorten payment cycles, and improve solution reuse</li>
      <li><strong>For government, campus, hospital, and other end users</strong>: Login page, command dashboard, and daily admin console all display their organization's name and identity—stronger ownership and credibility for leadership visits and internal rollout, meeting branding requirements for public-sector and large-enterprise IT projects</li>
      <li><strong>For private-deployment and operations teams</strong>: Configure on site the same day for acceptance—no waiting on development schedules; one-click restore after multi-customer demos or pilot phases, lowering switching and redeployment costs</li>
    </ul>
  </li>
  <li><strong>YOLO26 Next-Generation Object Detection</strong>: Built-in next-generation object detection, ready out of the box for real-time feed analysis and snapshot recognition. On the same hardware, connect more camera streams with faster response and fewer false alarms. Supports the full loop from data collection, annotation, and training to deployment and inference—helping users iteratively build custom detection models at lower cost and quickly cover common security and industrial scenarios such as hard hat compliance, unauthorized entry, and fire hazards, making "see accurately, compute fast, scale easily" the default capability</li>
  <li><strong>YOLO26 Human Pose Analysis</strong>: Builds on object detection with human keypoint and skeleton pose analysis, ready out of the box. Supports three input modes—images, videos, and real-time camera streams. Image mode can synchronously output skeleton annotations and person counts; video mode supports progress tracking and result download; camera mode can connect to RTSP/RTMP live streams and overlay pose recognition results on relayed output for remote monitoring and behavior analysis. The model inference page provides one-click switching between "Pose Analysis" and "Object Detection", suitable for construction site compliance, fitness form assessment, crowd gathering awareness, and other scenarios that require understanding human structure and motion—moving the platform from "boxing targets" to "understanding poses"</li>
  <li><strong>Multi-Protocol Camera Access Support</strong>: Comprehensive support for GB28181 and ONVIF, two mainstream video surveillance protocols, enabling standardized device access and management. GB28181, as China's national standard, perfectly adapts to mainstream domestic surveillance equipment; ONVIF, as an international universal standard, is widely compatible with global mainstream camera brands. Through dual-protocol support, the platform seamlessly integrates with existing surveillance systems, achieving plug-and-play device access, automatic discovery, and unified management, significantly reducing device access barriers, enhancing system compatibility and scalability, and providing a solid technical foundation for large-scale camera deployment. In addition, NVR batch scan, registration, and unified management across same-segment and cross-segment networks are supported, covering mainstream brands including Hikvision, Dahua, Huawei, Ezviz, and Xiaomi, with native-protocol subnet discovery, one-click registration, and batch channel import. For consumer cameras such as Mi Home that natively lack RTSP, the <strong>RTC module (go2rtc bridge)</strong> brings them into the same platform, further reducing large-scale surveillance onboarding and ops costs</li>
  <li><strong>DJI dock / drone aerial view access</strong>: Breaks fixed-camera “ground-only, hard to cover wide areas” limits; brings DJI FlightHub dock and drone aerial video into the platform’s unified video and AI judgment loop. Streaming module offers “Connect DJI livestream”: supports <strong>FlightHub API start livestream</strong> and <strong>manual livestream source</strong> — API mode one-click pulls vendor livestream and auto-registers device; manual mode accepts RTSP / RTMP / HTTP-FLV / HLS sources. After connect, aerial views can share the same screen as GB28181/ONVIF fixed points. Operators can view dock/aircraft live like fixed cameras, and attach real-time AI analysis, alarm linkage and evidence retention—covering wide-area patrol, emergency survey, perimeter fill-in that fixed points cannot reach; shortens “detect—locate—respond”; upgrades security from planar deployment to sky–ground collaborative sensing.</li>
  <li><strong>RTC Consumer-Camera P2P Bridging</strong>: One integration for <strong>Tapo (TP-Link home/store IPC), Tuya (mass white-label devices), Ring / Nest (overseas doorbell ecosystems), Xiaomi Mi Home (domestic reuse), Wyze (low-cost fill-in), DoorBird (premium entry intercom), GoPro (mobile patrol views), Roborock (vacuum mobile cameras)</strong>—all nine brands natively lack standard RTSP. The RTC module, built on go2rtc, provides P2P bridging and a unified management API. Web console "Connect RTC camera" guides per-brand form fill or OAuth binding, one-click go2rtc stream registration, VIDEO device enrollment, and SRS relay; after bridging, consumer and GB28181/ONVIF pro cameras <strong>share one screen, AI tasks, and alert linkage</strong>, bringing home/store cameras and project-grade devices into one video judgment system at lower integration and reuse cost</li>
  <li><strong>Real-Time Intercom & PTZ Remote Control</strong>: Breaks through traditional surveillance's "watch-only, can't act" limitation. Operators can conduct voice broadcasting and PTZ control on the same real-time preview screen—no system switching, no on-site presence required. Remotely communicate, guide evacuations, or stop violations, compressing response from "dispatch personnel" to "speak and reach instantly." PTZ control lets cameras pan, tilt, and zoom on demand—quickly aim at incident areas and magnify details during emergencies, forming an integrated on-site response loop of "see clearly, aim precisely, speak and reach." Fully compatible with GB28181 and ONVIF devices, leveraging existing surveillance assets without additional intercom hardware or third-party software, instantly upgrading deployed cameras with remote communication and flexible dispatch capabilities, significantly reducing system silos and monitoring costs</li>
  <li><strong>POST Custom Judgment (Orchestrable Post-Processing)</strong>: Breaks through the "detect but can't judge" bottleneck with a dedicated <strong>POST</strong> service as the business judgment layer, transforming visual perception into operable, accountable, and statistically trackable business events. Inside each algorithm task, orchestrate a rule chain: default filter by detection regions before alerting, and layer business scripts plus industry plugins for people counting, line-crossing, dwell timeout, area loitering, and multi-condition composite alerts—adapt to construction safety, campus security, and traffic control without repeatedly tuning models. Trial-run rules with sample events before go-live to see what is blocked and whether alerts fire; saving rules on a running task takes effect immediately without stopping analysis. Perception and judgment run independently in parallel—feeds keep analyzing smoothly while business logic scales on demand; judgment results archive automatically and drive precise alerts, cutting false positives/negatives and manual review. Business users focus on rules, integrators plug in industry capabilities, and the platform handles distribution, execution, and scale—from "being able to see" to "judge clearly, control effectively, and put it to use"</li>
  <li><strong>Multi-Central-Node × Multi-Worker-Node Federated Cluster</strong>: Designed for cross-region, multi-datacenter, and cloud-edge collaborative deployments, the platform adopts an "N central nodes + N worker nodes" federated architecture—central nodes provide unified orchestration while worker nodes carry compute and media execution, scaling horizontally. Each central node manages its domain worker nodes, supporting remote distribution and one-click deployment of streaming, AV transcoding, video analytics, model inference, and training capabilities; multiple central nodes can interconnect and synchronize; the cluster swimlane view intuitively presents "central—worker" topology and resource levels. Algorithm tasks, auto-labeling pipelines, and stream relay workloads are intelligently scheduled by node role and GPU capability—enabling massive stream ingestion, high-concurrency inference, and distributed training to run together in one cluster, truly delivering "onboard easily, schedule clearly, scale openly, govern completely"</li>
  <li><strong>SENTINEL Cluster-Node Sentinel</strong>: Built for federated scale-out and cross-datacenter compute pools—solves the delivery pain of “the machine joined, but nobody knows if it can take work.” Continuously reveals each node’s readiness and schedulable capacity by business function, so jobs land only on truly ready machines; can request environment fill-in when gaps appear, and supports offline onboarding for air-gapped sites—so the cluster truly “onboards cleanly, recognizes clearly, dispatches accurately, and boards fewer servers”</li>

  <li><strong>SAM Zero-Start Auto-Labeling Orchestration Pipeline</strong>: Built for cold-start scenarios with no annotated samples and no usable detection model, the platform integrates SAM open-vocabulary segmentation to deliver a one-click, unattended labeling pipeline. Per strategy, the system automatically chains camera frame extraction, SAM text-prompt bootstrap labeling, YOLO fine-tuning once thresholds are met, production-phase YOLO high-speed inference with intelligent SAM fallback for missed detections, periodic iterative training, and automatic dataset packaging and export—closing the full "capture-annotate-train-export" loop. Supports pause/resume and elastic scheduling on local or cluster compute queues. With visual strategy configuration and run logs, users can grow a custom detection capability from zero samples and zero models, making "define categories in words, watch the model take shape" the default path for dataset building</li>
  <li><strong>Ten-Thousand-Node Elastic Compute Cluster & Horizontal Scaling Pool</strong>: Built for hyperscale AI and video workloads, the platform provides a cloud-edge-end distributed compute foundation that unifies algorithm tasks, stream relay, algorithm services, model training, and inference under one horizontal load-balancing and elastic scaling fabric. New servers join the fleet with one-click onboarding and immediately become schedulable compute units—the scheduling hub automatically dispatches tasks and balances load based on resource levels and business pressure, enabling linear scaling from hundreds to tens of thousands of camera streams and from a single machine to ten-thousand-node clusters without redeployment or manual tuning. Massive stream ingestion, high-concurrency inference, and distributed training run together in a shared compute pool—truly delivering "scale on demand, run reliably, govern with confidence"</li>
  <li><strong>Distributed Storage Driver (Compute + Storage Dual-Cluster Decoupling)</strong>: Moving beyond the legacy pattern of per-node local directory mounts, hard-coded paths, and config rewrites on every scale-out, the platform replaces raw local-directory drivers with a <strong>cluster event-driven</strong> storage fabric—Export readiness, client mount state, primary/standby failover, and multi-cluster bridge links are sensed and propagated as events, so snapshots, recordings, alert evidence, and model assets flow into a distributed NFS cluster without business layers tracking mount paths. Compute and storage form <strong>two independently scalable domains</strong>: the compute side fully embraces the <strong>C++ RUNTIME</strong> high-speed execution pipeline, while the storage side builds an NFS cluster pool that scales out horizontally without bound—compute and storage grow on their own watermarks, not locked together. With cluster swimlanes, topology views, and multi-cluster bridge sync, new nodes join the storage domain with one-click onboarding, so "compute scales" and "storage scales" advance in parallel under massive stream ingestion—truly delivering "decoupled compute and storage, independent scale-out, event-driven coordination, unified governance, limitless expansion"</li>
  <li><strong>Tianditu Spatial Visualization & Map-Based Analysis</strong>: Integrated with China's national Tianditu map service, the platform brings cameras, alerts, and person/vehicle recognition onto a single map—upgrading surveillance from "watching feeds" to "seeing the big picture." Both the streaming media and alert modules offer a "Map Distribution" view with a device directory tree for regional focus, giving instant visibility into checkpoint layout and online status. Map click-to-pin, location search, and batch coordinate import help GB channels, NVR channels, and direct-connect cameras get mapped quickly so every feed has clear spatial context. Alerts are automatically placed on the map via linked camera coordinates; filter by time, event type, task, and business tags, then open snapshots and recordings in one click—helping operators move fast from "where did it happen" to action. Combined with face and plate libraries, hits across multiple sites can be woven into spatial trails—<strong>trace by person</strong> to reconstruct movement and presence within a monitored area; <strong>trace by vehicle</strong> to link passing records and pinpoint routes and stop zones for find-person/find-vehicle, patrol deployment, and post-incident review. Mobile devices also support track playback to replay patrol and travel paths on a timeline. Switch freely between vector and satellite basemaps with auto-fit view, so managers use the map as the anchor to spot anomalies, lock onto targets, and coordinate response faster</li>
  <li><strong>Qwen / DeepSeek Multi-GPU Deployment</strong>: Supports deploying Qwen, DeepSeek, and other large language models across multiple GPUs in parallel. GPU resources can be scheduled flexibly at the cluster level, enabling elastic scaling and load balancing of model instances to deliver stable inference under high concurrency and long-context workloads</li>
  <li><strong>Vision Large Model Intelligent Understanding</strong>: Integrated with QwenVL3 vision large model, supports deep visual reasoning and semantic understanding of real-time video frames, enabling intelligent analysis and scene comprehension of frame content, providing richer visual cognitive capabilities, achieving a leap from pixel-level perception to semantic-level understanding</li>
  <li><strong>Real-Time Camera Feed AI Analysis</strong>: For RTSP/RTMP real-time video streams, provides full-chain analysis from stream pull, frame extraction, model inference, structured output, and alert linkage—converting frame changes into searchable, analyzable structured detection events with millisecond response. Viewing and algorithm chains operate independently, balancing preview clarity with high-concurrency throughput. Analysis results seamlessly connect with detection regions, defense time periods, face/plate recognition, and orchestrable post-processing rules, upgrading the traditional "human staring at screens, reviewing after the fact" duty model to "machines monitor 24/7, anomalies pushed in seconds, evidence auto-archived", turning real-time video from passive viewing into infrastructure for active perception and intelligent judgment</li>
  <li><strong>Intelligent Camera Patrol</strong>: Designed for monitoring scenarios with many camera streams but limited staffing, the platform provides split-screen patrol and device-directory batch patrol capabilities, performing rotational AI analysis across large-scale camera fleets under limited concurrent connections. Supports three scheduling modes—rotation, connection pool, and hybrid—automatically capturing frames at set intervals, running detection models, and linking alerts with face/plate recognition. In hybrid mode, focus streams stay permanently monitored while background streams rotate on schedule, balancing priority surveillance and full-area coverage. Patrol progress is pushed in real time, captured frames are automatically archived, and patrol sessions for hundreds of cameras can be launched in one click from split-screen views or device directories—upgrading traditional manual screen-by-screen monitoring to intelligent automated patrol with "fewer connections, broader coverage, faster discovery"</li>
  <li><strong>Cloud-Edge-Device Integrated Algorithm Alert Monitoring Dashboard</strong>: Provides a unified cloud-edge-device integrated algorithm alert monitoring dashboard that displays key information in real-time, including device status, algorithm task operations, alarm event statistics, and video stream analysis results. Supports multi-dimensional data visualization, achieving unified monitoring and management of cloud, edge, and device layers, providing decision-makers with a global perspective intelligent monitoring command center</li>
  <li><strong>Face Recognition and Face Library Management</strong>: Supports flexibly enabling face recognition in camera tasks. Provides face library and facial feature management with create/query/update/delete capabilities for face samples and feature vectors, as well as high-performance vector retrieval. Supports efficient face comparison and identity retrieval on captured frames, while fully recording match results, snapshots, camera location information, and device context for personnel trajectory tracing, security forensics, and multidimensional statistical analysis.</li>
  <li><strong>License Plate Recognition and Plate Library Management</strong>: Enable license plate recognition in monitoring tasks with one click. Automatically reads plate information from passing vehicles and compares against your own plate libraries in real time. Flexibly maintain whitelists, blacklists, and business tags; trigger instant alerts when vehicles match rules—supporting access control at entrances and exits, targeted vehicle watchlists, and visitor vs. registered vehicle management. Automatically registers newly seen plates and keeps complete capture and match records for post-incident lookups, trace verification, and evidence retention. Recognition runs in parallel with existing video analytics without affecting monitoring and alert stability or real-time performance</li>
  <li><strong>Device Detection Region Drawing</strong>: Provides a visual device detection region drawing tool that supports drawing rectangular and polygonal detection regions on device snapshot images, supports flexible association configuration between regions and algorithm models, supports visual management, editing, and deletion of regions, supports keyboard shortcuts to improve drawing efficiency, enabling precise region detection configuration and providing accurate detection range definitions for algorithm tasks</li>
  <li><strong>Intelligent Linked Alert Mechanism</strong>: Supports a triple-link mechanism between detection regions, defense time periods, and event alerts. The system intelligently determines whether a detected event simultaneously meets the specified detection region range, falls within the defense time period, and matches the alert event type. Alerts are only triggered when all three conditions are met, achieving precise spatiotemporal condition filtering, significantly reducing false positive rates, and improving the accuracy and practicality of the alert system</li>
  <li><strong>Alert Work Orders (AI Alert Responsibility Closed Loop)</strong>: Makes "AI raises an alert" truly land as "someone is responsible, a workflow follows up, and the outcome is traceable." Once an alert is persisted, <strong>routing rules</strong> match it automatically (combining alert object / event / task / device / edge node conditions); a hit immediately generates an <strong>alert work order</strong> and starts a handling process—no manual dispatching, responsibility goes straight to a person. Work orders run on the platform's built-in <strong>process orchestration</strong> (visual flow designer: approval, countersign, copy, conditional branches, parallel branches, timeout reminders, etc.), supporting approve / reject / return / delegate / transfer / add-signature actions with in-app and mobile notifications (deep links straight to the approval detail). Each alert's handling status, current assignee, and elapsed time stay fully recorded, forming a complete "alert → work order → handling → review" loop; existing alerts can also be manually promoted to work orders as a fallback so none are missed</li>
  <li><strong>Large-Scale Camera Management</strong>: Supports access to hundreds of cameras, providing end-to-end services including collection, annotation, training, inference, export, analysis, alerting, recording, storage, and deployment</li>
  <li><strong>Algorithm Task Management</strong>: Supports creation and management of real-time, snapshot, and patrol algorithm tasks; each task can flexibly bind frame extractors and sorters for precise video frame extraction and result sorting
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>Real-Time Algorithm Tasks</strong>: Real-time video analysis with RTSP/RTMP processing; default backend <code>executor=cpp</code> (starts <strong>RUNTIME</strong>, default-pushes boxed AI streams and returns alerts/heartbeats), optional <code>python</code> compatibility path</li>
      <li><strong>Snapshot Algorithm Tasks</strong>: Captured-image analysis; default can also use <code>executor=cpp</code> (RUNTIME SnapScheduler / Cron)</li>
      <li><strong>Patrol Algorithm Tasks</strong>: Multi-stream rotation and connection-pool scheduling; default can also use <code>executor=cpp</code> (RUNTIME PatrolScheduler) for “fewer connections, wider coverage”</li>
    </ul>
  </li>
  <li><strong>Dataset Annotation and Multi-Format Dataset Management</strong>: Provides a visual image annotation workspace supporting rectangle and polygon labeling, category management, and progress tracking; fully supports flexible import and export of mainstream dataset formats including YOLO, COCO, and ImageFolder, with cloud platform dataset integration enabling one-click import and synchronized export of cloud-hosted datasets—seamlessly connecting data collection, annotation, training, and deployment across the full pipeline</li>
  <li><strong>Multi-GPU Training, Checkpoint Resume, and Node-Side Deployment</strong>: Breaks through the training bottlenecks of “GPUs available but unused, tasks hard to control, and progress lost on interruption” by systematically connecting multi-GPU utilization, controllable task scheduling, and node-side deployment—so on-site GPUs are truly usable and training jobs are truly manageable. The platform automatically discovers and schedules all server GPUs; users can select single- or multi-GPU on the training page instead of being limited to “only one card visible.” It supports common dataset formats and directory layouts, large local dataset uploads, and keeps original data after failed runs for quick retry—greatly reducing data-prep and rework costs. Training progress is fully visible, and jobs can be stopped and resumed—avoiding lost results after interruption or “stop clicked but still spinning in the background.” Local and remote training schedulers also roll back promptly on failure with clear feedback. Front-end GPU selection, resume training, and stop-state display are improved in parallel, and issues such as false failure on model publish, custom preview images being overwritten, models not found by name/version, and dataset sync timeouts/conflicts are fixed—making the train–publish–use loop smoother and more reliable</li>
  <li><strong>Stream Forwarding</strong>: View live camera feeds without enabling AI; batch push and auto NVR channel tasks work out of the box. Default <strong>RUNTIME</strong> high-performance path keeps multi-channel raw video cheaper on wall—“fill the wall first, AI on critical channels”; special sites can switch to Python/FFmpeg compatibility mode</li>
  <li><strong>GPU Discovery, Load-Aware Allocation, and Multi-GPU Collaboration</strong>: The platform provides GPU resource discovery and intelligent scheduling: it detects the number of available GPUs and dynamically assigns video encode/decode and algorithm inference work across cards according to per-GPU load, running tasks in parallel where appropriate to raise multi-stream throughput and utilization while keeping the pipeline stable—coordinating frame processing and model inference in multi-GPU deployments</li>
  <li><strong>Smart Transport Selection and Resilient Stream Pull</strong>: On RTSP and similar pull paths, the system can automatically select appropriate transport modes based on scenario to balance latency and stability. When consecutive frames indicate gray screen, decode errors, or stream stall, automatic reconnect and link recovery run to limit prolonged artifacts or frozen video</li>
  <li><strong>Dual Pathways for Watching and Judgment</strong>: Split “raw video on wall / split view” from “algorithm results”—duty side prioritizes clarity and smoothness; judgment side outputs boxed results independently, so neither starves the other. The same camera can keep both live and analyzed views, making shift switches natural and channel scale-out no longer a choice between “see clearly” and “analyze enough”</li>
  <li><strong>Model Service Cluster Inference</strong>: Supports distributed model inference service clusters, achieving intelligent load balancing, automatic failover, and high availability guarantees, significantly improving inference throughput and system stability</li>
  <li><strong>Defense Time Period Management</strong>: Supports two defense strategies: full defense mode and half defense mode, allowing flexible configuration of defense rules for different time periods, achieving precise time-based intelligent monitoring and alerting</li>
  <li><strong>OCR and Speech Recognition</strong>: Provides high-precision text recognition and speech-to-text capabilities, supporting multi-language recognition</li>
  <li><strong>Multimodal Vision Large Models</strong>: Supports various vision tasks including object recognition and text recognition, providing powerful image understanding and scene analysis capabilities</li>
  <li><strong>LLM Large Language Models</strong>: Supports intelligent analysis and understanding of multiple input formats including RTSP streams, video, images, audio, and text, achieving multimodal content understanding</li>
  <li><strong>Model Deployment and Version Management</strong>: Supports rapid deployment and version management of AI models, enabling one-click model deployment, version rollback, and gray release</li>
  <li><strong>Multi-Instance Management</strong>: Supports concurrent operation and resource scheduling of multiple model instances, improving system utilization and resource efficiency</li>
  <li><strong>Camera Snapshot</strong>: Supports real-time camera snapshot functionality with configurable snapshot rules and trigger conditions, achieving intelligent snapshot capture and event recording</li>
  <li><strong>Snapshot Storage Space Management</strong>: Provides storage space management for snapshot images with quota and cleanup policy support, ensuring rational utilization of storage resources</li>
  <li><strong>Video Storage Space Management</strong>: Provides storage space management for video files with automatic cleanup and archiving, achieving intelligent storage resource management</li>
  <li><strong>Snapshot Image Management</strong>: Supports full lifecycle management of snapshot images including viewing, searching, downloading, and deletion, providing convenient image management functionality</li>
  <li><strong>Device Directory Management</strong>: Provides hierarchical device directory management with device grouping, multi-level management, and permission control, achieving organized and fine-grained device management</li>
  <li><strong>Alarm Recording</strong>: Supports automatic recording triggered by alarm events. When abnormal events are detected, relevant video clips are automatically recorded, providing a complete alarm evidence chain. Supports viewing, downloading, and management of alarm recordings</li>
  <li><strong>Alarm Events</strong>: Provides comprehensive alarm event management functionality, supporting real-time alarm event push, historical query, statistical analysis, event processing, and status tracking, achieving full lifecycle management of alarms</li>
  <li><strong>Video Playback</strong>: Supports fast retrieval and playback of historical recordings, providing convenient operations such as timeline positioning, variable speed playback, and keyframe jumping. Supports synchronized playback of multiple video streams, meeting event backtracking and analysis needs</li>
</ul>

#### 🌐 IoT Capabilities

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
Many projects reduce IoT to a "device ledger + message relay"—devices connect but cannot be governed; data reports but cannot drive action; alerts fire but the site stays invisible; you have data but cannot build screens or align with process flows. EasyAIoT positions IoT as the <strong>execution nerve</strong> in a <strong>sense—understand—decide—act</strong> closed loop: sensors and actuators provide "numbers," cameras and AI provide "pictures," visualization dashboards and SCADA configuration turn "numbers" into commandable situational awareness, and rules plus device shadows weave both into operable business actions—so the platform not only "sees clearly," but also "displays on screen, understands the process, governs effectively, controls precisely, and scales openly."
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Visual Management</strong>: When device metrics, alerts, and business KPIs stay trapped in lists and message payloads, leadership cannot see the full picture, duty staff cannot read the situation, and reports still need separate PPTs—data value stalls at "collected but not displayed." The platform consolidates visualization projects, template center, asset library, data sources, and service deployment into one capability: drag IoT data into operational dashboards for campus situational awareness, production-line KPIs, equipment operations, and more—draft, refine, publish, and deploy—upgrading IoT from "data in the back office" to "screens in the front office," without bolting on a separate dashboard tool for command and display</li>
  <li><strong>Visualization Project Full Lifecycle</strong>: When dashboard projects live on personal PCs and temporary links, handoffs get messy, versions get lost, and go-live becomes contentious. The platform manages dashboard project creation, editing, preview, publishing, and retirement in one place—table/card views for inventory, published vs. unpublished at a glance—who is working on what, how far along, and whether it can go on the wall; project status is trackable, handoff-ready, and acceptance-ready, turning "build one screen" into a deliverable operational asset</li>
  <li><strong>Visualization Template Center</strong>: Starting every project from a blank canvas inevitably stretches delivery with design and integration. Mature templates for campus overview, factory situational awareness, equipment boards, and more can be reused—create a new project, apply a template, fine-tune—fewer blank-canvas starts for similar scenarios, faster PoC and multi-project replication with consistent metrics, turning "did it once" into "can deliver many times"</li>
  <li><strong>Visualization Assets & Data Source Governance</strong>: When icons, backgrounds, and video assets are hoarded per project and data APIs are rewritten per screen, styles clash and fields drift. The asset library centralizes reusable visual assets; data sources uniformly connect device and business APIs—the same visual style and data definitions serve multiple dashboards; change once, benefit everywhere, with less duplicate build and fewer metric disputes</li>
  <li><strong>Visualization Publishing & Service Deployment</strong>: A dashboard that cannot be deployed is wasted effort. After confirmation, projects link to service deployment and go live in command centers, duty rooms, or public display entry points—preview and production use the same project—from "edit mode" to "on-duty mode" with a clear path; acceptance and daily watch no longer rely on temporary links and verbal agreements</li>
  <li><strong>SCADA Configuration Management</strong>: Industrial and building sites fear "gauges everywhere but process unreadable"—meters, valves, and tank levels have readings, yet duty staff cannot map them to pipelines and steps, and anomalies are guessed from experience. The platform provides Web SCADA capability, binding device metrics to water-plant process overviews, production-line boards, plant network topology, electrical room monitoring, and more—edit and preview in one entry, publish for duty—so "numbers" return to "diagrams," process state is obvious at a glance, and watch shifts from flipping tables to reading process diagrams for judgment and action</li>
  <li><strong>SCADA Screen Real-Time Monitoring & Limited Control</strong>: Pure list monitoring "shows points but not the process"—slow anomaly localization, hard shift handoffs, and on-site training by senior staff only. SCADA runtime animates key metrics onto tanks, valve groups, motors, and switches; trends and status refresh on one screen; limited start/stop and reset actions can be done from the diagram when needed—newcomers learn from the diagram, shifts hand off on the same screen, and anomalies compress from "find the point" to "read the process," bringing industrial sites into daily operations that are watchable, accountable, and extensible</li>
  <li><strong>Product Model Management</strong>: The costliest part of IoT rollout is often not buying devices, but rebuilding profiles for every new device class. Products serve as templates for similar devices—create, enable/disable, search, and switch between table/card views; configure application scenarios, vendor, and model once—then scale by reusing the product template instead of filling each unit from scratch. Define once, reuse many times, and turn linear access cost into a reusable asset</li>
  <li><strong>Multi-Type Product Modeling</strong>: When direct terminals, edge gateways, gateway sub-devices, and video devices coexist, forcing one access path mixes topology and breaks protocols. Model four forms separately—direct-connected, gateway, gateway sub-device, and video—so edge aggregation, direct terminals, and video devices each follow their own path. Topology stays clean, protocols stay correct, and large-scale onboarding starts from the right product skeleton</li>
  <li><strong>Product Access Protocol & Auth Configuration</strong>: Agreeing protocol and auth per device is a classic source of integration rework. Finalize access protocol (MQTT / TCP / HTTP / Modbus-TCP / Modbus-RTU / OPC UA), data format, authentication, and encryption/decryption at the product level; child devices inherit the same rules—no more per-device auth or payload negotiations. Access norms shift from “oral tradition” to an inheritable product-level contract</li>
  <li><strong>Modbus-TCP industrial Ethernet access</strong>: For meters, PLCs, VFDs and other Ethernet-side industrial devices, built-in Modbus-TCP master acquisition—configure access parameters and measurement points at product/device level to go live; polled reads flow into device shadow and online status; register writes and property downlink are connected, so industrial points share the same closed loop as IoT thing models, rule engine and alarms—no separate SCADA/acquisition tool required.</li>
  <li><strong>Modbus-RTU serial field access</strong>: Many field instruments remain on RS-485; TCP-gateway-only paths double cost and failure points. Platform supports Modbus-RTU serial master acquisition, works with virtual and real serial ports—bus-side devices enter unified management and uplink/downlink control, filling the gap where Ethernet cannot reach and serial was unmanaged.</li>
  <li><strong>OPC UA industrial interconnect access</strong>: For modern industrial control and upper-system interconnect, OPC UA client access—configure node address, namespace and point mapping for subscribe/read/write; complex device models map to platform thing-model properties; uplink acquisition and downlink write points seamlessly connect to device shadow, rule chains and message push—bringing OPC UA field assets into an AIoT ops system that can “see, control, and link”.</li>
  <li><strong>EDGE C# edge collection runtime</strong>: An independently deployable edge collection module for industrial sites—C# pluggable collectors for Modbus RTU, Modbus TCP, OPC UA, and more; local scheduled acquisition and config-driven parsing; MQTT integration with DEVICE/<strong>iot-sink</strong> on the cloud platform. It maps to the GATEWAY role in device management (not a separate device UI): on-site aggregation, cloud-side governance; gateway/sub-device property uplink-downlink and config push are covered; topology and sub-device event/service passthrough are still evolving. Packagable for x86_64 / ARM64 Linux industrial PCs and edge gateways—"accurate on site, governed in the cloud" cloud-edge closed loop</li>
  <li><strong>Thing Model Property Definition</strong>: If dashboards, rules, and alerts each invent their own metric names, they will never understand each other. Define reportable/readable-writable properties first, with standard templates and custom ones; edit as draft, publish to take effect—dashboards, rules, and alerts then share one field set. “What can be observed” has unified semantics, and inconsistent metric-name rework is cut at the root</li>
  <li><strong>Thing Model Service Definition</strong>: Writing a one-off API for every remote start/stop or reset fragments the control plane. Define callable services with input/output parameters as a contract; edit as draft, publish to take effect—“what can be done remotely” is invoked by filling contract parameters, without stacking one-off control APIs. Control becomes reusable and auditable</li>
  <li><strong>Thing Model Event Definition</strong>: Without agreeing upfront on which business events devices report, alert wording will conflict over time. Define event types first; after draft publish they take effect uniformly—event logs and rule triggers share the same semantics. “What can happen” has one vocabulary, and alerts no longer speak past each other</li>
  <li><strong>Thing Model Publish Control</strong>: Pushing model changes straight to online devices can hit an entire fleet with one misoperation. Changes land as drafts first; only confirm-and-publish pushes them to the device side—unverified edits never strike live field devices, and misoperation risk drops sharply</li>
  <li><strong>Protocol Script Adaptation</strong>: The hardest part on site is rarely standard MQTT—it is private multi-vendor payloads and black-box devices that only local tools can debug. Standard messages work out of the box; for private protocols, write uplink/downlink encode-decode scripts with templates, validation, instant debug, and save-to-hot-reload—integration shifts from “change firmware and wait on the vendor” to “configure a script and hot-apply.” Legacy multi-vendor devices join a unified thing model without firmware changes</li>
  <li><strong>Product Access Guide</strong>: If newcomers depend entirely on on-site expert walkthroughs, delivery pace is capped by people. Product details include built-in integration parameters, auth, message samples, and acceptance notes—follow the page to accept a device. Each product ships with a standard integration playbook, less reliance on oral expertise, and faster, steadier PoC and acceptance</li>
  <li><strong>Product-Linked Device Overview</strong>: Ops and acceptance often argue over “how many devices does this batch cover, and what’s the online rate?” Open a product to see its device list and online status—coverage and online rate at a glance, with clear ownership boundaries between ops and acceptance</li>
  <li><strong>Device Profile Management</strong>: Devices scattered across spreadsheets, chat logs, and field memory make inventory and handoff chaotic. Full CRUD, search by product/identifier/online status, and table/card views turn scattered terminals into a searchable ledger—inventory, handoff, and expansion all enter through one door</li>
  <li><strong>Device Online & Activation Status</strong>: Problem devices buried in “all devices” force blind hunting on duty. Lists and details surface connection status, activation status, activation time, and last online time—offline and inactive units float up first, so ops energy hits truly abnormal devices</li>
  <li><strong>Register Devices by Product</strong>: Re-picking protocol and re-filling auth for every new unit is the biggest friction in scale-out. Bind the product on create to inherit protocol and scenario—registration attaches the right template; scale by cloning the product, with far less repeated protocol/auth work</li>
  <li><strong>Industrial Collection Access Config</strong>: If meters and sensors still need a separate collection tool, the site ends up running dual systems. When registering industrial collection devices, configure host, metrics, and collection interval in the same step—field points are filed once, no switch to another SCADA/collection tool; industrial collection and platform onboarding complete together</li>
  <li><strong>Device Basic Profile</strong>: If replacement, accountability, and reconciliation rely on verbal “who is this,” the responsibility chain breaks. Persist name, identifier, SN, product, version, IP, and other one-device-one-record fields—open the profile to confirm identity, with less verbal chasing and on-site digging</li>
  <li><strong>Device Access Guide</strong>: If field integration still means hunting thick docs and asking experts, go-live stretches endlessly. Per device type: recommended commands, integration parameters, auth, messages, and acceptance notes; copy commands after parameter edits—integration becomes copy-command acceptance, and go-live/PoC pace tightens</li>
  <li><strong>Real-Time Running Status</strong>: If operators must log into devices and parse raw payloads every time to judge metrics, duty cost stays high. Spread current property live values by thing model, with table/card views and refresh—judge key metrics at a glance without logging into devices or reading raw messages</li>
  <li><strong>Sensor Float Data Prediction</strong>: If key metrics can only be reviewed after the fact on historical curves, anomalies often stay invisible until they have already crossed the line. The platform forecasts trends for sensor float properties, turning past readings into forward-looking trajectories—ops upgrades from “looking at numbers after the fact” to “seeing ahead,” buying time to act</li>
  <li><strong>Running-Status Property Thresholds</strong>: If health boundaries live only in code or oral agreements, every new model or scenario means rework. Configure upper/lower thresholds for running-status properties by thing model—boundaries become definable, reusable, and fine-grained, turning each device’s “normal range” into a governable asset instead of scattered tribal knowledge</li>
  <li><strong>Threshold Alarms & Threshold Rules</strong>: Thresholds are decoration if crossings go unnoticed or cannot be linked. Out-of-bound metrics trigger alerts automatically and can drive rule-based actions—“know when crossed, manage when known,” closing health boundaries into an operable loop</li>
  <li><strong>Central-Device Associated Sub-Device One-Screen Control</strong>: If subordinate health must be checked device by device, inspection and incident response always lag. From the central-device view, survey associated sub-device running status on one screen—no device-by-device switching, faster field inspection and anomaly localization, so the device side truly closes the loop of “see the numbers, govern the bounds, raise the alerts, and grasp the whole picture”</li>
  <li><strong>Device Shadow Comparison</strong>: Classic troubleshooting pain is not knowing whether “desired” matches “actual.” View reported state, desired state, and diffs side by side, with full JSON retained—troubleshooting shifts from guessing to comparing, and consistency is obvious at a glance</li>
  <li><strong>Desired Property Push</strong>: Driving to site just to change one parameter is classic scale-out waste. Batch-edit desired values for writable properties and push in one click; track processing/success/failure—remote tuning has receipts, no truck roll for a parameter change, fewer wasted trips</li>
  <li><strong>Thing Model Service Invocation</strong>: If start/stop or reset cannot confirm execution after issue, disposal falls back to verbal accounting. Fill parameters for published services and invoke; track command receipts—actions confirm whether they executed, disposal is auditable, and “we said we controlled it” upgrades to a closed loop with receipts</li>
  <li><strong>Offline Command Queue</strong>: Commands dropped during weak network or brief offline must be redone later. While offline, commands still write to desired shadow and are pulled or received after reconnect per protocol—control intent survives jitter, catch-up on return, fewer repeated operations</li>
  <li><strong>Sub-Device Gateway Proxy Control</strong>: Requiring every edge terminal to connect directly to the platform explodes access complexity and certificate cost. Sub-devices are controlled via their parent gateway—edge terminals can be remoted without direct platform links, lowering terminal access complexity and making the gateway a truly operable aggregation plane</li>
  <li><strong>Linked Cameras</strong>: Sensor alerts without a live view leave operators “hearing numbers and guessing the scene.” IoT devices can bind cameras from the device catalog, mapping telemetry points to video locations—when something goes wrong, you know which stream to open, upgrading “report a number” to “find the picture”</li>
  <li><strong>Split-Screen Monitoring & AI Linkage</strong>: This is EasyAIoT’s key difference from pure IoT platforms—pure IoT “sees numbers but not the site,” pure video “sees the site but cannot control devices.” In function invocation, switch 1/4/9 split-screen preview of linked cameras and enable AI analysis—tune parameters and issue commands while watching the site. “Numbers” and “pictures” are verified and handled on one screen, with fewer system switches and missed judgments—true AI + IoT fusion value</li>
  <li><strong>Event Logs</strong>: Alert pop-ups vanish in a flash; postmortems then rely on memory and argument. Aggregate info/warning/error events from devices; filter by type, name, and time—reviews read the raw event stream, answering “what happened on site” with evidence, not just instantaneous pop-ups</li>
  <li><strong>Command Logs</strong>: Integration troubleshooting fears both sides claiming opposite facts: did the command reach the device, and did it accept it? Track processing/success/failure for property sets and service calls—end verbal blame games; the command path is checkable and accountable</li>
  <li><strong>Device Logs</strong>: If locating firmware or business faults still means logging into devices for local files, field network and permission walls kill efficiency. Aggregate multi-level device-side logs to the cloud with keyword and time search—locate anomalies in the cloud without logging into devices for local logs</li>
  <li><strong>Gateway Sub-Device Binding</strong>: Industrial and building sites often hang dozens or hundreds of sub-devices under one gateway; if topology lives only in oral memory, expansion and fault isolation fail. Gateways can batch bind/unbind sub-devices—who hangs under whom is clear, and ownership stays sharp when expanding, replacing gateways, or isolating faults</li>
  <li><strong>Topic Capability Inventory</strong>: If R&D and integration each hold a different channel contract, integration rework is guaranteed. Per device, list uplink/downlink channel docs for config, shadow, properties, services, events, OTA, clock sync, and more—integrate against one shared catalog, with fewer reworks from mismatched channel agreements</li>
  <li><strong>OTA Package Management</strong>: If patches and firmware rely on USB-stick copying device by device, scale-out upgrades are nearly impossible. Centrally upload and archive software/firmware packages with version, download, edit, delete, and dual views—patches and firmware live in one reusable place, no per-device media copying; firmware becomes a manageable delivery asset</li>
  <li><strong>OTA Upgrade Strategy</strong>: Missed upgrades leave security holes; chaotic upgrades create compatibility risk—the classic scale-out dilemma. Mark critical versions and choose forced/non-forced modes—urgent fixes can be pushed through, routine versions stay orderly, and both miss-upgrade and chaos risks stay controlled</li>
  <li><strong>Rule Chain Management</strong>: Business linkage rules scattered everywhere and impossible to toggle centrally breed false triggers and idle chains. Create, enable/disable, and batch-delete rules with list/card management—linkage chains switch centrally, idle rules turn off anytime, and false triggers drop</li>
  <li><strong>Visual Rule Chain Orchestration</strong>: Field business changes daily—thresholds to tune, linkages to add—if every change waits on custom code, response is always half a beat late. On a chain canvas, link data flow, conditions, and downstream actions by intent—scenario changes land by drag-and-drop, no waiting on a sprint. “What happens after device data arrives” is configured by business users</li>
  <li><strong>Rule Import/Export</strong>: If mature rules cannot travel, every project rewrites from scratch. Import/export rules across environments and projects—mature rules become copyable delivery assets</li>
  <li><strong>Message Configuration</strong>: If swapping notification channels or accounts still requires business-code changes, ops stays blocked by developers. Centrally maintain notification channels and base message settings—swap channels or accounts by config only, without touching business code</li>
  <li><strong>Message Templates</strong>: Ad-hoc alert wording is error-prone and hard to unify. Maintain templates for email, SMS, Enterprise WeChat, DingTalk, Feishu, Webhook, and more—copy once, reuse everywhere; unified alert wording, fewer temporary composition mistakes</li>
  <li><strong>Message Push</strong>: Even perfect detection and complete device events are worthless if stuck inside the system waiting for someone to open it. Create push tasks by channel; test first, then start—alerts and business events land in owners’ daily work tools, not trapped in the system</li>
  <li><strong>Push History</strong>: Without records of whether notices were sent or delivered, audit and optimization are guesswork. Review push records by channel—sent or not, delivered or not, with evidence for audit and reach-strategy improvement</li>
  <li><strong>Notification Users & Groups</strong>: All-hands critical alerts cause fatigue; missing the right people causes misses. Maintain notification users and groups for precise reach by role/shift—the right people get them, all-hands spam fatigue drops, and sense—judge—notify—act finally closes to the person</li>
  <li><strong>TRANSFORM Multidirectional Business Flow</strong>: If platform-side alerts, device events, and business results stay trapped inside EasyAIoT, integrating MES / ERP / CRM / WMS still means per-project custom APIs—delivery cycles and rework costs explode. TRANSFORM turns “who to send to, by which rules, how fields map, and whether it arrived” into configurable capability: destinations, forwarding rules, and mapping templates are set once and reused; delivery is monitorable and reviewable—multi-system integration shifts from “custom API per partner” to “wire by contract, accept by trail,” so platform data truly enters the customer’s existing business loop</li>
</ul>

#### 📱 Mobile APP

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Multi-Channel Access</strong>: Available on phones, mini programs, and apps—ops and management are no longer tied to a desk; handle issues on-site in real time</li>
  <li><strong>Capability Parity</strong>: Mobile matches the PC admin console feature-for-feature; switch devices without losing control</li>
  <li><strong>Device Management</strong>: Unified management across access methods; browse channels at a glance and tap for live view—stay informed during field inspections</li>
  <li><strong>Stream Forwarding</strong>: Create and stop forwarding anytime; see node and channel status; multi-channel raw video can go on screen efficiently—even while away from the desk</li>
  <li><strong>Algorithm Tasks</strong>: Start and stop real-time and snapshot tasks on the go; track detection results without waiting to get back to the office</li>
  <li><strong>Alert Center</strong>: Search alerts instantly; tap to view snapshots and recordings—verify and follow up while on mobile duty</li>
  <li><strong>Model Management</strong>: Deployment status at a glance; always know what's live</li>
  <li><strong>Model Inference</strong>: Upload an image on-site and get results immediately—spot checks without returning to PC</li>
  <li><strong>Model Training</strong>: Monitor training progress anytime; stop remotely when needed to avoid wasted compute</li>
  <li><strong>Personal Center</strong>: Account, tenant, and app preferences in one place—convenient across devices</li>
  <li><strong>Smooth Viewing</strong>: Live feeds and alarm recordings play smoothly on mobile—low latency, no stutter, uncompromised duty experience</li>
  <li><strong>Stay Connected</strong>: Sessions stay active with less re-login—bringing cloud-edge-device intelligent control to phones and mini programs</li>
</ul>

#### 💻 IDEA Cloud IDE

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Develop in the browser</strong>: VS Code–style online IDE on code-server; clones the full EasyAIoT repo by default—contributors can edit, run module-level checks, and open PRs without setting up a local toolchain first</li>
  <li><strong>Standalone portal and multi-user</strong>: Ops console on <code>:9300</code>, decoupled from the WEB admin; one Docker workspace per person; port pool 13338–13437 for concurrent users; console floating ball jumps to the portal</li>
  <li><strong>Six-language toolchain aligned with the host</strong>: Preinstalled <strong>JDK 21</strong>, Node 22, Python, Go, CMake/C++, and .NET 8—covers reading, light edits, and module-level checks for WEB / DEVICE / AI / RUNTIME / EDGE</li>
  <li><strong>AI co-creation</strong>: GitHub Copilot preinstalled (sign in with your own GitHub account; the platform never holds keys); without a Copilot subscription, bring your own OpenAI-compatible API key via Continue; toolbar opens HARNESS AI Assistant in a split pane—drag files to auto <code>@</code>-mention while you edit</li>
  <li><strong>Local publish</strong>: Suggests modules from workspace diffs, one-click build and replace running containers on the host—refresh to verify, shortening the edit-to-see loop</li>
  <li><strong>OAuth and idle reclaim</strong>: Gitee / GitHub login (can be required), one account per workspace; idle auto-stop after 8 hours by default; heartbeat and opening the IDE refresh activity so compute is not left spinning</li>
  <li><strong>Contribution loop</strong>: Bind your fork → branch → edit → push to the fork → open a PR to upstream</li>
</ul>

#### 🤖 HARNESS AI Assistant

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0 12px;">
Many modules and long chains—checking health, asking about architecture, and finding configs often means digging through docs and SSH. HARNESS bundles platform knowledge and live probes into a <strong>conversational assistant</strong>: ask and check from the bottom-right corner of any business page, shortening troubleshooting and PoC cycles with less reliance on the vendor and tribal knowledge.
</p>

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Ask and check</strong>: The Agent calls platform Tools to probe Gateway / video / AI service health and points to related config and source—compressing SSH + compose digging into one conversation</li>
  <li><strong>Knows the ontology</strong>: Built-in <code>HARNESS/ontology/AGENTS.md</code> and full-repo workspace—architecture, ports, APIs, and install conventions in one place</li>
  <li><strong>Chat in-page</strong>: Floating drawer iframe—no page switch or lost context while viewing alarms/devices; full-screen “AI Assistant” or new window also available</li>
  <li><strong>IDEA split-pane co-creation</strong>: Toolbar opens the AI assistant on the right—editor and Agent side by side; or deep-link with <code>?file=path&harness=1</code> to open a file and split</li>
  <li><strong>Drag to auto @</strong>: Drop explorer files onto the assistant pane to attach them as chat context</li>
  <li><strong>Two-way jump</strong>: Agent can generate portal links via <code>easyaiot_open_in_idea</code>—from Q&amp;A back to a full IDE where you can edit and publish; IDEA for code and PRs, HARNESS for architecture and health</li>
  <li><strong>MCP + Cursor Skill</strong>: Same <code>easyaiot_*</code> capabilities exposed via MCP to Cursor and other IDEs—what you can ask and check in the console, you can invoke in dev; Skills reusable across projects</li>
  <li><strong>Ready in all profiles</strong>: Based on <a href="https://github.com/deepseek-ai/deepseek-harness" style="color: #3498db; text-decoration: none; font-weight: 600;">DeepSeek Harness</a> Sidecar (<code>:3080</code>); included by default in <code>mini / standard / full</code> (<code>EASYAIOT_ENABLE_HARNESS=0</code> to disable); DeepSeek / OpenAI-compatible endpoints; bring your own Key in <code>harness.env</code> or the UI</li>
  <li><strong>Security note</strong>: Experimental module; upstream <code>dsh</code> is Developer Preview; restrict access in production and configure write/Shell approval; do not commit API Keys to Git</li>
</ul>

### 📦 Built-in AI Models

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
The platform is ready to use out of the box, with multiple pre-trained models built in for security monitoring, industrial sites, smart transportation, and similar scenarios. Select them directly in algorithm tasks for rapid deployment and inference—no training from scratch required to cover common vision detection needs.
</p>

| Model Name | Inference Format | Base Model | Capability |
| :-- | :--: | :--: | :-- |
| Safety Helmet Model | ONNX | YOLOv8 | Detect whether workers are wearing safety helmets |
| Sleeping on Duty Model | PyTorch | YOLOv8 | Detect sleeping on duty, leaving post, and other abnormal behaviors |
| Person Detection Model | PyTorch | YOLOv8 | General human detection for identifying and locating people in the frame |
| License Plate Model | ONNX | YOLOv8 | Recognize vehicle license plate information |
| Reflective Vest Model | PyTorch | YOLOv8 | Detect whether workers are wearing reflective vests |
| Flame Model | PyTorch | YOLOv8 | Detect open flames and fire hazards |
| Smoking Detection Model | PyTorch | YOLOv8 | Detect smoking behavior |
| Phone Call Detection Model | ONNX | YOLOv8 | Detect phone calls and mobile phone use |
| Road Waterlogging Model | ONNX | YOLOv8 | Detect road water accumulation and surface flooding |
| Face Mask Model | ONNX | YOLOv8 | Detect whether people are wearing masks correctly |
| Fall Detection Model | ONNX | YOLOv8 | Detect falls and other abnormal postures |
| Face Detection Model | ONNX | YOLOv8 | Detect face locations in the frame to support face recognition workflows |

### 💡 Technical Philosophy

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
We believe no single programming language excels at everything. EasyAIoT uses six programming languages mixed by scenario: Java for platform architecture, Python for AI algorithms, C++ for video execution, Go for protocol gateway, TypeScript for management UI, C# for edge industrial acquisition—cloud management, algorithms, execution, protocols, UI, and on-site acquisition each in its place, forming a complete cloud-edge-device technical closed loop.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Java excels at building stable and reliable platform architectures, but is ill-suited to network programming and AI development; Python excels at network programming and AI algorithms, but hits GIL and process-overhead bottlenecks on high-channel, low-latency frame execution; C++ excels at high-performance task execution, but is ill-suited to platform architecture and algorithm orchestration; Go excels at high-concurrency networking and protocol implementation, but is ill-suited to platform control planes and AI algorithms; TypeScript excels at complex front-end interactions and type-safe engineered UIs, but is ill-suited to high-performance backend computing and AI inference; C# excels at industrial protocol acquisition and edge runtime orchestration, with strong typing ensuring reliable point mapping and protocol parsing, <code>async/await</code> supporting concurrent multi-device polling, .NET cross-platform publishing adapting to x86/ARM industrial sites, mature industrial/SCADA ecosystem with fast integrator onboarding, but is ill-suited to cloud platform core business and AI algorithms. Six languages each play to their strengths and avoid weaknesses—challenging to implement, yet extremely easy to use.
</p>

![EasyAIoT Platform Architecture.jpg](.image/iframe2.jpg)

### 🔄 Module Data Flow

<img src=".image/iframe3.jpg" alt="EasyAIoT Platform Architecture" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🤖 Zero-Shot Labeling Technology

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Innovatively leveraging large models to construct a zero-shot labeling technical system (ideally completely eliminating manual labeling, achieving full automation of the labeling process), this technology generates initial data through large models and completes automatic labeling via prompt engineering. It then ensures data quality through optional human-machine collaborative verification, thereby training an initial small model. This small model, through continuous iteration and self-optimization, achieves co-evolution of labeling efficiency and model accuracy, ultimately driving continuous improvement in system performance.
</p>

<img src=".image/iframe4.jpg" alt="EasyAIoT Platform Architecture" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

### 🏗️ Project Architecture Features

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
EasyAIoT is not actually one project; it comprises multiple independently deployable sub-projects (WEB, DEVICE, EDGE, VIDEO, RTC, AI, and more).
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
What's the benefit? Suppose you are on a resource-constrained device (like an RK3588). You can extract and independently deploy just one of those projects. Therefore, while this project appears to be a cloud platform, it simultaneously functions as an edge platform.
</p>

<div style="margin: 30px 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">

<p style="font-size: 16px; line-height: 1.8; margin: 0; font-weight: 500;">
🌟 Genuine open source is rare. If you find this project useful, please star it before leaving - your support means everything to us!<br>
<small style="font-size: 14px; opacity: 0.9;">(In an era where fake open-source projects are rampant, this project stands out as an exception.)</small>
</p>

</div>

### 🌍 Localization Support

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT actively responds to localization strategies, providing comprehensive support for localized hardware and operating systems, delivering secure and controllable AIoT solutions for users. Deployment and PANEL packaging already cover domestic OS targets such as <strong>Kylin (麒麟) / openEuler (欧拉)</strong>.
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖥️ Server-Side Support</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Full compatibility with Hygon x86 architecture processors</li>
  <li>Support for localized server hardware platforms</li>
  <li>Targeted performance optimization solutions</li>
  <li>Ensures stable operation of enterprise applications</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📱 Edge-Side Support</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Ordinary development boards can perform on-site intelligent watch duty</li>
  <li><strong>EDGE</strong> C# edge collection deployable independently on industrial PCs and RS485 sites</li>
  <li>Lightweight deployment on site—no need to stack heavy storage at every site</li>
  <li>Intelligence out of the box, shortening edge go-live cycles</li>
  <li>Compute scales with deployment points; alerts and evidence automatically aggregate to the cloud</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖱️ Operating System Support</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Compatible with <strong>Kylin (麒麟) / openEuler (欧拉)</strong></li>
  <li>Support for localized Linux distributions like Founder</li>
  <li>Adaptation to mainstream localized operating systems like UOS</li>
  <li>Provides complete localized deployment solutions</li>
</ul>
</div>

</div>

## 🎯 Application Scenarios

![Application Scenarios.png](.image/适用场景.png)

## 🧩 Project Structure

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT comprises core modules including WEB, APP, DEVICE, EDGE, SENTINEL, VIDEO, RTC, AI, RUNTIME, POST, VISUALIZE, TRANSFORM, PANEL, IDEA, HARNESS, and SITE, plus COMPILE multi-platform packaging and delivery:
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 20%;">Module</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">Description</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>SITE Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Official value entry</strong>: Standalone official website for visitors, integrators, and end customers—explain cloud-edge-device integration clearly, then guide people to download and deploy</li>
    <li><strong>Shorter learning path</strong>: Features, four hardware tiers, installer entry, and docs on one site—less time hunting the repo or asking around for packages</li>
    <li><strong>Supports tier selection</strong>: Present edge / mini / standard / full for light standalone, edge boxes, AI cameras, and full-stack appliances so sites pick the right tier once</li>
    <li><strong>From interest to install</strong>: Website, demo, open-source repos, and Releases form one loop—understand → try → download → install</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>WEB Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Unified Admin UI</strong>: Frontend management interface with a consistent user experience</li>
    <li><strong>Multi-Protocol Onboarding Wizard</strong>: Tabbed guides for IPC / NVR / GB28181 / RTC platforms; ONVIF scan, cross-subnet scan, manual RTSP, DJI livestream, and consumer-camera P2P access</li>
    <li><strong>RTC Platform Access</strong>: "Connect RTC camera" shortcut with dynamic forms for <strong>Tapo / Tuya / Ring / Nest / Xiaomi / Wyze / DoorBird / GoPro / Roborock</strong>; OAuth platforms guided to go2rtc WebUI for binding</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>APP Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Multi-Channel Access</strong>: One build, multiple touchpoints—phones, mini programs, and apps</li>
    <li><strong>Capability Parity</strong>: Matches PC admin console capabilities with multi-tenant switching</li>
    <li><strong>Device Management</strong>: Unified management for direct cameras, GB28181, NVR, and RTC consumer cameras; online status and channel browsing with one-tap live preview in device details</li>
    <li><strong>Stream Forwarding</strong>: Task create/start/stop, node status, and multi-channel viewing; switch high-performance / compatibility mode by site</li>
    <li><strong>Algorithm Tasks</strong>: Real-time/snapshot algorithm task list, start/stop control, and detection/frame stats</li>
    <li><strong>Alert Center</strong>: Alert search, snapshot preview, and alarm recording VOD playback</li>
    <li><strong>Models & AI</strong>: Model list and deployment status, mobile image inference workbench, training task progress monitoring and stop</li>
    <li><strong>Profile</strong>: Personal info, account security, FAQ, feedback, and app settings</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>ANDROID / IOS / HARMONYOS Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>One frontend, three native shells</strong>: APP uni-app pages packaged into installable apps on Android (DCloud offline runtime + Gradle → APK), iOS (WKWebView shell + xcodebuild → .app / .ipa), and HarmonyOS (ArkWeb shell + hvigor → HAP)—same business logic on every mainstream phone OS</li>
    <li><strong>One-command packaging</strong>: <code>make-apk.sh</code> / <code>make-ipa.sh</code> / <code>make-hap.sh</code> with version-consistency checks; prod / test / dev environments build independent artifacts</li>
    <li><strong>Unified management</strong>: <code>.scripts/docker/mobile.sh</code> for status / build / bump / artifacts / clean; <code>bump</code> updates all five version fields at once and packaging refuses mismatched versions</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>DEVICE Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Device Management</strong>: Device registration, authentication, status monitoring, lifecycle management</li>
    <li><strong>Product Management</strong>: Product definition, thing model management, product configuration</li>
    <li><strong>Protocol Support</strong>: Multiple IoT and industrial protocols including MQTT, TCP, HTTP, Modbus-TCP, Modbus-RTU, OPC UA</li>
    <li><strong>Device Authentication</strong>: Device dynamic registration, identity authentication, secure access</li>
    <li><strong>Rule Engine</strong>: Data flow rules, message routing, data transformation</li>
    <li><strong>Data Collection</strong>: Device data collection, storage, query, and analysis</li>
    <li><strong>Node Orchestration</strong>: Compute/media node onboarding, connectivity testing, workload scheduling, and media node pool allocation</li>
    <li><strong>Visualization Backend</strong>: Unified management of dashboard/SCADA projects, templates, assets, data sources, and service deployment, providing project management and publishing for the visualization editor and Web SCADA</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>EDGE Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Why C#</strong>: Strong-typed point mapping, async multi-device concurrent polling, 7×24 long-running stability, Linux x86/ARM cross-platform self-contained publishing—mature industrial ecosystem, fast integrator onboarding</li>
    <li><strong>C# edge collection runtime</strong>: Independently deployable edge-side collection service—pluggable collectors + local scheduling + config-driven parsing</li>
    <li><strong>Multi-protocol collectors</strong>: Built-in Modbus RTU (RS485/serial), Modbus TCP, OPC UA collectors; extend via <code>ICollector</code> plugins per job</li>
    <li><strong>MQTT cloud-edge integration</strong>: Joins as device-management GATEWAY—property reporting, sub-device property proxy reporting, cloud config push (<code>config/downstream/push</code>) and property write downlink—integrated with DEVICE/<strong>iot-sink</strong>; data shown in the same device management UI, complementary to cloud-side industrial polling (platform reaches field devices directly)—EDGE suits OT isolation and RS-485 field sites</li>
    <li><strong>Dual config channels</strong>: Local <code>device-jobs.json</code> and cloud MQTT config push both drive collection jobs</li>
    <li><strong>Linux packaging</strong>: <code>pack_linux.sh</code> produces x86_64 / ARM64 standalone deployment packages for industrial PCs and edge gateways</li>
    <li><strong>Out-of-box integration</strong>: Built-in E2E demo validates collection → MQTT uplink → cloud persistence; cloud platform integration included</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>SENTINEL Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Business-readiness sentinel</strong>: Travels with every schedulable node; continuously checks whether the box can truly take the selected workloads</li>
    <li><strong>Monitor on onboard</strong>: Inspection starts automatically after join—accept readiness the same day of scale-out</li>
    <li><strong>Schedulable capacity aggregation</strong>: Surfaces “can this node run this business?” in the console so dispatch follows real capability</li>
    <li><strong>Self-serve gap fill-in</strong>: Requests platform fill-in when expected environment is missing—fewer on-site installs</li>
    <li><strong>Air-gap friendly scale-out</strong>: Offline onboarding and environment sync for sites without public internet</li>
    <li><strong>One delivery language</strong>: Component health and schedulable functions on one screen—less guessing during acceptance and troubleshooting</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VIDEO Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Stream Processing</strong>: Supports RTSP/RTMP stream real-time processing and transmission</li>
    <li><strong>Multi-Protocol Camera Access</strong>: Unified management for GB28181, ONVIF, NVR batch scan, DJI FlightHub livestream, and RTC consumer cameras</li>
    <li><strong>RTC Integration API</strong>: <code>/register/device/rtc-live</code> one-click go2rtc stream registration and device enrollment; auto-cleanup of RTC streams on device delete</li>
    <li><strong>Algorithm Task Management</strong>: Supports realtime / snapshot / patrol; high-performance execution is the default with boxed judgment views, and compatibility mode remains available</li>
    <li><strong>Stream Forwarding Orchestration</strong>: Multi-channel raw wall display defaults to high performance; special sites can use compatibility mode; start/stop and policy changes follow automatically to cut manual rework</li>
    <li><strong>Frame Extractor and Sorter</strong>: Supports flexible frame extraction strategies and result sorting mechanisms, each algorithm task can bind independent frame extractors and sorters</li>
    <li><strong>Defense Time Period</strong>: Supports time-based configuration for full defense mode and half defense mode</li>
    <li><strong>Orchestration vs Execution</strong>: VIDEO owns device orchestration, raw preview, alert archiving, and start/stop; heavy lifting goes to <strong>RUNTIME</strong> (inference and high-performance forward)—“governed” and “fast” stay separate so channel count and latency are not dragged by Python orchestration</li>
    <li><strong>Handoff to POST judgment</strong>: Algorithm tasks can configure post-processing rules so detections enter standard alerting only after custom judgment—change rules without stopping analysis</li>
    <li><strong>Acceptance Preview</strong>: Side-by-side raw vs judgment views for faster on-site checks of latency and overlay quality</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>RTC Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>go2rtc</strong>: Built on <a href="https://github.com/AlexxIT/go2rtc">go2rtc</a> source; vendor pulled by install script</li>
    <li><strong>Nine-Brand P2P Bridging</strong>:
      <ul style="margin: 4px 0; padding-left: 18px; line-height: 1.7;">
        <li><strong>Tapo</strong> (TP-Link) — home/store IPC, cloud-password connect + two-way audio</li>
        <li><strong>Tuya</strong> — mass white-label/OEM camera onboarding</li>
        <li><strong>Ring</strong> (Amazon) — doorbells/outdoor cams for overseas sites</li>
        <li><strong>Nest</strong> (Google) — Nest Cam / Doorbell for premium projects</li>
        <li><strong>Xiaomi</strong> (Mi Home) — domestic fleet reuse without Micam</li>
        <li><strong>Wyze</strong> — ultra-low-cost IPC for pilots and wide fill-in</li>
        <li><strong>DoorBird</strong> — smart doorbell entry intercom + video</li>
        <li><strong>GoPro</strong> — HERO9–12 mobile views / emergency patrol</li>
        <li><strong>Roborock</strong> — vacuum cameras for moving under-furniture views</li>
      </ul>
    </li>
    <li><strong>Unified Management API</strong>: Platform registry, stream URL builder, go2rtc REST proxy; default ports 6100 (mgmt) / 1984 (WebUI) / 8554 (RTSP)</li>
    <li><strong>Full VIDEO Pipeline</strong>: P2P ingest → standard RTSP → SRS relay → Web playback and AI analysis—consumer and pro cameras under one ops model</li>
    <li><strong>Docker All-in-One</strong>: Single container runs go2rtc core + Python management service; host network for P2P LAN access</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>AI Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Intelligent Analysis</strong>: Responsible for video analysis and AI algorithm execution</li>
    <li><strong>Model Service Cluster</strong>: Supports distributed model inference services, achieving load balancing and high availability</li>
    <li><strong>Real-Time Inference</strong>: Provides millisecond-level response real-time intelligent analysis capabilities</li>
    <li><strong>Model Management</strong>: Supports model deployment, version management, and multi-instance scheduling</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>RUNTIME Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>High-Performance Native Execution</strong>: One binary owns pull, decode, ONNX inference, alert/heartbeat callbacks, and boxed push; default <code>executor=cpp</code>—more channels per box, lower latency, leaner resources than Python paths</li>
    <li><strong>Four Field Shapes</strong>: Realtime watch, scheduled snapshot, rotating patrol, and raw-only forwarding—pick by business need so “just want video” does not pay full AI cost</li>
    <li><strong>Raw + Judgment Dual Views</strong>: Realtime tasks default-output boxed detection streams, presented separately from VIDEO raw preview—paths do not steal from each other</li>
    <li><strong>Resource-Efficient Multi-Channel Raw Wall</strong>: Stream forward defaults to the high-performance path so “many channels watch raw, few channels run AI” can coexist on NVR sites</li>
    <li><strong>Alerts &amp; Status Back to Center</strong>: Alerts and run status aggregate to VIDEO for persistence and notification; nodes do not stack business data locally</li>
    <li><strong>Keep Realtime Under Load</strong>: When compute is tight, prioritize current picture and alert freshness—avoid “busier means more lag, more lag means more misses”</li>
    <li><strong>Prefer Acceleration, Keep Running on Fallback</strong>: Use accelerators when available; automatically continue when not—tasks do not stop</li>
    <li><strong>One-Click Distribute</strong>: WEB “workload distribute” or install scripts batch-deploy; center VIDEO install auto-mounts the local executor</li>
    <li><strong>Event plane MQTT</strong>: Alerts/snapshots/post-process via EMQX algo bus; <strong>iot-sink</strong> persists, archives, and enriches notifications</li>
    <li><strong>Management plane HTTP heartbeat</strong>: Task liveness reports to VIDEO; start/stop and task table managed by VIDEO</li>
    <li><strong>NFS media root</strong>: Alert images and SRS DVR unified to <strong>NFS shared media root</strong> (<code>EASYAIOT_MEDIA_ROOT</code>, default <code>/mnt/easyaiot-media</code>; falls back to <code>$HOME/easyaiot/media</code> without sudo); MQTT carries paths only; <strong>iot-sink</strong> reads disk and archives to MinIO</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>POST Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Custom judgment</strong>: Independent business judgment on top of object detection—turn “boxed targets” into “whether to alert and under which standard”</li>
    <li><strong>Rules per task</strong>: Region filtering, pass-through, business scripts, and industry plugins compose into rule chains for sites, campuses, traffic, and more</li>
    <li><strong>Fewer false alarms, ready to accept</strong>: Outside regions do not flood screens; trial-run rules before go-live to see what is blocked and whether alerts fire</li>
    <li><strong>Change standards without stopping analysis</strong>: Saving rules on a running task takes effect immediately—no need to stop tasks to adjust forbidden zones or add a judgment step</li>
    <li><strong>Perception and judgment decoupled</strong>: Video analysis keeps running while business logic scales on demand; industry capabilities are pluggable so one detection stack serves many projects</li>
    <li><strong>Built-in plugins</strong>: <code>line_cross</code> line crossing, <code>region_enter_exit</code> zone enter/exit, <code>dwell_timer</code> dwell timeout, <code>headcount_gate</code> headcount threshold—select in algorithm task post-processing rules without plugin registration; line crossing, enter/exit, and dwell require target tracking (<code>track_id</code>)</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VISUALIZE Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Drag-and-Drop Dashboard Editor</strong>: A high-performance low-code visualization editor focused on canvas editing and preview</li>
    <li><strong>Integrated with WEB</strong>: Project creation, templates, assets, data sources, publishing, and deployment are done in the admin console "Visualization" menu; click "Open Editor" to enter the canvas</li>
    <li><strong>Dashboard Delivery</strong>: Drag-and-drop charts, metrics, and layouts; components can connect to platform data sources and IoT metrics, supporting rapid command dashboards for campus situational awareness, production-line KPIs, equipment ops, energy consumption, and more</li>
    <li><strong>Clear Division with SCADA</strong>: Dashboards use this module; process SCADA uses Web SCADA capability; project metadata is unified under the DEVICE visualization backend</li>
    <li><strong>Deployment Profile</strong>: Same as APP as a full-edition capability; mini / standard can skip per field hardware, reducing edge lite deployment size</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>TRANSFORM Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Multidirectional Business Flow</strong>: Delivers platform-side alerts, device events, and business results to external systems such as MES / ERP / CRM / WMS by contract, closing the last mile from “the platform has data” to “business systems can use it”</li>
    <li><strong>Configurable Integration</strong>: Configure destinations, forwarding rules, and field mappings once and reuse them—cutting the cost of “custom APIs for every customer system”</li>
    <li><strong>Delivery You Can Accept</strong>: Runtime clusters and delivery trails are monitorable and reviewable, so integration and acceptance can answer “did it arrive, and where did it stall”—less verbal reconciliation</li>
    <li><strong>Horizontal Scale-Out</strong>: As traffic grows, expand consume and delivery capacity by business contract—supporting parallel integration across lines, plants, and systems</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>PANEL Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Delivery & Watch Entry</strong>: Independent of the business console: install, accept, and watch on arrival—shorten acceptance cycles and cut on-site / remote support cost</li>
    <li><strong>Same-Day Closed Loop</strong>: UI-driven install by tier with progress and results on the spot; bring up and hand over the appliance even before the business console is ready</li>
    <li><strong>Self-Serve Troubleshooting</strong>: Container health, resource levels, task logs, and image readiness at a glance—common start/stop, pull, and cache cleanup without waiting for developer commands</li>
    <li><strong>Reuse Across Sites</strong>: One entry across appliances and machine rooms—PoC and production delivery share the same playbook</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>IDEA Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Community cloud IDE</strong>: Open a VS Code–style workspace in the browser, clones the full repo by default; one Docker workspace per person, with local publish and idle reclaim—turning open-source contribution from “set up an environment first” into “open and edit”</li>
    <li><strong>Split-pane AI Assistant</strong>: Toolbar opens HARNESS on the right; drag files to auto <code>@</code>; deep-link with <code>?file=&harness=1</code></li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>HARNESS Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Conversational assistant</strong>: Ask about health, architecture, and issues—shorter troubleshooting and PoC, less vendor dependency</li>
    <li><strong>In-page floating drawer</strong>: Chat without leaving business pages; included by default in <code>mini / standard / full</code></li>
    <li><strong>IDEA split-pane link</strong>: Assistant beside the editor; drag-to-<code>@</code>, deep links, and two-way jump</li>
    <li><strong>MCP / Skill</strong>: Console and IDE share platform semantics; Skills reusable across projects</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>COMPILE Packaging</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Multi-Platform Artifacts</strong>: Package PANEL and related capabilities into installers or binaries for Ubuntu / Debian, CentOS / RHEL <strong>7–9</strong> (x86 + <strong>CentOS ARM</strong>, packages per el7/el8/el9), Windows, macOS, and ARM / <strong>Kylin (麒麟) / openEuler (欧拉)</strong> targets—so customers can install without compiling from source on site</li>
    <li><strong>Shorter Delivery Chain</strong>: Integrators pick the matching package for the target environment to deploy and upgrade—unified install, start/stop, and uninstall paths reduce cross-OS delivery variance</li>
    <li><strong>Paired with PANEL</strong>: Build outputs land the on-site ops entry directly, connecting “package it out” with “install and watch on arrival” on one delivery chain</li>
  </ul>
</td>
</tr>
</table>

## 🖥️ Cross-Platform Deployment Advantages

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
EasyAIoT supports deployment on Linux, Mac, and Windows, providing flexible and convenient deployment solutions for users in different environments; with <strong>COMPILE</strong> producing installers and binaries per target OS, and <strong>PANEL</strong> completing on-site install and day-to-day watch:
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🐧 Linux Deployment Advantages</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Ideal for production environments, stable and reliable with low resource consumption</li>
  <li>Supports Docker containerized deployment with one-click service startup</li>
  <li>Perfect compatibility with servers and edge computing devices (such as RK3588 and other ARM architecture devices)</li>
  <li>Provides complete automated installation scripts to simplify deployment</li>
  <li>Covers mainstream server distros including Ubuntu, CentOS/RHEL <strong>7–9</strong> (incl. <strong>CentOS ARM</strong>), <strong>Kylin (麒麟) / openEuler (欧拉)</strong></li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🍎 Mac Deployment Advantages</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Suitable for development and testing environments with deep macOS integration</li>
  <li>Supports local development and debugging for rapid feature validation</li>
  <li>Provides convenient installation scripts compatible with package managers like Homebrew</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🪟 Windows Deployment Advantages</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Suitable for Windows server environments, reducing learning curve</li>
  <li>Supports PowerShell automation scripts to simplify deployment operations</li>
  <li>Compatible with both Windows Server and desktop Windows systems</li>
  <li>Provides graphical installation wizards for user-friendly experience</li>
</ul>
</div>

</div>


<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>Unified Experience</strong>: Regardless of the operating system chosen, EasyAIoT provides consistent installation scripts and deployment documentation, ensuring a uniform cross-platform deployment experience.
</p>

## ☁️ EasyAIoT = AI + IoT = Cloud-Edge-Device Integrated Solution

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Supports thousands of vertical scenarios, with customizable AI models and algorithm development, deeply integrated.
</p>

<div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
<h3 style="color: #2c3e50; margin-top: 0;">Empowering Intelligent Vision for Everything: EasyAIoT</h3>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
EasyAIoT constructs an efficient access and management network for IoT devices (especially massive cameras). We deeply integrate real-time streaming technology with cutting-edge AI to create a unified service core. This solution not only enables interoperability across heterogeneous devices but also deeply integrates HD video streams with powerful AI analytics engines, giving surveillance systems "intelligent eyes" – accurately enabling facial recognition, abnormal behavior analysis, risk personnel monitoring, and perimeter intrusion detection.
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
The platform supports real-time, snapshot, and patrol algorithm tasks: all three can default to the <strong>RUNTIME high-speed execution layer</strong> (<code>executor=cpp</code>)—a native binary for long-lived pull, decode, YOLO inference, and result callbacks; realtime <strong>default-pushes boxed AI detection streams</strong>; snap uses Cron capture; patrol rotates multi-channel coverage; stream forward can use the same high-performance path for resource-efficient raw walls. Versus the Python compatibility backend, RUNTIME holds up better under high channel counts and low latency. Alerts and heartbeats return to VIDEO. Algorithm task management keeps frame extraction and sorting flexible; model-service cluster inference ensures millisecond response and high availability. Full and half defense modes support precise time-based monitoring and alerting.
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
In terms of IoT device management, EasyAIoT provides comprehensive device lifecycle management capabilities, supporting multiple IoT and industrial protocols (MQTT, TCP, HTTP, Modbus-TCP, Modbus-RTU, OPC UA). Gateways in device management are cloud-side GATEWAY / sub-device topology; the <strong>EDGE</strong> C# edge collection runtime acts as that gateway on site, handling industrial protocol acquisition and MQTT cloud-edge integration, with data flowing back into the same device management UI—achieving rapid device access, secure authentication, real-time monitoring, and intelligent control. Through the rule engine, intelligent data flow and processing of device data are realized, combined with AI capabilities for in-depth analysis of device data, achieving full-process automation from device access, data collection, intelligent analysis to decision execution, truly realizing interconnected everything and intelligent control of everything.
</p>
</div>

<img src=".image/iframe1.jpg" alt="EasyAIoT Platform Architecture" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

## ⚠️ Disclaimer

EasyAIoT is an open-source learning project unrelated to commercial activities. Users must comply with laws and
regulations and refrain from illegal activities. If EasyAIoT discovers user violations, it will cooperate with
authorities and report to government agencies. Users bear full legal responsibility for illegal actions and shall
compensate third parties for damages caused by usage. All EasyAIoT-related resources are used at the user's own risk.

## 📚 Deployment Documentation

- [Platform Deployment Documentation](.doc/部署文档/平台部署文档.md) — Step-by-step guide for Linux (Ubuntu / CentOS·RHEL **7–9** / **CentOS ARM** / ARM / **Kylin (麒麟) / openEuler (欧拉)**) / Mac / Windows
- [macOS Image Deploy](.doc/部署文档/平台macOS部署文档.md) — One-click pull of pre-built images with Docker Desktop
- [Windows Image Deploy](.doc/部署文档/平台Windows部署文档.md) — `install_windows.ps1` recommended entry
- [Deployment Best Practices](.doc/部署文档/部署最佳实践_en.md) — Profiles, environment requirements, one-click deploy (incl. CentOS **7–9** / **CentOS ARM** / **Kylin (麒麟) / openEuler (欧拉)**), troubleshooting, and production recommendations

## 📘 Operations Manual

For delivery, watchkeeping, and business operations: organized by **operation chains** (goal → prerequisites → steps → acceptance). Assumes the platform is already deployed and available. (Content is currently in Simplified Chinese.)

- [Platform Operations Manual (Index)](.doc/操作手册/README.md) — How to read, shortest closed loop, and doc index
- [Operation Chain Overview](.doc/操作手册/00-操作链总览.md) — Global map, menu quick reference, same-day PoC checklist
- [Login & Basic Setup](.doc/操作手册/01-登录与基础准备.md) — Accounts, org, permissions, notification channels
- [Video Device Onboarding](.doc/操作手册/02-视频设备接入.md) — ONVIF / NVR / GB28181 / RTC / DJI → preview & stream forward
- [AI Algorithm Task Loop](.doc/操作手册/03-AI算法任务闭环.md) — Labeling/models → tasks → alerts
- [IoT Device Onboarding](.doc/操作手册/04-物联网设备接入.md) — Product thing model → devices → EDGE / industrial acquisition
- [Alerts, Notifications & External Integration](.doc/操作手册/05-告警通知与对外联动.md) — Alert handling, notifications, TRANSFORM
- [Visualization Dashboards](.doc/操作手册/06-可视化大屏.md) — Dashboard/SCADA edit, publish, and display
- [APP Mobile Watchkeeping](.doc/操作手册/07-APP移动值守.md) — Mobile vs WEB capability map

## 🎮 Demo Environment

- Demo URL: http://36.111.47.113:8888/
- Username: admin
- Password: admin123

## 🎬 Demo Video

- Bilibili: https://www.bilibili.com/video/BV1d3846yEQz/?vd_source=5d3350c0182a2cf35c2739f3d16c1161

## ⚙️ Project Repositories

- Gitee: https://gitee.com/soaring-xiongkulu/easyaiot
- Github: https://github.com/soaring-xiongkulu/easyaiot

## 📸 Screenshots

<div>
  <img src=".image/banner/banner-video1000.gif" alt="Demo" width="49%" style="margin-right: 10px">
  <img src=".image/banner/banner-video1001.gif" alt="Demo" width="49%">
</div>

#### 🖥️ Monitoring Dashboard

| | | |
|:---:|:---:|:---:|
| ![Situational Awareness](.image/banner/banner1001.png) | ![Overview](.image/banner/banner1076.jpg) | ![Alerts](.image/banner/banner1074.jpg) |
| ![Dashboard](.image/banner/banner1075.jpg) | ![Multi-Dimensional](.image/banner/banner1095.jpg) | ![Comprehensive](.image/banner/banner1096.jpg) |
| ![Monitoring](.image/banner/banner1078.jpg) | ![Real-Time](.image/banner/banner1077.jpg) |  |

#### 📺 Visualization & SCADA

| | | |
|:---:|:---:|:---:|
| ![Project](.image/banner/banner1185.png) | ![SCADA](.image/banner/banner1186.png) | ![Editor](.image/banner/banner1187.png) |
| ![Preview](.image/banner/banner1188.png) | ![Components](.image/banner/banner1189.png) | ![Data Source](.image/banner/banner1190.png) |
| ![Publish](.image/banner/banner1191.png) | ![Runtime](.image/banner/banner1192.png) | ![Template](.image/banner/banner1193.png) |
| ![Assets](.image/banner/banner1194.png) | ![Big Screen](.image/banner/banner1195.png) | ![Display](.image/banner/banner1196.png) |

#### 📹 Video Surveillance

| | | |
|:---:|:---:|:---:|
| ![Video Surveillance](.image/banner/banner1225.png) | ![Video Surveillance](.image/banner/banner1226.png) | ![Video Surveillance](.image/banner/banner1227.png) |
| ![Video Surveillance](.image/banner/banner1228.png) | ![Video Surveillance](.image/banner/banner1229.png) | ![Video Surveillance](.image/banner/banner1230.png) |
| ![Video Surveillance](.image/banner/banner1219.png) | ![Video Surveillance](.image/banner/banner1220.png) | ![Video Surveillance](.image/banner/banner1221.png) |
| ![Video Surveillance](.image/banner/banner1222.png) | ![Video Surveillance](.image/banner/banner1223.png) | ![Video Surveillance](.image/banner/banner1224.png) |
| ![Region Detection](.image/banner/banner1213.png) | ![Region Detection](.image/banner/banner1214.png) | ![Region Detection](.image/banner/banner1218.png) |
| ![Post-processing Rule Chain](.image/banner/banner1216.png) | ![Post-processing Rule Chain](.image/banner/banner1217.png) | ![Post-processing Rule Chain](.image/banner/banner1215.png) |
| ![Live Stream](.image/banner/banner1145.jpg) | ![Preview](.image/banner/banner1146.jpg) | ![Camera](.image/banner/banner1051.jpg) |
| ![List](.image/banner/banner1053.jpg) | ![Stream Push](.image/banner/banner1083.jpg) | ![Relay](.image/banner/banner1084.jpg) |
| ![Storage](.image/banner/banner1121.png) | ![Snapshot](.image/banner/banner1122.png) | ![Recording](.image/banner/banner1123.png) |
| ![Configuration](.image/banner/banner1124.png) | ![Capacity](.image/banner/banner1125.png) | ![Playback](.image/banner/banner1126.png) |
| ![Snapshot](.image/banner/banner1117.png) | ![Files](.image/banner/banner1118.png) | ![Policy](.image/banner/banner1119.png) |
| ![Quota](.image/banner/banner1120.png) | ![Gallery](.image/banner/banner1057.jpg) | ![Archive](.image/banner/banner1058.jpg) |
| ![Monitoring](.image/banner/banner1068.jpg) | ![Statistics](.image/banner/banner1069.jpg) | ![Map](.image/banner/banner1113.png) |
| ![Location](.image/banner/banner1114.png) | ![Distribution](.image/banner/banner1115.png) | ![Points](.image/banner/banner1116.png) |
| ![Live View](.image/banner/banner1026.jpg) | ![Multi-Stream](.image/banner/banner1028.jpg) | ![Stream Push](.image/banner/banner1103.png) |
| ![Preview](.image/banner/banner1104.png) | ![Access](.image/banner/banner1105.png) | ![NVR](.image/banner/banner1106.png) |
| ![Live View](.image/banner/banner1183.jpg) | ![Map](.image/banner/banner1184.jpg) |  |

#### 🤖 AI Assistant

| | | |
|:---:|:---:|:---:|
| ![IDEA Login](.image/banner/banner1203.png) | ![IDEA Workspace](.image/banner/banner1204.png) | ![IDEA Development](.image/banner/banner1205.png) |
| ![AI Assistant Chat](.image/banner/banner1210.png) | ![AI Assistant Analysis](.image/banner/banner1211.png) | ![AI Assistant Collaboration](.image/banner/banner1212.png) |

#### 🧠 AI Models

| | | |
|:---:|:---:|:---:|
| ![Multi-cluster Sync](.image/banner/banner1200.png) | ![NFS Cluster Topology](.image/banner/banner1198.png) | ![NFS Cluster Management](.image/banner/banner1197.png) |
| ![Node Management](.image/banner/banner1199.png) | ![NFS File Directory](.image/banner/banner1201.png) | ![NFS Directory Browser](.image/banner/banner1202.png) |
| ![Qwen](.image/banner/banner1093.jpg) | ![Vision Model](.image/banner/banner1094.jpg) | ![List](.image/banner/banner1099.png) |
| ![Configuration](.image/banner/banner1100.png) | ![Details](.image/banner/banner1101.png) | ![Invocation](.image/banner/banner1102.png) |
| ![Training](.image/banner/banner1019.jpg) | ![Task](.image/banner/banner1020.jpg) | ![List](.image/banner/banner1023.jpg) |
| ![Progress](.image/banner/banner1024.jpg) | ![Parameters](.image/banner/banner1017.jpg) | ![Evaluation](.image/banner/banner1018.jpg) |
| ![Details](.image/banner/banner1021.png) | ![Logs](.image/banner/banner1022.jpg) | ![Management](.image/banner/banner1097.png) |
| ![Repository](.image/banner/banner1098.png) | ![Version](.image/banner/banner1039.jpg) | ![Assets](.image/banner/banner1061.jpg) |
| ![Inference](.image/banner/banner1040.jpg) | ![Configuration](.image/banner/banner1042.jpg) | ![Results](.image/banner/banner1043.jpg) |
| ![Online](.image/banner/banner1044.jpg) | ![Batch](.image/banner/banner1047.jpg) | ![Monitoring](.image/banner/banner1048.jpg) |
| ![Service](.image/banner/banner1045.jpg) | ![Deployment](.image/banner/banner1046.jpg) | ![Cluster](.image/banner/banner1049.jpg) |
| ![Invocation](.image/banner/banner1050.jpg) | ![Weights](.image/banner/banner1111.png) | ![Download](.image/banner/banner1112.png) |
| ![Pose](.image/banner/banner1147.jpg) | ![Recognition](.image/banner/banner1148.jpg) | ![Task](.image/banner/banner1085.jpg) |
| ![Configuration](.image/banner/banner1086.jpg) | ![Details](.image/banner/banner1087.jpg) | ![Runtime](.image/banner/banner1088.jpg) |
| ![Region](.image/banner/banner1079.jpg) | ![Detection Box](.image/banner/banner1080.jpg) | ![Defense](.image/banner/banner1081.jpg) |
| ![Preview](.image/banner/banner1082.jpg) | ![Algorithm](.image/banner/banner1062.jpg) | ![Create](.image/banner/banner1063.png) |
| ![Frame](.image/banner/banner1064.jpg) | ![Analysis](.image/banner/banner1065.jpg) | ![Results](.image/banner/banner1066.jpg) |
| ![Playback](.image/banner/banner1067.jpg) | ![Live View](.image/banner/banner1052.jpg) | ![Intelligent](.image/banner/banner1054.jpg) |

#### 📋 Alert Work Orders

| | | |
|:---:|:---:|:---:|
| ![Flow Design](.image/banner/banner1231.png) | ![Node Configuration](.image/banner/banner1232.png) | ![Select Approver](.image/banner/banner1233.png) |
| ![Condition Branches](.image/banner/banner1234.png) | ![Condition Rules](.image/banner/banner1235.png) | ![Parallel Branches](.image/banner/banner1236.png) |

#### 📦 Datasets

| | | |
|:---:|:---:|:---:|
| ![Management](.image/banner/banner1015.png) | ![List](.image/banner/banner1010.jpg) | ![Annotation](.image/banner/banner1027.png) |
| ![Task](.image/banner/banner1016.jpg) | ![Tools](.image/banner/banner1059.jpg) | ![Preview](.image/banner/banner1060.jpg) |
| ![Details](.image/banner/banner1107.png) | ![Import](.image/banner/banner1108.png) | ![Project](.image/banner/banner1109.png) |
| ![Review](.image/banner/banner1110.png) | ![Create](.image/banner/banner1007.jpg) | ![Samples](.image/banner/banner1008.jpg) |

#### 🔌 IoT

| | | |
|:---:|:---:|:---:|
| ![Thing Model](.image/banner/banner1149.jpg) | ![Definition](.image/banner/banner1150.jpg) | ![Product](.image/banner/banner1151.jpg) |
| ![Details](.image/banner/banner1152.jpg) | ![Device](.image/banner/banner1153.jpg) | ![Details](.image/banner/banner1154.jpg) |
| ![Status](.image/banner/banner1155.jpg) | ![Properties](.image/banner/banner1156.jpg) | ![Service](.image/banner/banner1157.jpg) |
| ![Events](.image/banner/banner1158.jpg) | ![Shadow](.image/banner/banner1159.jpg) | ![Topology](.image/banner/banner1160.jpg) |
| ![Sub-Devices](.image/banner/banner1161.jpg) | ![Groups](.image/banner/banner1162.jpg) | ![Control](.image/banner/banner1163.jpg) |
| ![Telemetry](.image/banner/banner1164.jpg) | ![History](.image/banner/banner1165.jpg) | ![Protocol](.image/banner/banner1166.jpg) |
| ![Connection](.image/banner/banner1167.jpg) | ![Authentication](.image/banner/banner1168.jpg) | ![Debug](.image/banner/banner1169.jpg) |
| ![Functions](.image/banner/banner1170.jpg) | ![Read/Write](.image/banner/banner1171.jpg) | ![Service](.image/banner/banner1172.jpg) |
| ![Subscribe](.image/banner/banner1173.jpg) | ![Logs](.image/banner/banner1174.jpg) | ![Online](.image/banner/banner1175.jpg) |
| ![Statistics](.image/banner/banner1176.jpg) | ![Overview](.image/banner/banner1177.jpg) | ![Dashboard](.image/banner/banner1178.jpg) |
| ![Product](.image/banner/banner1006.jpg) | ![Device](.image/banner/banner1009.jpg) | ![OTA](.image/banner/banner1179.jpg) |
| ![Firmware](.image/banner/banner1180.jpg) | ![Task](.image/banner/banner1181.jpg) | ![Progress](.image/banner/banner1182.jpg) |
| ![Rules](.image/banner/banner1013.jpg) | ![Orchestration](.image/banner/banner1014.png) | ![Forwarding](.image/banner/banner1206.png) |
| ![Running](.image/banner/banner1209.png) | ![Destination](.image/banner/banner1207.png) | ![Delivery](.image/banner/banner1208.png) |

#### 🖥️ Cluster

| | | |
|:---:|:---:|:---:|
| ![Overview](.image/banner/banner1127.jpg) | ![Compute](.image/banner/banner1128.jpg) | ![Node](.image/banner/banner1129.jpg) |
| ![Details](.image/banner/banner1130.jpg) | ![Monitoring](.image/banner/banner1131.jpg) | ![Scheduling](.image/banner/banner1132.jpg) |
| ![List](.image/banner/banner1133.jpg) | ![Status](.image/banner/banner1134.jpg) | ![Configuration](.image/banner/banner1135.jpg) |
| ![Allocation](.image/banner/banner1136.jpg) |  |  |

#### 🔔 Alerts

| | | |
|:---:|:---:|:---:|
| ![Events](.image/banner/banner1089.jpg) | ![Processing](.image/banner/banner1090.jpg) | ![Notification](.image/banner/banner1029.jpg) |
| ![Configuration](.image/banner/banner1030.jpg) | ![List](.image/banner/banner1072.jpg) | ![Details](.image/banner/banner1031.jpg) |
| ![Handling](.image/banner/banner1070.jpg) | ![Statistics](.image/banner/banner1071.jpg) |  |

#### ⚙️ System

| | | |
|:---:|:---:|:---:|
| ![Branding](.image/banner/banner1143.jpg) | ![Reset](.image/banner/banner1144.jpg) | ![Users](.image/banner/banner1003.png) |
| ![Permissions](.image/banner/banner1004.png) | ![Menu](.image/banner/banner1005.png) | ![Configuration](.image/banner/banner1002.png) |

#### 📱 APP

| | | |
|:---:|:---:|:---:|
| ![APP Screenshot](.image/banner/app/app_1008.jpg) | ![APP Screenshot](.image/banner/app/app_1009.jpg) | ![APP Screenshot](.image/banner/app/app_1010.jpg) |
| ![APP Screenshot](.image/banner/app/app_1011.jpg) | ![APP Screenshot](.image/banner/app/app_1012.jpg) | ![APP Screenshot](.image/banner/app/app_1013.jpg) |
| ![APP Screenshot](.image/banner/app/app_2023.png) | ![APP Screenshot](.image/banner/app/app_2024.png) | ![APP Screenshot](.image/banner/app/app_2025.png) |
| ![APP Screenshot](.image/banner/app/app_2026.png) | ![APP Screenshot](.image/banner/app/app_2027.png) | ![APP Screenshot](.image/banner/app/app_2028.png) |
| ![APP Screenshot](.image/banner/app/app_1014.jpg) | ![APP Screenshot](.image/banner/app/app_1015.jpg) | ![APP Screenshot](.image/banner/app/app_1016.jpg) |
| ![APP Screenshot](.image/banner/app/app_1017.jpg) | ![APP Screenshot](.image/banner/app/app_1018.jpg) | ![APP Screenshot](.image/banner/app/app_1019.jpg) |
| ![APP Screenshot](.image/banner/app/app_1020.jpg) | ![APP Screenshot](.image/banner/app/app_1021.jpg) | ![APP Screenshot](.image/banner/app/app_1022.jpg) |
| ![APP Screenshot](.image/banner/app/app_2029.jpg) | ![APP Screenshot](.image/banner/app/app_2030.jpg) | ![APP Screenshot](.image/banner/app/app_2031.jpg) |

## 📞 Contact Information

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Please follow our official account below first, then reach us via the technical exchange group or WeChat.
</p>

## 👥 Official Account

<div>
  <img src=".image/公众号.jpg" alt="Official Account" width="30%">
</div>

## 💬 Technical Exchange Group

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
After following the official account, scan the QR code below with WeChat to join the EasyAIoT technical exchange group.
</p>

<div>
  <img src=".image/交流群3群.jpg" alt="EasyAIoT Technical Exchange Group" width="30%">
</div>

## 💬 WeChat Contact

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
After following the official account, scan the QR code below to add us as a WeChat friend for one-on-one communication.
</p>

<div>
  <img src=".image/微信联系方式.jpg" alt="WeChat Contact" width="200">
</div>

## 🪐 Knowledge Planet:

<p>
  <img src=".image/知识星球.jpg" alt="Knowledge Planet" width="30%">
</p>

## 💰 Sponsorship

<div>
    <img src=".image/微信支付.jpg" alt="WeChat Pay" width="30%" height="30%">
    <img src=".image/支付宝支付.jpg" alt="Alipay" width="30%" height="10%">
</div>

## 🤝 Contributing Guide

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
We welcome all forms of contributions! Whether you are a code developer, documentation writer, or issue reporter, your contribution will help make EasyAIoT better. Here are the main ways to contribute:
</p>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">

<div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">💻 Code Contribution</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Fork the project to your GitHub/Gitee account</li>
  <li>Create a feature branch (git checkout -b feature/AmazingFeature)</li>
  <li>Commit your changes (git commit -m 'Add some AmazingFeature')</li>
  <li>Push to the branch (git push origin feature/AmazingFeature)</li>
  <li>Open a Pull Request</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">📚 Documentation Contribution</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Improve existing documentation content</li>
  <li>Add usage examples and best practices</li>
  <li>Provide multilingual translations</li>
  <li>Fix documentation errors</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🌟 Other Contribution Methods</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Report and fix bugs</li>
  <li>Suggest feature improvements</li>
  <li>Participate in community discussions and help other developers</li>
  <li>Share usage experiences and case studies</li>
</ul>
</div>

</div>

## 🌟 Major Contributors

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
The following are outstanding contributors who have made major contributions to the EasyAIoT project. Their contributions have played a key role in promoting the project's development. We express our most sincere gratitude!
</p>

<table style="width: 100%; table-layout: fixed; border-collapse: collapse; margin: 20px 0; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0; width: 32%; min-width: 9rem;">Contributor</th>
<th style="padding: 15px; text-align: left; font-weight: 600; border: 1px solid #e0e0e0;">Contribution</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>℡夏别</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Contributed Windows deployment documentation for the EasyAIoT project, providing a complete deployment guide for Windows platform users, greatly reducing the deployment difficulty in Windows environments, and enabling more users to easily use the EasyAIoT platform.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>YiYaYiYaho</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Contributed Mac container one-click deployment script for the EasyAIoT project, providing an automated deployment solution for Mac platform users, significantly simplifying the deployment process in Mac environments, and improving the deployment experience for developers and users.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>山寒</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Contributed Linux container deployment script for the EasyAIoT project, providing a containerized deployment solution for Linux platform users, achieving fast and reliable container deployment, and providing important guarantees for stable operation in production environments.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>玖零。</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Contributed Linux container deployment script for the EasyAIoT project, further improving the containerized deployment solution for Linux platforms, providing more options for users of different Linux distributions, and promoting the project's cross-platform deployment capabilities.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>爱吃小柚子</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">To advance EasyAIoT toward training that actually runs, stays stable, and stays easy to operate, systematically delivered multi-GPU training, checkpoint resume, and node-side deployment so on-site compute can be fully used and training jobs stay under control: servers can auto-detect and use all GPUs, and users can pick one or more cards on the training page instead of being stuck with a single visible GPU; common dataset formats and directory layouts are supported, large local datasets can be uploaded, and original data is kept after failed runs for quick retries—greatly cutting the cost of data prep and rework; training progress is visible, jobs can be stopped and resumed, avoiding lost results after interruptions or “stop” clicks that leave processes spinning in the background, with clear fallback and feedback when local or remote scheduling fails; also improved frontend GPU selection, resume, and stop-state display, and fixed false “publish failed” results, custom preview images being overwritten, model lookup by name/version not working, and dataset sync timeouts or conflicts—making the train–publish–use loop smoother and more reliable. Previously also led end-to-end GB28181 and AI workflow integration testing and dedicated image-clarity evaluation, providing a strong basis for reliable national-standard access and better viewing experience.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>Dark</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Contributed end-to-end integration of GB28181 for EasyAIoT in national-standard video surveillance, delivering video playback and PTZ (pan-tilt) control so that device access supports practical live preview and remote camera steering.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>machh</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Contributed to the EasyAIoT-Edge project by validating camera onboarding and AI capabilities end to end, and wiring these features into a coherent edge-side workflow.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>遗忘的星空</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">Contributed to EasyAIoT's direct device onboarding by delivering a multi-vendor IP camera asset inventory and subnet scanner, supporting batch discovery and identification of Hikvision IPCs, NVRs, and related devices; improved batch search and one-click registration for directly connected devices across same-subnet and cross-subnet scenarios. Device access is implemented via native protocols, bypassing the Hikvision SDK and reducing reliance on the Hikvision platform—laying the groundwork for open, controllable large-scale camera onboarding.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>阿龙</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">To advance EasyAIoT in map visualization and spatial intelligence, independently contributed the complete implementation of Tianditu spatial visualization capabilities, covering national Tianditu basemap integration, camera and alarm device placement, map distribution views, location search and batch coordinate import, automatic alarm event mapping, person/vehicle trajectory tracking, and mobile device track playback—bringing the platform's "Tianditu spatial visualization and map-based analysis" capability from design to production-ready, usable form.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>雨落流殇</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">To advance EasyAIoT in ultra-large-scale streaming media delivery, contributed deployment and scheduling approaches for heterogeneous streaming media server clusters, proposing scalable solutions including multi-node pool coordination, decoupling of streaming from the business layer, and node registration scheduling—laying an important architectural foundation for the platform to support concurrent access of tens of thousands of camera streams with stable distribution and elastic scaling.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>常康</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">To advance EasyAIoT in intelligent transportation and vehicle management, independently contributed the license plate recognition algorithm and complete code implementation, covering plate detection, plate number and color recognition, double-layer plate merging and tilt/perspective correction, plate library management and multi-library sequential matching, one-click integration with algorithm tasks, and asynchronous matching—supporting mainstream plate types including blue, yellow, green, white, and new energy vehicle plates—bringing the platform's "license plate recognition and plate library management" capability from planning to production-ready, closed-loop application.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>Li</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">To advance EasyAIoT in youth developer community building and collaborative ecosystem development, demonstrated outstanding organizational leadership and rallying power by leading fellow students across campus to actively co-build the project, bringing together young talent and collective momentum to inject a continuous, enduring stream of growth energy into EasyAIoT; also made pivotal, irreplaceable contributions in project outreach, hands-on implementation, and cultivating the next generation of contributors.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>陈家林</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">To advance EasyAIoT in IoT device interoperability, industrial protocol access, and air–ground video fusion, delivered a closed loop for device commands and status so the platform can truly “send commands down, see status, and stay in control”; systematically contributed Modbus-TCP, Modbus-RTU, and OPC UA industrial protocol access—unified acquisition of Ethernet- and serial-side industrial devices and OPC UA nodes, with measurement read/write and thing-model mapping—so meters, sensors, PLCs, controllers and other industrial equipment data can be aggregated, monitored and linked on the platform, completing the key puzzle of “seeing the scene and hearing the devices”; also contributed DJI FlightHub dock and drone video integration, bringing aerial inspection into the unified video and alarm system, significantly expanding value in industrial data acquisition, production-line intelligence, wide-area patrol, emergency survey, and sky–ground collaborative sensing.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>空空</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">To advance EasyAIoT in camera direct-connect from “discoverable” to “production-ready,” closed critical gaps in authentication, channel sync, config changes, and multi-vendor stream URLs so the platform is deliverable on real NVR / multi-vendor sites: made device login work reliably so direct-connect devices can truly “log in and stay managed”; improved the post-NVR-sync streaming model so batch-synced channels play and scale; ensured access parameters remain maintainable; built stream URL rule libraries for common domestic camera brands and opened custom brand rules so heterogeneous devices can go live in one click without manual address trials—moving direct-connect from “devices can be scanned” to “login works, sync is accurate, configs can be changed, and multi-brand streams play,” laying a solid foundation for later PTZ and zoom controls.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>狗娃</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">To advance EasyAIoT toward "IoT data displayed on screen," proactively proposed the product vision of a visualization Board (drag-and-drop dashboard) module: traditional dashboards often require hand-written SQL for every screen and component, slowing delivery, making every change ripple across the stack, and leaving business users unable to self-serve. The Board approach puts charts, metrics, and layout on a drag-and-drop canvas and binds component variables directly to platform IoT thing-model metrics—real-time and historical values pulled from devices in one step, without bespoke queries per dashboard; campus situational awareness, production-line KPIs, equipment operations, and similar screens upgrade from "developers write SQL to get a screen" to "pick metrics, drag components, screen done," significantly shortening visualization delivery and turning IoT "data in the back office" into an operational "screens in the front office" capability. Previously also contributed sensor float data prediction, running-status property threshold configuration, threshold alarms with rule linkage, and one-screen running-status views for central-device associated sub-devices—closing the device operations loop of "predict—bound—alert—rule—one-screen control" so the device side can "see the numbers, govern the bounds, raise the alerts, and grasp the whole picture."</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>大老刘</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">To advance EasyAIoT in external communication and solution storytelling, contributed the illustrated introduction material <em>AI Video Surveillance Analytics Platform</em>, systematically presenting the platform's capability landscape and deployment value in AI video surveillance scenarios so that users, integrators, and partners can quickly grasp the positioning and key highlights—significantly improving outreach and business communication efficiency.</td>
</tr>
<tr style="background-color: #f8f9fa;">
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>刘兆中ᯤ⁵ᴳ</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">To advance EasyAIoT toward one-click macOS deployment, pioneered part of the Mac one-click deployment scripts—largely opening the main path of image pull, container orchestration, and environment precondition checks so that follow-on work only needed to close the “last mile.” His exploration clarified key nodes and risk points on the Mac deployment chain, substantially shortening the path to engineering completion, and remains an indispensable foundational contribution in taking macOS deployment from zero to usable.</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; font-weight: 600; color: #2c3e50; width: 32%; min-width: 9rem;"><nobr>添旺</nobr></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; color: #444; line-height: 1.8;">To advance EasyAIoT in cloud-edge collaborative video ingestion and AI analytics, independently delivered several pivotal capabilities that confront the core pain points of real-world edge delivery—“can't get cameras in, can't schedule right, doesn't truly run, can't look back”: pioneered edge camera ingress with algorithm-node affinity—IPC/NVR devices can designate an online edge node as their “ingress node,” so discovery, subnet scanning, ONVIF probing, and NVR channel enumeration all run locally on that node while source streams are pushed back to the control-plane media service for unified distribution and playback; cameras in branch sites or cross-segment/private networks no longer need direct reachability to the central platform to be onboarded and streamed, and algorithm tasks are automatically pinned to their cameras' ingress node so workloads never land on nodes that cannot reach the source stream. Diagnosed and fixed the critical defect where multiple algorithm tasks or multi-model pipelines on one camera left only a single channel effective—isolating inference chains with task-scoped stream identities, reusing one shared decode across concurrent tasks via a dedicated camera-source service, and propagating task identity through alerts and runtime status end to end—one camera can now stably run multiple algorithm tasks and multi-model detection (face + vehicle in the same frame) in parallel, guarded by regression tests over the long term. Also contributed tiered storage for edge recordings with unified event replay—recordings retained in tiers at the edge while alert events and video evidence stay searchable and replayable through one cloud-edge unified entry, closing the evidence loop from “event happened” to “proof in hand.” Together these markedly strengthen the platform's delivery certainty in complex real-world network environments and the trustworthiness of its AI analytics results.</td>
</tr>
</tbody>
</table>

<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>Special Thanks</strong>: The above contributors have advanced EasyAIoT in cross-platform deployment documentation and scripts, foundational macOS one-click deployment scripting and path exploration, national-standard video capability delivery and AI integration verification, multi-GPU training and checkpoint resume, multi-vendor camera direct discovery and batch onboarding, Tianditu spatial visualization, heterogeneous streaming media cluster deployment and scheduling, license plate recognition algorithm and complete implementation, EasyAIoT-Edge end-to-end edge-side integration, campus developer community organization and youth collaborative ecosystem building, IoT device uplink/downlink closed loop and DJI FlightHub aerial view integration, Modbus-TCP / Modbus-RTU / OPC UA industrial protocol access, the production-ready closed loop of camera direct-connect from discovery through login/sync/config/multi-brand streaming, the drag-and-drop Board vision with IoT metric real-time/historical value integration, sensor float data prediction with threshold alarm rules plus one-screen running-status views for central-device associated sub-devices, and illustrated introduction materials for the AI video surveillance analytics platform, edge camera ingress with algorithm-node affinity, isolation of multi-task/multi-model inference on the same camera, and tiered edge recording storage with unified event replay. Their professionalism and selfless dedication are worthy of our learning and respect. Once again, we express our most sincere gratitude to these outstanding contributors! 🙏
</p>

## 💝 Open Source Guardians

Sustaining an open-source project takes more than code and documentation. During the days when EasyAIoT's compute resources were most strained and the project was on the brink of stalling, the following individuals stepped forward with tangible financial support that gave the project the momentum it needed to keep going. You may never have submitted a single line of code, yet every act of trust and support helped EasyAIoT cross its hardest hurdles and continue to evolve. As long as people use it and stand behind it, the open-source ecosystem deserves to go further; what EasyAIoT has achieved today would not have been possible without these companions who reached out at critical moments. We extend our deepest respect and gratitude to every friend who lent a hand. The following rankings are in no particular order:

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

## 🏆 Best Practitioners

They are the pioneers who push EasyAIoT from "usable" to "easy to use and use well" — the following individuals have completed EasyAIoT project deployment or business scenario implementation. Their exploration and achievements set replicable and referable benchmarks for the community. We extend our highest respect and heartfelt congratulations to these outstanding practitioners! The following rankings are in no particular order:

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

## 🙏 Acknowledgements

Thanks to the following contributors for code, feedback, donations, and support (in no particular order):
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
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/ccqingshan" target="_blank"><img src="./.image/sponsor/青衫.jpg" width="80px;" alt="青衫"/><br /><sub><b>青衫</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/jiangchunJava" target="_blank"><img src="./.image/sponsor/Fae.jpg" width="80px;" alt="Fae"/><br /><sub><b>Fae</b></sub></a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/huang-xiangtai" target="_blank"><img src="./.image/sponsor/憨憨.jpg" width="80px;" alt="憨憨"/><br /><sub><b>憨憨</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/gu-beichen-starlight" target="_blank"><img src="./.image/sponsor/文艺小青年.jpg" width="80px;" alt="文艺小青年"/><br /><sub><b>文艺小青年</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://github.com/zhangnanchao" target="_blank"><img src="./.image/sponsor/lion.jpg" width="80px;" alt="lion"/><br /><sub><b>lion</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/yupccc" target="_blank"><img src="./.image/sponsor/汪汪队立大功.jpg" width="80px;" alt="汪汪队立大功"/><br /><sub><b>汪汪队立大功</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/wcjjjjjjj" target="_blank"><img src="./.image/sponsor/wcj.jpg" width="80px;" alt="wcj"/><br /><sub><b>wcj</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/hufanglei" target="_blank"><img src="./.image/sponsor/🌹怒放de生命😋.jpg" width="80px;" alt="怒放de生命"/><br /><sub><b>怒放de生命</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/juyunsuan" target="_blank"><img src="./.image/sponsor/蓝速传媒.jpg" width="80px;" alt="蓝速传媒"/><br /><sub><b>蓝速传媒</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/achieve275" target="_blank"><img src="./.image/sponsor/Achieve_Xu.jpg" width="80px;" alt="Achieve_Xu"/><br /><sub><b>Achieve_Xu</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="https://gitee.com/nicholasld" target="_blank"><img src="./.image/sponsor/NicholasLD.jpg" width="80px;" alt="NicholasLD"/><br /><sub><b>NicholasLD</b></sub></a></td>
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
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/常康.jpg" width="80px;" alt="常康"/><br /><sub><b>常康</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/嘎嗝.jpg" width="80px;" alt="嘎嗝"/><br /><sub><b>嘎嗝</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/曹.jpg" width="80px;" alt="曹"/><br /><sub><b>曹</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/滔滔.jpg" width="80px;" alt="滔滔"/><br /><sub><b>滔滔</b></sub></a></td>
        <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/sponsor/狗娃.jpg" width="80px;" alt="狗娃"/><br /><sub><b>狗娃</b></sub></a></td>
    </tr>
  </tbody>
</table>

## 💡 Expectations

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
We welcome suggestions for improvement to help refine EasyAIoT.
</p>

## 📄 Copyright

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Soaring Xiongkulu / easyaiot is licensed under the <a href="https://gitee.com/soaring-xiongkulu/easyaiot/blob/main/LICENSE" style="color: #3498db; text-decoration: none; font-weight: 600;">MIT LICENSE</a>. We are committed to promoting the popularization and development of AI technology, enabling more people to freely use and benefit from this technology.
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
<strong>Usage License</strong>: Individuals and enterprises can use it 100% free of charge, without the need to retain author or Copyright information. We believe the value of technology lies in its widespread use and continuous innovation, rather than being bound by copyright. We hope you can freely use, modify, and distribute this project, making AI technology truly benefit everyone.
</p>
