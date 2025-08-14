import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '../views/Home.vue'
import AIModels from '../views/AIModels.vue'
import Tasks from '../views/Tasks.vue'
import TaskDetail from '../views/TaskDetail.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/ai-models',
    name: 'AIModels',
    component: AIModels
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: Tasks
  },
  {
    path: '/tasks/:id',
    name: 'TaskDetail',
    component: TaskDetail,
    props: true
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router