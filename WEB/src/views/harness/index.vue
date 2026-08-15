<template>
  <div class="harness-page">
    <header class="harness-page__hero">
      <div class="harness-page__hero-inner">
        <div class="harness-page__title-block">
          <div class="harness-page__badge">
            <span class="harness-page__badge-dot" :class="{ 'is-online': health.online }" />
            {{ health.online ? '服务在线' : '服务未就绪' }}
          </div>
          <h1 class="harness-page__title">{{ appName }}</h1>
          <p class="harness-page__subtitle">
            请通过 IDEA 门户与 AI 助手组合使用（移动端仅显示聊天）。不再支持单独打开 HARNESS。
          </p>
        </div>
        <div class="harness-page__actions">
          <a-button type="primary" size="large" @click="openExternal">
            打开 IDEA + AI 助手
          </a-button>
          <a-button size="large" :loading="refreshing" @click="refreshHealth">
            刷新状态
          </a-button>
        </div>
      </div>
    </header>

    <section v-if="!health.online" class="harness-page__offline-banner">
      <a-alert
        type="warning"
        show-icon
        message="HARNESS 服务可能未启动"
        description="请执行 bash HARNESS/install.sh start，然后从 IDEA 门户打开 AI 助手。"
      />
    </section>

    <section class="harness-page__prompts">
        <span class="harness-page__prompts-label">快捷提问（点击复制，到 IDEA 门户聊天框粘贴）：</span>
        <div class="harness-page__chips">
          <button
            v-for="(item, idx) in prompts"
            :key="idx"
            type="button"
            class="harness-page__chip"
            @click="onCopyPrompt(item)"
          >
            {{ item }}
          </button>
        </div>
      </section>

      <section class="harness-page__frame-wrap harness-page__frame-wrap--cta">
        <div class="harness-page__cta">
          <p>AI 助手仅能在 IDEA 门户中使用</p>
          <a-button type="primary" size="large" @click="openExternal">进入门户</a-button>
        </div>
      </section>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  HARNESS_QUICK_PROMPTS,
  checkHarnessHealth,
  copyHarnessPrompt,
  getHarnessAppName,
  openHarnessPortal,
  type HarnessHealth,
} from '@/utils/harness'

defineOptions({ name: 'HarnessPortalPage' })

const appName = computed(() => getHarnessAppName())
const prompts = HARNESS_QUICK_PROMPTS
const health = reactive<HarnessHealth>({ online: false })
const refreshing = ref(false)

async function refreshHealth() {
  refreshing.value = true
  try {
    const result = await checkHarnessHealth()
    health.online = result.online
    health.status = result.status
    health.latencyMs = result.latencyMs
  } finally {
    refreshing.value = false
  }
}

function openExternal() {
  openHarnessPortal()
}

async function onCopyPrompt(text: string) {
  try {
    await copyHarnessPrompt(text)
    message.success('已复制，请到 IDEA 门户 AI 助手粘贴')
  } catch {
    message.info(text)
  }
}

onMounted(() => {
  refreshHealth()
})
</script>

<style scoped>
.harness-page {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 120px);
  margin: -12px -12px 0;
  background: #f8fafc;
}

.harness-page__hero {
  background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 45%, #2563eb 100%);
  color: #fff;
  padding: 28px 28px 24px;
  box-shadow: 0 8px 32px rgba(91, 33, 182, 0.22);
}

.harness-page__hero-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.harness-page__badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  font-size: 12px;
  letter-spacing: 0.02em;
  margin-bottom: 10px;
}

.harness-page__badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fbbf24;
  box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.35);
}

.harness-page__badge-dot.is-online {
  background: #34d399;
  box-shadow: 0 0 0 3px rgba(52, 211, 153, 0.35);
}

.harness-page__title {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.harness-page__subtitle {
  margin: 0;
  max-width: 640px;
  font-size: 14px;
  line-height: 1.65;
  color: rgba(255, 255, 255, 0.88);
}

.harness-page__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.harness-page__actions :deep(.ant-btn-primary) {
  background: #fff;
  color: #5b21b6;
  border: none;
  font-weight: 600;
}

.harness-page__actions :deep(.ant-btn-primary:hover) {
  background: #f5f3ff;
  color: #4c1d95;
}

.harness-page__actions :deep(.ant-btn-default) {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.35);
  color: #fff;
}

.harness-page__actions :deep(.ant-btn-default:hover) {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
  color: #fff;
}

.harness-page__offline-banner {
  padding: 12px 24px 0;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

.harness-page__cmd {
  display: inline-block;
  margin: 12px 0;
  padding: 10px 16px;
  border-radius: 8px;
  background: #1e293b;
  color: #e2e8f0;
  font-size: 13px;
  text-align: left;
}

.harness-page__hint {
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
}

.harness-page__prompts {
  padding: 16px 24px 8px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

.harness-page__prompts-label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 10px;
}

.harness-page__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.harness-page__chip {
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #334155;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 12px;
  line-height: 1.4;
  cursor: pointer;
  transition: all 0.2s ease;
  max-width: 100%;
  text-align: left;
}

.harness-page__chip:hover {
  border-color: #a78bfa;
  color: #5b21b6;
  background: #faf5ff;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.12);
}

.harness-page__frame-wrap {
  flex: 1;
  min-height: 520px;
  padding: 0 16px 16px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

.harness-page__frame-wrap--cta {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
}
.harness-page__cta {
  text-align: center;
  padding: 48px 24px;
  color: #475569;
}
.harness-page__cta p {
  margin: 0 0 16px;
  font-size: 15px;
}

.harness-page__frame {
  width: 100%;
  height: calc(100vh - 280px);
  min-height: 480px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
}

@media (max-width: 768px) {
  .harness-page__hero {
    padding: 20px 16px;
  }

  .harness-page__title {
    font-size: 22px;
  }

  .harness-page__frame {
    height: calc(100vh - 340px);
    min-height: 360px;
  }
}
</style>
