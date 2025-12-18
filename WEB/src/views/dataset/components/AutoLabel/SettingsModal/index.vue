<template>
  <BasicModal
    @register="register"
    width="800px"
    @cancel="handleCancel"
    :canFullscreen="false"
    :showOkBtn="false"
    :showCancelBtn="false"
  >
    <template #title>
      <span class="modal-title-with-icon">
        <Icon icon="ant-design:setting-outlined" class="title-icon" />
        设置
      </span>
    </template>
    <div class="modal-content">
      <Collapse v-model:activeKey="activeKeys" :bordered="false">
        <CollapsePanel key="about">
          <template #header>
            <span class="collapse-header">
              <Icon icon="ant-design:user-outlined" class="collapse-icon" />
              关于项目
            </span>
          </template>
          <div class="about-content">
            <p><strong>EasyAIoT 自动化标注系统</strong></p>
            <p>版本: 1.0.0</p>
          </div>
        </CollapsePanel>
        
        <CollapsePanel key="yolo11">
          <template #header>
            <span class="collapse-header">
              <Icon icon="ant-design:api-outlined" class="collapse-icon" />
              YOLO11 模型管理
            </span>
          </template>
          <Form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
            <FormItem label="安装路径">
              <Input v-model:value="config.installPath" disabled />
            </FormItem>
            
            <FormItem>
              <Space size="middle">
                <Button type="primary" @click="handleInstall" :loading="loading.install">
                  <template #icon><Icon icon="ant-design:download-outlined" /></template>
                  安装
                </Button>
                <Button @click="handleUninstall" :loading="loading.uninstall">
                  <template #icon><Icon icon="ant-design:delete-outlined" /></template>
                  卸载
                </Button>
                <Button @click="handleTutorial">
                  <template #icon><Icon icon="ant-design:book-outlined" /></template>
                  教程
                </Button>
              </Space>
            </FormItem>
            
            <FormItem>
              <div class="yolo-status-info">
                <div class="status-item">
                  <span class="status-label">安装时间:</span>
                  <span class="status-value">{{ config.installTime || '未知' }}</span>
                </div>
                <div class="status-item">
                  <span class="status-label">硬件支持:</span>
                  <Tag :color="config.hardwareSupport === 'GPU' ? 'green' : 'blue'">
                    {{ config.hardwareSupport }}
                  </Tag>
                </div>
              </div>
            </FormItem>
            
            <FormItem label="下载预训练模型:">
              <CheckboxGroup v-model:value="config.selectedSizes">
                <Checkbox value="n">n(小)</Checkbox>
                <Checkbox value="s">s(中)</Checkbox>
                <Checkbox value="m">m(大)</Checkbox>
                <Checkbox value="l">l(特大)</Checkbox>
                <Checkbox value="x">x(超大)</Checkbox>
              </CheckboxGroup>
              <Space size="middle" style="margin-top: 12px">
                <Button type="primary" @click="handleDownload" :loading="loading.download">
                  <template #icon><Icon icon="ant-design:download-outlined" /></template>
                  下载
                </Button>
                <Button @click="handleRefresh" :loading="loading.refresh">
                  <template #icon><Icon icon="ant-design:reload-outlined" /></template>
                  刷新
                </Button>
              </Space>
            </FormItem>
            
            <FormItem label="已安装模型:">
              <div class="installed-models-list">
                <div
                  v-for="model in installedModels"
                  :key="model.id"
                  class="model-item"
                >
                  <Icon icon="ant-design:file-outlined" class="model-icon" />
                  <span class="model-name">{{ model.name }}</span>
                  <Button
                    type="text"
                    size="small"
                    class="delete-model-btn"
                    @click="handleDeleteModel(model.id)"
                  >
                    <template #icon><Icon icon="ant-design:close-outlined" /></template>
                  </Button>
                </div>
                <div v-if="installedModels.length === 0" class="empty-models">
                  暂无已安装模型
                </div>
              </div>
            </FormItem>
            
            <FormItem label="模型文件上传">
              <div class="upload-area model-upload-area" @click="triggerModelUpload" @drop.prevent="handleModelDrop" @dragover.prevent>
                <div class="upload-content">
                  <Icon icon="ant-design:cloud-upload-outlined" class="upload-icon" />
                  <p class="upload-text">拖放模型文件到此处,或放置到 plugins/yolo11/models</p>
                </div>
              </div>
              <input
                ref="modelInput"
                type="file"
                accept=".pt,.onnx"
                style="display: none"
                @change="handleModelSelect"
              />
            </FormItem>
          </Form>
        </CollapsePanel>
      </Collapse>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, reactive } from 'vue';
import { BasicModal, useModal } from '@/components/Modal';
import { Icon } from '@/components/Icon';
import { Collapse, CollapsePanel, Form, FormItem, Input, CheckboxGroup, Checkbox, Tag, Button, Space } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';

defineOptions({ name: 'SettingsModal' });

const { createMessage } = useMessage();

const activeKeys = ref<string[]>(['yolo11']);
const modelInput = ref<HTMLInputElement | null>(null);
const installedModels = ref<any[]>([]);

const config = reactive({
  installPath: 'plugins/yolo11',
  installTime: null as string | null,
  hardwareSupport: 'CPU',
  selectedSizes: ['n'] as string[],
});

const loading = reactive({
  install: false,
  uninstall: false,
  download: false,
  refresh: false,
});

const [register, { openModal, closeModal }] = useModal();

// 暴露方法供父组件调用
defineExpose({
  openModal,
  closeModal,
  loadInstalledModels,
  loadYOLO11Config,
});

// 加载YOLO11配置
async function loadYOLO11Config() {
  // TODO: 从后端加载YOLO11配置
  try {
    // const res = await getYOLO11Config();
    // if (res.code === 0) {
    //   Object.assign(config, res.data);
    // }
  } catch (error) {
    console.error('加载YOLO11配置失败:', error);
  }
}

// 加载已安装模型
async function loadInstalledModels() {
  // TODO: 从后端加载已安装的模型列表
  try {
    // const res = await getInstalledModels();
    // if (res.code === 0) {
    //   installedModels.value = res.data || [];
    // }
    // 临时模拟数据
    installedModels.value = [
      { id: 1, name: 'best.pt' },
      { id: 2, name: 'yolo11l.pt' },
    ];
  } catch (error) {
    console.error('加载已安装模型失败:', error);
  }
}

// 安装YOLO11
async function handleInstall() {
  try {
    loading.install = true;
    // TODO: 调用后端API安装YOLO11
    createMessage.success('YOLO11安装任务已提交');
    await loadYOLO11Config();
  } catch (error) {
    console.error('安装YOLO11失败:', error);
    createMessage.error('安装YOLO11失败');
  } finally {
    loading.install = false;
  }
}

// 卸载YOLO11
async function handleUninstall() {
  try {
    loading.uninstall = true;
    // TODO: 调用后端API卸载YOLO11
    createMessage.success('YOLO11卸载成功');
    await loadYOLO11Config();
  } catch (error) {
    console.error('卸载YOLO11失败:', error);
    createMessage.error('卸载YOLO11失败');
  } finally {
    loading.uninstall = false;
  }
}

// YOLO11教程
function handleTutorial() {
  window.open('https://docs.ultralytics.com/', '_blank');
}

// 下载模型
async function handleDownload() {
  if (config.selectedSizes.length === 0) {
    createMessage.warning('请选择要下载的模型尺寸');
    return;
  }

  try {
    loading.download = true;
    // TODO: 调用后端API下载模型
    createMessage.success('模型下载任务已提交');
    await loadInstalledModels();
  } catch (error) {
    console.error('下载模型失败:', error);
    createMessage.error('下载模型失败');
  } finally {
    loading.download = false;
  }
}

// 刷新模型列表
async function handleRefresh() {
  try {
    loading.refresh = true;
    await loadInstalledModels();
    createMessage.success('刷新成功');
  } catch (error) {
    console.error('刷新模型列表失败:', error);
    createMessage.error('刷新失败');
  } finally {
    loading.refresh = false;
  }
}

// 删除模型
async function handleDeleteModel(modelId: number) {
  try {
    // TODO: 调用后端API删除模型
    createMessage.success('模型删除成功');
    await loadInstalledModels();
  } catch (error) {
    console.error('删除模型失败:', error);
    createMessage.error('删除模型失败');
  }
}

// 触发模型上传
const triggerModelUpload = () => {
  modelInput.value?.click();
};

// 处理模型选择
async function handleModelSelect(e: Event) {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    const file = target.files[0];
    try {
      // TODO: 调用后端API上传模型
      createMessage.success('模型上传成功');
      await loadInstalledModels();
    } catch (error) {
      console.error('上传模型失败:', error);
      createMessage.error('上传模型失败');
    }
  }
}

// 处理模型拖放
function handleModelDrop(e: DragEvent) {
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    const file = e.dataTransfer.files[0];
    if (file.name.endsWith('.pt') || file.name.endsWith('.onnx')) {
      handleModelSelect({ target: { files: [file] } } as any);
    } else {
      createMessage.error('只支持.pt和.onnx格式的模型文件');
    }
  }
}

// 取消
function handleCancel() {
  closeModal();
}
</script>

<style lang="less" scoped>
.modal-content {
  padding: 24px;
}

.modal-title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .title-icon {
    font-size: 18px;
  }
}

.collapse-header {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .collapse-icon {
    font-size: 16px;
  }
}

.about-content {
  padding: 16px 0;
  
  p {
    margin: 8px 0;
    color: #666;
    line-height: 1.8;
    
    strong {
      color: #333;
      font-size: 16px;
    }
  }
}

.installed-models-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 8px;
  background: #fafafa;
  
  .model-item {
    display: flex;
    align-items: center;
    padding: 8px;
    border-bottom: 1px solid #f0f0f0;
    transition: background 0.2s;
    
    &:hover {
      background: #f5f5f5;
    }
    
    &:last-child {
      border-bottom: none;
    }
    
    .model-icon {
      color: #52c41a;
      margin-right: 8px;
      font-size: 16px;
    }
    
    .model-name {
      flex: 1;
      font-size: 14px;
      color: #333;
    }

    .delete-model-btn {
      margin-left: 8px;
    }
  }
  
  .empty-models {
    padding: 20px;
    text-align: center;
    color: #999;
    font-size: 14px;
  }
}

.yolo-status-info {
  padding: 12px;
  background: #f0f9ff;
  border-radius: 4px;
  
  .status-item {
    margin-bottom: 8px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .status-label {
      font-size: 14px;
      color: #666;
      margin-right: 8px;
    }
    
    .status-value {
      font-size: 14px;
      color: #333;
    }
  }
}

.upload-area {
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: #fafafa;
  
  &:hover {
    border-color: #1890ff;
    background: #f0f7ff;
  }
  
  .upload-content {
    .upload-icon {
      font-size: 48px;
      color: #999;
      margin-bottom: 16px;
      display: block;
    }
    
    .upload-text {
      color: #666;
      font-size: 14px;
      margin: 0;
    }
  }
}

.model-upload-area {
  .upload-icon {
    font-size: 48px;
    color: #999;
  }
}
</style>
