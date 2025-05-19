from typing import Any, Dict, List, Optional
from pathlib import Path
import random
import aiohttp
import asyncio
from app.core.config import settings
from app.log import logger
from app.plugins import PluginBase
from app.schemas.types import EventType, Event
from app.utils.http import RequestUtils

class RandomApi(PluginBase):
    # 插件名称
    plugin_name = "随机图片API"
    # 插件描述
    plugin_desc = "提供随机图片API服务，支持多个图片源"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "randomapi_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    def __init__(self):
        super().__init__()
        self._enabled = False
        self._api_urls = {
            "unsplash": "https://api.unsplash.com/photos/random",
            "picsum": "https://picsum.photos/800/600",
            "randomuser": "https://randomuser.me/api/portraits/men/1.jpg"
        }
        self._current_api = "picsum"  # 默认使用picsum

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        定义插件命令
        """
        return [{
            "cmd": "/randompic",
            "event": EventType.PluginAction,
            "desc": "获取随机图片",
            "category": "图片",
            "data": {
                "action": "get_random_pic"
            }
        }]

    def get_api(self) -> List[Dict[str, Any]]:
        """
        获取插件API
        """
        return [{
            "path": "/api/v1/randompic",
            "endpoint": self.get_random_pic,
            "methods": ["GET"],
            "summary": "获取随机图片",
            "description": "返回一个随机图片URL"
        }]

    async def get_random_pic(self) -> Dict[str, Any]:
        """
        获取随机图片
        """
        try:
            api_url = self._api_urls.get(self._current_api)
            if not api_url:
                return {
                    "code": -1,
                    "msg": "未配置有效的API地址",
                    "data": None
                }

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        if self._current_api == "picsum":
                            return {
                                "code": 0,
                                "msg": "success",
                                "data": {
                                    "url": str(response.url)
                                }
                            }
                        else:
                            data = await response.json()
                            return {
                                "code": 0,
                                "msg": "success",
                                "data": data
                            }
                    else:
                        return {
                            "code": -1,
                            "msg": f"获取图片失败: HTTP {response.status}",
                            "data": None
                        }
        except Exception as e:
            logger.error(f"获取随机图片失败: {str(e)}")
            return {
                "code": -1,
                "msg": f"获取图片失败: {str(e)}",
                "data": None
            }

    def get_form(self) -> List[Dict[str, Any]]:
        """
        获取插件配置页面
        """
        return [{
            "component": "VForm",
            "content": [
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {
                                "cols": 12,
                                "md": 6
                            },
                            "content": [
                                {
                                    "component": "VSwitch",
                                    "props": {
                                        "model": "enabled",
                                        "label": "启用插件",
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "component": "VRow",
                    "content": [
                        {
                            "component": "VCol",
                            "props": {
                                "cols": 12,
                                "md": 6
                            },
                            "content": [
                                {
                                    "component": "VSelect",
                                    "props": {
                                        "model": "api_source",
                                        "label": "图片源",
                                        "items": [
                                            {"title": "Picsum", "value": "picsum"},
                                            {"title": "Unsplash", "value": "unsplash"},
                                            {"title": "RandomUser", "value": "randomuser"}
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }]

    def get_page(self) -> List[Dict[str, Any]]:
        """
        获取插件页面
        """
        return []

    def stop_service(self):
        """
        停止插件
        """
        self._enabled = False

    def start_service(self):
        """
        启动插件
        """
        self._enabled = True 