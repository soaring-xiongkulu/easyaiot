/**
 * 设备接入分类规范
 *
 * 大类：按平台接入协议划分（IP 网络 / 国标 SIP）
 * 小类：具体设备形态（IPC / NVR / GB28181 设备）
 * 厂商：仅 IP 网络接入时用于 RTSP 模板与 NVR 识别
 */

/** 设备小类（后端 device_kind 映射） */
export type DeviceKind = 'camera' | 'nvr' | 'gb28181';

/** 设备大类（接入协议） */
export type DeviceMajorCategory = 'ip_network' | 'gb28181_protocol';

/** 创建方式（第二步） */
export type CreateMethod = 'onvif' | 'segment_scan' | 'manual' | 'gb_access';

/**
 * 厂商/品牌
 * - hikvision 海康威视
 * - dahua 大华
 * - uniview 宇视
 * - huawei 华为
 * - xiaomi 小米
 * - tiandy 天地伟业
 * - lanpartix 中维世纪
 * - tp_link 普联 TP-Link
 * - tvt 天视通
 * - custom 其他/自定义规则
 */
export type CameraBrand =
  | 'custom'
  | 'hikvision'
  | 'dahua'
  | 'uniview'
  | 'huawei'
  | 'xiaomi'
  | 'tiandy'
  | 'lanpartix'
  | 'tp_link'
  | 'tvt';

export interface DeviceMinorOption {
  value: DeviceKind;
  label: string;
  shortLabel: string;
  description: string;
  keywords: string[];
}

export interface DeviceMajorOption {
  value: DeviceMajorCategory;
  label: string;
  description: string;
  keywords: string[];
  minors: DeviceMinorOption[];
}

export interface CreateMethodOption {
  value: CreateMethod;
  label: string;
  description: string;
  deviceKinds: DeviceKind[];
}

export interface CameraBrandOption {
  value: CameraBrand;
  label: string;
  /** 是否支持自定义填写规则（仅 custom 为 true） */
  customizable?: boolean;
}

/** IP 网络接入 — 小类 */
const IP_NETWORK_MINORS: DeviceMinorOption[] = [
  {
    value: 'camera',
    label: 'IPC 网络摄像机',
    shortLabel: 'IPC',
    description: '单路 RTSP 直连，支持 ONVIF 发现与跨网段扫描',
    keywords: ['ipc', '摄像头', '摄像机', '网络摄像机', 'rtsp', 'onvif', '直连'],
  },
  {
    value: 'nvr',
    label: 'NVR 网络录像机',
    shortLabel: 'NVR',
    description: '登记录像机并自动挂载下属摄像头通道',
    keywords: ['nvr', '录像机', '硬盘录像机', '网络录像机', '挂载'],
  },
];

/** 国标协议接入 — 小类 */
const GB28181_MINORS: DeviceMinorOption[] = [
  {
    value: 'gb28181',
    label: 'GB28181 国标设备',
    shortLabel: 'GB28181',
    description: '设备侧配置 SIP 参数后向平台主动注册',
    keywords: ['gb28181', '国标', 'sip', '28181', 'wvp'],
  },
];

export const DEVICE_MAJOR_CATEGORIES: DeviceMajorOption[] = [
  {
    value: 'ip_network',
    label: 'IP 网络接入',
    description: '通过 RTSP / ONVIF / 跨网段扫描接入摄像头或录像机',
    keywords: ['ip', 'rtsp', 'onvif', '网络', '直连', '扫描'],
    minors: IP_NETWORK_MINORS,
  },
  {
    value: 'gb28181_protocol',
    label: '国标协议接入',
    description: '设备通过 GB28181 SIP 信令注册到平台',
    keywords: ['gb28181', '国标', 'sip', '协议', '28181'],
    minors: GB28181_MINORS,
  },
];

export const CREATE_METHOD_OPTIONS: CreateMethodOption[] = [
  {
    value: 'onvif',
    label: '局域网 ONVIF 扫描',
    description: '同一局域网内 WS-Discovery 自动发现设备',
    deviceKinds: ['camera'],
  },
  {
    value: 'segment_scan',
    label: '跨网段扫描',
    description: '填写网段与 Web 凭证批量扫描注册',
    deviceKinds: ['camera', 'nvr'],
  },
  {
    value: 'manual',
    label: '手动填写',
    description: '直接填写 IP、凭证或 RTSP 地址',
    deviceKinds: ['camera', 'nvr'],
  },
  {
    value: 'gb_access',
    label: '生成接入配置',
    description: '生成 SIP 参数，复制到设备侧完成注册',
    deviceKinds: ['gb28181'],
  },
];

/**
 * 品牌下拉选项（顺序即展示顺序）
 * 「其他 / 自定义规则」放在最后，允许用户手填 RTSP 路径模板
 */
export const CAMERA_BRAND_OPTIONS: CameraBrandOption[] = [
  { value: 'hikvision', label: '海康威视' },
  { value: 'dahua', label: '大华' },
  { value: 'uniview', label: '宇视' },
  { value: 'huawei', label: '华为' },
  { value: 'xiaomi', label: '小米' },
  { value: 'tiandy', label: '天地伟业' },
  { value: 'lanpartix', label: '中维世纪' },
  { value: 'tp_link', label: 'TP-Link' },
  { value: 'tvt', label: '天视通' },
  { value: 'custom', label: '自定义规则', customizable: true },
];

/** 全部合法品牌值（用于 URL query 反序列化校验） */
const ALL_CAMERA_BRAND_VALUES: CameraBrand[] = CAMERA_BRAND_OPTIONS.map((o) => o.value);

/** 大类图标（添加设备向导） */
export const MAJOR_CATEGORY_ICONS: Record<DeviceMajorCategory, string> = {
  ip_network: 'ant-design:wifi-outlined',
  gb28181_protocol: 'ant-design:cluster-outlined',
};

/** 设备小类图标 */
export const DEVICE_KIND_ICONS: Record<DeviceKind, string> = {
  camera: 'ant-design:video-camera-outlined',
  nvr: 'ant-design:hdd-outlined',
  gb28181: 'ant-design:api-outlined',
};

/** 接入方式图标 */
export const CREATE_METHOD_ICONS: Record<CreateMethod, string> = {
  onvif: 'ant-design:radar-chart-outlined',
  segment_scan: 'ant-design:scan-outlined',
  manual: 'ant-design:edit-outlined',
  gb_access: 'ant-design:key-outlined',
};

/** 快捷接入场景（一步预选类型与方式） */
export interface QuickStartScenario {
  id: string;
  title: string;
  description: string;
  icon: string;
  tag?: string;
  kind: DeviceKind;
  method: CreateMethod;
  brand?: CameraBrand;
}

export const QUICK_START_SCENARIOS: QuickStartScenario[] = [
  {
    id: 'ipc_onvif',
    title: '局域网 IPC',
    description: '同一网段 ONVIF 自动发现，适合批量接入网络摄像机',
    icon: 'ant-design:video-camera-outlined',
    tag: '推荐',
    kind: 'camera',
    method: 'onvif',
    brand: 'dahua',
  },
  {
    id: 'nvr_manual',
    title: 'NVR 录像机',
    description: '填写 Web 凭证，自动挂载下属摄像头通道',
    icon: 'ant-design:hdd-outlined',
    kind: 'nvr',
    method: 'manual',
    brand: 'hikvision',
  },
  {
    id: 'gb28181',
    title: '国标 GB28181',
    description: '生成 SIP 参数，设备侧主动注册到平台',
    icon: 'ant-design:cluster-outlined',
    kind: 'gb28181',
    method: 'gb_access',
  },
  {
    id: 'segment_scan',
    title: '跨网段扫描',
    description: '填写网段批量扫描，适合多网段或未知 IP 场景',
    icon: 'ant-design:scan-outlined',
    kind: 'camera',
    method: 'segment_scan',
    brand: 'dahua',
  },
];

/** 所有小类（扁平列表，供兼容引用） */
export const ALL_DEVICE_MINORS: DeviceMinorOption[] = [
  ...IP_NETWORK_MINORS,
  ...GB28181_MINORS,
];

/** @deprecated 兼容旧引用 */
export const VIDEO_DEVICE_MINORS = ALL_DEVICE_MINORS;

/** @deprecated 兼容旧引用 */
export const DEVICE_KIND_OPTIONS = ALL_DEVICE_MINORS.map((m) => ({
  value: m.value,
  label: m.label,
  description: m.description,
}));

export function getCreateMethodsForKind(kind: DeviceKind): CreateMethodOption[] {
  return CREATE_METHOD_OPTIONS.filter((m) => m.deviceKinds.includes(kind));
}

export function getDefaultMethodForKind(kind: DeviceKind): CreateMethod {
  const methods = getCreateMethodsForKind(kind);
  return methods[0]?.value ?? 'manual';
}

export function getMinorOption(kind: DeviceKind): DeviceMinorOption | undefined {
  return ALL_DEVICE_MINORS.find((m) => m.value === kind);
}

export function getMajorForKind(kind: DeviceKind): DeviceMajorCategory | undefined {
  for (const major of DEVICE_MAJOR_CATEGORIES) {
    if (major.minors.some((m) => m.value === kind)) return major.value;
  }
  return undefined;
}

export function getMethodOption(method: CreateMethod): CreateMethodOption | undefined {
  return CREATE_METHOD_OPTIONS.find((m) => m.value === method);
}

export function getMajorCategory(value: DeviceMajorCategory): DeviceMajorOption | undefined {
  return DEVICE_MAJOR_CATEGORIES.find((m) => m.value === value);
}

export function getDefaultMajorCategory(): DeviceMajorCategory {
  return 'ip_network';
}

/** IP 网络接入才需要选择厂商 */
export function needsVendorSelection(major: DeviceMajorCategory): boolean {
  return major === 'ip_network';
}

/** 按关键词过滤大类/小类 */
export function filterDeviceCategories(keyword: string): {
  majors: DeviceMajorOption[];
  minorMap: Record<string, DeviceMinorOption[]>;
} {
  const q = keyword.trim().toLowerCase();
  if (!q) {
    const minorMap: Record<string, DeviceMinorOption[]> = {};
    for (const major of DEVICE_MAJOR_CATEGORIES) {
      minorMap[major.value] = major.minors;
    }
    return { majors: DEVICE_MAJOR_CATEGORIES, minorMap };
  }

  const majors: DeviceMajorOption[] = [];
  const minorMap: Record<string, DeviceMinorOption[]> = {};

  for (const major of DEVICE_MAJOR_CATEGORIES) {
    const majorHit =
      major.label.toLowerCase().includes(q) ||
      major.description.toLowerCase().includes(q) ||
      major.keywords.some((k) => k.toLowerCase().includes(q));

    const matchedMinors = major.minors.filter(
      (minor) =>
        minor.label.toLowerCase().includes(q) ||
        minor.shortLabel.toLowerCase().includes(q) ||
        minor.description.toLowerCase().includes(q) ||
        minor.keywords.some((k) => k.toLowerCase().includes(q)),
    );

    if (majorHit || matchedMinors.length) {
      majors.push(major);
      minorMap[major.value] = majorHit ? major.minors : matchedMinors;
    }
  }

  return { majors, minorMap };
}

export function parseDeviceCreateQuery(query: Record<string, unknown>): {
  kind: DeviceKind;
  method: CreateMethod;
  brand: CameraBrand;
} {
  const kindRaw = String(query.kind || query.deviceKind || 'camera');
  const kind: DeviceKind = ['camera', 'nvr', 'gb28181'].includes(kindRaw)
    ? (kindRaw as DeviceKind)
    : 'camera';

  const methodRaw = String(query.method || query.createMethod || '');
  const validMethods = getCreateMethodsForKind(kind).map((m) => m.value);
  const method: CreateMethod = validMethods.includes(methodRaw as CreateMethod)
    ? (methodRaw as CreateMethod)
    : getDefaultMethodForKind(kind);

  const brandRaw = String(query.brand || query.cameraBrand || 'dahua');
  const brand: CameraBrand = ALL_CAMERA_BRAND_VALUES.includes(brandRaw as CameraBrand)
    ? (brandRaw as CameraBrand)
    : 'dahua';

  return { kind, method, brand };
}

/** @deprecated 兼容旧引用 */
export function getKindOption(kind: DeviceKind) {
  return getMinorOption(kind);
}

// ====================== 品牌 RTSP 协议规则库 ======================

/**
 * 品牌协议规则
 *
 * 用于：
 * - 手动填写时根据品牌生成 RTSP 模板
 * - 跨网段扫描时根据路径标识识别品牌
 * - Web 接口特征用于 NVR 私有协议适配
 *
 * 模板占位符（仅 RTSP 路径部分，不含 rtsp://user:pass@ip:port 前缀）：
 * - `{ch}`      通道号（起始见 channelStart）
 * - `{stream}`  码流类型（主/子），由模板自行决定取值
 * - `{codec}`   编码类型，默认 h264
 */
export interface CameraBrandProtocol {
  /** 品牌 */
  brand: CameraBrand;
  /** 显示名 */
  label: string;
  /** 默认 RTSP 端口 */
  defaultRtspPort: number;
  /** 默认 Web 端口（HTTP） */
  defaultWebPort: number;
  /** 是否原生支持 RTSP（小米米家需桥接） */
  rtspNative: boolean;
  /** 主码流 RTSP 路径模板（实时） */
  rtspMainPath: string;
  /** 子码流 RTSP 路径模板（实时） */
  rtspSubPath: string;
  /**
   * 回放 RTSP 路径模板
   * 占位符同实时流，额外支持:
   * - {starttime} 开始时间（UTC/GMT，格式见 playbackTimeFormat）
   * - {endtime}   结束时间（UTC/GMT）
   */
  rtspReplayPath?: string;
  /** 回放时间格式，默认 YYYYMMDDTHHmmssZ（ISO8601 基本格式） */
  playbackTimeFormat?: string;
  /** 通道号起始 */
  channelStart: number;
  /**
   * RTSP 核心路径标识（不含前缀，仅 path 前缀片段）
   * 用于扫描结果反向匹配品牌
   */
  rtspPathIdentifiers: string[];
  /** 私有特色协议（HTTP API） */
  privateProtocols: string[];
  /** Web 接口特征路径（用于扫描识别/枚举通道） */
  webInterfaceFeatures: string[];
  /** 默认用户名 */
  defaultUsername: string;
  /** 备注（特殊说明） */
  remarks?: string;
}

/**
 * 品牌协议规则库
 *
 * 资料来源：
 * - 海康/大华/宇视/华为/TP-Link/天视通/中维/天地伟业 官方文档及社区汇总
 * - https://www.zwplayer.cn/articles/device/ip-camera-rtsp-url-guide.html
 * - https://security.tp-link.com.cn/m/detail_article_4432.html
 */
export const CAMERA_BRAND_PROTOCOLS: Record<CameraBrand, CameraBrandProtocol> = {
  hikvision: {
    brand: 'hikvision',
    label: '海康威视',
    defaultRtspPort: 554,
    defaultWebPort: 80,
    rtspNative: true,
    // 实时: /Streaming/Channels/{ch}{stream}，ch=通道号，stream: 1主/2子/3第三码流
    rtspMainPath: '/Streaming/Channels/{ch}01',
    rtspSubPath: '/Streaming/Channels/{ch}02',
    // 回放: /Streaming/tracks/{ch}01?starttime=...&endtime=...
    rtspReplayPath: '/Streaming/tracks/{ch}01?starttime={starttime}&endtime={endtime}',
    playbackTimeFormat: 'YYYYMMDDtHHmmssz',
    channelStart: 1,
    rtspPathIdentifiers: ['/Streaming/Channels/', '/Streaming/tracks/', '/h264/ch', '/h265/ch', '/av_stream'],
    privateProtocols: ['ISAPI（HTTP RESTful）', 'SDK（HCNetSDK）'],
    webInterfaceFeatures: ['/ISAPI/System/deviceInfo', '/ISAPI/Streaming/channels', '/ISAPI/ContentMgmt'],
    defaultUsername: 'admin',
    remarks:
      '实时: /Streaming/Channels/{ch}01 主码流 /{ch}02 子码流 /{ch}03 第三码流，例:/Streaming/Channels/1201 第12通道主码流\n' +
      '多播: 加 ?transportmode=multicast\n' +
      '老款设备: /h264/ch1/main/av_stream\n' +
      '回放: /Streaming/tracks/{ch}01?starttime=20221201t010000z&endtime=20221201t040000z（时间为GMT）',
  },
  dahua: {
    brand: 'dahua',
    label: '大华',
    defaultRtspPort: 554,
    defaultWebPort: 80,
    rtspNative: true,
    // 实时: /cam/realmonitor?channel={ch}&subtype={0|1}，0主 1子
    rtspMainPath: '/cam/realmonitor?channel={ch}&subtype=0',
    rtspSubPath: '/cam/realmonitor?channel={ch}&subtype=1',
    // 回放: /cam/playback?channel={ch}&subtype=0&starttime=...&endtime=...
    rtspReplayPath: '/cam/playback?channel={ch}&subtype=0&starttime={starttime}&endtime={endtime}',
    playbackTimeFormat: 'YYYY_MM_DD_HH_mm_ss',
    channelStart: 1,
    rtspPathIdentifiers: ['/cam/realmonitor', '/cam/playback'],
    privateProtocols: ['CGI（HTTP）', 'SDK（NetSDK）'],
    webInterfaceFeatures: ['/cgi-bin/magicBoxInfo.cgi', '/cgi-bin/current_config.cgi', '/cgi-bin/configManager.cgi'],
    defaultUsername: 'admin',
    remarks:
      '实时: /cam/realmonitor?channel=1&subtype=0 主码流 subtype=1 子码流\n' +
      '回放: /cam/playback?channel=1&subtype=0&starttime=2022_09_01_14_01_01&endtime=2022_09_01_15_01_01\n' +
      '0通道预览: channel=总路数+1，如64路设备填channel=65，仅主码流',
  },
  uniview: {
    brand: 'uniview',
    label: '宇视',
    defaultRtspPort: 554,
    defaultWebPort: 80,
    rtspNative: true,
    // /media/video{1|2}（1 主 2 子），可选 /multicast 组播
    rtspMainPath: '/media/video1',
    rtspSubPath: '/media/video2',
    channelStart: 1,
    rtspPathIdentifiers: ['/media/video'],
    privateProtocols: ['UNV 私有协议', 'onvif'],
    webInterfaceFeatures: ['/cgi-bin/media', '/LAPI'],
    defaultUsername: 'admin',
    remarks: '码流: video1主 video2子 video3第三码流；组播加 /multicast，例: /media/video2/multicast',
  },
  huawei: {
    brand: 'huawei',
    label: '华为',
    defaultRtspPort: 554,
    defaultWebPort: 80,
    rtspNative: true,
    // NVR实时: /rtsp/streaming?channel={ch}&subtype={0|1}，0主 1子
    rtspMainPath: '/rtsp/streaming?channel={ch}&subtype=0',
    rtspSubPath: '/rtsp/streaming?channel={ch}&subtype=1',
    // NVR回放: /rtsp/playback?channel={ch}&subtype=0&recordtype=1&starttime=...&endtime=...
    rtspReplayPath: '/rtsp/playback?channel={ch}&subtype=0&recordtype=1&starttime={starttime}&endtime={endtime}',
    playbackTimeFormat: 'YYYY-MM-DDTHH:mm:ssZ',
    channelStart: 1,
    rtspPathIdentifiers: ['/rtsp/streaming', '/rtsp/playback', '/LiveMedia/'],
    privateProtocols: ['HUAWEI SDK'],
    webInterfaceFeatures: ['/LAPI/Capability', '/LAPI/System'],
    defaultUsername: 'admin',
    remarks:
      'NVR实时: /rtsp/streaming?channel=1&subtype=0 主码流 subtype=1 子码流\n' +
      'NVR回放: /rtsp/playback?channel=2&subtype=0&recordtype=1&starttime=2025-10-24T08:00:00Z&endtime=...（GMT时间）\n' +
      'IPC取流: /LiveMedia/ch1/Media1（可选 trackID=1）\n' +
      'recordtype: 1计划录像 4移动侦测',
  },
  xiaomi: {
    brand: 'xiaomi',
    label: '小米',
    defaultRtspPort: 8554,
    defaultWebPort: 80,
    rtspNative: false,
    // 米家摄像头原生不支持 RTSP，需通过 Micam / Go2RTC 桥接，路径自定义
    rtspMainPath: '/xiaomi/{ch}',
    rtspSubPath: '/xiaomi/{ch}/sub',
    channelStart: 0,
    rtspPathIdentifiers: ['/xiaomi/'],
    privateProtocols: ['米家私有协议', 'EasyAIoT RTC 桥接', 'Go2RTC 桥接'],
    webInterfaceFeatures: [],
    defaultUsername: '',
    remarks: '米家摄像头原生不支持 RTSP，可通过 EasyAIoT RTC 模块（go2rtc 桥接）取流',
  },
  tiandy: {
    brand: 'tiandy',
    label: '天地伟业',
    defaultRtspPort: 554,
    defaultWebPort: 80,
    rtspNative: true,
    // 实时: /{ch}/{stream}，stream: 1=主 2=子 3=三码流
    rtspMainPath: '/{ch}/1',
    rtspSubPath: '/{ch}/2',
    // 回放: /replay/{ch}/{stream}?starttime=...&endtime=...，时间为 GMT
    rtspReplayPath: '/replay/{ch}/1?starttime={starttime}&endtime={endtime}',
    playbackTimeFormat: 'YYYYMMDDTHHmmssZ',
    channelStart: 1,
    rtspPathIdentifiers: ['/replay/', '/cgi-bin/hi3510'],
    privateProtocols: ['天地伟业 SDK', 'onvif'],
    webInterfaceFeatures: ['/cgi-bin/hi3510', '/onvif/device_service'],
    defaultUsername: 'admin',
    remarks:
      '实时格式: /通道/码流，主1 副2 三3；例: rtsp://admin:1111@192.168.1.15:554/1/1\n' +
      '回放格式: /replay/通道/码流?starttime=...&endtime=...，时间为 GMT（UTC+8需减8小时），不加Z则不限时间',
  },
  lanpartix: {
    brand: 'lanpartix',
    label: '中维世纪',
    defaultRtspPort: 8554,
    defaultWebPort: 80,
    rtspNative: true,
    // /profile{0|1}，0 主 1 子，默认端口 8554
    rtspMainPath: '/profile0',
    rtspSubPath: '/profile1',
    channelStart: 0,
    rtspPathIdentifiers: ['/profile0', '/profile1'],
    privateProtocols: ['中维世纪 SDK'],
    webInterfaceFeatures: ['/cgi-bin/devInfo', '/onvif/device_service'],
    defaultUsername: 'admin',
    remarks: 'RTSP 默认端口 8554（非 554）',
  },
  tp_link: {
    brand: 'tp_link',
    label: 'TP-Link',
    defaultRtspPort: 554,
    defaultWebPort: 80,
    rtspNative: true,
    // /stream{1|2}，1 主 2 子；双目: /stream2&channel={ch}
    rtspMainPath: '/stream1',
    rtspSubPath: '/stream2',
    channelStart: 1,
    rtspPathIdentifiers: ['/stream1', '/stream2'],
    privateProtocols: ['TP-Link 私有协议', 'onvif'],
    webInterfaceFeatures: ['/cgi-bin/luci', '/onvif/device_service'],
    defaultUsername: 'admin',
    remarks: '双目摄像头: /stream2&channel=2',
  },
  tvt: {
    brand: 'tvt',
    label: '天视通',
    defaultRtspPort: 554,
    defaultWebPort: 80,
    rtspNative: true,
    // /mpeg4 主 /mpeg4cif 子；数据端口 8091
    rtspMainPath: '/mpeg4',
    rtspSubPath: '/mpeg4cif',
    channelStart: 1,
    rtspPathIdentifiers: ['/mpeg4', '/mpeg4cif'],
    privateProtocols: ['天视通私有协议'],
    webInterfaceFeatures: ['/cgi-bin/hi3510', '/onvif/device_service'],
    defaultUsername: 'admin',
    remarks: '数据端口 8091；ONVIF 端口 80',
  },
  custom: {
    brand: 'custom',
    label: '自定义规则',
    defaultRtspPort: 554,
    defaultWebPort: 80,
    rtspNative: true,
    // 自定义规则由用户手填 RTSP 路径模板
    rtspMainPath: '/{channel}/{subtype}',
    rtspSubPath: '/{channel}/{subtype}',
    channelStart: 1,
    rtspPathIdentifiers: [],
    privateProtocols: ['onvif'],
    webInterfaceFeatures: ['/onvif/device_service'],
    defaultUsername: 'admin',
    remarks:
      '自定义 RTSP 路径模板，支持以下占位符：\n' +
      '  {username} - 用户名\n' +
      '  {password} - 密码\n' +
      '  {ip} - 设备IP\n' +
      '  {port} - RTSP端口（默认554）\n' +
      '  {channel} - 通道号\n' +
      '  {subtype} - 码流类型（主码流0，子码流1）\n' +
      '示例: /cam/realmonitor?channel={channel}&subtype={subtype}',
  },
};

/**
 * 获取品牌协议规则
 * 若品牌不存在，回退到 custom 规则
 */
export function getBrandProtocol(brand: CameraBrand | string | undefined): CameraBrandProtocol {
  if (brand && brand in CAMERA_BRAND_PROTOCOLS) {
    return CAMERA_BRAND_PROTOCOLS[brand as CameraBrand];
  }
  return CAMERA_BRAND_PROTOCOLS.custom;
}

/** 判断品牌是否为自定义规则 */
export function isCustomBrand(brand: CameraBrand | string | undefined): boolean {
  return !brand || brand === 'custom';
}

/**
 * 根据品牌协议规则生成完整 RTSP URL
 *
 * @param brand     品牌
 * @param ip        设备 IP
 * @param username  用户名
 * @param password  密码
 * @param channel   通道号（默认取 channelStart）
 * @param stream    码流：'main' | 'sub'，默认 'main'
 * @param port      RTSP 端口（默认取品牌 defaultRtspPort）
 * @param customPath 自定义路径（仅 custom 品牌且用户提供时使用）
 */
export function buildRtspUrl(
  brand: CameraBrand | string | undefined,
  ip: string,
  username: string,
  password: string,
  channel?: number,
  stream: 'main' | 'sub' = 'main',
  port?: number,
  customPath?: string,
): string {
  if (!ip) return '';
  const protocol = getBrandProtocol(brand);
  const ch = channel ?? protocol.channelStart;
  const rtspPort = port ?? protocol.defaultRtspPort;
  const subtype = stream === 'main' ? 0 : 1;

  let path: string;
  if (isCustomBrand(brand) && customPath) {
    path = customPath;
    // 自定义模板：支持 {username} {password} {ip} {port} {channel} {subtype} 占位符
    path = path
      .replace(/\{username\}/g, encodeURIComponent(username))
      .replace(/\{password\}/g, encodeURIComponent(password))
      .replace(/\{ip\}/g, ip)
      .replace(/\{port\}/g, String(rtspPort))
      .replace(/\{channel\}/g, String(ch))
      .replace(/\{subtype\}/g, String(subtype));
  } else {
    path = stream === 'main' ? protocol.rtspMainPath : protocol.rtspSubPath;
    // 内置品牌模板：使用 {ch} {stream} {codec} 占位符
    path = path
      .replace(/\{ch\}/g, String(ch))
      .replace(/\{stream\}/g, stream === 'main' ? '1' : '2')
      .replace(/\{codec\}/g, 'h264');
  }

  // 如果路径已经是完整的 rtsp:// URL，直接返回
  if (path.toLowerCase().startsWith('rtsp://')) {
    return path;
  }

  // 凭证
  const cred = username || password ? `${encodeURIComponent(username)}:${encodeURIComponent(password)}@` : '';
  return `rtsp://${cred}${ip}:${rtspPort}${path}`;
}

/**
 * 根据 RTSP URL 反向识别品牌
 *
 * 通过匹配 rtspPathIdentifiers 判断
 */
export function detectBrandByRtspUrl(rtspUrl: string): CameraBrand {
  if (!rtspUrl) return 'custom';
  const url = rtspUrl.toLowerCase();
  for (const brand of ALL_CAMERA_BRAND_VALUES) {
    if (brand === 'custom') continue;
    const protocol = CAMERA_BRAND_PROTOCOLS[brand];
    if (protocol.rtspPathIdentifiers.some((id) => id && url.includes(id.toLowerCase()))) {
      return brand;
    }
  }
  return 'custom';
}
