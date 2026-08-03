export interface DownloadPackage {
  id: string
  platform: string
  arch: string
  note: string
}

export interface DeployProfile {
  id: 'mini' | 'standard' | 'full'
  name: string
  hardware: string
  memory: string
  summary: string
  image: string
}

export const RELEASES_URL = 'https://gitee.com/volara/easyaiot/releases'

export const packages: DownloadPackage[] = [
  {
    id: 'deb',
    platform: 'Ubuntu / Debian',
    arch: 'amd64 / arm64',
    note: 'deb 安装包，适合常见 Linux 服务器与一体机',
  },
  {
    id: 'rpm',
    platform: 'CentOS / RHEL',
    arch: 'amd64 / arm64',
    note: 'rpm 安装包，企业机房与国产化主机常用',
  },
  {
    id: 'windows',
    platform: 'Windows',
    arch: 'x64',
    note: '桌面安装包，配合 PANEL 完成到场装机与值守',
  },
  {
    id: 'macos',
    platform: 'macOS',
    arch: 'Intel / Apple Silicon',
    note: '开发与演示环境快速安装',
  },
  {
    id: 'arm-kylin',
    platform: 'ARM / 麒麟',
    arch: 'arm64',
    note: '面向边缘盒子与国产操作系统环境',
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
