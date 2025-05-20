import os
import random
from typing import List, Dict, Any
from flask import Flask, send_file
from pathlib import Path

from app.core.config import settings
from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import PluginBase
from app.schemas import NotificationType

class RandomPicApi(PluginBase):
    # 插件名称
    plugin_name = "本地图片API"
    # 插件描述
    plugin_desc = "将本地图片文件夹映射为随机图片API服务，支持通过MoviePilot接口访问"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/main/icons/random.png"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    _config_prefix = "random_pic_api_"
    # 加载顺序
    plugin_order = 18
    # 可使用的用户级别
    user_level = 2

    # 私有属性
    _enabled = False
    _notify = False

    # Flask应用
    app = Flask(__name__)

    # 获取插件根目录
    PLUGIN_ROOT = Path(__file__).parent
    # 图片目录
    IMAGES_DIR = PLUGIN_ROOT / "images"

    def init_plugin(self, config: Dict[str, Any] = None):
        """插件初始化"""
        if config:
            self._enabled = config.get("enabled", False)
            self._notify = config.get("notify", False)
            self.__update_config()

        try:
            # 确保图片目录存在
            self.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"{self.plugin_name} 图片目录已就绪：{self.IMAGES_DIR}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 创建图片目录失败：{str(e)}")
            return False

        # 检查图片目录是否为空
        if not any(self.IMAGES_DIR.glob("*")):
            logger.warning(f"{self.plugin_name} 图片目录为空")
            if self._notify:
                self.post_message(
                    mtype=NotificationType.Warning,
                    title=f"{self.plugin_name} 启动提醒",
                    text="图片目录为空，请添加图片到 plugins.v2/random_pic_api/images 目录"
                )

        return {
            "name": self.plugin_name,
            "description": self.plugin_desc,
            "version": self.plugin_version,
            "author": self.plugin_author,
            "url": self.author_url,
            "priority": self.plugin_order,
            "app": self.app,
            "api_prefix": "/random_pic_api"
        }

    def get_state(self) -> bool:
        """获取插件启用状态"""
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        """获取插件命令"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """获取插件API"""
        return [{
            "path": "/random",
            "endpoint": self.random_image,
            "methods": ["GET"],
            "summary": "获取随机图片",
            "description": "从配置的图片目录中随机返回一张图片"
        }]

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """获取插件配置表单"""
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'notify',
                                            'label': '发送通知'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': '将图片放入 plugins.v2/random_pic_api/images 目录后，可通过 /random_pic_api/random 接口随机访问'
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

    def get_random_image(self):
        """获取图片目录下的随机图片"""
        if not self.IMAGES_DIR.exists():
            return None
        
        # 支持的图片格式
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        # 获取所有支持格式的图片
        images = []
        for ext in image_extensions:
            images.extend(self.IMAGES_DIR.glob(f"*{ext}"))
            images.extend(self.IMAGES_DIR.glob(f"*{ext.upper()}"))
        
        return random.choice(images) if images else None

    @app.route('/random')
    def random_image(self):
        """随机返回一张图片"""
        if not self._enabled:
            return "插件未启用", 403

        image_path = self.get_random_image()
        if not image_path:
            return "图片目录为空，请先添加图片到 plugins.v2/random_pic_api/images 目录", 404

        try:
            return send_file(str(image_path))
        except Exception as e:
            logger.error(f"{self.plugin_name} 读取图片失败：{str(e)}")
            return "读取图片失败", 500

    def __update_config(self):
        """更新配置"""
        self.update_config({
            "enabled": self._enabled,
            "notify": self._notify
        }) 