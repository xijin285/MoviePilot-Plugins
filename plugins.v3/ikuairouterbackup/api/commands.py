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
            "cmd": "/ikuai_help",
            "event": EventType.PluginAction,
            "desc": "查看爱快插件命令帮助",
            "category": "爱快路由",
            "data": {
                "action": "ikuai_help"
            }
        },
        {
            "cmd": "/ikuai_status",
            "event": EventType.PluginAction,
            "desc": "查看爱快路由器系统状态",
            "category": "爱快路由",
            "data": {
                "action": "ikuai_status"
            }
        },
        {
            "cmd": "/ikuai_line",
            "event": EventType.PluginAction,
            "desc": "查看爱快路由器线路监控状态",
            "category": "爱快路由",
            "data": {
                "action": "ikuai_line"
            }
        },
        {
            "cmd": "/ikuai_list",
            "event": EventType.PluginAction,
            "desc": "查看备份文件列表",
            "category": "爱快路由",
            "data": {
                "action": "ikuai_list"
            }
        },
        {
            "cmd": "/ikuai_history",
            "event": EventType.PluginAction,
            "desc": "查看备份历史记录",
            "category": "爱快路由",
            "data": {
                "action": "ikuai_history"
            }
        },
        {
            "cmd": "/ikuai_backup",
            "event": EventType.PluginAction,
            "desc": "立即执行备份任务",
            "category": "爱快路由",
            "data": {
                "action": "ikuai_backup"
            }
        }
    ]
    
    logger.debug(f"爱快路由时光机 注册了 {len(commands)} 个命令（仅带斜杠格式）")
    
    return commands

