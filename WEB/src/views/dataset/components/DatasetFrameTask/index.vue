<template>
  <div class="device-drawer-warpper" style="height: 100%">
    <Card class="device-tabs" ref="cardRef">
      <div class="ant-card">
        <BasicTable @register="registerTable">
          <template #toolbar>
            <a-button type="primary"
                      @click="openTaskMolal(true, { datasetId: route.params['id'], isEdit: false, isView: false })"
                      preIcon="ic:baseline-add">
              新建视频流帧捕获任务
            </a-button>
            <a-button @click="handleSearchCamera"
                      preIcon="mingcute:search-ai-line">
              搜索局域网摄像头
            </a-button>
          </template>
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'action'">
              <TableAction
                :stopButtonPropagation="true"
                :actions="[
                {
                  icon: 'ant-design:eye-outlined',
                  tooltip: {
                    title: '详情',
                    placement: 'top',
                  },
                  onClick: openTaskMolal.bind(null, true, { datasetId: route.params['id'], isEdit: false, isView: true, record }),
                },
                 {
                  icon: 'mingcute:edit-line',
                  tooltip: {
                    title: '编辑',
                    placement: 'top',
                  },
                  onClick: openTaskMolal.bind(null, true, { datasetId: route.params['id'], isEdit: true, isView: false, record }),
                },
                {
                  tooltip: {
                    title: '删除',
                    placement: 'top',
                  },
                  icon: 'material-symbols:delete-outline-rounded',
                  popConfirm: {
                    placement: 'topRight',
                    title: '是否确认删除？',
                    confirm: deleteJob.bind(null, record),
                  },
                },
              ]"
              />
            </template>
          </template>
        </BasicTable>
      </div>
    </Card>
    <TaskModal @register="taskModalRegister" @success="handleSuccess"/>
    <VideoSearchModal @register="videoSearchRegister"/>
  </div>
</template>
<script setup lang="ts">
import {onMounted, reactive, ref} from 'vue';
import {BasicTable, TableAction, useTable} from "@/components/Table";
import {getBasicColumns, getFormConfig} from "./data";
import {useMessage} from "@/hooks/web/useMessage";
import {deleteDatasetFrameTask, getDatasetFrameTaskPage,} from "@/api/device/dataset";
import {useModal} from "@/components/Modal";
import TaskModal from "./components/TaskModal.vue";
import VideoSearchModal from "@/views/dataset/components/VideoSearchModal/index.vue";
import {useRoute} from "vue-router";

defineOptions({name: 'DatasetFrameTask'})

const {createMessage} = useMessage();

const checkedKeys = ref<Array<string | number>>([]);

onMounted(() => {
});

const route = useRoute()
const state = reactive({});

const [taskModalRegister, {openModal: openTaskMolal}] = useModal();
const [videoSearchRegister, {openModal: openVideoSearchMolal}] = useModal();

const [registerTable, {reload}] = useTable({
  title: '视频流帧捕获列表',
  api: getDatasetFrameTaskPage,
  columns: getBasicColumns(),
  useSearchForm: true,
  formConfig: getFormConfig(),
  showTableSetting: false,
  tableSetting: {fullScreen: true},
  showIndexColumn: false,
  rowKey: 'id',
  rowSelection: {
    type: 'checkbox',
    selectedRowKeys: checkedKeys,
    onSelect: onSelect,
    onSelectAll: onSelectAll,
  },
});

//文件删除
const deleteJob = async (record) => {
  try {
    deleteDatasetFrameTask(record['id']).then(() => {
      createMessage.success('删除成功');
      reload();
    });
  } catch (error) {
    console.error(error)
    createMessage.success('删除失败');
    console.log('handleDelete', error);
  }
};

// 表格刷新
function handleSuccess() {
  reload({
    page: 0,
  });
}

//搜索局域网摄像头
function handleSearchCamera(record) {
  openVideoSearchMolal(true, {record});
}

function onSelect(record, selected) {
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, record.id];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => id !== record.id);
  }
}

function onSelectAll(selected, _, changeRows) {
  const changeIds = changeRows.map((item) => item.id);
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, ...changeIds];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => {
      return !changeIds.includes(id);
    });
  }
}
</script>
<style lang="less" scoped>
.device-drawer-warpper {
  overflow-y: hidden;

  .detail-info {
    margin-bottom: 20px;
  }

  .ant-card {
    box-sizing: border-box;
    padding: 0;
    color: #000000d9;
    font-size: 14px;
    font-variant: tabular-nums;
    line-height: 1.5715;
    list-style: none;
    font-feature-settings: tnum;
    position: relative;
    background: #fff;
    border-radius: 2px;
    margin: 16px 16px 0;

    .ant-card-body {
      padding: 24px;

      .device_title {
        height: 32px;
        font-size: 16px;
        font-weight: 600;
        color: #2e3033;
        line-height: 19px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;

        .ant-btn {
          line-height: 1.5715;
          position: relative;
          display: inline-block;
          font-weight: 400;
          white-space: nowrap;
          text-align: center;
          background-image: none;
          border: 1px solid transparent;
          box-shadow: 0 2px #00000004;
          cursor: pointer;
          transition: all .3s cubic-bezier(.645, .045, .355, 1);
          -webkit-user-select: none;
          -moz-user-select: none;
          user-select: none;
          touch-action: manipulation;
          height: 32px;
          padding: 4px 15px;
          font-size: 14px;
          border-radius: 2px;
          color: #000000d9;
          border-color: #d9d9d9;
          background: #fff;
        }

        .ant-btn-primary {
          color: #fff;
        }

        .ant-btn-dangerous.ant-btn-primary {
          border-color: #ff4d4f;
          background: #ff4d4f;
          text-shadow: 0 -1px 0 rgba(0, 0, 0, .12);
          box-shadow: 0 2px #0000000b;
        }
      }

      .base_data {
        display: flex;
        align-items: center;
        font-size: 12px;
        color: #a6a6a6;
        line-height: 17px;

        .item:first-child {
          border-left: 0;
        }

        .item {
          padding-left: 12px;
          padding-right: 12px;
          border-left: 1px solid #e0e0e0;

          .red {
            color: #fa3758;
          }
        }
      }
    }
  }

  .device-tabs {
    .ant-tabs {
      background-color: #FFFFFF;
      padding: 20px;
      padding-top: 10px;
      margin: 16px 19px 0 15px;
    }
  }
}
</style>
