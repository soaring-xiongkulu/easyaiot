<template>
  <div class="protoSchema">
    <Form :model="validateInfos" :colon="false">
      <FormItem class="schema">
        <template #label>LWM2M</template>
        <CodeEditor v-model:value="modelRef.deviceTelemetryProtoSchema" />
      </FormItem>
    </Form>
  </div>
</template>

<script setup lang="ts">
  import { reactive, defineExpose } from 'vue';
  import { Form, FormItem } from 'ant-design-vue';
  import { CodeEditor } from '@/components/CodeEditor';

  const useForm = Form.useForm;

  defineExpose({
    getProtoSchemaFormData,
  });

  const modelRef = reactive({
    deviceTelemetryProtoSchema: '',
  });
  const { validateInfos } = useForm(modelRef);
  async function getProtoSchemaFormData() {
    return modelRef;
  }
</script>

<style lang="less" scoped>
  .ProtoSchema {
    .commonCard {
      margin-bottom: 20px;

      .ant-form-item {
        margin-bottom: 0;
      }

      &__tip {
        margin-top: 12px;
      }
    }

    .schema {
      margin-top: 15px;
    }

    .checkTip {
      font-size: 12px;
    }
  }
</style>
