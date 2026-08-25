/** 告警列表展示与筛选共用常量 */

export const ALERT_EVENT_OPTIONS = [
  { value: null, label: '全部' },
  { value: '行人检测', label: '行人检测' },
  { value: 'face_library_match', label: '人脸库匹配' },
  { value: 'plate_library_match', label: '车牌库匹配' },
  { value: 'pose_intent_match', label: '姿态意图' },
  { value: 'pose_fall_detected', label: '跌倒检测' },
  { value: 'pose_climb_detected', label: '攀爬检测' },
  { value: 'pose_squat_detected', label: '蹲伏检测' },
  { value: 'pose_hands_up_detected', label: '举手求助' },
] as const;

const ALERT_EVENT_LABEL_MAP: Record<string, string> = {
  face_library_match: '人脸库匹配',
  plate_library_match: '车牌库匹配',
  pose_intent_match: '姿态意图',
  pose_fall_detected: '跌倒检测',
  pose_climb_detected: '攀爬检测',
  pose_squat_detected: '蹲伏检测',
  pose_hands_up_detected: '举手求助',
  行人检测: '行人检测',
};

export function formatAlertEvent(event?: string | null): string {
  if (!event) return '-';
  if (event.startsWith('pose_') && !ALERT_EVENT_LABEL_MAP[event]) {
    return event.replace(/^pose_/, '').replace(/_/g, ' ');
  }
  return ALERT_EVENT_LABEL_MAP[event] || event;
}

export function getAlertEventTagColor(event?: string | null): string {
  if (event === 'face_library_match') return 'purple';
  if (event === 'plate_library_match') return 'cyan';
  if (event === '行人检测') return 'orange';
  if (event?.startsWith('pose_')) return 'volcano';
  return 'default';
}

/** 解析告警 information（对象或 JSON 字符串） */
export function parseAlertInformation(information: unknown): Record<string, unknown> | null {
  if (information == null) return null;
  if (typeof information === 'object') return information as Record<string, unknown>;
  if (typeof information === 'string') {
    try {
      const parsed = JSON.parse(information);
      return typeof parsed === 'object' && parsed ? parsed : null;
    } catch {
      return null;
    }
  }
  return null;
}

/** 姿态意图告警摘要 */
export function formatPoseIntentAlertSummary(information: unknown): string | undefined {
  const info = parseAlertInformation(information);
  if (!info || info.match_type !== 'pose_intent') return undefined;
  const lib = info.library_name ? String(info.library_name) : '';
  const entry = info.entry_name ? String(info.entry_name) : '';
  const sim = info.similarity != null ? `${(Number(info.similarity) * 100).toFixed(1)}%` : '';
  const parts = [lib, entry, sim].filter(Boolean);
  return parts.length ? parts.join(' · ') : undefined;
}

type AlertPersonRecord = {
  event?: string | null;
  matched_person_name?: string | null;
  source_event?: string | null;
};

/** 人脸库匹配告警：读取已录入人员姓名 */
export function getAlertMatchedPersonName(record: AlertPersonRecord): string | undefined {
  if (record.matched_person_name) {
    return String(record.matched_person_name);
  }
  return undefined;
}

/** 人脸库匹配告警：读取触发的算法告警事件 */
export function getAlertSourceEvent(record: AlertPersonRecord): string | undefined {
  if (record.source_event) {
    return String(record.source_event);
  }
  return undefined;
}

/** 列表/大屏标题：人员姓名 + 触发告警 */
export function formatAlertListTitle(record: AlertPersonRecord & { event?: string | null; information?: unknown }): string {
  const poseSummary = formatPoseIntentAlertSummary(record.information);
  if (poseSummary) {
    return `${formatAlertEvent(record.event)} · ${poseSummary}`;
  }
  const personName = getAlertMatchedPersonName(record);
  const sourceEvent = getAlertSourceEvent(record);
  if (personName && sourceEvent) {
    return `${personName} · ${formatAlertEvent(sourceEvent)}`;
  }
  if (personName) {
    return `${formatAlertEvent(record.event)} · ${personName}`;
  }
  return formatAlertEvent(record.event);
}

/** 是否为抓拍类任务（无关联告警录像） */
export function isSnapAlertTask(record: {
  task_type?: string | null;
  information?: unknown;
}): boolean {
  let taskType = record.task_type;
  if (!taskType && record.information) {
    if (typeof record.information === 'object' && record.information !== null) {
      taskType = (record.information as { task_type?: string }).task_type;
    } else if (typeof record.information === 'string') {
      try {
        const info = JSON.parse(record.information);
        taskType = info?.task_type;
      } catch {
        // ignore
      }
    }
  }
  return taskType === 'snap' || taskType === 'snapshot';
}

export function normalizeAlertBusinessTagsParam(tags: unknown): string | undefined {
  if (Array.isArray(tags)) {
    const normalized = tags.map((t) => String(t).trim()).filter(Boolean);
    return normalized.length ? normalized.join(',') : undefined;
  }
  if (typeof tags === 'string' && tags.trim()) {
    return tags.trim();
  }
  return undefined;
}

export interface FaceMatchCandidate {
  face_entry_id?: number | null;
  person_name?: string | null;
  person_code?: string | null;
  similarity?: number | null;
  matched?: boolean;
}

/**
 * 人脸匹配信息：后端在告警序列化时按 correlation_id 关联 face_match_record，
 * 合并到告警 information.face_match（含姓名/相似度/人脸图 URL/候选列表）。
 */
export interface FaceMatchInfo {
  match_type?: string;
  matched?: boolean;
  match_record_id?: number;
  matched_person_name?: string | null;
  matched_person_code?: string | null;
  matched_face_entry_id?: number | null;
  similarity?: number | null;
  threshold?: number | null;
  library_id?: number | null;
  library_name?: string | null;
  face_image_path?: string | null;
  face_image_url?: string | null;
  candidates?: FaceMatchCandidate[];
}

/**
 * 提取告警关联的人脸匹配信息。
 * 优先取 information.face_match（后端增强）；兼容旧数据 information 顶层 match_type='face'。
 */
export function getAlertFaceMatchInfo(record: {
  information?: unknown;
  event?: string | null;
}): FaceMatchInfo | null {
  const info = parseAlertInformation(record.information);
  if (!info) return null;
  const fm = info.face_match as FaceMatchInfo | undefined;
  if (fm && (fm.matched || fm.match_type === 'face' || fm.matched_person_name)) {
    return fm;
  }
  // 兼容旧数据：information 顶层 match_type='face'
  if (info.match_type === 'face') {
    return {
      match_type: 'face',
      matched: true,
      matched_person_name: (info.matched_person_name as string) ?? null,
      matched_person_code: (info.matched_person_code as string) ?? null,
      similarity: info.similarity != null ? Number(info.similarity) : null,
      threshold: info.threshold != null ? Number(info.threshold) : null,
      library_name: info.library_name != null ? String(info.library_name) : null,
      face_image_path: info.face_image_path != null ? String(info.face_image_path) : null,
    };
  }
  return null;
}

/**
 * 提取告警关联的全部人脸匹配信息（同一帧画面可能匹配到多个人）。
 * 优先取 information.face_matches（后端按 similarity 降序返回全部）；
 * 兼容旧数据 information.face_match 单条与顶层 match_type='face'。
 */
export function getAlertFaceMatchInfos(record: {
  information?: unknown;
  event?: string | null;
}): FaceMatchInfo[] {
  const info = parseAlertInformation(record.information);
  if (!info) return [];
  const fmList = info.face_matches;
  if (Array.isArray(fmList)) {
    const valid = fmList.filter(
      (fm): fm is FaceMatchInfo =>
        Boolean(fm) && (fm.matched || fm.match_type === 'face' || fm.matched_person_name),
    );
    if (valid.length) return valid;
  }
  const single = getAlertFaceMatchInfo(record);
  return single ? [single] : [];
}

/** 告警是否关联人脸信息（决定弹框走人脸组件还是普通图片组件） */
export function hasAlertFaceMatch(record: {
  information?: unknown;
  event?: string | null;
}): boolean {
  return getAlertFaceMatchInfos(record).length > 0;
}

/**
 * 车牌匹配信息：后端在告警序列化时按 correlation_id 关联 plate_match_record，
 * 合并到告警 information.plate_match（含车牌号/颜色/车主/置信度/图片 URL）。
 */
export interface PlateMatchInfo {
  match_type?: string;
  matched?: boolean;
  match_record_id?: number;
  plate_no?: string | null;
  plate_color?: string | null;
  matched_owner_name?: string | null;
  matched_plate_entry_id?: number | null;
  detect_conf?: number | null;
  library_id?: number | null;
  library_name?: string | null;
  plate_image_path?: string | null;
  plate_image_url?: string | null;
  alert_id?: number | null;
}

/**
 * 提取告警关联的车牌匹配信息。
 * 优先取 information.plate_match（后端增强）；兼容旧数据 information 顶层 match_type='plate'。
 */
export function getAlertPlateMatchInfo(record: {
  information?: unknown;
  event?: string | null;
}): PlateMatchInfo | null {
  const info = parseAlertInformation(record.information);
  if (!info) return null;
  const pm = info.plate_match as PlateMatchInfo | undefined;
  if (pm && (pm.matched || pm.match_type === 'plate' || pm.plate_no)) {
    return pm;
  }
  // 兼容旧数据：information 顶层 match_type='plate'
  if (info.match_type === 'plate') {
    return {
      match_type: 'plate',
      matched: true,
      plate_no: (info.plate_no as string) ?? null,
      plate_color: (info.plate_color as string) ?? null,
      matched_owner_name: (info.matched_owner_name as string) ?? null,
      detect_conf: info.detect_conf != null ? Number(info.detect_conf) : null,
      library_name: info.library_name != null ? String(info.library_name) : null,
      plate_image_path: info.plate_image_path != null ? String(info.plate_image_path) : null,
    };
  }
  return null;
}

/**
 * 提取告警关联的全部车牌匹配信息（同一帧画面可能识别到多个车牌）。
 * 优先取 information.plate_matches（后端返回全部）；兼容旧数据单条与顶层 match_type='plate'。
 */
export function getAlertPlateMatchInfos(record: {
  information?: unknown;
  event?: string | null;
}): PlateMatchInfo[] {
  const info = parseAlertInformation(record.information);
  if (!info) return [];
  const pmList = info.plate_matches;
  if (Array.isArray(pmList)) {
    const valid = pmList.filter(
      (pm): pm is PlateMatchInfo =>
        Boolean(pm) && (pm.matched || pm.match_type === 'plate' || pm.plate_no),
    );
    if (valid.length) return valid;
  }
  const single = getAlertPlateMatchInfo(record);
  return single ? [single] : [];
}

/** 告警是否关联车牌信息（决定弹框走车牌组件还是普通图片组件） */
export function hasAlertPlateMatch(record: {
  information?: unknown;
  event?: string | null;
}): boolean {
  return getAlertPlateMatchInfos(record).length > 0;
}

/** 车牌库匹配告警：读取命中车牌号（兼容后端 matched_plate_no / object 兜底） */
export function getAlertMatchedPlateNo(record: {
  matched_plate_no?: string | null;
  object?: string | null;
  event?: string | null;
  information?: unknown;
}): string | undefined {
  if (record.matched_plate_no) {
    return String(record.matched_plate_no);
  }
  const pm = getAlertPlateMatchInfo(record);
  if (pm?.plate_no) {
    return String(pm.plate_no);
  }
  if (record.event === 'plate_library_match' && record.object) {
    return String(record.object);
  }
  return undefined;
}
