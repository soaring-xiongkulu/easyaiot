<template>
  <div class="idea-jump">
    <h2>在线 IDEA</h2>
    <p>
      操作台在独立门户（默认 :9300）。也可点右下角悬浮球新开页面；右键悬浮球可隐藏，鼠标移到屏幕右侧边缘可再唤出。
    </p>
    <a-button type="primary" @click="openPortal">打开 IDEA 门户</a-button>
  </div>
</template>

<script lang="ts" setup>
import { getIdeaPortalUrl } from '@/utils/idea'

defineOptions({ name: 'IdeaPortalJump' })

function openPortal() {
  window.open(getIdeaPortalUrl(), '_blank', 'noopener,noreferrer')
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
