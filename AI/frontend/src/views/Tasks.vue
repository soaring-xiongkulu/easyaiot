<template>
  <div class="tasks">
    <h1>AI任务</h1>
    <div class="task-actions">
      <button @click="createTask" class="create-btn">创建新任务</button>
    </div>
    <div class="task-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else>
        <div v-for="task in tasks" :key="task.id" class="task-card" @click="viewTask(task.id)">
          <h3>{{ task.name }}</h3>
          <p>{{ task.description }}</p>
          <div class="task-info">
            <span class="model">模型: {{ task.modelName }}</span>
            <span class="status" :class="task.status">{{ task.status }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 创建任务模态框 -->
    <div v-if="showModal" class="modal">
      <div class="modal-content">
        <span class="close" @click="closeModal">&times;</span>
        <h2>创建新任务</h2>
        <form @submit.prevent="submitTask">
          <div class="form-group">
            <label for="name">任务名称:</label>
            <input type="text" id="name" v-model="newTask.name" required>
          </div>
          <div class="form-group">
            <label for="description">描述:</label>
            <textarea id="description" v-model="newTask.description" required></textarea>
          </div>
          <div class="form-group">
            <label for="modelId">AI模型:</label>
            <select id="modelId" v-model="newTask.modelId" required>
              <option v-for="model in models" :key="model.id" :value="model.id">
                {{ model.name }} (v{{ model.version }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label for="inputData">输入数据:</label>
            <textarea id="inputData" v-model="newTask.inputData" required></textarea>
          </div>
          <button type="submit" class="submit-btn">创建任务</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Tasks',
  data() {
    return {
      tasks: [],
      models: [],
      loading: true,
      showModal: false,
      newTask: {
        name: '',
        description: '',
        modelId: '',
        inputData: ''
      }
    }
  },
  async mounted() {
    await this.fetchTasks()
    await this.fetchModels()
  },
  methods: {
    async fetchTasks() {
      try {
        const response = await axios.get('/tasks')
        this.tasks = response.data
      } catch (error) {
        console.error('获取任务时出错:', error)
      } finally {
        this.loading = false
      }
    },
    async fetchModels() {
      try {
        const response = await axios.get('/models')
        this.models = response.data
      } catch (error) {
        console.error('获取模型时出错:', error)
      }
    },
    createTask() {
      this.showModal = true
    },
    closeModal() {
      this.showModal = false
      this.newTask = {
        name: '',
        description: '',
        modelId: '',
        inputData: ''
      }
    },
    async submitTask() {
      try {
        const taskData = {
          name: this.newTask.name,
          description: this.newTask.description,
          modelId: this.newTask.modelId,
          inputData: this.newTask.inputData
        }
        
        await axios.post('/tasks', taskData)
        this.closeModal()
        await this.fetchTasks()
      } catch (error) {
        console.error('创建任务时出错:', error)
        alert('创建任务失败')
      }
    },
    viewTask(id) {
      this.$router.push(`/tasks/${id}`)
    }
  }
}
</script>

<style scoped>
.tasks {
  padding: 20px;
}

.task-actions {
  text-align: right;
  margin-bottom: 20px;
}

.create-btn {
  background-color: #42b983;
  border: none;
  color: white;
  padding: 10px 20px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 16px;
  cursor: pointer;
  border-radius: 4px;
}

.task-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.task-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: transform 0.2s;
}

.task-card:hover {
  transform: translateY(-5px);
}

.task-card h3 {
  margin-top: 0;
  color: #333;
}

.task-info {
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

.status.pending {
  background-color: #ffc107;
  color: #212529;
}

.status.running {
  background-color: #17a2b8;
  color: white;
}

.status.completed {
  background-color: #28a745;
  color: white;
}

.status.failed {
  background-color: #dc3545;
  color: white;
}

.loading {
  text-align: center;
  padding: 20px;
}

/* 模态框样式 */
.modal {
  display: block;
  position: fixed;
  z-index: 1;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  overflow: auto;
  background-color: rgb(0,0,0);
  background-color: rgba(0,0,0,0.4);
}

.modal-content {
  background-color: #fefefe;
  margin: 5% auto;
  padding: 20px;
  border: 1px solid #888;
  width: 80%;
  max-width: 600px;
  border-radius: 8px;
  position: relative;
}

.close {
  color: #aaa;
  float: right;
  font-size: 28px;
  font-weight: bold;
  position: absolute;
  right: 20px;
  top: 10px;
}

.close:hover,
.close:focus {
  color: black;
  text-decoration: none;
  cursor: pointer;
}

.form-group {
  margin-bottom: 15px;
  text-align: left;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.form-group textarea {
  height: 100px;
  resize: vertical;
}

.submit-btn {
  background-color: #42b983;
  border: none;
  color: white;
  padding: 10px 20px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 16px;
  cursor: pointer;
  border-radius: 4px;
  width: 100%;
}
</style>