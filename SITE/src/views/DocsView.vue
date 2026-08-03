<script setup lang="ts">
import SectionReveal from '../components/SectionReveal.vue'
import { docs } from '../data/docs'
</script>

<template>
  <div>
    <section class="page-hero">
      <div class="container">
        <SectionReveal>
          <h1 class="display section-title">文档入口</h1>
          <p class="lead">
            官方文档仍托管在仓库中。这里汇总常用入口，便于查找部署、打包与各模块说明。
          </p>
        </SectionReveal>
      </div>
    </section>

    <section class="section" style="padding-top: 8px">
      <div class="container doc-list">
        <SectionReveal
          v-for="(item, index) in docs"
          :key="item.href"
          :class="`reveal-delay-${(index % 3) + 1}`"
        >
          <a class="doc-row" :href="item.href" target="_blank" rel="noopener">
            <div>
              <h2>{{ item.title }}</h2>
              <p>{{ item.description }}</p>
            </div>
            <span>打开</span>
          </a>
        </SectionReveal>
      </div>
    </section>
  </div>
</template>

<style scoped>
.doc-list {
  display: grid;
  gap: 0;
}

.doc-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 26px 0;
  border-bottom: 1px solid var(--line);
  transition:
    color 0.25s var(--ease),
    padding-left 0.35s var(--ease);
}

.doc-row:hover {
  color: var(--brand-deep);
  padding-left: 8px;
}

.doc-row h2 {
  margin: 0 0 8px;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.35;
}

.doc-row p {
  margin: 0;
  color: var(--muted);
}

.doc-row span {
  flex-shrink: 0;
  color: var(--brand);
  font-weight: 600;
}

@media (max-width: 640px) {
  .doc-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
  }
}
</style>
