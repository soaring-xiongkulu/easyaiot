<template>
  <div class="deploy-service-card-list-wrapper">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm" @reset="handleSubmit"
                 @field-value-change="handleFieldValueChange"/>
    </div>
    <div class="bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 2, xs: 1, sm: 2, md: 4, lg: 5, xl: 6, xxl: 6 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div
              style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;">
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">部署服务列表</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem class="deploy-service-list-item">
              <div class="deploy-service-card-box">
                <div class="deploy-service-card-cont">
                  <!-- 模型标题：模型名称 + 版本号 -->
                  <h6 class="deploy-service-card-title">
                    <a>{{ getModelTitleWithVersion(item) }}</a>
                  </h6>

                  <!-- 状态标签和副本数 -->
                  <div class="status-format-wrapper">
                    <span class="status-tag" :class="`status-${item.status}`">
                      {{ getStatusText(item.status, item.running_count) }}
                    </span>
                    <span class="status-tag status-stopped" v-if="item.stopped_count !== undefined && item.stopped_count > 0">
                      停止中：{{ item.stopped_count }}
                    </span>
                    <span class="replica-tag" v-if="item.replica_count" @click="handleViewReplicas(item)">
                      副本数: {{ item.replica_count }}
                    </span>
                  </div>

                  <!-- 服务名称（带复制图标） -->
                  <div class="deploy-service-name">
                    <span class="service-name-value" :title="item.service_name">{{ getServiceNameDisplay(item.service_name) }}</span>
                    <CopyOutlined 
                      class="copy-icon" 
                      @click="copyToClipboard(item.service_name, '服务名称')"
                      title="复制服务名称"
                    />
                  </div>

                  <!-- 服务详情 -->
                  <div class="deploy-service-info">
                    <div class="info-item">
                      <span class="info-label">模型格式:</span>
                      <span class="info-value">{{ getFormatText(item) || '--' }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">模型名称:</span>
                      <span class="info-value">{{ item.model_name || '--' }}</span>
                    </div>
                    <div class="info-item">
                      <span class="info-label">模型版本:</span>
                      <span class="info-value">{{ item.model_version || '--' }}</span>
                    </div>
                  </div>

                  <!-- 操作按钮 -->
                  <div class="btns">
                    <div class="btn-group">
                      <div
                        class="btn"
                        @click="handleStart(item)"
                        :class="{ disabled: item.status === 'running' }"
                        title="批量启动"
                      >
                        <PlayCircleOutlined style="font-size: 16px;"/>
                      </div>
                      <div
                        class="btn"
                        @click="handleStop(item)"
                        :class="{ disabled: item.status !== 'running' }"
                        title="批量停止"
                      >
                        <StopOutlined style="font-size: 16px;"/>
                      </div>
                      <div
                        class="btn"
                        @click="handleRestart(item)"
                        :class="{ disabled: item.status !== 'running' }"
                        title="批量重启"
                      >
                        <ReloadOutlined style="font-size: 16px;"/>
                      </div>
                      <Popconfirm
                        title="确定删除此部署服务?"
                        @confirm="handleDelete(item)"
                      >
                        <div class="btn" title="删除服务">
                          <DeleteOutlined style="font-size: 16px;"/>
                        </div>
                      </Popconfirm>
                    </div>
                  </div>
                </div>
              </div>
            </ListItem>
          </template>
        </List>
      </Spin>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, reactive, ref, watch} from 'vue';
import {List, Popconfirm, Spin, Tag} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {
  DeleteOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
  StopOutlined,
  CopyOutlined
} from '@ant-design/icons-vue';
import {useMessage} from '@/hooks/web/useMessage';
const {createMessage} = useMessage();
import {
  deleteDeployService,
  getModelPage,
  batchStartDeployService,
  batchStopDeployService,
  batchRestartDeployService,
  getDeployServiceReplicas
} from '@/api/device/model';
import {getFormConfig} from '../DeployService/Data';

defineOptions({name: 'DeployServiceCardList'})

const ListItem = List.Item;

const props = defineProps({
  params: propTypes.object.def({}),
  api: propTypes.func,
});

const emit = defineEmits(['getMethod', 'field-value-change', 'viewReplicas']);


const data = ref([]);
const state = reactive({
  loading: true,
});

// 模型选项列表
const modelOptions = ref<any[]>([]);

// 加载模型列表
const loadModelOptions = async () => {
  try {
    const res = await getModelPage({pageNo: 1, pageSize: 1000});
    const models = res.data || [];
    modelOptions.value = models.map((model) => ({
      label: `${model.name} (${model.version})`,
      value: model.id,
    }));
  } catch (error) {
    console.error('获取模型列表失败:', error);
    modelOptions.value = [];
  }
};

// 先定义handleSubmit函数
async function handleSubmit() {
  const formData = await validate();
  await fetch(formData);
}

const formConfig = getFormConfig(modelOptions.value);
const [registerForm, {validate, updateSchema}] = useForm({
  schemas: formConfig.schemas || [],
  labelWidth: formConfig.labelWidth || 80,
  baseColProps: formConfig.baseColProps || {span: 6},
  actionColOptions: formConfig.actionColOptions || {span: 6},
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

onMounted(async () => {
  await loadModelOptions();
  // 更新表单配置中的模型选项
  updateSchema({
    field: 'model_id',
    componentProps: {
      options: [
        {label: '全部', value: ''},
        ...modelOptions.value,
      ],
    },
  });
  fetch();
  emit('getMethod', fetch);
});

// 监听params变化，自动刷新数据
watch(() => props.params, () => {
  fetch();
}, {deep: true});

// 处理表单字段值变化，实时通知父组件
function handleFieldValueChange(field: string, value: any) {
  emit('field-value-change', field, value);
}

async function fetch(p = {}) {
  const {api, params} = props;
  if (api && isFunction(api)) {
    state.loading = true;
    try {
      // 转换参数格式：page -> pageNo, pageSize -> pageSize
      const requestParams = {
        ...params,
        pageNo: page.value,
        pageSize: pageSize.value,
        ...p
      };
      // 将model_id传递给后端，如果为空则删除该参数
      if (requestParams.model_id === '' || requestParams.model_id === undefined) {
        delete requestParams.model_id;
      }
      const res = await api(requestParams);

      // 处理返回格式：后端返回 { code: 0, data: [...], total: ... }
      if (res && res.data) {
        data.value = Array.isArray(res.data) ? res.data : [];
        total.value = res.total || 0;
      } else if (res && res.success && res.data) {
        // 兼容其他可能的返回格式
        data.value = res.data.items || res.data.list || (Array.isArray(res.data) ? res.data : []);
        total.value = res.data.total || res.total || 0;
      } else {
        data.value = [];
        total.value = 0;
      }
    } catch (error) {
      console.error('获取部署服务列表失败:', error);
      data.value = [];
      total.value = 0;
    } finally {
      state.loading = false;
    }
  }
}

const page = ref(1);
const pageSize = ref(18);
const total = ref(0);
const paginationProp = ref({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize,
  current: page,
  total,
  showTotal: (total: number) => `总 ${total} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange,
});

function pageChange(p: number, pz: number) {
  page.value = p;
  pageSize.value = pz;
  fetch();
}

function pageSizeChange(_current: number, size: number) {
  pageSize.value = size;
  fetch();
}

function formatDateTime(dateString: string) {
  if (!dateString) return '--';
  try {
    // 解析ISO格式时间字符串（可能包含时区信息）
    const date = new Date(dateString);
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      return dateString;
    }
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  } catch (e) {
    return dateString;
  }
}

function getStatusText(status: string, runningCount?: number) {
  const textMap: Record<string, string> = {
    'running': '运行中',
    'stopped': '已停止'
  };
  const baseText = textMap[status] || status || '未知';
  // 如果是运行中状态且有running_count，显示"运行中：3"格式
  if (status === 'running' && runningCount !== undefined && runningCount > 0) {
    return `${baseText}：${runningCount}`;
  }
  return baseText;
}

// 获取模型格式文本
function getFormatText(item: any): string {
  // 优先使用 format 字段
  if (item.format) {
    const formatMap: Record<string, string> = {
      'onnx': 'ONNX',
      'openvino': 'OpenVINO',
      'pytorch': 'PyTorch',
      'torchscript': 'TorchScript',
      'tensorrt': 'TensorRT',
      'tflite': 'TensorFlow Lite',
      'coreml': 'CoreML'
    };
    const formatLower = item.format.toLowerCase();
    return formatMap[formatLower] || formatLower.toUpperCase();
  }
  
  // 根据模型路径判断格式（降级方案）
  if (item.model_path) {
    const path = item.model_path.toLowerCase();
    if (path.endsWith('.onnx')) {
      return 'ONNX';
    }
    if (path.endsWith('.pt') || path.endsWith('.pth')) {
      return 'PyTorch';
    }
    if (path.includes('openvino')) {
      return 'OpenVINO';
    }
    if (path.endsWith('.tflite')) {
      return 'TensorFlow Lite';
    }
  }
  
  // 默认返回空字符串
  return '';
}

// 获取模型标题：模型名称 + 版本号
function getModelTitleWithVersion(item: any): string {
  const modelName = item.model_name || '未知模型';
  const version = item.model_version || item.version || '';
  
  if (version) {
    // 如果版本号没有 v 前缀，则添加
    const versionText = version.startsWith('v') ? version : `v${version}`;
    return `${modelName} ${versionText}`;
  }
  
  return modelName;
}

// 显示完整的服务名称
function getServiceNameDisplay(serviceName: string): string {
  if (!serviceName || serviceName === '--') {
    return '--';
  }
  
  // 直接返回完整的服务名称
  return serviceName;
}

// 复制到剪贴板
function copyToClipboard(text: string, label: string) {
  if (!text || text === '--') {
    createMessage.warning(`${label}为空，无法复制`);
    return;
  }
  
  navigator.clipboard.writeText(text).then(() => {
    createMessage.success(`${label}已复制到剪贴板`);
  }).catch(() => {
    // 降级方案
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      createMessage.success(`${label}已复制到剪贴板`);
    } catch (err) {
      createMessage.error('复制失败，请手动复制');
    }
    document.body.removeChild(textArea);
  });
}

// 生成并复制测试命令
function copyTestCommand(item: any) {
  const serverIp = item.server_ip || 'localhost';
  const port = item.port || '8889';
  const testCommand = `curl -X POST -F 'file=@your_image.jpg' http://${serverIp}:${port}/inference`;
  
  copyToClipboard(testCommand, '测试命令');
}

// 批量启动服务
const handleStart = async (record: any) => {
  if (record.status === 'running') return;
  try {
    const result = await batchStartDeployService(record.service_name);
    
    // 现在 API 返回完整响应对象（包含 code、msg、data）
    // 当 isTransformResponse: false 时，实际数据在 result.data 中
    const responseData = result?.data || {};
    if (result && responseData.code === 0) {
      const data = responseData.data || {};
      const successCount = data.success_count || 0;
      const failCount = data.fail_count || 0;
      const errors = data.errors || [];
      
      // 优先使用后台返回的 msg
      if (responseData.msg) {
        // 根据成功/失败情况选择消息类型
        if (failCount === 0) {
          createMessage.success(responseData.msg);
        } else if (successCount === 0) {
          createMessage.error(responseData.msg);
        } else {
          createMessage.warning(responseData.msg);
        }
      } else {
        // 如果后台没有返回 msg，则根据数据判断
        // 如果全部成功
        if (failCount === 0) {
          createMessage.success('批量启动成功');
        } 
        // 如果全部失败
        else if (successCount === 0) {
          // 检查是否是模型文件相关错误
          let errorMessage = '批量启动失败';
          
          if (errors.length > 0) {
            const hasModelError = errors.some(err => 
              err.includes('MinIO') || 
              err.includes('Minio') || 
              err.includes('模型文件不存在') || 
              err.includes('模型文件下载失败')
            );
            
            if (hasModelError) {
              errorMessage = '模型不存在，启动失败';
            } else {
              // 其他错误，显示第一个错误信息
              errorMessage = errors[0] || '批量启动失败';
            }
          }
          
          createMessage.error(errorMessage);
        } 
        // 如果部分成功部分失败
        else {
          // 检查是否有模型文件相关错误
          let warningMessage = `批量启动部分成功：成功 ${successCount} 个，失败 ${failCount} 个`;
          
          if (errors.length > 0) {
            const hasModelError = errors.some(err => 
              err.includes('MinIO') || 
              err.includes('Minio') || 
              err.includes('模型文件不存在') || 
              err.includes('模型文件下载失败')
            );
            
            if (hasModelError) {
              warningMessage = `部分服务启动失败：模型不存在，启动失败（成功 ${successCount} 个，失败 ${failCount} 个）`;
            }
          }
          
          createMessage.warning(warningMessage);
        }
      }
    } else {
      console.log(JSON.stringify(result))
      // code !== 0 的情况
      createMessage.error(responseData?.msg || '批量启动失败');
    }
    
    fetch();
  } catch (error: any) {
    // 如果进入 catch，说明请求失败
    console.error('批量启动异常:', error);
    const errorData = error?.response?.data || error?.data || {};
    const errorMsg = errorData.msg || error?.message || '批量启动失败，请检查网络连接';
    createMessage.error(`批量启动失败：${errorMsg}`);
  }
};

// 批量停止服务
const handleStop = async (record: any) => {
  if (record.status !== 'running') return;
  try {
    const result = await batchStopDeployService(record.service_name);
    // 当 isTransformResponse: false 时，实际数据在 result.data 中
    const responseData = result?.data || {};
    if (responseData.code === 0) {
      createMessage.success(responseData.msg || '批量停止成功');
    } else {
      createMessage.error(responseData.msg || '批量停止失败');
    }
    fetch();
  } catch (error) {
    createMessage.error('批量停止失败');
    console.error('批量停止失败:', error);
  }
};

// 批量重启服务
const handleRestart = async (record: any) => {
  if (record.status !== 'running') return;
  try {
    const result = await batchRestartDeployService(record.service_name);
    // 当 isTransformResponse: false 时，实际数据在 result.data 中
    const responseData = result?.data || {};
    if (responseData.code === 0) {
      createMessage.success(responseData.msg || '批量重启成功');
    } else {
      createMessage.error(responseData.msg || '批量重启失败');
    }
    fetch();
  } catch (error) {
    createMessage.error('批量重启失败');
    console.error('批量重启失败:', error);
  }
};

// 删除服务
const handleDelete = async (record: any) => {
  try {
    await deleteDeployService(record.id);
    createMessage.success('删除成功');
    fetch();
  } catch (error) {
    createMessage.error('删除失败');
    console.error('删除失败:', error);
  }
};

// 查看副本详情
const handleViewReplicas = async (record: any) => {
  emit('viewReplicas', record);
};
</script>

<style lang="less" scoped>
.deploy-service-card-list-wrapper {
  :deep(.ant-list-header) {
    border: 0;
    padding: 16px 20px;
    background: transparent;
  }

  :deep(.ant-list) {
    padding: 8px;
  }

  :deep(.ant-list-item) {
    margin: 8px;
    padding: 0 !important;
  }
}

.deploy-service-list-item {
  padding: 0 !important;
  height: 100%;
  display: flex;
}

.deploy-service-card-box {
  background: #FFFFFF;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06);
  height: 100%;
  width: 100%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 260px;
  border: 1px solid rgba(0, 0, 0, 0.06);

  &:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12), 0 2px 4px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
    border-color: rgba(0, 0, 0, 0.1);
  }
}

.deploy-service-card-cont {
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
}

.status-format-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.status-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
  border: 1px solid;

  &.status-running {
    background: #f6ffed;
    border-color: #b7eb8f;
    color: #52c41a;
  }

  &.status-stopped {
    background: #fafafa;
    border-color: #d9d9d9;
    color: #8c8c8c;
  }
}

.replica-tag {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
  border: 1px solid;
  background: #e6f7ff;
  border-color: #91d5ff;
  color: #1890ff;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: #bae7ff;
    border-color: #69c0ff;
    color: #0050b3;
  }
}

.format-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  color: #1890ff;
  font-weight: 500;
  white-space: nowrap;
}

.deploy-service-card-title {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.5em;
  color: #1a1a1a;
  margin-bottom: 8px;
  flex-shrink: 0;
  min-height: 24px;
  display: flex;
  align-items: flex-start;

  a {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    color: #1a1a1a;
    transition: color 0.2s;
    word-break: break-word;
    line-height: 1.5em;
    max-height: 3em;
    overflow: hidden;
    font-weight: 600;

    &:hover {
      color: #1890ff;
    }
  }
}

.deploy-service-name {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 12px;
  padding: 6px 10px;
  background: #fafafa;
  border-radius: 6px;
  flex-shrink: 0;

  .service-name-label {
    font-size: 12px;
    color: #8c8c8c;
    font-weight: 500;
    flex-shrink: 0;
  }

  .service-name-value {
    flex: 1;
    font-size: 13px;
    color: #262626;
    word-break: break-all;
    line-height: 1.4;
  }

  .copy-icon {
    font-size: 14px;
    color: #8c8c8c;
    cursor: pointer;
    flex-shrink: 0;
    transition: color 0.2s;
    margin-top: 2px;

    &:hover {
      color: #1890ff;
    }
  }
}

.deploy-service-info {
  font-size: 13px;
  color: #595959;
  line-height: 1.5;
  margin-bottom: 10px;
  flex: 1;
  min-height: 80px;

  .info-item {
    display: flex;
    margin-bottom: 8px;
    align-items: flex-start;

    .info-label {
      min-width: 70px;
      font-weight: 500;
      color: #8c8c8c;
      flex-shrink: 0;
    }

    .info-value {
      flex: 1;
      word-break: break-word;
      color: #262626;
      font-weight: 400;

      &.ellipsis {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    .inference-endpoint-url {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 6px;

      .info-value {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        min-width: 0;
      }

      .copy-icon {
        font-size: 14px;
        color: #8c8c8c;
        cursor: pointer;
        flex-shrink: 0;
        transition: color 0.2s;

        &:hover {
          color: #1890ff;
        }
      }

      .copy-test-command-icon {
        font-size: 13px;
        color: #1890ff;
        
        &:hover {
          color: #40a9ff;
        }
      }
    }
  }
}

.btns {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  flex-shrink: 0;
  margin-top: auto;
  border-top: 1px solid #f0f0f0;
}

.btn-group {
  display: flex;
  gap: 10px;
  width: 100%;
  justify-content: center;
}

.btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid #e8e8e8;

  &:hover:not(.disabled) {
    background: #262626;
    border-color: #262626;
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);

    .anticon {
      color: #fff;
    }
  }

  &.disabled {
    opacity: 0.4;
    cursor: not-allowed;
    background: #f5f5f5;
  }

  .anticon {
    color: #8c8c8c;
    font-size: 16px;
    transition: color 0.25s;
  }
}

:deep(.ant-tag) {
  border-radius: 6px;
  font-size: 12px;
  padding: 2px 10px;
  height: 26px;
  line-height: 22px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 1;
  max-width: 100%;
  border: none;
  font-weight: 500;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.service-id-tag {
  background: #fafafa;
  color: #595959;
  border: 1px solid #e8e8e8;
  font-size: 12px;
  padding: 2px 10px;
  height: 24px;
  line-height: 20px;
}

</style>
