"""
OpenWrt状态获取模块
负责获取系统状态、接口状态、流量统计和服务状态（通过HTTP API）
"""
from typing import Optional, Dict, List

from .http_status import OpenWrtHTTPStatus


class OpenWrtStatus:
    """OpenWrt状态获取类（HTTP方式）"""
    
    def __init__(self, plugin_instance):
        """
        初始化OpenWrt状态获取器
        :param plugin_instance: OpenWrtBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        self.http_status = OpenWrtHTTPStatus(plugin_instance)
    
    def get_system_status(self) -> Optional[Dict]:
        """获取系统状态信息"""
        return self.http_status.get_system_status()
    
    def get_traffic_stats(self) -> Optional[List[Dict]]:
        """获取网络流量"""
        return self.http_status.get_traffic_stats()
    
    def get_plugin_services(self) -> Optional[List[Dict]]:
        """获取LuCI插件服务状态"""
        return self.http_status.get_plugin_services()