<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="drawerTitle"
    width="1400"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    destroy-on-close
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleClose">关闭</Button>
      </div>
    </template>

    <Spin :spinning="loading">
      <div class="family-drawer-content">
        <div class="family-header">
          <div class="family-header__main">
            <span class="family-header__name">{{ familyInfo.family_name || recordName }}</span>
            <Tag color="blue">{{ familyInfo.total ?? 0 }} 个版本</Tag>
            <Tag v-if="effectiveVersion" color="success">当前生效 v{{ effectiveVersion }}</Tag>
          </div>
          <p class="family-header__desc">
            同一模型的多版本归并为一个模型家族，对外只体现一个模型：默认使用生效版本（发布新版本时自动切换为最新版本），
            也可激活任意历史版本回退。激活不影响其它版本的权重文件。
          </p>
        </div>

        <Table
          :columns="versionColumns"
          :data-source="familyInfo.versions || []"
          row-key="id"
          :pagination="false"
          size="middle"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'version'">
              <span class="version-text">v{{ record.version || '1.0.0' }}</span>
              <Tag v-if="record.is_effective" color="success" class="version-tag">当前生效</Tag>
              <Tag v-else-if="record.is_latest" color="blue" class="version-tag">最新</Tag>
            </template>
            <template v-else-if="column.dataIndex === 'map50'">
              {{ formatMap50(record.map50) }}
            </template>
            <template v-else-if="column.dataIndex === 'annotated_count'">
              {{ record.annotated_count ?? '--' }}
            </template>
            <template v-else-if="column.dataIndex === 'model_origin'">
              <Tag :color="originMeta(record.model_origin).color">
                {{ originMeta(record.model_origin).label }}
              </Tag>
            </template>
            <template v-else-if="column.dataIndex === 'status'">
              {{ statusLabel(record.status) }}
            </template>
            <template v-else-if="column.dataIndex === 'created_at'">
              {{ formatDateTime(record.created_at) }}
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <Space :size="8">
                <Popconfirm
                  v-if="!record.is_effective"
                  :title="`激活后对外默认使用 v${record.version || '1.0.0'}，是否继续？`"
                  @confirm="handleActivate(record)"
                >
                  <Button size="small" type="primary" ghost :loading="activatingId === record.id">
                    激活此版本
                  </Button>
                </Popconfirm>
                <Tag v-else color="success">生效中</Tag>
                <Button size="small" @click="emit('view', record)">查看详情</Button>
              </Space>
            </template>
          </template>
        </Table>
      </div>
    </Spin>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, reactive, ref } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Button, Popconfirm, Space, Spin, Table, Tag } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { activateModelFamilyVersion, getModelFamily } from '@/api/device/model';

defineOptions({ name: 'ModelFamilyDrawer' });

interface FamilyVersion {
  id: number;
  name: string;
  version?: string;
  is_effective?: boolean;
  is_latest?: boolean;
  map50?: number | null;
  annotated_count?: number | null;
  model_origin?: string;
  status?: number;
  created_at?: string;
}

const emit = defineEmits<{
  (e: 'view', record: any): void;
  (e: 'changed'): void;
}>();

const { createMessage } = useMessage();

const loading = ref(false);
const activatingId = ref<number | null>(null);
const anchorModelId = ref<number | null>(null);
const recordName = ref('');
const familyInfo = reactive<{
  family_key: string;
  family_name: string;
  effective_id: number | null;
  total: number;
  versions: FamilyVersion[];
}>({ family_key: '', family_name: '', effective_id: null, total: 0, versions: [] });

const drawerTitle = computed(() => `版本管理 · ${familyInfo.family_name || recordName.value}`);
const effectiveVersion = computed(
  () => familyInfo.versions?.find((v) => v.is_effective)?.version,
);

const versionColumns = [
  { title: '版本', dataIndex: 'version', width: 170 },
  { title: 'mAP50', dataIndex: 'map50', width: 90 },
  { title: '训练样本数', dataIndex: 'annotated_count', width: 100 },
  { title: '来源', dataIndex: 'model_origin', width: 100 },
  { title: '部署状态', dataIndex: 'status', width: 90 },
  { title: '发布时间', dataIndex: 'created_at', width: 150 },
  { title: '操作', dataIndex: 'action', width: 190 },
];

const [register, { closeDrawer }] = useDrawerInner(async (data: { record?: any }) => {
  recordName.value = data?.record?.name || '';
  anchorModelId.value = data?.record?.id ?? null;
  await loadFamily();
});

async function loadFamily(): Promise<void> {
  if (!anchorModelId.value) return;
  loading.value = true;
  try {
    const res: any = await getModelFamily(anchorModelId.value);
    const payload = res?.data ?? res;
    familyInfo.family_key = payload?.family_key || '';
    familyInfo.family_name = payload?.family_name || recordName.value;
    familyInfo.effective_id = payload?.effective_id ?? null;
    familyInfo.total = payload?.total ?? payload?.versions?.length ?? 0;
    familyInfo.versions = payload?.versions || [];
  } catch (error: any) {
    createMessage.error(error?.response?.data?.msg || error?.message || '模型版本加载失败');
  } finally {
    loading.value = false;
  }
}

async function handleActivate(record: any): Promise<void> {
  activatingId.value = record.id;
  try {
    const res: any = await activateModelFamilyVersion(record.id);
    createMessage.success(res?.msg || `已激活 v${record.version || '1.0.0'}`);
    await loadFamily();
    emit('changed');
  } catch (error: any) {
    createMessage.error(error?.response?.data?.msg || error?.message || '激活失败');
  } finally {
    activatingId.value = null;
  }
}

function handleClose(): void {
  closeDrawer();
}

function formatMap50(value?: number | null): string {
  if (value === null || value === undefined) return '--';
  return (Number(value) * 100).toFixed(1) + '%';
}

function formatDateTime(dateString?: string): string {
  if (!dateString) return '--';
  const date = new Date(dateString);
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function statusLabel(status?: number): string {
  const map: Record<number, string> = { 0: '未部署', 1: '已部署', 2: '训练中', 3: '已下线' };
  return map[Number(status ?? 0)] ?? '未部署';
}

function originMeta(origin?: string): { label: string; color: string } {
  const map: Record<string, { label: string; color: string }> = {
    upload: { label: '手动上传', color: 'default' },
    auto_label: { label: '自动标注', color: 'success' },
    smart_label: { label: '智能标注', color: 'geekblue' },
    train: { label: '训练任务', color: 'processing' },
    import: { label: '导入', color: 'warning' },
  };
  return map[origin || 'upload'] ?? map.upload;
}
</script>

<style lang="less" scoped>
.family-drawer-content {
  padding: 0 4px;
}

.family-header {
  margin-bottom: 16px;

  &__main {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  &__name {
    font-size: 16px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.88);
  }

  &__desc {
    margin: 8px 0 0;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    line-height: 1.6;
  }
}

.version-text {
  font-weight: 600;
}

.version-tag {
  margin-left: 6px;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
