export interface BasicPageParams {
  page: number
  count: number
}

export interface BasicFetchResult<T> {
  list: T[]
  total: number
}

export interface StreamInfo {
  code: number
  app: string
  stream: string
  ip: string
  flv: string
  https_flv: string
  ws_flv: string
  wss_flv: string
  fmp4: string
  https_fmp4: string
  ws_fmp4: string
  wss_fmp4: string
  hls: string
  https_hls: string
  ws_hls: string
  wss_hls: string
  ts: string
  https_ts: string
  ws_ts: string
  wss_ts: string
  rtmp: string
  rtmps: string
  rtsp: string
  rtsps: string
  rtc: string
  rtcs: string
  mediaServerId: string
  tracks: Track[]
  startTime: string
  endTime: string
  progress: string
  schema: string
  vhost: string
  aliveSecond: number
  bytesSpeed: number
  totalReaderCount: number
  readerCount: number
  createStamp: number
  isRecordingHLS: boolean
  isRecordingMP4: boolean
  originSock: any
  originTypeStr: string
  originUrl: string
  downLoadFilePath: DownloadFileInfo
}

export interface DownloadFileInfo {
  httpPath: string
  httpsPath: string
  httpDomainPath: string
  httpsDomainPath: string
}

export interface Track {
  channels: number
  codec_id: number
  codec_id_name: string
  codec_type: number
  ready: boolean
  sample_bit: number
  sample_rate: number
  fps: number
  height: number
  width: number
  frames: number
  gop_interval_ms: number
  gop_size: number
  key_frames: number
  loss: number
}
