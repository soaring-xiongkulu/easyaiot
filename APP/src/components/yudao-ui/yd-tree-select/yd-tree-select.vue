<template>
  <view v-if="useDefaultSlot" @click="open">
    <slot :label="displayValue" />
  </view>
  <wd-form-item
    v-else-if="label || prop"
    :title="label"
    :title-width="labelWidth"
    :prop="prop || undefined"
    :value="displayValue"
    :placeholder="placeholder"
    :is-link="!disabled"
    @click="open"
  />
  <wd-cell
    v-else
    :title="title"
    :value="displayValue"
    :placeholder="placeholder"
    :is-link="!disabled"
    @click="open"
  />

  <wd-cascader
    v-if="!isCheckboxMode"
    v-model:visible="visible"
    :model-value="singleValue"
    :options="data"
    :title="popupTitle"
    :check-strictly="checkStrictly"
    :value-key="fieldNames.value"
    :text-key="fieldNames.label"
    :children-key="fieldNames.children"
    @confirm="handleSingleConfirm"
  />

  <wd-popup
    v-else
    v-model="visible"
    position="bottom"
    safe-area-inset-bottom
    custom-style="border-radius: 24rpx 24rpx 0 0;"
    @close="handlePopupClose"
  >
    <view class="yd-tree-select">
      <!-- 弹窗标题栏 -->
      <view class="yd-tree-select__header">
        <view class="yd-tree-select__action yd-tree-select__action--cancel" @click="handleCancelClick">
          取消
        </view>
        <view class="yd-tree-select__title">
          {{ popupTitle }}
        </view>
        <view class="yd-tree-select__action yd-tree-select__action--confirm" @click="handleCheckboxConfirm">
          确定
        </view>
      </view>

      <!-- 工具栏 -->
      <view v-if="filterable || showToolbar" class="yd-tree-select__toolbar">
        <wd-search
          v-if="filterable"
          v-model="filterText"
          :placeholder="filterPlaceholder"
          hide-cancel
        />
        <view v-if="showToolbar" class="yd-tree-select__toolbar-actions">
          <wd-button size="small" plain @click="handleToggleAll">
            {{ allChecked ? '全不选' : '全选' }}
          </wd-button>
          <wd-button size="small" plain @click="handleToggleExpand">
            {{ allExpanded ? '全部折叠' : '全部展开' }}
          </wd-button>
        </view>
      </view>

      <!-- 树列表 -->
      <scroll-view scroll-y class="yd-tree-select__body">
        <view
          v-for="item in visibleNodes"
          :key="String(item.value)"
          class="yd-tree-select__node"
          :class="{ 'yd-tree-select__node--disabled': item.disabled }"
          :style="{ paddingLeft: `${24 + item.level * indent}rpx` }"
          @click="handleNodeClick(item)"
        >
          <view class="yd-tree-select__expand" @click.stop="handleExpand(item)">
            <view
              v-if="item.hasChildren && !filterText"
              class="yd-tree-select__caret"
              :class="{ 'yd-tree-select__caret--open': isExpanded(item.value) }"
            />
          </view>
          <view
            class="yd-tree-select__checkbox"
            :class="getCheckboxClass(item)"
            @click.stop="handleCheck(item)"
          >
            <view
              v-if="getCheckState(item.value).checked"
              class="yd-tree-select__checkbox-check"
            />
            <view v-else-if="getCheckState(item.value).halfChecked" class="yd-tree-select__checkbox-half" />
          </view>
          <view class="yd-tree-select__label">
            {{ item.label }}
          </view>
        </view>

        <!-- 空状态 -->
        <view v-if="visibleNodes.length === 0" class="yd-tree-select__empty">
          <wd-empty icon="no-content" tip="暂无数据" />
        </view>
      </scroll-view>
    </view>
  </wd-popup>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue'

type TreeSelectValue = string | number

interface TreeSelectFieldProps {
  children?: string
  disabled?: string
  label?: string
  value?: string
}

interface TreeSelectOption {
  [key: string]: any
}

interface TreeFlatNode {
  children: TreeFlatNode[]
  disabled: boolean
  hasChildren: boolean
  label: string
  level: number
  node: TreeSelectOption
  parentValue?: TreeSelectValue
  pathLabels: string[]
  value: TreeSelectValue
}

const componentProps = withDefaults(defineProps<{
  checkStrictly?: boolean
  clearable?: boolean
  data?: TreeSelectOption[]
  defaultExpandAll?: boolean
  defaultExpandedKeys?: TreeSelectValue[]
  disabled?: boolean
  filterPlaceholder?: string
  filterable?: boolean
  indent?: number
  label?: string
  labelWidth?: string
  modelValue?: TreeSelectValue | TreeSelectValue[]
  multiple?: boolean
  nodeKey?: string
  placeholder?: string
  prop?: string
  props?: TreeSelectFieldProps
  showCheckbox?: boolean
  showToolbar?: boolean
  title?: string
  useDefaultSlot?: boolean
  valueKey?: string
}>(), {
  checkStrictly: true,
  clearable: false,
  data: () => [],
  defaultExpandAll: false,
  defaultExpandedKeys: () => [],
  disabled: false,
  filterPlaceholder: '搜索选项',
  filterable: false,
  indent: 40,
  label: '',
  labelWidth: '180rpx',
  multiple: false,
  nodeKey: '',
  placeholder: '请选择',
  prop: '',
  props: () => ({}),
  showCheckbox: false,
  showToolbar: false,
  title: '',
  useDefaultSlot: false,
  valueKey: '',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: TreeSelectValue | TreeSelectValue[] | undefined): void
  (e: 'change', value: TreeSelectValue | TreeSelectValue[] | undefined): void
  (e: 'cancel'): void
  (e: 'confirm', payload: {
    checkedKeys?: TreeSelectValue[]
    halfCheckedKeys?: TreeSelectValue[]
    selectedNode?: TreeSelectOption
    selectedOptions?: TreeSelectOption[]
    value: TreeSelectValue | TreeSelectValue[] | undefined
  }): void
  (e: 'open'): void
  (e: 'close'): void
}>()

const visible = ref(false) // 弹窗显示状态
const filterText = ref('') // 树过滤关键字
const draftCheckedKeys = ref<Set<TreeSelectValue>>(new Set()) // 复选草稿值
const expandedKeys = ref<Set<TreeSelectValue>>(new Set()) // 展开的节点

const fieldNames = computed(() => { // 字段映射配置
  return {
    children: componentProps.props?.children || 'children',
    disabled: componentProps.props?.disabled || 'disabled',
    label: componentProps.props?.label || 'name',
    value: componentProps.props?.value || componentProps.valueKey || componentProps.nodeKey || 'id',
  }
})
const isCheckboxMode = computed(() => componentProps.multiple || componentProps.showCheckbox) // 是否复选模式
const popupTitle = computed(() => componentProps.title || componentProps.label || componentProps.placeholder) // 弹窗标题
const singleValue = computed(() => normalizeSingleValue(componentProps.modelValue)) // 单选值
const flatNodes = computed(() => flattenTree(componentProps.data)) // 扁平节点列表
const nodeMap = computed(() => new Map(flatNodes.value.map(item => [String(item.value), item]))) // 节点索引
const visibleNodes = computed(() => { // 当前可见节点
  if (filterText.value) {
    return flatNodes.value.filter(item => matchesFilter(item))
  }
  return flatNodes.value.filter((item) => {
    if (item.level === 0) {
      return true
    }
    const parent = getNode(item.parentValue)
    return parent ? isAncestorExpanded(item) : true
  })
})
const displayValue = computed(() => { // 入口展示文案
  if (isCheckboxMode.value) {
    return formatMultipleValue(componentProps.modelValue)
  }
  return formatSingleValue(componentProps.modelValue)
})
const allChecked = computed(() => { // 是否已全选
  const selectableValues = flatNodes.value.filter(item => !item.disabled).map(item => item.value)
  return selectableValues.length > 0 && selectableValues.every(value => getCheckState(value).checked)
})
const allExpanded = computed(() => { // 是否已全部展开
  const expandableValues = flatNodes.value.filter(item => item.hasChildren).map(item => item.value)
  return expandableValues.length > 0 && expandableValues.every(value => expandedKeys.value.has(value))
})

watch(visible, (value) => {
  if (value) {
    initializePopupState()
    emit('open')
  } else {
    emit('close')
  }
})

/** 打开选择弹窗 */
function open() {
  if (componentProps.disabled) {
    return
  }
  visible.value = true
}

/** 清空选择 */
function clear() {
  const nextValue = isCheckboxMode.value ? [] : undefined
  emit('update:modelValue', nextValue)
  emit('change', nextValue)
}

/** 取消按钮操作 */
function handleCancelClick() {
  emit('cancel')
  visible.value = false
}

/** 关闭弹窗 */
function handlePopupClose() {
  visible.value = false
}

/** 单选确认 */
function handleSingleConfirm({ value, selectedOptions }: { selectedOptions: TreeSelectOption[], value: any }) {
  const selected = Array.isArray(value) ? value.at(-1) : value
  const nextValue = isEmptyValue(selected) ? undefined : selected
  emit('update:modelValue', nextValue)
  emit('change', nextValue)
  emit('confirm', {
    selectedNode: selectedOptions?.at(-1),
    selectedOptions,
    value: nextValue,
  })
}

/** 复选确认 */
function handleCheckboxConfirm() {
  const checkedKeys = getCheckedKeys(false)
  const halfCheckedKeys = getHalfCheckedKeys()
  const nextValue = checkedKeys
  emit('update:modelValue', nextValue)
  emit('change', nextValue)
  emit('confirm', {
    checkedKeys,
    halfCheckedKeys,
    value: nextValue,
  })
  visible.value = false
}

/** 处理节点点击 */
function handleNodeClick(item: TreeFlatNode) {
  handleCheck(item)
}

/** 展开或折叠节点 */
function handleExpand(item: TreeFlatNode) {
  if (!item.hasChildren) {
    return
  }
  const next = new Set(expandedKeys.value)
  if (next.has(item.value)) {
    next.delete(item.value)
  } else {
    next.add(item.value)
  }
  expandedKeys.value = next
}

/** 勾选节点 */
function handleCheck(item: TreeFlatNode) {
  if (item.disabled) {
    return
  }
  const next = new Set(draftCheckedKeys.value)
  if (componentProps.checkStrictly) {
    if (next.has(item.value)) {
      next.delete(item.value)
    } else {
      next.add(item.value)
    }
    draftCheckedKeys.value = next
    return
  }

  // 父子联动：当前节点和全部子节点保持同一勾选态。
  const state = getCheckState(item.value)
  const checked = !state.checked
  for (const value of getNodeAndChildrenValues(item)) {
    const node = getNode(value)
    if (!node?.disabled) {
      checked ? next.add(value) : next.delete(value)
    }
  }
  syncParentCheckedKeys(item, next)
  draftCheckedKeys.value = next
}

/** 全选或全不选 */
function handleToggleAll() {
  if (allChecked.value) {
    draftCheckedKeys.value = new Set()
    return
  }
  draftCheckedKeys.value = new Set(flatNodes.value.filter(item => !item.disabled).map(item => item.value))
}

/** 全部展开或折叠 */
function handleToggleExpand() {
  if (allExpanded.value) {
    expandedKeys.value = new Set()
    return
  }
  expandedKeys.value = new Set(flatNodes.value.filter(item => item.hasChildren).map(item => item.value))
}

/** 是否已展开 */
function isExpanded(value: TreeSelectValue) {
  return expandedKeys.value.has(value)
}

/** 获取复选样式 */
function getCheckboxClass(item: TreeFlatNode) {
  const state = getCheckState(item.value)
  return {
    'yd-tree-select__checkbox--checked': state.checked,
    'yd-tree-select__checkbox--disabled': item.disabled,
    'yd-tree-select__checkbox--half': state.halfChecked,
  }
}

/** 获取节点选中状态 */
function getCheckState(value: TreeSelectValue): { checked: boolean, halfChecked: boolean } {
  return getCheckStateByKeys(value, draftCheckedKeys.value)
}

/** 返回选中节点编号 */
function getCheckedKeys(leafOnly = false) {
  const checkedKeys = getActiveCheckedKeys()
  return flatNodes.value
    .filter(item => getCheckStateByKeys(item.value, checkedKeys).checked)
    .filter(item => !leafOnly || !item.hasChildren)
    .map(item => item.value)
}

/** 返回半选节点编号 */
function getHalfCheckedKeys() {
  if (componentProps.checkStrictly) {
    return []
  }
  const checkedKeys = getActiveCheckedKeys()
  return flatNodes.value
    .filter(item => getCheckStateByKeys(item.value, checkedKeys).halfChecked)
    .map(item => item.value)
}

/** 设置选中节点编号 */
function setCheckedKeys(keys: TreeSelectValue[]) {
  draftCheckedKeys.value = normalizeInitialCheckedKeys(keys)
}

defineExpose({
  clear,
  getCheckedKeys,
  getHalfCheckedKeys,
  open,
  setCheckedKeys,
})

/** 初始化弹窗状态 */
function initializePopupState() {
  filterText.value = ''
  draftCheckedKeys.value = normalizeInitialCheckedKeys(normalizeMultipleValue(componentProps.modelValue))
  expandedKeys.value = getInitialExpandedKeys()
}

/** 获取当前生效的选中值 */
function getActiveCheckedKeys() {
  return visible.value
    ? draftCheckedKeys.value
    : normalizeInitialCheckedKeys(normalizeMultipleValue(componentProps.modelValue))
}

/** 获取初始展开节点 */
function getInitialExpandedKeys() {
  if (componentProps.defaultExpandAll) {
    return new Set(flatNodes.value.filter(item => item.hasChildren).map(item => item.value))
  }

  const next = new Set(componentProps.defaultExpandedKeys)
  const selectedValues = isCheckboxMode.value
    ? normalizeMultipleValue(componentProps.modelValue)
    : [normalizeSingleValue(componentProps.modelValue)].filter(isValidValue)
  for (const value of selectedValues) {
    const item = getNode(value)
    if (item) {
      addAncestorKeys(item, next)
    }
  }
  return next
}

/** 归一化初始选中值 */
function normalizeInitialCheckedKeys(values: TreeSelectValue[]) {
  const next = new Set(values.filter(isValidValue))
  if (componentProps.checkStrictly) {
    return next
  }

  // 后端常返回 checked + halfChecked。父节点未全选时按半选展示，避免误选子节点。
  for (const item of flatNodes.value) {
    if (!item.hasChildren || !next.has(item.value)) {
      continue
    }
    const descendants = getDescendantValues(item).filter((value) => {
      const node = getNode(value)
      return node && !node.disabled
    })
    if (descendants.length > 0 && !descendants.every(value => next.has(value))) {
      next.delete(item.value)
    }
  }
  syncAllParentCheckedKeys(next)
  return next
}

/** 同步全部父节点选中状态 */
function syncAllParentCheckedKeys(checkedKeys: Set<TreeSelectValue>) {
  for (const item of [...flatNodes.value].reverse()) {
    if (!item.hasChildren) {
      continue
    }
    const selectableChildren = item.children.filter(child => !child.disabled)
    const allChildrenChecked = selectableChildren.length > 0
      && selectableChildren.every(child => getCheckStateByKeys(child.value, checkedKeys).checked)
    if (allChildrenChecked) {
      checkedKeys.add(item.value)
    } else {
      checkedKeys.delete(item.value)
    }
  }
}

/** 同步当前节点的父级选中状态 */
function syncParentCheckedKeys(item: TreeFlatNode, checkedKeys: Set<TreeSelectValue>) {
  let parent = getNode(item.parentValue)
  while (parent) {
    const selectableChildren = parent.children.filter(child => !child.disabled)
    const allChildrenChecked = selectableChildren.length > 0
      && selectableChildren.every(child => getCheckStateByKeys(child.value, checkedKeys).checked)
    if (allChildrenChecked) {
      checkedKeys.add(parent.value)
    } else {
      checkedKeys.delete(parent.value)
    }
    parent = getNode(parent.parentValue)
  }
}

/** 根据选中值计算节点状态 */
function getCheckStateByKeys(value: TreeSelectValue, checkedKeys: Set<TreeSelectValue>): { checked: boolean, halfChecked: boolean } {
  const item = getNode(value)
  if (!item || componentProps.checkStrictly || !item.hasChildren) {
    return {
      checked: checkedKeys.has(value),
      halfChecked: false,
    }
  }
  const selectableChildren = item.children.filter(child => !child.disabled)
  if (selectableChildren.length === 0) {
    return {
      checked: checkedKeys.has(value),
      halfChecked: false,
    }
  }
  const childStates = selectableChildren.map(child => getCheckStateByKeys(child.value, checkedKeys))
  const checked = childStates.every(state => state.checked)
  const halfChecked = !checked && childStates.some(state => state.checked || state.halfChecked)
  return { checked, halfChecked }
}

/** 扁平化树节点 */
function flattenTree(list: TreeSelectOption[], level = 0, parent?: TreeFlatNode, pathLabels: string[] = []): TreeFlatNode[] {
  return list.flatMap((node) => {
    const value = getNodeValue(node)
    if (!isValidValue(value)) {
      return []
    }
    const label = getNodeLabel(node, value)
    const children = getNodeChildren(node)
    const item: TreeFlatNode = {
      children: [],
      disabled: !!node[fieldNames.value.disabled],
      hasChildren: children.length > 0,
      label,
      level,
      node,
      parentValue: parent?.value,
      pathLabels: [...pathLabels, label],
      value,
    }
    const flatChildren = flattenTree(children, level + 1, item, item.pathLabels)
    item.children = flatChildren.filter(child => child.parentValue === item.value)
    return [item, ...flatChildren]
  })
}

/** 获取节点 */
function getNode(value?: TreeSelectValue) {
  if (!isValidValue(value)) {
    return undefined
  }
  return nodeMap.value.get(String(value))
}

/** 获取节点值 */
function getNodeValue(node: TreeSelectOption) {
  return node[fieldNames.value.value] ?? node.value ?? node.key ?? node.id
}

/** 获取节点名称 */
function getNodeLabel(node: TreeSelectOption, value: TreeSelectValue) {
  return String(node[fieldNames.value.label] ?? node.label ?? node.text ?? node.name ?? value)
}

/** 获取子节点 */
function getNodeChildren(node: TreeSelectOption) {
  const children = node[fieldNames.value.children]
  return Array.isArray(children) ? children : []
}

/** 获取节点及子节点编号 */
function getNodeAndChildrenValues(item: TreeFlatNode) {
  return [item.value, ...getDescendantValues(item)]
}

/** 获取全部子节点编号 */
function getDescendantValues(item: TreeFlatNode): TreeSelectValue[] {
  return item.children.flatMap(child => [child.value, ...getDescendantValues(child)])
}

/** 判断祖先节点是否都已展开 */
function isAncestorExpanded(item: TreeFlatNode): boolean {
  let parent = getNode(item.parentValue)
  while (parent) {
    if (!expandedKeys.value.has(parent.value)) {
      return false
    }
    parent = getNode(parent.parentValue)
  }
  return true
}

/** 添加祖先节点编号 */
function addAncestorKeys(item: TreeFlatNode, keys: Set<TreeSelectValue>) {
  let parent = getNode(item.parentValue)
  while (parent) {
    keys.add(parent.value)
    parent = getNode(parent.parentValue)
  }
}

/** 判断节点是否匹配搜索 */
function matchesFilter(item: TreeFlatNode) {
  const keyword = filterText.value.trim()
  if (!keyword) {
    return true
  }
  if (item.label.includes(keyword)) {
    return true
  }
  return item.children.some(child => matchesFilter(child))
}

/** 格式化单选展示文案 */
function formatSingleValue(value: any) {
  const nextValue = normalizeSingleValue(value)
  if (!isValidValue(nextValue)) {
    return ''
  }
  return getNode(nextValue)?.pathLabels.join(' / ') || String(nextValue)
}

/** 格式化多选展示文案 */
function formatMultipleValue(value: any) {
  // 后端可能返回 checked + halfChecked，展示时只统计真实全选节点。
  const checkedKeys = normalizeInitialCheckedKeys(normalizeMultipleValue(value))
  const values = flatNodes.value
    .filter(item => getCheckStateByKeys(item.value, checkedKeys).checked)
    .map(item => item.value)
  if (values.length === 0) {
    return ''
  }
  const labels = values.map(item => getNode(item)?.label || String(item))
  const visibleLabels = labels.slice(0, 2).join('、')
  return values.length > 2 ? `${visibleLabels} 等 ${values.length}项` : visibleLabels
}

/** 归一化单选值 */
function normalizeSingleValue(value: any): TreeSelectValue | '' {
  const nextValue = Array.isArray(value) ? value.at(-1) : value
  return isValidValue(nextValue) ? nextValue : ''
}

/** 归一化多选值 */
function normalizeMultipleValue(value: any): TreeSelectValue[] {
  return Array.isArray(value) ? value.filter(isValidValue) : []
}

/** 判断有效值 */
function isValidValue(value: any): value is TreeSelectValue {
  return (typeof value === 'number' || typeof value === 'string') && value !== ''
}

/** 判断空值 */
function isEmptyValue(value: any) {
  return value === undefined || value === null || value === ''
}
</script>

<style lang="scss" scoped>
.yd-tree-select {
  display: flex;
  width: 100vw;
  height: 70vh;
  flex-direction: column;
  background-color: #fff;

  &__header {
    position: relative;
    display: flex;
    height: 88rpx;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1rpx solid #f0f0f0;
    padding: 0 24rpx;
  }

  &__title {
    max-width: 420rpx;
    overflow: hidden;
    color: #1f1f1f;
    font-size: 32rpx;
    font-weight: 600;
    text-align: center;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__action {
    min-width: 88rpx;
    font-size: 28rpx;

    &--cancel {
      color: #8c8c8c;
    }

    &--confirm {
      color: var(--wot-color-theme);
      text-align: right;
    }
  }

  &__toolbar {
    border-bottom: 1rpx solid #f5f5f5;
    background-color: #fff;
  }

  &__toolbar-actions {
    display: flex;
    gap: 16rpx;
    padding: 0 24rpx 20rpx;
  }

  &__body {
    min-height: 0;
    flex: 1;
  }

  &__node {
    display: flex;
    min-height: 88rpx;
    align-items: center;
    border-bottom: 1rpx solid #f7f7f7;
    padding-right: 24rpx;
    background-color: #fff;

    &--disabled {
      opacity: 0.45;
    }
  }

  &__expand {
    width: 48rpx;
    height: 48rpx;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  &__caret {
    width: 16rpx;
    height: 16rpx;
    border-color: #8c8c8c;
    border-style: solid;
    border-width: 0 3rpx 3rpx 0;
    transform: rotate(-45deg);
  }

  &__caret--open {
    transform: rotate(45deg);
  }

  &__checkbox {
    width: 36rpx;
    height: 36rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2rpx solid #d9d9d9;
    border-radius: 6rpx;
    color: #fff;
    font-size: 24rpx;
    line-height: 1;

    &--checked,
    &--half {
      border-color: var(--wot-color-theme, #2f7dff);
      background-color: var(--wot-color-theme, #2f7dff);
    }

    &--disabled {
      background-color: #f5f5f5;
    }
  }

  &__checkbox-half {
    width: 18rpx;
    height: 4rpx;
    border-radius: 999rpx;
    background-color: #fff;
  }

  &__checkbox-check {
    width: 10rpx;
    height: 18rpx;
    margin-bottom: 4rpx;
    border-color: #fff;
    border-style: solid;
    border-width: 0 4rpx 4rpx 0;
    transform: rotate(45deg);
  }

  &__label {
    min-width: 0;
    flex: 1;
    overflow: hidden;
    margin-left: 20rpx;
    color: #333;
    font-size: 30rpx;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__empty {
    padding-top: 120rpx;
  }
}
</style>
