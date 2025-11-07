"""
API命令定义（微信消息命令）
将所有命令配置集中管理，便于维护
"""
from typing import List, Dict, Any
from app.schemas.types import EventType


def get_plugin_commands() -> List[Dict[str, Any]]:
    """
    获取所有插件命令配置
    只保留三个核心命令：/pve_status、/pve_containers、/pve_help
    
    Returns:
        命令配置列表
    """
    return [
        {
            "cmd": "/pve_status",
            "event": EventType.PluginAction,
            "desc": "查看PVE主机状态信息",
            "category": "PVE",
            "data": {
                "action": "pve_status"
            }
        },
        {
            "cmd": "/pve_containers",
            "event": EventType.PluginAction,
            "desc": "查看所有容器/虚拟机状态",
            "category": "PVE",
            "data": {
                "action": "container_status"
            }
        },
        {
            "cmd": "/pve_help",
            "event": EventType.PluginAction,
            "desc": "查看PVE插件命令帮助",
            "category": "PVE",
            "data": {
                "action": "pve_help"
            }
        }
    ]

