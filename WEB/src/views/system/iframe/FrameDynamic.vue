<template>
  <div :class="prefixCls" :style="getWrapStyle">
    <Spin :spinning="loading" size="large" :style="getWrapStyle">
      <iframe
        :src="_initPath"
        :class="`${prefixCls}__main`"
        ref="frameRef"
        @load="hideLoading"
      ></iframe>
    </Spin>
  </div>
</template>
<script lang="ts" setup>
  import type { CSSProperties } from 'vue';
  import { ref, unref, computed } from 'vue';
  import { Spin } from 'ant-design-vue';
  import { useWindowSizeFn } from '@/hooks/event/useWindowSizeFn'
  import { useDesign } from '/@/hooks/web/useDesign';
  import { useLayoutHeight } from '/@/layouts/default/content/useContentViewHeight';
  import { useRoute } from 'vue-router';
  import { useTabs } from '/@/hooks/web/useTabs';

  const route = useRoute();
  const index = route.params?.taskId ?? route.params?.id ?? '';
  const code = route.query?.code ?? '';
  const path = route.query?.path ?? '';
  const folder = route.query?.folder ?? '';
  const titleQuery = route.query?.title ?? '';
  const { setTitle } = useTabs();
  setTitle(
    decodeURIComponent(String(titleQuery || index)) || 'EasyAIoT',
  );
  
  // 构建完整的 iframe 路径（Node-RED 与 nginx /dev-api/nodeRed/ 同源代理一致）
  const _initPath = computed(() => {
    const flowId = String(code || index || '').trim();
    const rawPath = String(path || '').trim();

    if (rawPath && flowId) {
      const basePath = rawPath.startsWith('/') ? rawPath : `/${rawPath}`;
      return `${basePath}${flowId}`;
    }
    // 规则引擎兜底：无 query.path 时仍按 nginx 路径打开编辑器
    if (flowId && (route.name === 'RuleChainsNodeRed' || String(route.path).includes('rulechain-editor'))) {
      return `/dev-api/nodeRed/#flow/${flowId}`;
    }
    if (rawPath && folder) {
      const basePath = rawPath.startsWith('/') ? rawPath : `/${rawPath}`;
      const folderValue = decodeURIComponent(String(folder));
      const separator = basePath.includes('?') ? '&' : '?';
      return `${basePath}${separator}folder=${encodeURIComponent(folderValue)}`;
    }
    if (rawPath) {
      return rawPath.startsWith('/') ? rawPath : `/${rawPath}`;
    }
    return '';
  });

  const loading = ref(false);
  const topRef = ref(50);
  const heightRef = ref(window.innerHeight);
  const frameRef = ref<HTMLFrameElement>();
  const { headerHeightRef } = useLayoutHeight();

  const { prefixCls } = useDesign('iframe-page');
  useWindowSizeFn(calcHeight, { wait: 150, immediate: true });

  const getWrapStyle = computed((): CSSProperties => {
    return {
      height: `${unref(heightRef)}px`,
    };
  });

  function calcHeight() {
    const iframe = unref(frameRef);
    if (!iframe) {
      return;
    }
    const top = headerHeightRef.value;
    topRef.value = top;
    heightRef.value = window.innerHeight - top;
    const clientHeight = document.documentElement.clientHeight - top;
    iframe.style.height = `${clientHeight}px`;
  }

  function hideLoading() {
    loading.value = false;
    calcHeight();
  }
</script>
<style lang="less" scoped>
  @prefix-cls: ~'@{namespace}-iframe-page';

  .@{prefix-cls} {
    .ant-spin-nested-loading {
      position: relative;
      height: 100%;

      .ant-spin-container {
        width: 100%;
        height: 100%;
        padding: 10px;
      }
    }

    &__mask {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
    }

    &__main {
      box-sizing: border-box;
      width: 100%;
      height: 100%;
      overflow: hidden;
      border: 0;
      background-color: @component-background;
    }
  }
</style>
