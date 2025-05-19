from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import random
import os
from datetime import datetime

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType, NotificationType
from app.utils.http import RequestUtils


class RandomPicPlugin(_PluginBase):
    # 插件名称
    plugin_name = "随机图片API"
    # 插件描述
    plugin_desc = "提供随机图片API服务，支持横竖屏图片分类。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/madrays/MoviePilot-Plugins/main/icons/random.png"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "xijin285"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    _config_prefix = "random_pic_"
    # 加载顺序
    plugin_order = 25
    # 可使用的用户级别
    user_level = 1

    # 私有属性
    _enabled = False
    _notify = False
    _pc_dir = None
    _mobile_dir = None

    def init_plugin(self, config: dict = None):
        """初始化插件"""
        if config:
            self._enabled = config.get("enabled")
            self._notify = config.get("notify")
            
        # 创建图片目录
        self._pc_dir = Path(settings.DATA_PATH) / "random_pic" / "pc"
        self._mobile_dir = Path(settings.DATA_PATH) / "random_pic" / "mobile"
        
        # 确保目录存在
        self._pc_dir.mkdir(parents=True, exist_ok=True)
        self._mobile_dir.mkdir(parents=True, exist_ok=True)

    def get_state(self) -> bool:
        """获取插件状态"""
        return self._enabled

    def stop_service(self):
        """停止插件"""
        pass

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """获取插件命令"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """获取插件API"""
        return [
            {
                "path": "/random",
                "endpoint": self.api_route,
                "methods": ["GET"],
                "summary": "获取随机图片",
                "description": "获取随机图片，支持横竖屏分类"
            }
        ]

    def get_service(self) -> List[Dict[str, Any]]:
        """获取插件服务"""
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """获取插件配置页面"""
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'notify',
                                            'label': '发送通知',
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
            "notify": False
        }

    def get_page(self) -> List[dict]:
        """获取插件页面"""
        return []

    def api_route(self, **kwargs) -> dict:
        """API路由"""
        if not self._enabled:
            return {"error": "Plugin is disabled"}
            
        # 获取设备类型
        device_type = kwargs.get("type", "pc")
        if device_type not in ["pc", "mobile"]:
            return {"error": "Invalid device type"}
            
        # 获取随机图片
        image_url = self.get_random_pic(device_type)
        if not image_url:
            return {"error": "No images available"}
            
        # 发送通知
        if self._notify:
            self.send_notify(device_type)
            
        return {"url": image_url}

    def get_random_pic(self, device_type: str) -> Optional[str]:
        """获取随机图片"""
        # 选择目录
        target_dir = self._pc_dir if device_type == "pc" else self._mobile_dir
        
        # 获取所有图片文件
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            image_files.extend(list(target_dir.glob(f'*{ext}')))
            
        if not image_files:
            return None
            
        # 随机选择一张图片
        random_image = random.choice(image_files)
        return str(random_image.relative_to(settings.DATA_PATH))

    def send_notify(self, device_type: str):
        """发送通知"""
        self.post_message(
            mtype=NotificationType.Plugin,
            title="随机图片API",
            text=f"获取了一张{'横屏' if device_type == 'pc' else '竖屏'}图片"
        ) 