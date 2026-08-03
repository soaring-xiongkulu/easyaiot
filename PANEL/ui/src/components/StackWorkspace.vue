<template>
  <div class="page" :class="{ embedded }">
    <div class="page-head" v-if="!embedded">
      <div>
        <h1>{{ title }}</h1>
        <p>
          形态 <code>{{ profile }}</code> · {{ selectedProfileDesc }}；{{ subtitle }}
        </p>
      </div>
      <a-radio-group
        v-model:value="profile"
        button-style="solid"
        size="small"
        :disabled="!deploySupported"
      >
        <a-radio-button value="mini">mini</a-radio-button>
        <a-radio-button value="standard">standard</a-radio-button>
        <a-radio-button value="full">full</a-radio-button>
      </a-radio-group>
    </div>

    <div class="embed-bar" v-else>
      <div class="embed-meta">
        形态 <code>{{ profile }}</code>
        <span class="muted">· {{ selectedProfileDesc }}</span>
      </div>
      <a-radio-group
        v-model:value="profile"
        button-style="solid"
        size="small"
        :disabled="!deploySupported"
      >
        <a-radio-button value="mini">mini</a-radio-button>
        <a-radio-button value="standard">standard</a-radio-button>
        <a-radio-button value="full">full</a-radio-button>
      </a-radio-group>
    </div>

    <a-alert
      v-if="!deploySupported"
      type="warning"
      show-icon
      class="deploy-block"
      :message="deployBlockTitle"
      :description="deployBlockDesc"
    />

    <div class="split">
      <div class="col left">
        <div class="opts panel" v-if="showOptions">
          <div class="panel-hd">
            <h2>执行参数</h2>
          </div>
          <div class="opts-body">
            <div class="opt" v-if="needsImageMode">
              <label>镜像获取</label>
              <a-select
                v-model:value="imageMode"
                size="small"
                style="width: 100%"
                :disabled="!deploySupported"
                :options="imageModeOptions"
              />
            </div>
            <div class="opt" v-if="needsModule">
              <label>{{ moduleLabel }}</label>
              <a-select
                v-model:value="moduleArg"
                size="small"
                allow-clear
                style="width: 100%"
                :disabled="!deploySupported"
                :placeholder="moduleOptional ? '全部（默认）' : '请选择模块'"
                :options="moduleOptions"
              />
            </div>
            <div class="opt" v-if="needsBuildArch">
              <label>构建架构</label>
              <a-select
                v-model:value="buildArch"
                size="small"
                style="width: 100%"
                :disabled="!deploySupported"
                :options="buildArchOptions"
              />
            </div>
            <div class="opt check" v-if="needsParallelBuild">
              <a-checkbox v-model:checked="parallelBuild" :disabled="!deploySupported">并行构建（内存充足时）</a-checkbox>
            </div>
          </div>
        </div>

        <div class="action-grid">
          <button
            v-for="a in categoryActions"
            :key="a.action"
            type="button"
            class="action"
            :class="{ danger: a.dangerous || a.action === 'stop' }"
            :disabled="
              !deploySupported ||
              busy ||
              confirmLoading ||
              stopLoading ||
              procLoading ||
              (a.dangerous && !allowDangerous)
            "
            @click="askRun(a)"
          >
            <div class="action-title">
              <strong>{{ a.label }}</strong>
              <code>{{ a.action }}</code>
            </div>
            <span>{{ a.desc }}</span>
            <span v-if="!deploySupported" class="lock">当前系统不可用</span>
            <span v-else-if="a.dangerous && !allowDangerous" class="lock">需 PANEL_ALLOW_DANGEROUS=1</span>
          </button>
        </div>

        <div class="panel proc-panel" v-if="showProcesses">
          <div class="panel-hd">
            <div>
              <h2>部署进程</h2>
              <div class="muted">{{ processes.length ? `检测到 ${processes.length} 个` : '未检测到运行中进程' }}</div>
            </div>
            <a-space :size="6">
              <a-button size="small" :loading="procLoading" @click="loadProcesses">检测</a-button>
              <a-button
                size="small"
                danger
                type="primary"
                :disabled="!processes.length"
                :loading="procKillLoading"
                @click="askKillAll"
              >
                全部杀掉
              </a-button>
            </a-space>
          </div>
          <div class="procs" v-if="processes.length">
            <div v-for="p in processes.slice(0, 4)" :key="p.pid" class="proc">
              <div class="proc-main">
                <div class="proc-title">
                  <code>{{ p.marker }}</code>
                  <span class="mono">pid {{ p.pid }}</span>
                  <a-tag v-if="p.ownedByPanel" color="processing">面板任务</a-tag>
                </div>
                <div class="muted mono proc-cmd">{{ shortCmd(p.cmd) }}</div>
              </div>
              <a-button size="small" danger :loading="procKillLoading" @click="askKillOne(p)">杀掉</a-button>
            </div>
          </div>
          <div v-else class="panel-bd muted">可检测并终止宿主机上的部署脚本进程（install_linux / install_mac / install_windows 等）。</div>
        </div>

        <div class="panel jobs-panel" v-if="jobs.length">
          <div class="panel-hd"><h2>历史任务</h2></div>
          <div class="jobs">
            <button
              v-for="j in jobs.slice(0, 15)"
              :key="j.id"
              type="button"
              class="job"
              :class="{ active: j.id === activeJob?.id }"
              @click="selectJob(j.id)"
            >
              <div>
                <div class="job-name">{{ j.action }}</div>
                <div class="muted mono">{{ j.id }}</div>
              </div>
              <a-tag :color="jobColor(j.status)">{{ j.status }}</a-tag>
            </button>
          </div>
        </div>
      </div>

      <div class="col right">
        <div ref="logPanelRef" class="panel log-panel">
          <div class="panel-hd">
            <div>
              <h2>任务日志</h2>
              <div class="muted" v-if="activeJob">{{ activeJob.action }} · {{ activeJob.status }}</div>
              <div class="muted" v-else>执行后在此显示输出</div>
            </div>
            <a-space>
              <a-button
                v-if="canStop || processes.length"
                size="small"
                danger
                type="primary"
                :loading="stopLoading || procKillLoading"
                @click="canStop ? askStop() : askKillAll()"
              >
                {{ canStop ? '停止部署' : '杀掉进程' }}
              </a-button>
              <a-button size="small" :disabled="!activeJob" @click="refreshJob">刷新</a-button>
              <a-button size="small" :disabled="!logText" @click="copyLog">复制</a-button>
              <a-button size="small" :disabled="!logText" @click="scrollLogToBottom">到底部</a-button>
            </a-space>
          </div>
          <div class="panel-bd progress-hint" v-if="busy">
            <a-alert type="info" show-icon message="任务执行中。可随时点击「停止部署」终止。" />
          </div>
          <pre ref="logPreRef" class="logs live" @scroll="onLogScroll">{{ logText || '尚未执行任务' }}</pre>
        </div>
      </div>
    </div>

    <ConfirmDialog
      v-model:open="confirmOpen"
      :title="confirmTitle"
      :description="confirmDesc"
      :warning="confirmWarn"
      :rows="confirmRows"
      :ok-text="confirmOk"
      :danger="confirmDanger"
      :loading="confirmLoading"
      @confirm="doConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import ConfirmDialog from './ConfirmDialog.vue'
import {
  cancelStackJob,
  getProfile,
  getStackMeta,
  getStackJob,
  killDeployProcesses,
  listDeployProcesses,
  listStackJobs,
  runStackAction,
  type DeployProcess,
  type StackAction,
  type StackJob,
} from '../api'

const props = withDefaults(
  defineProps<{
    category: 'lifecycle' | 'image' | 'diagnose' | 'maintain'
    title: string
    subtitle?: string
    /** 嵌入页签时隐藏外层标题，由父级提供导航 */
    embedded?: boolean
  }>(),
  { subtitle: '右侧实时展示任务日志', embedded: false },
)

function stripAnsi(raw: string): string {
  return (raw || '')
    .replace(/\u001b\[[0-9;?]*[ -/]*[@-~]/g, '')
    .replace(/\u001b[@-Z\\-_]/g, '')
    .replace(/\r([^\n])/g, '\n$1')
}

const actions = ref<StackAction[]>([])
const allowDangerous = ref(false)
const deploySupported = ref(true)
const deployMessage = ref('')
const deployHint = ref('')
const platformLabel = ref('Linux')
const scriptName = ref('install_linux.sh')
const desktopImageOnly = ref(false)
const profile = ref('full')
const imageMode = ref('pull')
const moduleArg = ref<string | undefined>(undefined)
const buildArch = ref('all')
const parallelBuild = ref(false)
const imageModeOptions = ref<{ value: string; label: string }[]>([])
const buildArchOptions = ref<{ value: string; label: string }[]>([])
const profileDescMap: Record<string, string> = {
  mini: '轻量版（内存 >= 2 GB）',
  standard: '标准版（内存 >= 8 GB）',
  full: '完整版（推荐 >= 20 GB）',
}
const selectedProfileDesc = computed(() => profileDescMap[profile.value] || '按所选形态部署')
const deployBlockTitle = computed(() => {
  const os = platformLabel.value || '当前系统'
  return `${os} 不支持一键部署`
})
const deployBlockDesc = computed(
  () =>
    deployMessage.value ||
    deployHint.value ||
    '当前环境无法执行一键部署，请检查 Docker 与 INSTALL_SCRIPT / EASYAIOT_ROOT。',
)
const activeJob = ref<StackJob | null>(null)
const jobs = ref<StackJob[]>([])
const busy = ref(false)
const logPanelRef = ref<HTMLElement | null>(null)
const logPreRef = ref<HTMLPreElement | null>(null)
let pollTimer: number | undefined
let procTimer: number | undefined
let pendingAction: StackAction | null = null
let pendingMode: 'run' | 'stop' | 'kill-all' | 'kill-one' = 'run'
let pendingKillPid: number | null = null

const confirmOpen = ref(false)
const confirmLoading = ref(false)
const confirmTitle = ref('')
const confirmDesc = ref('')
const confirmWarn = ref('')
const confirmOk = ref('确认执行')
const confirmDanger = ref(false)
const confirmRows = ref<{ label: string; value: string }[]>([])
const stopLoading = ref(false)
const processes = ref<DeployProcess[]>([])
const procLoading = ref(false)
const procKillLoading = ref(false)

const categoryActions = computed(() =>
  actions.value.filter((a) => a.category === props.category || (!a.category && props.category === 'lifecycle')),
)

const showProcesses = computed(() => props.category === 'lifecycle' || props.category === 'maintain')

const needsImageMode = computed(() =>
  categoryActions.value.some((a) => a.supportsImageMode),
)
const needsModule = computed(() => categoryActions.value.some((a) => !!a.argKey))
const needsBuildArch = computed(() => categoryActions.value.some((a) => a.supportsBuildArch))
const needsParallelBuild = computed(() => categoryActions.value.some((a) => a.supportsParallelBuild))
const showOptions = computed(
  () => needsImageMode.value || needsModule.value || needsBuildArch.value || needsParallelBuild.value,
)

const moduleLabel = computed(() => {
  const hit = categoryActions.value.find((a) => a.argLabel)
  return hit?.argLabel || '模块'
})
const moduleOptional = computed(() => categoryActions.value.some((a) => a.argOptional !== false && a.argKey))
const moduleOptions = computed(() => {
  const hit = categoryActions.value.find((a) => a.argOptions?.length)
  return (hit?.argOptions || []).map((o) => ({ value: o.value, label: o.label }))
})

const logText = computed(() => stripAnsi(activeJob.value?.log || activeJob.value?.logTail || ''))
const autoScroll = ref(true)

const canStop = computed(
  () => !!activeJob.value?.id && ['running', 'queued'].includes(activeJob.value?.status || ''),
)

function onLogScroll() {
  const el = logPreRef.value
  if (!el) return
  autoScroll.value = el.scrollHeight - el.scrollTop - el.clientHeight < 80
}

async function scrollLogToBottom() {
  await nextTick()
  const el = logPreRef.value
  if (!el) return
  el.scrollTop = el.scrollHeight
  autoScroll.value = true
}

watch(logText, async () => {
  if (!autoScroll.value) return
  await scrollLogToBottom()
})

function jobColor(status?: string) {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'error'
  if (status === 'cancelled') return 'warning'
  if (status === 'running') return 'processing'
  return 'default'
}

async function loadMeta() {
  const [meta, prof] = await Promise.all([getStackMeta(), getProfile()])
  actions.value = meta.actions || []
  allowDangerous.value = !!meta.allowDangerous
  deploySupported.value = meta.deploySupported !== false
  deployMessage.value = meta.deployMessage || meta.platform?.message || ''
  deployHint.value = meta.deployHint || meta.platform?.hint || ''
  platformLabel.value = meta.platform?.label || '当前系统'
  scriptName.value = meta.scriptName || meta.platform?.scriptName || 'install_linux.sh'
  desktopImageOnly.value = !!(meta.desktopImageOnly || meta.platform?.desktopImageOnly)
  imageModeOptions.value = meta.imageModes || []
  buildArchOptions.value = meta.buildArchs || []
  if (desktopImageOnly.value || !imageModeOptions.value.some((x) => x.value === 'local')) {
    imageMode.value = 'pull'
  }
  if (prof.profile) profile.value = prof.profile
}

async function loadProcesses() {
  procLoading.value = true
  try {
    processes.value = (await listDeployProcesses()).list || []
  } catch {
    processes.value = []
  } finally {
    procLoading.value = false
  }
}

function shortCmd(cmd: string) {
  if (!cmd) return ''
  return cmd.length > 88 ? `${cmd.slice(0, 88)}…` : cmd
}

function askKillAll() {
  pendingMode = 'kill-all'
  pendingKillPid = null
  confirmTitle.value = '杀掉全部部署进程'
  confirmDesc.value = '将扫描并终止部署相关进程（含进程组）。'
  confirmWarn.value = '已拉起的容器不会自动删除；可稍后重新 install/start。'
  confirmOk.value = '确认全部杀掉'
  confirmDanger.value = true
  confirmRows.value = [
    { label: '进程数', value: String(processes.value.length || '检测后杀掉') },
    { label: '范围', value: `${scriptName.value} / middleware / runtime_image` },
  ]
  confirmOpen.value = true
}

function askKillOne(p: DeployProcess) {
  pendingMode = 'kill-one'
  pendingKillPid = p.pid
  confirmTitle.value = `杀掉进程 ${p.pid}`
  confirmDesc.value = '将终止该部署相关进程及其进程组。'
  confirmWarn.value = '若它是主安装脚本，整次部署会被中断。'
  confirmOk.value = '确认杀掉'
  confirmDanger.value = true
  confirmRows.value = [
    { label: 'PID', value: String(p.pid) },
    { label: '脚本', value: p.marker },
    { label: '命令', value: shortCmd(p.cmd) },
  ]
  confirmOpen.value = true
}

async function doKillProcesses(all: boolean, pid?: number | null) {
  confirmLoading.value = true
  procKillLoading.value = true
  try {
    const result = await killDeployProcesses(all ? { all: true } : { pids: pid ? [pid] : [] })
    processes.value = result.remaining || []
    confirmOpen.value = false
    stopPoll()
    await loadJobs()
    if (activeJob.value?.id) {
      try {
        activeJob.value = await getStackJob(activeJob.value.id)
      } catch {
        /* */
      }
    }
    message.success(`已处理 ${result.totalKilled || 0} 个进程`)
  } finally {
    confirmLoading.value = false
    procKillLoading.value = false
    pendingKillPid = null
  }
}

async function loadJobs() {
  try {
    jobs.value = (await listStackJobs(15)).list || []
  } catch {
    jobs.value = []
  }
}

async function selectJob(id: string) {
  autoScroll.value = true
  activeJob.value = await getStackJob(id)
  if (['running', 'queued'].includes(activeJob.value?.status || '')) {
    startPoll(id)
  } else {
    stopPoll()
  }
  await scrollLogToBottom()
}

async function refreshJob() {
  if (!activeJob.value?.id) return
  activeJob.value = await getStackJob(activeJob.value.id)
}

async function copyLog() {
  try {
    await navigator.clipboard.writeText(logText.value)
    message.success('已复制全文')
  } catch {
    message.error('复制失败')
  }
}

function stopPoll() {
  if (pollTimer) window.clearInterval(pollTimer)
  pollTimer = undefined
  busy.value = false
}

function startPoll(jobId: string) {
  stopPoll()
  busy.value = true
  pollTimer = window.setInterval(async () => {
    try {
      const job = await getStackJob(jobId)
      activeJob.value = job
      if (['success', 'failed', 'cancelled'].includes(job.status)) {
        stopPoll()
        await loadJobs()
        if (job.status === 'success') message.success(`${job.action} 完成`)
        else if (job.status === 'cancelled') message.warning(`${job.action} 已停止`)
        else message.error(`${job.action} 失败，请查看日志`)
      }
    } catch {
      stopPoll()
    }
  }, 1200)
}

function buildOptions(action: StackAction) {
  const options: Record<string, unknown> = {}
  if (action.supportsImageMode) options.imageMode = imageMode.value
  if (action.argKey && moduleArg.value) options.module = moduleArg.value
  if (action.supportsBuildArch) options.buildArch = buildArch.value
  if (action.supportsParallelBuild) options.parallelBuild = parallelBuild.value
  return options
}

function askRun(action: StackAction) {
  if (!deploySupported.value) {
    message.warning(deployBlockDesc.value)
    return
  }
  if (action.dangerous && !allowDangerous.value) {
    message.warning('危险操作已禁用，请在 panel.env 设置 PANEL_ALLOW_DANGEROUS=1')
    return
  }
  if (action.argKey && !action.argOptional && !moduleArg.value) {
    message.warning(`请先选择${action.argLabel || '参数'}`)
    return
  }
  pendingMode = 'run'
  pendingAction = action
  const options = buildOptions(action)
  confirmTitle.value = `执行「${action.label}」`
  confirmDesc.value = '将在仓库根目录调用统一安装脚本，请确认形态与命令。'
  confirmWarn.value = action.dangerous
    ? '危险操作，可能删除容器或镜像。'
    : action.action === 'stop'
      ? '停止全部服务会导致平台暂时不可用。'
      : ''
  confirmOk.value = '确认执行'
  confirmDanger.value = !!action.dangerous || action.action === 'stop'
  const rows: { label: string; value: string }[] = [
    {
      label: '命令',
      value: `${scriptName.value} ${action.action}${moduleArg.value && action.argKey ? ` ${moduleArg.value}` : ''}`,
    },
    { label: '说明', value: action.desc },
    { label: '选择形态', value: profile.value },
  ]
  if (action.supportsImageMode) {
    rows.push({
      label: '镜像获取',
      value: desktopImageOnly.value || imageMode.value !== 'local' ? '拉取预构建' : '本地构建',
    })
  }
  if (action.supportsBuildArch) {
    rows.push({ label: '构建架构', value: buildArch.value })
  }
  if (action.supportsParallelBuild) {
    rows.push({ label: '并行构建', value: parallelBuild.value ? '是' : '否' })
  }
  if (Object.keys(options).length && action.argKey && moduleArg.value) {
    rows.push({ label: action.argLabel || '模块', value: String(moduleArg.value) })
  }
  confirmRows.value = rows
  confirmOpen.value = true
}

function askStop() {
  if (!activeJob.value?.id) {
    askKillAll()
    return
  }
  pendingMode = 'stop'
  pendingAction = null
  confirmTitle.value = '停止当前部署'
  confirmDesc.value = '将终止面板任务，并清理检测到的部署相关进程。'
  confirmWarn.value = '停止后当前任务会标记为 cancelled，可稍后重新执行 install/start。'
  confirmOk.value = '确认停止'
  confirmDanger.value = true
  confirmRows.value = [
    { label: '任务', value: activeJob.value.action },
    { label: 'ID', value: activeJob.value.id },
    { label: '状态', value: activeJob.value.status },
    { label: '宿主机进程', value: String(processes.value.length) },
  ]
  confirmOpen.value = true
}

async function doConfirm() {
  if (pendingMode === 'stop') {
    await doStop()
    return
  }
  if (pendingMode === 'kill-all') {
    await doKillProcesses(true)
    return
  }
  if (pendingMode === 'kill-one') {
    await doKillProcesses(false, pendingKillPid)
    return
  }
  await doRun()
}

async function doRun() {
  if (!pendingAction) return
  confirmLoading.value = true
  try {
    const job = await runStackAction({
      action: pendingAction.action,
      profile: profile.value,
      options: buildOptions(pendingAction),
    })
    autoScroll.value = true
    activeJob.value = job
    confirmOpen.value = false
    await loadJobs()
    startPoll(job.id)
  } finally {
    confirmLoading.value = false
    pendingAction = null
  }
}

async function doStop() {
  const id = activeJob.value?.id
  confirmLoading.value = true
  stopLoading.value = true
  try {
    if (id) {
      const job = await cancelStackJob(id)
      activeJob.value = job
    } else {
      await killDeployProcesses({ all: true })
    }
    confirmOpen.value = false
    await loadJobs()
    await loadProcesses()
    stopPoll()
    message.warning(id ? `${activeJob.value?.action || '任务'} 已停止` : '部署进程已清理')
  } finally {
    confirmLoading.value = false
    stopLoading.value = false
  }
}

onMounted(async () => {
  try {
    await loadMeta()
    await Promise.all([loadJobs(), showProcesses.value ? loadProcesses() : Promise.resolve()])
    const running = jobs.value.find((j) => j.status === 'running')
    if (running) {
      activeJob.value = await getStackJob(running.id)
      startPoll(running.id)
    }
    if (showProcesses.value) {
      procTimer = window.setInterval(() => {
        loadProcesses()
      }, 3000)
    }
  } catch {
    /* */
  }
})
onUnmounted(() => {
  stopPoll()
  if (procTimer) window.clearInterval(procTimer)
})
</script>

<style scoped>
.page {
  height: 100%;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 12px 16px !important;
}

.page.embedded {
  padding: 0 16px 12px !important;
}

.embed-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  flex-shrink: 0;
  min-height: 36px;
}

.embed-meta {
  font-size: 13px;
  color: var(--c-text-2);
}

.embed-meta code {
  font-size: 12px;
  color: var(--c-primary);
  background: var(--c-primary-bg);
  padding: 1px 6px;
  border-radius: 4px;
}

.page,
.col,
.jobs {
  scrollbar-width: none;
}

.page::-webkit-scrollbar,
.col::-webkit-scrollbar,
.jobs::-webkit-scrollbar {
  width: 0;
  height: 0;
  display: none;
}

.page-head {
  flex-shrink: 0;
  margin-bottom: 10px !important;
  min-height: 32px !important;
}

.page-head :deep(h1) {
  font-size: 18px !important;
  line-height: 24px !important;
}

.page-head :deep(p) {
  margin-top: 2px !important;
}

.page-head code {
  font-size: 12px;
  background: var(--c-fill);
  border: 1px solid var(--c-border);
  padding: 1px 6px;
  border-radius: 4px;
}

.deploy-block {
  flex-shrink: 0;
  margin-bottom: 10px;
}

.split {
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(0, 1.25fr);
  gap: 10px;
  align-items: stretch;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.col {
  min-height: 0;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: flex-start;
}

.col.left {
  overflow: auto;
  scrollbar-width: thin;
}

.jobs-panel :deep(.panel-hd),
.proc-panel :deep(.panel-hd),
.log-panel :deep(.panel-hd),
.opts :deep(.panel-hd) {
  height: 40px;
}

.opts-body {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.opt label {
  display: block;
  font-size: 12px;
  color: var(--c-text-3);
  margin-bottom: 4px;
}

.opt.check {
  padding-top: 2px;
}

.action-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  flex: 0 0 auto;
}

.action {
  border: 1px solid var(--c-border);
  background: var(--c-white);
  border-radius: var(--radius);
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  min-height: 64px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.action:hover:not(:disabled) {
  border-color: var(--c-primary-border);
  background: var(--c-primary-bg);
}

.action:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.action.danger:hover:not(:disabled) {
  border-color: #ffccc7;
  background: var(--c-danger-bg);
}

.action-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.action-title strong {
  font-size: 13px;
}

.action-title code {
  font-size: 11px;
  color: var(--c-primary);
  background: var(--c-primary-bg);
  padding: 1px 5px;
  border-radius: 4px;
}

.action span {
  font-size: 11px;
  color: var(--c-text-3);
  line-height: 16px;
}

.action .lock {
  color: var(--c-warning);
}

.jobs-panel,
.proc-panel,
.opts {
  flex: 0 0 auto;
  overflow: hidden;
}

.procs {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 10px;
  max-height: 132px;
  overflow: hidden;
}

.proc {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 8px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: var(--c-fill);
}

.proc-main {
  min-width: 0;
  flex: 1;
}

.proc-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.proc-title code {
  font-size: 11px;
  color: var(--c-primary);
  background: var(--c-primary-bg);
  padding: 1px 5px;
  border-radius: 4px;
}

.proc-cmd {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.jobs {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 10px;
  overflow-y: auto;
  max-height: 420px;
}

.job {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: var(--c-white);
  cursor: pointer;
  text-align: left;
  flex-shrink: 0;
}

.job.active {
  border-color: var(--c-primary-border);
  background: var(--c-primary-bg);
}

.job-name {
  font-weight: 600;
  font-size: 13px;
}

.log-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.progress-hint {
  padding: 8px 12px 0;
  flex-shrink: 0;
}

.live {
  margin: 8px 12px 12px;
  flex: 1 1 auto;
  min-height: 0;
  height: auto;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  scrollbar-width: thin;
  scrollbar-color: #555 transparent;
}

.live::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.live::-webkit-scrollbar-thumb {
  background: #555;
  border-radius: 4px;
}

.live::-webkit-scrollbar-track {
  background: transparent;
}

@media (max-width: 1100px) {
  .split,
  .action-grid {
    grid-template-columns: 1fr;
  }
  .page {
    overflow: auto;
  }
  .live {
    min-height: 280px;
  }
}
</style>
