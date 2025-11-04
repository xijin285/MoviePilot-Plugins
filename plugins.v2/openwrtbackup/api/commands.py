"""
API命令定义（消息渠道命令）
将所有命令配置集中管理，便于维护
"""
from typing import List, Dict, Any
from app.schemas.types import EventType
from app.log import logger


def get_plugin_commands() -> List[Dict[str, Any]]:
    """
    获取所有插件命令配置
        
    Returns:
        命令配置列表
    """
    commands = [
        {
            "cmd": "/op帮助",
            "event": EventType.PluginAction,
            "desc": "查看OpenWrt插件命令帮助",
            "category": "OpenWrt路由",
            "data": {
                "action": "openwrt_help"
            }
        },
        {
            "cmd": "/op状态",
            "event": EventType.PluginAction,
            "desc": "查看OpenWrt路由器系统状态",
            "category": "OpenWrt路由",
            "data": {
                "action": "openwrt_status"
            }
        },
        {
            "cmd": "/op流量",
            "event": EventType.PluginAction,
            "desc": "查看OpenWrt路由器网络流量",
            "category": "OpenWrt路由",
            "data": {
                "action": "openwrt_traffic"
            }
        },
        {
            "cmd": "/op备份",
            "event": EventType.PluginAction,
            "desc": "立即执行备份任务",
            "category": "OpenWrt路由",
            "data": {
                "action": "openwrt_backup"
            }
        }
    ]
    
    logger.debug(f"OpenWrt路由助手 注册了 {len(commands)} 个命令（仅带斜杠格式）")
    
    return commands

