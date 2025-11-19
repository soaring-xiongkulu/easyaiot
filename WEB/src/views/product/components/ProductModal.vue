<template>
  <BasicModal
    @register="register"
    :title="getTitle"
    :width="700"
    @cancel="handleCancel"
    @ok="handleOk"
    :canFullscreen="false"
  >
    <div class="product-modal">
      <Spin :spinning="state.editLoading">
        <Form
          :labelCol="{ span: 6 }"
          :model="validateInfos"
          :wrapperCol="{ span: 16 }"
        >
          <Row :gutter="0">
            <Col :span="12">
              <FormItem label="产品模板" name="templateIdentification" v-bind=validateInfos.templateIdentification>
                <Select
                placeholder="产品模板"
                :options="state.productTemplateList"
                @change="handleCLickChange"
                v-model:value="modelRef.templateIdentification"
                allowClear
                />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="应用场景" name="appId" v-bind=validateInfos.appId>
               <Input v-model:value="modelRef.appId" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="产品名称" name="productName" v-bind=validateInfos.productName>
               <Input v-model:value="modelRef.productName" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="产品类型" name="productType" v-bind=validateInfos.productType>
                <Select
                placeholder="产品类型"
                :options="productTypeList"
                @change="handleCLickChange"
                v-model:value="modelRef.productType"
                allowClear
                />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="厂商ID" name="manufacturerId" v-bind=validateInfos.manufacturerId>
               <Input v-model:value="modelRef.manufacturerId" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="厂商名称" name="manufacturerName" v-bind=validateInfos.manufacturerName>
               <Input v-model:value="modelRef.manufacturerName" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="产品型号" name="model" v-bind=validateInfos.model>
                <Input v-model:value="modelRef.model" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="数据格式" name="dataFormat" v-bind=validateInfos.dataFormat>
                <Select
                placeholder="数据格式"
                :options="dataTypeList"
                @change="handleCLickChange"
                v-model:value="modelRef.dataFormat"
                allowClear
                />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="设备类型" name="deviceType" v-bind=validateInfos.deviceType>
               <Input v-model:value="modelRef.deviceType" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="认证方式" name="authMode" v-bind=validateInfos.authMode>
                <Input v-model:value="modelRef.authMode" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="用户名" name="userName" v-bind=validateInfos.userName>
               <Input v-model:value="modelRef.userName" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="密码" name="password" v-bind=validateInfos.password>
                <Input v-model:value="modelRef.password" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="连接实例" name="connector" v-bind=validateInfos.connector>
                <Input v-model:value="modelRef.connector" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="签名密钥" name="signKey" v-bind=validateInfos.signKey>
                <Input v-model:value="modelRef.signKey" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="传输加密" name="encryptMethod" v-bind=validateInfos.encryptMethod>
                <Select
                  placeholder="协议类型"
                  :options="encryptMethodList"
                  @change="handleCLickChange"
                  v-model:value="modelRef.encryptMethod"
                  allowClear
                />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="加密密钥" name="encryptKey" v-bind=validateInfos.encryptKey>
                <Input v-model:value="modelRef.encryptKey" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="加密向量" name="encryptVector" v-bind=validateInfos.encryptVector>
                <Input v-model:value="modelRef.encryptVector" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="协议类型" name="protocolType" v-bind=validateInfos.protocolType>
                <Select
                placeholder="协议类型"
                :options="protoTypeList"
                @change="handleCLickChange"
                v-model:value="modelRef.protocolType"
                allowClear
                />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="状态" name="status" v-bind=validateInfos.status>
                <Select
                placeholder="产品类型"
                :options="statusList"
                @change="handleCLickChange"
                v-model:value="modelRef.status"
                allowClear
                />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="产品描述" name="remark" v-bind=validateInfos.remark>
                <Input v-model:value="modelRef.remark" />
              </FormItem>
            </Col>
          </Row>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {computed, onMounted, reactive} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Col, Form, FormItem, Input, Row, Select, Spin,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {
  dataTypeList, encryptMethodList,
  productModel,
  productTypeList,
  protoTypeList,
  statusList
} from "@/views/product/Data";
import {addDeviceProfile, editDeviceProfile, getProductTemplateList} from "@/api/device/product";

const { createMessage } = useMessage();

const state = reactive({
  record: null,
  productType: true,
  fileList: [],
  loading: false,
  editLoading: false,
  defaultRule: [],
  defaultRuleParams: {
    pageSize: 30,
    page: 1,
    total: 0,
  },
  productTemplateList : [],
  defaultQueue: [],
  defaultQueueParams: {
    pageSize: 30,
    page: 1,
    total: 0,
  },
});
const modelRef = reactive(productModel);

const getTitle = computed(() => (state.productType ? '新增产品' : '编辑产品'));

onMounted(() => {
  initProductTemplates();
})

async function initProductTemplates(){
  const productTemplates = await getProductTemplateList();
  state.productTemplateList = state.productTemplateList.concat(
    productTemplates.map((item) => {
      item.value = item.templateIdentification;
      item.label = item.templateName;
      return item;
    }),
  );
}

const [register, { closeModal }] = useModalInner((data) => {
  const { type, record } = data;
  state.productType = type;

  !type && productEdit(record);
});

const emits = defineEmits(['update']);

const rulesRef = reactive({ productName: [{ required: true, message: '请输入产品名称', trigger: ['change'] }],
  productType: [{ required: true, message: '请选择产品类型', trigger: ['change'] }],
});

const useForm = Form.useForm;
const { validate, resetFields, validateInfos } = useForm(modelRef, rulesRef);

function handleCLickChange(value) {
  //console.log('handleCLickChange', value)
}

async function productEdit(record) {
  try {
    state.editLoading = true;
    Object.keys(modelRef).forEach((item) => {
      modelRef[item] = record[item];
    });
    state.editLoading = false;
    state.record = record;
  }catch (error) {
    console.error(error)
    //console.log('productEdit ...', error);
  }
}

function handleCancel() {
  //console.log('handleCancel');
  resetFields();
}

function handleOk() {
  validate().then(async () => {
    let api = addDeviceProfile;
    if (modelRef?.id) {
      api = editDeviceProfile;
    }
    state.editLoading = true;
    api(modelRef)
      .then(() => {
        closeModal();
        resetFields();
        emits('update');
      })
      .finally(() => {
        state.editLoading = false;
      });
  }).catch((err) => {
    createMessage.error('操作失败');
    console.error(err);
  });
}
</script>
<style lang="less" scoped>
  .product-modal {
    :deep(.ant-form-item-label) {
      & > label::after {
        content: '';
      }
    }

    :deep(.ant-form-item) {
      margin-bottom: 20px;
    }

    :deep(.ant-input),
    :deep(.ant-select-selector) {
      border-radius: 8px;
      transition: all 0.3s ease;

      &:hover {
        border-color: #40a9ff;
      }

      &:focus {
        border-color: #1890ff;
        box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
      }
    }

    :deep(.ant-btn) {
      border-radius: 8px;
      font-weight: 500;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
      }
    }
  }
</style>
