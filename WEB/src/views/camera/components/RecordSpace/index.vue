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
                <div class="list-header">
                  <span class="list-title">监控录像空间列表</span>
                </div>
                <Spin :spinning="loading">
                  <List
                    :grid="{ gutter: 8, xs: 10, sm: 10, md: 10, lg: 10, xl: 10, xxl: 10}"
                    :data-source="spaceList"
                    :pagination="paginationProp"
                  >
                    <template #renderItem="{ item }">
                      <ListItem class="device-item">
                        <div 
                          class="project-icon-item"
                          @contextmenu.prevent="handleRightClick($event, item)"
                        >
                          <a href="javascript:void(0)" @click="handleViewVideos(item)">
                            <img
                              class="project-icon-item_img"
                              :src="recordSpaceIcon">
                            <div class="project-icon-item_name">{{ item.space_name }}</div>
                          </a>
                        </div>
                      </ListItem>
                    </template>
                    <template #empty>
                      <Empty description="暂无监控录像空间"/>
                    </template>
                  </List>
                </Spin>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div>
      <div
        :class="`ezd-popover project-popover ezd-popover-placement-rightTop ${ezd_popover_hidden}`"
        :style="`z-index: 9999; width: 140px; padding: 0px; position: fixed; left: ${position.x}px; top: ${position.y}px; transform-origin: -4px 0px;`"
        @click.stop="handleMoreItem">
          <div class="ezd-popover-content">
            <div class="ezd-popover-arrow"><span class="ezd-popover-arrow-content"></span></div>
            <div class="ezd-popover-inner" role="tooltip" style="padding: 0px;">
              <div class="ezd-popover-inner-content" style="color: rgb(38, 38, 38);">
                <div>
                  <div class="project-operator-item" @click="handleViewDetail">查看录像</div>
                  <div>
                    <div class="project-operator-item" @click="handleEditDetail">编辑信息</div>
                    <div class="project-operator-item" @click="handleDeleteDetail">删除</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
    </div>

    <!-- 录像管理模态框 -->
    <RecordVideoModal @register="registerVideoModal"/>
  </div>
</template>

<script lang="ts" setup>
import {computed, onMounted, onUnmounted, ref} from 'vue';
import {Empty, List, Spin} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {useModal} from '@/components/Modal';
import {useMessage} from '@/hooks/web/useMessage';
import {deleteRecordSpace, getRecordSpaceList, getRecordVideoList, type RecordSpace} from '@/api/device/record';
import RecordVideoModal from './RecordVideoModal.vue';
import recordSpaceIcon from '@/assets/images/video/snap-space-icon.png';

const ListItem = List.Item;

defineOptions({name: 'RecordSpace'});

const {createMessage} = useMessage();
const [registerVideoModal, {openModal: openVideoModal}] = useModal();

const spaceList = ref<RecordSpace[]>([]);
const loading = ref(false);
const ezd_popover_hidden = ref("ezd-popover-hidden");
const currentItem = ref<RecordSpace | null>(null);
const position = ref({x: 0, y: 0});

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

// 搜索参数
const searchParams = ref<{ search?: string }>({});

// 加载空间列表
const loadSpaceList = async () => {
  loading.value = true;
  try {
    const response = await getRecordSpaceList({
      pageNo: page.value,
      pageSize: pageSize.value,
      ...searchParams.value
    });
    // 后台返回的数据结构可能是：
    // 1. 直接返回数组（响应拦截器已处理）
    // 2. 返回 { code, data, msg, total } 对象（分页接口）
    if (Array.isArray(response)) {
      // 如果直接返回数组
      spaceList.value = response;
      total.value = response.length;
    } else if (response && typeof response === 'object') {
      // 如果返回对象
      if (response.code === 0) {
        // 成功响应
        if (Array.isArray(response.data)) {
          // data是数组
          spaceList.value = response.data;
          total.value = response.total || response.data.length;
        } else if (response.data && Array.isArray(response.data.items)) {
          // data.items是数组（某些接口可能这样返回）
          spaceList.value = response.data.items;
          total.value = response.total || response.data.total || response.data.items.length;
        } else {
          spaceList.value = [];
          total.value = 0;
        }
      } else {
        // 错误响应
        createMessage.error(response.msg || '加载监控录像空间列表失败');
        spaceList.value = [];
        total.value = 0;
      }
    } else {
      spaceList.value = [];
      total.value = 0;
    }
  } catch (error) {
    console.error('加载监控录像空间列表失败', error);
    createMessage.error('加载监控录像空间列表失败');
    spaceList.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
};


// 查看录像
const handleViewVideos = (record: RecordSpace) => {
  openVideoModal(true, {space_id: record.id, space_name: record.space_name});
};

// 删除
const handleDelete = async (record: RecordSpace) => {
  try {
    // 如果监控录像空间关联了设备，提示用户删除设备
    if (record.device_id) {
      createMessage.warning('监控录像空间跟随设备，不能单独删除。请删除关联的设备，监控录像空间会自动删除。');
      return;
    }
    
    // 先检查空间下是否有录像
    const videoResponse = await getRecordVideoList(record.id, {
      pageNo: 1,
      pageSize: 1,
    });
    
    if (videoResponse.code === 0 && videoResponse.total > 0) {
      createMessage.warning('该空间下还有监控录像，无法删除。请先删除所有录像后再删除空间。');
      return;
    }
    
    await deleteRecordSpace(record.id);
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

// 右键菜单相关
function handleClick(event: MouseEvent) {
  // 如果点击的不是右键菜单本身，则隐藏菜单
  const target = event.target as HTMLElement;
  if (!target.closest('.ezd-popover') && ezd_popover_hidden.value === "") {
    ezd_popover_hidden.value = "ezd-popover-hidden";
  }
}

// 右键点击显示菜单
function handleRightClick(event: MouseEvent, item: RecordSpace) {
  event.preventDefault();
  event.stopPropagation();
  currentItem.value = item;
  position.value = {x: event.clientX, y: event.clientY};
  ezd_popover_hidden.value = "";
}

function handleMoreItem(event: MouseEvent) {
  event.stopPropagation();
}

function handleViewDetail() {
  if (currentItem.value) {
    handleViewVideos(currentItem.value);
  }
  ezd_popover_hidden.value = "ezd-popover-hidden";
}

function handleEditDetail() {
  // 编辑功能已禁用，监控录像空间跟随设备
  createMessage.info('监控录像空间信息跟随设备，无法单独编辑');
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

const [registerForm, {validate}] = useForm({
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
  baseColProps: {span: 6},
  actionColOptions: {span: 6},
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

// 暴露刷新方法给父组件
defineExpose({
  refresh: loadSpaceList
});

onMounted(() => {
  document.addEventListener('click', handleClick);
  loadSpaceList();
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
}

</style>

