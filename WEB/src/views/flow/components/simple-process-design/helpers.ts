import type { Ref } from 'vue'
import { computed, ref } from 'vue'
import type { SimpleFlowNode } from './consts'
import { CandidateStrategy, CANDIDATE_STRATEGIES, NodeType } from './consts'

/** 监听当前节点引用（节点内容为就地修改，删除/替换时走 update:flowNode 事件） */
export function useWatchNode(props: { flowNode: SimpleFlowNode }): Ref<SimpleFlowNode> {
  return computed(() => props.flowNode) as Ref<SimpleFlowNode>
}

/** 点击标题进入行内编辑 */
export function useNodeName(node: Ref<SimpleFlowNode>) {
  const editing = ref(false)
  function clickTitle() {
    editing.value = true
  }
  function changeNodeName() {
    editing.value = false
    if (!node.value.name || !node.value.name.trim()) {
      node.value.name = '未命名节点'
    }
  }
  return { editing, clickTitle, changeNodeName }
}

/** 按候选人策略生成节点摘要文案 */
export function buildCandidateShowText(strategy?: CandidateStrategy, param?: string, resolveNames?: (strategy: CandidateStrategy, ids: string[]) => string[]): string {
  if (!strategy) {
    return ''
  }
  const option = CANDIDATE_STRATEGIES.find(item => item.value === strategy)
  const label = option?.label ?? '未配置'
  if (!option?.paramRequired) {
    return label
  }
  if (!param) {
    return ''
  }
  const ids = param.split(',').filter(Boolean)
  if (resolveNames) {
    const names = resolveNames(strategy, ids)
    return `${label}：${names.join('、')}`
  }
  return `${label}：${ids.length} 人/项`
}

/** 将超时时长 ISO8601（PT1H30M）解析为数值 + 单位，用于表单展示 */
export function parseTimeDuration(iso?: string): { value: number; unit: number } {
  if (!iso) {
    return { value: 1, unit: 2 }
  }
  const match = /^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)D)?$/.exec(iso)
  if (!match) {
    return { value: 1, unit: 2 }
  }
  if (match[1]) {
    return { value: Number(match[1]), unit: 2 }
  }
  if (match[2]) {
    return { value: Number(match[2]), unit: 1 }
  }
  if (match[3]) {
    return { value: Number(match[3]), unit: 3 }
  }
  return { value: 1, unit: 2 }
}

/** 数值 + 单位 → ISO8601 时长 */
export function buildTimeDuration(value: number, unit: number): string {
  if (unit === 2) {
    return `PT${value}H`
  }
  if (unit === 3) {
    return `PT${value}D`
  }
  return `PT${value}M`
}

/** 从流程树中收集全部审批节点（供驳回/退回选择目标节点） */
export function collectUserTaskNodes(root?: SimpleFlowNode): SimpleFlowNode[] {
  const result: SimpleFlowNode[] = []
  const walk = (node?: SimpleFlowNode, visited = new Set<string>()) => {
    if (!node || visited.has(node.id)) {
      return
    }
    visited.add(node.id)
    if (node.type === NodeType.USER_TASK_NODE) {
      result.push(node)
    }
    node.conditionNodes?.forEach(branch => walk(branch.childNode, visited))
    walk(node.childNode, visited)
  }
  walk(root)
  return result
}

/** 校验流程树，返回错误信息列表（空数组代表通过） */
export function validateFlowTree(root?: SimpleFlowNode): string[] {
  const errors: string[] = []
  if (!root) {
    return ['流程为空，请先设计流程']
  }
  const walk = (node?: SimpleFlowNode) => {
    if (!node) {
      return
    }
    switch (node.type) {
      case NodeType.USER_TASK_NODE: {
        if (node.approveType === undefined) {
          node.approveType = 1
        }
        if (node.approveType === 1) {
          const option = CANDIDATE_STRATEGIES.find(item => item.value === node.candidateStrategy)
          if (!node.candidateStrategy) {
            errors.push(`「${node.name}」未配置审批人`)
          }
          else if (option?.paramRequired && !node.candidateParam) {
            errors.push(`「${node.name}」的候选人参数不能为空`)
          }
        }
        if (node.approveMethod === 2 && (!node.approveRatio || node.approveRatio < 1)) {
          errors.push(`「${node.name}」会签比例必须大于 0`)
        }
        break
      }
      case NodeType.COPY_TASK_NODE: {
        const option = CANDIDATE_STRATEGIES.find(item => item.value === node.candidateStrategy)
        if (!node.candidateStrategy) {
          errors.push(`「${node.name}」未配置抄送人`)
        }
        else if (option?.paramRequired && !node.candidateParam) {
          errors.push(`「${node.name}」的抄送人参数不能为空`)
        }
        break
      }
      case NodeType.CONDITION_BRANCH_NODE:
      case NodeType.PARALLEL_BRANCH_NODE: {
        if (!node.conditionNodes || node.conditionNodes.length < 2) {
          errors.push(`「${node.name}」至少需要 2 个分支`)
        }
        else if (node.type === NodeType.CONDITION_BRANCH_NODE) {
          const flows = node.conditionNodes
          const hasDefault = flows.some(item => item.conditionSetting?.defaultFlow)
          const unconfigured = flows.filter(item => !item.conditionSetting?.defaultFlow
            && !(item.conditionSetting?.conditionType === 2 && item.conditionSetting?.conditionGroups)
            && !(item.conditionSetting?.conditionType === 1 && item.conditionSetting?.conditionExpression))
          if (!hasDefault && unconfigured.length > 0) {
            errors.push(`「${node.name}」存在未设置条件且未设为默认的分支`)
          }
        }
        node.conditionNodes?.forEach(item => walk(item.childNode))
        break
      }
      case NodeType.CONDITION_NODE: {
        const setting = node.conditionSetting
        if (setting?.conditionType === 2) {
          const rules = setting.conditionGroups?.conditions?.flatMap(item => item.rules ?? []) ?? []
          if (rules.some(rule => !rule.leftSide || rule.rightSide === undefined || rule.rightSide === '')) {
            errors.push(`「${node.name}」条件规则未填写完整`)
          }
        }
        break
      }
    }
    walk(node.childNode)
  }
  walk(root)
  return errors
}

/** 条件规则 → 展示文案 */
export function buildConditionShowText(node: SimpleFlowNode): string {
  const setting = node.conditionSetting
  if (!setting) {
    return ''
  }
  if (setting.defaultFlow) {
    return '默认分支'
  }
  if (setting.conditionType === 1) {
    return setting.conditionExpression || ''
  }
  const rules = setting.conditionGroups?.conditions?.flatMap(item => item.rules ?? []) ?? []
  return rules.map(rule => `${rule.leftSide} ${rule.opCode} ${rule.rightSide}`).join(setting.conditionGroups?.and ? ' 且 ' : ' 或 ')
}

/** 节点摘要文案（设计器卡片动态计算，不依赖后端存储的 showText） */
export function nodeDisplayText(node: SimpleFlowNode): string {
  switch (node.type) {
    case NodeType.START_USER_NODE:
      return node.showText ?? '告警规则自动发起 / 用户自发起'
    case NodeType.USER_TASK_NODE: {
      if (node.approveType === 2) {
        return '自动通过'
      }
      if (node.approveType === 3) {
        return '自动拒绝'
      }
      const text = buildCandidateShowText(node.candidateStrategy, node.candidateParam)
      return text
    }
    case NodeType.COPY_TASK_NODE:
      return buildCandidateShowText(node.candidateStrategy, node.candidateParam)
    case NodeType.CONDITION_NODE:
      return buildConditionShowText(node)
    case NodeType.DELAY_TIMER_NODE: {
      const setting = node.delaySetting
      if (!setting?.delayTime) {
        return ''
      }
      const parsed = parseTimeDuration(setting.delayTime)
      const unitLabel = ['', '分钟', '小时', '天'][parsed.unit] ?? ''
      return setting.delayType === 2 ? setting.delayTime : `延迟 ${parsed.value} ${unitLabel}`
    }
    default:
      return node.showText ?? ''
  }
}
