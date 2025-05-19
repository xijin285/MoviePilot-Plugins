from typing import Any, Dict, List, Optional
from pathlib import Path
import random
import os
from app.core.config import settings
from app.log import logger
from app.plugins import PluginBase
from app.schemas.types import EventType, Event

class RandomApi(PluginBase):
    # 插件名称
    plugin_name = "随机图片API"
    # 插件描述
    plugin_desc = "提供随机图片API服务"
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
        self._image_dir = os.path.join(os.path.dirname(__file__), "images")
        # 确保图片目录存在
        if not os.path.exists(self._image_dir):
            os.makedirs(self._image_dir)

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

    def get_random_pic(self) -> Dict[str, Any]:
        """
        获取随机图片
        """
        try:
            # 获取图片目录下的所有图片文件
            image_files = [f for f in os.listdir(self._image_dir) 
                         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
            
            if not image_files:
                return {
                    "code": -1,
                    "msg": "图片目录为空",
                    "data": None
                }

            # 随机选择一张图片
            random_image = random.choice(image_files)
            image_path = os.path.join(self._image_dir, random_image)
            
            # 返回图片URL
            return {
                "code": 0,
                "msg": "success",
                "data": {
                    "url": f"/api/v1/randompic/image/{random_image}"
                }
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