from __future__ import annotations

VENDOR_HIKVISION = "hikvision"
VENDOR_DAHUA = "dahua"
VENDOR_HUAWEI = "huawei"
VENDOR_EZVIZ = "ezviz"
VENDOR_XIAOMI = "xiaomi"
VENDOR_UNIVIEW = "uniview"
VENDOR_TIANDY = "tiandy"
VENDOR_LANPARTIX = "lanpartix"
VENDOR_JOVISION = "jovision"
VENDOR_TP_LINK = "tp_link"
VENDOR_TVT = "tvt"
VENDOR_CUSTOM = "custom"

VENDOR_LABELS: dict[str, str] = {
    VENDOR_HIKVISION: "海康",
    VENDOR_DAHUA: "大华",
    VENDOR_HUAWEI: "华为",
    VENDOR_EZVIZ: "萤石",
    VENDOR_XIAOMI: "小米",
    VENDOR_UNIVIEW: "宇视",
    VENDOR_TIANDY: "天地伟业",
    VENDOR_LANPARTIX: "中维世纪",
    VENDOR_JOVISION: "中维世纪",
    VENDOR_TP_LINK: "TP-Link",
    VENDOR_TVT: "天视通",
    VENDOR_CUSTOM: "自定义",
}

ALL_VENDORS: tuple[str, ...] = tuple(VENDOR_LABELS.keys())

_VENDOR_ALIASES: dict[str, str] = {
    "海康": VENDOR_HIKVISION,
    "海康威视": VENDOR_HIKVISION,
    "大华": VENDOR_DAHUA,
    "华为": VENDOR_HUAWEI,
    "萤石": VENDOR_EZVIZ,
    "小米": VENDOR_XIAOMI,
    "宇视": VENDOR_UNIVIEW,
    "天地伟业": VENDOR_TIANDY,
    "中维世纪": VENDOR_LANPARTIX,
    "tp-link": VENDOR_TP_LINK,
    "tplink": VENDOR_TP_LINK,
    "天视通": VENDOR_TVT,
}


def normalize_vendor(vendor: str | None) -> str | None:
    if not vendor:
        return None
    v = vendor.strip().lower()
    if v in VENDOR_LABELS:
        return v
    if v in _VENDOR_ALIASES:
        return _VENDOR_ALIASES[v]
    alias = _VENDOR_ALIASES.get(vendor.strip())
    if alias:
        return alias
    return v


def vendor_label(vendor: str | None) -> str:
    if not vendor:
        return ""
    normalized = normalize_vendor(vendor) or vendor
    return VENDOR_LABELS.get(normalized, vendor)


def vendor_flag(vendor: str | None) -> str:
    """Short tag for CLI table output."""
    if not vendor:
        return "---"
    normalized = normalize_vendor(vendor) or vendor
    return {
        VENDOR_HIKVISION: "HIK",
        VENDOR_DAHUA: "DAH",
        VENDOR_HUAWEI: "HW ",
        VENDOR_EZVIZ: "YS ",
        VENDOR_XIAOMI: "MI ",
        VENDOR_UNIVIEW: "UNV",
        VENDOR_TIANDY: "TDY",
        VENDOR_LANPARTIX: "JVS",
        VENDOR_TP_LINK: "TPL",
        VENDOR_TVT: "TVT",
    }.get(normalized, normalized[:3].upper())
