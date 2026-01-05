<template>
  <BasicModal
    @register="register"
    title="拉流代理"
    @cancel="handleCancel"
    :width="700"
    @ok="handleOk"
    :canFullscreen="false"
  >
    <div class="product-modal">
      <Spin :spinning="state.editLoading">
        <Form
          :labelCol="{ span: 3 }"
          :model="validateInfos"
          :wrapperCol="{ span: 21 }"
        >
          <FormItem label="代理类型" name="type" v-bind=validateInfos.type>
            <Select
              placeholder="代理类型"
              :options="state.proxyTypeList"
              @change="handleCLickChange"
              v-model:value="modelRef.type"
              allowClear
            />
          </FormItem>
          <FormItem label="代理名称" name="name" v-bind=validateInfos.name>
            <Input v-model:value="modelRef.name"/>
          </FormItem>
          <FormItem label="流应用名" name="app" v-bind=validateInfos.app>
            <Input v-model:value="modelRef.app"/>
          </FormItem>
          <FormItem label="流ID" name="stream" v-bind=validateInfos.stream>
            <Input v-model:value="modelRef.stream"/>
          </FormItem>
          <FormItem label="拉流地址" name="url" v-bind=validateInfos.url>
            <Input v-model:value="modelRef.url"/>
          </FormItem>
          <FormItem label="节点选择" name="mediaServerId" v-bind=validateInfos.mediaServerId>
            <Select
              placeholder="节点选择"
              :options="state.mediaServerList"
              @change="handleCLickChange"
              v-model:value="modelRef.mediaServerId"
              allowClear
            />
          </FormItem>
          <FormItem label="国标编码" name="gbId" v-bind=validateInfos.gbId>
            <Input v-model:value="modelRef.gbId"/>
          </FormItem>
          <FormItem label="拉流方式" name="rtpType" v-bind=validateInfos.rtpType>
            <Select
              placeholder="拉流方式"
              :options="state.rtpTypeList"
              @change="handleCLickChange"
              v-model:value="modelRef.rtpType"
              allowClear
            />
          </FormItem>
          <FormItem label="无人观看" name="noneReader" v-bind=validateInfos.noneReader>
            <Select
              placeholder="无人观看"
              :options="state.noneReaderList"
              @change="handleCLickChange"
              v-model:value="modelRef.noneReader"
              allowClear
            />
          </FormItem>
          <FormItem label="是否启用" name="enable" v-bind=validateInfos.enable>
            <Select
              placeholder="是否启用"
              :options="state.enableList"
              @change="handleCLickChange"
              v-model:value="modelRef.enable"
              allowClear
            />
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {onMounted, reactive, ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, Select, Spin,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {useRoute} from "vue-router";
import {getMediaServerList, savePullProxy} from "@/api/device/gb28181";

defineOptions({name: 'PullProxyModal'})

const {createMessage} = useMessage();
const route = useRoute()

const state = reactive({
  editLoading: false,
  proxyTypeList: [
    {label: 'ZLM', value: 'default'}
  ],
  mediaServerList: [] as any,
  rtpTypeList: [
    {label: 'TCP', value: '0'},
    {label: 'UDP', value: '1'},
    {label: '组播', value: '2'},
  ],
  noneReaderList: [
    {label: '不做处理', value: '0'},
    {label: '停用', value: '1'},
    {label: '移除', value: '2'},
  ],
  enableList: [
    {label: '启用', value: true},
    {label: '禁用', value: false},
  ],
});

const modelRef = reactive({
  type: 'default',
  name: '',
  app: '',
  stream: '',
  url: '',
  mediaServerId: '',
  gbId: '',
  rtpType: '1',
  noneReader: '0',
  enable: true,
  enableRemoveNoneReader: false,
  enableDisableNoneReader: false,
});

const checkedKeys = ref<Array<string | number>>([]);

const [register, {closeModal}] = useModalInner(() => {

});

const emits = defineEmits(['success']);

function handleCLickChange(value) {
  //console.log('handleCLickChange', value)
}

const rulesRef = reactive({
  name: [{required: true, message: '请输入代理名称', trigger: ['change']}],
  app: [{required: true, message: '请输入流应用名', trigger: ['change']}],
  stream: [{required: true, message: '请输入流ID', trigger: ['change']}],
  url: [{required: true, message: '请输入拉流地址', trigger: ['change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

function handleCancel() {
  //console.log('handleCancel');
  resetFields();
}

//mediaServerList
onMounted(() => {
  state.mediaServerList = [];
  getMediaServerList().then((res) => {
    for (const item of res) {
      state.mediaServerList.push(
        {label: item.id, value: item.id}
      )
    }
  });
})

function handleOk() {
  validate().then(async () => {
    let api = savePullProxy;
    state.editLoading = true;
    api(modelRef)
      .then(() => {
        createMessage.success('操作成功');
        closeModal();
        resetFields();
        emits('success');
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
}
</style>
