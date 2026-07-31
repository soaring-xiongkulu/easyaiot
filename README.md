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

## 📖 Project Overview

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
<strong>EasyAIoT</strong> (Easy AI Internet of Things) is a <strong>cloud-edge-device integrated intelligent algorithm application platform</strong> dedicated to deeply fusing artificial intelligence with the Internet of Things—enabling cameras, sensors, and edge compute to work together on site. From device onboarding and data collection to real-time visual analysis, intelligent assessment, and alert orchestration, the entire chain runs on a single software stack.
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Many smart IoT projects hit the same wall at deployment: video systems, device platforms, and algorithm services live in silos—integration is costly, operations are fragmented, and scaling is painful. <strong>EasyAIoT resolves this with one platform</strong>—the same software deploys on a 4 GB edge box for single-point intelligence, on AI all-in-one cameras for floor-level coverage, or inside an enterprise full-stack appliance that packs IoT management, massive video access, and AI analysis into one box—no multiple versions to maintain, no repeated integration across heterogeneous systems.
</p>

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
The platform comprises eleven core modules—<strong>WEB, APP, DEVICE, NODE, VIDEO, AI, TASK, EDGE, VISUALIZE, TRANSFORM, and PANEL</strong>—with <strong>COMPILE</strong> handling multi-platform packaging and delivery. On the capability side, the platform covers GB28181 / ONVIF multi-protocol camera access, <strong>DJI dock and drone aerial view access</strong>, real-time and snapshot algorithm tasks, YOLO object detection and SAM zero-shot auto-annotation, face/plate recognition, orchestrable business post-processing, federated compute cluster scheduling, and <strong>Infinite Federated Edge Cluster mode</strong> (ordinary development boards ready out of the box, on-site intelligence for local decisions, alerts and evidence automatically aggregated to the cloud, compute scaling with business as needed), plus MQTT / TCP / HTTP / Modbus-TCP / Modbus-RTU / OPC UA IoT device lifecycle management, and <strong>visualization dashboards and Web SCADA configuration</strong>, so device data can be displayed as command-center situational awareness and mapped back to process screens; plus the new <strong>TRANSFORM multidirectional data-flow engine</strong>, which delivers platform-side business events to external systems such as MES / ERP / CRM / WMS by contract—multi-party integration that is configurable, traceable, and reusable; and the companion <strong>PANEL delivery & watch entry</strong>, so appliances can be installed and accepted on arrival day, and watch/troubleshooting no longer wait on developers running remote commands every time. On the experience side, the Web console and mobile App / mini-program are capability-aligned, so command centers and field inspections share the same business logic—handle incidents anytime, anywhere.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>In one sentence:</strong> EasyAIoT = AI + IoT—interconnect everything while enabling intelligent vision and intelligent control for everything.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
📄 For a more complete illustrated introduction, see <a href=".doc/项目介绍/EasyAIoT项目介绍 V2.0.pptx" style="color: #3498db; text-decoration: none; font-weight: 600;">EasyAIoT Project Introduction V2.0 (PPT)</a>.
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
  <li><strong>Shorter acceptance cycles</strong>: On arrival pick mini / standard / full, install, and see progress and results on the spot—fewer “stuck halfway, unsure where” cases from incomplete commands or skipped steps; PoC and production delivery clear acceptance faster</li>
  <li><strong>Lower on-site and remote cost</strong>: Whether containers are running, resources are tight, and where logs stall is obvious at a glance—restart, clean cache, and pull images without first hunting docs or waiting for developer support; watch staff can self-serve common faults</li>
  <li><strong>One playbook across projects</strong>: The same install and ops entry reuses across appliances and rooms—delivery, watch, and handoff share one standard, avoiding “each site has its own oral tradition”</li>
</ul>

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 12px 0 8px 0;">
📦 <strong>Installer download</strong>: Packages for Ubuntu / Debian, CentOS / RHEL, Windows, macOS, and ARM / Kylin targets are on <a href="https://gitee.com/volara/easyaiot/releases" style="color: #3498db; text-decoration: none; font-weight: 600;">Gitee Releases</a>.
</p>

| | | |
|:---:|:---:|:---:|
| ![Overview](.image/banner/panel/panel_1000.png) | ![Containers](.image/banner/panel/panel_1001.png) | ![Logs](.image/banner/panel/panel_1002.png) |
| ![Deploy](.image/banner/panel/panel_1003.png) | ![Images](.image/banner/panel/panel_1004.png) | ![Pull](.image/banner/panel/panel_1005.png) |
| ![Diagnose](.image/banner/panel/panel_1006.png) | ![Maintain](.image/banner/panel/panel_1007.png) | ![Topology](.image/banner/panel/panel_1008.png) |

### 🎯 Three Hardware Tiers, One Platform

<p style="font-size: 15px; line-height: 1.8; color: #333; margin: 15px 0;">
Many intelligent IoT projects stall at deployment: <strong>full features won't fit on small machines; to make them fit, you cut capabilities, split versions, and maintain multiple deployment packages.</strong> EasyAIoT resolves this with one platform—<strong>edge boxes for point intelligence, AI all-in-one cameras for on-wall analysis, AIoT full-stack all-in-ones for the complete stack in one box</strong>. Pick the tier that matches your field hardware; the same software runs from single-site pilots through floor coverage to full-stack delivery—no split versions.
</p>

| Tier | Typical hardware (examples) | Recommended RAM | What you can do | Verified |
| :-- | :-- | :--: | :-- | :--: |
| **mini** Edge Lite | <strong>Edge box</strong> (4 GB industrial PC, store security all-in-one, site gateway) | ≥ 4 GB | <strong>Intelligence at one point</strong>: camera access, real-time analysis, smart alerts, model inference—visual AI at lowest cost | ~2 GB used, ample headroom |
| **standard** Standard | <strong>AI all-in-one camera</strong> (smart camera terminal, AI surveillance camera with compute, multi-sensor AI analyzer) | ≥ 16 GB | <strong>Each camera is a smart node</strong>: multiple cameras on the wall cover a floor/campus; devices, rules, and compute orchestrated together | ~10 GB, stable with headroom |
| **full** Full (default) | <strong>AIoT full-stack all-in-one</strong> (enterprise full-stack control all-in-one, industry IoT full-stack host, cloud-edge-device smart platform all-in-one) | ≥ 20 GB | <strong>IoT + video + AI in one box</strong>: device management, massive access, intelligent analysis, command and judgment unified—full capabilities long-term | ~14 GB, full features with headroom |

<p style="font-size: 14px; line-height: 1.8; color: #444; margin: 16px 0 8px 0;">
<strong>Install tier selection and resource compliance (verified):</strong>
</p>

| | | |
|:---:|:---:|:---:|
| ![Edge box mini](.image/deploy-profile-mini.png) | ![AI all-in-one camera standard](.image/deploy-profile-standard.png) | ![Full-stack all-in-one full](.image/deploy-profile-full.png) |

#### 🧠 AI Capabilities

<ul style="font-size: 14px; line-height: 1.8; color: #444; margin: 10px 0;">
  <li><strong>Custom Platform Name &amp; Logo Across All Touchpoints</strong>: After deploying EasyAIoT on site, users should see <em>their</em> platform—not a generic product name. The monitoring dashboard includes a visual "Platform Branding" panel where administrators can rebrand in the UI: update the admin console name and logo (synced to the sidebar and browser tab); set an independent command-center title on the big screen; and customize the login page name, logo, form title, plus light/dark background images—all three touchpoints stay visually consistent, take effect immediately, and can be saved or reset with one click.
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>For system integrators and solution providers</strong>: Eliminates front-end reskinning, custom development, and release cycles; switch branding quickly between PoC demos and production delivery, reuse one codebase across multiple customers, shorten payment cycles, and improve solution reuse</li>
      <li><strong>For government, campus, hospital, and other end users</strong>: Login page, command dashboard, and daily admin console all display their organization's name and identity—stronger ownership and credibility for leadership visits and internal rollout, meeting branding requirements for public-sector and large-enterprise IT projects</li>
      <li><strong>For private-deployment and operations teams</strong>: Configure on site the same day for acceptance—no waiting on development schedules; one-click restore after multi-customer demos or pilot phases, lowering switching and redeployment costs</li>
    </ul>
  </li>
  <li><strong>YOLO26 Next-Generation Object Detection</strong>: Built-in next-generation object detection, ready out of the box for real-time feed analysis and snapshot recognition. On the same hardware, connect more camera streams with faster response and fewer false alarms. Supports the full loop from data collection, annotation, and training to deployment and inference—helping users iteratively build custom detection models at lower cost and quickly cover common security and industrial scenarios such as hard hat compliance, unauthorized entry, and fire hazards, making "see accurately, compute fast, scale easily" the default capability</li>
  <li><strong>YOLO26 Human Pose Analysis</strong>: Builds on object detection with human keypoint and skeleton pose analysis, ready out of the box. Supports three input modes—images, videos, and real-time camera streams. Image mode can synchronously output skeleton annotations and person counts; video mode supports progress tracking and result download; camera mode can connect to RTSP/RTMP live streams and overlay pose recognition results on relayed output for remote monitoring and behavior analysis. The model inference page provides one-click switching between "Pose Analysis" and "Object Detection", suitable for construction site compliance, fitness form assessment, crowd gathering awareness, and other scenarios that require understanding human structure and motion—moving the platform from "boxing targets" to "understanding poses"</li>
  <li><strong>Multi-Protocol Camera Access Support</strong>: Comprehensive support for GB28181 and ONVIF, two mainstream video surveillance protocols, enabling standardized device access and management. GB28181, as China's national standard, perfectly adapts to mainstream domestic surveillance equipment; ONVIF, as an international universal standard, is widely compatible with global mainstream camera brands. Through dual-protocol support, the platform seamlessly integrates with existing surveillance systems, achieving plug-and-play device access, automatic discovery, and unified management, significantly reducing device access barriers, enhancing system compatibility and scalability, and providing a solid technical foundation for large-scale camera deployment. In addition, NVR batch scan, registration, and unified management across same-segment and cross-segment networks are supported, covering mainstream brands including Hikvision, Dahua, Huawei, Ezviz, and Xiaomi, with native-protocol subnet discovery, one-click registration, and batch channel import, further reducing the cost of large-scale surveillance device onboarding and operations</li>
  <li><strong>DJI dock / drone aerial view access</strong>: Breaks fixed-camera “ground-only, hard to cover wide areas” limits; brings DJI FlightHub dock and drone aerial video into the platform’s unified video and AI judgment loop. Streaming module offers “Connect DJI livestream”: supports <strong>FlightHub API start livestream</strong> and <strong>manual livestream source</strong> — API mode one-click pulls vendor livestream and auto-registers device; manual mode accepts RTSP / RTMP / HTTP-FLV / HLS sources. After connect, aerial views can share the same screen as GB28181/ONVIF fixed points. Operators can view dock/aircraft live like fixed cameras, and attach real-time AI analysis, alarm linkage and evidence retention—covering wide-area patrol, emergency survey, perimeter fill-in that fixed points cannot reach; shortens “detect—locate—respond”; upgrades security from planar deployment to sky–ground collaborative sensing.</li>
  <li><strong>Real-Time Intercom & PTZ Remote Control</strong>: Breaks through traditional surveillance's "watch-only, can't act" limitation. Operators can conduct voice broadcasting and PTZ control on the same real-time preview screen—no system switching, no on-site presence required. Remotely communicate, guide evacuations, or stop violations, compressing response from "dispatch personnel" to "speak and reach instantly." PTZ control lets cameras pan, tilt, and zoom on demand—quickly aim at incident areas and magnify details during emergencies, forming an integrated on-site response loop of "see clearly, aim precisely, speak and reach." Fully compatible with GB28181 and ONVIF devices, leveraging existing surveillance assets without additional intercom hardware or third-party software, instantly upgrading deployed cameras with remote communication and flexible dispatch capabilities, significantly reducing system silos and monitoring costs</li>
  <li><strong>Orchestrable Algorithm Post-Processing</strong>: Breaks through the "detect but can't judge" bottleneck by adding an independent business judgment layer on top of object detection, transforming visual perception results into operable, accountable, and statistically trackable business events. Supports flexible per-task definition of scenario rules such as people counting, line-crossing, dwell timeout, area loitering, and multi-condition composite alerts—quickly adapting to differentiated needs in construction site safety supervision, campus security, and traffic control without repeatedly tuning models, forging general vision capabilities into field-ready management tools. Post-processing and real-time analysis run independently and in parallel—monitoring feeds continue smooth judgment while business logic scales elastically on demand; judgment results are automatically archived and drive precise alerts, significantly reducing false positives/negatives and manual review costs. Business users focus on rule expression while the platform handles distribution, execution, and scale—truly moving from "being able to see" to "judge clearly, control effectively, and put it to use"</li>
  <li><strong>Multi-Central-Node × Multi-Worker-Node Federated Cluster</strong>: Designed for cross-region, multi-datacenter, and cloud-edge collaborative deployments, the platform adopts an "N central nodes + N worker nodes" federated architecture—central nodes provide unified orchestration while worker nodes carry compute and media execution, scaling horizontally. Each central node manages its domain worker nodes, supporting remote distribution and one-click deployment of streaming, AV transcoding, video analytics, model inference, and training capabilities; multiple central nodes can interconnect and synchronize; the cluster swimlane view intuitively presents "central—worker" topology and resource levels. Algorithm tasks, auto-labeling pipelines, and stream relay workloads are intelligently scheduled by node role and GPU capability—enabling massive stream ingestion, high-concurrency inference, and distributed training to run together in one cluster, truly delivering "onboard easily, schedule clearly, scale openly, govern completely"</li>
  <li><strong>SAM Zero-Start Auto-Labeling Orchestration Pipeline</strong>: Built for cold-start scenarios with no annotated samples and no usable detection model, the platform integrates SAM open-vocabulary segmentation to deliver a one-click, unattended labeling pipeline. Per strategy, the system automatically chains camera frame extraction, SAM text-prompt bootstrap labeling, YOLO fine-tuning once thresholds are met, production-phase YOLO high-speed inference with intelligent SAM fallback for missed detections, periodic iterative training, and automatic dataset packaging and export—closing the full "capture-annotate-train-export" loop. Supports pause/resume and elastic scheduling on local or cluster compute queues. With visual strategy configuration and run logs, users can grow a custom detection capability from zero samples and zero models, making "define categories in words, watch the model take shape" the default path for dataset building</li>
  <li><strong>Ten-Thousand-Node Elastic Compute Cluster & Horizontal Scaling Pool</strong>: Built for hyperscale AI and video workloads, the platform provides a cloud-edge-end distributed compute foundation that unifies algorithm tasks, stream relay, algorithm services, model training, and inference under one horizontal load-balancing and elastic scaling fabric. New servers join the fleet with one-click onboarding and immediately become schedulable compute units—the scheduling hub automatically dispatches tasks and balances load based on resource levels and business pressure, enabling linear scaling from hundreds to tens of thousands of camera streams and from a single machine to ten-thousand-node clusters without redeployment or manual tuning. Massive stream ingestion, high-concurrency inference, and distributed training run together in a shared compute pool—truly delivering "scale on demand, run reliably, govern with confidence"</li>
  <li><strong>Infinite Federated Edge Cluster Mode</strong>: For wide-area deployment, weak-network sites, and phased scale-out, intelligence is deployed where the business is—ordinary development boards and edge compute nodes can become on-duty units at any time. The center distributes tasks and policies uniformly; the field performs perception and judgment locally, with alerts and evidence automatically reported and aggregated back—no need to stack heavy servers and complex ops at every site. As business grows, add nodes on demand to linearly extend coverage—"add a little, gain a lot; add a stream, gain more assurance"—truly achieving compute that grows with the scenario and intelligence that spreads with the business</li>
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
  <li><strong>Large-Scale Camera Management</strong>: Supports access to hundreds of cameras, providing end-to-end services including collection, annotation, training, inference, export, analysis, alerting, recording, storage, and deployment</li>
  <li><strong>Algorithm Task Management</strong>: Supports creation and management of two types of algorithm tasks, each task can flexibly bind frame extractors and sorters to achieve precise video frame extraction and result sorting
    <ul style="margin: 5px 0; padding-left: 20px;">
      <li><strong>Real-Time Algorithm Tasks</strong>: Used for real-time video analysis, supporting RTSP/RTMP stream real-time processing with millisecond-level response capabilities, suitable for monitoring, security, and other real-time scenarios</li>
      <li><strong>Snapshot Algorithm Tasks</strong>: Used for snapshot image analysis, performing intelligent recognition and analysis on captured images, suitable for event backtracking, image retrieval, and other scenarios</li>
    </ul>
  </li>
  <li><strong>Dataset Annotation and Multi-Format Dataset Management</strong>: Provides a visual image annotation workspace supporting rectangle and polygon labeling, category management, and progress tracking; fully supports flexible import and export of mainstream dataset formats including YOLO, COCO, and ImageFolder, with cloud platform dataset integration enabling one-click import and synchronized export of cloud-hosted datasets—seamlessly connecting data collection, annotation, training, and deployment across the full pipeline</li>
  <li><strong>Multi-GPU Training, Checkpoint Resume, and Node-Side Deployment</strong>: Breaks through the training bottlenecks of “GPUs available but unused, tasks hard to control, and progress lost on interruption” by systematically connecting multi-GPU utilization, controllable task scheduling, and node-side deployment—so on-site GPUs are truly usable and training jobs are truly manageable. The platform automatically discovers and schedules all server GPUs; users can select single- or multi-GPU on the training page instead of being limited to “only one card visible.” It supports common dataset formats and directory layouts, large local dataset uploads, and keeps original data after failed runs for quick retry—greatly reducing data-prep and rework costs. Training progress is fully visible, and jobs can be stopped and resumed—avoiding lost results after interruption or “stop clicked but still spinning in the background.” Local and remote training schedulers also roll back promptly on failure with clear feedback. Front-end GPU selection, resume training, and stop-state display are improved in parallel, and issues such as false failure on model publish, custom preview images being overwritten, models not found by name/version, and dataset sync timeouts/conflicts are fixed—making the train–publish–use loop smoother and more reliable</li>
  <li><strong>Stream Forwarding</strong>: Supports direct viewing of camera real-time feeds without enabling AI analysis functionality. By creating stream forwarding tasks, multiple cameras can be batch-pushed, enabling synchronous viewing of multiple video streams to meet pure video monitoring scenario requirements</li>
  <li><strong>GPU Discovery, Load-Aware Allocation, and Multi-GPU Collaboration</strong>: The platform provides GPU resource discovery and intelligent scheduling: it detects the number of available GPUs and dynamically assigns video encode/decode and algorithm inference work across cards according to per-GPU load, running tasks in parallel where appropriate to raise multi-stream throughput and utilization while keeping the pipeline stable—coordinating frame processing and model inference in multi-GPU deployments</li>
  <li><strong>Smart Transport Selection and Resilient Stream Pull</strong>: On RTSP and similar pull paths, the system can automatically select appropriate transport modes based on scenario to balance latency and stability. When consecutive frames indicate gray screen, decode errors, or stream stall, automatic reconnect and link recovery run to limit prolonged artifacts or frozen video</li>
  <li><strong>Separate Viewing vs Algorithm Pipelines and Tiered Bitrates</strong>: Live preview and wall viewing are decoupled from algorithm analysis frame extraction in both data path and control policy. The viewing path prioritizes sharp, smooth monitoring; the algorithm path balances detection quality with compute and bandwidth, avoiding analysis and viewing competing on one channel—so operators get clear, fluid video while analysis stays scalable</li>
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
  <li><strong>Stream Forwarding</strong>: Create and stop forwarding tasks anytime; monitor cluster nodes and stream status—schedule video resources remotely</li>
  <li><strong>Algorithm Tasks</strong>: Start and stop real-time and snapshot tasks on the go; track detection results without waiting to get back to the office</li>
  <li><strong>Alert Center</strong>: Search alerts instantly; tap to view snapshots and recordings—verify and follow up while on mobile duty</li>
  <li><strong>Model Management</strong>: Deployment status at a glance; always know what's live</li>
  <li><strong>Model Inference</strong>: Upload an image on-site and get results immediately—spot checks without returning to PC</li>
  <li><strong>Model Training</strong>: Monitor training progress anytime; stop remotely when needed to avoid wasted compute</li>
  <li><strong>Personal Center</strong>: Account, tenant, and app preferences in one place—convenient across devices</li>
  <li><strong>Smooth Viewing</strong>: Live feeds and alarm recordings play smoothly on mobile—low latency, no stutter, uncompromised duty experience</li>
  <li><strong>Stay Connected</strong>: Sessions stay active with less re-login—bringing cloud-edge-device intelligent control to phones and mini programs</li>
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
We believe no single programming language excels at everything, but through the deep integration of three programming languages, EasyAIoT leverages the strengths of each to build a powerful technical ecosystem.
</p>

<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 15px 0;">
Java excels at building stable and reliable platform architectures but is not suitable for network programming and AI development; Python excels at network programming and AI algorithm development but has bottlenecks in high-performance task execution; C++ excels at high-performance task execution but is less suitable than the other two for platform development and AI programming. EasyAIoT adopts a tri-lingual mixed programming architecture, fully leveraging the strengths of each language to build an AIoT platform that's challenging to implement but extremely easy to use.
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
EasyAIoT is not actually one project; it is nine distinct projects.
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
EasyAIoT actively responds to localization strategies, providing comprehensive support for localized hardware and operating systems, delivering secure and controllable AIoT solutions for users:
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
  <li>Lightweight deployment on site—no need to stack heavy storage at every site</li>
  <li>Intelligence out of the box, shortening edge go-live cycles</li>
  <li>Compute scales with deployment points; alerts and evidence automatically aggregate to the cloud</li>
</ul>
</div>

<div style="padding: 20px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
<h4 style="margin-top: 0; color: white; font-size: 18px;">🖱️ Operating System Support</h4>
<ul style="font-size: 14px; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
  <li>Compatible with Kylin operating system</li>
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
EasyAIoT consists of eleven core projects, plus COMPILE multi-platform packaging and delivery:
</p>

<table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50; width: 20%;">Module</td>
<td style="padding: 15px; border: 1px solid #e0e0e0; background-color: #f8f9fa; font-weight: 600; color: #2c3e50;">Description</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>WEB Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">Frontend management interface, providing a unified user interaction experience</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>APP Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Multi-Channel Access</strong>: One build, multiple touchpoints—phones, mini programs, and apps</li>
    <li><strong>Capability Parity</strong>: Matches PC admin console capabilities with multi-tenant switching</li>
    <li><strong>Device Management</strong>: Unified management for direct cameras, GB28181, and NVR; online status and channel browsing with one-tap live preview in device details</li>
    <li><strong>Stream Forwarding</strong>: Task creation, start/stop, cluster node status, and multi-stream URL viewing</li>
    <li><strong>Algorithm Tasks</strong>: Real-time/snapshot algorithm task list, start/stop control, and detection/frame stats</li>
    <li><strong>Alert Center</strong>: Alert search, snapshot preview, and alarm recording VOD playback</li>
    <li><strong>Models & AI</strong>: Model list and deployment status, mobile image inference workbench, training task progress monitoring and stop</li>
    <li><strong>Profile</strong>: Personal info, account security, FAQ, feedback, and app settings</li>
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
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>NODE Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Node Agent</strong>: Edge/remote node Agent; one-click install deploys and automatically joins the platform</li>
    <li><strong>Status Reporting</strong>: Periodic heartbeats reporting CPU, memory, disk, GPU utilization, and active workload status in real time</li>
    <li><strong>Remote Workloads</strong>: Receives deploy/stop commands from the platform, launching AI model services, algorithm tasks, FFmpeg transcoding, and other workloads locally on the node</li>
    <li><strong>Media Node Pool</strong>: Supports remote deployment of streaming capabilities on nodes, enabling device-to-media-node binding and stream URL generation</li>
    <li><strong>Node Roles</strong>: Supports compute, media, and hybrid roles, enabling cross-node scheduling and elastic scaling for AI inference, algorithm tasks, and streaming services</li>
    <li><strong>Offline-Friendly</strong>: Provides offline dependency bundling and Agent hot-update capabilities, suitable for batch node onboarding in air-gapped or restricted network environments</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VIDEO Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Stream Processing</strong>: Supports RTSP/RTMP stream real-time processing and transmission</li>
    <li><strong>Algorithm Task Management</strong>: Supports real-time algorithm tasks and snapshot algorithm tasks, used for real-time video analysis and snapshot image analysis respectively</li>
    <li><strong>Frame Extractor and Sorter</strong>: Supports flexible frame extraction strategies and result sorting mechanisms, each algorithm task can bind independent frame extractors and sorters</li>
    <li><strong>Defense Time Period</strong>: Supports time-based configuration for full defense mode and half defense mode</li>
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
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>TASK Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">High-performance task processing module responsible for compute-intensive task execution</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>EDGE Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Infinite Federated Edge Cluster Mode</strong>: The eighth core module—extends intelligence from the center to the field; ordinary development boards and edge nodes can join the watch network at any time, compute scales with business, alerts and evidence automatically aggregate to the cloud</li>
    <li><strong>Lightweight On-Site Watch</strong>: Focuses on nearby perception and judgment with feedback—without carrying heavy control UI or local business systems, lowering edge deployment barriers and long-term ops burden</li>
    <li><strong>Out-of-the-Box Access, Unified Management</strong>: Field nodes join quickly and are orchestrated by the center for tasks and policies, reducing manual configuration and per-site build costs</li>
    <li><strong>Seamless Business Extension</strong>: The center sees the big picture and sets rules; edges watch the field and respond fast; node count grows with coverage, supporting horizontal scale-out for real-time analysis, patrol, and snapshot scenarios</li>
    <li><strong>Lightweight Deployment</strong>: Edge focuses on "doing the work" rather than "stacking equipment," making wide-area deployment easier to land and replicate</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>VISUALIZE Module</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Drag-and-Drop Dashboard Editor</strong>: The ninth core module—a high-performance low-code visualization editor focused on canvas editing and preview</li>
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
    <li><strong>Multidirectional Business Flow</strong>: The tenth core module—delivers platform-side alerts, device events, and business results to external systems such as MES / ERP / CRM / WMS by contract, closing the last mile from “the platform has data” to “business systems can use it”</li>
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
    <li><strong>Delivery & Watch Entry</strong>: The eleventh core module—independent of the business console: install, accept, and watch on arrival—shorten acceptance cycles and cut on-site / remote support cost</li>
    <li><strong>Same-Day Closed Loop</strong>: UI-driven install by tier with progress and results on the spot; bring up and hand over the appliance even before the business console is ready</li>
    <li><strong>Self-Serve Troubleshooting</strong>: Container health, resource levels, task logs, and image readiness at a glance—common start/stop, pull, and cache cleanup without waiting for developer commands</li>
    <li><strong>Reuse Across Sites</strong>: One entry across appliances and machine rooms—PoC and production delivery share the same playbook</li>
  </ul>
</td>
</tr>
<tr>
<td style="padding: 15px; border: 1px solid #e0e0e0; vertical-align: top;"><strong>COMPILE Packaging</strong></td>
<td style="padding: 15px; border: 1px solid #e0e0e0; line-height: 1.8; color: #444;">
  <ul style="margin: 5px 0; padding-left: 20px;">
    <li><strong>Multi-Platform Artifacts</strong>: Package PANEL and related capabilities into installers or binaries for Ubuntu / Debian, CentOS / RHEL, Windows, macOS, and ARM / Kylin targets—so customers can install without compiling from source on site</li>
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
The platform supports two types of algorithm tasks: real-time algorithm tasks for real-time video analysis of RTSP/RTMP streams, providing millisecond-level response capabilities; snapshot algorithm tasks for intelligent analysis of captured images, supporting event backtracking and image retrieval. Through algorithm task management, flexible frame extraction and sorting strategies are achieved, with each task able to bind independent frame extractors and sorters. Combined with model service cluster inference capabilities, millisecond-level response and high availability are ensured. Additionally, two defense strategies are provided: full defense mode and half defense mode, allowing flexible configuration of monitoring rules for different time periods, achieving precise time-based intelligent monitoring and alerting.
</p>
<p style="font-size: 14px; line-height: 1.8; color: #555; margin: 10px 0;">
In terms of IoT device management, EasyAIoT provides comprehensive device lifecycle management capabilities, supporting multiple IoT and industrial protocols (MQTT, TCP, HTTP, Modbus-TCP, Modbus-RTU, OPC UA) to achieve rapid device access, secure authentication, real-time monitoring, and intelligent control. Through the rule engine, intelligent data flow and processing of device data are realized, combined with AI capabilities for in-depth analysis of device data, achieving full-process automation from device access, data collection, intelligent analysis to decision execution, truly realizing interconnected everything and intelligent control of everything.
</p>
</div>

<img src=".image/iframe1.jpg" alt="EasyAIoT Platform Architecture" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">

## ⚠️ Disclaimer

EasyAIoT is an open-source learning project unrelated to commercial activities. Users must comply with laws and
regulations and refrain from illegal activities. If EasyAIoT discovers user violations, it will cooperate with
authorities and report to government agencies. Users bear full legal responsibility for illegal actions and shall
compensate third parties for damages caused by usage. All EasyAIoT-related resources are used at the user's own risk.

## 📚 Deployment Documentation

- [Platform Deployment Documentation](.doc/部署文档/平台部署文档_zh.md) — Step-by-step deployment guide for Linux / Mac / Windows
- [Deployment Best Practices](.doc/部署文档/部署最佳实践.md) — Environment requirements, one-click deployment, troubleshooting, and production recommendations

## 🎮 Demo Environment

- Demo URL: http://36.111.47.113:8888/
- Username: admin
- Password: admin123

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

#### 🧠 AI Models

| | | |
|:---:|:---:|:---:|
| ![Qwen](.image/banner/banner1093.jpg) | ![Vision Model](.image/banner/banner1094.jpg) | ![List](.image/banner/banner1099.png) |
| ![Configuration](.image/banner/banner1100.png) | ![Details](.image/banner/banner1101.png) | ![Invocation](.image/banner/banner1102.png) |
| ![Training](.image/banner/banner1019.jpg) | ![Task](.image/banner/banner1020.jpg) | ![List](.image/banner/banner1023.jpg) |
| ![Progress](.image/banner/banner1024.jpg) | ![Parameters](.image/banner/banner1017.jpg) | ![Evaluation](.image/banner/banner1018.jpg) |
| ![Details](.image/banner/banner1021.jpg) | ![Logs](.image/banner/banner1022.jpg) | ![Management](.image/banner/banner1097.png) |
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
| ![Rules](.image/banner/banner1013.jpg) | ![Orchestration](.image/banner/banner1014.png) |  |

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
| ![Home](.image/banner/app/app_1000.jpg) | ![Monitoring](.image/banner/app/app_1001.jpg) | ![Preview](.image/banner/app/app_1002.jpg) |
| ![Alerts](.image/banner/app/app_1003.jpg) | ![Playback](.image/banner/app/app_1004.jpg) | ![Device](.image/banner/app/app_1005.jpg) |
| ![Messages](.image/banner/app/app_1006.jpg) | ![Profile](.image/banner/app/app_1007.jpg) |  |

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
</tbody>
</table>

<p style="font-size: 14px; line-height: 1.8; color: #2c3e50; font-weight: 500; margin: 20px 0; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #3498db; border-radius: 4px;">
<strong>Special Thanks</strong>: The above contributors have advanced EasyAIoT in cross-platform deployment documentation and scripts, national-standard video capability delivery and AI integration verification, multi-GPU training and checkpoint resume, multi-vendor camera direct discovery and batch onboarding, Tianditu spatial visualization, heterogeneous streaming media cluster deployment and scheduling, license plate recognition algorithm and complete implementation, EasyAIoT-Edge end-to-end edge-side integration, campus developer community organization and youth collaborative ecosystem building, IoT device uplink/downlink closed loop and DJI FlightHub aerial view integration, Modbus-TCP / Modbus-RTU / OPC UA industrial protocol access, the production-ready closed loop of camera direct-connect from discovery through login/sync/config/multi-brand streaming, the drag-and-drop Board vision with IoT metric real-time/historical value integration, and sensor float data prediction with threshold alarm rules plus one-screen running-status views for central-device associated sub-devices. Their professionalism and selfless dedication are worthy of our learning and respect. Once again, we express our most sincere gratitude to these outstanding contributors! 🙏
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
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/在路上.png" width="80px;" alt="在路上"/><br /><sub><b>在路上</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/忘记时间.png" width="80px;" alt="忘记时间"/><br /><sub><b>忘记时间</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/HuaZy.jpg" width="80px;" alt="HuaZy"/><br /><sub><b>HuaZy</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/ANDY.png" width="80px;" alt="ANDY"/><br /><sub><b>ANDY</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/A许庆.png" width="80px;" alt="A许庆"/><br /><sub><b>A许庆</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/刘兆中📶⁵ᴳ.png" width="80px;" alt="刘兆中📶⁵ᴳ"/><br /><sub><b>刘兆中📶⁵ᴳ</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/冯.png" width="80px;" alt="冯"/><br /><sub><b>冯</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/莫斯克.png" width="80px;" alt="莫斯克"/><br /><sub><b>莫斯克</b></sub></a></td>
      <td align="center" valign="top" width="11.11%"><a href="javascript:void(0)" target="_blank"><img src="./.image/open-source-guardian/赵欢.png" width="80px;" alt="赵欢"/><br /><sub><b>赵欢</b></sub></a></td>
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
