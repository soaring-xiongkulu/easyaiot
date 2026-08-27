/**
 * App 控制面板模板（云端定制产品级控制页）
 *
 * 云端在 WEB 管理端为每个产品设计控制页面模板并发布，
 * App 打开设备控制台时按产品标识拉取已发布模板，动态渲染出控制页。
 */
import type { IResponse } from '@/http/types'
import { http } from '@/http/http'

/** 面板组件类型 */
export type PanelWidgetType
  = | 'switch' // 开关
    | 'slider' // 滑条
    | 'number' // 步进器
    | 'status' // 状态标签
    | 'text' // 数值文本
    | 'button' // 命令按钮
    | 'video' // 实时画面
    | 'chart' // 折线图（实时采样曲线）
    | 'gauge' // 仪表盘
    | 'progress' // 进度条

export interface PanelWidgetOption {
  label: string
  value: string | number
  color?: string
}

export interface PanelWidgetConfig {
  min?: number
  max?: number
  step?: number
  unit?: string
  options?: PanelWidgetOption[]
  /** button：是否需要二次确认 */
  confirm?: boolean
  /** chart：曲线颜色 / gauge / progress 主色 */
  color?: string
  /** chart：采样点数量（默认 20） */
  maxPoints?: number
}

export interface PanelWidget {
  id: string
  type: PanelWidgetType
  title: string
  /** full-整行 half-半行，默认整行 */
  span?: 'full' | 'half'
  /** 读/写的物模型属性标识符 */
  propertyCode?: string
  /** 命令按钮下发的服务标识符 */
  serviceId?: string
  config?: PanelWidgetConfig
}

export interface PanelTemplatePage {
  name: string
  layout?: string
  widgets: PanelWidget[]
}

/** 云端模板实体（panelSchema 为 JSON 字符串） */
export interface AppPanelTemplate {
  id: number
  templateCode: string
  templateName: string
  productIdentification?: string
  status?: string
  version?: number
  panelSchema?: string
}

export interface IotDeviceItem {
  id: number
  deviceName?: string
  deviceIdentification?: string
  productName?: string
  productIdentification?: string
  connectStatus?: string
  deviceStatus?: string
  /** 设备当前固件/软件版本（OTA 检测入参） */
  deviceVersion?: string
  deviceSn?: string
  ipAddress?: string
  /** 子设备挂载的网关标识，非空即为子设备 */
  parentIdentification?: string
  deviceType?: string
  lastOnlineTime?: string
  activeStatus?: number
  deviceDescription?: string
}

export interface IotDeviceStatusCount {
  onlineCount: number
  offlineCount: number
  initCount: number
}

/** 设备在线状态归一化：ONLINE 在线 / OFFLINE 离线 / 其余未激活 */
export function normalizeConnectStatus(status?: string): 'online' | 'offline' | 'inactive' {
  const s = (status || '').toUpperCase()
  if (s === 'ONLINE')
    return 'online'
  if (s === 'OFFLINE')
    return 'offline'
  return 'inactive'
}

/** 解析模板 JSON；非法或缺省时返回 null */
export function parsePanelTemplate(template?: AppPanelTemplate | null): PanelTemplatePage[] {
  if (!template?.panelSchema)
    return []
  try {
    const schema = typeof template.panelSchema === 'string'
      ? JSON.parse(template.panelSchema)
      : template.panelSchema
    const pages: PanelTemplatePage[] = Array.isArray(schema?.pages) ? schema.pages : []
    return pages.filter(page => Array.isArray(page?.widgets))
  }
  catch {
    return []
  }
}

/** 拉取产品当前生效的已发布模板；未配置返回 null */
export async function getPublishedPanelByProduct(productIdentification: string): Promise<AppPanelTemplate | null> {
  if (!productIdentification)
    return null
  try {
    return await http.get<AppPanelTemplate | null>('/appPanelTemplate/get-by-product', { productIdentification })
  }
  catch {
    return null
  }
}

/** IoT 设备分页列表（设备控制台入口） */
export async function getIotDevicePage(params: { pageNum?: number, pageSize?: number, deviceName?: string }):
  Promise<{ list: IotDeviceItem[], total: number }> {
  const res = await http.get<IResponse<IotDeviceItem[]>>('/device/list', params, undefined, { original: true })
  const rows = res?.data ?? (res as any)?.rows ?? []
  return { list: rows, total: Number(res?.total ?? 0) }
}

/** 各连接状态设备数量（/device/listStatusCount） */
export async function getIotDeviceStatusCount(): Promise<IotDeviceStatusCount> {
  try {
    const data = await http.get<Partial<IotDeviceStatusCount>>('/device/listStatusCount')
    return {
      onlineCount: Number(data?.onlineCount ?? 0),
      offlineCount: Number(data?.offlineCount ?? 0),
      initCount: Number(data?.initCount ?? 0),
    }
  } catch {
    return { onlineCount: 0, offlineCount: 0, initCount: 0 }
  }
}

export interface IotProductItem {
  id?: number
  productId?: number
  productName?: string
  productIdentification?: string
  productImg?: string
}

/** 产品标识 → 产品信息映射（设备卡片展示产品名/图标用） */
export async function getProductNameMap(): Promise<Map<string, IotProductItem>> {
  const map = new Map<string, IotProductItem>()
  try {
    const res = await http.get<IResponse<IotProductItem[]>>('/product/list', { pageNum: 1, pageSize: 200 }, undefined, { original: true })
    const rows = res?.data ?? (res as any)?.rows ?? []
    for (const row of rows) {
      if (row?.productIdentification) {
        map.set(row.productIdentification, row)
      }
    }
  } catch {
    // 拉取失败时退化：卡片直接展示产品标识
  }
  return map
}

/** 物模型属性元数据（属性展示名/单位） */
export interface ThingPropertyMeta {
  propertyCode: string
  propertyName?: string
  datatype?: string
  unit?: string
}

/** 按产品拉取物模型属性元数据，code → meta 映射 */
export async function getPropertyMetaMap(productIdentification: string): Promise<Map<string, ThingPropertyMeta>> {
  const map = new Map<string, ThingPropertyMeta>()
  if (!productIdentification) {
    return map
  }
  try {
    const res = await http.get<IResponse<ThingPropertyMeta[]>>(
      '/productProperties/list',
      { productIdentification, pageNum: 1, pageSize: 200 },
      undefined,
      { original: true },
    )
    const rows = res?.data ?? (res as any)?.rows ?? []
    for (const row of rows) {
      if (row?.propertyCode) {
        map.set(row.propertyCode, row)
      }
    }
  } catch {
    // 拉取失败时退化：属性名直接展示 code
  }
  return map
}

/** 按产品标识 + 设备标识查询设备详情（含版本/SN/最后上线时间等全量字段） */
export async function getDeviceByIdentification(productIdentification: string, deviceIdentification: string): Promise<IotDeviceItem | null> {
  if (!productIdentification || !deviceIdentification) {
    return null
  }
  try {
    return await http.get<IotDeviceItem>(
      `/device/selectByProductIdentificationAndDeviceIdentification/${encodeURIComponent(productIdentification)}/${encodeURIComponent(deviceIdentification)}`,
    )
  } catch {
    return null
  }
}

export interface DeviceShadowResult {
  reported: Record<string, any>
  desired: Record<string, any>
  connectStatus?: string
}

/** 读取设备影子（reported 属性最新值） */
export async function getDeviceShadow(deviceId: number | string): Promise<DeviceShadowResult> {
  const empty = { reported: {}, desired: {} } as DeviceShadowResult
  try {
    const data = await http.get<any>(`/shadow/${deviceId}`)
    return {
      reported: data?.reported ?? {},
      desired: data?.desired ?? {},
      connectStatus: data?.connectStatus,
    }
  }
  catch {
    return empty
  }
}

/** IoT 设备关联的流媒体摄像头（video 服务摄像头 id） */
export async function getLinkedCameraIds(iotDeviceId: number | string): Promise<string[]> {
  try {
    interface CameraLinkRow {
      id: number
      iotDeviceId: number
      cameraDeviceId: string
    }
    const res = await http.get<IResponse<CameraLinkRow[]>>(
      '/device/cameraLinks',
      { iotDeviceId },
      undefined,
      { original: true },
    )
    const rows = res?.data ?? (res as any)?.rows ?? []
    return rows.map(r => r.cameraDeviceId).filter(Boolean)
  }
  catch {
    return []
  }
}

export interface IssueCommandParams {
  deviceIdentification: string
  productIdentification: string
  serviceCode: string
  commandName?: string
  commandCode?: string
  params?: Record<string, any>
}

/** 下发服务命令（走平台统一 issueCommands 下行链路） */
export async function issueDeviceCommand(p: IssueCommandParams): Promise<void> {
  const request = {
    deviceIdentification: p.deviceIdentification,
    productIdentification: p.productIdentification,
    msgType: 'SERVICE_INVOKE',
    serviceCode: p.serviceCode,
    commandName: p.commandName || p.serviceCode,
    commandCode: p.commandCode || p.serviceCode,
    params: p.params ?? {},
  }
  await http.post('/deviceCommand/issueCommands', { serial: [{ commandIssueRequestParamVo: request }] }, undefined, undefined, { hideErrorToast: false })
}
