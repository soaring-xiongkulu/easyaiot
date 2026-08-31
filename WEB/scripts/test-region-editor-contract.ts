import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { parse } from '@vue/compiler-sfc';

import {
  appendDistinctRegionPoint,
  isRegionRevisionConflict,
  normalizeRegionForSave,
  normalizeRegionModelScope,
  regionSyncSuccessMessage,
} from '../src/views/camera/components/DeviceRegionDrawer/regionEditorContract';

const polygonPoints = [{ x: 0.2, y: 0.2 }];
assert.equal(appendDistinctRegionPoint(polygonPoints, { x: 0.2, y: 0.2 }), false);
assert.equal(appendDistinctRegionPoint(polygonPoints, { x: 0.6, y: 0.2 }), true);
assert.equal(appendDistinctRegionPoint(polygonPoints, { x: 0.6, y: 0.2 }), false);
assert.equal(appendDistinctRegionPoint(polygonPoints, { x: 0.4, y: 0.7 }), true);
assert.deepEqual(polygonPoints, [
  { x: 0.2, y: 0.2 },
  { x: 0.6, y: 0.2 },
  { x: 0.4, y: 0.7 },
]);

const selected = normalizeRegionForSave({
  id: -1,
  region_name: '  模型区域  ',
  model_scope: 'selected',
  model_ids: [12, 11, 12],
  hit_mode: 'overlap_ratio',
  min_overlap_ratio: 0.65,
}, 2, 99);
assert.equal(selected.id, undefined);
assert.equal(selected.region_name, '模型区域');
assert.equal(selected.image_id, 99);
assert.equal(selected.sort_order, 2);
assert.deepEqual(selected.model_ids, [11, 12]);
assert.equal(selected.hit_mode, 'overlap_ratio');
assert.equal(selected.min_overlap_ratio, 0.65);

const all = normalizeRegionForSave({
  id: 8,
  region_name: '',
  model_scope: 'all',
  model_ids: [11],
  image_id: 5,
}, 0, 99);
assert.equal(all.id, 8);
assert.equal(all.region_name, '区域 1');
assert.equal(all.image_id, 5);
assert.deepEqual(all.model_ids, []);
assert.equal(all.hit_mode, 'center');
assert.equal(all.min_overlap_ratio, 0.5);

assert.deepEqual(
  normalizeRegionModelScope({ model_ids: [12] }),
  { model_ids: [12], model_scope: 'selected' },
);
assert.deepEqual(
  normalizeRegionModelScope({ model_ids: [] }),
  { model_ids: [], model_scope: 'all' },
);

assert.equal(regionSyncSuccessMessage('applied'), '区域已保存，已生效');
assert.equal(regionSyncSuccessMessage('pending'), '区域已保存，运行配置同步中');
assert.equal(regionSyncSuccessMessage('not_running'), '区域配置已保存，将在任务启动时生效');
assert.equal(isRegionRevisionConflict({ response: { status: 409 } }), true);
assert.equal(isRegionRevisionConflict({ status: 409 }), true);
assert.equal(isRegionRevisionConflict({ response: { status: 400 } }), false);

for (const relative of [
  'src/views/camera/components/DeviceRegionDrawer/index.vue',
  'src/views/camera/components/AlgorithmTask/DeviceRegionDetectionDrawer.vue',
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
assert.match(taskListSource, /tooltip:\s*'区域配置（支持运行时热更新）'/);
assert.match(taskListSource, /handleOpenRegions\(record\)/);
assert.match(taskListSource, /<DeviceRegionDetectionDrawer\s+@register="registerRegionDrawer"/);

const drawerSource = readFileSync(
  resolve(process.cwd(), 'src/views/camera/components/DeviceRegionDrawer/index.vue'),
  'utf8',
);
assert.doesNotMatch(drawerSource, /<a-(?:badge|empty|popconfirm|radio-(?:group|button)|select|spin)/);
assert.match(drawerSource, /Badge[\s\S]*Empty[\s\S]*Popconfirm[\s\S]*Spin[\s\S]*from 'ant-design-vue'/);
assert.match(drawerSource, /v-model:value="selectedRegion\.hit_mode"/);
assert.match(drawerSource, /v-model:value="selectedRegionOverlapPercent"/);
assert.match(drawerSource, /handleRegionHitModeChange/);
assert.match(drawerSource, /handleRegionOverlapChange/);

const detectionDrawerSource = readFileSync(
  resolve(process.cwd(), 'src/views/camera/components/AlgorithmTask/DeviceRegionDetectionDrawer.vue'),
  'utf8',
);
assert.doesNotMatch(detectionDrawerSource, /<a-(?:empty|spin|tag)/);
assert.match(detectionDrawerSource, /Empty[\s\S]*Spin[\s\S]*Tag[\s\S]*from 'ant-design-vue'/);

console.log('region editor contract: ok');
