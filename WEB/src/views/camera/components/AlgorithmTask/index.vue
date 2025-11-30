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
    <div v-else class="algorithm-task-card-list-wrapper p-2">
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
              <div
                style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;">
                <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">算法任务列表</span>
                <div style="display: flex; gap: 8px;">
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
            </template>
            <template #renderItem="{ item }">
              <ListItem :class="item.is_enabled ? 'task-item normal' : 'task-item error'">
                <div class="task-info">
                  <div class="status">{{ item.is_enabled ? '已启用' : '已禁用' }}</div>
                  <div class="title o2">{{ item.task_name || item.id }}</div>
                  <div class="props">
                    <div class="flex" style="justify-content: space-between;">
                      <div class="prop">
                        <div class="label">任务类型</div>
                        <div class="value">{{ item.task_type === 'realtime' ? '实时算法任务' : '抓拍算法任务' }}</div>
                      </div>
                      <div class="prop" v-if="item.device_names && item.device_names.length > 0">
                        <div class="label">关联摄像头</div>
                        <div class="value">{{ item.device_names.join(', ') }}</div>
                      </div>
                    </div>
                    <div class="prop">
                      <div class="label">关联算法服务</div>
                      <div class="value">{{ item.service_names || (item.algorithm_services && item.algorithm_services.length > 0 ? item.algorithm_services.map(s => s.service_name).join(', ') : '') }}</div>
                    </div>
                  </div>
                  <div class="btns">
                    <div class="btn" @click="handleView(item)">
                      <Icon icon="ant-design:eye-filled" :size="15" color="#3B82F6" />
                    </div>
                    <div class="btn" @click="handleEdit(item)">
                      <Icon icon="ant-design:edit-filled" :size="15" color="#3B82F6" />
                    </div>
                    <div class="btn" @click="handleManageServices(item)" title="服务管理">
                      <Icon icon="ant-design:setting-outlined" :size="15" color="#3B82F6" />
                    </div>
                    <div class="btn" v-if="item.run_status === 'running'" @click="handleStop(item)">
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
                      <div class="btn">
                        <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
                      </div>
                    </Popconfirm>
                  </div>
                </div>
                <div class="task-img">
                  <img
                    :src="getTaskImage(item.task_type)"
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
    <AlgorithmTaskModal @register="registerModal" @success="handleSuccess" />
    
    <!-- 服务管理抽屉 -->
    <ServiceManageDrawer @register="registerServiceDrawer" />
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
import { List, Popconfirm, Spin } from 'ant-design-vue';
import { useDrawer } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useMessage } from '@/hooks/web/useMessage';
import { Icon } from '@/components/Icon';
import {
  listAlgorithmTasks,
  deleteAlgorithmTask,
  startAlgorithmTask,
  stopAlgorithmTask,
  updateAlgorithmTask,
  type AlgorithmTask,
} from '@/api/device/algorithm_task';
import AlgorithmTaskModal from './AlgorithmTaskModal.vue';
import ServiceManageDrawer from './ServiceManageDrawer.vue';
import { getBasicColumns, getFormConfig } from './Data';
import AI_TASK_IMAGE from '@/assets/images/video/ai-task.png';

const ListItem = List.Item;

defineOptions({ name: 'AlgorithmTask' });

const { createMessage } = useMessage();

// 视图模式（默认卡片模式）
const viewMode = ref<'table' | 'card'>('card');

// 卡片模式相关
const taskList = ref<AlgorithmTask[]>([]);
const loading = ref(false);
const [registerModal, { openDrawer }] = useDrawer();
const [registerServiceDrawer, { openDrawer: openServiceDrawer }] = useDrawer();

// 分页相关
const page = ref(1);
const pageSize = ref(8);
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
    let is_enabled = undefined;
    if (params.is_enabled !== '' && params.is_enabled !== undefined) {
      // 将布尔值转换为整数：true -> 1, false -> 0
      is_enabled = params.is_enabled === true || params.is_enabled === 'true' ? 1 : 0;
    }
    return {
      pageNo: params.page,
      pageSize: params.pageSize,
      search: params.search || undefined,
      task_type: params.task_type || undefined,
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
    {
      icon: 'ant-design:setting-outlined',
      tooltip: '服务管理',
      onClick: () => handleManageServices(record),
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
    // 转换搜索参数中的布尔值为整数
    const params: any = {
      pageNo: page.value,
      pageSize: pageSize.value,
      ...searchParams.value
    };
    if (params.is_enabled !== undefined && params.is_enabled !== '') {
      params.is_enabled = params.is_enabled === true || params.is_enabled === 'true' ? 1 : 0;
    }
    const response = await listAlgorithmTasks(params);
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

// 根据任务类型获取图片
const getTaskImage = (taskType: string) => {
  return AI_TASK_IMAGE;
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
          { value: 1, label: '已启用' },
          { value: 0, label: '已禁用' },
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

const handleManageServices = (record: AlgorithmTask) => {
  openServiceDrawer(true, { taskId: record.id });
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
    // 将布尔值转换为整数：true -> 1, false -> 0
    const newValue = record.is_enabled ? 0 : 1;
    const response = await updateAlgorithmTask(record.id, {
      is_enabled: newValue,
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
  .toolbar-buttons {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.algorithm-task-card-list-wrapper {
  :deep(.ant-list-header) {
    border-block-end: 0;
  }
  :deep(.ant-list-header) {
    padding-top: 0;
    padding-bottom: 8px;
  }
  :deep(.ant-list) {
    padding: 6px;
  }
  :deep(.ant-list-item) {
    margin: 6px;
  }
  :deep(.task-item) {
    overflow: hidden;
    box-shadow: 0 0 4px #00000026;
    border-radius: 8px;
    padding: 16px 0;
    position: relative;
    background-color: #fff;
    background-repeat: no-repeat;
    background-position: center center;
    background-size: 104% 104%;
    transition: all 0.5s;
    min-height: 208px;
    height: 100%;

    &.normal {
      background-image: url('@/assets/images/product/blue-bg.719b437a.png');

      .task-info .status {
        background: #d9dffd;
        color: #266CFBFF;
      }
    }

    &.error {
      background-image: url('@/assets/images/product/red-bg.101af5ac.png');

      .task-info .status {
        background: #fad7d9;
        color: #d43030;
      }
    }

    .task-info {
      flex-direction: column;
      max-width: calc(100% - 128px);
      padding-left: 16px;

      .status {
        min-width: 90px;
        height: 25px;
        border-radius: 6px 0 0 6px;
        font-size: 12px;
        font-weight: 500;
        line-height: 25px;
        text-align: center;
        position: absolute;
        right: 0;
        top: 16px;
        padding: 0 8px;
        white-space: nowrap;
      }

      .title {
        font-size: 16px;
        font-weight: 600;
        color: #050708;
        line-height: 20px;
        height: 40px;
        padding-right: 60px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .props {
        margin-top: 10px;

        .prop {
          flex: 1;
          margin-bottom: 10px;

          .label {
            font-size: 12px;
            font-weight: 400;
            color: #666;
            line-height: 14px;
          }

          .value {
            font-size: 14px;
            font-weight: 600;
            color: #050708;
            line-height: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-top: 6px;
          }
        }
      }

      .btns {
        display: flex;
        position: absolute;
        left: 16px;
        bottom: 16px;
        margin-top: 20px;
        width: 180px;
        height: 28px;
        border-radius: 45px;
        justify-content: space-around;
        padding: 0 10px;
        align-items: center;
        border: 2px solid #266cfbff;

        .btn {
          width: 28px;
          text-align: center;
          position: relative;
          cursor: pointer;

          &:before {
            content: '';
            display: block;
            position: absolute;
            width: 1px;
            height: 7px;
            background-color: #e2e2e2;
            left: 0;
            top: 9px;
          }

          &:first-child:before {
            display: none;
          }

          :deep(.anticon) {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #87CEEB;
            transition: color 0.3s;
          }

          &:hover :deep(.anticon) {
            color: #5BA3F5;
          }
        }
      }
    }

    .task-img {
      position: absolute;
      right: 20px;
      top: 50px;

      img {
        cursor: pointer;
        width: 120px;
      }
    }
  }
}
</style>

