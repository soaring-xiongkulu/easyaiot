<template>
  <div>
    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="datasetList"
        row-key="id"
        :pagination="pagination"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'syncStatus'">
            <a-tag :color="getSyncStatusColor(record.syncStatus)">
              {{ getSyncStatusText(record.syncStatus) }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, reactive, ref} from 'vue';
import {getWarehouseDatasetPage} from '@/api/device/dataset';

defineOptions({name: 'WarehouseDatasetList'});

const props = defineProps({
  warehouseId: String // 从父组件传入的数据仓ID
});

// 数据集列表数据
const datasetList = ref([]);
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
});

// 表格列定义
const columns = [
  {title: '数据集ID', dataIndex: 'datasetId', key: 'datasetId'},
  {title: '数据集名称', dataIndex: 'datasetName', key: 'datasetName'},
  {title: '计划同步数量', dataIndex: 'planSyncCount', key: 'planSyncCount'},
  {title: '已同步数量', dataIndex: 'syncCount', key: 'syncCount'},
  {title: '同步状态', key: 'syncStatus'},
  {title: '失败次数', dataIndex: 'failCount', key: 'failCount'}
];

// 同步状态映射
const getSyncStatusText = (status) => {
  const map = {0: '未同步', 1: '同步中', 2: '同步完成'};
  return map[status] || '未知状态';
};

const getSyncStatusColor = (status) => {
  const map = {0: 'orange', 1: 'blue', 2: 'green'};
  return map[status] || 'gray';
};

// 加载数据集列表
const loadDatasetList = async () => {
  const params = {
    warehouseId: props.warehouseId,
    pageNo: pagination.current,
    pageSize: pagination.pageSize
  };
  const res = await getWarehouseDatasetPage(params);
  datasetList.value = res.records;
  pagination.total = res.total;
};

// 处理分页变化
const handleTableChange = (pag) => {
  pagination.current = pag.current;
  loadDatasetList();
};

onMounted(() => {
  if (props.warehouseId) loadDatasetList();
});
</script>
