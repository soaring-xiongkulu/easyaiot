<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { LINKS } from '../data/site'

const route = useRoute()
const scrolled = ref(false)
const open = ref(false)

const links: Array<{
  to?: string
  href?: string
  label: string
  external?: boolean
}> = [
  { to: '/', label: '首页' },
  { to: '/features', label: '产品特性' },
  { to: '/download', label: '下载' },
  { to: '/docs', label: '文档' },
  { to: '/about', label: '关于' },
  { href: LINKS.demo, label: '演示环境', external: true },
]

const overHero = computed(() => route.path === '/' && !scrolled.value && !open.value)

function onScroll() {
  scrolled.value = window.scrollY > 24
}

function closeMenu() {
  open.value = false
}

onMounted(() => {
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<template>
  <header class="site-header" :class="{ scrolled, open, 'over-hero': overHero }">
    <div class="container header-inner">
      <RouterLink class="brand" to="/" @click="closeMenu">
        <img src="/logo.png" alt="EasyAIoT" class="brand-logo" />
        <span class="brand-name">EasyAIoT</span>
      </RouterLink>

      <button
        class="menu-toggle"
        type="button"
        :aria-expanded="open"
        aria-label="打开导航"
        @click="open = !open"
      >
        <span />
        <span />
      </button>

      <nav class="nav" :class="{ open }">
        <template v-for="link in links" :key="link.label">
          <a
            v-if="link.external"
            class="nav-link"
            :href="link.href"
            target="_blank"
            rel="noopener"
            @click="closeMenu"
          >
            {{ link.label }}
          </a>
          <RouterLink
            v-else
            :to="link.to!"
            class="nav-link"
            :class="{ active: route.path === link.to }"
            @click="closeMenu"
          >
            {{ link.label }}
          </RouterLink>
        </template>

        <div class="nav-icons">
          <a
            class="nav-icon"
            :href="LINKS.gitee"
            target="_blank"
            rel="noopener"
            aria-label="Gitee"
            title="Gitee"
            @click="closeMenu"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="currentColor"
                d="M11.984 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.016 0zm6.09 5.333c.328 0 .593.266.592.593v1.482a.594.594 0 0 1-.593.592H9.777c-.982 0-1.778.796-1.778 1.778v5.63c0 .327.266.592.593.592h5.63c.982 0 1.778-.796 1.778-1.778v-.296a.593.593 0 0 0-.592-.593h-4.15a.592.592 0 0 1-.592-.592v-1.482a.593.593 0 0 1 .593-.592h6.815c.327 0 .593.265.593.592v3.408a4 4 0 0 1-4 4H5.926a.593.593 0 0 1-.593-.593V9.778a4.444 4.444 0 0 1 4.445-4.444h8.296z"
              />
            </svg>
          </a>
          <a
            class="nav-icon"
            :href="LINKS.github"
            target="_blank"
            rel="noopener"
            aria-label="GitHub"
            title="GitHub"
            @click="closeMenu"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="currentColor"
                d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"
              />
            </svg>
          </a>
        </div>

        <RouterLink class="btn btn-primary nav-cta" to="/download" @click="closeMenu">
          立即下载
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: fixed;
  inset: 0 0 auto;
  z-index: 50;
  height: var(--header-h);
  border-bottom: 1px solid transparent;
  background: transparent;
  transition:
    background 0.35s var(--ease),
    border-color 0.35s var(--ease),
    backdrop-filter 0.35s var(--ease),
    color 0.35s var(--ease);
}

.site-header.scrolled,
.site-header.open {
  background: rgba(247, 249, 252, 0.9);
  border-bottom-color: var(--line);
  backdrop-filter: blur(16px);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.brand-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  transition: filter 0.35s var(--ease);
}

.brand-name {
  font-family: var(--font-brand);
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--ink);
  transition: color 0.35s var(--ease);
}

.nav {
  display: flex;
  align-items: center;
  gap: 0;
}

.nav-link {
  position: relative;
  padding: 8px 11px;
  color: var(--ink-soft);
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.01em;
  transition: color 0.25s var(--ease);
}

.nav-link:hover {
  color: var(--ink);
}

.nav-link.active {
  color: var(--ink);
  font-weight: 600;
}

.nav-link.active::after {
  content: '';
  position: absolute;
  left: 11px;
  right: 11px;
  bottom: 4px;
  height: 1.5px;
  background: var(--brand);
  border-radius: 1px;
}

.nav-icons {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  margin-left: 4px;
}

.nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  color: var(--ink-soft);
  border-radius: var(--radius);
  transition:
    color 0.25s var(--ease),
    background 0.25s var(--ease);
}

.nav-icon svg {
  width: 18px;
  height: 18px;
}

.nav-icon:hover {
  color: var(--ink);
  background: var(--brand-soft);
}

.nav-cta {
  margin-left: 10px;
  min-height: 38px;
  padding: 0 16px;
  font-size: 13px;
}

.over-hero {
  background: linear-gradient(180deg, rgba(245, 247, 251, 0.55) 0%, rgba(245, 247, 251, 0.08) 100%);
}

.menu-toggle {
  display: none;
  width: 42px;
  height: 42px;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.7);
  cursor: pointer;
}

.menu-toggle span {
  display: block;
  width: 18px;
  height: 2px;
  margin: 5px auto;
  background: var(--ink);
  transition: transform 0.3s var(--ease);
}

@media (max-width: 900px) {
  .menu-toggle {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .nav {
    position: absolute;
    top: var(--header-h);
    left: 0;
    right: 0;
    display: none;
    flex-direction: column;
    align-items: stretch;
    gap: 2px;
    padding: 12px 20px 22px;
    background: rgba(247, 249, 252, 0.97);
    border-bottom: 1px solid var(--line);
    backdrop-filter: blur(16px);
  }

  .nav.open {
    display: flex;
  }

  .nav-link.active::after {
    display: none;
  }

  .nav-icons {
    margin: 8px 0 0;
    gap: 8px;
  }

  .nav-icon {
    width: 40px;
    height: 40px;
  }

  .nav-cta {
    margin: 12px 0 0;
    width: 100%;
  }
}
</style>
