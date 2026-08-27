<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    width="95%"
    placement="right"
    :showFooter="false"
    destroy-on-close
    class="panel-editor-drawer"
  >
    <div class="panel-editor">
      <!-- 顶部：模板元信息 + 操作区（参照主流装修器的头部动线：左信息、右动作） -->
      <div class="meta-card">
        <div class="meta-fields">
          <div class="meta-field">
            <span class="meta-label">模板名称<i class="req">*</i></span>
            <Input
              v-model:value="meta.templateName"
              :class="{'has-error': metaErrors.templateName}"
              :disabled="isView"
              placeholder="如：智能插座控制面板"
              @change="metaErrors.templateName = ''"
            />
          </div>
          <div class="meta-field">
            <span class="meta-label">模板编码<i class="req">*</i></span>
            <Input
              v-model:value="meta.templateCode"
              :class="{'has-error': metaErrors.templateCode}"
              :disabled="isView || !!editingId"
              placeholder="如：plug-panel-v1"
              @change="metaErrors.templateCode = ''"
            />
          </div>
          <div class="meta-field meta-field-product">
            <span class="meta-label">绑定产品<i class="req">*</i></span>
            <Select
              v-model:value="meta.productIdentification"
              :class="{'has-error': metaErrors.productIdentification}"
              :disabled="isView"
              show-search
              option-filter-prop="label"
              :options="productOptions"
              placeholder="选择要下发面板的产品"
              @change="onProductChange"
            />
          </div>
          <div class="meta-field meta-field-grow">
            <span class="meta-label">备注</span>
            <Input v-model:value="meta.remark" :disabled="isView" placeholder="选填" />
          </div>
        </div>
        <div class="meta-actions">
          <div class="source-toggle">
            <span class="source-toggle-label">JSON 源码</span>
            <Switch v-model:checked="sourceMode" :disabled="isView" size="small" />
          </div>
          <template v-if="!isView">
            <Button @click="handleClose">取消</Button>
            <Button type="primary" :loading="saving" @click="handleSave">
              {{ editingId ? '保存修改' : '保存为草稿' }}
            </Button>
          </template>
          <Button v-else type="primary" @click="handleClose">关闭</Button>
        </div>
      </div>
      <Alert
        v-if="!isView && productBindInfo"
        :type="productBindType"
        show-icon
        banner
        class="meta-alert"
        :message="productBindInfo"
      />

      <div class="panel-workspace">
        <!-- 左：组件库（分类折叠）+ 组件图层 -->
        <div class="workspace-card workspace-left">
          <template v-for="cate in widgetCategories" :key="cate.key">
            <div class="cate-section">
              <div class="cate-header" @click="toggleCate(cate.key)">
                <component :is="cate.icon" class="cate-icon" />
                <span class="cate-title">{{ cate.label }}</span>
                <DownOutlined class="cate-arrow" :class="{collapsed: collapsed[cate.key]}" />
              </div>
              <Transition name="cate-fold">
                <div v-show="!collapsed[cate.key]" class="palette-grid">
                  <Tooltip v-for="t in widgetsOf(cate.key)" :key="t.type" :title="t.desc" placement="right">
                    <div
                      class="palette-item"
                      :class="{disabled: isView}"
                      :draggable="!isView"
                      @click="!isView && addWidget(t.type)"
                      @dragstart="onPaletteDragStart($event, t.type)"
                    >
                      <component :is="t.icon" class="palette-icon" />
                      <span class="palette-label">{{ t.label }}</span>
                    </div>
                  </Tooltip>
                </div>
              </Transition>
            </div>
          </template>

          <div class="layer-section">
            <div class="cate-header static">
              <OrderedListOutlined class="cate-icon" />
              <span class="cate-title">组件图层（{{ widgets.length }}）</span>
              <Popconfirm v-if="!isView && widgets.length" title="清空画布上所有组件？" @confirm="clearWidgets">
                <ClearOutlined class="layer-clear" />
              </Popconfirm>
            </div>
            <div class="layer-body">
              <Empty
                v-if="!widgets.length"
                description="画布为空 · 点击左侧组件添加"
                :image="Empty.PRESENTED_IMAGE_SIMPLE"
                :image-style="{height: '48px'}"
              />
              <TransitionGroup v-else name="widget-list" tag="div" class="layer-list">
                <div
                  v-for="(w, idx) in widgets"
                  :key="w.uid"
                  class="layer-item"
                  :class="{active: w.uid === activeUid}"
                  @click="!isView && (activeUid = w.uid)"
                >
                  <span class="layer-index">{{ idx + 1 }}</span>
                  <component :is="typeMeta(w.type).icon" class="layer-icon" />
                  <span class="layer-title">{{ w.title || typeMeta(w.type).label }}</span>
                  <span v-if="w.span === 'half'" class="layer-span">半</span>
                  <span v-if="!isView" class="layer-actions">
                    <ArrowUpOutlined class="op" @click.stop="move(idx, -1)" />
                    <ArrowDownOutlined class="op" @click.stop="move(idx, 1)" />
                    <CopyOutlined class="op" @click.stop="duplicateWidget(idx)" />
                    <DeleteOutlined class="op danger" @click.stop="removeWidget(idx)" />
                  </span>
                </div>
              </TransitionGroup>
            </div>
          </div>
        </div>

        <!-- 中：手机预览画布 / JSON 源码 -->
        <div class="workspace-center">
          <template v-if="!sourceMode">
            <div class="canvas-scroll" @click.self="activeUid = null">
              <div class="canvas-stage" ref="stageRef">
                <!-- 画布浮动标注 -->
                <div class="float-label" style="top: 34px"><i class="float-dot"></i>顶部导航栏</div>
                <div class="float-label" style="top: 68px"><i class="float-dot page"></i>控制台</div>

                <!-- 手机机身 -->
                <div class="phone-frame">
                  <div class="phone-island"></div>
                  <div class="phone-status">
                    <span class="ps-time">9:41</span>
                    <span class="ps-icons">
                      <svg width="17" height="11" viewBox="0 0 17 11" fill="currentColor">
                        <rect x="0" y="7" width="3" height="4" rx="0.8" />
                        <rect x="4.5" y="5" width="3" height="6" rx="0.8" />
                        <rect x="9" y="2.5" width="3" height="8.5" rx="0.8" />
                        <rect x="13.5" y="0" width="3" height="11" rx="0.8" />
                      </svg>
                      <svg width="15" height="11" viewBox="0 0 15 11" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                        <path d="M1.5 3.8a9 9 0 0 1 12 0" />
                        <path d="M3.8 6.4a5.6 5.6 0 0 1 7.4 0" />
                        <circle cx="7.5" cy="9.3" r="1.1" fill="currentColor" stroke="none" />
                      </svg>
                      <svg width="25" height="12" viewBox="0 0 25 12">
                        <rect x="0.5" y="0.5" width="21" height="11" rx="3.2" fill="none" stroke="currentColor" opacity="0.4" />
                        <rect x="2" y="2" width="16" height="8" rx="1.8" fill="currentColor" />
                        <path d="M23 3.8v4.4c1.1-.3 1.6-1.1 1.6-2.2s-.5-1.9-1.6-2.2z" fill="currentColor" opacity="0.4" />
                      </svg>
                    </span>
                  </div>
                  <div class="phone-navbar">
                    <span class="phone-back">‹</span>
                    <div class="phone-title">{{ meta.templateName || '设备控制台' }}</div>
                    <span class="phone-online">在线</span>
                  </div>
                  <div
                    class="phone-body"
                    ref="phoneBodyRef"
                    @click.self="activeUid = null"
                    @dragover.prevent="onCanvasDragOver"
                    @dragleave="onCanvasDragLeave"
                    @drop.prevent="onCanvasDrop"
                  >
                    <template v-for="(w, idx) in widgets" :key="w.uid">
                      <div v-if="dragOverIndex === idx" class="drop-line"></div>
                      <div
                        class="mock-card"
                        :class="{half: w.span === 'half', selected: w.uid === activeUid}"
                        @click="!isView && (activeUid = w.uid)"
                      >
                        <!-- 开关 -->
                        <template v-if="w.type === 'switch'">
                          <div class="mock-row">
                            <span class="mock-label">{{ w.title }}</span>
                            <span class="mock-switch on"><i></i></span>
                          </div>
                        </template>
                        <!-- 滑条 / 步进器 -->
                        <template v-else-if="w.type === 'slider' || w.type === 'number'">
                          <div class="mock-col">
                            <div class="mock-row">
                              <span class="mock-label">{{ w.title }}</span>
                              <span class="mock-value">42<i class="mock-unit">{{ w.unit }}</i></span>
                            </div>
                            <div v-if="w.type === 'slider'" class="mock-slider">
                              <i :style="sliderStyle(w)"></i>
                            </div>
                            <div v-else class="mock-stepper"><b>−</b><span>42</span><b>+</b></div>
                          </div>
                        </template>
                        <!-- 状态标签 -->
                        <template v-else-if="w.type === 'status'">
                          <div class="mock-row">
                            <span class="mock-label">{{ w.title }}</span>
                            <span class="mock-pill" :style="pillStyle(w)"><i></i>{{ optionLabel(w) }}</span>
                          </div>
                        </template>
                        <!-- 数值文本 -->
                        <template v-else-if="w.type === 'text'">
                          <div class="mock-col">
                            <span class="mock-label">{{ w.title }}</span>
                            <span class="mock-big">25.4<i class="mock-unit">{{ w.unit }}</i></span>
                          </div>
                        </template>
                        <!-- 命令按钮 -->
                        <template v-else-if="w.type === 'button'">
                          <div class="mock-col center">
                            <span class="mock-btn" :style="btnStyle(w)">{{ w.title }}</span>
                          </div>
                        </template>
                        <!-- 折线图 -->
                        <template v-else-if="w.type === 'chart'">
                          <div class="mock-col">
                            <div class="mock-row">
                              <span class="mock-label">{{ w.title }}</span>
                              <span class="mock-value">42<i class="mock-unit">{{ w.unit }}</i></span>
                            </div>
                            <svg class="mock-chart" viewBox="0 0 200 60" preserveAspectRatio="none">
                              <defs>
                                <linearGradient :id="`chartFill-${w.uid}`" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="0%" :stop-color="themeColor(w)" stop-opacity="0.22" />
                                  <stop offset="100%" :stop-color="themeColor(w)" stop-opacity="0" />
                                </linearGradient>
                              </defs>
                              <polygon
                                :fill="`url(#chartFill-${w.uid})`"
                                points="0,48 25,40 50,44 75,30 100,36 125,22 150,28 175,14 200,20 200,60 0,60"
                              />
                              <polyline
                                fill="none" :stroke="themeColor(w)" stroke-width="2"
                                stroke-linecap="round" stroke-linejoin="round"
                                points="0,48 25,40 50,44 75,30 100,36 125,22 150,28 175,14 200,20"
                              />
                              <circle cx="197" cy="20" r="3" :fill="themeColor(w)" />
                            </svg>
                          </div>
                        </template>
                        <!-- 仪表盘 -->
                        <template v-else-if="w.type === 'gauge'">
                          <div class="mock-col">
                            <div class="mock-row">
                              <span class="mock-label">{{ w.title }}</span>
                              <span class="mock-value">68<i class="mock-unit">{{ w.unit }}</i></span>
                            </div>
                            <div class="mock-gauge">
                              <div class="mock-gauge-fill" :style="{background: themeColor(w)}">
                                <span class="mock-gauge-knob"></span>
                              </div>
                            </div>
                          </div>
                        </template>
                        <!-- 进度条 -->
                        <template v-else-if="w.type === 'progress'">
                          <div class="mock-col">
                            <div class="mock-row">
                              <span class="mock-label">{{ w.title }}</span>
                              <span class="mock-value">68<i class="mock-unit">{{ w.unit }}</i></span>
                            </div>
                            <div class="mock-progress"><i :style="{width: '68%', background: themeColor(w)}"></i></div>
                          </div>
                        </template>
                        <!-- 视频 -->
                        <template v-else-if="w.type === 'video'">
                          <div class="mock-col">
                            <div class="mock-row">
                              <span class="mock-label">{{ w.title }}</span>
                              <span class="mock-live"><i></i>LIVE</span>
                            </div>
                            <div class="mock-video"><span class="mock-play">▶</span></div>
                          </div>
                        </template>
                      </div>
                    </template>
                    <div v-if="dragOverIndex === widgets.length && dragOverIndex > 0" class="drop-line"></div>
                    <div v-if="!widgets.length" class="phone-empty">
                      <p class="pe-title">左侧点击或拖拽组件到此处</p>
                      <p class="pe-sub">实时预览 App 控制页效果</p>
                      <div v-if="!isView" class="pe-chips">
                        <span class="pe-chips-label">从示例开始</span>
                        <span v-for="p in PRESET_OPTIONS" :key="p.value" class="pe-chip" @click="applyPreset(p.value)">
                          {{ p.label }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="phone-home"></div>
                </div>

                <!-- 选中组件的浮动工具条 -->
                <Transition name="tool-fade">
                  <div
                    v-if="selTool.show && !isView"
                    class="sel-toolbar"
                    :style="{top: selTool.top + 'px'}"
                  >
                    <Tooltip title="上移">
                      <button class="st-btn" :disabled="activeIndex === 0" @click="move(activeIndex, -1)">
                        <ArrowUpOutlined />
                      </button>
                    </Tooltip>
                    <Tooltip title="下移">
                      <button class="st-btn" :disabled="activeIndex === widgets.length - 1" @click="move(activeIndex, 1)">
                        <ArrowDownOutlined />
                      </button>
                    </Tooltip>
                    <Tooltip title="复制">
                      <button class="st-btn" @click="duplicateWidget(activeIndex)"><CopyOutlined /></button>
                    </Tooltip>
                    <Tooltip title="删除">
                      <button class="st-btn danger" @click="removeWidget(activeIndex)"><DeleteOutlined /></button>
                    </Tooltip>
                  </div>
                </Transition>
              </div>
            </div>
            <p class="preview-tip">App 端实际效果预览 · 点击卡片选中配置 · 拖拽组件可插入位置</p>
          </template>
          <template v-else>
            <div class="schema-editor">
              <Textarea
                v-model:value="schemaText"
                class="schema-textarea"
                :rows="24"
                placeholder='{"version":1,"pages":[{"name":"控制台","widgets":[]}]}'
              />
              <Space class="schema-actions">
                <Button @click="formatSchema">格式化</Button>
                <Button type="primary" @click="applySchemaText">应用到设计器</Button>
              </Space>
            </div>
          </template>
        </div>

        <!-- 右：属性配置 -->
        <div class="workspace-card workspace-right">
          <template v-if="isView">
            <div class="cfg-title">模板信息</div>
            <div class="cfg-group">
              <div class="cfg-row">
                <span class="cfg-label">模板编码</span>
                <span class="view-text">{{ formView.templateCode || '-' }}</span>
              </div>
              <div class="cfg-row">
                <span class="cfg-label">模板版本</span>
                <span class="view-text">v{{ formView.version ?? '-' }}</span>
              </div>
              <div class="cfg-row">
                <span class="cfg-label">模板状态</span>
                <span class="view-text">{{ formView.statusText }}</span>
              </div>
              <div class="cfg-row">
                <span class="cfg-label">备注</span>
                <span class="view-text">{{ formView.remark || '无' }}</span>
              </div>
            </div>
            <p class="form-help">只读预览 · 点击「设计面板」可进入编辑</p>
          </template>

          <template v-else-if="activeWidget">
            <div class="cfg-title">
              <component :is="typeMeta(activeWidget.type).icon" class="cfg-title-icon" />
              <span>{{ activeWidget.title || typeMeta(activeWidget.type).label }}</span>
              <span class="cfg-title-type">{{ typeMeta(activeWidget.type).label }}</span>
            </div>

            <!-- 基础 -->
            <div class="cfg-group">
              <div class="cfg-group-title">基础</div>
              <div class="cfg-row col">
                <span class="cfg-label">标题</span>
                <Input v-model:value="activeWidget.title" placeholder="显示在 App 上的名称" />
              </div>
              <div class="cfg-row col">
                <span class="cfg-label">布局宽度</span>
                <Segmented
                  v-model:value="activeWidget.span"
                  :options="[{label: '整行', value: 'full'}, {label: '半行', value: 'half'}]"
                />
              </div>
            </div>

            <!-- 数据绑定（属性类组件） -->
            <div v-if="usesProperty.includes(activeWidget.type)" class="cfg-group">
              <div class="cfg-group-title">数据绑定</div>
              <div class="cfg-row col">
                <span class="cfg-label">物模型属性</span>
                <AutoComplete
                  v-model:value="activeWidget.propertyCode"
                  :options="propertyOptions"
                  allow-clear
                  show-search
                  :filter-option="propertyFilter"
                  placeholder="选择或输入属性标识符"
                  @select="onPropertySelect"
                />
                <p v-if="propertyMetaText" class="prop-meta">{{ propertyMetaText }}</p>
                <p v-else-if="!propertyOptions.length" class="form-help">
                  当前产品暂无物模型属性，可手动输入标识符
                </p>
              </div>
              <div v-if="writableTypes.includes(activeWidget.type)" class="cfg-row col">
                <span class="cfg-label">写入服务（可选）</span>
                <Select
                  v-model:value="activeWidget.serviceId"
                  :options="serviceOptions"
                  allow-clear
                  show-search
                  option-filter-prop="label"
                  placeholder="默认调用属性写服务"
                />
                <p class="form-help">不填时 App 端默认调用 setProperty 写属性</p>
              </div>
            </div>

            <!-- 数据绑定（命令按钮） -->
            <div v-if="activeWidget.type === 'button'" class="cfg-group">
              <div class="cfg-group-title">数据绑定</div>
              <div class="cfg-row col">
                <span class="cfg-label">下发服务</span>
                <Select
                  v-model:value="activeWidget.serviceId"
                  :options="serviceOptions"
                  allow-clear
                  show-search
                  option-filter-prop="label"
                  placeholder="选择物模型服务"
                />
                <p class="form-help">点击按钮即向设备下发该服务命令</p>
              </div>
              <div class="cfg-row">
                <span class="cfg-label">执行前确认</span>
                <Switch v-model:checked="activeWidget.confirm" checked-children="开" un-checked-children="关" />
              </div>
            </div>

            <!-- 取值范围 -->
            <div v-if="rangeTypes.includes(activeWidget.type)" class="cfg-group">
              <div class="cfg-group-title">取值范围</div>
              <div class="cfg-grid">
                <div class="cfg-row col">
                  <span class="cfg-label">最小值</span>
                  <InputNumber v-model:value="activeWidget.min" style="width: 100%" />
                </div>
                <div class="cfg-row col">
                  <span class="cfg-label">最大值</span>
                  <InputNumber v-model:value="activeWidget.max" style="width: 100%" />
                </div>
                <div v-if="stepperTypes.includes(activeWidget.type)" class="cfg-row col">
                  <span class="cfg-label">步长</span>
                  <InputNumber v-model:value="activeWidget.step" style="width: 100%" />
                </div>
                <div class="cfg-row col">
                  <span class="cfg-label">单位</span>
                  <Input v-model:value="activeWidget.unit" placeholder="如 %、℃" />
                </div>
              </div>
            </div>

            <!-- 显示样式 -->
            <div v-if="hasStyleConfig" class="cfg-group">
              <div class="cfg-group-title">显示样式</div>
              <div v-if="colorTypes.includes(activeWidget.type)" class="cfg-row col">
                <span class="cfg-label">主题色</span>
                <div class="color-field">
                  <input v-model="activeWidget.color" type="color" class="color-swatch" />
                  <Input v-model:value="activeWidget.color" class="color-input" placeholder="#1677FF" />
                </div>
              </div>
              <div v-if="activeWidget.type === 'chart'" class="cfg-row col">
                <span class="cfg-label">采样点数</span>
                <InputNumber v-model:value="activeWidget.maxPoints" :min="5" :max="60" style="width: 100%" />
                <p class="form-help">App 端每 10s 采样一次属性值并绘制实时曲线</p>
              </div>
              <div v-if="['status', 'switch'].includes(activeWidget.type)" class="cfg-row col">
                <span class="cfg-label">取值映射</span>
                <div class="enum-editor">
                  <div v-for="(row, ri) in activeWidget.enumRows" :key="ri" class="enum-row">
                    <Input v-model:value="row.label" placeholder="显示文本" />
                    <Input v-model:value="row.value" placeholder="原始值" />
                    <input v-if="activeWidget.type === 'status'" v-model="row.color" type="color" class="color-swatch" />
                    <DeleteOutlined class="enum-del" @click="removeEnumRow(ri)" />
                  </div>
                  <Button type="link" size="small" class="enum-add" @click="addEnumRow">+ 添加取值</Button>
                </div>
                <p v-if="activeWidget.type === 'switch'" class="form-help">默认识别 1/0、true/false、OPEN/CLOSE、ON/OFF</p>
              </div>
            </div>
          </template>

          <div v-else class="cfg-empty">
            <div class="cfg-empty-icon"><component :is="typeMeta('status').icon" /></div>
            <p>选中画布或图层中的组件</p>
            <p class="form-help">在此配置标题、物模型绑定与样式</p>
          </div>
        </div>
      </div>
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup name="appPanelTemplateEditor">
  import { computed, nextTick, reactive, ref, watch } from 'vue';
  import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
  import { Button } from '@/components/Button';
  import {
    Alert,
    AutoComplete,
    Empty,
    Input,
    InputNumber,
    Popconfirm,
    Segmented,
    Select,
    Space,
    Switch,
    Textarea,
    Tooltip,
  } from 'ant-design-vue';
  import {
    ArrowDownOutlined,
    ArrowUpOutlined,
    BarChartOutlined,
    ClearOutlined,
    ControlOutlined,
    CopyOutlined,
    DashboardOutlined,
    DeleteOutlined,
    DownOutlined,
    EyeOutlined,
    FieldNumberOutlined,
    LineChartOutlined,
    NumberOutlined,
    OrderedListOutlined,
    PoweroffOutlined,
    RiseOutlined,
    SlidersOutlined,
    TagOutlined,
    ThunderboltOutlined,
    VideoCameraOutlined,
  } from '@ant-design/icons-vue';
  import {
    createAppPanelTemplate,
    getAppPanelTemplatePage,
    updateAppPanelTemplate,
  } from '@/api/device/appPanelTemplate';
  import { getPropertiesList, getServicesList } from '@/api/device/phsyicalModal';
  import { getDeviceProfiles } from '@/api/device/product';
  import { useMessage } from '@/hooks/web/useMessage';

  const emit = defineEmits(['success']);
  const { createMessage } = useMessage();

  const saving = ref(false);
  const sourceMode = ref(false);
  const editingId = ref<number | null>(null);
  const isView = ref(false);

  // ==================== 组件定义（按语义分类，统一线性图标） ====================
  interface WidgetTypeMeta {
    type: string;
    label: string;
    desc: string;
    icon: any;
    cate: string;
  }

  const WIDGET_TYPES: WidgetTypeMeta[] = [
    { type: 'switch', label: '开关组件', desc: '布尔开关，绑定可写属性', icon: PoweroffOutlined, cate: 'control' },
    { type: 'slider', label: '滑条', desc: '数值调节滑条，绑定数值属性', icon: SlidersOutlined, cate: 'control' },
    { type: 'number', label: '步进器', desc: '加减步进调节数值属性', icon: NumberOutlined, cate: 'control' },
    { type: 'button', label: '命令按钮', desc: '点击下发设备服务命令', icon: ThunderboltOutlined, cate: 'control' },
    { type: 'status', label: '状态标签', desc: '只读属性值并映射为彩色标签', icon: TagOutlined, cate: 'display' },
    { type: 'text', label: '数值文本', desc: '只读数值/文本大字展示', icon: FieldNumberOutlined, cate: 'display' },
    { type: 'chart', label: '曲线图表', desc: '属性值实时采样曲线（每 10s 采样）', icon: LineChartOutlined, cate: 'viz' },
    { type: 'gauge', label: '仪表盘', desc: '弧形仪表盘展示数值占比', icon: DashboardOutlined, cate: 'viz' },
    { type: 'progress', label: '进度条', desc: '数值进度条展示', icon: RiseOutlined, cate: 'viz' },
    { type: 'video', label: '视频监控', desc: '当前设备的实时画面（摄像头）', icon: VideoCameraOutlined, cate: 'media' },
  ];

  const widgetCategories = [
    { key: 'control', label: '控制操作', icon: ControlOutlined },
    { key: 'display', label: '属性展示', icon: EyeOutlined },
    { key: 'viz', label: '数据可视化', icon: BarChartOutlined },
    { key: 'media', label: '多媒体', icon: VideoCameraOutlined },
  ];

  const collapsed = reactive<Record<string, boolean>>({});
  const toggleCate = (key: string) => (collapsed[key] = !collapsed[key]);
  const widgetsOf = (cate: string) => WIDGET_TYPES.filter((t) => t.cate === cate);
  const typeMeta = (type: string) => WIDGET_TYPES.find((t) => t.type === type) || { icon: TagOutlined, label: type };

  const usesProperty = ['switch', 'slider', 'number', 'status', 'text', 'chart', 'gauge', 'progress'];
  const writableTypes = ['switch', 'slider', 'number'];
  const rangeTypes = ['slider', 'number', 'chart', 'gauge', 'progress'];
  const stepperTypes = ['slider', 'number'];
  const colorTypes = ['chart', 'gauge', 'progress'];

  const hasStyleConfig = computed(() => {
    if (!activeWidget.value) return false;
    const t = activeWidget.value.type;
    return colorTypes.includes(t) || t === 'chart' || t === 'status' || t === 'switch';
  });

  // ==================== 模板数据 ====================
  let uidSeed = 1;
  const genUid = () => `w${Date.now().toString(36)}${uidSeed++}`;

  const widgets = ref<any[]>([]);
  const activeUid = ref<string | null>(null);
  const activeWidget = computed(() => widgets.value.find((w) => w.uid === activeUid.value));
  const activeIndex = computed(() => widgets.value.findIndex((w) => w.uid === activeUid.value));
  const schemaText = ref('');

  const meta = reactive({
    templateName: '',
    templateCode: '',
    productIdentification: undefined as string | undefined,
    remark: '',
  });
  const metaErrors = reactive({ templateName: '', templateCode: '', productIdentification: '' });

  const STATUS_TEXT: Record<string, string> = { DRAFT: '草稿', PUBLISHED: '已发布', DISABLED: '已停用' };

  // 只读模式下的模板摘要信息
  const formView = reactive({ templateCode: '', version: null as number | null, statusText: '', remark: '' });

  const getTitle = computed(() =>
    isView.value ? '查看面板模板' : editingId.value ? '编辑面板模板' : '新建面板模板',
  );

  // ==================== 打开抽屉 ====================
  const [register, { closeDrawer }] = useDrawerInner((data) => {
    isView.value = !!data?.isView;
    openLogic(data?.record ?? null);
  });

  async function openLogic(record) {
    await loadProducts();
    editingId.value = record?.id ?? null;
    meta.templateName = record?.templateName ?? '';
    meta.templateCode = record?.templateCode ?? '';
    meta.productIdentification = record?.productIdentification || undefined;
    meta.remark = record?.remark ?? '';
    metaErrors.templateName = '';
    metaErrors.templateCode = '';
    metaErrors.productIdentification = '';
    loadThingModel(meta.productIdentification);
    formView.templateCode = record?.templateCode ?? '';
    formView.version = record?.version ?? null;
    formView.statusText = STATUS_TEXT[record?.status] || record?.status || '草稿';
    formView.remark = record?.remark ?? '';
    if (record?.panelSchema) {
      let parsed;
      try {
        parsed = typeof record.panelSchema === 'string' ? JSON.parse(record.panelSchema) : record.panelSchema;
      } catch (e) {
        parsed = null;
      }
      widgets.value = parsed ? buildWidgetsFromParsed(parsed) : [];
    } else {
      widgets.value = [];
    }
    activeUid.value = widgets.value[0]?.uid ?? null;
    sourceMode.value = false;
    await nextTick();
    updateSelTool();
  }

  // ==================== 产品与物模型 ====================
  const productOptions = ref<{ label: string; value: string }[]>([]);
  // 产品 -> 已有模板映射（同一产品仅保留一个模板，联动提示）
  const templateMap = ref<Record<string, { id: number; templateName: string; status: string; version: number }>>({});
  // 物模型属性/服务（随绑定产品联动）
  const propertyDefs = ref<any[]>([]);
  const propertyOptions = ref<{ label: string; value: string }[]>([]);
  const serviceOptions = ref<{ label: string; value: string }[]>([]);

  const propertyMetaText = computed(() => {
    const code = activeWidget.value?.propertyCode;
    if (!code) return '';
    const def = propertyDefs.value.find((d) => d.propertyCode === code);
    if (!def) return '';
    const mode = def.accessMode === 'w' ? '可写' : def.accessMode === 'rw' ? '可读写' : '只读';
    return `${def.propertyName || code} · ${mode}${def.dataType ? ' · ' + def.dataType : ''}${
      def.unit ? ' · ' + def.unit : ''
    }`;
  });

  // 当前绑定产品的已有模板提示（与产品管理逻辑打通）
  const productBindInfo = computed(() => {
    const pid = meta.productIdentification;
    if (!pid) return '';
    const t = templateMap.value[pid];
    if (!t) return '';
    const isSelf = editingId.value && t.id === editingId.value;
    const statusText = STATUS_TEXT[t.status] || t.status;
    return isSelf
      ? `该产品当前绑定模板：${t.templateName}（v${t.version} · ${statusText}）`
      : `该产品已存在模板「${t.templateName}」（v${t.version} · ${statusText}）。同一产品仅保留一个模板，保存后需发布才会对 App 生效`;
  });
  const productBindType = computed(() => {
    const t = meta.productIdentification ? templateMap.value[meta.productIdentification] : null;
    return t && (!editingId.value || t.id !== editingId.value) ? 'warning' : 'info';
  });

  async function loadProducts() {
    try {
      const [profilesRes, templatesRes] = await Promise.all([
        getDeviceProfiles({ pageNum: 1, pageSize: 500 }),
        getAppPanelTemplatePage({ pageNum: 1, pageSize: 100 }),
      ]);
      const rows = profilesRes?.data ?? profilesRes ?? [];
      productOptions.value = (rows || [])
        .filter((r) => r.productIdentification)
        .map((r) => ({ label: `${r.productName}（${r.productIdentification}）`, value: r.productIdentification }));
      const list = templatesRes?.data ?? templatesRes?.rows ?? templatesRes ?? [];
      templateMap.value = {};
      (list || []).forEach((t) => {
        if (t?.productIdentification) templateMap.value[t.productIdentification] = t;
      });
    } catch (e) {
      console.warn('加载产品/模板信息失败', e);
    }
  }

  // 加载当前产品的物模型属性与服务（供下拉绑定）
  async function loadThingModel(pid?: string) {
    propertyDefs.value = [];
    propertyOptions.value = [];
    serviceOptions.value = [];
    if (!pid) return;
    try {
      const [propRes, svcRes] = await Promise.all([
        getPropertiesList({ productIdentification: pid, pageNum: 1, pageSize: 500 }),
        getServicesList({ productIdentification: pid, pageNum: 1, pageSize: 500 }),
      ]);
      const props = propRes?.data ?? propRes?.rows ?? propRes ?? [];
      const svcs = svcRes?.data ?? svcRes?.rows ?? svcRes ?? [];
      propertyDefs.value = Array.isArray(props) ? props : [];
      propertyOptions.value = propertyDefs.value
        .filter((p) => p.propertyCode)
        .map((p) => ({ label: `${p.propertyName || p.propertyCode}（${p.propertyCode}）`, value: p.propertyCode }));
      serviceOptions.value = (Array.isArray(svcs) ? svcs : [])
        .filter((s) => s.serviceCode)
        .map((s) => ({ label: `${s.serviceName || s.serviceCode}（${s.serviceCode}）`, value: s.serviceCode }));
    } catch (e) {
      console.warn('加载物模型失败', e);
    }
  }

  function onProductChange(pid) {
    metaErrors.productIdentification = '';
    loadThingModel(pid);
  }

  const propertyFilter = (input: string, option: any) => {
    const kw = (input || '').toLowerCase();
    return `${option.label}`.toLowerCase().includes(kw);
  };

  // 选择物模型属性后：自动同步单位/量程/步长（装修器关键的“绑定即推导”体验）
  function onPropertySelect(value: string) {
    const w = activeWidget.value;
    if (!w) return;
    const def = propertyDefs.value.find((d) => d.propertyCode === value);
    if (!def) return;
    const num = (v: any) => (v === '' || v === null || v === undefined || isNaN(Number(v)) ? undefined : Number(v));
    if (rangeTypes.includes(w.type)) {
      if (num(def.min) !== undefined) w.min = num(def.min);
      if (num(def.max) !== undefined) w.max = num(def.max);
      if (num(def.step) !== undefined && stepperTypes.includes(w.type)) w.step = num(def.step);
    }
    if (def.unit) w.unit = def.unit;
  }

  // ==================== 组件增删改 ====================
  const defaultEnumRows = {
    switch: () => [
      { label: '开启', value: '1', color: '#1677ff' },
      { label: '关闭', value: '0', color: '#98a2b3' },
    ],
    status: () => [
      { label: '制冷', value: 'COOL', color: '#1677ff' },
      { label: '制热', value: 'HEAT', color: '#fa541c' },
    ],
  };

  function widgetDefaults(type: string): Record<string, any> {
    const defaults: Record<string, any> = {
      switch: { title: '电源开关', enumRows: defaultEnumRows.switch() },
      slider: { title: '亮度', min: 0, max: 100, step: 1, unit: '%' },
      number: { title: '目标温度', min: 16, max: 30, step: 1, unit: '℃' },
      status: { title: '工作模式', enumRows: defaultEnumRows.status() },
      text: { title: '实时功率', unit: 'W' },
      button: { title: '一键执行', serviceId: '', confirm: false },
      chart: { title: '温度趋势', min: 0, max: 60, unit: '℃', color: '#1677ff', maxPoints: 20 },
      gauge: { title: '电量', min: 0, max: 100, unit: '%', color: '#16c2a2' },
      progress: { title: '任务进度', min: 0, max: 100, unit: '%', color: '#1677ff' },
      video: { title: '实时画面' },
    };
    return defaults[type] || {};
  }

  function addWidget(type) {
    insertWidget(type, widgetDefaults(type), widgets.value.length);
  }

  function insertWidget(type, extra: Record<string, any>, index: number) {
    const widget = { uid: genUid(), type, span: 'full', enumRows: [], ...extra };
    widgets.value.splice(index, 0, widget);
    activeUid.value = widget.uid;
    syncSchemaText();
    nextTick(updateSelTool);
  }

  function removeWidget(idx) {
    if (widgets.value[idx]?.uid === activeUid.value) activeUid.value = null;
    widgets.value.splice(idx, 1);
    syncSchemaText();
  }

  function duplicateWidget(idx) {
    const src = widgets.value[idx];
    if (!src) return;
    const copy = JSON.parse(JSON.stringify(src));
    copy.uid = genUid();
    copy.id = undefined;
    copy.title = `${src.title || typeMeta(src.type).label} 副本`;
    widgets.value.splice(idx + 1, 0, copy);
    activeUid.value = copy.uid;
    syncSchemaText();
    nextTick(updateSelTool);
  }

  function move(idx, dir) {
    const target = idx + dir;
    if (target < 0 || target >= widgets.value.length) return;
    [widgets.value[idx], widgets.value[target]] = [widgets.value[target], widgets.value[idx]];
    syncSchemaText();
    nextTick(updateSelTool);
  }

  function clearWidgets() {
    widgets.value = [];
    activeUid.value = null;
    syncSchemaText();
  }

  function addEnumRow() {
    activeWidget.value?.enumRows?.push({ label: '', value: '', color: '#1677ff' });
  }
  function removeEnumRow(ri) {
    activeWidget.value?.enumRows?.splice(ri, 1);
  }

  // ==================== 拖拽：组件库 -> 画布（支持指定插入位置） ====================
  const dragOverIndex = ref(-1);
  const phoneBodyRef = ref<HTMLElement | null>(null);

  function onPaletteDragStart(e: DragEvent, type: string) {
    if (isView.value) return;
    e.dataTransfer?.setData('widget-type', type);
    if (e.dataTransfer) e.dataTransfer.effectAllowed = 'copy';
  }

  function calcDropIndex(e: DragEvent): number {
    const body = phoneBodyRef.value;
    if (!body) return widgets.value.length;
    const cards = Array.from(body.querySelectorAll('.mock-card')) as HTMLElement[];
    for (let i = 0; i < cards.length; i++) {
      const r = cards[i].getBoundingClientRect();
      if (e.clientY < r.top + r.height / 2) return i;
    }
    return cards.length;
  }

  function onCanvasDragOver(e: DragEvent) {
    if (isView.value) return;
    dragOverIndex.value = calcDropIndex(e);
  }

  function onCanvasDragLeave() {
    dragOverIndex.value = -1;
  }

  function onCanvasDrop(e: DragEvent) {
    dragOverIndex.value = -1;
    if (isView.value) return;
    const type = e.dataTransfer?.getData('widget-type');
    if (!type) return;
    insertWidget(type, widgetDefaults(type), calcDropIndex(e));
  }

  // ==================== 画布选中工具条定位 ====================
  const stageRef = ref<HTMLElement | null>(null);
  const selTool = reactive({ show: false, top: 0 });

  function updateSelTool() {
    if (sourceMode.value || !stageRef.value || !activeUid.value) {
      selTool.show = false;
      return;
    }
    const el = stageRef.value.querySelector('.mock-card.selected') as HTMLElement | null;
    if (!el) {
      selTool.show = false;
      return;
    }
    const sr = stageRef.value.getBoundingClientRect();
    const er = el.getBoundingClientRect();
    selTool.show = true;
    selTool.top = er.top - sr.top + er.height / 2;
  }

  watch(activeUid, () => nextTick(updateSelTool));
  watch(
    () => widgets.value.length,
    () => nextTick(updateSelTool),
  );
  watch(sourceMode, (on) => {
    if (on) {
      schemaText.value = buildSchemaPayload();
      selTool.show = false;
    } else {
      nextTick(updateSelTool);
    }
  });

  // ==================== 快速起步示例 ====================
  const PRESET_OPTIONS = [
    { label: '智能插座', value: 'plug' },
    { label: '环境监测', value: 'env' },
    { label: '智能安防', value: 'security' },
    { label: '智能家居', value: 'home' },
    { label: '储能电站', value: 'energy' },
  ];

  const presets: Record<string, () => any[]> = {
    plug: () => [
      { uid: genUid(), type: 'switch', title: '电源开关', span: 'half', propertyCode: 'power', enumRows: [{ label: '开启', value: '1', color: '#1677ff' }, { label: '关闭', value: '0', color: '#98a2b3' }] },
      { uid: genUid(), type: 'status', title: '工作状态', span: 'half', propertyCode: 'work_status', enumRows: [{ label: '运行', value: 'RUNNING', color: '#16c2a2' }, { label: '待机', value: 'STANDBY', color: '#8c8c8c' }, { label: '故障', value: 'FAULT', color: '#f5222d' }] },
      { uid: genUid(), type: 'text', title: '实时功率', span: 'half', propertyCode: 'power_consumption', unit: 'W' },
      { uid: genUid(), type: 'slider', title: '定时电量阈值', span: 'half', propertyCode: 'threshold', min: 0, max: 100, step: 5, unit: '%' },
      { uid: genUid(), type: 'button', title: '重启设备', span: 'full', serviceId: 'reboot', confirm: true },
    ],
    env: () => [
      { uid: genUid(), type: 'chart', title: '温度趋势', span: 'full', propertyCode: 'temperature', min: 0, max: 60, unit: '℃', color: '#1677ff', maxPoints: 20 },
      { uid: genUid(), type: 'gauge', title: '空气湿度', span: 'half', propertyCode: 'humidity', min: 0, max: 100, unit: '%', color: '#16c2a2' },
      { uid: genUid(), type: 'text', title: 'PM2.5', span: 'half', propertyCode: 'pm25', unit: 'μg/m³' },
      { uid: genUid(), type: 'status', title: '空气质量', span: 'full', propertyCode: 'air_quality', enumRows: [{ label: '优', value: 'EXCELLENT', color: '#16c2a2' }, { label: '良', value: 'GOOD', color: '#52c41a' }, { label: '轻度污染', value: 'LIGHT', color: '#faad14' }, { label: '重度污染', value: 'HEAVY', color: '#f5222d' }] },
      { uid: genUid(), type: 'button', title: '一键巡检', span: 'full', serviceId: 'inspect', confirm: true },
    ],
    security: () => [
      { uid: genUid(), type: 'video', title: '门口摄像头', span: 'full' },
      { uid: genUid(), type: 'status', title: '布防状态', span: 'half', propertyCode: 'arm_status', enumRows: [{ label: '已布防', value: 'ARMED', color: '#16c2a2' }, { label: '已撤防', value: 'DISARMED', color: '#8c8c8c' }] },
      { uid: genUid(), type: 'switch', title: '声光报警', span: 'half', propertyCode: 'siren', enumRows: [{ label: '开启', value: '1', color: '#1677ff' }, { label: '关闭', value: '0', color: '#98a2b3' }] },
      { uid: genUid(), type: 'button', title: '一键布防', span: 'half', serviceId: 'arm', confirm: true },
      { uid: genUid(), type: 'button', title: '紧急抓拍', span: 'half', serviceId: 'snapshot', confirm: false },
    ],
    home: () => [
      { uid: genUid(), type: 'switch', title: '客厅灯光', span: 'half', propertyCode: 'light', enumRows: [{ label: '开启', value: '1', color: '#1677ff' }, { label: '关闭', value: '0', color: '#98a2b3' }] },
      { uid: genUid(), type: 'slider', title: '灯光亮度', span: 'half', propertyCode: 'brightness', min: 0, max: 100, step: 5, unit: '%' },
      { uid: genUid(), type: 'gauge', title: '室内温度', span: 'half', propertyCode: 'temperature', min: 10, max: 40, unit: '℃', color: '#fa8c16' },
      { uid: genUid(), type: 'progress', title: '窗帘开度', span: 'half', propertyCode: 'curtain', min: 0, max: 100, unit: '%', color: '#1677ff' },
      { uid: genUid(), type: 'chart', title: '用电功率', span: 'full', propertyCode: 'power', min: 0, max: 3000, unit: 'W', color: '#1677ff', maxPoints: 20 },
    ],
    energy: () => [
      { uid: genUid(), type: 'chart', title: '充放电功率', span: 'full', propertyCode: 'power', min: -100, max: 100, unit: 'kW', color: '#16c2a2', maxPoints: 20 },
      { uid: genUid(), type: 'gauge', title: '电池电量', span: 'half', propertyCode: 'soc', min: 0, max: 100, unit: '%', color: '#16c2a2' },
      { uid: genUid(), type: 'status', title: '运行状态', span: 'half', propertyCode: 'run_status', enumRows: [{ label: '充电', value: 'CHARGING', color: '#16c2a2' }, { label: '放电', value: 'DISCHARGING', color: '#fa8c16' }, { label: '待机', value: 'STANDBY', color: '#8c8c8c' }] },
      { uid: genUid(), type: 'progress', title: '负载率', span: 'half', propertyCode: 'load', min: 0, max: 100, unit: '%', color: '#1677ff' },
      { uid: genUid(), type: 'text', title: '今日发电', span: 'half', propertyCode: 'today_kwh', unit: 'kWh' },
      { uid: genUid(), type: 'button', title: '紧急停机', span: 'full', serviceId: 'emergency_stop', confirm: true },
    ],
  };

  function applyPreset(kind: string) {
    const maker = presets[kind];
    if (!maker) return;
    widgets.value.push(...maker());
    activeUid.value = widgets.value[0]?.uid ?? null;
    syncSchemaText();
    nextTick(updateSelTool);
  }

  // ==================== schema 序列化（结构与 APP 端约定保持不变） ====================
  function buildWidgetsFromParsed(parsed): any[] {
    const rawList = parsed?.pages?.[0]?.widgets ?? [];
    return rawList.map((raw, i) => {
      const cfg = raw.config || {};
      return {
        uid: genUid(),
        id: raw.id || `${raw.type}_${i}`,
        type: raw.type,
        title: raw.title ?? '',
        span: raw.span === 'half' ? 'half' : 'full',
        propertyCode: raw.propertyCode,
        serviceId: raw.serviceId,
        config: cfg,
        enumRows: (Array.isArray(cfg.options) ? cfg.options : []).map((o) => ({
          label: o.label ?? '',
          value: o.value ?? '',
          color: o.color || '#1677ff',
        })),
        confirm: cfg.confirm === true,
        min: cfg.min,
        max: cfg.max,
        step: cfg.step,
        unit: cfg.unit,
        color: cfg.color,
        maxPoints: cfg.maxPoints,
      };
    });
  }

  function buildSchemaPayload() {
    const normalized = widgets.value.map((w, i) => ({
      id: w.id || `${w.type}_${i}`,
      type: w.type,
      title: w.title,
      span: w.span,
      ...(w.propertyCode ? { propertyCode: w.propertyCode } : {}),
      ...(w.serviceId ? { serviceId: w.serviceId } : {}),
      config: {
        ...(w.min !== undefined ? { min: w.min } : {}),
        ...(w.max !== undefined ? { max: w.max } : {}),
        ...(w.step !== undefined ? { step: w.step } : {}),
        ...(w.unit ? { unit: w.unit } : {}),
        ...(w.color ? { color: w.color } : {}),
        ...(w.maxPoints ? { maxPoints: w.maxPoints } : {}),
        ...(['switch', 'status'].includes(w.type)
          ? {
              options: (w.enumRows || [])
                .filter((r) => r.label || r.value)
                .map((r) => ({ label: r.label, value: r.value, ...(r.color ? { color: r.color } : {}) })),
            }
          : {}),
        ...(w.type === 'button' ? { confirm: !!w.confirm } : {}),
      },
    }));
    return JSON.stringify({ version: 1, pages: [{ name: '控制台', layout: 'grid', widgets: normalized }] }, null, 2);
  }

  function syncSchemaText() {
    if (!sourceMode.value) return;
    schemaText.value = buildSchemaPayload();
  }

  function formatSchema() {
    try {
      schemaText.value = JSON.stringify(JSON.parse(schemaText.value || '{}'), null, 2);
    } catch (e: any) {
      createMessage.error('JSON 格式错误：' + e.message);
    }
  }

  function applySchemaText() {
    try {
      const parsed = JSON.parse(schemaText.value);
      widgets.value = buildWidgetsFromParsed(parsed);
      createMessage.success(`已应用，共 ${widgets.value.length} 个组件`);
      sourceMode.value = false;
    } catch (e: any) {
      createMessage.error('JSON 解析失败：' + e.message);
    }
  }

  // ==================== 预览渲染辅助 ====================
  const optionLabel = (w) => (w.enumRows || [])[0]?.label || '--';
  const themeColor = (w) => w.color || '#1677ff';

  function pillStyle(w) {
    const color = (w.enumRows || [])[0]?.color || '#1677ff';
    return { color, background: `${color}1f`, borderColor: `${color}45` };
  }

  function sliderStyle(w) {
    const c = themeColor(w);
    return { width: '42%', background: `linear-gradient(90deg, ${c}99, ${c})` };
  }

  function btnStyle(w) {
    const c = w.color || '#1677ff';
    return { background: `linear-gradient(135deg, ${c}d9, ${c})` };
  }

  // ==================== 保存 ====================
  function validateMeta(): boolean {
    metaErrors.templateName = meta.templateName.trim() ? '' : '请输入模板名称';
    metaErrors.templateCode = meta.templateCode.trim() ? '' : '请输入模板编码';
    metaErrors.productIdentification = meta.productIdentification ? '' : '请选择绑定产品';
    const firstError = [metaErrors.templateName, metaErrors.templateCode, metaErrors.productIdentification].find(Boolean);
    if (firstError) {
      createMessage.warning(firstError);
      return false;
    }
    return true;
  }

  async function handleSave() {
    if (!validateMeta()) return;
    saving.value = true;
    try {
      const payload = {
        id: editingId.value ?? undefined,
        templateCode: meta.templateCode.trim(),
        templateName: meta.templateName.trim(),
        productIdentification: meta.productIdentification || '',
        remark: meta.remark,
        panelSchema: buildSchemaPayload(),
      };
      if (editingId.value) {
        await updateAppPanelTemplate(payload);
        createMessage.success('保存成功');
      } else {
        await createAppPanelTemplate(payload);
        createMessage.success('模板已创建为草稿，发布后对 App 生效');
      }
      closeDrawer();
      emit('success');
    } catch (e: any) {
      createMessage.error(e?.message || '保存失败');
    } finally {
      saving.value = false;
    }
  }

  function handleClose() {
    closeDrawer();
  }
</script>

<style lang="less" scoped>
  @panel-border: #edf0f5;
  @panel-shadow: 0 1px 3px rgba(31, 45, 74, 0.05);
  @text-main: #1d2939;
  @text-sub: #667085;
  @text-faint: #98a2b3;
  @brand: #1677ff;

  .panel-editor {
    display: flex;
    flex-direction: column;
    gap: 12px;
    height: calc(100vh - 112px);
    min-height: 560px;
  }

  // ==================== 顶部元信息条 ====================
  .meta-card {
    display: flex;
    align-items: flex-end;
    gap: 16px;
    flex-wrap: wrap;
    background: #fff;
    border: 1px solid @panel-border;
    border-radius: 12px;
    box-shadow: @panel-shadow;
    padding: 12px 16px;
    flex-shrink: 0;
  }

  .meta-fields {
    display: flex;
    align-items: flex-end;
    gap: 12px;
    flex-wrap: wrap;
    flex: 1;
    min-width: 0;
  }

  .meta-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    width: 200px;

    &.meta-field-product {
      width: 250px;
    }

    &.meta-field-grow {
      flex: 1;
      min-width: 150px;
    }
  }

  .meta-label {
    font-size: 12px;
    color: @text-sub;

    .req {
      color: #f5222d;
      font-style: normal;
      margin-left: 2px;
    }
  }

  .has-error {
    border-color: #f5222d !important;
  }

  .meta-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .source-toggle {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-right: 8px;

    .source-toggle-label {
      font-size: 12px;
      color: @text-sub;
    }
  }

  .meta-alert {
    border-radius: 8px;
    flex-shrink: 0;
  }

  // ==================== 工作区三栏 ====================
  .panel-workspace {
    display: grid;
    grid-template-columns: 292px minmax(0, 1fr) 336px;
    gap: 12px;
    flex: 1;
    min-height: 0;
  }

  .workspace-card {
    background: #fff;
    border: 1px solid @panel-border;
    border-radius: 12px;
    box-shadow: @panel-shadow;
    padding: 12px;
    overflow-y: auto;
    min-height: 0;
  }

  // ==================== 左：组件库 ====================
  .workspace-left {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .cate-section + .cate-section {
    margin-top: 4px;
  }

  .cate-header {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 7px 8px;
    border-radius: 8px;
    cursor: pointer;
    user-select: none;
    transition: background 0.15s;

    &:hover {
      background: #f7f9fc;
    }

    &.static {
      cursor: default;

      &:hover {
        background: transparent;
      }
    }

    .cate-icon {
      font-size: 14px;
      color: @text-faint;
    }

    .cate-title {
      flex: 1;
      font-size: 13px;
      font-weight: 600;
      color: @text-main;
    }

    .cate-arrow {
      font-size: 10px;
      color: @text-faint;
      transition: transform 0.2s;

      &.collapsed {
        transform: rotate(-90deg);
      }
    }
  }

  .palette-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 4px;
    padding: 2px 4px 8px;
    overflow: hidden;
  }

  .palette-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
    padding: 10px 2px 8px;
    border-radius: 10px;
    cursor: grab;
    transition: all 0.15s;

    &:hover {
      background: #f0f6ff;

      .palette-icon,
      .palette-label {
        color: @brand;
      }
    }

    &:active {
      cursor: grabbing;
    }

    .palette-icon {
      font-size: 19px;
      color: #4b5563;
      transition: color 0.15s;
    }

    .palette-label {
      font-size: 12px;
      color: #475467;
      white-space: nowrap;
      transition: color 0.15s;
    }

    &.disabled {
      cursor: not-allowed;
      opacity: 0.5;

      &:hover {
        background: transparent;

        .palette-icon,
        .palette-label {
          color: inherit;
        }
      }
    }
  }

  .cate-fold-enter-active,
  .cate-fold-leave-active {
    transition: all 0.18s ease;
  }

  .cate-fold-enter-from,
  .cate-fold-leave-to {
    opacity: 0;
  }

  // ==================== 左：组件图层 ====================
  .layer-section {
    margin-top: 8px;
    border-top: 1px solid @panel-border;
    padding-top: 6px;
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 120px;
  }

  .layer-clear {
    font-size: 14px;
    color: @text-faint;
    padding: 4px;
    border-radius: 6px;
    transition: all 0.15s;

    &:hover {
      color: #f5222d;
      background: #fff1f0;
    }
  }

  .layer-body {
    flex: 1;
    overflow-y: auto;
    padding: 4px 4px 2px;
  }

  .layer-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .layer-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 9px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 13px;
    color: @text-main;
    transition: all 0.15s;

    &:hover {
      background: #f7f9fc;

      .layer-actions {
        opacity: 1;
      }
    }

    &.active {
      background: #f0f6ff;
      color: @brand;

      .layer-icon,
      .layer-index {
        color: @brand;
      }
    }

    .layer-index {
      font-size: 11px;
      color: @text-faint;
      width: 14px;
      text-align: center;
      flex-shrink: 0;
    }

    .layer-icon {
      font-size: 13px;
      color: @text-faint;
      flex-shrink: 0;
    }

    .layer-title {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .layer-span {
      font-size: 10px;
      color: @text-faint;
      border: 1px solid @panel-border;
      border-radius: 4px;
      padding: 0 3px;
      flex-shrink: 0;
    }

    .layer-actions {
      display: flex;
      gap: 7px;
      opacity: 0;
      transition: opacity 0.15s;

      .op {
        font-size: 12px;
        color: @text-faint;

        &:hover {
          color: @brand;
        }

        &.danger:hover {
          color: #f5222d;
        }
      }
    }
  }

  .widget-list-enter-active,
  .widget-list-leave-active,
  .widget-list-move {
    transition: all 0.25s ease;
  }

  .widget-list-enter-from,
  .widget-list-leave-to {
    opacity: 0;
    transform: translateY(-6px);
  }

  // ==================== 中：画布 ====================
  .workspace-center {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 380px;
    min-height: 0;
    gap: 6px;

    .preview-tip {
      color: @text-faint;
      font-size: 12px;
      flex-shrink: 0;
    }
  }

  .canvas-scroll {
    flex: 1;
    width: 100%;
    min-height: 0;
    overflow: auto;
    border-radius: 12px;
    background-color: #f2f4f8;
    background-image: radial-gradient(#e3e7ee 1px, transparent 1px);
    background-size: 18px 18px;
  }

  .canvas-stage {
    position: relative;
    display: flex;
    justify-content: center;
    padding: 28px 100px 36px;
    min-width: 100%;
    min-height: 100%;
    box-sizing: border-box;
  }

  .float-label {
    position: absolute;
    right: calc(50% + 186px);
    display: flex;
    align-items: center;
    gap: 6px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(31, 45, 74, 0.1);
    padding: 5px 10px;
    font-size: 12px;
    color: @text-main;
    white-space: nowrap;
    z-index: 5;

    .float-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: @brand;

      &.page {
        background: #16c2a2;
      }
    }
  }

  // ==================== 手机机身 ====================
  .phone-frame {
    width: 346px;
    height: 668px;
    flex-shrink: 0;
    background: linear-gradient(180deg, #f2f5fb 0%, #f8fafd 60%);
    border: 10px solid #0b0e16;
    border-radius: 46px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 24px 56px rgba(16, 19, 26, 0.2);
    display: flex;
    flex-direction: column;
    box-sizing: content-box;
  }

  .phone-island {
    position: absolute;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    width: 84px;
    height: 24px;
    border-radius: 14px;
    background: #0b0e16;
    z-index: 3;
  }

  .phone-status {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 22px 2px;
    color: @text-main;

    .ps-time {
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.3px;
    }

    .ps-icons {
      display: flex;
      align-items: center;
      gap: 5px;
    }
  }

  .phone-navbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px 10px;

    .phone-back {
      font-size: 20px;
      line-height: 1;
      color: @text-main;
    }

    .phone-title {
      flex: 1;
      text-align: center;
      font-size: 14px;
      font-weight: 600;
      color: @text-main;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .phone-online {
      font-size: 10px;
      color: #16a377;
      background: rgba(22, 163, 119, 0.12);
      border-radius: 99px;
      padding: 1px 8px;
    }
  }

  .phone-body {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: 6px 12px 14px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-content: flex-start;
  }

  .phone-home {
    width: 110px;
    height: 4px;
    border-radius: 99px;
    background: rgba(11, 14, 22, 0.35);
    margin: 6px auto 8px;
    flex-shrink: 0;
  }

  .drop-line {
    width: 100%;
    height: 3px;
    border-radius: 99px;
    background: @brand;
    box-shadow: 0 0 0 4px rgba(22, 119, 255, 0.12);
    margin: -2px 0;
  }

  .phone-empty {
    width: 100%;
    text-align: center;
    margin-top: 130px;

    .pe-title {
      font-size: 13px;
      color: @text-sub;
      margin-bottom: 2px;
    }

    .pe-sub {
      font-size: 12px;
      color: @text-faint;
      margin-bottom: 16px;
    }

    .pe-chips {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      flex-wrap: wrap;
      padding: 0 10px;

      .pe-chips-label {
        font-size: 11px;
        color: @text-faint;
      }

      .pe-chip {
        font-size: 12px;
        color: @text-main;
        background: #fff;
        border: 1px solid @panel-border;
        border-radius: 99px;
        padding: 4px 12px;
        cursor: pointer;
        transition: all 0.15s;

        &:hover {
          color: @brand;
          border-color: @brand;
          background: #f0f6ff;
        }
      }
    }
  }

  // ==================== 手机内组件卡片 ====================
  .mock-card {
    width: 100%;
    background: #fff;
    border-radius: 14px;
    padding: 12px 14px;
    box-shadow: 0 1px 4px rgba(31, 45, 74, 0.06);
    cursor: pointer;
    transition: box-shadow 0.2s, outline-color 0.2s;
    outline: 1px solid transparent;

    &:hover {
      outline-color: rgba(22, 119, 255, 0.35);
    }

    &.half {
      width: calc(50% - 4px);
    }

    &.selected {
      outline: 2px solid @brand;
      box-shadow: 0 4px 14px rgba(22, 119, 255, 0.18);
    }
  }

  .mock-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .mock-col {
    display: flex;
    flex-direction: column;
    gap: 8px;

    &.center {
      align-items: center;
    }
  }

  .mock-label {
    font-size: 12px;
    font-weight: 500;
    color: @text-sub;
  }

  .mock-value {
    font-size: 16px;
    font-weight: 700;
    color: @text-main;
    font-variant-numeric: tabular-nums;

    .mock-unit {
      font-style: normal;
      font-size: 11px;
      font-weight: 400;
      color: @text-faint;
      margin-left: 2px;
    }
  }

  .mock-big {
    font-size: 26px;
    font-weight: 700;
    color: @text-main;
    line-height: 1.2;
    font-variant-numeric: tabular-nums;

    .mock-unit {
      font-style: normal;
      font-size: 12px;
      font-weight: 400;
      color: @text-faint;
      margin-left: 3px;
    }
  }

  .mock-switch {
    width: 44px;
    height: 24px;
    border-radius: 99px;
    background: #d8dee9;
    position: relative;

    i {
      position: absolute;
      right: 2px;
      top: 2px;
      width: 20px;
      height: 20px;
      background: #fff;
      border-radius: 50%;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }

    &.on {
      background: linear-gradient(135deg, #4096ff, #1677ff);
    }
  }

  .mock-slider {
    height: 6px;
    border-radius: 3px;
    background: #edeff5;
    overflow: visible;
    position: relative;

    i {
      display: block;
      height: 100%;
      border-radius: 3px;
      position: relative;

      &::after {
        content: '';
        position: absolute;
        right: -5px;
        top: 50%;
        transform: translateY(-50%);
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #fff;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
      }
    }
  }

  .mock-stepper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #f2f4f8;
    border-radius: 10px;
    padding: 4px 12px;
    font-weight: 700;
    color: @text-main;

    b {
      color: @brand;
      font-weight: 700;
    }
  }

  .mock-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    font-weight: 500;
    border-radius: 99px;
    padding: 3px 10px;
    border: 1px solid transparent;

    i {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: currentColor;
    }
  }

  .mock-btn {
    background: linear-gradient(135deg, #4096ff, #1677ff);
    color: #fff;
    border-radius: 12px;
    padding: 9px 28px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
  }

  .mock-video {
    height: 104px;
    border-radius: 10px;
    background: linear-gradient(160deg, #1f2733 0%, #0b0e16 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;

    .mock-play {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.16);
      color: #fff;
      font-size: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding-left: 3px;
    }
  }

  .mock-live {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 9px;
    font-weight: 700;
    color: #f5222d;
    letter-spacing: 0.5px;

    i {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #f5222d;
      animation: live-pulse 1.4s ease-in-out infinite;
    }
  }

  @keyframes live-pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.25;
    }
  }

  .mock-chart {
    width: 100%;
    height: 60px;
    display: block;
  }

  .mock-gauge {
    position: relative;
    width: 100%;
    height: 50px;
    border-radius: 50px 50px 0 0;
    background: #edeff5;
    overflow: hidden;
    margin-top: 2px;

    .mock-gauge-fill {
      position: absolute;
      left: 0;
      bottom: 0;
      width: 68%;
      height: 100%;
      border-radius: 50px 50px 0 0;
      display: flex;
      align-items: flex-end;
      justify-content: flex-end;

      .mock-gauge-knob {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #fff;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
        margin: -6px -4px 6px 0;
      }
    }
  }

  .mock-progress {
    height: 8px;
    border-radius: 5px;
    background: #edeff5;
    overflow: hidden;

    i {
      display: block;
      height: 100%;
      border-radius: 5px;
    }
  }

  // ==================== 选中浮动工具条 ====================
  .sel-toolbar {
    position: absolute;
    right: calc(50% - 231px);
    transform: translateY(-50%);
    display: flex;
    flex-direction: column;
    gap: 2px;
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 6px 20px rgba(31, 45, 74, 0.18);
    padding: 4px;
    z-index: 10;

    .st-btn {
      width: 28px;
      height: 28px;
      border: none;
      border-radius: 7px;
      background: transparent;
      color: #475467;
      font-size: 13px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s;

      &:hover:not(:disabled) {
        background: #f0f6ff;
        color: @brand;
      }

      &.danger:hover {
        background: #fff1f0;
        color: #f5222d;
      }

      &:disabled {
        opacity: 0.3;
        cursor: not-allowed;
      }
    }
  }

  .tool-fade-enter-active,
  .tool-fade-leave-active {
    transition: opacity 0.15s, transform 0.15s;
  }

  .tool-fade-enter-from,
  .tool-fade-leave-to {
    opacity: 0;
    transform: translateY(-50%) scale(0.92);
  }

  // ==================== JSON 源码 ====================
  .schema-editor {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 4px 2px 0;
  }

  .schema-textarea {
    flex: 1;
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 12px;
    resize: none;
  }

  .schema-actions {
    margin-top: 8px;
  }

  // ==================== 右：配置面板 ====================
  .workspace-right {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .cfg-title {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 14px;
    font-weight: 600;
    color: @text-main;
    padding-bottom: 4px;

    .cfg-title-icon {
      color: @brand;
      font-size: 15px;
    }

    .cfg-title-type {
      margin-left: auto;
      font-size: 11px;
      font-weight: 500;
      color: @brand;
      background: #f0f6ff;
      border-radius: 99px;
      padding: 2px 9px;
    }
  }

  .cfg-group {
    border: 1px solid @panel-border;
    border-radius: 10px;
    padding: 10px 12px 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;

    .cfg-group-title {
      font-size: 12px;
      font-weight: 600;
      color: @text-faint;
      letter-spacing: 0.5px;
    }
  }

  .cfg-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;

    &.col {
      flex-direction: column;
      align-items: stretch;
      gap: 6px;
    }
  }

  .cfg-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .cfg-label {
    font-size: 12px;
    color: @text-sub;
    flex-shrink: 0;
  }

  .view-text {
    font-size: 13px;
    color: @text-main;
    word-break: break-all;
  }

  .form-help {
    margin: 0;
    font-size: 11px;
    color: @text-faint;
    line-height: 1.5;
  }

  .prop-meta {
    margin: 0;
    font-size: 11px;
    color: @brand;
    background: #f0f6ff;
    border-radius: 6px;
    padding: 3px 8px;
  }

  .color-field {
    display: flex;
    align-items: center;
    gap: 8px;

    .color-input {
      flex: 1;
    }
  }

  .color-swatch {
    width: 30px;
    height: 30px;
    padding: 0;
    border: 1px solid @panel-border;
    border-radius: 6px;
    background: transparent;
    cursor: pointer;
    flex-shrink: 0;

    &::-webkit-color-swatch-wrapper {
      padding: 2px;
    }

    &::-webkit-color-swatch {
      border: none;
      border-radius: 4px;
    }
  }

  .enum-editor {
    display: flex;
    flex-direction: column;
    gap: 6px;

    .enum-row {
      display: flex;
      align-items: center;
      gap: 6px;

      .ant-input {
        flex: 1;
        min-width: 0;
      }

      .color-swatch {
        width: 28px;
        height: 28px;
      }

      .enum-del {
        color: @text-faint;
        cursor: pointer;
        flex-shrink: 0;

        &:hover {
          color: #f5222d;
        }
      }
    }

    .enum-add {
      align-self: flex-start;
      padding-left: 0;
    }
  }

  .cfg-empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 4px;
    padding: 40px 0;
    text-align: center;

    p {
      margin: 0;
      font-size: 13px;
      color: @text-sub;
    }

    .cfg-empty-icon {
      width: 52px;
      height: 52px;
      border-radius: 14px;
      background: #f0f6ff;
      color: @brand;
      font-size: 22px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 8px;
    }
  }
</style>
