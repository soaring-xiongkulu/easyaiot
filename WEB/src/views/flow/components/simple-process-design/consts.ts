/**
 * FLOW Simple 流程设计器 —— 数据契约常量与类型
 * 与后端 iot-flow（移植自 yudao BPM）的 SimpleModel JSON 结构对齐：
 * 单链表 childNode + 条件分支 conditionNodes，后端 SimpleModelUtils 直接转 BPMN 部署。
 */

// ==================== 节点类型 ====================
export enum NodeType {
  /** 结束节点 */
  END_EVENT_NODE = 1,
  /** 发起人节点（根节点） */
  START_USER_NODE = 10,
  /** 审批人节点 */
  USER_TASK_NODE = 11,
  /** 抄送人节点 */
  COPY_TASK_NODE = 12,
  /** 延迟器节点 */
  DELAY_TIMER_NODE = 14,
  /** 条件分支（排他网关） */
  CONDITION_BRANCH_NODE = 51,
  /** 并行分支（包容网关 + 恒真条件） */
  PARALLEL_BRANCH_NODE = 52,
  /** 条件分支内的单个条件 */
  CONDITION_NODE = 50,
}

// ==================== 候选人策略 ====================
export enum CandidateStrategy {
  /** 指定角色 */
  ROLE = 10,
  /** 部门成员 */
  DEPT_MEMBER = 20,
  /** 部门负责人 */
  DEPT_LEADER = 21,
  /** 指定岗位 */
  POST = 22,
  /** 指定成员 */
  USER = 30,
  /** 审批人自选 */
  APPROVE_USER_SELECT = 34,
  /** 发起人自选 */
  START_USER_SELECT = 35,
  /** 发起人本人 */
  START_USER = 36,
  /** 发起人部门负责人 */
  START_USER_DEPT_LEADER = 37,
  /** 指定用户组 */
  USER_GROUP = 40,
}

// ==================== 审批方式 ====================
export enum ApproveMethodType {
  /** 随机挑选一人 */
  RANDOM = 1,
  /** 会签（按通过比例） */
  BY_RATIO = 2,
  /** 或签（一人通过即可） */
  ANY_OF = 3,
  /** 依次审批 */
  SEQUENTIAL = 4,
}

/** 审批类型 */
export enum ApproveType {
  /** 人工审批 */
  USER = 1,
  /** 自动通过 */
  AUTO_APPROVE = 2,
  /** 自动拒绝 */
  AUTO_REJECT = 3,
}

/** 审批拒绝处理类型 */
export enum RejectHandlerType {
  /** 终止流程 */
  FINISH_PROCESS = 1,
  /** 驳回到指定节点 */
  RETURN_USER_TASK = 2,
}

/** 超时处理类型 */
export enum TimeoutHandlerType {
  /** 自动提醒 */
  REMINDER = 1,
  /** 自动通过 */
  APPROVE = 2,
  /** 自动拒绝 */
  REJECT = 3,
}

/** 审批人为空处理类型 */
export enum AssignEmptyHandlerType {
  /** 自动通过 */
  APPROVE = 1,
  /** 自动拒绝 */
  REJECT = 2,
  /** 指定成员审批 */
  ASSIGN_USER = 3,
  /** 转交流程管理员 */
  ASSIGN_ADMIN = 4,
}

/** 审批人与发起人相同时处理类型 */
export enum AssignStartUserHandlerType {
  /** 发起人自己审批 */
  START_USER_AUDIT = 1,
  /** 自动跳过 */
  SKIP = 2,
  /** 转交部门负责人 */
  ASSIGN_DEPT_LEADER = 3,
}

/** 时间单位 */
export enum TimeUnitType {
  MINUTE = 1,
  HOUR = 2,
  DAY = 3,
}

/** 条件配置类型 */
export enum ConditionType {
  /** 条件规则 */
  RULE = 2,
  /** 条件表达式 */
  EXPRESSION = 1,
}

// ==================== 数据结构 ====================
export interface TimeoutHandler {
  enable: boolean
  type?: TimeoutHandlerType
  timeDuration?: string
  maxRemindCount?: number
}

export interface RejectHandler {
  type: RejectHandlerType
  returnNodeId?: string
}

export interface AssignEmptyHandler {
  type: AssignEmptyHandlerType
  userIds?: number[]
}

export interface ConditionRule {
  leftSide?: string
  opCode: string
  rightSide?: string
}

export interface Condition {
  and: boolean
  rules: ConditionRule[]
}

export interface ConditionGroup {
  and: boolean
  conditions: Condition[]
}

export interface ConditionSetting {
  conditionType?: ConditionType
  conditionExpression?: string
  conditionGroups?: ConditionGroup
  defaultFlow?: boolean
}

export interface DelaySetting {
  delayType: number
  delayTime: string
}

/** Simple 流程节点（与后端 BpmSimpleModelNodeVO 对齐，字段按需裁剪） */
export interface SimpleFlowNode {
  id: string
  type: NodeType
  name: string
  showText?: string
  /** 后续节点（单链表） */
  childNode?: SimpleFlowNode
  /** 分支节点集合（条件/并行分支） */
  conditionNodes?: SimpleFlowNode[]
  /** 审批类型 */
  approveType?: ApproveType
  /** 候选人策略 */
  candidateStrategy?: CandidateStrategy
  /** 候选人参数（逗号分隔 ID / 表达式） */
  candidateParam?: string
  /** 多人审批方式 */
  approveMethod?: ApproveMethodType
  /** 会签通过比例（百分比） */
  approveRatio?: number
  /** 超时处理 */
  timeoutHandler?: TimeoutHandler
  /** 拒绝处理 */
  rejectHandler?: RejectHandler
  /** 审批人为空处理 */
  assignEmptyHandler?: AssignEmptyHandler
  /** 审批人与发起人相同处理 */
  assignStartUserHandlerType?: AssignStartUserHandlerType
  /** 审批意见必填 */
  reasonRequire?: boolean
  /** 条件设置（条件分支内的条件节点） */
  conditionSetting?: ConditionSetting
  /** 延迟设置 */
  delaySetting?: DelaySetting
  /** 运行态节点状态（查看器染色用，不参与设计保存） */
  activityStatus?: number
}

// ==================== 展示文案 ====================
export const NODE_DEFAULT_TEXT = new Map<number, string>()
NODE_DEFAULT_TEXT.set(NodeType.USER_TASK_NODE, '请配置审批人')
NODE_DEFAULT_TEXT.set(NodeType.COPY_TASK_NODE, '请配置抄送人')
NODE_DEFAULT_TEXT.set(NodeType.CONDITION_NODE, '请设置条件')
NODE_DEFAULT_TEXT.set(NodeType.START_USER_NODE, '谁可发起')
NODE_DEFAULT_TEXT.set(NodeType.DELAY_TIMER_NODE, '请设置延迟时间')

export const NODE_DEFAULT_NAME = new Map<number, string>()
NODE_DEFAULT_NAME.set(NodeType.USER_TASK_NODE, '审批人')
NODE_DEFAULT_NAME.set(NodeType.COPY_TASK_NODE, '抄送人')
NODE_DEFAULT_NAME.set(NodeType.CONDITION_NODE, '条件')
NODE_DEFAULT_NAME.set(NodeType.START_USER_NODE, '发起人')
NODE_DEFAULT_NAME.set(NodeType.DELAY_TIMER_NODE, '延迟器')

/** 节点外观（图标 + 主题色） */
export const NODE_VISUALS: Record<number, { icon: string; color: string }> = {
  [NodeType.START_USER_NODE]: { icon: 'ant-design:user-outlined', color: '#0a7cff' },
  [NodeType.USER_TASK_NODE]: { icon: 'ant-design:audit-outlined', color: '#ff943e' },
  [NodeType.COPY_TASK_NODE]: { icon: 'ant-design:copy-outlined', color: '#32c2a0' },
  [NodeType.DELAY_TIMER_NODE]: { icon: 'ant-design:clock-circle-outlined', color: '#7b68ee' },
  [NodeType.CONDITION_NODE]: { icon: 'ant-design:branch-outlined', color: '#f5a623' },
  [NodeType.CONDITION_BRANCH_NODE]: { icon: 'ant-design:apartment-outlined', color: '#f5a623' },
  [NodeType.PARALLEL_BRANCH_NODE]: { icon: 'ant-design:partition-outlined', color: '#7b68ee' },
}

// ==================== 候选人策略展示 ====================
export interface StrategyOption {
  label: string
  value: CandidateStrategy
  /** 参数是否必填 */
  paramRequired: boolean
}

export const CANDIDATE_STRATEGIES: StrategyOption[] = [
  { label: '指定成员', value: CandidateStrategy.USER, paramRequired: true },
  { label: '指定角色', value: CandidateStrategy.ROLE, paramRequired: true },
  { label: '指定岗位', value: CandidateStrategy.POST, paramRequired: true },
  { label: '部门成员', value: CandidateStrategy.DEPT_MEMBER, paramRequired: true },
  { label: '部门负责人', value: CandidateStrategy.DEPT_LEADER, paramRequired: true },
  { label: '用户组', value: CandidateStrategy.USER_GROUP, paramRequired: true },
  { label: '发起人自选', value: CandidateStrategy.START_USER_SELECT, paramRequired: false },
  { label: '审批人自选', value: CandidateStrategy.APPROVE_USER_SELECT, paramRequired: false },
  { label: '发起人本人', value: CandidateStrategy.START_USER, paramRequired: false },
  { label: '发起人部门负责人', value: CandidateStrategy.START_USER_DEPT_LEADER, paramRequired: false },
]

export const APPROVE_METHODS = [
  { label: '随机挑选一人审批', value: ApproveMethodType.RANDOM },
  { label: '会签（可同时审批，按比例通过）', value: ApproveMethodType.BY_RATIO },
  { label: '或签（可同时审批，一人通过即可）', value: ApproveMethodType.ANY_OF },
  { label: '按顺序依次审批', value: ApproveMethodType.SEQUENTIAL },
]

export const APPROVE_TYPES = [
  { label: '人工审批', value: ApproveType.USER },
  { label: '自动通过', value: ApproveType.AUTO_APPROVE },
  { label: '自动拒绝', value: ApproveType.AUTO_REJECT },
]

export const TIMEOUT_HANDLER_TYPES = [
  { label: '自动提醒', value: TimeoutHandlerType.REMINDER },
  { label: '自动通过', value: TimeoutHandlerType.APPROVE },
  { label: '自动拒绝', value: TimeoutHandlerType.REJECT },
]

export const REJECT_HANDLER_TYPES = [
  { label: '终止流程', value: RejectHandlerType.FINISH_PROCESS },
  { label: '驳回到指定节点', value: RejectHandlerType.RETURN_USER_TASK },
]

export const ASSIGN_EMPTY_HANDLER_TYPES = [
  { label: '自动通过', value: AssignEmptyHandlerType.APPROVE },
  { label: '自动拒绝', value: AssignEmptyHandlerType.REJECT },
  { label: '指定成员审批', value: AssignEmptyHandlerType.ASSIGN_USER },
  { label: '转交给流程管理员', value: AssignEmptyHandlerType.ASSIGN_ADMIN },
]

export const ASSIGN_START_USER_HANDLER_TYPES = [
  { label: '由发起人对自己审批', value: AssignStartUserHandlerType.START_USER_AUDIT },
  { label: '自动跳过', value: AssignStartUserHandlerType.SKIP },
  { label: '转交给部门负责人审批', value: AssignStartUserHandlerType.ASSIGN_DEPT_LEADER },
]

export const TIME_UNIT_TYPES = [
  { label: '分钟', value: TimeUnitType.MINUTE },
  { label: '小时', value: TimeUnitType.HOUR },
  { label: '天', value: TimeUnitType.DAY },
]

/** 延迟器类型（DelaySetting.delayType：1 固定时长 / 2 固定日期） */
export const DELAY_TYPE = [
  { label: '固定时长', value: 1 },
  { label: '固定日期', value: 2 },
]

/** 条件配置方式（ConditionSetting.conditionType） */
export const CONDITION_CONFIG_TYPES = [
  { label: '条件规则', value: ConditionType.RULE },
  { label: '条件表达式', value: ConditionType.EXPRESSION },
]

/** 告警流程变量（条件规则可选字段，与后端注入的流程变量对齐） */
export const ALERT_VARIABLE_FIELDS = [
  { label: '告警对象 (alertObject)', value: 'alertObject' },
  { label: '告警事件 (alertEvent)', value: 'alertEvent' },
  { label: '算法任务名称 (taskName)', value: 'taskName' },
  { label: '任务类型 (taskType)', value: 'taskType' },
  { label: '设备名称 (deviceName)', value: 'deviceName' },
  { label: '设备编号 (deviceId)', value: 'deviceId' },
  { label: '边缘节点 (edgeNodeId)', value: 'edgeNodeId' },
]

export const COMPARISON_OPERATORS = [
  { label: '等于', value: '==' },
  { label: '不等于', value: '!=' },
  { label: '大于', value: '>' },
  { label: '大于等于', value: '>=' },
  { label: '小于', value: '<' },
  { label: '小于等于', value: '<=' },
  { label: '包含', value: 'contain' },
  { label: '不包含', value: '!contain' },
]

// ==================== 工厂方法 ====================
let nodeIdSeed = 0

/** 生成节点 ID（与 Flowable 活动Id兼容：字母开头） */
export function genNodeId(type: NodeType): string {
  nodeIdSeed += 1
  const prefixMap: Partial<Record<NodeType, string>> = {
    [NodeType.START_USER_NODE]: 'StartUser',
    [NodeType.USER_TASK_NODE]: 'Activity',
    [NodeType.COPY_TASK_NODE]: 'Copy',
    [NodeType.DELAY_TIMER_NODE]: 'Delay',
    [NodeType.CONDITION_NODE]: 'Condition',
    [NodeType.CONDITION_BRANCH_NODE]: 'Gateway',
    [NodeType.PARALLEL_BRANCH_NODE]: 'Gateway',
    [NodeType.END_EVENT_NODE]: 'EndEvent',
  }
  return `${prefixMap[type] ?? 'Activity'}_${Date.now()}_${nodeIdSeed}`
}

/** 创建新节点 */
export function createNode(type: NodeType, name?: string): SimpleFlowNode {
  const base: SimpleFlowNode = {
    id: genNodeId(type),
    type,
    name: name ?? NODE_DEFAULT_NAME.get(type) ?? '节点',
  }
  switch (type) {
    case NodeType.USER_TASK_NODE:
      return {
        ...base,
        approveType: ApproveType.USER,
        candidateStrategy: CandidateStrategy.USER,
        candidateParam: '',
        approveMethod: ApproveMethodType.ANY_OF,
        approveRatio: 100,
        rejectHandler: { type: RejectHandlerType.FINISH_PROCESS },
        timeoutHandler: { enable: false },
        assignEmptyHandler: { type: AssignEmptyHandlerType.APPROVE },
        assignStartUserHandlerType: AssignStartUserHandlerType.SKIP,
      }
    case NodeType.COPY_TASK_NODE:
      return {
        ...base,
        candidateStrategy: CandidateStrategy.USER,
        candidateParam: '',
      }
    case NodeType.DELAY_TIMER_NODE:
      return {
        ...base,
        delaySetting: { delayType: 1, delayTime: 'PT1H' },
      }
    case NodeType.CONDITION_NODE:
      return {
        ...base,
        conditionSetting: {
          conditionType: ConditionType.RULE,
          conditionGroups: {
            and: true,
            conditions: [
              {
                and: true,
                rules: [{ leftSide: 'alertEvent', opCode: '==', rightSide: '' }],
              },
            ],
          },
        },
      }
    default:
      return base
  }
}

/** 创建条件分支（含两个初始条件） */
export function createConditionBranch(parallel = false, afterNode?: SimpleFlowNode): SimpleFlowNode {
  const branchType = parallel ? NodeType.PARALLEL_BRANCH_NODE : NodeType.CONDITION_BRANCH_NODE
  const condition1 = createNode(NodeType.CONDITION_NODE, '条件1')
  const condition2 = createNode(NodeType.CONDITION_NODE, parallel ? '分支2' : '条件2')
  if (parallel) {
    // 并行分支用恒真条件实现
    condition1.conditionSetting!.conditionType = ConditionType.EXPRESSION
    condition1.conditionSetting!.conditionExpression = '${true}'
    condition2.conditionSetting!.conditionType = ConditionType.EXPRESSION
    condition2.conditionSetting!.conditionExpression = '${true}'
  }
  condition1.childNode = afterNode
  condition2.childNode = afterNode
  return {
    id: genNodeId(branchType),
    type: branchType,
    name: parallel ? '并行分支' : '条件分支',
    conditionNodes: [condition1, condition2],
  }
}

/** 根节点（发起人）默认结构 */
export function createStartUserNode(): SimpleFlowNode {
  return {
    id: 'StartUserNode',
    type: NodeType.START_USER_NODE,
    name: '发起人',
    showText: '告警规则自动发起 / 用户自发起',
  }
}

/** 深拷贝（简单结构，structuredClone 足够） */
export function cloneNode(node: SimpleFlowNode): SimpleFlowNode {
  return JSON.parse(JSON.stringify(node))
}
