<template>
  <div class="page images-page" :class="{ 'mode-build': mode === 'build' }">
    <div class="page-head">
      <div>
        <h1>镜像中心</h1>
        <p>{{ mode === 'manage' ? '核对本机 EasyAIoT 运行时镜像就绪情况' : '拉取预构建镜像，或执行本地构建 / 运行时构建' }}</p>
      </div>
      <div class="mode-switch" role="tablist" aria-label="镜像功能切换">
        <button
          type="button"
          class="mode-btn"
          :class="{ active: mode === 'manage' }"
          @click="mode = 'manage'"
        >
          本地管理
        </button>
        <button
          type="button"
          class="mode-btn"
          :class="{ active: mode === 'build' }"
          @click="mode = 'build'"
        >
          构建拉取
        </button>
      </div>
    </div>

    <ImagesManageView v-if="mode === 'manage'" embedded @goto-build="mode = 'build'" />
    <StackWorkspace
      v-else
      embedded
      category="image"
      title="构建拉取"
      subtitle="拉取预构建镜像、本地构建或构建运行时镜像"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ImagesManageView from './ImagesManageView.vue'
import StackWorkspace from '../components/StackWorkspace.vue'

const mode = ref<'manage' | 'build'>('manage')
</script>

<style scoped>
.images-page.mode-build {
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding-bottom: 0;
}

.images-page.mode-build :deep(.page.embedded) {
  flex: 1;
  min-height: 0;
}

.mode-switch {
  display: inline-flex;
  padding: 3px;
  border-radius: 8px;
  background: var(--c-fill);
  border: 1px solid var(--c-border);
  gap: 2px;
}

.mode-btn {
  min-width: 96px;
  height: 34px;
  padding: 0 16px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--c-text-2);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.mode-btn:hover {
  color: var(--c-text);
}

.mode-btn.active {
  background: var(--c-white);
  color: var(--c-primary);
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}
</style>
