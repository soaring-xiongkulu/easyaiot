<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="registerDrawer"
    @open-change="handleOpenChange"
    width="1320"
    placement="right"
    :showFooter="true"
    :showOkBtn="false"
    :showCancelBtn="false"
    destroy-on-close
    root-class-name="edge-setup-guide-drawer"
  >
    <template #title>
      <div class="setup-drawer-header">
        <div class="setup-drawer-header__main">
          <div class="setup-drawer-header__icon">
            <Icon icon="mdi:server-network" :size="22" />
          </div>
          <div>
            <BasicTitle span class="setup-drawer-header__title">边缘节点接入</BasicTitle>
            <div class="setup-drawer-header__meta">
              {{ headerMeta }}
            </div>
          </div>
        </div>
        <div v-if="focusNode" class="setup-drawer-header__tags">
          <a-tag :color="statusColor(focusNode.status)">{{ statusText(focusNode.status) }}</a-tag>
          <a-tag :color="focusNode.cephMountReady ? 'success' : 'warning'">
            NFS {{ focusNode.cephMountReady ? '就绪' : '未就绪' }}
          </a-tag>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleClose">
          {{ activeStepKey === 'finish' && verifiedOnline ? '完成' : '关闭' }}
        </Button>
        <div class="footer-nav">
          <Button v-if="!isFirstStep" @click="handlePrev">上一步</Button>
          <Button v-if="!isLastStep" type="primary" @click="handleNext">下一步</Button>
          <Button
            v-else
            type="primary"
            @click="emitSuccessAndClose"
          >
            完成
          </Button>
        </div>
      </div>
    </template>

    <div class="setup-drawer-content">
      <div class="setup-hero">
        <div class="setup-hero__copy">
          <div class="setup-hero__eyebrow">EasyAIoT 无限联邦边缘集群模式</div>
          <div class="setup-hero__title">一行命令，把普通开发板直接智能化</div>
          <div class="setup-hero__desc">
            内存占用约 512MB，Ceph 边缘 0 硬盘占用；可随点位铺开算力部署。写入控制面地址并启动后，节点自动登记、订阅任务，告警与事件汇聚上云。
            按下方步骤完成安装、配置、启动与验收。
          </div>
          <div class="setup-hero__tags">
            <span v-for="tag in heroTags" :key="tag" class="setup-hero__tag">{{ tag }}</span>
          </div>
        </div>
        <div class="setup-hero__visual">
          <img :src="NODE_IMAGE" alt="" />
        </div>
      </div>

      <div class="setup-steps-card">
        <Steps
          class="setup-steps"
          :current="currentStep"
          :items="stepItems"
          @change="handleStepChange"
        />
      </div>

      <div class="setup-content-card">
        <!-- 1 了解 -->
        <div v-show="activeStepKey === 'overview'" class="step-panel">
          <Alert
            type="info"
            show-icon
            message="边缘节点通过 CLI 自助登记，接入无限联邦边缘集群。与「工作节点 → SSH 部署监测代理」为不同接入方式，请勿混用。"
          />
          <div class="journey-grid">
            <div v-for="item in journeyCards" :key="item.title" class="journey-card">
              <div class="journey-card__index">{{ item.index }}</div>
              <div class="journey-card__title">{{ item.title }}</div>
              <div class="journey-card__desc">{{ item.desc }}</div>
            </div>
          </div>
          <CollapseContainer title="接入后能力" :can-expan="false">
            <ul class="bullet-list">
              <li>约 512MB 内存即可加入联邦集群，开发板 / 工控机随装随扩</li>
              <li>Ceph 边缘 0 硬盘占用：告警图写共享路径，不落本地业务盘</li>
              <li>节点登记至边缘管理表（<code>edge_node</code>），由中心统一调度</li>
              <li>通过 MQTT 接收算法启停指令，在本地执行推理并将告警汇聚上云</li>
              <li>AI 预览推流到中心选定的 SRS（边缘不装流媒体）；多节点时在指引中手动指定</li>
            </ul>
          </CollapseContainer>
        </div>

        <!-- 2 中心准备 -->
        <div v-show="activeStepKey === 'prepare'" class="step-panel">
          <Alert
            type="warning"
            show-icon
            message="请先确认中心侧服务就绪，否则节点登记或调度会失败。"
          />
          <CollapseContainer title="中心侧检查项" :can-expan="false">
            <div class="checklist">
              <div v-for="item in prepareChecklist" :key="item.key" class="checklist__item">
                <CheckCircleFilled v-if="item.ok === true" class="ok" />
                <CloseCircleFilled v-else-if="item.ok === false" class="bad" />
                <Icon v-else icon="ant-design:info-circle-filled" :size="14" color="#faad14" />
                <div>
                  <div class="checklist__label">{{ item.label }}</div>
                  <div class="checklist__hint">{{ item.hint }}</div>
                </div>
              </div>
            </div>
          </CollapseContainer>
          <CollapseContainer title="Join Token" :can-expan="false">
            <p class="form-hint">
              生产环境建议在控制面配置 <code>easyaiot.edge.join-token</code>，边缘侧执行
              <code>python -m edge config set-join-token &lt;token&gt;</code>。
              测试环境可开启 <code>easyaiot.edge.allow-open-enroll=true</code>，此时仅需控制面地址。
            </p>
          </CollapseContainer>
        </div>

        <!-- 3 安装 -->
        <div v-show="activeStepKey === 'install'" class="step-panel">
          <Alert type="info" show-icon message="在边缘设备终端进入仓库 EDGE 目录，安装 Python 依赖。" />
          <CollapseContainer title="安装依赖" :can-expan="false">
            <div class="script-toolbar">
              <Button size="small" preIcon="ant-design:copy-outlined" @click="copyText(installCmd, '安装命令已复制')">
                复制命令
              </Button>
            </div>
            <pre class="script-block">{{ installCmd }}</pre>
          </CollapseContainer>
        </div>

        <!-- 4 配置 -->
        <div v-show="activeStepKey === 'config'" class="step-panel">
          <Alert
            :type="isLocalControlPlaneUrl(controlPlaneUrl) ? 'warning' : 'info'"
            show-icon
            :message="
              isLocalControlPlaneUrl(controlPlaneUrl)
                ? '当前为 localhost，边缘设备无法通过回环地址访问中心，请改为局域网可达 IP（端口 48080）。'
                : '请确认控制面地址可达；多媒体节点时请在下方下拉选定本台边缘要推流的 SRS。'
            "
          />
          <CollapseContainer title="控制面地址" :can-expan="false">
            <div class="url-row">
              <a-input
                v-model:value="controlPlaneUrl"
                placeholder="http://<控制面主机>:48080"
                allow-clear
              />
              <Button @click="refreshControlPlaneUrl" :loading="resolvingUrl">重新探测</Button>
              <Button
                type="primary"
                preIcon="ant-design:copy-outlined"
                @click="copyText(controlPlaneUrl, '控制面地址已复制')"
              >
                复制
              </Button>
            </div>
            <p class="form-hint">
              对应环境变量 <code>EDGE_NODE_URL</code>。不要附加
              <code>/admin-api/node/agent</code> 等路径；Gateway 默认端口
              <code>48080</code>。
            </p>
            <div class="join-token-block">
              <div class="join-token-block__label">Join Token（生产可选）</div>
              <a-input
                v-model:value="joinToken"
                placeholder="与控制面 easyaiot.edge.join-token 一致"
                allow-clear
              />
            </div>
          </CollapseContainer>

          <CollapseContainer title="SRS 流媒体节点（AI 预览推流）" :can-expan="false">
            <Alert
              v-if="!mediaNodes.length && !loadingMedia"
              type="warning"
              show-icon
              style="margin-bottom: 12px"
              message="暂无在线直播/推流节点。请先在「节点管理」勾选直播接入或推流转发并部署 SRS，或确认节点在线后再刷新。"
            />
            <div class="url-row">
              <a-select
                v-model:value="selectedSrsNodeId"
                class="srs-select"
                allow-clear
                show-search
                option-filter-prop="label"
                placeholder="选择可用的 SRS 节点（已勾选直播接入或推流转发）"
                :options="srsSelectOptions"
                :loading="loadingMedia"
              />
              <Button @click="loadMediaNodes" :loading="loadingMedia">刷新节点</Button>
            </div>
            <p class="form-hint">
              边缘不在本机安装 SRS；从中心媒体节点中<strong>手动指定</strong>本台要推流的目标。
              选定后下方命令会自动拼接 <code>set-srs</code>，写入
              <code>EDGE_SRS_HOST</code> 等环境变量。
            </p>
            <div v-if="selectedSrsSummary" class="srs-summary">
              <div class="srs-summary__row">
                <span class="srs-summary__label">节点</span>
                <span>{{ selectedSrsSummary.name }} · {{ selectedSrsSummary.host }} · {{ selectedSrsSummary.role }}</span>
              </div>
              <div class="srs-summary__row">
                <span class="srs-summary__label">推流</span>
                <code>{{ selectedSrsSummary.rtmpBase }}</code>
              </div>
              <div class="srs-summary__row">
                <span class="srs-summary__label">播放</span>
                <code>{{ selectedSrsSummary.httpBase }}</code>
              </div>
            </div>
          </CollapseContainer>

          <CollapseContainer title="一键配置命令（自动拼接）" :can-expan="false">
            <div class="script-toolbar">
              <Button
                size="small"
                type="primary"
                preIcon="ant-design:copy-outlined"
                @click="copyText(configBundleCmd, '配置命令已复制')"
              >
                复制全部配置命令
              </Button>
              <Button size="small" preIcon="ant-design:copy-outlined" @click="copyText(setNodeCmd, 'set-node 已复制')">
                仅 set-node
              </Button>
              <Button
                size="small"
                preIcon="ant-design:copy-outlined"
                :disabled="!setSrsCmd"
                @click="copyText(setSrsCmd, 'set-srs 已复制')"
              >
                仅 set-srs
              </Button>
              <Button
                v-if="joinToken.trim()"
                size="small"
                preIcon="ant-design:copy-outlined"
                @click="copyText(setJoinTokenCmd, 'Join Token 命令已复制')"
              >
                仅 set-join-token
              </Button>
            </div>
            <pre class="script-block">{{ configBundleCmd }}</pre>
          </CollapseContainer>
        </div>

        <!-- 5 运行 -->
        <div v-show="activeStepKey === 'run'" class="step-panel">
          <Alert
            type="info"
            show-icon
            message="先常驻 edge run 订阅 MQTT；再用独立命令 task start/stop 完成负载启停（不在本 Tab 内建任务下发 UI）。"
          />
          <CollapseContainer title="① 启动 Agent（常驻订阅）" :can-expan="false">
            <div class="script-toolbar">
              <Button size="small" preIcon="ant-design:copy-outlined" @click="copyText(runCmd, '启动命令已复制')">
                复制
              </Button>
            </div>
            <pre class="script-block">{{ runCmd }}</pre>
          </CollapseContainer>
          <CollapseContainer title="② 命令下发负载（另一终端）" :can-expan="false">
            <Alert
              type="warning"
              show-icon
              style="margin-bottom: 12px"
              message="与「算法任务」Tab 互不影响。targetNodeId 为本机 enroll 的 compute 节点 ID；taskId 写入进程 TASK_ID。"
            />
            <div class="url-row" style="margin-bottom: 12px">
              <a-input-number
                v-model:value="guideTaskId"
                :min="1"
                :precision="0"
                placeholder="taskId"
                style="width: 160px"
              />
              <a-select
                v-model:value="guideTaskType"
                style="width: 140px"
                :options="taskTypeOptions"
              />
              <Button
                size="small"
                type="primary"
                preIcon="ant-design:copy-outlined"
                @click="copyText(taskStartCmd, 'task start 已复制')"
              >
                复制 start
              </Button>
              <Button
                size="small"
                preIcon="ant-design:copy-outlined"
                @click="copyText(taskStopCmd, 'task stop 已复制')"
              >
                复制 stop
              </Button>
            </div>
            <p class="form-hint">
              节点 computeNodeId：
              <code>{{ guideTargetNodeIdLabel }}</code>
              ；默认发到本机 enroll ID（命令省略 --target-node-id）。预览推流依赖上一步
              <code>set-srs</code>。
            </p>
            <pre class="script-block">{{ taskDispatchBundleCmd }}</pre>
            <div class="script-toolbar" style="margin-top: 8px">
              <Button
                size="small"
                preIcon="ant-design:copy-outlined"
                @click="copyText(taskDispatchBundleCmd, '下发命令已复制')"
              >
                复制全部下发命令
              </Button>
              <Button
                size="small"
                preIcon="ant-design:copy-outlined"
                @click="copyText(taskLocalSmokeCmd, '本机冒烟命令已复制')"
              >
                复制 --local 冒烟
              </Button>
            </div>
          </CollapseContainer>
          <CollapseContainer title="分步执行（配置 → enroll → run）" :can-expan="false">
            <div class="script-toolbar">
              <Button size="small" preIcon="ant-design:copy-outlined" @click="copyText(stepRunCmd, '分步命令已复制')">
                复制
              </Button>
            </div>
            <pre class="script-block">{{ stepRunCmd }}</pre>
          </CollapseContainer>
          <CollapseContainer title="常用运维命令" :can-expan="false">
            <pre class="script-block">{{ opsCmd }}</pre>
          </CollapseContainer>
        </div>

        <!-- 6 验收 -->
        <div v-show="activeStepKey === 'verify'" class="step-panel">
          <Alert
            :type="verifiedOnline ? 'success' : 'info'"
            show-icon
            :message="
              verifiedOnline
                ? '已检测到在线边缘节点，可调整容量或返回列表。'
                : '请保持边缘侧 agent 运行，点击「刷新验收」确认节点出现并处于在线状态。'
            "
          />
          <CollapseContainer title="验收结果" :can-expan="false">
            <div class="verify-toolbar">
              <Button type="primary" :loading="verifying" preIcon="ant-design:reload-outlined" @click="runVerify">
                刷新验收
              </Button>
              <span class="form-hint" style="margin: 0">最近刷新：{{ lastVerifyAt || '尚未验收' }}</span>
            </div>
            <div class="checklist" style="margin-top: 16px">
              <div v-for="item in verifyChecklist" :key="item.key" class="checklist__item">
                <CheckCircleFilled v-if="item.ok" class="ok" />
                <CloseCircleFilled v-else class="bad" />
                <div>
                  <div class="checklist__label">{{ item.label }}</div>
                  <div class="checklist__hint">{{ item.hint }}</div>
                </div>
              </div>
            </div>
            <a-table
              v-if="recentNodes.length"
              style="margin-top: 16px"
              size="small"
              row-key="id"
              :pagination="false"
              :columns="verifyColumns"
              :data-source="recentNodes"
              :custom-row="(record) => ({ onClick: () => selectFocusNode(record) })"
            />
          </CollapseContainer>
          <CollapseContainer v-if="focusNode" title="节点配置" :can-expan="false">
            <a-form layout="vertical" class="edit-inline">
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="显示名称">
                    <a-input v-model:value="editForm.name" />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="最大任务数">
                    <a-input-number v-model:value="editForm.maxTaskCount" :min="1" :max="64" style="width: 100%" />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="启用">
                    <a-switch
                      :checked="editForm.enabled"
                      checked-children="启"
                      un-checked-children="停"
                      @change="(v) => (editForm.enabled = !!v)"
                    />
                  </a-form-item>
                </a-col>
              </a-row>
              <a-form-item label="备注">
                <a-textarea v-model:value="editForm.remark" :rows="2" />
              </a-form-item>
              <Button type="primary" :loading="saving" @click="saveFocusNode">保存配置</Button>
            </a-form>
          </CollapseContainer>
        </div>

        <!-- 7 完成 -->
        <div v-show="activeStepKey === 'finish'" class="step-panel">
          <Alert
            type="success"
            show-icon
            message="节点已加入无限联邦边缘集群。边缘节点与「算法任务」Tab 相互独立，互不影响。"
          />
          <div class="finish-grid">
            <div class="finish-card">
              <div class="finish-card__title">联邦纳管</div>
              <div class="finish-card__desc">
                节点已登记至边缘管理表，可在本 Tab 调整最大任务数、启停与备注。
              </div>
            </div>
            <div class="finish-card">
              <div class="finish-card__title">铺开扩容</div>
              <div class="finish-card__desc">
                约 512MB 即可再接入一台开发板；调整最大任务数控制容量，停用后不再参与边缘侧调度。
              </div>
            </div>
            <div class="finish-card">
              <div class="finish-card__title">命令启停</div>
              <div class="finish-card__desc">
                常驻 <code>edge run</code>，再用
                <code>python -m edge task start/stop</code> 经 MQTT 启停负载；告警写共享 Ceph，经总线回中心归档。
              </div>
            </div>
          </div>
          <div class="finish-actions">
            <Button type="primary" size="large" @click="emitSuccessAndClose">
              返回边缘节点列表
            </Button>
          </div>
        </div>
      </div>
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue';
import {
  Alert,
  Col as ACol,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  InputNumber as AInputNumber,
  Row as ARow,
  Select as ASelect,
  Switch as ASwitch,
  Table as ATable,
  Tag as ATag,
  Textarea as ATextarea,
  Steps,
} from 'ant-design-vue';
import { CheckCircleFilled, CloseCircleFilled } from '@ant-design/icons-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicTitle } from '@/components/Basic';
import { CollapseContainer } from '@/components/Container';
import { Button } from '@/components/Button';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import { copyText } from '@/utils/copyTextToClipboard';
import {
  getEdgeNode,
  getEdgeNodePage,
  updateEdgeNode,
  type EdgeNodeVO,
} from '@/api/device/edge';
import { listMediaNodes, type ComputeNodeVO } from '@/api/device/node';
import {
  getControlPlaneHookEndpoint,
  isLocalControlPlaneUrl,
  readMediaPortsFromTags,
  resolveControlPlaneAgentUrl,
  formatNodeFunctions,
} from '@/views/node/utils/constants';
import NODE_COMPUTE_IMAGE from '@/assets/images/node/node-compute.svg';
import { statusColor, statusText } from './Data';

defineOptions({ name: 'EdgeSetupGuideDrawer' });

const emit = defineEmits(['register', 'success']);

const EDGE_NODE_URL_KEY = 'easyaiot_edge_node_url';
const EDGE_SRS_NODE_ID_KEY = 'easyaiot_edge_srs_node_id';
const NODE_IMAGE = NODE_COMPUTE_IMAGE;
const { createMessage } = useMessage();

type StepKey = 'overview' | 'prepare' | 'install' | 'config' | 'run' | 'verify' | 'finish';

interface StepDef {
  key: StepKey;
  title: string;
  description: string;
}

const STEPS: StepDef[] = [
  { key: 'overview', title: '概述', description: '接入方式说明' },
  { key: 'prepare', title: '中心准备', description: '服务与凭证' },
  { key: 'install', title: '安装依赖', description: '边缘侧环境' },
  { key: 'config', title: '配置地址', description: 'NODE 与 SRS' },
  { key: 'run', title: '启动', description: '订阅与命令下发' },
  { key: 'verify', title: '验收', description: '在线与 Ceph' },
  { key: 'finish', title: '完成', description: '常驻与命令启停' },
];

const currentStep = ref(0);
const controlPlaneUrl = ref('');
const joinToken = ref('');
const resolvingUrl = ref(false);
const verifying = ref(false);
const verifiedOnline = ref(false);
const lastVerifyAt = ref('');
const focusNode = ref<EdgeNodeVO | null>(null);
const recentNodes = ref<EdgeNodeVO[]>([]);
const saving = ref(false);
const mediaNodes = ref<ComputeNodeVO[]>([]);
const selectedSrsNodeId = ref<number | undefined>(undefined);
const loadingMedia = ref(false);

const editForm = reactive({
  id: 0,
  name: '',
  maxTaskCount: 1,
  remark: '',
  enabled: true,
});

const heroTags = ['内存约 512MB', 'Ceph 边缘 0 硬盘', '一行命令上线', '算力铺开部署', '汇聚上云', '无限联邦扩容'];

const journeyCards = [
  { index: '01', title: '中心就绪', desc: '确认 Gateway、MQTT、Ceph、流媒体节点可用；按需配置 Join Token' },
  { index: '02', title: '安装配置', desc: '写入控制面地址，并下拉选定可用的 SRS 节点' },
  { index: '03', title: '常驻 + 命令下发', desc: 'edge run 订阅总线；另开终端用 edge task start/stop 启停负载' },
  { index: '04', title: '验收上云', desc: '确认在线与 Ceph 就绪；预览推流走已选定的 SRS' },
];

const installCmd = `cd EDGE
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt`;

const opsCmd = `python -m edge status
python -m edge pull-config
python -m edge task stop --task-id <TASK_ID>
python -m edge stop`;

const guideTaskId = ref<number>(900001);
const guideTaskType = ref<'realtime' | 'snap' | 'patrol'>('realtime');
const taskTypeOptions = [
  { value: 'realtime', label: 'realtime' },
  { value: 'snap', label: 'snap' },
  { value: 'patrol', label: 'patrol' },
];

const activeStepKey = computed(() => STEPS[currentStep.value]?.key ?? 'overview');
const isFirstStep = computed(() => currentStep.value === 0);
const isLastStep = computed(() => currentStep.value === STEPS.length - 1);
const stepItems = computed(() =>
  STEPS.map((s) => ({ title: s.title, description: s.description })),
);

const headerMeta = computed(() => {
  if (focusNode.value) {
    return `${focusNode.value.name || '未命名'} · ${focusNode.value.host || '-'}`;
  }
  return '无限联邦边缘集群 · 512MB内存 · Ceph 0 硬盘 · 汇聚上云';
});

const setNodeCmd = computed(
  () => `python -m edge config set-node ${controlPlaneUrl.value || 'http://<控制面主机>:48080'}`,
);

const setJoinTokenCmd = computed(
  () => `python -m edge config set-join-token ${joinToken.value.trim()}`,
);

const selectedSrsNode = computed(() => {
  if (selectedSrsNodeId.value == null) return null;
  return mediaNodes.value.find((n) => n.id === selectedSrsNodeId.value) || null;
});

const selectedSrsPorts = computed(() => {
  const node = selectedSrsNode.value;
  if (!node) return null;
  return readMediaPortsFromTags(node.tags);
});

const selectedSrsSummary = computed(() => {
  const node = selectedSrsNode.value;
  const ports = selectedSrsPorts.value;
  if (!node?.host || !ports) return null;
  return {
    name: node.name || '未命名',
    host: node.host,
    role: formatNodeFunctions(node),
    rtmpBase: `rtmp://${node.host}:${ports.srsRtmpPort}/ai/<deviceId>`,
    httpBase: `http://${node.host}:${ports.srsHttpPort}/ai/<deviceId>.flv`,
  };
});

const srsSelectOptions = computed(() =>
  mediaNodes.value
    .filter((n) => n.id != null && !!n.host)
    .map((n) => {
      const ports = readMediaPortsFromTags(n.tags);
      return {
        value: n.id as number,
        label: `${n.name || '未命名'} (${n.host}) · ${formatNodeFunctions(n)} · RTMP ${ports.srsRtmpPort}`,
      };
    }),
);

const setSrsCmd = computed(() => {
  const node = selectedSrsNode.value;
  const ports = selectedSrsPorts.value;
  if (!node?.host || !ports) return '';
  return [
    'python -m edge config set-srs',
    `--host ${node.host}`,
    `--rtmp-port ${ports.srsRtmpPort}`,
    `--http-port ${ports.srsHttpPort}`,
    `--api-port ${ports.srsApiPort}`,
  ].join(' ');
});

/** 控制面 + SRS + Join Token 自动拼接，供现场一键复制 */
const configBundleCmd = computed(() => {
  const lines = [
    '# EasyAIoT EDGE 现场配置（控制面 + 选定的 SRS）',
    setNodeCmd.value,
  ];
  if (setSrsCmd.value) {
    lines.push(setSrsCmd.value);
  } else {
    lines.push('# （未选择 SRS）建议先在上方下拉选定已勾选直播/推流的节点后再复制');
  }
  if (joinToken.value.trim()) {
    lines.push(setJoinTokenCmd.value);
  }
  return lines.join('\n');
});

const runCmd = computed(() => {
  const lines = [
    '# 尚未配置时先执行：',
    setNodeCmd.value,
  ];
  if (setSrsCmd.value) {
    lines.push(setSrsCmd.value);
  }
  if (joinToken.value.trim()) {
    lines.push(setJoinTokenCmd.value);
  }
  lines.push(`python -m edge run`);
  return lines.join('\n');
});

const stepRunCmd = computed(() => {
  const lines = [setNodeCmd.value];
  if (setSrsCmd.value) lines.push(setSrsCmd.value);
  if (joinToken.value.trim()) lines.push(setJoinTokenCmd.value);
  lines.push('python -m edge enroll', 'python -m edge run');
  return lines.join('\n');
});

const guideTargetNodeId = computed(() => focusNode.value?.computeNodeId ?? undefined);

const guideTargetNodeIdLabel = computed(() => {
  if (guideTargetNodeId.value != null) {
    return `${guideTargetNodeId.value}（来自当前选中边缘节点）`;
  }
  return '执行 edge status / enroll 后的 nodeId（命令默认用本机）';
});

const taskStartCmd = computed(() => {
  const parts = [
    'python -m edge task start',
    `--task-id ${guideTaskId.value}`,
    `--type ${guideTaskType.value}`,
  ];
  if (guideTargetNodeId.value != null) {
    parts.push(`--target-node-id ${guideTargetNodeId.value}`);
  }
  return parts.join(' ');
});

const taskStopCmd = computed(() => {
  const parts = ['python -m edge task stop', `--task-id ${guideTaskId.value}`];
  if (guideTargetNodeId.value != null) {
    parts.push(`--target-node-id ${guideTargetNodeId.value}`);
  }
  return parts.join(' ');
});

const taskDispatchBundleCmd = computed(() => {
  const srsHint = setSrsCmd.value
    ? '# 已选定 SRS，推流目标来自 edge.env 中 EDGE_SRS_*'
    : '# 未选定 SRS 时，推流可能回落到默认逻辑；建议先在「配置地址」下拉选定';
  return [
    '# 终端 A：常驻（已在上方复制）',
    '# python -m edge run',
    '',
    '# 终端 B：命令下发（不经算法任务 Tab）',
    srsHint,
    taskStartCmd.value,
    '',
    '# 停止',
    taskStopCmd.value,
  ].join('\n');
});

const taskLocalSmokeCmd = computed(() => {
  return [
    '# 本机冒烟（不经 MQTT，直接拉起 EDGE/runtime；适合单机验收）',
    `${taskStartCmd.value} --local`,
    `${taskStopCmd.value} --local`,
  ].join('\n');
});

const prepareChecklist = computed(() => [
  {
    key: 'gateway',
    label: 'iot-node Gateway 可达（:48080）',
    ok: !!controlPlaneUrl.value && !isLocalControlPlaneUrl(controlPlaneUrl.value) ? true : false,
    hint: controlPlaneUrl.value || '在「配置地址」步骤确认',
  },
  {
    key: 'srs',
    label: '在线 SRS / 媒体节点可用',
    ok: mediaNodes.value.length > 0 ? (selectedSrsNodeId.value != null ? true : false) : false,
    hint: mediaNodes.value.length
      ? selectedSrsNodeId.value != null
        ? `已选定：${selectedSrsSummary.value?.name || selectedSrsNodeId.value}`
        : `发现 ${mediaNodes.value.length} 个媒体节点，请在「配置地址」下拉选定`
      : '请先部署/上线已勾选直播接入或推流转发的节点',
  },
  {
    key: 'mqtt',
    label: '中心 MQTT / EMQX 集群在线',
    ok: null as boolean | null,
    hint: 'runtime-config 会下发 broker 列表；请在节点管理中确认 MQTT 可用',
  },
  {
    key: 'ceph',
    label: 'NFS 与中心路径一致',
    ok: null as boolean | null,
    hint: '边缘需挂载同一 NFS 路径，否则 nfsMountReady=false',
  },
  {
    key: 'token',
    label: 'Join Token 或开放登记策略已确认',
    ok: null as boolean | null,
    hint: joinToken.value.trim()
      ? '已填写 Join Token，将写入配置命令'
      : '测试可用 allow-open-enroll；生产建议配置 join-token',
  },
]);

const verifyChecklist = computed(() => {
  const node = focusNode.value;
  return [
    {
      key: 'appear',
      label: '管理表出现节点记录',
      ok: recentNodes.value.length > 0,
      hint: recentNodes.value.length
        ? `当前可见 ${recentNodes.value.length} 条`
        : '暂无记录，请确认 agent 已启动且控制面地址正确',
    },
    {
      key: 'online',
      label: '节点状态为在线',
      ok: !!node && node.status === 'online',
      hint: node ? statusText(node.status) : '请点击列表行选中节点，或刷新验收',
    },
    {
      key: 'ceph',
      label: 'Ceph 挂载就绪',
      ok: !!node?.cephMountReady,
      hint: node?.cephMountReady ? '已挂载' : '未就绪时部分边缘能力受限',
    },
    {
      key: 'heartbeat',
      label: '最近心跳正常',
      ok: !!node?.lastHeartbeatAt,
      hint: node?.lastHeartbeatAt || '暂无心跳',
    },
  ];
});

const verifyColumns = [
  { title: '名称', dataIndex: 'name', ellipsis: true },
  { title: '主机', dataIndex: 'host', width: 140 },
  {
    title: '状态',
    dataIndex: 'status',
    width: 90,
    customRender: ({ text }: { text: string }) => statusText(text),
  },
  {
    title: 'Ceph',
    dataIndex: 'cephMountReady',
    width: 90,
    customRender: ({ text }: { text: boolean }) => (text ? '就绪' : '未就绪'),
  },
  { title: '心跳', dataIndex: 'lastHeartbeatAt', width: 170 },
];

watch(controlPlaneUrl, (url) => {
  try {
    if (url?.trim() && !isLocalControlPlaneUrl(url)) {
      localStorage.setItem(EDGE_NODE_URL_KEY, url.trim());
    }
  } catch {
    /* ignore */
  }
});

watch(selectedSrsNodeId, (id) => {
  try {
    if (id != null) localStorage.setItem(EDGE_SRS_NODE_ID_KEY, String(id));
    else localStorage.removeItem(EDGE_SRS_NODE_ID_KEY);
  } catch {
    /* ignore */
  }
});

const [registerDrawer, { closeDrawer }] = useDrawerInner(async (data?: { nodeId?: number; step?: StepKey }) => {
  currentStep.value = data?.step ? Math.max(0, STEPS.findIndex((s) => s.key === data.step)) : 0;
  if (currentStep.value < 0) currentStep.value = 0;
  verifiedOnline.value = false;
  lastVerifyAt.value = '';
  focusNode.value = null;
  recentNodes.value = [];
  await Promise.all([refreshControlPlaneUrl(), loadMediaNodes()]);
  if (data?.nodeId) {
    await loadFocusNode(data.nodeId);
    currentStep.value = STEPS.findIndex((s) => s.key === 'verify');
    await runVerify();
  }
});

async function loadMediaNodes() {
  loadingMedia.value = true;
  try {
    mediaNodes.value = await listMediaNodes();
    let savedId: number | undefined;
    try {
      const raw = localStorage.getItem(EDGE_SRS_NODE_ID_KEY);
      if (raw) {
        const n = Number(raw);
        if (Number.isFinite(n)) savedId = n;
      }
    } catch {
      /* ignore */
    }
    if (savedId != null && mediaNodes.value.some((n) => n.id === savedId)) {
      selectedSrsNodeId.value = savedId;
    } else if (
      selectedSrsNodeId.value != null &&
      !mediaNodes.value.some((n) => n.id === selectedSrsNodeId.value)
    ) {
      selectedSrsNodeId.value = mediaNodes.value[0]?.id;
    } else if (selectedSrsNodeId.value == null && mediaNodes.value.length === 1) {
      selectedSrsNodeId.value = mediaNodes.value[0]?.id;
    }
  } catch (e: any) {
    mediaNodes.value = [];
    createMessage.warning(e?.message || '加载媒体节点失败');
  } finally {
    loadingMedia.value = false;
  }
}

async function refreshControlPlaneUrl() {
  resolvingUrl.value = true;
  try {
    let saved = '';
    try {
      saved = localStorage.getItem(EDGE_NODE_URL_KEY)?.trim() || '';
    } catch {
      /* ignore */
    }
    if (saved && !isLocalControlPlaneUrl(saved)) {
      controlPlaneUrl.value = saved;
      return;
    }
    await resolveControlPlaneAgentUrl();
    const { host, port } = getControlPlaneHookEndpoint();
    controlPlaneUrl.value = `http://${host}:${port}`;
  } finally {
    resolvingUrl.value = false;
  }
}

async function loadFocusNode(id: number) {
  try {
    const node = (await getEdgeNode(id)) as EdgeNodeVO;
    selectFocusNode(node);
  } catch (e: any) {
    createMessage.error(e?.message || '加载节点详情失败');
  }
}

function selectFocusNode(node: EdgeNodeVO) {
  focusNode.value = node;
  editForm.id = node.id || 0;
  editForm.name = node.name || '';
  editForm.maxTaskCount = node.maxTaskCount || 1;
  editForm.remark = node.remark || '';
  editForm.enabled = node.enabled !== false;
  if (node.status === 'online') verifiedOnline.value = true;
}

async function runVerify() {
  verifying.value = true;
  try {
    const res = await getEdgeNodePage({ pageNo: 1, pageSize: 20 });
    recentNodes.value = res?.list || [];
    lastVerifyAt.value = new Date().toLocaleString();
    if (focusNode.value?.id) {
      const matched = recentNodes.value.find((n) => n.id === focusNode.value?.id);
      if (matched) selectFocusNode(matched);
      else await loadFocusNode(focusNode.value.id);
    } else if (recentNodes.value.length) {
      const online = recentNodes.value.find((n) => n.status === 'online') || recentNodes.value[0];
      selectFocusNode(online);
    }
    if (recentNodes.value.some((n) => n.status === 'online')) {
      verifiedOnline.value = true;
      createMessage.success('已检测到在线边缘节点');
    } else if (recentNodes.value.length) {
      createMessage.warning('已有节点记录但未在线，请检查 agent 进程与网络');
    } else {
      createMessage.warning('暂无边缘节点记录，请确认 agent 已启动');
    }
  } catch (e: any) {
    createMessage.error(e?.message || '验收失败');
  } finally {
    verifying.value = false;
  }
}

async function saveFocusNode() {
  if (!editForm.id) return;
  saving.value = true;
  try {
    await updateEdgeNode({
      id: editForm.id,
      name: editForm.name,
      maxTaskCount: editForm.maxTaskCount,
      remark: editForm.remark,
      enabled: editForm.enabled,
    });
    createMessage.success('节点配置已保存');
    await runVerify();
    emit('success');
  } catch (e: any) {
    createMessage.error(e?.message || '保存失败');
  } finally {
    saving.value = false;
  }
}

function handlePrev() {
  if (!isFirstStep.value) currentStep.value -= 1;
}

function handleNext() {
  if (isLastStep.value) return;
  currentStep.value += 1;
  if (STEPS[currentStep.value]?.key === 'verify') void runVerify();
}

function handleStepChange(idx: number) {
  currentStep.value = idx;
  if (STEPS[idx]?.key === 'verify') void runVerify();
}

function handleClose() {
  closeDrawer();
}

function handleOpenChange(open: boolean) {
  if (!open) emit('success');
}

function emitSuccessAndClose() {
  emit('success');
  closeDrawer();
}
</script>

<style lang="less" scoped>
@import '@/views/node/utils/setup-panel.less';

.setup-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  padding-right: 32px;
}

.setup-drawer-header__main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.setup-drawer-header__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #eef4ff, #dce8ff);
  color: @node-primary;
  flex-shrink: 0;
}

.setup-drawer-header__title {
  font-size: 18px !important;
  font-weight: 600 !important;
}

.setup-drawer-header__meta {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.setup-drawer-header__tags {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.setup-drawer-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 4px 0 8px;
}

.setup-hero {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 24px;
  padding: 22px 26px;
  border-radius: @setup-panel-radius;
  background: linear-gradient(120deg, #f3f7ff 0%, #ffffff 55%, #eef6ff 100%);
  border: 1px solid rgba(38, 108, 251, 0.12);
  box-shadow: @setup-panel-shadow;
}

.setup-hero__eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: @node-primary;
  margin-bottom: 8px;
}

.setup-hero__title {
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.35;
}

.setup-hero__desc {
  margin-top: 10px;
  max-width: 720px;
  color: rgba(15, 23, 42, 0.65);
  font-size: 13px;
  line-height: 1.7;
}

.setup-hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.setup-hero__tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  color: #1d4ed8;
  background: rgba(38, 108, 251, 0.08);
  border: 1px solid rgba(38, 108, 251, 0.14);
}

.setup-hero__visual {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  img {
    width: 108px;
    filter: drop-shadow(0 8px 16px rgba(67, 120, 154, 0.18));
  }
}

.setup-steps-card {
  padding: 16px 18px;
  border-radius: @setup-panel-radius;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: @setup-panel-shadow;
}

.setup-steps {
  :deep(.ant-steps-item) {
    flex: 1;
    min-width: 0;
  }

  :deep(.ant-steps-item-title) {
    font-size: 13px;
    font-weight: 500;
  }

  :deep(.ant-steps-item-description) {
    font-size: 12px;
  }

  :deep(.ant-steps-item-process .ant-steps-item-icon) {
    background: @node-primary;
    border-color: @node-primary;
  }
}

.step-panel {
  display: flex;
  flex-direction: column;
  gap: @setup-section-gap;
}

.journey-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.journey-card {
  padding: 16px 18px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: @setup-panel-shadow;
  min-height: 132px;
}

.journey-card__index {
  font-size: 12px;
  font-weight: 700;
  color: @node-primary;
  letter-spacing: 0.06em;
}

.journey-card__title {
  margin-top: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.journey-card__desc {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(15, 23, 42, 0.6);
}

.bullet-list {
  margin: 0;
  padding-left: 18px;
  color: rgba(0, 0, 0, 0.75);
  line-height: 1.8;
}

.checklist {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.checklist__item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fafbfd;

  .ok {
    color: #52c41a;
    margin-top: 2px;
  }

  .bad {
    color: #ff4d4f;
    margin-top: 2px;
  }
}

.checklist__label {
  font-weight: 600;
  color: #0f172a;
}

.checklist__hint {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  line-height: 1.5;
}

.url-row {
  display: flex;
  gap: 8px;
  align-items: center;

  .srs-select {
    flex: 1;
    min-width: 0;
  }
}

.srs-summary {
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: 8px;
  background: #fafbfd;
  border: 1px solid #f0f0f0;
}

.srs-summary__row {
  display: flex;
  gap: 12px;
  align-items: baseline;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(0, 0, 0, 0.75);

  code {
    font-size: 12px;
    word-break: break-all;
  }
}

.srs-summary__label {
  flex: 0 0 36px;
  color: rgba(0, 0, 0, 0.45);
  font-weight: 600;
}

.script-toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 8px;
}

.script-block {
  margin: 0;
  padding: 14px 16px;
  border-radius: 8px;
  background: #0b1220;
  color: #e2e8f0;
  font-size: 12px;
  line-height: 1.7;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.join-token-block {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px dashed #f0f0f0;
}

.join-token-block__label {
  margin-bottom: 8px;
  font-weight: 600;
}

.verify-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
}

.edit-inline {
  max-width: 960px;
}

.finish-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.finish-card {
  padding: 18px 20px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: @setup-panel-shadow;
}

.finish-card__title {
  font-size: 16px;
  font-weight: 600;
}

.finish-card__desc {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(0, 0, 0, 0.65);
}

.finish-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.footer-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.footer-nav {
  display: flex;
  gap: 8px;
}

@media (max-width: 1100px) {
  .journey-grid,
  .finish-grid {
    grid-template-columns: 1fr 1fr;
  }

  .setup-hero {
    flex-direction: column;
  }
}
</style>

<style lang="less">
@import '@/views/node/utils/setup-panel.less';

.edge-setup-guide-drawer {
  .ant-drawer-header {
    padding: 16px 24px;
    border-bottom: 1px solid #f0f0f0;
  }

  .ant-drawer-body {
    background: linear-gradient(180deg, #f7f9fc 0%, #ffffff 140px);
  }

  .scrollbar__wrap {
    padding: 20px 24px !important;
  }

  .ant-drawer-footer {
    padding: 12px 24px;
    border-top: 1px solid #f0f0f0;
    background: #fff;
  }

  .xingyuv-collapse-container {
    .setup-section-card();
    padding: 0;
    overflow: hidden;

    .p-2 {
      padding: @setup-section-body-padding !important;
    }

    &__header {
      height: auto;
      min-height: 48px;
      padding: @setup-section-header-padding !important;
      border-bottom: 1px solid #f0f0f0;
    }
  }
}
</style>
