export const SELECTABLE_REGION_HIT_MODES = [
  'center',
  'bottom_center',
  'any_intersection',
  'overlap_ratio',
  'fully_inside',
] as const;

export type SelectableRegionHitMode = typeof SELECTABLE_REGION_HIT_MODES[number];

export interface RegionHitModeOption {
  label: string;
  value: string;
  disabled?: boolean;
}

export const FALLBACK_REGION_HIT_MODE_OPTIONS: RegionHitModeOption[] = [
  { label: '中心点', value: 'center' },
  { label: '底边中点', value: 'bottom_center' },
  { label: '任意交集', value: 'any_intersection' },
  { label: '区域内面积达到阈值', value: 'overlap_ratio' },
  { label: '完全位于区域内', value: 'fully_inside' },
];

export const REGION_HIT_MODE_HELP: Record<string, string> = {
  center: '检测框中心点位于此区域时视为区域内；是否告警由绑定的监测规则决定。',
  bottom_center: '使用检测框底边中点判断是否位于此区域，适合脚底或车辆落地点。',
  any_intersection: '检测框与此区域有交集或边界接触即视为区域内，判定最宽松。',
  overlap_ratio: '检测框落入此区域的面积占检测框面积达到下方比例时，视为区域内。',
  fully_inside: '检测框全部位于此区域才视为区域内，判定最严格。',
};

export function resolveRegionHitModeOptions(
  dictOptions: Array<{ label: string; value: unknown }>,
  currentMode?: string,
): RegionHitModeOption[] {
  const selectable = new Set<string>(SELECTABLE_REGION_HIT_MODES);
  const fromDict = dictOptions
    .map((item) => ({ label: item.label, value: String(item.value) }))
    .filter((item) => selectable.has(item.value));
  const options: RegionHitModeOption[] = fromDict.length
    ? fromDict
    : FALLBACK_REGION_HIT_MODE_OPTIONS.map((item) => ({ ...item }));
  if (currentMode && !options.some((item) => item.value === currentMode)) {
    options.push({
      label: `${currentMode}（存量兼容配置）`,
      value: currentMode,
      disabled: true,
    });
  }
  return options;
}
