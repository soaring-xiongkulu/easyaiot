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
  center: '检测框中心点进入任一区域时产生预警。',
  bottom_center: '检测框底边中点进入任一区域时产生预警，适合以脚底或车辆落地点判断。',
  any_intersection: '检测框与任一区域有交集或边界接触时产生预警，判定最宽松。',
  overlap_ratio: '检测框落入区域的面积占检测框面积达到设定比例时产生预警。',
  fully_inside: '检测框全部位于任一区域内时产生预警，判定最严格。',
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
