<script setup lang="ts">
import { computed, ref } from 'vue'
import SectionReveal from '../components/SectionReveal.vue'
import {
  packages,
  platformGroups,
  profiles,
  RELEASES_URL,
  type DownloadPackage,
} from '../data/downloads'
import { LINKS } from '../data/site'

const activeGroup = ref<string>('all')

const filters = [
  { id: 'all', label: '全部' },
  ...platformGroups.map((g) => ({ id: g.id, label: g.title })),
]

const filteredPackages = computed(() => {
  const group = activeGroup.value
  if (group === 'all') return packages
  if (group === 'domestic') {
    return packages.filter((item) => item.category === 'domestic')
  }
  if (group === 'deb') {
    return packages.filter((item) => item.format.includes('.deb'))
  }
  if (group === 'rpm') {
    return packages.filter((item) => item.format.includes('.rpm'))
  }
  return packages.filter((item) => item.category === group)
})

function packageHref(_item: DownloadPackage) {
  return RELEASES_URL
}
</script>

<template>
  <div>
    <section class="page-hero">
      <div class="container">
        <SectionReveal>
          <h1 class="display section-title">下载安装包</h1>
          <p class="lead">
            官方安装包发布于 Gitee Releases。覆盖 Ubuntu、CentOS/RHEL el7–el9（x86 /
            ARM）、Windows、macOS、麒麟 (Kylin) 与 欧拉 (openEuler)，再按 mini / standard / full
            三档完成到场部署。
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
          <h2 class="display section-title">平台覆盖</h2>
          <p class="lead">按发行版族系选择，现场系统多一套选择就少一次临时编译。</p>
        </SectionReveal>

        <div class="group-grid">
          <SectionReveal
            v-for="(group, index) in platformGroups"
            :key="group.id"
            :class="`reveal-delay-${(index % 3) + 1}`"
          >
            <button
              class="group-chip"
              type="button"
              :class="{ active: activeGroup === group.id }"
              @click="activeGroup = activeGroup === group.id ? 'all' : group.id"
            >
              <strong>{{ group.title }}</strong>
              <span>{{ group.summary }}</span>
            </button>
          </SectionReveal>
        </div>
      </div>
    </section>

    <section class="section package-section">
      <div class="container">
        <SectionReveal>
          <div class="package-head">
            <div>
              <h2 class="display section-title">支持的安装包</h2>
              <p class="lead">按操作系统与架构选择对应格式，点击前往 Releases 下载。</p>
            </div>
            <div class="filter-bar" role="tablist" aria-label="按平台筛选">
              <button
                v-for="item in filters"
                :key="item.id"
                class="filter-btn"
                type="button"
                role="tab"
                :aria-selected="activeGroup === item.id"
                :class="{ active: activeGroup === item.id }"
                @click="activeGroup = item.id"
              >
                {{ item.label }}
              </button>
            </div>
          </div>
        </SectionReveal>

        <div class="package-list">
          <SectionReveal
            v-for="(item, index) in filteredPackages"
            :key="item.id"
            :class="`reveal-delay-${(index % 3) + 1}`"
          >
            <a class="package-row" :href="packageHref(item)" target="_blank" rel="noopener">
              <div class="package-main">
                <div class="package-title-row">
                  <h3>{{ item.platform }}</h3>
                  <span class="format-tag">{{ item.format }}</span>
                </div>
                <p>{{ item.note }}</p>
                <div class="highlights">
                  <span v-for="tag in item.highlights" :key="tag">{{ tag }}</span>
                </div>
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
            <li>在 Gitee Releases 下载对应系统与架构的安装包（.deb / .rpm / .exe / .dmg）。</li>
            <li>安装后通过 PANEL 选择 mini / standard / full 完成装机。</li>
            <li>打开 WEB 管控台，接入摄像头与设备，启动算法任务。</li>
          </ol>
          <div class="links">
            <a :href="LINKS.github" target="_blank" rel="noopener">GitHub 镜像</a>
            <a :href="LINKS.gitee" target="_blank" rel="noopener">Gitee 仓库</a>
            <a :href="LINKS.compileReadme" target="_blank" rel="noopener">COMPILE 说明</a>
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

.group-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-top: 32px;
  align-items: stretch;
}

.group-grid :deep(.reveal) {
  display: flex;
  height: 100%;
}

.group-chip {
  display: grid;
  gap: 8px;
  width: 100%;
  height: 100%;
  padding: 18px 16px;
  text-align: left;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  color: inherit;
  cursor: pointer;
  transition:
    border-color 0.25s var(--ease),
    background 0.25s var(--ease),
    transform 0.25s var(--ease);
}

.group-chip:hover {
  border-color: rgba(47, 111, 237, 0.35);
  transform: translateY(-1px);
}

.group-chip.active {
  border-color: rgba(47, 111, 237, 0.55);
  background: rgba(47, 111, 237, 0.06);
}

.group-chip strong {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
}

.group-chip span {
  color: var(--muted);
  font-size: 13px;
  line-height: 1.55;
}

.package-section {
  padding-top: 8px;
}

.package-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-btn {
  padding: 8px 14px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: transparent;
  color: var(--ink-soft);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.2s var(--ease),
    border-color 0.2s var(--ease),
    color 0.2s var(--ease);
}

.filter-btn:hover {
  border-color: rgba(47, 111, 237, 0.35);
  color: var(--brand-deep);
}

.filter-btn.active {
  border-color: transparent;
  background: var(--brand);
  color: #fff;
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

.package-title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.package-row h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.35;
}

.format-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--brand-soft);
  color: var(--brand-deep);
  font-family: var(--font-brand);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.package-row p {
  margin: 0;
  color: var(--muted);
}

.highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.highlights span {
  color: var(--ink-soft);
  font-size: 12px;
  line-height: 1.4;
  padding: 4px 0;
}

.highlights span::before {
  content: '';
  display: inline-block;
  width: 5px;
  height: 5px;
  margin-right: 8px;
  border-radius: 50%;
  background: var(--brand);
  vertical-align: 1px;
}

.package-side {
  display: grid;
  justify-items: end;
  gap: 8px;
  min-width: 140px;
  color: var(--ink-soft);
  font-size: 14px;
  text-align: right;
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
  .group-grid {
    grid-template-columns: 1fr 1fr;
  }

  .profile-grid {
    grid-template-columns: 1fr;
  }

  .package-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .package-side {
    justify-items: start;
    text-align: left;
  }

  .package-head {
    align-items: flex-start;
  }
}

@media (max-width: 560px) {
  .group-grid {
    grid-template-columns: 1fr;
  }
}
</style>
