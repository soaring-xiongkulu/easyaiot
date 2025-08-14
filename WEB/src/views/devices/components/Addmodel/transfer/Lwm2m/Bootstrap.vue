<template>
  <Form :colon="false">
    <FormItem label=" ">
      <Popconfirm
        title="你已经配置了Bootstrap Server，您确定要排除更新吗？请注意确认更新后Bootstrap Server配置数据将无法恢复。"
        :visible="visible"
        ok-text="是"
        cancel-text="否"
        @confirm="handleConfirm"
        @visible-change="handleVisibleChange"
      >
        <Checkbox v-model:checked="modelRef.bootstrapServerUpdateEnable">
          包含Bootstrap Server更新
        </Checkbox>
      </Popconfirm>
      <Collapse v-model:activeKey="modelRef.activeKey" expand-icon-position="right">
        <CollapsePanel
          v-for="(item, index) in modelRef.collapseFormList"
          :key="index"
          :header="fetchHeaderText(item)"
        >
          <CollapseForm :defaultShortServerId="item.defaultShortServerId" />
          <template #extra>
            <Popconfirm
              title="你确定要删除服务器吗？请注意确认删除后服务器配置将无法恢复。"
              ok-text="是"
              cancel-text="否"
              @confirm="handleConfirmDelCollapse(index)"
            >
              <delete-outlined class="delIcon" @click.stop />
            </Popconfirm>
          </template>
        </CollapsePanel>
      </Collapse>
      <Button type="primary" @click="handleClickAddServer">添加LwM2M服务器</Button>
      <Modal v-model:visible="modelVisible" title="添加新的服务器配置" @ok="handleOk">
        <Form :colon="false" class="securityModeForm">
          <FormItem label="Server type">
            <Select v-model:value="securityMode" :options="securityModeList" />
          </FormItem>
        </Form>
      </Modal>
    </FormItem>
  </Form>
</template>

<script setup lang="ts">
  import { DeleteOutlined } from '@ant-design/icons-vue';
  import {
    Form,
    FormItem,
    Button,
    Popconfirm,
    Modal,
    Select,
    Checkbox,
    Collapse,
    CollapsePanel,
  } from 'ant-design-vue';
  import { ref, reactive } from 'vue';
  import CollapseForm from './CollapseForm.vue';

  const useForm = Form.useForm;

  const securityModeList = [
    { label: 'LwM2M Server', value: 'LwM2M Server' },
    { label: 'Bootstrap Server', value: 'Bootstrap Server' },
  ];
  const securityMode = ref<string>('LwM2M Server');

  const visible = ref<boolean>(false);
  const modelVisible = ref<boolean>(false);
  const modelRef = reactive({
    bootstrapServerUpdateEnable: false,
    activeKey: [],
    collapseFormList: [{ title: 'LwM2M Server', defaultShortServerId: '123' }],
    shortServerId: '',
  });
  useForm(modelRef);

  function handleConfirmDelCollapse(index) {
    modelRef.collapseFormList.splice(index, 1);
  }
  const handleVisibleChange = (bool: boolean) => {
    if (!bool) {
      visible.value = false;
      return;
    }
    if (!modelRef.bootstrapServerUpdateEnable) {
      modelRef.bootstrapServerUpdateEnable = true;
    } else {
      visible.value = true;
    }
  };
  function fetchHeaderText(item) {
    return item.title + ' ' + ' 服务器ID: ' + item.defaultShortServerId;
  }
  function handleConfirm() {
    modelRef.bootstrapServerUpdateEnable = false;
    const index = modelRef.collapseFormList.findIndex((item) => item.title === 'Bootstrap Server');
    modelRef.collapseFormList.splice(index, 1);
  }
  function handleOk() {
    const temp =
      securityMode.value === 'Bootstrap Server'
        ? { title: 'Bootstrap Server', defaultShortServerId: '111' }
        : { title: 'LwM2M Server', defaultShortServerId: '123' };
    modelRef.collapseFormList.push(temp);
    securityMode.value = 'LwM2M Server';
    modelVisible.value = false;
  }
  function handleClickAddServer() {
    const tempIndex = modelRef.collapseFormList.findIndex(
      (item) => item.title === 'Bootstrap Server',
    );
    if (modelRef.bootstrapServerUpdateEnable && tempIndex === -1) {
      modelVisible.value = true;
    } else {
      modelRef.collapseFormList.push({ title: 'LwM2M Server', defaultShortServerId: '123' });
    }
  }
</script>

<style lang="less" scoped>
  .delIcon {
    margin-top: 5px;
  }

  .securityModeForm {
    padding: 15px;
  }
</style>
