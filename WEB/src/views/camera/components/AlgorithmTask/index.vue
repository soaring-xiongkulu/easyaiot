<template>
  <div class="algorithm-task-page">
    <div class="page-header">
      <div class="header-left">
        <h2>算法任务管理</h2>
        <p class="description">管理用于分析实时RTSP/RTMP流的算法任务</p>
      </div>
      <div class="header-right">
        <a-button type="primary" @click="handleCreate">
          <template #icon><PlusOutlined /></template>
          新建算法任务
        </a-button>
      </div>
    </div>

    <div class="page-content">
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
              <div class="info-item" v-if="item.extractor_name">
                <span class="label">抽帧器:</span>
                <span class="value">{{ item.extractor_name }}</span>
              </div>
              <div class="info-item" v-if="item.sorter_name">
                <span class="label">排序器:</span>
                <span class="value">{{ item.sorter_name }}</span>
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
              <div class="info-item">
                <span class="label">处理帧数:</span>
                <span class="value">{{ item.total_frames || 0 }}</span>
              </div>
              <div class="info-item">
                <span class="label">检测次数:</span>
                <span class="value">{{ item.total_detections || 0 }}</span>
              </div>
              <div class="info-item" v-if="item.algorithm_services">
                <span class="label">算法服务:</span>
                <span class="value">{{ item.algorithm_services.length }} 个</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
      <a-empty v-if="taskList.length === 0" description="暂无算法任务" />
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
} from '@ant-design/icons-vue';
import { useDrawer } from '@/components/Drawer';
import { useMessage } from '@/hooks/web/useMessage';
import {
  listAlgorithmTasks,
  deleteAlgorithmTask,
  startAlgorithmTask,
  stopAlgorithmTask,
  type AlgorithmTask,
} from '@/api/device/algorithm_task';
import AlgorithmTaskModal from './AlgorithmTaskModal.vue';

defineOptions({ name: 'AlgorithmTask' });

const { createMessage } = useMessage();

const taskList = ref<AlgorithmTask[]>([]);
const [registerModal, { openDrawer }] = useDrawer();

const loadTasks = async () => {
  try {
    const response = await listAlgorithmTasks({ pageNo: 1, pageSize: 1000 });
    if (response.code === 0) {
      taskList.value = response.data || [];
    }
  } catch (error) {
    console.error('加载算法任务列表失败', error);
    createMessage.error('加载算法任务列表失败');
  }
};

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
      await loadTasks();
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
      await loadTasks();
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
      await loadTasks();
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
    const { updateAlgorithmTask } = await import('@/api/device/algorithm_task');
    const response = await updateAlgorithmTask(record.id, {
      is_enabled: !record.is_enabled,
    });
    if (response.code === 0) {
      createMessage.success('更新成功');
      await loadTasks();
    } else {
      createMessage.error(response.msg || '更新失败');
    }
  } catch (error) {
    console.error('更新算法任务状态失败', error);
    createMessage.error('更新失败');
  }
};

const handleSuccess = () => {
  loadTasks();
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

onMounted(() => {
  loadTasks();
});
</script>

<style scoped lang="less">
.algorithm-task-page {
  padding: 24px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;

    .header-left {
      h2 {
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 500;
      }

      .description {
        margin: 0;
        color: rgba(0, 0, 0, 0.45);
        font-size: 14px;
      }
    }
  }

  .page-content {
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
</style>

