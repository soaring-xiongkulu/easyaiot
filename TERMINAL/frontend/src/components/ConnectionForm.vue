<template>
  <el-dialog append-to-body v-model="visible" :title="isEdit ? t('conn.editTitle') : t('conn.newTitle')" width="43.75rem" class="conn-dialog" @opened="onDialogOpened">
    <div class="conn-layout">
      <!-- Left sidebar: category icons -->
      <div class="conn-categories">
        <div
          v-for="cat in categories"
          :key="cat.key"
          class="cat-item"
          :class="{ active: category === cat.key }"
          @click="onCategorySelect(cat.key)"
        >
          <component :is="cat.icon" :size="'1.25rem'" />
          <span>{{ cat.label }}</span>
        </div>
      </div>

      <!-- Right content: sub-type grid + form -->
      <div class="conn-main">
        <!-- Sub-type icon grid -->
        <div class="subtype-grid">
          <button
            v-for="st in currentSubTypes"
            :key="st.type + (st.dbType || '') + (st.containerRuntime || '')"
            class="subtype-btn"
            :class="{ active: isSubTypeActive(st) }"
            @click="selectType(st)"
          >
            <component :is="st.icon" :size="'1.125rem'" />
            <span>{{ st.label }}</span>
          </button>
        </div>

        <!-- Form fields -->
        <div class="conn-fields">
          <el-form :model="form" label-width="5.625rem" @submit.prevent="onSave">
            <el-form-item :label="t('conn.name')">
              <div class="name-group-row">
                <el-input v-model="form.name" :placeholder="t('conn.namePlaceholder')" class="name-input" />
                <el-tree-select
                  v-model="selectedGroupId"
                  :data="groupTreeData"
                  :render-after-expand="false"
                  check-strictly
                  clearable
                  :placeholder="t('conn.noGroup')"
                  class="group-select"
                />
                <el-button class="new-group-btn" @click="onGroupSelect('__new__')" :title="t('conn.newGroup')">
                  <Plus :size="'0.875rem'" />
                </el-button>
              </div>
            </el-form-item>
            <el-form-item v-if="form.type === 'redis'" :label="t('conn.redisMode')">
              <el-radio-group v-model="form.redisMode">
                <el-radio-button value="standalone">{{ t('conn.redisModeStandalone') }}</el-radio-button>
                <el-radio-button value="sentinel">{{ t('conn.redisModeSentinel') }}</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <template v-if="isRedisSentinel">
              <el-form-item :label="t('conn.redisSentinels')" required>
                <el-input v-model="form.redisSentinels" :placeholder="t('conn.redisSentinelsPlaceholder')" />
              </el-form-item>
              <el-form-item :label="t('conn.redisMasterName')" required>
                <el-input v-model="form.redisMasterName" placeholder="mymaster" />
              </el-form-item>
            </template>
            <el-form-item :label="form.type === 's3' ? 'Endpoint' : (form.type === 'webdav' || form.type === 'url') ? 'URL' : t('conn.host')" required v-if="form.type !== 'local' && form.type !== 'wsl' && form.type !== 'serial' && form.type !== 'k8s' && form.type !== 'container' && !isRedisSentinel">
              <div class="host-port-row">
                <el-input ref="hostInputRef" v-model="form.host" class="host-input" :placeholder="form.type === 's3' ? 'e.g. https://s3.amazonaws.com' : (form.type === 'webdav' || form.type === 'url') ? 'https://dav.example.com/dav/' : t('conn.hostPlaceholder')" />
                <template v-if="form.type !== 's3' && form.type !== 'webdav' && form.type !== 'url'">
                  <span class="host-port-sep">:</span>
                  <el-input-number v-model="form.port" :min="0" :max="65535" class="port-input" />
                </template>
              </div>
            </el-form-item>
            <el-form-item v-if="form.type === 'ssh' || form.type === 'scp' || form.type === 'sftp' || form.type === 'mosh' || form.type === 'x11-desktop' || isElasticsearch" :label="t('conn.authType')">
              <el-radio-group v-model="form.authType">
                <el-radio-button v-if="form.type === 'ssh' || form.type === 'scp' || form.type === 'sftp' || form.type === 'mosh' || form.type === 'x11-desktop'" value="identity">{{ t('conn.identity') }}</el-radio-button>
                <el-radio-button value="password">{{ t('conn.password') }}</el-radio-button>
                <el-radio-button v-if="form.type === 'ssh' || form.type === 'scp' || form.type === 'sftp' || form.type === 'mosh' || form.type === 'x11-desktop'" value="key">{{ t('conn.keyPath') }}</el-radio-button>
                <el-radio-button v-if="form.type === 'ssh' || form.type === 'scp' || form.type === 'sftp' || form.type === 'mosh' || form.type === 'x11-desktop'" value="keyText">{{ t('conn.keyText') }}</el-radio-button>
                <el-radio-button v-if="form.type === 'ssh' || form.type === 'scp' || form.type === 'sftp' || form.type === 'mosh' || form.type === 'x11-desktop'" value="kerberos">{{ t('conn.kerberos') }}</el-radio-button>
                <el-radio-button v-if="(isWindows || isMac) && (form.type === 'ssh' || form.type === 'scp' || form.type === 'sftp' || form.type === 'mosh' || form.type === 'x11-desktop')" value="agent">{{ t('conn.sshAgent') }}</el-radio-button>
                <el-radio-button v-if="isElasticsearch" value="apikey">{{ t('conn.esAuthApiKey') }}</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="form.authType !== 'identity' && form.type !== 'vnc' && form.type !== 'spice' && form.type !== 'url' && !(form.type === 'database' && form.dbType === 'rqlite') && form.type !== 'local' && form.type !== 'wsl' && form.type !== 'serial' && form.type !== 'tcp' && form.type !== 'k8s' && form.type !== 'container' && !isEsApiKey" :label="form.type === 's3' ? 'Access Key' : t('conn.user')">
              <el-input v-model="form.user" :placeholder="form.type === 's3' ? 'Access Key ID' : t('conn.userPlaceholder')" />
            </el-form-item>
            <el-form-item v-if="form.type === 'rdp' && isWindows && form.authType !== 'identity'" :label="t('conn.rdpDomain')">
              <el-input v-model="form.rdpDomain" placeholder="e.g. WORKGROUP or WIN-ABC123" />
            </el-form-item>
            <el-form-item
              v-if="form.authType === 'identity' && (form.type === 'ssh' || form.type === 'scp' || form.type === 'sftp' || form.type === 'mosh' || form.type === 'x11-desktop')"
              :label="t('conn.identity')"
            >
              <div class="inline-add-row">
                <el-select v-model="form.identityId" filterable style="flex: 1; min-width: 0">
                  <el-option v-for="id in identityStore.identities" :key="id.id" :label="`${id.name} (${id.username})`" :value="id.id" />
                </el-select>
                <el-button class="inline-add-btn" :title="t('conn.newIdentity')" @click="openNewIdentityDialog">
                  <Plus :size="'0.875rem'" />
                </el-button>
              </div>
            </el-form-item>
            <template v-if="form.type === 'rdp' && isWindows">
              <el-form-item :label="t('conn.rdpEnableNLA')">
                <el-select v-model="form.rdpEnableNLA" style="width: 100%">
                  <el-option :value="true" :label="t('conn.rdpEnableNLAOn')" />
                  <el-option :value="false" :label="t('conn.rdpEnableNLAOff')" />
                </el-select>
              </el-form-item>
            </template>
            <el-form-item v-if="form.type !== 'local' && form.type !== 'wsl' && form.type !== 'serial' && form.type !== 'tcp' && form.type !== 'k8s' && form.type !== 'container' && form.type !== 'url' && form.authType !== 'identity' && ((form.authType === 'password' && form.type !== 'rdp') || (form.type === 'rdp' && !form.rdpEnableNLA) || form.type === 'vnc' || form.type === 'spice' || form.type === 'database' || form.type === 'telnet' || form.type === 'ftp' || form.type === 'smb' || form.type === 'webdav' || form.type === 's3') && !(form.type === 'database' && form.dbType === 'rqlite')" :label="form.type === 's3' ? 'Secret Key' : (isEsApiKey ? t('conn.esApiKey') : t('conn.password'))">
              <el-input v-model="form.password" type="password" show-password :key="passwordInputKey" :placeholder="form.type === 's3' ? 'Secret Access Key' : (isEsApiKey ? t('conn.esApiKeyPlaceholder') : '')" />
            </el-form-item>
            <el-form-item v-if="form.authType === 'kerberos'" :label="t('conn.kerberos')">
              <div class="field-hint">{{ t('conn.kerberosHint') }}</div>
            </el-form-item>
            <el-form-item v-if="form.authType === 'kerberos'" :label="t('conn.kerberosRealm')">
              <el-input v-model="form.kerberosRealm" :placeholder="t('conn.kerberosRealmPlaceholder')" />
              <div class="field-hint">{{ t('conn.kerberosRealmHint') }}</div>
            </el-form-item>
            <template v-if="isElasticsearch">
              <el-form-item :label="t('conn.esUseSsl')">
                <el-switch v-model="form.esUseSsl" />
              </el-form-item>
              <el-form-item v-if="form.esUseSsl" :label="t('conn.esSkipVerify')">
                <div class="nla-row">
                  <el-switch v-model="form.esSkipVerify" />
                  <span class="field-hint">{{ t('conn.esSkipVerifyHint') }}</span>
                </div>
              </el-form-item>
              <el-form-item :label="t('conn.esPathPrefix')">
                <el-input v-model="form.esPathPrefix" placeholder="/es" />
              </el-form-item>
            </template>
            <template v-if="isRedisSentinel">
              <el-form-item :label="t('conn.sentinelUser')">
                <el-input v-model="form.sentinelUser" :placeholder="t('conn.sentinelAuthHint')" />
              </el-form-item>
              <el-form-item :label="t('conn.sentinelPassword')">
                <el-input v-model="form.sentinelPassword" type="password" show-password :key="passwordInputKey" :placeholder="t('conn.sentinelAuthHint')" />
              </el-form-item>
            </template>
            <el-form-item v-if="form.authType === 'key' && (form.type === 'ssh' || form.type === 'scp' || form.type === 'sftp' || form.type === 'mosh' || form.type === 'x11-desktop')" :label="t('conn.keyPath')">
              <el-input v-model="form.keyPath" :placeholder="t('conn.keyPathPlaceholder')">
                <template #append>
                  <div class="key-path-actions">
                    <el-tooltip :content="t('conn.selectKeyFile')" placement="top">
                      <el-button :aria-label="t('conn.selectKeyFile')" @click="selectKeyFile">
                        <el-icon><FolderOpen :size="'1rem'" /></el-icon>
                      </el-button>
                    </el-tooltip>
                    <span class="key-path-divider" aria-hidden="true"></span>
                    <el-tooltip :content="t('conn.useDefaultKey')" placement="top">
                      <el-button :aria-label="t('conn.useDefaultKey')" @click="useDefaultKeyPath">
                        <el-icon><KeyRound :size="'1rem'" /></el-icon>
                      </el-button>
                    </el-tooltip>
                  </div>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item v-if="form.authType === 'keyText' && (form.type === 'ssh' || form.type === 'scp' || form.type === 'sftp' || form.type === 'mosh' || form.type === 'x11-desktop')" :label="t('conn.keyContent')">
              <template v-if="!keyContentRevealed">
                <el-button size="small" @click="keyContentRevealed = true">
                  <el-icon><Eye :size="'0.875rem'" /></el-icon>
                  <span style="margin-left: 0.25rem">{{ t('conn.keyTextReveal') }}</span>
                </el-button>
              </template>
              <template v-else>
                <el-input
                  v-model="form.keyContent"
                  type="textarea"
                  :rows="7"
                  class="key-text-area mono"
                  :placeholder="t('conn.keyContentPlaceholder')"
                  spellcheck="false"
                />
                <div class="key-content-actions">
                  <el-button size="small" @click="keyContentRevealed = false">
                    <el-icon><EyeOff :size="'0.875rem'" /></el-icon>
                    <span style="margin-left: 0.25rem">{{ t('conn.keyTextHide') }}</span>
                  </el-button>
                  <el-button size="small" @click="importKeyText">
                    <el-icon><FolderOpen :size="'0.875rem'" /></el-icon>
                    <span style="margin-left: 0.25rem">{{ t('conn.importFromFile') }}</span>
                  </el-button>
                </div>
              </template>
            </el-form-item>
            <el-form-item v-if="(form.authType === 'key' || form.authType === 'keyText') && (form.type === 'ssh' || form.type === 'scp' || form.type === 'sftp' || form.type === 'mosh' || form.type === 'x11-desktop')" :label="t('conn.keyPassphrase')">
              <el-input v-model="form.password" type="password" show-password :key="passwordInputKey" :placeholder="t('conn.keyPassphrasePlaceholder')" />
            </el-form-item>
            <el-form-item v-if="form.type === 'ssh'" :label="t('conn.fileTransferProto')">
              <el-radio-group v-model="form.fileTransferProto">
                <el-radio-button value="sftp">SFTP</el-radio-button>
                <el-radio-button value="scp">SCP</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="form.type === 'database' && form.dbType !== 'rqlite' && form.dbType !== 'redis' && form.dbType !== 'elasticsearch'" :label="t('db.databases')" :required="form.dbType === 'postgres'">
              <el-input v-model="form.dbName" :placeholder="t('db.databases')" />
            </el-form-item>
            <el-form-item v-if="form.type === 'database' && form.dbType !== 'elasticsearch' && form.dbType !== 'redis'" :label="t('db.params')">
              <el-input v-model="form.dbParams" :placeholder="defaultParamsHint" style="width:100%" />
            </el-form-item>
            <el-form-item v-if="form.type === 'local' || form.type === 'wsl'" :label="t('conn.shell')">
              <el-select v-model="form.shellPath" filterable allow-create clearable>
                <el-option
                  v-for="sh in shellOptionsForType"
                  :key="sh.value"
                  :label="sh.label"
                  :value="sh.value"
                />
              </el-select>
            </el-form-item>
            <template v-if="form.type === 'serial'">
              <el-form-item :label="t('serial.portLabel')" required>
                <div style="display:flex;gap:0.5rem;width:100%">
                  <el-select v-model="form.serialPort" :placeholder="portPlaceholder" :disabled="serialPorts.length === 0 || serialScanning" :loading="serialScanning" style="flex:1">
                    <el-option v-for="p in serialPorts" :key="p" :label="p" :value="p" />
                  </el-select>
                  <el-button :icon="RefreshCw" :loading="serialScanning" @click="scanSerialPorts">
                    {{ t('serial.scan') }}
                  </el-button>
                </div>
              </el-form-item>
              <el-form-item :label="t('serial.baudRate')">
                <el-autocomplete
                  v-model="serialBaudRateInput"
                  :fetch-suggestions="queryBaudRateSuggestions"
                  :placeholder="t('serial.baudRate')"
                  clearable
                  style="width:100%"
                />
              </el-form-item>
              <el-form-item :label="t('serial.dataBits')">
                <el-select v-model="serialDataBitsValue">
                  <el-option v-for="b in [5,6,7,8]" :key="b" :label="String(b)" :value="b" />
                </el-select>
              </el-form-item>
              <el-form-item :label="t('serial.stopBits')">
                <el-select v-model="serialStopBitsValue">
                  <el-option v-for="b in [1,1.5,2]" :key="b" :label="String(b)" :value="b" />
                </el-select>
              </el-form-item>
              <el-form-item :label="t('serial.parity')">
                <el-select v-model="serialParityValue">
                  <el-option :label="t('serial.parityNone')" value="none" />
                  <el-option :label="t('serial.parityOdd')" value="odd" />
                  <el-option :label="t('serial.parityEven')" value="even" />
                  <el-option :label="t('serial.parityMark')" value="mark" />
                  <el-option :label="t('serial.paritySpace')" value="space" />
                </el-select>
              </el-form-item>
            </template>
            <template v-if="form.type === 'smb'">
              <el-form-item :label="t('conn.smbDomain')" required>
                <el-input v-model="form.smbDomain" placeholder="e.g. WORKGROUP" />
              </el-form-item>
              <el-form-item :label="t('conn.smbShare')">
                <el-input v-model="form.smbShare" placeholder="Share name (leave empty to browse all)" />
              </el-form-item>
            </template>
            <template v-if="form.type === 's3'">
              <el-form-item :label="t('conn.s3Region')" required>
                <el-input v-model="form.s3Region" placeholder="us-east-1" />
              </el-form-item>
              <el-form-item :label="t('conn.s3Bucket')">
                <el-input v-model="form.s3Bucket" placeholder="my-bucket (leave empty to list all buckets)" />
              </el-form-item>
              <el-form-item :label="t('conn.s3UrlStyle')">
                <el-select v-model="form.s3UrlStyle">
                  <el-option label="Virtual-hosted (https://bucket.endpoint/key)" value="virtual" />
                  <el-option label="Path (https://endpoint/bucket/key)" value="path" />
                </el-select>
              </el-form-item>
            </template>
            <!-- ── K8s 字段 ── -->
            <template v-if="form.type === 'k8s'">
              <el-form-item :label="t('conn.k8sConfigSource')">
                <el-radio-group v-model="k8sSourceMode">
                  <el-radio-button value="inline">{{ t('conn.k8sConfigSourceInline') }}</el-radio-button>
                  <el-radio-button value="file">{{ t('conn.k8sConfigSourceFile') }}</el-radio-button>
                </el-radio-group>
              </el-form-item>

              <el-form-item v-if="k8sSourceMode === 'file'" :label="t('conn.k8sConfigPath')">
                <el-input v-model="form.k8sConfigPath" placeholder="~/.kube/config">
                  <template #append>
                    <el-button @click="pickKubeconfigFile">
                      <el-icon><FolderOpen :size="'1rem'" /></el-icon>
                    </el-button>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item v-else :label="t('conn.k8sConfigInline')">
                <template v-if="!k8sConfigRevealed">
                  <el-button size="small" @click="k8sConfigRevealed = true">
                    <el-icon><Eye :size="'0.875rem'" /></el-icon>
                    <span style="margin-left: 0.25rem">{{ t('conn.k8sConfigReveal') }}</span>
                  </el-button>
                </template>
                <template v-else>
                  <SyntaxEditor
                    :model-value="form.k8sConfigInline ?? ''"
                    lang="yaml"
                    class="kubeconfig-editor"
                    @update:model-value="form.k8sConfigInline = $event"
                  />
                  <div class="key-content-actions">
                    <el-button size="small" @click="k8sConfigRevealed = false">
                      <el-icon><EyeOff :size="'0.875rem'" /></el-icon>
                      <span style="margin-left: 0.25rem">{{ t('conn.k8sConfigHide') }}</span>
                    </el-button>
                    <el-button size="small" @click="importKubeconfigText">
                      <el-icon><FolderOpen :size="'0.875rem'" /></el-icon>
                      <span style="margin-left: 0.25rem">{{ t('conn.importFromFile') }}</span>
                    </el-button>
                  </div>
                </template>
              </el-form-item>

              <el-form-item :label="t('conn.k8sContext')">
                <div style="display: flex; align-items: center; gap: 0.5rem; width: 100%">
                  <el-select v-model="form.k8sContext" filterable :placeholder="k8sContextsError || ''" :loading="k8sContextsLoading" style="flex: 1">
                    <el-option v-for="c in k8sContexts" :key="c.name" :value="c.name" :label="c.current ? c.name + ' (current)' : c.name" />
                  </el-select>
                  <el-button @click="reloadK8sContexts" :loading="k8sContextsLoading" :title="t('conn.k8sReloadContexts')">
                    <el-icon><RefreshCw :size="'1rem'" /></el-icon>
                  </el-button>
                </div>
              </el-form-item>

              <el-form-item :label="t('conn.k8sNamespace')">
                <el-select
                  v-model="form.k8sNamespace"
                  filterable
                  allow-create
                  default-first-option
                  clearable
                  placeholder="Namespace"
                  style="width: 100%"
                  @change="onK8sNamespaceInput"
                >
                  <el-option v-for="ns in k8sNamespaceOptions" :key="ns" :value="ns" :label="ns" />
                </el-select>
              </el-form-item>
            </template>
            <!-- ── Container 字段 ── -->
            <template v-if="form.type === 'container'">
              <el-form-item :label="t('conn.containerTransport')">
                <el-radio-group v-model="form.containerTransport">
                  <el-radio-button value="ssh">{{ t('conn.transportSSH') }}</el-radio-button>
                  <el-radio-button value="local">{{ t('conn.transportLocal') }}</el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item v-if="form.containerTransport === 'ssh'" :label="t('conn.containerSSHRef')" required>
                <el-select
                  v-model="form.containerSSHConnId"
                  :placeholder="t('conn.containerSSHRefPlaceholder')"
                  filterable
                >
                  <el-option
                    v-for="c in sshConnections"
                    :key="c.id"
                    :label="`${c.name} (${c.user}@${c.host}:${c.port})`"
                    :value="c.id"
                  />
                </el-select>
                <div class="field-hint">
                  {{ sshConnections.length ? t('conn.containerSSHRefHint') : t('conn.containerNoSSH') }}
                </div>
              </el-form-item>
              <el-form-item v-if="form.containerTransport === 'local'">
                <div class="field-hint">{{ t('conn.containerLocalHint') }}</div>
              </el-form-item>
            </template>
            <template v-if="form.type === 'rdp' && isWindows">
              <el-form-item :label="t('rdp.resolution')">
                <el-select v-model="rdpResolution" placeholder="1280×720">
                  <el-option
                    v-for="r in rdpResolutionOptions"
                    :key="r.value"
                    :label="r.label"
                    :value="r.value"
                  />
                </el-select>
              </el-form-item>
              <el-form-item v-if="rdpResolution === RDP_CUSTOM_RESOLUTION" :label="t('rdp.customResolution')">
                <div class="rdp-custom-resolution">
                  <el-input-number v-model="rdpCustomWidth" :min="320" :max="7680" :step="8" controls-position="right" />
                  <span class="rdp-custom-resolution-x">×</span>
                  <el-input-number v-model="rdpCustomHeight" :min="240" :max="4320" :step="8" controls-position="right" />
                </div>
              </el-form-item>
            </template>
            <template v-if="form.type === 'x11-desktop'">
              <el-form-item :label="t('conn.x11DesktopDE')" required>
                <el-select v-model="form.x11DesktopDesktopType">
                  <el-option label="GNOME" value="gnome" />
                  <el-option label="KDE" value="kde" />
                  <el-option label="XFCE" value="xfce" />
                  <el-option label="MATE" value="mate" />
                  <el-option label="Cinnamon" value="cinnamon" />
                  <el-option label="Openbox" value="openbox" />
                  <el-option :label="t('conn.x11DesktopDECustom')" value="custom" />
                </el-select>
              </el-form-item>
              <el-form-item v-if="form.x11DesktopDesktopType === 'custom'"
                            :label="t('conn.x11DesktopCustomCmd')" required>
                <el-input v-model="form.x11DesktopCustomCmd"
                          :placeholder="t('conn.x11DesktopCustomCmdPlaceholder')" />
                <div class="field-hint">{{ t('conn.x11DesktopCustomCmdHint') }}</div>
              </el-form-item>
            </template>
            <el-form-item :label="t('conn.remark')">
              <el-input v-model="form.remark" type="textarea" :rows="3" />
            </el-form-item>
            <div v-if="showAdvancedToggle" class="advanced-toggle" @click="showAdvanced = !showAdvanced">
              <el-icon class="advanced-arrow" :class="{ expanded: showAdvanced }"><ChevronRight :size="'0.875rem'" /></el-icon>
              <span>{{ t('conn.advanced') }}</span>
            </div>
            <template v-if="showAdvanced">
            <el-form-item v-if="form.type === 'database'" :label="t('db.params')">
              <el-input v-model="form.dbParams" :placeholder="defaultParamsHint" style="width:100%" />
            </el-form-item>
<el-form-item v-if="form.type === 'redis'" :label="t('conn.redisKeySeparator')">
              <el-input v-model="form.redisKeySeparator" style="width: 10.0rem" />
            </el-form-item>
            <el-form-item v-if="form.type === 'ssh' || form.type === 'telnet' || form.type === 'mosh' || form.type === 'local' || form.type === 'wsl'" :label="t('conn.postLoginScript')">
              <div class="post-login-config">
                <el-radio-group v-model="postLoginMode" size="small">
                  <el-radio-button value="script">{{ t('conn.postLoginModeScript') }}</el-radio-button>
                  <el-radio-button value="expect" :disabled="form.type !== 'ssh'">{{ t('conn.postLoginModeExpect') }}</el-radio-button>
                </el-radio-group>
                <el-input
                  v-if="postLoginMode === 'script'"
                  v-model="form.postLoginScript"
                  type="textarea"
                  :rows="3"
                  :placeholder="t('conn.postLoginScriptPlaceholder')"
                />
                <div v-else class="expect-steps">
                  <div class="expect-table">
                    <div class="expect-row expect-head">
                      <span></span>
                      <span>{{ t('conn.expectColExpect') }}</span>
                      <span>{{ t('conn.expectColSend') }}</span>
                      <span>{{ t('conn.expectColTimeout') }}</span>
                      <span>{{ t('conn.expectEnter') }}</span>
                      <span></span>
                    </div>
                    <div
                      v-for="(step, idx) in form.postLoginExpectSteps"
                      :key="idx"
                      class="expect-row"
                    >
                      <span class="step-index">{{ idx + 1 }}</span>
                      <el-input
                        v-model="step.expect"
                        :placeholder="t('conn.expectPlaceholder')"
                        class="expect-input"
                      />
                      <el-input
                        v-model="step.send"
                        :placeholder="t('conn.sendPlaceholder')"
                        class="send-input"
                      />
                      <el-input-number
                        v-model="step.timeoutSecond"
                        :min="1"
                        :max="120"
                        :controls="false"
                        class="timeout-input"
                      />
                      <el-checkbox v-model="step.enter" class="enter-check" />
                      <el-button
                        link
                        type="danger"
                        class="remove-step-btn"
                        :title="t('conn.expectRemoveStep')"
                        @click="removeExpectStep(idx)"
                      >
                        <Trash2 :size="'0.875rem'" />
                      </el-button>
                    </div>
                  </div>
                  <el-button class="add-step-btn" @click="addExpectStep">
                    <Plus :size="'0.875rem'" />
                    {{ t('conn.expectAddStep') }}
                  </el-button>
                  <div class="expect-help">{{ t('conn.expectVariableHint') }}</div>
                </div>
              </div>
            </el-form-item>
            <el-form-item
              v-if="form.type === 'ssh' || form.type === 'telnet' || form.type === 'serial' || form.type === 'mosh' || form.type === 'local' || form.type === 'wsl' || form.type === 'tcp'"
              :label="t('conn.encoding')"
            >
              <el-select v-model="form.encoding" placeholder="Unicode (UTF-8)">
                <el-option label="Unicode (UTF-8)" value="utf-8" />
                <el-option label="Simplified Chinese (GBK)" value="gbk" />
                <el-option label="Simplified Chinese (GB2312)" value="gb2312" />
                <el-option label="Simplified Chinese (GB18030)" value="gb18030" />
                <el-option label="Traditional Chinese (Big5)" value="big5" />
                <el-option label="Japanese (Shift-JIS)" value="shift-jis" />
                <el-option label="Japanese (EUC-JP)" value="euc-jp" />
                <el-option label="Korean (EUC-KR)" value="euc-kr" />
              </el-select>
            </el-form-item>
            <template v-if="form.type === 'telnet'">
              <el-form-item :label="t('conn.telnetNegotiationMode')">
                <el-select v-model="form.telnetNegotiationMode">
                  <el-option :label="t('conn.telnetNegotiationActive')" value="active" />
                  <el-option :label="t('conn.telnetNegotiationPassive')" value="passive" />
                </el-select>
              </el-form-item>
              <el-form-item :label="t('conn.telnetSendMode')">
                <el-select v-model="form.telnetSendMode">
                  <el-option :label="t('conn.telnetSendModeChar')" value="character" />
                  <el-option :label="t('conn.telnetSendModeLine')" value="line" />
                </el-select>
              </el-form-item>
            </template>
            <template v-if="form.type === 'telnet' || form.type === 'serial' || form.type === 'tcp'">
              <el-form-item :label="t('conn.localEcho')">
                <el-switch v-model="form.localEcho" />
              </el-form-item>
              <el-form-item :label="t('conn.newlineMode')">
                <el-select v-model="form.newlineMode">
                  <el-option label="CR" value="cr" />
                  <el-option label="CR+LF" value="crlf" />
                </el-select>
              </el-form-item>
            </template>
            <el-form-item
              v-if="form.type === 'ssh' || form.type === 'telnet' || form.type === 'serial' || form.type === 'mosh' || form.type === 'tcp'"
              :label="t('conn.backspaceKey')"
            >
              <el-select v-model="form.backspaceKey">
                <el-option label="ASCII Backspace (0x08)" value="bs" />
                <el-option label="ASCII Delete (0x7F)" value="del" />
                <el-option label="VT220 Delete (ESC[3~)" value="vt220" />
              </el-select>
            </el-form-item>
            <el-form-item v-if="form.type === 'ssh' || form.type === 'scp'" :label="t('conn.sftpMaxConcurrency')">
              <el-input-number v-model="form.sftpMaxConcurrency" :min="0" :max="20" />
            </el-form-item>
            <el-form-item v-if="form.type === 'ssh'" :label="t('conn.x11Forwarding')">
              <el-switch v-model="form.x11Forwarding" />
              <span v-if="x11HintKey" class="field-hint" style="margin-left: 0.75rem;">{{ t(x11HintKey) }}</span>
            </el-form-item>
            <el-form-item v-if="form.type === 'ssh'" :label="t('conn.agentForwarding')">
              <el-switch v-model="form.agentForwarding" />
              <span class="field-hint" style="margin-left: 0.75rem;">{{ t('conn.agentForwardingDesc') }}</span>
            </el-form-item>
            <el-form-item v-if="form.type === 'ssh'" :label="t('conn.shellIntegration')">
              <el-switch v-model="form.shellIntegration" />
              <span class="field-hint" style="margin-left: 0.75rem;">{{ t('conn.shellIntegrationDesc') }}</span>
            </el-form-item>
            <template v-if="form.type === 'ftp'">
              <el-form-item :label="t('conn.ftpEncryption')">
                <el-select v-model="form.ftpEncryption">
                  <el-option :label="t('conn.ftpEncryptionNone')" value="none" />
                  <el-option :label="t('conn.ftpEncryptionAuto')" value="auto" />
                  <el-option :label="t('conn.ftpEncryptionRequired')" value="required" />
                </el-select>
              </el-form-item>
              <el-form-item v-if="form.ftpEncryption !== 'none'" :label="t('conn.ftpSkipVerify')">
                <el-switch v-model="form.ftpSkipVerify" />
                <div class="field-hint">{{ t('conn.ftpSkipVerifyDesc') }}</div>
              </el-form-item>
              <el-form-item :label="t('conn.ftpPassive')">
                <el-switch v-model="form.ftpPassive" />
              </el-form-item>
              <el-form-item :label="t('conn.ftpEncoding')">
                <el-select v-model="form.ftpEncoding" placeholder="UTF-8">
                  <el-option label="UTF-8" value="utf-8" />
                  <el-option label="GBK" value="gbk" />
                  <el-option label="Shift-JIS" value="shift-jis" />
                  <el-option label="Latin-1" value="latin-1" />
                </el-select>
              </el-form-item>
            </template>
            <template v-if="form.type === 'vnc'">
              <el-form-item :label="t('conn.vncShared')">
                <el-switch v-model="form.vncShared" />
              </el-form-item>
              <el-form-item :label="t('conn.vncRepeaterID')">
                <el-input v-model="form.vncRepeaterID" :placeholder="t('conn.vncRepeaterIDPlaceholder')" />
              </el-form-item>
            </template>
            <template v-if="form.type === 'rdp' && isWindows">
              <el-form-item :label="t('conn.rdpAdminSession')">
                <el-select v-model="form.rdpAdminSession" style="width: 100%">
                  <el-option :value="false" :label="t('conn.rdpAdminSessionOff')" />
                  <el-option :value="true" :label="t('conn.rdpAdminSessionOn')" />
                </el-select>
              </el-form-item>
              <el-form-item :label="t('conn.rdpSmartSizing')">
                <el-switch v-model="form.rdpSmartSizing" />
              </el-form-item>
            </template>
            <el-form-item v-if="showProxy" :label="t('conn.proxy')">
              <div class="inline-add-row">
                <el-select v-model="form.proxyId" :placeholder="t('conn.proxyPlaceholder')" clearable filterable style="flex: 1; min-width: 0">
                  <el-option :label="t('conn.proxySystemOption')" value="system" />
                  <el-option
                    v-for="p in proxyStore.proxies"
                    :key="p.id"
                    :label="proxyOptionLabel(p)"
                    :value="p.id"
                    :disabled="p.enabled === false"
                  />
                </el-select>
                <el-button class="inline-add-btn" :title="t('conn.newProxy')" @click="openNewProxyDialog">
                  <Plus :size="'0.875rem'" />
                </el-button>
              </div>
            </el-form-item>
            <el-form-item v-if="showTunnel" :label="t('conn.tunnel')">
              <el-select
                v-model="form.tunnelSSHConnId"
                :placeholder="t('conn.tunnelPlaceholder')"
                clearable
                filterable
              >
                <el-option
                  v-for="c in sshConnections"
                  :key="c.id"
                  :label="`${c.name} (${c.user}@${c.host}:${c.port})`"
                  :value="c.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item
              v-if="['ssh','telnet','serial','mosh','local','wsl','tcp'].includes(form.type)"
              :label="t('conn.logOnConnect')"
            >
              <el-switch v-model="form.logOnConnect" />
              <div class="field-hint">{{ t('conn.logOnConnectDesc') }}</div>
            </el-form-item>
            </template>
          </el-form>
        </div>
      </div>
    </div>
    <template #footer>
      <el-button @click="visible = false">{{ t('conn.cancel') }}</el-button>
      <el-button
        v-if="canTest"
        :loading="testStatus === 'checking'"
        :icon="testStatus === 'success' ? CircleCheck : testStatus === 'error' ? CircleX : undefined"
        :class="{ 'test-success': testStatus === 'success', 'test-error': testStatus === 'error' }"
        class="test-status-btn"
        @click="onTest"
      >
        {{ t('conn.testConnection') }}
      </el-button>
      <el-button v-if="!isEdit" @click="onConnectOnly">{{ t('conn.connectOnly') }}</el-button>
      <el-button @click="onSave">{{ t('conn.saveOnly') }}</el-button>
      <el-button type="primary" @click="onConnect">{{ t('conn.saveConnect') }}</el-button>
    </template>
  </el-dialog>

  <!-- New group dialog -->
  <el-dialog append-to-body v-model="showNewGroupDialog" :title="t('conn.newGroupTitle')" width="25rem">
    <el-form label-width="5rem" @submit.prevent="confirmNewGroup">
      <el-form-item :label="t('conn.groupName')">
        <el-input
          v-model="newGroupName"
          :placeholder="t('conn.groupNamePlaceholder')"
          @keyup.enter="confirmNewGroup"
        />
      </el-form-item>
      <el-form-item :label="t('conn.parentGroup')">
        <el-tree-select
          v-model="newGroupParentId"
          :data="groupTreeData"
          :render-after-expand="false"
          check-strictly
          clearable
          :placeholder="t('conn.noGroup')"
          style="width:100%"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showNewGroupDialog = false">{{ t('conn.cancel') }}</el-button>
      <el-button type="primary" @click="confirmNewGroup">{{ t('conn.save') }}</el-button>
    </template>
  </el-dialog>

  <!-- New identity / keychain dialog (reuses the settings one) -->
  <IdentityEditDialog v-model:visible="identityDialogVisible" :identity="null" @saved="onIdentitySaved" />
  <!-- New proxy dialog (reuses the settings one) -->
  <ProxyEditDialog v-model:visible="proxyDialogVisible" :proxy="null" @saved="onProxySaved" />
</template>

<script setup lang="ts">
import { reactive, computed, watch, ref, nextTick, onMounted } from 'vue'
import { useConnectionStore } from '../stores/connectionStore'
import { useSettingsStore } from '../stores/settingsStore'
import { useIdentityStore } from '../stores/identityStore'
import { useProxyStore } from '../stores/proxyStore'
import { useI18n } from '../i18n'
import type { ConnectionConfig, PostLoginExpectStep } from '../types/session'
import { OpenFileDialog, OpenPrivateKeyFile, OpenKubeconfigFile, GetPlatform, ListSerialPorts, TestConnection, GetDefaultSSHKeyPaths } from '../../bindings/easyaiot/terminal/app'
import { ElInput } from 'element-plus'
import { msg } from '../services/message'
import { Plus, Trash2, ChevronRight, FolderOpen, Eye, EyeOff, RefreshCw, CircleCheck, CircleX, KeyRound } from '@lucide/vue'
import { listContexts } from '../services/k8sClient'
import SyntaxEditor from './SyntaxEditor.vue'
import type { K8sContextInfo } from '../types/k8s'
import IdentityEditDialog from './IdentityEditDialog.vue'
import ProxyEditDialog from './ProxyEditDialog.vue'
import { isSqlDbType } from '../utils/quickConnect'
import { CATEGORY_META, CATEGORY_ORDER, CONNECTION_TYPES, connectionTypeFormLabel, connectionTypeInfo, defaultPortFor } from '../utils/connectionTypes'
import type { ConnectionCategory } from '../utils/connectionTypes'
import { getShellLabel as getShellLabelBase } from '../utils/shellLabel'
import { backendErrorText } from '../utils/backendError'
import type { Identity } from '../types/identity'
import type { Proxy } from '../types/proxy'

const { t } = useI18n()
const connectionStore = useConnectionStore()
const settingsStore = useSettingsStore()
const identityStore = useIdentityStore()
const proxyStore = useProxyStore()

// Gates the keyText paste area: the private key stays hidden behind a single
// "show" button until the user reveals it. Declared early (top of setup) so
// resetForm — fired by an immediate watch during setup — can read it without
// hitting the temporal dead zone (a late declaration there caused a ReferenceError
// that blanked the whole form in dev).
const keyContentRevealed = ref(false)
// Gates the inline kubeconfig paste area, mirroring keyContentRevealed: hidden
// behind a single "show" button so a stored kubeconfig isn't dumped on screen
// the moment the form opens.
const k8sConfigRevealed = ref(false)

onMounted(() => {
  identityStore.load()
  proxyStore.load()
})

// ── Platform detection (before allSubTypes so it's available in computed closures) ──
const isWindows = ref(/windows/i.test(navigator.userAgent) || /win32/i.test(navigator.platform))
const isMac = ref(/mac/i.test(navigator.platform))
const platform = ref<string>('')
GetPlatform().then(p => {
  platform.value = p
  isWindows.value = p === 'windows'
  isMac.value = p === 'darwin'
})

// ── Categories & sub-types ──
interface SubTypeInfo {
  type: string
  dbType?: string
  containerRuntime?: string
  label: string
  icon: any
}

// Category sidebar and subtype cards derive from the connectionTypes registry.
// 'other' (web-app URL entries) trails the main categories.
const categories = computed(() => ([...CATEGORY_ORDER, 'other'] as ConnectionCategory[]).map(key => ({
  key,
  label: t(CATEGORY_META[key].labelKey),
  icon: CATEGORY_META[key].icon,
})))

const allSubTypes = computed((): Record<string, SubTypeInfo[]> => {
  const groups: Record<string, SubTypeInfo[]> = {}
  for (const cat of [...CATEGORY_ORDER, 'other'] as ConnectionCategory[]) groups[cat] = []
  for (const info of CONNECTION_TYPES) {
    if (info.formHidden) continue
    if (info.windowsOnly && !isWindows.value) continue
    groups[info.category]?.push({
      type: info.type,
      dbType: info.dbType,
      containerRuntime: info.containerRuntime,
      label: connectionTypeFormLabel(info, t),
      icon: info.icon,
    })
  }
  return groups
})

const currentSubTypes = computed(() => allSubTypes.value[category.value] || allSubTypes.value.terminal)

function isSubTypeActive(st: SubTypeInfo): boolean {
  if (st.dbType) {
    return form.type === 'database' && form.dbType === st.dbType
  }
  if (st.containerRuntime) {
    return form.type === 'container' && form.containerRuntime === st.containerRuntime
  }
  return form.type === st.type
}

function selectType(st: SubTypeInfo) {
  if (st.dbType) {
    form.type = 'database'
    form.dbType = st.dbType
  } else if (st.containerRuntime) {
    form.type = 'container'
    form.containerRuntime = st.containerRuntime as 'docker' | 'podman' | 'nerdctl' | 'wslc'
  } else {
    form.type = st.type
  }
}

function onCategorySelect(catKey: string) {
  if (category.value === catKey) return
  const subs = allSubTypes.value[catKey]
  if (subs && subs.length > 0) {
    selectType(subs[0])
  }
}

function getShellLabel(path: string): string {
  return getShellLabelBase(path)
}

// Local-shell options exclude WSL entries: the ordinary local terminal type
// never surfaces `wsl://<distro>` shells (those belong to the wsl type).
const localShellOptions = computed(() =>
  settingsStore.availableShells
    .filter(sh => !sh.toLowerCase().startsWith('wsl://'))
    .map(sh => ({ label: getShellLabel(sh), value: sh }))
)

// WSL options reuse the terminal "shell" field: their value is the `wsl://<distro>`
// shell path (which carries the distro on the backend), not a separate field.
const wslShellOptions = computed(() =>
  settingsStore.availableShells
    .filter(sh => sh.toLowerCase().startsWith('wsl://'))
    .map(sh => ({ label: getShellLabel(sh), value: sh }))
)

const shellOptionsForType = computed(() =>
  form.type === 'wsl' ? wslShellOptions.value : localShellOptions.value
)

const x11HintKey = computed(() => {
  if (platform.value === 'darwin') return 'conn.x11ForwardingDescMac'
  return ''
})
const passwordInputKey = ref(0)

const postLoginMode = ref<'script' | 'expect'>('script')
const showAdvanced = ref(false)

// Connection types that support the "test connection" button (issue #377).
// local/serial/mosh/vnc/rdp/spice/x11-desktop don't have a non-interactive probe.
const TESTABLE_TYPES = ['ssh', 'telnet', 'ftp', 'sftp', 'scp', 's3', 'webdav', 'smb', 'database', 'k8s', 'container', 'tcp']
// Test-connection result state: 'checking' shows a spinner; 'success'/'error'
// keep a colored status icon on the button until the next test or a reopen.
const testStatus = ref<'idle' | 'checking' | 'success' | 'error'>('idle')
const canTest = computed(() => TESTABLE_TYPES.includes(form.type))

// Serial port config (separate refs so allow-create doesn't produce strings)
const serialPorts = ref<string[]>([])
const serialScanning = ref(false)
const serialBaudRateInput = ref('')
const serialDataBitsValue = ref(8)
const serialStopBitsValue = ref(1)
const serialParityValue = ref('none')

const portPlaceholder = computed(() => {
  if (serialScanning.value) return t('serial.scanning')
  if (serialPorts.value.length === 0) return t('serial.noPorts')
  return t('serial.portLabel')
})

async function scanSerialPorts() {
  serialScanning.value = true
  try {
    serialPorts.value = await ListSerialPorts()
  } catch {
    serialPorts.value = []
  } finally {
    serialScanning.value = false
  }
}

const baudRatePresets = [300, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

function queryBaudRateSuggestions(queryString: string, cb: (results: { value: string }[]) => void) {
  const suggestions = baudRatePresets
    .filter(r => String(r).includes(queryString))
    .map(r => ({ value: String(r) }))
  cb(suggestions)
}

const props = defineProps<{
  modelValue: boolean
  editConfig?: ConnectionConfig
  defaultGroupId?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [config: ConnectionConfig]
  connect: [config: ConnectionConfig]
  connectOnly: [config: ConnectionConfig]
  cancel: []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

// Dismissal bookkeeping: close routed through save/connect/connectOnly is
// "handled" (the host already cleared its state); any other close — cancel
// button, X, Esc, overlay click — reports `cancel` so the host can reset the
// edited config. Reset on every open.
let handled = false
watch(visible, (v) => {
  if (v) {
    handled = false
  } else if (!handled) {
    emit('cancel')
  }
})

const hostInputRef = ref<InstanceType<typeof ElInput> | null>(null)

watch(visible, (val) => {
  if (val) {
    testStatus.value = 'idle'
    passwordInputKey.value++
    // Apply group on open: the defaultGroupId watch won't fire when the value
    // is unchanged, so restore it here to avoid losing the group on the second
    // consecutive create within the same group.
    if (!props.editConfig) {
      selectedGroupId.value = props.defaultGroupId
      form.groupId = props.defaultGroupId
    }
  }
})

function onDialogOpened() {
  // New connections: focus the host field by default. The dialog's @opened
  // event fires after the open transition, so the host input is mounted.
  if (!isEdit.value) {
    nextTick(() => hostInputRef.value?.focus())
  }
}

const isEdit = computed(() => !!props.editConfig?.id)

// Category comes from the connectionTypes registry; only the discriminated
// 'database' type needs the dbType check (SQL vs NoSQL).
const category = computed(() => {
  if (form.type === 'database') return isSqlDbType(form.dbType) ? 'sql' : 'nosql'
  return connectionTypeInfo(form.type)?.category || 'terminal'
})

const sshConnections = computed(() =>
  connectionStore.connections
    .filter(c => c.type === 'ssh' && c.id !== form.id)
    .sort((a, b) => a.name.localeCompare(b.name))
)

const TUNNEL_UNSUPPORTED = ['spice', 'mosh', 'local', 'wsl', 'serial', 'container']
const showTunnel = computed(() =>
  !TUNNEL_UNSUPPORTED.includes(form.type)
)
const showProxy = computed(() => ['ssh', 'sftp', 'scp', 'monitor'].includes(form.type))
const showAdvancedToggle = computed(() =>
  showTunnel.value || form.type === 'ssh' || form.type === 'sftp' || form.type === 'scp' || form.type === 'telnet' || form.type === 'mosh' || form.type === 'local' || form.type === 'wsl' || form.type === 'serial' || form.type === 'ftp' || form.type === 'database'
)

const isRedisSentinel = computed(() =>
  form.type === 'redis' && form.redisMode === 'sentinel'
)
const isElasticsearch = computed(() =>
  form.type === 'elasticsearch'
)
const isEsApiKey = computed(() =>
  isElasticsearch.value && form.authType === 'apikey'
)

const defaultParamsHint = computed(() => {
  switch (form.dbType) {
    case 'mysql': return '默认: charset=utf8mb4'
    case 'postgres': return '默认: sslmode=disable'
    case 'sqlserver': return '默认: encrypt=disable'
    default: return ''
  }
})

const form = reactive<ConnectionConfig>({
  id: '',
  name: '',
  remark: '',
  type: 'ssh',
  host: '',
  port: 22,
  user: '',
  authType: 'password',
  kerberosRealm: '',
  password: '',
  keyPath: '',
  keyContent: '',
  groupId: undefined,
  rdpFixedWidth: -1,
  rdpFixedHeight: -1,
  rdpSmartSizing: false,
  rdpEnableNLA: true,
  rdpDomain: '',
  rdpAdminSession: false,
  dbType: '',
  dbName: '',
  dbParams: '',
  esUseSsl: false,
  esPathPrefix: '',
  esSkipVerify: false,
  redisMode: 'standalone',
  redisMasterName: '',
  redisSentinels: '',
  redisKeySeparator: ':',
  sentinelUser: '',
  sentinelPassword: '',
  postLoginScript: '',
  postLoginExpectSteps: [],
  sftpMaxConcurrency: 5,
  fileTransferProto: 'sftp' as 'sftp' | 'scp',
  x11Forwarding: false,
  agentForwarding: false,
  shellIntegration: true,
  ftpEncryption: 'none',
  ftpPassive: true,
  ftpEncoding: 'utf-8',
  ftpSkipVerify: false,
  vncShared: true,
  vncRepeaterID: '',
  encoding: 'utf-8',
  backspaceKey: 'del',
  telnetNegotiationMode: 'active' as 'active' | 'passive',
  telnetSendMode: 'character' as 'character' | 'line',
  localEcho: false,
  newlineMode: 'cr' as 'cr' | 'crlf',
  shellPath: '',
  smbDomain: 'WORKGROUP',
  smbShare: '',
  s3Region: 'us-east-1',
  s3Bucket: '',
  s3UrlStyle: 'virtual',
  logOnConnect: false,
  k8sConfigPath: '~/.kube/config',
  k8sConfigInline: '',
  k8sContext: '',
  k8sNamespace: 'default',
  containerTransport: 'ssh',
  containerSSHConnId: undefined,
  containerRuntime: 'docker',
  proxyId: undefined,
  x11DesktopDesktopType: 'gnome',
  x11DesktopCustomCmd: '',
})

const RDP_CUSTOM_RESOLUTION = 'custom'

// Default preset list (mstsc-style), plus a "custom" entry that reveals
// free width/height inputs — the RDP protocol accepts any desktop size, so
// presets cannot cover every monitor (e.g. 1360×768).
const rdpResolutions = [
  { label: '800 × 600 (SVGA)', w: 800, h: 600 },
  { label: '1024 × 768 (XGA)', w: 1024, h: 768 },
  { label: '1280 × 720 (HD)', w: 1280, h: 720 },
  { label: '1280 × 800 (WXGA)', w: 1280, h: 800 },
  { label: '1280 × 1024 (SXGA)', w: 1280, h: 1024 },
  { label: '1366 × 768 (HD)', w: 1366, h: 768 },
  { label: '1440 × 900 (WXGA+)', w: 1440, h: 900 },
  { label: '1600 × 900 (HD+)', w: 1600, h: 900 },
  { label: '1600 × 1200 (UXGA)', w: 1600, h: 1200 },
  { label: '1680 × 1050 (WSXGA+)', w: 1680, h: 1050 },
  { label: '1920 × 1080 (Full HD)', w: 1920, h: 1080 },
  { label: '1920 × 1200 (WUXGA)', w: 1920, h: 1200 },
  { label: '2560 × 1440 (QHD)', w: 2560, h: 1440 },
  { label: '2560 × 1600 (WQXGA)', w: 2560, h: 1600 },
  { label: '3840 × 2160 (4K UHD)', w: 3840, h: 2160 },
]

const rdpResolutionOptions = [
  { value: 'fullscreen', label: t('rdp.fullscreen') },
  ...rdpResolutions.map(r => ({ value: `${r.w}x${r.h}`, label: r.label })),
  { value: RDP_CUSTOM_RESOLUTION, label: t('rdp.customResolution') },
]

function rdpResolutionKey(w?: number, h?: number): string {
  if (w === undefined || h === undefined || w === -1 || h === -1) return 'fullscreen'
  const match = rdpResolutions.find(r => r.w === w && r.h === h)
  return match ? `${match.w}x${match.h}` : RDP_CUSTOM_RESOLUTION
}

const rdpResolution = ref('fullscreen')
const rdpCustomWidth = ref(1360)
const rdpCustomHeight = ref(768)

// Keep the form's fixed size fields in sync with the resolution picker.
watch(rdpResolution, (val) => {
  if (val === 'fullscreen') {
    form.rdpFixedWidth = -1
    form.rdpFixedHeight = -1
  } else if (val === RDP_CUSTOM_RESOLUTION) {
    form.rdpFixedWidth = rdpCustomWidth.value
    form.rdpFixedHeight = rdpCustomHeight.value
  } else {
    const [w, h] = val.split('x').map(Number)
    form.rdpFixedWidth = w
    form.rdpFixedHeight = h
  }
})

// A change to the custom width/height inputs applies immediately while
// "custom" is selected.
watch([rdpCustomWidth, rdpCustomHeight], ([w, h]) => {
  if (rdpResolution.value === RDP_CUSTOM_RESOLUTION && w && h) {
    form.rdpFixedWidth = w
    form.rdpFixedHeight = h
  }
})

const selectedGroupId = ref<string | undefined>(undefined)

// Tree data for el-tree-select
interface TreeOption {
  value: string
  label: string
  children?: TreeOption[]
}

const groupTreeData = computed<TreeOption[]>(() => {
  function buildTree(nodes: any[]): TreeOption[] {
    return nodes.map(node => ({
      value: node.group.id,
      label: node.group.name,
      children: node.children.length > 0 ? buildTree(node.children) : undefined,
    }))
  }
  return [
    { value: '__none__', label: t('conn.noGroup') },
    ...buildTree(connectionStore.groupedConnections.roots),
  ]
})

// New group dialog
const showNewGroupDialog = ref(false)
const newGroupName = ref('')
const newGroupParentId = ref<string | undefined>(undefined)

// New identity / proxy dialogs (reuse the settings ones, in "create" mode)
const identityDialogVisible = ref(false)
const proxyDialogVisible = ref(false)

function openNewIdentityDialog() {
  identityDialogVisible.value = true
}

// Enable toggle (issue #749): disabled proxies are dimmed and unselectable for
// NEW connections; existing connections referencing one dial directly (backend).
function proxyOptionLabel(p: Proxy): string {
  const base = `${p.name} (${p.kind} ${p.host}:${p.port})`
  return p.enabled === false ? `${base} — ${t('conn.proxyDisabled')}` : base
}

function openNewProxyDialog() {
  proxyDialogVisible.value = true
}

// After creating an item from the "+" button, select it immediately so the
// user keeps typing. The stores are already up to date (the dialogs add via
// the same stores), so no explicit reload is needed.
function onIdentitySaved(id: Identity) {
  form.identityId = id.id
}

function onProxySaved(p: Proxy) {
  form.proxyId = p.id
}

// ── K8s state ──
const k8sSourceMode = ref<'file' | 'inline'>('inline')
const k8sContexts = ref<K8sContextInfo[]>([])
const k8sContextsLoading = ref(false)
const k8sContextsError = ref('')
// Guard against watchers wiping restored state during edit-hydration.
const hydrating = ref(false)

// True once the user hand-edits the namespace field, so that switching the
// k8s context later doesn't silently overwrite a value they typed.
const k8sNamespaceTouched = ref(false)
// Namespace suggestions drawn from the contexts' declared defaults plus the
// current field value. allow-create lets the user type any namespace.
const k8sNamespaceOptions = computed(() => {
  const set = new Set<string>()
  if (form.k8sNamespace) set.add(form.k8sNamespace)
  for (const c of k8sContexts.value) if (c.namespace) set.add(c.namespace)
  return Array.from(set)
})

watch(() => props.editConfig, (config) => {
  if (config) {
    // Always reset first so fields absent from the config (e.g. an empty
    // password) don't leak values from a previously edited connection. Then
    // merge the config over the clean defaults.
    resetForm()
    hydrating.value = true
    Object.assign(form, { ...config, postLoginExpectSteps: cloneExpectSteps(config.postLoginExpectSteps || []) })
    // Backfill legacy ES auth: older versions stored the auth type in a dedicated
    // `esAuthType` ('basic'|'apikey') and the key in `esApiKey`. Both now live in
    // the shared `authType` ('password'|'apikey') and `password` fields.
    if (form.type === 'elasticsearch') {
      const legacy = config as any
      const legacyType = legacy?.esAuthType
      if (legacyType) {
        form.authType = legacyType === 'apikey' ? 'apikey' : 'password'
        if (form.authType === 'apikey' && !form.password && legacy?.esApiKey) {
          form.password = legacy.esApiKey
        }
      } else if (form.authType !== 'apikey' && form.authType !== 'password') {
        form.authType = 'password'
      }
    }
    // Existing connections without the field default to NLA off (old behavior).
    form.rdpEnableNLA = config.rdpEnableNLA ?? false
    form.rdpAdminSession = config.rdpAdminSession ?? false
    form.x11Forwarding = config.x11Forwarding ?? false
    form.agentForwarding = config.agentForwarding ?? false
    // Startup shell integration defaults to ON: absent field (historical
    // configs) means enabled, matching the backend's nil semantics.
    form.shellIntegration = config.shellIntegration ?? true
    // Existing SSH connections without the field default to SFTP (old behavior).
    form.fileTransferProto = config.fileTransferProto ?? 'sftp'
    // Redis key separator defaults to ":" (empty from old connections = ":").
    form.redisKeySeparator = config.redisKeySeparator ?? ':'
    postLoginMode.value = (config.postLoginExpectSteps?.length || 0) > 0 ? 'expect' : 'script'
    selectedGroupId.value = config.groupId || undefined
    // Sync serial refs from config
    if (config.serialBaudRate) serialBaudRateInput.value = String(config.serialBaudRate)
    if (config.serialDataBits) serialDataBitsValue.value = config.serialDataBits
    if (config.serialStopBits) serialStopBitsValue.value = config.serialStopBits
    if (config.serialParity) serialParityValue.value = config.serialParity
    if (config.type === 'serial') scanSerialPorts()
    // Sync k8s source-mode radio from restored config
    if (config.type === 'k8s') {
      k8sSourceMode.value = config.k8sConfigInline ? 'inline' : 'file'
    }
    // Defaults for container connections saved before these fields existed
    if (config.type === 'container') {
      form.containerTransport = config.containerTransport ?? 'ssh'
      form.containerRuntime = config.containerRuntime ?? 'docker'
    }
    if (config.type === 'x11-desktop') {
      form.x11DesktopDesktopType = config.x11DesktopDesktopType ?? 'gnome'
      form.x11DesktopCustomCmd = config.x11DesktopCustomCmd ?? ''
    }
    // Sync resolution picker to the config's fixed size. Sizes outside the
    // preset list fall back to the custom inputs so they stay visible and
    // editable.
    rdpResolution.value = rdpResolutionKey(config.rdpFixedWidth, config.rdpFixedHeight)
    if (rdpResolution.value === RDP_CUSTOM_RESOLUTION) {
      rdpCustomWidth.value = config.rdpFixedWidth ?? 1360
      rdpCustomHeight.value = config.rdpFixedHeight ?? 768
    }
    nextTick(() => { hydrating.value = false })
  } else {
    resetForm()
    if (props.defaultGroupId) {
      selectedGroupId.value = props.defaultGroupId
      form.groupId = props.defaultGroupId
    }
  }
}, { immediate: true })

watch(() => props.defaultGroupId, (gid) => {
  if (!props.editConfig && gid) {
    selectedGroupId.value = gid
    form.groupId = gid
  }
})

// Auto-switch default port when changing type
watch(() => form.type, (newType) => {
  // A result icon for the previous type is stale; clear it.
  testStatus.value = 'idle'
  if (newType !== 'ssh' && postLoginMode.value === 'expect') {
    postLoginMode.value = 'script'
  }
  if (isEdit.value) return
  const port = defaultPortFor(newType)
  if (port !== undefined) form.port = port
  if (newType === 'elasticsearch') {
    // ES shares the common `authType` field; default to 'password' unless an API key was already chosen.
    form.authType = form.authType === 'apikey' ? 'apikey' : 'password'
  }
  if (['rdp', 'vnc', 'spice', 'x11-desktop'].includes(newType) || newType === 'database') {
    form.authType = 'password'
  }
  // The shell ("terminal type") is specific to local/wsl; always reset to the
  // new type's default instead of inheriting the previous type's shell path.
  if (newType === 'local' && localShellOptions.value.length > 0) {
    form.shellPath = localShellOptions.value[0].value
  }
  if (newType === 'wsl' && wslShellOptions.value.length > 0) {
    form.shellPath = wslShellOptions.value[0].value
  }
  if (newType === 'serial') {
    scanSerialPorts()
  }
})

// Auto-switch default port when changing SQL database subtype
watch(() => form.dbType, (newType) => {
  if (isEdit.value) return
  const port = defaultPortFor('database', newType)
  if (port !== undefined) form.port = port
})

// Clear the identity reference when switching away from the identity auth
// type, and don't carry credentials (username, password/passphrase, key path,
// key content, kerberos realm) across an auth type switch — each type owns its
// own fields. Skip while hydrating the form from an existing config, or
// opening the edit dialog would wipe the stored credentials.
watch(() => form.authType, (val) => {
  if (hydrating.value) return
  if (val !== 'identity') form.identityId = ''
  if (val !== 'kerberos') form.kerberosRealm = ''
  form.user = ''
  form.password = ''
  form.keyPath = ''
  form.keyContent = ''
})

function resetForm() {
  // Always re-hide the keyText paste area when the dialog (re)opens, whether
  // editing an existing connection or creating a new one, so a prior reveal
  // can't leak the previous connection's PEM into a fresh edit.
  keyContentRevealed.value = false
  // Same for the inline kubeconfig area — a stored kubeconfig is sensitive
  // material just like a private key.
  k8sConfigRevealed.value = false
  form.id = ''
  form.name = ''
  form.remark = ''
  form.type = 'ssh'
  form.host = ''
  form.port = 22
  form.user = ''
  form.authType = 'password'
  form.password = ''
  form.keyPath = ''
  form.keyContent = ''
  form.identityId = ''
  form.groupId = undefined
  form.rdpFixedWidth = -1
  form.rdpFixedHeight = -1
  form.rdpSmartSizing = false
  form.rdpEnableNLA = true
  form.rdpDomain = ''
  form.rdpAdminSession = false
  form.kerberosRealm = ''
  form.dbType = ''
  form.dbName = ''
  form.dbParams = ''
  form.esUseSsl = false
  form.esPathPrefix = ''
  form.esSkipVerify = false
  form.redisMode = 'standalone'
  form.redisMasterName = ''
  form.redisSentinels = ''
  form.redisKeySeparator = ':'
  form.sentinelUser = ''
  form.sentinelPassword = ''
  form.postLoginScript = ''
  form.postLoginExpectSteps = []
  postLoginMode.value = 'script'
  form.sftpMaxConcurrency = 5
  form.fileTransferProto = 'sftp'
  form.x11Forwarding = false
  form.agentForwarding = false
  form.shellIntegration = true
  form.ftpEncryption = 'none'
  form.ftpPassive = true
  form.ftpEncoding = 'utf-8'
  form.ftpSkipVerify = false
  form.vncShared = true
  form.vncRepeaterID = ''
  form.encoding = 'utf-8'
  form.backspaceKey = 'del'
  form.telnetNegotiationMode = 'active'
  form.telnetSendMode = 'character'
  form.localEcho = false
  form.newlineMode = 'cr'
  form.shellPath = ''
  form.serialPort = ''
  form.serialBaudRate = 115200
  form.serialDataBits = 8
  form.serialStopBits = 1
  form.serialParity = 'none'
  serialBaudRateInput.value = ''
  form.tunnelSSHConnId = undefined
  form.proxyId = undefined
  form.logOnConnect = false
  form.k8sConfigPath = '~/.kube/config'
  form.k8sConfigInline = ''
  form.k8sContext = ''
  form.k8sNamespace = 'default'
  k8sNamespaceTouched.value = false
  form.containerTransport = 'ssh'
  form.containerSSHConnId = undefined
  form.containerRuntime = 'docker'
  k8sSourceMode.value = 'inline'
  k8sContexts.value = []
  k8sContextsLoading.value = false
  k8sContextsError.value = ''
  rdpResolution.value = 'fullscreen'
  form.x11DesktopDesktopType = 'gnome'
  form.x11DesktopCustomCmd = ''
  selectedGroupId.value = undefined
}

// Sync tree-select value to form
watch(selectedGroupId, (val) => {
  form.groupId = val === '__none__' ? undefined : (val || undefined)
})

function onGroupSelect(value: string | undefined) {
  if (value === '__new__') {
    showNewGroupDialog.value = true
    newGroupName.value = ''
    newGroupParentId.value = undefined
    return
  }
}

async function confirmNewGroup() {
  const name = newGroupName.value.trim()
  if (!name) {
    return
  }
  showNewGroupDialog.value = false
  const group = await connectionStore.addGroup(name, newGroupParentId.value)
  newGroupParentId.value = undefined
  newGroupName.value = ''
  form.groupId = group.id
  selectedGroupId.value = group.id
}

async function reloadK8sContexts() {
  k8sContextsLoading.value = true
  k8sContextsError.value = ''
  try {
    const src = k8sSourceMode.value === 'file' ? form.k8sConfigPath : form.k8sConfigInline
    if (!src) return
    const list = await listContexts(src, k8sSourceMode.value === 'file')
    k8sContexts.value = list
    if (!form.k8sContext) {
      const current = list.find(c => c.current)
      if (current) form.k8sContext = current.name
    }
  } catch (e: any) {
    k8sContextsError.value = String(e?.message || e)
  } finally {
    k8sContextsLoading.value = false
  }
}

async function selectKeyFile() {
  try {
    const selected = await OpenFileDialog('~/.ssh')
    if (selected) form.keyPath = selected
  } catch (e) {
    console.error('select key file:', e)
  }
}

// Fill the key path with a local default private key (~/.ssh/id_ed25519,
// ~/.ssh/id_rsa, etc.). The backend resolves the home directory and returns
// only the standard keys that exist, in preference order. Repeated clicks
// cycle through them (wrapping around); if the field holds a non-default path
// the first click resets it to the preferred default.
async function useDefaultKeyPath() {
  try {
    const paths = await GetDefaultSSHKeyPaths()
    if (!paths?.length) return
    const current = form.keyPath.trim()
    const idx = paths.indexOf(current)
    form.keyPath = idx >= 0 ? paths[(idx + 1) % paths.length] : paths[0]
  } catch (e) {
    console.error('default key paths:', e)
  }
}

async function importKeyText() {
  try {
    const content = await OpenPrivateKeyFile()
    if (content) {
      form.keyContent = content
      keyContentRevealed.value = true
    }
  } catch (e: any) {
    msg.error(backendErrorText(e))
  }
}

async function importKubeconfigText() {
  try {
    const content = await OpenKubeconfigFile()
    if (content) {
      form.k8sConfigInline = content
      k8sConfigRevealed.value = true
    }
  } catch (e: any) {
    msg.error(backendErrorText(e))
  }
}

async function pickKubeconfigFile() {
  try {
    const selected = await OpenFileDialog('~/.kube')
    if (selected) form.k8sConfigPath = selected
  } catch (e) {
    console.error('pick kubeconfig:', e)
  }
}

watch(() => [k8sSourceMode.value, form.k8sConfigPath, form.k8sConfigInline], () => {
  if (hydrating.value) return
  form.k8sContext = ''
  k8sContexts.value = []
})

watch(() => form.type, (t) => {
  if (t === 'k8s' && (form.k8sConfigPath || form.k8sConfigInline)) {
    reloadK8sContexts()
  }
})

function onK8sNamespaceInput() {
  k8sNamespaceTouched.value = true
}

// Adopt the selected context's declared default namespace, unless the user has
// already hand-typed a value. Editing an existing connection runs under
// hydrating, where the stored namespace must win.
watch(() => form.k8sContext, (ctxName) => {
  if (hydrating.value) return
  if (k8sNamespaceTouched.value) return
  if (!ctxName) return
  const ctx = k8sContexts.value.find(c => c.name === ctxName)
  if (ctx && ctx.namespace) form.k8sNamespace = ctx.namespace
})

function generateUniqueName(name: string): string {
  if (!connectionStore.connections.some(c => c.name === name)) {
    return name
  }
  let idx = 1
  while (connectionStore.connections.some(c => c.name === `${name} (${idx})`)) {
    idx++
  }
  return `${name} (${idx})`
}

function normalizeForm(): ConnectionConfig {
  // Sync serial refs into form before normalization
  if (form.type === 'serial') {
    form.serialBaudRate = parseInt(serialBaudRateInput.value, 10) || 115200
    serialBaudRateInput.value = String(form.serialBaudRate)
    form.serialDataBits = serialDataBitsValue.value
    form.serialStopBits = serialStopBitsValue.value
    form.serialParity = serialParityValue.value
  }
  const normalized = { ...form }
  // Identity (密钥库) 的用户名与凭据完全由所引用的 identity 提供，连接时
  // MaterializeIdentity 会以 identity 的 username/password 覆盖本字段。
  // 从别的认证方式切到 identity 时，旧字段若残留 enc:v1: 密文，会被
  // 云同步原样带进仓库（同步规范化只处理 authType=="password" 的连接），
  // 导致他机显示字面量 enc:v1:xxx（issue #711）。保存时清掉两者以绝后患。
  if (normalized.authType === 'identity') {
    normalized.password = ''
    normalized.user = ''
  }
  // key 相关字段只在对应认证方式下有效；切走后清掉，避免把残留的路径/密钥
  // 文本原样带进仓库（同 #711 语义）。
  if (normalized.authType !== 'key') normalized.keyPath = ''
  if (normalized.authType !== 'keyText') normalized.keyContent = ''
  normalized.kerberosRealm = normalized.authType === 'kerberos'
    ? normalized.kerberosRealm?.trim()
    : ''
  normalized.postLoginExpectSteps = normalizeExpectSteps(form.postLoginExpectSteps || [])
  if (postLoginMode.value === 'script') {
    normalized.postLoginExpectSteps = []
  } else {
    normalized.postLoginScript = ''
  }
  const redisSentinel = normalized.type === 'redis' && normalized.redisMode === 'sentinel'
  if (redisSentinel) {
    if (!normalized.redisSentinels?.trim()) throw new Error(t('conn.redisSentinelsRequired'))
    if (!normalized.redisMasterName?.trim()) throw new Error(t('conn.redisMasterNameRequired'))
  } else if (normalized.type !== 'local' && normalized.type !== 'wsl' && normalized.type !== 'serial' && normalized.type !== 'k8s' && normalized.type !== 'container' && !normalized.host.trim()) {
    throw new Error(t('conn.hostRequired'))
  }
  if (normalized.type === 's3') {
    if (!normalized.user?.trim()) throw new Error('S3: Access Key is required')
    if (!normalized.password?.trim()) throw new Error('S3: Secret Key is required')
  }
  if (normalized.type === 'database' && normalized.dbType === 'postgres' && !normalized.dbName?.trim()) {
    throw new Error(t('db.pgDbNameRequired'))
  }
  if (normalized.type === 'elasticsearch' && normalized.authType === 'apikey' && !normalized.password?.trim()) {
    throw new Error(t('conn.esApiKeyRequired'))
  }
  if (!normalized.name.trim()) {
    normalized.name = generateUniqueName(
      normalized.type === 'serial' ? (normalized.serialPort || 'Serial')
        : normalized.type === 'k8s' ? (normalized.k8sContext || 'Kubernetes')
        : normalized.type === 'container' ? (normalized.containerRuntime || 'container')
        : redisSentinel ? (normalized.redisMasterName?.trim() || 'redis')
        : normalized.host.trim()
    )
  }
  return normalized
}

function cloneExpectSteps(steps: PostLoginExpectStep[]): PostLoginExpectStep[] {
  return steps.map(step => ({ ...step }))
}

function normalizeExpectSteps(steps: PostLoginExpectStep[]): PostLoginExpectStep[] {
  return steps
    .map(step => ({
      expect: step.expect.trim(),
      send: step.send,
      enter: step.enter !== false,
      timeoutSecond: step.timeoutSecond || 10
    }))
    .filter(step => step.expect || step.send)
}

function addExpectStep() {
  if (!form.postLoginExpectSteps) {
    form.postLoginExpectSteps = []
  }
  form.postLoginExpectSteps.push({
    expect: '',
    send: '',
    enter: true,
    timeoutSecond: 10
  })
}

function removeExpectStep(index: number) {
  form.postLoginExpectSteps?.splice(index, 1)
}

function validateContainer(): boolean {
  if (form.type !== 'container') return true
  if (form.containerTransport === 'ssh' && !form.containerSSHConnId) {
    msg.error(t('conn.containerSSHRefRequired'))
    return false
  }
  if (form.containerTransport === 'ssh' && !sshConnections.value.length) return false
  return true
}

function validateX11Desktop(): boolean {
  if (form.type !== 'x11-desktop') return true
  if (form.x11DesktopDesktopType === 'custom' && !form.x11DesktopCustomCmd?.trim()) {
    msg.error(t('conn.x11DesktopCustomCmdRequired'))
    return false
  }
  return true
}

async function onTest() {
  if (!validateContainer()) return
  if (!validateX11Desktop()) return
  let config: ConnectionConfig
  try {
    config = normalizeForm()
  } catch (e: any) {
    // 表单校验失败（如必填字段为空）；把错误提示出来而不是静默返回。
    msg.error(e?.message || String(e))
    return
  }
  testStatus.value = 'checking'
  try {
    const desc = await TestConnection(config)
    testStatus.value = 'success'
    msg.success(desc)
  } catch (e: any) {
    testStatus.value = 'error'
    msg.error(backendErrorText(e))
  }
}

function onSave() {
  if (!validateContainer()) return
  if (!validateX11Desktop()) return
  try {
    const config = normalizeForm()
    handled = true
    emit('save', config)
    visible.value = false
    if (!props.editConfig) {
      resetForm()
    }
  } catch (e: any) {
    // 表单校验失败（如必填字段为空）；提示错误并保持对话框打开。
    msg.error(e?.message || String(e))
  }
}

function onConnectOnly() {
  if (!validateContainer()) return
  if (!validateX11Desktop()) return
  try {
    const config = normalizeForm()
    handled = true
    emit('connectOnly', config)
    visible.value = false
    if (!props.editConfig) {
      resetForm()
    }
  } catch (e: any) {
    // 表单校验失败（如必填字段为空）；提示错误并保持对话框打开。
    msg.error(e?.message || String(e))
  }
}

function onConnect() {
  if (!validateContainer()) return
  if (!validateX11Desktop()) return
  try {
    const config = normalizeForm()
    handled = true
    emit('connect', config)
    visible.value = false
    if (!props.editConfig) {
      resetForm()
    }
  } catch (e: any) {
    // 表单校验失败（如必填字段为空）；提示错误并保持对话框打开。
    msg.error(e?.message || String(e))
  }
}
</script>

<style scoped>
/* Key-path field: the folder-picker and use-default buttons share one append
   slot. Element Plus styles a single append button with `margin: 0 -20px` to
   cancel the slot's padding; with two buttons that negative margin makes them
   overlap each other, so neutralise it and let the pair flow side by side. */
.key-path-actions {
  display: flex;
  align-items: center;
  height: 100%;
  margin: 0 -20px;
}
.key-path-actions :deep(.el-button) {
  margin: 0;
}
/* Thin vertical divider between the two append buttons, slightly inset so it
   reads as a separator rather than a border of either button. */
.key-path-divider {
  width: 1px;
  align-self: stretch;
  margin: 6px 0;
  background: var(--el-input-border-color);
}
/* Inline kubeconfig YAML editor (replaces the former plain textarea). */
.kubeconfig-editor {
  height: 8.75rem;
  width: 100%;
}
/* Color the connection-test status icon (rendered via el-button's `icon` prop,
   so spacing matches the native loading spinner) by result. */
.test-status-btn.test-success :deep(.el-icon) {
  color: var(--success);
}
.test-status-btn.test-error :deep(.el-icon) {
  color: var(--error);
}
/* KeyText paste area renders in a monospace font so PEM blocks stay aligned;
   the textarea only appears after the user reveals the private key. */
.key-text-area :deep(textarea) {
  font-family: var(--font-mono, ui-monospace, "JetBrains Mono", monospace);
}
.key-content-actions {
  margin-top: 0.375rem;
}
.key-content-actions .el-button + .el-button {
  margin-left: 0.5rem;
}

/* ── Layout ── */
.conn-layout {
  display: flex;
  gap: 0;
  min-height: 22.5rem;
}

/* ── Left sidebar ── */
.conn-categories {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  width: 5.625rem;
  flex-shrink: 0;
  padding: 0.5rem 0.5rem 0.5rem 0;
  border-right: 1px solid var(--border-subtle);
}

.cat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  padding: 0.75rem 0.25rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  user-select: none;
  color: var(--text-muted);
  border-left: 0.125rem solid transparent;
  transition: all 0.15s ease;
}

.cat-item:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.cat-item.active {
  color: var(--accent);
  background: var(--accent-subtle);
  border-left-color: var(--accent);
}

.cat-item span {
  font-size: 0.6875rem;
  font-weight: 500;
  font-family: var(--font-ui);
  text-align: center;
  line-height: 1.2;
}

/* ── Right main content ── */
.conn-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 0 0 0 1rem;
}

/* ── Sub-type icon grid ── */
.subtype-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.25rem;
  padding-bottom: 0.875rem;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid var(--border-subtle);
}

.subtype-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.1875rem;
  min-width: 4rem;
  height: 3.25rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 0.6875rem;
  font-weight: 500;
  transition: all 0.15s ease;
}

.subtype-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-default);
}

.subtype-btn.active {
  background: linear-gradient(135deg, var(--accent), var(--accent));
  color: var(--on-accent);
  border-color: var(--accent-glow);
  box-shadow: 0 0 0 1px var(--accent-glow), 0 0.125rem 0.5rem var(--accent-glow);
}

.subtype-btn span {
  text-align: center;
  line-height: 1.2;
  font-size: 0.6875rem;
  white-space: nowrap;
}

/* ── Form fields ── */
.conn-fields {
  padding-right: 0.25rem;
}

/* ── Name + group row ── */
.name-group-row {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  width: 100%;
}

.name-input {
  flex: 1;
  min-width: 0;
}

.group-select {
  width: 10rem;
  flex-shrink: 0;
}

.new-group-btn {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  padding: 0;
}

/* ── Host + port row ── */
.host-port-row {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  width: 100%;
}

.host-input {
  width: calc(100% - 9.375rem) !important;
}

.host-port-sep {
  color: var(--text-muted);
  font-weight: 500;
}

.port-input {
  width: 8.125rem !important;
  flex-shrink: 0;
}

/* ── Field hint text ── */
.field-hint {
  color: var(--text-muted);
  font-size: 0.75rem;
  line-height: 1.4;
}

/* ── RDP custom resolution inputs ── */
.rdp-custom-resolution {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
}

.rdp-custom-resolution .el-input-number {
  flex: 1;
}

.rdp-custom-resolution-x {
  color: var(--text-muted);
}

/* ── Advanced toggle ── */
.advanced-toggle {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.625rem 0 0.5rem;
  margin-bottom: 0.25rem;
  cursor: pointer;
  user-select: none;
  color: var(--text-secondary);
  font-size: 0.8125rem;
  font-weight: 500;
  border-bottom: 1px solid var(--border-subtle);
  transition: color 0.15s;
}

.advanced-toggle:hover {
  color: var(--accent);
}

.advanced-arrow {
  transition: transform 0.2s;
  display: inline-flex;
  align-items: center;
}

.advanced-arrow.expanded {
  transform: rotate(90deg);
}

/* ── Post-login config ── */
.post-login-config {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
}

.expect-steps {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.expect-table {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-subtle);
  border-radius: 0.25rem;
  overflow: hidden;
}

.expect-row {
  display: grid;
  grid-template-columns: 1.625rem minmax(5rem, 1fr) minmax(5.625rem, 1fr) 4rem 2.5rem 1.875rem;
  align-items: stretch;
}

.expect-row:not(:last-child) {
  border-bottom: 1px solid var(--border-subtle);
}

.expect-row > * {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
}

.expect-row > *:not(:last-child) {
  border-right: 1px solid var(--border-subtle);
}

.expect-head {
  background: var(--bg-elevated);
  font-size: 0.75rem;
  line-height: 1.2;
  color: var(--text-secondary);
}

.expect-head > span {
  padding: 0.1875rem 0.25rem;
}

.expect-row :deep(.el-input__wrapper),
.expect-row :deep(.el-input-number .el-input__wrapper) {
  box-shadow: none;
  border-radius: 0;
}

.expect-input,
.send-input,
.timeout-input {
  width: 100%;
}

.timeout-input :deep(.el-input__inner) {
  text-align: center;
}

.step-index {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.remove-step-btn {
  min-width: 0;
}

.add-step-btn {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.expect-help {
  color: var(--text-muted);
  font-size: 0.75rem;
  line-height: 1.4;
}

/* ── Group selector row ── */
.group-select-row {
  display: flex;
  gap: 0.375rem;
  align-items: center;
}
.add-group-btn {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  padding: 0;
}

/* ── Inline select + "+" rows (identity / proxy) ── */
.inline-add-row {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  width: 100%;
}
.inline-add-btn {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  padding: 0;
}

/* ── Dialog overrides ── */
:deep(.el-dialog__body) {
  padding: 1rem 1.25rem;
}
</style>
