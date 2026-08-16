import { defineConfig, presetTypography, presetUno } from 'unocss'

export default defineConfig({
  // 开发态预扫 src，避免 HTTP/2 自定义 server 下首屏 __uno.css 尚无 utility、布局「裸奔」
  // （Uno 默认靠按需扫描 + HMR 回填；HMR 未连上时登录页等会丢 flex/w-full 等类）
  content: {
    filesystem: ['src/**/*.{vue,ts,tsx,jsx}'],
  },
  presets: [
    presetUno(),
    presetTypography(),
  ],
  theme: {
    colors: {
      primary: '#0960bd',
    },
  },
})
