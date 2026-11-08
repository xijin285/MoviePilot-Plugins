<template>
  <div class="app-page">
    <!-- 顶部标题栏 -->
    <div class="page-header d-flex align-center flex-wrap ga-3 mb-4">
      <v-icon color="primary" size="28">mdi-router-network</v-icon>
      <span class="text-h5 font-weight-bold">爱快路由</span>
      <v-chip :color="status.ok ? 'success' : 'error'" size="small" variant="tonal">
        {{ status.ok ? '已连接' : '未连接' }}
      </v-chip>
      <v-chip v-if="status.version" size="small" variant="tonal" class="text-caption">
        {{ status.hostname || 'iKuai' }} · {{ status.version }}
      </v-chip>
      <v-spacer />
      <v-btn v-if="paused" size="small" variant="tonal" color="warning" prepend-icon="mdi-pause-circle-outline" @click="togglePause">
        已暂停
      </v-btn>
      <v-select v-model="refreshInterval" :items="refreshOptions" density="compact" variant="outlined"
        hide-details label="刷新间隔" style="max-width: 120px" :disabled="paused" />
      <v-btn size="small" variant="tonal" :color="paused ? 'success' : 'default'" @click="togglePause">
        <v-icon size="16" class="mr-1">{{ paused ? 'mdi-play' : 'mdi-pause' }}</v-icon>
        {{ paused ? '继续' : '暂停' }}
      </v-btn>
      <v-menu v-if="hiddenSections.length" location="bottom end">
        <template #activator="{ props: act }">
          <v-btn v-bind="act" size="small" variant="text" prepend-icon="mdi-eye-off-outline">
            已隐藏 {{ hiddenSections.length }}
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item v-for="s in hiddenSections" :key="s.key" @click="toggleHiddenByKey(s.key)">
            <template #prepend><v-icon size="16">mdi-eye-outline</v-icon></template>
            <v-list-item-title>恢复「{{ s.title }}」</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
      <v-btn size="small" variant="tonal" color="primary" :loading="refreshing" @click="refreshAll">
        <v-icon size="16" class="mr-1">mdi-refresh</v-icon>
        刷新
      </v-btn>
    </div>

    <!-- 连接错误 -->
    <v-alert v-if="!status.ok" type="error" variant="tonal" density="compact" class="mb-4">
      {{ status.error || '无法连接爱快路由，请检查插件配置' }}
    </v-alert>

    <!-- ============ 可排序卡片 ============ -->
    <template v-for="sec in orderedSections" :key="sec.key">
      <!-- 路由概况 -->
      <v-card v-if="sec.key === 'sys'" class="glass-card section-card"
        :class="{ 'is-dragging': dragIndex === sec.index, 'is-drag-over': dragOverIndex === sec.index }"
        @dragover.prevent="onDragOver(sec.index)" @dragleave.prevent="onDragLeave(sec.index)" @drop.prevent="onDrop(sec.index)">
        <v-card-title class="d-flex align-center">
          <v-icon class="drag-handle mr-1" size="18" draggable="true" title="按住拖动排序"
            @dragstart="onDragStart(sec.index, $event)" @dragend="onDragEnd">mdi-drag-vertical</v-icon>
          <v-icon color="info" size="22" class="mr-1">mdi-router-wireless</v-icon>
          <span>路由概况</span>
          <v-chip v-if="status.hostname" size="x-small" variant="tonal" color="info" class="ml-2">{{ status.hostname }}</v-chip>
          <v-spacer />
          <span class="text-caption text-medium-emphasis mr-2">{{ refreshHint }}</span>
          <LayoutBtns :index="sec.index" @move="moveSection" @hide="toggleHidden" />
        </v-card-title>
        <v-card-text class="pt-1">
          <!-- 实时指标 -->
          <div class="stat-grid mb-3">
            <div v-for="card in statCards" :key="card.label" class="stat-card">
              <div class="stat-card-icon" :style="{ background: card.bg }">
                <v-icon :color="card.color" size="24">{{ card.icon }}</v-icon>
              </div>
              <div class="stat-card-body">
                <div class="stat-card-number">{{ card.value }}</div>
                <div class="stat-card-label">{{ card.label }}</div>
                <div class="stat-card-sub" v-if="card.sub">{{ card.sub }}</div>
              </div>
            </div>
          </div>
          <!-- 静态信息 -->
          <div class="sys-grid">
            <div class="sys-item">
              <div class="sys-label">路由型号</div>
              <div class="sys-value">{{ status.model || '通用 x86' }}</div>
              <div class="sys-sub">{{ [status.arch, status.sysbit].filter(Boolean).join(' / ') || '—' }}</div>
            </div>
            <div class="sys-item">
              <div class="sys-label">固件版本</div>
              <div class="sys-value">{{ status.version_short || status.version || '—' }}</div>
              <div class="sys-sub">{{ buildText }}</div>
            </div>
            <div class="sys-item">
              <div class="sys-label">运行时长</div>
              <div class="sys-value">{{ uptimeText }}</div>
              <div class="sys-sub">{{ status.cpu_cores ? status.cpu_cores + ' 核 CPU' : '' }}</div>
            </div>
            <div class="sys-item">
              <div class="sys-label">CPU 温度</div>
              <div class="sys-value" :class="{ 'text-medium-emphasis': status.cpu_temp == null }">
                {{ status.cpu_temp == null ? '不支持' : status.cpu_temp + ' ℃' }}
              </div>
              <div class="sys-sub">{{ status.cpu_temp == null ? '机型未提供传感器' : '核心温度' }}</div>
            </div>
            <div class="sys-item">
              <div class="sys-label">内存占用</div>
              <div class="sys-value">{{ memText }}</div>
              <div class="sys-sub">已用 {{ status.mem_usage ?? 0 }}%</div>
            </div>
            <div class="sys-item">
              <div class="sys-label">累计流量</div>
              <div class="sys-value">{{ fmtBytes((status.total_up || 0) + (status.total_down || 0)) }}</div>
              <div class="sys-sub">↑ {{ fmtBytes(status.total_up) }} / ↓ {{ fmtBytes(status.total_down) }}</div>
            </div>
            <div class="sys-item">
              <div class="sys-label">当前连接数</div>
              <div class="sys-value">{{ status.connect_num ?? 0 }}</div>
              <div class="sys-sub">在线终端 {{ status.online_devices ?? 0 }} 台</div>
            </div>
            <div class="sys-item">
              <div class="sys-label">WAN 状态</div>
              <div class="sys-value">{{ wanOnlineText }}</div>
              <div class="sys-sub">{{ wanIpText }}</div>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- 线路监控 -->
      <v-card v-else-if="sec.key === 'lines'" class="glass-card section-card"
        :class="{ 'is-dragging': dragIndex === sec.index, 'is-drag-over': dragOverIndex === sec.index }"
        @dragover.prevent="onDragOver(sec.index)" @dragleave="onDragLeave(sec.index)" @drop.prevent="onDrop(sec.index)">
        <v-card-title class="d-flex align-center">
          <v-icon class="drag-handle mr-1" size="18" draggable="true" title="按住拖动排序"
            @dragstart="onDragStart(sec.index, $event)" @dragend="onDragEnd">mdi-drag-vertical</v-icon>
          <v-icon color="primary" size="22" class="mr-1">mdi-lan</v-icon>
          <span>线路监控</span>
          <v-spacer />
          <span class="text-caption text-medium-emphasis mr-2">WAN / LAN 线路状态与实时流量</span>
          <LayoutBtns :index="sec.index" @move="moveSection" @hide="toggleHidden" />
        </v-card-title>
        <v-card-text class="pt-0">
          <v-table density="compact" class="iface-table">
            <thead>
              <tr>
                <th class="text-left">线路</th>
                <th class="text-left">类型</th>
                <th class="text-left">IP 地址</th>
                <th class="text-left">状态</th>
                <th class="text-right">上行</th>
                <th class="text-right">下行</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(iface, i) in status.interfaces" :key="i">
                <td><v-chip :color="iface.type === 'LAN' ? 'info' : 'primary'" size="x-small" variant="outlined">{{ iface.name }}</v-chip></td>
                <td class="text-caption">{{ iface.type }}</td>
                <td class="text-caption font-weight-medium">{{ iface.ip || '--' }}</td>
                <td><v-chip :color="iface.connected ? 'success' : 'error'" size="x-small">{{ iface.connected ? '已连接' : '未连接' }}</v-chip></td>
                <td class="text-caption text-right">{{ fmtSpeed(iface.upload) }}</td>
                <td class="text-caption text-right">{{ fmtSpeed(iface.download) }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
      </v-card>

      <!-- 实时监控（多视图切换） -->
      <v-card v-else-if="sec.key === 'monitor'" class="glass-card section-card"
        :class="{ 'is-dragging': dragIndex === sec.index, 'is-drag-over': dragOverIndex === sec.index }"
        @dragover.prevent="onDragOver(sec.index)" @dragleave="onDragLeave(sec.index)" @drop.prevent="onDrop(sec.index)">
        <v-card-title class="d-flex align-center flex-wrap ga-2">
          <v-icon class="drag-handle mr-1" size="18" draggable="true" title="按住拖动排序"
            @dragstart="onDragStart(sec.index, $event)" @dragend="onDragEnd">mdi-drag-vertical</v-icon>
          <v-icon color="primary" size="22" class="mr-1">mdi-monitor-dashboard</v-icon>
          <span>实时监控</span>
          <v-spacer />
          <v-chip-group v-model="monitorView" selected-class="text-primary" density="compact" class="monitor-chips">
            <v-chip v-for="v in monitorViews" :key="v.value" :value="v.value" size="small" variant="outlined" filter>
              {{ v.title }}
            </v-chip>
          </v-chip-group>
          <LayoutBtns :index="sec.index" @move="moveSection" @hide="toggleHidden" />
        </v-card-title>
        <v-card-text>
          <v-alert v-if="monitorError" type="warning" variant="tonal" density="compact">{{ monitorError }}</v-alert>

          <!-- 流量/连接数分布 -->
          <template v-else-if="monitorView === 'proto'">
            <div v-if="protocols.length" class="d-flex align-center flex-wrap proto-top">
              <div class="proto-donut-wrap">
                <div class="proto-donut" :style="protoDonutStyle">
                  <div class="proto-donut-hole">
                    <div class="proto-donut-total">{{ protoTotalText }}</div>
                    <div class="proto-donut-label">总流量</div>
                  </div>
                </div>
              </div>
              <div class="proto-bars flex-1">
                <div class="text-caption text-medium-emphasis mb-1">网络会话数 Top5</div>
                <div v-for="p in protoConnTop" :key="'c-' + p.app_name" class="proto-bar-row" :title="`${protoName(p.app_name)}：${p.connect_num} 个会话`">
                  <span class="proto-bar-name">{{ protoName(p.app_name) }}</span>
                  <div class="proto-bar-track">
                    <div class="proto-bar-fill" :style="{ width: protoBarWidth(p.connect_num, protoConnMax) }"></div>
                  </div>
                  <span class="proto-bar-value">{{ p.connect_num }}</span>
                </div>
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无协议流量数据' }}
            </div>
            <v-divider v-if="protocols.length" class="my-3" />
            <div v-if="protocols.length" class="proto-table">
              <div class="proto-row proto-row-head">
                <span>协议</span><span class="text-right">总流量</span><span class="text-right">上行</span><span class="text-right">下行</span><span class="text-right">会话数</span>
              </div>
              <div v-for="p in protocols.slice(0, 10)" :key="p.app_name" class="proto-row">
                <span class="proto-name">
                  <i class="legend-dot" :style="{ background: protoColor(p.app_name) }"></i>
                  {{ protoName(p.app_name) }}
                </span>
                <span class="text-right proto-mono">{{ fmtKB(p.total) }}</span>
                <span class="text-right proto-mono">{{ fmtKB(p.upload) }}</span>
                <span class="text-right proto-mono">{{ fmtKB(p.download) }}</span>
                <span class="text-right proto-mono">{{ p.connect_num || 0 }}</span>
              </div>
            </div>
          </template>

          <!-- 终端排行（流量 / 连接数） -->
          <template v-else-if="monitorView === 'topflow'">
            <div class="d-flex align-center flex-wrap ga-2 mb-2">
              <v-chip-group v-model="rankField" density="compact" selected-class="text-primary">
                <v-chip size="small" value="total" variant="outlined" filter>流量 Top20</v-chip>
                <v-chip size="small" value="connect_num" variant="outlined" filter>连接数 Top20</v-chip>
              </v-chip-group>
              <v-spacer />
              <v-btn size="small" variant="text" prepend-icon="mdi-download" @click="exportTopflow">CSV</v-btn>
            </div>
            <div v-if="rankRows.length" class="rank-list">
              <div v-for="(r, idx) in rankRows" :key="'tp-' + idx" class="rank-row" :title="`${r.ip}  ${r.mac}`"
                @click="copyIp(r.ip)">
                <span class="rank-idx" :class="{ 'rank-top3': idx < 3 }">{{ idx + 1 }}</span>
                <span class="rank-name">
                  {{ r.hostname || r.comment || r.ip || '-' }}
                  <span class="rank-sub">{{ r.ip }}</span>
                </span>
                <div class="rank-track">
                  <div class="rank-fill" :style="{ width: rankWidth(r) }"></div>
                </div>
                <span class="rank-value">{{ rankField === 'connect_num' ? (r.connect_num + ' 个') : fmtBytes(r.total) }}</span>
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无终端流量数据' }}
            </div>
          </template>

          <!-- 应用协议排行 -->
          <template v-else-if="monitorView === 'apptop'">
            <div class="d-flex align-center mb-2">
              <span class="text-caption text-medium-emphasis">按累计流量排序（协议监控数据）</span>
              <v-spacer />
              <v-btn size="small" variant="text" prepend-icon="mdi-download" @click="exportApptop">CSV</v-btn>
            </div>
            <div v-if="appRows.length" class="rank-list">
              <div v-for="(r, idx) in appRows" :key="'ap-' + idx" class="rank-row">
                <span class="rank-idx" :class="{ 'rank-top3': idx < 3 }">{{ idx + 1 }}</span>
                <span class="rank-name">
                  <i class="legend-dot" :style="{ background: protoColor(r.name) }"></i>
                  {{ protoName(r.name) }}
                </span>
                <div class="rank-track">
                  <div class="rank-fill" :style="{ width: appWidth(r) }"></div>
                </div>
                <span class="rank-value">{{ fmtBytes(r.total) }}</span>
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无协议排行数据' }}
            </div>
          </template>

          <!-- 性能负载 -->
          <template v-else-if="monitorView === 'perf'">
            <div v-if="perfData" class="chart-grid">
              <div v-for="ch in perfCharts" :key="ch.key" class="chart-cell">
                <div class="d-flex justify-space-between text-caption mb-1">
                  <span>{{ ch.title }}</span>
                  <span class="font-weight-bold" :style="{ color: ch.color }">{{ ch.last }}</span>
                </div>
                <svg class="mini-chart" viewBox="0 0 300 64" preserveAspectRatio="none">
                  <polyline :points="ch.points" fill="none" :stroke="ch.color" stroke-width="1.6" />
                  <polygon :points="ch.areaPoints" :fill="ch.color" opacity="0.12" stroke="none" />
                </svg>
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无性能负载数据' }}
            </div>
          </template>

          <!-- 网络负载 -->
          <template v-else-if="monitorView === 'network'">
            <div v-if="netData" class="chart-grid">
              <div class="chart-cell">
                <div class="d-flex justify-space-between text-caption mb-1">
                  <span>上 / 下行速率</span>
                  <span>
                    <span class="font-weight-bold" style="color:#ef6b6b">↑ {{ fmtSpeed(netLatest.upload) }}</span>
                    <span class="font-weight-bold ml-2" style="color:#43b581">↓ {{ fmtSpeed(netLatest.download) }}</span>
                  </span>
                </div>
                <svg class="mini-chart" viewBox="0 0 300 64" preserveAspectRatio="none">
                  <polyline :points="netUpChart.points" fill="none" stroke="#ef6b6b" stroke-width="1.6" />
                  <polyline :points="netDownChart.points" fill="none" stroke="#43b581" stroke-width="1.6" />
                </svg>
                <div class="d-flex justify-space-between text-caption text-medium-emphasis mt-1">
                  <span>{{ netRangeStart }}</span><span>{{ netRangeEnd }}</span>
                </div>
              </div>
              <div class="chart-cell">
                <div class="d-flex justify-space-between text-caption mb-1">
                  <span>收 / 发包数</span>
                  <span>
                    <span class="font-weight-bold" style="color:#4f8cff">收 {{ netLatest.rx }}</span>
                    <span class="font-weight-bold ml-2" style="color:#f59e0b">发 {{ netLatest.tx }}</span>
                  </span>
                </div>
                <svg class="mini-chart" viewBox="0 0 300 64" preserveAspectRatio="none">
                  <polyline :points="netRxChart.points" fill="none" stroke="#4f8cff" stroke-width="1.6" />
                  <polyline :points="netTxChart.points" fill="none" stroke="#f59e0b" stroke-width="1.6" />
                </svg>
                <div class="d-flex justify-space-between text-caption text-medium-emphasis mt-1">
                  <span>{{ netRangeStart }}</span><span>{{ netRangeEnd }}</span>
                </div>
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无网络负载数据' }}
            </div>
          </template>

          <!-- 分流监控 -->
          <template v-else-if="monitorView === 'flowsplit'">
            <div v-if="flowTableRows.length" class="proto-table">
              <div class="proto-row proto-row-head">
                <span>分流方式</span><span class="text-right">今天连接数</span><span class="text-right">昨天连接数</span><span class="text-right">最近 7 天连接数</span>
              </div>
              <div v-for="r in flowTableRows" :key="r.name" class="proto-row">
                <span class="proto-name">{{ r.name }}</span>
                <span class="text-right proto-mono">{{ r.today }}</span>
                <span class="text-right proto-mono">{{ r.yesterday }}</span>
                <span class="text-right proto-mono">{{ r.week }}</span>
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无分流监控数据' }}
            </div>
            <div v-if="flowTableRows.length" class="text-caption text-medium-emphasis mt-2">
              总连接数包含未命中分流策略的连接；数据由路由器累计，可在爱快「分流监控」页清除
            </div>
          </template>

          <!-- IPv4 终端 -->
          <template v-else-if="monitorView === 'devices4'">
            <div class="d-flex align-center flex-wrap ga-2 mb-2">
              <v-chip size="x-small" variant="tonal" color="info">{{ filteredDevices.length }} / {{ devices.length }} 台在线</v-chip>
              <v-spacer />
              <v-text-field v-model="deviceSearch" density="compact" hide-details prepend-inner-icon="mdi-magnify"
                label="搜索 IP / MAC / 主机名" max-width="240" variant="outlined" clearable />
              <v-btn size="small" variant="text" prepend-icon="mdi-download" @click="exportDevices4">CSV</v-btn>
              <v-btn size="small" variant="text" :loading="devicesLoading" @click="loadDevices">
                <v-icon size="16" class="mr-1">mdi-refresh</v-icon>刷新
              </v-btn>
            </div>
            <v-alert v-if="devicesError" type="warning" variant="tonal" density="compact">{{ devicesError }}</v-alert>
            <div v-else-if="devices.length" class="device-table">
              <div class="device-row device-row-head">
                <span>主机名</span><span>IP 地址</span><span>MAC 地址</span>
              </div>
              <div v-for="(d, idx) in filteredDevices.slice(0, 50)" :key="'v4-' + idx" class="device-row clickable"
                title="点击复制 IP" @click="copyIp(d.ip || d.userip)">
                <span class="device-name" :title="d.hostname || d.username || '未知设备'">
                  <v-icon size="13" class="mr-1" color="primary">mdi-laptop</v-icon>
                  {{ d.hostname || d.username || '未知设备' }}
                </span>
                <span class="device-mono">{{ d.ip || d.userip || '-' }}</span>
                <span class="device-mono">{{ d.mac || d.usermac || '-' }}</span>
              </div>
              <div v-if="filteredDevices.length > 50" class="text-caption text-medium-emphasis mt-1">
                仅显示前 50 条，共 {{ filteredDevices.length }} 台
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ devicesLoading || monitorLoading ? '加载中...' : '暂无在线设备数据，请检查路由器连接与认证配置' }}
            </div>
          </template>

          <!-- IPv6 终端 -->
          <template v-else-if="monitorView === 'devices6'">
            <div class="d-flex align-center flex-wrap ga-2 mb-2">
              <v-chip size="x-small" variant="tonal" color="info">{{ filteredDevices6.length }} / {{ devices6.length }} 台</v-chip>
              <v-spacer />
              <v-text-field v-model="searchMap.devices6" density="compact" hide-details prepend-inner-icon="mdi-magnify"
                label="搜索 IPv6 / MAC / 主机名" max-width="240" variant="outlined" clearable />
              <v-btn size="small" variant="text" prepend-icon="mdi-download" @click="exportDevices6">CSV</v-btn>
            </div>
            <div v-if="devices6.length" class="device-table">
              <div class="device-row device-row-head">
                <span>主机名</span><span>IPv6 地址</span><span>MAC 地址</span>
              </div>
              <div v-for="(d, idx) in filteredDevices6.slice(0, 50)" :key="'v6-' + idx" class="device-row clickable"
                title="点击复制 IPv6" @click="copyIp(d.ip)">
                <span class="device-name" :title="d.hostname || '未知设备'">
                  <v-icon size="13" class="mr-1" color="primary">mdi-laptop</v-icon>
                  {{ d.hostname || '未知设备' }}
                </span>
                <span class="device-mono">{{ d.ip || '-' }}</span>
                <span class="device-mono">{{ d.mac || '-' }}</span>
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无 IPv6 在线终端（可能未开启 IPv6 或无 IPv6 设备）' }}
            </div>
          </template>

          <!-- 摄像头 -->
          <template v-else-if="monitorView === 'camera'">
            <div v-if="cameras.length" class="device-table">
              <div class="device-row device-row-head camera-head">
                <span>设备</span><span>IP 地址</span><span>状态</span>
              </div>
              <div v-for="(c, idx) in cameras" :key="'cam-' + idx" class="device-row camera-row">
                <span class="device-name">
                  <v-icon size="13" class="mr-1" color="primary">mdi-cctv</v-icon>
                  {{ c.name || c.hostname || c.ip || '摄像头' }}
                </span>
                <span class="device-mono">{{ c.ip || '-' }}</span>
                <span>
                  <v-chip size="x-small" :color="camOnline(c) ? 'success' : 'grey'" variant="tonal">
                    {{ camOnline(c) ? '在线' : '离线' }}
                  </v-chip>
                </span>
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无摄像头数据（需在路由器上绑定爱快云平台后自动发现摄像头）' }}
            </div>
          </template>

          <!-- DHCP 终端 -->
          <template v-else-if="monitorView === 'dhcp'">
            <div class="d-flex align-center flex-wrap ga-2 mb-2">
              <v-chip size="x-small" variant="tonal" color="info">{{ filteredDhcp.length }} / {{ dhcpLeases.length }} 条</v-chip>
              <v-spacer />
              <v-text-field v-model="searchMap.dhcp" density="compact" hide-details prepend-inner-icon="mdi-magnify"
                label="搜索 IP / MAC / 主机名" max-width="240" variant="outlined" clearable />
              <v-btn size="small" variant="text" prepend-icon="mdi-download" @click="exportDhcp">CSV</v-btn>
            </div>
            <div v-if="dhcpLeases.length" class="device-table">
              <div class="device-row device-row-head">
                <span>主机名</span><span>IP 地址</span><span>MAC 地址</span><span>接口</span><span>租约到期</span>
              </div>
              <div v-for="(d, idx) in filteredDhcp.slice(0, 50)" :key="'dh-' + idx" class="device-row dhcp-row clickable"
                title="点击复制 IP" @click="copyIp(d.ip || d.ip_addr)">
                <span class="device-name" :title="d.comment || d.hostname || '未知终端'">
                  <v-icon size="13" class="mr-1" color="primary">mdi-ticket-confirmation-outline</v-icon>
                  {{ d.comment || d.hostname || '未知终端' }}
                </span>
                <span class="device-mono">{{ d.ip || d.ip_addr || '-' }}</span>
                <span class="device-mono">{{ d.mac || '-' }}</span>
                <span class="device-mono">{{ d.interface || '-' }}</span>
                <span class="device-mono">{{ fmtTs(d.end_time) }}</span>
              </div>
              <div v-if="filteredDhcp.length > 50" class="text-caption text-medium-emphasis mt-1">
                仅显示前 50 条，共 {{ filteredDhcp.length }} 条
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无 DHCP 租约记录' }}
            </div>
          </template>

          <!-- 黑名单 -->
          <template v-else-if="monitorView === 'blacklist'">
            <div class="d-flex align-center flex-wrap ga-2 mb-2">
              <v-chip size="x-small" variant="tonal" color="error">{{ filteredBlacklist.length }} / {{ blacklistItems.length }} 条</v-chip>
              <v-spacer />
              <v-text-field v-model="searchMap.blacklist" density="compact" hide-details prepend-inner-icon="mdi-magnify"
                label="搜索 MAC / 备注" max-width="240" variant="outlined" clearable />
              <v-btn size="small" variant="text" prepend-icon="mdi-download" @click="exportBlacklist">CSV</v-btn>
            </div>
            <div v-if="blacklistItems.length" class="device-table">
              <div class="device-row device-row-head">
                <span>MAC 地址</span><span>备注</span><span>状态</span>
              </div>
              <div v-for="(b, idx) in filteredBlacklist.slice(0, 50)" :key="'bl-' + idx" class="device-row clickable"
                title="点击复制 MAC" @click="copyIp(b.mac)">
                <span class="device-mono">{{ b.mac || '-' }}</span>
                <span class="device-name">{{ b.comment || '-' }}</span>
                <span>
                  <v-chip size="x-small" :color="String(b.enabled) === 'yes' ? 'error' : 'grey'" variant="tonal">
                    {{ String(b.enabled) === 'yes' ? '生效中' : '已停用' }}
                  </v-chip>
                </span>
              </div>
            </div>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '黑名单列表为空（可在爱快「终端接入控制」中将终端加入黑名单）' }}
            </div>
          </template>

          <!-- DNS 设置 -->
          <template v-else-if="monitorView === 'dns'">
            <template v-if="dnsData">
              <div class="dns-cfg">
                <div class="dns-cfg-item"><span class="dns-cfg-label">上游 DNS1</span><span class="device-mono">{{ dnsData.config.dns1 || '-' }}</span></div>
                <div class="dns-cfg-item"><span class="dns-cfg-label">上游 DNS2</span><span class="device-mono">{{ dnsData.config.dns2 || '-' }}</span></div>
                <div class="dns-cfg-item"><span class="dns-cfg-label">DoH 加密解析</span><span class="device-mono">{{ dnsData.config.query || '-' }}</span></div>
                <div class="dns-cfg-item"><span class="dns-cfg-label">DNS 缓存</span>
                  <v-chip size="x-small" :color="String(dnsData.config.enabled) === 'yes' ? 'success' : 'grey'" variant="tonal">
                    {{ String(dnsData.config.enabled) === 'yes' ? `已开启（TTL ${dnsData.config.cache_ttl || '-'}s）` : '关闭' }}
                  </v-chip>
                </div>
                <div class="dns-cfg-item"><span class="dns-cfg-label">DNS 强制代理</span>
                  <v-chip size="x-small" :color="dnsData.config.proxy_force ? 'warning' : 'grey'" variant="tonal">
                    {{ dnsData.config.proxy_force ? '开启' : '关闭' }}
                  </v-chip>
                </div>
              </div>
              <v-divider class="my-2" />
              <div class="text-caption text-medium-emphasis mb-1">自定义解析规则（共 {{ dnsData.rules_total || dnsData.rules.length }} 条）</div>
              <div v-if="dnsData.rules.length" class="device-table">
                <div class="device-row device-row-head">
                  <span>域名</span><span>解析地址</span><span>来源</span><span>状态</span>
                </div>
                <div v-for="(r, idx) in dnsData.rules.slice(0, 30)" :key="'dn-' + idx" class="device-row">
                  <span class="device-name" :title="r.domain">{{ r.domain || '-' }}</span>
                  <span class="device-mono">{{ r.dns_addr || '-' }}</span>
                  <span class="device-mono">{{ r.comment || r.src_addr || '-' }}</span>
                  <span>
                    <v-chip size="x-small" :color="String(r.enabled) === 'yes' ? 'success' : 'grey'" variant="tonal">
                      {{ String(r.enabled) === 'yes' ? '启用' : '停用' }}
                    </v-chip>
                  </span>
                </div>
                <div v-if="dnsData.rules.length > 30" class="text-caption text-medium-emphasis mt-1">
                  仅显示前 30 条，共 {{ dnsData.rules.length }} 条
                </div>
              </div>
              <div v-else class="text-caption text-medium-emphasis text-center py-2">暂无自定义解析规则</div>
            </template>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无 DNS 设置数据' }}
            </div>
          </template>

          <!-- 路由表 -->
          <template v-else-if="monitorView === 'routes'">
            <div class="d-flex align-center flex-wrap ga-2 mb-2">
              <v-chip-group v-model="routeFamily" density="compact" selected-class="text-primary">
                <v-chip size="small" value="v4" variant="outlined" filter>IPv4（{{ filteredRoutes4.length }}）</v-chip>
                <v-chip size="small" value="v6" variant="outlined" filter>IPv6（{{ filteredRoutes6.length }}）</v-chip>
              </v-chip-group>
              <v-spacer />
              <v-text-field v-model="searchMap.routes" density="compact" hide-details prepend-inner-icon="mdi-magnify"
                label="搜索网段 / 网关 / 接口" max-width="240" variant="outlined" clearable />
              <v-btn size="small" variant="text" prepend-icon="mdi-download" @click="exportRoutes">CSV</v-btn>
            </div>
            <template v-if="routeData">
              <div v-if="routeFamily === 'v4' && filteredRoutes4.length" class="device-table">
                <div class="device-row device-row-head">
                  <span>目的网段</span><span>子网掩码</span><span>网关</span><span>接口</span><span>优先级</span>
                </div>
                <div v-for="(r, idx) in filteredRoutes4.slice(0, 50)" :key="'r4-' + idx" class="device-row route-row clickable"
                  title="点击复制网段" @click="copyIp(r.dst_addr)">
                  <span class="device-mono">{{ r.dst_addr || '-' }}</span>
                  <span class="device-mono">{{ r.netmask || '-' }}</span>
                  <span class="device-mono">{{ r.gateway || '-' }}</span>
                  <span class="device-mono">{{ r.interface || '-' }}</span>
                  <span class="device-mono">{{ r.prio ?? '-' }}</span>
                </div>
                <div v-if="filteredRoutes4.length > 50" class="text-caption text-medium-emphasis mt-1">
                  仅显示前 50 条，共 {{ filteredRoutes4.length }} 条
                </div>
              </div>
              <div v-else-if="routeFamily === 'v6' && filteredRoutes6.length" class="device-table">
                <div class="device-row device-row-head">
                  <span>目的网段</span><span>网关</span><span>接口</span><span>优先级</span>
                </div>
                <div v-for="(r, idx) in filteredRoutes6.slice(0, 50)" :key="'r6-' + idx" class="device-row route-row-6 clickable"
                  title="点击复制网段" @click="copyIp(r.dst_addr)">
                  <span class="device-mono">{{ r.dst_addr || '-' }}</span>
                  <span class="device-mono">{{ r.gateway || '-' }}</span>
                  <span class="device-mono">{{ r.interface || '-' }}</span>
                  <span class="device-mono">{{ r.prio ?? '-' }}</span>
                </div>
              </div>
              <div v-else class="text-caption text-medium-emphasis text-center py-4">
                {{ monitorLoading ? '加载中...' : '暂无路由表数据' }}
              </div>
            </template>
          </template>

          <!-- UPnP -->
          <template v-else-if="monitorView === 'upnp'">
            <template v-if="upnpData">
              <div class="d-flex align-center flex-wrap ga-2 mb-2">
                <v-chip size="small" :color="String(upnpData.config.enabled) === 'yes' ? 'success' : 'grey'" variant="tonal" prepend-icon="mdi-switch">
                  UPnP 服务：{{ String(upnpData.config.enabled) === 'yes' ? '已开启' : '未开启' }}
                </v-chip>
                <v-chip v-if="upnpData.config.interface" size="small" variant="tonal" prepend-icon="mdi-ethernet">
                  线路：{{ upnpData.config.interface }}
                </v-chip>
                <v-chip v-if="upnpData.config.exclude_port" size="small" variant="tonal" prepend-icon="mdi-block-helper">
                  排除端口：{{ upnpData.config.exclude_port }}
                </v-chip>
              </div>
              <div v-if="upnpData.leases.length" class="device-table">
                <div class="device-row device-row-head">
                  <span>内网地址</span><span>协议</span><span>内网端口</span><span>外网端口</span><span>应用描述</span><span>创建时间</span>
                </div>
                <div v-for="(u, idx) in upnpData.leases.slice(0, 50)" :key="'up-' + idx" class="device-row upnp-row">
                  <span class="device-mono">{{ u.lan_ip || '-' }}</span>
                  <span class="device-mono">{{ u.protocol || u.proto || '-' }}</span>
                  <span class="device-mono">{{ u.lan_port || '-' }}</span>
                  <span class="device-mono">{{ u.wan_port || '-' }}</span>
                  <span class="device-name">{{ u.comment || '-' }}</span>
                  <span class="device-mono">{{ fmtTs(u.time) }}</span>
                </div>
              </div>
              <div v-else class="text-caption text-medium-emphasis text-center py-2">
                暂无 UPnP 端口映射（内网设备通过 UPnP 自动创建映射后显示在这里）
              </div>
            </template>
            <div v-else class="text-caption text-medium-emphasis text-center py-4">
              {{ monitorLoading ? '加载中...' : '暂无 UPnP 状态数据' }}
            </div>
          </template>
        </v-card-text>
      </v-card>

      <!-- 系统日志 -->
      <v-card v-else-if="sec.key === 'logs'" class="glass-card section-card"
        :class="{ 'is-dragging': dragIndex === sec.index, 'is-drag-over': dragOverIndex === sec.index }"
        @dragover.prevent="onDragOver(sec.index)" @dragleave="onDragLeave(sec.index)" @drop.prevent="onDrop(sec.index)">
        <v-card-title class="d-flex align-center flex-wrap ga-2">
          <v-icon class="drag-handle mr-1" size="18" draggable="true" title="按住拖动排序"
            @dragstart="onDragStart(sec.index, $event)" @dragend="onDragEnd">mdi-drag-vertical</v-icon>
          <v-icon color="warning" size="22" class="mr-1">mdi-text-box-outline</v-icon>
          <span>系统日志</span>
          <v-spacer />
          <v-select v-model="logType" :items="logTypes" density="compact" hide-details variant="outlined"
            style="max-width: 150px" label="日志类型" />
          <v-btn size="small" variant="text" :loading="logsLoading" @click="loadLogs">
            <v-icon size="16" class="mr-1">mdi-refresh</v-icon>刷新
          </v-btn>
          <LayoutBtns :index="sec.index" @move="moveSection" @hide="toggleHidden" />
        </v-card-title>
        <v-card-text>
          <v-alert v-if="logsError" type="warning" variant="tonal" density="compact">{{ logsError }}</v-alert>
          <div v-else-if="logs.length" class="log-list">
            <div v-for="(l, idx) in logs.slice(0, 80)" :key="idx" class="log-row">
              <span class="log-time">{{ fmtLogTime(l) }}</span>
              <span class="log-msg">{{ l.msg || l.message || l.content || JSON.stringify(l) }}</span>
            </div>
          </div>
          <div v-else class="text-caption text-medium-emphasis text-center py-2">
            {{ logsLoading ? '加载中...' : '暂无日志' }}
          </div>
        </v-card-text>
      </v-card>

    </template>

    <v-snackbar v-model="snack.show" :timeout="1800" location="bottom" color="success" variant="tonal">
      {{ snack.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, onUnmounted, reactive, ref, watch } from 'vue'

const props = defineProps({
  api: { type: Object, default: () => ({}) },
  pluginId: { type: String, default: 'IkuaiRouterBackup' },
  navKey: { type: String, default: 'main' },
})

const pluginId = computed(() => props.pluginId || 'IkuaiRouterBackup')

// ============ 卡片排序 / 显示隐藏（自定义排版） ============
const DEFAULT_LAYOUT = ['sys', 'monitor', 'lines', 'logs']
const SECTION_TITLES = { monitor: '实时监控', sys: '路由概况', lines: '线路监控', logs: '系统日志' }
const layout = ref([...DEFAULT_LAYOUT])
const hiddenKeys = ref([])

// 排序 / 隐藏按钮小组件
const LayoutBtns = defineComponent({
  name: 'LayoutBtns',
  props: { index: { type: Number, required: true } },
  emits: ['move', 'hide'],
  setup(props2, { emit }) {
    return () => h('span', { class: 'layout-btns' }, [
      h('button', {
        class: 'layout-btn', title: '上移',
        onClick: (e) => { e.stopPropagation(); emit('move', props2.index, -1) },
      }, [h('i', { class: 'mdi mdi-arrow-up' })]),
      h('button', {
        class: 'layout-btn', title: '下移',
        onClick: (e) => { e.stopPropagation(); emit('move', props2.index, 1) },
      }, [h('i', { class: 'mdi mdi-arrow-down' })]),
      h('button', {
        class: 'layout-btn', title: '隐藏此卡片',
        onClick: (e) => { e.stopPropagation(); emit('hide', props2.index) },
      }, [h('i', { class: 'mdi mdi-eye-off-outline' })]),
    ])
  },
})

const orderedSections = computed(() =>
  layout.value
    .map((key, index) => ({ key, index }))
    .filter((s) => !hiddenKeys.value.includes(s.key)),
)

const hiddenSections = computed(() =>
  layout.value
    .filter((k) => hiddenKeys.value.includes(k))
    .map((k) => ({ key: k, title: SECTION_TITLES[k] || k })),
)

// 拖拽排序
const dragIndex = ref(-1)
const dragOverIndex = ref(-1)

const onDragStart = (index, e) => {
  dragIndex.value = index
  try {
    if (e?.dataTransfer) {
      e.dataTransfer.effectAllowed = 'move'
      e.dataTransfer.setData('text/plain', String(index))
    }
  } catch (err) { /* 忽略 */ }
}
const onDragOver = (index) => {
  if (dragIndex.value >= 0 && index !== dragIndex.value) dragOverIndex.value = index
}
const onDragLeave = (index) => {
  if (dragOverIndex.value === index) dragOverIndex.value = -1
}
const onDragEnd = () => {
  dragIndex.value = -1
  dragOverIndex.value = -1
}
const onDrop = (index) => {
  const from = dragIndex.value
  onDragEnd()
  if (from < 0 || from === index) return
  const arr = [...layout.value]
  const [moved] = arr.splice(from, 1)
  arr.splice(index, 0, moved)
  layout.value = arr
  persistLayout()
}

const LAYOUT_VERSION = 2
const persistLayout = async () => {
  try {
    await props.api.post(`plugin/${pluginId.value}/dashboard_layout`, {
      layout: [...layout.value],
      hidden: [...hiddenKeys.value],
      version: LAYOUT_VERSION,
    })
  } catch (e) { /* 静默 */ }
}

const moveSection = (index, delta) => {
  const target = index + delta
  if (target < 0 || target >= layout.value.length) return
  const arr = [...layout.value]
  ;[arr[index], arr[target]] = [arr[target], arr[index]]
  layout.value = arr
  persistLayout()
}

const loadLayout = async () => {
  try {
    const data = await props.api.get(`plugin/${pluginId.value}/dashboard_layout`)
    let saved = Array.isArray(data?.layout) ? data.layout.filter((k) => DEFAULT_LAYOUT.includes(k)) : []
    // 布局版本迁移：路由概况合并实时指标后改为默认第一张，旧保存布局整体作废
    const layoutVer = Number(data?.version) || 1
    if (layoutVer < 2) {
      saved = []
      hiddenKeys.value = []
    }
    if (saved.length) {
      // 保存过的排前，未配置的按默认顺序补后
      const rest = DEFAULT_LAYOUT.filter((k) => !saved.includes(k))
      layout.value = [...saved, ...rest]
    }
    if (!saved.length) {
      layout.value = [...DEFAULT_LAYOUT]
      hiddenKeys.value = []
      persistLayout()
    } else {
      hiddenKeys.value = Array.isArray(data?.hidden)
        ? data.hidden.filter((k) => DEFAULT_LAYOUT.includes(k))
        : []
    }
  } catch (e) { /* 静默 */ }
}

const toggleHidden = (index) => {
  const key = layout.value[index]
  if (!key) return
  // 至少保留一张卡片，避免整页空白
  if (!hiddenKeys.value.includes(key) && orderedSections.value.length <= 1) return
  hiddenKeys.value = hiddenKeys.value.includes(key)
    ? hiddenKeys.value.filter((k) => k !== key)
    : [...hiddenKeys.value, key]
  persistLayout()
}

const toggleHiddenByKey = (key) => {
  hiddenKeys.value = hiddenKeys.value.filter((k) => k !== key)
  persistLayout()
}

// ============ 实时状态 ============
const refreshing = ref(false)
const status = reactive({
  ok: false, error: '', hostname: '', version: '',
  cpu_usage: 0, mem_usage: 0, uptime: 0,
  upload_speed: 0, download_speed: 0,
  interfaces: [],
})

const barColor = (v) => {
  const n = Number(v) || 0
  return n < 50 ? 'success' : n < 80 ? 'warning' : 'error'
}

const statCards = computed(() => [
  {
    label: 'CPU 使用率', value: `${status.cpu_usage ?? 0}%`,
    icon: 'mdi-cpu-64-bit', color: barColor(status.cpu_usage), bg: 'rgba(79,140,255,0.12)',
    sub: '',
  },
  {
    label: '内存使用率', value: `${status.mem_usage ?? 0}%`,
    icon: 'mdi-memory', color: barColor(status.mem_usage), bg: 'rgba(67,233,123,0.12)',
    sub: '',
  },
  {
    label: '实时上行', value: fmtSpeed(status.upload_speed),
    icon: 'mdi-arrow-up-bold', color: 'info', bg: 'rgba(79,172,254,0.12)',
    sub: '',
  },
  {
    label: '实时下行', value: fmtSpeed(status.download_speed),
    icon: 'mdi-arrow-down-bold', color: 'warning', bg: 'rgba(255,183,77,0.12)',
    sub: '',
  },
])

const fmtSpeed = (bps) => {
  const v = Number(bps) || 0
  if (v >= 1024 * 1024 * 1024) return (v / 1024 / 1024 / 1024).toFixed(2) + ' GB/s'
  if (v >= 1024 * 1024) return (v / 1024 / 1024).toFixed(1) + ' MB/s'
  if (v >= 1024) return (v / 1024).toFixed(1) + ' KB/s'
  return v + ' B/s'
}

// WAN 口连接状态（概况卡）
const wanIfaces = computed(() => (status.interfaces || []).filter((i) => i.type === 'WAN'))
const wanOnlineText = computed(() => {
  const list = wanIfaces.value
  if (!list.length) return '—'
  const up = list.filter((i) => i.connected).length
  return `${up}/${list.length} 已连接`
})
const wanIpText = computed(() => {
  const list = wanIfaces.value
  if (!list.length) return '未检测到 WAN 口'
  return list.map((i) => i.ip).filter(Boolean).join(' / ') || '未获取到 IP'
})

const fmtBytes = (b) => {
  const v = Number(b) || 0
  if (v >= 1024 * 1024 * 1024 * 1024) return (v / 1024 / 1024 / 1024 / 1024).toFixed(2) + ' TB'
  if (v >= 1024 * 1024 * 1024) return (v / 1024 / 1024 / 1024).toFixed(2) + ' GB'
  if (v >= 1024 * 1024) return (v / 1024 / 1024).toFixed(1) + ' MB'
  if (v >= 1024) return (v / 1024).toFixed(1) + ' KB'
  return v + ' B'
}

const fmtUptime = (sec) => {
  const s = Number(sec) || 0
  const d = Math.floor(s / 86400)
  const h = Math.floor((s % 86400) / 3600)
  const m = Math.floor((s % 3600) / 60)
  if (d > 0) return `${d}天${h}小时`
  if (h > 0) return `${h}小时${m}分钟`
  return `${m}分钟`
}

const fmtTs = (ts) => {
  const n = Number(ts)
  if (!n) return '-'
  try {
    return new Date(n * 1000).toLocaleString()
  } catch (e) {
    return '-'
  }
}

// ============ 实时监控（多视图） ============
const monitorViews = [
  { title: '流量/连接数分布', value: 'proto' },
  { title: '终端排行', value: 'topflow' },
  { title: '协议排行', value: 'apptop' },
  { title: '性能负载', value: 'perf' },
  { title: '网络负载', value: 'network' },
  { title: '分流监控', value: 'flowsplit' },
  { title: 'IPv4 终端', value: 'devices4' },
  { title: 'IPv6 终端', value: 'devices6' },
  { title: '摄像头', value: 'camera' },
  { title: 'DHCP 终端', value: 'dhcp' },
  { title: '黑名单', value: 'blacklist' },
  { title: 'DNS 设置', value: 'dns' },
  { title: '路由表', value: 'routes' },
  { title: 'UPnP', value: 'upnp' },
]
const monitorView = ref('proto')
const monitorLoading = ref(false)
const monitorError = ref('')
const viewLoaded = reactive({})

const protocols = ref([])
const perfData = ref(null)
const netData = ref(null)
const flowRows = ref(null)
const devices6 = ref([])
const cameras = ref([])
const dhcpLeases = ref([])
const blacklistItems = ref([])
const dnsData = ref(null)
const routeData = ref(null)
const routeFamily = ref('v4')
const upnpData = ref(null)
const topRows = ref([])
const appRows = ref([])
const rankField = ref('total')

// 排行视图：按流量或连接数排序取前 10
const rankRows = computed(() => {
  const arr = [...topRows.value]
  arr.sort((a, b) => (Number(b[rankField.value]) || 0) - (Number(a[rankField.value]) || 0))
  return arr.slice(0, 10)
})
const rankMax = computed(() => Math.max(1, ...rankRows.value.map((r) => Number(r[rankField.value]) || 0)))
const appMax = computed(() => Math.max(1, ...appRows.value.map((r) => Number(r.total) || 0)))
const rankWidth = (r) => `${Math.max(2, Math.round(((Number(r[rankField.value]) || 0) / rankMax.value) * 100))}%`
const appWidth = (r) => `${Math.max(2, Math.round(((Number(r.total) || 0) / appMax.value) * 100))}%`

// 路由概况文案
const uptimeText = computed(() => fmtUptime(status.uptime))
const memText = computed(() => {
  const total = Number(status.memory_total) || 0
  const used = Number(status.memory_used) || 0
  if (!total) return `${status.mem_usage ?? 0}%`
  return `${(used / 1024 / 1024 / 1024).toFixed(2)} / ${(total / 1024 / 1024 / 1024).toFixed(2)} GB`
})
const buildText = computed(() => {
  const b = String(status.build_date || '')
  if (b.length !== 12) return status.version || ''
  return `Build ${b.slice(0, 4)}-${b.slice(4, 6)}-${b.slice(6, 8)}`
})

// 协议配色（对齐爱快协议监控）
const PROTO_COLORS = {
  'HTTP': '#9a7fd1', 'Video': '#ffb980', 'Game': '#dc69aa', 'Download': '#5cadff',
  'Transport': '#2db7f5', 'IM': '#19be6b', 'Common': '#ff9900', 'Others': '#808695',
  'Test': '#e062ae', 'Unknown': '#c5c8ce',
}
// 协议分类中文名（对齐爱快「协议监控」官方译名）
const PROTO_NAMES = {
  'HTTP': 'HTTP协议', 'Video': '网络视频', 'Game': '网络游戏', 'Transport': '文件传输',
  'IM': '网络通讯', 'Common': '常用协议', 'Download': '网络下载', 'Others': '其它应用',
  'Test': '测速软件', 'Unknown': '未知应用', 'Total': '所有协议',
}
const protoName = (name) => PROTO_NAMES[name] || name
const protoColor = (name) => PROTO_COLORS[name] || '#4f8cff'

const fmtKB = (kb) => {
  const v = Number(kb) || 0
  if (v >= 1024 * 1024) return (v / 1024 / 1024).toFixed(2) + ' GB'
  if (v >= 1024) return (v / 1024).toFixed(1) + ' MB'
  return v.toFixed(0) + ' KB'
}

const protoTotalText = computed(() => {
  const total = protocols.value.reduce((s, p) => s + (Number(p.total) || 0), 0)
  return total ? fmtKB(total) : '--'
})

const protoDonutStyle = computed(() => {
  const ps = protocols.value.filter((p) => (Number(p.total) || 0) > 0)
  const totalSum = ps.reduce((s, p) => s + Number(p.total), 0)
  if (!totalSum) return { background: 'conic-gradient(#808695 0deg 360deg)' }
  let acc = 0
  const stops = []
  ps.forEach((p) => {
    const from = (acc / totalSum) * 360
    acc += Number(p.total)
    const to = (acc / totalSum) * 360
    stops.push(`${protoColor(p.app_name)} ${from.toFixed(2)}deg ${to.toFixed(2)}deg`)
  })
  return { background: `conic-gradient(${stops.join(', ')})` }
})

const protoConnTop = computed(() =>
  [...protocols.value].sort((a, b) => (b.connect_num || 0) - (a.connect_num || 0)).slice(0, 5),
)
const protoConnMax = computed(() =>
  Math.max(1, ...protocols.value.map((p) => Number(p.connect_num) || 0)),
)
const protoBarWidth = (v, max) => `${Math.max(4, Math.round(((Number(v) || 0) / max) * 100))}%`

// 折线图构建
const buildChart = (values, w = 300, h = 64, maxV = null) => {
  const pts = values.map((v) => Number(v) || 0)
  if (!pts.length) return { points: '', areaPoints: '' }
  const max = maxV || Math.max(...pts, 1)
  const stepX = pts.length > 1 ? w / (pts.length - 1) : 0
  const coords = pts.map((v, i) => {
    const x = i * stepX
    const y = h - Math.max(0, Math.min(1, v / max)) * (h - 4) - 2
    return [x, y]
  })
  const points = coords.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
  const areaPoints = `${points} ${w},${h} 0,${h}`
  return { points, areaPoints }
}

// 性能负载 4 小图（容器键与数据点字段由后端分别命名）
const perfCharts = computed(() => {
  if (!perfData.value) return []
  const mk = (containerKey, fieldKey, title, color, unit = '', fixedMax = null, scale = 1) => {
    const items = perfData.value[containerKey] || []
    const values = items.map((p) => (Number(p[fieldKey]) || 0) * scale)
    const ch = buildChart(values, 300, 64, fixedMax)
    const last = values.length ? values[values.length - 1] / scale : 0
    return { key: containerKey, title, color, points: ch.points, areaPoints: ch.areaPoints, last: `${Math.round(last * 10) / 10}${unit}` }
  }
  return [
    mk('cpu', 'cpu', 'CPU 使用率', '#4f8cff', '%', 100),
    mk('memory', 'memory_use', '内存使用率', '#43e97b', '%', 100),
    mk('terminals', 'on_terminal', '在线终端数', '#f59e0b', ' 台'),
    mk('conns', 'conn_num', '网络连接数', '#dc69aa', ' 个'),
  ]
})

// 网络负载
const netSeries = computed(() => {
  if (!netData.value) return []
  return netData.value
})
const netUpChart = computed(() => buildChart(netSeries.value.map((p) => Number(p.max_upload) || 0)))
const netDownChart = computed(() => buildChart(netSeries.value.map((p) => Number(p.max_download) || 0)))
const netRxChart = computed(() => buildChart(netSeries.value.map((p) => Number(p.rx_packages) || 0)))
const netTxChart = computed(() => buildChart(netSeries.value.map((p) => Number(p.tx_packages) || 0)))
const netLatest = computed(() => {
  const s = netSeries.value
  const last = s.length ? s[s.length - 1] : {}
  return {
    upload: last.max_upload || 0,
    download: last.max_download || 0,
    rx: last.rx_packages || 0,
    tx: last.tx_packages || 0,
  }
})
const tsText = (t) => {
  try { return new Date(Number(t) * 1000).toLocaleTimeString() } catch (e) { return '' }
}
const netRangeStart = computed(() => {
  const s = netSeries.value
  return s.length ? tsText(s[0].timestamp) : ''
})
const netRangeEnd = computed(() => {
  const s = netSeries.value
  return s.length ? tsText(s[s.length - 1].timestamp) : ''
})

// 分流监控表格行（today/yesterday/week 三列）
const FLOW_ROW_DEFS = [
  { key: 'port_cnt', name: '端口分流' },
  { key: 'proto_cnt', name: '协议分流' },
  { key: 'domain_cnt', name: '域名分流' },
  { key: 'llb_cnt', name: '多线负载' },
  { key: 'conn_cnt', name: '总连接数（含未分流）' },
]
const flowTableRows = computed(() => {
  if (!flowRows.value) return []
  const src = flowRows.value
  const num = (v) => (v === '' || v === null || v === undefined ? 0 : Number(v) || 0)
  return FLOW_ROW_DEFS.map((d) => ({
    name: d.name,
    today: num(src.today?.[d.key]),
    yesterday: num(src.yesterday?.[d.key]),
    week: num(src.week?.[d.key]),
  }))
})

const camOnline = (c) => {
  const t = Number(c.last_time || c.online_time || c.online || 0)
  return t > 0
}

const loadMonitorView = async (force = false) => {
  const view = monitorView.value
  if (view === 'proto') {
    if (!force && protocols.value.length) return
    monitorLoading.value = true
    try {
      const data = await props.api.get(`plugin/${pluginId.value}/protocol_flow`)
      if (data?.ok) protocols.value = data.protocols || []
      else { protocols.value = []; monitorError.value = data?.error || '' }
    } catch (e) { protocols.value = [] } finally { monitorLoading.value = false }
    return
  }
  // IPv4 终端：复用设备接口
  if (view === 'devices4') {
    if (!force && devices.value.length) return
    monitorLoading.value = true
    try {
      await loadDevices()
    } finally {
      monitorLoading.value = false
    }
    return
  }
  if (!force && viewLoaded[view]) return
  monitorLoading.value = true
  monitorError.value = ''
  try {
    const data = await props.api.get(`plugin/${pluginId.value}/monitor_view`, {
      params: { view, datetype: 'hour' },
    })
    if (!data?.ok) {
      monitorError.value = data?.error || '获取监控数据失败'
      return
    }
    viewLoaded[view] = true
    if (view === 'perf') perfData.value = data
    else if (view === 'network') netData.value = data.rate_stat || []
    else if (view === 'flowsplit') flowRows.value = data.rows || {}
    else if (view === 'devices6') devices6.value = data.devices || []
    else if (view === 'camera') cameras.value = data.cameras || []
    else if (view === 'dhcp') dhcpLeases.value = data.leases || []
    else if (view === 'blacklist') blacklistItems.value = data.items || []
    else if (view === 'dns') dnsData.value = { config: data.config || {}, rules: data.rules || [], rules_total: data.rules_total || 0 }
    else if (view === 'routes') routeData.value = { v4: data.v4 || [], v6: data.v6 || [] }
    else if (view === 'upnp') upnpData.value = { config: data.config || {}, leases: data.leases || [] }
    else if (view === 'topflow') topRows.value = data.rows || []
    else if (view === 'apptop') appRows.value = data.rows || []
  } catch (e) {
    monitorError.value = '获取监控数据失败'
  } finally {
    monitorLoading.value = false
  }
}

watch(monitorView, () => loadMonitorView())

// ============ 在线设备 ============
const devices = ref([])
const devicesLoading = ref(false)
const devicesError = ref('')
const deviceSearch = ref('')

// 各视图搜索关键字（前端过滤，不请求路由）
const searchMap = reactive({ devices6: '', dhcp: '', blacklist: '', routes: '' })

const hit = (q, ...vals) => {
  const s = String(q || '').trim().toLowerCase()
  if (!s) return true
  return vals.some((v) => String(v ?? '').toLowerCase().includes(s))
}

const filteredDevices = computed(() => {
  const q = (deviceSearch.value || '').trim().toLowerCase()
  if (!q) return devices.value
  return devices.value.filter((d) => {
    const s = `${d.hostname || ''} ${d.username || ''} ${d.ip || d.userip || ''} ${d.mac || d.usermac || ''}`.toLowerCase()
    return s.includes(q)
  })
})

const filteredDevices6 = computed(() =>
  devices6.value.filter((d) => hit(searchMap.devices6, d.hostname, d.ip, d.mac)),
)
const filteredDhcp = computed(() =>
  dhcpLeases.value.filter((d) =>
    hit(searchMap.dhcp, d.comment, d.hostname, d.ip, d.ip_addr, d.mac, d.interface)),
)
const filteredBlacklist = computed(() =>
  blacklistItems.value.filter((b) => hit(searchMap.blacklist, b.mac, b.comment)),
)
const filteredRoutes4 = computed(() =>
  (routeData.value?.v4 || []).filter((r) =>
    hit(searchMap.routes, r.dst_addr, r.netmask, r.gateway, r.interface)),
)
const filteredRoutes6 = computed(() =>
  (routeData.value?.v6 || []).filter((r) =>
    hit(searchMap.routes, r.dst_addr, r.gateway, r.interface)),
)

// ============ 复制 / 导出 ============
const snack = reactive({ show: false, text: '' })
const showSnack = (text) => {
  snack.text = text
  snack.show = true
}

const copyIp = async (value) => {
  const text = String(value ?? '').trim()
  if (!text || text === '-') return
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      ta.remove()
    }
    showSnack(`已复制：${text}`)
  } catch (e) {
    showSnack('复制失败，请手动选择文本')
  }
}

const csvCell = (v) => {
  const s = String(v ?? '')
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

const downloadCsv = (name, headers, rows) => {
  const lines = [headers.map(csvCell).join(',')]
  rows.forEach((r) => lines.push(r.map(csvCell).join(',')))
  const blob = new Blob(['\ufeff' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
  showSnack(`已导出 ${name}（${rows.length} 行）`)
}

const todayTag = () => {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}`
}

const exportDevices4 = () => downloadCsv(
  `ikuai_终端IPv4_${todayTag()}.csv`,
  ['主机名', 'IP 地址', 'MAC 地址'],
  filteredDevices.value.map((d) => [d.hostname || d.username || '', d.ip || d.userip || '', d.mac || d.usermac || '']),
)

const exportDevices6 = () => downloadCsv(
  `ikuai_终端IPv6_${todayTag()}.csv`,
  ['主机名', 'IPv6 地址', 'MAC 地址'],
  filteredDevices6.value.map((d) => [d.hostname || '', d.ip || '', d.mac || '']),
)

const exportDhcp = () => downloadCsv(
  `ikuai_DHCP终端_${todayTag()}.csv`,
  ['主机名', 'IP 地址', 'MAC 地址', '接口', '租约到期'],
  filteredDhcp.value.map((d) => [
    d.comment || d.hostname || '', d.ip || d.ip_addr || '', d.mac || '', d.interface || '', fmtTs(d.end_time),
  ]),
)

const exportBlacklist = () => downloadCsv(
  `ikuai_黑名单_${todayTag()}.csv`,
  ['MAC 地址', '备注', '状态'],
  filteredBlacklist.value.map((b) => [
    b.mac || '', b.comment || '', String(b.enabled) === 'yes' ? '生效中' : '已停用',
  ]),
)

const exportTopflow = () => downloadCsv(
  `ikuai_终端排行_${todayTag()}.csv`,
  ['排名', '主机名', 'IP 地址', 'MAC 地址', '累计上行(字节)', '累计下行(字节)', '累计总流量(字节)', '连接数', '上线时间'],
  rankRows.value.map((r, i) => [
    i + 1, r.hostname || r.comment || '', r.ip || '', r.mac || '',
    r.total_up, r.total_down, r.total, r.connect_num, r.uptime || '',
  ]),
)

const exportApptop = () => downloadCsv(
  `ikuai_协议排行_${todayTag()}.csv`,
  ['排名', '协议', '累计上行(字节)', '累计下行(字节)', '累计总流量(字节)', '会话数'],
  appRows.value.map((r, i) => [i + 1, protoName(r.name), r.total_up, r.total_down, r.total, r.connect_num || 0]),
)

const exportRoutes = () => {
  if (routeFamily.value === 'v6') {
    downloadCsv(
      `ikuai_路由表IPv6_${todayTag()}.csv`,
      ['目的网段', '网关', '接口', '优先级'],
      filteredRoutes6.value.map((r) => [r.dst_addr || '', r.gateway || '', r.interface || '', r.prio ?? '']),
    )
    return
  }
  downloadCsv(
    `ikuai_路由表IPv4_${todayTag()}.csv`,
    ['目的网段', '子网掩码', '网关', '接口', '优先级'],
    filteredRoutes4.value.map((r) => [
      r.dst_addr || '', r.netmask || '', r.gateway || '', r.interface || '', r.prio ?? '',
    ]),
  )
}

const loadDevices = async () => {
  devicesLoading.value = true
  devicesError.value = ''
  try {
    const data = await props.api.get(`plugin/${pluginId.value}/devices`)
    if (data?.ok) {
      devices.value = data.devices || []
    } else {
      devices.value = []
      devicesError.value = data?.error || '获取在线设备失败'
    }
  } catch (e) {
    devicesError.value = '获取在线设备失败'
  } finally {
    devicesLoading.value = false
  }
}

// ============ 系统日志 ============
const logs = ref([])
const logsLoading = ref(false)
const logsError = ref('')
const logType = ref('system')
const logTypes = [
  { title: '系统事件', value: 'system' },
  { title: 'PPPoE 拨号', value: 'pppoe' },
  { title: 'DHCP', value: 'dhcp' },
  { title: 'DDNS', value: 'ddns' },
  { title: '认证（需令牌）', value: 'auth' },
  { title: 'ARP（需令牌）', value: 'arp' },
  { title: '通知（需令牌）', value: 'notice' },
  { title: '无线（需令牌）', value: 'wireless' },
  { title: 'Web 访问（需令牌）', value: 'web' },
]

const fmtLogTime = (l) => {
  const ts = l.time || l.timestamp || l.created_at
  if (!ts) return ''
  try {
    const n = Number(ts)
    return new Date((n > 1e12 ? n : n * 1000)).toLocaleString()
  } catch (e) {
    return String(ts)
  }
}

const loadLogs = async () => {
  logsLoading.value = true
  logsError.value = ''
  try {
    const data = await props.api.get(`plugin/${pluginId.value}/logs`, {
      params: { log_type: logType.value, page_size: 100 },
    })
    if (data?.ok) {
      logs.value = data.logs || []
    } else {
      logs.value = []
      logsError.value = data?.error || '获取日志失败'
    }
  } catch (e) {
    logsError.value = '获取日志失败'
  } finally {
    logsLoading.value = false
  }
}

// 切换日志类型后立即加载对应日志
watch(logType, () => {
  loadLogs()
})

// ============ 刷新 ============
const refreshStatus = async () => {
  try {
    const data = await props.api.get(`plugin/${pluginId.value}/status`)
    if (data) Object.assign(status, data)
  } catch (e) {
    /* 静默 */
  }
}

const refreshAll = async () => {
  refreshing.value = true
  try {
    await refreshStatus()
    loadLogs()
    loadMonitorView(true)
  } finally {
    refreshing.value = false
  }
}

let tickTimer = null

// 刷新间隔 / 暂停
const REFRESH_KEY = 'ikuai_dashboard_refresh'
const refreshOptions = [
  { title: '10 秒', value: 10 },
  { title: '30 秒', value: 30 },
  { title: '60 秒', value: 60 },
  { title: '手动', value: 0 },
]
const readInterval = () => {
  try {
    const v = Number(localStorage.getItem(REFRESH_KEY))
    if ([0, 10, 30, 60].includes(v)) return v
  } catch (e) { /* 忽略 */ }
  return 30
}
const refreshInterval = ref(readInterval())
const paused = ref(false)
const refreshHint = computed(() => {
  if (paused.value) return '已暂停自动刷新'
  if (!refreshInterval.value) return '手动刷新'
  return `每 ${refreshInterval.value} 秒自动刷新`
})

// 需要随定时器自动刷新的视图（静态列表类视图不重复拉取）
const LIVE_VIEWS = ['proto', 'perf', 'network', 'flowsplit', 'devices4', 'devices6']

const tick = async () => {
  if (paused.value || !refreshInterval.value) return
  await refreshStatus()
  if (LIVE_VIEWS.includes(monitorView.value)) loadMonitorView(true)
}

const restartTimer = () => {
  if (tickTimer) {
    clearInterval(tickTimer)
    tickTimer = null
  }
  if (paused.value || !refreshInterval.value) return
  tickTimer = setInterval(tick, refreshInterval.value * 1000)
}

const togglePause = () => {
  paused.value = !paused.value
  restartTimer()
  showSnack(paused.value ? '已暂停自动刷新' : `已恢复自动刷新（${refreshHint.value}）`)
}

watch(refreshInterval, (v) => {
  try { localStorage.setItem(REFRESH_KEY, String(v)) } catch (e) { /* 忽略 */ }
  restartTimer()
})

onMounted(() => {
  loadLayout()
  refreshStatus()
  loadLogs()
  loadMonitorView()
  restartTimer()
})

onUnmounted(() => {
  if (tickTimer) clearInterval(tickTimer)
})
</script>

<style scoped>
.app-page {
  padding: 4px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(var(--v-theme-surface), 0.6);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.07);
  min-width: 0;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 10px;
}
.stat-card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-card-number {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-card-label {
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface-variant));
}
.stat-card-sub {
  font-size: 11px;
  color: rgb(var(--v-theme-on-surface-variant));
  opacity: 0.7;
}

.glass-card {
  border-radius: 12px;
}
.section-card {
  margin-bottom: 16px;
}

/* 排序按钮 */
.layout-btns {
  display: inline-flex;
  gap: 2px;
}
.layout-btn {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: rgb(var(--v-theme-on-surface-variant));
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0.55;
  transition: all 0.15s;
}
.layout-btn:hover {
  opacity: 1;
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
}

/* 监控视图 chips */
.monitor-chips {
  max-width: 100%;
}
.monitor-chips .v-chip {
  cursor: pointer;
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

/* 协议流量监控 */
.proto-top {
  gap: 16px;
}
.proto-donut-wrap {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  width: 150px;
}
.proto-donut {
  width: 130px;
  height: 130px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.proto-donut-hole {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: rgb(var(--v-theme-surface));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.proto-donut-total {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.2;
}
.proto-donut-label {
  font-size: 10px;
  color: rgb(var(--v-theme-on-surface-variant));
}
.proto-bars {
  min-width: 200px;
}
.proto-bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 0;
  font-size: 12px;
}
.proto-bar-name {
  width: 72px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgb(var(--v-theme-on-surface-variant));
}
.proto-bar-track {
  flex: 1;
  height: 10px;
  border-radius: 5px;
  background: rgba(var(--v-border-color), 0.08);
  overflow: hidden;
}
.proto-bar-fill {
  height: 100%;
  border-radius: 5px;
  background: linear-gradient(90deg, rgba(79, 140, 255, 0.85), rgba(79, 140, 255, 0.5));
}
.proto-bar-value {
  width: 40px;
  text-align: right;
  font-family: 'Courier New', monospace;
}
.proto-table {
  font-size: 12px;
}
.proto-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) repeat(3, minmax(0, 1fr));
  gap: 8px;
  align-items: center;
  padding: 4px 8px;
  border-radius: 6px;
}
.proto-row:not(.proto-row-head):hover {
  background: rgba(var(--v-theme-primary), 0.05);
}
.proto-row-head {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 11px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 0;
}
.proto-name {
  display: flex;
  align-items: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.proto-mono {
  font-family: 'Courier New', monospace;
  color: rgb(var(--v-theme-on-surface-variant));
}
.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 2px;
  margin-right: 6px;
  flex-shrink: 0;
}

/* 设备表 */
.device-table {
  font-size: 12px;
}
.device-row {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1.2fr) minmax(0, 1.6fr);
  gap: 8px;
  align-items: center;
  padding: 5px 8px;
  border-radius: 6px;
}
.device-row:not(.device-row-head):hover {
  background: rgba(var(--v-theme-primary), 0.05);
}
.device-row-head {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 11px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 0;
}
.camera-row {
  grid-template-columns: minmax(0, 2fr) minmax(0, 1.6fr) minmax(0, 0.8fr);
}
.dhcp-row {
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1.2fr) minmax(0, 1.6fr) minmax(0, 0.8fr) minmax(0, 1.4fr);
}
.route-row {
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1.2fr) minmax(0, 1.2fr) minmax(0, 1fr) minmax(0, 0.6fr);
}
.route-row-6 {
  grid-template-columns: minmax(0, 2fr) minmax(0, 1.6fr) minmax(0, 1fr) minmax(0, 0.6fr);
}
.upnp-row {
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 0.6fr) minmax(0, 0.8fr) minmax(0, 0.8fr) minmax(0, 1.2fr) minmax(0, 1.4fr);
}
/* DNS 设置 */
.dns-cfg {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
  font-size: 12px;
}
.dns-cfg-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.dns-cfg-label {
  color: rgb(var(--v-theme-on-surface-variant));
  font-size: 11px;
}
.device-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.device-mono {
  font-family: 'Courier New', monospace;
  color: rgb(var(--v-theme-on-surface-variant));
}

/* 日志 */
.log-list {
  max-height: 300px;
  overflow-y: auto;
  font-size: 12px;
}
.log-row {
  display: flex;
  gap: 10px;
  padding: 3px 6px;
  border-radius: 4px;
}
.log-row:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}
.log-time {
  font-family: 'Courier New', monospace;
  color: rgb(var(--v-theme-on-surface-variant));
  white-space: nowrap;
  flex-shrink: 0;
}
.log-msg {
  word-break: break-all;
}

@media (max-width: 768px) {
  .device-row {
    grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr) minmax(0, 1.4fr);
    gap: 4px;
    font-size: 11px;
  }
  .camera-row {
    grid-template-columns: minmax(0, 1.6fr) minmax(0, 1.2fr) minmax(0, 0.8fr);
  }
}

/* 拖拽排序 */
.drag-handle {
  cursor: grab;
  opacity: 0.45;
  flex-shrink: 0;
}
.drag-handle:hover {
  opacity: 0.9;
}
.drag-handle:active {
  cursor: grabbing;
}
.section-card {
  transition: box-shadow 0.15s ease, transform 0.15s ease, opacity 0.15s ease;
}
.section-card.is-dragging {
  opacity: 0.5;
  transform: scale(0.995);
}
.section-card.is-drag-over {
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.55) !important;
}

/* 可点击行（复制） */
.device-row.clickable {
  cursor: pointer;
}
.device-row.clickable:hover {
  background: rgba(var(--v-theme-primary), 0.07);
}

/* 路由概况 */
.sys-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}
.sys-item {
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(var(--v-theme-primary), 0.05);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  min-width: 0;
}
.sys-label {
  font-size: 11px;
  letter-spacing: 0.02em;
  opacity: 0.6;
  margin-bottom: 2px;
}
.sys-value {
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sys-sub {
  font-size: 11px;
  opacity: 0.55;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 排行列表 */
.rank-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.rank-row {
  display: grid;
  grid-template-columns: 22px minmax(0, 1.4fr) minmax(60px, 2fr) auto;
  align-items: center;
  gap: 10px;
  padding: 5px 6px;
  border-radius: 8px;
  cursor: pointer;
}
.rank-row:hover {
  background: rgba(var(--v-theme-primary), 0.07);
}
.rank-idx {
  font-size: 12px;
  font-weight: 700;
  text-align: center;
  opacity: 0.55;
}
.rank-idx.rank-top3 {
  color: rgb(var(--v-theme-primary));
  opacity: 1;
}
.rank-name {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 4px;
}
.rank-sub {
  font-size: 11px;
  opacity: 0.5;
  margin-left: 4px;
  font-family: ui-monospace, monospace;
}
.rank-track {
  height: 8px;
  border-radius: 4px;
  background: rgba(var(--v-theme-on-surface), 0.07);
  overflow: hidden;
}
.rank-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, rgba(var(--v-theme-primary), 0.55), rgba(var(--v-theme-primary), 0.95));
}
.rank-value {
  font-size: 12px;
  font-family: ui-monospace, monospace;
  text-align: right;
  white-space: nowrap;
  opacity: 0.85;
}
</style>
