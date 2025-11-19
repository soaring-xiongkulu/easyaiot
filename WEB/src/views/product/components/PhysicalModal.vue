<template>
  <div class="phsyical-modal">
    <!-- 标题栏和视图切换 -->
    <div class="modal-header">
      <PhysicalModalTitle
        v-model:isEdit="isEdit"
        @add-phsyical="handleEdit('add')"
        @reload="reload"
        @release="handleRelease"
        @update:function-type="updateFunctionType"
      />
      <div class="view-switch">
        <ButtonGroup>
          <Button
            :type="viewMode === 'table' ? 'primary' : 'default'"
            @click="viewMode = 'table'"
          >
            <template #icon>
              <Icon icon="ant-design:table-outlined" />
            </template>
            表格
          </Button>
          <Button
            :type="viewMode === 'card' ? 'primary' : 'default'"
            @click="viewMode = 'card'"
          >
            <template #icon>
              <Icon icon="ant-design:appstore-outlined" />
            </template>
            卡片
          </Button>
        </ButtonGroup>
      </div>
    </div>

    <!-- 表格视图 -->
    <div v-show="viewMode === 'table'" class="table-view">
      <BasicTable @register="registerTable">
        <template #action="{ record }">
          <TableAction :actions="actionsBtn(record)" />
        </template>
      </BasicTable>
    </div>

    <!-- 卡片视图 -->
    <div v-show="viewMode === 'card'" class="card-view">
      <!-- 搜索表单 -->
      <div class="card-search-form">
        <BasicTable @register="registerTable" />
      </div>
      <div class="card-container">
        <div v-if="cardData.length === 0" class="empty-state">
          <Empty description="暂无数据" />
        </div>
        <div v-else class="card-grid">
          <Card
            v-for="record in cardData"
            :key="record.id"
            class="model-card"
            :hoverable="true"
          >
            <template #title>
              <div class="card-title">
                <span class="title-text">{{ getCardTitle(record) }}</span>
                <Tag
                  v-if="record.templateIdentification"
                  color="green"
                  class="standard-tag"
                >
                  标准
                </Tag>
                <Tag v-else color="red" class="standard-tag">自定义</Tag>
              </div>
            </template>
            <div class="card-content">
              <div class="card-item" v-for="item in getCardFields(record)" :key="item.key">
                <span class="item-label">{{ item.label }}：</span>
                <span class="item-value">{{ item.value }}</span>
              </div>
            </div>
            <template #actions>
              <div class="card-actions">
                <TableAction :actions="actionsBtn(record)" />
              </div>
            </template>
          </Card>
        </div>
      </div>
      <!-- 卡片视图分页 -->
      <div v-if="cardData.length > 0" class="card-pagination">
        <Pagination
          v-model:current="pagination.current"
          v-model:pageSize="pagination.pageSize"
          :total="pagination.total"
          :showSizeChanger="true"
          :showTotal="(total) => `共 ${total} 条`"
          @change="handlePageChange"
          @showSizeChange="handlePageSizeChange"
        />
      </div>
    </div>

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

<script lang="ts" setup name="PhysicalModal">
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {getBasicColumns, getFormConfig} from '../data/ProductData';
import PhysicalModalTitle from './PhysicalModalTitle.vue';
import {useModal} from '@/components/Modal';
import Edit from './Edit.vue';
import {onMounted, reactive, ref, withDefaults, watch} from 'vue';
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
import {Button, ButtonGroup, Card, Tag, Empty, Pagination} from 'ant-design-vue';
import {Icon} from '@/components/Icon';

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
  // 视图模式：table 或 card
  const viewMode = ref<'table' | 'card'>('card');
  // 卡片数据
  const cardData = ref<any[]>([]);
  // 分页信息
  const pagination = reactive({
    current: 1,
    pageSize: 12,
    total: 0,
  });

  const [registerTable, { reload, setColumns, getDataSource, getPaginationRef }] = useTable({
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
    afterFetch: (data) => {
      // 更新卡片数据
      cardData.value = data || [];
      const paginationInfo = getPaginationRef();
      if (paginationInfo && typeof paginationInfo === 'object') {
        pagination.total = paginationInfo.total || 0;
        pagination.current = paginationInfo.current || 1;
        pagination.pageSize = paginationInfo.pageSize || 12;
      }
      return data;
    },
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
    pagination.current = 1;
    reload();
  }

  // 获取卡片标题
  const getCardTitle = (record: any) => {
    if (state.functionType === 'properties') {
      return record.propertyName || record.propertyCode || '--';
    } else if (state.functionType === 'services') {
      return record.serviceName || record.serviceCode || '--';
    } else if (state.functionType === 'events') {
      return record.eventName || record.eventCode || '--';
    }
    return '--';
  }

  // 获取卡片字段
  const getCardFields = (record: any) => {
    const fields: Array<{ key: string; label: string; value: any }> = [];
    
    if (state.functionType === 'properties') {
      fields.push(
        { key: 'propertyCode', label: '属性标识', value: record.propertyCode || '--' },
        { key: 'datatype', label: '数据类型', value: formatDataType(record.datatype) },
      );
      if (record.description) {
        fields.push({ key: 'description', label: '描述', value: record.description });
      }
    } else if (state.functionType === 'services') {
      fields.push(
        { key: 'serviceCode', label: '服务标识', value: record.serviceCode || '--' },
      );
      if (record.description) {
        fields.push({ key: 'description', label: '描述', value: record.description });
      }
    } else if (state.functionType === 'events') {
      fields.push(
        { key: 'eventCode', label: '事件标识', value: record.eventCode || '--' },
        { key: 'eventType', label: '事件类型', value: formatEventType(record.eventType) },
      );
    }
    
    return fields;
  }

  // 格式化数据类型
  const formatDataType = (text: string) => {
    if (text === 'TEXT' || text === 'string' || text === 'String' || text === 'text') {
      return 'text（字符串）';
    } else if (text === 'INT' || text === 'int' || text === 'Int' || text === 'int32') {
      return 'int32（整数型）';
    } else if (text === 'DOUBLE' || text === 'double' || text === 'Double') {
      return 'double（双精度浮点型）';
    } else if (text === 'BOOL' || text === 'bool' || text === 'Bool' || text === 'boolean' || text === 'Boolean') {
      return 'bool（布尔型）';
    } else if (text === 'SUBUCT' || text === 'struct' || text === 'Struct') {
      return 'struct（结构体）';
    }
    return text || '--';
  }

  // 格式化事件类型
  const formatEventType = (text: string) => {
    if (text === 'INFO_EVENT_TYPE') {
      return '信息';
    } else if (text === 'ALERT_EVENT_TYPE') {
      return '告警';
    } else if (text === 'ERROR_EVENT_TYPE') {
      return '故障';
    }
    return text || '--';
  }

  // 页面变化处理
  const handlePageChange = (page: number, pageSize: number) => {
    pagination.current = page;
    pagination.pageSize = pageSize;
    reload();
  }

  // 页面大小变化处理
  const handlePageSizeChange = (current: number, size: number) => {
    pagination.current = current;
    pagination.pageSize = size;
    reload();
  }

  // 监听视图模式变化，加载卡片数据
  watch(viewMode, (newMode) => {
    if (newMode === 'card') {
      // 延迟获取数据，确保表格已加载
      setTimeout(() => {
        const data = getDataSource();
        cardData.value = data || [];
        const paginationInfo = getPaginationRef();
        if (paginationInfo && typeof paginationInfo === 'object') {
          pagination.total = paginationInfo.total || 0;
          pagination.current = paginationInfo.current || 1;
          pagination.pageSize = paginationInfo.pageSize || 12;
        }
      }, 100);
    }
  }, { immediate: true });

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
  .phsyical-modal {
    background-color: transparent;
    padding: 0;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0;
      gap: 16px;

      .view-switch {
        flex-shrink: 0;
        margin-top: 8px;

        :deep(.ant-btn) {
          font-size: 13px;
          height: 32px;
          padding: 4px 15px;
        }
      }
    }

    .table-view {
      flex: 1;
      overflow: hidden;
      display: flex;
      flex-direction: column;

      :deep(.vben-basic-table-form-container) {
        padding: 12px 16px;
        background: #fafafa;
        border-radius: 8px;
        margin-bottom: 12px;
      }

      :deep(.ant-table) {
        font-size: 13px;

        .ant-table-thead > tr > th {
          font-size: 13px;
          font-weight: 600;
          color: #333;
          padding: 12px 16px;
          background: #fafafa;
        }

        .ant-table-tbody > tr > td {
          font-size: 13px;
          padding: 12px 16px;
          color: #666;
        }

        .ant-table-tbody > tr:hover > td {
          background: #f5f7fa;
        }
      }
    }

    .card-view {
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;

      .card-search-form {
        margin-bottom: 0;
        flex-shrink: 0;
        
        :deep(.vben-basic-table-form-container) {
          padding: 8px 16px;
          background: #fafafa;
          border-radius: 8px;
        }

        // 隐藏表格，只显示搜索表单
        :deep(.ant-table-wrapper) {
          display: none;
        }

        :deep(.ant-pagination) {
          display: none;
        }
      }

      .card-container {
        flex: 1;
        overflow-y: auto;
        overflow-x: hidden;
        min-height: 0;

        :deep(.ant-tabs) {
          margin-bottom: 0;
          background-color: #ffffff;

          .ant-tabs-nav {
            margin-bottom: 0;
          }

          .ant-tabs-tab {
            font-size: 13px;
            padding: 8px 16px;
          }

          .ant-tabs-content-holder {
            display: none;
          }
        }
        
        // 自定义滚动条样式
        &::-webkit-scrollbar {
          width: 6px;
        }

        &::-webkit-scrollbar-track {
          background: #f5f5f5;
          border-radius: 3px;
        }

        &::-webkit-scrollbar-thumb {
          background: #d9d9d9;
          border-radius: 3px;
          
          &:hover {
            background: #bfbfbf;
          }
        }
      }

      .empty-state {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
        min-height: 300px;
        background: #ffffff;
        border-radius: 8px;
      }

      .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 12px;
        padding-bottom: 4px;

        .model-card {
          border-radius: 10px;
          background: 
            linear-gradient(135deg, #ffffff 0%, #fafbfc 100%),
            radial-gradient(circle at top right, rgba(24, 144, 255, 0.03) 0%, transparent 50%);
          box-shadow: 
            0 0.5px 2px rgba(0, 0, 0, 0.03),
            0 2px 8px rgba(0, 0, 0, 0.05),
            0 0 0 0.5px rgba(0, 0, 0, 0.015),
            inset 0 1px 0 rgba(255, 255, 255, 0.8);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          border: 0.5px solid rgba(0, 0, 0, 0.06);
          position: relative;
          overflow: hidden;
          backdrop-filter: blur(10px);

          &::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #1890ff 0%, #40a9ff 50%, #69c0ff 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
            box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
          }

          &::after {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(24, 144, 255, 0.05) 0%, transparent 70%);
            opacity: 0;
            transition: opacity 0.4s ease;
            pointer-events: none;
          }

          &:hover {
            box-shadow: 
              0 2px 8px rgba(0, 0, 0, 0.06),
              0 6px 20px rgba(0, 0, 0, 0.08),
              0 0 0 1px rgba(24, 144, 255, 0.15),
              inset 0 1px 0 rgba(255, 255, 255, 0.9);
            transform: translateY(-3px) scale(1.01);
            border-color: rgba(24, 144, 255, 0.25);
            background: 
              linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%),
              radial-gradient(circle at top right, rgba(24, 144, 255, 0.08) 0%, transparent 50%);

            &::before {
              opacity: 1;
            }

            &::after {
              opacity: 1;
            }
          }

          :deep(.ant-card-head) {
            border-bottom: 0.5px solid rgba(0, 0, 0, 0.05);
            padding: 12px 14px;
            min-height: 44px;
            background: linear-gradient(to bottom, rgba(250, 251, 252, 0.6), transparent);

            .ant-card-head-title {
              padding: 0;
            }
          }

          :deep(.ant-card-body) {
            padding: 14px;
            background: transparent;
          }

          :deep(.ant-card-actions) {
            border-top: 0.5px solid rgba(0, 0, 0, 0.05);
            background: linear-gradient(to top, rgba(250, 251, 252, 0.4), transparent);
            padding: 8px 0;
            margin: 0;
          }

          .card-title {
            display: flex;
            align-items: center;
            gap: 8px;

            .title-text {
              font-size: 13px;
              font-weight: 600;
              color: #1a1a1a;
              flex: 1;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
              letter-spacing: 0.1px;
              line-height: 1.4;
            }

            .standard-tag {
              flex-shrink: 0;
              font-size: 11px;
              margin: 0;
              border-radius: 3px;
              padding: 1px 6px;
              font-weight: 500;
              line-height: 1.5;
            }
          }

          .card-content {
            .card-item {
              display: flex;
              margin-bottom: 10px;
              font-size: 12px;
              line-height: 1.6;
              padding: 6px 0;
              border-bottom: 0.5px solid rgba(0, 0, 0, 0.03);
              transition: all 0.2s ease;

              &:last-child {
                margin-bottom: 0;
                border-bottom: none;
              }

              &:hover {
                background: rgba(24, 144, 255, 0.03);
                border-radius: 4px;
                padding-left: 6px;
                padding-right: 6px;
                margin-left: -6px;
                margin-right: -6px;
              }

              .item-label {
                color: #666;
                font-weight: 500;
                min-width: 75px;
                flex-shrink: 0;
                letter-spacing: 0.05px;
                font-size: 12px;
              }

              .item-value {
                color: #1a1a1a;
                font-weight: 600;
                flex: 1;
                word-break: break-word;
                letter-spacing: 0.05px;
                font-size: 12px;
              }
            }
          }

          .card-actions {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 0 8px;
          }
        }
      }

      .card-pagination {
        display: flex;
        justify-content: flex-end;
        padding: 4px 0;
        flex-shrink: 0;
        margin-top: 0;

        :deep(.ant-pagination) {
          font-size: 13px;
        }
      }
    }

    :deep(.ant-btn) {
      font-size: 13px;
      height: 32px;
      padding: 4px 15px;
    }

    :deep(.ant-btn-sm) {
      font-size: 12px;
      height: 28px;
      padding: 2px 12px;
    }

    :deep(.ant-input),
    :deep(.ant-select-selector),
    :deep(.ant-picker) {
      font-size: 13px;
    }

    :deep(.ant-form-item-label > label) {
      font-size: 13px;
      font-weight: 500;
      color: #333;
    }

    :deep(.ant-alert) {
      font-size: 13px;
      padding: 10px 16px;
      margin-bottom: 16px;
    }

    :deep(.ant-space-item) {
      font-size: 13px;
    }
  }
</style>
