export type RegionModelScope = 'all' | 'selected';

export interface RegionDraftLike {
  id?: number;
  region_name?: string;
  image_id?: number;
  model_scope?: RegionModelScope;
  model_ids?: number[];
  hit_mode?: string;
  min_overlap_ratio?: number;
  sort_order?: number;
  [key: string]: unknown;
}

export interface RegionPoint {
  x: number;
  y: number;
}

export function appendDistinctRegionPoint(
  points: RegionPoint[],
  point: RegionPoint,
  epsilon = 1e-6,
): boolean {
  const last = points[points.length - 1];
  if (
    last
    && Math.abs(last.x - point.x) <= epsilon
    && Math.abs(last.y - point.y) <= epsilon
  ) {
    return false;
  }
  points.push(point);
  return true;
}

export function normalizeRegionModelScope<T extends RegionDraftLike>(region: T): T & RegionDraftLike {
  const selected = region.model_scope === 'selected' ||
    (!region.model_scope && (region.model_ids || []).length > 0);
  return {
    ...region,
    model_scope: selected ? 'selected' : 'all',
    model_ids: selected ? [...new Set(region.model_ids || [])].sort((a, b) => a - b) : [],
  };
}

export function normalizeRegionForSave<T extends RegionDraftLike>(
  region: T,
  index: number,
  currentImageId?: number | null,
): T & RegionDraftLike {
  const normalized = normalizeRegionModelScope(region);
  return {
    ...normalized,
    id: typeof region.id === 'number' && region.id > 0 ? region.id : undefined,
    region_name: region.region_name?.trim() || `区域 ${index + 1}`,
    image_id: region.image_id || currentImageId || undefined,
    sort_order: index,
    hit_mode: region.hit_mode || 'center',
    min_overlap_ratio: typeof region.min_overlap_ratio === 'number'
      && Number.isFinite(region.min_overlap_ratio)
      ? Math.min(1, Math.max(0.01, Number(region.min_overlap_ratio)))
      : 0.5,
  };
}

export function regionSyncSuccessMessage(status: unknown): string {
  if (status === 'pending') return '区域已保存，运行配置同步中';
  if (status === 'not_running') return '区域配置已保存，将在任务启动时生效';
  return '区域已保存，已生效';
}

export function isRegionRevisionConflict(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false;
  const candidate = error as { status?: number; response?: { status?: number } };
  return candidate.status === 409 || candidate.response?.status === 409;
}
