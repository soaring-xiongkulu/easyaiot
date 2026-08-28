<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    title="车牌待入库工作台"
    width="96%"
    placement="right"
    :showFooter="false"
    destroy-on-close
  >
    <div class="plate-workbench">
      <!-- 顶部：统计 + 状态筛选 + 搜索 -->
      <div class="workbench-bar">
        <div class="workbench-bar__stats">
          <div
            v-for="tab in statusTabs"
            :key="tab.value"
            class="stat-chip"
            :class="{ 'is-active': status === tab.value }"
            @click="switchStatus(tab.value)"
          >
            <span class="stat-chip__count">{{ stats[tab.value] ?? 0 }}</span>
            <span class="stat-chip__label">{{ tab.label }}</span>
          </div>
        </div>
        <div class="workbench-bar__actions">
          <Input
            v-model:value="searchText"
            style="width: 220px"
            placeholder="搜索设备 / 任务 / 车牌号"
            allow-clear
            @press-enter="reload"
          >
            <template #prefix><SearchOutlined /></template>
          </Input>
          <Button preIcon="ant-design:reload-outlined" :loading="loading" @click="reload">刷新</Button>
        </div>
      </div>

      <!-- 批量操作条 -->
      <div class="workbench-toolbar">
        <template v-if="status === 'pending'">
          <Button
            type="primary"
            preIcon="ant-design:car-outlined"
            :disabled="!checkedIds.length"
            @click="openBatchEnroll"
          >
            批量入库{{ checkedIds.length ? `（${checkedIds.length}）` : '' }}
          </Button>
          <PopConfirmButton
            placement="bottomLeft"
            type="default"
            :disabled="!checkedIds.length"
            title="确定忽略所选目标？忽略后可随时在「已忽略」中恢复。"
            preIcon="ant-design:eye-invisible-outlined"
            @confirm="handleBatchDiscard"
          >
            忽略所选{{ checkedIds.length ? `（${checkedIds.length}）` : '' }}
          </PopConfirmButton>
        </template>
        <Button
          v-if="status === 'discarded'"
          :disabled="!checkedIds.length"
          preIcon="ant-design:undo-outlined"
          @click="handleBatchRestore"
        >
          恢复所选{{ checkedIds.length ? `（${checkedIds.length}）` : '' }}
        </Button>
        <PopConfirmButton
          placement="bottomLeft"
          type="primary"
          color="error"
          :disabled="!checkedIds.length"
          title="确定删除所选记录？记录及其整帧图片将被移除。"
          preIcon="ant-design:delete-outlined"
          @confirm="handleBatchDelete"
        >
          删除所选{{ checkedIds.length ? `（${checkedIds.length}）` : '' }}
        </PopConfirmButton>
        <span class="workbench-toolbar__hint" v-if="status === 'pending'">
          AI 检测到但未匹配车牌库的车辆会出现在这里，核对车牌号后即可批量入库
        </span>
      </div>

      <!-- 卡片列表 -->
      <div class="workbench-grid-wrap">
        <Spin :spinning="loading" :tip="loadingTip" size="large">
          <div v-if="records.length" class="workbench-grid">
            <div
              v-for="item in records"
              :key="item.id"
              class="target-card"
              :class="{ selected: checkedIds.includes(item.id) }"
            >
              <div
                class="target-card__check"
                :class="{ checked: checkedIds.includes(item.id) }"
                @click.stop="toggleCheck(item.id)"
              >
                <span class="check-inner" />
              </div>
              <div class="target-card__cover" @click="openEnroll(item)">
                <img
                  :src="resolvePlateImageDisplayUrl(item.crop_image_url) || defaultPlate"
                  class="target-card__img"
                  alt="车牌"
                  loading="lazy"
                  @error="onImgError"
                />
                <span v-if="item.enroll_status === 'enrolled'" class="target-card__badge is-enrolled">
                  已入库
                </span>
                <span v-else-if="item.enroll_status === 'discarded'" class="target-card__badge is-discarded">
                  已忽略
                </span>
                <span v-else class="target-card__badge is-pending">待入库</span>
                <div class="target-card__overlay">
                  <button class="overlay-btn" title="核对车牌号并入库" @click.stop="openEnroll(item)">
                    <AuditOutlined />
                  </button>
                  <button
                    v-if="item.enroll_status === 'pending'"
                    class="overlay-btn"
                    title="忽略"
                    @click.stop="handleDiscardOne(item)"
                  >
                    <EyeInvisibleOutlined />
                  </button>
                  <button
                    v-if="item.enroll_status === 'discarded'"
                    class="overlay-btn"
                    title="恢复"
                    @click.stop="handleRestoreOne(item)"
                  >
                    <UndoOutlined />
                  </button>
                  <button class="overlay-btn is-danger" title="删除" @click.stop="handleDeleteOne(item)">
                    <DeleteOutlined />
                  </button>
                </div>
              </div>
              <div class="target-card__body">
                <p class="target-card__plate">
                  <span class="plate-no" :class="{ 'is-empty': !item.plate_no }">
                    {{ item.plate_no || '未识别车牌号' }}
                  </span>
                  <a-tag v-if="item.plate_color" color="orange" class="target-card__color">
                    {{ item.plate_color }}
                  </a-tag>
                </p>
                <p class="target-card__device" :title="item.device_name || item.device_id">
                  <VideoCameraOutlined />
                  {{ item.device_name || item.device_id }}
                </p>
                <p class="target-card__meta">
                  <span>{{ formatTime(item.created_at) }}</span>
                  <span v-if="item.detect_conf">{{ (item.detect_conf * 100).toFixed(0) }}%</span>
                  <a-tag v-if="item.enroll_status === 'enrolled'" color="success" class="target-card__tag">
                    {{ item.enroll_target_library_id ? `库 #${item.enroll_target_library_id}` : '已入库' }}
                  </a-tag>
                </p>
              </div>
            </div>
          </div>
          <Empty
            v-else
            class="workbench-grid__empty"
            :description="emptyText"
            :image="Empty.PRESENTED_IMAGE_SIMPLE"
          />
        </Spin>
      </div>

      <!-- 分页 -->
      <div class="workbench-pagination">
        <a-pagination
          v-model:current="page"
          :page-size="pageSize"
          :total="total"
          :show-size-changer="false"
          show-quick-jumper
          :show-total="(t: number) => `共 ${t} 条`"
          @change="loadRecords"
        />
      </div>
    </div>

    <PlateEnrollDrawer @register="registerEnrollDrawer" @success="onEnrollSuccess" />
    <PlateBatchEnrollModal @register="registerBatchModal" @success="onBatchEnrollSuccess" />
  </BasicDrawer>
</template>

<script lang="ts" setup>
/**
 * 车牌待入库工作台：集中管理算法任务中「检测到但未匹配车牌库」的车辆。
 * 支持批量入库 / 忽略 / 恢复 / 删除，单条核对车牌号后两步入库。
 */
import { computed, ref } from 'vue';
import {
  AuditOutlined,
  DeleteOutlined,
  EyeInvisibleOutlined,
  SearchOutlined,
  UndoOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons-vue';
import { Empty, Input as AInput, Spin, Tag as ATag } from 'ant-design-vue';
import { BasicDrawer, useDrawer, useDrawerInner } from '@/components/Drawer';
import { useModal } from '@/components/Modal';
import { Button, PopConfirmButton } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import { resolvePlateImageDisplayUrl } from '@/api/device/plate_library';
import {
  batchDeletePendingRecords,
  batchDiscardPendingRecords,
  batchRestorePendingRecords,
  getPendingStats,
  listPendingRecords,
  type PendingEnrollRecord,
  type PendingEnrollStats,
  type PendingEnrollStatus,
} from '@/api/device/pending_enroll';
import DEFAULT_PLATE_IMAGE from '@/assets/images/video/snap-task.png';
import PlateEnrollDrawer from './PlateEnrollDrawer.vue';
import PlateBatchEnrollModal from './PlateBatchEnrollModal.vue';

const Input = AInput;

defineOptions({ name: 'PlatePendingWorkbench' });

const defaultPlate = DEFAULT_PLATE_IMAGE;

const emit = defineEmits<{
  (e: 'stats-change', stats: PendingEnrollStats): void;
}>();

const { createMessage } = useMessage();

const statusTabs: Array<{ value: PendingEnrollStatus; label: string }> = [
  { value: 'pending', label: '待入库' },
  { value: 'enrolled', label: '已入库' },
  { value: 'discarded', label: '已忽略' },
];

const status = ref<PendingEnrollStatus>('pending');
const stats = ref<PendingEnrollStats>({ pending: 0, enrolled: 0, discarded: 0 });
const records = ref<PendingEnrollRecord[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(24);
const searchText = ref('');
const loading = ref(false);
const loadingTip = ref('加载中…');
const checkedIds = ref<number[]>([]);

const [registerEnrollDrawer, { openDrawer: openEnrollDrawer }] = useDrawer();
const [registerBatchModal, { openModal: openBatchModal }] = useModal();

const [register, { closeDrawer }] = useDrawerInner(async () => {
  page.value = 1;
  checkedIds.value = [];
  searchText.value = '';
  status.value = 'pending';
  await Promise.all([loadStats(), loadRecords()]);
});

const emptyText = computed(() => {
  if (status.value === 'pending') {
    return '暂无待入库目标。算法任务开启车牌检测并匹配车牌库后，未匹配到的车辆会自动出现在这里';
  }
  if (status.value === 'enrolled') return '暂无已入库记录';
  return '暂无已忽略记录';
});

function formatTime(value?: string) {
  if (!value) return '—';
  return String(value).replace('T', ' ').slice(5, 16);
}

function onImgError(e: Event) {
  const img = e.target as HTMLImageElement;
  if (img && img.src !== defaultPlate) img.src = defaultPlate;
}

function toggleCheck(id: number) {
  checkedIds.value = checkedIds.value.includes(id)
    ? checkedIds.value.filter((x) => x !== id)
    : [...checkedIds.value, id];
}

function switchStatus(value: PendingEnrollStatus) {
  status.value = value;
  page.value = 1;
  checkedIds.value = [];
  void loadRecords();
}

function reload() {
  page.value = 1;
  void loadRecords();
  void loadStats();
}

async function loadStats() {
  try {
    const res = await getPendingStats('plate');
    if (res?.data) {
      stats.value = res.data;
      emit('stats-change', res.data);
    }
  } catch (e) {
    console.warn('加载统计失败', e);
  }
}

async function loadRecords() {
  loading.value = true;
  loadingTip.value = '加载待入库目标…';
  try {
    const res = await listPendingRecords('plate', {
      status: status.value,
      page: page.value,
      pageSize: pageSize.value,
      search: searchText.value.trim() || undefined,
    });
    records.value = res?.list || [];
    total.value = res?.total ?? 0;
    if (res?.stats) {
      stats.value = res.stats;
      emit('stats-change', res.stats);
    }
    checkedIds.value = checkedIds.value.filter((id) => records.value.some((r) => r.id === id));
  } catch (e: any) {
    createMessage.error(e?.message || '加载待入库目标失败');
    records.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function openEnroll(item: PendingEnrollRecord) {
  if (item.enroll_status === 'enrolled') return;
  openEnrollDrawer(true, { record: item });
}

function openBatchEnroll() {
  const selected = records.value.filter(
    (r) => checkedIds.value.includes(r.id) && r.enroll_status === 'pending',
  );
  if (!selected.length) return;
  openBatchModal(true, { records: selected });
}

async function handleDiscardOne(item: PendingEnrollRecord) {
  try {
    await batchDiscardPendingRecords('plate', [item.id]);
    createMessage.success('已忽略');
    await Promise.all([loadRecords(), loadStats()]);
  } catch (e: any) {
    createMessage.error(e?.message || '操作失败');
  }
}

async function handleRestoreOne(item: PendingEnrollRecord) {
  try {
    await batchRestorePendingRecords('plate', [item.id]);
    createMessage.success('已恢复');
    await Promise.all([loadRecords(), loadStats()]);
  } catch (e: any) {
    createMessage.error(e?.message || '操作失败');
  }
}

async function handleDeleteOne(item: PendingEnrollRecord) {
  try {
    await batchDeletePendingRecords('plate', [item.id]);
    createMessage.success('已删除');
    await Promise.all([loadRecords(), loadStats()]);
  } catch (e: any) {
    createMessage.error(e?.message || '操作失败');
  }
}

async function handleBatchDiscard() {
  if (!checkedIds.value.length) return;
  try {
    const res = await batchDiscardPendingRecords('plate', [...checkedIds.value]);
    createMessage.success(res.msg || '已忽略所选目标');
    checkedIds.value = [];
    await Promise.all([loadRecords(), loadStats()]);
  } catch (e: any) {
    createMessage.error(e?.message || '操作失败');
  }
}

async function handleBatchRestore() {
  if (!checkedIds.value.length) return;
  try {
    const res = await batchRestorePendingRecords('plate', [...checkedIds.value]);
    createMessage.success(res.msg || '已恢复所选目标');
    checkedIds.value = [];
    await Promise.all([loadRecords(), loadStats()]);
  } catch (e: any) {
    createMessage.error(e?.message || '操作失败');
  }
}

async function handleBatchDelete() {
  if (!checkedIds.value.length) return;
  try {
    const res = await batchDeletePendingRecords('plate', [...checkedIds.value]);
    createMessage.success(res.msg || '已删除所选记录');
    checkedIds.value = [];
    await Promise.all([loadRecords(), loadStats()]);
  } catch (e: any) {
    createMessage.error(e?.message || '操作失败');
  }
}

function onEnrollSuccess() {
  checkedIds.value = [];
  void Promise.all([loadRecords(), loadStats()]);
}

function onBatchEnrollSuccess() {
  checkedIds.value = [];
  void Promise.all([loadRecords(), loadStats()]);
}

defineExpose({ closeDrawer });
</script>

<style lang="less" scoped>
@border: #f0f0f0;
@primary: #266cfb;

.plate-workbench {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: calc(100vh - 96px);
  min-height: 640px;
  padding: 4px 8px 12px;
}

.workbench-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 10px 16px;
  background: #fff;
  border: 1px solid @border;
  border-radius: 8px;

  &__stats {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.stat-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border: 1px solid @border;
  border-radius: 18px;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;

  &:hover {
    border-color: rgba(38, 108, 251, 0.4);
  }

  &.is-active {
    background: rgba(38, 108, 251, 0.06);
    border-color: rgba(38, 108, 251, 0.55);

    .stat-chip__count {
      color: @primary;
    }
  }

  &__count {
    min-width: 20px;
    font-size: 16px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
    text-align: center;
  }

  &__label {
    font-size: 13px;
    color: rgba(0, 0, 0, 0.55);
  }
}

.workbench-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 16px;
  background: #fff;
  border: 1px solid @border;
  border-radius: 8px;

  &__hint {
    margin-left: auto;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.4);
  }
}

.workbench-grid-wrap {
  flex: 1;
  min-height: 0;
  padding: 4px 8px;
  overflow-y: auto;

  :deep(.ant-spin-nested-loading) {
    min-height: 200px;
  }
}

.workbench-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;

  &__empty {
    padding: 48px 0;
  }
}

.target-card {
  position: relative;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 2px solid transparent;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(24, 24, 24, 0.1);
  overflow: hidden;
  transition: box-shadow 0.25s ease, transform 0.25s ease, border-color 0.2s;

  &:hover {
    box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
    transform: translateY(-1px);

    .target-card__overlay {
      opacity: 1;
    }
  }

  &.selected {
    border-color: @primary;
    box-shadow: 0 0 0 1px @primary, 0 3px 12px rgba(38, 108, 251, 0.15);
  }

  &__check {
    position: absolute;
    top: 8px;
    left: 8px;
    z-index: 4;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    background: #fff;
    border: 2px solid #d9d9d9;
    border-radius: 3px;
    cursor: pointer;

    .check-inner {
      width: 12px;
      height: 12px;
      border-radius: 2px;
      background: transparent;
    }

    &.checked {
      border-color: @primary;

      .check-inner {
        background: @primary;
      }
    }
  }

  &__cover {
    position: relative;
    height: 150px;
    overflow: hidden;
    background: #f5f6f8;
    cursor: pointer;
  }

  &__img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &__badge {
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 2;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 500;
    border-radius: 10px;
    color: #fff;

    &.is-pending {
      background: rgba(38, 108, 251, 0.88);
    }

    &.is-enrolled {
      background: rgba(82, 196, 26, 0.9);
    }

    &.is-discarded {
      background: rgba(0, 0, 0, 0.45);
    }
  }

  &__overlay {
    position: absolute;
    inset: 0;
    z-index: 3;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: rgba(0, 0, 0, 0.45);
    opacity: 0;
    transition: opacity 0.2s;
  }

  &__body {
    padding: 10px 12px 12px;
  }

  &__plate {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0 0 6px;
    min-width: 0;
  }

  &__color {
    margin: 0;
    flex-shrink: 0;
    font-size: 11px;
    line-height: 18px;
  }

  &__device {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0 0 6px;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.75);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
  }

  &__tag {
    margin: 0;
    margin-left: auto;
    font-size: 11px;
    line-height: 18px;
  }
}

.plate-no {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1px;
  color: rgba(0, 0, 0, 0.85);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;

  &.is-empty {
    font-size: 12px;
    font-weight: 400;
    letter-spacing: 0;
    color: rgba(0, 0, 0, 0.35);
  }
}

.overlay-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: @primary;
  font-size: 16px;
  cursor: pointer;
  transition: transform 0.15s, background 0.15s;

  &:hover {
    background: #fff;
    transform: scale(1.08);
  }

  &.is-danger {
    color: #ff4d4f;
  }
}

.workbench-pagination {
  display: flex;
  justify-content: flex-end;
  padding: 4px 8px 0;
}
</style>
