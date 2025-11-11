<template>
  <div>
    <BasicTable @register="registerTable" v-if="state.isTableMode">
      <template #form-custom></template>
      <template #toolbar>
        <a-button type="primary" @click="openTargetModal('add')" preIcon="ant-design:plus-outlined">新增规则</a-button>
         <a-button type="default" @click="openTargetModal('import')" preIcon="ant-design:plus-outlined">导入规则</a-button>
        <a-button type="default" @click="handleClickSwap"
                  preIcon="ant-design:swap-outlined">切换视图
        </a-button>
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
                // label: '导出规则链',
                tooltip: {
                  title: '详情',
                  placement: 'top',
                },
                icon: 'ant-design:eye-filled',
                onClick: handleOpen.bind(null, record),
              },
              {
                // label: '导出规则链',
                tooltip: {
                  title: '编辑',
                  placement: 'top',
                },
                icon: 'ant-design:edit-filled',
                onClick: () => openTargetModal('edit', record),
              },
              {
                // label: '导出规则链',
                tooltip: {
                  title: '编辑规则链',
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
              },
            ]"
            :dropDownActions="[
              // {
              //   label: '规则链详情',
              //   icon: 'material-symbols:edit',
              //   onClick: handleOpen.bind(null, record),
              // },
            ]"
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
    <div v-else>
      <RulechainCardList :params="params" :api="flowsList" @get-method="getMethod"
                         @delete="handleDel" @edit="handleEdit" @view="handleView" @go="rowClickTable">
        <template #header>
          <a-button type="primary" @click="openTargetModal('add')"
                    preIcon="ant-design:plus-outlined">
            新增规则
          </a-button>
          <a-button type="default" @click="openTargetModal('import')"
                    preIcon="ant-design:plus-outlined">
            导入规则
          </a-button>
          <a-button type="default" @click="handleClickSwap"
                    preIcon="ant-design:swap-outlined">切换视图
          </a-button>
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
</template>
<script lang="ts" name="RuleChains">
import {defineComponent, reactive, ref} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {getBasicColumns, getFormConfig} from './tableData';
// import moment from 'moment';
import {deleteflows, flowsList,} from '@/api/device/rule-chains';
import {useGo} from '@/hooks/web/usePage';
import {PopConfirmButton} from '@/components/Button';
import {useMessage} from '@/hooks/web/useMessage';
import {useModal} from '@/components/Modal';
import Modal from './model.vue';
import {useDrawer} from '@/components/Drawer';
import Drawer from './drawer.vue';
import {Tag} from 'ant-design-vue';
import ProductCardList from "@/views/product/components/CardList/ProductCardList.vue";
import RulechainCardList from "@/views/rulechains/components/CardList/RulechainCardList.vue";

export default defineComponent({
  name: "RuleChains",
  methods: {flowsList},
  components: {
    RulechainCardList,
    ProductCardList, BasicTable, TableAction, PopConfirmButton, Modal, Drawer, Tag
  },
  setup() {
    const checkedKeys = ref<Array<string | number>>([]);
    const go = useGo();
    const {createMessage} = useMessage();
    const [registerModel, {openModal: openModal}] = useModal();
    const [registerDrawer, {openDrawer: openDrawer}] = useDrawer();

    const state = reactive({
      isTableMode: false,
    });

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
      openDrawer(true, {
        data: record.label,
        id: record.id,
      });
    }

    //编辑按钮事件
    function handleEdit(record) {
      openTargetModal('edit', record)
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

    const [registerTable, {getForm, reload}] = useTable({
      title: '链式规则列表',
      api: flowsList,
      beforeFetch: (data) => {
        // 接口请求前 参数处理
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
          // Demo: 第一行（id为0）的选择框禁用
          if (record.root) {
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
      try {
        await deleteflows(record.id);
        createMessage.success('删除成功！');
        reload();
        cardListReload();
      }catch (error) {
    console.error(error)
        console.log(error);
        createMessage.error('删除失败！');
      }
    }

    function handleOpen(record) {
      openDrawer(true, {
        data: record.label,
        id: record.id,
      });
    }

    async function deleteAll() {
      try {
        await Promise.all([...checkedKeys.value.map((item) => deleteflows(item + ''))]);
        createMessage.success('删除成功！');
      }catch (error) {
    console.error(error)
        console.log(error);
        createMessage.error('删除失败！');
      }
      reload({
        page: 0,
      });
      cardListReload();
    }

    //http://127.0.0.1:1880/#flow/
    function rowClickTable(record) {
      go({
        path: `/rulechains/index/${record.label} - 规则链`,
        query: {code: record.id, path: "//localhost:1880/#flow/"}
      });
    }

    function handleSuccess() {
      reload({
        page: 0,
      });
      cardListReload();
    }

    return {
      state, params, getMethod, handleView, handleEdit, handleDel, handleClickSwap,
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
    };
  },
});
</script>
