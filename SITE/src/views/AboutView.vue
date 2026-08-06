<script setup lang="ts">
import { RouterLink } from 'vue-router'
import SectionReveal from '../components/SectionReveal.vue'
import { LINKS, MISSION, TAGLINE } from '../data/site'
</script>

<template>
  <div>
    <section class="page-hero">
      <div class="container">
        <SectionReveal>
          <h1 class="display section-title">关于 EasyAIoT</h1>
          <p class="lead">{{ TAGLINE }}。开源学习项目，致力于让 AI 真正 0 门槛。</p>
        </SectionReveal>
      </div>
    </section>

    <section class="section" style="padding-top: 8px">
      <div class="container grid-2">
        <SectionReveal>
          <h2 class="display section-title">项目使命</h2>
          <p class="mission">{{ MISSION }}</p>
          <p class="body">
            EasyAIoT（Easy AI Internet of Things）专注于人工智能与物联网深度融合，让摄像头、传感器与边缘算力在现场即可协同运转——从设备接入、数据采集，到实时视觉分析、智能研判与告警联动，全链路在一套软件中贯通完成。
          </p>
        </SectionReveal>
        <SectionReveal class="reveal-delay-2">
          <div class="media-frame">
            <img src="/images/architecture.jpg" alt="云边端智能落地场景" />
          </div>
        </SectionReveal>
      </div>
    </section>

    <section class="section open-section">
      <div class="container">
        <SectionReveal>
          <h2 class="display section-title">开源与社区</h2>
          <p class="lead">
            本项目与商业行为无关。欢迎通过仓库参与讨论、提交 Issue，或在 Releases 获取安装包。
          </p>
        </SectionReveal>
        <div class="repo-links">
          <SectionReveal>
            <a class="repo-link" :href="LINKS.gitee" target="_blank" rel="noopener">Gitee 主仓库</a>
          </SectionReveal>
          <SectionReveal class="reveal-delay-1">
            <a class="repo-link" :href="LINKS.github" target="_blank" rel="noopener">GitHub 镜像</a>
          </SectionReveal>
          <SectionReveal class="reveal-delay-2">
            <a class="repo-link" :href="LINKS.releases" target="_blank" rel="noopener">安装包 Releases</a>
          </SectionReveal>
        </div>
      </div>
    </section>

    <section class="section-tight">
      <div class="container close">
        <SectionReveal>
          <h2 class="display">从下载开始</h2>
          <p>按操作系统下载安装包，选择适合现场的部署档位，把云边端智能落到实处。</p>
          <RouterLink class="btn btn-primary" to="/download">前往下载</RouterLink>
        </SectionReveal>
      </div>
    </section>
  </div>
</template>

<style scoped>
.mission {
  margin: 18px 0 0;
  max-width: 560px;
  color: var(--ink-soft);
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 500;
  line-height: 1.7;
}

.body {
  margin: 22px 0 0;
  max-width: 560px;
  color: var(--muted);
}

.open-section {
  background: linear-gradient(180deg, rgba(38, 108, 251, 0.05), transparent);
}

.repo-links {
  display: grid;
  gap: 12px;
  margin-top: 32px;
}

.repo-link {
  display: block;
  padding: 18px 0;
  border-bottom: 1px solid var(--line);
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  transition:
    color 0.25s var(--ease),
    padding-left 0.35s var(--ease);
}

.repo-link:hover {
  color: var(--brand-deep);
  padding-left: 8px;
}

.close {
  border-top: 1px solid var(--line);
  padding-top: 36px;
}

.close h2 {
  margin-bottom: 10px;
}

.close p {
  margin: 0 0 22px;
  color: var(--muted);
}
</style>
