<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="drawerTitle"
    width="1000"
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
            <Tag v-if="effectiveVersion" color="success">
              生效 {{ formatModelVersionDisplay(effectiveVersion) }}
            </Tag>
          </div>
          <p class="family-header__desc">
            同一模型的多个版本统一归为一个家族，对外默认使用生效版本；发布新版本后自动生效，也可随时手动切换回历史版本。
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
              <span class="version-text">{{ formatModelVersionDisplay(record.version || '1.0.0') }}</span>
              <Tag v-if="record.is_effective" color="success" class="version-tag">生效</Tag>
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
              <Popconfirm
                v-if="!record.is_effective"
                :title="`确认将 ${formatModelVersionDisplay(record.version || '1.0.0')} 设为对外生效版本？`"
                @confirm="handleActivate(record)"
              >
                <Button size="small" type="primary" ghost :loading="activatingId === record.id">
                  设为生效
                </Button>
              </Popconfirm>
            </template>
          </template>

          <template #expandedRowRender="{ record }">
            <div class="version-detail">
              <div class="version-detail__cover">
                <img :src="versionCover(record)" alt="模型封面" @error="onCoverError" />
              </div>
              <div class="version-detail__content">
                <div v-if="versionDesc(record)" class="version-detail__row">
                  <span class="version-detail__label">模型描述</span>
                  <span class="version-detail__text">{{ versionDesc(record) }}</span>
                </div>
                <div class="version-detail__row">
                  <span class="version-detail__label">模型文件</span>
                  <span class="version-detail__text">{{ versionFile(record) }}</span>
                </div>
                <div v-if="versionClasses(record).length" class="version-detail__row">
                  <span class="version-detail__label">检测类别</span>
                  <div class="version-detail__classes">
                    <Tag v-for="name in versionClasses(record)" :key="name">{{ name }}</Tag>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </Table>
      </div>
    </Spin>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, reactive, ref } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Button, Popconfirm, Spin, Table, Tag } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { activateModelFamilyVersion, getModelFamily } from '@/api/device/model';
import { formatModelVersionDisplay } from '../../utils/modelVersionUtils';
import { resolveModelImageDisplayUrl } from '@/utils/alertMinioImage';
import DEFAULT_MODEL_IMAGE from '@/assets/images/video/ai-task.png';

defineOptions({ name: 'ModelFamilyDrawer' });

interface FamilyVersion {
  id: number;
  name: string;
  version?: string;
  description?: string;
  image_url?: string;
  imageUrl?: string;
  model_path?: string;
  onnx_model_path?: string;
  class_names?: string[];
  classNames?: string[];
  is_effective?: boolean;
  is_latest?: boolean;
  map50?: number | null;
  annotated_count?: number | null;
  model_origin?: string;
  status?: number;
  created_at?: string;
}

const emit = defineEmits<{
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
  { title: '版本', dataIndex: 'version', width: 150 },
  { title: 'mAP50', dataIndex: 'map50', width: 80 },
  { title: '训练样本数', dataIndex: 'annotated_count', width: 90 },
  { title: '来源', dataIndex: 'model_origin', width: 96 },
  { title: '部署状态', dataIndex: 'status', width: 90 },
  { title: '发布时间', dataIndex: 'created_at', width: 140 },
  { title: '操作', dataIndex: 'action', width: 110 },
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
    createMessage.success(res?.msg || `已将 ${formatModelVersionDisplay(record.version || '1.0.0')} 设为生效版本`);
    await loadFamily();
    emit('changed');
  } catch (error: any) {
    createMessage.error(error?.response?.data?.msg || error?.message || '设置生效版本失败');
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
  if (Number.isNaN(date.getTime())) return '--';
  const pad = (n: number) => String(n).padStart(2, '0');
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    ` ${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
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

/** 展开区：版本描述（完整展示，不做截断） */
function versionDesc(record: any): string {
  return (record.description || '').trim();
}

/** 展开区：模型文件名（取 MinIO 路径最后一段） */
function versionFile(record: any): string {
  const path = String(record.model_path || record.onnx_model_path || '').split('?')[0];
  const name = path ? path.split('/').pop() : '';
  return name || '--';
}

/** 展开区：检测类别列表 */
function versionClasses(record: any): string[] {
  const names = record.classNames || record.class_names || [];
  return Array.isArray(names) ? names : [];
}

/** 展开区：版本封面图 */
function versionCover(record: any): string {
  const url = record.imageUrl || record.image_url;
  return url ? resolveModelImageDisplayUrl(url) : DEFAULT_MODEL_IMAGE;
}

function onCoverError(e: Event): void {
  const img = e.target as HTMLImageElement;
  if (img && img.src !== DEFAULT_MODEL_IMAGE) {
    img.src = DEFAULT_MODEL_IMAGE;
  }
}
</script>

<style lang="less" scoped>
.family-drawer-content {
  padding: 0 4px;
}

.family-header {
  margin-bottom: 14px;

  &__main {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }

  &__name {
    font-size: 16px;
    font-weight: 600;
    color: rgb(0 0 0 / 88%);
  }

  &__desc {
    margin: 6px 0 0;
    font-size: 12px;
    line-height: 1.6;
    color: rgb(0 0 0 / 45%);
  }
}

.version-text {
  font-weight: 600;
}

.version-tag {
  margin-left: 6px;
}

.version-detail {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  padding: 10px 16px 10px 44px;
  margin: 4px 0 12px;
  background: #fafafa;
  border-radius: 6px;

  &__cover {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    width: 120px;
    height: 76px;
    overflow: hidden;
    background: #fff;
    border: 1px solid #f0f0f0;
    border-radius: 4px;

    img {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }
  }

  &__content {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }

  &__row {
    display: flex;
    align-items: flex-start;
    font-size: 13px;
    line-height: 1.6;
  }

  &__label {
    flex-shrink: 0;
    width: 64px;
    color: rgb(0 0 0 / 45%);
  }

  &__text {
    flex: 1;
    min-width: 0;
    color: rgb(0 0 0 / 88%);
    word-break: break-all;
  }

  &__classes {
    display: flex;
    flex: 1;
    flex-wrap: wrap;
    gap: 4px;
    min-width: 0;
    max-height: 60px;
    overflow-y: auto;

    :deep(.ant-tag) {
      margin-right: 0;
    }
  }
}

.footer-buttons {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
