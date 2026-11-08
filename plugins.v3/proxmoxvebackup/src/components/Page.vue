<template>
  <v-card flat class="plugin-page glass-card">
    <!-- 顶部标题栏 -->
    <v-card-title class="section-title d-flex align-center mb-1 header-title-row" style="padding: 10px 0 6px 0; min-height:unset;">
      <v-icon class="mr-1" color="primary" size="26">mdi-server</v-icon>
      <span style="font-size:1.15rem; font-weight:600; letter-spacing:1px;">PVE虚拟机守护神</span>
      <v-spacer :style="{ flexGrow: 0.5 }" />
      <span class="cache-notice-text">提示：本界面数据可能存在延迟 最终数据请以Proxmox VE控制台为准</span>
      <v-spacer :style="{ flexGrow: 1.0 }" />
      <v-btn
        v-if="isMobile"
        icon
        class="close-btn"
        @click="$emit('close')"
        style="margin-left:auto; background:transparent; box-shadow:none; min-width:unset; width:auto; height:auto;"
      >
        <v-icon size="28" style="color:#999;">mdi-close</v-icon>
      </v-btn>
    </v-card-title>
    <!-- 统一的主内容区域 -->
    <div class="status-page-container">
      <!-- PVE主机状态卡片：全宽显示 -->
      <v-row class="status-main-row">
        <v-col cols="12" class="status-col">
        <v-card class="modern-status-card" elevation="0">
          <div class="card-header-modern">
            <div class="card-header-left">
              <div class="card-icon-wrapper card-icon-success">
                <v-icon size="24" color="success">mdi-server</v-icon>
              </div>
              <div>
                <div class="card-title-modern">PVE主机状态</div>
                <div class="card-subtitle-modern">Host Status</div>
              </div>
            </div>
            <div class="pve-header-info">
              <div class="pve-header-info-item">
                <v-icon size="16" color="primary" class="mr-1">mdi-server-network</v-icon>
                <span class="pve-header-label">主机名</span>
                <span class="pve-header-value">{{ pveStatus.hostname || '-' }}</span>
              </div>
              <div class="pve-header-info-item">
                <v-icon size="16" color="cyan" class="mr-1">mdi-ip-network</v-icon>
                <span class="pve-header-label">主机IP</span>
                <span class="pve-header-value">{{ pveStatus.ip || '-' }}</span>
              </div>
              <div class="pve-header-info-item">
                <v-icon size="16" color="cyan" class="mr-1">mdi-chart-line</v-icon>
                <span class="pve-header-label">负载</span>
                <span class="pve-header-value">{{ pveStatus.load_avg?.join(' / ') || '-' }}</span>
              </div>
              <div class="pve-header-info-item">
                <v-icon size="16" color="grey" class="mr-1">mdi-cog</v-icon>
                <span class="pve-header-label">内核</span>
                <span class="pve-header-value">{{ pveStatus.kernel || '-' }}</span>
              </div>
              <div class="pve-header-info-item" v-if="pveStatus.pve_version">
                <v-icon size="16" color="blue" class="mr-1">mdi-tag</v-icon>
                <span class="pve-header-label">PVE版本</span>
                <span class="pve-header-value text-caption">{{ pveStatus.pve_version }}</span>
              </div>
            </div>
            <div class="host-action-btns-modern">
              <v-tooltip text="重启主机" location="bottom">
                <template #activator="{ props }">
                  <v-btn 
                    icon 
                    v-bind="props"
                    class="modern-action-btn reboot-btn" 
                    :loading="hostActionLoading === 'reboot'" 
                    @click="handleHostActionClick('reboot')"
                    size="small"
                  >
                    <v-icon size="20">mdi-restart</v-icon>
              </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="关闭主机" location="bottom">
                <template #activator="{ props }">
                  <v-btn 
                    icon 
                    v-bind="props"
                    class="modern-action-btn shutdown-btn" 
                    :loading="hostActionLoading === 'shutdown'" 
                    @click="handleHostActionClick('shutdown')"
                    size="small"
                  >
                    <v-icon size="20">mdi-power</v-icon>
              </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="刷新状态" location="bottom">
              <template #activator="{ props }">
                <v-btn 
                  icon 
                  v-bind="props"
                    class="modern-action-btn refresh-btn" 
                    @click="fetchPveStatus"
                    size="small"
                  >
                    <v-icon size="20">mdi-refresh</v-icon>
              </v-btn>
                </template>
              </v-tooltip>
            </div>
        </div>
          <div class="card-body-modern">
            <div v-if="pveStatus.online" class="pve-info-grid">
              <!-- 资源使用情况 -->
              <div class="pve-info-right">
                <div class="status-item-modern">
                  <div class="status-item-header">
                    <v-icon size="16" color="info" class="mr-2">mdi-chip</v-icon>
                    <span class="status-label">CPU</span>
        </div>
                  <div class="resource-info">
                    <div class="resource-text-compact">
                      <span class="resource-model">{{ pveStatus.cpu_cores }}核</span>
                      <span v-if="pveStatus.cpu_temp" class="resource-temp-inline" :class="`temp-${getTempColor(pveStatus.cpu_temp)}`">
                        <v-icon size="12" class="mr-1" :color="getTempColor(pveStatus.cpu_temp)">mdi-thermometer</v-icon>
                        <span :style="{ color: getTempColorValue(pveStatus.cpu_temp) }">{{ pveStatus.cpu_temp }}°C</span>
                      </span>
                    </div>
                    <div class="resource-progress-wrapper">
                      <v-progress-linear 
                        :model-value="pveStatus.cpu_usage || 0" 
                        :color="getUsageColor(pveStatus.cpu_usage || 0)"
                        height="6"
                        rounded
                        class="resource-progress"
                      ></v-progress-linear>
                      <span class="resource-percent">{{ pveStatus.cpu_usage }}%</span>
                    </div>
                  </div>
                </div>
                <div class="status-item-modern">
                  <div class="status-item-header">
                    <v-icon size="16" color="purple" class="mr-2">mdi-memory</v-icon>
                    <span class="status-label">内存</span>
                  </div>
                  <div class="resource-info">
                    <div class="resource-text-compact">
                      <span class="resource-model">{{ pveStatus.mem_used }}/{{ pveStatus.mem_total }}MB</span>
                    </div>
                    <div class="resource-progress-wrapper">
                      <v-progress-linear 
                        :model-value="pveStatus.mem_usage || 0" 
                        :color="getUsageColor(pveStatus.mem_usage || 0)"
                        height="6"
                        rounded
                        class="resource-progress"
                      ></v-progress-linear>
                      <span class="resource-percent">{{ pveStatus.mem_usage }}%</span>
                    </div>
                  </div>
                </div>
                <div class="status-item-modern">
                  <div class="status-item-header">
                    <v-icon size="16" color="orange" class="mr-2">mdi-harddisk</v-icon>
                    <span class="status-label">硬盘</span>
                  </div>
                  <div class="resource-info">
                    <div class="resource-text-compact">
                      <span class="resource-model">{{ pveStatus.disk_used }}/{{ pveStatus.disk_total }}MB</span>
                      <span v-if="pveStatus.disk_temp" class="resource-temp-inline" :class="`temp-${getTempColor(pveStatus.disk_temp)}`">
                        <v-icon size="12" class="mr-1" :color="getTempColor(pveStatus.disk_temp)">mdi-thermometer</v-icon>
                        <span :style="{ color: getTempColorValue(pveStatus.disk_temp) }">{{ pveStatus.disk_temp }}°C</span>
                      </span>
                    </div>
                    <div class="resource-progress-wrapper">
                      <v-progress-linear 
                        :model-value="pveStatus.disk_usage || 0" 
                        :color="getDiskUsageColor(pveStatus.disk_usage || 0)"
                        height="6"
                        rounded
                        class="resource-progress"
                      ></v-progress-linear>
                      <span class="resource-percent">{{ pveStatus.disk_usage }}%</span>
                    </div>
                  </div>
                </div>
                <div class="status-item-modern" v-if="pveStatus.swap_total">
                  <div class="status-item-header">
                    <v-icon size="16" color="purple" class="mr-2">mdi-swap-horizontal</v-icon>
                    <span class="status-label">SWAP</span>
                  </div>
                  <div class="resource-info">
                    <div class="resource-text-compact">
                      <span class="resource-model">{{ pveStatus.swap_used || 0 }}/{{ pveStatus.swap_total }}MB</span>
                    </div>
                    <div class="resource-progress-wrapper">
                      <v-progress-linear 
                        :model-value="pveStatus.swap_usage || 0" 
                        :color="getUsageColor(pveStatus.swap_usage || 0)"
                        height="6"
                        rounded
                        class="resource-progress"
                      ></v-progress-linear>
                      <span class="resource-percent">{{ pveStatus.swap_usage ? pveStatus.swap_usage.toFixed(1) : 0 }}%</span>
                    </div>
                  </div>
                </div>
                <div class="status-item-modern" v-if="pveStatus.io_delay !== undefined && pveStatus.io_delay !== null">
                  <div class="status-item-header">
                    <v-icon size="16" color="red" class="mr-2">mdi-clock-outline</v-icon>
                    <span class="status-label">IO延迟</span>
                  </div>
                  <div class="resource-info">
                    <div class="resource-text-compact">
                      <span class="resource-model">{{ formatIODelay(pveStatus.io_delay) }}</span>
                    </div>
                    <div class="resource-progress-wrapper">
                      <v-progress-linear 
                        :model-value="getIODelayProgress(pveStatus.io_delay || 0)" 
                        :color="getIODelayColor(pveStatus.io_delay || 0)"
                        height="6"
                        rounded
                        class="resource-progress"
                      ></v-progress-linear>
                      <span class="resource-percent">{{ formatIODelay(pveStatus.io_delay) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="offline-state">
              <v-icon size="56" color="error" class="mb-3">mdi-alert-circle-outline</v-icon>
              <div class="offline-text">主机离线或连接失败</div>
              <div class="offline-error text-caption">{{ pveStatus.error }}</div>
            </div>
          </div>
    </v-card>
      </v-col>
    </v-row>

      <!-- 容器状态卡片：全宽 -->
      <v-row class="status-main-row">
        <v-col cols="12" class="status-col">
        <v-card class="modern-status-card" elevation="0">
          <div class="card-header-modern">
            <div class="card-header-left">
              <div class="card-icon-wrapper card-icon-info">
                <v-icon size="24" color="info">mdi-docker</v-icon>
              </div>
              <div>
                <div class="card-title-modern">容器状态</div>
                <div class="card-subtitle-modern">Container Status</div>
              </div>
            </div>
            <div class="container-header-summary">
              <div class="header-summary-item">
                <v-icon size="18" color="primary" class="mr-2">mdi-docker</v-icon>
                <span class="header-summary-label">容器总数</span>
                <v-chip size="x-small" color="primary" class="ml-2">{{ containerStatus.length }}</v-chip>
              </div>
              <div class="header-summary-item">
                <v-icon size="18" color="purple" class="mr-2">mdi-server</v-icon>
                <span class="header-summary-label">QEMU</span>
                <v-chip size="x-small" color="purple" class="ml-2">{{ containerStatus.filter(c => c.type === 'qemu').length }}</v-chip>
              </div>
              <div class="header-summary-item">
                <v-icon size="18" color="info" class="mr-2">mdi-cube-outline</v-icon>
                <span class="header-summary-label">LXC</span>
                <v-chip size="x-small" color="info" class="ml-2">{{ containerStatus.filter(c => c.type === 'lxc').length }}</v-chip>
              </div>
              <div class="header-summary-item">
                <v-icon size="18" color="success" class="mr-2">mdi-play-circle</v-icon>
                <span class="header-summary-label">运行中</span>
                <v-chip size="x-small" color="success" class="ml-2">{{ containerStatus.filter(c => c.status === 'running').length }}</v-chip>
              </div>
              <div class="header-summary-item">
                <v-icon size="18" color="grey" class="mr-2">mdi-stop-circle</v-icon>
                <span class="header-summary-label">已停止</span>
                <v-chip size="x-small" color="grey" class="ml-2">{{ containerStatus.filter(c => c.status !== 'running').length }}</v-chip>
              </div>
            </div>
            <v-tooltip text="刷新容器状态" location="bottom">
              <template #activator="{ props }">
                <v-btn 
                  icon 
                  v-bind="props"
                  class="modern-action-btn refresh-btn" 
                  @click="fetchContainerStatus"
                  size="small"
                >
                  <v-icon icon="mdi-sync" size="20" />
                </v-btn>
              </template>
            </v-tooltip>
        </div>
          <div class="card-body-modern">
        <div v-if="!isMobile">
    <v-data-table
      :headers="containerHeaders"
      :items="containerStatus"
      class="elevation-0"
      hide-default-footer
      density="compact"
    >
      <template #item.type="{ item }">
        <v-chip size="x-small" :color="item.type === 'qemu' ? 'primary' : 'info'">{{ item.type === 'qemu' ? 'QEMU' : (item.type === 'lxc' ? 'LXC' : item.type) }}</v-chip>
      </template>
      <template #item.status="{ item }">
        <v-chip :color="item.status === 'running' ? 'success' : 'grey'" size="x-small">{{ item.status }}</v-chip>
      </template>
      <template #item.tags="{ item }">
        <span v-if="!item.tags || !item.tags.trim()">-</span>
        <template v-else>
          <v-chip
            v-for="tag in item.tags.split(/[,;]+/).map(t => t.trim()).filter(Boolean)"
            :key="tag"
            size="x-small"
            :style="{ backgroundColor: getPveTagColor(tag), color: '#fff', fontWeight: 600 }"
            class="mr-1"
          >{{ tag }}</v-chip>
        </template>
      </template>
      <template #item.uptime="{ item }">
        <span v-html="formatUptime(item.uptime)"></span>
      </template>
      <template #item.actions="{ item }">
        <div class="d-flex justify-end align-center" style="gap: 4px;">
          <v-btn size="x-small" color="success" :loading="item._actionLoading === 'start'" :disabled="item.status === 'running'" @click="handleVmAction(item, 'start')" class="mr-1">启动</v-btn>
          <v-btn size="x-small" color="error" :loading="item._actionLoading === 'stop'" :disabled="item.status !== 'running'" @click="handleVmAction(item, 'stop')" class="mr-1">关闭</v-btn>
          <v-btn size="x-small" color="info" :loading="item._actionLoading === 'reboot'" :disabled="item.status !== 'running'" @click="handleVmAction(item, 'reboot')" class="mr-1">重启</v-btn>
          <v-btn size="x-small" color="primary" :loading="item._actionLoading === 'snapshot'" @click="handleVmSnapshot(item)">创建快照</v-btn>
        </div>
      </template>
    </v-data-table>
  </div>
  <div v-else>
    <div v-for="item in containerStatus" :key="item.vmid" class="mobile-card">
      <div class="d-flex align-center mb-1">
        <span class="font-weight-bold" style="font-size:1.1em;">{{ item.displayName || item.description || item.hostname || item.name || '-' }}</span>
        <v-chip size="x-small" :color="item.type === 'qemu' ? 'primary' : 'info'" class="ml-2">{{ item.type === 'qemu' ? 'QEMU' : (item.type === 'lxc' ? 'LXC' : item.type) }}</v-chip>
        <v-chip :color="item.status === 'running' ? 'success' : 'grey'" size="x-small" class="ml-2">{{ item.status }}</v-chip>
      </div>
      <div class="d-flex align-center mb-1" style="font-size:0.95em;color:#90caf9;">
        <span>ID: {{ item.vmid }}</span>
      </div>
      <div class="d-flex align-center mb-1" style="font-size:0.95em;">
        <v-icon size="18" color="success" class="mr-1">mdi-timer-outline</v-icon>
        <span v-html="formatUptime(item.uptime)"></span>
      </div>
      <div class="mobile-actions d-flex align-center" style="gap:8px;flex-wrap:wrap;">
        <v-btn size="small" color="success" :loading="item._actionLoading === 'start'" :disabled="item.status === 'running'" @click="handleVmAction(item, 'start')">启动</v-btn>
        <v-btn size="small" color="error" :loading="item._actionLoading === 'stop'" :disabled="item.status !== 'running'" @click="handleVmAction(item, 'stop')">关闭</v-btn>
        <v-btn size="small" color="info" :loading="item._actionLoading === 'reboot'" :disabled="item.status !== 'running'" @click="handleVmAction(item, 'reboot')">重启</v-btn>
        <v-btn size="small" color="primary" :loading="item._actionLoading === 'snapshot'" @click="handleVmSnapshot(item)">快照</v-btn>
      </div>
    </div>
  </div>
          </div>
      </v-card>
      </v-col>
    </v-row>
    </div>

    <!-- 底部固定操作栏 -->
    <v-card-actions class="px-2 py-1 footer-btns">
      <v-btn class="glow-btn glow-btn-blue" size="small" prepend-icon="mdi-history" @click="showHistoryDialog = true">任务历史</v-btn>
      <v-btn class="glow-btn glow-btn-cyan" size="small" prepend-icon="mdi-file-document-multiple" @click="openBackupFilesDialog">备份文件</v-btn>
      <v-btn class="glow-btn glow-btn-purple" size="small" prepend-icon="mdi-cube-outline" @click="openTemplateImagesDialog" :disabled="!cleanupTemplateImagesEnabled">镜像模板</v-btn>
      <v-spacer />
      <v-btn class="glow-btn glow-btn-red" size="small" prepend-icon="mdi-delete-sweep" :disabled="!status.enabled || !status.auto_cleanup_tmp" :loading="loadingCleanupTempSpace" @click="handleCleanupTempSpace">清理临时空间</v-btn>
      <v-btn class="glow-btn glow-btn-gold" size="small" prepend-icon="mdi-broom" :disabled="!status.enabled || !status.enable_log_cleanup" :loading="loadingCleanupLogs" @click="handleCleanupLogs">清理系统日志</v-btn>
      <v-btn class="glow-btn glow-btn-orange" size="small" prepend-icon="mdi-broom" :loading="loadingClear" @click="clearHistory">清理历史记录</v-btn>
      <v-spacer />
      <v-btn class="glow-btn glow-btn-purple" size="small" prepend-icon="mdi-restore" :loading="loadingRestore" :disabled="!status.enabled || !status.enable_restore" @click="openRestoreDialog()">立即恢复</v-btn>
      <v-btn class="glow-btn glow-btn-green" size="small" prepend-icon="mdi-database-arrow-up" :loading="loadingBackup" :disabled="!status.enabled" @click="runBackup">立即备份</v-btn>
      <v-btn class="glow-btn" size="small" prepend-icon="mdi-stop-circle" :loading="loadingStopTasks" @click="stopAllTasks">停止任务</v-btn>
      <v-spacer />
      <v-btn class="glow-btn glow-btn-pink" size="small" prepend-icon="mdi-cog" @click="$emit('switch')">配置</v-btn>
    </v-card-actions>
  </v-card>

    <!-- 恢复弹窗 -->
    <v-dialog v-model="showRestoreDialog" max-width="500">
      <v-card>
        <v-card-title>选择要恢复的备份文件</v-card-title>
        <v-card-text>
          <v-select
            v-model="selectedRestoreFile"
            :items="backupFiles"
            :item-title="item => item.filename + ' (' + item.source + ')'"
            item-value="filename"
            label="备份文件"
          />
          <v-text-field v-model="restoreDisk" label="恢复存储硬盘" placeholder="请输入存储池" />
          <v-text-field v-model="restoreVmid" label="目标VMID(可选)"/>
          <v-switch v-model="restoreForce" label="强制恢复(覆盖现有VM)"/>
          <v-switch v-model="restoreSkipExisting" label="跳过已存在的VM"/>
        </v-card-text>
        <v-card-actions>
          <v-btn color="grey" @click="showRestoreDialog = false">取消</v-btn>
          <v-btn color="success" :loading="loadingRestore" @click="runRestore" :disabled="!selectedRestoreFile">确认恢复</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 进度条/提示 -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="snackbar.timeout">
      {{ snackbar.text }}
    </v-snackbar>

    <!-- 删除确认弹窗 -->
    <v-dialog v-model="showDeleteDialog" max-width="420">
      <v-card>
        <v-card-title class="text-h6">删除确认</v-card-title>
        <v-card-text>
          <div class="mb-2">
            确定要删除备份文件
            <span class="font-weight-bold" style="color:#d32f2f">{{ deleteTarget?.filename }}</span>
            吗？
          </div>
          <div v-if="deleteTarget">
            <v-chip size="small" color="primary" class="mr-2">{{ deleteTarget.source }}</v-chip>
            <span class="grey--text text--darken-1">{{ deleteTarget.size_mb ? (deleteTarget.size_mb.toFixed(2) + ' MB') : '-' }}</span>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text color="grey" @click="showDeleteDialog = false" :disabled="deleteLoading">取消</v-btn>
          <v-btn color="error" :loading="deleteLoading === (deleteTarget?.filename + deleteTarget?.source)" @click="handleDeleteConfirm">
            删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 历史记录弹窗 -->
    <v-dialog v-model="showHistoryDialog" max-width="900">
      <v-card>
        <v-card-title class="text-h6">任务历史</v-card-title>
        <v-card-text>
          <v-data-table
            :headers="[
              { text: '时间', value: 'timestamp' },
              { text: '类型', value: 'type' },
              { text: '状态', value: 'success' },
              { text: '详情', value: 'message' },
              { text: '消息', value: 'details' }
            ]"
            :items="history"
            class="elevation-0"
            hide-default-footer
            density="compact"
            style="max-height: 500px; overflow-y: auto;"
          >
            <template #item.timestamp="{ item }">
              {{ formatTime(item.timestamp) }}
            </template>
            <template #item.success="{ item }">
              <v-chip :color="item.success ? 'success' : 'error'" size="small">
                {{ item.success ? '成功' : '失败' }}
              </v-chip>
            </template>
            <template #item.type="{ item }">
              <v-chip :color="item.type === '备份' ? 'primary' : 'purple'" size="small">{{ item.type }}</v-chip>
            </template>
          </v-data-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="showHistoryDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 备份文件弹窗 -->
    <v-dialog v-model="showBackupFilesDialog" max-width="1400">
      <v-card>
        <v-card-title class="text-h6" style="padding:8px 16px 0 16px;font-size:18px;">备份文件</v-card-title>
        <v-card-text style="padding:0 16px 8px 16px;">
          <v-data-table
            :headers="backupFileHeaders"
            :items="backupFiles"
            item-key="filenameWithSource"
            class="elevation-0"
            hide-default-footer
            density="compact"
            style="margin:0;padding:0;"
          >
            <template #item.filename="{ item }">
              {{ item.filename }}
            </template>
            <template #item.size_mb="{ item }">
              {{ item.size_mb ? item.size_mb.toFixed(2) : '-' }}
            </template>
            <template #item.date="{ item }">
              {{ item.time_str ? item.time_str.split(' ')[0] : '-' }}
            </template>
            <template #item.time="{ item }">
              {{ item.time_str ? (item.time_str.split(' ')[1] || '-') : '-' }}
            </template>
            <template #item.actions="{ item }">
              <div class="d-flex align-center" style="gap: 4px;">
                <v-tooltip v-if="!status.enabled" text="请先启用插件">
                  <template #activator="{ props }">
                    <v-btn icon size="x-small" :disabled="!status.enabled" v-bind="props"><v-icon icon="mdi-download" /></v-btn>
                  </template>
                </v-tooltip>
                <v-btn v-else icon size="x-small" @click="downloadBackup(item)"><v-icon icon="mdi-download" /></v-btn>
                <v-tooltip v-if="!status.enabled || !status.enable_restore" text="请先启用插件并开启恢复功能">
                  <template #activator="{ props }">
                    <v-btn icon size="x-small" color="success" :disabled="!status.enabled || !status.enable_restore" v-bind="props"><v-icon icon="mdi-restore" /></v-btn>
                  </template>
                </v-tooltip>
                <v-btn v-else icon size="x-small" color="success" @click="openRestoreDialog(item)"><v-icon icon="mdi-restore" /></v-btn>
                <v-tooltip v-if="!status.enabled" text="请先启用插件">
                  <template #activator="{ props }">
                    <v-btn icon size="x-small" color="error" :disabled="!status.enabled" v-bind="props"><v-icon icon="mdi-delete" /></v-btn>
                  </template>
                </v-tooltip>
                <v-btn v-else icon size="x-small" color="error" @click="confirmDelete(item)"><v-icon icon="mdi-delete" /></v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" @click="showBackupFilesDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  <!-- 主机操作确认弹窗 -->
  <v-dialog v-model="showHostActionDialog" max-width="400">
    <v-card>
      <v-card-title class="d-flex align-center" :style="`color:${pendingHostAction==='shutdown'?'#d32f2f':'#1976d2'};font-weight:600;`">
        <v-icon :color="pendingHostAction==='shutdown'?'error':'info'" size="32" class="mr-2">
          {{ pendingHostAction==='shutdown' ? 'mdi-power' : 'mdi-restart' }}
        </v-icon>
        {{ pendingHostAction==='shutdown' ? '关机主机' : '重启主机' }}
      </v-card-title>
      <v-card-text>
        <div style="font-size:1.1em;">
          确定要<strong>{{ pendingHostAction==='shutdown' ? '关机' : '重启' }}</strong>当前PVE主机吗？<br/>
          <span v-if="pendingHostAction==='shutdown'" style="color:#d32f2f;">关机后需物理开机或远程唤醒！</span>
          <span v-else style="color:#1976d2;">重启期间主机将短暂不可用。</span>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn text color="grey" @click="showHostActionDialog=false" :disabled="hostActionLoading === pendingHostAction">取消</v-btn>
        <v-btn :color="pendingHostAction==='shutdown'?'error':'info'" :loading="hostActionLoading === pendingHostAction" @click="doHostAction">
          确认{{ pendingHostAction==='shutdown' ? '关机' : '重启' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- 镜像模板管理弹窗 -->
  <v-dialog v-model="showTemplateImagesDialog" max-width="1400">
    <v-card>
      <v-card-title class="text-h6" style="padding:8px 16px 0 16px;font-size:18px;">镜像模板管理</v-card-title>
      <v-card-text style="padding:0 16px 8px 16px;">
        <v-data-table
          :headers="templateImageHeaders.filter(h => h.value !== 'actions')"
          :items="templateImages"
          item-key="filenameWithType"
          class="elevation-0"
          hide-default-footer
          density="compact"
          style="margin:0;padding:0;"
        >
          <template #item.filename="{ item }">
            {{ item.filename }}
          </template>
          <template #item.type="{ item }">
            <v-chip size="x-small" :color="item.type === 'iso' ? 'info' : 'purple'">{{ item.type === 'iso' ? 'ISO镜像' : 'CT模板' }}</v-chip>
          </template>
          <template #item.size_mb="{ item }">
            {{ item.size_mb ? item.size_mb.toFixed(2) : '-' }}
          </template>
          <template #item.date="{ item }">
            {{ item.date || '-' }}
          </template>
        </v-data-table>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn color="primary" class="ml-2" @click="showTemplateImagesDialog = false">关闭</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import axios from 'axios';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
dayjs.extend(duration);
// PVE标签色数组（可根据实际PVE配色调整）
const pveTagColors = [
  '#e573b7', // 粉
  '#bdb76b', // 黄褐
  '#81c784', // 绿
  '#ba68c8', // 紫
  '#ffd54f', // 黄
  '#64b5f6', // 蓝
  '#4db6ac', // 青
  '#f06292', // 粉2
  '#9575cd', // 紫2
  '#90caf9'  // 浅蓝
];
function getPveTagColor(tag) {
  // 简单hash算法，将标签内容hash到颜色数组
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = ((hash << 5) - hash) + tag.charCodeAt(i);
    hash |= 0;
  }
  const idx = Math.abs(hash) % pveTagColors.length;
  return pveTagColors[idx];
}
const props = defineProps({ api: { type: [Object, Function], required: true } });
const emit = defineEmits(['switch', 'close']);

const status = ref({});
const backupFiles = ref([]);
const history = ref([]);
// 轮询定时器引用
const statusPollTimer = ref(null);
const pveStatusPollTimer = ref(null);
const containerStatusPollTimer = ref(null);
const loadingBackup = ref(false);
const loadingRestore = ref(false);
const loadingClear = ref(false);
const loadingStopTasks = ref(false);
const showRestoreDialog = ref(false);
const selectedRestoreFile = ref(null);
const restoreVmid = ref('');
const restoreForce = ref(false);
const restoreSkipExisting = ref(true);
const restoreDisk = ref('');
const snackbar = ref({ show: false, text: '', color: 'success', timeout: 3000 });
const deleteLoading = ref(null);
const showDeleteDialog = ref(false);
const deleteTarget = ref(null);
const showHistoryDialog = ref(false);
const pveStatus = ref({});
const containerStatus = ref([]);
const containerHeaders = [
  { text: 'ID', value: 'vmid' },
  { text: '名称', value: 'displayName' },
  { text: '类型', value: 'type' },
  { text: '状态', value: 'status' },
  { text: '标签', value: 'tags' },
  { text: '运行时间', value: 'uptime' },
  { text: '操作', value: 'actions', sortable: false },
];
const showBackupFilesDialog = ref(false);
const backupFileHeaders = [
  { text: '文件名', value: 'filename' },
  { text: '类型', value: 'source' },
  { text: '大小(MB)', value: 'size_mb' },
  { text: '日期', value: 'date' },
  { text: '时间', value: 'time' },
  { text: '备份路径', value: 'path' },
  { text: '操作', value: 'actions', sortable: false }
];

function showTip(text, color = 'success') {
  snackbar.value.text = text;
  snackbar.value.color = color;
  snackbar.value.show = true;
}

function formatTime(ts) {
  if (!ts) return '-';
  const d = new Date(ts * 1000);
  return d.toLocaleString();
}


async function fetchStatus() {
  try {
    const oldStatusPollInterval = status.value?.status_poll_interval;
    const oldContainerPollInterval = status.value?.container_poll_interval;
    
    status.value = await props.api.get('plugin/ProxmoxVEBackup/status');
    
    // 新增：同步镜像模板开关
    if (status.value && typeof status.value.cleanup_template_images !== 'undefined') {
      cleanupTemplateImagesEnabled.value = !!status.value.cleanup_template_images;
    } else {
      // 兼容老后端
      cleanupTemplateImagesEnabled.value = false;
    }
    
    // 检查轮询间隔是否改变，如果改变则更新定时器
    if (oldStatusPollInterval !== status.value?.status_poll_interval) {
      const newInterval = status.value?.status_poll_interval || 30000;
      console.log(`[轮询配置更新] 状态轮询间隔从 ${oldStatusPollInterval || 30000}ms 更新为 ${newInterval}ms`);
      if (statusPollTimer.value) clearInterval(statusPollTimer.value);
      if (pveStatusPollTimer.value) clearInterval(pveStatusPollTimer.value);
      statusPollTimer.value = setInterval(fetchStatus, newInterval);
      pveStatusPollTimer.value = setInterval(fetchPveStatus, newInterval);
    }
    
    if (oldContainerPollInterval !== status.value?.container_poll_interval) {
      const newInterval = status.value?.container_poll_interval || 30000;
      console.log(`[轮询配置更新] 容器状态轮询间隔从 ${oldContainerPollInterval || 30000}ms 更新为 ${newInterval}ms`);
      if (containerStatusPollTimer.value) clearInterval(containerStatusPollTimer.value);
      containerStatusPollTimer.value = setInterval(fetchContainerStatus, newInterval);
    }
  } catch (e) {
    showTip('获取状态失败: ' + (e?.message || '未知错误'), 'error');
    cleanupTemplateImagesEnabled.value = false;
  }
}

async function fetchHistory() {
  try {
    const [backup, restore] = await Promise.all([
      props.api.get('plugin/ProxmoxVEBackup/backup_history'),
      props.api.get('plugin/ProxmoxVEBackup/restore_history')
    ]);
    // 合并并加类型
    const backupList = Array.isArray(backup) ? backup.map(item => ({ ...item, type: '备份' })) : [];
    const restoreList = Array.isArray(restore) ? restore.map(item => ({ ...item, type: '恢复' })) : [];
    // 合并并按时间倒序
    history.value = [...backupList, ...restoreList].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
  } catch (e) {
    showTip('获取历史记录失败: ' + (e?.message || '未知错误'), 'error');
  }
}

// fetchPveStatus 成功后写入 localStorage
async function fetchPveStatus() {
  try {
    const data = await props.api.get('plugin/ProxmoxVEBackup/pve_status');
    pveStatus.value = data;
    localStorage.setItem('pveStatus', JSON.stringify(data));
  } catch (e) {
    pveStatus.value = { online: false, error: e?.message || '获取失败' };
  }
}

// fetchContainerStatus 成功后写入 localStorage
async function fetchContainerStatus() {
  try {
    const data = await props.api.get('plugin/ProxmoxVEBackup/container_status');
    containerStatus.value = data;
    localStorage.setItem('containerStatus', JSON.stringify(data));
  } catch (e) {
    containerStatus.value = [{ error: e?.message || '获取失败' }];
  }
}

async function runBackup() {
  loadingBackup.value = true;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/run_backup');
    if (res.success) {
      showTip(res.message || '备份任务已启动');
    await fetchStatus();
    await fetchHistory();
    } else {
      showTip(res.message || '备份失败', 'error');
    }
  } catch (e) {
    showTip('备份失败: ' + (e?.message || '未知错误'), 'error');
  }
  loadingBackup.value = false;
}

function openRestoreDialog(file) {
  if (file && file.filename && file.source) selectedRestoreFile.value = file.filename;
  else selectedRestoreFile.value = null;
  if (!restoreDisk.value) restoreDisk.value = 'local';
  showRestoreDialog.value = true;
}

async function runRestore() {
  const fileObj = backupFiles.value.find(f => f.filename === selectedRestoreFile.value);
  if (!fileObj || !fileObj.filename || !fileObj.source) {
    return showTip('请选择备份文件', 'error');
  }
  loadingRestore.value = true;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/restore', {
      filename: fileObj.filename,
      source: fileObj.source,
      restore_vmid: restoreVmid.value,
      restore_force: restoreForce.value,
      restore_skip_existing: restoreSkipExisting.value,
      restore_storage: restoreDisk.value
    });
    if (res.success) {
      showTip(res.message || '恢复任务已启动');
      await fetchStatus();
      await fetchHistory();
    } else {
      showTip(res.message || '恢复失败', 'error');
    }
  } catch (e) {
    showTip('恢复失败: ' + (e?.message || '未知错误'), 'error');
  }
  loadingRestore.value = false;
  showRestoreDialog.value = false;
}

async function clearHistory() {
  loadingClear.value = true;
  try {
    await props.api.post('plugin/ProxmoxVEBackup/clear_history');
    showTip('历史已清理');
    await fetchHistory();
  } catch (e) {
    showTip('清理失败: ' + (e?.message || '未知错误'), 'error');
  }
  loadingClear.value = false;
}

function openBackupFilesDialog() {
  fetchBackupFiles();
  showBackupFilesDialog.value = true;
}

async function fetchBackupFiles() {
  try {
    // 直接请求 available_backups 接口，获取备份文件列表
    const files = await props.api.get('plugin/ProxmoxVEBackup/available_backups');
    if (Array.isArray(files)) {
      backupFiles.value = files.map(f => ({
        ...f,
        filenameWithSource: f.filename + '_' + f.source
      }));
    } else {
      backupFiles.value = [];
    }
  } catch (e) {
    backupFiles.value = [];
  }
}

async function downloadBackup(item) {
  // 获取 apikey（假设登录后已存到 localStorage 或 window 变量）
  const apikey = window.API_TOKEN || localStorage.getItem('api_token') || '';
  const params = new URLSearchParams({ filename: item.filename, source: item.source });
  if (apikey) params.append('apikey', apikey); // 新增 apikey
  const url = '/api/v1/plugin/ProxmoxVEBackup/download_backup?' + params.toString();
  try {
    const res = await axios.get(
      url,
      { responseType: 'blob' }
    );
    // 处理文件名
    let filename = item.filename || 'backup.dat';
    const disposition = res.headers['content-disposition'];
    if (disposition) {
      const match = disposition.match(/filename="?([^";]+)"?/);
      if (match) filename = decodeURIComponent(match[1]);
    }
    // 创建blob下载
    const blobUrl = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  } catch (error) {
    alert('下载失败: ' + (error.message || '未知错误'));
  }
}

function confirmDelete(item) {
  deleteTarget.value = item;
  showDeleteDialog.value = true;
}

async function handleDeleteConfirm() {
  if (!deleteTarget.value) return;
  deleteLoading.value = deleteTarget.value.filename + deleteTarget.value.source;
  try {
    await props.api.post('plugin/ProxmoxVEBackup/delete_backup', {
      filename: deleteTarget.value.filename,
      source: deleteTarget.value.source
    });
    showTip('删除成功');
    await fetchBackupFiles();
  } catch (e) {
    showTip('删除失败: ' + (e?.message || '未知错误'), 'error');
  }
  deleteLoading.value = null;
  showDeleteDialog.value = false;
}


// 3. onMounted 时先从 localStorage 读取缓存
onMounted(async () => {
  // 自动获取API_TOKEN
  try {
    const res = await props.api.get('plugin/ProxmoxVEBackup/token');
    if (res && res.api_token) {
      window.API_TOKEN = res.api_token;
      localStorage.setItem('api_token', res.api_token);
    }
  } catch (e) {
    // console.warn('获取API令牌失败', e);
  }
  // 先读缓存
  try {
    const cachePve = localStorage.getItem('pveStatus');
    if (cachePve) pveStatus.value = JSON.parse(cachePve);
  } catch {}
  try {
    const cacheContainer = localStorage.getItem('containerStatus');
    if (cacheContainer) containerStatus.value = JSON.parse(cacheContainer);
  } catch {}
  // 再异步刷新
  await fetchStatus();
  fetchHistory();
  fetchPveStatus();
  fetchContainerStatus();
  fetchBackupFiles();
  
  // 使用配置的轮询间隔设置定时器
  const statusInterval = status.value?.status_poll_interval || 30000; // 默认30秒
  const containerInterval = status.value?.container_poll_interval || 30000; // 默认30秒
  
  // 调试信息（可在浏览器控制台查看）
  console.log(`[轮询配置] 状态轮询间隔: ${statusInterval}ms (${statusInterval/1000}秒)`);
  console.log(`[轮询配置] 容器状态轮询间隔: ${containerInterval}ms (${containerInterval/1000}秒)`);
  
  // 清除旧的定时器（如果存在）
  if (statusPollTimer.value) clearInterval(statusPollTimer.value);
  if (pveStatusPollTimer.value) clearInterval(pveStatusPollTimer.value);
  if (containerStatusPollTimer.value) clearInterval(containerStatusPollTimer.value);
  
  // 设置新的定时器
  statusPollTimer.value = setInterval(fetchStatus, statusInterval);
  pveStatusPollTimer.value = setInterval(fetchPveStatus, statusInterval); // 使用相同的状态轮询间隔
  containerStatusPollTimer.value = setInterval(fetchContainerStatus, containerInterval);
  
  // 监听配置变化，动态更新轮询间隔
  watch(() => status.value?.status_poll_interval, (newVal) => {
    if (newVal && newVal > 0) {
      if (statusPollTimer.value) clearInterval(statusPollTimer.value);
      if (pveStatusPollTimer.value) clearInterval(pveStatusPollTimer.value);
      statusPollTimer.value = setInterval(fetchStatus, newVal);
      pveStatusPollTimer.value = setInterval(fetchPveStatus, newVal);
    }
  });
  
  watch(() => status.value?.container_poll_interval, (newVal) => {
    if (newVal && newVal > 0) {
      if (containerStatusPollTimer.value) clearInterval(containerStatusPollTimer.value);
      containerStatusPollTimer.value = setInterval(fetchContainerStatus, newVal);
    }
  });
});

async function handleVmAction(item, action) {
  item._actionLoading = action;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/container_action', {
      vmid: item.vmid,
      type: item.type,
      action
    });
    showTip(res.message || (action + '操作完成'), res.success ? 'success' : 'error');
    await fetchContainerStatus();
  } catch (e) {
    showTip('操作失败: ' + (e?.message || '未知错误'), 'error');
  }
  item._actionLoading = null;
}

async function handleVmSnapshot(item) {
  item._actionLoading = 'snapshot';
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/container_snapshot', {
      vmid: item.vmid,
      type: item.type
    });
    showTip(res.message || '快照操作完成', res.success ? 'success' : 'error');
    await fetchContainerStatus();
  } catch (e) {
    showTip('快照失败: ' + (e?.message || '未知错误'), 'error');
  }
  item._actionLoading = null;
}

function formatUptime(uptime) {
  const sec = Number(uptime);
  if (!sec || isNaN(sec) || sec <= 0) return '<span style="color:#888;">未运行</span>';
  if (sec < 60) return '<span style="color:#4caf50;font-weight:600;">刚启动</span>';
  const days = Math.floor(sec / 86400);
  const hours = Math.floor((sec % 86400) / 3600);
  const mins = Math.floor((sec % 3600) / 60);
  let parts = [];
  if (days > 0) parts.push(days + '天');
  if (hours > 0) parts.push(hours + '小时');
  if (mins > 0) parts.push(mins + '分');
  return `<span style="color:#4caf50;font-weight:600;">运行${parts.join('')}</span>`;
}

const isMobile = ref(false);
onMounted(() => {
  const check = () => isMobile.value = window.innerWidth < 600;
  check();
  window.addEventListener('resize', check);
});

// 辅助函数：获取使用率颜色
function getUsageColor(usage) {
  if (usage >= 80) return 'error';
  if (usage >= 50) return 'warning';
  return 'success';
}

// 辅助函数：获取磁盘使用率颜色
function getDiskUsageColor(usage) {
  if (usage >= 90) return 'error';
  if (usage >= 70) return 'warning';
  return 'success';
}

// 辅助函数：获取温度颜色
function getTempColor(temp) {
  if (temp >= 80) return 'error';
  if (temp >= 60) return 'warning';
  return 'success';
}

// 辅助函数：获取温度颜色的实际值（用于内联样式）
function getTempColorValue(temp) {
  if (temp >= 80) return '#f44336'; // 红色 - 高温
  if (temp >= 60) return '#ff9800'; // 橙色 - 警告
  return '#4caf50'; // 绿色 - 正常
}

// 辅助函数：格式化IO延迟
function formatIODelay(delay) {
  if (!delay && delay !== 0) return '-';
  if (delay < 1) return '< 1ms';
  return `${delay.toFixed(1)}ms`;
}

// 辅助函数：获取IO延迟颜色
function getIODelayColor(delay) {
  if (delay >= 50) return 'error'; // 红色 - 严重延迟
  if (delay >= 10) return 'warning'; // 橙色 - 警告
  return 'success'; // 绿色 - 正常
}

// 辅助函数：获取IO延迟进度条值（将毫秒映射到0-100）
function getIODelayProgress(delay) {
  // 将0-100ms映射到0-100%，超过100ms显示为100%
  return Math.min((delay / 100) * 100, 100);
}

const showHostActionDialog = ref(false);
const pendingHostAction = ref(''); // reboot/shutdown
const hostActionLoading = ref('');
const handleHostActionClick = (action) => {
  if (hostActionLoading.value) return;
  pendingHostAction.value = action;
  showHostActionDialog.value = true;
};
const doHostAction = async () => {
  const action = pendingHostAction.value;
  if (!action) return;
  hostActionLoading.value = action;
  try {
    const actionText = action === 'reboot' ? '重启' : '关机';
    const res = await props.api.post('plugin/ProxmoxVEBackup/host_action', { action });
    if (res.success) {
      showTip(res.msg || `${actionText}命令已发送`);
      setTimeout(fetchPveStatus, 2000);
    } else {
      showTip(res.msg || `${actionText}失败`);
    }
  } catch (e) {
    showTip(e.message || '操作失败');
  }
  hostActionLoading.value = '';
  showHostActionDialog.value = false;
  pendingHostAction.value = '';
};

const loadingCleanupLogs = ref(false);
const loadingCleanupTempSpace = ref(false); // 新增临时空间清理loading
async function handleCleanupLogs() {
  if (!status.value.enabled || !status.value.enable_log_cleanup) return;
  loadingCleanupLogs.value = true;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/cleanup_logs');
    let detail = '';
    if (res.result && typeof res.result === 'object') {
      detail = Object.entries(res.result).map(([k, v]) => {
        const [count, err] = v;
        if (err) return `${k}：失败（${err}）`;
        if (count === null || typeof count === 'undefined') return `${k}：已清理`;
        return `${k}：已清理${count}个`;
      }).join('\n');
    }
    showTip((res.msg || '系统日志清理完成') + (detail ? '\n' + detail : ''), res.success ? 'success' : 'error');
  } catch (e) {
    showTip(e?.msg || e?.message || '系统日志清理失败', 'error');
  }
  loadingCleanupLogs.value = false;
}

// 新增：清理临时空间方法
async function handleCleanupTempSpace() {
  if (!status.value.enabled) return;
  if (status.value.backup_activity && status.value.backup_activity !== '空闲') {
    showTip('当前有备份任务进行中，请稍后再清理临时空间', 'warning');
    return;
  }
  loadingCleanupTempSpace.value = true;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/cleanup_tmp');
    let detail = '';
    if (res.result && typeof res.result === 'object') {
      detail = Object.entries(res.result).map(([k, v]) => {
        const [count, err] = v;
        if (err) return `${k}：失败（${err}）`;
        if (count === null || typeof count === 'undefined') return `${k}：已清理`;
        return `${k}：已清理${count}个`;
      }).join('\n');
    }
    showTip((res.msg || '临时空间清理完成') + (detail ? '\n' + detail : ''), res.success ? 'success' : 'error');
  } catch (e) {
    showTip(e?.msg || e?.message || '临时空间清理失败', 'error');
  }
  loadingCleanupTempSpace.value = false;
}

// 新增：停止所有任务方法
async function stopAllTasks() {
  loadingStopTasks.value = true;
  try {
    const res = await props.api.post('plugin/ProxmoxVEBackup/stop_all_tasks');
    showTip(res.msg || '任务已停止', res.success ? 'success' : 'error');
    if (res.success) {
      await fetchStatus(); // 刷新状态
    }
  } catch (e) {
    showTip(e?.msg || e?.message || '停止任务失败', 'error');
  }
  loadingStopTasks.value = false;
}

const cleanupTemplateImagesEnabled = ref(false); // 镜像模板开关联动
const showTemplateImagesDialog = ref(false);
const templateImages = ref([]);
const templateImageHeaders = [
  { text: '文件名', value: 'filename' },
  { text: '类型', value: 'type' },
  { text: '大小(MB)', value: 'size_mb' },
  { text: '日期', value: 'date' }
  // 不再有操作列
];
function openTemplateImagesDialog() {
  fetchTemplateImages();
  showTemplateImagesDialog.value = true;
}
async function fetchTemplateImages() {
  try {
    const files = await props.api.get('plugin/ProxmoxVEBackup/template_images');
    if (Array.isArray(files)) {
      templateImages.value = files.map(f => ({
        ...f,
        filenameWithType: f.filename + '_' + f.type
      }));
    } else {
      templateImages.value = [];
    }
  } catch (e) {
    templateImages.value = [];
  }
}
</script>

<style scoped>
.plugin-page { max-width: 80rem; margin: 0 auto; padding: 0.5rem; }

/* 玻璃拟态卡片样式 - 继承父级主题 */
.glass-card {
  background: transparent;
  border-radius: 18px;
  box-shadow: none;
  backdrop-filter: none;
  border: none;
  margin-bottom: 0;
  padding: 24px 32px 8px 32px;
}
.section-title {
  font-weight: 600;
  font-size: 1.15rem;
  display: flex;
  align-items: center;
  color: #00eaff;
  margin-bottom: 4px;
  letter-spacing: 1px;
  text-shadow: 0 2px 8px #00eaff44;
}
.glow-btn {
  border-radius: 10px;
  font-weight: 500;
  min-width: 90px;
  background: linear-gradient(90deg, #00eaff 0%, #3f51b5 100%);
  color: #fff !important;
  box-shadow: 0 2px 16px 0 #00eaff55;
  transition: box-shadow 0.3s, background 0.3s;
}
.glow-btn:hover {
  box-shadow: 0 4px 32px 0 #00eaffcc;
  background: linear-gradient(90deg, #3f51b5 0%, #00eaff 100%);
}
.tight-switch {
  margin-bottom: -8px;
  margin-top: -8px;
}
.section-title .v-icon {
  filter: drop-shadow(0 0 8px #00eaff88);
}
.footer-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
  margin-bottom: 0 !important;
  padding-bottom: 8px !important;
}
@media (max-width: 600px) {
  .footer-btns {
    flex-direction: column;
    align-items: stretch;
  }
  .mobile-card {
    margin-bottom: 12px;
    padding: 12px;
    border-radius: 10px;
    background: transparent;
    box-shadow: none;
  }
  .mobile-actions {
    margin-top: 8px;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
}
/* .close-btn 样式已集成到内联style，可保留空或加hover效果 */
 .close-btn:hover {
   background: #7c3aed !important;
   box-shadow: 0 4px 16px #a259f7cc;
 }
.glow-btn-blue {
  background: linear-gradient(90deg, #2196f3 0%, #3f51b5 100%) !important;
}
.glow-btn-cyan {
  background: linear-gradient(90deg, #00eaff 0%, #00bcd4 100%) !important;
}
.glow-btn-orange {
  background: linear-gradient(90deg, #ff9800 0%, #ff5722 100%) !important;
}
.glow-btn-purple {
  background: linear-gradient(90deg, #a259f7 0%, #e040fb 100%) !important;
}
.glow-btn-green {
  background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%) !important;
}
.glow-btn-pink {
  background: linear-gradient(90deg, #ff6a88 0%, #ff99ac 100%) !important;
}
.glow-btn-multicolor {
  background: linear-gradient(90deg, #ff6a88 0%, #ffd600 30%, #43e97b 60%, #00eaff 100%) !important;
  color: #fff !important;
  box-shadow: 0 2px 16px 0 #ffd60088, 0 2px 16px 0 #00eaff55;
  border: none;
}
.glow-btn-multicolor:hover {
  box-shadow: 0 4px 32px 0 #ff6a88cc, 0 4px 32px 0 #00eaffcc;
  background: linear-gradient(90deg, #00eaff 0%, #43e97b 30%, #ffd600 60%, #ff6a88 100%) !important;
}
.glow-btn-rainbow {
  background: linear-gradient(90deg, #ff6a88 0%, #ffd600 20%, #43e97b 40%, #38f9d7 60%, #00eaff 80%, #a259f7 100%) !important;
  color: #fff !important;
  box-shadow: 0 2px 16px 0 #ffd60088, 0 2px 16px 0 #00eaff55;
  border: none;
}
.glow-btn-rainbow:hover {
  box-shadow: 0 4px 32px 0 #ff6a88cc, 0 4px 32px 0 #00eaffcc;
  background: linear-gradient(90deg, #a259f7 0%, #00eaff 20%, #38f9d7 40%, #43e97b 60%, #ffd600 80%, #ff6a88 100%) !important;
}

.glow-btn-gold {
  background: linear-gradient(90deg, #ffd700 0%, #ffb300 100%) !important;
  color: #fff !important;
  box-shadow: 0 2px 16px 0 #ffd70088, 0 2px 16px 0 #ffb30055;
  border: none;
}
.glow-btn-gold:hover {
  box-shadow: 0 4px 32px 0 #ffd700cc, 0 4px 32px 0 #ffb300cc;
  background: linear-gradient(90deg, #ffb300 0%, #ffd700 100%) !important;
}
.glow-btn-deep-orange {
  background: linear-gradient(90deg, #ff3d00 0%, #ff7043 100%) !important;
  color: #fff !important;
  box-shadow: 0 2px 16px 0 #ff704388;
  border: none;
}
.glow-btn-deep-orange:hover {
  box-shadow: 0 4px 32px 0 #ff5722cc;
  background: linear-gradient(90deg, #ff7043 0%, #ff3d00 100%) !important;
}
.glow-btn-red {
  background: linear-gradient(90deg, #ff1744 0%, #f44336 100%) !important;
  color: #fff !important;
  box-shadow: 0 2px 16px 0 #ff174488;
  border: none;
}
.glow-btn-red:hover {
  box-shadow: 0 4px 32px 0 #f44336cc;
  background: linear-gradient(90deg, #f44336 0%, #ff1744 100%) !important;
}

/* ========== 全新现代化状态页样式 ========== */

/* 统一的主容器 */
.status-page-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 0;
}

/* 统一的行布局 */
.status-main-row {
  margin: 0 !important;
  gap: 16px;
}

.status-col {
  padding: 0 !important;
  height: 100%;
}

.status-col > .modern-status-card {
  display: flex;
  flex-direction: column;
}

.status-col > .modern-status-card > .card-body-modern {
  display: flex;
  flex-direction: column;
}


/* 现代化状态卡片 - 统一样式，完全继承父级主题 */
.modern-status-card {
  border-radius: 16px;
  background: transparent;
  border: 1px solid;
  border-color: inherit;
  backdrop-filter: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-shadow: none;
}

.modern-status-card:hover {
  transform: translateY(-2px);
  border-color: inherit;
}

.card-header-modern {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: transparent;
  border-bottom: 1px solid;
  border-color: inherit;
  flex-wrap: wrap;
  gap: 16px;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.card-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
}

.card-icon-primary { background: transparent; }
.card-icon-success { background: transparent; }
.card-icon-info { background: transparent; }

.card-title-modern {
  font-size: 1.1rem;
  font-weight: 600;
  color: inherit;
  line-height: 1.4;
}

.card-subtitle-modern {
  font-size: 0.75rem;
  color: inherit;
  opacity: 0.6;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-body-modern {
  padding: 16px 20px;
}

/* 确保容器状态卡片内容区域也能自适应 */
.status-col:last-child .modern-status-card .card-body-modern {
  display: flex;
  flex-direction: column;
}

/* 优化容器状态表格行高 */
.card-body-modern :deep(.v-data-table__tbody tr) {
  height: auto !important;
}

.card-body-modern :deep(.v-data-table__tbody td) {
  padding: 6px 16px !important;
  height: auto !important;
}

.card-body-modern :deep(.v-data-table__thead th) {
  padding: 10px 16px !important;
  height: auto !important;
  font-size: 0.813rem !important;
}

.card-body-modern :deep(.v-btn) {
  min-height: 28px !important;
  height: auto !important;
}

/* 状态项样式 */
.status-item-modern {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid;
  border-color: inherit;
  gap: 12px;
}

.status-item-modern:last-child {
  border-bottom: none;
}

.status-item-header {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  min-width: 80px;
}

.status-label {
  font-size: 0.875rem;
  color: inherit;
  opacity: 0.7;
  font-weight: 500;
}

.status-text {
  font-size: 0.875rem;
  color: inherit;
  font-weight: 500;
  flex: 1;
  min-width: 0;
  word-break: break-word;
  text-align: left;
}

.status-text-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.status-text-separator {
  font-size: 0.875rem;
  color: inherit;
  opacity: 0.4;
  margin: 0 4px;
}

.status-text-with-icon {
  display: inline-flex;
  align-items: center;
  font-size: 0.875rem;
  color: inherit;
  font-weight: 500;
}

.status-text.highlight {
  color: inherit;
  opacity: 1;
  font-weight: 600;
}

.status-badge {
  font-weight: 600;
}

/* 资源信息样式 */
.resource-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.resource-text {
  font-size: 0.75rem;
  color: inherit;
  opacity: 0.6;
}

.resource-text-compact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.813rem;
  color: inherit;
  opacity: 0.8;
}

.resource-model {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.resource-temp-inline {
  display: flex;
  align-items: center;
  font-size: 0.813rem;
  white-space: nowrap;
  flex-shrink: 0;
  font-weight: 600;
}

.resource-temp-inline span {
  font-weight: 600;
  margin-left: 2px;
}

.resource-progress-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.resource-progress {
  flex: 1;
  min-width: 0;
  max-width: none;
}

.resource-percent {
  font-size: 0.813rem;
  font-weight: 600;
  color: inherit;
  min-width: 45px;
  text-align: right;
  flex-shrink: 0;
}

.temp-chip {
  font-weight: 600;
}

/* PVE信息网格布局 - 充分利用全宽空间 */
.pve-info-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.pve-info-right {
  display: flex;
  flex-direction: column;
  width: 100%;
}

@media (max-width: 960px) {
  .pve-info-grid {
    gap: 0;
  }
}

/* 离线状态 */
.offline-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.offline-text {
  font-size: 1rem;
  font-weight: 600;
  color: #f44336;
  margin-bottom: 8px;
}

.offline-error {
  color: rgba(255, 255, 255, 0.5);
}

/* 现代化操作按钮 */
.modern-action-btn {
  width: 36px !important;
  height: 36px !important;
  min-width: 36px !important;
  border-radius: 8px !important;
  transition: all 0.3s;
}

.health-btn {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%) !important;
  color: #fff !important;
}

.refresh-btn {
  background: linear-gradient(135deg, #00eaff 0%, #00bcd4 100%) !important;
  color: #fff !important;
}

.reboot-btn {
  background: linear-gradient(135deg, #2196f3 0%, #64b5f6 100%) !important;
  color: #fff !important;
}

.shutdown-btn {
  background: linear-gradient(135deg, #f44336 0%, #ff7043 100%) !important;
  color: #fff !important;
}

.modern-action-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

/* PVE头部信息 */
.pve-header-info {
  display: flex;
  align-items: center;
  gap: 20px;
  flex: 1;
  margin: 0 20px;
  flex-wrap: wrap;
}

.pve-header-info-item {
  display: flex;
  align-items: center;
  white-space: nowrap;
  font-size: 0.813rem;
}

.pve-header-label {
  color: inherit;
  opacity: 0.7;
  margin: 0 4px;
  font-weight: 500;
}

.pve-header-value {
  color: inherit;
  font-weight: 500;
  margin-left: 2px;
}

.host-action-btns-modern {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

/* 容器头部统计信息 - 紧凑横向布局 */
.container-header-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  margin: 0 24px;
  flex-wrap: nowrap;
  overflow-x: auto;
}

.header-summary-item {
  display: flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 6px;
  background: transparent;
  transition: all 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.header-summary-item:hover {
  background: transparent;
  opacity: 0.8;
}

.header-summary-label {
  font-size: 0.75rem;
  color: inherit;
  opacity: 0.7;
  margin-right: 4px;
  white-space: nowrap;
}

.header-summary-value {
  font-size: 0.813rem;
  font-weight: 600;
  color: inherit;
  white-space: nowrap;
}

/* 容器统计信息现代化 - 继承父级主题（已移至头部，保留以防其他地方使用） */
.container-summary-modern {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  padding: 16px;
  background: transparent;
  border-radius: 12px;
  border: 1px solid;
  border-color: inherit;
  margin-bottom: 20px;
}

.summary-item-modern {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  background: transparent;
  border-radius: 8px;
  transition: all 0.3s;
}

.summary-item-modern:hover {
  background: transparent;
  transform: translateY(-1px);
}

.summary-label-modern {
  font-size: 0.875rem;
  color: inherit;
  opacity: 0.7;
  margin-right: 8px;
  white-space: nowrap;
}

.summary-value-modern {
  font-size: 0.875rem;
  font-weight: 600;
  color: inherit;
  margin-left: auto;
  white-space: nowrap;
}
/* 移动端响应式 */
@media (max-width: 960px) {
  .status-main-row {
    gap: 16px !important;
  }

  .status-col {
    margin-bottom: 16px;
  }

  .modern-status-card {
    min-height: auto;
  }

  .container-header-summary {
    margin: 0 16px;
    gap: 12px;
  }

  .header-summary-item {
    padding: 4px 8px;
  }

  .header-summary-label {
    font-size: 0.7rem;
  }
}

@media (max-width: 600px) {
  .status-page-container {
    gap: 16px;
  }

  .container-summary-modern {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .container-header-summary {
    margin: 12px 0 0 0;
    gap: 12px;
    width: 100%;
    flex-wrap: wrap;
  }

  .header-summary-item {
    padding: 4px 10px;
    font-size: 0.75rem;
  }

  .card-header-modern {
    flex-wrap: wrap;
    padding: 16px;
    gap: 12px;
  }

  .card-header-left {
    width: 100%;
    margin-bottom: 0;
  }

  .pve-header-info {
    width: 100%;
    margin: 0;
    gap: 12px;
    justify-content: flex-start;
  }

  .pve-header-info-item {
    font-size: 0.75rem;
  }

  .host-action-btns-modern {
    width: 100%;
    justify-content: flex-start;
    margin-top: 4px;
  }
}

/* 标题行布局 */
.header-title-row {
  position: relative;
}

/* 缓存提示文字样式 */
.cache-notice-text {
  font-size: 0.9rem;
  color: #fb8c00;
  opacity: 1;
  font-weight: 500;
  white-space: nowrap;
  margin: 0 12px;
  flex-shrink: 1;
  min-width: 0;
}

@media (max-width: 960px) {
  .cache-notice-text {
    display: none; /* 移动端隐藏提示文字，节省空间 */
  }
  
  .header-title-row {
    justify-content: space-between;
  }
}
</style>
