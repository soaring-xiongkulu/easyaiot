<template>
  <div class="device-wrapper">
    <div class="device-tab page-content-card">
      <Tabs
        v-model:activeKey="state.activeKey"
        :animated="{ inkBar: true, tabPane: false }"
        :destroyInactiveTabPane="true"
        :tabBarGutter="60"
      >
        <TabPane key="list" tab="规则列表">
          <div class="device-list-pane">
            <BasicTable @register="registerTable" v-if="state.isTableMode">
              <template #form-custom></template>
              <template #toolbar>
                <Button type="primary" @click="openTargetModal('add')" preIcon="ant-design:plus-outlined">新增规则</Button>
                <Button type="default" @click="openTargetModal('import')" preIcon="ant-design:plus-outlined">导入规则</Button>
                <Button type="default" @click="handleClickSwap"
                          preIcon="ant-design:swap-outlined">切换视图
                </Button>
                <PopConfirmButton
                  placement="topRight"
                  @confirm="deleteAll"
                  type="primary"
                  color="error"
                  :disabled="!checkedKeys.length"
                  :title="`是否确认删除？`"
                  preIcon="ant-design:delete-outlined"
                >
                  批量删除
                </PopConfirmButton>
              </template>
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'action'">
                  <TableAction
                    :stopButtonPropagation="true"
                    :actions="[
                      {
                        tooltip: {
                          title: '详情',
                          placement: 'top',
                        },
                        icon: 'ant-design:eye-filled',
                        onClick: handleOpen.bind(null, record),
                      },
                      {
                        tooltip: {
                          title: '编辑',
                          placement: 'top',
                        },
                        icon: 'ant-design:edit-filled',
                        onClick: () => openTargetModal('edit', record),
                        ifShow: !isNodeRedDemoFlow(record),
                      },
                      {
                        tooltip: {
                          title: isNodeRedDemoFlow(record) ? '查看规则链（只读）' : '编辑规则链',
                          placement: 'top',
                        },
                        icon: 'material-symbols:media-link-outline-sharp',
                        onClick: rowClickTable.bind(null, record),
                      },
                      {
                        tooltip: {
                          title: '删除',
                          placement: 'top',
                        },
                        icon: 'material-symbols:delete-outline-rounded',
                        popConfirm: {
                          title: `是否确认删除?`,
                          confirm: handleDelete.bind(null, record),
                        },
                        ifShow: !isNodeRedDemoFlow(record),
                      },
                    ]"
                    :dropDownActions="[]"
                  />
                </template>
                <template v-if="column.key === 'root'">
                  <Tag :color="record.disabled ? 'red' : 'blue'">{{
                      record.disabled ? '禁用' : '启用'
                    }}
                  </Tag>
                </template>
              </template>
            </BasicTable>
            <div v-else class="device-card-wrap">
              <RulechainCardList :params="params" :api="flowsList" @get-method="getMethod"
                                 @delete="handleDel" @edit="handleEdit" @view="handleView" @go="rowClickTable">
                <template #header>
                  <Button type="primary" @click="openTargetModal('add')"
                            preIcon="ant-design:plus-outlined">
                    新增规则
                  </Button>
                  <Button type="default" @click="openTargetModal('import')"
                            preIcon="ant-design:plus-outlined">
                    导入规则
                  </Button>
                  <Button type="default" @click="handleClickSwap"
                            preIcon="ant-design:swap-outlined">切换视图
                  </Button>
                  <PopConfirmButton
                    placement="topRight"
                    @confirm="deleteAll"
                    type="primary"
                    color="error"
                    :disabled="!checkedKeys.length"
                    :title="`您确定要批量删除数据?`"
                    preIcon="ant-design:delete-outlined"
                  >批量删除
                  </PopConfirmButton>
                </template>
              </RulechainCardList>
            </div>
            <Modal @register="registerModel" @success="handleSuccess"/>
            <Drawer @register="registerDrawer" @success="handleSuccess"/>
          </div>
        </TabPane>
      </Tabs>
    </div>
  </div>
</template>
<script lang="ts" name="RuleChains">
import {defineComponent, reactive, ref} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {getBasicColumns, getFormConfig} from './tableData';
import {deleteflows, flowsList,} from '@/api/device/rule-chains';
import {useGo} from '@/hooks/web/usePage';
import {Button, PopConfirmButton} from '@/components/Button';
import {useMessage} from '@/hooks/web/useMessage';
import Modal from './model.vue';
import {useDrawer} from '@/components/Drawer';
import Drawer from './drawer.vue';
import {Tabs, Tag} from 'ant-design-vue';
import RulechainCardList from '@/views/rulechains/components/CardList/RulechainCardList.vue';
import {isNodeRedDemoFlow} from '@/utils/noderedDemo';

export default defineComponent({
  name: 'RuleChains',
  methods: {flowsList},
  components: {
    RulechainCardList,
    BasicTable,
    TableAction,
    Button,
    PopConfirmButton,
    Modal,
    Drawer,
    Tag,
    Tabs,
    TabPane: Tabs.TabPane,
  },
  setup() {
    const checkedKeys = ref<Array<string | number>>([]);
    const go = useGo();
    const {createMessage} = useMessage();
    const [registerModel, {openDrawer: openModal}] = useDrawer();
    const [registerDrawer, {openDrawer: openDrawer}] = useDrawer();

    const state = reactive({
      isTableMode: false,
      activeKey: 'list',
    });

    const params = {};
    let cardListReload = () => {
    };

    function getMethod(m: any) {
      cardListReload = m;
    }

    function handleView(record) {
      openDrawer(true, {
        data: record.label,
        id: record.id,
      });
    }

    function handleEdit(record) {
      openTargetModal('edit', record);
      cardListReload();
    }

    function handleDel(record) {
      handleDelete(record);
    }

    function handleClickSwap() {
      state.isTableMode = !state.isTableMode;
    }

    const [registerTable, {getForm, reload}] = useTable({
      title: '链式规则列表',
      api: flowsList,
      beforeFetch: (data) => {
        console.log('-------', data);
        let params = {
          page: data.page,
          pageSize: data.pageSize,
          sortOrder: data.order == 'ascend' ? 'ASC' : 'DESC',
          sortProperty: data.field == 'rootx' ? 'root' : data.field,
          type: 'CORE',
          textSearch: data.textSearch,
        };

        return params;
      },
      afterFetch: (data) => {
        let list = [];
        data.forEach((element) => {
          if (element.type == 'tab') {
            list.push(element);
          }
        });
        console.log('-------！', list);
        return list;
      },
      defSort: {
        field: 'createdTime',
        order: 'DESC',
      },
      columns: getBasicColumns(),
      useSearchForm: true,
      formConfig: getFormConfig(),
      showTableSetting: false,
      tableSetting: {fullScreen: true},
      showIndexColumn: false,
      rowKey: 'id',
      pagination: {
        defaultPageSize: 20,
        pageSizeOptions: ['1', '10'],
      },
      fetchSetting: {
        listField: 'data',
        totalField: 'total',
      },
      rowSelection: {
        type: 'checkbox',
        selectedRowKeys: checkedKeys,
        onSelect: onSelect,
        onSelectAll: onSelectAll,
        getCheckboxProps(record) {
          if (record.root || isNodeRedDemoFlow(record)) {
            return {disabled: true};
          } else {
            return {disabled: false};
          }
        },
      },
      actionColumn: {
        width: 200,
        title: '操作',
        dataIndex: 'action',
        fixed: 'right',
      },
    });

    function getFormValues() {
      console.log(getForm().getFieldsValue());
    }

    function openTargetModal(type: string, data?: any) {
      if (type === 'edit' && isNodeRedDemoFlow(data)) {
        createMessage.warning('EasyAIoT 演示规则链为只读，禁止修改');
        return;
      }
      openModal(true, {
        data,
        info: type,
        isEdit: type === 'edit',
      });
    }

    function onSelect(record, selected) {
      if (selected) {
        checkedKeys.value = [...checkedKeys.value, record.id];
      } else {
        checkedKeys.value = checkedKeys.value.filter((id) => id !== record.id);
      }
      console.log(checkedKeys);
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
      console.log(checkedKeys);
    }

    async function handleDelete(record) {
      if (!record || !record.id || record.id === 'undefined') {
        createMessage.error('规则链ID无效！');
        return;
      }
      if (isNodeRedDemoFlow(record)) {
        createMessage.warning('EasyAIoT 演示规则链为只读，禁止删除');
        return;
      }
      try {
        await deleteflows(record.id);
        createMessage.success('删除成功！');
        reload();
        cardListReload();
      } catch (error: any) {
        console.error(error);
        createMessage.error(error?.message || '删除失败！');
      }
    }

    function handleOpen(record) {
      openDrawer(true, {
        data: record.label,
        id: record.id,
      });
    }

    async function deleteAll() {
      if (!checkedKeys.value || checkedKeys.value.length === 0) {
        createMessage.warning('请选择要删除的规则链！');
        return;
      }
      const validKeys = checkedKeys.value.filter((item) => item && item !== 'undefined');
      if (validKeys.length === 0) {
        createMessage.error('没有有效的规则链ID！');
        return;
      }
      const deletableKeys = validKeys.filter((item) => !isNodeRedDemoFlow({id: String(item)}));
      if (deletableKeys.length === 0) {
        createMessage.warning('所选均为演示规则链，禁止删除');
        return;
      }
      if (deletableKeys.length < validKeys.length) {
        createMessage.warning('已跳过演示规则链，仅删除可编辑项');
      }
      try {
        await Promise.all([...deletableKeys.map((item) => deleteflows(item + ''))]);
        createMessage.success('删除成功！');
        reload({
          page: 0,
        });
        cardListReload();
      } catch (error: any) {
        console.error(error);
        createMessage.error(error?.message || '删除失败！');
      }
    }

    function rowClickTable(record) {
      if (!record || !record.id) {
        createMessage.error('规则链信息无效！');
        return;
      }
      const nodeRedPath = '/dev-api/nodeRed/#flow/';
      const title = isNodeRedDemoFlow(record)
        ? `EasyAIoT · ${record.label || '演示规则链'}`
        : (record.label || 'EasyAIoT');
      go({
        path: `/rulechains/index/${encodeURIComponent(title)}`,
        query: {code: record.id, path: nodeRedPath, title},
      });
    }

    function handleSuccess() {
      reload({
        page: 0,
      });
      cardListReload();
    }

    return {
      state,
      params,
      getMethod,
      handleView,
      handleEdit,
      handleDel,
      handleClickSwap,
      registerTable,
      getFormValues,
      checkedKeys,
      onSelect,
      onSelectAll,
      handleDelete,
      handleOpen,
      rowClickTable,
      deleteAll,
      registerModel,
      openTargetModal,
      handleSuccess,
      registerDrawer,
      flowsList,
      isNodeRedDemoFlow,
    };
  },
});
</script>

<style lang="less" scoped>
:deep(.iot-basic-table-action.left) {
  justify-content: center;
}

.device-wrapper {
  padding: 0;
  box-sizing: border-box;
  min-height: calc(100vh - 88px);
  background: #ffffff;

  .page-content-card {
    background: #fff;
    border-radius: 0;
    overflow: hidden;
  }

  .device-tab {
    :deep(.ant-tabs-nav) {
      padding: 5px 0 0 25px;
      margin-bottom: 0;
    }

    :deep(.ant-tabs) {
      background-color: #fff;
    }
  }

  .device-list-pane {
    min-height: calc(100vh - 200px);
  }

  .device-card-wrap {
    min-height: calc(100vh - 200px);
    background: #fff;
    display: flex;
    flex-direction: column;
  }

  :deep(.ant-form-item) {
    margin-bottom: 10px;
  }

  :deep(.iot-basic-table-form-container) {
    padding: 0;
    background: #fff;

    .ant-form {
      margin-bottom: 0;
      border-radius: 0;
      background: transparent;
      padding: 16px 16px 0;
    }
  }

  :deep(.ant-table-wrapper) {
    border-radius: 0;
    background: #fff;
    padding: 8px 16px 16px;
  }
}
</style>
