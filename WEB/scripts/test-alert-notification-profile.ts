import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { parse } from '@vue/compiler-sfc';
import ts from 'typescript';

// 告警通知只由 iot-message 下发；部署脚本不启动它的形态，前端不给算法任务配置通知。
const deployProfileSh = readFileSync(
  resolve(process.cwd(), '../.scripts/docker/deploy_profile.sh'),
  'utf8',
);

function skippedDeviceServices(profile: string): string[] {
  const body = /device_skipped_services\(\) \{([\s\S]*?)\n\}/.exec(deployProfileSh)?.[1] ?? '';
  const branch = new RegExp(`\\n\\s*${profile}\\)\\s*\\n([\\s\\S]*?);;`).exec(body)?.[1] ?? '';
  return [...branch.matchAll(/skips\+=\(([^)]*)\)/g)].flatMap(([, list]) => (list ?? '').trim().split(/\s+/));
}

const transpile = (source: string) =>
  ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;

// deployProfile.ts 读的是 Vite 注入的 import.meta.env，这里换成入参后执行。
const deployProfileJs = transpile(
  readFileSync(resolve(process.cwd(), 'src/utils/deployProfile.ts'), 'utf8').replace(
    /import\.meta\.env/g,
    '__viteEnv',
  ),
);

type DeployProfileModule = typeof import('../src/utils/deployProfile');

function loadDeployProfile(viteEnv: Record<string, string>): DeployProfileModule {
  const exports = {} as DeployProfileModule;
  new Function('exports', '__viteEnv', deployProfileJs)(exports, viteEnv);
  return exports;
}

// [VITE_GLOB_DEPLOY_PROFILE, VITE_GLOB_EDGE_STANDALONE, 是否给任务配置通知]，取值与 deploy_profile.sh 写入 WEB/.env 的一致。
const profiles: Array<[string, string, boolean]> = [
  ['mini', 'true', false], // edge 单体：前端与 mini 共用裁剪
  ['mini', 'false', false],
  ['standard', 'false', true],
  ['full', 'false', true],
  ['', '', true], // 缺省按 full
];

// 部署脚本与前端必须对“哪些形态有通知服务”保持一致。
for (const name of ['edge', 'mini', 'standard', 'full']) {
  assert.equal(
    skippedDeviceServices(name).includes('iot-message'),
    name === 'edge' || name === 'mini',
    `${name} 形态是否部署 iot-message 与前端裁剪不一致`,
  );
}

const filename = resolve(
  process.cwd(),
  'src/views/camera/components/AlgorithmTask/AlgorithmTaskModal.vue',
);
const source = readFileSync(filename, 'utf8');
const { descriptor, errors } = parse(source, { filename });
assert.deepEqual(errors, [], 'AlgorithmTaskModal.vue must remain a valid Vue SFC');
const script = descriptor.scriptSetup?.content ?? '';
assert.match(script, /import \{ isAlertNotificationEnabled \} from '@\/utils\/deployProfile';/);

// 只认表单定义里的多行条目；updateSchema 的单行补丁不算。
function schemaEntry(field: string): string {
  const marker = `\n      field: '${field}',\n`;
  const start = script.indexOf(marker);
  assert.notEqual(start, -1, `任务表单缺少字段 ${field}`);
  assert.equal(script.indexOf(marker, start + 1), -1, `任务表单字段 ${field} 重复定义`);
  const next = script.indexOf("\n    {\n      field: '", start + marker.length);
  return script.slice(start, next === -1 ? script.length : next);
}

function scriptFunction(name: string): string {
  const body = new RegExp(`^function ${name}\\([\\s\\S]*?^\\}`, 'm').exec(script)?.[0];
  assert.ok(body, `任务表单缺少函数 ${name}`);
  return body;
}

// 顶层的 const 箭头函数：从声明起到列首的 “};” 止。
function scriptArrowFunction(name: string): string {
  const start = script.indexOf(`\nconst ${name} = async (`);
  assert.notEqual(start, -1, `任务表单缺少函数 ${name}`);
  const end = script.indexOf('\n};', start);
  assert.notEqual(end, -1, `函数 ${name} 没有正常结束`);
  return script.slice(start, end + '\n};'.length);
}

const taskForm: {
  alertNotificationRequested(values: Record<string, any>): boolean;
  buildNotificationChannels(
    selectedTemplates: Record<string, string | number>,
    templatesByChannel: Record<string, any[]>,
    savedChannels: any[],
  ): Array<{ method: string; template_id: string | number; template_name: string }>;
} = new Function(
  `${transpile(
    `${scriptFunction('baseTaskType')}\n${scriptFunction('alertNotificationRequested')}\n${scriptFunction('buildNotificationChannels')}`,
  )}
return { baseTaskType, alertNotificationRequested, buildNotificationChannels };`,
)();

const NOTIFICATION_FIELDS = [
  'alert_notification_enabled',
  'alarm_suppress_time',
  'notification_channels',
  'notification_templates',
];
const NOTICE_FIELD = 'alert_notification_unavailable';

// 取出字段真实的显示条件并执行；表单库调用时传入的是 { values, model, … }。
function ifShowOf(
  field: string,
  alertNotificationRequested: (values: Record<string, any>) => boolean,
  isAlertNotificationEnabled: () => boolean,
): (params: { values: Record<string, any> }) => boolean {
  const entry = schemaEntry(field);
  const expression = /ifShow: \(\{ values \}\) =>\s*([\s\S]*?),?\s*\n\s*\},/.exec(entry)?.[1];
  assert.ok(expression, `字段 ${field} 的显示条件应基于表单值`);
  return new Function(
    'alertNotificationRequested',
    'isAlertNotificationEnabled',
    `return ${transpile(`({ values }) => (${expression}\n)`)};`,
  )(alertNotificationRequested, isAlertNotificationEnabled);
}

const expectVisible = (fields: string[]) =>
  Object.fromEntries([...NOTIFICATION_FIELDS, NOTICE_FIELD].map((field) => [field, fields.includes(field)]));

// 执行弹窗里真实的 loadTemplates，只把模板接口换成记录调用的替身。
function loadTemplatesOf(isAlertNotificationEnabled: () => boolean) {
  const requests: Array<{ msgType: number }> = [];
  const templates = { value: {} as Record<string, any[]> };
  const templateLoading = { value: {} as Record<string, boolean> };
  const loadTemplates = new Function(
    'templates',
    'templateLoading',
    'channelToMsgType',
    'notifyTemplateQueryByType',
    'getChannelLabel',
    'isAlertNotificationEnabled',
    `${transpile(scriptArrowFunction('loadTemplates'))}\nreturn loadTemplates;`,
  )(
    templates,
    templateLoading,
    { ding: 6 },
    (params: { msgType: number }) => {
      requests.push(params);
      return Promise.resolve({ code: 0, data: [{ id: 'tpl-1', name: '钉钉模板' }] });
    },
    (channel: string) => channel,
    isAlertNotificationEnabled,
  );
  return {
    loadTemplates,
    requests,
    templates: templates.value,
    templateLoading: templateLoading.value,
  };
}

const templateLoadingChecks: Array<Promise<void>> = [];

for (const [profile, edgeStandalone, notification] of profiles) {
  const { isAlertNotificationEnabled } = loadDeployProfile({
    VITE_GLOB_DEPLOY_PROFILE: profile,
    VITE_GLOB_EDGE_STANDALONE: edgeStandalone,
  });
  const label = `profile=${profile || '(unset)'} edgeStandalone=${edgeStandalone}`;
  const visible = (values: Record<string, any>) =>
    Object.fromEntries(
      [...NOTIFICATION_FIELDS, NOTICE_FIELD].map((field) => [
        field,
        ifShowOf(field, taskForm.alertNotificationRequested, isAlertNotificationEnabled)({ values }),
      ]),
    );

  // 开启告警事件并打开通知开关：有通知服务时给出配置项，否则只留一行说明。
  assert.deepEqual(
    visible({
      task_mode: 'snap_cpp',
      alert_event_enabled: true,
      alert_notification_enabled: true,
      notification_channels: ['ding'],
    }),
    notification ? expectVisible(NOTIFICATION_FIELDS) : expectVisible([NOTICE_FIELD]),
    label,
  );
  // 未开启告警事件：配置与说明都不出现。
  assert.deepEqual(
    visible({ task_mode: 'patrol', alert_event_enabled: false, alert_notification_enabled: false }),
    expectVisible([]),
    label,
  );
  // 通知开关关闭：依赖它的三项不出现。
  assert.deepEqual(
    visible({ task_mode: 'realtime', alert_event_enabled: true, alert_notification_enabled: false }),
    notification ? expectVisible(['alert_notification_enabled']) : expectVisible([NOTICE_FIELD]),
    label,
  );
  // 告警事件已关闭、通知开关还留着旧值：配置与说明都不出现。
  assert.deepEqual(
    visible({
      task_mode: 'snap',
      alert_event_enabled: false,
      alert_notification_enabled: true,
      notification_channels: ['ding'],
    }),
    expectVisible([]),
    label,
  );

  // 编辑一个已带通知配置的任务会逐个渠道加载模板：没有通知服务的形态不发请求，也不进入加载态。
  templateLoadingChecks.push(
    (async () => {
      const { loadTemplates, requests, templates, templateLoading } = loadTemplatesOf(isAlertNotificationEnabled);
      await loadTemplates('ding');
      assert.deepEqual(requests, notification ? [{ msgType: 6 }] : [], label);
      assert.equal(Boolean(templateLoading.ding), false, `${label} 加载结束后不应停留在加载态`);
      assert.equal(templates.ding?.length, notification ? 1 : undefined, label);
    })(),
  );
}

// 提交时的通知渠道：模板列表没加载到时，任务上已保存的渠道配置原样写回。
const savedChannels = [
  { method: 'ding', template_id: 'tpl-1', template_name: '钉钉模板' },
  { method: 'sms', template_id: 7, template_name: '短信模板' },
];
assert.deepEqual(taskForm.buildNotificationChannels({ ding: 'tpl-1', sms: 7 }, {}, savedChannels), savedChannels);
// 选了另一个模板而列表里没有它：不把旧模板的名字带过去。
assert.deepEqual(
  taskForm.buildNotificationChannels(
    { ding: 'tpl-2' },
    { ding: [{ id: 'tpl-1', name: '旧模板' }] },
    [{ method: 'ding', template_id: 'tpl-1', template_name: '旧模板' }],
  ),
  [{ method: 'ding', template_id: 'tpl-2', template_name: '' }],
);
// 列表里有所选模板时以列表为准。
assert.deepEqual(
  taskForm.buildNotificationChannels(
    { ding: 'tpl-2' },
    { ding: [{ id: 'tpl-1', name: '旧模板' }, { id: 'tpl-2', name: '新模板' }] },
    [{ method: 'ding', template_id: 'tpl-1', template_name: '旧模板' }],
  ),
  [{ method: 'ding', template_id: 'tpl-2', template_name: '新模板' }],
);
// 没选模板的渠道不提交；表单清空后的运行时值是 undefined / null，渠道映射的类型上体现不出来。
const withClearedChannel = { ding: undefined, sms: null, email: 'tpl-9' } as unknown as Record<
  string,
  string | number
>;
assert.deepEqual(taskForm.buildNotificationChannels(withClearedChannel, {}, savedChannels), [
  { method: 'email', template_id: 'tpl-9', template_name: '' },
]);
// 提交逻辑必须走这个函数，而不是另写一份。
assert.equal(script.split('buildNotificationChannels(').length - 1, 2);

assert.match(schemaEntry(NOTICE_FIELD), /当前部署形态未部署通知服务/);

// 本文件按 CommonJS 运行，不支持顶层 await。
Promise.all(templateLoadingChecks).then(
  () => console.log('alert notification profile contract: ok'),
  (error) => {
    console.error(error);
    process.exitCode = 1;
  },
);
