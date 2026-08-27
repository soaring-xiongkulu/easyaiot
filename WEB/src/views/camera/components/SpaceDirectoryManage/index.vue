<template>
  <div class="space-directory-manage" :class="{ 'space-directory-manage--embedded': embedded }">
    <div class="space-panel">
      <div class="panel-toolbar">
        <Input
          v-model:value="searchKeyword"
          allow-clear
          placeholder="搜索空间名称或设备 ID"
          class="panel-search"
        >
          <template #prefix>
            <Icon icon="ant-design:search-outlined" :size="15" color="#a3a3a3" />
          </template>
        </Input>
        <Button :loading="loading" preIcon="ant-design:reload-outlined" @click="handleRefresh">
          刷新
        </Button>
        <span v-if="!loading && total > 0" class="panel-summary">{{ summaryText }}</span>
      </div>

      <div v-if="showBreadcrumbs" class="panel-breadcrumbs">
        <template v-for="(crumb, index) in breadcrumbs" :key="crumb.key">
          <button
            type="button"
            class="breadcrumb-item"
            :class="{ 'breadcrumb-item--current': index === breadcrumbs.length - 1 }"
            :disabled="index === breadcrumbs.length - 1"
            @click="handleBreadcrumbClick(crumb.key)"
          >
            {{ crumb.name }}
          </button>
          <Icon
            v-if="index < breadcrumbs.length - 1"
            icon="ant-design:right-outlined"
            :size="12"
            class="breadcrumb-sep"
          />
        </template>
      </div>

      <SpaceFolderGrid
        :nodes="folderList"
        :space-kind="spaceKind"
        :loading="loading"
        @open="handleOpenSpace"
        @enter="handleEnterFolder"
        @policy="openSpacePolicyModal"
        @group-policy="openGroupPolicyModal"
      />

      <div v-if="total > 0" class="panel-footer">
        <Pagination
          :current="pageNo"
          :total="total"
          :page-size="pageSize"
          :show-size-changer="false"
          show-less-items
          @change="handlePageChange"
        />
      </div>
    </div>

    <DeviceSaveTimeModal
      @register="registerDeviceModal"
      @success="handlePolicySuccess"
    />
    <GroupSaveTimeDrawer
      @register="registerGroupDrawer"
      @success="handlePolicySuccess"
    />
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Input, Pagination } from 'ant-design-vue';
import { Button } from '@/components/Button';
import { Icon } from '@/components/Icon';
import { useDrawer } from '@/components/Drawer';
import { useModal } from '@/components/Modal';
import {
  DEFAULT_SAVE_TIME,
  isSpaceFolderNode,
  isSpaceLeafNode,
  parseSpaceFolderQuery,
  SPACE_FOLDER_ROOT_KEY,
  type SpaceFolderNode,
  type SpaceInfo,
  type SpaceKind,
} from '@/views/camera/utils/spaceSaveTime';
import {
  ROOT_PARENT_KEY,
  SPACE_FOLDER_PAGE_SIZE,
  useSpaceDirectoryManage,
} from './useSpaceDirectoryManage';
import DeviceSaveTimeModal from './DeviceSaveTimeModal.vue';
import GroupSaveTimeDrawer from './GroupSaveTimeDrawer.vue';
import SpaceFolderGrid from './SpaceFolderGrid.vue';

const props = defineProps<{
  spaceKind: SpaceKind;
  title: string;
  detailPathPrefix: string;
  embedded?: boolean;
  /** 嵌入存储空间页时，是否当前可见子 Tab */
  active?: boolean;
}>();

const route = useRoute();
const router = useRouter();

const {
  loading,
  folderList,
  searchKeyword,
  pageNo,
  total,
  parentKey,
  breadcrumbs,
  isSearchMode,
  dataLoaded,
  setPage,
  enterFolder,
  navigateToBreadcrumb,
  refreshAll,
  init,
} = useSpaceDirectoryManage(props.spaceKind);

const [registerDeviceModal, { openModal: openDeviceModal }] = useModal();
const [registerGroupDrawer, { openDrawer: openGroupDrawer }] = useDrawer();

const pageSize = SPACE_FOLDER_PAGE_SIZE;

const showBreadcrumbs = computed(
  () => !isSearchMode.value && breadcrumbs.value.length > 1,
);

const summaryText = computed(() => {
  if (isSearchMode.value) {
    return `搜索到 ${total.value} 个空间`;
  }
  return `${total.value} 项`;
});

function isActivePanel(): boolean {
  if (!props.embedded) return true;
  return props.active !== false;
}

/** 仅在外链/详情页返回等带 tab=4 的场景下，从 URL 恢复钻取目录 */
function shouldApplyRouteFolder(): boolean {
  if (!props.embedded || !isActivePanel()) return false;
  if (route.query.tab !== '4') return false;
  const storage = route.query.storage;
  if (storage === 'record') return props.spaceKind === 'record';
  if (storage === 'snap') return props.spaceKind === 'snap';
  return props.spaceKind === 'snap';
}

function syncFolderFromRoute(force = false) {
  if (!isActivePanel()) return;
  if (!force && !shouldApplyRouteFolder()) return;
  const folder = force && !shouldApplyRouteFolder()
    ? SPACE_FOLDER_ROOT_KEY
    : parseSpaceFolderQuery(route.query.folder);
  if (folder === parentKey.value && dataLoaded.value) return;
  if (folder === SPACE_FOLDER_ROOT_KEY) {
    init();
  } else {
    navigateToBreadcrumb(folder);
  }
}

function handleOpenSpace(node: SpaceFolderNode) {
  if (!isSpaceLeafNode(node)) return;
  const query: Record<string, string> = { view: 'alerts' };
  if (parentKey.value !== ROOT_PARENT_KEY) {
    query.folder = parentKey.value;
  }
  router.push({
    path: `${props.detailPathPrefix}/${node.id}`,
    query,
  });
}

function handleEnterFolder(node: SpaceFolderNode) {
  enterFolder(node);
}

function handleBreadcrumbClick(key: string) {
  navigateToBreadcrumb(key);
}

function openSpacePolicyModal(space: SpaceInfo) {
  const optionalGroupFields = space as unknown as Partial<SpaceFolderNode>;
  openDeviceModal(true, {
    spaceId: space.id,
    deviceId: space.device_id,
    spaceKind: props.spaceKind,
    deviceName: space.space_name,
    saveTimeCustom: space.save_time_custom,
    saveTime: space.save_time,
    saveMode: space.save_mode,
    directorySaveTime: space.directory_save_time ?? DEFAULT_SAVE_TIME,
    groupSaveTime: optionalGroupFields.group_save_time,
    groupType: optionalGroupFields.group_type,
  });
}

function openGroupPolicyModal(node: SpaceFolderNode) {
  if (!isSpaceFolderNode(node) || !node.folder_type) return;
  const groupKey = node.folder_type === 'nvr'
    ? String(node.nvr_id ?? node.node_key.replace(/^nvr_/, ''))
    : String(node.sip_device_id ?? node.node_key.replace(/^gb_sip_/, ''));
  openGroupDrawer(true, {
    spaceKind: props.spaceKind,
    groupType: node.folder_type,
    groupKey,
    groupName: node.name || node.space_name,
    saveTime: node.group_save_time ?? DEFAULT_SAVE_TIME,
    childCount: node.child_count,
    ip: node.ip,
    port: node.port,
    sipDeviceId: node.sip_device_id,
  });
}

async function handlePolicySuccess() {
  await refreshAll();
}

function handleRefresh() {
  refreshAll();
}

function handlePageChange(page: number) {
  setPage(page);
}

defineExpose({
  refresh: refreshAll,
});

watch(
  () => [route.query.tab, route.query.storage, route.query.folder] as const,
  () => {
    syncFolderFromRoute();
  },
);

watch(
  () => props.active,
  (active) => {
    if (active !== false && !dataLoaded.value) {
      syncFolderFromRoute(true);
    }
  },
);

onMounted(() => {
  syncFolderFromRoute(true);
});
</script>

<style lang="less" scoped>
.space-directory-manage {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 192px);
  max-height: calc(100vh - 192px);
  padding-bottom: 4px;
  box-sizing: border-box;
  overflow: hidden;

  &--embedded {
    height: 100%;
    max-height: 100%;

    .space-panel {
      box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
    }
  }
}

.space-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.panel-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 24px 8px;
  flex-shrink: 0;
}

.panel-breadcrumbs {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  padding: 0 24px 10px;
  flex-shrink: 0;
}

.breadcrumb-item {
  padding: 2px 6px;
  border: none;
  border-radius: 4px;
  background: transparent;
  font-size: 13px;
  color: #2563eb;
  cursor: pointer;
  transition: background-color 0.15s ease;

  &:hover:not(:disabled) {
    background: #eff6ff;
  }

  &--current,
  &:disabled {
    color: rgba(0, 0, 0, 0.65);
    cursor: default;
    font-weight: 500;
  }
}

.breadcrumb-sep {
  color: rgba(0, 0, 0, 0.25);
}

.panel-search {
  width: 280px;

  :deep(.ant-input-affix-wrapper) {
    border-radius: 6px;
    border-color: #e5e7eb;
    background: #fafafa;

    &:hover,
    &:focus,
    &.ant-input-affix-wrapper-focused {
      background: #fff;
      border-color: #93c5fd;
    }
  }
}

.panel-summary {
  margin-left: auto;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.45);
}

.panel-footer {
  display: flex;
  justify-content: center;
  padding: 8px 24px 18px;
  flex-shrink: 0;
}
</style>
