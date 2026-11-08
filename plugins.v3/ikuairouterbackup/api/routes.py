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
        },
        # ---------- Vue 前端接口 ----------
        {
            "path": "/config",
            "endpoint": api_handler.get_config,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取配置"
        },
        {
            "path": "/config",
            "endpoint": api_handler.save_config,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "保存配置"
        },
        {
            "path": "/status",
            "endpoint": api_handler.get_status,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "实时监控状态"
        },
        {
            "path": "/devices",
            "endpoint": api_handler.get_devices,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "在线设备列表"
        },
        {
            "path": "/logs",
            "endpoint": api_handler.get_logs,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "系统日志"
        },
        {
            "path": "/trend",
            "endpoint": api_handler.get_trend,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "负载流量趋势"
        },
        {
            "path": "/protocol_flow",
            "endpoint": api_handler.get_protocol_flow,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "协议流量分布"
        },
        {
            "path": "/monitor_view",
            "endpoint": api_handler.get_monitor_view,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "监控面板多视图"
        },
        {
            "path": "/alert_history",
            "endpoint": api_handler.get_alert_history,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "负载告警记录"
        },
        {
            "path": "/alert_history",
            "endpoint": api_handler.clear_alert_history,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "清空负载告警记录"
        },
        {
            "path": "/dashboard_layout",
            "endpoint": api_handler.get_dashboard_layout,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取仪表盘布局"
        },
        {
            "path": "/dashboard_layout",
            "endpoint": api_handler.save_dashboard_layout,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "保存仪表盘布局"
        },
        {
            "path": "/available_backups",
            "endpoint": api_handler.get_available_backups,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "可恢复备份列表"
        },
        {
            "path": "/download_backup",
            "endpoint": api_handler.download_backup,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "下载备份文件（base64）"
        },
        {
            "path": "/delete_backup",
            "endpoint": api_handler.delete_backup,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "删除备份文件"
        },
        {
            "path": "/histories",
            "endpoint": api_handler.get_histories,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "备份恢复历史"
        },
        {
            "path": "/list_dir",
            "endpoint": api_handler.list_dir,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "浏览本地目录"
        },
        {
            "path": "/test",
            "endpoint": api_handler.test_connection,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "测试爱快连接"
        },
    ]

