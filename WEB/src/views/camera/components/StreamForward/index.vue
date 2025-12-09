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
                <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">推流任务列表</span>
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
                  <div class="title o2" :title="item.task_name || item.id">{{ item.task_name || item.id }}</div>
                  <div class="props">
                    <div class="flex" style="justify-content: space-between;">
                      <div class="prop">
                        <div class="label">关联摄像头</div>
                        <div class="value" style="display: flex; align-items: center; gap: 4px;">
                          <span>{{ item.device_names && item.device_names.length > 0 ? (item.device_names.length > 1 ? item.device_names[0] + '...' : item.device_names[0]) : '无' }}</span>
                          <Icon 
                            v-if="item.device_names && item.device_names.length > 0" 
                            icon="ant-design:copy-outlined" 
                            :size="14" 
                            color="#666"
                            style="cursor: pointer; flex-shrink: 0;"
                            @click.stop="handleCopyDeviceNames(item)"
                            title="复制所有摄像头名称"
                          />
                        </div>
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
                    <div class="btn" @click="handleViewServiceInfo(item)" title="心跳信息">
                      <Icon icon="ant-design:heart-outlined" :size="15" color="#3B82F6" />
                    </div>
                    <div class="btn" v-if="item.is_enabled" @click="handleStop(item)">
                      <Icon icon="ant-design:pause-circle-outlined" :size="15" color="#3B82F6" />
                    </div>
                    <div class="btn" v-else @click="handleStart(item)">
                      <Icon icon="ant-design:play-circle-outlined" :size="15" color="#3B82F6" />
                    </div>
                    <div class="btn" v-if="item.is_enabled" @click="handleRestart(item)" title="重启">
                      <Icon icon="ant-design:reload-outlined" :size="15" color="#3B82F6" />
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
                    src="@/assets/images/video/push-stream.png"
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
    
    <!-- 日志查看模态框 -->
    <StreamForwardLogsModal @register="registerLogsModal" />
    
    <!-- 服务管理抽屉（心跳信息） -->
    <ServiceManageDrawer @register="registerServiceDrawer" @success="handleSuccess" />
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
import { useModal } from '@/components/Modal';
import { copyText } from '@/utils/copyTextToClipboard';
import {
  listStreamForwardTasks,
  deleteStreamForwardTask,
  startStreamForwardTask,
  stopStreamForwardTask,
  restartStreamForwardTask,
  type StreamForwardTask,
} from '@/api/device/stream_forward';
import StreamForwardModal from './StreamForwardModal.vue';
import StreamForwardLogsModal from './StreamForwardLogsModal.vue';
import ServiceManageDrawer from './ServiceManageDrawer.vue';
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
const [registerLogsModal, { openModal: openLogsModal }] = useModal();
const [registerServiceDrawer, { openDrawer: openServiceDrawer }] = useDrawer();

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
  title: '推流任务列表',
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
    {
      icon: 'ant-design:heart-outlined',
      tooltip: '心跳信息',
      onClick: () => handleViewServiceInfo(record),
    },
  ];

  if (record.is_enabled) {
    actions.push({
      icon: 'ant-design:pause-circle-outlined',
      tooltip: '停止',
      onClick: () => handleStop(record),
    });
    actions.push({
      icon: 'ant-design:reload-outlined',
      tooltip: '重启',
      onClick: () => handleRestart(record),
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
      createMessage.error(response.msg || '加载推流任务列表失败');
      taskList.value = [];
      total.value = 0;
    }
  } catch (error) {
    console.error('加载推流任务列表失败', error);
    createMessage.error('加载推流任务列表失败');
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
      // 延迟刷新，等待服务启动和心跳上报
      setTimeout(() => {
        handleSuccess();
      }, 2000);
    } else if (response && typeof response === 'object' && 'code' in response) {
      if ((response as any).code === 0) {
        const data = (response as any).data || response;
        if (data && data.already_running) {
          createMessage.warning('任务运行中');
        } else {
          createMessage.success('启动成功');
        }
        // 延迟刷新，等待服务启动和心跳上报
        setTimeout(() => {
          handleSuccess();
        }, 2000);
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

const handleRestart = async (record: StreamForwardTask) => {
  try {
    const response = await restartStreamForwardTask(record.id);
    if (response && (response as any).id) {
      createMessage.success('重启成功');
      // 延迟刷新，等待服务重启和心跳上报
      setTimeout(() => {
        handleSuccess();
      }, 2000);
    } else if (response && typeof response === 'object' && 'code' in response) {
      if ((response as any).code === 0) {
        createMessage.success('重启成功');
        // 延迟刷新，等待服务重启和心跳上报
        setTimeout(() => {
          handleSuccess();
        }, 2000);
      } else {
        createMessage.error((response as any).msg || '重启失败');
      }
    } else {
      createMessage.error('重启失败');
    }
  } catch (error) {
    console.error('重启推流转发任务失败', error);
    createMessage.error('重启失败');
  }
};

const handleSuccess = () => {
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadTasks();
  }
};

// 复制摄像头名称
const handleCopyDeviceNames = (item: StreamForwardTask) => {
  if (!item.device_names || item.device_names.length === 0) {
    createMessage.warning('无摄像头名称可复制');
    return;
  }
  const deviceNamesText = item.device_names.join(', ');
  copyText(deviceNamesText, '摄像头名称已复制到剪贴板');
};

// 查看服务信息（心跳信息）
const handleViewServiceInfo = (record: StreamForwardTask) => {
  openServiceDrawer(true, {
    taskId: record.id,
  });
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

<style scoped lang="less">
#stream-forward {
  .toolbar-buttons {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

.stream-forward-card-list-wrapper {
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
        padding-right: 90px;
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
        width: 220px;
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
            color: #3B82F6;
            transition: color 0.3s;
          }

          &:hover :deep(.anticon) {
            color: #5BA3F5;
          }

          &.disabled {
            cursor: not-allowed;
            opacity: 0.4;

            :deep(.anticon) {
              color: #ccc;
            }

            &:hover :deep(.anticon) {
              color: #ccc;
            }
          }

          &.delete-btn {
            :deep(.anticon) {
              color: #DC2626;
            }

            &:hover :deep(.anticon) {
              color: #DC2626;
            }
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

