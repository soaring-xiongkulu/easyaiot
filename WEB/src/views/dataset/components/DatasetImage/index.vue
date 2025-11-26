<template>
  <div class="subDevice-wrapper">
    <BasicTable @register="registerTable" v-if="state.isTableMode">
      <template #toolbar>
        <a-button type="primary"
                  preIcon="ant-design:picture-outlined"
                  @click="openAddModal(true, { datasetId: route.params['id'], isImage: true, isZip: false, isVideo: false, isStream: false })">
          上传图片
        </a-button>
        <a-button type="default"
                  preIcon="ant-design:file-zip-outlined"
                  @click="openAddModal(true, { datasetId: route.params['id'], isImage: false, isZip: true, isVideo: false, isStream: false })">
          上传图片压缩包
        </a-button>
        <PopConfirmButton
          placement="topRight"
          @confirm="handleSetModel"
          type="default"
          :title="`是否确认设置自动化标注模型服务？`"
          preIcon="ant-design:setting-outlined"
        >
          设置自动化标注模型服务
        </PopConfirmButton>
        <PopConfirmButton
          placement="topRight"
          @confirm="handleAutoLabel"
          type="default"
          :title="`是否确认执行一键自动化标注？`"
          preIcon="ant-design:robot-outlined"
        >
          一键自动化标注
        </PopConfirmButton>
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
          :disabled="!state.isSyncReady"
        >
          一键同步到Minio
        </PopConfirmButton>
        <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
          切换视图
        </a-button>
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
          <a-button type="primary"
                    preIcon="ant-design:picture-outlined"
                    @click="openAddModal(true, { datasetId: route.params['id'], isImage: true, isZip: false, isVideo: false, isStream: false })">
            上传图片
          </a-button>
          <a-button type="default"
                    preIcon="ant-design:file-zip-outlined"
                    @click="openAddModal(true, { datasetId: route.params['id'], isImage: false, isZip: true, isVideo: false, isStream: false })">
            上传图片压缩包
          </a-button>
          <PopConfirmButton
            placement="topRight"
            @confirm="handleSetModel"
            type="default"
            :title="`是否确认设置自动化标注模型服务？`"
            preIcon="ant-design:setting-outlined"
          >
            设置自动化标注模型服务
          </PopConfirmButton>
          <PopConfirmButton
            placement="topRight"
            @confirm="handleAutoLabel"
            type="default"
            :title="`是否确认执行一键自动化标注？`"
            preIcon="ant-design:robot-outlined"
          >
            一键自动化标注
          </PopConfirmButton>
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
            :disabled="!state.isSyncReady"
          >
            一键同步到Minio
          </PopConfirmButton>
          <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
            切换视图
          </a-button>
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
import {Tag} from "ant-design-vue";
import {useRoute} from "vue-router";
import {useModal} from "@/components/Modal";
import {
  autoLabel,
  checkSyncCondition,
  deleteDatasetImage,
  deleteDatasetImages,
  getDatasetImagePage,
  resetDataset,
  setAutoLabelModel,
  splitDataset,
  syncToMinio,
} from "@/api/device/dataset";
import DatasetImageModal from "@/views/dataset/components/DatasetImageModal/index.vue";
import {PopConfirmButton} from "@/components/Button";
import {onMounted, reactive, ref} from "vue";
import DatasetImageCardList from "@/views/dataset/components/DatasetImageCardList/index.vue";
import {createImgPreview} from "@/components/Preview";

const {createMessage} = useMessage();

const [registerAddModel, {openModal: openAddModal}] = useModal();

defineOptions({name: 'DatasetImage'})

const route = useRoute()
const checkedKeys = ref<Array<string | number>>([]);

onMounted(async () => {
  try {
    const ret = await checkSyncCondition(route.params.id);
    state.isSyncReady = ret['data'];
  } catch (error) {
    console.error('检查同步条件失败:', error);
    state.isSyncReady = false;
  }
});

const state = reactive({
  isTableMode: false,
  activeKey: '1',
  pushActiveKey: '1',
  historyActiveKey: '1',
  loadVideoUrl: '',
  frameVideoUrl: '',
  isSyncReady: false,
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

async function handleSyncToMinio() {
  try {
    // 1. 检查同步条件
    const ret = await checkSyncCondition(route.params.id);
    const checkResult = ret['data'];
    if (!checkResult) {
      createMessage.error('数据集未完成标注或未划分用途，无法同步');
      return;
    }

    // 2. 执行同步
    await syncToMinio(route.params.id);
    createMessage.success('数据集同步任务已启动');

    // 3. 刷新界面
    handleSuccess(); // 刷新列表
  } catch (error) {
    console.error('同步数据集失败:', error);
    createMessage.error('同步数据集失败');
  }
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

async function handleSetModel() {
  try {
    await setAutoLabelModel(route.params.id, {
      modelServiceId: 'model-123'
    });
    createMessage.success('设置自动化标注模型成功');
    handleSuccess(); // 刷新列表
  } catch (error) {
    console.error('设置自动化标注模型失败:', error);
    createMessage.error('设置自动化标注模型失败');
  }
}

// 一键自动化标注
async function handleAutoLabel() {
  try {
    await autoLabel(route.params.id);
    createMessage.success('自动化标注任务已启动');
    handleSuccess(); // 刷新列表
  } catch (error) {
    console.error('执行自动化标注失败:', error);
    createMessage.error('执行自动化标注失败');
  }
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

  // 刷新同步状态
  checkSyncCondition(route.params.id).then(ret => {
    state.isSyncReady = ret['data'];
  });
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
.device-wrapper {
  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }
}
</style>
