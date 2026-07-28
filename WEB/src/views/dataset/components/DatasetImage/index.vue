<template>
  <div class="subDevice-wrapper">
    <MinioSyncStatus
      class="dataset-sync-status"
      :status="syncCheck"
      :connection-error="syncConnectionError"
      @refresh="handleRefreshSyncStatus"
      @retry="handleRetryMinioSync"
      @start-train="handleStartTrain"
    />
    <Alert
      v-if="syncCheck.totalImages > 0 && !syncCheck.usageAllocated"
      type="warning"
      show-icon
      banner
      class="dataset-workflow-alert"
      message="请先划分数据集用途"
      description="标注完成后，需先点击「按比例划分数据集用途」，将图片划分为训练集/验证集/测试集，再执行「一键同步到 Minio」用于模型训练。"
    />
    <Alert
      v-else-if="syncCheck.totalImages > 0 && syncCheck.usageAllocated && !syncCheck.annotationCompleted"
      type="warning"
      show-icon
      banner
      class="dataset-workflow-alert"
      message="尚有图片未完成标注"
      :description="`还有 ${syncCheck.unannotatedCount} 张图片待标注，完成标注并划分用途后方可同步到 Minio。`"
    />
    <Alert
      v-else-if="syncCheck.syncReady && !syncCheck.syncedToMinio"
      type="info"
      show-icon
      banner
      class="dataset-workflow-alert"
      message="可以同步到 Minio"
      description="用途已划分且标注已完成，请点击「一键同步到 Minio」生成训练用数据集包。"
    />
    <BasicTable @register="registerTable" v-if="state.isTableMode">
      <template #toolbar>
        <Button type="primary"
                  preIcon="ant-design:picture-outlined"
                  @click="openAddModal(true, { datasetId: route.params['id'], isImage: true, isZip: false, isVideo: false, isStream: false })">
          上传图片
        </Button>
        <Button type="default"
                  preIcon="ant-design:file-zip-outlined"
                  @click="openAddModal(true, { datasetId: route.params['id'], isImage: false, isZip: true, isVideo: false, isStream: false })">
          上传图片压缩包
        </Button>
        <PopConfirmButton
          placement="topRight"
          @confirm="handleSplitDataset"
          type="default"
          :title="`是否确认按比例划分数据集用途？`"
          preIcon="ant-design:pie-chart-outlined"
        >
          按比例划分数据集用途
        </PopConfirmButton>
        <PopConfirmButton
          placement="topRight"
          @confirm="handleResetDataset"
          type="default"
          :title="`是否确认重置数据集用途？`"
          preIcon="ant-design:reload-outlined"
        >
          一键重置数据集用途
        </PopConfirmButton>
        <PopConfirmButton
          placement="topRight"
          @confirm="handleSyncToMinio"
          type="default"
          :title="`是否确认同步数据集到Minio？`"
          preIcon="ant-design:cloud-upload-outlined"
          :disabled="!syncCheck.syncReady || syncCheck.syncing || syncCheck.syncedToMinio"
        >
          {{ syncActionLabel }}
        </PopConfirmButton>
        <Button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
          切换视图
        </Button>
        <PopConfirmButton
          placement="topRight"
          @confirm="handleDeleteAll"
          type="primary"
          color="error"
          :disabled="!checkedKeys.length"
          :title="`是否确认删除？`"
          preIcon="ant-design:delete-outlined"
        >
          批量删除
        </PopConfirmButton>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
             {
                icon: 'ant-design:eye-filled',
                tooltip: {
                  title: '详情',
                  placement: 'top',
                },
                onClick: handleView.bind(record)
              },
              {
                tooltip: {
                  title: '编辑',
                  placement: 'top',
                },
                icon: 'ant-design:edit-filled',
                onClick: openAddModal.bind(null, true, { datasetId: route.params['id'], isEdit: true, isView: false, record }),
              },
              {
                tooltip: {
                  title: '删除',
                  placement: 'top',
                },
                icon: 'material-symbols:delete-outline-rounded',
                popConfirm: {
                  placement: 'topRight',
                  title: '是否确认删除？',
                  confirm: handleDelete.bind(null, record),
                },
              },
            ]"
          />
        </template>
        <!-- 新增标注状态列渲染 -->
        <template v-else-if="column.dataIndex === 'completed'">
          <Tag :color="record.completed == 1 ? '#52c41a' : '#f5222d'">
            {{ record.completed == 1 ? '已标注' : '待标注' }}
          </Tag>
        </template>
        <!-- 新增数据集类型列渲染 -->
        <template v-else-if="column.dataIndex === 'usageType'">
          <Tag v-if="record.isTrain == 1" color="#096dd9">训练集</Tag>
          <Tag v-else-if="record.isValidation == 1" color="#fa8c16">验证集</Tag>
          <Tag v-else-if="record.isTest == 1" color="#722ed1">测试集</Tag>
        </template>
      </template>
    </BasicTable>
    <div v-else>
      <DatasetImageCardList :params="params" :api="getDatasetImagePage" @get-method="getMethod"
                            @delete="handleDel"
                            @view="handleView" @edit="handleEdit">
        <template #header>
          <Button type="primary"
                    preIcon="ant-design:picture-outlined"
                    @click="openAddModal(true, { datasetId: route.params['id'], isImage: true, isZip: false, isVideo: false, isStream: false })">
            上传图片
          </Button>
          <Button type="default"
                    preIcon="ant-design:file-zip-outlined"
                    @click="openAddModal(true, { datasetId: route.params['id'], isImage: false, isZip: true, isVideo: false, isStream: false })">
            上传图片压缩包
          </Button>
          <PopConfirmButton
            placement="topRight"
            @confirm="handleSplitDataset"
            type="default"
            :title="`是否确认按比例划分数据集用途？`"
            preIcon="ant-design:pie-chart-outlined"
          >
            按比例划分数据集用途
          </PopConfirmButton>
          <PopConfirmButton
            placement="topRight"
            @confirm="handleResetDataset"
            type="default"
            :title="`是否确认重置数据集用途？`"
            preIcon="ant-design:reload-outlined"
          >
            一键重置数据集用途
          </PopConfirmButton>
          <PopConfirmButton
            placement="topRight"
            @confirm="handleSyncToMinio"
            type="default"
            :title="`是否确认同步数据集到Minio？`"
            preIcon="ant-design:cloud-upload-outlined"
            :disabled="!syncCheck.syncReady || syncCheck.syncing || syncCheck.syncedToMinio"
          >
            {{ syncActionLabel }}
          </PopConfirmButton>
          <Button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
            切换视图
          </Button>
        </template>
      </DatasetImageCardList>
    </div>
    <DatasetImageModal @register="registerAddModel" @success="handleSuccess"/>
  </div>
</template>

<script setup lang="ts" name="devicesPage">
import {getBasicColumns, getFormConfig} from './data';
import {useMessage} from '@/hooks/web/useMessage';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {Alert, Tag} from "ant-design-vue";
import {useRoute, useRouter} from "vue-router";
import {useModal} from "@/components/Modal";
import {
  checkSyncCondition,
  type DatasetSyncCheckResult,
  deleteDatasetImage,
  deleteDatasetImages,
  getDatasetImagePage,
  parseDatasetSyncCheckResult,
  resetDataset,
  splitDataset,
  syncToMinio,
  waitForDatasetMinioSync,
} from "@/api/device/dataset";
import DatasetImageModal from "@/views/dataset/components/DatasetImageModal/index.vue";
import {PopConfirmButton} from "@/components/Button";
import DatasetImageCardList from "@/views/dataset/components/DatasetImageCardList/index.vue";
import MinioSyncStatus from "@/views/dataset/components/MinioSyncStatus/index.vue";
import {createImgPreview} from "@/components/Preview";
import {computed, onMounted, onUnmounted, reactive, ref} from "vue";

const {createMessage, createConfirm} = useMessage();

const [registerAddModel, {openModal: openAddModal}] = useModal();

defineOptions({name: 'DatasetImage'})

const route = useRoute()
const router = useRouter();
const checkedKeys = ref<Array<string | number>>([]);

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

const syncActionLabel = computed(() => {
  if (syncCheck.syncStatus === 'QUEUED') return '排队中';
  if (syncCheck.syncStatus === 'RUNNING') return `同步中 ${syncCheck.syncProgress}%`;
  if (syncCheck.syncStatus === 'FAILED') return '重试同步';
  if (syncCheck.syncedToMinio) return '已同步';
  return '一键同步到Minio';
});

async function refreshSyncCheck() {
  try {
    const ret = await checkSyncCondition(route.params.id);
    const status = parseDatasetSyncCheckResult(ret);
    Object.assign(syncCheck, status);
    syncConnectionError.value = null;
    return status;
  } catch (error) {
    console.error('检查同步条件失败:', error);
    syncConnectionError.value = error instanceof Error ? error.message : '状态查询失败';
    return null;
  }
}

onMounted(async () => {
  const status = await refreshSyncCheck();
  if (status?.syncing) {
    monitorMinioSync(false);
  }
});

onUnmounted(() => syncPollController?.abort());

const state = reactive({
  isTableMode: false,
  activeKey: '1',
  pushActiveKey: '1',
  historyActiveKey: '1',
  loadVideoUrl: '',
  frameVideoUrl: '',
});

const [registerTable, {reload}] = useTable({
  title: '图片数据集列表',
  api: getDatasetImagePage,
  columns: getBasicColumns(),
  useSearchForm: true,
  formConfig: getFormConfig(),
  showTableSetting: false,
  tableSetting: {fullScreen: true},
  showIndexColumn: false,
  rowKey: 'id',
  fetchSetting: {
    listField: 'list',
    totalField: 'total',
  },
  // 添加beforeFetch钩子转换参数
  beforeFetch: (params) => {
    const {usageType, ...rest} = params;

    rest['datasetId'] = route.params['id'];
    // 将usageType转换为后端需要的字段
    if (usageType !== undefined) {
      return {
        ...rest,
        isTrain: usageType === 1 ? 1 : undefined,
        isValidation: usageType === 2 ? 1 : undefined,
        isTest: usageType === 3 ? 1 : undefined
      };
    }

    return rest;
  },
  rowSelection: {
    type: 'checkbox',
    selectedRowKeys: checkedKeys,
    onSelect: onSelect,
    onSelectAll: onSelectAll,
    getCheckboxProps(record) {
      // Demo: 第一行（id为0）的选择框禁用
      if (record.root) {
        return {disabled: true};
      } else {
        return {disabled: false};
      }
    },
  },
});

// 切换视图
function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

// 请求api时附带参数
const params = {};

let cardListReload = () => {
};

// 获取内部fetch方法;
function getMethod(m: any) {
  cardListReload = m;
}

//删除按钮事件
function handleDel(record) {
  handleDelete(record);
  cardListReload();
}

//详情按钮事件
function handleView(record) {
  createImgPreview({imageList: [record['path']], maskClosable: true})
}

//编辑按钮事件
function handleEdit(record) {
  openAddModal(true, {datasetId: route.params['id']});
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
      createMessage.success('数据集已同步到 Minio，可用于模型训练');
    }
    handleSuccess();
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

async function handleSyncToMinio() {
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
      createMessage.error('请先点击「按比例划分数据集用途」，将图片划分为训练集/验证集/测试集后再同步');
      return;
    }
    if (!syncCheck.annotationCompleted) {
      createMessage.error(`尚有 ${syncCheck.unannotatedCount} 张图片未完成标注，无法同步到 Minio`);
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
    console.error('同步数据集失败:', error);
    createMessage.error(error?.message || '同步数据集失败');
  }
}

async function handleRefreshSyncStatus() {
  const status = await refreshSyncCheck();
  if (status?.syncing) {
    monitorMinioSync(false);
  }
}

function handleRetryMinioSync() {
  createConfirm({
    iconType: 'warning',
    title: '重新同步数据集到 MinIO？',
    content: '将重新生成训练数据包并上传。',
    onOk: handleSyncToMinio,
  });
}

function handleStartTrain() {
  void router.push({
    path: '/train',
    query: {tab: '6', launch: '1', datasetId: String(route.params.id)},
  });
}

function onSelect(record, selected) {
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, record.id];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => id !== record.id);
  }
  console.log(checkedKeys);
}

function onSelectAll(selected, _, changeRows) {
  const changeIds = changeRows.map((item) => item.id);
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, ...changeIds];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => {
      return !changeIds.includes(id);
    });
  }
  console.log(checkedKeys);
}

// 按比例划分数据集用途
async function handleSplitDataset() {
  try {
    await splitDataset(route.params.id, {
      trainRatio: 0.7,
      valRatio: 0.2,
      testRatio: 0.1
    });
    createMessage.success('数据集划分成功');
    handleSuccess(); // 刷新列表
  } catch (error) {
    console.error('数据集划分失败:', error);
    createMessage.error('数据集划分失败');
  }
}

// 一键重置数据集用途
async function handleResetDataset() {
  try {
    await resetDataset(route.params.id);
    createMessage.success('数据集用途已重置');
    handleSuccess(); // 刷新列表
  } catch (error) {
    console.error('重置数据集用途失败:', error);
    createMessage.error('重置数据集用途失败');
  }
}

// 表格刷新
function handleSuccess() {
  reload({
    page: 0,
  });
  cardListReload();

  refreshSyncCheck();
}

const handleDelete = async (record) => {
  try {
    await deleteDatasetImage(record['id']);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error) {
    console.error(error)
    createMessage.success('删除失败');
    console.log('handleDelete', error);
  }
};

async function handleDeleteAll() {
  if (!checkedKeys.value.length) {
    createMessage.warning('请选择要删除的项');
    return;
  }

  try {
    await deleteDatasetImages(checkedKeys.value);
    createMessage.success(`已成功删除${checkedKeys.value.length}项`);

    // 清空选中项并刷新数据
    checkedKeys.value = [];
    handleSuccess();
  } catch (error) {
    console.error('批量删除失败:', error);
    createMessage.error('批量删除失败');
  }
}
</script>

<style lang="less" scoped>
.dataset-workflow-alert {
  margin-bottom: 12px;
}

.dataset-sync-status {
  margin-bottom: 12px;
}

.device-wrapper {
  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }
}
</style>
