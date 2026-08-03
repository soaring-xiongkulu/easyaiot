<script setup lang="ts">
import SectionReveal from '../components/SectionReveal.vue'
import { packages, profiles, RELEASES_URL } from '../data/downloads'
import { LINKS } from '../data/site'
</script>

<template>
  <div>
    <section class="page-hero">
      <div class="container">
        <SectionReveal>
          <h1 class="display section-title">下载安装包</h1>
          <p class="lead">
            官方安装包发布于 Gitee Releases。按操作系统与架构选择，再用 mini / standard / full 三档完成到场部署。
          </p>
          <div class="hero-actions">
            <a class="btn btn-primary" :href="RELEASES_URL" target="_blank" rel="noopener">
              打开 Gitee Releases
            </a>
            <a class="btn btn-outline" :href="LINKS.compileReadme" target="_blank" rel="noopener">
              COMPILE 打包说明
            </a>
          </div>
        </SectionReveal>
      </div>
    </section>

    <section class="section" style="padding-top: 12px">
      <div class="container">
        <SectionReveal>
          <h2 class="display section-title">支持的平台</h2>
          <p class="lead">安装包覆盖常见服务器、桌面与国产化目标环境。</p>
        </SectionReveal>

        <div class="package-list">
          <SectionReveal
            v-for="(item, index) in packages"
            :key="item.id"
            :class="`reveal-delay-${(index % 3) + 1}`"
          >
            <a class="package-row" :href="RELEASES_URL" target="_blank" rel="noopener">
              <div>
                <h3>{{ item.platform }}</h3>
                <p>{{ item.note }}</p>
              </div>
              <div class="package-side">
                <span>{{ item.arch }}</span>
                <strong>去下载</strong>
              </div>
            </a>
          </SectionReveal>
        </div>
      </div>
    </section>

    <section class="section profile-section">
      <div class="container">
        <SectionReveal>
          <h2 class="display section-title">部署档位</h2>
          <p class="lead">同一套软件，按现场硬件选一档即可，不必维护多套版本。</p>
        </SectionReveal>

        <div class="profile-grid">
          <SectionReveal
            v-for="(item, index) in profiles"
            :key="item.id"
            :class="`reveal-delay-${index + 1}`"
          >
            <article class="profile-item">
              <div class="media-frame">
                <img :src="item.image" :alt="item.name" />
              </div>
              <h3>{{ item.name }}</h3>
              <p>{{ item.summary }}</p>
              <div class="meta">
                <span>{{ item.hardware }}</span>
                <span>{{ item.memory }}</span>
              </div>
            </article>
          </SectionReveal>
        </div>
      </div>
    </section>

    <section class="section-tight">
      <div class="container quickstart">
        <SectionReveal>
          <h2 class="display">快速开始</h2>
          <ol>
            <li>在 Gitee Releases 下载对应系统的安装包。</li>
            <li>安装后通过 PANEL 选择 mini / standard / full 完成装机。</li>
            <li>打开 WEB 管控台，接入摄像头与设备，启动算法任务。</li>
          </ol>
          <div class="links">
            <a :href="LINKS.github" target="_blank" rel="noopener">GitHub 镜像</a>
            <a :href="LINKS.gitee" target="_blank" rel="noopener">Gitee 仓库</a>
          </div>
        </SectionReveal>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.package-list {
  display: grid;
  gap: 12px;
  margin-top: 36px;
}

.package-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 22px 0;
  border-bottom: 1px solid var(--line);
  transition: color 0.25s var(--ease);
}

.package-row:hover {
  color: var(--brand-deep);
}

.package-row h3 {
  margin: 0 0 6px;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.35;
}

.package-row p {
  margin: 0;
  color: var(--muted);
}

.package-side {
  display: grid;
  justify-items: end;
  gap: 8px;
  min-width: 120px;
  color: var(--ink-soft);
  font-size: 14px;
}

.package-side strong {
  color: var(--brand);
  font-weight: 600;
  transition: transform 0.3s var(--ease);
}

.package-row:hover .package-side strong {
  transform: translateX(4px);
}

.profile-section {
  background: linear-gradient(180deg, rgba(38, 108, 251, 0.04), transparent);
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 28px;
  margin-top: 36px;
}

.profile-item h3 {
  margin: 18px 0 8px;
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 700;
  line-height: 1.35;
}

.profile-item p {
  margin: 0;
  color: var(--muted);
}

.meta {
  display: grid;
  gap: 4px;
  margin-top: 14px;
  color: var(--ink-soft);
  font-size: 13px;
}

.quickstart {
  border-top: 1px solid var(--line);
  padding-top: 36px;
}

.quickstart ol {
  margin: 18px 0 0;
  padding-left: 20px;
  color: var(--ink-soft);
}

.quickstart li {
  margin-bottom: 10px;
}

.links {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin-top: 24px;
}

.links a {
  color: var(--brand-deep);
  font-weight: 600;
}

@media (max-width: 900px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }

  .package-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .package-side {
    justify-items: start;
  }
}
</style>
