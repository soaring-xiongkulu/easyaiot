"""车辆电子身份（VID）解析；第一阶段仅依赖现有车牌 OCR、颜色与时空信息。"""
import json
import math
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from models import (
    Device, PlateEntry, PlateMatchRecord, VehicleIdentity, VehiclePlateAlias, db,
)


def normalize_plate_no(value: str) -> str:
    text = str(value or '').strip().upper()
    return re.sub(r'[\s·•.\-_]+', '', text)


def _new_code(now: datetime) -> str:
    return f'VID-{now:%Y%m%d}-{uuid.uuid4().hex[:8].upper()}'


def _normalize_color(value: Optional[str]) -> Optional[str]:
    text = str(value or '').strip().lower()
    aliases = {
        '蓝': 'blue', '蓝色': 'blue', 'blue': 'blue',
        '黄': 'yellow', '黄色': 'yellow', 'yellow': 'yellow',
        '绿': 'green', '绿色': 'green', 'green': 'green',
        '白': 'white', '白色': 'white', 'white': 'white',
        '黑': 'black', '黑色': 'black', 'black': 'black',
    }
    return aliases.get(text, text or None)


def _distance_km(a: Device, b: Device) -> Optional[float]:
    if not a or not b or a.latitude is None or a.longitude is None or b.latitude is None or b.longitude is None:
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, [a.latitude, a.longitude, b.latitude, b.longitude])
    delta_lat, delta_lon = lat2 - lat1, lon2 - lon1
    value = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(value))


def _risk_flags(identity: VehicleIdentity, device_id: Optional[str], seen_at: datetime,
                plate_color: Optional[str]) -> list[str]:
    flags = []
    old_color, new_color = _normalize_color(identity.plate_color), _normalize_color(plate_color)
    if old_color and new_color and old_color != new_color:
        flags.append('plate_color_conflict')
    if identity.last_seen_at and identity.last_device_id and device_id and identity.last_device_id != str(device_id):
        seconds = max(1.0, (seen_at - identity.last_seen_at).total_seconds())
        distance = _distance_km(Device.query.get(identity.last_device_id), Device.query.get(str(device_id)))
        if distance is not None and distance / (seconds / 3600.0) > float(os.getenv('VEHICLE_IMPOSSIBLE_SPEED_KMH', '180')):
            flags.append('impossible_travel')
    return flags


def resolve_vehicle_identity(*, plate_no: str, raw_plate_no: Optional[str] = None,
                             plate_color: Optional[str] = None, confidence: Optional[float] = None,
                             image_path: Optional[str] = None, device_id: Optional[str] = None,
                             seen_at: Optional[datetime] = None,
                             formal_plate_entry_id: Optional[int] = None) -> Dict[str, Any]:
    normalized = normalize_plate_no(plate_no)
    if not normalized:
        raise ValueError('车牌号为空，无法解析车辆电子身份')
    now = seen_at or datetime.utcnow()
    identity = None
    resolution = 'new'
    if formal_plate_entry_id:
        identity = VehicleIdentity.query.filter_by(
            business_plate_entry_id=int(formal_plate_entry_id),
        ).filter(VehicleIdentity.status != 'merged').first()
        resolution = 'confirmed'

    aliases = VehiclePlateAlias.query.filter_by(plate_no=normalized).order_by(
        VehiclePlateAlias.is_verified.desc(), VehiclePlateAlias.last_seen_at.desc(),
    ).all()
    candidates = [a.identity for a in aliases if a.identity and a.identity.status in ('anonymous', 'confirmed')]
    conflict_candidate = None
    if identity is None and candidates:
        compatible = [item for item in candidates if not _risk_flags(item, device_id, now, plate_color)]
        if compatible:
            identity, resolution = compatible[0], 'exact_plate'
        else:
            conflict_candidate = candidates[0]

    flags = _risk_flags(identity or conflict_candidate, device_id, now, plate_color) if (identity or conflict_candidate) else []
    # 相同车牌但颜色或时空严重冲突时保留独立 VID，不能强制归并。
    if identity is not None and flags:
        identity = None
        resolution = 'risk_split'
    elif identity is None and flags:
        resolution = 'risk_split'

    created = identity is None
    if created:
        entry = PlateEntry.query.get(int(formal_plate_entry_id)) if formal_plate_entry_id else None
        code = _new_code(now)
        identity = VehicleIdentity(
            identity_code=code,
            display_name=(f'{entry.plate_no}-{entry.owner_name}' if entry and entry.owner_name else f'未知车辆-{code[-8:]}'),
            status='confirmed' if entry else 'anonymous',
            current_plate_no=normalized,
            plate_color=plate_color,
            owner_name=entry.owner_name if entry else None,
            business_plate_entry_id=entry.id if entry else None,
            cover_image_path=image_path,
            first_seen_at=now, last_seen_at=now,
            first_device_id=str(device_id) if device_id else None,
            last_device_id=str(device_id) if device_id else None,
            occurrence_count=1,
            risk_status='suspected_clone' if flags else 'normal',
        )
        db.session.add(identity)
        db.session.flush()
        alias = VehiclePlateAlias(
            identity_id=identity.id, plate_no=normalized,
            raw_plate_no=raw_plate_no or plate_no, plate_color=plate_color,
            confidence=confidence, alias_type='current',
            first_seen_at=now, last_seen_at=now, occurrence_count=1,
            is_verified=bool(entry),
        )
        db.session.add(alias)
    else:
        dedup_start = now - timedelta(seconds=max(1, int(os.getenv('VEHICLE_TRAJECTORY_DEDUP_SECONDS', '20'))))
        suppressed = PlateMatchRecord.query.filter(
            PlateMatchRecord.vehicle_identity_id == identity.id,
            PlateMatchRecord.device_id == str(device_id or ''),
            PlateMatchRecord.created_at >= dedup_start,
        ).first() is not None
        alias = next((a for a in aliases if a.identity_id == identity.id), None)
        if not suppressed:
            identity.last_seen_at = now
            identity.last_device_id = str(device_id) if device_id else identity.last_device_id
            identity.occurrence_count = int(identity.occurrence_count or 0) + 1
            identity.cover_image_path = identity.cover_image_path or image_path
            if alias:
                alias.last_seen_at = now
                alias.occurrence_count = int(alias.occurrence_count or 0) + 1
                alias.confidence = max(float(alias.confidence or 0), float(confidence or 0)) or None
        return {
            'identity': identity, 'created': False, 'resolution': resolution,
            'normalized_plate_no': normalized, 'risk_flags': flags,
            'trajectory_suppressed': suppressed,
        }
    return {
        'identity': identity, 'created': True, 'resolution': resolution,
        'normalized_plate_no': normalized, 'risk_flags': flags,
        'trajectory_suppressed': False,
    }


def apply_to_record(record: PlateMatchRecord, result: Dict[str, Any]) -> None:
    identity = result['identity']
    record.vehicle_identity_id = identity.id
    record.vehicle_identity_code = identity.identity_code
    record.vehicle_identity_name = identity.display_name
    record.vehicle_resolution = result['resolution']
    record.normalized_plate_no = result['normalized_plate_no']
    record.risk_flags = json.dumps(result.get('risk_flags') or [], ensure_ascii=False)


def list_identities(*, page=1, page_size=20, status=None, risk_status=None, search=None) -> Dict[str, Any]:
    query = VehicleIdentity.query.filter(VehicleIdentity.status != 'merged')
    if status:
        query = query.filter_by(status=status)
    if risk_status:
        query = query.filter_by(risk_status=risk_status)
    if search:
        word = f'%{str(search).strip()}%'
        query = query.filter(db.or_(VehicleIdentity.identity_code.ilike(word),
                                    VehicleIdentity.display_name.ilike(word),
                                    VehicleIdentity.current_plate_no.ilike(word),
                                    VehicleIdentity.owner_name.ilike(word)))
    total = query.count()
    rows = query.order_by(VehicleIdentity.last_seen_at.desc()).offset(
        max(0, (int(page) - 1) * int(page_size)),
    ).limit(max(1, min(int(page_size), 200))).all()
    return {'list': [row.to_dict() for row in rows], 'total': total}


def update_identity(identity_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    identity = VehicleIdentity.query.get_or_404(int(identity_id))
    for field in ('display_name', 'owner_name', 'remark'):
        if field in payload:
            setattr(identity, field, str(payload[field]).strip() or None)
    if payload.get('status') in ('anonymous', 'confirmed', 'disabled'):
        identity.status = payload['status']
    if payload.get('risk_status') in ('normal', 'review', 'suspected_clone'):
        identity.risk_status = payload['risk_status']
    if payload.get('business_plate_entry_id') is not None:
        entry = PlateEntry.query.get_or_404(int(payload['business_plate_entry_id']))
        identity.business_plate_entry_id = entry.id
        identity.current_plate_no = normalize_plate_no(entry.plate_no)
        identity.owner_name = identity.owner_name or entry.owner_name
        identity.status = 'confirmed'
    db.session.commit()
    return identity.to_dict()


def merge_identities(target_id: int, source_ids) -> Dict[str, Any]:
    target = VehicleIdentity.query.get_or_404(int(target_id))
    sources = VehicleIdentity.query.filter(VehicleIdentity.id.in_([int(x) for x in source_ids])).all()
    merged = 0
    for source in sources:
        if source.id == target.id or source.status == 'merged':
            continue
        for alias in list(source.aliases or []):
            existing = VehiclePlateAlias.query.filter_by(identity_id=target.id, plate_no=alias.plate_no).first()
            if existing:
                existing.occurrence_count += int(alias.occurrence_count or 0)
                db.session.delete(alias)
            else:
                alias.identity_id = target.id
        PlateMatchRecord.query.filter_by(vehicle_identity_id=source.id).update({
            'vehicle_identity_id': target.id,
            'vehicle_identity_code': target.identity_code,
            'vehicle_identity_name': target.display_name,
        })
        target.occurrence_count += int(source.occurrence_count or 0)
        source.status, source.merged_into_id = 'merged', target.id
        merged += 1
    db.session.commit()
    return {'target': target.to_dict(), 'merged_count': merged}


def trajectory(identity_id: int, *, date: Optional[str] = None, limit=500) -> Dict[str, Any]:
    identity = VehicleIdentity.query.get_or_404(int(identity_id))
    query = PlateMatchRecord.query.filter_by(vehicle_identity_id=identity.id)
    if date:
        local = datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=timezone(timedelta(hours=8)))
        start = (local - timedelta(hours=8)).replace(tzinfo=None)
        query = query.filter(PlateMatchRecord.created_at >= start,
                             PlateMatchRecord.created_at < start + timedelta(days=1))
    rows = query.order_by(PlateMatchRecord.created_at.asc()).limit(max(1, min(int(limit), 2000))).all()
    points = [r.to_dict() for r in rows]
    return {'identity': identity.to_dict(), 'points': points, 'total': len(points)}


def backfill_unresolved_records(limit=10000) -> Dict[str, int]:
    rows = PlateMatchRecord.query.filter(
        PlateMatchRecord.vehicle_identity_id.is_(None), PlateMatchRecord.plate_no.isnot(None),
        PlateMatchRecord.status == 'success',
    ).order_by(PlateMatchRecord.id.asc()).limit(max(1, min(int(limit), 20000))).all()
    resolved = failed = 0
    for record in rows:
        try:
            result = resolve_vehicle_identity(
                plate_no=record.plate_no, raw_plate_no=record.plate_no,
                plate_color=record.plate_color, confidence=record.detect_conf,
                image_path=record.plate_image_path, device_id=record.device_id,
                seen_at=record.created_at,
                formal_plate_entry_id=record.matched_plate_entry_id,
            )
            apply_to_record(record, result)
            if not result['created'] and record.enroll_status == 'pending':
                record.enroll_status = 'tracked'
            db.session.commit()
            resolved += 1
        except Exception:
            db.session.rollback()
            failed += 1
    return {'resolved': resolved, 'failed': failed}
