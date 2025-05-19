from typing import Any, Dict, Optional
from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType
from app.utils.http import RequestUtils
import json
import os
import base64
from datetime import datetime

class ImageHosting(_PluginBase):
    # 插件名称
    plugin_name = "图床上传助手"
    # 插件描述
    plugin_desc = "支持多种图床的图片上传功能"
    # 插件图标
    plugin_icon = "sitemonitor.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285/MoviePilot-Plugins/"
    # 插件配置项ID前缀
    plugin_config_prefix = "imagehosting_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    def __init__(self):
        super().__init__()
        self._enabled = False
        self._config = {}

    def init_plugin(self, config: dict = None):
        if config:
            self._config = config
            self._enabled = config.get("enabled", False)

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> list:
        pass

    def get_api(self) -> list:
        return [
            {
                "path": "/upload",
                "endpoint": self.upload_image,
                "methods": ["POST"],
                "summary": "上传图片",
                "description": "上传图片到图床"
            }
        ]

    def upload_image(self, image_data: str) -> Dict[str, Any]:
        """
        上传图片到图床
        """
        try:
            # 这里实现具体的图床上传逻辑
            # 示例：使用 SM.MS 图床
            api_url = "https://sm.ms/api/v2/upload"
            headers = {
                "Authorization": self._config.get("api_token", "")
            }
            
            # 将base64图片数据转换为文件
            image_bytes = base64.b64decode(image_data)
            
            files = {
                "smfile": ("image.jpg", image_bytes)
            }
            
            response = RequestUtils(headers=headers).post(api_url, files=files)
            
            if response and response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return {
                        "success": True,
                        "url": result.get("data", {}).get("url", ""),
                        "message": "上传成功"
                    }
            
            return {
                "success": False,
                "message": "上传失败"
            }
            
        except Exception as e:
            logger.error(f"图床上传失败: {str(e)}")
            return {
                "success": False,
                "message": f"上传失败: {str(e)}"
            }

    def get_form(self) -> tuple[list, dict]:
        """
        拼装插件配置页面，需要返回两个数据：1、页面配置；2、数据结构
        """
        return [
            {
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
                                        "component": "VTextField",
                                        "props": {
                                            "model": "api_token",
                                            "label": "API Token",
                                            "placeholder": "请输入图床API Token"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "api_token": ""
        }

    def get_page(self) -> list:
        pass

    def stop_service(self):
        """
        停止服务
        """
        pass 