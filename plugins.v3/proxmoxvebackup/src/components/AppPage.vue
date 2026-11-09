<template>
  <div class="app-page">
    <!-- 顶部标题栏 -->
    <div class="page-header d-flex align-center flex-wrap ga-3 mb-4">
      <v-icon color="primary" size="28">mdi-server</v-icon>
      <span class="text-h5 font-weight-bold">PVE 守护神</span>
      <v-chip :color="host.online ? 'success' : 'error'" size="small" variant="tonal">
        {{ host.online ? '已连接' : '未连接' }}
      </v-chip>
      <v-chip v-if="host.pve_version" size="small" variant="tonal" class="text-caption">
        PVE {{ host.pve_version }}
      </v-chip>
      <v-spacer />
      <v-tooltip text="查看 PVE 上的 ISO 镜像与 CT 模板" location="bottom">
        <template #activator="{ props: tip }">
          <v-btn v-bind="tip" size="small" variant="tonal" color="deep-purple"
            :disabled="!status.cleanup_template_images" @click="openTplDialog">
            <v-icon size="16" class="mr-1">mdi-cube-outline</v-icon>镜像模板
          </v-btn>
        </template>
      </v-tooltip>
      <v-select v-model="refreshInterval" :items="refreshOptions" density="compact" variant="outlined"
        hide-details label="刷新间隔" style="max-width: 130px" />
      <v-btn size="small" variant="tonal" color="primary" :loading="refreshing" @click="refreshAll">
        <v-icon size="16" class="mr-1">mdi-refresh</v-icon>
        刷新
      </v-btn>
    </div>

    <!-- 连接错误 -->
    <v-alert v-if="!host.online && host.error" type="error" variant="tonal" density="compact" class="mb-4">
      {{ host.error }}
    </v-alert>

    <v-row>
      <!-- ============ 主机概况 ============ -->
      <v-col cols="12" md="6">
        <v-card :class="[{ 'card-collapsed': collapsed.host }, collapsed.host ? '' : 'fill-height']">
          <v-card-title class="d-flex align-center flex-wrap ga-1 cursor-pointer" @click="collapsed.host = !collapsed.host">
            <v-icon color="info" size="22" class="mr-2">mdi-cpu-64-bit</v-icon>
            <span>主机概况</span>
            <v-chip v-if="host.hostname" size="x-small" variant="tonal" color="info" class="ml-2">{{ host.hostname }}</v-chip>
            <v-spacer />
            <v-tooltip text="清理系统日志" location="top">
              <template #activator="{ props: tip }">
                <v-btn v-bind="tip" size="small" variant="text" color="teal" icon="mdi-broom"
                  :loading="busy.cleanupLogs" @click.stop="doCleanup('cleanup_logs', '系统日志清理完成')" />
              </template>
            </v-tooltip>
            <v-tooltip text="清理临时空间" location="top">
              <template #activator="{ props: tip }">
                <v-btn v-bind="tip" size="small" variant="text" color="teal" icon="mdi-delete-sweep-outline"
                  :loading="busy.cleanupTmp" @click.stop="doCleanup('cleanup_tmp', '临时空间清理完成')" />
              </template>
            </v-tooltip>
            <v-tooltip text="重启主机" location="top">
              <template #activator="{ props: tip }">
                <v-btn v-bind="tip" size="small" variant="text" color="warning" icon="mdi-restart"
                  @click.stop="askConfirm('hostReboot', '重启 PVE 主机', '确认重启 PVE 主机？所有虚拟机将受影响！')" />
              </template>
            </v-tooltip>
            <v-tooltip text="关闭主机" location="top">
              <template #activator="{ props: tip }">
                <v-btn v-bind="tip" size="small" variant="text" color="error" icon="mdi-power"
                  @click.stop="askConfirm('hostShutdown', '关闭 PVE 主机', '确认关闭 PVE 主机？所有虚拟机将关机！')" />
              </template>
            </v-tooltip>
            <v-tooltip text="宿主机终端" location="top">
              <template #activator="{ props: tip }">
                <v-btn v-bind="tip" size="small" variant="text" color="deep-purple" icon="mdi-console"
                  @click.stop="termDialog = true" />
              </template>
            </v-tooltip>
            <v-icon size="18" class="ml-1">{{ collapsed.host ? 'mdi-chevron-down' : 'mdi-chevron-up' }}</v-icon>
          </v-card-title>
          <v-card-text v-if="!collapsed.host">
            <div class="text-caption text-medium-emphasis mb-2">
              {{ host.cpu_model || 'CPU 未知' }} · {{ host.cpu_cores || '?' }} 核
              <template v-if="host.ip"> · {{ host.ip }}</template>
              <template v-if="host.kernel"> · {{ host.kernel }}</template>
            </div>
            <template v-for="bar in hostBars" :key="bar.label">
              <div class="d-flex justify-space-between text-body-2 mt-1">
                <span>{{ bar.label }}<template v-if="bar.extra"> · {{ bar.extra }}</template></span>
                <span class="text-medium-emphasis">{{ bar.value }}</span>
              </div>
              <v-progress-linear :model-value="bar.percent" rounded height="8" class="mt-1"
                :color="barColor(bar.percent)" />
            </template>
            <template v-if="storageBars.length">
              <v-divider class="my-2" />
              <template v-for="bar in storageBars" :key="bar.label">
                <div class="d-flex justify-space-between text-body-2 mt-1">
                  <span>{{ bar.label }}</span>
                  <span class="text-medium-emphasis">{{ bar.value }}</span>
                </div>
                <v-progress-linear :model-value="bar.percent" rounded height="8" class="mt-1"
                  :color="barColor(bar.percent)" />
              </template>
            </template>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ============ 最近任务 ============ -->
      <v-col cols="12" md="6">
        <v-card :class="[{ 'card-collapsed': collapsed.tasks }, collapsed.tasks ? '' : 'fill-height']">
          <v-card-title class="d-flex align-center cursor-pointer" @click="collapsed.tasks = !collapsed.tasks">
            <v-icon color="indigo" size="22" class="mr-2">mdi-format-list-bulleted</v-icon>
            <span>最近任务</span>
            <v-spacer />
            <v-icon size="18">{{ collapsed.tasks ? 'mdi-chevron-down' : 'mdi-chevron-up' }}</v-icon>
          </v-card-title>
          <v-card-text v-if="!collapsed.tasks" class="task-list-body">
            <v-list density="compact" class="py-0">
              <v-list-item v-for="t in taskList" :key="t.upid" class="px-0">
                <template #prepend>
                  <v-icon size="18" :color="t.running ? 'warning' : (t.ok ? 'success' : 'error')">
                    {{ t.running ? 'mdi-progress-clock' : (t.ok ? 'mdi-check-circle' : 'mdi-alert-circle') }}
                  </v-icon>
                </template>
                <div class="d-flex align-center flex-wrap ga-2">
                  <span class="text-body-2">{{ t.desc }}</span>
                  <v-chip v-if="t.vmid" size="x-small" variant="tonal" color="info">#{{ t.vmid }}</v-chip>
                  <span class="text-caption text-medium-emphasis">{{ t.timeText }}</span>
                </div>
                <template #append>
                  <span class="text-caption" :class="t.running ? 'text-warning' : (t.ok ? 'text-success' : 'text-error')">
                    {{ t.statusText }}
                  </span>
                </template>
              </v-list-item>
              <v-list-item v-if="!taskList.length">
                <v-list-item-title class="text-caption text-medium-emphasis text-center py-2">
                  {{ monitorLoading ? '加载中...' : '暂无任务记录' }}
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ============ 性能监控 ============ -->
      <v-col cols="12">
        <v-card :class="{ 'card-collapsed': collapsed.mon }">
          <v-card-title class="d-flex align-center flex-wrap ga-2 cursor-pointer" @click="collapsed.mon = !collapsed.mon">
            <v-icon color="primary" size="22" class="mr-1">mdi-chart-areaspline</v-icon>
            <span>性能监控</span>
            <v-spacer />
            <v-btn-toggle v-model="monitorTf" mandatory density="compact" variant="outlined" divided @click.stop>
              <v-btn value="hour" size="small">小时</v-btn>
              <v-btn value="day" size="small">天</v-btn>
              <v-btn value="week" size="small">周</v-btn>
              <v-btn value="month" size="small">月</v-btn>
            </v-btn-toggle>
            <v-icon size="18">{{ collapsed.mon ? 'mdi-chevron-down' : 'mdi-chevron-up' }}</v-icon>
          </v-card-title>
          <v-card-text v-if="!collapsed.mon">
            <v-progress-linear v-if="monitorLoading" indeterminate height="2" color="primary" class="mb-2" />
            <div v-if="monCharts.length" class="chart-grid">
              <div v-for="ch in monCharts" :key="ch.key" class="chart-cell">
                <div class="d-flex justify-space-between text-caption mb-1">
                  <span>{{ ch.title }}</span>
                  <span class="font-weight-bold" :style="{ color: ch.lines.length > 1 ? '' : ch.lines[0].color }">{{ ch.last }}</span>
                </div>
                <svg class="mini-chart" viewBox="0 0 300 64" preserveAspectRatio="none">
                  <template v-for="(ln, i) in ch.lines" :key="i">
                    <polygon :points="ln.areaPoints" :fill="ln.color" opacity="0.12" stroke="none" />
                    <polyline :points="ln.points" fill="none" :stroke="ln.color" stroke-width="1.6" />
                  </template>
                </svg>
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无监控数据（请检查 PVE API 端口 8006 是否可达）' }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ============ 虚拟机 / 容器 ============ -->
      <v-col cols="12">
        <v-card :class="{ 'card-collapsed': collapsed.vm }">
          <v-card-title class="d-flex align-center flex-wrap ga-2 cursor-pointer" @click="collapsed.vm = !collapsed.vm">
            <v-icon color="teal" size="22" class="mr-1">mdi-monitor-multiple</v-icon>
            <span>虚拟机 / 容器</span>
            <v-chip size="x-small" color="success" variant="tonal">运行 {{ vmRunning }}</v-chip>
            <v-chip size="x-small" color="grey" variant="tonal">停止 {{ vmStopped }}</v-chip>
            <v-spacer />
            <v-text-field v-model="vmSearch" density="compact" variant="outlined" hide-details clearable
              placeholder="搜索 ID / 名称 / 标签" prepend-inner-icon="mdi-magnify" style="max-width: 220px"
              @click.stop />
            <v-btn size="small" variant="text" color="error" :loading="busy.stopAll"
              @click.stop="askConfirm('stopAll', '停止所有任务', '确认停止 PVE 上所有正在运行的任务？')">
              <v-icon size="16" class="mr-1">mdi-stop-circle-outline</v-icon>全部停止
            </v-btn>
            <v-icon size="18">{{ collapsed.vm ? 'mdi-chevron-down' : 'mdi-chevron-up' }}</v-icon>
          </v-card-title>
          <v-card-text v-if="!collapsed.vm">
            <v-list density="compact" class="py-0">
              <v-list-item v-for="vm in filteredVms" :key="vm.vmid + vm.type" class="px-0 vm-row">
                <template #prepend>
                  <v-icon size="20" :color="vm.status === 'running' ? 'success' : 'grey'">
                    {{ vm.type === 'LXC' ? 'mdi-cube-outline' : 'mdi-server' }}
                  </v-icon>
                </template>
                <div class="d-flex align-center flex-wrap ga-2">
                  <span class="font-weight-medium">{{ vm.displayName || vm.name || vm.vmid }}</span>
                  <span class="text-caption text-medium-emphasis">#{{ vm.vmid }} · {{ vm.type }}</span>
                  <v-chip size="x-small" :color="vm.status === 'running' ? 'success' : 'grey'" variant="tonal">
                    {{ vm.status === 'running' ? '运行中' : '已停止' }}
                  </v-chip>
                  <span v-if="vm.status === 'running' && vm.uptime" class="text-caption text-medium-emphasis">
                    {{ fmtUptime(vm.uptime) }}
                  </span>
                </div>
                <template #append>
                  <div class="d-flex ga-1">
                    <v-tooltip text="noVNC 控制台" location="top">
                      <template #activator="{ props: tip }">
                        <v-btn v-bind="tip" size="x-small" variant="text" color="deep-purple" @click="openConsole(vm)">
                          <v-icon size="16">mdi-console</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                    <v-tooltip text="监控图表" location="top">
                      <template #activator="{ props: tip }">
                        <v-btn v-bind="tip" size="x-small" variant="text" color="primary" @click="openGuest(vm)">
                          <v-icon size="16">mdi-chart-line</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                    <template v-for="act in vmActions(vm)" :key="act.action">
                      <v-tooltip :text="act.label" location="top">
                        <template #activator="{ props: tip }">
                          <v-btn v-bind="tip" size="x-small" variant="text" :color="act.color"
                            :loading="vm._actionLoading === act.action" @click="onVmAction(vm, act.action)">
                            <v-icon size="16">{{ act.icon }}</v-icon>
                          </v-btn>
                        </template>
                      </v-tooltip>
                    </template>
                  </div>
                </template>
              </v-list-item>
              <v-list-item v-if="!filteredVms.length">
                <v-list-item-title class="text-caption text-medium-emphasis text-center py-2">
                  {{ vmList.length ? '没有匹配的虚拟机 / 容器' : '暂无数据' }}
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- ============ 备份文件 ============ -->
      <v-col cols="12">
        <v-card :class="{ 'card-collapsed': collapsed.files }">
          <v-card-title class="d-flex align-center flex-wrap ga-2 cursor-pointer" @click="collapsed.files = !collapsed.files">
            <v-icon color="amber-darken-2" size="22" class="mr-1">mdi-file-multiple-outline</v-icon>
            <span>备份文件</span>
            <v-chip size="x-small" variant="tonal" color="info">本地 {{ backupCounts.local }}</v-chip>
            <v-chip size="x-small" variant="tonal" color="deep-purple">WebDAV {{ backupCounts.webdav }}</v-chip>
            <v-chip v-if="status.backup_activity || status.restore_activity" size="x-small" color="warning" variant="tonal">
              <v-icon size="12" class="mr-1">mdi-progress-clock</v-icon>{{ status.backup_activity ? '备份中' : '恢复中' }}
            </v-chip>
            <v-chip v-else-if="status.enabled && status.next_run_time" size="x-small" color="success" variant="tonal"
              prepend-icon="mdi-clock-outline">
              下次：{{ status.next_run_time }}
            </v-chip>
            <v-spacer />
            <v-btn size="small" variant="tonal" color="primary" :loading="busy.backup" @click.stop="runBackup">
              <v-icon size="16" class="mr-1">mdi-play-circle-outline</v-icon>立即备份
            </v-btn>
            <v-tooltip text="清空备份/恢复历史" location="top">
              <template #activator="{ props: tip }">
                <v-btn v-bind="tip" size="small" variant="text" color="error" icon="mdi-history"
                  :loading="busy.clearHistory"
                  @click.stop="askConfirm('clearHistory', '清空历史记录', '确认清空所有备份与恢复历史记录？')" />
              </template>
            </v-tooltip>
            <v-select v-model="fileSource" :items="['全部', '本地备份', 'WebDAV备份']" density="compact" variant="outlined"
              hide-details style="max-width: 140px" @click.stop />
            <v-text-field v-model="fileSearch" density="compact" variant="outlined" hide-details clearable
              placeholder="搜索文件名" prepend-inner-icon="mdi-magnify" style="max-width: 200px" @click.stop />
            <v-icon size="18">{{ collapsed.files ? 'mdi-chevron-down' : 'mdi-chevron-up' }}</v-icon>
          </v-card-title>
          <v-card-text v-if="!collapsed.files">
            <v-list density="compact" class="py-0">
              <v-list-item v-for="f in filteredFiles" :key="f.source + f.filename" class="px-0">
                <template #prepend>
                  <v-icon size="20" :color="f.source === 'WebDAV备份' ? 'deep-purple' : 'primary'">
                    {{ f.source === 'WebDAV备份' ? 'mdi-cloud-outline' : 'mdi-harddisk' }}
                  </v-icon>
                </template>
                <div class="d-flex align-center flex-wrap ga-2">
                  <span class="text-body-2 text-truncate" :title="f.filename">{{ f.filename }}</span>
                  <span class="text-caption text-medium-emphasis">{{ f.size_mb }} MB · {{ f.date }} {{ f.time }}</span>
                </div>
                <template #append>
                  <div class="d-flex ga-1">
                    <v-tooltip text="下载" location="top">
                      <template #activator="{ props: tip }">
                        <v-btn v-bind="tip" size="x-small" variant="text" color="primary" :loading="busy.dl === f.filename"
                          @click="downloadBackup(f)">
                          <v-icon size="16">mdi-download</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                    <v-tooltip text="恢复" location="top">
                      <template #activator="{ props: tip }">
                        <v-btn v-bind="tip" size="x-small" variant="text" color="deep-purple"
                          @click="askRestore(f)">
                          <v-icon size="16">mdi-restore</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                    <v-tooltip text="删除" location="top">
                      <template #activator="{ props: tip }">
                        <v-btn v-bind="tip" size="x-small" variant="text" color="error" :loading="busy.del === f.filename"
                          @click="askConfirm('delete', '删除备份', `确认删除 ${f.source} 中的 ${f.filename}？此操作不可恢复！`, f)">
                          <v-icon size="16">mdi-delete-outline</v-icon>
                        </v-btn>
                      </template>
                    </v-tooltip>
                  </div>
                </template>
              </v-list-item>
              <v-list-item v-if="!filteredFiles.length">
                <v-list-item-title class="text-caption text-medium-emphasis text-center py-2">
                  {{ backupFiles.length ? '没有匹配的备份文件' : '暂无备份文件' }}
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 镜像模板对话框 -->
    <v-dialog v-model="tplDialog" max-width="760" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center flex-wrap ga-2">
          <v-icon color="deep-purple" size="20" class="mr-1">mdi-cube-outline</v-icon>
          <span>镜像模板</span>
          <v-chip size="x-small" variant="tonal" color="info">ISO {{ tplCounts.iso }}</v-chip>
          <v-chip size="x-small" variant="tonal" color="deep-purple">CT 模板 {{ tplCounts.ct }}</v-chip>
          <v-spacer />
          <v-btn icon="mdi-refresh" size="small" variant="text" :loading="tplLoading" @click="fetchTplImages" />
          <v-btn icon="mdi-close" size="small" variant="text" @click="tplDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-0" style="max-height: 480px; overflow-y: auto">
          <v-list density="compact" class="py-0">
            <v-list-item v-for="f in tplList" :key="f.filenameWithType" class="px-4">
              <template #prepend>
                <v-icon size="20" :color="f.type === 'iso' ? 'info' : 'deep-purple'">
                  {{ f.type === 'iso' ? 'mdi-disc' : 'mdi-cube-outline' }}
                </v-icon>
              </template>
              <div class="d-flex align-center flex-wrap ga-2">
                <span class="text-body-2 text-truncate" :title="f.filename">{{ f.filename }}</span>
                <v-chip size="x-small" :color="f.type === 'iso' ? 'info' : 'deep-purple'" variant="tonal">
                  {{ f.type === 'iso' ? 'ISO 镜像' : 'CT 模板' }}
                </v-chip>
              </div>
              <template #append>
                <span class="text-caption text-medium-emphasis">
                  {{ f.size_mb != null ? f.size_mb.toFixed(2) + ' MB' : '-' }}
                  <template v-if="f.date"> · {{ f.date }}</template>
                </span>
              </template>
            </v-list-item>
            <v-list-item v-if="!tplList.length">
              <v-list-item-title class="text-caption text-medium-emphasis text-center py-4">
                {{ tplLoading ? '加载中...' : '暂无 ISO 镜像 / CT 模板' }}
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- 虚机实时画面对话框 -->
    <v-dialog v-model="screenDialog.show" max-width="960" @after-leave="stopScreenTimer()">
      <v-card>
        <v-card-title class="d-flex align-center flex-wrap ga-2 py-3">
          <v-icon color="deep-purple" size="20">mdi-monitor-shimmer</v-icon>
          <span class="text-subtitle-1">实时画面 · {{ screenDialog.name }} (#{{ screenDialog.vmid }})</span>
          <v-spacer />
          <v-select v-model="screenRate" :items="[
            { title: '1 秒', value: 1 }, { title: '2 秒', value: 2 }, { title: '3 秒', value: 3 },
            { title: '5 秒', value: 5 }, { title: '暂停', value: 0 }]"
            density="compact" variant="outlined" hide-details label="刷新" style="max-width: 110px" />
          <v-btn size="small" variant="text" color="grey" icon="mdi-refresh" title="立即刷新" @click="screenTick++" />
          <v-btn size="small" variant="tonal" color="info" prepend-icon="mdi-console"
            title="完整图形控制台（需登录 PVE）" @click="openNovnc({ vmid: screenDialog.vmid, type: 'qemu', displayName: screenDialog.name })">
            noVNC
          </v-btn>
          <v-btn size="small" variant="text" color="grey" icon="mdi-close" @click="screenDialog.show = false" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-0">
          <div class="screen-wrap">
            <div v-if="screenError" class="text-caption text-error pa-4 text-center">
              获取画面失败：虚机可能未运行，或显示设备不支持截图。可稍后重试或使用 noVNC 完整控制台。
            </div>
            <img v-if="screenSrc" :src="screenSrc" class="screen-img" alt="虚机画面"
              @error="screenError = true" @load="screenError = false" />
          </div>
          <v-alert type="info" variant="tonal" density="compact" class="ma-2 text-caption">
            实时画面为只读监视（每 1~5 秒截图，无需登录 PVE）；需要键鼠操作请点上方「noVNC」打开完整控制台，或在「主机概况 → 宿主机终端」用命令操作。
          </v-alert>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- 宿主机终端对话框 -->
    <v-dialog v-model="termDialog" max-width="860" scrollable @after-leave="termOutput = ''">
      <v-card class="terminal-card">
        <v-card-title class="d-flex align-center ga-2 py-3">
          <v-icon color="deep-purple" size="20">mdi-console</v-icon>
          <span class="text-subtitle-1">宿主机终端 · root@{{ host.hostname || monitorData?.node || 'PVE' }}</span>
          <v-spacer />
          <v-btn size="small" variant="text" color="grey" icon="mdi-delete-outline" title="清屏" @click="termOutput = ''" />
          <v-btn size="small" variant="text" color="grey" icon="mdi-close" @click="termDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-0">
          <div ref="termBox" class="terminal-box">
            <div v-if="!termOutput" class="text-grey text-caption pa-3">
              输入命令回车执行（非交互模式，单次超时 20 秒；不支持 top/vim 等全屏程序，请用 top -bn1 等）
            </div>
            <pre v-else class="terminal-pre">{{ termOutput }}</pre>
            <div v-if="termBusy" class="text-caption text-warning pa-2">
              <v-icon size="14" class="mr-1">mdi-progress-clock</v-icon>执行中...
            </div>
          </div>
          <div class="pa-2 d-flex flex-wrap ga-1 quick-cmds">
            <v-chip v-for="c in quickCmds" :key="c" size="x-small" variant="tonal" color="deep-purple"
              style="cursor:pointer" @click="runCommand(c)">{{ c }}</v-chip>
          </div>
        </v-card-text>
        <v-divider />
        <v-card-text class="py-2">
          <div class="d-flex align-center ga-2">
            <span class="terminal-prompt">$</span>
            <v-text-field v-model="termInput" variant="plain" density="compact" hide-details
              placeholder="输入命令，回车执行" style="font-family: monospace"
              :disabled="termBusy" @keyup.enter="runCommand()"
              @keyup.up="termHistoryNav(-1)" @keyup.down="termHistoryNav(1)" />
            <v-btn color="deep-purple" variant="tonal" size="small" :loading="termBusy" @click="runCommand()">
              执行
            </v-btn>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- 虚机监控图表对话框 -->
    <v-dialog v-model="guestDialog.show" max-width="760" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center flex-wrap ga-2">
          <v-icon color="primary" size="20" class="mr-1">mdi-chart-line</v-icon>
          <span>{{ guestDialog.name }}</span>
          <span class="text-caption text-medium-emphasis">#{{ guestDialog.vmid }} · {{ guestDialog.type === 'lxc' ? 'LXC' : 'VM' }}</span>
          <v-spacer />
          <v-btn-toggle v-model="guestTf" mandatory density="compact" variant="outlined" divided>
            <v-btn value="hour" size="small">小时</v-btn>
            <v-btn value="day" size="small">天</v-btn>
            <v-btn value="week" size="small">周</v-btn>
            <v-btn value="month" size="small">月</v-btn>
          </v-btn-toggle>
          <v-btn icon="mdi-close" size="small" variant="text" @click="guestDialog.show = false" />
        </v-card-title>
        <v-card-text>
          <div v-if="guestCharts.length" class="chart-grid">
            <div v-for="ch in guestCharts" :key="ch.key" class="chart-cell">
              <div class="d-flex justify-space-between text-caption mb-1">
                <span>{{ ch.title }}</span>
                <span class="font-weight-bold" :style="{ color: ch.lines.length > 1 ? '' : ch.lines[0].color }">{{ ch.last }}</span>
              </div>
              <svg class="mini-chart" viewBox="0 0 300 64" preserveAspectRatio="none">
                <template v-for="(ln, i) in ch.lines" :key="i">
                  <polygon :points="ln.areaPoints" :fill="ln.color" opacity="0.12" stroke="none" />
                  <polyline :points="ln.points" fill="none" :stroke="ln.color" stroke-width="1.6" />
                </template>
              </svg>
            </div>
          </div>
          <div v-else class="text-caption text-medium-emphasis text-center py-6">
            {{ guestLoading ? '加载中...' : '暂无监控数据' }}
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- 恢复对话框 -->
    <v-dialog v-model="restoreDialog.show" max-width="420">
      <v-card>
        <v-card-title class="text-subtitle-1">恢复备份</v-card-title>
        <v-card-text>
          <div class="text-body-2 mb-3 text-truncate" :title="restoreDialog.item?.filename">
            {{ restoreDialog.item?.filename }}
            <span class="text-caption text-medium-emphasis">（{{ restoreDialog.item?.source }}）</span>
          </div>
          <v-text-field v-model="restoreDialog.vmid" label="目标 VMID（可选，默认恢复到原机）" density="compact"
            variant="outlined" hide-details />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="restoreDialog.show = false">取消</v-btn>
          <v-btn color="deep-purple" variant="tonal" :loading="busy.restore" @click="doRestore">开始恢复</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 通用确认对话框 -->
    <v-dialog v-model="confirmDialog.show" max-width="380">
      <v-card>
        <v-card-title class="text-subtitle-1">{{ confirmDialog.title }}</v-card-title>
        <v-card-text class="text-body-2">{{ confirmDialog.text }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmDialog.show = false">取消</v-btn>
          <v-btn color="error" variant="tonal" @click="confirmDialog.confirm && confirmDialog.confirm()">确认执行</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 提示条 -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">{{ snackbar.text }}</v-snackbar>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import axios from 'axios';

const props = defineProps({
  api: { type: [Object, Function], required: true },
  pluginId: { type: String, default: 'ProxmoxVEBackup' },
});

const pluginId = computed(() => props.pluginId || 'ProxmoxVEBackup');
const API_BASE = computed(() => `plugin/${pluginId.value}`);

// ---------- 状态 ----------
const refreshing = ref(false);
const refreshInterval = ref(30);
const refreshOptions = [
  { title: '10 秒', value: 10 },
  { title: '30 秒', value: 30 },
  { title: '60 秒', value: 60 },
  { title: '手动', value: 0 },
];
const collapsed = reactive({ host: false, vm: false, files: false, mon: false, tasks: false });

const pve = ref({});
const status = ref({});
const vmList = ref([]);
const backupFiles = ref([]);

// ---------- PVE 监控（RRD） ----------
const monitorData = ref(null);
const monitorLoading = ref(false);
const monitorTf = ref('hour');
const guestDialog = reactive({ show: false, vmid: null, type: 'qemu', name: '' });
const guestTf = ref('hour');
const guestData = ref(null);
const guestLoading = ref(false);

const vmSearch = ref('');
const fileSearch = ref('');
const fileSource = ref('全部');

// ---------- 宿主机终端 ----------
const termDialog = ref(false);
const termOutput = ref('');
const termInput = ref('');
const termBusy = ref(false);
const termHistory = ref([]);
const termHistIdx = ref(-1);
const termBox = ref(null);
const quickCmds = ['qm list', 'pct list', 'df -h', 'free -h', 'uptime', 'pveversion -v | head -20'];

function termHistoryNav(dir) {
  if (!termHistory.value.length) return;
  let idx = termHistIdx.value + dir;
  if (idx < -1) idx = -1;
  if (idx >= termHistory.value.length) idx = termHistory.value.length - 1;
  termHistIdx.value = idx;
  termInput.value = idx === -1 ? '' : termHistory.value[idx];
}

async function runCommand(cmd) {
  const command = (cmd || termInput.value).trim();
  if (!command || termBusy.value) return;
  termBusy.value = true;
  if (!cmd) {
    termHistory.value.push(command);
    if (termHistory.value.length > 50) termHistory.value.shift();
    termHistIdx.value = -1;
    termInput.value = '';
  }
  termOutput.value += `\nroot@pve:~# ${command}\n`;
  await nextTick(() => {
    if (termBox.value) termBox.value.scrollTop = termBox.value.scrollHeight;
  });
  try {
    const res = await props.api.post(`${API_BASE.value}/terminal`, { command });
    if (res?.success) {
      termOutput.value += (res.output || '') + (res.exit_code ? `\n[退出码 ${res.exit_code}]\n` : '\n');
    } else {
      termOutput.value += `${res?.message || res?.error || '执行失败'}\n`;
    }
  } catch (e) {
    termOutput.value += `${e?.message || '请求失败'}\n`;
  }
  await nextTick(() => {
    if (termBox.value) termBox.value.scrollTop = termBox.value.scrollHeight;
  });
  termBusy.value = false;
}

// ---------- 虚机控制台 ----------
// noVNC 需要浏览器持有 PVE 登录 cookie（SameSite 限制 iframe 内不可用，且 MP 插件 API 无 WebSocket 无法转发画面流）。
// 故 QEMU 虚机走 screendump 实时画面（后端 API+SSH，无需登录 PVE）；完整图形控制台仍用 noVNC 独立小窗。
const screenDialog = reactive({ show: false, vmid: null, name: '' });
const screenTick = ref(0);
const screenRate = ref(2);
const screenTimer = ref(null);
const screenError = ref(false);

const screenSrc = computed(() => {
  if (!screenDialog.show || !screenDialog.vmid) return '';
  const apikey = window.API_TOKEN || localStorage.getItem('api_token') || '';
  return `/api/v1/${API_BASE.value}/vm_screen?vmid=${screenDialog.vmid}&type=qemu`
    + `&apikey=${encodeURIComponent(apikey)}&t=${screenTick.value}`;
});

function startScreenTimer() {
  stopScreenTimer();
  if (screenRate.value > 0) {
    screenTimer.value = setInterval(() => { screenTick.value++; }, screenRate.value * 1000);
  }
}
function stopScreenTimer() {
  if (screenTimer.value) { clearInterval(screenTimer.value); screenTimer.value = null; }
}
watch(screenRate, startScreenTimer);

function openConsole(vm) {
  const isLxc = String(vm.type || '').toUpperCase() === 'LXC';
  if (!isLxc) {
    screenDialog.vmid = vm.vmid;
    screenDialog.name = vm.displayName || vm.name || vm.vmid;
    screenError.value = false;
    screenDialog.show = true;
    nextTick(startScreenTimer);
    return;
  }
  openNovnc(vm);
}

function consoleUrl(vm) {
  const m = monitorData.value || {};
  const apiHost = m.api_host || host.value.ip || window.location.hostname;
  const ctype = String(vm?.type || '').toUpperCase() === 'LXC' ? 'lxc' : 'kvm';
  const node = m.node ? `&node=${encodeURIComponent(m.node)}` : '';
  return `https://${apiHost}:8006/?console=${ctype}&novnc=1&vmid=${vm?.vmid}${node}&resize=off`;
}

function openNovnc(vm) {
  const m = monitorData.value || {};
  const apiHost = m.api_host || host.value.ip || window.location.hostname;
  const feat = 'popup=yes,width=1100,height=760,menubar=no,toolbar=no,location=no,status=no';

  let ticketTs = 0;
  try { ticketTs = parseInt(localStorage.getItem('pveWebLoginTs') || '0', 10) || 0; } catch {}
  const loggedIn = ticketTs && (Date.now() - ticketTs) < 2 * 3600 * 1000; // 与 PVE ticket 有效期对齐

  if (loggedIn) {
    window.open(consoleUrl(vm), `pvenovnc-${vm.vmid}`, feat);
    return;
  }
  // 首次（或超过2小时）：弹 PVE 登录页，登录后再次点击控制台直达
  try { localStorage.setItem('pveWebLoginTs', String(Date.now())); } catch {}
  window.open(`https://${apiHost}:8006/`, 'pvelogin', feat);
  showTip('已弹出 PVE 登录窗口，请先登录；登录后回到本页再次点击控制台即可打开 noVNC', 'info');
}

// ---------- 镜像模板 ----------
const tplDialog = ref(false);
const tplList = ref([]);
const tplLoading = ref(false);
const tplCounts = computed(() => ({
  iso: tplList.value.filter((f) => f.type === 'iso').length,
  ct: tplList.value.filter((f) => f.type !== 'iso').length,
}));

async function fetchTplImages() {
  tplLoading.value = true;
  try {
    const files = await props.api.get(`${API_BASE.value}/template_images`);
    tplList.value = Array.isArray(files)
      ? files.map((f) => ({ ...f, filenameWithType: `${f.filename}_${f.type}` }))
      : [];
  } catch {
    tplList.value = [];
  }
  tplLoading.value = false;
}

function openTplDialog() {
  tplDialog.value = true;
  fetchTplImages();
}

const busy = reactive({ backup: false, restore: false, del: null, dl: null, stopAll: false, cleanupLogs: false, cleanupTmp: false, clearHistory: false });

const snackbar = ref({ show: false, text: '', color: 'success' });
let timer = null;

function showTip(text, color = 'success') {
  snackbar.value = { show: true, text, color };
}

// ---------- 计算属性 ----------
// 主机信息：REST 监控数据优先，SSH pve_status 兜底
const host = computed(() => {
  const p = pve.value || {};
  const m = monitorData.value || {};
  return {
    online: p.online !== false,
    error: p.error || '',
    hostname: m.node || p.hostname || '',
    pve_version: m.pveversion || p.pve_version || '',
    cpu_model: m.cpu_model || p.cpu_model || '',
    cpu_cores: m.cpu_cores || p.cpu_cores || '',
    ip: p.ip && p.ip !== '-' ? p.ip : '',
    kernel: p.kernel || m.kversion || '',
  };
});

const hostBars = computed(() => {
  const p = pve.value || {};
  const m = monitorData.value || {};
  const mem = m.memory || {};
  const root = m.rootfs || {};
  const swap = m.swap || {};
  const fmtGB = (v) => (v == null || isNaN(v) ? '-' : (v / 1073741824).toFixed(1) + ' GB');
  const pct = (u, t) => (u != null && t > 0 ? Math.round((u / t) * 1000) / 10 : 0);
  // REST（bytes）优先；SSH pve_status 容量单位为 MB，换算为 bytes
  const cpuVal = m.cpu != null ? Math.round(m.cpu * 1000) / 10 : (p.cpu_usage ?? null);
  const toB = (v) => (v == null ? null : v * 1048576);
  const memUsed = mem.used ?? toB(p.mem_used);
  const memTotal = mem.total ?? toB(p.mem_total);
  const rootUsed = root.used ?? toB(p.disk_used);
  const rootTotal = root.total ?? toB(p.disk_total);
  const swapUsed = swap.used ?? toB(p.swap_used);
  const swapTotal = swap.total ?? toB(p.swap_total);
  // 温度合理值过滤（SSH 解析可能出垃圾值）
  const okTemp = (t) => (t != null && t >= 10 && t <= 110 ? t : null);
  const cpuTemp = okTemp(p.cpu_temp);
  return [
    {
      label: 'CPU',
      percent: cpuVal ?? 0,
      value: cpuVal != null ? cpuVal + '%' : '-',
      extra: cpuTemp != null ? cpuTemp + '°C' : '',
    },
    {
      label: '内存',
      percent: pct(memUsed, memTotal),
      value: `${fmtGB(memUsed)} / ${fmtGB(memTotal)}`,
    },
    {
      label: '根分区',
      percent: pct(rootUsed, rootTotal),
      value: `${fmtGB(rootUsed)} / ${fmtGB(rootTotal)}`,
    },
    {
      label: 'Swap',
      percent: pct(swapUsed, swapTotal),
      value: swapTotal ? `${fmtGB(swapUsed)} / ${fmtGB(swapTotal)}` : '未启用',
    },
  ];
});

function barColor(v) {
  if (v == null) return 'grey';
  if (v >= 90) return 'error';
  if (v >= 75) return 'warning';
  return 'success';
}

const vmRunning = computed(() => vmList.value.filter((v) => v.status === 'running').length);
const vmStopped = computed(() => vmList.value.filter((v) => v.status !== 'running').length);

const filteredVms = computed(() => {
  const kw = (vmSearch.value || '').trim().toLowerCase();
  if (!kw) return vmList.value;
  return vmList.value.filter((v) =>
    [v.vmid, v.displayName, v.name, v.tags].some((x) => String(x ?? '').toLowerCase().includes(kw))
  );
});

const backupCounts = computed(() => ({
  local: backupFiles.value.filter((f) => f.source === '本地备份').length,
  webdav: backupFiles.value.filter((f) => f.source === 'WebDAV备份').length,
}));

// 存储使用（来自 PVE API）
const storageBars = computed(() => {
  const fmtGB = (v) => (v == null ? '-' : (v / 1073741824).toFixed(1) + ' GB');
  return (monitorData.value?.storages || [])
    .filter((s) => s.total > 0)
    .map((s) => ({
      label: `存储 · ${s.storage} (${s.type})`,
      percent: Math.round((s.used_fraction || 0) * 100),
      value: `${fmtGB(s.used)} / ${fmtGB(s.total)}`,
    }));
});

// 最近任务列表
const taskList = computed(() => (monitorData.value?.tasks || []).map((t) => {
  const st = String(t.status || '');
  const ok = st.toUpperCase() === 'OK';
  const running = !st;
  const d = t.starttime ? new Date(t.starttime * 1000) : null;
  const timeText = d
    ? `${d.getMonth() + 1}-${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    : '';
  return { ...t, ok, running, timeText, statusText: running ? '运行中' : (ok ? 'OK' : '失败') };
}));

// ---------- SVG 图表 ----------
function chartSeries(values, color, w = 300, h = 64, maxV = null) {
  const pts = values.map((v) => Number(v) || 0);
  if (!pts.length) return null;
  const max = maxV || Math.max(...pts, 1e-9);
  const stepX = pts.length > 1 ? w / (pts.length - 1) : 0;
  const coords = pts.map((v, i) => [i * stepX, h - Math.max(0, Math.min(1, v / max)) * (h - 4) - 2]);
  const points = coords.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  return { points, areaPoints: `${points} ${w},${h} 0,${h}`, color };
}

function fmtChartNum(v) {
  return v >= 100 ? Math.round(v).toString() : String(Math.round(v * 10) / 10);
}

// 节点监控 6 图：CPU / 内存 / 网络进出 / 根分区 / Swap / IO等待
const monCharts = computed(() => {
  const rrd = monitorData.value?.rrd || [];
  if (!rrd.length) return [];
  const gb = 1 / 1073741824;
  const mb = 1 / 1048576;
  const num = (r, f) => Number(r[f]) || 0;
  const maxOf = (f) => Math.max(...rrd.map((r) => num(r, f)));
  const defs = [
    { key: 'cpu', title: 'CPU 使用率', unit: '%', fixedMax: 100,
      fields: [{ f: 'cpu', color: '#4f8cff', scale: 100 }] },
    { key: 'mem', title: '内存使用', unit: ' GB', fixedMax: maxOf('memtotal') * gb,
      fields: [{ f: 'memused', color: '#43b581', scale: gb }] },
    { key: 'net', title: '网络 进/出', unit: ' MB/s',
      fields: [{ f: 'netin', color: '#ef6b6b', scale: mb }, { f: 'netout', color: '#43b581', scale: mb }] },
    { key: 'root', title: '根分区已用', unit: ' GB',
      fields: [{ f: 'rootused', color: '#f59e0b', scale: gb }] },
    { key: 'swap', title: 'Swap 使用', unit: ' GB',
      fields: [{ f: 'swapused', color: '#9c27b0', scale: gb }] },
    { key: 'iowait', title: 'IO 等待', unit: '%', fixedMax: 100,
      fields: [{ f: 'iowait', color: '#e91e63', scale: 100 }] },
  ];
  return defs.map((d) => {
    const lines = [];
    for (const fd of d.fields) {
      const values = rrd.map((r) => num(r, fd.f) * fd.scale);
      const ln = chartSeries(values, fd.color, 300, 64, d.fixedMax);
      if (!ln) return null;
      lines.push(ln);
    }
    const lastVals = d.fields.map((fd) => (rrd.length ? num(rrd[rrd.length - 1], fd.f) * fd.scale : 0));
    const last = `${lastVals.map(fmtChartNum).join(' / ')}${d.unit}`;
    return { key: d.key, title: d.title, lines, last };
  }).filter(Boolean);
});

// 单虚机监控 4 图：CPU / 内存 / 网络 / 磁盘IO
const guestCharts = computed(() => {
  const rrd = guestData.value?.rrd || [];
  if (!rrd.length) return [];
  const gb = 1 / 1073741824;
  const mb = 1 / 1048576;
  const num = (r, f) => Number(r[f]) || 0;
  const maxOf = (f) => Math.max(...rrd.map((r) => num(r, f)));
  const defs = [
    { key: 'cpu', title: 'CPU 使用率', unit: '%', fixedMax: 100,
      fields: [{ f: 'cpu', color: '#4f8cff', scale: 100 }] },
    { key: 'mem', title: '内存使用', unit: ' GB', fixedMax: maxOf('maxmem') * gb,
      fields: [{ f: 'mem', color: '#43b581', scale: gb }] },
    { key: 'net', title: '网络 进/出', unit: ' MB/s',
      fields: [{ f: 'netin', color: '#ef6b6b', scale: mb }, { f: 'netout', color: '#43b581', scale: mb }] },
    { key: 'disk', title: '磁盘 读/写', unit: ' MB/s',
      fields: [{ f: 'diskread', color: '#f59e0b', scale: mb }, { f: 'diskwrite', color: '#e91e63', scale: mb }] },
  ];
  return defs.map((d) => {
    const lines = [];
    for (const fd of d.fields) {
      const values = rrd.map((r) => num(r, fd.f) * fd.scale);
      const ln = chartSeries(values, fd.color, 300, 64, d.fixedMax);
      if (!ln) return null;
      lines.push(ln);
    }
    const lastVals = d.fields.map((fd) => (rrd.length ? num(rrd[rrd.length - 1], fd.f) * fd.scale : 0));
    const last = `${lastVals.map(fmtChartNum).join(' / ')}${d.unit}`;
    return { key: d.key, title: d.title, lines, last };
  }).filter(Boolean);
});

const filteredFiles = computed(() => {
  let list = backupFiles.value;
  if (fileSource.value !== '全部') list = list.filter((f) => f.source === fileSource.value);
  const kw = (fileSearch.value || '').trim().toLowerCase();
  if (kw) list = list.filter((f) => String(f.filename || '').toLowerCase().includes(kw));
  return list;
});

function vmActions(vm) {
  if (vm.status === 'running') {
    return [
      { action: 'reboot', label: '重启', icon: 'mdi-restart', color: 'warning' },
      { action: 'stop', label: '停止', icon: 'mdi-stop', color: 'error' },
      { action: 'snapshot', label: '快照', icon: 'mdi-camera-outline', color: 'teal' },
    ];
  }
  return [{ action: 'start', label: '启动', icon: 'mdi-play', color: 'success' }];
}

function fmtUptime(sec) {
  const d = Math.floor(sec / 86400);
  const h = Math.floor((sec % 86400) / 3600);
  const m = Math.floor((sec % 3600) / 60);
  if (d) return `${d}天${h}小时`;
  if (h) return `${h}小时${m}分`;
  return `${m}分钟`;
}

// ---------- 数据拉取 ----------
// 本地缓存：上次数据立即呈现、后台静默刷新（stale-while-revalidate）
const CACHE_PREFIX = 'pveCache_';
const CACHE_TTL = 2 * 3600 * 1000;

function loadCache(key) {
  try {
    const raw = localStorage.getItem(CACHE_PREFIX + key);
    if (!raw) return null;
    const obj = JSON.parse(raw);
    if (!obj || Date.now() - (obj.ts || 0) > CACHE_TTL) return null;
    return obj.data;
  } catch {
    return null;
  }
}

function saveCache(key, data) {
  try {
    localStorage.setItem(CACHE_PREFIX + key, JSON.stringify({ ts: Date.now(), data }));
  } catch {
    /* 存储失败忽略 */
  }
}

async function fetchPveStatus() {
  try {
    const data = await props.api.get(`${API_BASE.value}/pve_status`);
    pve.value = data || {};
    saveCache('pve', pve.value);
  } catch (e) {
    if (!Object.keys(pve.value).length) pve.value = loadCache('pve') || { online: false, error: e?.message || '获取失败' };
  }
}

async function fetchVmList() {
  try {
    const data = await props.api.get(`${API_BASE.value}/container_status`);
    vmList.value = Array.isArray(data) ? data : [];
    saveCache('vmlist', vmList.value);
  } catch {
    if (!vmList.value.length) vmList.value = loadCache('vmlist') || [];
    /* 请求失败保留当前数据，下次刷新重试 */
  }
}

async function fetchStatus() {
  try {
    status.value = (await props.api.get(`${API_BASE.value}/status`)) || {};
    saveCache('status', status.value);
  } catch {
    if (!Object.keys(status.value).length) status.value = loadCache('status') || {};
  }
}

async function fetchBackupFiles() {
  try {
    const files = await props.api.get(`${API_BASE.value}/available_backups`);
    backupFiles.value = Array.isArray(files) ? files : [];
    saveCache('files', backupFiles.value);
  } catch {
    if (!backupFiles.value.length) backupFiles.value = loadCache('files') || [];
  }
}

async function fetchMonitor() {
  monitorLoading.value = true;
  try {
    const data = await props.api.get(`${API_BASE.value}/monitor?timeframe=${monitorTf.value}`);
    if (data && !data.error) {
      monitorData.value = data;
      saveCache('monitor', data);
    }
  } catch {
    if (!monitorData.value) monitorData.value = loadCache('monitor');
  }
  monitorLoading.value = false;
}

async function fetchGuest() {
  if (!guestDialog.vmid) return;
  guestLoading.value = true;
  try {
    const data = await props.api.get(
      `${API_BASE.value}/guest_monitor?type=${guestDialog.type}&vmid=${guestDialog.vmid}&timeframe=${guestTf.value}`);
    guestData.value = data && !data.error ? data : null;
  } catch {
    guestData.value = null;
  }
  guestLoading.value = false;
}

async function openGuest(vm) {
  guestDialog.vmid = vm.vmid;
  guestDialog.type = vm.type === 'LXC' ? 'lxc' : 'qemu';
  guestDialog.name = vm.displayName || vm.name || vm.vmid;
  guestData.value = null;
  guestDialog.show = true;
  await fetchGuest();
}

async function refreshAll() {
  refreshing.value = true;
  await Promise.all([fetchStatus(), fetchPveStatus(), fetchVmList(), fetchBackupFiles(), fetchMonitor()]);
  refreshing.value = false;
}

function setupTimer() {
  if (timer) clearInterval(timer);
  if (refreshInterval.value > 0) timer = setInterval(refreshAll, refreshInterval.value * 1000);
}
watch(refreshInterval, setupTimer);
watch(monitorTf, fetchMonitor);
watch(guestTf, () => { if (guestDialog.show) fetchGuest(); });

// ---------- 交互 ----------
const confirmDialog = reactive({ show: false, title: '', text: '', confirm: null });
function askConfirm(key, title, text, item = null) {
  const acts = {
    delete: () => doDelete(item),
    stopAll: doStopAll,
    clearHistory: doClearHistory,
    hostReboot: () => doHostAction('reboot'),
    hostShutdown: () => doHostAction('shutdown'),
  };
  confirmDialog.title = title;
  confirmDialog.text = text;
  confirmDialog.confirm = acts[key] || null;
  confirmDialog.show = true;
}

async function runBackup() {
  busy.backup = true;
  try {
    const res = await props.api.post(`${API_BASE.value}/run_backup`, {});
    showTip(res.message || '备份任务已启动', res.success === false ? 'error' : 'success');
    await fetchStatus();
  } catch (e) {
    showTip('启动失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.backup = false;
}

async function onVmAction(vm, action) {
  if (action === 'snapshot') {
    vm._actionLoading = 'snapshot';
    try {
      const res = await props.api.post(`${API_BASE.value}/container_snapshot`, { vmid: vm.vmid, type: vm.type });
      showTip(res.message || '快照操作完成', res.success ? 'success' : 'error');
    } catch (e) {
      showTip('快照失败: ' + (e?.message || '未知错误'), 'error');
    }
    vm._actionLoading = null;
    return;
  }
  vm._actionLoading = action;
  try {
    const res = await props.api.post(`${API_BASE.value}/container_action`, {
      vmid: vm.vmid,
      type: vm.type,
      action,
    });
    showTip(res.message || `${action} 操作完成`, res.success ? 'success' : 'error');
    await fetchVmList();
  } catch (e) {
    showTip('操作失败: ' + (e?.message || '未知错误'), 'error');
  }
  vm._actionLoading = null;
}

async function doDelete(item) {
  confirmDialog.show = false;
  if (!item) return;
  busy.del = item.filename;
  try {
    const payload = { filename: item.filename, source: item.source };
    if (item.storage) payload.storage = item.storage;
    if (item.remote_dir) payload.remote_dir = item.remote_dir;
    const res = await props.api.post(`${API_BASE.value}/delete_backup`, payload);
    showTip(res.message || '删除完成', res.success ? 'success' : 'error');
    await fetchBackupFiles();
  } catch (e) {
    showTip('删除失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.del = null;
}

async function doStopAll() {
  confirmDialog.show = false;
  busy.stopAll = true;
  try {
    const res = await props.api.post(`${API_BASE.value}/stop_all_tasks`, {});
    showTip(res.message || '已停止所有任务', res.success ? 'success' : 'error');
    await fetchVmList();
  } catch (e) {
    showTip('操作失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.stopAll = false;
}

async function doClearHistory() {
  confirmDialog.show = false;
  busy.clearHistory = true;
  try {
    await props.api.post(`${API_BASE.value}/clear_history`, {});
    showTip('历史记录已清空');
  } catch (e) {
    showTip('清空失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.clearHistory = false;
}

async function doHostAction(action) {
  confirmDialog.show = false;
  try {
    const res = await props.api.post(`${API_BASE.value}/host_action`, { action });
    showTip(res.msg || res.message || '指令已下发', res.success ? 'warning' : 'error');
  } catch (e) {
    showTip('操作失败: ' + (e?.message || '未知错误'), 'error');
  }
}

async function doCleanup(path, okText) {
  const key = path === 'cleanup_logs' ? 'cleanupLogs' : 'cleanupTmp';
  busy[key] = true;
  try {
    const res = await props.api.post(`${API_BASE.value}/${path}`, {});
    showTip(res.message || okText, res.success ? 'success' : 'error');
  } catch (e) {
    showTip('清理失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy[key] = false;
}

// ---------- 恢复与下载 ----------
const restoreDialog = reactive({ show: false, item: null, vmid: '' });
function askRestore(item) {
  restoreDialog.item = item;
  restoreDialog.vmid = '';
  restoreDialog.show = true;
}

async function doRestore() {
  restoreDialog.show = false;
  busy.restore = true;
  try {
    const payload = { filename: restoreDialog.item.filename, source: restoreDialog.item.source };
    if (restoreDialog.vmid) payload.vmid = restoreDialog.vmid;
    const res = await props.api.post(`${API_BASE.value}/restore`, payload);
    showTip(res.message || '恢复任务已启动', res.success === false ? 'error' : 'success');
    await fetchStatus();
  } catch (e) {
    showTip('恢复失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.restore = false;
}

async function downloadBackup(item) {
  busy.dl = item.filename;
  try {
    const res = await props.api.get(`${API_BASE.value}/token`);
    if (res && res.api_token) {
      window.API_TOKEN = res.api_token;
      localStorage.setItem('api_token', res.api_token);
    }
  } catch {
    /* 已有 token 则忽略 */
  }
  const apikey = window.API_TOKEN || localStorage.getItem('api_token') || '';
  const params = new URLSearchParams({ filename: item.filename, source: item.source });
  if (apikey) params.append('apikey', apikey);
  if (item.storage) params.append('storage', item.storage);
  if (item.remote_dir) params.append('remote_dir', item.remote_dir);
  try {
    const resp = await axios.get(`/api/v1/${API_BASE.value}/download_backup?` + params.toString(), {
      responseType: 'blob',
    });
    let filename = item.filename || 'backup.dat';
    const disposition = resp.headers['content-disposition'];
    if (disposition) {
      const match = disposition.match(/filename="?([^";]+)"?/);
      if (match) filename = decodeURIComponent(match[1]);
    }
    const blobUrl = window.URL.createObjectURL(new Blob([resp.data]));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
    showTip('已开始下载: ' + filename);
  } catch (e) {
    showTip('下载失败: ' + (e?.message || '未知错误'), 'error');
  }
  busy.dl = null;
}

// ---------- 生命周期 ----------
onMounted(async () => {
  // 先用上次缓存立即呈现（2小时内有效），随后后台静默刷新
  pve.value = loadCache('pve') || {};
  status.value = loadCache('status') || {};
  vmList.value = loadCache('vmlist') || [];
  backupFiles.value = loadCache('files') || [];
  monitorData.value = loadCache('monitor');
  await refreshAll();
  setupTimer();
});

onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped>
.app-page {
  padding: 4px 2px;
}
.cursor-pointer {
  cursor: pointer;
}
.vm-row {
  min-height: 40px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
.vm-row:last-child {
  border-bottom: none;
}

/* 迷你折线图 */
.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}
.chart-cell {
  min-width: 0;
}
.mini-chart {
  width: 100%;
  height: 64px;
  display: block;
  border-radius: 8px;
  background: rgba(var(--v-border-color), 0.04);
}
.task-list-body {
  max-height: 360px;
  overflow-y: auto;
}
/* 折叠态：卡片去边框底色，只留标题行 */
.card-collapsed {
  background: transparent !important;
  box-shadow: none !important;
  border: none !important;
}

.terminal-card {
  background: #1a1a2e;
}

.terminal-box {
  height: 380px;
  overflow-y: auto;
  background: #0d1117;
  padding: 8px 12px;
}

.terminal-pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #c9d1d9;
}

.terminal-prompt {
  color: #7ee787;
  font-family: monospace;
  font-weight: bold;
}

.quick-cmds {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.screen-wrap {
  min-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0d1117;
}

.screen-img {
  max-width: 100%;
  max-height: 70vh;
  display: block;
}
</style>
