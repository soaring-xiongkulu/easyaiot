<template>
  <div class="device-wrapper">
    <div class="device-tab">
      <Tabs
        :animated="{ inkBar: true, tabPane: true }"
        :activeKey="state.activeKey"
        :tabBarGutter="60"
        @tabClick="handleTabClick"
      >
        <TabPane key="1" tab="消息配置">
          <BasicTable @register="registerTable" v-if="state.isTableMode">
            <template #toolbar>
              <a-button type="primary" @click="openConfigModal(true, { type: 'add' })">新增设置
              </a-button>
              <a-button type="default" @click="handleClickSwap"
                        preIcon="ant-design:swap-outlined">切换视图
              </a-button>
            </template>
            <template #bodyCell="{ column, record }">
              <template v-if="column.dataIndex === 'action'">
                <TableAction
                  :actions="[
              {
                icon: 'ant-design:eye-filled',
                tooltip: {
                  title: '详情',
                  placement: 'top',
                },
                onClick: openDetailDrawer.bind(null, true, { record }),
              },
              {
                tooltip: {
                  title: '编辑',
                  placement: 'top',
                },
                icon: 'ant-design:edit-filled',
                onClick: openConfigModal.bind(null, true, { type: 'edit', record }),
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
                  confirm: handleDelete.bind(null, record),
                },
              },
            ]"
                />
              </template>
            </template>
          </BasicTable>
          <div v-else>
            <NoficeCardList :params="params" :api="messageConfigQuery" @get-method="getMethod"
                            @delete="handleDel" @edit="handleEdit" @view="handleView">
              <template #header>
                <a-button type="primary" @click="openConfigModal(true, { type: 'add' })">新增设置
                </a-button>
                <a-button type="default" @click="handleClickSwap"
                          preIcon="ant-design:swap-outlined">切换视图
                </a-button>
              </template>
            </NoficeCardList>
          </div>
        </TabPane>
        <TabPane key="2" tab="消息推送">
          <div style="padding: 12px; padding-top: 0">
            <Tabs
              :animated="{ inkBar: true, tabPane: true }"
              :activeKey="state.pushActiveKey"
              :tabBarGutter="60"
              @tabClick="handlePushTabClick"
            >
              <TabPane key="1" tab="邮件">
                <email/>
              </TabPane>
              <TabPane key="2" tab="短信">
                <sms/>
              </TabPane>
              <TabPane key="3" tab="微信">
                <wechat/>
              </TabPane>
              <TabPane key="4" tab="钉钉">
                <ding/>
              </TabPane>
              <TabPane key="5" tab="HTTP">
                <http/>
              </TabPane>
            </Tabs>
          </div>
        </TabPane>
        <TabPane key="4" tab="推送历史">
          <div style="padding: 12px; padding-top: 0">
            <Tabs
              :animated="{ inkBar: true, tabPane: true }"
              :activeKey="state.historyActiveKey"
              :tabBarGutter="60"
              @tabClick="handleHistoryTabClick"
            >
              <TabPane key="3" tab="邮件">
                <History :msgType="state.historyActiveKey"/>
              </TabPane>
              <TabPane key="1" tab="短信">
                <History :msgType="state.historyActiveKey"/>
              </TabPane>
              <TabPane key="4" tab="微信">
                <History :msgType="state.historyActiveKey"/>
              </TabPane>
              <TabPane key="5" tab="钉钉">
                <History :msgType="state.historyActiveKey"/>
              </TabPane>
              <TabPane key="6" tab="HTTP">
                <History :msgType="state.historyActiveKey"/>
              </TabPane>
            </Tabs>
          </div>
        </TabPane>
        <TabPane key="5" tab="用户分组">
          <Group/>
        </TabPane>
        <TabPane key="6" tab="用户管理">
          <Audience/>
        </TabPane>
      </Tabs>
      <!-- 新增/编辑配置 -->
      <ConfigModal @register="registerConfigModal" @success="reload"/>
      <!-- 通知记录 -->
      <DetailDrawer @register="registerDetailDrawer"/>
    </div>
  </div>
</template>
<script lang="ts" setup name="noticeSetting">
import {onMounted, reactive} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {useModal} from '@/components/Modal';
import {useDrawer} from '@/components/Drawer';
import {getFormConfig, getTableColumns} from './Data';
import ConfigModal from '@/views/notice/components/configuration/ConfigModal.vue';
import DetailDrawer from '@/views/notice/components/configuration/DetailDrawer.vue';
import {messageConfigDelete, messageConfigQuery} from '/@/api/modules/notice';
import {TabPane, Tabs} from "ant-design-vue";

import email from '@/views/notice/components/msgPush/email/index.vue';
import ding from '@/views/notice/components/msgPush/ding/index.vue';
import http from '@/views/notice/components/msgPush/http/index.vue';
import sms from '@/views/notice/components/msgPush/sms/index.vue';
import wechat from '@/views/notice/components/msgPush/wechat/index.vue';

import History from '@/views/notice/components/task/History/index.vue';
import Group from '@/views/notice/components/user/Group/index.vue';
import Audience from '@/views/notice/components/user/Audience/index.vue';
import NoficeCardList from "@/views/notice/components/CardList/NoficeCardList.vue";

defineOptions({name: 'Notice'})

const [registerConfigModal, {openModal: openConfigModal}] = useModal();
const [registerDetailDrawer, {openDrawer: openDetailDrawer}] = useDrawer();

const state = reactive({
  isTableMode: false,
  activeKey: '1',
  pushActiveKey: '1',
  historyActiveKey: '1',
  SmsActiveKey: '1',
});

const handleTabClick = (activeKey) => {
  state.activeKey = activeKey;
};

const handlePushTabClick = (activeKey) => {
  state.pushActiveKey = activeKey;
};

const handleHistoryTabClick = (activeKey) => {
  state.historyActiveKey = activeKey;
};

// 请求api时附带参数
const params = {};

let cardListReload = () => {
};

// 获取内部fetch方法;
function getMethod(m: any) {
  cardListReload = m;
}

//详情按钮事件
function handleView(record) {
  openDetailDrawer(true, record);
}

//编辑按钮事件
function handleEdit(record) {
  openConfigModal(true,{ type: 'edit', record })
  cardListReload();
}

//删除按钮事件
function handleDel(record) {
  handleDelete(record);
  cardListReload();
}

// 切换视图
function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

const {createMessage} = useMessage();
const [
  registerTable,
  {
    // setLoading,
    // setColumns,
    // getColumns,
    // getDataSource,
    // getRawDataSource,
    reload,
    // getPaginationRef,
    // setPagination,
    // getSelectRows,
    // getSelectRowKeys,
    // setSelectedRowKeys,
    // clearSelectedRowKeys,
  },
] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '消息配置',
  api: messageConfigQuery,
  columns: getTableColumns(),
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: getFormConfig(),
  rowKey: 'id',
});

const handleDelete = async ({id}) => {
  try {
    await messageConfigDelete({id});
    createMessage.success('删除成功');
    reload();
  }catch (error) {
    console.error(error)
    createMessage.success('删除失败');
    console.log('handleDelete', error);
  }
};

onMounted(() => {
  // openConfigModal(true, { type: 'add' });
});
</script>

<style lang="less" scoped>
:deep(.iot-basic-table-action.left) {
  justify-content: center;
}

.device-wrapper {
  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }

  :deep(.ant-form-item) {
    margin-bottom: 10px;
  }

  .device-tab {
    padding: 16px 19px 0 15px;

    .ant-tabs {
      background-color: #FFFFFF;

      :deep(.ant-tabs-nav) {
        padding: 5px 0 0 25px;
      }
    }
  }

  .device-info {
    padding: 16px 16px 0;

    .ant-row {
      display: flex;
      flex-flow: row wrap;

      .ant-col {
        margin-top: 6px !important;
        margin-bottom: 6px !important;
        position: relative;
        min-height: 1px;

        .ant-card {
          box-sizing: border-box;
          margin: 0;
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
          box-shadow: 0 0 4px #00000026;

          .ant-card-body {
            padding: 24px;

            .card-box {
              display: flex;

              .img {
                width: 104px;
                margin-right: 8px;
                border-radius: 10px;
              }

              .info-box {
                flex: 1;

                .title {
                  font-size: 12px;
                  line-height: 1;
                  font-weight: 600;
                  margin-bottom: 10px;
                  padding-left: 8px;
                }

                .list {
                  display: flex;

                  .item {
                    flex: 1;
                    text-align: center;

                    .num {
                      font-size: 26px;
                      font-weight: 600;
                    }

                    .name {
                      font-weight: 600;
                    }
                  }
                }
              }
            }
          }

          .ant-card-body:before {
            display: table;
            content: "";
          }

          .ant-card-body:after {
            display: table;
            clear: both;
            content: "";
          }
        }
      }
    }

    .ant-col-7 {
      display: block;
      flex: 0 0 29.1%;
      max-width: 29.1%;
    }

    .ant-col-10 {
      display: block;
      flex: 0 0 41.6%;
      max-width: 41.6%;
    }
  }

  .device-tab {
    padding: 16px 19px 0 15px;

    .ant-tabs {
      background-color: #FFFFFF;
    }
  }
}
</style>
