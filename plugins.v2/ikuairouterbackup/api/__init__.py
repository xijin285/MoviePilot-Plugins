"""
API模块
包含API路由和处理功能
"""
from .routes import get_api_routes
from .handlers import APIHandler

__all__ = ['get_api_routes', 'APIHandler']

