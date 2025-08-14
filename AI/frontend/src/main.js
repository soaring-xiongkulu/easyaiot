import Vue from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'

Vue.config.productionTip = false

// 配置axios基础URL
axios.defaults.baseURL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8080/api'

new Vue({
  router,
  render: h => h(App),
}).$mount('#app')