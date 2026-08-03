import { LINKS } from './site'

export interface DocLink {
  title: string
  description: string
  href: string
}

export const docs: DocLink[] = [
  {
    title: '项目总览 README',
    description: '产品定位、模块组成、三档部署与能力全景。',
    href: LINKS.readmeZh,
  },
  {
    title: 'COMPILE 打包交付',
    description: '多平台安装包与可执行文件产出说明。',
    href: LINKS.compileReadme,
  },
  {
    title: 'Gitee Releases',
    description: '官方安装包发布页，按系统与架构下载。',
    href: LINKS.releases,
  },
  {
    title: 'GitHub 镜像仓库',
    description: '源码镜像与 Issue 协作入口。',
    href: LINKS.github,
  },
  {
    title: 'WEB 管控台文档',
    description: '管理端前端模块说明与本地开发指引。',
    href: 'https://gitee.com/volara/easyaiot/blob/main/WEB/README.md',
  },
  {
    title: 'PANEL 运维控制台',
    description: '到场装机、健康巡检与值守入口说明。',
    href: 'https://gitee.com/volara/easyaiot/blob/main/PANEL/README.md',
  },
  {
    title: 'DEVICE 服务说明',
    description: '网关与设备微服务架构、配置与部署。',
    href: 'https://gitee.com/volara/easyaiot/blob/main/DEVICE/README.md',
  },
  {
    title: 'VIDEO / AI 模块',
    description: '视频接入与算法服务相关文档入口。',
    href: 'https://gitee.com/volara/easyaiot/tree/main',
  },
]
