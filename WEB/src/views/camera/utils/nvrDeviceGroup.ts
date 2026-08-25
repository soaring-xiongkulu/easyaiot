import type { DeviceInfo, NvrInfo } from '@/api/device/camera';
import { getDeviceList, getNvrList } from '@/api/device/camera';
import { formatNvrDisplayName, isNvrChannelDevice, isNvrListRow } from './deviceLabel';

export type { NvrInfo };

export interface NvrCardItem {
  nvrId: number;
  name: string;
  ip: string;
  port: number;
  vendor_label?: string;
  model?: string;
  rtsp_url?: string;
  camera_count: number;
  _nvr: NvrInfo;
}

/** 未挂载到 NVR 的直连设备（顶层卡片/表格行） */
export function filterStandaloneDirectDevices(
  devices: DeviceInfo[],
  nvrs?: NvrInfo[],
): DeviceInfo[] {
  const nvrBrief = nvrs?.map((n) => ({ id: n.id, ip: n.ip }));
  return devices.filter((d) => !isNvrChannelDevice(d, nvrBrief) && !isNvrListRow(d));
}

export function nvrToCardItem(nvr: NvrInfo): NvrCardItem {
  return {
    nvrId: nvr.id!,
    name: formatNvrDisplayName(nvr),
    ip: nvr.ip,
    port: nvr.port ?? 80,
    vendor_label: nvr.vendor_label,
    model: nvr.model,
    rtsp_url: nvr.rtsp_url,
    camera_count: nvr.camera_count ?? nvr.cameras?.length ?? 0,
    _nvr: nvr,
  };
}

export function nvrToTableRow(nvr: NvrInfo): DeviceInfo & { _isNvr: boolean; nvr_id_num: number } {
  return {
    id: `nvr_${nvr.id}`,
    name: formatNvrDisplayName(nvr),
    device_kind: 'nvr',
    nvr_id_num: nvr.id!,
    ip: nvr.ip,
    port: nvr.port ?? 80,
    model: nvr.model ?? '-',
    manufacturer: nvr.vendor_label || nvr.vendor || 'NVR',
    source: nvr.rtsp_url || '',
    online: true,
    channel_count: nvr.camera_count ?? 0,
    ingress_node_id: nvr.ingress_node_id,
    ingress_node_name: nvr.ingress_node_name,
    ingress_node_host: nvr.ingress_node_host,
    ingress_node_status: nvr.ingress_node_status,
    _isNvr: true,
  } as DeviceInfo & { _isNvr: boolean; nvr_id_num: number };
}

export type DeviceListDisplayItem =
  | { kind: 'direct'; device: DeviceInfo }
  | { kind: 'gb_sip'; gbItem: Record<string, unknown> }
  | { kind: 'nvr'; nvrItem: NvrCardItem };

/** @param includeCameras 为 true 时拉取每路挂载通道（较重，仅 NVR 详情等场景使用） */
export async function fetchNvrList(includeCameras = true): Promise<NvrInfo[]> {
  try {
    const res = await getNvrList(includeCameras);
    return Array.isArray(res) ? res : (res as { data?: NvrInfo[] })?.data ?? [];
  } catch {
    return [];
  }
}

/** 监控树/卡片列表仅需 NVR 元数据，避免 includeCameras 拖垮首屏 */
export function fetchNvrListBrief(): Promise<NvrInfo[]> {
  return fetchNvrList(false);
}

/** 设备目录表格：NVR 通道挂到 NVR 父行下（Ant Design Table children） */
export function buildDirectoryDeviceTableRows(
  devices: DeviceInfo[],
  nvrs: NvrInfo[] = [],
): DeviceInfo[] {
  const nvrMap = new Map(nvrs.filter((n) => n.id).map((n) => [n.id!, n]));
  const standalone: DeviceInfo[] = [];
  const byNvr = new Map<number, DeviceInfo[]>();

  for (const d of devices) {
    if (isNvrChannelDevice(d) && d.nvr_id) {
      const list = byNvr.get(d.nvr_id) || [];
      list.push(d);
      byNvr.set(d.nvr_id, list);
    } else {
      standalone.push(d);
    }
  }

  const result: DeviceInfo[] = [...standalone];
  const sortedNvrIds = [...byNvr.keys()].sort((a, b) => a - b);
  for (const nvrId of sortedNvrIds) {
    const channels = byNvr.get(nvrId)!;
    channels.sort((a, b) => (a.nvr_channel ?? 0) - (b.nvr_channel ?? 0));
    const nvr = nvrMap.get(nvrId);
    result.push({
      id: `nvr_group_${nvrId}`,
      name: formatNvrDisplayName(nvr || { id: nvrId, ip: `NVR-${nvrId}` }),
      device_kind: 'nvr',
      ip: nvr?.ip ?? '-',
      port: nvr?.port ?? 80,
      manufacturer: nvr?.vendor_label || nvr?.vendor || 'NVR',
      model: nvr?.model ?? '-',
      online: true,
      channel_count: channels.length,
      children: channels,
      _isNvrGroup: true,
    } as DeviceInfo & { _isNvrGroup: boolean; children: DeviceInfo[] });
  }
  return result;
}

export function buildCardRowsWithNvr(
  devices: DeviceInfo[],
  nvrs: NvrInfo[],
  gbItems: DeviceListDisplayItem[] = [],
): DeviceListDisplayItem[] {
  const items: DeviceListDisplayItem[] = filterStandaloneDirectDevices(devices, nvrs).map((device) => ({
    kind: 'direct' as const,
    device,
  }));
  for (const nvr of nvrs) {
    if (nvr.id) {
      items.push({ kind: 'nvr' as const, nvrItem: nvrToCardItem(nvr) });
    }
  }
  for (const g of gbItems) {
    if (g.kind === 'gb_sip') items.push(g);
  }
  return items;
}
