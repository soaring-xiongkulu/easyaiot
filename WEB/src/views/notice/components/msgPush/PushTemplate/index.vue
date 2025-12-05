<template>
  <div>
    <BasicTable @register="registerTable">
      <template #toolbar>
        <a-button type="primary" @click="openConfigModal(true, { type: 'add', pushType })"
          >新增推送</a-button
        >
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
                onClick: openConfigModal.bind(null, true, { type: 'edit', record, pushType }),
              },

              {
                tooltip: {
                  title: '开始推送',
                  placement: 'top',
                },
                icon: 'ion:push',
                onClick: handleStartPush.bind(null, record),
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
    <!-- 新增/编辑配置 -->
    <ConfigModal @register="registerConfigModal" @success="reload" />
    <!-- drawer -->
    <DetailDrawer @register="registerDetailDrawer" />
    <!-- 计划推送 -->
    <PlanModal @register="registerPlanModal" />
  </div>
</template>
<script lang="ts" setup name="PushTemplate">
  import { onMounted } from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { useModal } from '/@/components/Modal';
  import { useDrawer } from '@/components/Drawer';
  import PlanModal from './components/PlanModal.vue';
  // import { getFormConfig } from './Data';
  import ConfigModal from './components/ConfigModal.vue';
  import DetailDrawer from './components/DetailDrawer.vue';
  import { messagePrepareQuery, messagePrepareDelete, messageSendByBody, messageSendByParam } from '/@/api/modules/notice';

  defineOptions({name: 'PushTemplate'})

  const props = defineProps({
    pushType: {
      type: String,
      default: 'email',
    },
    columns: {
      type: Array,
      default: () => [],
    },
    searchField: {
      type: Array,
      default: () => [],
    },
  });

  const [registerConfigModal, { openModal: openConfigModal }] = useModal();
  // , { openModal: openPlanModal }
  const [registerPlanModal] = useModal();
  const [registerDetailDrawer, { openDrawer: openDetailDrawer }] = useDrawer();

  const { createMessage } = useMessage();
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
    title: '消息推送',
    api: messagePrepareQuery,
    beforeFetch: (data) => {
      const configKey = {
        sms: 1,
        email: 3,
        weixin: 4,
        http: 5,
        ding: 6,
      };
      let params = {
        ...data,
        msgType: props.pushType == 'sms' ? data.msgType : configKey[props.pushType],
      };
      return params;
    },
    columns: getColumns(),
    useSearchForm: true,
    formConfig: getFormConfig(),
    rowKey: 'id',
    dataSource: [{ name: 'test' }],
    fetchSetting: {
      listField: 'data',
      totalField: 'total',
    },
  });

  function getFormConfig() {
    return {
      labelWidth: 70,
      baseColProps: { span: 6 },
      schemas: [
        ...props.searchField,
        {
          field: `msgName`,
          label: `消息名称`,
          component: 'Input',
        },
      ],
    };
  }

  function getColumns() {
    return [
      {
        title: '消息类型',
        dataIndex: 'msgType',
        customRender: ({ text }) => {
          return {
            1: '阿里云短信',
            2: '腾讯云短信',
            3: 'EMail',
            4: '企业微信',
            5: 'Webhook',
            6: '钉钉',
            7: '飞书',
          }[text];
        },
      },
      {
        title: '消息名称',
        dataIndex: 'msgName',
      },
      {
        title: '用户组',
        dataIndex: 'userGroupName',
        ifShow: () => {
          return props.pushType != 'http';
        },
      },
      ...props.columns,
      {
        width: 230,
        title: '操作',
        dataIndex: 'action',
        fixed: 'right',
      },
    ];
  }

  const handleDelete = async ({ id }) => {
    try {
      const configKey = {
        sms: 1,
        email: 3,
        weixin: 4,
        http: 5,
        ding: 6,
      };
      await messagePrepareDelete({ id, msgType: configKey[props.pushType] });
      createMessage.success('删除成功');
      reload();
    }catch (error) {
    console.error(error)
      createMessage.success('删除失败');
      console.log('handleDelete', error);
    }
  };

  /**
   * 解析 JSON 字符串，如果解析失败则返回空对象或空数组
   */
  const parseJsonSafely = (jsonString, defaultValue = {}) => {
    if (!jsonString || typeof jsonString !== 'string') {
      return defaultValue;
    }
    try {
      const parsed = JSON.parse(jsonString);
      return parsed || defaultValue;
    } catch (error) {
      console.warn('JSON 解析失败:', jsonString, error);
      return defaultValue;
    }
  };

  /**
   * 将参数数组转换为对象
   * 输入: [{name: 'key1', value: 'value1'}, ...]
   * 输出: {key1: 'value1', ...}
   */
  const convertParamsArrayToObject = (paramsArray) => {
    if (!Array.isArray(paramsArray)) {
      return {};
    }
    return paramsArray.reduce((acc, item) => {
      if (item && item.name !== undefined && item.value !== undefined) {
        acc[item.name] = item.value;
      }
      return acc;
    }, {});
  };

  /**
   * 将 Cookie 数组转换为对象
   * 输入: [{name: 'key1', value: 'value1', domain: '', path: '', time: ''}, ...]
   * 输出: {key1: 'value1', ...}
   */
  const convertCookiesArrayToObject = (cookiesArray) => {
    if (!Array.isArray(cookiesArray)) {
      return {};
    }
    return cookiesArray.reduce((acc, item) => {
      if (item && item.name !== undefined && item.value !== undefined) {
        acc[item.name] = item.value;
      }
      return acc;
    }, {});
  };

  const handleStartPush = async (record) => {
    console.log('开始推送，完整 record 数据:', JSON.stringify(record, null, 2));
    
    try {
      // 解析 record 的所有参数
      const {
        id,
        msgType,
        msgId = id, // 兼容 msgId 字段
        msgName,
        method,
        url,
        body,
        bodyType,
        params: paramsJson,
        headers: headersJson,
        cookies: cookiesJson,
        ...otherFields
      } = record;

      // 验证必要参数
      if (!msgType || !msgId) {
        createMessage.error('推送失败：缺少必要参数 msgType 或 msgId');
        return;
      }

      // 解析 params、headers、cookies（从 JSON 字符串转换为对象）
      const paramsArray = parseJsonSafely(paramsJson, []);
      const headersArray = parseJsonSafely(headersJson, []);
      const cookiesArray = parseJsonSafely(cookiesJson, []);

      // 转换为对象格式
      const paramsObj = convertParamsArrayToObject(paramsArray);
      const headersObj = convertParamsArrayToObject(headersArray);
      const cookiesObj = convertCookiesArrayToObject(cookiesArray);

      console.log('解析后的参数:', {
        msgType,
        msgId,
        params: paramsObj,
        headers: headersObj,
        cookies: cookiesObj,
        body,
        bodyType,
        otherFields,
      });

      // 判断是否有 body 和 bodyType，决定使用哪种推送方式
      const hasBody = body && bodyType;
      
      let sendResult = null;

      // 如果有 body 和 bodyType，优先使用 Body 方式
      if (hasBody) {
        try {
          console.log('使用 Body 方式推送（bodyType: ' + bodyType + '）...');
          
          // 将 params、headers、cookies 对象转换为 JSON 字符串，以便后端解析
          const paramsJsonStr = Object.keys(paramsObj).length > 0 ? JSON.stringify(paramsObj) : null;
          const headersJsonStr = Object.keys(headersObj).length > 0 ? JSON.stringify(headersObj) : null;
          const cookiesJsonStr = Object.keys(cookiesObj).length > 0 ? JSON.stringify(
            Object.entries(cookiesObj).map(([name, value]) => ({ name, value, domain: '', path: '', time: '' }))
          ) : null;
          
          // 构建完整的请求数据对象，包含所有 HTTP 相关字段
          // 注意：method 和 url 必须包含在请求中，以便后端判断是否使用新方法
          const requestData: any = {
            msgType: Number(msgType),
            msgId: String(msgId),
            method: method || null,  // HTTP 方法（必须包含，即使为 null）
            url: url || null,        // HTTP URL（必须包含，即使为 null）
            body: body,               // HTTP 请求体
            bodyType: bodyType,       // HTTP 请求体类型
            params: paramsJsonStr,    // HTTP 参数（JSON 字符串）
            headers: headersJsonStr,  // HTTP 请求头（JSON 字符串）
            cookies: cookiesJsonStr,  // HTTP Cookie（JSON 字符串）
            // 包含所有其他字段，以便后端可能需要
            ...otherFields,
          };
          
          console.log('构建的请求数据:', JSON.stringify(requestData, null, 2));

        const ret: any = await messageSendByBody(requestData, headersObj, cookiesObj);
        
        // 由于设置了 isTransformResponse: false，响应是原始的 axios 响应对象
        // 数据在 ret.data 中，可能被包装在 data 字段中，也可能直接是 SendResult
        sendResult = ret['data'];
        if (sendResult && sendResult['data']) {
          // 如果被包装在 data 字段中（统一响应格式）
          sendResult = sendResult['data'];
        }
        
        console.log('Body 方式推送成功:', sendResult);
      } catch (bodyError) {
          console.error('Body 方式推送失败:', bodyError);
          throw bodyError;
        }
      } else {
        // 如果没有 body 和 bodyType，使用 Param 方式
        try {
          console.log('使用 Param 方式推送（无 body 数据）...');
          const ret: any = await messageSendByParam(
            { msgType: Number(msgType), msgId: String(msgId) },
            headersObj,
            cookiesObj
          );
          
          sendResult = ret['data'];
          if (sendResult && sendResult['data']) {
            sendResult = sendResult['data'];
          }
          
          console.log('Param 方式推送成功:', sendResult);
        } catch (paramError) {
          console.error('Param 方式推送失败:', paramError);
          throw paramError;
        }
      }

      // 处理推送结果
      if (sendResult && sendResult.success) {
        createMessage.success('推送成功');
        reload();
      } else {
        const errorMsg = sendResult?.info || sendResult?.message || '推送失败';
        createMessage.error(errorMsg);
      }
    } catch (error) {
      console.error('推送失败:', error);
      const errorMsg = 
        error?.response?.data?.info || 
        error?.response?.data?.message || 
        error?.message || 
        '推送失败';
      createMessage.error(errorMsg);
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
</style>
