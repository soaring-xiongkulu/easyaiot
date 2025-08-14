<template>
  <div class="home">
    <h1>AI Platform</h1>
    <p>Welcome to the AI Platform. You can manage AI models and tasks here.</p>
    <div class="actions">
      <button @click="goToModels">Manage AI Models</button>
      <button @click="goToTasks">View Tasks</button>
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