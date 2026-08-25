<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="告警图片"
    :footer="null"
    :maskClosable="true"
    @cancel="handleCancel"
  >
    <div class="face-alert-modal">
      <!-- 左侧：主模型检测到的告警全景图（人脸检测为任务附带的一路独立识别） -->
      <div class="face-alert-modal__scene">
        <img
          v-if="panoramaUrl && !sceneError"
          :src="panoramaUrl"
          alt="告警全景图"
          class="face-alert-modal__scene-img"
          @error="sceneError = true"
        />
        <div v-else class="face-alert-modal__scene-empty">
          <Icon icon="ant-design:picture-outlined" :size="48" />
          <span>告警图片不存在</span>
        </div>
      </div>

      <!-- 右侧：人脸识别信息面板 -->
      <div class="face-alert-modal__panel">
        <!-- 人物区：单人大卡片 / 多人横向人员卡片 -->
        <div v-if="faceMatches.length === 1" class="face-alert-modal__person">
          <div
            class="face-alert-modal__avatar-wrap"
            :title="personName ? `查看 ${personName} 的出现轨迹` : '人脸头像'"
            @click="openTrajectory"
          >
            <div class="face-alert-modal__avatar">
              <img v-if="current.faceUrl" :src="current.faceUrl" alt="人脸头像" />
              <Icon v-else icon="ant-design:user-outlined" :size="28" />
            </div>
            <span v-if="personName" class="face-alert-modal__avatar-hint">出现轨迹</span>
            <button
              v-if="personName"
              type="button"
              class="face-alert-modal__avatar-trajectory"
              :title="`查看 ${personName} 的出现轨迹`"
              @click.stop="openTrajectory"
            >
              <Icon icon="icon-park-outline:map-draw" :size="14" />
            </button>
          </div>
          <div class="face-alert-modal__identity">
            <div class="face-alert-modal__name">{{ current.personName || '未知人员' }}</div>
            <div class="face-alert-modal__sub">
              <span v-if="current.personCode" class="code">{{ current.personCode }}</span>
              <span v-if="current.matchRecordId != null" class="record">匹配记录 #{{ current.matchRecordId }}</span>
            </div>
            <div v-if="current.similarity != null" class="face-alert-modal__score">
              <span class="score-value">{{ formatSim(current.similarity) }}</span>
              <span class="score-label">相似度 · 阈值 {{ current.threshold ?? '-' }}</span>
            </div>
          </div>
        </div>

        <div v-else-if="faceMatches.length > 1" class="face-alert-modal__persons">
          <div class="section-title">命中人员（{{ faceMatches.length }}）</div>
          <div class="face-alert-modal__person-cards">
            <div
              v-for="(m, idx) in faceMatches"
              :key="m.matchRecordId ?? idx"
              class="person-card"
              :class="{ 'person-card--active': idx === selectedIndex }"
              @click="selectedIndex = idx"
            >
              <div
                class="person-card__avatar-wrap"
                :title="m.personName ? `查看 ${m.personName} 的出现轨迹` : '人脸头像'"
                @click.stop="m.personName && openTrajectoryFor(m.personName)"
              >
                <div class="person-card__avatar">
                  <img v-if="m.faceUrl" :src="m.faceUrl" alt="人脸头像" />
                  <Icon v-else icon="ant-design:user-outlined" :size="16" />
                </div>
                <span v-if="m.personName" class="face-alert-modal__avatar-hint">出现轨迹</span>
                <button
                  v-if="m.personName"
                  type="button"
                  class="face-alert-modal__avatar-trajectory"
                  :title="`查看 ${m.personName} 的出现轨迹`"
                  @click.stop="openTrajectoryFor(m.personName)"
                >
                  <Icon icon="icon-park-outline:map-draw" :size="12" />
                </button>
              </div>
              <div class="person-card__info">
                <div class="person-card__name">{{ m.personName || '未知人员' }}</div>
                <div class="person-card__sim">{{ formatSim(m.similarity) }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 事实区：什么人 / 在什么地方 / 做了什么行为 / 造成了什么事件 -->
        <div class="face-alert-modal__facts">
          <div class="fact">
            <span class="fact__label">人物</span>
            <span class="fact__value">{{ allPersonsText }}</span>
          </div>
          <div class="fact">
            <span class="fact__label">地点</span>
            <span class="fact__value">{{ locationText }}</span>
          </div>
          <div class="fact">
            <span class="fact__label">行为</span>
            <span class="fact__value">{{ behaviorText }}</span>
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

        <!-- 匹配详情区（跟随选中人员） -->
        <div class="face-alert-modal__match">
          <div class="section-title">
            匹配详情
            <template v-if="faceMatches.length > 1 && current.personName"> · {{ current.personName }}</template>
          </div>
          <div class="face-alert-modal__meta">
            <span v-if="current.libraryName">人脸库：{{ current.libraryName }}</span>
            <span v-if="taskName">任务：{{ taskName }}</span>
            <span v-if="deviceName">设备：{{ deviceName }}</span>
          </div>
          <div v-if="current.candidates.length" class="face-alert-modal__candidates">
            <div
              v-for="(c, idx) in current.candidates"
              :key="idx"
              class="face-alert-modal__candidate"
              :class="{ 'face-alert-modal__candidate--hit': c.matched }"
            >
              <span class="rank">{{ idx + 1 }}</span>
              <span class="name">{{ c.person_name || '未知' }}</span>
              <span class="bar">
                <span class="bar-fill" :style="{ width: barWidth(c.similarity) }" />
              </span>
              <span class="sim">{{ formatSim(c.similarity) }}</span>
            </div>
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
import { useMessage } from '@/hooks/web/useMessage';
import { resolveAlertImageDisplayUrl } from '@/utils/alertMinioImage';
import {
  formatAlertEvent,
  getAlertFaceMatchInfos,
  parseAlertInformation,
  type FaceMatchInfo,
} from '@/views/alert/alertDisplay';

defineOptions({ name: 'FaceAlertModal' });

const { createMessage } = useMessage();
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
    wrapClassName: 'face-alert-modal-wrap',
  });
}

interface FaceMatchView {
  matchRecordId: number | null;
  personName: string;
  personCode: string;
  similarity: number | null;
  threshold: number | null;
  libraryName: string;
  faceUrl: string;
  candidates: any[];
}

function toFaceMatchView(fm: FaceMatchInfo): FaceMatchView {
  const faceUrl = fm.face_image_url ? resolveAlertImageDisplayUrl(fm.face_image_url) : '';
  return {
    matchRecordId: fm.match_record_id ?? null,
    personName: fm.matched_person_name || '',
    personCode: fm.matched_person_code || '',
    similarity: fm.similarity ?? null,
    threshold: fm.threshold ?? null,
    libraryName: fm.library_name || '',
    faceUrl,
    candidates: Array.isArray(fm.candidates) ? (fm.candidates as any[]) : [],
  };
}

/** 全部命中人员（同一帧画面可能匹配到多个人） */
const faceMatches = computed<FaceMatchView[]>(() => {
  const record = state.record;
  if (!record) return [];
  return getAlertFaceMatchInfos(record).map(toFaceMatchView);
});

/** 当前选中人员（多人布局中点击切换） */
const current = computed<FaceMatchView>(() => {
  const list = faceMatches.value;
  const idx = Math.min(selectedIndex.value, Math.max(0, list.length - 1));
  return list[idx] || ({} as FaceMatchView);
});

/** 当前选中人员姓名（头像点击/出现轨迹入口） */
const personName = computed(() => current.value.personName || '');

/** 左侧：告警全景图（主模型检测整帧画面） */
const panoramaUrl = computed(() => {
  const record = state.record;
  if (!record?.image_url) return '';
  return resolveAlertImageDisplayUrl(record.image_url);
});

/** 全部命中人员姓名（事实区"人物"行） */
const allPersonsText = computed(() => {
  const list = faceMatches.value;
  if (!list.length) return '-';
  return list
    .map((m) => (m.personName ? `${m.personName}${m.similarity != null ? `（${formatSim(m.similarity)}）` : ''}` : '未知'))
    .join('、');
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

/** 行为：触发该告警的算法事件 */
const behaviorText = computed(() => {
  const record = state.record;
  if (!record) return '-';
  const info = parseAlertInformation(record.information);
  const sourceEvent = info?.source_event ? String(info.source_event) : '';
  if (sourceEvent) return formatAlertEvent(sourceEvent);
  const detections = Array.isArray(info?.detections) ? (info.detections as any[]) : [];
  if (detections.length) {
    const names = detections.map((d) => d.class_name || '目标').filter(Boolean);
    return `检测到 ${Array.from(new Set(names)).join('、')} 目标`;
  }
  if (record.object) return `检测到 ${record.object} 目标`;
  return '目标出现';
});

/** 事件：告警事件类型 */
const eventText = computed(() => formatAlertEvent(state.record?.event));

function formatSim(sim: unknown): string {
  if (sim == null || Number.isNaN(Number(sim))) return '-';
  return `${(Number(sim) * 100).toFixed(1)}%`;
}

function openTrajectory() {
  if (!personName.value) return;
  openTrajectoryFor(personName.value);
}

function openTrajectoryFor(name: string) {
  // 跳转告警页地图分布：先发起跳转，成功后再关闭当前弹框（避免先关弹框导致跳转被中断）
  router
    .push({
      path: '/alert',
      query: {
        tab: '1',
        trajectory_person: name,
        trajectory_date: new Date().toISOString().slice(0, 10),
      },
    })
    .then(() => closeModal())
    .catch(() => closeModal());
}

function barWidth(sim: unknown): string {
  if (sim == null || Number.isNaN(Number(sim))) return '0%';
  return `${Math.max(0, Math.min(100, Number(sim) * 100))}%`;
}

function handleCancel() {
  state.record = null;
  sceneError.value = false;
  selectedIndex.value = 0;
  closeModal();
}
</script>

<style lang="less">
// 白色苹果风：浅灰画布、白卡片、深灰文字、蓝色点缀
.face-alert-modal-wrap {
  // 整体固定高度：标题栏+内容合计 84vh（上下各留 8vh），任何屏幕都不超出
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

  .face-alert-modal {
    display: flex;
    height: 100%;
    background: #f5f5f7; // 苹果浅灰画布

    // 左侧：告警全景图舞台（主图，占主要篇幅）
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
        height: 100%;
        gap: 14px;
        color: #86868b;
      }

      &-toolbar {
        position: absolute;
        right: 16px;
        bottom: 16px;
        display: flex;
        gap: 8px;
      }
    }

    // 右侧：人脸识别信息面板（附属信息区）
    &__panel {
      flex: 1;
      min-width: 0;
      padding: 28px 30px;
      background: #f5f5f7;
      display: flex;
      flex-direction: column;
      gap: 22px;
      overflow-y: auto;
    }

    .section-title {
      font-size: 12px;
      font-weight: 600;
      color: #86868b;
      letter-spacing: 1.5px;
      text-transform: uppercase;
    }

    // 单人大人物区
    &__person {
      display: flex;
      align-items: center;
      gap: 18px;
      padding: 20px;
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }

    // 头像容器 + 右上角"出现轨迹"按钮；hover 头像有光圈反馈，点击查看该人轨迹
    &__avatar-wrap {
      position: relative;
      flex: 0 0 auto;
      border-radius: 50%;
      cursor: pointer;
      transition: transform 0.2s ease;

      &:hover {
        transform: scale(1.06);

        .face-alert-modal__avatar {
          box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.35), 0 4px 14px rgba(0, 113, 227, 0.25);
        }

        .face-alert-modal__avatar-hint {
          opacity: 1;
          transform: translate(-50%, 0);
        }
      }
    }

    // hover 提示气泡：说明头像可点击查看出现轨迹
    &__avatar-hint {
      position: absolute;
      top: calc(100% + 6px);
      left: 50%;
      transform: translate(-50%, -4px);
      z-index: 5;
      padding: 3px 10px;
      border-radius: 8px;
      background: rgba(29, 29, 31, 0.92);
      color: #fff;
      font-size: 12px;
      white-space: nowrap;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s ease, transform 0.2s ease;
    }

    &__avatar {
      width: 84px;
      height: 84px;
      flex: 0 0 84px;
      border-radius: 50%;
      overflow: hidden;
      border: 2px solid rgba(0, 113, 227, 0.15);
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f5f5f7;
      transition: box-shadow 0.2s ease;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    &__avatar-trajectory {
      position: absolute;
      top: -4px;
      right: -4px;
      width: 24px;
      height: 24px;
      padding: 0;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 2px solid #fff;
      border-radius: 50%;
      background: #0071e3;
      color: #fff;
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(0, 113, 227, 0.4);
      transition: transform 0.15s;

      &:hover {
        transform: scale(1.1);
      }
    }

    &__avatar {
      width: 72px;
      height: 72px;
      flex: 0 0 72px;
      border-radius: 50%;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f5f5f7;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    &__identity {
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
    }

    &__name {
      font-size: 22px;
      font-weight: 700;
      color: #1d1d1f;
      letter-spacing: 1px;
      line-height: 1.2;
    }

    &__sub {
      display: flex;
      gap: 10px;
      font-size: 12px;
      color: #86868b;

      .record {
        color: #aeaeb2;
      }
    }

    &__score {
      display: flex;
      align-items: baseline;
      gap: 10px;
      margin-top: 4px;

      .score-value {
        font-size: 20px;
        font-weight: 700;
        color: #0071e3; // 苹果蓝
      }

      .score-label {
        font-size: 12px;
        color: #86868b;
      }
    }

    // 多人人员卡片区
    &__persons {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    &__person-cards {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;

      .person-card {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        border-radius: 14px;
        background: #fff;
        border: 1.5px solid transparent;
        cursor: pointer;
        transition: all 0.2s;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);

        &:hover {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        &--active {
          border-color: #0071e3;
          background: #f0f7ff;
        }

        &__avatar-wrap {
          position: relative;
          flex: 0 0 auto;
          border-radius: 50%;
          cursor: pointer;
          transition: transform 0.2s ease;

          &:hover {
            transform: scale(1.1);

            .person-card__avatar {
              box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.35), 0 4px 14px rgba(0, 113, 227, 0.25);
            }

            .face-alert-modal__avatar-hint {
              opacity: 1;
              transform: translate(-50%, 0);
            }
          }

          .face-alert-modal__avatar-trajectory {
            width: 20px;
            height: 20px;
            top: -3px;
            right: -3px;
          }
        }

        &__avatar {
          width: 40px;
          height: 40px;
          flex: 0 0 40px;
          border-radius: 50%;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f5f5f7;
          border: 2px solid rgba(0, 113, 227, 0.15);
          transition: box-shadow 0.2s ease;

          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }

        &__info {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        &__name {
          font-size: 14px;
          font-weight: 600;
          color: #1d1d1f;
        }

        &__sim {
          font-size: 12px;
          color: #86868b;
          font-variant-numeric: tabular-nums;
        }
      }
    }

    // 事实区
    &__facts {
      display: flex;
      flex-direction: column;
      gap: 0;
      padding: 4px 20px;
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);

      .fact {
        display: flex;
        gap: 14px;
        padding: 13px 0;
        font-size: 14px;
        line-height: 1.6;
        border-bottom: 1px solid #f0f0f2;

        &:last-child {
          border-bottom: none;
        }

        &__label {
          flex: 0 0 46px;
          color: #86868b;
          font-weight: 500;
        }

        &__value {
          color: #1d1d1f;
          word-break: break-all;
        }
      }
    }

    // 匹配详情区
    &__match {
      display: flex;
      flex-direction: column;
      gap: 12px;
      padding: 16px 20px;
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }

    &__meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 16px;
      font-size: 12px;
      color: #86868b;
    }

    &__candidates {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    &__candidate {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 7px 12px;
      border-radius: 10px;
      background: #f5f5f7;
      font-size: 13px;

      &--hit {
        background: #f0f7ff;
        border: 1px solid #cce5ff;
      }

      .rank {
        flex: 0 0 18px;
        color: #aeaeb2;
        font-size: 12px;
      }

      .name {
        flex: 0 0 80px;
        color: #1d1d1f;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .bar {
        flex: 1;
        height: 6px;
        border-radius: 3px;
        background: #e8e8ed;
        overflow: hidden;

        .bar-fill {
          display: block;
          height: 100%;
          border-radius: 3px;
          background: #0071e3;
        }
      }

      .sim {
        flex: 0 0 56px;
        text-align: right;
        color: #515154;
        font-variant-numeric: tabular-nums;
      }
    }
  }
}
</style>
