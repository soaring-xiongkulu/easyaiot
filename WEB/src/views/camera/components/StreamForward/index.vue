<template>
  <div id="stream-forward">
    <!-- 表格模式 -->
    <BasicTable v-if="viewMode === 'table'" @register="registerTable">
      <template #toolbar>
        <div class="toolbar-buttons">
          <a-button type="primary" @click="handleCreate">
            <template #icon>
              <PlusOutlined />
            </template>
            新建推流转发任务
          </a-button>
          <a-button @click="handleToggleViewMode" type="default">
            <template #icon>
              <SwapOutlined />
            </template>
            切换视图
          </a-button>
        </div>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction :actions="getTableActions(record)" />
        </template>
      </template>
    </BasicTable>

    <!-- 卡片模式 -->
    <div v-else class="stream-forward-card-list-wrapper p-2">
      <div class="p-4 bg-white" style="margin-bottom: 10px">
        <BasicForm @register="registerForm" @reset="handleSubmit"/>
      </div>
      <div class="p-2 bg-white">
        <Spin :spinning="loading">
          <List
            :grid="{ gutter: 12, xs: 1, sm: 2, md: 3, lg: 4, xl: 4, xxl: 4 }"
            :data-source="taskList"
            :pagination="paginationProp"
          >
            <template #header>
              <div style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;">
                <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">推流转发任务列表</span>
                <div style="display: flex; gap: 8px;">
                  <a-button type="primary" @click="handleCreate">
                    <template #icon>
                      <PlusOutlined />
                    </template>
                    新建推流转发任务
                  </a-button>
                  <a-button @click="handleToggleViewMode" type="default">
                    <template #icon>
                      <SwapOutlined />
                    </template>
                    切换视图
                  </a-button>
                </div>
              </div>
            </template>
            <template #renderItem="{ item }">
              <ListItem :class="item.is_enabled ? 'task-item normal' : 'task-item error'">
                <div class="task-info">
                  <div class="status">{{ item.is_enabled ? '运行中' : '已停止' }}</div>
                  <div class="title o2">{{ item.task_name || item.id }}</div>
                  <div class="props">
                    <div class="flex" style="justify-content: space-between;">
                      <div class="prop">
                        <div class="label">关联摄像头</div>
                        <div class="value">{{ item.device_names && item.device_names.length > 0 ? item.device_names.join(', ') : '无' }}</div>
                      </div>
                      <div class="prop">
                        <div class="label">活跃流数</div>
                        <div class="value">{{ item.active_streams || 0 }}/{{ item.total_streams || 0 }}</div>
                      </div>
                    </div>
                    <div class="flex" style="justify-content: space-between;">
                      <div class="prop">
                        <div class="label">输出格式</div>
                        <div class="value">{{ item.output_format?.toUpperCase() || 'RTMP' }}</div>
                      </div>
                      <div class="prop">
                        <div class="label">输出质量</div>
                        <div class="value">{{ item.output_quality === 'low' ? '低' : item.output_quality === 'medium' ? '中' : '高' }}</div>
                      </div>
                    </div>
                  </div>
                  <div class="btns">
                    <div class="btn" @click="handleView(item)">
                      <Icon icon="ant-design:eye-filled" :size="15" color="#3B82F6" />
                    </div>
                    <div class="btn" @click="handleEdit(item)">
                      <Icon icon="ant-design:edit-filled" :size="15" color="#3B82F6" />
                    </div>
                    <div class="btn" v-if="item.is_enabled" @click="handleStop(item)">
                      <Icon icon="ant-design:pause-circle-outlined" :size="15" color="#3B82F6" />
                    </div>
                    <div class="btn" v-else @click="handleStart(item)">
                      <Icon icon="ant-design:play-circle-outlined" :size="15" color="#3B82F6" />
                    </div>
                    <Popconfirm
                      title="是否确认删除？"
                      ok-text="是"
                      cancel-text="否"
                      @confirm="handleDelete(item)"
                    >
                      <div class="btn delete-btn">
                        <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
                      </div>
                    </Popconfirm>
                  </div>
                </div>
                <div class="task-img">
                  <img
                    src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Crect fill='%234287FC' width='100' height='100'/%3E%3Ctext fill='%23fff' x='50' y='50' text-anchor='middle' dominant-baseline='middle' font-size='20'%3E推流%3C/text%3E%3C/svg%3E"
                    alt="" 
                    class="img" 
                    @click="handleView(item)">
                </div>
              </ListItem>
            </template>
          </List>
        </Spin>
      </div>
    </div>

    <!-- 创建/编辑模态框 -->
    <StreamForwardModal @register="registerModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import {
  PlusOutlined,
  SwapOutlined,
} from '@ant-design/icons-vue';
import { List, Popconfirm, Spin } from 'ant-design-vue';
import { BasicForm, useForm } from '@/components/Form';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useMessage } from '@/hooks/web/useMessage';
import { Icon } from '@/components/Icon';
import { useDrawer } from '@/components/Drawer';
import {
  listStreamForwardTasks,
  deleteStreamForwardTask,
  startStreamForwardTask,
  stopStreamForwardTask,
  type StreamForwardTask,
} from '@/api/device/stream_forward';
import StreamForwardModal from './StreamForwardModal.vue';
import { getBasicColumns, getFormConfig } from './Data';

const ListItem = List.Item;

defineOptions({ name: 'StreamForward' });

const { createMessage } = useMessage();

// 视图模式（默认卡片模式）
const viewMode = ref<'table' | 'card'>('card');

// 卡片模式相关
const taskList = ref<StreamForwardTask[]>([]);
const loading = ref(false);
const [registerModal, { openDrawer }] = useDrawer();

// 分页相关
const page = ref(1);
const pageSize = ref(8);
const total = ref(0);

// 搜索参数
const searchParams = ref<{
  search?: string;
  is_enabled?: boolean;
}>({});

// 表格模式配置
const [registerTable, { reload }] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '推流转发任务列表',
  api: listStreamForwardTasks,
  beforeFetch: (params) => {
    let is_enabled = undefined;
    if (params.is_enabled !== '' && params.is_enabled !== undefined) {
      is_enabled = params.is_enabled === true || params.is_enabled === 'true' ? 1 : 0;
    }
    return {
      pageNo: params.page,
      pageSize: params.pageSize,
      search: params.search || undefined,
      is_enabled: is_enabled,
    };
  },
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
});

// 获取表格操作按钮
const getTableActions = (record: StreamForwardTask) => {
  const actions = [
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
  ];

  if (record.is_enabled) {
    actions.push({
      icon: 'ant-design:pause-circle-outlined',
      tooltip: '停止',
      onClick: () => handleStop(record),
    });
  } else {
    actions.push({
      icon: 'ant-design:play-circle-outlined',
      tooltip: '启动',
      onClick: () => handleStart(record),
    });
  }

  actions.push({
    icon: 'material-symbols:delete-outline-rounded',
    tooltip: '删除',
    popConfirm: {
      title: '确定删除此任务？',
      confirm: () => handleDelete(record),
    },
  });

  return actions;
};

// 切换视图模式
const handleToggleViewMode = () => {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  if (viewMode.value === 'card') {
    loadTasks();
  }
};

// 加载任务列表
const loadTasks = async () => {
  loading.value = true;
  try {
    const params: any = {
      pageNo: page.value,
      pageSize: pageSize.value,
    };
    if (searchParams.value.search) {
      params.search = searchParams.value.search;
    }
    if (searchParams.value.is_enabled !== undefined) {
      params.is_enabled = searchParams.value.is_enabled ? 1 : 0;
    }
    
    const response = await listStreamForwardTasks(params);
    if (response.code === 0) {
      taskList.value = response.data || [];
      total.value = response.total || 0;
    } else {
      createMessage.error(response.msg || '加载推流转发任务列表失败');
      taskList.value = [];
      total.value = 0;
    }
  } catch (error) {
    console.error('加载推流转发任务列表失败', error);
    createMessage.error('加载推流转发任务列表失败');
    taskList.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};

// 分页变化
const handlePageChange = (p: number, pz: number) => {
  page.value = p;
  pageSize.value = pz;
  loadTasks();
};

const handlePageSizeChange = (_current: number, size: number) => {
  pageSize.value = size;
  page.value = 1;
  loadTasks();
};

// 分页配置
const paginationProp = ref({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize,
  current: page,
  total,
  showTotal: (total: number) => `总 ${total} 条`,
  onChange: handlePageChange,
  onShowSizeChange: handlePageSizeChange,
});

// 表单提交
async function handleSubmit() {
  const params = await validate();
  searchParams.value = params || {};
  page.value = 1;
  if (viewMode.value === 'card') {
    await loadTasks();
  } else {
    reload();
  }
}

const [registerForm, { validate }] = useForm({
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
      field: 'is_enabled',
      label: '启用状态',
      component: 'Select',
      componentProps: {
        placeholder: '请选择启用状态',
        options: [
          { value: '', label: '全部' },
          { value: 1, label: '已启用' },
          { value: 0, label: '已禁用' },
        ],
      },
    },
  ],
  labelWidth: 80,
  baseColProps: { span: 6 },
  actionColOptions: { span: 6, offset: 0, style: { textAlign: 'right' } },
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

const handleCreate = () => {
  openDrawer(true, {});
};

const handleView = (record: StreamForwardTask) => {
  openDrawer(true, { type: 'view', record });
};

const handleEdit = (record: StreamForwardTask) => {
  openDrawer(true, { type: 'edit', record });
};

const handleDelete = async (record: StreamForwardTask) => {
  try {
    const response = await deleteStreamForwardTask(record.id);
    if (response.code === 0) {
      createMessage.success('删除成功');
      handleSuccess();
    } else {
      createMessage.error(response.msg || '删除失败');
    }
  } catch (error) {
    console.error('删除推流转发任务失败', error);
    createMessage.error('删除失败');
  }
};

const handleStart = async (record: StreamForwardTask) => {
  try {
    const response = await startStreamForwardTask(record.id);
    if (response && (response as any).id) {
      if ((response as any).already_running) {
        createMessage.warning('任务运行中');
      } else {
        createMessage.success('启动成功');
      }
      handleSuccess();
    } else if (response && typeof response === 'object' && 'code' in response) {
      if ((response as any).code === 0) {
        const data = (response as any).data || response;
        if (data && data.already_running) {
          createMessage.warning('任务运行中');
        } else {
          createMessage.success('启动成功');
        }
        handleSuccess();
      } else {
        createMessage.error((response as any).msg || '启动失败');
      }
    } else {
      createMessage.error('启动失败');
    }
  } catch (error) {
    console.error('启动推流转发任务失败', error);
    createMessage.error('启动失败');
  }
};

const handleStop = async (record: StreamForwardTask) => {
  try {
    const response = await stopStreamForwardTask(record.id);
    if (response && (response as any).id) {
      createMessage.success('停止成功');
      handleSuccess();
    } else if (response && typeof response === 'object' && 'code' in response) {
      if ((response as any).code === 0) {
        createMessage.success('停止成功');
        handleSuccess();
      } else {
        createMessage.error((response as any).msg || '停止失败');
      }
    } else {
      createMessage.error('停止失败');
    }
  } catch (error) {
    console.error('停止推流转发任务失败', error);
    createMessage.error('停止失败');
  }
};

const handleSuccess = () => {
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadTasks();
  }
};

// 刷新方法（供父组件调用）
const refresh = () => {
  handleSuccess();
};

defineExpose({
  refresh,
});

// 组件挂载时加载数据
onMounted(() => {
  if (viewMode.value === 'card') {
    loadTasks();
  }
});
</script>

<style lang="less" scoped>
.stream-forward-card-list-wrapper {
  .task-item {
    background: #fff;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s;

    &:hover {
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    &.normal {
      border-left: 4px solid #52c41a;
    }

    &.error {
      border-left: 4px solid #ff4d4f;
    }

    .task-info {
      flex: 1;

      .status {
        font-size: 12px;
        color: #999;
        margin-bottom: 8px;
      }

      .title {
        font-size: 16px;
        font-weight: 500;
        margin-bottom: 12px;
        color: #333;
      }

      .props {
        margin-bottom: 12px;

        .prop {
          .label {
            font-size: 12px;
            color: #999;
            margin-bottom: 4px;
          }

          .value {
            font-size: 14px;
            color: #333;
          }
        }
      }

      .btns {
        display: flex;
        gap: 8px;

        .btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.3s;

          &:hover {
            background: #f0f0f0;
          }

          &.delete-btn:hover {
            background: #fff1f0;
          }
        }
      }
    }

    .task-img {
      width: 100px;
      height: 100px;
      flex-shrink: 0;
      margin-left: 16px;

      .img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 8px;
        cursor: pointer;
      }
    }
  }
}

.toolbar-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>

