<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    width="1280"
    placement="right"
    :showFooter="false"
    :destroyOnClose="true"
  >
    <div v-if="person" class="person-detail-drawer">
      <div class="detail-header">
        <div class="header-main">
          <h2 class="person-name">{{ person.person_name }}</h2>
          <div class="person-meta">
            <a-tag v-if="person.person_code">{{ person.person_code }}</a-tag>
            <a-tag :color="person.is_enabled ? 'success' : 'default'">
              {{ person.is_enabled ? '启用' : '停用' }}
            </a-tag>
            <span>{{ entries.length }} 张人脸照片</span>
          </div>
        </div>
        <div class="header-actions">
          <Button type="primary" ghost @click="handleShowTrajectory">
            <template #icon><EnvironmentOutlined /></template>
            出现轨迹
          </Button>
          <Button type="primary" @click="handleAddPhoto">
            <template #icon><PlusOutlined /></template>
            添加照片
          </Button>
        </div>
      </div>

      <div class="detail-body">
        <div class="cover-panel">
          <div class="panel-label">当前封面</div>
          <div class="cover-preview">
            <img :src="coverUrl" alt="封面" @error="onCoverError" />
          </div>
          <p class="cover-tip">点击下方任意照片可设为封面</p>
        </div>

        <div class="photos-panel">
          <div class="panel-label">全部照片</div>
          <a-spin :spinning="loading">
            <div class="photo-grid">
              <div
                v-for="entry in entries"
                :key="entry.id"
                class="photo-item"
                :class="{ 'is-cover': entry.id === person.cover_entry_id }"
              >
                <div class="photo-thumb" @click="previewImage(entry.image_url)">
                  <img :src="faceImageUrl(entry.image_url) || fallbackImg" alt="" @error="onThumbError" />
                  <a-tag v-if="entry.id === person.cover_entry_id" color="blue" class="cover-tag">封面</a-tag>
                </div>
                <div class="photo-info">
                  <div class="photo-name">{{ entry.person_name }}</div>
                  <div class="photo-time">{{ entry.created_at || '-' }}</div>
                </div>
                <div class="photo-actions">
                  <Button
                    v-if="entry.id !== person.cover_entry_id"
                    size="small"
                    type="link"
                    :loading="settingCoverId === entry.id"
                    @click="handleSetCover(entry.id)"
                  >
                    设为封面
                  </Button>
                  <Button size="small" type="link" @click="handleEdit(entry)">编辑</Button>
                  <PopConfirmButton
                    size="small"
                    type="link"
                    danger
                    title="确认删除该照片？"
                    @confirm="handleDelete(entry.id)"
                  >
                    删除
                  </PopConfirmButton>
                </div>
              </div>
            </div>
            <a-empty v-if="!loading && entries.length === 0" description="暂无照片" />
          </a-spin>
        </div>
      </div>
    </div>

    <FaceEntryModal @register="registerEntryModal" @success="handleEntrySuccess" />
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { PlusOutlined, EnvironmentOutlined } from '@ant-design/icons-vue';
import { BasicDrawer, useDrawer, useDrawerInner } from '@/components/Drawer';
import { useMessage } from '@/hooks/web/useMessage';
import {
  deleteFaceEntry,
  getFacePerson,
  setFacePersonCover,
  unwrapFaceApiEntity,
  resolveFaceImageDisplayUrl,
  type FaceEntry,
  type FaceLibrary,
  type FacePerson,
} from '@/api/device/face_library';
import FaceEntryModal from '@/views/camera/components/FaceLibrary/FaceEntryModal.vue';
import DEFAULT_FACE_IMAGE from '@/assets/images/video/snap-task.png';
import { Button, PopConfirmButton } from '@/components/Button'
defineOptions({ name: 'PersonDetailDrawer' });

const emit = defineEmits(['success', 'register']);
const { createMessage } = useMessage();

const library = ref<FaceLibrary | null>(null);
const person = ref<FacePerson | null>(null);
const entries = ref<FaceEntry[]>([]);
const loading = ref(false);
const settingCoverId = ref<number | null>(null);

const fallbackImg =
  'data:image/svg+xml,' +
  encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120"><rect fill="#f0f0f0" width="120" height="120"/></svg>');

const [registerEntryModal, { openDrawer: openEntryModal }] = useDrawer();
const router = useRouter();

const coverUrl = computed(() => {
  const coverId = person.value?.cover_entry_id;
  const cover = entries.value.find((e) => e.id === coverId);
  return (
    faceImageUrl(cover?.image_url)
    || faceImageUrl(person.value?.cover_image_url)
    || DEFAULT_FACE_IMAGE
  );
});

function faceImageUrl(url?: string | null) {
  return resolveFaceImageDisplayUrl(url);
}

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  library.value = data?.library || null;
  person.value = data?.person || null;
  setDrawerProps({ title: `人员详情 · ${person.value?.person_name || ''}` });
  await loadDetail();
});

async function loadDetail() {
  if (!person.value?.id) return;
  loading.value = true;
  try {
    const res = await getFacePerson(person.value.id, true);
    const data = unwrapFaceApiEntity(res);
    if (data) {
      person.value = data;
      entries.value = data.entries || [];
    }
  } catch (e: any) {
    createMessage.error(e?.message || '加载人员详情失败');
    entries.value = [];
  } finally {
    loading.value = false;
  }
}

function onCoverError(e: Event) {
  (e.target as HTMLImageElement).src = DEFAULT_FACE_IMAGE;
}

function onThumbError(e: Event) {
  (e.target as HTMLImageElement).src = fallbackImg;
}

function previewImage(url?: string) {
  const resolved = faceImageUrl(url);
  if (resolved) window.open(resolved, '_blank');
}

async function handleSetCover(entryId: number) {
  if (!person.value?.id) return;
  settingCoverId.value = entryId;
  try {
    const res = await setFacePersonCover(person.value.id, entryId);
    const data = unwrapFaceApiEntity(res);
    if (data) person.value = data;
    createMessage.success('封面已更新');
    emit('success');
  } catch (e: any) {
    createMessage.error(e?.message || '设置封面失败');
  } finally {
    settingCoverId.value = null;
  }
}

function handleAddPhoto() {
  openEntryModal(true, {
    type: 'create',
    library: library.value,
    person: person.value,
    addToPerson: true,
  });
}

/** 打开该人员的"出现轨迹"：跳转告警页地图分布，在地图上绘制该人当天的出现点位 */
function handleShowTrajectory() {
  if (!person.value?.person_name) return;
  router.push({
    path: '/alert',
    query: {
      tab: '1',
      trajectory_person: person.value.person_name,
      trajectory_date: new Date().toISOString().slice(0, 10),
    },
  });
}

function handleEdit(entry: FaceEntry) {
  openEntryModal(true, { type: 'edit', library: library.value, record: entry });
}

async function handleDelete(entryId: number) {
  try {
    await deleteFaceEntry(entryId);
    createMessage.success('删除成功');
    emit('success');
    await loadDetail();
    if (entries.value.length === 0) {
      closeDrawer();
    }
  } catch (e: any) {
    createMessage.error(e?.message || '删除失败');
  }
}

function handleEntrySuccess() {
  emit('success');
  loadDetail();
}
</script>

<style lang="less" scoped>
.person-detail-drawer {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;

  .person-name {
    margin: 0 0 8px;
    font-size: 22px;
    font-weight: 600;
  }

  .person-meta {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 13px;
    color: rgba(0, 0, 0, 0.45);
  }
}

.detail-body {
  display: flex;
  gap: 24px;
  align-items: flex-start;

  @media (max-width: 900px) {
    flex-direction: column;
  }
}

.panel-label {
  font-size: 14px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.85);
  margin-bottom: 12px;
}

.cover-panel {
  flex-shrink: 0;
  width: 280px;

  .cover-preview {
    width: 280px;
    height: 340px;
    border-radius: 10px;
    overflow: hidden;
    background: #f5f5f5;
    border: 1px solid #f0f0f0;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }

  .cover-tip {
    margin: 10px 0 0;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
  }
}

.photos-panel {
  flex: 1;
  min-width: 0;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.photo-item {
  border: 2px solid transparent;
  border-radius: 8px;
  padding: 10px;
  background: #fafafa;
  transition: border-color 0.2s, box-shadow 0.2s;

  &.is-cover {
    border-color: #266cfb;
    background: #f0f5ff;
  }

  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }

  .photo-thumb {
    position: relative;
    height: 160px;
    border-radius: 6px;
    overflow: hidden;
    cursor: pointer;
    background: #eee;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .cover-tag {
      position: absolute;
      top: 6px;
      left: 6px;
      margin: 0;
    }
  }

  .photo-info {
    margin-top: 8px;

    .photo-name {
      font-size: 13px;
      font-weight: 500;
    }

    .photo-time {
      font-size: 12px;
      color: rgba(0, 0, 0, 0.45);
      margin-top: 2px;
    }
  }

  .photo-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0 4px;
    margin-top: 4px;
  }
}
</style>
