<template>
  <div class="monitor-header">
    <div class="header-left">
      <div class="date-time">
        {{ currentDate }} {{ currentDay }}
      </div>
    </div>
    
    <div class="header-center">
      <h1 class="platform-title">云边端一体算法预警监控平台</h1>
    </div>
    
    <div class="header-right">
      <div class="user-info">
        <span class="user-role" @click="handleGoToAdmin">管理后台</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

defineOptions({
  name: 'MonitorHeader'
})

const router = useRouter()

const handleGoToAdmin = () => {
  router.push('/camera/index')
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
  background: url(@/assets/images/bigscreen/head_bg.png) no-repeat center center;
  background-size: 100% 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
}

.header-left {
  flex: 1;
  display: flex;
  align-items: center;
}

.date-time {
  font-size: 16px;
  color: #bde4ff;
  font-weight: 500;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.platform-title {
  color: #bde4ff;
  text-align: center;
  height: 100%;
  font-size: 32px;
  line-height: 87px;
  letter-spacing: .06rem;
  font-weight: bold;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);

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
  color: #bde4ff;
  padding: 6px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    background: rgba(255, 255, 255, 0.2);
    color: #ffffff;
  }
}
</style>
