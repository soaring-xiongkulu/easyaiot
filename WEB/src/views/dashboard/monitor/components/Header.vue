<template>
  <div class="monitor-header">
    <div class="header-left">
      <div class="date-time">
        {{ currentDate }} {{ currentDay }}
      </div>
    </div>
    
    <div class="header-center">
      <div class="title-row">
        <h1 class="platform-title">{{ dashboardTitle }}</h1>
        <PlatformBrandingFab />
      </div>
    </div>
    
    <div class="header-right">
      <div class="user-info">
        <span class="user-role" @click="handleGoToAdmin">管理后台</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAdminHomeRoute } from '@/utils/deployProfile'
import { usePlatformBranding } from '@/hooks/web/usePlatformBranding'
import PlatformBrandingFab from './PlatformBrandingFab.vue'

defineOptions({
  name: 'MonitorHeader'
})

defineProps<{
  activeVideos?: any[]
}>()

const router = useRouter()
const { config } = usePlatformBranding()
const dashboardTitle = computed(() => config.value.dashboardTitle)

const handleGoToAdmin = () => {
  const target = getAdminHomeRoute()
  router.push(target.query ? { path: target.path, query: target.query } : target.path)
}

const currentDate = ref('')
const currentDay = ref('')

const updateDateTime = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  currentDate.value = `${year}年${month}月${day}日`
  
  const weekDays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  currentDay.value = weekDays[now.getDay()]
}

let timer: any = null

onMounted(() => {
  updateDateTime()
  timer = setInterval(updateDateTime, 1000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style lang="less" scoped>
.monitor-header {
  height: 70px;
  background: linear-gradient(135deg, rgba(15, 34, 73, 0.8), rgba(24, 46, 90, 0.6));
  border-bottom: 1px solid rgba(52, 134, 218, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 0 30px rgba(52, 134, 218, 0.1);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      linear-gradient(90deg, transparent 0%, rgba(52, 134, 218, 0.05) 50%, transparent 100%),
      radial-gradient(circle at top left, rgba(52, 134, 218, 0.1), transparent 50%);
    pointer-events: none;
  }
}

.header-left {
  flex: 1;
  display: flex;
  align-items: center;
}

.date-time {
  font-size: 16px;
  color: rgba(200, 220, 255, 0.95);
  font-weight: 500;
  text-shadow: 0 0 8px rgba(52, 134, 218, 0.5);
  position: relative;
  z-index: 1;
}

.header-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  max-width: 100%;
  position: relative;
  z-index: 1;
}

.platform-title {
  color: #ffffff;
  text-align: center;
  font-size: 32px;
  line-height: 1.2;
  letter-spacing: .06rem;
  font-weight: bold;
  margin: 0;
  text-shadow: 0 0 8px rgba(52, 134, 218, 0.5);
  position: relative;
  z-index: 1;

  a {
    color: #fff;
  }
}

.header-right {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-role {
  font-size: 16px;
  color: rgba(200, 220, 255, 0.95);
  padding: 6px 16px;
  background: rgba(52, 134, 218, 0.15);
  border-radius: 4px;
  border: 1px solid rgba(52, 134, 218, 0.3);
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  z-index: 1;
  
  &:hover {
    background: rgba(52, 134, 218, 0.25);
    border-color: rgba(52, 134, 218, 0.6);
    color: #ffffff;
    box-shadow: 0 0 12px rgba(52, 134, 218, 0.3);
  }
}
</style>
