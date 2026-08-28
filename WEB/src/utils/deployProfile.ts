/** 与后端 EASYAIOT_DEPLOY_PROFILE 对齐：mini / standard / full */
export type DeployProfile = 'mini' | 'standard' | 'full';

function normalizeDeployProfile(raw: string | undefined): DeployProfile {
  const p = String(raw ?? 'full')
    .trim()
    .toLowerCase();
  if (p === 'mini' || p === '1' || p === 'minimal' || p === '4g') return 'mini';
  if (p === 'standard' || p === '2' || p === 'std' || p === '16g') return 'standard';
  return 'full';
}

/** 当前前端构建时的部署形态（VITE_GLOB_DEPLOY_PROFILE，默认 full） */
export function getDeployProfile(): DeployProfile {
  return normalizeDeployProfile(import.meta.env.VITE_GLOB_DEPLOY_PROFILE);
}

export function isMiniDeployProfile(): boolean {
  return getDeployProfile() === 'mini';
}

/** edge 单机合装：登录无租户、无滑块验证码（VITE 编译时关闭） */
export function isLoginTenantEnabled(): boolean {
  return String(import.meta.env.VITE_GLOB_APP_TENANT_ENABLE ?? 'true').trim().toLowerCase() !== 'false';
}

export function isLoginCaptchaEnabled(): boolean {
  return String(import.meta.env.VITE_GLOB_APP_CAPTCHA_ENABLE ?? 'true').trim().toLowerCase() !== 'false';
}

/** edge 单机合装（与 mini 共用前端裁剪，但零 DEVICE / 无集群 Tab） */
export function isEdgeStandaloneDeployProfile(): boolean {
  return String(import.meta.env.VITE_GLOB_EDGE_STANDALONE ?? 'false').trim().toLowerCase() === 'true';
}

/** edge 单机合装不部署 NFS 集群，仅隐藏 NFS 相关 Tab */
const EDGE_HIDDEN_CAMERA_TAB_KEYS = new Set([
  '20', // NFS 集群管理
  '24', // NFS 集群拓扑
  '22', // NFS 节点部署
  '23', // NFS 文件目录
]);

export function isEdgeCameraTabVisible(tabKey: string): boolean {
  if (!isEdgeStandaloneDeployProfile())
    return true;
  return !EDGE_HIDDEN_CAMERA_TAB_KEYS.has(String(tabKey));
}

/** 大屏「管理后台」默认落地页（edge/mini 均进入流媒体 — 地图分布 Tab） */
export function getAdminHomeRoute(): { path: string; query?: Record<string, string> } {
  if (isEdgeStandaloneDeployProfile() || isMiniDeployProfile()) {
    return { path: '/camera/index', query: { tab: '1' } };
  }
  return { path: '/node/index' };
}

/** mini 形态不启动 iot-gb28181 / WVP，前端不应请求国标接口 */
export function isGb28181Enabled(): boolean {
  return !isMiniDeployProfile();
}

/** mini / edge 不部署 go2rtc，前端隐藏 RTC 平台接入入口 */
export function isRtcEnabled(): boolean {
  return !isMiniDeployProfile() && !isEdgeStandaloneDeployProfile();
}

/** mini / edge 仅保留模型管理（edge 再隐藏推理）；隐藏训练/导出/部署/大模型/SAM 等 */
export function isTrainAdvancedEnabled(): boolean {
  return !isMiniDeployProfile() && !isEdgeStandaloneDeployProfile();
}

/** mini 形态不展示人脸库 / 车牌库 / 场景姿态库 Tab */
export function isFacePlateLibraryEnabled(): boolean {
  return !isMiniDeployProfile();
}

/** mini / edge 单机不部署 iot-flow 工作流服务，告警管理隐藏「告警工单」Tab */
export function isFlowTicketEnabled(): boolean {
  return !isMiniDeployProfile() && !isEdgeStandaloneDeployProfile();
}

export function isScenarioPoseLibraryEnabled(): boolean {
  return !isMiniDeployProfile();
}

/** EDGE 模块已移除：边缘联邦由 RUNTIME 原子模式 + MQTT 事件面替代，不再展示边缘节点管理 */
export function isEdgeNodeEnabled(): boolean {
  return false;
}

/** mini / standard 均不部署可视化后端与编辑器，统一隐藏相关顶级菜单 */
const VISUALIZE_HIDDEN_MENU_NAMES = ['可视化管理', '大屏管理', '可视化大屏'] as const;
const TRANSFORM_HIDDEN_MENU_NAMES = ['系统对接', '数据转发'] as const;

/** mini 形态不部署 iot-flow 工作流服务，隐藏工作流顶级菜单（菜单已改名「告警工单」，入口收敛至告警管理 Tab；
 *  顶级目录 /flow 无 componentName，路由名由路径解析为 Flow） */
const MINI_HIDDEN_MENU_NAMES = new Set([
  'Flow',
  '集群管理',
  '设备管理',
  '产品管理',
  'OTA升级',
  '数据标注',
  '规则引擎',
  '通知管理',
  '基础设施',
  ...VISUALIZE_HIDDEN_MENU_NAMES,
  ...TRANSFORM_HIDDEN_MENU_NAMES,
]);

/** standard 形态隐藏的顶级菜单 */
const STANDARD_HIDDEN_MENU_NAMES = new Set([
  '设备管理',
  '产品管理',
  'OTA升级',
  '规则引擎',
  ...VISUALIZE_HIDDEN_MENU_NAMES,
  ...TRANSFORM_HIDDEN_MENU_NAMES,
]);

/** full 形态才启用可视化（iot-visualize / VISUALIZE） */
export function isVisualizeEnabled(): boolean {
  return getDeployProfile() === 'full';
}

/** full 形态才启用系统对接（TRANSFORM） */
export function isTransformEnabled(): boolean {
  return getDeployProfile() === 'full';
}

/** 各部署形态均启用 HARNESS（edge 单机合装除外） */
export function isHarnessEnabled(): boolean {
  return !isEdgeStandaloneDeployProfile();
}

function getHiddenMenuNamesForDeployProfile(): Set<string> {
  const profile = getDeployProfile();
  if (profile === 'mini') return MINI_HIDDEN_MENU_NAMES;
  if (profile === 'standard') return STANDARD_HIDDEN_MENU_NAMES;
  return new Set();
}

/** 当前部署形态下是否应隐藏该菜单项（按菜单名称匹配） */
export function isMenuHiddenByDeployProfile(menuName: string | undefined | null): boolean {
  const name = String(menuName ?? '').trim();
  if (!name) return false;
  return getHiddenMenuNamesForDeployProfile().has(name);
}
