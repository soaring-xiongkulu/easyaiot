<!-- 参数类型输入组件 -->
<template>
  <div class="value-item-warp">
    <Select
      v-if="typeMap.get(itemType) === 'select'"
      v-model:value="myValue"
      :options="options"
      allowClear
      style="width: 100%"
      @change="selectChange"
    />
    <TimePicker
      v-else-if="typeMap.get(itemType) === 'time'"
      v-model:value="myValue"
      allowClear
      valueFormat="HH:mm:ss"
      style="width: 100%"
      @change="timeChange"
    />
    <DatePicker
      v-else-if="typeMap.get(itemType) === 'date'"
      v-model:value="myValue"
      allowClear
      showTime
      valueFormat="YYYY-MM-DD HH:mm:ss"
      style="width: 100%"
      @change="dateChange"
    />
    <InputNumber
      v-else-if="typeMap.get(itemType) === 'inputNumber'"
      v-model:value="myValue"
      allowClear
      style="width: 100%"
      @change="inputChange"
    />
    <Input
      allowClear
      v-else-if="typeMap.get(itemType) === 'object'"
      v-model:value="myValue"
      @change="inputChange"
    >
      <template #addonAfter>
        <FormOutlined class="app-iconify" @click="openModal()" />
      </template>
    </Input>

    <!-- <GeoComponent
      v-else-if="typeMap.get(itemType) === 'geoPoint'"
      v-model:point="myValue"
      @change="inputChange"
    /> -->

    <Input
      v-else-if="typeMap.get(itemType) === 'file'"
      v-model:value="myValue"
      placeholder="请输入链接"
      allowClear
      @change="inputChange"
    >
      <template #addonAfter>
        <BasicUpload
          name="file"
          :action="FILE_UPLOAD"
          :headers="headers"
          :showUploadList="false"
          @change="handleFileChange"
        >
          <!-- <AIcon type="UploadOutlined" /> -->
        </BasicUpload>
      </template>
    </Input>

    <InputPassword
      v-else-if="typeMap.get(itemType) === 'password'"
      allowClear
      type="password"
      v-model:value="myValue"
      style="width: 100%"
      @change="inputChange"
    />
    <Input
      v-else
      allowClear
      type="text"
      v-model:value="myValue"
      style="width: 100%"
      @change="inputChange"
    />

    <!-- 代码编辑器弹窗 -->
    <BasicModal
      title="编辑"
      ok-text="确认"
      cancel-text="取消"
      width="700px"
      @cancel="closeModal"
      @ok="handleItemModalSubmit"
      :zIndex="1100"
      @register="register"
    >
      <div style="width: 100%; height: 300px">
        <CodeEditor v-model:modelValue="objectValue" />
      </div>
    </BasicModal>
  </div>
</template>

<script setup lang="ts" name="ValueItem">
  import { PropType, ref, watch } from 'vue';
  import {
    UploadChangeParam,
    UploadFile,
    Select,
    TimePicker,
    DatePicker,
    InputNumber,
    Input,
    InputPassword,
  } from 'ant-design-vue';
  import { FormOutlined } from '@ant-design/icons-vue';
  import { DefaultOptionType } from 'ant-design-vue/lib/select';
  //   import GeoComponent from '@/components/GeoComponent/EasyPlayer.vue';
  import { ACCESS_TOKEN_KEY } from '/@/enums/cacheEnum';
  import { LocalStore } from '/@/utils/comm';
  import { ItemData, ITypes } from './types';
  import { BasicUpload } from '../Upload';
  import { BasicModal, useModal } from '/@/components/Modal/index';
  import { CodeEditor } from '/@/components/CodeEditor';

  //   import { FILE_UPLOAD } from '@/api/comm';
  //   import { Upload } from 'jetlinks-ui-components';

  type Emits = {
    (e: 'update:modelValue', data: string | number | boolean): void;
    (e: 'change', data: any, item?: any): void;
  };
  const emit = defineEmits<Emits>();

  const props = defineProps({
    itemData: {
      type: Object as PropType<ItemData>,
      default: () => ({}),
    },
    // 组件双向绑定的值
    modelValue: {
      type: [Number, String],
      default: '',
    },
    // 组件类型
    itemType: {
      type: String,
      default: () => 'string',
    },
    // 下拉选择框下拉数据
    options: {
      type: Array as PropType<DefaultOptionType[]>,
      default: () => [],
    },
  });
  // type Props = {
  //     itemData?: Object;
  //     modelValue?: string | number | boolean;
  // };
  // const props = withDefaults(defineProps<Props>(), {
  //     itemData: () => ({ type: 'object' }),
  //     modelValue: '',
  // });

  const [register, { openModal, closeModal }] = useModal();

  const componentsType = ref<ITypes>({
    int: 'inputNumber',
    long: 'inputNumber',
    float: 'inputNumber',
    double: 'inputNumber',
    string: 'input',
    array: 'input',
    password: 'password',
    enum: 'select',
    boolean: 'select',
    date: 'date',
    object: 'object',
    geoPoint: 'geoPoint',
    file: 'file',
  });
  const typeMap = new Map(Object.entries(componentsType.value));

  // const myValue = computed({
  //     get: () => {
  //         return props.modelValue;
  //     },
  //     set: (val: any) => {
  //         objectValue.value = val;
  //         emit('update:modelValue', val);
  //     },
  // });

  const myValue = ref(props.modelValue);

  const objectValue = ref<string>('');
  const handleItemModalSubmit = () => {
    myValue.value = objectValue.value.replace(/[\r\n]\s*/g, '');
    closeModal();
    emit('update:modelValue', objectValue.value);
    emit('change', objectValue.value);
  };

  // 文件上传
  const headers = ref({ [ACCESS_TOKEN_KEY]: LocalStore.get(ACCESS_TOKEN_KEY) });
  const handleFileChange = (info: UploadChangeParam<UploadFile<any>>) => {
    if (info.file.status === 'done') {
      const url = info.file.response?.result;
      myValue.value = url;
      emit('update:modelValue', url);
      emit('change', url);
    }
  };

  const selectChange = (e: any, option: any) => {
    emit('update:modelValue', myValue.value);
    emit('change', e, option);
  };

  const timeChange = (e: any) => {
    emit('update:modelValue', myValue.value);
    emit('change', e);
  };

  const inputChange = (e: any) => {
    emit('update:modelValue', myValue.value);
    emit('change', e && e.target ? e.target.value : e);
  };

  const dateChange = (e: any) => {
    emit('update:modelValue', myValue.value);
    emit('change', e);
  };

  watch(
    () => props.modelValue,
    () => {
      myValue.value = props.modelValue;
    },
    { immediate: true },
  );

  if (props.itemType === 'object') {
    objectValue.value = props.modelValue as string;
  }
</script>

<style lang="less" scoped></style>
