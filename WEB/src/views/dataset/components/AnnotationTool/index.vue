<template>
  <ConfigProvider :get-popup-container="getModalContainer">
  <div ref="container" class="annotation-container">
    <!-- 顶栏：工作流 + 标注工具 + 核心操作 -->
    <div class="top-toolbar">
      <div class="toolbar-left">
        <AnnotationWorkflowBar
          :total-images="totalImages"
          :completed-count="completedCount"
          :usage-allocated="syncCheck.usageAllocated"
          :annotation-completed="syncCheck.annotationCompleted"
          :synced-to-minio="syncCheck.syncedToMinio"
          :syncing="syncCheck.syncing"
          @action="onWorkflowAction"
        />
        <span v-if="totalImages > 0" class="toolbar-progress">
          第 <strong>{{ globalImageIndex + 1 }}</strong>/{{ totalImages }} 张
          <span class="progress-percent">· {{ progressPercent }}%</span>
        </span>
        <span v-if="batchTaskRunning" class="batch-task-hint">
          <Icon icon="ant-design:loading-outlined" spin/>
          AI 标注中
          <template v-if="batchTaskProgress.total > 0">
            {{ batchTaskProgress.processed }}/{{ batchTaskProgress.total }}
            <span v-if="batchTaskProgress.failed > 0" class="batch-failed">（失败 {{ batchTaskProgress.failed }}）</span>
          </template>
        </span>
      </div>

      <div class="toolbar-center tool-group">
        <button
          v-for="tool in tools"
          :key="tool.id"
          type="button"
          class="tool-button"
          :class="{ active: activeTool === tool.id }"
          :title="`${tool.name} (${tool.shortcut})`"
          @click="setActiveTool(tool.id)"
        >
          <Icon :icon="tool.icon"/>
          <span class="tool-name">{{ tool.name }}</span>
          <span class="tool-shortcut">{{ tool.shortcut }}</span>
        </button>
      </div>

      <div class="toolbar-right">
        <div class="save-btn-group">
          <button
            type="button"
            class="action-btn action-btn-primary action-btn-save-next"
            :class="{ 'has-unsaved': !isSaved && totalImages > 0 }"
            :disabled="saving || totalImages === 0"
            title="保存当前标注并跳到下一张待标注 (Ctrl+Shift+S)"
            @click="saveAndJumpToNextPending"
          >
            <Icon icon="ant-design:save-outlined"/>
            保存并下一张
            <Icon icon="ant-design:arrow-right-outlined" class="save-next-arrow"/>
            <span v-if="!isSaved && totalImages > 0" class="unsaved-dot" title="有未保存的修改"/>
          </button>
          <button
            type="button"
            class="action-btn action-btn-primary action-btn-save-only"
            :disabled="saving"
            title="仅保存当前标注 (Ctrl+S)"
            @click="saveCurrentAnnotations()"
          >
            保存
          </button>
        </div>
        <button
          type="button"
          class="action-btn ai-batch-btn"
          :disabled="batchTaskRunning || totalImages === 0"
          :title="aiBatchBtnTitle"
          @click="openAiBatchModal"
        >
          <Icon icon="ant-design:robot-outlined"/>
          AI 标注
        </button>
        <button
          type="button"
          class="action-btn sam-bootstrap-btn"
          :disabled="batchTaskRunning"
          title="SAM 冷启动批量标注，对数据集中已有图片生成初始标注"
          @click="openSamAutoLabelDrawer"
        >
          <Icon icon="ant-design:experiment-outlined"/>
          智能标注
          <span
            v-if="samModelChecked && !samModelReady"
            class="sam-model-badge"
            title="SAM 模型未安装，点击前往安装"
            @click.stop="openSamModelSetupPage"
          >!</span>
        </button>
        <button
          type="button"
          class="action-btn unattended-label-btn"
          :disabled="batchTaskRunning"
          title="选择摄像头抽帧任务，自动打标扩充本数据集"
          @click="openUnattendedLabelDrawer"
        >
          <Icon icon="ant-design:cluster-outlined"/>
          无人值守扩充
        </button>
        <span class="top-actions-divider"/>
        <Dropdown :trigger="['click']" placement="bottomRight">
          <button type="button" class="action-btn">
            <Icon icon="ant-design:plus-outlined"/>
            添加
            <Icon icon="ant-design:down-outlined" class="dropdown-caret"/>
          </button>
          <template #overlay>
            <Menu @click="onAddMenuClick">
              <MenuItem key="import">
                <Icon icon="ant-design:folder-open-outlined"/>
                导入数据（文件夹 / 格式 / 云平台）
              </MenuItem>
              <MenuItem key="upload">
                <Icon icon="ant-design:picture-outlined"/>
                上传图片
              </MenuItem>
              <MenuItem key="zip">
                <Icon icon="ant-design:file-zip-outlined"/>
                上传 ZIP 压缩包
              </MenuItem>
              <MenuDivider/>
              <MenuItem key="frame">
                <Icon icon="ant-design:video-camera-outlined"/>
                视频流抽帧任务
              </MenuItem>
              <MenuItem key="video">
                <Icon icon="ant-design:play-square-outlined"/>
                视频库管理
              </MenuItem>
            </Menu>
          </template>
        </Dropdown>
        <Dropdown :trigger="['click']" placement="bottomRight">
          <button type="button" class="action-btn" :class="{ 'train-ready': syncCheck.syncReady && !syncCheck.syncedToMinio && !syncCheck.syncing }">
            <Icon icon="ant-design:export-outlined"/>
            训练集
            <span v-if="syncCheck.syncReady && !syncCheck.syncedToMinio && !syncCheck.syncing" class="ready-badge"/>
            <Icon icon="ant-design:down-outlined" class="dropdown-caret"/>
          </button>
          <template #overlay>
            <Menu @click="onTrainMenuClick" class="train-menu-overlay">
              <div v-if="totalImages > 0" class="train-menu-header">
                <template v-if="!syncCheck.annotationCompleted">
                  待标注 <strong>{{ pendingCount }}</strong> 张
                </template>
                <template v-else-if="!syncCheck.usageAllocated">
                  标注已完成，待划分用途
                </template>
                <template v-else-if="syncCheck.syncing">
                  {{ syncCheck.syncStatus === 'QUEUED' ? '同步任务排队中' : `同步到 Minio ${syncCheck.syncProgress}%` }}
                </template>
                <template v-else-if="syncCheck.syncReady && !syncCheck.syncedToMinio">
                  可同步到 Minio
                </template>
                <template v-else-if="syncCheck.syncedToMinio">
                  已同步，可用于训练
                </template>
                <template v-else>
                  划分已完成
                </template>
              </div>
              <MenuItem key="split" :disabled="totalImages === 0 || !syncCheck.annotationCompleted">
                <Icon icon="ant-design:pie-chart-outlined"/>
                划分用途 (7:2:1)
              </MenuItem>
              <MenuItem key="reset" :disabled="totalImages === 0">
                <Icon icon="ant-design:reload-outlined"/>
                重置用途划分
              </MenuItem>
              <MenuDivider/>
              <MenuItem key="export" :disabled="totalImages === 0">
                <Icon icon="ant-design:download-outlined"/>
                导出数据集
              </MenuItem>
              <MenuItem key="sync" :disabled="!syncCheck.syncReady || syncCheck.syncing || syncCheck.syncedToMinio" :title="syncDisabledReason">
                <Icon icon="ant-design:cloud-upload-outlined"/>
                {{ syncActionLabel }}
              </MenuItem>
            </Menu>
          </template>
        </Dropdown>
        <button type="button" class="action-btn" title="标签与数据源管理" @click="openManageDrawer('tags')">
          <Icon icon="ant-design:setting-outlined"/>
        </button>
      </div>
    </div>

    <AnnotationProgressStrip
      :total="totalImages"
      :completed="completedCount"
      :tip="workflowTip"
      @tip-action="onTipAction"
    />

    <MinioSyncStatus
      compact
      :status="syncCheck"
      :connection-error="syncConnectionError"
      @refresh="handleRefreshSyncStatus"
      @retry="handleSyncToMinio"
      @start-train="handleStartTrain"
    />

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧图片列表（虚拟滚动，单次最多加载 1000 条） -->
      <div ref="imagePanelRef" class="image-panel">
        <div class="image-list-header">
          <div v-if="batchSelectMode" class="batch-selection-toolbar">
            <div class="batch-selection-summary">
              <span>已选 {{ selectedImageCount }}/{{ MAX_BATCH_SELECTION }}</span>
              <Button size="small" type="text" @click="toggleBatchSelectMode">
                取消
              </Button>
            </div>
            <div class="batch-action-group">
              <Button
                class="image-panel-toolbar-btn"
                size="small"
                type="default"
                :disabled="displayImages.length === 0 || allSelectableImagesSelected"
                @click="selectAllImagesInChunk"
              >
                全选
              </Button>
              <Button
                class="image-panel-toolbar-btn"
                size="small"
                type="default"
                :disabled="selectedImageCount === 0"
                @click="clearImageSelection"
              >
                全不选
              </Button>
              <Button
                class="image-panel-toolbar-btn image-panel-toolbar-btn--danger"
                size="small"
                type="primary"
                danger
                :disabled="selectedImageCount === 0"
                preIcon="ant-design:delete-outlined"
                @click="confirmBatchDeleteSelected"
              >
                删除
              </Button>
            </div>
          </div>
          <template v-else>
            <div class="image-list-stats">
              <span class="stat-done">已完成 {{ completedCount }}</span>
              <span class="stat-sep">/</span>
              <span class="stat-total">{{ totalImages }}</span>
              <span v-if="listFilterStatus !== 'all'" class="stat-filtered">· {{ displayImages.length }}</span>
            </div>
            <div class="image-list-header-actions">
              <Button
                v-if="totalImages > 0"
                class="image-panel-toolbar-btn image-panel-toolbar-btn--icon"
                size="small"
                type="default"
                preIcon="ant-design:delete-outlined"
                title="批量删除"
                @click="toggleBatchSelectMode"
              />
              <Button
                v-if="pendingCount > 0"
                class="image-panel-toolbar-btn image-panel-toolbar-btn--icon"
                size="small"
                type="default"
                preIcon="ant-design:forward-outlined"
                title="跳到下一张待标注 (N)"
                @click="jumpToNextPending"
              />
              <Select
                v-model:value="listFilterStatus"
                size="small"
                class="filter-select"
                :options="listFilterOptions"
                popup-class-name="image-panel-dropdown"
                :get-popup-container="getSidePanelPopupContainer"
              />
            </div>
          </template>
        </div>
        <div
          ref="listScrollRef"
          class="image-list-scroll"
          @scroll="onListScroll"
        >
          <div class="image-list-phantom" :style="{ height: `${listPhantomHeight}px` }"/>
          <ul
            class="image-list"
            :style="{ transform: `translateY(${listOffsetY}px)` }"
          >
            <li
              v-for="{ img, index } in visibleListImages"
              :key="img.id"
              class="image-list-item"
              :class="{
                active: currentImage.id === img.id,
                annotated: hasAnnotations(img),
                completed: img.completed === 1,
                selected: batchSelectMode && isImageSelected(img.id)
              }"
              @click="onImageListItemClick(img)"
            >
              <Checkbox
                v-if="batchSelectMode"
                :checked="isImageSelected(img.id)"
                class="image-select-checkbox"
                @click.stop
                @change="(e) => toggleImageSelection(img.id, e.target.checked)"
              />
              <span v-else class="image-index">{{ index + 1 }}</span>
              <span class="image-name" :title="img.name">{{ img.name }}</span>
              <span v-if="!batchSelectMode" class="image-status-badge" :class="getImageStatusClass(img)">
                {{ getImageStatusText(img) }}
              </span>
            </li>
          </ul>
          <div v-if="displayImages.length === 0" class="image-list-empty">
            <Icon icon="ant-design:inbox-outlined" class="empty-icon"/>
            <p>暂无图片</p>
            <p class="empty-hint">从「添加」导入或上传后开始标注</p>
            <button type="button" class="empty-import-btn" @click="openImportModal">
              <Icon icon="ant-design:upload-outlined"/>
              导入数据
            </button>
          </div>
        </div>
        <div v-if="totalImages > 0" class="image-panel-footer">
          <button type="button" class="panel-footer-btn" @click="openImportModal">
            <Icon icon="ant-design:plus-outlined"/>
            添加图片
          </button>
        </div>
        <Pagination
          v-if="totalPages > 1"
          v-model:current="listChunkPage"
          class="image-list-pagination"
          size="small"
          simple
          :total="totalImages"
          :page-size="LIST_CHUNK_SIZE"
          :show-size-changer="false"
          @change="onListChunkPageChange"
        />
      </div>

      <!-- 画布区域 -->
      <div class="canvas-area">
        <div v-if="totalImages > 0" class="canvas-nav">
          <button
            type="button"
            class="nav-btn"
            :disabled="globalImageIndex <= 0"
            title="上一张 (←)"
            @click="prevImage"
          >
            <Icon icon="ant-design:left-outlined"/>
          </button>
          <span class="nav-index">{{ globalImageIndex + 1 }} / {{ totalImages }}</span>
          <button
            type="button"
            class="nav-btn"
            :disabled="globalImageIndex >= totalImages - 1"
            title="下一张 (→ / 空格)"
            @click="nextImage"
          >
            <Icon icon="ant-design:right-outlined"/>
          </button>
          <span class="nav-divider"/>
          <button
            type="button"
            class="nav-btn nav-btn-danger"
            title="删除当前图片 (Shift+Delete)"
            @click="confirmDeleteCurrentImage"
          >
            <Icon icon="ant-design:delete-outlined"/>
          </button>
        </div>
        <div class="canvas-wrapper">
          <div
            v-if="totalImages > 0 && labels.length === 0"
            class="canvas-no-tag-hint"
          >
            <Icon icon="ant-design:tags-outlined"/>
            <span>请先在右侧添加标注类别，再开始框选</span>
            <button type="button" class="hint-action" @click="focusLabelAdd">去添加</button>
          </div>
          <canvas
            ref="canvas"
            class="annotation-canvas"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @dblclick="handleDoubleClick"
            @wheel.prevent="handleCanvasWheel"
          ></canvas>
        </div>

        <div class="status-indicator">
          <div class="status-header">
            <div class="completion-status" :class="{ completed: currentImage.completed === 1 }">
              {{ currentImage.completed === 1 ? '✅ 已完成标注' : '⏳ 标注中' }}
            </div>
            <div v-if="currentImage.completed === 1" class="modification-info">
              <div>修改次数: {{ currentImage.modificationCount || 0 }}</div>
              <div>最后修改: {{ formatDateTime(currentImage.lastModified) }}</div>
            </div>
          </div>
          <div class="annotation-count">
            <div class="status-dot"></div>
            <span>{{ statusText }}</span>
            <div v-if="!isSaved" class="unsaved-indicator">(未保存)</div>
          </div>
        </div>

        <div class="fullscreen-control" @click="toggleFullscreen">
          <Icon :icon="isFullscreen ? 'fa:compress' : 'fa:expand'"/>
          <span>{{ isFullscreen ? '退出全屏' : '全屏标注' }}</span>
        </div>

        <div class="shortcut-hint">
          <div v-for="hint in shortcutHints" :key="hint.key" class="hint-item">
            <span class="key">{{ hint.key }}</span>
            <span class="text">{{ hint.text }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧标签栏 -->
      <div class="label-panel">
        <AnnotationLabelPanel
          ref="labelPanelRef"
          :labels="labels"
          :current-index="currentLabelIndex"
          :dataset-id="datasetId"
          @select="setCurrentLabel"
          @changed="onLabelsChanged"
          @manage="openManageDrawer('tags')"
        />

        <div class="object-layer-section">
          <div class="panel-header">
            <Icon icon="ant-design:appstore-outlined"/>
            <span>对象图层</span>
            <span class="object-count">{{ annotations.length }}</span>
          </div>
          <div class="object-list">
            <div
              v-for="(anno, index) in annotations"
              :key="anno.id"
              class="object-item"
              :class="{ selected: selectedAnnotationId === anno.id }"
              @click="selectAnnotation(anno.id)"
            >
              <div class="object-color" :style="{ backgroundColor: resolveAnnotationColor(anno.label, anno.color) }"></div>
              <div class="object-name">{{ getLabelName(anno.label) }} #{{ index + 1 }}</div>
              <div class="object-actions">
                <button class="delete-btn" @click.stop="deleteAnnotation(anno.id)">
                  <Icon icon="fa:trash"/>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <AILabelModal
      ref="aiLabelModalRef"
      :dataset-id="datasetId"
      :total-images="totalImages"
      :annotated-count="completedCount"
      :get-container="getModalContainer"
      @success="onBatchAiSuccess"
    />
    <SamAutoLabelDrawer
      @register="registerSamDrawer"
      :dataset-id="datasetId"
      @success="onBatchAiSuccess"
      @open-frame-tasks="openManageDrawer('frame')"
      @open-auto-label="openAiBatchModal"
    />
    <UnattendedLabelDrawer
      ref="unattendedDrawerRef"
      @register="registerUnattendedDrawer"
      :dataset-id="datasetId"
      @success="onUnattendedLabelSuccess"
      @open-frame-tasks="openManageDrawer('frame')"
    />
    <ImportDatasetModal
      ref="importModalRef"
      :dataset-id="datasetId"
      :get-container="getModalContainer"
      @success="onImportSuccess"
    />
    <ExportDatasetModal
      ref="exportModalRef"
      :dataset-id="datasetId"
      :dataset-labels="labels"
      :get-container="getModalContainer"
    />
    <DatasetImageModal @register="registerImageModal" @success="onImageUploadSuccess"/>
    <DatasetManageDrawer
      v-model:open="manageDrawerOpen"
      :initial-tab="manageDrawerTab"
      :get-container="getModalContainer"
      @tags-changed="fetchLabels"
      @open-unattended="openUnattendedLabelDrawer"
      @frame-tasks-changed="reloadUnattendedFrameTasks"
    />
  </div>
  </ConfigProvider>
</template>

<script setup lang="ts">
import {computed, nextTick, onMounted, onUnmounted, reactive, ref, watch} from 'vue';
import {Checkbox, ConfigProvider, Dropdown, Menu, MenuDivider, MenuItem, Pagination, Select} from 'ant-design-vue';
import {Icon} from '@/components/Icon';
import {Button} from '@/components/Button';
import {useMessage} from "@/hooks/web/useMessage";
import {useRoute, useRouter} from "vue-router";
import {useModal} from '@/components/Modal';
import {
  checkSyncCondition,
  deleteDatasetImage,
  deleteDatasetImages,
  type DatasetAnnotationImportResult,
  type DatasetSyncCheckResult,
  getDatasetImagePage,
  parseDatasetSyncCheckResult,
  resetDataset,
  splitDataset,
  syncToMinio,
  updateDatasetImage,
  waitForDatasetMinioSync,
} from "@/api/device/dataset";
import {
  colorWithAlpha,
  fetchDatasetTags,
  syncTagsFromImport,
  type DatasetTagItem,
} from '@/views/dataset/components/AnnotationTool/datasetTagUtils';

/** 标注框描边宽度 */
const ANNOTATION_STROKE_WIDTH = 2;
const ANNOTATION_SELECTED_STROKE_WIDTH = 2.5;
/** 标注框填充透明度（高度透明） */
const ANNOTATION_FILL_ALPHA = 0.1;
import { getAutoLabelTask } from '@/api/device/auto-label';
import { getSamModelStatus } from '@/api/device/sam';
import { useDrawer } from '@/components/Drawer';
import AILabelModal from '@/views/dataset/components/AutoLabel/AILabelModal/index.vue';
import SamAutoLabelDrawer from '@/views/dataset/components/AutoLabel/SamAutoLabelDrawer/index.vue';
import UnattendedLabelDrawer from '@/views/dataset/components/AutoLabel/UnattendedLabelDrawer/index.vue';
import ImportDatasetModal from '@/views/dataset/components/AutoLabel/ImportDatasetModal/index.vue';
import ExportDatasetModal from '@/views/dataset/components/AutoLabel/ExportDatasetModal/index.vue';
import DatasetImageModal from '@/views/dataset/components/DatasetImageModal/index.vue';
import DatasetManageDrawer, {
  type ManageDrawerTab,
} from '@/views/dataset/components/AnnotationTool/DatasetManageDrawer.vue';
import AnnotationWorkflowBar, {
  type WorkflowStepKey,
} from '@/views/dataset/components/AnnotationTool/AnnotationWorkflowBar.vue';
import AnnotationProgressStrip, {
  type TipAction,
  type WorkflowTip,
} from '@/views/dataset/components/AnnotationTool/AnnotationProgressStrip.vue';
import AnnotationLabelPanel from '@/views/dataset/components/AnnotationTool/AnnotationLabelPanel.vue';
import MinioSyncStatus from '@/views/dataset/components/MinioSyncStatus/index.vue';
defineOptions({name: 'AnnotationTool'});

const {createMessage, createConfirm} = useMessage();
const route = useRoute();
const router = useRouter();
const datasetId = computed(() => Number(route.params['id']));
const manageDrawerOpen = ref(false);
const manageDrawerTab = ref<ManageDrawerTab>('tags');
const [registerImageModal, {openModal: openImageUploadModalInner}] = useModal();
const labelPanelRef = ref<InstanceType<typeof AnnotationLabelPanel> | null>(null);

const defaultSyncCheck = (): DatasetSyncCheckResult => ({
  usageAllocated: false,
  annotationCompleted: false,
  syncReady: false,
  syncing: false,
  syncedToMinio: false,
  syncError: null,
  syncStatus: 'IDLE',
  syncStage: null,
  syncProgress: 0,
  processedImages: 0,
  syncSubmittedAt: null,
  syncStartedAt: null,
  syncFinishedAt: null,
  totalImages: 0,
  unallocatedCount: 0,
  unannotatedCount: 0,
});

const syncCheck = reactive(defaultSyncCheck());
const syncConnectionError = ref<string | null>(null);
let syncPollController: AbortController | null = null;

async function refreshSyncCheck() {
  try {
    const ret = await checkSyncCondition(route.params.id);
    const status = parseDatasetSyncCheckResult(ret);
    Object.assign(syncCheck, status);
    syncConnectionError.value = null;
    return status;
  } catch (error) {
    syncConnectionError.value = error instanceof Error ? error.message : '状态查询失败';
    return null;
  }
}
const aiLabelModalRef = ref<InstanceType<typeof AILabelModal> | null>(null);
const unattendedDrawerRef = ref<InstanceType<typeof UnattendedLabelDrawer> | null>(null);
const [registerSamDrawer, { openDrawer: openSamDrawer }] = useDrawer();
const [registerUnattendedDrawer, { openDrawer: openUnattendedDrawer }] = useDrawer();
const samModelChecked = ref(false);
const samModelReady = ref(false);
const importModalRef = ref<InstanceType<typeof ImportDatasetModal> | null>(null);
const exportModalRef = ref<InstanceType<typeof ExportDatasetModal> | null>(null);

// 标注数据
const annotations = ref<Annotation[]>([]);
const selectedAnnotationId = ref<number | null>(null);
const annotationCount = computed<number>(() => annotations.value.length);
const statusText = computed<string>(() => `已标注 ${annotationCount.value} 个对象`);
const isSaved = ref(true);

/** 左侧列表每个分块展示的条数（与后端 PageParam.PAGE_SIZE_MAX 一致） */
const LIST_CHUNK_SIZE = 1000;
const MAX_BATCH_SELECTION = 100;
const LIST_ITEM_HEIGHT = 36;
const LIST_OVERSCAN = 10;

type ListFilterStatus = 'all' | 'pending' | 'annotated' | 'completed';

const listFilterOptions: { label: string; value: ListFilterStatus }[] = [
  {label: '全部', value: 'all'},
  {label: '待完成', value: 'pending'},
  {label: '有标注', value: 'annotated'},
  {label: '已完成', value: 'completed'},
];

const listFilterStatus = ref<ListFilterStatus>('all');
const batchSelectMode = ref(false);
const selectedImageIds = ref<Set<number>>(new Set());
const selectedImageCount = computed(() => selectedImageIds.value.size);
const imagePanelRef = ref<HTMLElement | null>(null);
const listLoading = ref(false);
const listChunkPage = ref(1);
const totalImages = ref(0);
const completedCount = ref(0);
const listScrollRef = ref<HTMLElement | null>(null);
const listScrollTop = ref(0);

// 添加保存状态锁
const saving = ref(false);

const batchTaskRunning = ref(false);
const batchTaskProgress = reactive({
  total: 0,
  processed: 0,
  success: 0,
  failed: 0,
});
let batchTaskPollTimer: ReturnType<typeof setInterval> | null = null;

const totalPages = computed(() => Math.max(1, Math.ceil(totalImages.value / LIST_CHUNK_SIZE)));

const displayImages = computed(() => images.value);
const selectableImageIds = computed(() =>
  displayImages.value.slice(0, MAX_BATCH_SELECTION).map((image) => image.id),
);
const allSelectableImagesSelected = computed(() =>
  selectableImageIds.value.length > 0
  && selectableImageIds.value.every((id) => selectedImageIds.value.has(id)),
);

const globalImageIndex = computed(() => {
  return (listChunkPage.value - 1) * LIST_CHUNK_SIZE + currentImageIndex.value;
});

const progressPercent = computed(() => {
  if (totalImages.value <= 0) return 0;
  return Math.round((completedCount.value / totalImages.value) * 100);
});

const pendingCount = computed(() => {
  if (syncCheck.unannotatedCount > 0) return syncCheck.unannotatedCount;
  return Math.max(0, totalImages.value - completedCount.value);
});

const syncDisabledReason = computed(() => {
  if (syncCheck.syncing) return '数据集正在同步';
  if (syncCheck.syncedToMinio) return '数据集已同步';
  if (syncCheck.syncReady) return '';
  if (totalImages.value === 0) return '请先导入图片';
  if (!syncCheck.annotationCompleted) return `尚有 ${pendingCount.value} 张未完成标注`;
  if (!syncCheck.usageAllocated) return '请先划分数据集用途';
  return '';
});

const syncActionLabel = computed(() => {
  if (syncCheck.syncStatus === 'QUEUED') return '排队中';
  if (syncCheck.syncStatus === 'RUNNING') return `同步中 ${syncCheck.syncProgress}%`;
  if (syncCheck.syncStatus === 'FAILED') return '重新同步';
  if (syncCheck.syncedToMinio) return '已同步';
  return '同步到 Minio';
});

const aiBatchBtnTitle = computed(() => {
  if (totalImages.value === 0) return '请先导入图片后再使用 AI 批量标注';
  if (batchTaskRunning.value) return 'AI 批量标注进行中，请等待完成';
  return '使用已部署的推理模型对本数据集全部图片批量自动标注';
});

const workflowTip = computed((): WorkflowTip | null => {
  if (batchTaskRunning.value) {
    const p = batchTaskProgress;
    if (p.total > 0) {
      return {
        text: `AI 批量标注进行中：${p.processed}/${p.total} 张（成功 ${p.success}，失败 ${p.failed}）`,
      };
    }
    return {text: 'AI 批量标注已启动，正在处理…'};
  }
  if (syncCheck.syncStatus === 'QUEUED') {
    return {text: 'MinIO 同步任务已提交，正在排队'};
  }
  if (syncCheck.syncStatus === 'RUNNING') {
    return {text: `数据集正在同步到 Minio，当前进度 ${syncCheck.syncProgress}%`};
  }
  if (syncCheck.syncStatus === 'FAILED') {
    return {text: `MinIO 同步失败：${syncCheck.syncError || '请重新同步'}`, action: 'sync', actionLabel: '重新同步'};
  }
  if (totalImages.value === 0) {
    return {text: '数据集为空，请先导入或上传图片', action: 'import', actionLabel: '去导入'};
  }
  if (!syncCheck.annotationCompleted) {
    if (pendingCount.value >= 5) {
      return {
        text: `还有 ${pendingCount.value} 张待标注，推荐使用 AI 批量标注加速`,
        action: 'aiLabel',
        actionLabel: '开启 AI 标注',
      };
    }
    return {
      text: `还有 ${pendingCount.value} 张待标注，可手动标注或使用顶栏「AI 标注」`,
      action: 'nextPending',
      actionLabel: '跳到下一张待标注',
    };
  }
  if (!syncCheck.usageAllocated) {
    return {text: '标注已全部完成，请划分训练/验证/测试集', action: 'split', actionLabel: '划分用途'};
  }
  if (syncCheck.syncReady && !syncCheck.syncedToMinio) {
    return {text: '数据集已就绪，可同步到 Minio 用于模型训练', action: 'sync', actionLabel: '同步 Minio'};
  }
  if (syncCheck.syncedToMinio) {
    return {text: '已同步到 Minio，可用于模型训练'};
  }
  return null;
});

const listPhantomHeight = computed(() => displayImages.value.length * LIST_ITEM_HEIGHT);

const listOffsetY = computed(() => visibleListRange.value.start * LIST_ITEM_HEIGHT);

const visibleListRange = computed(() => {
  const count = displayImages.value.length;
  if (count === 0) return {start: 0, end: 0};
  const container = listScrollRef.value;
  const viewHeight = container?.clientHeight ?? 480;
  const start = Math.max(0, Math.floor(listScrollTop.value / LIST_ITEM_HEIGHT) - LIST_OVERSCAN);
  const visibleCount = Math.ceil(viewHeight / LIST_ITEM_HEIGHT) + LIST_OVERSCAN * 2;
  const end = Math.min(count, start + visibleCount);
  return {start, end};
});

const visibleListImages = computed(() => {
  const {start, end} = visibleListRange.value;
  const base = (listChunkPage.value - 1) * LIST_CHUNK_SIZE;
  return displayImages.value.slice(start, end).map((img, i) => ({
    img,
    index: base + start + i,
  }));
});

const onListScroll = (e: Event) => {
  listScrollTop.value = (e.target as HTMLElement).scrollTop;
};

const scrollListToActive = () => {
  nextTick(() => {
    const idx = images.value.findIndex((i) => i.id === currentImage.value.id);
    if (idx < 0 || !listScrollRef.value) return;
    const targetTop = idx * LIST_ITEM_HEIGHT;
    const el = listScrollRef.value;
    const viewBottom = el.scrollTop + el.clientHeight;
    if (targetTop < el.scrollTop || targetTop + LIST_ITEM_HEIGHT > viewBottom) {
      el.scrollTop = Math.max(0, targetTop - el.clientHeight / 2 + LIST_ITEM_HEIGHT / 2);
      listScrollTop.value = el.scrollTop;
    }
  });
};

const buildListQueryParams = (pageNo: number) => {
  const params: Record<string, unknown> = {
    datasetId: route.params['id'],
    pageNo,
    pageSize: LIST_CHUNK_SIZE,
  };
  if (listFilterStatus.value === 'pending') {
    params.completed = 0;
  } else if (listFilterStatus.value === 'completed') {
    params.completed = 1;
  }
  return params;
};

const getSidePanelPopupContainer = (): HTMLElement => {
  return imagePanelRef.value || document.body;
};

const onListChunkPageChange = async (page: number) => {
  const prevPage = listChunkPage.value;
  if (page === prevPage) return;
  const ok = await confirmDiscardUnsaved();
  if (!ok) {
    listChunkPage.value = prevPage;
    return;
  }
  clearImageSelection();
  currentImageIndex.value = 0;
  await fetchImages(page);
};

// 快捷键提示
const shortcutHints = ref<{ key: string, text: string }[]>([
  {key: 'Del', text: '删除标注'},
  {key: 'Shift+Del', text: '删图片'},
  {key: 'Ctrl+S', text: '保存'},
  {key: 'Ctrl+Shift+S', text: '保存并下一张'},
  {key: 'Space', text: '下一张'},
  {key: '←→', text: '切图'},
  {key: 'N', text: '待标注'},
  {key: '1-9', text: '标签'},
  {key: '滚轮', text: '缩放'},
  {key: 'Ctrl+Z', text: '撤销'},
]);

// 操作历史记录
const historyStack = ref<Annotation[][]>([]);

// Canvas 状态
const canvas = ref<HTMLCanvasElement | null>(null);
const ctx = ref<CanvasRenderingContext2D | null>(null);
const isDrawing = ref<boolean>(false);
const startX = ref<number>(0);
const startY = ref<number>(0);
const currentPoints = ref<Point[]>([]);
const zoomLevel = ref<number>(1.0);
const offsetX = ref<number>(0);
const offsetY = ref<number>(0);

// 全屏状态
const isFullscreen = ref(false);
const container = ref<HTMLElement | null>(null);

// 定义 TypeScript 类型
const ToolType = {
  SELECT: 'select',
  RECTANGLE: 'rectangle',
  POLYGON: 'polygon'
};

const AnnotationType = {
  RECTANGLE: 'rectangle',
  POLYGON: 'polygon'
};

// 工具类型
interface Tool {
  id: string;
  name: string;
  icon: string;
  shortcut: string;
}

// 标签类型
interface Label {
  id: number;
  name: string;
  color: string;
  shortcut: string; // 确保定义为string类型
}

// 点类型
interface Point {
  x: number;
  y: number;
}

// 标注数据格式
interface Annotation {
  id: number;
  type: string;
  label: string; // 改为存储标签的 shortcut
  color: string;
  points: Point[];
}

// 图片类型
interface Image {
  id: number;
  name: string;
  path: string;
  annotations: Annotation[] | string;
  completed: 0 | 1;
  modificationCount: number;
  lastModified: Date | null;
}

// 保存标注请求类型
interface SaveAnnotationRequest {
  id: number;
  name: string;
  annotations: string;
  completed: 0 | 1;
  modificationCount: number;
  lastModified: Date | null;
}

// 工具状态
const activeTool = ref<string>(ToolType.SELECT);
const tools = ref<Tool[]>([
  {id: ToolType.SELECT, name: '选择', icon: 'mage:mouse-pointer', shortcut: 'V'},
  {id: ToolType.RECTANGLE, name: '矩形', icon: 'uil:vector-square', shortcut: 'R'},
  {id: ToolType.POLYGON, name: '多边形', icon: 'fa-solid:draw-polygon', shortcut: 'P'},
]);

// 图片显示尺寸
const imageDisplaySize = ref({
  x: 0,
  y: 0,
  width: 0,
  height: 0
});

// 标签状态
const currentLabelIndex = ref<number>(0);
const labels = ref<Label[]>([]);

const currentLabel = computed<Label>(() => labels.value[currentLabelIndex.value]);

// 图片数据
const images = ref<Image[]>([]);

// 图片标注状态存储
const imageAnnotations = ref<{ [key: number]: Annotation[] }>({});

const currentImageIndex = ref<number>(0);
const currentImage = computed<Image>(() => images.value[currentImageIndex.value] || {
  id: 0,
  name: '',
  path: '',
  annotations: [],
  completed: 0,
  modificationCount: 0,
  lastModified: null
});

// 图片对象引用
const currentImageObj = ref<HTMLImageElement | null>(null);
const imageLoaded = ref(false);

// 修改图片加载逻辑
const loadImage = (src: string) => {
  imageLoaded.value = false;
  const img = new Image();
  img.crossOrigin = "Anonymous";
  img.onload = () => {
    currentImageObj.value = img;
    imageLoaded.value = true;

    // 计算初始缩放比例和位置
    if (canvas.value) {
      const canvasWidth = canvas.value.width;
      const canvasHeight = canvas.value.height;

      // 确保图片不超过画布
      const scaleX = canvasWidth / img.width;
      const scaleY = canvasHeight / img.height;
      const initScale = Math.min(scaleX, scaleY);

      // 重置缩放和偏移
      zoomLevel.value = initScale;
      offsetX.value = 0;
      offsetY.value = 0;
    }

    draw();
  };
  img.src = src;
};

const findLabelByKey = (labelKey: string): Label | undefined => {
  const key = String(labelKey);
  return labels.value.find((l) => String(l.shortcut) === key)
    ?? labels.value.find((l) => l.name === key);
};

const getLabelName = (shortcut: string): string => {
  const label = findLabelByKey(shortcut);
  return label ? label.name : '未知标签';
};

/** 绘制与图层面板统一使用标签定义色，避免历史/导入数据中的 color 与右侧标签不一致 */
const resolveAnnotationColor = (labelKey: string, storedColor?: string): string => {
  const label = findLabelByKey(labelKey);
  if (label?.color) return label.color;
  if (storedColor) return storedColor;
  return '#4361ee';
};

watch(listFilterStatus, () => {
  clearImageSelection();
  listChunkPage.value = 1;
  fetchImages(1);
});

// 监听当前图片变化
watch(currentImageIndex, () => {
  scrollListToActive();
});

function normalizeLoadedAnnotations(raw: Annotation[]): Annotation[] {
  return raw.map((anno) => ({
    ...anno,
    color: resolveAnnotationColor(anno.label, anno.color),
  }));
}

watch(currentImage, (newImage) => {
  if (newImage.path) {
    loadImage(newImage.path);

    // 加载当前图片的标注
    if (typeof newImage.annotations === 'string') {
      try {
        annotations.value = normalizeLoadedAnnotations(JSON.parse(newImage.annotations));
      } catch (e) {
        createMessage.error('标注解析失败');
        annotations.value = [];
      }
    } else {
      annotations.value = normalizeLoadedAnnotations([...newImage.annotations]);
    }
    isSaved.value = true;
  }
}, {immediate: true});

watch(labels, () => {
  if (annotations.value.length > 0) {
    annotations.value = normalizeLoadedAnnotations(annotations.value);
    draw();
  }
});

// 检查图片是否有标注
const hasAnnotations = (image: Image) => {
  if (typeof image.annotations === 'string') {
    try {
      const parsed = JSON.parse(image.annotations);
      return Array.isArray(parsed) && parsed.length > 0;
    } catch (e) {
      return false;
    }
  }
  return image.annotations && image.annotations.length > 0;
};

// 设置活动工具
const setActiveTool = (toolId: string): void => {
  activeTool.value = toolId;
  selectedAnnotationId.value = null;
  currentPoints.value = [];
};

// 设置当前标签
const setCurrentLabel = (index: number): void => {
  currentLabelIndex.value = index;
  console.log(`当前标签已设置为: ${labels.value[index].name} (shortcut: ${labels.value[index].shortcut})`);
};

const confirmDiscardUnsaved = (): Promise<boolean> => {
  if (isSaved.value) return Promise.resolve(true);
  return new Promise((resolve) => {
    createConfirm({
      iconType: 'warning',
      title: '未保存的标注',
      content: '当前图片有未保存的修改，切换后将丢失。是否继续？',
      onOk: () => resolve(true),
      onCancel: () => resolve(false),
    });
  });
};

const selectImageInList = async (img: Image): Promise<void> => {
  if (currentImage.value.id === img.id) return;
  const ok = await confirmDiscardUnsaved();
  if (!ok) return;
  const idx = images.value.findIndex((i) => i.id === img.id);
  if (idx >= 0) {
    currentImageIndex.value = idx;
    scrollListToActive();
  }
};

const isImageSelected = (id: number): boolean => selectedImageIds.value.has(id);

const toggleImageSelection = (id: number, checked: boolean): void => {
  const next = new Set(selectedImageIds.value);
  if (checked) {
    if (!next.has(id) && next.size >= MAX_BATCH_SELECTION) {
      createMessage.warning(`单次最多选择 ${MAX_BATCH_SELECTION} 张图片`);
      return;
    }
    next.add(id);
  } else {
    next.delete(id);
  }
  selectedImageIds.value = next;
};

const clearImageSelection = (): void => {
  selectedImageIds.value = new Set();
};

const selectAllImagesInChunk = (): void => {
  selectedImageIds.value = new Set(selectableImageIds.value);
  if (displayImages.value.length > MAX_BATCH_SELECTION) {
    createMessage.info(`已按单次限制选中前 ${MAX_BATCH_SELECTION} 张图片`);
  }
};

const toggleBatchSelectMode = (): void => {
  batchSelectMode.value = !batchSelectMode.value;
  if (!batchSelectMode.value) {
    clearImageSelection();
  }
};

const onImageListItemClick = async (img: Image): Promise<void> => {
  if (batchSelectMode.value) {
    toggleImageSelection(img.id, !isImageSelected(img.id));
    return;
  }
  await selectImageInList(img);
};

const buildDeleteConfirmContent = (ids: number[]): string => {
  const deletingCurrent = ids.includes(currentImage.value.id);
  let content = ids.length > 1
    ? `将永久删除 ${ids.length} 张图片及其标注和存储中的原图，此操作无法恢复。`
    : '删除后图片及标注数据将无法恢复，且会同时删除存储中的原图。';
  if (deletingCurrent && !isSaved.value) {
    content += ' 当前图片有未保存的标注，也将一并删除。';
  }
  if (ids.length === 1) {
    const name = images.value.find((i) => i.id === ids[0])?.name;
    if (name) {
      content = `「${name}」\n\n${content}`;
    }
  }
  return content;
};

const resolveIndexAfterDelete = (deletedIds: number[], prevGlobalIndex: number): number => {
  const deletedSet = new Set(deletedIds);
  const newTotal = Math.max(0, totalImages.value - deletedIds.length);
  if (newTotal <= 0) {
    return 0;
  }
  if (deletedSet.has(currentImage.value.id)) {
    return Math.min(prevGlobalIndex, newTotal - 1);
  }
  let deletedBefore = 0;
  for (let i = 0; i < images.value.length; i++) {
    const globalIdx = (listChunkPage.value - 1) * LIST_CHUNK_SIZE + i;
    if (globalIdx >= prevGlobalIndex) {
      break;
    }
    if (deletedSet.has(images.value[i].id)) {
      deletedBefore += 1;
    }
  }
  return Math.max(0, prevGlobalIndex - deletedBefore);
};

const deleteImagesByIds = async (ids: number[]): Promise<void> => {
  if (ids.length === 0 || listLoading.value) return;

  const uniqueIds = [...new Set(ids)];
  if (uniqueIds.length > MAX_BATCH_SELECTION) {
    createMessage.warning(`单次最多删除 ${MAX_BATCH_SELECTION} 张图片`);
    return;
  }
  const prevGlobalIndex = globalImageIndex.value;

  try {
    listLoading.value = true;
    if (uniqueIds.length === 1) {
      await deleteDatasetImage(uniqueIds[0]);
    } else {
      await deleteDatasetImages(uniqueIds);
    }

    clearImageSelection();
    batchSelectMode.value = false;
    isSaved.value = true;

    const nextGlobalIndex = resolveIndexAfterDelete(uniqueIds, prevGlobalIndex);
    const nextPage = Math.floor(nextGlobalIndex / LIST_CHUNK_SIZE) + 1;
    const nextIndex = nextGlobalIndex % LIST_CHUNK_SIZE;

    listChunkPage.value = nextPage;
    await fetchImages(nextPage);

    if (images.value.length > 0) {
      currentImageIndex.value = Math.min(nextIndex, images.value.length - 1);
    } else if (totalImages.value > 0) {
      const lastPage = Math.max(1, Math.ceil(totalImages.value / LIST_CHUNK_SIZE));
      listChunkPage.value = lastPage;
      await fetchImages(lastPage);
      currentImageIndex.value = Math.max(0, images.value.length - 1);
    } else {
      currentImageIndex.value = 0;
      annotations.value = [];
    }

    await refreshSyncCheck();
    createMessage.success(uniqueIds.length === 1 ? '图片已删除' : `已删除 ${uniqueIds.length} 张图片`);
  } catch {
    createMessage.error('删除失败');
  } finally {
    listLoading.value = false;
  }
};

const confirmDeleteCurrentImage = (): void => {
  if (totalImages.value === 0 || !currentImage.value.id) return;
  createConfirm({
    iconType: 'warning',
    title: '删除当前图片？',
    content: buildDeleteConfirmContent([currentImage.value.id]),
    okText: '删除',
    okType: 'danger',
    onOk: () => deleteImagesByIds([currentImage.value.id]),
  });
};

const confirmBatchDeleteSelected = (): void => {
  const ids = [...selectedImageIds.value];
  if (ids.length === 0) return;
  createConfirm({
    iconType: 'warning',
    title: `永久删除 ${ids.length} 张图片？`,
    content: buildDeleteConfirmContent(ids),
    okText: '删除',
    okType: 'danger',
    onOk: () => deleteImagesByIds(ids),
  });
};

const getImageStatusText = (img: Image): string => {
  if (img.completed === 1) return '已完成';
  if (hasAnnotations(img)) return '已标注';
  return '待标注';
};

const getImageStatusClass = (img: Image): string => {
  if (img.completed === 1) return 'status-completed';
  if (hasAnnotations(img)) return 'status-annotated';
  return 'status-pending';
};

// 选择图片（全局索引，用于键盘切换）
const selectImage = async (index: number): Promise<void> => {
  if (index < 0 || index >= totalImages.value) return;
  const ok = await confirmDiscardUnsaved();
  if (!ok) return;

  const targetPage = Math.floor(index / LIST_CHUNK_SIZE) + 1;
  const targetIndex = index % LIST_CHUNK_SIZE;

  if (targetPage !== listChunkPage.value) {
    listChunkPage.value = targetPage;
    await fetchImages(targetPage);
  }
  currentImageIndex.value = Math.min(targetIndex, Math.max(0, images.value.length - 1));
  scrollListToActive();
};

// 图片导航
const nextImage = async (): Promise<void> => {
  const newIndex = globalImageIndex.value + 1;
  if (newIndex < totalImages.value) {
    await selectImage(newIndex);
  }
};

const prevImage = async (): Promise<void> => {
  const newIndex = globalImageIndex.value - 1;
  if (newIndex >= 0) {
    await selectImage(newIndex);
  }
};

/** 跳到下一张未完成标注的图片，返回是否成功跳转 */
const jumpToNextPending = async (): Promise<boolean> => {
  if (totalImages.value === 0) {
    openImportModal();
    return false;
  }

  for (let i = currentImageIndex.value + 1; i < images.value.length; i++) {
    if (images.value[i].completed !== 1) {
      await selectImageInList(images.value[i]);
      return true;
    }
  }

  for (let g = globalImageIndex.value + 1; g < totalImages.value; g++) {
    await selectImage(g);
    if (currentImage.value.completed !== 1) {
      return true;
    }
  }

  for (let g = 0; g < globalImageIndex.value; g++) {
    await selectImage(g);
    if (currentImage.value.completed !== 1) {
      return true;
    }
  }

  createMessage.success('全部图片已标注完成');
  return false;
};

// 更新图片状态
const updateImageStatus = (modified: boolean = true) => {
  if (modified) {
    currentImage.value.modificationCount += 1;
    currentImage.value.lastModified = new Date();
    currentImage.value.completed = 0;
    isSaved.value = false;
  }
};

// 保存当前状态到历史记录
const saveToHistory = () => {
  historyStack.value.push(JSON.parse(JSON.stringify(annotations.value)));
  if (historyStack.value.length > 50) {
    historyStack.value.shift();
  }
  isSaved.value = false;
};

// 撤销操作
const undo = () => {
  if (historyStack.value.length > 0) {
    const prevState = historyStack.value.pop();
    if (prevState) {
      annotations.value = JSON.parse(JSON.stringify(prevState));
      draw();
      updateImageStatus();
    }
  }
};

// 从后端获取标签（无默认占位标签）
const fetchLabels = async (): Promise<void> => {
  try {
    const list: DatasetTagItem[] = await fetchDatasetTags(route.params['id']);
    labels.value = list.map((tag) => ({
      id: tag.id,
      name: tag.name,
      color: tag.color,
      shortcut: tag.shortcut,
    }));
    if (labels.value.length > 0 && currentLabelIndex.value >= labels.value.length) {
      currentLabelIndex.value = 0;
    }
  } catch {
    labels.value = [];
    currentLabelIndex.value = 0;
  }
};

/** 导入后刷新标签：优先后端 import 响应，仅在无 tagsCreated/classes 时前端兜底扫描 */
async function syncTagsAfterImport(importResult?: DatasetAnnotationImportResult): Promise<void> {
  const tagsCreated = importResult?.tagsCreated ?? 0;
  const classNames =
    importResult?.classes ??
    (importResult as { class_names?: string[] })?.class_names;

  if (tagsCreated > 0 || (classNames && classNames.length > 0)) {
    await fetchLabels();
    if (tagsCreated > 0) {
      createMessage.success(`已从导入数据创建 ${tagsCreated} 个标签`);
    }
    return;
  }

  const created = await syncTagsFromImport(route.params['id'], {classNames});
  await fetchLabels();
  if (created > 0) {
    createMessage.success(`已从导入数据创建 ${created} 个标签`);
  }
}

const mapImageRow = (img: any): Image => {
  let rowAnnotations: Annotation[] | string = [];
  if (img.annotations) {
    try {
      rowAnnotations = typeof img.annotations === 'string'
        ? JSON.parse(img.annotations)
        : img.annotations;
    } catch {
      rowAnnotations = [];
    }
  }
  return {
    id: img.id,
    name: img.name,
    path: img.path,
    annotations: rowAnnotations,
    completed: img.completed || 0,
    modificationCount: img.modificationCount || 0,
    lastModified: img.lastModified ? new Date(img.lastModified) : null,
  };
};

const fetchCompletedCount = async (): Promise<void> => {
  try {
    const res = await getDatasetImagePage({
      datasetId: route.params['id'],
      pageNo: 1,
      pageSize: 1,
      completed: 1,
    });
    completedCount.value = res?.total ?? 0;
  } catch {
    completedCount.value = images.value.filter((i) => i.completed === 1).length;
  }
};

/** 加载左侧列表的一个分块（单次最多 LIST_CHUNK_SIZE 条） */
const fetchImages = async (chunkPage: number = 1): Promise<void> => {
  listLoading.value = true;
  try {
    const res = await getDatasetImagePage(buildListQueryParams(chunkPage));

    if (res?.list) {
      totalImages.value = res.total ?? res.list.length;

      let mapped = res.list.map(mapImageRow);
      if (listFilterStatus.value === 'annotated') {
        mapped = mapped.filter((img) => hasAnnotations(img));
      }

      images.value = mapped;
      listChunkPage.value = chunkPage;

      if (images.value.length > 0 && currentImageIndex.value >= images.value.length) {
        currentImageIndex.value = 0;
      }
      await fetchCompletedCount();
      scrollListToActive();
    }
  } catch (error) {
    createMessage.error('获取图片失败:' + error);
    images.value = [];
    totalImages.value = 0;
  } finally {
    listLoading.value = false;
  }
};

// 保存标注到后端（简化版）
const saveAnnotationsToDB = async (requestData: SaveAnnotationRequest): Promise<void> => {
  try {
    requestData['datasetId'] = route.params['id'];
    await updateDatasetImage(requestData);
  } catch (error) {
    createMessage.error('保存到数据库失败:' + error);
    throw error; // 重新抛出错误
  }
};

// 格式化日期时间
const formatDateTime = (date: Date | null): string => {
  if (!date) return '从未修改';

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date);
};

type SaveOptions = {
  /** 保存成功后跳到下一张待标注 */
  jumpToNextPending?: boolean;
  /** 不弹出成功提示（用于保存并下一张，避免连弹两条） */
  quiet?: boolean;
};

// 保存当前标注
const saveCurrentAnnotations = async (options?: SaveOptions): Promise<boolean> => {
  if (saving.value) return false;

  if (annotations.value.length === 0) {
    createMessage.warning('请至少标注一个对象');
    return false;
  }

  saving.value = true;

  try {
    const updatedStatus = {
      completed: 1 as 0 | 1,
      modificationCount: currentImage.value.modificationCount + 1,
      lastModified: new Date(),
    };

    const requestData: SaveAnnotationRequest = {
      id: currentImage.value.id,
      name: currentImage.value.name,
      annotations: JSON.stringify(annotations.value),
      ...updatedStatus,
    };

    await saveAnnotationsToDB(requestData);

    const currentId = currentImage.value.id;
    const imageIndex = images.value.findIndex((img) => img.id === currentId);
    if (imageIndex !== -1) {
      images.value[imageIndex] = {
        ...images.value[imageIndex],
        ...updatedStatus,
        annotations: requestData.annotations,
      };
    }

    try {
      imageAnnotations.value[currentId] = JSON.parse(requestData.annotations);
    } catch {
      imageAnnotations.value[currentId] = [];
    }

    if (!options?.quiet) {
      createMessage.success('标注保存成功');
    }
    isSaved.value = true;
    await fetchCompletedCount();
    await refreshSyncCheck();

    if (options?.jumpToNextPending) {
      await jumpToNextPending();
    }
    return true;
  } catch (error) {
    createMessage.error('保存失败:' + error);
    return false;
  } finally {
    saving.value = false;
  }
};

/** 保存并跳到下一张待标注（已保存且已完成时仅跳转） */
const saveAndJumpToNextPending = async (): Promise<void> => {
  if (saving.value || totalImages.value === 0) return;

  if (annotations.value.length === 0) {
    createMessage.warning('请至少标注一个对象');
    return;
  }

  const alreadySaved = isSaved.value && currentImage.value.completed === 1;
  if (alreadySaved) {
    await jumpToNextPending();
    return;
  }

  const saved = await saveCurrentAnnotations({jumpToNextPending: true, quiet: true});
  if (saved) {
    createMessage.success('已保存并跳到下一张待标注');
  }
};

const handleCanvasWheel = (e: WheelEvent): void => {
  if (!imageLoaded.value) return;
  const delta = e.deltaY > 0 ? -0.08 : 0.08;
  zoomLevel.value = Math.min(5, Math.max(0.05, zoomLevel.value + delta * zoomLevel.value));
  draw();
};

// 初始化画布
const initCanvas = (): void => {
  if (!canvas.value) return;

  ctx.value = canvas.value.getContext('2d');
  resizeCanvas();
  draw();
};

// 调整画布大小 - 优化版
const resizeCanvas = (): void => {
  if (!canvas.value) return;

  const container = canvas.value.parentElement;
  if (!container) return;

  // 保存当前状态
  const wasDrawing = isDrawing.value;
  const hadPoints = [...currentPoints.value];

  // 暂停绘制状态
  isDrawing.value = false;
  currentPoints.value = [];

  // 更新画布尺寸
  canvas.value.width = container.clientWidth;
  canvas.value.height = container.clientHeight;

  // 恢复状态
  requestAnimationFrame(() => {
    isDrawing.value = wasDrawing;
    currentPoints.value = hadPoints;
    draw();
  });
};

// 添加防抖处理 - 优化性能
let resizeTimeout: number | null = null;
const handleResize = () => {
  if (resizeTimeout) clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    resizeCanvas();
  }, 100) as unknown as number;
};

// 绘制网格背景
const drawGridBackground = (): void => {
  if (!ctx.value || !canvas.value) return;

  ctx.value.fillStyle = '#2d3748';
  ctx.value.fillRect(0, 0, canvas.value.width, canvas.value.height);

  ctx.value.strokeStyle = '#3c4757';
  ctx.value.lineWidth = 1;

  for (let x = 0; x < canvas.value.width; x += 25) {
    ctx.value.beginPath();
    ctx.value.moveTo(x, 0);
    ctx.value.lineTo(x, canvas.value.height);
    ctx.value.stroke();
  }

  for (let y = 0; y < canvas.value.height; y += 25) {
    ctx.value.beginPath();
    ctx.value.moveTo(0, y);
    ctx.value.lineTo(canvas.value.width, y);
    ctx.value.stroke();
  }

  ctx.value.fillStyle = '#4cc9f0';
  ctx.value.beginPath();
  ctx.value.arc(canvas.value.width / 2, canvas.value.height / 2, 5, 0, Math.PI * 2);
  ctx.value.fill();
};

// 修改绘制逻辑
const draw = (): void => {
  if (!ctx.value || !canvas.value) return;

  // 清空画布
  ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height);

  // 绘制网格背景
  drawGridBackground();

  if (currentImageObj.value && imageLoaded.value) {
    const img = currentImageObj.value;

    // 计算缩放后的尺寸
    const scaledWidth = img.width * zoomLevel.value;
    const scaledHeight = img.height * zoomLevel.value;

    // 计算居中位置
    const x = (canvas.value.width - scaledWidth) / 2 + offsetX.value;
    const y = (canvas.value.height - scaledHeight) / 2 + offsetY.value;

    // 保存显示尺寸用于坐标转换
    imageDisplaySize.value = {
      x: x,
      y: y,
      width: scaledWidth,
      height: scaledHeight
    };

    // 绘制图片
    ctx.value.drawImage(img, x, y, scaledWidth, scaledHeight);
  }

  // 绘制标注
  annotations.value.forEach(annotation => {
    drawAnnotation(annotation);
  });

  // 绘制当前标注
  if (isDrawing.value && currentPoints.value.length > 0) {
    drawCurrentAnnotation();
  }
};

// 绘制单个标注
const drawAnnotation = (annotation: Annotation): void => {
  if (!ctx.value || !imageDisplaySize.value) return;

  const {x: imgX, y: imgY, width: imgWidth, height: imgHeight} = imageDisplaySize.value;
  const color = resolveAnnotationColor(annotation.label, annotation.color);
  const isSelected = annotation.id === selectedAnnotationId.value;

  const toCanvasCoords = (point: Point) => ({
    x: imgX + point.x * imgWidth,
    y: imgY + point.y * imgHeight
  });

  ctx.value.save();
  ctx.value.strokeStyle = color;
  ctx.value.lineWidth = isSelected ? ANNOTATION_SELECTED_STROKE_WIDTH : ANNOTATION_STROKE_WIDTH;
  ctx.value.fillStyle = colorWithAlpha(color, ANNOTATION_FILL_ALPHA);

  if (annotation.points.length > 0) {
    const startPoint = toCanvasCoords(annotation.points[0]);
    ctx.value.beginPath();
    ctx.value.moveTo(startPoint.x, startPoint.y);

    for (let i = 1; i < annotation.points.length; i++) {
      const point = toCanvasCoords(annotation.points[i]);
      ctx.value.lineTo(point.x, point.y);
    }

    if (annotation.type === AnnotationType.RECTANGLE ||
      annotation.type === AnnotationType.POLYGON) {
      ctx.value.closePath();
    }

    ctx.value.fill();
    ctx.value.stroke();
    drawAnnotationLabel(annotation, startPoint.x, startPoint.y, color);
  }

  ctx.value.restore();
};

// 绘制当前正在创建的标注
const drawCurrentAnnotation = (): void => {
  if (!ctx.value || !imageDisplaySize.value || currentPoints.value.length === 0) return;

  const {x: imgX, y: imgY, width: imgWidth, height: imgHeight} = imageDisplaySize.value;

  // 转换归一化坐标为实际canvas坐标
  const toCanvasCoords = (point: Point) => ({
    x: imgX + point.x * imgWidth,
    y: imgY + point.y * imgHeight
  });

  const draftColor = currentLabel.value?.color ?? '#4361ee';
  ctx.value.save();
  ctx.value.strokeStyle = draftColor;
  ctx.value.lineWidth = ANNOTATION_STROKE_WIDTH;
  ctx.value.fillStyle = colorWithAlpha(draftColor, ANNOTATION_FILL_ALPHA);

  switch (activeTool.value) {
    case ToolType.RECTANGLE:
      const rectStart = toCanvasCoords(currentPoints.value[0]);
      const rectEnd = toCanvasCoords({x: startX.value, y: startY.value});
      const width = rectEnd.x - rectStart.x;
      const height = rectEnd.y - rectStart.y;

      ctx.value.beginPath();
      ctx.value.rect(rectStart.x, rectStart.y, width, height);
      ctx.value.fill();
      ctx.value.stroke();

      drawAnnotationLabel({
        id: 0,
        type: AnnotationType.RECTANGLE,
        label: currentLabel.value.shortcut,
        color: draftColor,
        points: [
          {x: currentPoints.value[0].x, y: currentPoints.value[0].y},
          {x: currentPoints.value[0].x + width / imgWidth, y: currentPoints.value[0].y},
          {
            x: currentPoints.value[0].x + width / imgWidth,
            y: currentPoints.value[0].y + height / imgHeight
          },
          {x: currentPoints.value[0].x, y: currentPoints.value[0].y + height / imgHeight}
        ]
      }, rectStart.x, rectStart.y, draftColor);
      break;

    case ToolType.POLYGON:
      if (currentPoints.value.length > 0) {
        ctx.value.beginPath();
        const firstPoint = toCanvasCoords(currentPoints.value[0]);
        ctx.value.moveTo(firstPoint.x, firstPoint.y);

        for (let i = 1; i < currentPoints.value.length; i++) {
          const point = toCanvasCoords(currentPoints.value[i]);
          ctx.value.lineTo(point.x, point.y);
        }

        const currentPoint = toCanvasCoords({x: startX.value, y: startY.value});
        ctx.value.lineTo(currentPoint.x, currentPoint.y);
        ctx.value.stroke();

        ctx.value.fillStyle = draftColor;
        currentPoints.value.forEach(point => {
          const canvasPoint = toCanvasCoords(point);
          ctx.value.beginPath();
          ctx.value.arc(canvasPoint.x, canvasPoint.y, 4, 0, Math.PI * 2);
          ctx.value.fill();
        });
      }
      break;
  }

  ctx.value.restore();
};

// 绘制标注名称标签
const drawAnnotationLabel = (
  annotation: Annotation,
  x: number,
  y: number,
  color?: string,
): void => {
  if (!ctx.value) return;

  const labelColor = color ?? resolveAnnotationColor(annotation.label, annotation.color);
  const labelName = getLabelName(annotation.label);

  ctx.value.save();
  ctx.value.font = '12px Inter, sans-serif';
  const textWidth = ctx.value.measureText(labelName).width;
  const padX = 4;
  const padY = 2;
  const boxH = 16;
  const boxW = textWidth + padX * 2;

  ctx.value.fillStyle = colorWithAlpha(labelColor, 0.85);
  ctx.value.fillRect(x, y - boxH - 4, boxW, boxH);
  ctx.value.fillStyle = '#fff';
  ctx.value.fillText(labelName, x + padX, y - 6);

  ctx.value.restore();
};

// 检查点是否在标注内
const isPointInAnnotation = (annotation: Annotation, x: number, y: number): boolean => {
  if (annotation.type === AnnotationType.RECTANGLE) {
    const [p1, p2, p3, p4] = annotation.points;
    const minX = Math.min(p1.x, p2.x, p3.x, p4.x);
    const maxX = Math.max(p1.x, p2.x, p3.x, p4.x);
    const minY = Math.min(p1.y, p2.y, p3.y, p4.y);
    const maxY = Math.max(p1.y, p2.y, p3.y, p4.y);

    return x >= minX && x <= maxX && y >= minY && y <= maxY;
  } else if (annotation.type === AnnotationType.POLYGON) {
    let inside = false;
    for (let i = 0, j = annotation.points.length - 1; i < annotation.points.length; j = i++) {
      const xi = annotation.points[i].x;
      const yi = annotation.points[i].y;
      const xj = annotation.points[j].x;
      const yj = annotation.points[j].y;

      const intersect = ((yi > y) !== (yj > y)) &&
        (x < ((xj - xi) * (y - yi)) / (yj - yi) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  }
  return false;
};

// 选择标注
const selectAnnotation = (id: number): void => {
  selectedAnnotationId.value = id;
  draw();
};

// 删除标注
const deleteAnnotation = (id: number): void => {
  saveToHistory();
  annotations.value = annotations.value.filter(a => a.id !== id);
  if (selectedAnnotationId.value === id) {
    selectedAnnotationId.value = null;
  }
  draw();
  updateImageStatus();
};

// 鼠标事件处理
const handleMouseDown = (e: MouseEvent): void => {
  if (!canvas.value || !imageDisplaySize.value) return;

  const rect = canvas.value.getBoundingClientRect();
  const canvasX = e.clientX - rect.left;
  const canvasY = e.clientY - rect.top;

  const {x: imgX, y: imgY, width: imgWidth, height: imgHeight} = imageDisplaySize.value;

  // 转换为归一化坐标 (0-1)
  const x = (canvasX - imgX) / imgWidth;
  const y = (canvasY - imgY) / imgHeight;

  // 确保坐标在图片范围内
  if (x < 0 || x > 1 || y < 0 || y > 1) return;

  startX.value = x;
  startY.value = y;

  if (activeTool.value === ToolType.SELECT) {
    let clickedAnnotation = false;

    for (let i = annotations.value.length - 1; i >= 0; i--) {
      const annotation = annotations.value[i];
      if (isPointInAnnotation(annotation, x, y)) {
        selectedAnnotationId.value = annotation.id;
        clickedAnnotation = true;
        saveToHistory();
        break;
      }
    }

    if (!clickedAnnotation) {
      selectedAnnotationId.value = null;
    }
    draw();
    return;
  }

  if ([ToolType.RECTANGLE, ToolType.POLYGON].includes(activeTool.value)) {
    isDrawing.value = true;

    if (activeTool.value === ToolType.POLYGON && currentPoints.value.length === 0) {
      currentPoints.value.push({x, y});
    } else if (activeTool.value !== ToolType.POLYGON) {
      currentPoints.value = [{x, y}];
    }

    saveToHistory();
    updateImageStatus();
  }
};

const handleMouseMove = (e: MouseEvent): void => {
  if (!canvas.value || !imageDisplaySize.value) return;

  const rect = canvas.value.getBoundingClientRect();
  const canvasX = e.clientX - rect.left;
  const canvasY = e.clientY - rect.top;

  const {x: imgX, y: imgY, width: imgWidth, height: imgHeight} = imageDisplaySize.value;

  // 转换为归一化坐标 (0-1)
  const x = (canvasX - imgX) / imgWidth;
  const y = (canvasY - imgY) / imgHeight;

  startX.value = x;
  startY.value = y;

  if (isDrawing.value) {
    draw();
  }
};

const handleMouseUp = (): void => {
  if (isDrawing.value && currentPoints.value.length > 0) {
    if (activeTool.value === ToolType.RECTANGLE) {
      const width = startX.value - currentPoints.value[0].x;
      const height = startY.value - currentPoints.value[0].y;

      if (Math.abs(width) > 0.01 && Math.abs(height) > 0.01) {
        console.log(`创建矩形标注，使用标签: ${currentLabel.value.name} (shortcut: ${currentLabel.value.shortcut})`);

        const newAnnotation: Annotation = {
          id: Date.now(),
          type: AnnotationType.RECTANGLE,
          label: currentLabel.value.shortcut, // 确保使用 shortcut
          color: currentLabel.value.color,
          points: [
            {x: currentPoints.value[0].x, y: currentPoints.value[0].y},
            {x: currentPoints.value[0].x + width, y: currentPoints.value[0].y},
            {x: currentPoints.value[0].x + width, y: currentPoints.value[0].y + height},
            {x: currentPoints.value[0].x, y: currentPoints.value[0].y + height}
          ]
        };

        annotations.value.push(newAnnotation);
        selectedAnnotationId.value = newAnnotation.id;
        draw();
      }
    } else if (activeTool.value === ToolType.POLYGON) {
      currentPoints.value.push({x: startX.value, y: startY.value});
      return;
    }

    isDrawing.value = false;
    currentPoints.value = [];
  }
};

const handleDoubleClick = (): void => {
  if (activeTool.value === ToolType.POLYGON && currentPoints.value.length > 2) {
    console.log(`创建多边形标注，使用标签: ${currentLabel.value.name} (shortcut: ${currentLabel.value.shortcut})`);

    const newAnnotation: Annotation = {
      id: Date.now(),
      type: AnnotationType.POLYGON,
      label: currentLabel.value.shortcut, // 确保使用 shortcut
      color: currentLabel.value.color,
      points: [...currentPoints.value]
    };

    annotations.value.push(newAnnotation);
    selectedAnnotationId.value = newAnnotation.id;
    draw();

    isDrawing.value = false;
    currentPoints.value = [];
  }
};

/** 全屏时 Modal/下拉层须挂到全屏元素内，否则浏览器不会显示（默认挂 body） */
const getModalContainer = (): HTMLElement => {
  const fsEl =
    document.fullscreenElement ||
    (document as any).webkitFullscreenElement ||
    (document as any).msFullscreenElement;
  if (fsEl instanceof HTMLElement) {
    return fsEl;
  }
  return document.body;
};

// 全屏切换逻辑
const toggleFullscreen = () => {
  if (!container.value) return;

  if (!isFullscreen.value) {
    const element = container.value;
    if (element.requestFullscreen) {
      element.requestFullscreen();
    } else if ((element as any).webkitRequestFullscreen) {
      (element as any).webkitRequestFullscreen();
    } else if ((element as any).msRequestFullscreen) {
      (element as any).msRequestFullscreen();
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if ((document as any).webkitExitFullscreen) {
      (document as any).webkitExitFullscreen();
    } else if ((document as any).msExitFullscreen) {
      (document as any).msExitFullscreen();
    }
  }
};

// 处理全屏变化
const handleFullscreenChange = () => {
  isFullscreen.value = Boolean(
    document.fullscreenElement ||
    (document as any).webkitFullscreenElement ||
    (document as any).msFullscreenElement
  );

  requestAnimationFrame(() => {
    resizeCanvas();
  });
};

const isTypingInInput = (): boolean => {
  const el = document.activeElement as HTMLElement | null;
  if (!el) return false;
  return !!el.closest('.ant-input, .ant-select, textarea, input, select');
};

// 键盘快捷键
const handleKeyDown = (e: KeyboardEvent): void => {
  if (isTypingInInput()) {
    return;
  }

  if (e.ctrlKey) {
    if (e.key === 's' || e.key === 'S') {
      e.preventDefault();
      if (e.shiftKey) {
        saveAndJumpToNextPending();
      } else {
        saveCurrentAnnotations();
      }
    } else if (e.key === 'z') {
      e.preventDefault();
      undo();
    }
  }

  switch (e.key) {
    case '1':
    case '2':
    case '3':
    case '4':
    case '5':
    case '6':
    case '7':
    case '8':
    case '9':
    case '0':
      const shortcut = e.key;
      const index = labels.value.findIndex(l => l.shortcut === shortcut);
      if (index !== -1) {
        setCurrentLabel(index);
      } else {
        console.warn(`未找到匹配的标签 shortcut: ${shortcut}`);
      }
      break;
    case 'r':
      setActiveTool(ToolType.RECTANGLE);
      break;
    case 'p':
      setActiveTool(ToolType.POLYGON);
      break;
    case 'v':
      setActiveTool(ToolType.SELECT);
      break;
    case 'ArrowRight':
    case ' ':
      e.preventDefault();
      nextImage();
      break;
    case 'ArrowLeft':
      prevImage();
      break;
    case 'n':
    case 'N':
      e.preventDefault();
      jumpToNextPending();
      break;
    case 'b':
    case 'B':
      prevImage();
      break;
    case 'Delete':
      if (e.shiftKey && totalImages.value > 0) {
        e.preventDefault();
        confirmDeleteCurrentImage();
      } else if (selectedAnnotationId.value !== null) {
        deleteAnnotation(selectedAnnotationId.value);
      }
      break;
    case 'Escape':
      if (isDrawing.value && activeTool.value === ToolType.POLYGON) {
        isDrawing.value = false;
        currentPoints.value = [];
        draw();
      }
      break;
    case 'f':
      toggleFullscreen();
      break;
  }
};

function openAiBatchModal(): void {
  aiLabelModalRef.value?.openModal();
}

async function refreshSamModelStatus(): Promise<boolean> {
  try {
    const res = await getSamModelStatus();
    samModelReady.value = !!res?.data?.exists;
  } catch {
    samModelReady.value = false;
  } finally {
    samModelChecked.value = true;
  }
  return samModelReady.value;
}

async function openSamAutoLabelDrawer(): Promise<void> {
  const ready = await refreshSamModelStatus();
  if (!ready) {
    router.push({
      name: 'SamModelSetup',
      query: {
        datasetId: String(route.params.id ?? ''),
        autoOpen: '1',
      },
    });
    return;
  }
  openSamDrawer(true);
}

function openUnattendedLabelDrawer(): void {
  openUnattendedDrawer(true, {});
}

async function reloadUnattendedFrameTasks(): Promise<void> {
  await unattendedDrawerRef.value?.reloadFrameTasks();
}

async function onUnattendedLabelSuccess(): Promise<void> {
  await fetchImages();
}

function openSamModelSetupPage(): void {
  router.push({
    name: 'SamModelSetup',
    query: {
      datasetId: String(route.params.id ?? ''),
    },
  });
}

function openImportModal(): void {
  importModalRef.value?.openModal();
}

function openExportModal(): void {
  exportModalRef.value?.openModal();
}

function openImageUploadModal(isZip = false): void {
  openImageUploadModalInner(true, {
    datasetId: route.params['id'],
    isImage: !isZip,
    isZip,
    isVideo: false,
    isStream: false,
  });
}

function openManageDrawer(tab: ManageDrawerTab = 'tags'): void {
  manageDrawerTab.value = tab;
  manageDrawerOpen.value = true;
}

function onWorkflowAction(key: WorkflowStepKey): void {
  switch (key) {
    case 'import':
      openImportModal();
      break;
    case 'annotate':
      if (pendingCount.value > 0) {
        listFilterStatus.value = 'pending';
        jumpToNextPending();
      }
      break;
    case 'split':
      handleSplitDataset();
      break;
    case 'sync':
      handleSyncToMinio();
      break;
  }
}

function onTipAction(action: TipAction): void {
  switch (action) {
    case 'import':
      openImportModal();
      break;
    case 'aiLabel':
      openAiBatchModal();
      break;
    case 'nextPending':
      jumpToNextPending();
      break;
    case 'split':
      handleSplitDataset();
      break;
    case 'sync':
      handleSyncToMinio();
      break;
    case 'filterPending':
      listFilterStatus.value = 'pending';
      break;
  }
}

function onAddMenuClick({key}: { key: string }): void {
  switch (key) {
    case 'import':
      openImportModal();
      break;
    case 'upload':
      openImageUploadModal(false);
      break;
    case 'zip':
      openImageUploadModal(true);
      break;
    case 'frame':
      openManageDrawer('frame');
      break;
    case 'video':
      openManageDrawer('video');
      break;
  }
}

function onTrainMenuClick({key}: { key: string }): void {
  switch (key) {
    case 'split':
      handleSplitDataset();
      break;
    case 'reset':
      handleResetDataset();
      break;
    case 'export':
      openExportModal();
      break;
    case 'sync':
      handleSyncToMinio();
      break;
  }
}

function focusLabelAdd(): void {
  labelPanelRef.value?.focusAddInput();
}

async function onLabelsChanged(addedName?: string): Promise<void> {
  await fetchLabels();
  if (addedName) {
    const idx = labels.value.findIndex((l) => l.name === addedName);
    if (idx >= 0) setCurrentLabel(idx);
    else if (labels.value.length > 0) setCurrentLabel(labels.value.length - 1);
  }
}

async function onImageUploadSuccess(): Promise<void> {
  listChunkPage.value = 1;
  await fetchImages(1);
  await syncTagsAfterImport();
  await refreshSyncCheck();
}

function handleSplitDataset(): void {
  createConfirm({
    iconType: 'warning',
    title: '按比例划分数据集用途？',
    content: '将按 7:2:1 划分为训练集、验证集、测试集。',
    onOk: async () => {
      try {
        await splitDataset(route.params.id, {trainRatio: 0.7, valRatio: 0.2, testRatio: 0.1});
        createMessage.success('数据集划分成功');
        await refreshSyncCheck();
      } catch {
        createMessage.error('数据集划分失败');
      }
    },
  });
}

function handleResetDataset(): void {
  createConfirm({
    iconType: 'warning',
    title: '重置数据集用途？',
    content: '将清除所有图片的训练/验证/测试集划分。',
    onOk: async () => {
      try {
        await resetDataset(route.params.id);
        createMessage.success('数据集用途已重置');
        await refreshSyncCheck();
      } catch {
        createMessage.error('重置数据集用途失败');
      }
    },
  });
}

function monitorMinioSync(notifyCompletion: boolean) {
  syncPollController?.abort();
  const controller = new AbortController();
  syncPollController = controller;
  void waitForDatasetMinioSync(route.params.id, {
    signal: controller.signal,
    onStatus: (status) => {
      Object.assign(syncCheck, status);
      syncConnectionError.value = null;
    },
    onPollError: (error) => {
      syncConnectionError.value = error.message || '状态查询失败';
    },
  }).then(() => {
    if (notifyCompletion) {
      createMessage.success('数据集已同步到 Minio');
    }
    refreshSyncCheck();
  }).catch((error: Error) => {
    if (error.name !== 'AbortError') {
      createMessage.error(error.message || '同步数据集失败');
      refreshSyncCheck();
    }
  }).finally(() => {
    if (syncPollController === controller) {
      syncPollController = null;
    }
  });
}

function handleSyncToMinio(): void {
  createConfirm({
    iconType: 'info',
    title: '同步数据集到 Minio？',
    onOk: async () => {
      try {
        const latestStatus = await refreshSyncCheck();
        if (!latestStatus) {
          createMessage.error('无法确认当前同步状态，请检查网络后重试');
          return;
        }
        if (syncCheck.syncedToMinio) {
          createMessage.info('数据集已同步到 Minio，无需重复提交');
          return;
        }
        if (syncCheck.syncing) {
          createMessage.info('数据集正在同步，请等待完成');
          monitorMinioSync(false);
          return;
        }
        if (!syncCheck.usageAllocated) {
          createMessage.error('请先划分数据集用途后再同步');
          return;
        }
        if (!syncCheck.annotationCompleted) {
          createMessage.error(`尚有 ${syncCheck.unannotatedCount} 张图片未完成标注`);
          return;
        }
        await syncToMinio(route.params.id);
        Object.assign(syncCheck, {
          syncing: true,
          syncError: null,
          syncStatus: 'QUEUED',
          syncStage: 'WAITING',
          syncProgress: 0,
          processedImages: 0,
          syncSubmittedAt: new Date().toISOString(),
          syncStartedAt: null,
          syncFinishedAt: null,
        });
        syncConnectionError.value = null;
        createMessage.info('同步任务已提交，正在后台处理');
        monitorMinioSync(true);
      } catch (error: any) {
        createMessage.error(error?.message || '同步数据集失败');
      }
    },
  });
}

async function handleRefreshSyncStatus() {
  const status = await refreshSyncCheck();
  if (status?.syncing) {
    monitorMinioSync(false);
  }
}

function handleStartTrain() {
  void router.push({
    path: '/train',
    query: {tab: '6', launch: '1', datasetId: String(route.params.id)},
  });
}

async function onImportSuccess(importResult?: DatasetAnnotationImportResult): Promise<void> {
  listChunkPage.value = 1;
  await fetchImages(1);
  await syncTagsAfterImport(importResult);
  await refreshSyncCheck();
}

function resetBatchTaskProgress(): void {
  batchTaskProgress.total = 0;
  batchTaskProgress.processed = 0;
  batchTaskProgress.success = 0;
  batchTaskProgress.failed = 0;
}

function applyBatchTaskProgress(task: Record<string, unknown>): void {
  batchTaskProgress.total = Number(task.total_images ?? 0);
  batchTaskProgress.processed = Number(task.processed_images ?? 0);
  batchTaskProgress.success = Number(task.success_count ?? 0);
  batchTaskProgress.failed = Number(task.failed_count ?? 0);
}

function clearBatchTaskPollTimer(): void {
  if (batchTaskPollTimer) {
    clearInterval(batchTaskPollTimer);
    batchTaskPollTimer = null;
  }
}

function stopBatchTaskPoll(): void {
  clearBatchTaskPollTimer();
  batchTaskRunning.value = false;
  resetBatchTaskProgress();
}

let batchTaskPollFailCount = 0;

async function pollBatchTask(taskId: number): Promise<void> {
  clearBatchTaskPollTimer();
  resetBatchTaskProgress();
  batchTaskRunning.value = true;
  batchTaskPollFailCount = 0;

  const check = async () => {
    try {
      const res = await getAutoLabelTask(datasetId.value, taskId);
      batchTaskPollFailCount = 0;
      const task = (res?.data ?? res) as Record<string, unknown>;
      applyBatchTaskProgress(task);
      const status = task?.status as string | undefined;
      if (status === 'COMPLETED') {
        stopBatchTaskPoll();
        const processed = Number(task.processed_images ?? 0);
        const success = Number(task.success_count ?? 0);
        const failed = Number(task.failed_count ?? 0);
        createMessage.success(
          `AI 批量标注完成：处理 ${processed} 张，成功 ${success} 张${failed > 0 ? `，失败 ${failed} 张` : ''}`,
        );
        listChunkPage.value = 1;
        await fetchImages(1);
        await syncTagsAfterImport();
        await refreshSyncCheck();
      } else if (status === 'FAILED') {
        stopBatchTaskPoll();
        createMessage.error(String(task?.error_message || 'AI 批量标注失败'));
      }
    } catch {
      batchTaskPollFailCount += 1;
      if (batchTaskPollFailCount >= 5) {
        stopBatchTaskPoll();
        createMessage.warning('任务进度查询失败，请在大抽屉中查看任务状态');
      }
    }
  };

  await check();
  batchTaskPollTimer = setInterval(check, 2500);
}

function onBatchAiSuccess(payload: { taskId?: number }): void {
  if (payload?.taskId) {
    pollBatchTask(payload.taskId);
  }
}

// 初始化
onMounted(() => {
  initCanvas();
  window.addEventListener('resize', handleResize);
  window.addEventListener('keydown', handleKeyDown);
  window.addEventListener('resize', resizeCanvas);

  document.addEventListener('fullscreenchange', handleFullscreenChange);
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
  document.addEventListener('msfullscreenchange', handleFullscreenChange);

  fetchLabels();
  fetchImages(1);
  refreshSyncCheck().then((status) => {
    if (status?.syncing) {
      monitorMinioSync(false);
    }
  });
  refreshSamModelStatus().then((ready) => {
    if (route.query.openSam === '1' && ready) {
      const nextQuery = { ...route.query };
      delete nextQuery.openSam;
      router.replace({ query: nextQuery });
      openSamDrawer(true);
    }
  });
});

onUnmounted(() => {
  stopBatchTaskPoll();
  syncPollController?.abort();
  window.removeEventListener('resize', handleResize);
  window.removeEventListener('keydown', handleKeyDown);
  window.removeEventListener('resize', resizeCanvas);
  document.removeEventListener('fullscreenchange', handleFullscreenChange);
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
  document.removeEventListener('msfullscreenchange', handleFullscreenChange);
});
</script>

<style lang="less">
// 定义LESS变量
@primary-color: #4361ee;
@success-color: #4cc9f0;
@warning-color: #f8961e;
@error-color: #f72585;
@dark-color: #1a1c2c;
@light-color: #f8f9fa;
@gray-color: #6c757d;
@border-color: #dee2e6;

.annotation-container {
  height: min(92vh, 900px);
  display: flex;
  flex-direction: column;
  background: @dark-color;
  transition: all 0.3s ease;

  .top-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 8px 12px;
    background: #fff;
    border-bottom: 1px solid #e8e8e8;
    flex-shrink: 0;
    flex-wrap: wrap;

    .toolbar-left {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
      flex: 1;
      flex-wrap: wrap;
    }

    .toolbar-progress {
      font-size: 13px;
      color: #595959;
      white-space: nowrap;

      strong {
        color: @primary-color;
      }

      .progress-percent {
        color: #8c8c8c;
        font-size: 12px;
      }
    }

    .batch-task-hint {
      font-size: 12px;
      color: @warning-color;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: 4px;

      .batch-failed {
        color: @error-color;
      }
    }

    .toolbar-center.tool-group {
      display: flex;
      align-items: center;
      gap: 4px;
      flex-shrink: 0;
    }

    .toolbar-right {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-shrink: 0;
      flex-wrap: wrap;
    }

    .save-btn-group {
      display: inline-flex;
      align-items: stretch;
      border-radius: 6px;
      overflow: hidden;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);

      .action-btn-primary {
        border-radius: 0;
        margin: 0;
      }

      .action-btn-save-next {
        border-right: 1px solid rgba(255, 255, 255, 0.25);
        padding-right: 10px;

        .save-next-arrow {
          font-size: 11px;
          opacity: 0.85;
        }
      }

      .action-btn-save-only {
        padding: 6px 10px;
        font-size: 12px;
        min-width: auto;
        opacity: 0.92;
      }
    }

    .top-actions-divider {
      width: 1px;
      height: 22px;
      background: #e8e8e8;
      margin: 0 2px;
      flex-shrink: 0;
    }

    .tool-button {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 6px 10px;
      border-radius: 6px;
      border: 1px solid #d9d9d9;
      background: #fff;
      font-size: 13px;
      color: @gray-color;
      cursor: pointer;
      transition: all 0.2s;

      .tool-shortcut {
        font-size: 11px;
        padding: 0 4px;
        background: #f0f0f0;
        border-radius: 3px;
        color: #8c8c8c;
      }

      &:hover {
        border-color: @primary-color;
        color: @primary-color;
      }

      &.active {
        background: fade(@primary-color, 10%);
        border-color: @primary-color;
        color: @primary-color;

        .tool-shortcut {
          background: fade(@primary-color, 15%);
          color: @primary-color;
        }
      }
    }

    .dropdown-caret {
      font-size: 10px;
      margin-left: 2px;
      opacity: 0.6;
    }

    .action-btn {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 6px 12px;
      border-radius: 6px;
      border: 1px solid #d9d9d9;
      background: #fff;
      font-size: 13px;
      color: @gray-color;
      cursor: pointer;
      transition: all 0.2s;

      &:hover:not(:disabled) {
        border-color: @primary-color;
        color: @primary-color;
      }

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      &.action-btn-primary {
        background: @primary-color;
        border-color: @primary-color;
        color: #fff;
        font-weight: 500;
        position: relative;

        &:hover:not(:disabled) {
          opacity: 0.92;
          border-color: @primary-color;
          color: #fff;
        }

        &.has-unsaved {
          box-shadow: 0 0 0 2px fade(@warning-color, 35%);
        }

        .unsaved-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: @warning-color;
          flex-shrink: 0;
        }
      }

      &.train-ready {
        border-color: #52c41a;
        position: relative;

        .ready-badge {
          position: absolute;
          top: 2px;
          right: 2px;
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #52c41a;
        }
      }

      &.ai-batch-btn {
        background: #fff7e6;
        border-color: #ffc53d;
        color: #d48806;

        &:hover:not(:disabled) {
          background: #ffe58f;
          border-color: #ffc53d;
          color: #d48806;
        }
      }

      &.sam-bootstrap-btn {
        position: relative;
        background: #f0f5ff;
        border-color: #adc6ff;
        color: #266cfb;

        &:hover:not(:disabled) {
          background: #d6e4ff;
          border-color: #85a5ff;
          color: #266cfb;
        }
      }

      .sam-model-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 14px;
        height: 14px;
        margin-left: 4px;
        border-radius: 50%;
        background: #ff4d4f;
        cursor: pointer;
        color: #fff;
        font-size: 10px;
        font-weight: 700;
        line-height: 1;
      }

    }
  }

  .main-content {
    display: flex;
    flex: 1;
    min-height: 0;
    min-width: 0;
  }

  .image-panel {
    width: 280px;
    min-width: 240px;
    background: #1e2433;
    display: flex;
    flex-direction: column;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
    flex-shrink: 0;

    .image-list-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 10px 10px 8px;
      flex-shrink: 0;
    }

    .image-list-header-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      margin-left: auto;
      flex-shrink: 0;
    }

    .batch-selection-toolbar {
      display: flex;
      flex-direction: column;
      width: 100%;
      min-width: 0;
      gap: 8px;
    }

    .batch-selection-summary {
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 24px;
      color: rgba(255, 255, 255, 0.88);
      font-size: 13px;
      font-weight: 500;

      .ant-btn {
        height: 24px;
        padding: 0 4px;
        color: rgba(255, 255, 255, 0.72);
      }
    }

    .batch-action-group {
      display: flex;
      align-items: center;
      width: 100%;
      gap: 8px;

      .ant-btn {
        flex: 1;
        height: 28px !important;
        min-width: 56px;
        padding: 0 12px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        line-height: 1 !important;
        box-shadow: none !important;
      }
    }

    .image-panel-toolbar-btn.ant-btn {
      height: 28px !important;
      min-width: 56px;
      padding: 0 12px !important;
      font-size: 13px !important;
      font-weight: 500 !important;
      line-height: 1 !important;
      box-shadow: none !important;
    }

    .image-panel-toolbar-btn.ant-btn-default {
      background-color: #ffffff !important;
      border-color: #d9d9d9 !important;
      color: #262626 !important;

      .anticon,
      span {
        color: #262626 !important;
      }

      &:not(:disabled):hover {
        background-color: #ffffff !important;
        border-color: @primary-color !important;
        color: @primary-color !important;

        .anticon,
        span {
          color: @primary-color !important;
        }
      }

      &:disabled {
        background-color: rgba(255, 255, 255, 0.55) !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
        color: rgba(38, 38, 38, 0.45) !important;
      }
    }

    .image-panel-toolbar-btn--icon.ant-btn {
      min-width: 28px;
      width: 28px;
      padding: 0 !important;
    }

    .image-panel-toolbar-btn--danger.ant-btn-dangerous.ant-btn-primary {
      background-color: #ff4d4f !important;
      border-color: #ff4d4f !important;
      color: #ffffff !important;

      .anticon,
      span {
        color: #ffffff !important;
      }

      &:not(:disabled):not(.ant-btn-disabled):hover {
        background-color: #ff7875 !important;
        border-color: #ff7875 !important;
        color: #ffffff !important;
      }

      &:disabled,
      &.ant-btn-disabled,
      &.is-disabled {
        background-color: #8c3a3a !important;
        border-color: #a84848 !important;
        color: rgba(255, 255, 255, 0.85) !important;
        opacity: 1 !important;

        .anticon,
        span {
          color: rgba(255, 255, 255, 0.85) !important;
        }
      }
    }

    :deep(.ant-select-selector) {
      background: rgba(255, 255, 255, 0.06) !important;
      border-color: rgba(255, 255, 255, 0.12) !important;
      color: #e8edf5;
    }

    :deep(.ant-select) {
      .ant-select-selection-item {
        color: #e8edf5;
        font-size: 12px;
      }

      .ant-select-arrow {
        color: #8c9ab0;
      }

      &:hover .ant-select-selector,
      &.ant-select-focused .ant-select-selector {
        border-color: @primary-color !important;
      }
    }

    .image-list-stats {
      display: flex;
      align-items: center;
      gap: 4px;
      min-width: 0;
      flex: 1;
      font-size: 12px;
      color: #9aa8bc;

      .stat-done {
        color: #6bcb77;
      }

      .stat-total {
        color: #c5d0e0;
        font-weight: 600;
      }

      .stat-filtered {
        color: #8c9ab0;
      }
    }

    .filter-select {
      width: 96px;
      flex-shrink: 0;
    }

    .image-list-scroll {
      position: relative;
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      margin: 0 8px;

      &::-webkit-scrollbar {
        width: 6px;
      }

      &::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 3px;
      }
    }

    .image-list-phantom {
      width: 100%;
      pointer-events: none;
    }

    .image-list {
      list-style: none;
      margin: 0;
      padding: 0;
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      will-change: transform;
    }

    .image-list-item {
      display: flex;
      align-items: center;
      gap: 6px;
      height: 36px;
      box-sizing: border-box;
      padding: 0 8px;
      margin-bottom: 0;
      border-radius: 6px;
      cursor: pointer;
      border: 1px solid transparent;
      transition: background 0.15s;
      color: #c5d0e0;
      font-size: 13px;

      &:hover {
        background: rgba(255, 255, 255, 0.08);
      }

      &.active {
        background: rgba(67, 97, 238, 0.35);
        border-color: rgba(67, 97, 238, 0.5);
        color: #fff;
      }

      &.selected {
        background: rgba(247, 37, 133, 0.12);
        border-color: rgba(247, 37, 133, 0.35);
      }

      .image-select-checkbox {
        flex-shrink: 0;

        :deep(.ant-checkbox-inner) {
          background: rgba(255, 255, 255, 0.08);
          border-color: rgba(255, 255, 255, 0.25);
        }
      }

      .image-index {
        flex-shrink: 0;
        width: 28px;
        text-align: right;
        color: #8c9ab0;
        font-size: 12px;
        font-variant-numeric: tabular-nums;
      }

      &.active .image-index {
        color: rgba(255, 255, 255, 0.85);
      }

      .image-name {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .image-status-badge {
        flex-shrink: 0;
        font-size: 11px;
        padding: 1px 6px;
        border-radius: 10px;

        &.status-pending {
          color: #9aa8bc;
          background: rgba(255, 255, 255, 0.06);
        }

        &.status-annotated {
          color: #4cc9f0;
          background: rgba(76, 201, 240, 0.15);
        }

        &.status-completed {
          color: #6bcb77;
          background: rgba(107, 203, 119, 0.15);
        }
      }
    }

    .image-list-empty {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 16px;
      text-align: center;
      color: #6b7a90;
      font-size: 13px;

      .empty-icon {
        font-size: 36px;
        opacity: 0.5;
        margin-bottom: 4px;
      }

      .empty-hint {
        margin: 0;
        font-size: 12px;
        color: #5a6a80;
      }

      .empty-import-btn {
        margin-top: 8px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 6px;
        border: 1px solid @primary-color;
        background: fade(@primary-color, 15%);
        color: #a8b8ff;
        cursor: pointer;
        font-size: 13px;

        &:hover {
          background: fade(@primary-color, 28%);
        }
      }
    }

    .image-panel-footer {
      padding: 8px 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;

      .panel-footer-btn {
        width: 100%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 6px 0;
        border: 1px dashed rgba(255, 255, 255, 0.2);
        border-radius: 6px;
        background: transparent;
        color: #9aa8bc;
        font-size: 12px;
        cursor: pointer;

        &:hover {
          border-color: @primary-color;
          color: @primary-color;
          background: fade(@primary-color, 8%);
        }
      }
    }

    .image-list-pagination {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 8px;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      flex-shrink: 0;

      :deep(.ant-pagination) {
        color: #9aa8bc;
      }

      :deep(.ant-pagination-simple-pager input) {
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 255, 255, 0.12);
        color: #e8edf5;
      }

      :deep(.ant-pagination-item-link) {
        color: #c5d0e0;

        &:hover {
          color: @primary-color;
        }
      }
    }
  }

  .canvas-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: @dark-color;
    position: relative;
    min-width: 0;
    overflow: hidden;

    .canvas-nav {
      position: absolute;
      top: 12px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 15;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 8px;
      background: rgba(0, 0, 0, 0.65);
      border-radius: 20px;
      backdrop-filter: blur(6px);

      .nav-index {
        font-size: 13px;
        color: #e8edf5;
        min-width: 64px;
        text-align: center;
      }

      .nav-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border: none;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
        cursor: pointer;

        &:hover:not(:disabled) {
          background: fade(@primary-color, 50%);
        }

        &:disabled {
          opacity: 0.35;
          cursor: not-allowed;
        }

        &.nav-btn-danger:hover {
          background: fade(@error-color, 55%);
        }
      }

      .nav-divider {
        width: 1px;
        height: 18px;
        background: rgba(255, 255, 255, 0.2);
        flex-shrink: 0;
      }
    }

    .image-position-indicator {
      position: absolute;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0, 0, 0, 0.85);
      color: white;
      padding: 8px 16px;
      border-radius: 30px;
      font-size: 16px;
      font-weight: 500;
      z-index: 20;
      display: flex;
      align-items: center;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);

      .position-text {
        display: flex;
        align-items: center;

        .current-index {
          color: #4cc9f0;
          font-weight: bold;
          font-size: 18px;
          margin: 0 4px;
        }

        .total-count {
          color: #a0aec0;
          margin-left: 4px;
        }
      }
    }

    .canvas-wrapper {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: auto;
      padding: 20px;
      max-width: 100%;
      position: relative;

      .canvas-no-tag-hint {
        position: absolute;
        top: 56px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 18;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 14px;
        background: rgba(0, 0, 0, 0.72);
        color: #e8edf5;
        border-radius: 6px;
        font-size: 13px;
        max-width: calc(100% - 40px);
        backdrop-filter: blur(4px);

        .hint-action {
          flex-shrink: 0;
          border: none;
          padding: 4px 10px;
          border-radius: 4px;
          background: @primary-color;
          color: #fff;
          font-size: 12px;
          cursor: pointer;

          &:hover {
            opacity: 0.9;
          }
        }
      }

      .annotation-canvas {
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        background: #2d3748;
        border-radius: 8px;
      }
    }

    .shortcut-hint {
      position: absolute;
      bottom: 90px;
      left: 50%;
      transform: translateX(-50%);
      max-width: calc(100% - 40px);
      background: rgba(0, 0, 0, 0.7);
      color: white;
      padding: 10px 20px;
      border-radius: 30px;
      font-size: 14px;
      display: flex;
      flex-wrap: nowrap;
      align-items: center;
      gap: 14px;
      z-index: 10;
      overflow-x: auto;
      overflow-y: hidden;
      white-space: nowrap;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
      scrollbar-width: none;

      &::-webkit-scrollbar {
        display: none;
      }

      .hint-item {
        display: inline-flex;
        flex-shrink: 0;
        align-items: center;
        gap: 6px;
        white-space: nowrap;

        .key {
          flex-shrink: 0;
          background: rgba(255, 255, 255, 0.2);
          padding: 2px 8px;
          border-radius: 4px;
          font-weight: 500;
          line-height: 1.5;
        }

        .text {
          flex-shrink: 0;
          line-height: 1.5;
        }
      }
    }

    .status-indicator {
      position: absolute;
      top: 20px;
      right: 20px;
      background: rgba(0, 0, 0, 0.85);
      color: white;
      padding: 12px;
      border-radius: 8px;
      font-size: 14px;
      min-width: 280px;
      z-index: 10;

      .status-header {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 10px;

        .completion-status {
          font-weight: bold;
          font-size: 16px;

          &.completed {
            color: #4CAF50;
          }
        }

        .modification-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
          font-size: 13px;
          color: #e0e0e0;
        }
      }

      .annotation-count {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;

        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #4CAF50;
        }

        .unsaved-indicator {
          color: #ff6b6b;
          font-weight: bold;
          margin-left: 8px;
        }
      }
    }

    .fullscreen-control {
      position: absolute;
      bottom: 20px;
      right: 20px;
      background: rgba(0, 0, 0, 0.7);
      color: white;
      padding: 10px 15px;
      border-radius: 30px;
      font-size: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      z-index: 10;
      transition: background 0.3s;

      &:hover {
        background: rgba(0, 0, 0, 0.9);
      }

      i {
        font-size: 16px;
      }
    }
  }

  .label-panel {
    width: 240px;
    background: white;
    padding: 16px 14px;
    box-shadow: -2px 0 10px rgba(0, 0, 0, 0.05);
    display: flex;
    flex-direction: column;
    gap: 12px;
    z-index: 5;
    overflow-y: auto;

    .object-layer-section {
      margin-top: 8px;
      border-top: 1px solid #eee;
      padding-top: 15px;

      .panel-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
        font-size: 14px;
        font-weight: 600;
        color: #666;

        .object-count {
          margin-left: auto;
          font-size: 12px;
          font-weight: 400;
          color: @gray-color;
        }
      }

      .object-list {
        max-height: 250px;
        overflow-y: auto;
        border: 1px solid #eee;
        border-radius: 6px;
        padding: 5px;

        .object-item {
          display: flex;
          align-items: center;
          padding: 8px;
          border-radius: 4px;
          margin-bottom: 5px;
          cursor: pointer;
          transition: background 0.15s;

          &:last-child {
            margin-bottom: 0;
          }

          &:hover {
            background-color: #f5f7fa;
          }

          &.selected {
            background-color: fade(@primary-color, 10%);
            border-left: 3px solid @primary-color;
          }

          .object-color {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            margin-right: 10px;
            flex-shrink: 0;
          }

          .object-name {
            flex: 1;
            font-size: 13px;
            color: #333;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .object-actions {
            .delete-btn {
              background: none;
              border: none;
              color: #f44336;
              cursor: pointer;
              padding: 4px;
              border-radius: 4px;

              &:hover {
                background-color: #ffeeee;
              }
            }
          }
        }
      }
    }
  }
}

// 全屏模式下的样式调整
:fullscreen .annotation-container,
:-webkit-full-screen .annotation-container,
:-moz-full-screen .annotation-container,
:-ms-fullscreen .annotation-container {
  height: 100vh;
  width: 100vw;
  background: @dark-color;

  :deep(.ant-modal-wrap),
  :deep(.ant-modal-mask) {
    position: fixed;
    z-index: 2000;
  }

  .main-content {
    flex: 1;
    min-height: 0;
  }

  .canvas-area {
    flex: 1;
  }

  .label-panel {
    width: 220px;
    min-width: 250px;
    max-width: 350px;
    transition: width 0.3s ease;
  }
}

@media (min-width: 1920px) {
  :fullscreen .label-panel {
    width: 220px;
  }
}

.train-menu-overlay {
  .train-menu-header {
    padding: 8px 12px 6px;
    font-size: 12px;
    color: #8c8c8c;
    line-height: 1.4;
    border-bottom: 1px solid #f0f0f0;
    margin-bottom: 4px;

    strong {
      color: #fa8c16;
    }
  }
}

.image-panel-dropdown.ant-select-dropdown {
  background: #2a3142;
  border: 1px solid rgba(255, 255, 255, 0.12);
  padding: 4px;

  .ant-select-item {
    color: #c5d0e0;
    border-radius: 4px;
  }

  .ant-select-item-option-active,
  .ant-select-item-option-selected {
    background: rgba(67, 97, 238, 0.35);
    color: #fff;
  }
}
</style>
