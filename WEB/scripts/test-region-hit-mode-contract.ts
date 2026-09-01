import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { parse } from '@vue/compiler-sfc';

import {
  FALLBACK_REGION_HIT_MODE_OPTIONS,
  resolveRegionHitModeOptions,
} from '../src/views/camera/components/DeviceRegionDrawer/regionHitMode';

const fallback = resolveRegionHitModeOptions([], 'center');
assert.deepEqual(fallback, FALLBACK_REGION_HIT_MODE_OPTIONS);

const configured = resolveRegionHitModeOptions([
  { label: '完全位于区域内', value: 'fully_inside' },
  { label: '未知实现', value: 'future_mode' },
], 'any_corner');
assert.deepEqual(configured.slice(0, 1), [{ label: '完全位于区域内', value: 'fully_inside' }]);
assert.deepEqual(configured[1], {
  label: 'any_corner（存量兼容配置）',
  value: 'any_corner',
  disabled: true,
});

for (const relative of [
  'src/views/camera/components/AlgorithmTask/DeviceRegionDetectionDrawer.vue',
  'src/views/camera/components/DeviceRegionDrawer/index.vue',
  'src/views/camera/components/AlgorithmTask/PostPipelineDrawer.vue',
  'src/views/camera/components/AlgorithmTask/index.vue',
]) {
  const filename = resolve(process.cwd(), relative);
  const source = readFileSync(filename, 'utf8');
  const parsed = parse(source, { filename });
  assert.deepEqual(parsed.errors, [], `${relative} must remain a valid Vue SFC`);
}

const taskListSource = readFileSync(
  resolve(process.cwd(), 'src/views/camera/components/AlgorithmTask/index.vue'),
  'utf8',
);
assert.doesNotMatch(taskListSource, /handleOpenRegionFilter/);
assert.doesNotMatch(taskListSource, /<RegionFilterDrawer/);
assert.doesNotMatch(taskListSource, /alertEventEnabled: record\.alert_event_enabled/);
assert.doesNotMatch(taskListSource, /onFilterSave:/);

const integratedRegionDrawerSource = readFileSync(
  resolve(process.cwd(), 'src/views/camera/components/AlgorithmTask/DeviceRegionDetectionDrawer.vue'),
  'utf8',
);
assert.doesNotMatch(integratedRegionDrawerSource, /事件命中判定/);
assert.doesNotMatch(integratedRegionDrawerSource, /onFilterSaveRef/);

const editorSource = readFileSync(
  resolve(process.cwd(), 'src/views/camera/components/DeviceRegionDrawer/index.vue'),
  'utf8',
);
assert.doesNotMatch(editorSource, /<slot name="task-filter" \/>/);
assert.match(editorSource, /v-model:value="selectedRegion\.hit_mode"/);
assert.match(editorSource, /v-model:value="selectedRegionOverlapPercent"/);

const pipelineDrawerSource = readFileSync(
  resolve(process.cwd(), 'src/views/camera/components/AlgorithmTask/PostPipelineDrawer.vue'),
  'utf8',
);
assert.match(pipelineDrawerSource, /selectedStep\.value\?\.plugin === 'region_gate'\) return \[\]/);
assert.match(pipelineDrawerSource, /命中方式和面积阈值请在「区域检测配置」中/);
assert.match(pipelineDrawerSource, /Alert as AAlert/);
assert.match(pipelineDrawerSource, /Empty as AEmpty/);
assert.doesNotMatch(pipelineDrawerSource, /<a-(alert|empty)\b/);

const dictSource = readFileSync(resolve(process.cwd(), 'src/utils/dict.ts'), 'utf8');
assert.match(dictSource, /AI_REGION_HIT_MODE = 'ai_region_hit_mode'/);

const sqlPatch = readFileSync(
  resolve(process.cwd(), '../.scripts/postgresql/ai_region_hit_mode_patch.sql'),
  'utf8',
);
for (const mode of ['center', 'bottom_center', 'any_intersection', 'overlap_ratio', 'fully_inside']) {
  assert.match(sqlPatch, new RegExp(`'${mode}'`));
}

console.log('region hit mode contract: ok');
