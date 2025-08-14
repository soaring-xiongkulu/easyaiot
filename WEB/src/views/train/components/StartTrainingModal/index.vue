<template>
  <div v-if="visible" class="modal-overlay" @click.self="handleOverlayClick">
    <div class="modal-content">
      <!-- 标题区 -->
      <header class="modal-header">
        <slot name="header">
          <h3>{{ title }}</h3>
        </slot>
        <button class="close-button" @click="closeModal">×</button>
      </header>

      <!-- 参数配置区 -->
      <section class="modal-body">
        <div class="param-section">
          <h4>基础参数</h4>
          <div class="param-group">
            <label>迭代次数 (epochs)</label>
            <input type="number" v-model="params.epochs" min="10" max="1000"/>
            <span class="hint">范围: 10-1000 [3](@ref)</span>
          </div>

          <div class="param-group">
            <label>批量大小 (batch_size)</label>
            <input type="number" v-model="params.batch_size" min="16" :max="16 * 16"/>
          </div>

          <div class="param-group">
            <label>图像尺寸 (imgsz)</label>
            <input type="number" v-model="params.imgsz"/>
            <span class="hint">默认640px [3](@ref)</span>
          </div>
        </div>

        <div class="param-section">
          <h4>高级设置</h4>
          <div class="param-group">
            <label>初始学习率 (lr0)</label>
            <input type="number" step="0.001" v-model="params.lr0"/>
          </div>

          <div class="param-group">
            <label>优化器</label>
            <select v-model="params.optimizer">
              <option v-for="opt in optimizers" :key="opt" :value="opt">{{ opt }}</option>
            </select>
          </div>

          <div class="param-group">
            <label>主动学习</label>
            <input type="checkbox" v-model="params.activeLearning"/>
            <span v-if="params.activeLearning" class="hint">每次查询{{ params.querySize }}个样本 [1](@ref)</span>
          </div>
        </div>

        <div class="file-selector">
          <h4>资源选择</h4>
          <div class="param-group">
            <label>预训练模型</label>
            <button @click="selectModel">选择模型文件 (.pt)</button>
            <span>{{ modelPath || '未选择' }}</span>
          </div>

          <div class="param-group">
            <label>数据集配置</label>
            <button @click="selectDataset">选择配置文件 (.yaml)</button>
            <span>{{ datasetPath || '未选择' }}</span>
          </div>
        </div>
      </section>

      <!-- 操作区 -->
      <footer class="modal-footer">
        <button class="btn-cancel" @click="cancel">取消</button>
        <button class="btn-confirm" @click="startTraining">开始训练</button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import {reactive, ref} from 'vue'

const props = defineProps({
  title: {type: String, default: '训练参数配置'},
  visible: Boolean
})

const emit = defineEmits(['close', 'start-training'])

// 训练参数配置
const params = reactive({
  epochs: 100,
  batch_size: 16,
  imgsz: 640,
  lr0: 0.01,
  optimizer: 'AdamW',
  activeLearning: false,
  querySize: 100  // 主动学习每次查询样本数
})

const modelPath = ref('')
const datasetPath = ref('')
const optimizers = ref(['AdamW', 'SGD', 'Adam', 'RMSProp']) // 优化器选项 [3](@ref)

// 文件选择方法
const selectModel = () => {
  // 实际项目中接入文件系统API
  modelPath.value = '/models/pretrained_yolov8.pt'
}

const selectDataset = () => {
  // 实际项目中接入文件系统API
  datasetPath.value = '/datasets/coco.yaml'
}

// 训练启动逻辑
const startTraining = () => {
  if (!modelPath.value || !datasetPath.value) {
    alert('请先选择模型和数据集!')
    return
  }

  const config = {
    ...params,
    modelPath: modelPath.value,
    datasetPath: datasetPath.value
  }

  emit('start-training', config)
  closeModal()
}

// 模态框控制
const closeModal = () => emit('close')
const handleOverlayClick = () => closeModal()
const cancel = () => closeModal()
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 20px;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
  margin-bottom: 20px;
}

.param-section {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f5f5f5;
}

.param-group {
  margin: 12px 0;
  display: flex;
  align-items: center;
}

.param-group label {
  width: 180px;
  font-weight: 500;
}

.param-group input,
.param-group select {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.hint {
  margin-left: 10px;
  color: #888;
  font-size: 0.85em;
}

.file-selector button {
  background: #f0f0f0;
  border: 1px solid #ddd;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.btn-cancel, .btn-confirm {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-cancel {
  background: #f0f0f0;
  color: #333;
}

.btn-confirm {
  background: #007bff;
  color: white;
}
</style>
