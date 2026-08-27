import {
  resolveAlertRecordVideoUrl,
  resolveAlertVideoUrl,
  type AlertRecordLike,
} from '@/utils/alertRecord';
import { useMessage } from '@/hooks/web/useMessage';

const { createMessage } = useMessage();
const PLAYBACK_LOADING_KEY = 'alert-record-playback';

export type AlertRecordModalMethods = {
  openModal: (open?: boolean, data?: any, openOnSet?: boolean) => void;
  closeModal?: () => void;
  setModalProps?: (props: Record<string, any>) => void;
};

export type AlertRecordPlayInput = AlertRecordLike & {
  device_id?: string | number;
  time?: string;
  video_url?: string | null;
  url?: string | null;
};

/** 每次播放递增，避免 useModal 在快速连续 openModal 时合并/跳过回调 */
let playbackSeq = 0;

function buildModalPayload(
  deviceId: string | number,
  videoUrl: string,
  seq: number,
  pending: boolean,
) {
  return {
    id: deviceId,
    http_stream: videoUrl,
    // This payload is created only for an alert recording.  Keep an explicit
    // mode marker so modal layout does not depend solely on URL heuristics.
    _forceVod: true as const,
    ...(pending ? { _pendingRecord: true as const } : {}),
    _playbackSeq: seq,
  };
}

/** 打开录像弹框前先设置布局，避免首次打开闪退 */
export function prepareAlertRecordModalShell(
  setModalProps?: (props: Record<string, any>) => void,
) {
  setModalProps?.({
    defaultFullscreen: false,
    canFullscreen: false,
    width: 1000,
    title: '录像回放',
    minHeight: 0,
    bodyStyle: { padding: 0 },
    wrapClassName: 'monitor-dialog-wrap monitor-dialog-wrap--vod',
  });
}

/**
 * 在大屏/告警等场景打开告警录像：先解析地址，确认有录像后再打开播放器。
 * mini / standard / full 共用，兼容 MinIO 直链与按设备+时间查询。
 */
export async function playAlertRecordInModal(
  modal: AlertRecordModalMethods,
  record: AlertRecordPlayInput,
): Promise<boolean> {
  const { openModal, setModalProps } = modal;
  const seq = ++playbackSeq;

  const directRaw = record.video_url || record.url;
  if (directRaw) {
    const videoUrl = resolveAlertVideoUrl(String(directRaw).trim());
    if (videoUrl) {
      prepareAlertRecordModalShell(setModalProps);
      openModal(true, buildModalPayload(record.device_id ?? 0, videoUrl, seq, false));
      return true;
    }
  }

  const deviceId = record.device_id;
  if (deviceId == null || deviceId === '' || !record.time) {
    return false;
  }

  createMessage.loading({ content: '正在查询告警录像...', key: PLAYBACK_LOADING_KEY, duration: 0 });

  try {
    const videoUrl = await resolveAlertRecordVideoUrl(record);
    createMessage.destroy(PLAYBACK_LOADING_KEY);
    if (videoUrl) {
      prepareAlertRecordModalShell(setModalProps);
      openModal(true, buildModalPayload(deviceId, videoUrl, seq, false));
      return true;
    }
    return false;
  } catch (error) {
    createMessage.destroy(PLAYBACK_LOADING_KEY);
    throw error;
  }
}
