<template>
  <div>
    <!-- 测试结果录入 -->
    <BasicDrawer
      v-bind="$attrs"
      @register="registerTestResult"
      title="测试结果录入"
      width="1400"
      :showFooter="true"
      destroy-on-close
    >
      <div class="op-tip">
        <span>包名称：</span><b>{{ record.name }}</b>
        <span style="margin-left: 16px">版本：</span><b>{{ record.version }}</b>
      </div>
      <Form :label-col="{style: {width: '150px'}}" :wrapper-col="{span: 21}">
        <FormItem label="测试结论">
          <RadioGroup v-model:value="form.passed">
            <Radio :value="true">通过</Radio>
            <Radio :value="false">未通过</Radio>
          </RadioGroup>
        </FormItem>
        <FormItem label="备注">
          <Textarea v-model:value="form.remark" :maxlength="500" :rows="4" showCount
                    placeholder="测试说明（未通过时填写原因，便于修复后重新提交）"/>
        </FormItem>
      </Form>
      <template #footer>
        <div class="footer-buttons">
          <Button @click="closeTestResult">取消</Button>
          <Button type="primary" :loading="loading" @click="handleTestResult">提交</Button>
        </div>
      </template>
    </BasicDrawer>

    <!-- 发布 -->
    <BasicDrawer
      v-bind="$attrs"
      @register="registerPublish"
      title="发布OTA升级包"
      width="1400"
      :showFooter="true"
      destroy-on-close
    >
      <Spin :spinning="loading">
        <div class="op-tip">
          <span>包名称：</span><b>{{ record.name }}</b>
          <span style="margin-left: 16px">版本：</span><b>{{ record.version }}</b>
        </div>
        <Form :label-col="{style: {width: '150px'}}" :wrapper-col="{span: 21}">
          <FormItem v-if="needSkipVerify" label="免测发布">
            <Checkbox v-model:checked="form.skipVerify">
              跳过测试验证直接发布（测试未通过的包需要勾选）
            </Checkbox>
          </FormItem>
          <FormItem label="发布策略">
            <RadioGroup v-model:value="form.publishStrategy">
              <Radio :value="0">全量发布</Radio>
              <Radio :value="1">灰度发布</Radio>
            </RadioGroup>
          </FormItem>
          <template v-if="form.publishStrategy === 1">
            <FormItem label="灰度阶梯" required>
              <Select v-model:value="form.grayLadder" :options="grayLadderOptions" placeholder="请选择灰度阶梯"/>
            </FormItem>
            <FormItem v-if="form.grayLadder === 1" label="灰度设备" required>
              <Select
                v-model:value="scopeValues"
                mode="tags"
                placeholder="输入设备标识搜索或粘贴多个（回车确认）"
                :options="deviceOptions"
                @search="handleDeviceSearch"
                :filter-option="false"
                :token-separators="[',']"
              />
            </FormItem>
            <FormItem v-if="form.grayLadder === 2" label="灰度产品" required>
              <Select
                v-model:value="scopeValues"
                mode="multiple"
                placeholder="选择产品"
                :options="productOptions"
                optionFilterProp="label"
              />
            </FormItem>
          </template>
        </Form>
        <Alert
          message="全量发布将自动撤回同类型的其他已发布包；灰度发布仅命中范围内的设备可见。"
          type="info"
          show-icon
          class="op-alert"
        />
      </Spin>
      <template #footer>
        <div class="footer-buttons">
          <Button @click="closePublish">取消</Button>
          <Button type="primary" :loading="loading" @click="handlePublish">发布</Button>
        </div>
      </template>
    </BasicDrawer>

    <!-- 扩大灰度 / 灰度升阶 -->
    <BasicDrawer
      v-bind="$attrs"
      @register="registerGray"
      :title="grayMode === 'promote' ? '灰度升阶' : '扩大灰度范围'"
      width="1400"
      :showFooter="true"
      destroy-on-close
    >
      <Spin :spinning="loading">
        <div class="op-tip">
          <span>包名称：</span><b>{{ record.name }}</b>
          <span style="margin-left: 16px">当前阶梯：</span><b>{{ currentLadderLabel }}</b>
        </div>
        <Form :label-col="{style: {width: '150px'}}" :wrapper-col="{span: 21}">
          <FormItem v-if="grayMode === 'promote'" label="目标阶梯">
            <Select v-model:value="grayTargetLadder" disabled
                    :options="[{value: grayTargetLadder, label: GRAY_LADDER_MAP[grayTargetLadder]}]"/>
          </FormItem>
          <FormItem v-if="grayScopeType !== null" :label="grayScopeType === 1 ? '添加设备' : '添加产品'" required>
            <Select
              v-if="grayScopeType === 1"
              v-model:value="scopeValues"
              mode="tags"
              placeholder="输入设备标识搜索或粘贴多个（回车确认）"
              :options="deviceOptions"
              @search="handleDeviceSearch"
              :filter-option="false"
              :token-separators="[',']"
            />
            <Select
              v-else
              v-model:value="scopeValues"
              mode="multiple"
              placeholder="选择产品"
              :options="productOptions"
              optionFilterProp="label"
            />
          </FormItem>
          <FormItem v-else label="灰度范围">
            <span>目标为全量发布，无需选择范围。</span>
          </FormItem>
          <FormItem v-if="grayMode === 'promote' && grayTargetLadder !== 3" label="现有范围">
            <div class="scope-preview">
              <Tag v-for="item in existScopes" :key="item.scopeValue">{{ item.scopeValue }}</Tag>
              <span v-if="!existScopes.length">暂无</span>
            </div>
          </FormItem>
        </Form>
        <Alert
          v-if="grayMode === 'expand'"
          message="新选择的范围将与已有范围合并（同值自动去重）。"
          type="info"
          show-icon
          class="op-alert"
        />
        <Alert
          v-else
          message="仅支持相邻升阶：设备级 → 产品级 → 全量。升到产品级会替换为新选择的范围。"
          type="info"
          show-icon
          class="op-alert"
        />
      </Spin>
      <template #footer>
        <div class="footer-buttons">
          <Button @click="closeGray">取消</Button>
          <Button type="primary" :loading="loading" @click="handleGray">{{
              grayMode === 'promote' ? '升阶' : '确定'
            }}
          </Button>
        </div>
      </template>
    </BasicDrawer>

    <!-- 撤回 -->
    <BasicDrawer
      v-bind="$attrs"
      @register="registerWithdraw"
      title="撤回发布"
      width="1400"
      :showFooter="true"
      destroy-on-close
    >
      <div class="op-tip">
        <span>包名称：</span><b>{{ record.name }}</b>
        <span style="margin-left: 16px">版本：</span><b>{{ record.version }}</b>
      </div>
      <Form :label-col="{style: {width: '150px'}}" :wrapper-col="{span: 21}">
        <FormItem label="撤回原因" required>
          <Textarea v-model:value="form.reason" :maxlength="500" :rows="4" showCount
                    placeholder="请输入撤回原因（例如：发现严重缺陷、被新版本替换等）"/>
        </FormItem>
      </Form>
      <template #footer>
        <div class="footer-buttons">
          <Button @click="closeWithdraw">取消</Button>
          <Button danger type="primary" :loading="loading" @click="handleWithdraw">撤回</Button>
        </div>
      </template>
    </BasicDrawer>

    <!-- 升级统计 -->
    <BasicDrawer
      v-bind="$attrs"
      @register="registerStats"
      title="升级统计（近7天漏斗）"
      width="1400"
      :showFooter="false"
      destroy-on-close
    >
      <Spin :spinning="loading">
        <div class="op-tip">
          <span>包名称：</span><b>{{ record.name }}</b>
          <span style="margin-left: 16px">版本：</span><b>{{ record.version }}</b>
        </div>
        <Descriptions size="small" bordered :column="2" class="stats-desc">
          <DescriptionsItem label="命中设备数">{{ stats.checkHitCount ?? '-' }}</DescriptionsItem>
          <DescriptionsItem label="启动成功设备数">{{ stats.launchOkCount ?? '-' }}</DescriptionsItem>
          <DescriptionsItem label="升级覆盖率">
            {{ stats.coverage == null ? '-' : (stats.coverage * 100).toFixed(0) + '%' }}
          </DescriptionsItem>
          <DescriptionsItem label="安装成功率">
            {{ stats.successRate == null ? '-' : (stats.successRate * 100).toFixed(0) + '%' }}
          </DescriptionsItem>
        </Descriptions>

        <Divider orientation="left" plain>升级漏斗</Divider>
        <div v-for="item in stats.funnel || []" :key="item.phase" class="funnel-row">
          <span class="funnel-label">{{ item.phaseName }}</span>
          <Progress
            class="funnel-bar"
            :percent="funnelPercent(item.deviceCount)"
            :format="() => String(item.deviceCount)"
          />
        </div>

        <template v-if="(stats.errorTops || []).length">
          <Divider orientation="left" plain>Top 错误码</Divider>
          <Tag v-for="err in stats.errorTops" :key="err.errorCode" color="red">
            {{ err.errorCode || '未知错误' }} × {{ err.count }}
          </Tag>
        </template>

        <Alert
          v-if="stats.suggestPromote"
          :message="`覆盖率与样本已达阈值，建议升阶至「${GRAY_LADDER_MAP[stats.nextLadder] || '下一阶梯'}」`"
          type="success"
          show-icon
          class="op-alert"
        />
      </Spin>
    </BasicDrawer>
  </div>
</template>

<script lang="ts" setup>
import {computed, reactive, ref} from 'vue';
import {
  Alert,
  Checkbox,
  Divider,
  Form,
  FormItem,
  Progress,
  Radio,
  RadioGroup,
  Select,
  Descriptions,
  DescriptionsItem,
  Tag,
  Textarea,
} from 'ant-design-vue';
import {BasicDrawer, useDrawer} from '@/components/Drawer';
import {useMessage} from '@/hooks/web/useMessage';
import {
  expandGrayPackage,
  fetchGrayScopes,
  fetchUpgradeStats,
  promoteGrayPackage,
  publishPackage,
  withdrawPackage,
  testResultPackage,
} from '/@/api/device/ota';
import {getDeviceProfiles} from '@/api/device/product';
import {getDevicesList} from '@/api/device/devices';
import {GRAY_LADDER_MAP} from '../../Data';
import {Button} from '@/components/Button';

defineOptions({name: 'OtaPackageActions'});

const {createMessage} = useMessage();

const [registerTestResult, {openDrawer: openTestResult, closeDrawer: closeTestResult}] = useDrawer();
const [registerPublish, {openDrawer: openPublish, closeDrawer: closePublish}] = useDrawer();
const [registerGray, {openDrawer: openGray, closeDrawer: closeGray}] = useDrawer();
const [registerWithdraw, {openDrawer: openWithdraw, closeDrawer: closeWithdraw}] = useDrawer();
const [registerStats, {openDrawer: openStats}] = useDrawer();

const emits = defineEmits(['success']);

const loading = ref(false);
//当前操作的记录与动作
const record = ref<any>({});
const grayMode = ref<'expand' | 'promote'>('expand');
//升级统计结果
const stats = ref<any>({});

const form = reactive({
  passed: true,
  remark: '',
  skipVerify: false,
  publishStrategy: 0,
  grayLadder: undefined as number | undefined,
  reason: '',
});

const scopeValues = ref<string[]>([]);
const deviceOptions = ref<any[]>([]);
const productOptions = ref<any[]>([]);
const existScopes = ref<any[]>([]);

const grayLadderOptions = [
  {value: 1, label: '设备级（指定设备先行）'},
  {value: 2, label: '产品级（指定产品先行）'},
];

//发布时是否允许勾选跳过验证
const needSkipVerify = computed(() => record.value.testPassed !== 1);

//扩大/升阶范围类型：null 表示目标全量无范围
const grayScopeType = computed<number | null>(() => {
  if (grayMode.value === 'expand') {
    return record.value.grayLadder === 1 ? 1 : 2;
  }
  return grayTargetLadder.value === 3 ? null : grayTargetLadder.value === 2 ? 2 : 1;
});

//灰度升阶的目标阶梯（相邻下一阶）
const grayTargetLadder = computed<number>(() => {
  const cur = Number(record.value.grayLadder || 1);
  return Math.min(cur + 1, 3);
});

const currentLadderLabel = computed(() => GRAY_LADDER_MAP[record.value.grayLadder] || '-');

let maxFunnelCount = 0;

function funnelPercent(count: number) {
  if (!maxFunnelCount) {
    return 0;
  }
  return Math.round((count / maxFunnelCount) * 100);
}

async function handleDeviceSearch(keyword: string) {
  try {
    const res = await getDevicesList({
      deviceIdentification: keyword,
      pageNo: 1,
      pageSize: 20,
    });
    deviceOptions.value = (res.data || []).map((d) => ({
      label: d.deviceIdentification + (d.deviceName ? `（${d.deviceName}）` : ''),
      value: d.deviceIdentification,
    }));
  } catch (e) {
    console.error(e);
  }
}

async function loadProductOptions() {
  if (productOptions.value.length) {
    return;
  }
  try {
    const res = await getDeviceProfiles({page: 1, pageSize: 200});
    productOptions.value = (res.data || []).map((p) => ({
      label: p.productName,
      value: p.productIdentification,
    }));
  } catch (e) {
    console.error(e);
  }
}

function buildScopes(scopeType: number) {
  return (scopeValues.value || [])
    .filter((v) => !!String(v).trim())
    .map((v) => ({scopeType, scopeValue: String(v).trim()}));
}

//外部入口：打开对应操作抽屉
function open(action: string, rec: any) {
  record.value = rec || {};
  //重置表单
  form.passed = true;
  form.remark = '';
  form.skipVerify = false;
  form.publishStrategy = 0;
  form.grayLadder = undefined;
  form.reason = '';
  scopeValues.value = [];
  deviceOptions.value = [];
  existScopes.value = [];
  switch (action) {
    case 'test-result':
      openTestResult(true);
      break;
    case 'publish':
      //灰度发布可能选择产品级阶梯，提前加载产品选项
      loadProductOptions();
      openPublish(true);
      break;
    case 'expand':
    case 'promote':
      grayMode.value = action;
      loadExistScopes(rec.id);
      loadProductOptions();
      openGray(true);
      break;
    case 'withdraw':
      openWithdraw(true);
      break;
    case 'stats':
      loadStats(rec.id);
      openStats(true);
      break;
  }
}

defineExpose({open});

async function loadExistScopes(pkgId: number) {
  try {
    const res = await fetchGrayScopes(pkgId);
    existScopes.value = res?.data || [];
    loadProductOptions();
  } catch (e) {
    console.error(e);
  }
}

async function loadStats(pkgId: number) {
  loading.value = true;
  try {
    const res = await fetchUpgradeStats(pkgId);
    const funnel = res?.funnel || [];
    maxFunnelCount = funnel.reduce((max, f) => Math.max(max, f.deviceCount || 0), 0);
    stats.value = res || {};
  } catch (e) {
    console.error(e);
    createMessage.error('获取升级统计失败');
  } finally {
    loading.value = false;
  }
}

async function handleTestResult() {
  loading.value = true;
  try {
    await testResultPackage({
      id: record.value.id,
      passed: form.passed,
      remark: form.remark,
    });
    createMessage.success(form.passed ? '测试通过已记录' : '测试未通过已记录，可修复后重新提交');
    closeTestResult();
    emits('success');
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function handlePublish() {
  const payload: any = {
    id: record.value.id,
    skipVerify: needSkipVerify.value && form.skipVerify,
    publishStrategy: form.publishStrategy,
  };
  if (form.publishStrategy === 1) {
    if (!form.grayLadder) {
      createMessage.warning('请选择灰度阶梯');
      return;
    }
    payload.grayLadder = form.grayLadder;
    const scopeType = form.grayLadder === 1 ? 1 : 2;
    const scopes = buildScopes(scopeType);
    if (!scopes.length) {
      createMessage.warning(form.grayLadder === 1 ? '请至少输入一个设备标识' : '请至少选择一个产品');
      return;
    }
    payload.grayScopes = scopes;
  }
  loading.value = true;
  try {
    await publishPackage(payload);
    createMessage.success('发布成功');
    closePublish();
    emits('success');
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function handleGray() {
  let api = expandGrayPackage;
  const payload: any = {id: record.value.id};
  if (grayMode.value === 'promote') {
    api = promoteGrayPackage;
    payload.targetLadder = grayTargetLadder.value;
  }
  if (grayScopeType.value !== null) {
    const scopes = buildScopes(grayScopeType.value);
    if (!scopes.length) {
      createMessage.warning(grayScopeType.value === 1 ? '请至少输入一个设备标识' : '请至少选择一个产品');
      return;
    }
    payload.grayScopes = scopes;
  }
  loading.value = true;
  try {
    await api(payload);
    createMessage.success(grayMode.value === 'promote' ? '灰度升阶成功' : '扩大灰度范围成功');
    closeGray();
    emits('success');
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function handleWithdraw() {
  if (!form.reason || !form.reason.trim()) {
    createMessage.warning('请填写撤回原因');
    return;
  }
  loading.value = true;
  try {
    await withdrawPackage({id: record.value.id, reason: form.reason.trim()});
    createMessage.success('撤回成功');
    closeWithdraw();
    emits('success');
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}
</script>

<style lang="less" scoped>
.op-tip {
  margin-bottom: 16px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;

  span {
    color: #888;
  }
}

.op-alert {
  margin-top: 8px;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.stats-desc {
  margin-bottom: 8px;
}

.funnel-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;

  .funnel-label {
    width: 96px;
    text-align: right;
    padding-right: 8px;
    color: #666;
  }

  .funnel-bar {
    flex: 1;
  }
}

.scope-preview {
  max-height: 120px;
  overflow: auto;
}
</style>
