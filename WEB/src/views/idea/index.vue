<template>
  <div class="idea-jump">
    <h2>在线 IDEA</h2>
    <p>
      完整编辑器在独立门户（默认 :9300）。门户工具栏可打开右侧 HARNESS AI 助手，与 code-server 分屏协作。
    </p>
    <a-space>
      <a-button type="primary" @click="openPortal()">打开 IDEA 门户</a-button>
      <a-button @click="openPortal(true)">打开并显示 AI 助手</a-button>
    </a-space>
  </div>
</template>

<script lang="ts" setup>
import { getIdeaPortalUrl } from '@/utils/idea'

defineOptions({ name: 'IdeaPortalJump' })

function openPortal(withHarness = false) {
  const base = getIdeaPortalUrl()
  const url = withHarness ? `${base}/?harness=1` : base
  window.open(url, '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
.idea-jump {
  padding: 48px 24px;
  text-align: center;
}
.idea-jump h2 {
  margin-bottom: 12px;
}
.idea-jump p {
  max-width: 560px;
  margin: 0 auto 24px;
  color: #6b7280;
  line-height: 1.6;
}
</style>
