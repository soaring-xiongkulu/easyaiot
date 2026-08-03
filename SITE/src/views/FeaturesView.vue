<script setup lang="ts">
import { RouterLink } from 'vue-router'
import SectionReveal from '../components/SectionReveal.vue'
import { features } from '../data/features'
</script>

<template>
  <div>
    <section class="section feature-section">
      <div class="container feature-stack">
        <SectionReveal
          v-for="(item, index) in features"
          :key="item.id"
          :class="`reveal-delay-${(index % 3) + 1}`"
        >
          <article class="feature-block" :class="{ reverse: index % 2 === 1 }">
            <div class="feature-copy">
              <h2 class="display feature-title">{{ item.title }}</h2>
              <p class="feature-summary">{{ item.summary }}</p>
              <ul>
                <li v-for="point in item.points" :key="point">{{ point }}</li>
              </ul>
            </div>
            <div class="media-frame feature-media">
              <img :src="item.image" :alt="item.title" />
            </div>
          </article>
        </SectionReveal>
      </div>
    </section>

    <section class="section-tight">
      <div class="container cta">
        <SectionReveal>
          <h2 class="display">准备好落地了吗？</h2>
          <p>按系统与架构下载安装包，三档部署任选。</p>
          <RouterLink class="btn btn-primary" to="/download">前往下载</RouterLink>
        </SectionReveal>
      </div>
    </section>
  </div>
</template>

<style scoped>
.feature-section {
  padding-top: 28px;
  padding-bottom: 40px;
}

.feature-stack {
  display: grid;
  gap: 0;
}

.feature-block {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  gap: 40px;
  align-items: start;
  padding: 36px 0;
  border-bottom: 1px solid var(--line);
}

.feature-block.reverse {
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
}

.feature-block.reverse .feature-copy {
  order: 2;
}

.feature-block.reverse .feature-media {
  order: 1;
}

.feature-stack > :last-child .feature-block {
  border-bottom: none;
}

.feature-copy {
  padding-top: 4px;
}

.feature-title {
  font-size: clamp(22px, 2.6vw, 28px);
  line-height: 1.35;
}

.feature-summary {
  margin: 10px 0 0;
  max-width: 36em;
  color: var(--muted);
  font-size: 15px;
  line-height: 1.75;
}

.feature-media {
  aspect-ratio: 16 / 10;
  min-height: 0;
}

.feature-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

ul {
  margin: 18px 0 0;
  padding: 0;
  list-style: none;
}

li {
  position: relative;
  padding-left: 16px;
  margin-bottom: 8px;
  color: var(--ink-soft);
  font-size: 15px;
  line-height: 1.65;
}

li:last-child {
  margin-bottom: 0;
}

li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.75em;
  width: 7px;
  height: 1.5px;
  background: var(--brand);
}

.cta {
  padding-top: 20px;
  border-top: 1px solid var(--line);
}

.cta h2 {
  margin-bottom: 8px;
  font-size: clamp(22px, 2.8vw, 28px);
}

.cta p {
  margin: 0 0 20px;
  color: var(--muted);
  font-size: 15px;
}

@media (max-width: 900px) {
  .feature-block,
  .feature-block.reverse {
    grid-template-columns: 1fr;
    gap: 20px;
    padding: 28px 0;
  }

  .feature-block.reverse .feature-copy,
  .feature-block.reverse .feature-media {
    order: initial;
  }

  .feature-copy {
    padding-top: 0;
  }

  .feature-media {
    aspect-ratio: 16 / 10;
  }
}
</style>
