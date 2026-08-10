from __future__ import annotations

from .models import Device
from .vendors import VENDOR_DAHUA, VENDOR_HIKVISION

ROLE_NVR_HIK = "nvr_hik"
ROLE_NVR_DAHUA = "nvr_dahua"
ROLE_IPC = "ipc"
ROLE_CAMERA = "camera"

ROLE_LABELS: dict[str, str] = {
    ROLE_NVR_HIK: "海康NVR",
    ROLE_NVR_DAHUA: "大华NVR",
    ROLE_IPC: "摄像机",
    ROLE_CAMERA: "摄像机",
}


def role_label(role: str | None) -> str:
    if not role:
        return ""
    return ROLE_LABELS.get(role, role)


def is_nvr_role(role: str | None) -> bool:
    return role in (ROLE_NVR_HIK, ROLE_NVR_DAHUA)


def infer_device_role(device: Device) -> str | None:
    """Classify scanned device as NVR or camera for display and NVR enumeration."""
    if not device.is_recognized:
        return None

    hits = device.evidence.get("fingerprint_hits") or {}
    server = str(hits.get("server") or "").upper()

    if device.vendor == VENDOR_HIKVISION:
        if "DNVRS" in server:
            return ROLE_NVR_HIK
        dt = (device.device_type or "").upper()
        if any(k in dt for k in ("NVR", "DVR", "XVR", "NETWORK VIDEO RECORDER")):
            return ROLE_NVR_HIK
        model = (device.model or "").upper()
        if any(k in model for k in ("-NVR", "NVR-", "DS-77", "DS-86", "DS-96")):
            if "IPC" not in model and "CD" not in model[:6]:
                return ROLE_NVR_HIK
        return ROLE_IPC

    if device.vendor == VENDOR_DAHUA:
        dc = str(device.evidence.get("dahua_device_class") or "").upper()
        if dc in ("NVR", "DVR", "XVR", "HCVR", "SDVR"):
            return ROLE_NVR_DAHUA
        dt = (device.device_type or "").upper()
        if any(k in dt for k in ("NVR", "DVR", "XVR", "HCVR")):
            return ROLE_NVR_DAHUA
        model = (device.model or "").upper()
        if any(k in model for k in ("NVR", "XVR", "DVR", "HCVR")):
            return ROLE_NVR_DAHUA
        return ROLE_IPC

    return ROLE_CAMERA
