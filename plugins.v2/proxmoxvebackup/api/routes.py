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
            "path": "/config",
            "endpoint": api_handler._get_config,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取插件配置"
        },
        {
            "path": "/config",
            "endpoint": api_handler._save_config,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "保存插件配置"
        },
        {
            "path": "/status",
            "endpoint": api_handler._get_status,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取插件运行状态"
        },
        {
            "path": "/backup_history",
            "endpoint": api_handler._get_backup_history,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取备份历史记录"
        },
        {
            "path": "/restore_history",
            "endpoint": api_handler._get_restore_history,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取恢复历史记录"
        },
        {
            "path": "/dashboard_data",
            "endpoint": api_handler._get_dashboard_data,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取仪表板数据"
        },
        {
            "path": "/run_backup",
            "endpoint": api_handler._run_backup,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "手动启动备份任务"
        },
        {
            "path": "/clear_history",
            "endpoint": api_handler._clear_history_api,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "清理备份和恢复历史"
        },
        {
            "path": "/pve_status",
            "endpoint": api_handler._get_pve_status_api,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取PVE主机状态"
        },
        {
            "path": "/container_status",
            "endpoint": api_handler._get_container_status_api,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取所有LXC容器状态"
        },
        {
            "path": "/available_backups",
            "endpoint": api_handler._get_available_backups_api,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取可用备份文件列表"
        },
        {
            "path": "/delete_backup",
            "endpoint": api_handler._delete_backup_api,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "删除备份文件"
        },
        {
            "path": "/restore",
            "endpoint": api_handler._restore_backup_api,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "恢复备份文件"
        },
        {
            "path": "/download_backup",
            "endpoint": api_handler._download_backup_api,
            "methods": ["GET"],
            "summary": "下载本地备份文件"
        },
        {
            "path": "/token",
            "endpoint": api_handler._get_token,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "获取API令牌"
        },
        {
            "path": "/container_action",
            "endpoint": api_handler._container_action_api,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "对指定虚拟机/容器执行操作"
        },
        {
            "path": "/container_snapshot",
            "endpoint": api_handler._container_snapshot_api,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "对指定虚拟机/容器创建快照"
        },
        {
            "path": "/host_action",
            "endpoint": api_handler._host_action_api,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "对PVE主机执行重启或关机"
        },
        {
            "path": "/cleanup_logs",
            "endpoint": api_handler._cleanup_logs_api,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "清理PVE系统日志"
        },
        {
            "path": "/cleanup_tmp",
            "endpoint": api_handler._cleanup_tmp_api,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "清理PVE临时空间"
        },
        {
            "path": "/template_images",
            "endpoint": api_handler._template_images_api,
            "methods": ["GET"],
            "auth": "bear",
            "summary": "列出所有CT模板和ISO镜像"
        },
        {
            "path": "/stop_all_tasks",
            "endpoint": api_handler._stop_all_tasks_api,
            "methods": ["POST"],
            "auth": "bear",
            "summary": "停止所有正在运行的任务"
        },
    ]

