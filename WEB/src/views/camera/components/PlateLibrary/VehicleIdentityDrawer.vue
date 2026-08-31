<template>
  <BasicDrawer v-bind="$attrs" @register="register" title="车辆电子身份档案" width="92%" :showFooter="false">
    <a-alert class="mb-3" type="info" show-icon message="VID 与正式车牌库相互独立"
      description="未入正式车牌库的车辆也会获得稳定 VID 并形成轨迹；确认车主后历史轨迹保持不变。" />
    <div class="toolbar">
      <a-input-search v-model:value="search" placeholder="搜索 VID / 车牌 / 电子名称 / 车主" allow-clear style="width:340px" @search="load" />
      <a-select v-model:value="riskStatus" allow-clear placeholder="全部风险" style="width:150px" @change="load">
        <a-select-option value="normal">正常</a-select-option>
        <a-select-option value="review">待复核</a-select-option>
        <a-select-option value="suspected_clone">疑似套牌</a-select-option>
      </a-select>
      <Button preIcon="ant-design:reload-outlined" :loading="loading" @click="load">刷新</Button>
      <Button :disabled="selectedIds.length < 2" preIcon="ant-design:merge-cells-outlined" @click="mergeSelected">合并所选（{{ selectedIds.length }}）</Button>
    </div>
    <a-table :data-source="rows" :columns="columns" :loading="loading" row-key="id"
      :row-selection="{ selectedRowKeys: selectedIds, onChange: onSelectionChange }"
      :pagination="{ current: page, pageSize, total, showSizeChanger: false }" @change="onTableChange">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'cover'">
          <img :src="imageUrl(record.cover_image_path) || defaultPlate" class="cover" alt="车牌" />
        </template>
        <template v-else-if="column.key === 'identity'">
          <div class="name">{{ record.display_name }}</div><div class="code">{{ record.identity_code }}</div>
        </template>
        <template v-else-if="column.key === 'plate'">
          <a-tag color="blue">{{ record.current_plate_no || '未识别' }}</a-tag>
          <span v-if="record.plate_color" class="color">{{ record.plate_color }}</span>
        </template>
        <template v-else-if="column.key === 'risk'">
          <a-tag :color="record.risk_status === 'suspected_clone' ? 'red' : record.risk_status === 'review' ? 'orange' : 'green'">{{ riskLabel(record.risk_status) }}</a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-button type="link" size="small" @click="openTrajectory(record)">轨迹</a-button>
          <a-button type="link" size="small" @click="openEdit(record)">命名/确认</a-button>
        </template>
      </template>
    </a-table>

    <a-drawer v-model:open="trajectoryOpen" title="车辆轨迹" width="580" :get-container="false">
      <a-descriptions v-if="selected" bordered size="small" :column="1" class="mb-3">
        <a-descriptions-item label="车辆编码">{{ selected.identity_code }}</a-descriptions-item>
        <a-descriptions-item label="当前车牌">{{ selected.current_plate_no || '—' }}</a-descriptions-item>
        <a-descriptions-item label="累计出现">{{ selected.occurrence_count }} 次</a-descriptions-item>
      </a-descriptions>
      <a-timeline>
        <a-timeline-item v-for="point in trajectory" :key="point.id">
          <div>{{ formatTime(point.created_at) }} · {{ point.device_name || point.device_id }}</div>
          <div class="code">{{ point.normalized_plate_no || point.plate_no }} · {{ point.vehicle_resolution }}</div>
          <img v-if="point.plate_image_path" :src="imageUrl(point.plate_image_path)" class="trajectory-image" alt="车牌" />
        </a-timeline-item>
      </a-timeline>
      <a-empty v-if="!trajectoryLoading && !trajectory.length" description="暂无轨迹" />
      <a-spin :spinning="trajectoryLoading" />
    </a-drawer>

    <a-modal v-model:open="editOpen" title="车辆电子身份" @ok="saveIdentity">
      <a-form layout="vertical">
        <a-form-item label="VID"><a-input :value="selected?.identity_code" disabled /></a-form-item>
        <a-form-item label="电子名称"><a-input v-model:value="editForm.display_name" /></a-form-item>
        <a-form-item label="车主"><a-input v-model:value="editForm.owner_name" placeholder="未知可留空" /></a-form-item>
        <a-form-item label="风险状态"><a-select v-model:value="editForm.risk_status" style="width:100%">
          <a-select-option value="normal">正常</a-select-option><a-select-option value="review">待复核</a-select-option><a-select-option value="suspected_clone">疑似套牌</a-select-option>
        </a-select></a-form-item>
        <a-form-item label="备注"><a-textarea v-model:value="editForm.remark" :rows="3" /></a-form-item>
      </a-form>
    </a-modal>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { Modal } from 'ant-design-vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import { getVehicleIdentityTrajectory, listVehicleIdentities, mergeVehicleIdentities, resolvePlateImageDisplayUrl,
  updateVehicleIdentity, type PlateMatchRecord, type VehicleIdentity } from '@/api/device/plate_library';
import DEFAULT_PLATE_IMAGE from '@/assets/images/video/snap-task.png';

defineOptions({ name: 'VehicleIdentityDrawer' });
const { createMessage } = useMessage();
const defaultPlate = DEFAULT_PLATE_IMAGE;
const rows = ref<VehicleIdentity[]>([]), loading = ref(false), search = ref('');
const riskStatus = ref<string>(), page = ref(1), total = ref(0), selectedIds = ref<number[]>([]);
const pageSize = 20;
const selected = ref<VehicleIdentity>(), trajectory = ref<PlateMatchRecord[]>([]);
const trajectoryOpen = ref(false), trajectoryLoading = ref(false), editOpen = ref(false);
const editForm = ref({ display_name: '', owner_name: '', risk_status: 'normal', remark: '' });
const columns = [
  { title:'车牌图', key:'cover', width:110 }, { title:'车辆电子身份', key:'identity' },
  { title:'当前车牌', key:'plate', width:150 }, { title:'车主', dataIndex:'owner_name', width:120 },
  { title:'风险', key:'risk', width:100 }, { title:'出现次数', dataIndex:'occurrence_count', width:90 },
  { title:'最近出现', dataIndex:'last_seen_at', width:175 }, { title:'操作', key:'action', width:150 },
];
const [register] = useDrawerInner(async () => { page.value = 1; await load(); });
function imageUrl(path?: string) { return resolvePlateImageDisplayUrl(path ? `/video/alert/image?path=${encodeURIComponent(path)}` : ''); }
function riskLabel(v: string) { return ({ normal:'正常', review:'待复核', suspected_clone:'疑似套牌' } as Record<string,string>)[v] || v; }
function formatTime(v?: string) { return v ? v.replace('T',' ').replace('Z','').slice(0,19) : '—'; }
async function load() { loading.value=true; try { const r=await listVehicleIdentities({page:page.value,pageSize,risk_status:riskStatus.value,search:search.value||undefined}); rows.value=r.list||[];total.value=r.total||0; } finally { loading.value=false; } }
function onTableChange(p:{current?:number}) { page.value=p.current||1; void load(); }
function onSelectionChange(keys:Array<string|number>) { selectedIds.value=keys.map(Number); }
async function openTrajectory(record:VehicleIdentity) { selected.value=record;trajectoryOpen.value=true;trajectoryLoading.value=true;try { const r=await getVehicleIdentityTrajectory(record.id,{limit:500});trajectory.value=r.data?.points||[]; } finally { trajectoryLoading.value=false; } }
function openEdit(record:VehicleIdentity) { selected.value=record;editForm.value={display_name:record.display_name||'',owner_name:record.owner_name||'',risk_status:record.risk_status||'normal',remark:record.remark||''};editOpen.value=true; }
async function saveIdentity() { if(!selected.value||!editForm.value.display_name.trim()) return createMessage.warning('电子名称不能为空');await updateVehicleIdentity(selected.value.id,{display_name:editForm.value.display_name.trim(),owner_name:editForm.value.owner_name.trim()||undefined,risk_status:editForm.value.risk_status as VehicleIdentity['risk_status'],remark:editForm.value.remark.trim()||undefined,status:editForm.value.owner_name.trim()?'confirmed':'anonymous'});editOpen.value=false;createMessage.success('车辆身份已更新');await load(); }
function mergeSelected() { if(selectedIds.value.length<2)return;const [target,...sources]=selectedIds.value;Modal.confirm({title:'确认合并车辆身份？',content:`以 VID #${target} 为主身份，合并其余 ${sources.length} 个身份。`,onOk:async()=>{await mergeVehicleIdentities(target,sources);selectedIds.value=[];createMessage.success('车辆身份已合并');await load();}}); }
</script>

<style scoped>
.toolbar{display:flex;gap:10px;margin-bottom:14px}.cover{width:90px;height:48px;object-fit:cover;border-radius:6px;background:#f0f2f5}.name{font-weight:600}.code{margin-top:3px;color:#64748b;font:12px monospace}.color{margin-left:5px;color:#64748b}.trajectory-image{width:150px;max-height:80px;margin-top:6px;object-fit:cover;border-radius:5px}
</style>
