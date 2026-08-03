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
    id: 'ai',
    title: 'AI 算法与联邦算力',
    summary: '从标注、训练到推理调度，同一套平台贯通视觉智能闭环。',
    points: [
      'YOLO 目标检测与 SAM 零样本标注',
      '人脸 / 车牌识别与可编排后处理',
      '无限联邦边缘集群，算力随业务铺开',
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
