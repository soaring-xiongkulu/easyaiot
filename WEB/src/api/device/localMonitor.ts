import { defHttp } from '@/utils/http/axios';

export interface LocalMonitorMetrics {
  collectedAt: string;
  host: {
    hostname: string;
    platform: string;
    release: string;
    architecture: string;
    uptimeSec: number;
    bootAt: string;
  };
  cpu: {
    percent: number;
    logicalCores: number;
    physicalCores: number;
    load1: number;
    load5: number;
    load15: number;
  };
  memory: {
    percent: number;
    usedBytes: number;
    availableBytes: number;
    totalBytes: number;
    swapPercent: number;
  };
  disk: {
    path: string;
    percent: number;
    usedBytes: number;
    freeBytes: number;
    totalBytes: number;
  };
  network: {
    rxBytes: number;
    txBytes: number;
    rxBytesPerSec: number;
    txBytesPerSec: number;
    packetsReceived: number;
    packetsSent: number;
  };
  temperatureC: number | null;
  process: {
    pid: number;
    rssBytes: number;
    threads: number;
    processCount: number;
  };
  runtime: {
    target: 'auto' | 'generic' | 'rk3588' | string;
    ready: boolean;
    version?: string | null;
    binPath?: string | null;
    enabledTasks: number;
    runningTasks: number;
    runningStreams: number;
  };
}

export function getLocalMonitorMetrics() {
  return defHttp.get<LocalMonitorMetrics>({
    url: '/video/local-monitor/metrics',
    headers: { ignoreCancelToken: true },
  });
}
