<template>
  <div class="commConfig">
    <Form ref="formRef" name="dynamic_form_nest_item" :model="formData">
      <div class="commConfig__item">
        <div class="commConfig__left">
          <FormItem>
            <template #label>范围</template>
            <Select v-model:value="formData.spec" @change="handleChangeSpec">
              <SelectOption
                v-for="spec in specMap"
                :key="spec.value"
                :value="spec.value"
                :disabled="mappingIsDisabled(spec.value)"
              >
                {{ spec.label }}
              </SelectOption>
            </Select>
          </FormItem>
        </div>
        <div class="commConfig__right">
          <div
            class="commConfig__queryingFrequencyMs"
            v-if="formData.spec === 'LATEST_TELEMETRY' || formData.spec === 'CLIENT_SCOPE'"
          >
            <FormItem
              label="查询频率（ms）"
              :rules="{
                required: true,
                message: '查询频率（ms）必填。',
              }"
            >
              <Input
                v-model:value="formData.queryingFrequencyMs"
                type="number"
                placeholder="请输入查询频率（ms）"
              />
            </FormItem>
          </div>
          <div class="commConfig__mappings">
            <div class="warnMappingText" v-if="formData.mappings.length < 1"> 请添加映射配置 </div>
            <Space
              v-for="(mapping, index) in formData.mappings"
              :key="mapping.id"
              style="display: flex; margin-bottom: 12px"
              align="baseline"
            >
              <FormItem label="数据类型" :name="['mappings', index, 'dataType']">
                <Select v-model:value="mapping.dataType" :options="DataTypeTranslationMap" />
              </FormItem>
              <FormItem
                label="数据键"
                :name="['mappings', index, 'key']"
                :rules="{
                  required: true,
                  message: '数据键必填。',
                }"
              >
                <Input v-model:value="mapping.key" placeholder="请输入数据键" />
              </FormItem>
              <FormItem
                label="OID"
                :name="['mappings', index, 'oid']"
                :rules="{
                  required: true,
                  message: 'OID必填。',
                }"
              >
                <Input v-model:value="mapping.oid" placeholder="请输入OID" />
              </FormItem>
              <MinusCircleOutlined @click="removeMapping(mapping)" />
            </Space>
            <FormItem>
              <Button @click="addMapping">
                <PlusCircleOutlined />
                添加映射
              </Button>
            </FormItem>
          </div>
        </div>
      </div>
    </Form>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, defineExpose, defineProps, defineEmits, watch } from 'vue';
  import { Form, Space, FormItem, Select, Input, Button } from 'ant-design-vue';
  import { MinusCircleOutlined, PlusCircleOutlined } from '@ant-design/icons-vue';
  import type { FormInstance } from 'ant-design-vue';

  defineExpose({
    getCommConfigFormData,
  });

  const props = defineProps({
    value: {
      type: String,
      required: true,
    },
    specMap: {
      type: Array as any,
      required: true,
    },
    communicationConfigsSpecs: {
      type: Array,
      required: true,
    },
  });

  const emits = defineEmits(['update:value']);

  interface Mapping {
    dataType: string;
    key: string;
    oid: string;
    id: number;
  }
  interface FormData {
    spec: string;
    queryingFrequencyMs: number;
    mappings: Array<Mapping>;
  }
  enum DataType {
    STRING = 'STRING',
    LONG = 'LONG',
    BOOLEAN = 'BOOLEAN',
    DOUBLE = 'DOUBLE',
    JSON = 'JSON',
  }

  const DataTypeTranslationMap = reactive([
    { label: '字符串', value: DataType.STRING },
    { label: '数字', value: DataType.LONG },
    { label: '布尔值', value: DataType.BOOLEAN },
    { label: '双精度小数', value: DataType.DOUBLE },
    { label: 'JSON', value: DataType.JSON },
  ]);
  const formRef = ref<FormInstance>();
  const formData = reactive<FormData>({
    spec: '',
    queryingFrequencyMs: 5000,
    mappings: [
      {
        dataType: DataType.STRING,
        key: '',
        oid: '',
        id: Date.now(),
      },
    ],
  });
  watch(
    () => props.value,
    (newValue: string) => {
      formData.spec = newValue;
    },
    { immediate: true },
  );
  const removeMapping = (item: Mapping) => {
    let index = formData.mappings.indexOf(item);
    if (index !== -1) {
      formData.mappings.splice(index, 1);
    }
  };
  const addMapping = () => {
    formData.mappings.push({
      dataType: DataType.STRING,
      key: '',
      oid: '',
      id: Date.now(),
    });
  };
  function mappingIsDisabled(value: string) {
    if (props.communicationConfigsSpecs.length === 1) {
      return false;
    }
    return props.communicationConfigsSpecs.includes(value) && value !== formData.spec;
  }
  function handleChangeSpec(value) {
    emits('update:value', value);
  }
  async function getCommConfigFormData() {
    await formRef.value?.validate();
    return new Promise((resolve) => {
      resolve(formData);
    });
  }
</script>

<style lang="less" scoped>
  .commConfig {
    width: 100%;
    margin-right: 10px;

    &__item {
      display: flex;
      margin: 10px 0;
      padding: 5px;
      border: 1px groove rgb(0 0 0 / 25%);
      border-radius: 4px;
    }

    &__left {
      width: 140px;
      padding: 5px;
      border-right: 1px solid #ccc;
    }

    &__right {
      flex: 1;
      margin: 0 10px;
    }

    .warnMappingText {
      color: #dd2c00;
      font-size: 16px;
      text-align: center;
    }

    &__queryingFrequencyMs {
      width: 100%;
      border-bottom: 1px solid #ccc;

      .ant-form-item {
        margin-bottom: 10px;
      }
    }

    &__mappings {
      padding-top: 10px;
    }

    .ant-space-align-baseline .ant-form-item {
      margin-bottom: 0;
    }
  }
</style>
