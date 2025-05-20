import os
import random
from typing import List, Dict, Any, Tuple, Optional, Union
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
    plugin_version = "1.0.3"
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
    _app_instance = None # 用于存储Flask App实例

    # 获取插件根目录
    PLUGIN_ROOT = Path(__file__).parent
    # 图片目录
    IMAGES_DIR = PLUGIN_ROOT / "images"

    def init_plugin(self, config: Optional[Dict[str, Any]] = None) -> Union[bool, Dict[str, Any]]:
        """插件初始化"""
        logger.info(f"开始初始化插件：{self.plugin_name}")
        if config:
            self._enabled = config.get("enabled", False)
            self._notify = config.get("notify", False)
            self.__update_config()

        try:
            self.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"{self.plugin_name} 图片目录已就绪：{self.IMAGES_DIR}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 创建图片目录失败：{str(e)}")
            return {"code": 1, "msg": f"创建图片目录失败: {str(e)}"}

        if not any(self.IMAGES_DIR.glob("*")):
            logger.warning(f"{self.plugin_name} 图片目录为空: {self.IMAGES_DIR}")
            if self._enabled and self._notify:
                self.post_message(
                    mtype=NotificationType.Warning,
                    title=f"{self.plugin_name} 启动提醒",
                    text=f"图片目录 {self.IMAGES_DIR} 为空，请添加图片。"
                )
        
        # 初始化Flask App
        self._app_instance = Flask(__name__)
        self._app_instance.route("/random")(self.random_image_route)

        logger.info(f"插件 {self.plugin_name} 初始化成功。")
        return {
            "code": 0,
            "msg": "初始化成功",
            "name": self.plugin_name,
            "description": self.plugin_desc,
            "version": self.plugin_version,
            "author": self.plugin_author,
            "url": self.author_url,
            "priority": self.plugin_order,
            "app": self._app_instance, # 返回Flask app实例
            "api_prefix": "/random_pic_api"
        }

    def get_state(self) -> bool:
        """获取插件启用状态"""
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        """获取插件命令"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """获取插件API (此插件通过app实例直接注册)"""
        return [] # 由于直接通过Flask app实例注册路由，这里可以返回空列表
        # 或者，如果想通过MoviePilot的API管理方式，则在此处定义
        # return [{
        #     "path": "/random",
        #     "endpoint": self.random_image_route, # 指向实际处理函数
        #     "methods": ["GET"],
        #     "summary": "获取随机图片",
        #     "description": "从配置的图片目录中随机返回一张图片"
        # }]

    def get_service(self) -> List[Dict[str, Any]]:
        """获取插件服务"""
        return []

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
                                            'label': '图片目录为空时发送通知'
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
                                            'text': f'请将图片放入插件的 images 目录 ({self.IMAGES_DIR})。然后通过 /random_pic_api/random 接口随机访问。'
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
            "notify": True # 默认开启通知
        }

    def get_page(self) -> List[dict]:
        """获取插件页面"""
        if not self._enabled:
            return [
                {
                    'component': 'VAlert',
                    'props': {
                        'type': 'warning',
                        'variant': 'tonal',
                        'text': '插件未启用。请在配置中启用插件。'
                    }
                }
            ]

        return [
            {
                'component': 'VCard',
                'props': {'variant': 'outlined', 'class': 'mb-3'},
                'content': [
                    {
                        'component': 'VCardTitle',
                        'props': {'class': 'text-h6'},
                        'text': '📸 本地图片API服务状态'
                    },
                    {
                        'component': 'VCardText',
                        'content': [
                            f"图片目录：{self.IMAGES_DIR}",
                            f"API访问地址：/random_pic_api/random",
                            f"当前图片数量：{len(list(self.IMAGES_DIR.glob('*'))) if self.IMAGES_DIR.exists() else 0}"
                        ]
                    }
                ]
            }
        ]

    def _get_random_image_path(self) -> Optional[Path]:
        """内部方法：获取图片目录下的随机图片路径"""
        if not self.IMAGES_DIR.exists():
            logger.error(f"{self.plugin_name} 图片目录 {self.IMAGES_DIR} 不存在")
            return None
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        images = []
        for ext in image_extensions:
            images.extend(self.IMAGES_DIR.glob(f"*{ext.lower()}"))
            images.extend(self.IMAGES_DIR.glob(f"*{ext.upper()}")) # 同时匹配大小写扩展名
        
        if not images:
            logger.warning(f"{self.plugin_name} 在目录 {self.IMAGES_DIR} 未找到支持的图片文件 ({', '.join(image_extensions)}) ")
            return None
        return random.choice(images)

    def random_image_route(self):
        """Flask路由处理函数：随机返回一张图片"""
        if not self._enabled:
            logger.warning(f"{self.plugin_name} 收到请求，但插件未启用。")
            return "插件未启用", 403

        try:
            image_path = self._get_random_image_path()
            if not image_path:
                logger.warning(f"{self.plugin_name} 图片目录为空或未找到图片")
                return f"图片目录 {self.IMAGES_DIR} 为空或未找到支持的图片", 404
            
            logger.debug(f"{self.plugin_name} 提供图片: {image_path}")
            return send_file(str(image_path))
        except Exception as e:
            logger.error(f"{self.plugin_name} 处理随机图片请求失败：{str(e)}")
            return "服务器内部错误，无法提供图片", 500

    def __update_config(self):
        """更新配置到存储"""
        if self.is_config_available(): # 确保配置已加载
            self.update_config({
                "enabled": self._enabled,
                "notify": self._notify
            })
            logger.debug(f"{self.plugin_name} 配置已更新: enabled={self._enabled}, notify={self._notify}")
        else:
            logger.warning(f"{self.plugin_name} 尝试更新配置，但配置模块不可用。")

    def stop_plugin(self):
        """停止插件（可选实现）"""
        logger.info(f"插件 {self.plugin_name} 已停止。")
        # 清理 Flask app 实例等资源（如果需要）
        self._app_instance = None
        return True

    def __init__(self, name: str = None, plugin_id: str = None):
        super().__init__(name=name, plugin_id=plugin_id)
        self._app_instance = None # 确保初始状态 