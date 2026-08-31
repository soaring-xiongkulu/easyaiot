// 厂商元数据：中文名 + 官方 logo（静态资源位于 public/vendor-logos）
// logo 用于模型未上传自定义图标时作为卡片的默认展示图
export const VENDOR_META: Record<string, { name: string; logo: string }> = {
  dashscope: { name: '阿里云百炼', logo: '/vendor-logos/dashscope.png' },
  deepseek: { name: 'DeepSeek', logo: '/vendor-logos/deepseek.png' },
  zhipu: { name: '智谱', logo: '/vendor-logos/zhipu.png' },
  openai: { name: 'OpenAI', logo: '/vendor-logos/openai.png' },
  kimi: { name: 'Kimi', logo: '/vendor-logos/kimi.png' },
  anthropic: { name: 'Anthropic', logo: '/vendor-logos/anthropic.png' },
  claude: { name: 'Claude', logo: '/vendor-logos/claude.png' },
  custom: { name: '自定义', logo: '/vendor-logos/custom.svg' },
};

export function getVendorMeta(vendor: string): { name: string; logo: string } {
  return VENDOR_META[vendor] || { name: vendor || '--', logo: '' };
}
