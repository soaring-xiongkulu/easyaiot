export interface FeatureItem {
  id: string
  title: string
  summary: string
  points: string[]
  image: string
}

export const features: FeatureItem[] = [
  {
    id: 'video',
    title: '视频接入与智视',
    summary: 'GB28181 / ONVIF 多协议接入，分屏监控与 AI 联动同屏处置。',
    points: [
      '摄像头全生命周期纳管与预览',
      '大疆机场与无人机空中视角接入',
      '实时流分析与抓拍算法任务',
    ],
    image: '/images/feature-video.jpg',
  },
  {
    id: 'rtc',
    title: '消费级摄像头 P2P 桥接',
    summary:
      'RTC 模块把 Tapo、涂鸦、Ring、Nest、小米、Wyze、DoorBird、GoPro、Roborock 等无 RTSP 设备纳入同一平台。',
    points: [
      '九大品牌 Web 一键接入，OAuth 平台在线完成账号绑定',
      'P2P 取流 → 标准 RTSP → SRS 推流 → 播放与 AI 分析',
      '双向对讲、设备删除自动清理流，与国标/ONVIF 同屏共管',
    ],
    image: '/images/feature-rtc.jpg',
  },
  {
    id: 'runtime',
    title: 'RUNTIME 实时分析加速',
    summary:
      '需要更高实时性时按任务打开加速：画面跟得更紧，预览、告警与任务编排仍在原平台完成。',
    points: [
      '实时看场更顺滑，高峰优先保住最新画面',
      '定时抓拍、多路轮巡共用同一套加速能力',
      '按任务启用即可，不必改预览与告警习惯',
    ],
    image: '/images/feature-runtime.jpg',
  },
  {
    id: 'ai',
    title: 'AI 算法与联邦算力',
    summary: '从标注、训练到推理调度，同一套平台贯通视觉智能闭环。',
    points: [
      'YOLO 目标检测与 SAM 零样本标注',
      '人脸 / 车牌识别与可编排后处理',
      'RUNTIME 原子边缘：MQTT 告警 + HTTP 心跳，算力随业务铺开',
    ],
    image: '/images/feature-ai.jpg',
  },
  {
    id: 'iot',
    title: '物联网全生命周期',
    summary: '把「数」与「图」拧成可运营动作，感知—理解—决策—执行闭环。',
    points: [
      'MQTT / TCP / HTTP / Modbus / OPC UA',
      '规则引擎与设备影子联动',
      '告警研判与现场处置同口径',
    ],
    image: '/images/feature-iot.jpg',
  },
  {
    id: 'panel',
    title: 'PANEL 交付与值守',
    summary: '一体机到场当天可装可验，值守不必事事等开发远程敲命令。',
    points: [
      '按 mini / standard / full 一键装机',
      '容器健康、日志与依赖一目了然',
      '多项目交付口径一致可复用',
    ],
    image: '/images/feature-panel.jpg',
  },
  {
    id: 'platforms',
    title: '多系统安装包与国产化',
    summary:
      'Ubuntu、CentOS/RHEL、Windows、macOS、麒麟 (Kylin)、欧拉 (openEuler) 一套交付口径，按现场系统直接下载安装。',
    points: [
      'Ubuntu / Debian .deb（amd64 / arm64，内置 runtime）',
      'CentOS/RHEL el7–el9 x86 与 ARM 分版本 .rpm；Windows NSIS、macOS .dmg / .app',
      '麒麟 (Kylin) ARM64 .deb、欧拉 (openEuler) .rpm 国产化适配',
    ],
    image: '/images/feature-platforms.jpg',
  },
  {
    id: 'visualize',
    title: '可视化大屏与组态',
    summary: '设备数据既能展成指挥态势，也能落回工艺画面。',
    points: [
      '可视化大屏编辑与运行',
      'Web 工艺组态联动现场',
      '平台标识与品牌可现场替换',
    ],
    image: '/images/feature-visualize.jpg',
  },
  {
    id: 'transform',
    title: 'TRANSFORM 业务流转',
    summary: '把平台侧事件按约定投递到 MES / ERP / CRM / WMS。',
    points: [
      '目的、规则与映射模板可配置',
      '投递过程可监控、可回看',
      '多方对接从定制接口变为约定配通',
    ],
    image: '/images/feature-transform.jpg',
  },
]
