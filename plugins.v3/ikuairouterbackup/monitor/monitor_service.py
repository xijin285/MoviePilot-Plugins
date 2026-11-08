"""爱快路由实时监控服务

提供：
- 实时状态获取（带 TTL 缓存，避免仪表盘频繁刷新打爆路由器）
- 在线设备列表（v4 令牌优先，v3 密码会话尽力兼容）
- 系统日志查看（v4 REST /log/{type}，端点参考 ikuai-cli 项目）
- 24h 负载/流量趋势采样（save_data 持久化）
- CPU/内存负载告警（连续 N 次超阈值推送 MP 通知）
"""
import threading
import time
from typing import Any, Dict, List, Optional

from app.log import logger

from ..ikuai.client import IkuaiClient

# 日志类型 → v4 REST 路径（参考 ikuaios/ikuai-cli internal/cmd/log/command.go）
LOG_TYPES = {
    "system": "系统日志",
    "pppoe": "PPPoE日志",
    "dhcp": "DHCP日志",
    "auth": "认证日志",
    "arp": "ARP日志",
    "ddns": "DDNS日志",
    "notice": "通知日志",
    "wireless": "无线日志",
    "web": "Web访问日志",
}

# 日志类型 → v4 路径映射
_LOG_PATH = {
    "system": "log/system",
    "pppoe": "log/pppoe",
    "dhcp": "log/dhcp",
    "auth": "log/auth",
    "arp": "log/arp",
    "ddns": "log/ddns",
    "notice": "log/notice",
    "wireless": "log/wireless",
    "web": "log/web_activity",
}

STATUS_CACHE_TTL = 30  # 实时状态缓存秒数
TREND_MAX_POINTS = 288  # 24h × 每5分钟一点
ALERT_KEY = "alert_history"  # 告警记录（插件数据）
ALERT_MAX_RECORDS = 100  # 最多保留条数
TREND_KEY = "ikuai_monitor_trend"


class MonitorService:
    """监控服务类"""

    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        self._status_cache: Optional[Dict[str, Any]] = None
        self._status_cache_time: float = 0
        self._cache_lock = threading.Lock()
        # 负载告警连续计数
        self._load_breach_count = 0
        self._load_notified = False

    # ---------- 客户端 ----------

    def _get_client(self) -> IkuaiClient:
        return IkuaiClient(
            url=self.plugin._ikuai_url,
            username=self.plugin._ikuai_username,
            password=self.plugin._ikuai_password,
            plugin_name=self.plugin_name,
            auth_mode=getattr(self.plugin, '_ikuai_auth_mode', 'auto'),
            api_token=getattr(self.plugin, '_ikuai_api_token', '')
        )

    @staticmethod
    def _require_config(plugin) -> Optional[str]:
        """校验连接配置，返回错误信息或 None"""
        auth_mode = (getattr(plugin, '_ikuai_auth_mode', 'auto') or 'auto').lower()
        api_token = (getattr(plugin, '_ikuai_api_token', '') or '').strip()
        if not plugin._ikuai_url:
            return "爱快路由器地址未设置"
        if auth_mode == "token" and not api_token:
            return "API令牌模式未填写令牌"
        if auth_mode != "token" and (not plugin._ikuai_username or not plugin._ikuai_password):
            return "URL、用户名或密码未设置"
        return None

    # ---------- 实时状态（缓存） ----------

    def get_status(self, force: bool = False) -> Dict[str, Any]:
        """
        获取实时状态（30 秒缓存）。
        :return: {'ok': bool, 'error': str, ...状态字段}
        """
        with self._cache_lock:
            now = time.time()
            if not force and self._status_cache and now - self._status_cache_time < STATUS_CACHE_TTL:
                return self._status_cache

        error = self._require_config(self.plugin)
        if error:
            result = {'ok': False, 'error': error}
        else:
            result = {'ok': True, 'error': ''}
            try:
                client = self._get_client()
                if not client.login():
                    result = {'ok': False, 'error': '登录爱快路由失败'}
                else:
                    system_info = client.get_system_info() or {}
                    monitor_info = client.get_monitor_info() or {}
                    # CPU / 内存：monitor 优先，system 兜底
                    cpu = monitor_info.get("cpu_usage") if isinstance(monitor_info, dict) else None
                    mem = monitor_info.get("mem_usage") if isinstance(monitor_info, dict) else None
                    if cpu is None:
                        cpu = system_info.get("cpu_usage", 0)
                    if mem is None:
                        mem = system_info.get("mem_usage", 0)
                    try:
                        cpu = round(float(cpu or 0), 1)
                    except (TypeError, ValueError):
                        cpu = 0.0
                    try:
                        mem = round(float(mem or 0), 1)
                    except (TypeError, ValueError):
                        mem = 0.0
                    result.update({
                        'cpu_usage': cpu,
                        'mem_usage': mem,
                        'hostname': system_info.get("hostname", ""),
                        'version': system_info.get("version", ""),
                        'uptime': system_info.get("uptime", 0),
                        'upload_speed': system_info.get("upload_speed", 0) or 0,
                        'download_speed': system_info.get("download_speed", 0) or 0,
                        'wan_ip': system_info.get("wan_ip", ""),
                        'online_devices': system_info.get("online_users"),
                        # ---- 系统概览 ----
                        'model': system_info.get("model", "") or "",
                        'arch': system_info.get("arch", "") or "",
                        'sysbit': system_info.get("sysbit", "") or "",
                        'version_short': system_info.get("version_short", "") or "",
                        'build_date': system_info.get("build_date", 0) or 0,
                        'enterprise': system_info.get("enterprise", False),
                        'cpu_cores': system_info.get("cpu_cores", 0) or 0,
                        'cpu_temp': system_info.get("cpu_temp"),
                        'memory_total': system_info.get("memory_total", 0) or 0,
                        'memory_used': system_info.get("memory_used", 0) or 0,
                        'total_up': system_info.get("total_up", 0) or 0,
                        'total_down': system_info.get("total_down", 0) or 0,
                        'connect_num': system_info.get("connect_num", 0) or 0,
                    })
            except Exception as e:
                logger.error(f"{self.plugin_name} 获取实时状态失败: {e}")
                result = {'ok': False, 'error': str(e)}

        # 线路监控（WAN/LAN，失败不影响主状态）
        result['interfaces'] = []
        if result.get('ok'):
            try:
                iface_info = client.get_interface_info() or {}
                stream_map = {line.get("interface"): line for line in (iface_info.get("iface_stream") or []) if isinstance(line, dict)}
                for line in (iface_info.get("iface_check") or [])[:4]:
                    if not isinstance(line, dict):
                        continue
                    name = line.get("interface", "")
                    if name.startswith("adsl") or name.startswith("pppoe"):
                        iface_type = "子线路"
                    elif name.startswith("wan"):
                        iface_type = "WAN"
                    else:
                        iface_type = "其他"
                    stream = stream_map.get(name, {})
                    result['interfaces'].append({
                        'name': name,
                        'type': iface_type,
                        'ip': line.get("ip_addr", "") or "--",
                        'connected': line.get("result", "") == "success",
                        'upload': stream.get("upload", 0) or 0,
                        'download': stream.get("download", 0) or 0,
                    })
                for lan in (iface_info.get("snapshoot_lan") or [])[:2]:
                    if not isinstance(lan, dict):
                        continue
                    name = lan.get("interface", "")
                    stream = stream_map.get(name, {})
                    result['interfaces'].append({
                        'name': name,
                        'type': 'LAN',
                        'ip': lan.get("ip_addr", "") or "--",
                        'connected': True,
                        'upload': stream.get("upload", 0) or 0,
                        'download': stream.get("download", 0) or 0,
                    })
            except Exception as e:
                logger.debug(f"{self.plugin_name} 获取线路监控信息失败: {e}")

        with self._cache_lock:
            self._status_cache = result
            self._status_cache_time = time.time()
        return result

    # ---------- 在线设备 ----------

    def get_devices(self) -> Dict[str, Any]:
        """获取在线设备列表（v4 令牌优先，v3 尽力兼容）"""
        error = self._require_config(self.plugin)
        if error:
            return {'ok': False, 'error': error, 'devices': [], 'auth_v4': False}
        try:
            client = self._get_client()
            if not client.login():
                return {'ok': False, 'error': '登录爱快路由失败', 'devices': [], 'auth_v4': False}
            devices = client.get_online_devices()
            if devices is None:
                return {
                    'ok': False,
                    'error': '获取在线设备失败，请检查路由器连接与认证配置',
                    'devices': [],
                    'auth_v4': bool((getattr(self.plugin, '_ikuai_api_token', '') or '').strip()),
                }
            return {'ok': True, 'error': '', 'devices': devices, 'auth_v4': True}
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取在线设备失败: {e}")
            return {'ok': False, 'error': str(e), 'devices': [], 'auth_v4': False}

    # ---------- 系统日志 ----------

    def get_logs(self, log_type: str = "system", page_size: int = 100) -> Dict[str, Any]:
        """获取系统日志（v4 令牌走 REST，v3 密码走 syslog-{type}）"""
        if log_type not in _LOG_PATH:
            return {'ok': False, 'error': f'不支持的日志类型: {log_type}', 'logs': []}
        error = self._require_config(self.plugin)
        if error:
            return {'ok': False, 'error': error, 'logs': []}
        try:
            client = self._get_client()
            if not client.login():
                return {'ok': False, 'error': '登录爱快路由失败', 'logs': []}
            logs = client.get_logs(log_type, page_size=page_size)
            if logs is None:
                auth_mode = (getattr(self.plugin, '_ikuai_auth_mode', 'auto') or 'auto').lower()
                api_token = (getattr(self.plugin, '_ikuai_api_token', '') or '').strip()
                if auth_mode != "token" and not api_token and log_type in ("auth", "arp", "notice", "wireless", "web"):
                    return {'ok': False, 'error': '该日志类型需配置爱快4.x API 令牌；v3 密码模式仅支持 系统事件/PPPoE/DHCP/DDNS', 'logs': []}
                return {'ok': False, 'error': '获取日志失败，请检查路由器连接与认证配置', 'logs': []}
            return {'ok': True, 'error': '', 'logs': logs}
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取日志失败: {e}")
            return {'ok': False, 'error': str(e), 'logs': []}

    # ---------- 协议流量分布 ----------

    def get_protocol_flow(self) -> Dict[str, Any]:
        """获取协议流量分布（爱快「协议监控」，v3 monitor_app_flow）"""
        error = self._require_config(self.plugin)
        if error:
            return {'ok': False, 'error': error, 'protocols': []}
        try:
            client = self._get_client()
            if not client.login():
                return {'ok': False, 'error': '登录爱快路由失败', 'protocols': []}
            data = client.get_protocol_flow()
            if data is None:
                return {'ok': False, 'error': '获取协议流量失败，当前固件可能不支持协议监控', 'protocols': []}
            protocols = sorted(
                [p for p in data if isinstance(p, dict)],
                key=lambda p: (p.get('total') or 0),
                reverse=True,
            )
            return {'ok': True, 'error': '', 'protocols': protocols}
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取协议流量失败: {e}")
            return {'ok': False, 'error': str(e), 'protocols': []}

    def get_monitor_view(self, view: str, datetype: str = "hour") -> Dict[str, Any]:
        """
        监控面板多视图分发（性能负载/网络负载/分流监控/IPv6终端/摄像头）
        :param view: perf | network | flowsplit | devices6 | camera
        :param datetype: perf/network 的时间范围 hour|day|week|month
        """
        error = self._require_config(self.plugin)
        base = {'ok': False, 'error': error, 'view': view}
        if error:
            return base
        try:
            client = self._get_client()
            if not client.login():
                return {**base, 'error': '登录爱快路由失败'}

            if view == 'perf':
                data = client.get_system_history(datetype)
                if data is None:
                    return {**base, 'error': '获取性能负载历史失败，当前固件可能不支持'}
                return {'ok': True, 'error': '', 'view': view,
                        'cpu': data.get('cpu', []),
                        'memory': data.get('memory', []),
                        'terminals': data.get('on_terminal', []),
                        'conns': data.get('conn_num', [])}

            if view == 'network':
                data = client.get_network_history(datetype)
                if data is None:
                    return {**base, 'error': '获取网络负载历史失败，当前固件可能不支持'}
                return {'ok': True, 'error': '', 'view': view, 'rate_stat': data}

            if view == 'flowsplit':
                data = client.get_flow_split()
                if data is None:
                    return {**base, 'error': '获取分流监控失败，当前固件可能不支持'}
                return {'ok': True, 'error': '', 'view': view, 'rows': data}

            if view == 'devices6':
                data = client.get_devices_v6()
                if data is None:
                    return {**base, 'error': '获取 IPv6 终端失败，当前固件可能不支持'}
                return {'ok': True, 'error': '', 'view': view,
                        'devices': data, 'total': len(data)}

            if view == 'camera':
                data = client.get_cameras()
                if data is None:
                    return {**base, 'error': '获取摄像头失败（需路由器绑定爱快云平台）'}
                return {'ok': True, 'error': '', 'view': view,
                        'cameras': data, 'total': len(data)}

            if view == 'dhcp':
                data = client.get_dhcp_leases()
                if data is None:
                    return {**base, 'error': '获取 DHCP 终端列表失败（当前连接模式或固件不支持）'}
                return {'ok': True, 'error': '', 'view': view,
                        'leases': data, 'total': len(data)}

            if view == 'blacklist':
                data = client.get_blacklist()
                if data is None:
                    return {**base, 'error': '获取黑名单列表失败（当前连接模式或固件不支持）'}
                return {'ok': True, 'error': '', 'view': view,
                        'items': data.get('items', []), 'total': data.get('total', 0)}

            if view == 'dns':
                data = client.get_dns_settings()
                if data is None:
                    return {**base, 'error': '获取 DNS 设置失败（当前连接模式或固件不支持）'}
                return {'ok': True, 'error': '', 'view': view, **data}

            if view == 'routes':
                data = client.get_route_table()
                if data is None:
                    return {**base, 'error': '获取路由表失败（当前连接模式或固件不支持）'}
                return {'ok': True, 'error': '', 'view': view,
                        'v4': data.get('v4', []), 'v6': data.get('v6', [])}

            if view == 'upnp':
                data = client.get_upnp()
                if data is None:
                    return {**base, 'error': '获取 UPnP 状态失败（当前连接模式或固件不支持）'}
                return {'ok': True, 'error': '', 'view': view, **data}

            if view == 'topflow':
                devices = client.get_online_devices()
                if devices is None:
                    return {**base, 'error': '获取终端流量排行失败（当前连接模式或固件不支持）'}
                rows = []
                for d in devices:
                    if not isinstance(d, dict):
                        continue
                    try:
                        up = int(d.get('total_up') or 0)
                    except (TypeError, ValueError):
                        up = 0
                    try:
                        down = int(d.get('total_down') or 0)
                    except (TypeError, ValueError):
                        down = 0
                    try:
                        conns = int(d.get('connect_num') or 0)
                    except (TypeError, ValueError):
                        conns = 0
                    rows.append({
                        'ip': d.get('ip') or d.get('ip_addr') or '',
                        'mac': d.get('mac') or d.get('usermac') or '',
                        'hostname': d.get('hostname') or d.get('comment') or d.get('username') or '',
                        'comment': d.get('comment') or '',
                        'client_type': d.get('client_type') or '',
                        'total_up': up,
                        'total_down': down,
                        'total': up + down,
                        'upload': d.get('upload') or 0,
                        'download': d.get('download') or 0,
                        'connect_num': conns,
                        'uptime': d.get('uptime') or '',
                    })
                rows.sort(key=lambda r: r['total'], reverse=True)
                return {'ok': True, 'error': '', 'view': view,
                        'rows': rows[:20], 'total': len(rows)}

            if view == 'apptop':
                protocols = client.get_protocol_flow() or []
                rows = []
                for p in protocols:
                    if not isinstance(p, dict):
                        continue
                    try:
                        up = int(p.get('total_up') or 0)
                    except (TypeError, ValueError):
                        up = 0
                    try:
                        down = int(p.get('total_down') or 0)
                    except (TypeError, ValueError):
                        down = 0
                    if up + down <= 0:
                        continue
                    rows.append({
                        'name': p.get('app_name') or p.get('name') or '未知',
                        'total_up': up,
                        'total_down': down,
                        'total': up + down,
                        'upload': p.get('upload') or 0,
                        'download': p.get('download') or 0,
                        'connect_num': p.get('connect_num') or 0,
                    })
                rows.sort(key=lambda r: r['total'], reverse=True)
                return {'ok': True, 'error': '', 'view': view,
                        'rows': rows[:15], 'total': len(rows)}

            return {**base, 'error': f'未知监控视图: {view}'}
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取监控视图 {view} 失败: {e}")
            return {**base, 'error': str(e)}

    # ---------- 趋势采样 ----------

    def sample_trend(self):
        """定时采样负载/流量，存入插件数据（24h 环形）"""
        status = self.get_status()
        if not status.get('ok'):
            return
        point = {
            't': int(time.time()),
            'cpu': status.get('cpu_usage', 0),
            'mem': status.get('mem_usage', 0),
            'up': status.get('upload_speed', 0) or 0,
            'down': status.get('download_speed', 0) or 0,
        }
        try:
            trend = self.plugin.get_data(TREND_KEY) or []
            if not isinstance(trend, list):
                trend = []
            trend.append(point)
            trend = trend[-TREND_MAX_POINTS:]
            self.plugin.save_data(TREND_KEY, trend)
        except Exception as e:
            logger.error(f"{self.plugin_name} 保存监控趋势失败: {e}")

    def get_trend(self) -> List[Dict[str, Any]]:
        """读取趋势数据"""
        try:
            trend = self.plugin.get_data(TREND_KEY) or []
            return trend if isinstance(trend, list) else []
        except Exception:
            return []

    # ---------- 负载告警 ----------

    def run_load_check(self):
        """定时负载检查：连续超阈值推送通知，并记录告警事件（含恢复时间）"""
        if not getattr(self.plugin, '_load_warn_enable', False):
            return
        status = self.get_status()
        if not status.get('ok'):
            self._load_breach_count = 0
            return
        cpu = status.get('cpu_usage', 0) or 0
        mem = status.get('mem_usage', 0) or 0
        cpu_limit = float(getattr(self.plugin, '_load_cpu_threshold', 90) or 90)
        mem_limit = float(getattr(self.plugin, '_load_mem_threshold', 90) or 90)
        need_times = max(1, int(getattr(self.plugin, '_load_warn_times', 3) or 3))

        breached = cpu >= cpu_limit or mem >= mem_limit
        if breached:
            self._load_breach_count += 1
            logger.debug(
                f"{self.plugin_name} 负载超阈值 {self._load_breach_count}/{need_times}"
                f"（CPU {cpu}% / 内存 {mem}%）"
            )
            if self._load_breach_count >= need_times and not self._load_notified:
                self._load_notified = True
                msg = (
                    f"路由器负载持续偏高：CPU {cpu}%（阈值 {cpu_limit:g}%）、"
                    f"内存 {mem}%（阈值 {mem_limit:g}%），已连续 {self._load_breach_count} 次检测超标。"
                )
                logger.warning(f"{self.plugin_name} {msg}")
                self.plugin._send_notification(success=False, message=msg)
            # 告警期间持续刷新峰值
            self._record_alert(cpu, mem, cpu_limit, mem_limit, ongoing=True)
        else:
            if self._load_notified:
                logger.info(f"{self.plugin_name} 负载已恢复正常（CPU {cpu}% / 内存 {mem}%）")
                self._record_alert(cpu, mem, cpu_limit, mem_limit, recover=True)
            self._load_breach_count = 0
            self._load_notified = False

    # ---------- 告警记录 ----------

    def _load_alert_history(self) -> List[Dict[str, Any]]:
        try:
            data = self.plugin.get_data(ALERT_KEY)
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _record_alert(self, cpu: float, mem: float, cpu_limit: float, mem_limit: float,
                      ongoing: bool = False, recover: bool = False):
        """记录/更新一条负载告警（未恢复的为 ongoing，恢复时补 end 与持续时长）"""
        try:
            history = self._load_alert_history()
            now = int(time.time())
            current = None
            for rec in history:
                if isinstance(rec, dict) and not rec.get('end'):
                    current = rec
                    break
            if ongoing and current is None:
                kinds = []
                if cpu >= cpu_limit:
                    kinds.append('CPU')
                if mem >= mem_limit:
                    kinds.append('内存')
                history.append({
                    'id': now,
                    'kind': '+'.join(kinds) or '负载',
                    'start': now,
                    'end': None,
                    'peak_cpu': round(float(cpu), 1),
                    'peak_mem': round(float(mem), 1),
                    'cpu_limit': cpu_limit,
                    'mem_limit': mem_limit,
                })
            elif ongoing and current is not None:
                current['peak_cpu'] = max(float(current.get('peak_cpu') or 0), round(float(cpu), 1))
                current['peak_mem'] = max(float(current.get('peak_mem') or 0), round(float(mem), 1))
            elif recover and current is not None:
                current['end'] = now
                current['duration'] = now - int(current.get('start') or now)
            history = history[-ALERT_MAX_RECORDS:]
            self.plugin.save_data(ALERT_KEY, history)
        except Exception as e:
            logger.debug(f"{self.plugin_name} 记录告警事件失败: {e}")

    def get_alert_history(self, limit: int = 30) -> Dict[str, Any]:
        """最近告警记录（新的在前），并附带启用状态与阈值"""
        history = self._load_alert_history()
        items = [r for r in history if isinstance(r, dict)]
        items.sort(key=lambda r: int(r.get('start') or 0), reverse=True)
        active = next((r for r in items if not r.get('end')), None)
        return {
            'ok': True,
            'items': items[:limit],
            'total': len(items),
            'active': active,
            'enabled': bool(getattr(self.plugin, '_load_warn_enable', False)),
            'cpu_threshold': float(getattr(self.plugin, '_load_cpu_threshold', 90) or 90),
            'mem_threshold': float(getattr(self.plugin, '_load_mem_threshold', 90) or 90),
        }

    def clear_alert_history(self) -> Dict[str, Any]:
        """清空告警记录"""
        try:
            self.plugin.save_data(ALERT_KEY, [])
            return {'ok': True, 'msg': '告警记录已清空'}
        except Exception as e:
            logger.error(f"{self.plugin_name} 清空告警记录失败: {e}")
            return {'ok': False, 'error': str(e)}

    # ---------- 测试连接 ----------

    def test_connection(self) -> Dict[str, Any]:
        """测试爱快连接，返回基本状态供配置页展示"""
        error = self._require_config(self.plugin)
        if error:
            return {'ok': False, 'error': error}
        try:
            client = self._get_client()
            if not client.login():
                return {'ok': False, 'error': '登录失败，请检查地址、账号密码或令牌'}
            system_info = client.get_system_info() or {}
            auth_mode = (getattr(self.plugin, '_ikuai_auth_mode', 'auto') or 'auto').lower()
            token_ok = False
            if auth_mode != "password" and (getattr(self.plugin, '_ikuai_api_token', '') or '').strip():
                try:
                    token_ok = bool(client._v4 and client._v4.validate())
                except Exception:
                    token_ok = False
            return {
                'ok': True,
                'error': '',
                'hostname': system_info.get("hostname", ""),
                'version': system_info.get("version", ""),
                'auth_mode': auth_mode,
                'token_ok': token_ok,
            }
        except Exception as e:
            return {'ok': False, 'error': str(e)}
