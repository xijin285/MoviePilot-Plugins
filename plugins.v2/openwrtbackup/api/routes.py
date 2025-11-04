"""
API路由定义
将所有API端点配置集中管理，便于维护
"""
from typing import List, Dict, Any


def get_api_routes(plugin_instance) -> List[Dict[str, Any]]:
    """
    获取所有API路由配置
    
    Args:
        plugin_instance: 插件实例，用于绑定endpoint方法
        
    Returns:
        API路由配置列表
    """
    from .handlers import APIHandler
    api_handler = APIHandler(plugin_instance)
    
    return [
        {
            "path": "/backup",
            "endpoint": api_handler.backup,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "执行备份"
        }
    ]

