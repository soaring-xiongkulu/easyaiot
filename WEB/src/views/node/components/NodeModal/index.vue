<script lang="ts" setup>
import { computed, ref, unref } from 'vue';
import { Alert, Input, InputNumber, Spin } from 'ant-design-vue';
import { formSchema } from '../../Data';
import { useMessage } from '@/hooks/web/useMessage';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { Button } from '@/components/Button';
import { createNode, preflightRecordingStorage, updateNode, type ComputeNodeVO } from '@/api/device/node';
import { generateDefaultAgentPort, generateRandomDeployPorts, SETUP_COPY, readMediaPortsFromTags, buildMediaPortTags, readStorageTagsFromTags, buildStorageTags, readMqttPortsFromTags, buildMqttPortTags, nodeHasAnyFunction } from '../../utils/constants';
import {
  nodeFormHistoryToFields,
  saveNodeFormHistory,
  valuesToNodeFormHistoryEntry,
  type NodeFormHistoryEntry,
} from '../../utils/nodeFormHistory';
import NodeNameField from '../NodeNameField/index.vue';

defineOptions({ name: 'NodeModal' });

const emit = defineEmits(['success', 'register', 'created', 'hostExists']);
const { createMessage } = useMessage();
const isUpdate = ref(false);
const submitting = ref(false);
const editRecord = ref<ComputeNodeVO | null>(null);
const historyRefreshToken = ref(0);

const drawerTitle = computed(() => (unref(isUpdate) ? '编辑节点' : '添加节点'));

const [registerForm, { setFieldsValue, resetFields, validate, clearValidate }] = useForm({
  labelWidth: 150,
  schemas: formSchema,
  showActionButtonGroup: false,
  baseColProps: { span: 24 },
});

function handleGenerateRandomPorts(model: Record<string, unknown>) {
  const ports = generateRandomDeployPorts({
    functions: model.functions as string[] | undefined,
    nodeRole: String(model.nodeRole || ''),
  });
  setFieldsValue(ports);
  createMessage.success(SETUP_COPY.generateRandomPortsSuccess);
}

function flattenNodeTags(record: ComputeNodeVO) {
  return {
    ...record,
    recordingStorageMode: record.recordingStorageMode || 'central_shared',
    functions: record.functions?.length ? record.functions : undefined,
    ...readMediaPortsFromTags(record.tags),
    ...readStorageTagsFromTags(record.tags),
    ...readMqttPortsFromTags(record.tags),
  };
}

function buildNodeTags(values: Record<string, unknown>) {
  const base = (values.tags as Record<string, string> | undefined) || {};
  const functions = Array.isArray(values.functions) ? (values.functions as string[]) : [];
  if (functions.includes('live') || functions.includes('forward')) {
    return { ...base, ...buildMediaPortTags(values) };
  }
  if (functions.includes('nfs')) {
    return { ...base, ...buildStorageTags(values) };
  }
  if (functions.includes('mqtt')) {
    return { ...base, ...buildMqttPortTags(values) };
  }
  return base;
}

const [registerDrawer, { closeDrawer }] = useDrawerInner(async (data) => {
  resetFields();
  isUpdate.value = !!data?.isUpdate;
  editRecord.value = data?.isUpdate && data.record ? data.record : null;
  if (unref(isUpdate) && data.record) {
    setFieldsValue(flattenNodeTags(data.record));
  } else {
    setFieldsValue({
      sshUsername: 'root',
      agentPort: generateDefaultAgentPort(),
      recordingStorageMode: 'central_shared',
    });
  }
});

function handleNameChange() {
  clearValidate(['name']).catch(() => {});
}

async function applyHistoryEntry(entry: NodeFormHistoryEntry) {
  setFieldsValue(nodeFormHistoryToFields(entry));
  await clearValidate(['name']).catch(() => {});
}

function persistFormHistory(values: Record<string, unknown>) {
  saveNodeFormHistory(valuesToNodeFormHistoryEntry(values));
  historyRefreshToken.value += 1;
}

async function handleSubmit() {
  let raw: ComputeNodeVO & Record<string, unknown>;
  try {
    raw = (await validate()) as ComputeNodeVO & Record<string, unknown>;
  } catch (error) {
    console.warn('[NodeModal] node form validation failed', error);
    createMessage.warning('请检查节点表单中的必填项和字段格式');
    return;
  }
  const values = {
    ...raw,
    tags: buildNodeTags(raw),
  };
  delete (values as Record<string, unknown>).nodeRole;
  if (unref(isUpdate) && editRecord.value) {
    values.maxTaskCount = editRecord.value.maxTaskCount ?? 50;
    values.weight = editRecord.value.weight ?? 100;
  }
  submitting.value = true;
  try {
    if (unref(isUpdate)) {
      const storageModeChanged = editRecord.value?.recordingStorageMode !== values.recordingStorageMode
        || (editRecord.value?.mediaPublicUrl || '') !== (values.mediaPublicUrl || '');
      if (storageModeChanged && values.id && values.recordingStorageMode) {
        const preflight = await preflightRecordingStorage(
          Number(values.id),
          values.recordingStorageMode as 'central_shared' | 'edge_local',
          String(values.mediaPublicUrl || ''),
        );
        const blockers = preflight.checks.filter((item) => item.required && !item.ok);
        if (!preflight.ok || blockers.length) {
          throw new Error(blockers.map((item) => `${item.name}：${item.detail}`).join('；') || preflight.message || '录像存储模式预检未通过');
        }
        const warnings = preflight.checks.filter((item) => !item.required && !item.ok);
        if (warnings.length) {
          createMessage.warning(warnings.map((item) => item.detail).join('；'));
        }
      }
      await updateNode(values);
      createMessage.success('更新成功');
      closeDrawer();
      emit('success');
    } else {
      const res = await createNode(values, { errorMessageMode: 'none' });
      persistFormHistory(raw);
      closeDrawer();
      emit('success');
      emit('created', { ...values, ...(res || {}), agentToken: res?.agentToken });
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    if (!unref(isUpdate) && msg.includes('主机地址已存在')) {
      closeDrawer();
      emit('hostExists', raw.host);
      return;
    }
    createMessage.error(msg || '保存失败');
  } finally {
    submitting.value = false;
  }
}

function handleCancel() {
  closeDrawer();
}
</script>

<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="registerDrawer"
    :title="drawerTitle"
    width="1400"
    placement="right"
    :showFooter="true"
    :showOkBtn="false"
    :showCancelBtn="false"
    destroy-on-close
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleCancel">取消</Button>
        <Button type="primary" :loading="submitting" @click="handleSubmit">
          保存
        </Button>
      </div>
    </template>

    <Spin :spinning="submitting">
      <div class="node-drawer-content">
        <BasicForm @register="registerForm">
          <template #centralStorageHint>
            <Alert
              type="warning"
              show-icon
              message="中心共享存储前置条件"
              description="边缘节点的 /mnt/easyaiot-media 必须挂载与中心相同的 NFS/CephFS。仅创建本地目录或目录可写不会通过预检；未准备共享挂载时请选择“边缘本地存储”。"
            />
          </template>
          <template #name="{ model, field }">
            <NodeNameField
              v-model:value="model[field]"
              :show-history="!isUpdate"
              :refresh-token="historyRefreshToken"
              @update:value="handleNameChange"
              @apply-history="applyHistoryEntry"
            />
          </template>
          <template #zlmRtpPortMax="{ model, field }">
            <div class="field-with-action">
              <InputNumber
                v-model:value="model[field]"
                :min="1"
                :max="65535"
                class="field-with-action__control"
              />
              <Button type="default" class="field-with-action__btn" @click="() => handleGenerateRandomPorts(model)">
                {{ SETUP_COPY.generateRandomPortsBtn }}
              </Button>
            </div>
          </template>
          <template #sshPassword="{ model, field }">
            <div class="field-with-action">
              <Input.Password
                v-model:value="model[field]"
                placeholder="更换目标服务器时请重新填写密码"
                class="field-with-action__control"
              />
              <Button
                v-if="nodeHasAnyFunction({ functions: model.functions }, ['live', 'forward'])"
                type="default"
                class="field-with-action__btn"
                @click="() => handleGenerateRandomPorts(model)"
              >
                {{ SETUP_COPY.generateRandomPortsBtn }}
              </Button>
            </div>
          </template>
          <template #sshPrivateKey="{ model, field }">
            <div class="field-with-action field-with-action--top">
              <Input.TextArea
                v-model:value="model[field]"
                :rows="4"
                placeholder="-----BEGIN RSA PRIVATE KEY-----"
                class="field-with-action__control"
              />
              <Button
                v-if="nodeHasAnyFunction({ functions: model.functions }, ['live', 'forward'])"
                type="default"
                class="field-with-action__btn"
                @click="() => handleGenerateRandomPorts(model)"
              >
                {{ SETUP_COPY.generateRandomPortsBtn }}
              </Button>
            </div>
          </template>
        </BasicForm>
      </div>
    </Spin>
  </BasicDrawer>
</template>

<style lang="less" scoped>
.node-drawer-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}

.field-with-action {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.field-with-action--top {
  align-items: flex-start;
}

.field-with-action__control {
  flex: 1;
  min-width: 0;
}

.field-with-action__btn {
  flex-shrink: 0;
  white-space: nowrap;
}

</style>
