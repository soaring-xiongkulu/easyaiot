<template>
  <div>
    <!-- 数据仓基础信息卡片 -->
    <a-card :bordered="false" style="margin-top: 0">
      <h2 class="section-title">数据仓详情</h2>
      <a-divider style="margin: 12px 0 20px" />
      <Description
        layout="vertical"
        :column="2"
        :data="warehouseInfo"
        :schema="warehouseSchema"
      />
    </a-card>

    <!-- 关联数据集卡片 -->
    <a-card :bordered="false" style="margin-top: 20px">
      <div class="card-header">
        <h2 class="section-title">关联数据集</h2>
        <a-button type="primary" @click="refreshDatasets">刷新</a-button>
      </div>
      <a-divider style="margin: 12px 0 20px" />
      <a-table
        :columns="datasetColumns"
        :data-source="datasetList"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'syncStatus'">
            <a-tag :color="getSyncStatusColor(record.syncStatus)">
              {{ getSyncStatusText(record.syncStatus) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'progress'">
            <a-progress
              :percent="calculateSyncProgress(record)"
              :stroke-color="progressColor"
              size="small"
            />
          </template>
          <template v-if="column.key === 'action'">
            <a-button type="link" @click="viewDataset(record.datasetId)">查看</a-button>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { Description } from '@/components/Description/index';
import { useMessage } from '@/hooks/web/useMessage';
import { useRoute, useRouter } from "vue-router";
import {
  getWarehouse,
  getWarehouseDatasetPage
} from "@/api/device/dataset";
import { Card as ACard, Divider as ADivider, Progress as AProgress } from 'ant-design-vue';

const route = useRoute();
const router = useRouter();
const { createMessage } = useMessage();

// 数据仓基本信息
const warehouseInfo = reactive({
  id: '',
  name: '',
  coverPath: '',
  description: '',
  datasetCount: 0,
  lastSyncTime: ''
});

// 数据仓schema
const warehouseSchema = [
  {
    field: 'id',
    label: '数据仓ID',
  },
  {
    field: 'name',
    label: '数据仓名称',
  },
  {
    field: 'description',
    label: '描述',
  },
  {
    field: 'datasetCount',
    label: '关联数据集数量',
    render: val => val || 0
  },
  {
    field: 'coverPath',
    label: '封面地址',
    render: (value) => value ? value : '无'
  },
  {
    field: 'lastSyncTime',
    label: '最后同步时间',
    render: (value) => value ? value : '--'
  }
];

// 数据集列表相关数据
const datasetList = ref([]);
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  pageSizeOptions: ['10', '20', '50']
});

// 数据集表格列定义
const datasetColumns = [
  { title: '数据集ID', dataIndex: 'datasetId', key: 'datasetId' },
  { title: '数据集名称', dataIndex: 'datasetName', key: 'datasetName' },
  {
    title: '同步状态',
    key: 'syncStatus',
    align: 'center'
  },
  {
    title: '同步进度',
    key: 'progress',
    width: '200px',
    align: 'center'
  },
  {
    title: '计划/已同步',
    key: 'syncCount',
    align: 'center',
    customRender: ({ record }) => `${record.syncCount}/${record.planSyncCount}`
  },
  {
    title: '失败次数',
    dataIndex: 'failCount',
    key: 'failCount',
    align: 'center'
  },
  {
    title: '操作',
    key: 'action',
    align: 'center'
  }
];

// 计算同步进度百分比
const calculateSyncProgress = (record) => {
  if (!record.planSyncCount || record.planSyncCount === 0) return 0;
  const progress = (record.syncCount / record.planSyncCount) * 100;
  return Math.min(100, Math.round(progress));
};

// 同步状态文本映射
const getSyncStatusText = (status) => {
  const map = { 0: '未同步', 1: '同步中', 2: '同步完成' };
  return map[status] || '未知状态';
};

// 同步状态颜色映射
const getSyncStatusColor = (status) => {
  const map = { 0: 'orange', 1: 'blue', 2: 'green' };
  return map[status] || 'gray';
};

// 进度条颜色
const progressColor = computed(() => {
  return { '0%': '#108ee9', '100%': '#87d068' };
});

// 查看数据集详情
const viewDataset = (datasetId) => {
  router.push({ name: 'DatasetDetail', params: { id: datasetId } });
};

// 刷新数据集列表
const refreshDatasets = () => {
  pagination.current = 1;
  loadDatasetList();
};

// 处理分页变化
const handleTableChange = (pag) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  loadDatasetList();
};

// 加载数据集列表
const loadDatasetList = async () => {
  try {
    const params = {
      warehouseId: warehouseInfo.id,
      pageNo: pagination.current,
      pageSize: pagination.pageSize
    };

    const res = await getWarehouseDatasetPage(params);
    datasetList.value = res.records.map(item => ({
      ...item,
      datasetName: item.name || `数据集-${item.datasetId.slice(0, 6)}`
    }));

    pagination.total = res.total;
  } catch (error) {
    createMessage.error('获取数据集列表失败');
    console.error('Error fetching dataset list:', error);
  }
};

// 初始化数据仓详情
async function initWarehouseDetail(id) {
  try {
    const info = await getWarehouse({ id });
    Object.assign(warehouseInfo, {
      id: info.id,
      name: info.name,
      coverPath: info.coverPath,
      description: info.description,
      datasetCount: info.datasetCount || 0,
      lastSyncTime: info.lastSyncTime || ''
    });

    // 加载关联数据集
    loadDatasetList();
  } catch (error) {
    createMessage.error('获取数据仓详情失败');
    console.error('Error fetching warehouse details:', error);
  }
}

onMounted(() => {
  initWarehouseDetail(route.params.id);
});
</script>

<style lang="less" scoped>
.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f1f1f;
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 原有样式保持不变 */
:deep(.copy-warpper) {
  display: flex;
  align-items: center;

  .copy {
    margin-left: 10px;
    opacity: 0;
  }
}

:deep(.copy-warpper):hover .copy {
  opacity: 1;
}
</style>
