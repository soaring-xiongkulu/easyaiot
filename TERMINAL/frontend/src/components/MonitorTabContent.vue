<template>
  <div class="monitor-tab">
    <div class="monitor-tabs-header">
      <div class="tab-item" :class="{ active: activeTab === 'performance' }" @click="activeTab = 'performance'">{{ t('monitor.performance') }}</div>
      <div class="tab-item" :class="{ active: activeTab === 'processes' }" @click="activeTab = 'processes'">{{ t('monitor.processes') }}</div>
      <div class="tab-item" :class="{ active: activeTab === 'ports' }" @click="activeTab = 'ports'">{{ t('monitor.ports') }}</div>
      <div class="tab-item" :class="{ active: activeTab === 'disks' }" @click="activeTab = 'disks'">{{ t('monitor.disks') }}</div>
      <div class="tab-item" :class="{ active: activeTab === 'network' }" @click="activeTab = 'network'">{{ t('monitor.networkCards') }}</div>
      <div class="tab-item" :class="{ active: activeTab === 'services' }" @click="activeTab = 'services'">{{ t('monitor.services') }}</div>
      <div class="tab-item" :class="{ active: activeTab === 'system' }" @click="activeTab = 'system'">{{ t('monitor.system') }}</div>
      <div class="tab-item" :class="{ active: activeTab === 'devices' }" @click="activeTab = 'devices'">{{ t('monitor.devices') }}</div>
      <div class="tab-item" :class="{ active: activeTab === 'health' }" @click="activeTab = 'health'">{{ t('monitor.health') }}</div>
    </div>

    <!-- Performance -->
    <div v-show="activeTab === 'performance'" class="tab-pane performance-pane">
      <div class="perf-sidebar">
        <div
          v-for="item in perfItems"
          :key="item.key"
          class="perf-nav-item"
          :class="{ active: selectedPerf === item.key }"
          @click="selectedPerf = item.key"
        >
          <div class="perf-nav-name">{{ item.label }}</div>
          <div class="perf-nav-value" :style="{ color: item.color }">{{ item.value }}</div>
          <div class="perf-nav-bar"><div class="perf-nav-bar-inner" :style="{ width: item.percent + '%', background: item.color }" /></div>
        </div>
      </div>
      <div class="perf-main">
        <div class="perf-big-value" :style="{ color: currentPerf.color }">{{ currentPerf.bigValue }}</div>
        <canvas ref="chartCanvas" class="perf-chart" />
        <div class="perf-details">
          <div v-for="d in currentPerf.details" :key="d.label" class="perf-detail-item">
            <span class="detail-label">{{ d.label }}</span>
            <span class="detail-value">{{ d.value }}</span>
          </div>
        </div>

        <!-- Expandable: all cores / all NICs / all disks -->
        <div class="perf-extras">
          <template v-if="selectedPerf === 'cpu'">
            <div class="perf-sub-toggle" @click="showCores = !showCores">
              <ChevronRight :size="'0.875rem'" class="chev" :class="{ open: showCores }" />
              <span>{{ t('monitor.allCores') }} ({{ cpus.length }})</span>
            </div>
            <div v-if="showCores" class="perf-sub-list">
              <div v-for="c in cpus" :key="c.core" class="perf-sub-row">
                <span class="sub-name">CPU {{ c.core }}</span>
                <div class="sub-bar"><div class="sub-fill" :style="{ width: fmtWidth(c.usage) }" /></div>
                <span class="sub-val">{{ c.usage }}%</span>
              </div>
            </div>
          </template>

          <template v-else-if="selectedPerf === 'network'">
            <div class="perf-sub-toggle" @click="showNets = !showNets">
              <ChevronRight :size="'0.875rem'" class="chev" :class="{ open: showNets }" />
              <span>{{ t('monitor.allNetworks') }} ({{ nets.length }})</span>
            </div>
            <div v-if="showNets" class="perf-sub-list">
              <div v-for="n in nets" :key="n.name" class="perf-sub-row net">
                <span class="sub-name" :title="n.name">{{ n.name }}</span>
                <span class="sub-val">↓{{ formatBytes(n.rx) }}/s</span>
                <span class="sub-val tx">↑{{ formatBytes(n.tx) }}/s</span>
              </div>
            </div>
          </template>

          <template v-else-if="selectedPerf === 'disk'">
            <div class="perf-sub-toggle" @click="toggleDisks">
              <ChevronRight :size="'0.875rem'" class="chev" :class="{ open: showDisks }" />
              <span>{{ t('monitor.allDisks') }} ({{ mountedDisks.length }})</span>
            </div>
            <div v-if="showDisks" class="perf-sub-list">
              <div v-if="diskLoading" class="perf-sub-empty">{{ t('monitor.loading') }}</div>
              <div v-for="d in mountedDisks" v-else :key="d.name + d.mountPoint" class="perf-sub-row">
                <span class="sub-name" :title="d.mountPoint || d.name">{{ d.mountPoint || d.name }}</span>
                <div class="sub-bar"><div class="sub-fill" :style="{ width: fmtWidth(d.usage) }" /></div>
                <span class="sub-val">{{ d.used }} / {{ d.total }}</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Processes -->
    <div v-show="activeTab === 'processes'" class="tab-pane processes-pane">
      <div class="process-toolbar">
        <div class="process-summary">
          <div class="summary-item">
            <span class="summary-label">CPU</span>
            <span class="summary-value">{{ processSummaryCpu.usage }}%</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('monitor.memory') }}</span>
            <span class="summary-value">{{ processSummaryMem.usage }}%</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('monitor.total') }}</span>
            <span class="summary-value">{{ processSummaryMem.total.toFixed(2) }} GB</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('monitor.used') }}</span>
            <span class="summary-value">{{ processSummaryMem.used.toFixed(2) }} GB</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('monitor.free') }}</span>
            <span class="summary-value">{{ processSummaryMem.free.toFixed(2) }} GB</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">{{ t('monitor.processCount') }}</span>
            <span class="summary-value">{{ processSummaryCpu.processes }}</span>
          </div>
        </div>
        <div class="process-actions">
          <el-button :type="paused ? 'primary' : 'default'" @click="togglePause">
            {{ paused ? t('monitor.resume') : t('monitor.pause') }}
          </el-button>
        </div>
      </div>
      <el-input v-model="processSearch" :placeholder="t('monitor.searchProcess')" clearable class="process-search" />
      <el-table :data="filteredProcesses" size="small" height="calc(100% - 2.5rem)" class="process-table" @row-click="onProcessRowClick">
        <el-table-column prop="pid" label="PID" sortable :width="uiPx(80)" />
        <el-table-column prop="name" :label="t('monitor.processName')" sortable />
        <el-table-column prop="user" :label="t('monitor.user')" sortable :width="uiPx(100)" />
        <el-table-column prop="state" :label="t('monitor.state')" sortable :width="uiPx(80)">
          <template #default="{ row }">{{ row.state ? String(row.state)[0] : '-' }}</template>
        </el-table-column>
        <el-table-column prop="cpu" :label="t('monitor.cpu')" sortable :width="uiPx(90)">
          <template #default="{ row }">{{ row.cpu }}%</template>
        </el-table-column>
        <el-table-column prop="mem" :label="t('monitor.mem')" sortable :width="uiPx(90)">
          <template #default="{ row }">{{ row.mem }}%</template>
        </el-table-column>
        <el-table-column :label="''" :width="uiPx(86)" align="center" class-name="proc-act-cell">
          <template #default="{ row }">
            <el-button size="small" @click.stop="onTableSignal(row, $event)">
              {{ t('monitor.sendSignal') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Ports -->
    <div v-show="activeTab === 'ports'" class="tab-pane ports-pane" @contextmenu.prevent="showContextMenu($event)">
      <div class="od-toolbar">
        <el-input v-model="portSearch" :placeholder="t('monitor.searchPort')" clearable class="od-search" />
        <el-button :icon="RefreshRight" :loading="loadingPorts" @click="fetchPorts">
          {{ t('monitor.refresh') }}
        </el-button>
      </div>
      <el-table :data="filteredPorts" size="small" v-loading="loadingPorts" height="calc(100% - 2.25rem)" class="od-table">
        <el-table-column prop="protocol" :label="t('monitor.port.protocol')" sortable :width="uiPx(90)" />
        <el-table-column prop="localAddr" :label="t('monitor.port.localAddr')" sortable :width="uiPx(160)" />
        <el-table-column prop="process" :label="t('monitor.port.process')" sortable />
      </el-table>
    </div>

    <!-- Disks -->
    <div v-show="activeTab === 'disks'" class="tab-pane disks-pane" @contextmenu.prevent="showContextMenu($event)">
      <div class="od-toolbar">
        <el-input v-model="diskSearch" :placeholder="t('monitor.searchDisk')" clearable class="od-search" />
        <el-button :icon="RefreshRight" :loading="loadingDisks" @click="fetchDisks">
          {{ t('monitor.refresh') }}
        </el-button>
      </div>
      <el-table :data="filteredDisks" size="small" v-loading="loadingDisks" height="calc(100% - 2.25rem)" class="od-table">
        <el-table-column prop="name" :label="t('monitor.disk.name')" sortable>
          <template #default="{ row }">
            <span :style="{ paddingLeft: (row.name.match(/^ +/)?.[0].length || 0) * 6 + 'px' }">{{ row.name.trim() }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" :label="t('monitor.disk.type')" sortable :width="uiPx(90)" />
        <el-table-column prop="mountPoint" :label="t('monitor.disk.mountPoint')" sortable />
        <el-table-column prop="size" :label="t('monitor.disk.size')" sortable :width="uiPx(100)" />
        <el-table-column prop="used" :label="t('monitor.disk.used')" sortable :width="uiPx(90)" />
        <el-table-column prop="usage" :label="t('monitor.disk.usage')" sortable :width="uiPx(100)">
          <template #default="{ row }">{{ row.usage ? row.usage + '%' : '-' }}</template>
        </el-table-column>
        <el-table-column prop="media" :label="t('monitor.disk.media')" sortable :width="uiPx(80)" />
        <el-table-column prop="fsType" :label="t('monitor.disk.fstype')" sortable :width="uiPx(100)" />
        <el-table-column prop="uuid" :label="t('monitor.disk.uuid')" sortable :width="uiPx(180)" />
        <el-table-column prop="vendor" :label="t('monitor.disk.vendor')" sortable :width="uiPx(120)" />
        <el-table-column prop="model" :label="t('monitor.disk.model')" sortable />
      </el-table>
    </div>

    <!-- Network -->
    <div v-show="activeTab === 'network'" class="tab-pane network-pane" @contextmenu.prevent="showContextMenu($event)">
      <div class="od-toolbar">
        <el-input v-model="netSearch" :placeholder="t('monitor.searchNetwork')" clearable class="od-search" />
        <el-button :icon="RefreshRight" :loading="loadingNetCards" @click="fetchNetCards">
          {{ t('monitor.refresh') }}
        </el-button>
      </div>
      <el-table :data="filteredNetCards" size="small" v-loading="loadingNetCards" height="calc(100% - 2.25rem)" class="od-table">
        <el-table-column prop="name" :label="t('monitor.net.name')" sortable :width="uiPx(120)" />
        <el-table-column prop="state" :label="t('monitor.net.state')" sortable :width="uiPx(90)" />
        <el-table-column prop="mac" :label="t('monitor.net.mac')" sortable :width="uiPx(160)" />
        <el-table-column prop="speed" :label="t('monitor.net.speed')" sortable :width="uiPx(120)" />
        <el-table-column prop="type" :label="t('monitor.net.type')" sortable :width="uiPx(100)" />
        <el-table-column prop="bondMaster" :label="t('monitor.net.bond')" sortable :width="uiPx(120)" />
        <el-table-column prop="ipAddrs" :label="t('monitor.net.ipAddrs')" sortable>
          <template #default="{ row }">{{ row.ipAddrs?.join(', ') || '-' }}</template>
        </el-table-column>
      </el-table>
    </div>

    <!-- System Info -->
    <div v-show="activeTab === 'system'" class="tab-pane system-pane">
      <div v-if="systemInfo" class="system-content">
        <div v-for="group in systemGroups" :key="group.title" class="system-group">
          <div class="system-group-title">{{ group.title }}</div>
          <div class="system-group-items">
            <div v-for="item in group.items" :key="item.label" class="system-row">
              <span class="system-row-label">{{ item.label }}</span>
              <span class="system-row-value" @contextmenu.prevent="showContextMenu($event)">{{ item.value }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="system-loading">{{ t('monitor.loading') }}</div>
    </div>

    <!-- Services -->
    <div v-show="activeTab === 'services'" class="tab-pane services-pane" @contextmenu.prevent="showContextMenu($event)">
      <div class="od-toolbar">
        <el-input v-model="serviceSearch" :placeholder="t('monitor.searchService')" clearable class="od-search" />
        <el-button :icon="RefreshRight" :loading="loadingServices" @click="fetchServices">
          {{ t('monitor.refresh') }}
        </el-button>
      </div>
      <el-table :data="filteredServices" size="small" v-loading="loadingServices" height="calc(100% - 2.25rem)" class="od-table" @row-click="onServiceRowClick">
        <el-table-column prop="name" :label="t('monitor.service.name')" sortable :min-width="uiPx(220)" />
        <el-table-column prop="active" :label="t('monitor.service.active')" sortable :width="uiPx(100)">
          <template #default="{ row }">
            <span class="svc-state" :class="serviceStateClass(row)">{{ row.active }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="enabled" :label="t('monitor.service.enabled')" sortable :width="uiPx(110)">
          <template #default="{ row }">{{ row.enabled || '-' }}</template>
        </el-table-column>
        <el-table-column prop="description" :label="t('monitor.service.description')" :min-width="uiPx(220)" show-overflow-tooltip />
        <el-table-column :label="t('monitor.service.actions')" :width="uiPx(120)" align="center">
          <template #default="{ row }">
            <el-button size="small" @click.stop="onServiceActionMenu(row, $event)">
              {{ t('monitor.service.actions') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Devices -->
    <div v-show="activeTab === 'devices'" class="tab-pane devices-pane" @contextmenu.prevent="showContextMenu($event)">
      <div class="od-toolbar">
        <el-input v-model="deviceSearch" :placeholder="t('monitor.searchDevice')" clearable class="od-search" />
        <el-button :icon="RefreshRight" :loading="loadingDevices" @click="fetchDevices">
          {{ t('monitor.refresh') }}
        </el-button>
      </div>
      <el-table :data="deviceTreeData" row-key="rowKey" :tree-props="{ children: 'children' }" size="small" v-loading="loadingDevices" height="calc(100% - 2.25rem)" class="od-table">
        <el-table-column prop="id" :label="t('monitor.device.slot')" sortable :width="uiPx(150)" show-overflow-tooltip />
        <el-table-column prop="class" :label="t('monitor.device.class')" :min-width="uiPx(150)" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.isGroup">{{ t('monitor.device.cat.' + row.category) }} ({{ row.count }})</span>
            <span v-else>{{ row.class }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="vendor" :label="t('monitor.device.vendor')" sortable :min-width="uiPx(150)" show-overflow-tooltip />
        <el-table-column prop="product" :label="t('monitor.device.device')" :min-width="uiPx(220)" show-overflow-tooltip />
        <el-table-column prop="driver" :label="t('monitor.device.driver')" sortable :width="uiPx(120)" show-overflow-tooltip />
        <el-table-column prop="serial" :label="t('monitor.device.serial')" :width="uiPx(140)" show-overflow-tooltip />
        <el-table-column prop="capacity" :label="t('monitor.device.capacity')" sortable :width="uiPx(100)" />
        <el-table-column prop="rev" :label="t('monitor.device.rev')" :width="uiPx(90)" show-overflow-tooltip />
      </el-table>
    </div>

    <!-- Hardware health -->
    <div v-show="activeTab === 'health'" class="tab-pane health-pane" @contextmenu.prevent="showContextMenu($event)">
      <!-- Top: device identity (FRU + IPMI LAN), each card loads and refreshes independently -->
      <div class="health-top">
        <div class="health-cards">
          <div class="health-card">
            <div class="health-card-header">
              <span class="health-card-title">{{ t('monitor.health.fru') }}</span>
              <el-button link :icon="RefreshRight" :loading="loadingHardwareFru" @click="fetchHardwareFru" />
            </div>
            <div class="health-card-body" v-loading="loadingHardwareFru">
              <template v-if="hardwareFru">
                <div class="info-grid">
                  <div class="system-row">
                    <span class="system-row-label">{{ t('monitor.health.product') }}</span>
                    <span class="system-row-value">{{ hardwareFru.product || '-' }}</span>
                  </div>
                  <div class="system-row">
                    <span class="system-row-label">{{ t('monitor.health.manufacturer') }}</span>
                    <span class="system-row-value">{{ hardwareFru.manufacturer || '-' }}</span>
                  </div>
                  <div class="system-row">
                    <span class="system-row-label">{{ t('monitor.health.serial') }}</span>
                    <span class="system-row-value">{{ hardwareFru.serial || '-' }}</span>
                  </div>
                  <div class="system-row">
                    <span class="system-row-label">{{ t('monitor.health.partNumber') }}</span>
                    <span class="system-row-value">{{ hardwareFru.partNumber || '-' }}</span>
                  </div>
                </div>
              </template>
              <div v-else-if="!loadingHardwareFru" class="health-hint">{{ t('monitor.health.noIpmi') }}</div>
            </div>
          </div>
          <div class="health-card">
            <div class="health-card-header">
              <span class="health-card-title">{{ t('monitor.health.lan') }}</span>
              <el-button link :icon="RefreshRight" :loading="loadingHardwareLan" @click="fetchHardwareLan" />
            </div>
            <div class="health-card-body" v-loading="loadingHardwareLan">
              <div v-if="hardwareLan.length" class="info-grid">
                <div v-for="f in hardwareLan" :key="f.key" class="system-row">
                  <span class="system-row-label">{{ f.key }}</span>
                  <span class="system-row-value">{{ f.value }}</span>
                </div>
              </div>
              <div v-else-if="!loadingHardwareLan" class="health-hint">{{ t('monitor.health.noIpmi') }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom: sensors, loads and refreshes independently -->
      <div class="health-bottom">
        <div class="health-card-header">
          <span class="health-card-title">{{ t('monitor.health.sensors') }}</span>
          <div class="health-card-actions">
            <el-input v-model="sensorSearch" :placeholder="t('monitor.searchSensor')" clearable class="health-search" />
            <el-button link :icon="RefreshRight" :loading="loadingHardwareSensors" @click="fetchHardwareSensors" />
          </div>
        </div>
        <div v-if="hardwareSensors && !hardwareSensors.hasIpmi" class="health-hint health-bottom-hint">
          {{ t('monitor.health.noIpmi') }}
        </div>
        <el-table v-if="hardwareSensors && hardwareSensors.sensors.length" :data="filteredSensors" size="small" v-loading="loadingHardwareSensors" height="calc(100% - 2.25rem)" class="od-table health-table">
          <el-table-column prop="name" :label="t('monitor.health.name')" sortable :min-width="uiPx(160)" />
          <el-table-column prop="value" :label="t('monitor.health.value')" :min-width="uiPx(140)" />
          <el-table-column prop="unit" :label="t('monitor.health.unit')" :width="uiPx(110)">
            <template #default="{ row }">{{ row.unit || '-' }}</template>
          </el-table-column>
          <el-table-column prop="status" :label="t('monitor.health.status')" :width="uiPx(110)">
            <template #default="{ row }">
              <span class="svc-state" :class="sensorStatusClass(row.status)">{{ row.status }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="source" :label="t('monitor.health.source')" :width="uiPx(110)" />
        </el-table>
      </div>
    </div>

    <!-- Process Detail Panel (inside monitor-tab) -->
    <!-- 两个抽屉 Teleport 到 .app-container（main-content 的兄弟节点）：
         遮罩要盖住左侧栏/顶栏在内的整个应用，而不是只盖工作区 -->
    <Teleport to=".app-container">
    <div class="detail-drawer-backdrop" :class="{ open: detailDrawerVisible }" @click="detailDrawerVisible = false"></div>
    <div class="detail-drawer" :class="{ open: detailDrawerVisible }">
      <div class="detail-drawer-header">
        <span class="detail-drawer-title">{{ t('monitor.processDetail') }}</span>
        <el-button link @click="detailDrawerVisible = false">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      <div v-if="processDetail" class="process-detail">
        <div class="detail-section" @contextmenu="onDetailSectionContextMenu">
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.pid') }}</span>
            <span class="detail-value">{{ processDetail.pid }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.ppid') }}</span>
            <span class="detail-value">{{ processDetail.ppid ?? '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.processName') }}</span>
            <span class="detail-value">{{ processDetail.name ?? '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.state') }}</span>
            <span class="detail-value">{{ processDetail.state ?? '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.threads') }}</span>
            <span class="detail-value">{{ processDetail.threads ?? '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.exe') }}</span>
            <span class="detail-value">{{ processDetail.exe ?? '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.cwd') }}</span>
            <span class="detail-value">{{ processDetail.cwd ?? '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.cmdline') }}</span>
            <span class="detail-value cmdline">{{ processDetail.cmdline ?? '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.startTime') }}</span>
            <span class="detail-value">{{ processDetail.startTime ?? '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.fd') }}</span>
            <div class="detail-value io-stats" v-if="processDetail.fd">
              <div>{{ t('monitor.detail.fdTotal') }}: {{ processDetail.fd.total ?? 0 }}</div>
              <div>{{ t('monitor.detail.fdFiles') }}: {{ processDetail.fd.files ?? 0 }}</div>
              <div>{{ t('monitor.detail.fdSockets') }}: {{ processDetail.fd.sockets ?? 0 }}</div>
              <div>{{ t('monitor.detail.fdPipes') }}: {{ processDetail.fd.pipes ?? 0 }}</div>
              <div>{{ t('monitor.detail.fdAnons') }}: {{ processDetail.fd.anons ?? 0 }}</div>
              <div>{{ t('monitor.detail.fdDevs') }}: {{ processDetail.fd.devs ?? 0 }}</div>
              <div>{{ t('monitor.detail.fdOthers') }}: {{ processDetail.fd.others ?? 0 }}</div>
            </div>
            <span class="detail-value" v-else>-</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.vmRss') }}</span>
            <span class="detail-value">{{ processDetail.vmRss ?? '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.vmSize') }}</span>
            <span class="detail-value">{{ processDetail.vmSize ?? '-' }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.cpuTicks') }}</span>
            <span class="detail-value">{{ processDetail.cpuTicks ?? '-' }}</span>
          </div>
          <div v-if="processDetail.voluntaryCtxSwitches != null || processDetail.nonvoluntaryCtxSwitches != null" class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.ctxSwitches') }}</span>
            <span class="detail-value">
              vol: {{ processDetail.voluntaryCtxSwitches ?? 0 }} / nonvol: {{ processDetail.nonvoluntaryCtxSwitches ?? 0 }}
            </span>
          </div>
          <div v-if="processDetail.io" class="detail-row">
            <span class="detail-label">{{ t('monitor.detail.io') }}</span>
            <div class="detail-value io-stats">
              <div>rchar: {{ formatIo(processDetail.io.rchar) }}</div>
              <div>wchar: {{ formatIo(processDetail.io.wchar) }}</div>
              <div>read_bytes: {{ formatIo(processDetail.io.read_bytes) }}</div>
              <div>write_bytes: {{ formatIo(processDetail.io.write_bytes) }}</div>
            </div>
          </div>
        </div>
        <div class="detail-actions">
          <el-button @click="detailDrawerVisible = false">{{ t('common.cancel') }}</el-button>
        </div>
      </div>
      <div v-else class="process-detail-empty">{{ t('monitor.noProcessSelected') }}</div>
    </div>
    </Teleport>

    <!-- Kill Confirmation Dialog -->
    <el-dialog append-to-body v-model="killDialogVisible" :title="killType === 'kill' ? t('monitor.forceKill') : t('monitor.kill')" width="22.5rem" align-center>
      <p>{{ killMessage }}</p>
      <template #footer>
        <el-button @click="killDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="danger" @click="confirmKill">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- Service Action Confirmation Dialog -->
    <el-dialog append-to-body v-model="serviceDialogVisible" :title="serviceActionCmd ? t('monitor.service.' + serviceActionCmd) : ''" width="22.5rem" align-center>
      <p>{{ serviceActionMessage }}</p>
      <template #footer>
        <el-button @click="serviceDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="confirmServiceAction">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- Service Detail Drawer (slides out like the process detail drawer);
         two tabs: properties detail / k8s-style journal logs -->
    <Teleport to=".app-container">
    <div class="detail-drawer-backdrop" :class="{ open: serviceDetailVisible }" @click="serviceDetailVisible = false"></div>
    <div class="detail-drawer" :class="{ open: serviceDetailVisible }" :style="serviceDetailVisible ? { width: svcDrawerWidth + 'px' } : undefined">
      <div class="svc-resizer" @mousedown="onServiceResizeStart"></div>
      <div class="detail-drawer-header">
        <span class="detail-drawer-title">{{ serviceDetailName }}</span>
        <el-button link @click="serviceDetailVisible = false">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      <div class="svc-drawer-tabs">
        <div class="svc-tab" :class="{ active: svcDrawerTab === 'detail' }" @click="svcDrawerTab = 'detail'">{{ t('monitor.service.detail') }}</div>
        <div class="svc-tab" :class="{ active: svcDrawerTab === 'logs' }" @click="onServiceLogsTab">{{ t('monitor.service.logs') }}</div>
      </div>
      <!-- Detail tab (same structure/styles as the process detail drawer) -->
      <div v-show="svcDrawerTab === 'detail'" class="svc-detail-pane">
        <div class="process-detail">
          <div class="detail-section" @contextmenu="onDetailSectionContextMenu">
            <div v-for="row in serviceDetailRows" :key="row.label" class="detail-row">
              <span class="detail-label">{{ row.label }}</span>
              <span class="detail-value">{{ row.value }}</span>
            </div>
            <div v-if="loadingServiceDetail && serviceDetailRows.length === 0" class="detail-row">
              <span class="detail-label">{{ t('monitor.loading') }}</span>
            </div>
          </div>
        </div>
      </div>
      <!-- Logs tab (k8s log-viewer style: line rows + muted timestamp column) -->
      <div v-show="svcDrawerTab === 'logs'" class="svc-logs-pane">
        <div class="svc-logs-toolbar">
          <el-select v-model="logLines" size="small" class="svc-log-lines" @change="onLogLinesChange">
            <el-option v-for="n in [100, 200, 500, 1000, 2000]" :key="n" :label="String(n)" :value="n" />
          </el-select>
          <el-checkbox v-model="logAutoScroll" border size="small">{{ t('monitor.service.autoScroll') }}</el-checkbox>
          <el-checkbox v-model="logTimestamps" border size="small">{{ t('k8s.logTimestamps') }}</el-checkbox>
          <el-checkbox v-model="logWrap" border size="small">{{ t('k8s.logWrap') }}</el-checkbox>
          <div class="flex-spacer" />
          <el-button size="small" :icon="RefreshRight" :loading="loadingServiceLogs" @click="fetchServiceLogs" />
        </div>
        <div
          ref="logViewerRef"
          class="svc-log-viewer"
          :class="{ 'logs-nowrap': !logWrap, 'logs-hide-ts': !logTimestamps }"
          v-loading="loadingServiceLogs"
          @contextmenu="showContextMenu"
        >
          <div v-for="(l, i) in serviceLogLines" :key="i" class="log-line"><span class="log-ts">{{ l.ts }}</span>{{ l.msg }}</div>
          <div v-if="!loadingServiceLogs && serviceLogLines.length === 0" class="health-hint" style="padding: 0.5rem 0;">{{ t('monitor.service.noLogs') }}</div>
        </div>
      </div>
    </div>
    </Teleport>

    <!-- Service action menu (shared, mounted once; opens next to the row button) -->
    <Menu ref="serviceMenuRef" v-model:visible="serviceMenuVisible">
      <MenuItem @click="onServiceCmd('start')">{{ t('monitor.service.start') }}</MenuItem>
      <MenuItem @click="onServiceCmd('stop')">{{ t('monitor.service.stop') }}</MenuItem>
      <MenuItem @click="onServiceCmd('restart')">{{ t('monitor.service.restart') }}</MenuItem>
      <MenuItem @click="onServiceCmd('enable')">{{ t('monitor.service.enable') }}</MenuItem>
      <MenuItem @click="onServiceCmd('disable')">{{ t('monitor.service.disable') }}</MenuItem>
    </Menu>

    <Menu ref="ctxMenuRef" v-model:visible="ctxMenuVisible" v-slot="{ current }">
      <MenuItem @click="copyContextText(current)">{{ t('terminal.copy') }}</MenuItem>
    </Menu>

    <!-- Send-signal dropdown for the per-row table button. Kept OUTSIDE the
         processDetail-scoped drawer (which v-if's until a row is clicked) so it
         is always mounted and the button in the process table works on first
         open, independent of whether a process detail has been loaded yet. -->
    <Menu ref="signalMenuRef" v-model:visible="signalMenuVisible">
      <MenuItem @click="onSignal('term')">{{ t('monitor.signalTerm') }}</MenuItem>
      <MenuItem @click="onSignal('kill')">{{ t('monitor.signalKill') }}</MenuItem>
      <MenuItem @click="onSignal('hup')">{{ t('monitor.signalHup') }}</MenuItem>
      <MenuItem @click="onSignal('int')">{{ t('monitor.signalInt') }}</MenuItem>
    </Menu>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, onActivated, onDeactivated, watch, nextTick } from 'vue'
import { SetMonitorActiveTab, SetMonitorPaused, GetProcessDetail, KillProcess, GetPorts, GetDisks, GetNetworkCards, GetServices, GetServiceDetail, GetServiceLogs, ServiceAction, GetDevices, GetHardwareFru, GetHardwareLan, GetHardwareSensors } from '../../bindings/easyaiot/terminal/app'
import { msg } from '../services/message'
import { Close, RefreshRight } from '@element-plus/icons-vue'
import { ChevronRight } from '@lucide/vue'
import { useI18n } from '../i18n'
import { uiPx } from '../utils/uiScale'

import Menu from './Menu.vue'
import { Events } from '@wailsio/runtime'
import MenuItem from './MenuItem.vue'

const props = defineProps<{
  sessionId: string
}>()

defineOptions({ name: 'MonitorTabContent' })

const { t } = useI18n()
const activeTab = ref('performance')
const selectedPerf = ref('cpu')
const processSearch = ref('')
const portSearch = ref('')
const diskSearch = ref('')
const netSearch = ref('')
const paused = ref(false)

// Process detail
const detailDrawerVisible = ref(false)
const selectedProcess = ref<any>(null)
const processDetail = ref<any>(null)

// Kill dialog
const killDialogVisible = ref(false)
const killTarget = ref<any>(null)
const killType = ref<string>('term') // 'term' | 'kill' | 'hup' | 'int'

// Context menu
const ctxMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const ctxMenuVisible = ref(false)

// Histories (max 60 points)
const cpuHistory = ref<number[]>([])
const memHistory = ref<number[]>([])
const diskHistory = ref<number[]>([])
const netRxHistory = ref<number[]>([])
const netTxHistory = ref<number[]>([])

// Current values (performance tab)
const currentCpu = ref({ usage: 0, total: 0, user: 0, system: 0, iowait: 0, cores: 0, processes: 0, handles: 0, load1: '-', load5: '-', load15: '-' })
const currentMem = ref({ total: 0, used: 0, free: 0, usage: 0, cached: 0, buffers: 0 })
const currentSwap = ref({ total: 0, used: 0, usage: 0 })
const currentDisk = ref({ total: '', used: '', usage: 0 })
const currentNet = ref({ rx: 0, tx: 0, rxTotal: 0, txTotal: 0 })
const processList = ref<any[]>([])
const systemInfo = ref<Record<string, any> | null>(null)

// Expandable detail lists: per-core / per-NIC (live from perf payload) and
// per-disk (fetched on-demand via GetDisks when expanded).
const cpus = ref<any[]>([])
const nets = ref<any[]>([])
const disks = ref<any[]>([])
const diskLoading = ref(false)
const showCores = ref(false)
const showNets = ref(false)
const showDisks = ref(false)

// Only directories with a mount point are shown in the disk detail list.
const mountedDisks = computed(() => disks.value.filter((d: any) => d.mountPoint))

// Summary values for processes tab (independent from performance tab)
const processSummaryCpu = ref({ usage: 0, cores: 0, processes: 0, load1: '-', load5: '-', load15: '-' })
const processSummaryMem = ref({ total: 0, used: 0, free: 0, usage: 0, cached: 0, buffers: 0 })

// On-demand tab data
const portList = ref<any[]>([])
const diskList = ref<any[]>([])
const netCardList = ref<any[]>([])
const loadingPorts = ref(false)
const loadingDisks = ref(false)
const loadingNetCards = ref(false)

// Services / devices / hardware health (on-demand tabs)
const serviceList = ref<any[]>([])
const deviceList = ref<any[]>([])
// Hardware health loads as three independent parts (FRU / IPMI LAN /
// sensors) so a slow ipmitool call does not block the others.
const hardwareFru = ref<any>(null)
const hardwareLan = ref<any[]>([])
const hardwareSensors = ref<any>(null)
const loadingServices = ref(false)
const loadingDevices = ref(false)
const loadingHardwareFru = ref(false)
const loadingHardwareLan = ref(false)
const loadingHardwareSensors = ref(false)
const serviceSearch = ref('')
const deviceSearch = ref('')
const sensorSearch = ref('')

// Service action confirm dialog
const serviceDialogVisible = ref(false)
const serviceActionTarget = ref<any>(null)
const serviceActionCmd = ref('')
const serviceMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const serviceMenuVisible = ref(false)

// Service detail drawer: two tabs (properties detail / journal logs)
const serviceDetailVisible = ref(false)
const serviceDetailName = ref('')
const serviceDetail = ref<any>(null)
const loadingServiceDetail = ref(false)
const svcDrawerTab = ref<'detail' | 'logs'>('detail')
const logLines = ref(200)
const logAutoScroll = ref(true)
const logTimestamps = ref(true)
const logWrap = ref(false)
const serviceLogs = ref('')
const loadingServiceLogs = ref(false)
const logViewerRef = ref<HTMLElement | null>(null)

// Drawer width (draggable via the left-edge resizer, same as the k8s drawer;
// not persisted across sessions). The logs tab widens to ~80% of the viewport
// (log lines are long); a width the user dragged larger is kept.
const svcDrawerWidth = ref(480)
function logsTargetWidth() {
  return Math.min(window.innerWidth - 120, Math.max(720, Math.round(window.innerWidth * 0.8)))
}
let svcResizeStartX = 0
let svcResizeStartW = 0

function onServiceResizeMove(e: MouseEvent) {
  const dx = svcResizeStartX - e.clientX
  svcDrawerWidth.value = Math.max(320, Math.min(window.innerWidth - 120, svcResizeStartW + dx))
}

function onServiceResizeEnd() {
  document.removeEventListener('mousemove', onServiceResizeMove)
  document.removeEventListener('mouseup', onServiceResizeEnd)
}

function onServiceResizeStart(e: MouseEvent) {
  svcResizeStartX = e.clientX
  svcResizeStartW = svcDrawerWidth.value
  document.addEventListener('mousemove', onServiceResizeMove)
  document.addEventListener('mouseup', onServiceResizeEnd)
  e.preventDefault()
}

// Split a journalctl short-iso line into "<RFC3339 timestamp> <message>",
// mirroring the k8s log viewer's line model.
function splitLogLine(line: string): { ts: string; msg: string } {
  const sp = line.indexOf(' ')
  if (sp > 0 && /^\d{4}-\d\d-\d\dT/.test(line)) {
    return { ts: line.slice(0, sp), msg: line.slice(sp + 1) }
  }
  return { ts: '', msg: line }
}

const serviceLogLines = computed(() => serviceLogs.value.split('\n').map(splitLogLine))

const chartCanvas = ref<HTMLCanvasElement>()

function pushHistory(arr: number[], val: number) {
  arr.push(val)
  if (arr.length > 60) arr.shift()
}

const perfItems = computed(() => [
  {
    key: 'cpu',
    label: t('monitor.cpu'),
    value: currentCpu.value.usage + '%',
    percent: Math.min(currentCpu.value.usage, 100),
    color: 'var(--chart-1)'
  },
  {
    key: 'memory',
    label: t('monitor.memory'),
    value: currentMem.value.usage + '%',
    percent: Math.min(currentMem.value.usage, 100),
    color: 'var(--chart-2)'
  },
  {
    key: 'disk',
    label: t('monitor.disk'),
    value: currentDisk.value.usage + '%',
    percent: Math.min(currentDisk.value.usage, 100),
    color: 'var(--chart-3)'
  },
  {
    key: 'network',
    label: t('monitor.network'),
    value: formatBytes(currentNet.value.rx + currentNet.value.tx) + '/s',
    percent: Math.min((currentNet.value.rx + currentNet.value.tx) / 1048576 * 100, 100),
    color: 'var(--chart-4)'
  }
])

const currentPerf = computed(() => {
  switch (selectedPerf.value) {
    case 'cpu':
      return {
        bigValue: currentCpu.value.usage + '%',
        color: 'var(--chart-1)',
        history: cpuHistory.value,
        yMin: 0,
        yMax: 100,
        details: [
          { label: t('monitor.cores'), value: String(currentCpu.value.cores) },
          { label: t('monitor.processCount'), value: String(currentCpu.value.processes) },
          { label: t('monitor.handleCount'), value: String(currentCpu.value.handles) },
          { label: t('monitor.load1'), value: String(currentCpu.value.load1 ?? '-') },
          { label: t('monitor.load5'), value: String(currentCpu.value.load5 ?? '-') },
          { label: t('monitor.load15'), value: String(currentCpu.value.load15 ?? '-') },
          { label: t('companion.cpuUser'), value: (currentCpu.value.user ?? 0) + '%' },
          { label: t('companion.cpuSystem'), value: (currentCpu.value.system ?? 0) + '%' },
          { label: t('companion.cpuIowait'), value: (currentCpu.value.iowait ?? 0) + '%' },
          { label: t('companion.cpuTotal'), value: (currentCpu.value.total ?? currentCpu.value.usage ?? 0) + '%' }
        ]
      }
    case 'memory':
      return {
        bigValue: currentMem.value.usage + '%',
        color: 'var(--chart-2)',
        history: memHistory.value,
        yMin: 0,
        yMax: 100,
        details: [
          { label: t('monitor.total'), value: currentMem.value.total.toFixed(2) + ' GB' },
          { label: t('monitor.used'), value: currentMem.value.used.toFixed(2) + ' GB' },
          { label: t('monitor.free'), value: currentMem.value.free.toFixed(2) + ' GB' },
          { label: t('monitor.cached'), value: (currentMem.value.cached?.toFixed(2) ?? '-') + ' GB' },
          { label: t('monitor.buffers'), value: (currentMem.value.buffers?.toFixed(2) ?? '-') + ' GB' },
          { label: t('companion.swapMem'), value: currentSwap.value.total
            ? currentSwap.value.used.toFixed(2) + ' / ' + currentSwap.value.total.toFixed(2) + ' GB (' + (currentSwap.value.usage ?? 0) + '%)'
            : '-' }
        ]
      }
    case 'disk':
      return {
        bigValue: currentDisk.value.usage + '%',
        color: 'var(--chart-3)',
        history: diskHistory.value,
        yMin: 0,
        yMax: 100,
        details: [
          { label: t('monitor.total'), value: currentDisk.value.total },
          { label: t('monitor.used'), value: currentDisk.value.used }
        ]
      }
    case 'network':
      return {
        bigValue: formatBytes(currentNet.value.rx + currentNet.value.tx) + '/s',
        color: 'var(--chart-4)',
        color2: 'var(--chart-4-alt)',
        history: netRxHistory.value,
        history2: netTxHistory.value,
        yMin: 0,
        details: [
          { label: t('monitor.rx'), value: formatBytes(currentNet.value.rx) + '/s' },
          { label: t('monitor.tx'), value: formatBytes(currentNet.value.tx) + '/s' }
        ]
      }
    default:
      return { bigValue: '', color: 'var(--text-primary)', history: [] as number[], details: [] }
  }
})

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatIo(val: number | undefined): string {
  if (val == null) return '-'
  return formatBytes(val)
}

function formatUptime(sec: number | undefined): string {
  const s = Number(sec || 0)
  if (!s) return ''
  const d = Math.floor(s / 86400)
  const h = Math.floor((s % 86400) / 3600)
  const m = Math.floor((s % 3600) / 60)
  if (d > 0) return `${d}d ${h}h ${m}m`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

function fmtWidth(v: unknown): string {
  const n = Number(v)
  if (!Number.isFinite(n)) return '0%'
  return Math.min(100, Math.max(0, n)) + '%'
}

const filteredProcesses = computed(() => {
  const q = processSearch.value.trim().toLowerCase()
  if (!q) return processList.value
  return processList.value.filter((p: any) =>
    String(p.name).toLowerCase().includes(q) ||
    String(p.user).toLowerCase().includes(q) ||
    String(p.pid).includes(q)
  )
})

const filteredPorts = computed(() => {
  const q = portSearch.value.trim().toLowerCase()
  if (!q) return portList.value
  return portList.value.filter((p: any) =>
    String(p.localAddr).toLowerCase().includes(q) ||
    String(p.process).toLowerCase().includes(q)
  )
})

const filteredNetCards = computed(() => {
  const q = netSearch.value.trim().toLowerCase()
  if (!q) return netCardList.value
  return netCardList.value.filter((n: any) =>
    String(n.name).toLowerCase().includes(q) ||
    String(n.mac).toLowerCase().includes(q) ||
    (n.ipAddrs || []).some((ip: string) => ip.toLowerCase().includes(q)) ||
    String(n.bondMaster).toLowerCase().includes(q) ||
    (n.bondSlaves || []).some((s: string) => s.toLowerCase().includes(q))
  )
})

const filteredDisks = computed(() => {
  const q = diskSearch.value.trim().toLowerCase()
  if (!q) return diskList.value
  return diskList.value.filter((d: any) =>
    String(d.name).toLowerCase().includes(q)
  )
})

const filteredServices = computed(() => {
  const q = serviceSearch.value.trim().toLowerCase()
  if (!q) return serviceList.value
  return serviceList.value.filter((s: any) =>
    String(s.name).toLowerCase().includes(q) ||
    String(s.description).toLowerCase().includes(q)
  )
})

const filteredDevices = computed(() => {
  const q = deviceSearch.value.trim().toLowerCase()
  if (!q) return deviceList.value
  return deviceList.value.filter((d: any) =>
    String(d.id).toLowerCase().includes(q) ||
    String(d.class).toLowerCase().includes(q) ||
    String(d.vendor).toLowerCase().includes(q) ||
    String(d.product).toLowerCase().includes(q) ||
    String(d.driver).toLowerCase().includes(q) ||
    String(d.serial).toLowerCase().includes(q)
  )
})

// Devices grouped by category for the tree table. Search filters the flat
// list first, so empty categories disappear while searching.
const deviceCatOrder = ['processor', 'memory', 'storage', 'network', 'display', 'bus', 'other']
const deviceTreeData = computed(() => {
  const groups = new Map<string, any[]>()
  for (const d of filteredDevices.value) {
    const cat = d.category || 'other'
    if (!groups.has(cat)) groups.set(cat, [])
    groups.get(cat)!.push(d)
  }
  const rows: any[] = []
  for (const cat of deviceCatOrder) {
    const kids = groups.get(cat)
    if (!kids?.length) continue
    rows.push({
      rowKey: `cat:${cat}`,
      isGroup: true,
      category: cat,
      count: kids.length,
      children: kids.map((d, i) => ({ ...d, rowKey: `${cat}:${i}:${d.id}` }))
    })
  }
  return rows
})

const filteredSensors = computed(() => {
  const list = hardwareSensors.value?.sensors || []
  const q = sensorSearch.value.trim().toLowerCase()
  if (!q) return list
  return list.filter((s: any) =>
    String(s.name).toLowerCase().includes(q) ||
    String(s.value).toLowerCase().includes(q) ||
    String(s.source).toLowerCase().includes(q)
  )
})

function serviceStateClass(row: any) {
  if (row.active === 'active') return 'state-ok'
  if (row.active === 'failed') return 'state-bad'
  return 'state-idle'
}

function sensorStatusClass(status: string) {
  const s = String(status || '').toLowerCase()
  if (s === 'ok') return 'state-ok'
  if (s === 'nc' || s === 'cr' || s === 'nr' || s.includes('alarm')) return 'state-bad'
  return 'state-idle'
}

const serviceActionMessage = computed(() => {
  if (!serviceActionTarget.value) return ''
  return t('monitor.service.actionConfirm', {
    action: t('monitor.service.' + serviceActionCmd.value),
    name: serviceActionTarget.value.name
  })
})

const serviceDetailRows = computed(() => {
  const d = serviceDetail.value
  if (!d) return []
  return [
    { label: t('monitor.service.description'), value: d.Description },
    { label: t('monitor.service.load'), value: d.LoadState },
    { label: t('monitor.service.active'), value: d.SubState && d.SubState !== d.ActiveState ? `${d.ActiveState} (${d.SubState})` : d.ActiveState },
    { label: t('monitor.service.enabled'), value: d.UnitFileState },
    { label: 'PID', value: d.ExecMainPID && d.ExecMainPID !== '0' ? d.ExecMainPID : '' },
    { label: t('monitor.memory'), value: memBytes(d.MemoryCurrent) }
  ].filter(r => r.value)
})

function memBytes(v: unknown): string {
  const n = Number(v)
  if (!Number.isFinite(n) || n <= 0) return ''
  return formatBytes(n)
}

const systemGroups = computed(() => {
  if (!systemInfo.value) return []
  return [
    {
      title: t('monitor.system'),
      items: [
        { label: t('monitor.user'), value: systemInfo.value.user || '' },
        { label: t('companion.uptime'), value: formatUptime(systemInfo.value.uptimeSec) },
        { label: t('monitor.os'), value: systemInfo.value.os || '' },
        { label: t('monitor.version'), value: systemInfo.value.version || '' },
        { label: t('monitor.kernel'), value: systemInfo.value.kernel || '' },
        { label: t('monitor.hostname'), value: systemInfo.value.hostname || '' },
        { label: t('monitor.localIP'), value: systemInfo.value.localIP || '' }
      ].filter(i => i.value)
    },
    {
      title: t('monitor.cpu'),
      items: [
        { label: t('monitor.cpuModel'), value: systemInfo.value.cpuModel || '' },
        { label: t('monitor.cores'), value: String(systemInfo.value.cores || '') },
        { label: t('monitor.arch'), value: systemInfo.value.arch || '' },
        { label: t('monitor.cpuFreq'), value: systemInfo.value.cpuFreq ? systemInfo.value.cpuFreq + ' MHz' : '' },
        { label: t('monitor.memTotal'), value: systemInfo.value.memTotal ? systemInfo.value.memTotal + ' GB' : '' },
        { label: t('monitor.diskTotal'), value: systemInfo.value.diskTotal || '' }
      ].filter(i => i.value)
    },
    {
      title: t('monitor.clock'),
      items: [
        { label: t('monitor.timezone'), value: systemInfo.value.timezone || '' },
        { label: t('monitor.clock'), value: hostClockText.value },
        { label: t('monitor.skew'), value: clockSkewText.value }
      ].filter(i => i.value && i.value !== '-')
    },
    ].filter(g => g.items.length > 0)
})

// Host clock: systemInfo.epochSec is the host's POSIX time at the moment the
// system payload arrived (hostClockAt). Extrapolating with the live tick lets
// the host clock keep ticking between payload refreshes, and the skew to the
// local clock stays constant. (Same approach as MonitorOverviewSidebar.)
const hostClockAt = ref(0)
const clockNow = ref(0)
let clockTimer: ReturnType<typeof setInterval> | null = null

const hostClockText = computed(() => {
  const base = Number(systemInfo.value?.epochSec)
  if (!base || !hostClockAt.value) return '-'
  const liveMs = base * 1000 + (clockNow.value - hostClockAt.value)
  const tz = systemInfo.value?.timezone
  try {
    return new Intl.DateTimeFormat(undefined, {
      timeZone: tz,
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
    }).format(new Date(liveMs))
  } catch {
    return new Date(liveMs).toLocaleString(undefined, { hour12: false })
  }
})

const clockSkewText = computed(() => {
  const base = Number(systemInfo.value?.epochSec)
  if (!base || !hostClockAt.value) return '-'
  // Positive = host clock is ahead of the local machine.
  const s = (base * 1000 - hostClockAt.value) / 1000
  return formatSkew(s)
})

function formatSkew(seconds: number): string {
  const sign = seconds < 0 ? '-' : '+'
  const abs = Math.abs(seconds)
  if (abs < 1) return `${sign}${abs.toFixed(1)}s`
  const d = Math.floor(abs / 86400)
  const h = Math.floor((abs % 86400) / 3600)
  const m = Math.floor((abs % 3600) / 60)
  const s = Math.round(abs % 60)
  if (d > 0) return `${sign}${d}d ${h}h ${m}m`
  if (h > 0) return `${sign}${h}h ${m}m`
  if (m > 0) return `${sign}${m}m ${s}s`
  return `${sign}${s}s`
}

const killMessage = computed(() => {
  if (!killTarget.value) return ''
  const name = killTarget.value.name || ''
  const pid = killTarget.value.pid || ''
  if (killType.value === 'kill') {
    return t('monitor.forceKillConfirm', { name, pid })
  }
  return t('monitor.killConfirm', { name, pid })
})

function togglePause() {
  paused.value = !paused.value
  SetMonitorPaused(props.sessionId, paused.value).catch(() => {})
}

async function onProcessRowClick(row: any) {
  selectedProcess.value = row
  await fetchProcessDetail(row.pid)
  detailDrawerVisible.value = true
}

function onTableSignal(row: any, e: MouseEvent) {
  selectedProcess.value = row
  signalMenuRef.value?.toggle(e.currentTarget as HTMLElement)
}

async function fetchProcessDetail(pid: number) {
  try {
    const detail = await GetProcessDetail(props.sessionId, pid)
    processDetail.value = detail
  } catch (e: any) {
    msg.error(e?.message || 'Failed to fetch process detail')
    processDetail.value = null
  }
}

function onDetailAction(cmd: string) {
  if (!selectedProcess.value) return
  killTarget.value = selectedProcess.value
  killType.value = cmd
  killDialogVisible.value = true
}

const signalMenuRef = ref<InstanceType<typeof Menu> | null>(null)
const signalMenuVisible = ref(false)
function onSignal(cmd: string) {
  signalMenuVisible.value = false
  onDetailAction(cmd)
}

async function confirmKill() {
  if (!killTarget.value) return
  const pid = killTarget.value.pid
  const signalMap: Record<string, string> = {
    term: 'TERM',
    kill: 'KILL',
    hup: 'HUP',
    int: 'INT'
  }
  const signal = signalMap[killType.value] || 'TERM'
  try {
    await KillProcess(props.sessionId, pid, signal)
    msg.success('Signal sent')
    killDialogVisible.value = false
  } catch (e: any) {
    msg.error(e?.message || 'Failed to send signal')
  }
}

async function toggleDisks() {
  showDisks.value = !showDisks.value
  if (!showDisks.value || disks.value.length > 0) return
  diskLoading.value = true
  try {
    disks.value = await GetDisks(props.sessionId)
  } catch {
    disks.value = []
  } finally {
    diskLoading.value = false
  }
}

async function fetchPorts() {
  loadingPorts.value = true
  try {
    portList.value = await GetPorts(props.sessionId)
  } catch (e: any) {
    msg.error(e?.message || 'Failed to fetch ports')
    portList.value = []
  } finally {
    loadingPorts.value = false
  }
}

async function fetchDisks() {
  loadingDisks.value = true
  try {
    diskList.value = await GetDisks(props.sessionId)
  } catch (e: any) {
    msg.error(e?.message || 'Failed to fetch disks')
    diskList.value = []
  } finally {
    loadingDisks.value = false
  }
}

async function fetchNetCards() {
  loadingNetCards.value = true
  try {
    netCardList.value = await GetNetworkCards(props.sessionId)
  } catch (e: any) {
    msg.error(e?.message || 'Failed to fetch network cards')
    netCardList.value = []
  } finally {
    loadingNetCards.value = false
  }
}

async function fetchServices() {
  loadingServices.value = true
  try {
    serviceList.value = await GetServices(props.sessionId)
  } catch (e: any) {
    msg.error(e?.message || 'Failed to fetch services')
    serviceList.value = []
  } finally {
    loadingServices.value = false
  }
}

async function fetchDevices() {
  loadingDevices.value = true
  try {
    deviceList.value = await GetDevices(props.sessionId)
  } catch (e: any) {
    msg.error(e?.message || 'Failed to fetch devices')
    deviceList.value = []
  } finally {
    loadingDevices.value = false
  }
}

async function fetchHardwareFru() {
  loadingHardwareFru.value = true
  try {
    hardwareFru.value = await GetHardwareFru(props.sessionId)
  } catch (e: any) {
    msg.error(e?.message || 'Failed to fetch FRU info')
    hardwareFru.value = null
  } finally {
    loadingHardwareFru.value = false
  }
}

async function fetchHardwareLan() {
  loadingHardwareLan.value = true
  try {
    hardwareLan.value = await GetHardwareLan(props.sessionId)
  } catch (e: any) {
    msg.error(e?.message || 'Failed to fetch IPMI LAN info')
    hardwareLan.value = []
  } finally {
    loadingHardwareLan.value = false
  }
}

async function fetchHardwareSensors() {
  loadingHardwareSensors.value = true
  try {
    hardwareSensors.value = await GetHardwareSensors(props.sessionId)
  } catch (e: any) {
    msg.error(e?.message || 'Failed to fetch hardware sensors')
    hardwareSensors.value = null
  } finally {
    loadingHardwareSensors.value = false
  }
}

function onServiceActionMenu(row: any, e: MouseEvent) {
  serviceActionTarget.value = row
  serviceMenuRef.value?.toggle(e.currentTarget as HTMLElement)
}

function onServiceCmd(cmd: string) {
  serviceMenuVisible.value = false
  serviceActionCmd.value = cmd
  serviceDialogVisible.value = true
}

async function confirmServiceAction() {
  if (!serviceActionTarget.value) return
  const name = serviceActionTarget.value.name
  const cmd = serviceActionCmd.value
  try {
    await ServiceAction(props.sessionId, name, cmd)
    msg.success(`${cmd} ${name} OK`)
    serviceDialogVisible.value = false
    fetchServices()
  } catch (e: any) {
    msg.error(e?.message || 'Failed to run service action')
  }
}

async function onServiceRowClick(row: any) {
  serviceDetailName.value = row.name
  serviceDetail.value = null
  serviceLogs.value = ''
  svcDrawerTab.value = 'detail'
  serviceDetailVisible.value = true
  loadingServiceDetail.value = true
  try {
    serviceDetail.value = await GetServiceDetail(props.sessionId, row.name)
  } catch (e: any) {
    msg.error(e?.message || 'Failed to fetch service detail')
  } finally {
    loadingServiceDetail.value = false
  }
}

function onServiceLogsTab() {
  svcDrawerTab.value = 'logs'
  if (svcDrawerWidth.value < logsTargetWidth()) svcDrawerWidth.value = logsTargetWidth()
  // Always re-fetch on tab entry so the view is fresh; journalctl is cheap.
  fetchServiceLogs()
}

function onLogLinesChange() {
  fetchServiceLogs()
}

async function fetchServiceLogs() {
  if (!serviceDetailName.value) return
  loadingServiceLogs.value = true
  try {
    serviceLogs.value = await GetServiceLogs(props.sessionId, serviceDetailName.value, logLines.value)
    if (logAutoScroll.value) {
      nextTick(() => {
        const el = logViewerRef.value
        if (el) el.scrollTop = el.scrollHeight
      })
    }
  } catch (e: any) {
    msg.error(e?.message || 'Failed to fetch service logs')
    serviceLogs.value = ''
  } finally {
    loadingServiceLogs.value = false
  }
}

function showContextMenu(e: MouseEvent) {
  const selection = window.getSelection()?.toString().trim()
  if (!selection) return
  e.preventDefault()
  ctxMenuRef.value?.openAt(e.clientX, e.clientY, selection)
}

function copyContextText(text: unknown) {
  if (typeof text !== 'string' || !text) return
  navigator.clipboard.writeText(text).then(() => {
    msg.success(t('common.copied'))
  }).catch(() => {
    // fallback
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    msg.success(t('common.copied'))
  })
  ctxMenuVisible.value = false
}

function onDetailSectionContextMenu(e: MouseEvent) {
  const target = e.target as HTMLElement
  const detailValue = target.closest('.detail-value') as HTMLElement | null
  if (detailValue) {
    showContextMenu(e)
  }
}

function resolveColor(cssVar: string): string {
  const match = cssVar.match(/var\((--[\w-]+)\)/)
  if (match) {
    return getComputedStyle(document.documentElement).getPropertyValue(match[1]).trim()
  }
  return cssVar
}

function drawChart() {
  const canvas = chartCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  ctx.scale(dpr, dpr)

  const w = rect.width
  const h = rect.height
  const history = currentPerf.value.history
  const history2 = currentPerf.value.history2 as number[] | undefined

  ctx.clearRect(0, 0, w, h)

  if (history.length < 2) return

  const yMin = currentPerf.value.yMin ?? 0
  let yMax = currentPerf.value.yMax
  if (yMax == null) {
    const allVals = [...history]
    if (history2) allVals.push(...history2)
    yMax = Math.max(...allVals, yMin + 1)
  }
  const range = yMax - yMin
  const padding = 4

  // Grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.05)'
  ctx.lineWidth = 1
  for (let i = 1; i < 5; i++) {
    const y = h - (h * i / 5)
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(w, y)
    ctx.stroke()
  }

  const mainColor = resolveColor(currentPerf.value.color)
  const altColor = currentPerf.value.color2 ? resolveColor(currentPerf.value.color2) : null

  // Helper to draw a line
  const ctx2 = ctx
  function drawLine(data: number[], color: string, fill?: boolean) {
    ctx2.strokeStyle = color
    ctx2.lineWidth = 2
    ctx2.beginPath()
    data.forEach((val: number, i: number) => {
      const x = (i / (data.length - 1)) * w
      const normalizedVal = Math.max(Math.min(val, yMax!) - yMin, 0)
      const y = h - padding - ((normalizedVal / range) * (h - padding * 2))
      if (i === 0) ctx2.moveTo(x, y)
      else ctx2.lineTo(x, y)
    })
    ctx2.stroke()

    if (fill) {
      ctx2.fillStyle = color + '20'
      ctx2.beginPath()
      data.forEach((val: number, i: number) => {
        const x = (i / (data.length - 1)) * w
        const normalizedVal = Math.max(Math.min(val, yMax!) - yMin, 0)
        const y = h - padding - ((normalizedVal / range) * (h - padding * 2))
        if (i === 0) ctx2.moveTo(x, y)
        else ctx2.lineTo(x, y)
      })
      ctx2.lineTo(w, h)
      ctx2.lineTo(0, h)
      ctx2.closePath()
      ctx2.fill()
    }
  }

  // Draw second line first (so it appears behind the main line)
  if (history2 && history2.length >= 2) {
    drawLine(history2, altColor || mainColor)
  }

  // Draw main line with fill
  drawLine(history, mainColor, true)
}

let unlisten: (() => void) | null = null

onMounted(() => {
  // Drive the live host clock (1s local tick extrapolating from epochSec).
  clockNow.value = Date.now()
  clockTimer = window.setInterval(() => { clockNow.value = Date.now() }, 1000)

  unlisten =Events.On('session:data', (ev) => { const data: any = ev.data;
    if (data?.id !== props.sessionId) return
    try {
      const payload = JSON.parse(data.data)
      if (payload.type === 'system') {
        systemInfo.value = payload.system
        return
      }
      if (payload.type === 'performance') {
        if (payload.cpu) {
          currentCpu.value = payload.cpu
          pushHistory(cpuHistory.value, payload.cpu.usage || 0)
        }
        if (payload.memory) {
          currentMem.value = payload.memory
          pushHistory(memHistory.value, payload.memory.usage || 0)
        }
        if (payload.swap) {
          currentSwap.value = payload.swap
        }
        if (payload.disk) {
          currentDisk.value = payload.disk
          pushHistory(diskHistory.value, payload.disk.usage || 0)
        }
        if (payload.network) {
          currentNet.value = payload.network
          pushHistory(netRxHistory.value, payload.network.rx || 0)
          pushHistory(netTxHistory.value, payload.network.tx || 0)
          if (Array.isArray(payload.nets)) nets.value = payload.nets
        }
        if (Array.isArray(payload.cpus)) cpus.value = payload.cpus
      }
      if (payload.type === 'processes' && payload.processes) {
        processList.value = payload.processes
        if (payload.summary) {
          if (payload.summary.cpu) {
            processSummaryCpu.value = payload.summary.cpu
          }
          if (payload.summary.memory) {
            processSummaryMem.value = payload.summary.memory
          }
        }
      }
      nextTick(drawChart)
    } catch {
      // ignore parse errors
    }
   })

  // Notify backend of initial active tab
  SetMonitorActiveTab(props.sessionId, activeTab.value).catch(() => {})
})

onActivated(() => {
  // Sync active tab when component is reactivated from KeepAlive cache
  SetMonitorActiveTab(props.sessionId, activeTab.value).catch(() => {})
  SetMonitorPaused(props.sessionId, false).catch(() => {})
})

onDeactivated(() => {
  // Pause data collection when component is hidden by KeepAlive
  SetMonitorPaused(props.sessionId, true).catch(() => {})
})

onUnmounted(() => {
  if (unlisten) unlisten()
  if (clockTimer) window.clearInterval(clockTimer)
  clockTimer = null
  SetMonitorPaused(props.sessionId, true).catch(() => {})
})

watch(() => currentPerf.value.history, drawChart, { deep: true })
watch(() => currentPerf.value.history2, drawChart, { deep: true })
watch(selectedPerf, () => nextTick(drawChart))
watch(activeTab, (tab) => {
  SetMonitorActiveTab(props.sessionId, tab).catch(() => {})
  if (tab === 'ports' && portList.value.length === 0 && !loadingPorts.value) {
    fetchPorts()
  }
  if (tab === 'disks' && diskList.value.length === 0 && !loadingDisks.value) {
    fetchDisks()
  }
  if (tab === 'network' && netCardList.value.length === 0 && !loadingNetCards.value) {
    fetchNetCards()
  }
  if (tab === 'services' && serviceList.value.length === 0 && !loadingServices.value) {
    fetchServices()
  }
  if (tab === 'devices' && deviceList.value.length === 0 && !loadingDevices.value) {
    fetchDevices()
  }
  if (tab === 'health') {
    if (hardwareFru.value === null && !loadingHardwareFru.value) {
      fetchHardwareFru()
    }
    if (hardwareLan.value.length === 0 && !loadingHardwareLan.value) {
      fetchHardwareLan()
    }
    if (!hardwareSensors.value && !loadingHardwareSensors.value) {
      fetchHardwareSensors()
    }
  }
})
</script>

<style scoped>
.monitor-tab {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-base);
  position: relative;
  overflow: hidden;
}

.monitor-tabs-header {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.tab-item {
  padding: 0.5rem 1.25rem;
  font-size: 0.8125rem;
  font-family: var(--font-ui);
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
  border-bottom: 0.125rem solid transparent;
  transition: all 0.15s ease;
}

.tab-item:hover {
  color: var(--text-primary);
}

.tab-item.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.tab-pane {
  flex: 1;
  overflow: hidden;
  display: flex;
}

/* Performance pane */
.performance-pane {
  display: flex;
}

.perf-sidebar {
  width: 11.25rem;
  flex-shrink: 0;
  border-right: 1px solid var(--border-subtle);
  padding: 0.5rem;
  overflow-y: auto;
}

.perf-nav-item {
  padding: 0.625rem 0.75rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  margin-bottom: 0.25rem;
  transition: background 0.12s ease;
}

.perf-nav-item:hover {
  background: var(--bg-hover);
}

.perf-nav-item.active {
  background: var(--accent-subtle);
}

.perf-nav-name {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-family: var(--font-ui);
}

.perf-nav-value {
  font-size: 1.125rem;
  font-weight: 600;
  font-family: var(--font-mono);
  margin: 0.25rem 0;
}

.perf-nav-bar {
  height: 0.25rem;
  background: var(--bg-hover);
  border-radius: 0.125rem;
  overflow: hidden;
}

.perf-nav-bar-inner {
  height: 100%;
  border-radius: 0.125rem;
  transition: width 0.3s ease;
}

.perf-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 1rem 1.25rem;
  overflow-y: auto;
  min-height: 0;
}

.perf-big-value {
  font-size: 3rem;
  font-weight: 700;
  font-family: var(--font-mono);
  margin-bottom: 0.75rem;
}

.perf-chart {
  height: 11.25rem;
  width: 100%;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.perf-details {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr));
  gap: 0.75rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-subtle);
}

.perf-detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.detail-label {
  font-size: 0.6875rem;
  color: var(--text-muted);
  font-family: var(--font-ui);
}

.detail-value {
  font-size: 0.875rem;
  color: var(--text-primary);
  font-family: var(--font-mono);
  user-select: text;
}

/* Expandable per-core / per-NIC / per-disk lists */
.perf-extras {
  margin-top: 1.125rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-subtle);
}
.perf-sub-toggle {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  font-family: var(--font-ui);
  user-select: none;
  padding: 0.125rem 0 0.375rem;
}
.perf-sub-toggle:hover { color: var(--text-primary); }
.perf-sub-toggle .chev { transition: transform 0.15s ease; }
.perf-sub-toggle .chev.open { transform: rotate(90deg); }
.perf-sub-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  max-height: 13.75rem;
  overflow-y: auto;
}
.perf-sub-row {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 0.75rem;
  min-width: 0;
  padding: 1px 0.25rem;
  border-radius: 0.25rem;
  transition: background 0.12s ease;
}
.perf-sub-row:hover {
  background: var(--bg-hover);
}
.sub-name {
  flex: 1;
  min-width: 3.75rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
  font-family: var(--font-ui);
}
.sub-bar {
  flex: 1;
  height: 0.375rem;
  max-width: 10rem;
  border-radius: 62.4375rem;
  background: var(--bg-hover);
  overflow: hidden;
}
.sub-fill {
  height: 100%;
  border-radius: 62.4375rem;
  background: linear-gradient(90deg, var(--accent), var(--accent-glow));
  transition: width 0.3s ease;
}
.sub-val {
  min-width: 3.5rem;
  text-align: right;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
}
.sub-val.tx { color: #f59e0b; }
.perf-sub-row.net .sub-val {
  width: 6.5rem;
  min-width: 0;
  text-align: right;
  white-space: nowrap;
}
.perf-sub-empty {
  padding: 0.5rem 0;
  color: var(--text-muted);
  font-size: 0.75rem;
}

/* Processes pane */
.processes-pane {
  flex-direction: column;
  padding: 0.75rem;
}

.process-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  flex-shrink: 0;
}

.process-summary {
  display: flex;
  gap: 1.25rem;
  padding: 0.5rem 0.75rem;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow-x: auto;
  flex: 1;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  min-width: 3.75rem;
  justify-content: center;
}

.summary-label {
  font-size: 0.625rem;
  color: var(--text-muted);
  font-family: var(--font-ui);
  text-transform: uppercase;
  height: 0.875rem;
  line-height: 0.875rem;
}

.summary-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.process-actions {
  flex-shrink: 0;
}

.process-search {
  width: 17.5rem;
  margin-bottom: 0.5rem;
  flex-shrink: 0;
}

.process-table {
  flex: 1;
  min-height: 0;
}

.process-table :deep(.el-table__row) {
  cursor: pointer;
}

/* System pane */
.system-pane {
  padding: 1.25rem;
  overflow-y: auto;
}

.system-content {
  max-width: 37.5rem;
}

.system-group {
  margin-bottom: 1.5rem;
}

.system-group-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-ui);
  margin-bottom: 0.5rem;
  padding-bottom: 0.375rem;
  border-bottom: 1px solid var(--border-subtle);
}

.system-group-items {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.system-row {
  display: flex;
  align-items: baseline;
  padding: 0.5rem 0;
  gap: 2.5rem;
  border-bottom: 1px solid var(--border-subtle);
}

.system-row:last-child {
  border-bottom: none;
}

.system-row-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: var(--font-ui);
  flex-shrink: 0;
  width: 7.5rem;
  min-width: 7.5rem;
}

.system-row-value {
  font-size: 0.8125rem;
  color: var(--text-primary);
  font-family: var(--font-mono);
  word-break: break-all;
  text-align: left;
  flex: 1;
  user-select: text;
}

.system-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  font-size: 0.875rem;
}

/* Process detail drawer */
.process-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.process-detail .detail-section {
  flex: 1;
  overflow-y: auto;
  padding: 0 1rem;
}

.process-detail .detail-row {
  display: flex;
  padding: 0.625rem 0;
  border-bottom: 1px solid var(--border-subtle);
  gap: 0.75rem;
}

.process-detail .detail-row:last-child {
  border-bottom: none;
}

.process-detail .detail-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: var(--font-ui);
  flex-shrink: 0;
  width: 6.25rem;
  min-width: 6.25rem;
}

.process-detail .detail-value {
  font-size: 0.8125rem;
  color: var(--text-primary);
  font-family: var(--font-mono);
  word-break: break-all;
  flex: 1;
  user-select: text;
}

.process-detail .detail-value.cmdline {
  white-space: pre-wrap;
  line-height: 1.5;
}

.process-detail .io-stats {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.process-detail .detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid var(--border-subtle);
  margin-top: 0.75rem;
}

.process-detail-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  font-size: 0.875rem;
}

/* Detail drawer (inside monitor-tab) */
.detail-drawer-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
  z-index: 99;
}

.detail-drawer-backdrop.open {
  opacity: 1;
  pointer-events: auto;
}

.detail-drawer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 30rem;
  background: var(--bg-elevated);
  border-left: 1px solid var(--border-subtle);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.detail-drawer.open {
  transform: translateX(0);
}

.detail-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.detail-drawer-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-ui);
}

/* On-demand tabs (ports, disks, network) */
.od-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  flex-shrink: 0;
  gap: 0.75rem;
}

.od-search {
  width: 15rem;
}

.ports-pane,
.disks-pane,
.network-pane,
.services-pane,
.devices-pane,
.health-pane {
  flex-direction: column;
  padding: 0;
}

.od-table {
  flex: 1;
  min-height: 0;
}

.od-table :deep(.cell) {
  user-select: text;
}

/* Services / devices / hardware health */
.svc-state {
  font-variant-numeric: tabular-nums;
}
.svc-state.state-ok {
  color: #67c23a;
}
.svc-state.state-bad {
  color: #f56c6c;
}
.svc-state.state-idle {
  color: var(--text-muted);
}

.health-top {
  flex: 0 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.health-cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  padding: 0 0.75rem;
}

.health-card {
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.health-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  flex-shrink: 0;
}

.health-card-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.health-card-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.health-search {
  width: 11.25rem;
}

.health-card-body {
  padding: 0 0.75rem 0.625rem;
  min-height: 1.5rem;
}

.health-bottom {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.health-bottom-hint {
  padding: 0 0.75rem 0.75rem;
}

/* Single-column label/value grid for FRU and IPMI LAN blocks */
.info-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0;
}

.health-table {
  flex: 1;
}

.health-hint {
  flex: 1;
  color: var(--text-muted);
  font-size: 0.75rem;
}

/* Service drawer: detail/logs tabs and the k8s-style log viewer */
/* Left-edge drag handle to resize the service drawer (same as the k8s one) */
.svc-resizer {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  width: 0.3125rem;
  cursor: col-resize;
  z-index: 101;
  background: transparent;
  transition: background 0.15s ease;
}

.svc-resizer:hover {
  background: var(--accent, #4096ff);
}

.svc-drawer-tabs {
  display: flex;
  gap: 0.25rem;
  padding: 0 0.75rem;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.svc-tab {
  padding: 0.5rem 0.625rem;
  font-size: 0.75rem;
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
  border-bottom: 0.125rem solid transparent;
}

.svc-tab.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.svc-detail-pane {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.svc-detail-pane .process-detail {
  flex: 1;
  min-height: 0;
}

.svc-logs-pane {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.svc-logs-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  flex-shrink: 0;
  /* wrap instead of squeezing controls (same as the k8s log toolbar) */
  flex-wrap: wrap;
}

.svc-logs-toolbar :deep(.el-checkbox) {
  margin-right: 0;
}

.flex-spacer {
  flex: 1;
}

.svc-log-lines {
  width: 3.75rem;
  flex-shrink: 0;
}

.svc-log-viewer {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 0.75rem;
  font-family: var(--font-mono, monospace);
  font-size: 0.75rem;
  background: var(--bg-base);
  user-select: text;
}

/* Line model identical to the k8s log viewer */
.svc-log-viewer .log-line {
  white-space: pre-wrap;
  word-break: break-all;
}

/* No-wrap mode: keep each journal line on one row, scroll horizontally */
.svc-log-viewer.logs-nowrap .log-line {
  white-space: pre;
  word-break: normal;
}

.svc-log-viewer .log-ts {
  color: var(--text-muted);
  margin-right: 0.5rem;
}

.svc-log-viewer .log-ts:empty {
  margin-right: 0;
}

.svc-log-viewer.logs-hide-ts .log-ts {
  display: none;
}
</style>
