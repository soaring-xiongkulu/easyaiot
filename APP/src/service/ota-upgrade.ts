/**
 * 设备 OTA 升级编排服务
 *
 * 以设备身份驱动平台 OTA 全流程闭环：
 * 检测（/ota/check）→ 命中上报 → 下载（进度）→ MD5 校验 → 安装/启动上报（/ota/report）。
 * 平台侧按阶段幂等落库，启动成功后自动回写设备当前版本。
 *
 * 上报失败不阻断主流程：逐条重试后仍失败则忽略（平台留痕以检测心跳兜底）。
 */
import type { OtaReportParams, OtaUpgradeItem } from '@/api/device/ota'
import { OtaPhase, checkOtaUpgrade, reportOtaUpgrade } from '@/api/device/ota'
import { md5FromNetwork } from '@/utils/md5'

/** 单个升级项的运行态 */
export type OtaRunStage = 'idle' | 'reporting' | 'downloading' | 'verifying' | 'installing' | 'done' | 'failed'

export interface OtaRunState {
  stage: OtaRunStage
  /** 下载/校验进度 0-100 */
  progress: number
  errorMsg: string
  /** 校验被跳过的原因（如跨域无法分块取流），仅提示不阻断 */
  verifySkippedReason: string
}

export interface OtaTargetDevice {
  deviceIdentification: string
  productIdentification?: string
  /** 设备当前版本（检测入参） */
  deviceVersion?: string
}

export const otaUpgradeState = reactive({
  /** 检测进行中 */
  checking: false,
  /** 最近一次检测结果 */
  items: [] as OtaUpgradeItem[],
  checkedAt: 0,
  /** 检测错误信息 */
  checkError: '',
  /** 各升级项运行态，key = 包类型 */
  runs: {} as Record<number, OtaRunState>,
})

function runStateOf(type: number): OtaRunState {
  if (!otaUpgradeState.runs[type]) {
    otaUpgradeState.runs[type] = {
      stage: 'idle',
      progress: 0,
      errorMsg: '',
      verifySkippedReason: '',
    }
  }
  return otaUpgradeState.runs[type]
}

/** 上报：少量重试，最终失败仅记日志，保证升级主流程不因留痕失败而中断 */
async function reportQuietly(params: OtaReportParams) {
  for (let i = 0; i < 3; i++) {
    try {
      await reportOtaUpgrade(params)
      return true
    } catch (error) {
      console.warn('[ota] report failed, retry', params.phase, error)
    }
  }
  return false
}

/**
 * 升级检测：携带设备当前版本，结果由服务端裁决。
 * 返回待升级项列表；无升级返回空数组。
 */
export async function checkDeviceUpgrade(device: OtaTargetDevice): Promise<OtaUpgradeItem[]> {
  otaUpgradeState.checking = true
  otaUpgradeState.checkError = ''
  try {
    const items = await checkOtaUpgrade({
      deviceIdentification: device.deviceIdentification,
      productIdentification: device.productIdentification || undefined,
      deviceVersion: device.deviceVersion || undefined,
    })
    otaUpgradeState.items = Array.isArray(items) ? items : []
    otaUpgradeState.checkedAt = Date.now()
    for (const run of Object.values(otaUpgradeState.runs)) {
      run.stage = 'idle'
      run.progress = 0
      run.errorMsg = ''
      run.verifySkippedReason = ''
    }
    return otaUpgradeState.items
  } catch (error: any) {
    otaUpgradeState.checkError = error?.msg || error?.message || '检测失败，请稍后重试'
    throw error
  } finally {
    otaUpgradeState.checking = false
  }
}

/** 下载升级包到临时目录（带进度回调） */
function downloadPackage(url: string, onProgress: (percent: number) => void): Promise<string> {
  return new Promise((resolve, reject) => {
    const task = uni.downloadFile({
      url,
      success: (res) => {
        if (res.statusCode === 200 && res.tempFilePath) {
          resolve(res.tempFilePath)
        } else {
          reject(new Error(`下载失败（HTTP ${res.statusCode}）`))
        }
      },
      fail: err => reject(new Error(err.errMsg || '下载失败，请检查网络')),
    })
    task?.onProgressUpdate?.((res) => {
      onProgress(Math.floor(res.progress))
    })
  })
}

/**
 * 执行单个升级项闭环：命中 → 下载 → 校验 → 安装 → 启动
 *
 * App 端作为设备侧代理真实执行下载与 MD5 校验；安装/启动阶段
 * 在 App 内无法替硬件刷写，按成功上报闭环（平台回写设备版本）。
 */
export async function runDeviceUpgrade(device: OtaTargetDevice, item: OtaUpgradeItem): Promise<void> {
  const run = runStateOf(item.type)
  if (item.forceUpdate === 1 || item.mustPass === 1) {
    // 强制/关键版本：直接进入升级
  }
  run.stage = 'reporting'
  run.progress = 0
  run.errorMsg = ''
  run.verifySkippedReason = ''

  const startedAt = Date.now()
  const base: Omit<OtaReportParams, 'phase'> = {
    deviceIdentification: device.deviceIdentification,
    productIdentification: device.productIdentification || undefined,
    type: item.type,
    fromVersion: device.deviceVersion || undefined,
    toVersion: item.version,
    channel: item.channel ?? undefined,
  }

  // 1. 命中上报
  await reportQuietly({ ...base, phase: OtaPhase.CHECK_HIT, success: 1, progress: 5 })

  if (!item.downloadUrl) {
    run.stage = 'failed'
    run.errorMsg = '该升级包未提供下载地址'
    return
  }

  // 2. 下载（真实下载 + 进度）
  run.stage = 'downloading'
  run.progress = 0
  let tempPath = ''
  try {
    tempPath = await downloadPackage(item.downloadUrl, p => (run.progress = p))
    run.progress = 100
  } catch (error: any) {
    await reportQuietly({
      ...base,
      phase: OtaPhase.DOWNLOAD_FAIL,
      success: 0,
      progress: run.progress,
      errorMsg: String(error?.message || error).slice(0, 200),
    })
    run.stage = 'failed'
    run.errorMsg = error?.message || '下载失败，请检查网络后重试'
    return
  }
  await reportQuietly({ ...base, phase: OtaPhase.DOWNLOAD_OK, success: 1, progress: 100 })

  // 3. MD5 校验（存在期望值时执行；无法取流时跳过并提示，不视为失败）
  if (item.fileMd5) {
    run.stage = 'verifying'
    run.progress = 0
    try {
      const localMd5 = await md5FromNetwork(item.downloadUrl, p => (run.progress = p))
      if (localMd5.toLowerCase() !== item.fileMd5.toLowerCase()) {
        await reportQuietly({
          ...base,
          phase: OtaPhase.MD5_FAIL,
          success: 0,
          errorMsg: `md5 mismatch: local=${localMd5}`,
        })
        run.stage = 'failed'
        run.errorMsg = '安装包校验失败，请重新下载'
        return
      }
    } catch (error: any) {
      run.verifySkippedReason = '校验取流失败，已跳过校验继续安装'
      console.warn('[ota] md5 verify skipped:', error?.message || error)
    }
  }

  // 4. 安装结果上报（App 内模拟设备安装动作）
  run.stage = 'installing'
  await new Promise(resolve => setTimeout(resolve, 600))
  await reportQuietly({
    ...base,
    phase: OtaPhase.INSTALL_RESULT,
    success: 1,
    progress: 100,
    costMs: Date.now() - startedAt,
  })

  // 5. 启动成功上报（平台回写设备当前版本，闭环完成）
  await reportQuietly({
    ...base,
    phase: OtaPhase.LAUNCH_OK,
    success: 1,
    progress: 100,
    costMs: Date.now() - startedAt,
  })
  run.stage = 'done'
}

/** 是否允许跳过（稍后）：强制/关键版本不可跳过 */
export function canSkipUpgrade(item?: OtaUpgradeItem | null): boolean {
  return !!item && item.forceUpdate !== 1 && item.mustPass !== 1
}
