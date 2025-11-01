"""
API模块
包含API路由和命令配置
"""
from .routes import get_api_routes
from .commands import get_plugin_commands
from .handlers import APIHandler

__all__ = ['get_api_routes', 'get_plugin_commands', 'APIHandler']

