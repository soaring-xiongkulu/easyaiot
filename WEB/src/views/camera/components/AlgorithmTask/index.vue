<template>
  <div id="algorithm-task">
    <!-- 表格模式 -->
    <BasicTable v-if="viewMode === 'table'" @register="registerTable">
      <template #toolbar>
        <div class="toolbar-buttons">
          <a-button type="primary" @click="handleCreate">
            <template #icon>
              <PlusOutlined />
            </template>
            新建算法任务
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
    <div v-else class="card-mode-wrapper">
      <div class="statistics-detail-container">
        <div class="console-pre-cloud-record">
          <div style="display: flex;">
            <div class="ant-card resource-card" style="width: 100%;">
              <div class="device-card-list-wrapper p-2">
                <div class="p-4 bg-white">
                  <BasicForm @register="registerForm" @reset="handleSubmit"/>
                </div>
                <div class="p-2 bg-white">
                  <div class="list-header">
                    <span class="list-title">算法任务列表</span>
                    <div class="header-actions">
                      <a-button type="primary" @click="handleCreate">
                        <template #icon>
                          <PlusOutlined />
                        </template>
                        新建算法任务
                      </a-button>
                      <a-button @click="handleToggleViewMode" type="default">
                        <template #icon>
                          <SwapOutlined />
                        </template>
                        切换视图
                      </a-button>
                    </div>
                  </div>
                  <Spin :spinning="loading">
                    <a-row :gutter="[16, 16]">
                      <a-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in taskList" :key="item.id">
                        <a-card :title="item.task_name" size="small" hoverable>
                          <template #extra>
                            <a-dropdown>
                              <a-button type="text" size="small">
                                <template #icon><MoreOutlined /></template>
                              </a-button>
                              <template #overlay>
                                <a-menu>
                                  <a-menu-item @click="handleView(item)">
                                    <EyeOutlined /> 查看
                                  </a-menu-item>
                                  <a-menu-item @click="handleEdit(item)">
                                    <EditOutlined /> 编辑
                                  </a-menu-item>
                                  <a-menu-item v-if="item.run_status === 'running'" @click="handleStop(item)">
                                    <StopOutlined /> 停止
                                  </a-menu-item>
                                  <a-menu-item v-else @click="handleStart(item)">
                                    <PlayCircleOutlined /> 启动
                                  </a-menu-item>
                                  <a-menu-divider />
                                  <a-menu-item danger @click="handleDelete(item)">
                                    <DeleteOutlined /> 删除
                                  </a-menu-item>
                                </a-menu>
                              </template>
                            </a-dropdown>
                          </template>
                          <div class="card-content">
                            <div class="info-item">
                              <span class="label">任务类型:</span>
                              <a-tag :color="item.task_type === 'realtime' ? 'blue' : 'green'">
                                {{ item.task_type === 'realtime' ? '实时算法任务' : '抓拍算法任务' }}
                              </a-tag>
                            </div>
                            <div class="info-item" v-if="item.space_name">
                              <span class="label">抓拍空间:</span>
                              <span class="value">{{ item.space_name }}</span>
                            </div>
                            <div class="info-item" v-if="item.device_names && item.device_names.length > 0">
                              <span class="label">关联摄像头:</span>
                              <span class="value">{{ item.device_names.join(', ') }}</span>
                            </div>
                            <div class="info-item">
                              <span class="label">运行状态:</span>
                              <a-tag :color="getRunStatusColor(item.run_status)">
                                {{ getRunStatusText(item.run_status) }}
                              </a-tag>
                            </div>
                            <div class="info-item">
                              <span class="label">启用状态:</span>
                              <a-switch :checked="item.is_enabled" size="small" @change="handleToggleEnabled(item)" />
                            </div>
                            <div class="info-item" v-if="item.task_type === 'realtime'">
                              <span class="label">处理帧数:</span>
                              <span class="value">{{ item.total_frames || 0 }}</span>
                            </div>
                            <div class="info-item" v-if="item.task_type === 'realtime'">
                              <span class="label">检测次数:</span>
                              <span class="value">{{ item.total_detections || 0 }}</span>
                            </div>
                            <div class="info-item" v-if="item.task_type === 'snap'">
                              <span class="label">抓拍次数:</span>
                              <span class="value">{{ item.total_captures || 0 }}</span>
                            </div>
                            <div class="info-item" v-if="item.algorithm_services">
                              <span class="label">算法服务:</span>
                              <span class="value">{{ item.algorithm_services.length }} 个</span>
                            </div>
                          </div>
                        </a-card>
                      </a-col>
                    </a-row>
                    <a-empty v-if="taskList.length === 0 && !loading" description="暂无算法任务" />
                    <div v-if="taskList.length > 0" class="pagination-wrapper">
                      <a-pagination
                        v-model:current="page"
                        v-model:page-size="pageSize"
                        :total="total"
                        :show-total="(total: number) => `总 ${total} 条`"
                        :show-size-changer="true"
                        :show-quick-jumper="true"
                        @change="handlePageChange"
                        @show-size-change="handlePageSizeChange"
                      />
                    </div>
                  </Spin>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑模态框 -->
    <AlgorithmTaskModal @register="registerModal" @success="handleSuccess" />
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
  PlayCircleOutlined,
  StopOutlined,
  SwapOutlined,
} from '@ant-design/icons-vue';
import { Spin } from 'ant-design-vue';
import { useDrawer } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useMessage } from '@/hooks/web/useMessage';
import {
  listAlgorithmTasks,
  deleteAlgorithmTask,
  startAlgorithmTask,
  stopAlgorithmTask,
  updateAlgorithmTask,
  type AlgorithmTask,
} from '@/api/device/algorithm_task';
import AlgorithmTaskModal from './AlgorithmTaskModal.vue';
import { getBasicColumns, getFormConfig } from './Data';

defineOptions({ name: 'AlgorithmTask' });

const { createMessage } = useMessage();

// 视图模式（默认卡片模式）
const viewMode = ref<'table' | 'card'>('card');

// 卡片模式相关
const taskList = ref<AlgorithmTask[]>([]);
const loading = ref(false);
const [registerModal, { openDrawer }] = useDrawer();

// 分页相关
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);

// 搜索参数
const searchParams = ref<{
  search?: string;
  task_type?: 'realtime' | 'snap';
  is_enabled?: boolean;
}>({});

// 表格模式配置
const [registerTable, { reload }] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '算法任务列表',
  api: listAlgorithmTasks,
  beforeFetch: (params) => {
    // 转换参数格式
    return {
      pageNo: params.page,
      pageSize: params.pageSize,
      search: params.search || undefined,
      task_type: params.task_type || undefined,
      is_enabled: params.is_enabled !== '' && params.is_enabled !== undefined ? params.is_enabled : undefined,
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
const getTableActions = (record: AlgorithmTask) => {
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

  if (record.run_status === 'running') {
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
      title: '确定删除此算法任务？',
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

// 卡片模式加载任务
const loadTasks = async () => {
  loading.value = true;
  try {
    const response = await listAlgorithmTasks({
      pageNo: page.value,
      pageSize: pageSize.value,
      ...searchParams.value
    });
    if (response.code === 0) {
      taskList.value = response.data || [];
      total.value = response.total || 0;
    } else {
      createMessage.error(response.msg || '加载算法任务列表失败');
      taskList.value = [];
      total.value = 0;
    }
  } catch (error) {
    console.error('加载算法任务列表失败', error);
    createMessage.error('加载算法任务列表失败');
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
      field: 'task_type',
      label: '任务类型',
      component: 'Select',
      componentProps: {
        placeholder: '请选择任务类型',
        options: [
          { value: '', label: '全部' },
          { value: 'realtime', label: '实时算法任务' },
          { value: 'snap', label: '抓拍算法任务' },
        ],
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
          { value: true, label: '已启用' },
          { value: false, label: '已禁用' },
        ],
      },
    },
  ],
  labelWidth: 80,
  baseColProps: { span: 6 },
  // 将按钮放到第一行，与第三个字段同一行
  actionColOptions: { span: 6, offset: 0, style: { textAlign: 'right' } },
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

const handleCreate = () => {
  openDrawer(true, { type: 'add' });
};

const handleView = (record: AlgorithmTask) => {
  openDrawer(true, { type: 'view', record });
};

const handleEdit = (record: AlgorithmTask) => {
  openDrawer(true, { type: 'edit', record });
};

const handleDelete = async (record: AlgorithmTask) => {
  try {
    const response = await deleteAlgorithmTask(record.id);
    if (response.code === 0) {
      createMessage.success('删除成功');
      handleSuccess();
    } else {
      createMessage.error(response.msg || '删除失败');
    }
  } catch (error) {
    console.error('删除算法任务失败', error);
    createMessage.error('删除失败');
  }
};

const handleStart = async (record: AlgorithmTask) => {
  try {
    const response = await startAlgorithmTask(record.id);
    if (response.code === 0) {
      createMessage.success('启动成功');
      handleSuccess();
    } else {
      createMessage.error(response.msg || '启动失败');
    }
  } catch (error) {
    console.error('启动算法任务失败', error);
    createMessage.error('启动失败');
  }
};

const handleStop = async (record: AlgorithmTask) => {
  try {
    const response = await stopAlgorithmTask(record.id);
    if (response.code === 0) {
      createMessage.success('停止成功');
      handleSuccess();
    } else {
      createMessage.error(response.msg || '停止失败');
    }
  } catch (error) {
    console.error('停止算法任务失败', error);
    createMessage.error('停止失败');
  }
};

const handleToggleEnabled = async (record: AlgorithmTask) => {
  try {
    const response = await updateAlgorithmTask(record.id, {
      is_enabled: !record.is_enabled,
    });
    if (response.code === 0) {
      createMessage.success('更新成功');
      handleSuccess();
    } else {
      createMessage.error(response.msg || '更新失败');
    }
  } catch (error) {
    console.error('更新算法任务状态失败', error);
    createMessage.error('更新失败');
  }
};

const handleSuccess = () => {
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadTasks();
  }
};

const getRunStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    running: 'green',
    stopped: 'default',
    restarting: 'orange',
  };
  return colorMap[status] || 'default';
};

const getRunStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    running: '运行中',
    stopped: '已停止',
    restarting: '重启中',
  };
  return textMap[status] || status;
};

// 暴露刷新方法给父组件
defineExpose({
  refresh: () => {
    if (viewMode.value === 'table') {
      reload();
    } else {
      loadTasks();
    }
  }
});

onMounted(() => {
  if (viewMode.value === 'card') {
    loadTasks();
  }
});
</script>

<style scoped lang="less">
#algorithm-task {
  .resource-card {
    border-radius: 2px;
  }

  .p-2 {
    padding: 8px;
  }

  .p-4 {
    padding: 16px;
  }

  .bg-white {
    background-color: #fff;
  }

  .list-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    margin-bottom: 16px;
    border-bottom: 1px solid #f0f0f0;

    .list-title {
      font-size: 16px;
      font-weight: 500;
      line-height: 24px;
      color: rgba(0, 0, 0, 0.85);
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .toolbar-buttons {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .card-mode-wrapper {
    .p-2 {
      padding: 8px;
    }

    .p-4 {
      padding: 16px;
    }

    .bg-white {
      background-color: #fff;
    }
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

  .pagination-wrapper {
    margin-top: 24px;
    text-align: right;
  }

  .ant-card {
    -webkit-font-feature-settings: "tnum";
    font-feature-settings: "tnum", "tnum";
    background: #fff;
    border-radius: 2px;
    -webkit-box-sizing: border-box;
    box-sizing: border-box;
    color: #000000a6;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5;
    list-style: none;
    margin: 0;
    padding: 0;
    position: relative;
    -webkit-transition: all .3s;
    transition: all .3s;
  }
}
</style>

