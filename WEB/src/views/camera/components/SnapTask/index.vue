<template>
  <div class="snap-task-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <a-button type="primary" @click="handleCreate">
        <template #icon>
          <PlusOutlined />
        </template>
        新建算法任务
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
        <template v-if="column.dataIndex === 'status'">
          <a-tag :color="record.status === 0 ? 'green' : 'red'">
            {{ record.status === 0 ? '正常' : '异常' }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'is_enabled'">
          <a-switch :checked="record.is_enabled" @change="handleToggleEnabled(record)" />
        </template>
        <template v-else-if="column.dataIndex === 'capture_type'">
          <a-tag>{{ record.capture_type === 0 ? '抽帧' : '抓拍' }}</a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction :actions="getTableActions(record)" />
        </template>
      </template>
    </BasicTable>

    <!-- 卡片模式 -->
    <div v-else class="card-list">
      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in taskList" :key="item.id">
          <a-card :hoverable="true" class="task-card">
            <template #title>
              <div class="card-title">
                <span>{{ item.task_name }}</span>
                <a-tag :color="item.status === 0 ? 'green' : 'red'" size="small">
                  {{ item.status === 0 ? '正常' : '异常' }}
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
                <span class="label">空间:</span>
                <span class="value">{{ item.space_name }}</span>
              </div>
              <div class="info-item">
                <span class="label">设备:</span>
                <span class="value">{{ item.device_name }}</span>
              </div>
              <div class="info-item">
                <span class="label">类型:</span>
                <a-tag size="small">{{ item.capture_type === 0 ? '抽帧' : '抓拍' }}</a-tag>
              </div>
              <div class="info-item">
                <span class="label">Cron:</span>
                <span class="value">{{ item.cron_expression }}</span>
              </div>
              <div class="info-item">
                <span class="label">状态:</span>
                <a-switch :checked="item.is_enabled" size="small" @change="handleToggleEnabled(item)" />
              </div>
              <div class="info-item">
                <span class="label">抓拍次数:</span>
                <span class="value">{{ item.total_captures || 0 }}</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
      <a-empty v-if="taskList.length === 0" description="暂无算法任务" />
    </div>

    <!-- 创建/编辑模态框 -->
    <SnapTaskModal @register="registerModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { PlusOutlined, SwapOutlined, EyeOutlined, EditOutlined, DeleteOutlined, MoreOutlined } from '@ant-design/icons-vue';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useModal } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import { getSnapTaskList, deleteSnapTask, startSnapTask, stopSnapTask, type SnapTask } from '@/api/device/snap';
import SnapTaskModal from './SnapTaskModal.vue';

defineOptions({ name: 'SnapTask' });

const { createMessage } = useMessage();
const [registerModal, { openModal }] = useModal();

// 视图模式
const viewMode = ref<'table' | 'card'>('card');
const taskList = ref<SnapTask[]>([]);

// 切换视图
const handleClickSwap = () => {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  if (viewMode.value === 'card') {
    loadTaskList();
  }
};

// 表格列定义
const getBasicColumns = () => [
  {
    title: '任务名称',
    dataIndex: 'task_name',
    width: 150,
  },
  {
    title: '空间名称',
    dataIndex: 'space_name',
    width: 120,
  },
  {
    title: '设备名称',
    dataIndex: 'device_name',
    width: 120,
  },
  {
    title: '抓拍类型',
    dataIndex: 'capture_type',
    width: 80,
  },
  {
    title: 'Cron表达式',
    dataIndex: 'cron_expression',
    width: 150,
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 80,
  },
  {
    title: '启用',
    dataIndex: 'is_enabled',
    width: 80,
  },
  {
    title: '抓拍次数',
    dataIndex: 'total_captures',
    width: 100,
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 150,
    fixed: 'right',
  },
];

// 表格配置
const [registerTable, { reload }] = useTable({
  title: '算法任务列表',
  api: async (params) => {
    const response = await getSnapTaskList(params);
    return {
      items: response.data || [],
      total: response.total || 0,
    };
  },
  columns: getBasicColumns(),
  useSearchForm: true,
  formConfig: {
    labelWidth: 80,
    schemas: [
      {
        field: 'search',
        label: '任务名称',
        component: 'Input',
        componentProps: {
          placeholder: '请输入任务名称',
        },
      },
      {
        field: 'space_id',
        label: '空间',
        component: 'Select',
        componentProps: {
          placeholder: '请选择空间',
          options: [], // 需要从API获取
        },
      },
      {
        field: 'status',
        label: '状态',
        component: 'Select',
        componentProps: {
          placeholder: '请选择状态',
          options: [
            { label: '正常', value: 0 },
            { label: '异常', value: 1 },
          ],
        },
      },
    ],
  },
  pagination: true,
  rowKey: 'id',
  fetchSetting: {
    listField: 'items',
    totalField: 'total',
  },
});

// 获取表格操作按钮
const getTableActions = (record: SnapTask) => {
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
      icon: record.is_enabled ? 'ant-design:pause-circle-outlined' : 'ant-design:play-circle-outlined',
      tooltip: record.is_enabled ? '停用' : '启用',
      onClick: () => handleToggleEnabled(record),
    },
    {
      icon: 'material-symbols:delete-outline-rounded',
      tooltip: '删除',
      popConfirm: {
        title: '确定删除此算法任务？',
        confirm: () => handleDelete(record),
      },
    },
  ];
};

// 加载任务列表（卡片模式）
const loadTaskList = async () => {
  try {
    const response = await getSnapTaskList({ pageNo: 1, pageSize: 1000 });
    taskList.value = response.data || [];
  } catch (error) {
    console.error('加载算法任务列表失败', error);
    createMessage.error('加载算法任务列表失败');
  }
};

// 创建
const handleCreate = () => {
  openModal(true, { type: 'create' });
};

// 查看
const handleView = (record: SnapTask) => {
  openModal(true, { type: 'view', record });
};

// 编辑
const handleEdit = (record: SnapTask) => {
  openModal(true, { type: 'edit', record });
};

// 删除
const handleDelete = async (record: SnapTask) => {
  try {
    await deleteSnapTask(record.id);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error) {
    console.error('删除失败', error);
    createMessage.error('删除失败');
  }
};

// 切换启用状态
const handleToggleEnabled = async (record: SnapTask) => {
  try {
    if (record.is_enabled) {
      await stopSnapTask(record.id);
      createMessage.success('任务已停用');
    } else {
      await startSnapTask(record.id);
      createMessage.success('任务已启用');
    }
    handleSuccess();
  } catch (error) {
    console.error('操作失败', error);
    createMessage.error('操作失败');
  }
};

// 刷新
const handleSuccess = () => {
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadTaskList();
  }
};

onMounted(() => {
  if (viewMode.value === 'card') {
    loadTaskList();
  }
});
</script>

<style lang="less" scoped>
.snap-task-container {
  padding: 16px;

  .toolbar {
    margin-bottom: 16px;
    display: flex;
    gap: 8px;
  }

  .card-list {
    .task-card {
      height: 100%;

      .card-title {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .card-content {
        .info-item {
          margin-bottom: 12px;
          display: flex;
          align-items: center;

          .label {
            font-weight: 500;
            margin-right: 8px;
            min-width: 80px;
          }

          .value {
            flex: 1;
            color: #666;
            word-break: break-all;
          }
        }
      }
    }
  }
}
</style>

