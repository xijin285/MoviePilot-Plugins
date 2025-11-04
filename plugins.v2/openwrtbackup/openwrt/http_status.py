"""
OpenWrt HTTP状态获取模块
负责通过HTTP API获取系统状态、流量统计和服务状态
"""
import re
from typing import Optional, Dict, List
from app.log import logger

from .http_client import OpenWrtHTTPClient


class OpenWrtHTTPStatus:
    """OpenWrt HTTP状态获取类"""
    
    def __init__(self, plugin_instance):
        """
        初始化OpenWrt HTTP状态获取器
        :param plugin_instance: OpenWrtBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        self.http_client = OpenWrtHTTPClient(plugin_instance)
    
    def _ensure_connected(self) -> bool:
        """确保已连接"""
        # 如果session或auth_token不存在，直接登录
        if not self.http_client.session or not self.http_client.auth_token:
            success, error = self.http_client.login()
            if not success:
                logger.error(f"{self.plugin_name} HTTP连接失败: {error}")
                return False
            return True
        
        # 如果已存在session，先尝试一个简单的RPC调用来验证是否有效
        # 如果RPC调用失败（可能是session过期），则重新登录
        try:
            test_result = self.http_client._call_rpc('system', 'board', {})
            if test_result is None:
                # RPC调用失败，可能是session过期，重新登录
                logger.debug(f"{self.plugin_name} 检测到session可能过期，重新登录...")
                self.http_client.session = None
                self.http_client.auth_token = None
                success, error = self.http_client.login()
                if not success:
                    logger.error(f"{self.plugin_name} HTTP重新连接失败: {error}")
                    return False
        except Exception as e:
            # 如果测试调用异常，也重新登录
            logger.debug(f"{self.plugin_name} 连接测试异常，重新登录: {e}")
            self.http_client.session = None
            self.http_client.auth_token = None
            success, error = self.http_client.login()
            if not success:
                logger.error(f"{self.plugin_name} HTTP重新连接失败: {error}")
                return False
        
        return True
    
    def get_system_status(self) -> Optional[Dict]:
        """获取系统状态信息"""
        if not self._ensure_connected():
            return None
        
        try:
            status = {}
            
            # 获取系统信息
            result = self.http_client._call_rpc('system', 'info', {})
            if result:
                # 解析系统信息
                if 'uptime' in result:
                    uptime_seconds = result['uptime']
                    days = int(uptime_seconds // 86400)
                    hours = int((uptime_seconds % 86400) // 3600)
                    minutes = int((uptime_seconds % 3600) // 60)
                    if days > 0:
                        status['uptime'] = f"{days}天{hours}小时{minutes}分钟"
                    else:
                        status['uptime'] = f"{hours}小时{minutes}分钟"
                    status['uptime_seconds'] = int(uptime_seconds)
                
                if 'load' in result:
                    load = result['load']
                    if isinstance(load, list) and len(load) >= 3:
                        # ubus返回的load值是固定点格式，需要除以65536
                        load_1min = load[0] / 65536.0 if isinstance(load[0], (int, float)) else float(load[0])
                        load_5min = load[1] / 65536.0 if isinstance(load[1], (int, float)) else float(load[1])
                        load_15min = load[2] / 65536.0 if isinstance(load[2], (int, float)) else float(load[2])
                        
                        status['load_1min'] = f"{load_1min:.2f}".rstrip('0').rstrip('.')
                        status['load_5min'] = f"{load_5min:.2f}".rstrip('0').rstrip('.')
                        status['load_15min'] = f"{load_15min:.2f}".rstrip('0').rstrip('.')
                
                if 'memory' in result:
                    memory = result['memory']
                    if isinstance(memory, dict):
                        total = memory.get('total', 0)
                        free = memory.get('free', 0)
                        cached = memory.get('cached', 0)
                        buffered = memory.get('buffered', 0)
                        used = total - free - cached - buffered
                        
                        status['memory_total'] = total // (1024 * 1024)  # 转换为MB
                        status['memory_used'] = used // (1024 * 1024)
                        status['memory_free'] = free // (1024 * 1024)
                        status['memory_usage'] = round((used / total * 100), 1) if total > 0 else 0
                
                if 'swap' in result:
                    swap = result['swap']
                    if isinstance(swap, dict):
                        swap_total = swap.get('total', 0)
                        swap_free = swap.get('free', 0)
                        swap_used = swap_total - swap_free
                        status['swap_total'] = swap_total // (1024 * 1024)
                        status['swap_used'] = swap_used // (1024 * 1024)
                        status['swap_usage'] = round((swap_used / swap_total * 100), 1) if swap_total > 0 else 0
            
            # 获取CPU使用率
            cpu_usage_result = self.http_client._call_rpc('luci', 'getCPUUsage', {})
            if cpu_usage_result and isinstance(cpu_usage_result, dict):
                cpuusage_str = cpu_usage_result.get('cpuusage', '')
                if cpuusage_str:
                    # 提取百分比数值，如 "0%" -> 0
                    cpu_match = re.search(r'(\d+\.?\d*)%', cpuusage_str)
                    if cpu_match:
                        status['cpu_usage'] = round(float(cpu_match.group(1)), 1)
            
            # 获取系统版本
            luci_version = self.http_client._call_rpc('luci', 'getVersion', {})
            if luci_version and isinstance(luci_version, dict):
                revision = luci_version.get('revision', '')
                branch = luci_version.get('branch', '')
                # 格式化版本信息：branch (revision)
                if revision and branch:
                    status['version'] = f"{branch} ({revision})"
                elif revision:
                    status['version'] = revision
                elif branch:
                    status['version'] = branch
            
            # 获取板子信息（包含内核版本和架构信息）
            board_result = self.http_client._call_rpc('system', 'board', {})
            if board_result and isinstance(board_result, dict):
                # 获取内核版本（从board中获取）
                if 'kernel' in board_result:
                    status['kernel'] = board_result['kernel']
                
                # 获取架构信息
                board_name = board_result.get('board_name', '')
                model = board_result.get('model', '')
                system = board_result.get('system', '')
                
                arch_parts = []
                if board_name:
                    arch_parts.append(board_name)
                if model:
                    arch_parts.append(model)
                if system:
                    arch_parts.append(system)
                
                if arch_parts:
                    status['architecture'] = ' / '.join(arch_parts)
            
            # 获取温度信息
            temp_result = self.http_client._call_rpc('luci', 'getTempInfo', {})
            if temp_result and isinstance(temp_result, dict):
                tempinfo_str = temp_result.get('tempinfo', '')
                if tempinfo_str:
                    status['temperature'] = tempinfo_str
                else:
                    status['temperature'] = 'N/A'
            else:
                status['temperature'] = 'N/A'
            
            return status
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取系统状态失败: {e}")
            return None
    
    def get_traffic_stats(self) -> Optional[List[Dict]]:
        """获取网络流量（按设备显示）"""
        if not self._ensure_connected():
            return None
        
        try:
            traffic_stats = []
            
            # 使用ubus luci.wrtbwmon.get_db_raw获取流量数据
            result = self.http_client._call_rpc('luci.wrtbwmon', 'get_db_raw', {'protocol': 'ipv4'})
            if result and isinstance(result, dict):
                data_content = result.get('data', '')
                if isinstance(data_content, str):
                    # 解析CSV格式的数据
                    # 格式: #mac,ip,iface,speed_in,speed_out,in,out,total,first_date,last_date
                    lines = data_content.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        # 跳过空行和注释行
                        if not line or line.startswith('#'):
                            continue
                        
                        # 解析CSV行: mac,ip,iface,speed_in,speed_out,in,out,total,first_date,last_date
                        parts = line.split(',')
                        if len(parts) >= 9:
                            try:
                                mac = parts[0]  # MAC地址
                                ip = parts[1] if parts[1] != 'NA' else ''  # IP地址
                                iface = parts[2]  # 接口名称
                                in_bytes = int(parts[5]) if parts[5] else 0  # 下行流量（字节）
                                out_bytes = int(parts[6]) if parts[6] else 0  # 上行流量（字节）
                                
                                # 按设备显示，使用MAC地址作为设备标识
                                rx_mb = round(in_bytes / (1024 * 1024), 2)
                                tx_mb = round(out_bytes / (1024 * 1024), 2)
                                
                                # 设备名称：优先使用IP，如果没有则使用MAC地址
                                device_name = ip if ip else mac
                                
                                traffic_stats.append({
                                    'interface': device_name,  # 使用设备名称作为显示标识
                                    'mac': mac,  # MAC地址
                                    'ip': ip,  # IP地址
                                    'iface': iface,  # 所属接口
                                    'rx_bytes': in_bytes,
                                    'rx_mb': rx_mb,
                                    'rx_packets': 0,  # wrtbwmon不提供包数统计
                                    'tx_bytes': out_bytes,
                                    'tx_mb': tx_mb,
                                    'tx_packets': 0   # wrtbwmon不提供包数统计
                                })
                            except (ValueError, IndexError):
                                continue
            
            # 按流量总量排序（降序）
            traffic_stats.sort(key=lambda x: x['rx_bytes'] + x['tx_bytes'], reverse=True)
            
            return traffic_stats
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取流量统计失败: {e}")
            return None
    
    def get_plugin_services(self) -> Optional[List[Dict]]:
        """获取LuCI插件服务状态"""
        if not self._ensure_connected():
            return None
        
        try:
            plugin_services = []
            
            # 已知的LuCI插件服务名称关键词
            plugin_keywords = [
                'lucky', 'nikki', 'nps', 'snmpd', 'turboacc', 'eqos',
                'wrtbwmon', 'design', 'adguard', 'passwall', 'openclash',
                'vssr', 'ssr-plus', 'shadowsocks', 'v2ray', 'xray'
            ]
            
            # 使用ubus rc.list获取服务列表
            rc_result = self.http_client._call_rpc('rc', 'list', {})
            if rc_result and isinstance(rc_result, dict):
                # rc.list返回格式: {'service_name': {'start': 80, 'enabled': True, 'running': True}, ...}
                for service_name, service_info in rc_result.items():
                    if isinstance(service_info, dict):
                        # 检查服务名是否包含插件关键词
                        service_name_lower = service_name.lower()
                        is_plugin = any(keyword in service_name_lower for keyword in plugin_keywords)
                        
                        if is_plugin:
                            is_enabled = service_info.get('enabled', False)
                            is_running = service_info.get('running', False)
                            
                            # 只显示已启用或正在运行的插件服务
                            if is_enabled or is_running:
                                plugin_services.append({
                                    'name': service_name,
                                    'enabled': is_enabled,
                                    'running': is_running,
                                    'status': '运行中' if is_running else '已停止'
                                })
                
                # 按服务名排序
                plugin_services.sort(key=lambda x: x['name'])
            
            return plugin_services
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取插件服务状态失败: {e}")
            return None

