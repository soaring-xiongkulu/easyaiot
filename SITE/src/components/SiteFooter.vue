<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { LINKS } from '../data/site'

const year = new Date().getFullYear()
</script>

<template>
  <footer class="site-footer">
    <div class="container footer-grid">
      <div>
        <div class="footer-brand">
          <img src="/logo.png" alt="" class="footer-logo" />
          <span>EasyAIoT</span>
        </div>
        <p class="footer-copy">云边端一体化智能算法应用平台。AI + IoT，万物智视、万物智控。</p>
      </div>

      <div>
        <h3>导航</h3>
        <div class="footer-links">
          <RouterLink to="/features">产品特性</RouterLink>
          <RouterLink to="/download">下载安装包</RouterLink>
          <RouterLink to="/docs">文档入口</RouterLink>
          <a :href="LINKS.demo" target="_blank" rel="noopener">演示环境</a>
          <RouterLink to="/about">关于我们</RouterLink>
        </div>
      </div>

      <div>
        <h3>仓库</h3>
        <div class="footer-links">
          <a :href="LINKS.gitee" target="_blank" rel="noopener">Gitee</a>
          <a :href="LINKS.github" target="_blank" rel="noopener">GitHub</a>
          <a :href="LINKS.releases" target="_blank" rel="noopener">Releases</a>
        </div>
      </div>
    </div>
    <div class="container footer-bottom">
      <span>© {{ year }} EasyAIoT. Open source for learning.</span>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  margin-top: 0;
  padding: 56px 0 28px;
  color: #d7e0ef;
  background: linear-gradient(180deg, #152033 0%, #0f1624 100%);
}

.footer-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr;
  gap: 36px;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  font-family: var(--font-brand);
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.footer-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.footer-copy {
  margin: 0;
  max-width: 360px;
  color: rgba(215, 224, 239, 0.72);
}

.site-footer h3 {
  margin: 0 0 14px;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(215, 224, 239, 0.55);
}

.footer-links {
  display: grid;
  gap: 10px;
}

.footer-links a {
  color: #eef3fb;
  transition: color 0.25s var(--ease);
}

.footer-links a:hover {
  color: #8eb4ff;
}

.footer-bottom {
  margin-top: 36px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(215, 224, 239, 0.5);
  font-size: 13px;
}

@media (max-width: 800px) {
  .footer-grid {
    grid-template-columns: 1fr;
    gap: 28px;
  }
}
</style>
