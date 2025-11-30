<template>
  <div class="algorithm-service-list">
    <a-table
      :columns="columns"
      :data-source="serviceList"
      :pagination="false"
      row-key="id"
      size="small"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <a-space>
            <a-popconfirm title="确定要删除吗？" @confirm="handleDelete(record.id)">
              <a-button type="link" size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
        <template v-else-if="column.key === 'is_enabled'">
          <a-switch :checked="record.is_enabled" size="small" @change="handleToggleEnabled(record)" />
        </template>
      </template>
    </a-table>
    
    <a-empty v-if="serviceList.length === 0" description="暂无算法服务" />
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { useMessage } from '@/hooks/web/useMessage';
import {
  listTaskServices,
  deleteTaskService,
  updateTaskService,
  type AlgorithmModelService,
} from '@/api/device/algorithm_task';

defineOptions({ name: 'AlgorithmServiceList' });

const props = defineProps<{
  taskId: number;
}>();

const emit = defineEmits(['refresh']);

const { createMessage } = useMessage();

const serviceList = ref<AlgorithmModelService[]>([]);

const columns = [
  { title: '服务名称', dataIndex: 'service_name', key: 'service_name' },
  { title: '服务URL', dataIndex: 'service_url', key: 'service_url', ellipsis: true },
  { title: '服务类型', dataIndex: 'service_type', key: 'service_type' },
  { title: '阈值', dataIndex: 'threshold', key: 'threshold' },
  { title: '排序', dataIndex: 'sort_order', key: 'sort_order' },
  { title: '启用', key: 'is_enabled', width: 80 },
  { title: '操作', key: 'action', width: 120 },
];

const loadServices = async () => {
  try {
    const response = await listTaskServices(props.taskId);
    if (response.code === 0) {
      serviceList.value = response.data || [];
    }
  } catch (error) {
    console.error('加载算法服务列表失败', error);
  }
};

const handleDelete = async (serviceId: number) => {
  try {
    const response = await deleteTaskService(serviceId);
    if (response.code === 0) {
      createMessage.success('删除成功');
      await loadServices();
      emit('refresh');
    } else {
      createMessage.error(response.msg || '删除失败');
    }
  } catch (error) {
    console.error('删除算法服务失败', error);
    createMessage.error('删除失败');
  }
};

const handleToggleEnabled = async (record: AlgorithmModelService) => {
  try {
    // 将布尔值转换为整数：true -> 1, false -> 0
    const newValue = record.is_enabled ? 0 : 1;
    const response = await updateTaskService(record.id, {
      is_enabled: newValue,
    });
    if (response.code === 0) {
      createMessage.success('更新成功');
      await loadServices();
    } else {
      createMessage.error(response.msg || '更新失败');
    }
  } catch (error) {
    console.error('更新算法服务状态失败', error);
    createMessage.error('更新失败');
  }
};


onMounted(() => {
  loadServices();
});

defineExpose({
  loadServices,
});
</script>

<style scoped lang="less">
.algorithm-service-list {
}
</style>

