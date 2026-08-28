<script lang="ts" setup>
/**
 * 流程设计页（隐藏路由 /flow/model/design/:id）：
 * 顶栏基本信息只读展示 + Simple 设计器画布 + 保存 / 保存并发布
 */
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Modal, Space, Tag, Tooltip } from 'ant-design-vue'
import { Icon } from '@/components/Icon'
import { FlowDesigner } from '../components/simple-process-design'
import type { SimpleFlowNode } from '../components/simple-process-design'
import { createStartUserNode } from '../components/simple-process-design'
import { deployModel, getModel, getModelSimple, updateModelSimple } from '@/api/flow/model'
import { useMessage } from '@/hooks/web/useMessage'

defineOptions({ name: 'FlowModelDesign' })

const route = useRoute()
const router = useRouter()
const { createMessage } = useMessage()

const modelId = route.params.id as string
const loading = ref(false)
const saving = ref(false)

const modelInfo = ref<Recordable>({})
const designerRef = ref<InstanceType<typeof FlowDesigner>>()
const flowTree = ref<SimpleFlowNode>()

onMounted(async () => {
  loading.value = true
  try {
    modelInfo.value = (await getModel(modelId)) ?? {}
    // 注意：/simple/get 直接返回 Simple 流程根节点（没有 simpleModel 包装字段），
    // 只有数据库没有编辑器源（新模型）时才回退到「仅发起人」占位结构
    const simpleRes = await getModelSimple(modelId).catch(() => null)
    flowTree.value = simpleRes ?? createStartUserNode()
  }
  finally {
    loading.value = false
  }
})

async function handleSave(): Promise<boolean> {
  const errors = designerRef.value?.validate() ?? []
  if (errors.length) {
    createMessage.error(errors[0])
    return false
  }
  saving.value = true
  try {
    await updateModelSimple({ id: modelId, simpleModel: flowTree.value })
    return true
  }
  finally {
    saving.value = false
  }
}

async function handleSaveDraft() {
  if (await handleSave()) {
    createMessage.success('保存成功')
  }
}

async function handleSaveAndDeploy() {
  if (!(await handleSave())) {
    return
  }
  Modal.confirm({
    title: '发布流程',
    content: '发布将生成新的流程定义版本，告警路由规则会引用最新版本。确认发布？',
    async onOk() {
      await deployModel(modelId)
      createMessage.success('发布成功')
      goBack()
    },
  })
}

/**
 * 返回上一页：从「告警管理 → 告警工单 → 流程模型」进入时回到双层 Tab 页；
 * 无浏览历史（如直接刷新进入设计页）时回退到流程模型列表
 */
function goBack() {
  if (window.history.state?.back) {
    router.back()
  } else {
    router.push('/flow/model')
  }
}

function handleBack() {
  goBack()
}
</script>

<template>
  <div class="flow-design-page">
    <div class="flow-design-page__bar">
      <div class="flow-design-page__left">
        <Button type="text" @click="handleBack">
          <template #icon>
            <Icon icon="ant-design:arrow-left-outlined" />
          </template>
        </Button>
        <div class="flow-design-page__info">
          <div class="flow-design-page__name">
            {{ modelInfo.name || '加载中…' }}
            <Tag v-if="modelInfo.key" color="blue" style="margin-left: 8px">{{ modelInfo.key }}</Tag>
          </div>
          <div class="flow-design-page__tip">
            点击节点配置审批人 / 条件；点击节点间的「+」插入节点
          </div>
        </div>
      </div>
      <Space>
        <Tooltip title="仅保存设计内容，不发布">
          <Button :loading="saving" @click="handleSaveDraft">保存草稿</Button>
        </Tooltip>
        <Button type="primary" :loading="saving" @click="handleSaveAndDeploy">
          <template #icon>
            <Icon icon="ant-design:cloud-upload-outlined" />
          </template>
          保存并发布
        </Button>
      </Space>
    </div>

    <div class="flow-design-page__body" v-loading="loading">
      <FlowDesigner ref="designerRef" v-model:value="flowTree" />
    </div>
  </div>
</template>

<style lang="less" scoped>
.flow-design-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 110px);

  &__bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 16px;
    background: #fff;
    border-bottom: 1px solid #eef0f4;
  }

  &__left {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  &__name {
    color: #1f2d3d;
    font-size: 15px;
    font-weight: 600;
  }

  &__tip {
    color: #8c94a5;
    font-size: 12px;
  }

  &__body {
    flex: 1;
    overflow: auto;
    background: #f5f7fa;
  }
}
</style>
