<template>
  <div class="home">
    <h1>AI平台</h1>
    <p>欢迎来到AI平台。您可以在此管理AI模型和任务。</p>
    <div class="actions">
      <button @click="goToModels">管理AI模型</button>
      <button @click="goToTasks">查看任务</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home',
  methods: {
    goToModels() {
      this.$router.push('/ai-models')
    },
    goToTasks() {
      this.$router.push('/tasks')
    }
  }
}
</script>

<style scoped>
.home {
  padding: 20px;
}

.actions {
  margin-top: 30px;
}

button {
  background-color: #42b983;
  border: none;
  color: white;
  padding: 10px 20px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 16px;
  margin: 10px;
  cursor: pointer;
  border-radius: 4px;
}
</style>