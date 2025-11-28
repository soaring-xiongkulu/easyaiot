<template>
  <div id="space">
    <div class="statistics-detail-container">
      <div class="console-pre-cloud-record">
        <div style="display: flex;">
          <div class="ant-card resource-card" style="width: 100%;">
            <div class="device-card-list-wrapper p-2">
              <div class="p-4 bg-white">
                <BasicForm @register="registerForm" @reset="handleSubmit"/>
              </div>
              <div class="p-2 bg-white">
                <a-spin :spinning="loading">
                  <a-list
                    :grid="{ gutter: 8, xs: 10, sm: 10, md: 10, lg: 10, xl: 10, xxl: 10}"
                    :data-source="spaceList"
                    :pagination="paginationProp"
                  >
                    <template #header>
                      <div
                        style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;">
                        <span
                          style="padding-left: 30px;font-size: 16px;font-weight: 500;line-height: 24px;">抓拍空间列表</span>
                        <div class="space-x-2">
                          <a-button type="primary" @click="handleCreate" preIcon="ant-design:plus-outlined">
                            新建抓拍空间
                          </a-button>
                          <a-button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">
                            切换视图
                          </a-button>
                        </div>
                      </div>
                    </template>
                    <template #renderItem="{ item }">
                      <a-list-item class="device-item">
                        <div class="project-icon-item">
                          <a href="javascript:void(0)" @click="handleView(item)">
                            <img
                              class="project-icon-item_img"
                              :src="snapSpaceIcon">
                            <div class="project-icon-item_name">{{ item.space_name }}</div>
                          </a>
                          <div class="project-icon-item_more" @click.stop="handleProjectItem($event, item)">…
                          </div>
                        </div>
                      </a-list-item>
                    </template>
                    <template #empty>
                      <a-empty description="暂无抓拍空间" />
                    </template>
                  </a-list>
                </a-spin>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div style="position: absolute; top: 0px; left: 0px; width: 100%;">
      <div>
        <div
          :class="`ezd-popover project-popover ezd-popover-placement-rightTop ${ezd_popover_hidden}`"
          :style="`z-index: 1; width: 140px; padding: 0px; margin-left: 24px; left: ${position.x - 96}px; top: ${position.y - 175}px; transform-origin: -4px 0px;`"
          @click.stop="handleMoreItem">
          <div class="ezd-popover-content">
            <div class="ezd-popover-arrow"><span class="ezd-popover-arrow-content"></span></div>
            <div class="ezd-popover-inner" role="tooltip" style="padding: 0px;">
              <div class="ezd-popover-inner-content" style="color: rgb(38, 38, 38);">
                <div>
                  <div class="project-operator-item" @click="handleViewDetail">查看详情</div>
                  <div>
                    <div class="project-operator-item" @click="handleEditDetail">编辑信息</div>
                    <div class="project-operator-item" @click="handleViewImagesDetail">查看图片</div>
                    <div class="project-operator-item" @click="handleDeleteDetail">删除</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- 创建/编辑模态框 -->
    <SnapSpaceModal @register="registerModal" @success="handleSuccess" />
    
    <!-- 图片管理模态框 -->
    <SnapImageModal @register="registerImageModal" />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';
import { PlusOutlined, SwapOutlined, EyeOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { BasicForm, useForm } from '@/components/Form';
import { List } from 'ant-design-vue';
import { useModal } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import { getSnapSpaceList, deleteSnapSpace, type SnapSpace } from '@/api/device/snap';
import SnapSpaceModal from './SnapSpaceModal.vue';
import SnapImageModal from './SnapImageModal.vue';
import snapSpaceIcon from '@/assets/images/video/snap-space-icon.png';

defineOptions({ name: 'SnapSpace' });

const { createMessage } = useMessage();
const [registerModal, { openModal }] = useModal();
const [registerImageModal, { openModal: openImageModal }] = useModal();

// 视图模式
const viewMode = ref<'table' | 'card'>('card');
const spaceList = ref<SnapSpace[]>([]);
const loading = ref(false);
const ezd_popover_hidden = ref("ezd-popover-hidden");
const currentItem = ref<SnapSpace | null>(null);
const position = ref({ x: 0, y: 0 });

// 分页相关
const page = ref(1);
const pageSize = ref(20);
const total = ref(0);
const paginationProp = computed(() => ({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize: pageSize.value,
  current: page.value,
  total: total.value,
  showTotal: (total: number) => `总 ${total} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange,
}));

function pageChange(p: number, pz: number) {
  page.value = p;
  pageSize.value = pz;
  loadSpaceList();
}

function pageSizeChange(_current: number, size: number) {
  pageSize.value = size;
  loadSpaceList();
}

// 切换视图
const handleClickSwap = () => {
  viewMode.value = viewMode.value === 'table' ? 'card' : 'table';
  if (viewMode.value === 'card') {
    loadSpaceList();
  }
};

// 搜索参数
const searchParams = ref<{ search?: string }>({});

// 加载空间列表
const loadSpaceList = async () => {
  loading.value = true;
  try {
    const response = await getSnapSpaceList({ 
      pageNo: page.value, 
      pageSize: pageSize.value,
      ...searchParams.value
    });
    // 响应拦截器当total存在时会返回 { code, data, msg, total } 对象
    // 当total不存在时返回 data 数组
    if (response && typeof response === 'object') {
      if (Array.isArray(response)) {
        // 如果直接返回数组（total不存在的情况）
        spaceList.value = response;
        total.value = response.length;
      } else if (response.code === 0 && response.data) {
        // 如果返回整个响应对象（total存在的情况）
        spaceList.value = Array.isArray(response.data) ? response.data : [];
        total.value = response.total || 0;
      } else {
        createMessage.error(response.msg || '加载抓拍空间列表失败');
        spaceList.value = [];
      }
    } else {
      spaceList.value = [];
    }
  } catch (error) {
    console.error('加载抓拍空间列表失败', error);
    createMessage.error('加载抓拍空间列表失败');
    spaceList.value = [];
  } finally {
    loading.value = false;
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
  loadSpaceList();
};

// 弹出菜单相关
function handleClick(event: MouseEvent) {
  if (!document.contains(event.target as Node)) {
    return;
  }
  if (ezd_popover_hidden.value == "") {
    ezd_popover_hidden.value = "ezd-popover-hidden";
  }
}

async function handleProjectItem(event: MouseEvent, item: SnapSpace) {
  currentItem.value = item;
  position.value = { x: event.clientX, y: event.clientY };
  if (ezd_popover_hidden.value == "ezd-popover-hidden") {
    ezd_popover_hidden.value = "";
  }
}

function handleMoreItem(event: MouseEvent) {
  event.stopPropagation();
}

function handleViewDetail() {
  if (currentItem.value) {
    handleView(currentItem.value);
  }
  ezd_popover_hidden.value = "ezd-popover-hidden";
}

function handleEditDetail() {
  if (currentItem.value) {
    handleEdit(currentItem.value);
  }
  ezd_popover_hidden.value = "ezd-popover-hidden";
}

function handleViewImagesDetail() {
  if (currentItem.value) {
    handleViewImages(currentItem.value);
  }
  ezd_popover_hidden.value = "ezd-popover-hidden";
}

async function handleDeleteDetail() {
  if (currentItem.value) {
    await handleDelete(currentItem.value);
  }
  ezd_popover_hidden.value = "ezd-popover-hidden";
}

// 表单提交
async function handleSubmit() {
  const params = await validate();
  searchParams.value = params || {};
  page.value = 1;
  await loadSpaceList();
}

const [registerForm, { validate }] = useForm({
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
  labelWidth: 80,
  baseColProps: { span: 6 },
  actionColOptions: { span: 6 },
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

onMounted(() => {
  document.addEventListener('click', handleClick);
  if (viewMode.value === 'card') {
    loadSpaceList();
  }
});

onUnmounted(() => {
  document.removeEventListener('click', handleClick);
});
</script>

<style lang="less" scoped>
#space {
  .resource-card {
    border-radius: 2px;

    .device-item {
      padding: 0;
      margin-top: 16px;
    }

    .project-icon-item {
      display: inline-block;
      width: 100%;
      height: 122px;
      margin-bottom: 8px;
      position: relative;
      text-align: center;
      vertical-align: top;

      .project-icon-item_name {
        color: #000000a6;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .project-icon-item_more {
        background: #fff;
        border-radius: 100%;
        cursor: pointer;
        display: inline-block;
        height: 20px;
        line-height: 20px;
        opacity: 0;
        position: absolute;
        right: 5px;
        top: 5px;
        vertical-align: middle;
        width: 20px;
        text-align: center;
        font-size: 14px;
        transition: opacity 0.3s;
      }

      .project-icon-item_img {
        margin: 16px 0;
        width: 58px;
      }
    }

    .project-icon-item:hover {
      background: #1890ff1a;
      border-radius: 6px;
    }

    .project-icon-item:hover .project-icon-item_more {
      display: inline-block;
      opacity: 1;
    }
  }

  .ezd-popover-hidden {
    display: none;
  }

  .ezd-popover {
    font-feature-settings: "tnum", "tnum";
    box-sizing: border-box;
    color: #595959;
    cursor: auto;
    font-size: 14px;
    font-variant: tabular-nums;
    font-weight: 400;
    left: 0;
    line-height: 1.5715;
    list-style: none;
    margin: 0;
    padding: 0;
    position: absolute;
    text-align: left;
    top: 0;
    -webkit-user-select: text;
    -moz-user-select: text;
    -ms-user-select: text;
    user-select: text;
    white-space: normal;
    z-index: 1030;

    .ezd-popover-inner {
      background-clip: padding-box;
      background-color: #fff;
      border-radius: 2px;
      box-shadow: 0 3px 6px -4px #0000001f, 0 6px 16px 0 #00000014, 0 9px 28px 8px #0000000d;
      box-shadow: 0 0 8px #00000026 \9;

      .ezd-popover-inner-content {
        color: #595959;
        padding: 12px 16px;
      }

      .project-operator-item {
        color: #000000d9;
        cursor: pointer;
        font-size: 14px;
        line-height: 34px;
        padding: 0 8px;
        margin: 0 -8px;
        border-radius: 2px;
        transition: background-color 0.3s;
      }

      .project-operator-item:hover {
        background: #1890ff1a;
      }

      .project-operator-item:first-child {
        padding-top: 0;
      }
    }
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

.space-x-2 {
  display: flex;
  gap: 8px;
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
</style>