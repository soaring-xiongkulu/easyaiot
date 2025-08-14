<template>
  <div class="ai-models">
    <h1>AI Models</h1>
    <div class="model-list">
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else>
        <div v-for="model in models" :key="model.id" class="model-card">
          <h3>{{ model.name }}</h3>
          <p>{{ model.description }}</p>
          <div class="model-info">
            <span class="version">Version: {{ model.version }}</span>
            <span class="status" :class="model.status">{{ model.status }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'AIModels',
  data() {
    return {
      models: [],
      loading: true
    }
  },
  async mounted() {
    try {
      const response = await axios.get('/models')
      this.models = response.data
    } catch (error) {
      console.error('Error fetching models:', error)
    } finally {
      this.loading = false
    }
  }
}
</script>

<style scoped>
.ai-models {
  padding: 20px;
}

.model-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.model-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.model-card h3 {
  margin-top: 0;
  color: #333;
}

.model-info {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
}

.status {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: bold;
}

.status.active {
  background-color: #42b983;
  color: white;
}

.status.inactive {
  background-color: #ddd;
  color: #666;
}

.loading {
  text-align: center;
  padding: 20px;
}
</style>