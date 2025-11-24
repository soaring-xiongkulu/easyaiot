<template>
  <div class="monitor-header">
    <div class="header-left">
      <div class="date-time">
        {{ currentDate }} {{ currentDay }}
      </div>
    </div>
    
    <div class="header-center">
      <h1 class="platform-title">综合监控预警处置平台</h1>
    </div>
    
    <div class="header-right">
      <div class="user-info">
        <span class="user-role">超级管理员</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'

defineOptions({
  name: 'MonitorHeader'
})

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
  height: 60px;
  background: linear-gradient(90deg, rgba(0, 0, 0, 0.4) 0%, rgba(26, 35, 50, 0.6) 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.header-left {
  flex: 1;
  display: flex;
  align-items: center;
}

.date-time {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.platform-title {
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  letter-spacing: 2px;
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
  color: rgba(255, 255, 255, 0.9);
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}
</style>
