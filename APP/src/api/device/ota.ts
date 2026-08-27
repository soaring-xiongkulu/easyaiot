/**
 * 设备侧统一 OTA 出入口
 *
 * 平台采用拉取模型：由设备/APP 主动发起检测（/ota/check），
 * 升级过程按阶段上报（/ota/report），平台侧幂等落库并在启动成功后回写设备版本。
 */
import { http } from '@/http/http'

/** 升级包类型[0:软件包,1:固件包,2:APP包,3:PC包] */
export const OTA_PACKAGE_TYPES = [
  { code: 0, name: '软件包', icon: 'i-carbon-application-web', color: '#2f6bff' },
  { code: 1, name: '固件包', icon: 'i-carbon-chip', color: '#f59e0b' },
  { code: 2, name: 'APP包', icon: 'i-carbon-mobile', color: '#8b5cf6' },
  { code: 3, name: 'PC包', icon: 'i-carbon-laptop', color: '#0ea5e9' },
] as const

export function otaPackageTypeName(type?: number | null): string {
  return OTA_PACKAGE_TYPES.find(t => t.code === type)?.name || '升级包'
}

/** 升级阶段[0:检测,1:命中,2:下载完成,3:下载失败,4:MD5校验失败,5:安装结果,6:启动成功] */
export const OtaPhase = {
  CHECK: 0,
  CHECK_HIT: 1,
  DOWNLOAD_OK: 2,
  DOWNLOAD_FAIL: 3,
  MD5_FAIL: 4,
  INSTALL_RESULT: 5,
  LAUNCH_OK: 6,
} as const

/** 通道[1:测试,2:正式] */
export const OTA_CHANNEL = { TEST: 1, RELEASE: 2 } as const

export function otaChannelName(channel?: number | null): string {
  return channel === OTA_CHANNEL.TEST ? '测试' : '正式'
}

/** 检测入参：一次携带全部类型当前版本，由服务端统一裁决 */
export interface OtaCheckParams {
  deviceIdentification: string
  productIdentification?: string
  /** 设备整机版本号（versions 未携带时作为全部类型的当前版本） */
  deviceVersion?: string
  versions?: Array<{ type: number, version?: string }>
}

/** 单个待升级项（四类包统一返回结构） */
export interface OtaUpgradeItem {
  type: number
  typeName?: string
  pkgId?: number
  name?: string
  /** 目标版本号 */
  version: string
  /** 是否强制升级[0:否,1:是] */
  forceUpdate?: number
  /** 是否关键版本[0:否,1:是]（关键版本不可跳过） */
  mustPass?: number
  downloadUrl?: string
  fileMd5?: string
  fileSize?: number
  fileName?: string
  changelog?: string
  /** 通道[1:测试,2:正式] */
  channel?: number
  publishStrategy?: number
  grayLadder?: number
}

/** 升级上报入参 */
export interface OtaReportParams {
  deviceIdentification: string
  productIdentification?: string
  type: number
  fromVersion?: string
  toVersion: string
  channel?: number
  phase: number
  /** 升级进度（0-100） */
  progress?: number
  /** 是否成功[0:否,1:是] */
  success?: number
  errorCode?: string
  errorMsg?: string
  costMs?: number
}

/** 升级检测：结果由服务端裁决，客户端不挑版本 */
export function checkOtaUpgrade(data: OtaCheckParams) {
  return http.post<OtaUpgradeItem[]>('/ota/check', data, undefined, undefined, { hideErrorToast: true })
}

/** 升级过程上报（灰度健康度依据，服务端幂等落库） */
export function reportOtaUpgrade(data: OtaReportParams) {
  return http.post<boolean>('/ota/report', data, undefined, undefined, { hideErrorToast: true })
}
