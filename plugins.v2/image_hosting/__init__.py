from typing import Any, Dict, List, Optional
from pathlib import Path
import os
import json
import requests
from app.core.config import settings
from app.log import logger
from app.plugins import PluginBase
from app.schemas.types import EventType, NotificationType
from app.utils.http import RequestUtils
from app.utils.string import StringUtils

class ImageHostingPlugin(PluginBase):
    # 插件名称
    plugin_name = "图床助手"
    # 插件描述
    plugin_desc = "支持多种图床服务的图片上传插件"
   # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/ikuai.png"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "imagehosting_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    def __init__(self):
        super().__init__()
        # 图床配置
        self._hosting_config = {}
        # 当前使用的图床
        self._current_hosting = None
        # 图床列表
        self._hosting_list = {
            "smms": {
                "name": "SM.MS",
                "url": "https://sm.ms/api/v2/upload",
                "token": "",
                "headers": {
                    "Authorization": ""
                }
            },
            "imgur": {
                "name": "Imgur",
                "url": "https://api.imgur.com/3/image",
                "client_id": "",
                "headers": {
                    "Authorization": "Client-ID "
                }
            }
        }

    def init_plugin(self, config: dict = None):
        """
        初始化插件
        """
        if config:
            self._hosting_config = config
            # 设置当前使用的图床
            self._current_hosting = config.get("current_hosting")
            # 更新图床配置
            for hosting in self._hosting_list:
                if hosting in config:
                    self._hosting_list[hosting].update(config[hosting])

    def get_state(self) -> bool:
        """
        获取插件状态
        """
        return True

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        定义插件命令
        """
        return [{
            "cmd": "/upload_image",
            "event": EventType.PluginAction,
            "desc": "上传图片到图床",
            "category": "图床",
            "data": {
                "action": "upload_image"
            }
        }]

    def get_api(self) -> List[Dict[str, Any]]:
        """
        获取插件API
        """
        return [{
            "path": "/upload",
            "endpoint": self.upload_image,
            "methods": ["POST"],
            "summary": "上传图片",
            "description": "上传图片到图床"
        }]

    def get_form(self) -> List[Dict[str, Any]]:
        """
        获取插件配置页面
        """
        return [{
            "component": "VForm",
            "content": [
                {
                    "component": "VSelect",
                    "props": {
                        "model": "current_hosting",
                        "label": "选择图床",
                        "items": [
                            {"title": v["name"], "value": k}
                            for k, v in self._hosting_list.items()
                        ]
                    }
                },
                {
                    "component": "VTextField",
                    "props": {
                        "model": "smms.token",
                        "label": "SM.MS Token",
                        "placeholder": "请输入SM.MS的API Token"
                    }
                },
                {
                    "component": "VTextField",
                    "props": {
                        "model": "imgur.client_id",
                        "label": "Imgur Client ID",
                        "placeholder": "请输入Imgur的Client ID"
                    }
                }
            ]
        }]

    def upload_image(self, image_path: str) -> Optional[str]:
        """
        上传图片到图床
        :param image_path: 图片路径
        :return: 图片URL
        """
        if not self._current_hosting:
            logger.error("未选择图床")
            return None

        hosting = self._hosting_list.get(self._current_hosting)
        if not hosting:
            logger.error(f"图床 {self._current_hosting} 不存在")
            return None

        try:
            # 读取图片文件
            with open(image_path, 'rb') as f:
                files = {'smfile' if self._current_hosting == 'smms' else 'image': f}
                
                # 发送请求
                response = requests.post(
                    hosting["url"],
                    headers=hosting["headers"],
                    files=files
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if self._current_hosting == 'smms':
                        return result.get('data', {}).get('url')
                    elif self._current_hosting == 'imgur':
                        return result.get('data', {}).get('link')
                else:
                    logger.error(f"上传失败: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"上传图片失败: {str(e)}")
            return None

    def stop_service(self):
        """
        停止插件
        """
        pass 