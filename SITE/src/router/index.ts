import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { title: '首页' },
    },
    {
      path: '/features',
      name: 'features',
      component: () => import('../views/FeaturesView.vue'),
      meta: { title: '产品特性' },
    },
    {
      path: '/download',
      name: 'download',
      component: () => import('../views/DownloadView.vue'),
      meta: { title: '下载' },
    },
    {
      path: '/docs',
      name: 'docs',
      component: () => import('../views/DocsView.vue'),
      meta: { title: '文档' },
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
      meta: { title: '关于我们' },
    },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.afterEach((to) => {
  const page = typeof to.meta.title === 'string' ? to.meta.title : ''
  document.title = page
    ? `${page} · EasyAIoT`
    : 'EasyAIoT — 云边端一体化智能算法应用平台'
})

export default router
