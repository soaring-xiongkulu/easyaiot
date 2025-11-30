<template>
  <div class="frame-extractor-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <a-button type="primary" @click="handleCreate">
        <template #icon>
          <PlusOutlined />
        </template>
        新建抽帧器
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
        <template v-else-if="column.dataIndex === 'extractor_type'">
          <a-tag>{{ record.extractor_type === 'interval' ? '按间隔' : '按时间' }}</a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction :actions="getTableActions(record)" />
        </template>
      </template>
    </BasicTable>

    <!-- 卡片模式 -->
    <div v-else class="card-list">
      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in extractorList" :key="item.id">
          <a-card :hoverable="true" class="extractor-card">
            <template #title>
              <div class="card-title">
                <span>{{ item.extractor_name }}</span>
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
                <span class="value">{{ item.extractor_code }}</span>
              </div>
              <div class="info-item">
                <span class="label">类型:</span>
                <a-tag size="small">{{ item.extractor_type === 'interval' ? '按间隔' : '按时间' }}</a-tag>
              </div>
              <div class="info-item">
                <span class="label">间隔:</span>
                <span class="value">{{ item.interval }}</span>
              </div>
              <div class="info-item" v-if="item.description">
                <span class="label">描述:</span>
                <span class="value">{{ item.description }}</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
      <a-empty v-if="extractorList.length === 0" description="暂无抽帧器" />
    </div>

    <!-- 创建/编辑模态框 -->
    <FrameExtractorModal @register="registerModal" @success="handleSuccess" />
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
  listFrameExtractors,
  deleteFrameExtractor,
  type FrameExtractor,
} from '@/api/device/algorithm_task';
import FrameExtractorModal from './FrameExtractorModal.vue';

defineOptions({ name: 'FrameExtractor' });

const { createMessage } = useMessage();

const viewMode = ref<'table' | 'card'>('card');
const extractorList = ref<FrameExtractor[]>([]);
const [registerModal, { openDrawer }] = useDrawer();

// 表格列配置
const getColumns = () => [
  {
    title: '抽帧器名称',
    dataIndex: 'extractor_name',
    width: 150,
  },
  {
    title: '抽帧器编号',
    dataIndex: 'extractor_code',
    width: 150,
  },
  {
    title: '抽帧类型',
    dataIndex: 'extractor_type',
    width: 100,
  },
  {
    title: '间隔',
    dataIndex: 'interval',
    width: 80,
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
  title: '抽帧器列表',
  api: listFrameExtractors,
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
      extractorList.value = data.data;
    }
  },
});

const loadExtractors = async () => {
  try {
    const response = await listFrameExtractors({ pageNo: 1, pageSize: 1000 });
    if (response.code === 0) {
      extractorList.value = response.data || [];
    }
  } catch (error) {
    console.error('加载抽帧器列表失败', error);
    createMessage.error('加载抽帧器列表失败');
  }
};

const handleClickSwap = () => {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  if (viewMode.value === 'card') {
    loadExtractors();
  }
};

const handleCreate = () => {
  openDrawer(true, { type: 'add' });
};

const handleView = (record: FrameExtractor) => {
  openDrawer(true, { type: 'view', record });
};

const handleEdit = (record: FrameExtractor) => {
  openDrawer(true, { type: 'edit', record });
};

const handleDelete = async (record: FrameExtractor) => {
  try {
    const response = await deleteFrameExtractor(record.id);
    if (response.code === 0) {
      createMessage.success('删除成功');
      handleSuccess();
    } else {
      createMessage.error(response.msg || '删除失败');
    }
  } catch (error) {
    console.error('删除抽帧器失败', error);
    createMessage.error('删除失败');
  }
};

const handleToggleEnabled = async (record: FrameExtractor) => {
  try {
    const { updateFrameExtractor } = await import('@/api/device/algorithm_task');
    const response = await updateFrameExtractor(record.id, {
      is_enabled: !record.is_enabled,
    });
    if (response.code === 0) {
      createMessage.success('更新成功');
      handleSuccess();
    } else {
      createMessage.error(response.msg || '更新失败');
    }
  } catch (error) {
    console.error('更新抽帧器状态失败', error);
    createMessage.error('更新失败');
  }
};

const handleSuccess = () => {
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadExtractors();
  }
};

const getTableActions = (record: FrameExtractor) => {
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
        title: '确定删除此抽帧器？',
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
    loadExtractors();
  }
});
</script>

<style scoped lang="less">
.frame-extractor-container {
  padding: 24px;

  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .card-list {
    .extractor-card {
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

