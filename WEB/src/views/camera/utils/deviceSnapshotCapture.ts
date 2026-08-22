import { captureDeviceSnapshot } from '@/api/device/device_detection_region';
import type { DeviceInfo } from '@/api/device/camera';
import {
  getSnapshotCapturePolicy,
  isGb28181Device,
  sleep,
  verifySnapshotQuality,
} from './snapshotQuality';

export interface SnapshotCaptureResult {
  ok: boolean;
  imageId?: number;
  imageUrl?: string;
  isGrey?: boolean;
  isGb?: boolean;
}

export interface CaptureSnapshotOptions {
  silent?: boolean;
  force?: boolean;
  /** 跳过 GB 预热等待（刷新/重试时使用） */
  skipPreWait?: boolean;
  device?: Pick<DeviceInfo, 'id' | 'name' | 'source' | 'device_kind'> | null;
}

/**
 * 带质量校验的抓图：GB28181 设备预热等待 + 灰图重试
 */
export async function captureSnapshotWithQuality(
  deviceId: string,
  options: CaptureSnapshotOptions = {},
): Promise<SnapshotCaptureResult> {
  const device = options.device ?? { id: deviceId };
  const policy = getSnapshotCapturePolicy(device);
  const isGb = isGb28181Device(device);

  if (policy.preCaptureWaitMs > 0 && !options.skipPreWait) {
    await sleep(policy.preCaptureWaitMs);
  }

  for (let attempt = 0; attempt < policy.maxRetries; attempt++) {
    if (attempt > 0) {
      await sleep(policy.retryGapMs);
    }

    try {
      const response = await captureDeviceSnapshot(deviceId);
      const result = (response as any)?.data || response;
      if (result?.code !== 0 || !result?.data?.image_url) {
        continue;
      }

      if (policy.postCaptureWaitMs > 0) {
        await sleep(policy.postCaptureWaitMs);
      }

      const quality = await verifySnapshotQuality(result.data.image_url, { bustCache: true });
      if (quality.loadable && quality.valid) {
        return {
          ok: true,
          imageId: result.data.image_id,
          imageUrl: result.data.image_url,
          isGb,
        };
      }
    } catch {
      // 继续重试
    }
  }

  return { ok: false, isGb, isGrey: true };
}
