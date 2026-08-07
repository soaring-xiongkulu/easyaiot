<script setup lang="ts">
import { RouterLink } from 'vue-router'
import SectionReveal from '../components/SectionReveal.vue'
import { packages, platformGroups, profiles } from '../data/downloads'
import { TAGLINE } from '../data/site'

const platformCount = packages.length
</script>

<template>
  <div class="home">
    <section class="hero">
      <div class="hero-media" aria-hidden="true">
        <img src="/images/hero.jpg" alt="" />
        <div class="hero-veil" />
      </div>
      <div class="container hero-content">
        <h1 class="brand-title hero-anim">EasyAIoT</h1>
        <p class="hero-line hero-anim delay-1">{{ TAGLINE }}</p>
        <p class="hero-support hero-anim delay-2">
          同一套软件贯穿边缘盒子、AI 一体摄像头与全栈一体机；安装包覆盖 Ubuntu、CentOS、Windows、macOS、麒麟 (Kylin) 与 欧拉 (openEuler)。
        </p>
        <div class="hero-actions hero-anim delay-3">
          <RouterLink class="btn btn-primary" to="/download">立即下载</RouterLink>
          <RouterLink class="btn btn-ghost" to="/features">了解特性</RouterLink>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <SectionReveal>
          <h2 class="display section-title">三档硬件，一套平台</h2>
          <p class="lead">
            不必为装得下而砍能力、拆版本。按现场选一档即可，同一套 EasyAIoT 贯穿试点到全栈交付。
          </p>
        </SectionReveal>

        <div class="profile-list">
          <SectionReveal
            v-for="(item, index) in profiles"
            :key="item.id"
            :class="`reveal-delay-${Math.min(index + 1, 3)}`"
          >
            <article class="profile-row">
              <div class="profile-copy">
                <h3>{{ item.name }}</h3>
                <p>{{ item.summary }}</p>
                <div class="profile-meta">
                  <span>{{ item.hardware }}</span>
                  <span>推荐内存 {{ item.memory }}</span>
                </div>
              </div>
              <div class="media-frame profile-media">
                <img :src="item.image" :alt="item.name" />
              </div>
            </article>
          </SectionReveal>
        </div>
      </div>
    </section>

    <section class="section platform-section">
      <div class="container grid-2">
        <SectionReveal>
          <h2 class="display section-title">更多系统，直接下载</h2>
          <p class="lead">
            现已提供 {{ platformCount }} 类官方安装包：Debian 系 .deb、CentOS/RHEL el7–el9（x86 /
            ARM）.rpm、Windows / macOS 桌面包，以及 麒麟 (Kylin) / 欧拉 (openEuler)——到场少一次临时编译。
          </p>
          <ul class="platform-points">
            <li v-for="group in platformGroups" :key="group.id">
              <strong>{{ group.title }}</strong>
              <span>{{ group.summary }}</span>
            </li>
          </ul>
          <div class="cta-row">
            <RouterLink class="btn btn-outline" to="/download">查看全部安装包</RouterLink>
          </div>
        </SectionReveal>
        <SectionReveal class="reveal-delay-2">
          <div class="media-frame">
            <img src="/images/platform-coverage.jpg" alt="多操作系统安装包覆盖" />
          </div>
        </SectionReveal>
      </div>
    </section>

    <section class="section rtc-section">
      <div class="container grid-2">
        <SectionReveal>
          <p class="eyebrow">RTC 模块</p>
          <h2 class="display section-title">没有 RTSP，也能进平台</h2>
          <p class="lead">
            家庭、门店里已在用的 Tapo、涂鸦、Ring、Nest、小米、Wyze、DoorBird、GoPro、Roborock
            等设备，走厂商私有 P2P 协议、原生不提供标准 RTSP。EasyAIoT RTC 模块
            一次打通九大品牌取流与对讲，与国标/ONVIF 摄像头同屏共管、同挂 AI 任务。
          </p>
          <ul class="rtc-points">
            <li>Web 一键接入，按品牌动态表单填参</li>
            <li>P2P 取流 → RTSP → SRS → 播放与 AI 分析</li>
            <li>Tapo / Tuya / Ring / Wyze / DoorBird / Roborock 支持双向对讲</li>
          </ul>
          <div class="cta-row">
            <RouterLink class="btn btn-outline" to="/features">查看 RTC 能力详情</RouterLink>
          </div>
        </SectionReveal>
        <SectionReveal class="reveal-delay-2">
          <div class="media-frame">
            <img src="/images/feature-rtc.jpg" alt="消费级摄像头 P2P 桥接统一纳管" />
          </div>
        </SectionReveal>
      </div>
    </section>

    <section class="section runtime-section">
      <div class="container grid-2">
        <SectionReveal class="reveal-delay-2">
          <div class="media-frame">
            <img src="/images/feature-runtime.jpg" alt="RUNTIME 实时视觉分析加速" />
          </div>
        </SectionReveal>
        <SectionReveal>
          <p class="eyebrow">RUNTIME 模块</p>
          <h2 class="display section-title">画面不停，分析跟得上</h2>
          <p class="lead">
            预览、告警与任务编排还是原来那一套；现场路数多、要更跟手时，打开
            RUNTIME 加速，让实时看、定时抓、多路巡都更快跟上画面，不必改使用习惯。
          </p>
          <ul class="runtime-points">
            <li>实时监控更顺滑，高峰也不容易拖成积压</li>
            <li>定时抓拍、多路轮巡同一套加速能力</li>
            <li>按任务启用即可，平台侧预览与告警不变</li>
          </ul>
          <div class="cta-row">
            <RouterLink class="btn btn-outline" to="/features#runtime">查看 RUNTIME 能力详情</RouterLink>
          </div>
        </SectionReveal>
      </div>
    </section>

    <section class="section loop-section">
      <div class="container grid-2">
        <SectionReveal>
          <h2 class="display section-title">看得见场，也管得住设备</h2>
          <p class="lead">
            纯物联看得见数却看不见场，纯视频看得见场却控不住设备。EasyAIoT 让「数」与「图」在同一屏里核实与处置。
          </p>
          <div class="cta-row">
            <RouterLink class="btn btn-outline" to="/features">查看全部能力</RouterLink>
          </div>
        </SectionReveal>
        <SectionReveal class="reveal-delay-2">
          <div class="media-frame">
            <img src="/images/architecture.jpg" alt="视频智视与物联网同屏处置" />
          </div>
        </SectionReveal>
      </div>
    </section>

    <section class="section-tight close-section">
      <div class="container close-inner">
        <SectionReveal>
          <h2 class="display">开始你的云边端智能落地</h2>
          <p>多系统安装包已就绪。选好操作系统与部署档位，当天即可装机验收。</p>
          <RouterLink class="btn btn-primary" to="/download">前往下载</RouterLink>
        </SectionReveal>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero {
  position: relative;
  min-height: 100vh;
  margin-top: calc(var(--header-h) * -1);
  display: grid;
  align-items: center;
  color: var(--ink);
  overflow: hidden;
}

.hero-media {
  position: absolute;
  inset: 0;
}

.hero-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: 18% center;
  filter: saturate(0.92) brightness(1.04);
  animation: fade-soft 1.4s var(--ease) both;
}

.hero-veil {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(
      100deg,
      rgba(245, 247, 251, 0.94) 0%,
      rgba(245, 247, 251, 0.88) 28%,
      rgba(245, 247, 251, 0.55) 46%,
      rgba(245, 247, 251, 0.12) 64%,
      transparent 78%
    ),
    linear-gradient(180deg, rgba(245, 247, 251, 0.4) 0%, transparent 26%, transparent 72%, rgba(245, 247, 251, 0.6) 100%);
}

.hero::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 140px;
  background: linear-gradient(180deg, transparent 0%, var(--paper) 100%);
  pointer-events: none;
  z-index: 1;
}

.hero-content {
  position: relative;
  z-index: 2;
  padding: calc(var(--header-h) + 24px) 0 72px;
  max-width: 640px;
  margin-left: max(20px, calc((100% - 1180px) / 2));
  margin-right: auto;
  width: min(640px, calc(100% - 40px));
}

.brand-title {
  margin: 0;
  font-family: var(--font-brand);
  font-size: clamp(42px, 6.5vw, 64px);
  font-weight: 700;
  line-height: 1.05;
  letter-spacing: -0.03em;
  color: var(--ink);
}

.hero-line {
  margin: 14px 0 0;
  font-family: var(--font-display);
  font-size: clamp(18px, 2.2vw, 24px);
  font-weight: 600;
  line-height: 1.45;
  letter-spacing: 0.01em;
  color: var(--ink);
}

.hero-support {
  margin: 14px 0 0;
  max-width: 480px;
  color: var(--ink-soft);
  font-size: 16px;
  font-weight: 500;
  line-height: 1.75;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}

.hero-actions .btn-ghost {
  border-color: rgba(16, 24, 40, 0.18);
  color: var(--ink-soft);
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(8px);
}

.hero-actions .btn-ghost:hover {
  border-color: rgba(16, 24, 40, 0.28);
  background: rgba(255, 255, 255, 0.82);
  color: var(--ink);
}

.hero-anim {
  opacity: 0;
  animation: rise-in 0.9s var(--ease) forwards;
}

.delay-1 {
  animation-delay: 0.1s;
}

.delay-2 {
  animation-delay: 0.2s;
}

.delay-3 {
  animation-delay: 0.32s;
}

.profile-list {
  display: grid;
  gap: 0;
  margin-top: 40px;
}

.profile-row {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 36px;
  align-items: center;
  padding: 36px 0;
  border-bottom: 1px solid var(--line);
}

.profile-copy h3 {
  margin: 0 0 8px;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.35;
}

.profile-copy p {
  margin: 0;
  color: var(--muted);
  font-size: 15px;
  line-height: 1.7;
}

.profile-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-top: 14px;
  color: var(--ink-soft);
  font-size: 13px;
}

.profile-media {
  min-height: 168px;
}

.cta-row {
  margin-top: 24px;
}

.platform-section {
  background: linear-gradient(180deg, rgba(47, 111, 237, 0.035), transparent);
}

.platform-points {
  margin: 22px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 12px;
}

.platform-points li {
  display: grid;
  gap: 2px;
}

.platform-points strong {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
}

.platform-points span {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
}

.loop-section {
  background: linear-gradient(180deg, transparent, rgba(47, 111, 237, 0.04) 50%, transparent);
}

.rtc-section {
  background: linear-gradient(180deg, rgba(47, 111, 237, 0.03), transparent);
}

.rtc-points,
.runtime-points {
  margin: 20px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}

.rtc-points li,
.runtime-points li {
  position: relative;
  padding-left: 16px;
  color: var(--ink-soft);
  font-size: 15px;
  line-height: 1.65;
}

.rtc-points li::before,
.runtime-points li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.75em;
  width: 7px;
  height: 1.5px;
  background: var(--brand);
}

.runtime-section {
  background: linear-gradient(180deg, transparent, rgba(47, 111, 237, 0.035) 50%, transparent);
}

.close-section {
  padding-bottom: 88px;
}

.close-inner {
  padding: 40px 0 0;
  border-top: 1px solid var(--line);
  text-align: left;
}

.close-inner h2 {
  margin-bottom: 10px;
  font-size: clamp(24px, 3.2vw, 32px);
}

.close-inner p {
  margin: 0 0 22px;
  color: var(--muted);
  font-size: 15px;
  line-height: 1.7;
}

@media (max-width: 900px) {
  .hero {
    min-height: 100svh;
    align-items: center;
  }

  .hero-content {
    margin-left: auto;
    margin-right: auto;
    padding: calc(var(--header-h) + 32px) 0 64px;
  }

  .profile-row {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>
