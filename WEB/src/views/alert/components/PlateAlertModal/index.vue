<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="告警图片"
    :footer="null"
    :maskClosable="true"
    @cancel="handleCancel"
  >
    <div class="plate-alert-modal">
      <!-- 左侧：主模型检测到的告警全景图 -->
      <div class="plate-alert-modal__scene">
        <img
          v-if="panoramaUrl && !sceneError"
          :src="panoramaUrl"
          alt="告警全景图"
          class="plate-alert-modal__scene-img"
          @error="sceneError = true"
        />
        <div v-else class="plate-alert-modal__scene-empty">
          <Icon icon="ant-design:picture-outlined" :size="48" />
          <span>告警图片不存在</span>
        </div>
      </div>

      <!-- 右侧：车牌识别信息面板 -->
      <div class="plate-alert-modal__panel">
        <!-- 车牌区：单个/多个车牌卡片 -->
        <div v-if="plateMatches.length === 1" class="plate-alert-modal__plate">
          <div
            class="plate-alert-modal__thumb-wrap"
            :title="plateNo ? `查看 ${plateNo} 的出现轨迹` : '车牌图片'"
            @click="openTrajectory"
          >
            <div class="plate-alert-modal__thumb">
              <img v-if="current.plateUrl" :src="current.plateUrl" alt="车牌图片" />
              <Icon v-else icon="ant-design:car-outlined" :size="28" />
            </div>
            <span v-if="plateNo" class="plate-alert-modal__thumb-hint">出现轨迹</span>
            <button
              v-if="plateNo"
              type="button"
              class="plate-alert-modal__thumb-trajectory"
              :title="`查看 ${plateNo} 的出现轨迹`"
              @click.stop="openTrajectory"
            >
              <Icon icon="icon-park-outline:map-draw" :size="14" />
            </button>
          </div>
          <div class="plate-alert-modal__identity">
            <div class="plate-alert-modal__name">{{ current.plateNo || '未知车牌' }}</div>
            <div class="plate-alert-modal__sub">
              <span v-if="current.plateColor" class="color">{{ current.plateColor }}</span>
              <span v-if="current.matchRecordId != null" class="record">匹配记录 #{{ current.matchRecordId }}</span>
            </div>
            <div v-if="current.ownerName" class="plate-alert-modal__owner">
              车主：<b>{{ current.ownerName }}</b>
            </div>
            <div v-if="current.detectConf != null" class="plate-alert-modal__score">
              <span class="score-value">{{ formatConf(current.detectConf) }}</span>
              <span class="score-label">识别置信度</span>
            </div>
          </div>
        </div>

        <div v-else-if="plateMatches.length > 1" class="plate-alert-modal__plates">
          <div class="section-title">命中车牌（{{ plateMatches.length }}）</div>
          <div class="plate-alert-modal__plate-cards">
            <div
              v-for="(m, idx) in plateMatches"
              :key="m.matchRecordId ?? idx"
              class="plate-card"
              :class="{ 'plate-card--active': idx === selectedIndex }"
              @click="selectedIndex = idx"
            >
              <div
                class="plate-card__thumb-wrap"
                :title="m.plateNo ? `查看 ${m.plateNo} 的出现轨迹` : '车牌图片'"
                @click.stop="m.plateNo && openTrajectoryFor(m.plateNo)"
              >
                <div class="plate-card__thumb">
                  <img v-if="m.plateUrl" :src="m.plateUrl" alt="车牌图片" />
                  <Icon v-else icon="ant-design:car-outlined" :size="16" />
                </div>
                <span v-if="m.plateNo" class="plate-alert-modal__thumb-hint">出现轨迹</span>
                <button
                  v-if="m.plateNo"
                  type="button"
                  class="plate-alert-modal__thumb-trajectory"
                  :title="`查看 ${m.plateNo} 的出现轨迹`"
                  @click.stop="openTrajectoryFor(m.plateNo)"
                >
                  <Icon icon="icon-park-outline:map-draw" :size="12" />
                </button>
              </div>
              <div class="plate-card__info">
                <div class="plate-card__no">{{ m.plateNo || '未知车牌' }}</div>
                <div class="plate-card__conf">{{ formatConf(m.detectConf) }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 事实区：什么车 / 在什么地方 / 造成了什么事件 -->
        <div class="plate-alert-modal__facts">
          <div class="fact">
            <span class="fact__label">车牌</span>
            <span class="fact__value">{{ allPlatesText }}</span>
          </div>
          <div class="fact">
            <span class="fact__label">车主</span>
            <span class="fact__value">{{ allOwnersText }}</span>
          </div>
          <div class="fact">
            <span class="fact__label">地点</span>
            <span class="fact__value">{{ locationText }}</span>
          </div>
          <div class="fact">
            <span class="fact__label">事件</span>
            <span class="fact__value">{{ eventText }}</span>
          </div>
          <div class="fact">
            <span class="fact__label">时间</span>
            <span class="fact__value">{{ alertTime || '-' }}</span>
          </div>
        </div>

        <!-- 匹配详情区（跟随选中车牌） -->
        <div class="plate-alert-modal__match">
          <div class="section-title">
            匹配详情
            <template v-if="plateMatches.length > 1 && current.plateNo"> · {{ current.plateNo }}</template>
          </div>
          <div class="plate-alert-modal__meta">
            <span v-if="current.libraryName">车牌库：{{ current.libraryName }}</span>
            <span v-if="taskName">任务：{{ taskName }}</span>
            <span v-if="deviceName">设备：{{ deviceName }}</span>
          </div>
          <div v-if="current.ownerName" class="plate-alert-modal__owner-row">
            <span class="label">车主</span>
            <span class="value">{{ current.ownerName }}</span>
          </div>
        </div>
      </div>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { computed, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Icon } from '@/components/Icon';
import { resolveAlertImageDisplayUrl } from '@/utils/alertMinioImage';
import {
  formatAlertEvent,
  getAlertPlateMatchInfos,
  type PlateMatchInfo,
} from '@/views/alert/alertDisplay';

defineOptions({ name: 'PlateAlertModal' });

const [register, { setModalProps, closeModal }] = useModalInner((data) => {
  applyModalLayout();
  state.record = data?.record || null;
  sceneError.value = false;
  selectedIndex.value = 0;
});

const router = useRouter();

const state = reactive<{ record: Record<string, any> | null }>({ record: null });
const sceneError = ref(false);
const selectedIndex = ref(0);

/** 固定弹框尺寸：整体高度（含标题栏）不超过屏幕，上下各留 8vh 呼吸空间 */
function applyModalLayout() {
  setModalProps({
    defaultFullscreen: false,
    canFullscreen: false,
    width: 'min(1440px, 94vw)',
    minHeight: 0,
    bodyStyle: { padding: 0 },
    wrapClassName: 'plate-alert-modal-wrap',
  });
}

interface PlateMatchView {
  matchRecordId: number | null;
  plateNo: string;
  plateColor: string;
  ownerName: string;
  detectConf: number | null;
  libraryName: string;
  plateUrl: string;
}

function toPlateMatchView(pm: PlateMatchInfo): PlateMatchView {
  const plateUrl = pm.plate_image_url ? resolveAlertImageDisplayUrl(pm.plate_image_url) : '';
  return {
    matchRecordId: pm.match_record_id ?? null,
    plateNo: pm.plate_no || '',
    plateColor: pm.plate_color || '',
    ownerName: pm.matched_owner_name || '',
    detectConf: pm.detect_conf ?? null,
    libraryName: pm.library_name || '',
    plateUrl,
  };
}

/** 全部命中车牌（同一帧画面可能识别到多个车牌） */
const plateMatches = computed<PlateMatchView[]>(() => {
  const record = state.record;
  if (!record) return [];
  return getAlertPlateMatchInfos(record).map(toPlateMatchView);
});

/** 当前选中车牌（多车牌布局中点击切换） */
const current = computed<PlateMatchView>(() => {
  const list = plateMatches.value;
  const idx = Math.min(selectedIndex.value, Math.max(0, list.length - 1));
  return list[idx] || ({} as PlateMatchView);
});

/** 当前选中车牌号（车牌图点击/出现轨迹入口） */
const plateNo = computed(() => current.value.plateNo || '');

/** 左侧：告警全景图（主模型检测整帧画面） */
const panoramaUrl = computed(() => {
  const record = state.record;
  if (!record?.image_url) return '';
  return resolveAlertImageDisplayUrl(record.image_url);
});

/** 全部命中车牌号（事实区"车牌"行） */
const allPlatesText = computed(() => {
  const list = plateMatches.value;
  if (!list.length) return '-';
  return list
    .map((m) => (m.plateNo ? `${m.plateNo}${m.detectConf != null ? `（${formatConf(m.detectConf)}）` : ''}` : '未知'))
    .join('、');
});

/** 全部命中车主（事实区"车主"行） */
const allOwnersText = computed(() => {
  const list = plateMatches.value;
  if (!list.length) return '-';
  return list.map((m) => m.ownerName || '-').join('、');
});

const deviceName = computed(() => state.record?.device_name || '');
const region = computed(() => state.record?.region || '');
const taskName = computed(() => state.record?.task_name || '');
const alertTime = computed(() => state.record?.time || '');

/** 地点：设备名 + 检测区域 */
const locationText = computed(() => {
  const parts = [deviceName.value, region.value].filter(Boolean);
  return parts.length ? parts.join(' · ') : '-';
});

/** 事件：告警事件类型 */
const eventText = computed(() => formatAlertEvent(state.record?.event));

/** 行为：触发该告警的算法事件（车牌弹框在事实区以事件行呈现，行为并入事件） */

function formatConf(conf: unknown): string {
  if (conf == null || Number.isNaN(Number(conf))) return '-';
  return `${(Number(conf) * 100).toFixed(1)}%`;
}

function openTrajectory() {
  if (!plateNo.value) return;
  openTrajectoryFor(plateNo.value);
}

function openTrajectoryFor(plate: string) {
  // 跳转告警页地图分布：先发起跳转，成功后再关闭当前弹框（避免先关弹框导致跳转被中断）
  router
    .push({
      path: '/alert',
      query: {
        tab: '1',
        trajectory_plate: plate,
        trajectory_date: new Date().toISOString().slice(0, 10),
      },
    })
    .then(() => closeModal())
    .catch(() => closeModal());
}

function handleCancel() {
  state.record = null;
  sceneError.value = false;
  selectedIndex.value = 0;
  closeModal();
}
</script>

<style lang="less">
// 白色苹果风：浅灰画布、白卡片、深灰文字、蓝色点缀（与人脸弹框同一视觉体系）
.plate-alert-modal-wrap {
  .ant-modal {
    top: 8vh;
    height: 84vh;
    max-height: 84vh;
    padding-bottom: 0;
    display: flex;
    flex-direction: column;
  }

  .ant-modal-content {
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .ant-modal-header {
    flex: 0 0 auto;
  }

  .ant-modal-body {
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
    padding: 0;
  }

  .plate-alert-modal {
    display: flex;
    height: 100%;
    background: #f5f5f7;

    // 左侧：告警全景图舞台
    &__scene {
      position: relative;
      flex: 0 0 64%;
      background: #f5f5f7;
      border-right: 1px solid #e5e5ea;

      &-img {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: contain;
      }

      &-empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 12px;
        height: 100%;
        color: #8e8e93;
        font-size: 14px;
      }
    }

    // 右侧：车牌信息面板
    &__panel {
      flex: 1 1 0;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 16px;
      padding: 24px;
      overflow-y: auto;
      background: #f5f5f7;
    }

    // 单车牌大卡片
    &__plate {
      display: flex;
      align-items: center;
      gap: 18px;
      padding: 20px;
      background: #fff;
      border-radius: 16px;
      border: 1px solid #e5e5ea;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
    }

    &__thumb-wrap {
      position: relative;
      flex: 0 0 auto;
      cursor: pointer;
    }

    &__thumb {
      width: 96px;
      height: 96px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 12px;
      background: #f0f0f2;
      border: 1px solid #e5e5ea;
      overflow: hidden;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    &__thumb-hint {
      position: absolute;
      left: 50%;
      bottom: -18px;
      transform: translateX(-50%);
      padding: 1px 8px;
      border-radius: 8px;
      background: #266cfb;
      color: #fff;
      font-size: 11px;
      white-space: nowrap;
      pointer-events: none;
    }

    &__thumb-trajectory {
      position: absolute;
      right: -6px;
      top: -6px;
      width: 24px;
      height: 24px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: none;
      border-radius: 50%;
      background: #fff;
      color: #266cfb;
      box-shadow: 0 2px 8px rgba(38, 108, 251, 0.35);
      cursor: pointer;
      z-index: 2;
    }

    &__identity {
      min-width: 0;
      flex: 1;
    }

    &__name {
      font-size: 28px;
      font-weight: 700;
      color: #1d1d1f;
      letter-spacing: 2px;
      line-height: 1.3;
    }

    &__sub {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 6px;

      .color {
        padding: 2px 10px;
        border-radius: 10px;
        background: #eef4ff;
        color: #266cfb;
        font-size: 12px;
      }

      .record {
        color: #8e8e93;
        font-size: 12px;
      }
    }

    &__owner {
      margin-top: 8px;
      color: #48484a;
      font-size: 13px;

      b {
        color: #1d1d1f;
      }
    }

    &__score {
      display: flex;
      align-items: baseline;
      gap: 8px;
      margin-top: 10px;

      .score-value {
        font-size: 18px;
        font-weight: 700;
        color: #266cfb;
      }

      .score-label {
        color: #8e8e93;
        font-size: 12px;
      }
    }

    // 多车牌横向卡片
    &__plates {
      padding: 20px;
      background: #fff;
      border-radius: 16px;
      border: 1px solid #e5e5ea;
    }

    &__plate-cards {
      display: flex;
      gap: 12px;
      margin-top: 12px;
      overflow-x: auto;
    }

    .plate-card {
      flex: 0 0 120px;
      padding: 12px;
      border-radius: 12px;
      border: 2px solid transparent;
      background: #fafafa;
      cursor: pointer;
      transition: border-color 0.15s;

      &--active {
        border-color: #266cfb;
        background: #f4f8ff;
      }

      &__thumb-wrap {
        position: relative;
      }

      &__thumb {
        width: 100%;
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: #f0f0f2;
        overflow: hidden;

        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }

      &__info {
        margin-top: 8px;
        text-align: center;
      }

      &__no {
        font-size: 13px;
        font-weight: 600;
        color: #1d1d1f;
      }

      &__conf {
        font-size: 11px;
        color: #266cfb;
        margin-top: 2px;
      }
    }

    // 事实区
    &__facts {
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding: 16px 20px;
      background: #fff;
      border-radius: 16px;
      border: 1px solid #e5e5ea;

      .fact {
        display: flex;
        gap: 16px;
        font-size: 13px;

        &__label {
          flex: 0 0 56px;
          color: #8e8e93;
        }

        &__value {
          min-width: 0;
          flex: 1;
          color: #1d1d1f;
          word-break: break-all;
        }
      }
    }

    // 匹配详情区
    &__match {
      padding: 16px 20px;
      background: #fff;
      border-radius: 16px;
      border: 1px solid #e5e5ea;
    }

    .section-title {
      font-size: 14px;
      font-weight: 600;
      color: #1d1d1f;
    }

    &__meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 18px;
      margin-top: 10px;
      color: #48484a;
      font-size: 13px;
    }

    &__owner-row {
      display: flex;
      gap: 16px;
      margin-top: 12px;
      font-size: 13px;

      .label {
        flex: 0 0 56px;
        color: #8e8e93;
      }

      .value {
        color: #1d1d1f;
      }
    }
  }
}
</style>
