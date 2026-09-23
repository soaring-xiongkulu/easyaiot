<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    title="车辆电子身份档案"
    width="92%"
    placement="right"
    :show-footer="false"
    destroy-on-close
  >
    <div class="identity-workbench">
      <!-- 顶栏：风险统计芯片（可点筛选） + 搜索 / 刷新 -->
      <div class="workbench-bar">
        <div class="workbench-bar__stats">
          <div
            v-for="tab in riskTabs"
            :key="tab.value"
            class="stat-chip"
            :class="{ 'is-active': currentRisk === tab.value }"
            @click="switchRisk(tab.value)"
          >
            <span class="stat-chip__count">{{ counts[tab.value] ?? 0 }}</span>
            <span class="stat-chip__label">{{ tab.label }}</span>
          </div>
        </div>
        <div class="workbench-bar__actions">
          <Input
            v-model:value="search"
            style="width: 264px"
            placeholder="搜索 VID / 车牌 / 电子名称 / 车主"
            allow-clear
            @press-enter="reload"
          >
            <template #prefix><SearchOutlined /></template>
          </Input>
          <Button preIcon="ant-design:reload-outlined" :loading="loading" @click="reload">刷新</Button>
        </div>
      </div>

      <!-- 操作条：合并 + 场景提示 -->
      <div class="workbench-toolbar">
        <Button
          :disabled="selectedIds.length < 2"
          preIcon="ant-design:merge-cells-outlined"
          @click="mergeSelected"
        >
          合并所选{{ selectedIds.length ? `（${selectedIds.length}）` : '' }}
        </Button>
        <span v-if="selectedIds.length >= 2" class="workbench-toolbar__hint is-active">
          将以最先勾选的 #{{ selectedIds[0] }} 为主身份
        </span>
        <span v-else class="workbench-toolbar__hint">
          <InfoCircleOutlined />
          未入正式车牌库的车辆也会获得稳定 VID 并形成轨迹；勾选 2 个及以上身份可手动合并
        </span>
      </div>

      <!-- 身份卡片网格 -->
      <div class="workbench-grid-wrap">
        <Spin :spinning="loading" size="large">
          <div v-if="rows.length" class="workbench-grid">
            <div
              v-for="item in rows"
              :key="item.id"
              class="identity-card"
              :class="{ selected: selectedIds.includes(item.id) }"
            >
              <div
                class="identity-card__check"
                :class="{ checked: selectedIds.includes(item.id) }"
                title="勾选用于合并"
                @click.stop="toggleCheck(item.id)"
              >
                <span class="check-inner" />
              </div>
              <div class="identity-card__cover" @click="openTrajectory(item)">
                <img
                  :src="imageUrl(item.cover_image_path) || defaultPlate"
                  class="identity-card__img"
                  alt="车牌"
                  loading="lazy"
                  @error="onImgError"
                />
                <span class="identity-card__badge" :class="`is-${item.risk_status}`">
                  {{ riskLabel(item.risk_status) }}
                </span>
                <div class="identity-card__overlay">
                  <button class="overlay-btn" title="查看轨迹" @click.stop="openTrajectory(item)">
                    <NodeIndexOutlined />
                  </button>
                  <button class="overlay-btn" title="命名 / 确认车主" @click.stop="openEdit(item)">
                    <EditOutlined />
                  </button>
                </div>
              </div>
              <div class="identity-card__body">
                <p class="identity-card__name" :title="item.display_name">{{ item.display_name }}</p>
                <p class="identity-card__code" :title="item.identity_code">{{ item.identity_code }}</p>
                <p class="identity-card__plate">
                  <Tag color="blue" class="plate-tag">{{ item.current_plate_no || '未识别' }}</Tag>
                  <span v-if="item.owner_name" class="owner">车主：{{ item.owner_name }}</span>
                </p>
                <p class="identity-card__meta">
                  <span>出现 {{ item.occurrence_count }} 次</span>
                  <span class="is-muted">最近 {{ formatShortTime(item.last_seen_at) }}</span>
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
        <Pagination
          v-model:current="page"
          :page-size="pageSize"
          :total="total"
          :show-size-changer="false"
          show-quick-jumper
          :show-total="(t: number) => `共 ${t} 条`"
          @change="() => load()"
        />
      </div>
    </div>

    <!-- 轨迹抽屉 -->
    <Drawer
      v-model:open="trajectoryOpen"
      title="车辆轨迹"
      width="620"
      :get-container="false"
      class="trajectory-drawer"
    >
      <template v-if="selected">
        <div class="trajectory-profile">
          <img
            :src="imageUrl(selected.cover_image_path) || defaultPlate"
            class="trajectory-profile__avatar"
            alt="车牌"
          />
          <div class="trajectory-profile__info">
            <p class="trajectory-profile__name">
              {{ selected.display_name }}
              <Tag :color="riskColor(selected.risk_status)">{{ riskLabel(selected.risk_status) }}</Tag>
            </p>
            <p class="trajectory-profile__code">{{ selected.identity_code }}</p>
            <p class="trajectory-profile__real">
              当前车牌：{{ selected.current_plate_no || '—' }}
              <template v-if="selected.owner_name"> · 车主：{{ selected.owner_name }}</template>
            </p>
          </div>
        </div>
        <div class="trajectory-stats">
          <div class="trajectory-stats__item">
            <span class="num">{{ selected.occurrence_count }}</span>
            <span class="label">累计出现</span>
          </div>
          <div class="trajectory-stats__item">
            <span class="num">{{ selected.alias_count }}</span>
            <span class="label">关联车牌</span>
          </div>
          <div class="trajectory-stats__item">
            <span class="num">{{ formatShortTime(selected.first_seen_at) }}</span>
            <span class="label">首次出现</span>
          </div>
          <div class="trajectory-stats__item">
            <span class="num">{{ formatShortTime(selected.last_seen_at) }}</span>
            <span class="label">最近出现</span>
          </div>
        </div>
      </template>

      <Spin :spinning="trajectoryLoading" size="large">
        <template v-if="groupedTrajectory.length">
          <p class="trajectory-section-title">按天分组 · 共 {{ trajectory.length }} 条记录</p>
          <div v-for="group in groupedTrajectory" :key="group.date" class="trajectory-group">
            <p class="trajectory-group__date">{{ group.date }}</p>
            <Timeline>
              <TimelineItem v-for="point in group.points" :key="point.id">
                <div class="trajectory-point">
                  <img
                    v-if="point.plate_image_path"
                    :src="imageUrl(point.plate_image_path)"
                    class="trajectory-point__img"
                    alt="车牌快照"
                    loading="lazy"
                  />
                  <div class="trajectory-point__info">
                    <p class="trajectory-point__time">
                      {{ formatClockTime(point.created_at) }} · {{ point.normalized_plate_no || point.plate_no || '未识别' }}
                    </p>
                    <p class="trajectory-point__device" :title="point.device_name || point.device_id">
                      <VideoCameraOutlined />
                      {{ point.device_name || point.device_id || '未知设备' }}
                      <template v-if="point.vehicle_resolution">
                        · {{ vehicleResolutionLabel(point.vehicle_resolution) }}
                      </template>
                    </p>
                  </div>
                </div>
              </TimelineItem>
            </Timeline>
          </div>
        </template>
        <Empty
          v-else-if="!trajectoryLoading"
          description="暂无轨迹记录"
          :image="Empty.PRESENTED_IMAGE_SIMPLE"
        />
      </Spin>
    </Drawer>

    <!-- 命名 / 确认弹框 -->
    <Modal
      v-model:open="editOpen"
      title="命名与确认车辆身份"
      :confirm-loading="saving"
      ok-text="保存"
      cancel-text="取消"
      @ok="saveIdentity"
    >
      <div class="edit-form">
        <div class="edit-form__item">
          <label class="edit-form__label">车辆编码</label>
          <Input :value="selected?.identity_code" disabled />
        </div>
        <div class="edit-form__item">
          <label class="edit-form__label">电子名称</label>
          <Input v-model:value="editForm.display_name" placeholder="用于轨迹与告警中展示" />
        </div>
        <div class="edit-form__item">
          <label class="edit-form__label">车主</label>
          <Input v-model:value="editForm.owner_name" placeholder="未知可留空" />
          <p class="edit-form__help">填写车主后，该身份将自动标记为「已确认」；历史轨迹保持不变</p>
        </div>
        <div class="edit-form__item">
          <label class="edit-form__label">风险状态</label>
          <Select v-model:value="editForm.risk_status" style="width: 100%">
            <SelectOption value="normal">正常</SelectOption>
            <SelectOption value="review">待复核</SelectOption>
            <SelectOption value="suspected_clone">疑似套牌</SelectOption>
          </Select>
        </div>
        <div class="edit-form__item">
          <label class="edit-form__label">备注</label>
          <Textarea v-model:value="editForm.remark" :rows="3" placeholder="选填" />
        </div>
      </div>
    </Modal>
  </BasicDrawer>
</template>

<script lang="ts" setup>
/**
 * 车辆电子身份档案：按稳定 VID 管理算法归并出的车辆身份。
 * 支持风险筛选、搜索、手动合并、命名确认与按天分组轨迹查看。
 */
import { computed, ref } from 'vue';
import {
  Drawer,
  Empty,
  Input as AInput,
  Modal,
  Pagination,
  Select,
  SelectOption,
  Spin,
  Tag,
  Textarea,
  Timeline,
  TimelineItem,
} from 'ant-design-vue';
import {
  EditOutlined,
  InfoCircleOutlined,
  NodeIndexOutlined,
  SearchOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import {
  getVehicleIdentityTrajectory,
  listVehicleIdentities,
  mergeVehicleIdentities,
  resolvePlateImageDisplayUrl,
  updateVehicleIdentity,
  type PlateMatchRecord,
  type VehicleIdentity,
} from '@/api/device/plate_library';
import DEFAULT_PLATE_IMAGE from '@/assets/images/video/snap-task.png';

defineOptions({ name: 'VehicleIdentityDrawer' });

const Input = AInput;
const { createMessage } = useMessage();
const defaultPlate = DEFAULT_PLATE_IMAGE;

type RiskFilter = 'all' | 'normal' | 'review' | 'suspected_clone';

const riskTabs: Array<{ value: RiskFilter; label: string }> = [
  { value: 'all', label: '全部' },
  { value: 'normal', label: '正常' },
  { value: 'review', label: '待复核' },
  { value: 'suspected_clone', label: '疑似套牌' },
];

const rows = ref<VehicleIdentity[]>([]);
const loading = ref(false);
const search = ref('');
const currentRisk = ref<RiskFilter>('all');
const counts = ref<Record<RiskFilter, number>>({ all: 0, normal: 0, review: 0, suspected_clone: 0 });
const page = ref(1);
const pageSize = 20;
const total = ref(0);
const selectedIds = ref<number[]>([]);

const selected = ref<VehicleIdentity>();
const trajectory = ref<PlateMatchRecord[]>([]);
const trajectoryLoading = ref(false);
const trajectoryOpen = ref(false);
const editOpen = ref(false);
const saving = ref(false);
const editForm = ref({ display_name: '', owner_name: '', risk_status: 'normal', remark: '' });

const groupedTrajectory = computed(() => {
  const groups: Array<{ date: string; points: PlateMatchRecord[] }> = [];
  const index = new Map<string, number>();
  for (const point of trajectory.value) {
    const date = (point.created_at || '').slice(0, 10);
    let at = index.get(date);
    if (at == null) {
      at = groups.length;
      index.set(date, at);
      groups.push({ date, points: [] });
    }
    groups[at].points.push(point);
  }
  return groups;
});

const emptyText = computed(() =>
  search.value.trim() ? '没有匹配的车辆身份，换个关键词试试' : '暂无车辆身份档案，算法识别到车辆后会自动归档',
);

const [register] = useDrawerInner(async () => {
  page.value = 1;
  await reload();
});

function imageUrl(path?: string) {
  return resolvePlateImageDisplayUrl(path ? `/video/alert/image?path=${encodeURIComponent(path)}` : '');
}

function onImgError(e: Event) {
  (e.target as HTMLImageElement).src = defaultPlate;
}

function riskLabel(value: string) {
  return (
    ({ normal: '正常', review: '待复核', suspected_clone: '疑似套牌' } as Record<string, string>)[value] ||
    value
  );
}

function riskColor(value: string) {
  return (
    ({ normal: 'green', review: 'orange', suspected_clone: 'red' } as Record<string, string>)[value] ||
    'default'
  );
}

function vehicleResolutionLabel(value: string) {
  return (
    ({ new: '新建档', matched: '已匹配', confirmed: '已确认' } as Record<string, string>)[value] || value
  );
}

function formatShortTime(value?: string) {
  // 完整时间太长，卡片里只展示 月-日 时:分
  return value ? value.replace('T', ' ').replace('Z', '').slice(5, 16) : '—';
}

function formatClockTime(value?: string) {
  return value ? value.replace('T', ' ').replace('Z', '').slice(11, 19) : '—';
}

async function load() {
  loading.value = true;
  try {
    const res = await listVehicleIdentities({
      page: page.value,
      pageSize,
      risk_status: currentRisk.value === 'all' ? undefined : currentRisk.value,
      search: search.value || undefined,
    });
    rows.value = res.list || [];
    total.value = res.total || 0;
  } catch (error: any) {
    createMessage.error(error?.message || '加载车辆身份失败');
  } finally {
    loading.value = false;
  }
}

/** 各风险等级总数来自独立查询，仅在新数据落地后刷新，翻页不打扰 */
async function loadStats() {
  try {
    const [all, normal, review, clone] = await Promise.all([
      listVehicleIdentities({ page: 1, pageSize: 1 }),
      listVehicleIdentities({ page: 1, pageSize: 1, risk_status: 'normal' }),
      listVehicleIdentities({ page: 1, pageSize: 1, risk_status: 'review' }),
      listVehicleIdentities({ page: 1, pageSize: 1, risk_status: 'suspected_clone' }),
    ]);
    counts.value = {
      all: all.total || 0,
      normal: normal.total || 0,
      review: review.total || 0,
      suspected_clone: clone.total || 0,
    };
  } catch {
    // 统计失败不阻塞列表展示
  }
}

async function reload() {
  await Promise.all([load(), loadStats()]);
}

function switchRisk(value: RiskFilter) {
  currentRisk.value = value;
  page.value = 1;
  void load();
}

function toggleCheck(id: number) {
  const at = selectedIds.value.indexOf(id);
  if (at >= 0) {
    selectedIds.value.splice(at, 1);
  } else {
    selectedIds.value.push(id);
  }
}

async function openTrajectory(record: VehicleIdentity) {
  selected.value = record;
  trajectoryOpen.value = true;
  trajectoryLoading.value = true;
  try {
    const res = await getVehicleIdentityTrajectory(record.id, { limit: 500 });
    trajectory.value = res.data?.points || [];
  } catch (error: any) {
    createMessage.error(error?.message || '加载轨迹失败');
  } finally {
    trajectoryLoading.value = false;
  }
}

function openEdit(record: VehicleIdentity) {
  selected.value = record;
  editForm.value = {
    display_name: record.display_name || '',
    owner_name: record.owner_name || '',
    risk_status: record.risk_status || 'normal',
    remark: record.remark || '',
  };
  editOpen.value = true;
}

async function saveIdentity() {
  if (!selected.value) return;
  if (!editForm.value.display_name.trim()) {
    createMessage.warning('电子名称不能为空');
    return;
  }
  saving.value = true;
  try {
    await updateVehicleIdentity(selected.value.id, {
      display_name: editForm.value.display_name.trim(),
      owner_name: editForm.value.owner_name.trim() || undefined,
      risk_status: editForm.value.risk_status as VehicleIdentity['risk_status'],
      remark: editForm.value.remark.trim() || undefined,
      status: editForm.value.owner_name.trim() ? 'confirmed' : 'anonymous',
    });
    editOpen.value = false;
    createMessage.success('车辆身份已更新');
    await reload();
  } catch (error: any) {
    createMessage.error(error?.message || '保存失败');
  } finally {
    saving.value = false;
  }
}

function mergeSelected() {
  if (selectedIds.value.length < 2) return;
  const [targetId, ...sourceIds] = selectedIds.value;
  Modal.confirm({
    title: '确认合并车辆身份？',
    content: `将以最先勾选的 #${targetId} 为主身份，合并其余 ${sourceIds.length} 个身份；轨迹和样本会一并归集，操作不可撤销。`,
    okText: '确认合并',
    cancelText: '再想想',
    onOk: async () => {
      try {
        await mergeVehicleIdentities(targetId, sourceIds);
        selectedIds.value = [];
        createMessage.success('车辆身份已合并');
        await reload();
      } catch (error: any) {
        createMessage.error(error?.message || '合并失败');
      }
    },
  });
}
</script>

<style lang="less" scoped>
@border: #f0f0f0;
@primary: #266cfb;

.identity-workbench {
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
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.4);

    &.is-active {
      color: @primary;
    }
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
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 16px;

  &__empty {
    padding: 48px 0;
  }
}

.identity-card {
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

    .identity-card__overlay {
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
    height: 120px;
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

    &.is-normal {
      background: rgba(82, 196, 26, 0.9);
    }

    &.is-review {
      background: rgba(250, 173, 20, 0.92);
    }

    &.is-suspected_clone {
      background: rgba(255, 77, 79, 0.92);
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

  &__name {
    margin: 0 0 2px;
    font-size: 14px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__code {
    margin: 0 0 6px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.4);
    font-family: monospace;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__plate {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 6px;
    min-width: 0;

    .plate-tag {
      margin: 0;
    }

    .owner {
      font-size: 12px;
      color: rgba(0, 0, 0, 0.55);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }

  &__meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin: 0;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.6);

    .is-muted {
      color: rgba(0, 0, 0, 0.4);
    }
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
}

.workbench-pagination {
  display: flex;
  justify-content: flex-end;
  padding: 4px 8px 0;
}

// ---- 轨迹抽屉 ----
.trajectory-profile {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 4px 0 14px;

  &__avatar {
    width: 96px;
    height: 56px;
    border-radius: 8px;
    object-fit: cover;
    background: #f5f6f8;
  }

  &__info {
    min-width: 0;
  }

  &__name {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 4px;
    font-size: 16px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.85);
  }

  &__code {
    margin: 0 0 2px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.4);
    font-family: monospace;
  }

  &__real {
    margin: 0;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.55);
  }
}

.trajectory-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  padding: 12px 0;
  margin-bottom: 6px;
  border-top: 1px solid @border;
  border-bottom: 1px solid @border;

  &__item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;

    .num {
      font-size: 15px;
      font-weight: 600;
      color: rgba(0, 0, 0, 0.85);
    }

    .label {
      font-size: 12px;
      color: rgba(0, 0, 0, 0.45);
    }
  }
}

.trajectory-section-title {
  margin: 0 0 12px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.4);
}

.trajectory-group {
  margin-bottom: 8px;

  &__date {
    margin: 0 0 10px;
    font-size: 13px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.65);
  }
}

.trajectory-point {
  display: flex;
  align-items: flex-start;
  gap: 10px;

  &__img {
    width: 110px;
    max-height: 64px;
    object-fit: cover;
    border-radius: 6px;
    background: #f5f6f8;
  }

  &__info {
    padding-top: 2px;
    min-width: 0;
  }

  &__time {
    margin: 0 0 4px;
    font-size: 13px;
    font-weight: 500;
    color: rgba(0, 0, 0, 0.75);
    font-family: monospace;
  }

  &__device {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.5);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

// ---- 命名弹框 ----
.edit-form {
  padding-top: 4px;

  &__item {
    margin-bottom: 16px;

    &:last-child {
      margin-bottom: 0;
    }
  }

  &__label {
    display: block;
    margin-bottom: 6px;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.65);
  }

  &__help {
    margin: 6px 0 0;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.4);
  }
}
</style>
