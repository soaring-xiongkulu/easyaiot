import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const version = process.env.VITE_VERSION || 'dev'

export default defineConfig({
  plugins: [vue()],
  define: {
    'import.meta.env.VITE_VERSION': JSON.stringify(version)
  },
  // esnext everywhere so the dev server's esbuild transform also accepts
  // top-level await (used by @novnc/novnc). `build.target` alone only affects
  // the production bundle; without this the `wails3 dev` Vite server crashes.
  build: {
    target: 'esnext'
  },
  esbuild: {
    target: 'esnext'
  },
  // NOTE: no optimizeDeps target needed on Vite 8 (rolldown pre-bundling does
  // no syntax downleveling, so TLA in deps passes through untouched; the old
  // optimizeDeps.esbuildOptions.target is deprecated and has no rolldown
  // equivalent).
  server: {
    host: '127.0.0.1',
    port: 34115,
    strictPort: true
  }
})
