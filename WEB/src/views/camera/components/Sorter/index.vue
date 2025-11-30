<template>
  <div class="sorter-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <a-button type="primary" @click="handleCreate">
        <template #icon>
          <PlusOutlined />
        </template>
        新建排序器
      </a-button>
      <a-button @click="handleClickSwap" type="default">
        <template #icon>
          <SwapOutlined />
        </template>
        切换视图
      </a-button>
    </div>

    <!-- 表格模式 -->
    <BasicTable v-if="viewMode === 'table'" @register="registerTable">
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'is_enabled'">
          <a-switch :checked="record.is_enabled" @change="handleToggleEnabled(record)" />
        </template>
        <template v-else-if="column.dataIndex === 'sorter_type'">
          <a-tag>{{ getSorterTypeText(record.sorter_type) }}</a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'sort_order'">
          <a-tag :color="record.sort_order === 'asc' ? 'blue' : 'red'">
            {{ record.sort_order === 'asc' ? '升序' : '降序' }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction :actions="getTableActions(record)" />
        </template>
      </template>
    </BasicTable>

    <!-- 卡片模式 -->
    <div v-else class="card-list">
      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in sorterList" :key="item.id">
          <a-card :hoverable="true" class="sorter-card">
            <template #title>
              <div class="card-title">
                <span>{{ item.sorter_name }}</span>
                <a-tag :color="item.is_enabled ? 'green' : 'default'" size="small">
                  {{ item.is_enabled ? '启用' : '停用' }}
                </a-tag>
              </div>
            </template>
            <template #extra>
              <a-dropdown>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="handleView(item)">
                      <EyeOutlined /> 查看
                    </a-menu-item>
                    <a-menu-item @click="handleEdit(item)">
                      <EditOutlined /> 编辑
                    </a-menu-item>
                    <a-menu-item @click="handleToggleEnabled(item)">
                      {{ item.is_enabled ? '停用' : '启用' }}
                    </a-menu-item>
                    <a-menu-item @click="handleDelete(item)" danger>
                      <DeleteOutlined /> 删除
                    </a-menu-item>
                  </a-menu>
                </template>
                <MoreOutlined />
              </a-dropdown>
            </template>
            <div class="card-content">
              <div class="info-item">
                <span class="label">编号:</span>
                <span class="value">{{ item.sorter_code }}</span>
              </div>
              <div class="info-item">
                <span class="label">排序类型:</span>
                <a-tag size="small">{{ getSorterTypeText(item.sorter_type) }}</a-tag>
              </div>
              <div class="info-item">
                <span class="label">排序顺序:</span>
                <a-tag :color="item.sort_order === 'asc' ? 'blue' : 'red'" size="small">
                  {{ item.sort_order === 'asc' ? '升序' : '降序' }}
                </a-tag>
              </div>
              <div class="info-item" v-if="item.description">
                <span class="label">描述:</span>
                <span class="value">{{ item.description }}</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
      <a-empty v-if="sorterList.length === 0" description="暂无排序器" />
    </div>

    <!-- 创建/编辑模态框 -->
    <SorterModal @register="registerModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import {
  PlusOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  MoreOutlined,
  SwapOutlined,
} from '@ant-design/icons-vue';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useDrawer } from '@/components/Drawer';
import { useMessage } from '@/hooks/web/useMessage';
import {
  listSorters,
  deleteSorter,
  type Sorter,
} from '@/api/device/algorithm_task';
import SorterModal from './SorterModal.vue';

defineOptions({ name: 'Sorter' });

const { createMessage } = useMessage();

const viewMode = ref<'table' | 'card'>('card');
const sorterList = ref<Sorter[]>([]);
const [registerModal, { openDrawer }] = useDrawer();

// 获取排序类型文本
const getSorterTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    confidence: '置信度',
    time: '时间',
    score: '分数',
  };
  return typeMap[type] || type;
};

// 表格列配置
const getColumns = () => [
  {
    title: '排序器名称',
    dataIndex: 'sorter_name',
    width: 150,
  },
  {
    title: '排序器编号',
    dataIndex: 'sorter_code',
    width: 150,
  },
  {
    title: '排序类型',
    dataIndex: 'sorter_type',
    width: 100,
  },
  {
    title: '排序顺序',
    dataIndex: 'sort_order',
    width: 100,
  },
  {
    title: '描述',
    dataIndex: 'description',
    width: 200,
  },
  {
    title: '启用状态',
    dataIndex: 'is_enabled',
    width: 100,
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 150,
    fixed: 'right',
  },
];

const [registerTable, { reload }] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '排序器列表',
  api: listSorters,
  columns: getColumns(),
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
  onSuccess: (data) => {
    if (data && data.data) {
      sorterList.value = data.data;
    }
  },
});

const loadSorters = async () => {
  try {
    const response = await listSorters({ pageNo: 1, pageSize: 1000 });
    if (response.code === 0) {
      sorterList.value = response.data || [];
    }
  } catch (error) {
    console.error('加载排序器列表失败', error);
    createMessage.error('加载排序器列表失败');
  }
};

const handleClickSwap = () => {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  if (viewMode.value === 'card') {
    loadSorters();
  }
};

const handleCreate = () => {
  openDrawer(true, { type: 'add' });
};

const handleView = (record: Sorter) => {
  openDrawer(true, { type: 'view', record });
};

const handleEdit = (record: Sorter) => {
  openDrawer(true, { type: 'edit', record });
};

const handleDelete = async (record: Sorter) => {
  try {
    const response = await deleteSorter(record.id);
    if (response.code === 0) {
      createMessage.success('删除成功');
      handleSuccess();
    } else {
      createMessage.error(response.msg || '删除失败');
    }
  } catch (error) {
    console.error('删除排序器失败', error);
    createMessage.error('删除失败');
  }
};

const handleToggleEnabled = async (record: Sorter) => {
  try {
    const { updateSorter } = await import('@/api/device/algorithm_task');
    const response = await updateSorter(record.id, {
      is_enabled: !record.is_enabled,
    });
    if (response.code === 0) {
      createMessage.success('更新成功');
      handleSuccess();
    } else {
      createMessage.error(response.msg || '更新失败');
    }
  } catch (error) {
    console.error('更新排序器状态失败', error);
    createMessage.error('更新失败');
  }
};

const handleSuccess = () => {
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadSorters();
  }
};

const getTableActions = (record: Sorter) => {
  return [
    {
      icon: 'ant-design:eye-filled',
      tooltip: '查看',
      onClick: () => handleView(record),
    },
    {
      icon: 'ant-design:edit-filled',
      tooltip: '编辑',
      onClick: () => handleEdit(record),
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: '删除',
      popConfirm: {
        title: '确定删除此排序器？',
        confirm: () => handleDelete(record),
      },
    },
  ];
};

// 暴露刷新方法
const refresh = () => {
  handleSuccess();
};

defineExpose({
  refresh,
});

onMounted(() => {
  if (viewMode.value === 'card') {
    loadSorters();
  }
});
</script>

<style scoped lang="less">
.sorter-container {
  padding: 24px;

  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .card-list {
    .sorter-card {
      .card-title {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .card-content {
        .info-item {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 14px;

          .label {
            color: rgba(0, 0, 0, 0.45);
          }

          .value {
            color: rgba(0, 0, 0, 0.85);
            font-weight: 500;
          }
        }
      }
    }
  }
}
</style>

