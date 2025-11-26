<template>
  <BasicModal
    @register="register"
    :title="getTitle"
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
          :disabled="state.isView"
        >
          <FormItem label="快捷键编号" name="shortcut" v-bind=validateInfos.shortcut>
            <InputNumber
              v-model:value="modelRef.shortcut"
              step="1"
              min="0"
              max="9"
              allowClear
            />
          </FormItem>
          <FormItem label="标签名称" name="name"
                    v-bind=validateInfos.name>
            <Input v-model:value="modelRef.name"/>
          </FormItem>
          <FormItem label="标签颜色" name="color" v-bind=validateInfos.color>
            <Input type="color" v-model:value="modelRef.color" style="width: 100px"/>
          </FormItem>
          <FormItem label="标签描述" name="description" v-bind=validateInfos.description>
            <Input v-model:value="modelRef.description"/>
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import {computed, reactive} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, InputNumber, Spin,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {createDatasetTag, updateDatasetTag} from "@/api/device/dataset";

defineOptions({name: 'DatasetTagModal'})

const {createMessage} = useMessage();

const state = reactive({
  record: null,
  isEdit: false,
  isView: false,
  fileList: [],
  loading: false,
  editLoading: false,
});

const modelRef = reactive({
  id: null,
  shortcut: 1,
  name: '',
  color: '',
  description: '',
  datasetId: null,
  warehouseId: null,
});

const getTitle = computed(() => (state.isEdit ? '编辑数据集标签' : state.isView ? '查看数据集标签' : '新增数据集标签'));

const [register, {closeModal}] = useModalInner((data) => {
  const {datasetId, isEdit, isView, record} = data;
  state.isEdit = isEdit;
  state.isView = isView;
  modelRef.datasetId = datasetId;
  if (state.isEdit || state.isView) {
    datasetEdit(record);
  }
});

const emits = defineEmits(['success']);

const rulesRef = reactive({
  shortcut: [{required: true, message: '请输入快捷键编号', trigger: ['change']}],
  name: [{required: true, message: '请输入标签名称', trigger: ['change']}],
  color: [{required: true, message: '请输入标签颜色', trigger: ['change']}],
  description: [{required: true, message: '请输入描述', trigger: ['change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

async function datasetEdit(record) {
  try {
    state.editLoading = true;
    Object.keys(modelRef).forEach((item) => {
      modelRef[item] = record[item];
    });
    state.editLoading = false;
    state.record = record;
  } catch (error) {
    console.error(error)
    //console.log('datasetEdit ...', error);
  }
}

function handleCancel() {
  //console.log('handleCancel');
  resetFields();
}

function handleOk() {
  validate().then(async () => {
    let api = createDatasetTag;
    if (modelRef?.id) {
      api = updateDatasetTag;
    }
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
