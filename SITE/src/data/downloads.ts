export interface DownloadPackage {
  id: string
  platform: string
  arch: string
  format: string
  category: 'deb' | 'rpm' | 'desktop' | 'domestic'
  note: string
  highlights: string[]
}

export interface DeployProfile {
  id: 'mini' | 'standard' | 'full'
  name: string
  hardware: string
  memory: string
  summary: string
  image: string
}

export interface PlatformGroup {
  id: string
  title: string
  summary: string
}

export const RELEASES_URL = 'https://gitee.com/volara/easyaiot/releases'

export const platformGroups: PlatformGroup[] = [
  {
    id: 'deb',
    title: 'Debian 系',
    summary: 'Ubuntu / Debian / 麒麟 (Kylin)，.deb + 内置 runtime',
  },
  {
    id: 'rpm',
    title: 'RPM 系',
    summary: 'CentOS / RHEL el7–el9（x86 / ARM）与 欧拉 (openEuler)',
  },
  {
    id: 'desktop',
    title: '桌面系统',
    summary: 'Windows 安装包与 macOS .dmg / .app',
  },
  {
    id: 'domestic',
    title: '国产化适配',
    summary: '麒麟 (Kylin) ARM64、欧拉 (openEuler) 到场交付',
  },
]

export const packages: DownloadPackage[] = [
  {
    id: 'ubuntu-amd64',
    platform: 'Ubuntu / Debian',
    arch: 'amd64',
    format: '.deb',
    category: 'deb',
    note: '常见 Linux 服务器与一体机首选，内置 runtime，装完即可用 PANEL 部署。',
    highlights: ['内置 runtime', 'systemd 服务', '桌面快捷方式'],
  },
  {
    id: 'ubuntu-arm64',
    platform: 'Ubuntu ARM',
    arch: 'arm64',
    format: '.deb',
    category: 'deb',
    note: '面向 ARM 服务器与边缘盒子，绑定 ARM 部署脚本。',
    highlights: ['ARM64', '内置 runtime', '边缘一体机'],
  },
  {
    id: 'centos-x86',
    platform: 'CentOS / RHEL',
    arch: 'x86_64 · el7 / el8 / el9',
    format: '.rpm',
    category: 'rpm',
    note: '按 EL 大版本分别构建，覆盖企业机房存量与新装主机。',
    highlights: ['el7 / el8 / el9', '企业机房', 'systemd'],
  },
  {
    id: 'centos-arm',
    platform: 'CentOS / RHEL ARM',
    arch: 'aarch64 · el7 / el8 / el9',
    format: '.rpm',
    category: 'rpm',
    note: 'ARM64 交叉构建 rpm，适合国产 ARM 服务器与边缘集群。',
    highlights: ['aarch64', 'el7 / el8 / el9', '交叉构建'],
  },
  {
    id: 'windows',
    platform: 'Windows',
    arch: 'x64',
    format: '.exe / NSIS',
    category: 'desktop',
    note: '桌面可执行文件 + 内置 runtime，可选 NSIS 安装程序。',
    highlights: ['内置 runtime', '可选安装器', '到场值守'],
  },
  {
    id: 'macos',
    platform: 'macOS',
    arch: 'Intel / Apple Silicon',
    format: '.dmg / .app',
    category: 'desktop',
    note: '开发与演示环境快速安装，圆形白底图标与 Linux 一致。',
    highlights: ['arm64 / amd64', '.dmg', '内置 runtime'],
  },
  {
    id: 'kylin-arm64',
    platform: '麒麟 (Kylin)',
    arch: 'arm64',
    format: '.deb',
    category: 'domestic',
    note: '国产操作系统环境专用包，适配麒麟 (Kylin) ARM 到场装机。',
    highlights: ['国产化', '麒麟 (Kylin) ARM64', '内置 runtime'],
  },
  {
    id: 'openeuler',
    platform: '欧拉 (openEuler)',
    arch: 'x86_64',
    format: '.rpm',
    category: 'domestic',
    note: '基于 欧拉 (openEuler) 24.03 构建，面向国产化服务器与信创交付。',
    highlights: ['openEuler 24.03', '信创适配', 'rpm'],
  },
]

export const profiles: DeployProfile[] = [
  {
    id: 'mini',
    name: 'mini 边缘精简版',
    hardware: '边缘盒子 / 门店安防一体机',
    memory: '≥ 4 GB',
    summary: '一个点位装上就有智能：摄像头接入、实时分析、智能告警。',
    image: '/images/profile-mini.jpg',
  },
  {
    id: 'standard',
    name: 'standard 标准版',
    hardware: 'AI 一体摄像头 / 多目分析终端',
    memory: '≥ 16 GB',
    summary: '每路摄像头即智能节点，楼面与园区级覆盖。',
    image: '/images/profile-standard.jpg',
  },
  {
    id: 'full',
    name: 'full 完整版',
    hardware: 'AIoT 智能全栈一体机',
    memory: '≥ 20 GB',
    summary: '一箱配齐 IoT + 视频 + AI，全链路长期稳跑。',
    image: '/images/profile-full.jpg',
  },
]
