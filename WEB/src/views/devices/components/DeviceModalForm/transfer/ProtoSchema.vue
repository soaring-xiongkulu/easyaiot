<template>
  <div class="protoSchema">
    <Form :model="validateInfos" :colon="false">
      <FormItem class="schema">
        <template #label>遥测数据 proto schema</template>
        <CodeEditor v-model:value="modelRef.deviceTelemetryProtoSchema" />
      </FormItem>
      <FormItem class="schema">
        <template #label>Attributes proto schema</template>
        <CodeEditor v-model:value="modelRef.deviceAttributesProtoSchema" />
      </FormItem>
      <FormItem class="schema">
        <template #label>RPC 请求 proto schema</template>
        <CodeEditor v-model:value="modelRef.deviceRpcRequestProtoSchema" />
      </FormItem>
      <FormItem class="schema">
        <template #label>RPC 响应 proto schema</template>
        <CodeEditor v-model:value="modelRef.deviceRpcResponseProtoSchema" />
      </FormItem>
    </Form>
  </div>
</template>

<script setup lang="ts">
  import { reactive, defineExpose } from 'vue';
  import {
    defaultTelemetrySchema,
    defaultAttributesSchema,
    defaultRpcRequestSchema,
    defaultRpcResponseSchema,
  } from './protoSchema.ts';
  import { Form, FormItem } from 'ant-design-vue';
  import { CodeEditor } from '@/components/CodeEditor';

  const useForm = Form.useForm;

  defineExpose({
    getProtoSchemaFormData,
  });

  const modelRef = reactive({
    deviceTelemetryProtoSchema: defaultTelemetrySchema,
    deviceAttributesProtoSchema: defaultAttributesSchema,
    deviceRpcRequestProtoSchema: defaultRpcRequestSchema,
    deviceRpcResponseProtoSchema: defaultRpcResponseSchema,
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
