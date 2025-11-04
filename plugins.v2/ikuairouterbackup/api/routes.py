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
        },
        {
            "path": "/restore",
            "endpoint": api_handler.restore_backup,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "执行恢复"
        },
        {
            "path": "/sync_ip_groups",
            "endpoint": api_handler.sync_ip_groups,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "同步IP分组"
        },
        {
            "path": "/get_ip_blocks_info",
            "endpoint": api_handler.get_ip_blocks_info,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取IP段信息"
        },
        {
            "path": "/get_available_options",
            "endpoint": api_handler.get_available_options,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取可用选项"
        },
        {
            "path": "/get_cities_by_province",
            "endpoint": api_handler.get_cities_by_province,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "根据省份获取城市列表"
        },
        {
            "path": "/test_ip_group",
            "endpoint": api_handler.test_ip_group,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "测试IP分组创建"
        }
    ]

