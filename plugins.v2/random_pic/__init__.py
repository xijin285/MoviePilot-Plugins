from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import random
import os
from datetime import datetime

from moviepilot.core.plugin import PluginBase
from moviepilot.core.settings import settings
from moviepilot.core.logger import logger

class RandomPicPlugin(PluginBase):
    # 插件名称
    plugin_name = "随机图片API"
    # 插件描述
    plugin_desc = "提供随机图片API服务，支持横竖屏图片分类"
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
    plugin_order = 10
    # 可使用的用户级别
    user_level = 1

    # 私有属性
    _enabled: bool = False
    _pc_dir: Optional[Path] = None
    _mobile_dir: Optional[Path] = None
    _notify: bool = False

    def init_plugin(self, config: Optional[dict] = None):
        """初始化插件"""
        if config:
            self._enabled = bool(config.get("enabled", False))
            self._notify = bool(config.get("notify", False))
            
        # 初始化图片目录
        self._pc_dir = self.get_data_path() / "pc"
        self._mobile_dir = self.get_data_path() / "mobile"
        
        # 确保目录存在
        self._pc_dir.mkdir(parents=True, exist_ok=True)
        self._mobile_dir.mkdir(parents=True, exist_ok=True)
        
        self.__update_config()

    def __update_config(self):
        """更新配置"""
        self.update_config({
            "enabled": self._enabled,
            "notify": self._notify
        })

    def get_state(self) -> bool:
        """获取插件状态"""
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        """获取命令"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """获取API"""
        return [{
            "path": "/random",
            "endpoint": self.api_route,
            "method": "GET",
            "description": "获取随机图片"
        }]

    def get_service(self) -> List[Dict[str, Any]]:
        """获取服务"""
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """获取表单"""
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
                    }
                ]
            }
        ], {
            "enabled": self._enabled,
            "notify": self._notify
        }

    def get_page(self) -> List[dict]:
        """获取页面"""
        return [
            {
                'component': 'VCard',
                'content': [
                    {
                        'component': 'VCardTitle',
                        'props': {
                            'title': '随机图片API'
                        }
                    },
                    {
                        'component': 'VCardText',
                        'content': [
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
                                                    'text': 'API使用说明：\n1. 访问 /random 获取随机图片\n2. 可通过 type 参数指定设备类型（pc/mobile）'
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]

    def api_route(self, path: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """API路由处理
        
        Args:
            path: API路径
            method: 请求方法
            params: 请求参数
            
        Returns:
            Dict[str, Any]: API响应
        """
        if not self._enabled:
            return {"error": "插件未启用"}
            
        if path == "/random":
            device_type = params.get("type", "pc")
            if device_type not in ["pc", "mobile"]:
                return {"error": "Invalid device type"}
                
            image_url = self.get_random_pic(device_type)
            if not image_url:
                return {"error": "No images available"}
                
            if self._notify:
                self.send_notify(f"获取到{device_type}随机图片：{image_url}")
                
            return {"url": image_url}
            
        return {"error": "Invalid path"}

    def get_random_pic(self, device_type: str = "pc") -> Optional[str]:
        """获取随机图片
        
        Args:
            device_type: 设备类型，可选值：pc（横屏）或 mobile（竖屏）
            
        Returns:
            str: 图片URL或None
        """
        target_dir = self._pc_dir if device_type == "pc" else self._mobile_dir
        
        # 获取目录下所有图片文件
        image_files = [f for f in target_dir.glob("*") if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']]
        
        if not image_files:
            return None
            
        # 随机选择一张图片
        random_image = random.choice(image_files)
        return str(random_image)

    def send_notify(self, message: str):
        """发送通知
        
        Args:
            message: 通知消息
        """
        if not self._notify:
            return
            
        try:
            self.send_message(
                title=f"{self.plugin_name}通知",
                text=message
            )
        except Exception as e:
            logger.error(f"发送通知失败：{str(e)}") 