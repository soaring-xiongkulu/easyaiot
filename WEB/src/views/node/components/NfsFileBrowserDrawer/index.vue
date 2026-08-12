<template>
  <BasicDrawer
    v-bind="$attrs"
    width="96%"
    placement="right"
    :show-footer="true"
    :show-ok-btn="false"
    cancel-text="关闭"
    destroy-on-close
    root-class-name="nfs-file-browser-drawer"
    @register="registerDrawer"
    @open-change="handleOpenChange"
  >
    <template #title>
      <div class="file-drawer-header">
        <div class="file-drawer-header__main">
          <div class="file-drawer-header__icon">
            <Icon icon="ant-design:folder-open-outlined" :size="22" />
          </div>
          <div>
            <BasicTitle span class="file-drawer-header__title">
              {{ NODE_TERM.storageFileOpsDrawer }}
            </BasicTitle>
            <div class="file-drawer-header__meta">浏览、上传、下载与整理 NFS 媒体目录</div>
          </div>
        </div>
      </div>
    </template>

    <div v-if="open" class="file-drawer-body">
      <NfsFileBrowser :initial-node-id="initialNodeId" layout="manager" />
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicTitle } from '@/components/Basic';
import { Icon } from '@/components/Icon';
import { NODE_TERM } from '../../utils/constants';
import NfsFileBrowser from '../NfsFileBrowser/index.vue';

defineOptions({ name: 'NfsFileBrowserDrawer' });

const open = ref(false);
const initialNodeId = ref<number | undefined>();

const [registerDrawer, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  open.value = true;
  initialNodeId.value = data?.nodeId;
  setDrawerProps({
    showFooter: true,
    showOkBtn: false,
    showCancelBtn: true,
    cancelText: '关闭',
    loading: false,
  });
});

function handleOpenChange(visible: boolean) {
  open.value = visible;
  if (!visible) {
    initialNodeId.value = undefined;
  }
}

defineExpose({ closeDrawer });
</script>

<style lang="less" scoped>
.file-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  padding-right: 32px;
}

.file-drawer-header__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.file-drawer-header__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #eef4ff, #dce8ff);
  color: #1677ff;
  flex-shrink: 0;
}

.file-drawer-header__title {
  font-size: 18px !important;
  font-weight: 600 !important;
}

.file-drawer-header__meta {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.file-drawer-body {
  height: calc(100vh - 148px);
  min-height: 560px;

  :deep(.nfs-file-ops) {
    height: 100%;
  }
}
</style>

<style lang="less">
.nfs-file-browser-drawer {
  .ant-drawer-content-wrapper {
    max-width: 100%;
  }

  .ant-drawer-header {
    padding: 16px 24px;
    border-bottom: 1px solid #f0f0f0;
  }

  .ant-drawer-body {
    background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 80px);
  }

  .scrollbar__wrap {
    padding: 12px 16px !important;
    height: 100%;
  }

  .ant-drawer-footer {
    padding: 12px 24px;
    border-top: 1px solid #f0f0f0;
    background: #fff;
  }
}
</style>
