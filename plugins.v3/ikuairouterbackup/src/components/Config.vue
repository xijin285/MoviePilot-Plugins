<template>
  <div class="ikuai-cfg-page">
    <!-- 顶栏 -->
    <div class="ikuai-cfg-topbar">
      <div class="ikuai-cfg-topbar__left">
        <div class="ikuai-cfg-topbar__icon">
          <v-icon icon="mdi-router-network" size="24" />
        </div>
        <div class="ikuai-cfg-topbar__meta">
          <div class="ikuai-cfg-topbar__title">爱快时光机 · 配置</div>
          <div class="ikuai-cfg-topbar__sub">备份恢复 · 实时监控 · 负载告警</div>
        </div>
      </div>
      <div class="ikuai-cfg-topbar__right">
        <v-btn-group variant="tonal" density="compact" class="elevation-0">
          <v-btn color="primary" @click="emit('switch')" size="small" min-width="40" class="px-0 px-sm-3">
            <v-icon icon="mdi-view-dashboard" size="18" class="mr-sm-1" />
            <span class="d-none d-sm-inline">状态页</span>
          </v-btn>
          <v-btn color="primary" :loading="saving" @click="save" size="small" min-width="40" class="px-0 px-sm-3">
            <v-icon icon="mdi-content-save" size="18" class="mr-sm-1" />
            <span class="d-none d-sm-inline">保存</span>
          </v-btn>
          <v-btn color="primary" @click="emit('close')" size="small" min-width="40" class="px-0 px-sm-3">
            <v-icon icon="mdi-close" size="18" />
            <span class="d-none d-sm-inline">关闭</span>
          </v-btn>
        </v-btn-group>
      </div>
    </div>

    <!-- Toast -->
    <Transition name="ikuai-cfg-slide">
      <div v-if="message.show" class="ikuai-cfg-toast" :class="`ikuai-cfg-toast--${message.type}`">
        <v-icon :icon="message.type === 'success' ? 'mdi-check-circle' : 'mdi-alert-circle'" size="18" />
        <span>{{ message.text }}</span>
      </div>
    </Transition>

    <!-- 基本设置（含爱快连接） -->
    <div class="ikuai-cfg-card">
      <div class="ikuai-cfg-card__header ikuai-cfg-card__header--toggle" @click="collapsed.basic = !collapsed.basic">
        <span class="ikuai-cfg-card__title d-flex align-center">
          <v-icon icon="mdi-cog-outline" size="18" color="#8b5cf6" class="mr-1" />
          基本设置
        </span>
        <span class="d-flex align-center ga-2">
          <v-btn variant="tonal" color="primary" size="small" prepend-icon="mdi-speedometer" :loading="testing" @click.stop="runTest">
            测试连接
          </v-btn>
          <v-icon icon="mdi-chevron-down" size="20" class="ikuai-cfg-card__chevron" :class="{ 'ikuai-cfg-card__chevron--open': !collapsed.basic }" />
        </span>
      </div>
      <div v-show="!collapsed.basic" class="ikuai-cfg-card__body">
      <div class="ikuai-cfg-switch-grid">
        <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.enabled }" style="--accent: #22c55e">
          <div class="ikuai-cfg-switch-item__main">
            <v-icon icon="mdi-power" size="18" />
            <span>启用插件</span>
          </div>
          <v-switch v-model="config.enabled" color="#22c55e" density="compact" hide-details inset />
        </div>
        <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': !!config.notify }" style="--accent: #f59e0b">
          <div class="ikuai-cfg-switch-item__main">
            <v-icon icon="mdi-bell-outline" size="18" />
            <span>消息通知</span>
          </div>
          <v-switch :model-value="!!config.notify" @update:model-value="config.notify = $event ? 1 : 0" color="#f59e0b" density="compact" hide-details inset />
        </div>
      </div>
      <div class="ikuai-cfg-form-grid">
        <div class="ikuai-cfg-form-item">
          <v-text-field v-model="config.cron" label="定时备份（cron 表达式）" placeholder="0 3 * * *" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          <div class="ikuai-cfg-hint">五位 cron，如 0 3 * * * 表示每天凌晨 3 点备份</div>
        </div>
        <div class="ikuai-cfg-form-item">
          <v-text-field v-model.number="config.retry_count" type="number" min="0" max="10" label="重试次数" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
        </div>
        <div class="ikuai-cfg-form-item">
          <v-text-field v-model.number="config.retry_interval" type="number" min="10" label="重试间隔（秒）" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
        </div>
        <div class="ikuai-cfg-form-item">
          <v-text-field v-model="config.ikuai_url" label="路由器地址" placeholder="https://192.168.9.1" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          <div class="ikuai-cfg-hint">爱快管理后台地址，如 https://192.168.9.1</div>
        </div>
        <div class="ikuai-cfg-form-item">
          <v-text-field v-model="config.ikuai_username" label="用户名" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
        </div>
        <div class="ikuai-cfg-form-item">
          <v-text-field v-model="config.ikuai_password" label="密码（留空保持不变）" type="password" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
        </div>
        <div class="ikuai-cfg-form-item">
          <v-select v-model="config.ikuai_auth_mode" :items="authModes" label="认证方式" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
        </div>
        <div class="ikuai-cfg-form-item">
          <v-text-field v-model="config.ikuai_api_token" label="爱快4.x 个人 API 令牌（可选）" type="password" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          <div class="ikuai-cfg-hint">高级设置 → 系统设置 → API Token 生成；令牌模式下设备 / 日志 / 备份控制面走 REST</div>
        </div>
      </div>
      <div v-if="testResult" class="ikuai-cfg-hint" :style="{ color: testResult.ok ? '#22c55e' : '#ef4444' }">
        <v-icon :icon="testResult.ok ? 'mdi-check-circle' : 'mdi-alert-circle-outline'" size="14" class="mr-1" />
        <template v-if="testResult.ok">
          ✓ {{ testResult.hostname || 'iKuai' }} {{ testResult.version || '' }}
          · 认证：{{ testResult.auth_mode }}
          <template v-if="testResult.auth_mode !== 'password'">· 令牌{{ testResult.token_ok ? '有效' : '无效' }}</template>
        </template>
        <template v-else>✗ {{ testResult.error }}</template>
      </div>
      </div>
    </div>

    <!-- 备份设置 -->
    <div class="ikuai-cfg-card">
      <div class="ikuai-cfg-card__header ikuai-cfg-card__header--toggle" @click="collapsed.backup = !collapsed.backup">
        <span class="ikuai-cfg-card__title d-flex align-center">
          <v-icon icon="mdi-content-save-check" size="18" color="#22c55e" class="mr-1" />
          备份目标
        </span>
        <span class="d-flex align-center ga-2">
          <v-chip size="x-small" variant="tonal" :color="anyTarget ? 'success' : 'warning'">
            {{ anyTarget ? '已启用 ' + activeTargets + ' 个目标' : '未启用任何目标' }}
          </v-chip>
          <v-icon icon="mdi-chevron-down" size="20" class="ikuai-cfg-card__chevron" :class="{ 'ikuai-cfg-card__chevron--open': !collapsed.backup }" />
        </span>
      </div>

      <div v-show="!collapsed.backup" class="ikuai-cfg-card__body">
      <!-- 存储备份（本地磁盘 + MP 网盘存储，可多目标同时备份） -->
      <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.storage_backup_enable }" style="--accent: #22c55e">
        <div class="ikuai-cfg-switch-item__main">
          <v-icon icon="mdi-database-outline" size="18" />
          <span>存储备份（MoviePilot 存储）</span>
        </div>
        <v-switch v-model="config.storage_backup_enable" color="#22c55e" density="compact" hide-details inset />
      </div>
      <div v-if="config.storage_backup_enable" class="ikuai-cfg-subblock">
        <div v-for="(t, idx) in config.storage_targets" :key="'target-' + idx" class="ikuai-cfg-target-row">
          <div class="ikuai-cfg-target-row__fields">
            <div class="ikuai-cfg-form-item">
              <v-select v-model="t.type" :items="storageOptions" label="选择存储" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input"
                no-data-text="未找到可用存储" />
              <div class="ikuai-cfg-hint">本地磁盘或 MP「设置 → 存储与应用」中配置的存储</div>
            </div>
            <div class="ikuai-cfg-form-item">
              <v-text-field v-model="t.path" :label="isLocalTarget(t) ? '备份路径（留空使用插件数据目录）' : '远端目录'" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input">
                <template #append-inner>
                  <v-icon icon="mdi-folder-open-outline" size="18" color="primary" style="cursor: pointer" title="浏览目录"
                    @click="openDirPicker(idx)" />
                </template>
              </v-text-field>
              <div v-if="isLocalTarget(t)" class="ikuai-cfg-hint">选择 MP 服务器上的本地目录</div>
              <div v-else class="ikuai-cfg-hint">网盘上的备份目录，可点击文件夹图标浏览选择</div>
            </div>
            <div class="ikuai-cfg-form-item">
              <v-text-field v-model.number="t.keep_backup_num" type="number" min="1" label="保留份数" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
              <div class="ikuai-cfg-hint">超出数量的旧备份自动清理</div>
            </div>
          </div>
          <v-btn icon="mdi-trash-can-outline" variant="text" color="error" size="small"
            :disabled="config.storage_targets.length <= 1" title="删除该目标"
            @click="removeTarget(idx)" />
        </div>
        <div class="d-flex align-center flex-wrap ga-2">
          <v-btn size="small" variant="tonal" color="primary" prepend-icon="mdi-plus" @click="addTarget">
            添加备份目标
          </v-btn>
          <span class="ikuai-cfg-hint">可同时添加本地磁盘与多个网盘存储，备份时同时保存到所有目标</span>
        </div>
        <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.delete_after_backup }" style="--accent: #f59e0b">
          <div class="ikuai-cfg-switch-item__main">
            <v-icon icon="mdi-delete-sweep-outline" size="18" />
            <span>备份后删除路由器上的备份文件</span>
          </div>
          <v-switch v-model="config.delete_after_backup" color="#f59e0b" density="compact" hide-details inset />
        </div>
      </div>

      <!-- WebDAV 备份 -->
      <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.enable_webdav }" style="--accent: #3b82f6">
        <div class="ikuai-cfg-switch-item__main">
          <v-icon icon="mdi-cloud-upload-outline" size="18" />
          <span>WebDAV 远程备份</span>
        </div>
        <v-switch v-model="config.enable_webdav" color="#3b82f6" density="compact" hide-details inset />
      </div>
      <div v-if="config.enable_webdav" class="ikuai-cfg-subblock">
        <div class="ikuai-cfg-form-grid">
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model="config.webdav_url" label="WebDAV 地址" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          </div>
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model="config.webdav_username" label="用户名" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          </div>
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model="config.webdav_password" label="密码（留空保持不变）" type="password" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          </div>
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model="config.webdav_path" label="远端目录" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          </div>
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model.number="config.webdav_keep_backup_num" type="number" min="1" label="保留份数" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          </div>
        </div>
      </div>

      <!-- 备份增强 -->
      <v-divider class="my-1" />
      <div class="ikuai-cfg-switch-grid">
        <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.skip_unchanged_backup }" style="--accent: #4f8cff">
          <div class="ikuai-cfg-switch-item__main">
            <v-icon icon="mdi-file-compare" size="18" />
            <span>配置无变化时跳过保存</span>
          </div>
          <v-switch v-model="config.skip_unchanged_backup" color="#4f8cff" density="compact" hide-details inset />
        </div>
        <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.restore_point_enable }" style="--accent: #f59e0b">
          <div class="ikuai-cfg-switch-item__main">
            <v-icon icon="mdi-backup-restore" size="18" />
            <span>恢复前自动创建恢复点</span>
          </div>
          <v-switch v-model="config.restore_point_enable" color="#f59e0b" density="compact" hide-details inset />
        </div>
      </div>
      <div class="ikuai-cfg-hint">
        <v-icon icon="mdi-information-outline" size="14" class="mr-1" />
        备份内容哈希对比，无变化自动跳过；恢复点会在每次恢复前把当前配置备份到本地，防止恢复失败无法回退。
      </div>
      </div>
    </div>

    <!-- 恢复设置 -->
    <div class="ikuai-cfg-card">
      <div class="ikuai-cfg-card__header ikuai-cfg-card__header--toggle" @click="collapsed.restore = !collapsed.restore">
        <span class="ikuai-cfg-card__title d-flex align-center">
          <v-icon icon="mdi-restore" size="18" color="#ef4444" class="mr-1" />
          恢复设置
        </span>
        <v-icon icon="mdi-chevron-down" size="20" class="ikuai-cfg-card__chevron" :class="{ 'ikuai-cfg-card__chevron--open': !collapsed.restore }" />
      </div>
      <div v-show="!collapsed.restore" class="ikuai-cfg-card__body">
      <div class="ikuai-cfg-switch-grid">
        <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.enable_restore }" style="--accent: #ef4444">
          <div class="ikuai-cfg-switch-item__main">
            <v-icon icon="mdi-playlist-remove" size="18" />
            <span>启用恢复功能</span>
          </div>
          <v-switch v-model="config.enable_restore" color="#ef4444" density="compact" hide-details inset />
        </div>
        <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.restore_force }" style="--accent: #ef4444">
          <div class="ikuai-cfg-switch-item__main">
            <v-icon icon="mdi-alert-octagon-outline" size="18" />
            <span>强制恢复（覆盖现有配置）</span>
          </div>
          <v-switch v-model="config.restore_force" color="#ef4444" density="compact" hide-details inset :disabled="!config.enable_restore" />
        </div>
      </div>
      <div class="ikuai-cfg-hint">
        <v-icon icon="mdi-information-outline" size="14" class="mr-1" />
        恢复操作请在左侧导航「爱快路由」仪表盘的备份管理中选择备份文件执行。
      </div>
      </div>
    </div>

    <!-- 监控与告警 -->
    <div class="ikuai-cfg-card">
      <div class="ikuai-cfg-card__header ikuai-cfg-card__header--toggle" @click="collapsed.monitor = !collapsed.monitor">
        <span class="ikuai-cfg-card__title d-flex align-center">
          <v-icon icon="mdi-monitor-dashboard" size="18" color="#3b82f6" class="mr-1" />
          监控与告警
        </span>
        <v-icon icon="mdi-chevron-down" size="20" class="ikuai-cfg-card__chevron" :class="{ 'ikuai-cfg-card__chevron--open': !collapsed.monitor }" />
      </div>
      <div v-show="!collapsed.monitor" class="ikuai-cfg-card__body">
      <div class="ikuai-cfg-switch-grid">
        <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.monitor_enable }" style="--accent: #3b82f6">
          <div class="ikuai-cfg-switch-item__main">
            <v-icon icon="mdi-view-dashboard-outline" size="18" />
            <span>监控仪表盘（侧边栏「爱快路由」入口）</span>
          </div>
          <v-switch v-model="config.monitor_enable" color="#3b82f6" density="compact" hide-details inset />
        </div>
        <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.load_warn_enable }" style="--accent: #f59e0b">
          <div class="ikuai-cfg-switch-item__main">
            <v-icon icon="mdi-bell-alert-outline" size="18" />
            <span>负载超限告警（推送 MP 消息）</span>
          </div>
          <v-switch v-model="config.load_warn_enable" color="#f59e0b" density="compact" hide-details inset />
        </div>
      </div>
      <div v-if="config.load_warn_enable" class="ikuai-cfg-subblock">
        <div class="ikuai-cfg-form-grid ikuai-cfg-form-grid--four">
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model.number="config.load_cpu_threshold" type="number" min="50" max="100" label="CPU 阈值 %" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          </div>
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model.number="config.load_mem_threshold" type="number" min="50" max="100" label="内存阈值 %" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          </div>
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model.number="config.load_warn_times" type="number" min="1" max="36" label="连续超限次数" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
            <div class="ikuai-cfg-hint">连续 N 次采样超阈值才告警</div>
          </div>
        </div>
      </div>
      <div class="ikuai-cfg-hint">
        <v-icon icon="mdi-information-outline" size="14" class="mr-1" />
        每 5 分钟采样一次负载 / 流量用于仪表盘趋势图；告警恢复后自动复位。
      </div>
      </div>
    </div>

    <!-- IP 分组同步 -->
    <div class="ikuai-cfg-card">
      <div class="ikuai-cfg-card__header ikuai-cfg-card__header--toggle" @click="collapsed.ipgroup = !collapsed.ipgroup">
        <span class="ikuai-cfg-card__title d-flex align-center">
          <v-icon icon="mdi-ip-network" size="18" color="#22c55e" class="mr-1" />
          IP 分组同步
        </span>
        <v-icon icon="mdi-chevron-down" size="20" class="ikuai-cfg-card__chevron" :class="{ 'ikuai-cfg-card__chevron--open': !collapsed.ipgroup }" />
      </div>
      <div v-show="!collapsed.ipgroup" class="ikuai-cfg-card__body">
      <div class="ikuai-cfg-switch-grid">
        <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.enable_ip_group }" style="--accent: #22c55e">
          <div class="ikuai-cfg-switch-item__main">
            <v-icon icon="mdi-vector-line" size="18" />
            <span>启用 IP 分组</span>
          </div>
          <v-switch v-model="config.enable_ip_group" color="#22c55e" density="compact" hide-details inset />
        </div>
        <div class="ikuai-cfg-switch-item" :class="{ 'ikuai-cfg-switch-item--active': config.ip_group_address_pool }" style="--accent: #3b82f6">
          <div class="ikuai-cfg-switch-item__main">
            <v-icon icon="mdi-link-variant" size="18" />
            <span>绑定地址池</span>
          </div>
          <v-switch v-model="config.ip_group_address_pool" color="#3b82f6" density="compact" hide-details inset :disabled="!config.enable_ip_group" />
        </div>
      </div>
      <div v-if="config.enable_ip_group" class="ikuai-cfg-subblock">
        <div class="ikuai-cfg-form-grid ikuai-cfg-form-grid--four">
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model="config.ip_group_province" label="省份（如 广东）" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          </div>
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model="config.ip_group_city" label="城市（如 深圳）" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          </div>
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model="config.ip_group_isp" label="运营商（电信/联通/移动）" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          </div>
          <div class="ikuai-cfg-form-item">
            <v-text-field v-model="config.ip_group_prefix" label="分组名前缀（可空）" density="compact" variant="outlined" hide-details="auto" class="ikuai-cfg-input" />
          </div>
        </div>
      </div>
      <div class="ikuai-cfg-hint">
        <v-icon icon="mdi-information-outline" size="14" class="mr-1" />
        按省份 / 城市 / 运营商筛选 IP 段并自动同步到爱快创建 IP 分组，可在流控、分流、防火墙中使用。
      </div>
      </div>
    </div>

    <!-- 目录选择器 -->
    <v-dialog v-model="dirPicker.show" max-width="440" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon icon="mdi-folder-open-outline" size="20" color="primary" class="mr-2" />
          {{ pickerIsLocal() ? '选择本地目录' : '选择网盘目录' }}
        </v-card-title>
        <v-card-text>
          <v-text-field v-model="dirPicker.input" label="当前路径" density="compact" variant="outlined" hide-details
            append-inner-icon="mdi-arrow-right" @click:append-inner="browseTo(dirPicker.input)"
            @keyup.enter="browseTo(dirPicker.input)" class="mb-2" />
          <div class="dir-list">
            <div v-if="dirPicker.parent" class="dir-row" @click="browseTo(dirPicker.parent)">
              <v-icon size="18" class="mr-2">mdi-arrow-up</v-icon>
              <span>返回上级</span>
            </div>
            <div v-for="d in dirPicker.dirs" :key="d" class="dir-row" @click="browseTo(dirJoin(d))">
              <v-icon size="18" color="primary" class="mr-2">mdi-folder</v-icon>
              <span>{{ d }}</span>
            </div>
            <div v-if="dirPicker.loading" class="text-caption text-medium-emphasis pa-2">加载中...</div>
            <div v-else-if="!dirPicker.dirs.length" class="text-caption text-medium-emphasis pa-2">无子目录</div>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dirPicker.show = false">取消</v-btn>
          <v-btn color="primary" variant="tonal" :disabled="!dirPicker.path" @click="chooseCurrent">选择当前目录</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

const props = defineProps({
  initialConfig: { type: Object, default: () => ({}) },
  api: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['close', 'switch'])

const PLUGIN_ID = 'IkuaiRouterBackup'

const config = reactive({
  enabled: false,
  cron: '0 3 * * *',
  notify: false,
  notification_style: 0,
  retry_count: 3,
  retry_interval: 60,
  ikuai_url: '',
  ikuai_username: 'admin',
  ikuai_password: '',
  ikuai_auth_mode: 'auto',
  ikuai_api_token: '',
  storage_backup_enable: true,
  storage_type: 'local',
  storage_path: '',
  storage_keep_backup_num: 7,
  storage_targets: [],
  delete_after_backup: false,
  enable_webdav: false,
  webdav_url: '',
  webdav_username: '',
  webdav_password: '',
  webdav_path: '',
  webdav_keep_backup_num: 7,
  skip_unchanged_backup: true,
  restore_point_enable: true,
  enable_restore: false,
  restore_force: false,
  monitor_enable: true,
  load_warn_enable: false,
  load_cpu_threshold: 90,
  load_mem_threshold: 90,
  load_warn_times: 3,
  enable_ip_group: false,
  ip_group_province: '',
  ip_group_city: '',
  ip_group_isp: '',
  ip_group_prefix: '',
  ip_group_address_pool: false,
  mp_storages: [],
  ...props.initialConfig,
})

const authModes = [
  { title: '自动识别（推荐）', value: 'auto' },
  { title: '账号密码（v3 会话）', value: 'password' },
  { title: 'API 令牌（4.x REST）', value: 'token' },
]

const isLocalTarget = (t) => !t || !t.type || t.type === 'local'

const storageOptions = computed(() => [
  { title: '本地磁盘', value: 'local' },
  ...(config.mp_storages || [])
    .filter((s) => s.type !== 'local')
    .map((s) => ({ title: s.name ? `${s.name} (${s.type})` : s.type, value: s.type })),
])

// 保证目标列表至少一行（旧配置/首次加载时从单字段迁移）
const ensureTargets = () => {
  if (!Array.isArray(config.storage_targets) || !config.storage_targets.length) {
    config.storage_targets = [{
      type: config.storage_type || 'local',
      path: config.storage_path || '',
      keep_backup_num: Number(config.storage_keep_backup_num) || 7,
    }]
  }
}

const addTarget = () => {
  ensureTargets()
  config.storage_targets.push({ type: 'local', path: '', keep_backup_num: 7 })
}

const removeTarget = (idx) => {
  if (config.storage_targets.length <= 1) return
  config.storage_targets.splice(idx, 1)
}

const anyTarget = computed(() =>
  !!(config.storage_backup_enable || config.enable_webdav),
)
const activeTargets = computed(() =>
  [config.storage_backup_enable ? (config.storage_targets || []).length : 0, config.enable_webdav]
    .reduce((sum, v) => sum + (typeof v === 'number' ? v : v ? 1 : 0), 0),
)

const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)
const message = reactive({ show: false, type: 'success', text: '' })
let messageTimer = null

// 分区折叠状态（恢复设置/监控与告警/IP 分组同步默认收起）
const collapsed = reactive({ basic: false, backup: false, restore: true, monitor: true, ipgroup: true })

const showMessage = (text, type = 'success') => {
  message.text = text
  message.type = type
  message.show = true
  if (messageTimer) clearTimeout(messageTimer)
  messageTimer = setTimeout(() => (message.show = false), type === 'error' ? 6000 : 3500)
}

const runTest = async () => {
  testing.value = true
  testResult.value = null
  try {
    const data = await props.api.post(`plugin/${PLUGIN_ID}/test`, {
      ikuai_url: config.ikuai_url,
      ikuai_username: config.ikuai_username,
      ikuai_password: config.ikuai_password,
      ikuai_auth_mode: config.ikuai_auth_mode,
      ikuai_api_token: config.ikuai_api_token,
    })
    testResult.value = data || { ok: false, error: '无响应' }
  } catch (e) {
    testResult.value = { ok: false, error: e?.response?.data?.detail || '测试请求失败' }
  } finally {
    testing.value = false
  }
}

const save = async () => {
  if (config.enabled && !String(config.ikuai_url || '').trim()) {
    showMessage('启用插件前请先填写爱快路由器地址', 'error')
    return
  }
  saving.value = true
  try {
    const result = await props.api.post(`plugin/${PLUGIN_ID}/config`, { ...config })
    if (result?.success === false) {
      showMessage(result?.msg || '保存失败', 'error')
    } else {
      showMessage(result?.msg || '配置保存成功', 'success')
      loadConfig()
    }
  } catch (e) {
    showMessage(e?.response?.data?.detail || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

const loadConfig = async () => {
  try {
    const data = await props.api.get(`plugin/${PLUGIN_ID}/config`)
    if (data) {
      // 不覆盖正在输入的密码字段
      const pwd = config.ikuai_password
      const wdavPwd = config.webdav_password
      Object.assign(config, data)
      config.ikuai_password = pwd
      config.webdav_password = wdavPwd
      ensureTargets()
    }
  } catch (e) { /* 静默 */ }
}

// ============ 目录选择器 ============
const dirPicker = reactive({ show: false, path: '', input: '', parent: '', dirs: [], loading: false, targetIdx: 0 })

// 当前浏览的目标是否本地存储
const pickerIsLocal = () => {
  const t = (config.storage_targets || [])[dirPicker.targetIdx] || {}
  return isLocalTarget(t)
}

const pickerStorage = () => {
  const t = (config.storage_targets || [])[dirPicker.targetIdx] || {}
  return isLocalTarget(t) ? '' : t.type
}

const browseDir = async (path) => {
  dirPicker.loading = true
  try {
    const data = await props.api.get(`plugin/${PLUGIN_ID}/list_dir`, {
      params: { path: path || '', storage: pickerStorage() },
    })
    if (data?.ok) {
      dirPicker.path = data.path
      dirPicker.input = data.path
      dirPicker.parent = data.parent || ''
      dirPicker.dirs = data.dirs || []
    } else {
      dirPicker.dirs = []
      dirPicker.parent = ''
      if (data?.error) showMessage(data.error, 'error')
    }
  } catch (e) { /* 静默 */ } finally {
    dirPicker.loading = false
  }
}

const openDirPicker = (idx = 0) => {
  ensureTargets()
  dirPicker.targetIdx = idx
  dirPicker.show = true
  const t = config.storage_targets[idx] || {}
  browseDir(isLocalTarget(t) ? (t.path || '') : (t.path || '/'))
}

const browseTo = (path) => {
  browseDir(path)
}

const dirJoin = (name) => {
  const base = (dirPicker.path || '').replace(/\/+$/, '')
  return base ? `${base}/${name}` : `/${name}`
}

const chooseCurrent = () => {
  ensureTargets()
  const t = config.storage_targets[dirPicker.targetIdx]
  if (t) t.path = dirPicker.path
  dirPicker.show = false
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.ikuai-cfg-page {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Inter', sans-serif;
  -webkit-font-smoothing: antialiased;
  color: rgba(var(--v-theme-on-surface), 0.85);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px;
}

/* ===== 顶栏 ===== */
.ikuai-cfg-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 8px;
}

.ikuai-cfg-topbar__left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.ikuai-cfg-topbar__meta { min-width: 0; flex: 1; }
.ikuai-cfg-topbar__right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.ikuai-cfg-topbar__icon {
  width: 42px;
  height: 42px;
  border-radius: 11px;
  background: rgba(79, 140, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4f8cff;
  flex-shrink: 0;
}

.ikuai-cfg-topbar__title {
  font-size: 16px;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.ikuai-cfg-topbar__sub {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.55);
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===== Toast ===== */
.ikuai-cfg-toast {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 0.82rem;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.ikuai-cfg-toast--success {
  background: rgba(34, 197, 94, 0.08);
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.15);
}

.ikuai-cfg-toast--error {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
  border-color: rgba(239, 68, 68, 0.15);
}

.ikuai-cfg-slide-enter-active,
.ikuai-cfg-slide-leave-active { transition: all 0.3s ease; }
.ikuai-cfg-slide-enter-from,
.ikuai-cfg-slide-leave-to { opacity: 0; transform: translateY(-8px); }

/* ===== 卡片 ===== */
.ikuai-cfg-card {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 14px;
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ikuai-cfg-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

/* 折叠内容包裹层：保持卡片内各区块间距 */
.ikuai-cfg-card__body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ikuai-cfg-card__header--toggle {
  cursor: pointer;
  user-select: none;
  border-radius: 8px;
  transition: opacity 0.15s ease;
}
.ikuai-cfg-card__header--toggle:hover {
  opacity: 0.85;
}

.ikuai-cfg-card__chevron {
  color: rgba(var(--v-theme-on-surface), 0.45);
  transform: rotate(-90deg);
  transition: transform 0.2s ease;
}
.ikuai-cfg-card__chevron--open {
  transform: rotate(0deg);
}

.ikuai-cfg-card__title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

/* ===== 开关网格 ===== */
.ikuai-cfg-switch-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px;
}

.ikuai-cfg-switch-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 11px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.07);
  transition: all 0.2s ease;
}

.ikuai-cfg-switch-item--active {
  background: color-mix(in srgb, var(--accent) 8%, transparent);
  border-color: color-mix(in srgb, var(--accent) 22%, transparent);
}

.ikuai-cfg-switch-item__main {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: rgba(var(--v-theme-on-surface), 0.75);
  min-width: 0;
}

.ikuai-cfg-switch-item--active .ikuai-cfg-switch-item__main { color: var(--accent); }

/* ===== 表单 ===== */
.ikuai-cfg-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  align-items: start;
}

.ikuai-cfg-form-grid--four {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.ikuai-cfg-form-item { display: flex; flex-direction: column; gap: 5px; }

/* ===== 存储备份多目标行 ===== */
.ikuai-cfg-target-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.ikuai-cfg-target-row__fields {
  flex: 1;
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(150px, 1.1fr) minmax(0, 2.2fr) minmax(95px, 0.8fr);
  gap: 12px;
  align-items: start;
}

@media (max-width: 720px) {
  .ikuai-cfg-target-row { flex-direction: column; }
  .ikuai-cfg-target-row__fields { grid-template-columns: 1fr; }
}

.ikuai-cfg-subblock {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px 12px;
  margin: -4px 0 0;
  border-radius: 11px;
  background: rgba(var(--v-theme-on-surface), 0.015);
  border: 0.5px dashed rgba(var(--v-theme-on-surface), 0.08);
}

.ikuai-cfg-hint {
  display: flex;
  align-items: center;
  font-size: 11px;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.45);
}

/* ===== 目录选择器 ===== */
.dir-list {
  max-height: 280px;
  overflow-y: auto;
  border-radius: 10px;
  border: 0.5px solid rgba(var(--v-theme-on-surface), 0.08);
}

.dir-row {
  display: flex;
  align-items: center;
  padding: 9px 12px;
  font-size: 13px;
  cursor: pointer;
  color: rgba(var(--v-theme-on-surface), 0.8);
  border-bottom: 0.5px solid rgba(var(--v-theme-on-surface), 0.05);
  transition: background 0.15s ease;
}

.dir-row:hover { background: rgba(var(--v-theme-primary), 0.08); }

@media (max-width: 600px) {
  .ikuai-cfg-page { padding: 12px; }
  .ikuai-cfg-topbar__sub { display: none; }
}
</style>
