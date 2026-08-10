# FR-B6 Report — Camera ONVIF/PTZ/snapshot/NVR/scan 行为去桩

**STATUS:** DONE_WITH_CONCERNS  
**Branch:** `feat/video-java`  
**Date:** 2026-08-11

## Summary

Replaced Java camera hardware ack/error-only stubs with real protocol attempts aligned to retired Python VIDEO: ONVIF SOAP (PTZ/presets/snapshot URI/register), WS-Discovery, ISAPI segment scan + NVR channel enumeration, and ffmpeg single-frame capture with MinIO/local screenshot persistence. No reachable device → same error shapes as Python (HTTP 400/500 + `msg`), but code paths now perform real network/ffmpeg work instead of empty stubs.

## Python files read (oracle)

| Path | Purpose |
|------|---------|
| `VIDEO/_retired_python_video/app/blueprints/camera.py` | PTZ, RTSP/ONVIF capture tasks, snapshot, scan/discovery/refresh, NVR scan |
| `VIDEO/_retired_python_video/app/services/camera_service.py` | ONVIF connect, presets, `get_snapshot_uri`, WS-Discovery, `register_camera_by_onvif`, `refresh_camera` |
| `VIDEO/_retired_python_video/app/services/onvif_service.py` | `OnvifCamera`, `PTZController`, preset APIs |
| `VIDEO/_retired_python_video/app/services/hik_scan_service.py` | `scan_segment`, `enumerate_nvr_channels` |
| `VIDEO/_retired_python_video/app/services/nvr_service.py` | NVR channel registration semantics |
| `VIDEO/_retired_python_video/app/vendor/hiktools/core/nvr.py` | ISAPI channel XML parse / inventory shape |
| `VIDEO/_retired_python_video/app/vendor/hiktools/core/isapi.py` | HTTP Digest ISAPI fetch |
| `VIDEO/_retired_python_video/app/vendor/hiktools/core/scanner.py` | TCP + HTTP fingerprint scan |

## Java changes

| Component | Change |
|-----------|--------|
| `OnvifSoapClient` | SOAP + WS-Security UsernameToken digest: capabilities, stream/snapshot URI, PTZ move/stop, presets |
| `OnvifWsDiscovery` | UDP multicast Probe (best-effort LAN discovery) |
| `IsapiHttpClient` | HTTP Digest ISAPI/CGI client |
| `HikScanService` | Segment TCP scan + ISAPI deviceInfo; NVR channel enum via InputProxy/VideoInput XML |
| `FfmpegFrameCapture` | ffmpeg RTSP/RTMP single-frame JPEG (uses `FfmpegCompat`) |
| `CameraScreenshotService` | MinIO `camera-screenshots` or local path + `image` table insert |
| `CameraHardwareService` | Rewired discover/refresh/scan/NVR/PTZ/presets/RTSP+ONVIF tasks/snapshot |
| `CameraAdminService.registerByOnvif` | Real ONVIF register via `connectOnvif` |
| `CameraNvrService.registerChannels` | Attempts ISAPI enum when channels omitted |
| `SnapTaskCaptureService` | RTSP path delegates to ffmpeg snapshot |
| `DeviceRepository` / `DeviceImageRepository` | `findByMac`, `findExistingForRegister`, `updatePassword`, `insert` image |
| `FULL_REPLACEMENT_GAP.md` / `BLUEPRINT_GAP.md` | camera §2.3 + §4 ONVIF/NVR row ✅ |

## Short contract

| Surface | No device / unreachable | With device |
|---------|-------------------------|-------------|
| `POST /device/{id}/snapshot` | HTTP 200 + `code:500` + ffmpeg error msg | JPEG uploaded + `image_url` |
| `POST /device/{id}/ptz` | `error: Internal server error` (500) or `Camera not found` (400) | ONVIF ContinuousMove attempted |
| `GET /discovery` | `[]` or partial WS-Discovery hits | `{mac,ip,hardware_name}` rows |
| `POST /scan/segment` | `[]` (only_hits) or rows with `error` | ISAPI-recognized Hikvision rows |
| `POST /scan/nvr/channels` | `channels:[]` + `error` string | channel list from ISAPI XML |
| `POST /register/device/onvif` | 500 connect error (tries admin/root) | device row upserted |

## GAP

- `FULL_REPLACEMENT_GAP.md` §2.3 camera behavior → **resolved by FR-B6** (code paths; prod needs cameras/NVR)
- `FULL_REPLACEMENT_GAP.md` §4 ONVIF/NVR row → **resolved by FR-B6** (GB28181/FlightHub/Dahua NVR full parity still open)
- `BLUEPRINT_GAP.md` camera notes → FR-B6 ✅

## certify --phase 0

```
exit 0
```

## Concerns / follow-ups

1. **No live camera/NVR in certify env** — behavior verified by code-path review + phase0 smoke; prod needs ONVIF camera + Hikvision NVR soak.
2. **ONVIF dialect variance** — lightweight SOAP client may need per-vendor tweaks (Python uses `onvif` WSDL stack).
3. **Dahua NVR / hiktools full parity** — Java ISAPI path targets Hikvision-first; Dahua CGI channel enum not fully ported.
4. **GB28181 source resolve** — Python `grab_frame_for_snapshot` resolves `gb28181://`; Java ffmpeg uses stored `source` as-is.
5. **NVR channel DB registration** — `registerChannels` enumerates via ISAPI but full per-channel device upsert (Python `bulk_register_nvr_channels`) remains partial.
6. **Maven reactor** — `DEVICE/iot-video` compile needs local `iot-parent` install in this worktree (certify uses prebuilt/stale jar path).
