<template>
  <div class="snap-space-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <a-button type="primary" @click="handleCreate">
        <template #icon>
          <PlusOutlined />
        </template>
        新建抓拍空间
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
        <template v-if="column.dataIndex === 'save_mode'">
          <a-tag :color="record.save_mode === 0 ? 'blue' : 'orange'">
            {{ record.save_mode === 0 ? '标准存储' : '归档存储' }}
          </a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'save_time'">
          {{ record.save_time === 0 ? '永久保存' : `${record.save_time}天` }}
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction :actions="getTableActions(record)" />
        </template>
        <template v-else-if="column.dataIndex === 'image_count'">
          <a-button type="link" @click="handleViewImages(record)">
            查看图片 ({{ record.image_count || 0 }})
          </a-button>
        </template>
      </template>
    </BasicTable>

    <!-- 卡片模式 -->
    <div v-else class="card-list">
      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in spaceList" :key="item.id">
          <a-card :hoverable="true" class="space-card">
            <template #title>
              <span>{{ item.space_name }}</span>
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
                    <a-menu-item @click="handleViewImages(item)">
                      <EyeOutlined /> 查看图片
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
                <span class="label">空间编号:</span>
                <span class="value">{{ item.space_code }}</span>
              </div>
              <div class="info-item">
                <span class="label">存储模式:</span>
                <a-tag :color="item.save_mode === 0 ? 'blue' : 'orange'">
                  {{ item.save_mode === 0 ? '标准存储' : '归档存储' }}
                </a-tag>
              </div>
              <div class="info-item">
                <span class="label">保存时间:</span>
                <span class="value">{{ item.save_time === 0 ? '永久保存' : `${item.save_time}天` }}</span>
              </div>
              <div class="info-item">
                <span class="label">任务数量:</span>
                <span class="value">{{ item.task_count || 0 }}</span>
              </div>
              <div class="info-item" v-if="item.description">
                <span class="label">描述:</span>
                <span class="value">{{ item.description }}</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
      <a-empty v-if="spaceList.length === 0" description="暂无抓拍空间" />
    </div>

    <!-- 创建/编辑模态框 -->
    <SnapSpaceModal @register="registerModal" @success="handleSuccess" />
    
    <!-- 图片管理模态框 -->
    <SnapImageModal @register="registerImageModal" />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted } from 'vue';
import { PlusOutlined, SwapOutlined, EyeOutlined, EditOutlined, DeleteOutlined, MoreOutlined } from '@ant-design/icons-vue';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useModal } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import { getSnapSpaceList, deleteSnapSpace, type SnapSpace } from '@/api/device/snap';
import SnapSpaceModal from './SnapSpaceModal.vue';
import SnapImageModal from './SnapImageModal.vue';

defineOptions({ name: 'SnapSpace' });

const { createMessage } = useMessage();
const [registerModal, { openModal }] = useModal();
const [registerImageModal, { openModal: openImageModal }] = useModal();

// 视图模式
const viewMode = ref<'table' | 'card'>('card');
const spaceList = ref<SnapSpace[]>([]);

// 切换视图
const handleClickSwap = () => {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  if (viewMode.value === 'card') {
    loadSpaceList();
  }
};

// 表格列定义
const getBasicColumns = () => [
  {
    title: '空间名称',
    dataIndex: 'space_name',
    width: 150,
  },
  {
    title: '空间编号',
    dataIndex: 'space_code',
    width: 150,
  },
  {
    title: 'Bucket名称',
    dataIndex: 'bucket_name',
    width: 200,
  },
  {
    title: '存储模式',
    dataIndex: 'save_mode',
    width: 100,
  },
  {
    title: '保存时间',
    dataIndex: 'save_time',
    width: 100,
  },
  {
    title: '任务数量',
    dataIndex: 'task_count',
    width: 100,
  },
  {
    title: '图片管理',
    dataIndex: 'image_count',
    width: 120,
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    width: 180,
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
  title: '抓拍空间列表',
  api: async (params) => {
    const response = await getSnapSpaceList(params);
    // 后端返回格式: { code: 0, data: [...], total: ... }
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
        label: '空间名称',
        component: 'Input',
        componentProps: {
          placeholder: '请输入空间名称',
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
const getTableActions = (record: SnapSpace) => {
  return [
    {
      icon: 'ant-design:eye-filled',
      tooltip: '查看',
      onClick: () => handleView(record),
    },
    {
      icon: 'ant-design:picture-outlined',
      tooltip: '查看图片',
      onClick: () => handleViewImages(record),
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
        title: '确定删除此抓拍空间？',
        confirm: () => handleDelete(record),
      },
    },
  ];
};

// 加载空间列表（卡片模式）
const loadSpaceList = async () => {
  try {
    const response = await getSnapSpaceList({ pageNo: 1, pageSize: 1000 });
    // 后端返回格式: { code: 0, data: [...], total: ... }
    if (response.code === 0) {
      spaceList.value = response.data || [];
    } else {
      createMessage.error(response.msg || '加载抓拍空间列表失败');
      spaceList.value = [];
    }
  } catch (error) {
    console.error('加载抓拍空间列表失败', error);
    createMessage.error('加载抓拍空间列表失败');
    spaceList.value = [];
  }
};

// 创建
const handleCreate = () => {
  openModal(true, { type: 'create' });
};

// 查看
const handleView = (record: SnapSpace) => {
  openModal(true, { type: 'view', record });
};

// 编辑
const handleEdit = (record: SnapSpace) => {
  openModal(true, { type: 'edit', record });
};

// 查看图片
const handleViewImages = (record: SnapSpace) => {
  openImageModal(true, { space_id: record.id, space_name: record.space_name });
};

// 删除
const handleDelete = async (record: SnapSpace) => {
  try {
    await deleteSnapSpace(record.id);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error: any) {
    console.error('删除失败', error);
    const errorMsg = error?.response?.data?.msg || error?.message || '删除失败';
    createMessage.error(errorMsg);
  }
};

// 刷新
const handleSuccess = () => {
  if (viewMode.value === 'table') {
    reload();
  } else {
    loadSpaceList();
  }
};

onMounted(() => {
  if (viewMode.value === 'card') {
    loadSpaceList();
  }
});
</script>

<style lang="less" scoped>
.snap-space-container {
  padding: 16px;
  background: #f0f2f5;
  min-height: calc(100vh - 200px);

  .toolbar {
    margin-bottom: 16px;
    display: flex;
    gap: 8px;
    background: #fff;
    padding: 16px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .card-list {
    background: #fff;
    padding: 16px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    min-height: 400px;

    .space-card {
      height: 100%;
      transition: all 0.3s;

      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      .card-content {
        .info-item {
          margin-bottom: 12px;
          display: flex;
          align-items: center;
          line-height: 1.6;

          .label {
            font-weight: 500;
            margin-right: 8px;
            min-width: 90px;
            color: #595959;
          }

          .value {
            flex: 1;
            color: #262626;
            word-break: break-all;
          }
        }
      }
    }
  }
}
</style>

