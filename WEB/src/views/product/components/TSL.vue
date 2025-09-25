<template>
  <BasicModal @register="register" title="物理模型TSL">
    <Typography>
      <TypographyParagraph>
        <blockquote>
          物模型是对设备在云端的功能描述，包括设备的属性、服务和事件。云边端一体化协同算法应用平台通过定义一种物的描述语言来描述物模型，称之为
          TSL（即 Thing Specification Language），采用 JSON 格式，您可以根据 TSL
          组装上报设备的数据。您可以导出完整物模型，用于云端应用开发；您也可以只导出
          精简物模型，配合设备端 SDK 实现设备开发。
        </blockquote>
      </TypographyParagraph>
    </Typography>

    <Tabs v-model:activeKey="tabsActive" type="card">
      <TabPane v-for="v in tabsOptions" :key="v.key" :tab="v.label">
        <CodeEditor :value="jsonData" readonly />
      </TabPane>
      <template #rightExtra>
        <Button @click="handleCopy">
          <template #icon>
            <CopyOutlined class="app-iconify" />
          </template>
          copy
        </Button>
      </template>
    </Tabs>

    <template #footer>
      <Button @click="handleClose">取消</Button>
      <Button type="primary" @click="handleExport('all')">导出全部</Button>
      <Button type="primary" @click="handleExport('model')">导出物模型</Button>
    </template>
  </BasicModal>
</template>

<script lang="ts" setup name="TSL">
  import { BasicModal, useModalInner } from '@/components/Modal';
  import { CopyOutlined } from '@ant-design/icons-vue';
  import { Typography, TypographyParagraph, Tabs, TabPane, Button } from 'ant-design-vue';
  import { CodeEditor } from '@/components/CodeEditor';
  import { ref, computed } from 'vue';
  import { copyText } from '@/utils/copyText';
  import { useMessage } from '@/hooks/web/useMessage';
  import { tabsOptions } from '../data/ProductData';
  import { downloadByData } from '@/utils/file/download';

  const { createMessage } = useMessage();

  const originData = ref<{
    deviceProfileName: '';
  }>({ deviceProfileName: '' });
  const tabsActive = ref('properties');

  const [register, { closeModal }] = useModalInner((data) => {
    originData.value = data;
  });

  const jsonData = computed(() => {
    return originData.value[tabsActive.value];
  });

  const handleCopy = () => {
    if (!jsonData.value) return createMessage.warning('没有可以复制的数据');
    copyText(JSON.stringify(jsonData.value), '数据');
  };

  const handleClose = () => {
    closeModal();
  };

  const handleExport = (type: 'model' | 'all') => {
    const { deviceProfileName, ...ext } = originData.value;

    const temp = type === 'model' ? jsonData.value : ext;

    const fileName =
      type === 'model' ? `${deviceProfileName}-model.json` : `${deviceProfileName}.json`;

    downloadByData(JSON.stringify(temp), fileName, 'application/json');
  };
</script>

<style lang="less" scoped></style>
