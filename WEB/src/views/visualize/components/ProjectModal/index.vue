<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    width="1100"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    destroy-on-close
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleCancel">{{ state.isView ? '关闭' : '取消' }}</Button>
        <Button
          v-if="state.isView && state.recordId && !isDemoScada"
          type="default"
          @click="handleOpenEditor"
        >
          {{ isTwinProject(state.projectType) ? '打开数字孪生' : isScadaProject(state.projectType) ? '打开组态编辑器' : '打开编辑器' }}
        </Button>
        <Button
          v-if="state.isView && state.recordId && isDemoScada"
          type="default"
          @click="handleOpenPreview"
        >
          预览组态（只读）
        </Button>
        <Button v-if="!state.isView" type="primary" :loading="state.editLoading" @click="handleOk">
          保存
        </Button>
      </div>
    </template>

    <Spin :spinning="state.editLoading">
      <div class="visualize-drawer">
        <div class="drawer-hero" :class="{ 'drawer-hero--scada': isScadaProject(state.projectType) }">
          <img v-if="previewUrl" :src="previewUrl" alt="项目封面" class="hero-image" @error="onPreviewError" />
          <div v-else class="hero-empty">
            <span>{{ isScadaProject(state.projectType) ? '组态项目封面' : '项目封面预览' }}</span>
            <p>{{ isScadaProject(state.projectType) ? 'FUXA Web 组态（SCADA/HMI）' : '填写缩略图地址后将在此展示' }}</p>
          </div>
        </div>

        <div class="drawer-body">
          <div class="section-title">基本信息</div>
          <BasicForm @register="registerForm" @field-value-change="onFieldChange" />
        </div>
      </div>
    </Spin>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, reactive, ref } from 'vue'
import { BasicDrawer, useDrawerInner } from '@/components/Drawer'
import { BasicForm, useForm } from '@/components/Form'
import { Spin } from 'ant-design-vue'
import { useMessage } from '@/hooks/web/useMessage'
import {
  createVisualizeProject,
  getVisualizeProject,
  updateVisualizeProject,
} from '@/api/device/visualize'
import {
  VISUALIZE_PROJECT_TYPE_OPTIONS,
  getProjectTypeLabel,
  isFuxaDemoProject,
  isScadaProject,
  isTwinProject,
  openVisualizeEditor,
} from '@/utils/visualizeEditor'
import { Button } from '@/components/Button'

defineOptions({ name: 'VisualizeProjectDrawer' })

const { createMessage } = useMessage()
const emits = defineEmits(['success', 'register'])

const previewUrl = ref('')
const previewBroken = ref(false)

const state = reactive({
  isEdit: false,
  isView: false,
  editLoading: false,
  recordId: null as number | null,
  projectType: 'dashboard' as string,
  projectName: '' as string,
  editorRef: '' as string,
})

const getTitle = computed(() => {
  const typeLabel = getProjectTypeLabel(state.projectType)
  if (state.isEdit) return `编辑${typeLabel}项目`
  if (state.isView) return `查看${typeLabel}项目`
  return '新增项目'
})

const isDemoScada = computed(() =>
  isFuxaDemoProject({
    id: state.recordId,
    projectType: state.projectType,
    projectName: state.projectName,
    editorRef: state.editorRef,
  }),
)

const [registerForm, { setFieldsValue, validate, resetFields, setProps, updateSchema, getFieldsValue }] = useForm({
  labelWidth: 120,
  baseColProps: { span: 24 },
  showActionButtonGroup: false,
  schemas: [
    {
      field: 'projectName',
      label: '项目名称',
      component: 'Input',
      required: true,
      colProps: { span: 12 },
      componentProps: { placeholder: '请输入项目名称', maxlength: 128 },
    },
    {
      field: 'projectType',
      label: '项目类型',
      component: 'Select',
      required: true,
      defaultValue: 'dashboard',
      colProps: { span: 12 },
      componentProps: {
        options: VISUALIZE_PROJECT_TYPE_OPTIONS,
        placeholder: '请选择项目类型',
        onChange: (val: string) => {
          state.projectType = val || 'dashboard'
          syncEditorRefSchema()
          ensureScadaEditorRefDefault(val)
        },
      },
    },
    {
      field: 'state',
      label: '发布状态',
      component: 'Select',
      colProps: { span: 12 },
      ifShow: () => state.isView || state.isEdit,
      componentProps: {
        disabled: true,
        options: [
          { value: -1, label: '未发布' },
          { value: 1, label: '已发布' },
        ],
      },
    },
    {
      field: 'editorRef',
      label: '运行时引用',
      component: 'Input',
      colProps: { span: 12 },
      ifShow: () => isScadaProject(state.projectType) || isTwinProject(state.projectType),
      componentProps: {
        placeholder: '组态填 FUXA 画面名；数字孪生填 industrial / campus / port / energy',
        maxlength: 256,
      },
    },
    {
      field: 'indexImage',
      label: '缩略图地址',
      component: 'Input',
      componentProps: {
        placeholder: '填写可访问的封面图 URL',
        onChange: (e: any) => {
          previewBroken.value = false
          previewUrl.value = e?.target?.value || ''
        },
      },
    },
    {
      field: 'remarks',
      label: '备注',
      component: 'InputTextArea',
      componentProps: { placeholder: '请输入备注', rows: 4, maxlength: 512 },
    },
  ],
})

const [register, { closeDrawer }] = useDrawerInner(async (data) => {
  const { isEdit, isView, record } = data || {}
  state.isEdit = !!isEdit
  state.isView = !!isView
  state.recordId = record?.id ?? null
  setProps({ disabled: state.isView })

  if (state.isEdit || state.isView) {
    await loadDetail(record)
  } else {
    resetFormState()
  }
  syncEditorRefSchema()
  // 类型创建后不可改
  updateSchema({
    field: 'projectType',
    componentProps: {
      options: VISUALIZE_PROJECT_TYPE_OPTIONS,
      disabled: state.isEdit || state.isView,
      placeholder: '请选择项目类型',
      onChange: (val: string) => {
        state.projectType = val || 'dashboard'
        syncEditorRefSchema()
        ensureScadaEditorRefDefault(val)
      },
    },
  })
})

function ensureScadaEditorRefDefault(projectType?: string) {
  if (!isScadaProject(projectType) || state.isEdit || state.isView) return
  const cur = (getFieldsValue?.() || {}) as Recordable
  // 默认用项目名作为 FUXA 画面名；未填项目名时留空，打开时再回退
  if (!cur.editorRef) {
    const name = (cur.projectName || '').trim()
    if (name) {
      setFieldsValue({ editorRef: name })
    }
  }
}

function syncEditorRefSchema() {
  updateSchema({
    field: 'editorRef',
    ifShow: () => isScadaProject(state.projectType) || isTwinProject(state.projectType),
  })
}

function onFieldChange(key: string, value: any) {
  if (key === 'indexImage') {
    previewBroken.value = false
    previewUrl.value = value || ''
  }
  if (key === 'projectType') {
    state.projectType = value || 'dashboard'
    syncEditorRefSchema()
    ensureScadaEditorRefDefault(value)
  }
}

function onPreviewError() {
  previewBroken.value = true
  previewUrl.value = ''
}

function resetFormState() {
  resetFields()
  state.recordId = null
  state.projectType = 'dashboard'
  state.projectName = ''
  state.editorRef = ''
  previewUrl.value = ''
  previewBroken.value = false
  setFieldsValue({ projectType: 'dashboard', editorRef: '' })
}

async function loadDetail(record: any) {
  try {
    state.editLoading = true
    let detail = record
    if (record?.id) {
      try {
        detail = (await getVisualizeProject(record.id)) || record
      } catch {
        detail = record
      }
    }
    state.recordId = detail?.id ?? null
    state.projectType = detail?.projectType || 'dashboard'
    state.projectName = detail?.projectName ?? ''
    state.editorRef = detail?.editorRef ?? ''
    previewUrl.value = detail?.indexImage ?? ''
    previewBroken.value = false
    await setFieldsValue({
      projectName: detail?.projectName ?? '',
      projectType: detail?.projectType || 'dashboard',
      editorRef: detail?.editorRef ?? '',
      indexImage: detail?.indexImage ?? '',
      remarks: detail?.remarks ?? '',
      state: detail?.state ?? -1,
    })
  } catch (error) {
    console.error(error)
    createMessage.error('加载项目信息失败')
  } finally {
    state.editLoading = false
  }
}

function handleCancel() {
  resetFormState()
  closeDrawer()
}

function handleOpenEditor() {
  if (!state.recordId) return
  try {
    const values = (getFieldsValue?.() || {}) as Recordable
    openVisualizeEditor(state.recordId, 'edit', {
      projectType: state.projectType,
      editorRef: values.editorRef,
      projectName: values.projectName,
    })
  } catch (e: any) {
    createMessage.error(e?.message || '打开编辑器失败')
  }
}

function handleOpenPreview() {
  if (!state.recordId) return
  try {
    const values = (getFieldsValue?.() || {}) as Recordable
    openVisualizeEditor(state.recordId, 'preview', {
      projectType: state.projectType,
      editorRef: values.editorRef,
      projectName: values.projectName,
    })
  } catch (e: any) {
    createMessage.error(e?.message || '打开预览失败')
  }
}

async function handleOk() {
  try {
    const values = await validate()
    state.editLoading = true
    if (state.isEdit && state.recordId) {
      await updateVisualizeProject({
        id: state.recordId,
        projectName: values.projectName,
        indexImage: values.indexImage,
        remarks: values.remarks,
        editorRef: values.editorRef,
      })
      createMessage.success('更新成功')
    } else {
      const id = await createVisualizeProject({
        projectName: values.projectName,
        projectType: values.projectType || 'dashboard',
        indexImage: values.indexImage,
        remarks: values.remarks,
        editorRef: values.editorRef,
      })
      createMessage.success('创建成功')
      state.recordId = id
      state.projectType = values.projectType || 'dashboard'
    }
    emits('success')
    closeDrawer()
  } catch (error) {
    console.error(error)
  } finally {
    state.editLoading = false
  }
}
</script>

<style lang="less" scoped>
.visualize-drawer {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100%;
}

.drawer-hero {
  width: 100%;
  height: 240px;
  border-radius: 8px;
  overflow: hidden;
  background: linear-gradient(145deg, #eef3ff 0%, #dce7ff 50%, #c5d6ff 100%);
  box-shadow: 0 1px 4px rgba(24, 24, 24, 0.08);

  &--scada {
    background: linear-gradient(145deg, #e8f7f0 0%, #d4efe3 50%, #b8e0d0 100%);
  }
}

.hero-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.hero-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #266cfb;

  span {
    font-size: 16px;
    font-weight: 600;
  }

  p {
    margin: 8px 0 0;
    font-size: 13px;
    color: #8c8c8c;
  }
}

.drawer-hero--scada .hero-empty {
  color: #1a8f5c;
}

.drawer-body {
  padding: 4px 4px 12px;
}

.section-title {
  margin-bottom: 16px;
  padding-left: 10px;
  border-left: 3px solid #266cfb;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.2;
  color: #181818;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}
</style>
