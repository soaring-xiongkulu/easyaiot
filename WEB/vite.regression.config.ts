/** Loopback-only integration profile; never part of the production entry. */
import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import UnoCSS from 'unocss/vite';
import { resolve } from 'node:path';
import { generateModifyVars } from './build/generate/generateModifyVars';
import { configSvgIconsPlugin } from './build/vite/plugin/svgSprite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());
  const regressionPort = Number(process.env.MONITORING_REGRESSION_WEB_PORT || 8888);
  const videoTarget = process.env.MONITORING_REGRESSION_VIDEO_URL || 'http://127.0.0.1:6000';
  return {
    define: { __APP_INFO__: JSON.stringify({ pkg: { name: 'Monitoring regression', version: 'local' }, lastBuildTime: '' }) },
    resolve: { alias: { '@': resolve(__dirname, 'src'), 'vue-i18n': 'vue-i18n/dist/vue-i18n.cjs.js' } },
    plugins: [vue(), vueJsx(), UnoCSS(), configSvgIconsPlugin(false)],
    server: { host: '127.0.0.1', port: regressionPort, strictPort: true, proxy: {
      '/dev-api/video': { target: videoTarget, rewrite: path => path.replace(/^\/dev-api/, '') },
      '/dev-api': { target: videoTarget, rewrite: path => path.replace(/^\/dev-api/, '/admin-api') },
    } },
    css: { preprocessorOptions: { less: { modifyVars: generateModifyVars(), javascriptEnabled: true } } },
  };
});
