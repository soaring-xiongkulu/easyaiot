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

/** 大屏「管理后台」默认落地页：mini 无集群管理，进流媒体地图分布 */
export function getAdminHomeRoute(): { path: string; query?: Record<string, string> } {
  if (isMiniDeployProfile()) {
    return { path: '/camera/index', query: { tab: '1' } };
  }
  return { path: '/node/index' };
}

/** mini 形态不启动 iot-gb28181 / WVP，前端不应请求国标接口 */
export function isGb28181Enabled(): boolean {
  return !isMiniDeployProfile();
}

/** mini 形态仅保留模型管理与推理，隐藏训练/导出/部署/大模型/SAM 等 */
export function isTrainAdvancedEnabled(): boolean {
  return !isMiniDeployProfile();
}

/** mini 形态不展示人脸库 / 车牌库 / 场景姿态库 Tab */
export function isFacePlateLibraryEnabled(): boolean {
  return !isMiniDeployProfile();
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

/** mini 形态隐藏的顶级菜单（与后端 system_menu.name 一致） */
const MINI_HIDDEN_MENU_NAMES = new Set([
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

/** 各部署形态均启用 HARNESS（与 IDEA 一致；install 侧可用 EASYAIOT_ENABLE_HARNESS=0 关闭） */
export function isHarnessEnabled(): boolean {
  return true;
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
