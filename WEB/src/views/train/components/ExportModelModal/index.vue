<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="visible" class="modal-overlay" @click.self="closeModal">
        <div class="modal-content">
          <!-- 头部区域 -->
          <div class="modal-header">
            <h3>导出模型</h3>
            <button class="close-button" @click="closeModal">×</button>
          </div>

          <!-- 表单区域 -->
          <div class="modal-body">
            <div class="form-group">
              <label>模型路径 *</label>
              <div class="path-selector">
                <input
                  type="text"
                  v-model="form.model_path"
                  required
                  placeholder="输入模型文件路径"
                />
                <button type="button" @click="browseFile">
                  <i class="icon-folder"></i> 浏览
                </button>
              </div>
            </div>

            <div class="form-group">
              <label>导出格式 *</label>
              <select v-model="form.export_format">
                <option v-for="format in exportFormats" :key="format" :value="format">
                  {{ format.toUpperCase() }}
                </option>
              </select>
            </div>

            <!-- 高级设置区域 -->
            <div class="advanced-section">
              <h4 @click="showAdvanced = !showAdvanced">
                <i :class="['icon-arrow', { rotated: showAdvanced }]"></i>
                高级设置
              </h4>

              <div v-if="showAdvanced" class="advanced-options">
                <div class="form-group">
                  <label>ONNX Opset版本</label>
                  <input
                    type="number"
                    v-model="form.opset_version"
                    min="7"
                    max="17"
                    placeholder="11"
                  />
                </div>

                <div class="form-group">
                  <label>动态轴设置</label>
                  <div class="dynamic-axes">
                    <div v-for="(axis, index) in form.dynamic_axes" :key="index" class="axis-item">
                      <input
                        type="text"
                        v-model="axis.name"
                        placeholder="轴名称"
                      />
                      <input
                        type="text"
                        v-model="axis.dim"
                        placeholder="维度名称"
                      />
                      <button @click="removeAxis(index)" class="remove-axis">×</button>
                    </div>
                    <button @click="addAxis" class="add-axis">+ 添加动态轴</button>
                  </div>
                </div>

                <div class="form-group">
                  <label>常量折叠优化</label>
                  <label class="switch">
                    <input type="checkbox" v-model="form.do_constant_folding">
                    <span class="slider"></span>
                  </label>
                </div>
              </div>
            </div>

            <!-- 导出状态提示 -->
            <div v-if="exportStatus" class="export-status" :class="exportStatus.type">
              <i :class="statusIcon"></i>
              <span>{{ exportStatus.message }}</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="modal-footer">
            <button class="btn-cancel" @click="closeModal">取消</button>
            <button
              class="btn-confirm"
              @click="exportModel"
              :disabled="!isFormValid || isExporting"
            >
              <span v-if="isExporting">导出中...</span>
              <span v-else>开始导出</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import {computed, reactive, ref} from 'vue'
import {exportModel} from '@/api/device/model'
import {useMessage} from '@/hooks/web/useMessage'

const {createMessage} = useMessage()

const props = defineProps({
  visible: Boolean,
  initialModelPath: String
})

const emit = defineEmits(['close', 'success'])

// 表单数据
const form = reactive({
  model_path: props.initialModelPath || '',
  export_format: 'onnx',
  opset_version: 11,
  dynamic_axes: [],
  do_constant_folding: true
})

// 导出格式选项
const exportFormats = ref(['onnx', 'tensorrt', 'openvino', 'coreml'])

// 高级设置显示状态
const showAdvanced = ref(false)

// 导出状态
const exportStatus = ref(null)
const isExporting = ref(false)

// 验证表单
const isFormValid = computed(() => {
  return form.model_path.trim() !== '' &&
    form.export_format !== ''
})

// 状态图标
const statusIcon = computed(() => {
  if (!exportStatus.value) return ''
  return exportStatus.value.type === 'success' ? 'icon-check' : 'icon-error'
})

// 添加动态轴
const addAxis = () => {
  form.dynamic_axes.push({name: '', dim: ''})
}

// 移除动态轴
const removeAxis = (index) => {
  form.dynamic_axes.splice(index, 1)
}

// 浏览文件
const browseFile = () => {
  // 实际项目中接入文件系统API
  console.log('打开文件浏览器')
  form.model_path = '/path/to/model.pt'
}

// 导出模型
const exportModelHandler = async () => {
  if (!isFormValid.value) {
    createMessage.error('请填写必填字段')
    return
  }

  isExporting.value = true
  exportStatus.value = {
    type: 'info',
    message: '模型导出中，请稍候...'
  }

  try {
    // 准备导出参数
    const params = {
      model_path: form.model_path,
      export_format: form.export_format,
      opset_version: form.opset_version,
      dynamic_axes: form.dynamic_axes.filter(axis => axis.name && axis.dim),
      do_constant_folding: form.do_constant_folding
    }

    // 调用导出API
    const response = await exportModel(params)

    exportStatus.value = {
      type: 'success',
      message: `导出成功！模型ID: ${response.model_id}`
    }

    // 3秒后关闭模态框
    setTimeout(() => {
      emit('success', response)
      closeModal()
    }, 3000)
  } catch (error) {
    console.error('导出失败:', error)
    exportStatus.value = {
      type: 'error',
      message: `导出失败: ${error.message || '未知错误'}`
    }
  } finally {
    isExporting.value = false
  }
}

// 关闭模态框
const closeModal = () => {
  // 重置表单
  form.model_path = props.initialModelPath || ''
  form.export_format = 'onnx'
  form.opset_version = 11
  form.dynamic_axes = []
  form.do_constant_folding = true
  exportStatus.value = null
  isExporting.value = false
  showAdvanced.value = false

  emit('close')
}
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
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.path-selector {
  display: flex;
  gap: 10px;
}

.path-selector input {
  flex: 1;
}

.path-selector button {
  padding: 10px 15px;
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
}

.advanced-section {
  margin: 25px 0;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.advanced-section h4 {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-bottom: 15px;
}

.icon-arrow {
  display: inline-block;
  margin-right: 8px;
  transition: transform 0.3s;
}

.icon-arrow.rotated {
  transform: rotate(90deg);
}

.advanced-options {
  padding: 15px;
  background: #f9f9f9;
  border-radius: 4px;
}

.dynamic-axes {
  display: grid;
  gap: 10px;
}

.axis-item {
  display: flex;
  gap: 10px;
  align-items: center;
}

.axis-item input {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.remove-axis {
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
}

.add-axis {
  padding: 8px;
  background: #e6f7ff;
  color: #1890ff;
  border: 1px dashed #91d5ff;
  border-radius: 4px;
  cursor: pointer;
}

.switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #2196F3;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

.export-status {
  padding: 12px;
  border-radius: 4px;
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.export-status.info {
  background: #e6f7ff;
  color: #1890ff;
}

.export-status.success {
  background: #f6ffed;
  color: #52c41a;
}

.export-status.error {
  background: #fff2f0;
  color: #ff4d4f;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.btn-cancel, .btn-confirm {
  padding: 10px 20px;
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

.btn-confirm:disabled {
  background: #c0c0c0;
  cursor: not-allowed;
}

/* 过渡动画 */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.3s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
