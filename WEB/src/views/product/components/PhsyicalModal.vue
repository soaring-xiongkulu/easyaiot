<template>
  <div class="phsyical-modal">
    <!-- 物理模型管理 -->
    <BasicTable @register="registerTable">
      <template #tableTitle>
        <PhsyicalModalTitle
          v-model:isEdit="isEdit"
          @add-phsyical="handleEdit('add')"
          @reload="reload"
          @release="handleRelease"
          @update:function-type="updateFunctionType"
        />
      </template>
      <template #action="{ record }">
        <TableAction :actions="actionsBtn(record)" />
      </template>
    </BasicTable>

    <!-- 新增、编辑、查看物模型弹窗 -->
    <Edit
      :title="state.editModelTitle"
      :productIdentification="props.productIdentification"
      @register="registerEditModal"
      @submit="handleSubmit"
      @update:edit-function-type="updateEditFunctionType"
    />
  </div>
</template>

<script lang="ts" setup name="PhsyicalModal">
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {getBasicColumns, getFormConfig} from '../data/ProductData';
import PhsyicalModalTitle from './PhsyicalModalTitle.vue';
import {useModal} from '@/components/Modal';
import Edit from './Edit.vue';
import {onMounted, reactive, ref, withDefaults} from 'vue';
import {
  delPhsyicalEvent,
  delPhsyicalProperties,
  delPhsyicalService,
  getEventsList,
  getPropertiesList,
  getServicesList,
  releasePhsyical,
  savePhsyicalEvent, savePhsyicalEventResponse,
  savePhsyicalProperties,
  savePhsyicalService,
  updatePhsyicalEvent, updatePhsyicalEventResponse,
  updatePhsyicalProperties,
  updatePhsyicalService,
} from '@/api/device/phsyicalModal';
import {useMessage} from '@/hooks/web/useMessage';

interface Props {
    productIdentification: string;
    deviceProfileName: string;
    templateIdentification: string;
  }

  const props = withDefaults(defineProps<Props>(), {
    productIdentification: '',
    deviceProfileName: '',
    templateIdentification: '',
  });

  const state = reactive({
    functionType : 'properties',
    editFunctionType : 'properties',
    editModelTitle: '物模型',
  });

  const { createMessage } = useMessage();
  // 是否处理编辑物模型
  const isEdit = ref(false);

  const [registerTable, { reload, setColumns }] = useTable({
    canResize: true,
    showIndexColumn: false,
    columns: getBasicColumns('properties'),
    useSearchForm: true,
    formConfig: getFormConfig(),
    rowKey: 'id',
    actionColumn: {
      width: 100,
      title: '操作',
      dataIndex: 'action',
      slots: { customRender: 'action' },
    },
    api: getPropertiesList,
    beforeFetch(params) {
      return {
        ...params,
        productIdentification: props.productIdentification,
        templateIdentification: props.templateIdentification,
        customApi: state.functionType == 'properties' ? getPropertiesList : state.functionType == 'services' ? getServicesList : getEventsList,
      };
    },
    fetchSetting: {
      listField: 'data',
      totalField: 'total',
    },
    pagination: true,
  });

  const [registerEditModal, { openModal: openEditModal }] = useModal();
  const actionsBtn = (record: { id: string }) => {
    if (isEdit.value) {
      return [
        {
          tooltip: {
            title: '编辑',
            placement: 'top',
          },
          icon: 'ant-design:edit-filled',
          onClick: () => {
            state.editModelTitle = '编辑物模型' + (state.functionType == 'properties'?'属性':state.functionType == 'services'?'服务':'事件')
            handleEdit('edit', record);
          },
        },
        {
          tooltip: {
            title: '删除',
            placement: 'top',
          },
          icon: 'material-symbols:delete-outline-rounded',

          popConfirm: {
            title: '是否确认删除？',
            confirm: () => {
              if(state.functionType == 'properties') {
                delPhsyicalProperties(record.id).then(() => {
                  createMessage.success('删除成功');
                  reload();
                });
              } else if(state.functionType == 'services'){
                delPhsyicalService(record.id).then(() => {
                  createMessage.success('删除成功');
                  reload();
                });
              } else if(state.functionType == 'events'){
                delPhsyicalEvent(record.id).then(() => {
                  createMessage.success('删除成功');
                  reload();
                });
              }
            },
          },
        },
      ];
    } else {
      return [
        {
          tooltip: {
            title: '查看',
            placement: 'top',
          },
          icon: 'ant-design:eye-outlined',
          onClick: () => {
            state.editModelTitle = '查看物模型' + (state.functionType == 'properties'?'属性':state.functionType == 'services'?'服务':'事件')
            handleEdit('view', record)
          },
        },
      ];
    }
  };

  //更新物模型功能类型
  const updateFunctionType = (type) => {
    state.functionType = type;
    setColumns(getBasicColumns(state.functionType ?? 'properties'));
    reload();
  }

  //更新物模型编辑功能类型
  const updateEditFunctionType = (type) => {
    state.editFunctionType = type;
  }

  // 新增物模型
  const handleEdit = (modalType: 'add' | 'edit' | 'view', record?: any) => {
    let params = record ?? {};
    params.functionType = state.functionType ?? 'properties';
    if (record) {
      const functionJson =
        typeof record?.functionJson === 'string'
          ? JSON.parse(record.functionJson)
          : record?.functionJson ?? '';
      params = {
        ...functionJson,
        ...params,
      };
    }
    // alert(JSON.stringify(params));
    openEditModal(true, { modalType, ...params });
  };

  // 保存物模型数据到列表
  const handleSubmit = (res) => {
    const { id, datatype, functionJson } = res;
    let text = '新增';
    let enumlist = "";
    if(datatype == 'BOOL') {
      let tmp = {};
      tmp['0'] = functionJson['boolClose'];
      tmp['1'] = functionJson['boolOpen'];
      enumlist = JSON.stringify(tmp);
    }
    let maxlength = "";
    if(datatype == 'TEXT') {
      if(functionJson['maxlength'] == null || functionJson['maxlength'] == undefined) {
        maxlength = '10240';
      } else {
        maxlength = functionJson['maxlength'];
      }
    }
    const params = {
      ...res,
      ...functionJson,
      enumlist: enumlist,
      maxlength: maxlength,
      productIdentification: props.productIdentification,
    };
    delete params.functionJson;
    if (id) {
      params.id = id;
      text = '修改';
      if(state.editFunctionType == 'properties') {
        updatePhsyicalProperties(params).then(() => {
          reload();
          createMessage.success(`${text}成功`);
        });
      } else if(state.editFunctionType == 'services'){
        updatePhsyicalService(params).then(() => {
          reload();
          createMessage.success(`${text}成功`);
        });
      } else if(state.editFunctionType == 'events') {
        updatePhsyicalEvent(params).then(() => {
          reload();
          createMessage.success(`${text}成功`);
        });
      }
    } else {
      delete params.id;
      if(state.editFunctionType == 'properties') {
        savePhsyicalProperties(params).then(() => {
          reload();
          createMessage.success(`${text}成功`);
        });
      } else if(state.editFunctionType == 'services'){
        savePhsyicalService(params).then(() => {
          reload();
          createMessage.success(`${text}成功`);
        });
      } else if(state.editFunctionType == 'events') {
        savePhsyicalEvent(params).then(() => {
          reload();
          createMessage.success(`${text}成功`);
        });
      }
    }
  };

  // 发布上线
  const handleRelease = () => {
    releasePhsyical(props.productIdentification).then(() => {
      createMessage.success('发布成功');
      reload();
      isEdit.value = false;
    });
  };

  const handleFormatTsl = (obj) => {
    const { name, identifier, datatype, functionJson, functionType, eventType } = obj;

    const { callType, innerJson, accessMode, inputParams, outParams } = functionJson ?? {};

    switch (functionType) {
      case 'properties':
        return {
          functionName: name,
          identifier,
          datatype,
          readWrite: accessMode ?? null,
          specs: {
            type: datatype,
            specs: innerJson.map((e) => {
              return {
                ...handleFormatTsl({ functionType, ...e }),
                accessMode: accessMode ?? null,
              };
            }),
          },
        };
      case 'services':
        return {
          functionName: name,
          identifier,
          callType,
          inputData: inputParams?.map((e) => {
            return {
              ...handleFormatTsl({ functionType, ...e }),
              accessMode: e.accessMode ?? null,
              datatype: {
                type: e.datatype,
                specs: e.innerJson?.map((v) => {
                  return {
                    ...handleFormatTsl({ functionType, ...v }),
                    accessMode: v.accessMode ?? null,
                  };
                }),
              },
            };
          }),
          outData: outParams?.map((e) => {
            return {
              ...handleFormatTsl({ functionType, ...e }),
              accessMode: e.accessMode ?? null,
              datatype: {
                type: e.datatype,
                specs: e.innerJson?.map((v) => {
                  return {
                    ...handleFormatTsl({ functionType, ...v }),
                    accessMode: v.accessMode ?? null,
                  };
                }),
              },
            };
          }),
        };

      case 'events':
        return {
          functionName: name,
          identifier,
          eventType: eventType ?? null,
          outputData: outParams?.map((e) => {
            return {
              ...handleFormatTsl({ functionType, ...e }),
              accessMode: e.accessMode ?? null,
              datatype: {
                type: e.datatype,
                specs: e.innerJson?.map((v) => {
                  return {
                    ...handleFormatTsl({ functionType, ...v }),
                    accessMode: v.accessMode ?? null,
                  };
                }),
              },
            };
          }),
        };
      default:
        return obj;
    }
  };
  onMounted(() => {});
</script>

<style lang="less" scoped>
  :deep(.vben-basic-table-form-container) {
    padding: 10px;
  }
  .phsyical-modal {
    background-color: #FFFFFF;
  }
</style>
