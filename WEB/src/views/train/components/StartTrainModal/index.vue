<template>
  <BasicModal
    @register="registerModal"
    title="训练参数配置"
    @cancel="handleCancel"
    :width="700"
    :canFullscreen="false"
  >
    <div class="modal-content">
      <div class="param-section">
        <h4 class="section-title">基础参数配置</h4>
        <div class="param-group">
          <label>迭代次数 (epochs)</label>
          <input type="number" v-model="params.epochs" min="10" max="1000"
                 class="param-input"/>
          <span class="hint">推荐值: 100-300</span>
        </div>

        <div class="param-group">
          <label>批量大小 (batch_size)</label>
          <input type="number" v-model="params.batch_size" min="1" :max="maxBatchSize"
                 class="param-input"/>
          <span class="hint">根据显存调整</span>
        </div>

        <div class="param-group">
          <label>图像尺寸 (imgsz)</label>
          <input type="number" v-model="params.imgsz" class="param-input"/>
          <span class="hint">默认640px</span>
        </div>
      </div>

      <div class="resource-selector">
        <h4 class="section-title">资源选择</h4>

        <div class="param-group">
          <label>预训练模型</label>
          <select v-model="selectedModel" class="resource-select">
            <option value="">默认模型 (yolov8n.pt)</option>
            <option v-for="model in modelList"
                    :key="model.id"
                    :value="model.model_path">
              {{ model.name }} ({{ model.version }})
            </option>
          </select>
        </div>
        <div class="param-group">
          <label>数据集配置</label>
          <select v-model="selectedDataset" class="resource-select">
            <option v-for="dataset in datasetList"
                    :key="dataset.id"
                    :value="dataset.zipUrl">
              {{ dataset.name }} ({{ dataset.description }})
            </option>
          </select>
        </div>
      </div>
    </div>
    <template #footer>
      <div class="modal-footer">
        <a-button @click="handleCancel">
          取消
        </a-button>
        <a-button type="primary" @click="startTrain">
          开始训练
        </a-button>
      </div>
    </template>
  </BasicModal>
</template>

<script lang="ts" setup>
import {reactive, ref} from 'vue'
import {BasicModal, useModalInner} from '@/components/Modal'
import {getModelPage} from '@/api/device/model'
import {getDatasetPage} from '@/api/device/dataset'
import {useMessage} from "@/hooks/web/useMessage";
import {t} from "@/hooks/web/useI18n";

// 定义模型项类型
interface ModelItem {
  id: string | number;
  name: string;
  version: string;
  model_path: string;
}

interface DatasetItem {
  id: string | number;
  name: string;
  description: string;
  zipUrl: string;
}

const { createMessage, notification } = useMessage()

const [registerModal, { closeModal }] = useModalInner(() => {
  loadModels()
  loadDatasets()
})

// 训练参数配置
const params = reactive({
  epochs: 100,
  batch_size: 16,
  imgsz: 640
})

const modelList = ref<ModelItem[]>([])
const datasetList = ref<DatasetItem[]>([])
const selectedModel = ref('')
const selectedDataset = ref('')
const maxBatchSize = ref(64)

const emit = defineEmits(['success'])

// 加载模型列表
const loadModels = async () => {
  try {
    const res = await getModelPage({ page: 1, size: 100 })
    modelList.value = res.data || []
    selectedModel.value = ''
  } catch (e) {
    createMessage.error(t('加载模型列表失败'))
    console.error('加载模型列表失败', e)
  }
}

// 加载数据集列表
const loadDatasets = async () => {
  try {
    const res = await getDatasetPage({ page: 1, size: 100 })
    datasetList.value = res.data.list || []
    if (datasetList.value.length) {
      selectedDataset.value = datasetList.value[0].zipUrl
    }
  } catch (e) {
    createMessage.error(t('加载数据集失败'))
    console.error('加载数据集失败', e)
  }
}

// 训练启动逻辑
const startTrain = () => {
  if (!selectedDataset.value) {
    createMessage.warn(t('请先选择数据集'))
    return
  }
  const modelPath = selectedModel.value || 'yolov8n.pt'
  const config = {
    ...params,
    modelPath,
    datasetPath: selectedDataset.value
  }
  emit('success', config)
  closeModal()
}

const handleCancel = () => closeModal()
</script>


<style scoped>
/* 基础容器 */
.modal-content {
  padding: 25px;
  background: #ffffff;
}

/* 分区标题 */
.section-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid transparent;
  border-image: linear-gradient(to right, #3498db, #2c3e50) 1;
}

/* 参数组网格布局 */
.param-group {
  display: grid;
  grid-template-columns: 160px 1fr auto;
  align-items: center;
  margin-bottom: 15px;
  gap: 12px;
}

/* 输入控件 */
.param-input, .resource-select {
  padding: 10px 14px;
  border: 1px solid #dce1e6;
  border-radius: 8px;
  background: #f8fafc;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.param-input:focus, .resource-select:focus {
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.3);
  background: white;
}

/* 按钮组 */
.btn-confirm {
  background: linear-gradient(135deg, #3498db, #2c3e50);
  border-radius: 6px;
  box-shadow: 0 4px 6px rgba(52, 152, 219, 0.2);
}

.btn-confirm:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(52, 152, 219, 0.3);
}

/* 响应式适配 */
@media (max-width: 768px) {
  .param-group {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .hint {
    grid-column: 1;
    margin-top: 4px;
  }
}
</style>
