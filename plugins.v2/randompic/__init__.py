import os
import random
import aiohttp
from typing import Optional
from app.plugins import _PluginBase
from app.core.config import settings

class RandomPic(_PluginBase):
    # 插件名称
    plugin_name = "随机图片"
    # 插件描述
    plugin_desc = "获取随机图片的插件"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/sitemonitor.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "randompic_"
    # 加载顺序
    plugin_order = 20
    # 可使用的用户级别
    auth_level = 1
    
    # 插件配置
    _api_source = None
    _width = None
    _height = None
    
    def init_plugin(self, config: dict):
        self._api_source = config.get('api_source', 'picsum')
        self._width = config.get('width', '1920')
        self._height = config.get('height', '1080')
    
    async def get_random_image(self) -> Optional[bytes]:
        """
        获取随机图片
        """
        try:
            async with aiohttp.ClientSession() as session:
                if self._api_source == "picsum":
                    url = f"https://picsum.photos/{self._width}/{self._height}"
                else:  # unsplash
                    url = f"https://source.unsplash.com/random/{self._width}x{self._height}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        self.debug.error(f"获取随机图片失败：HTTP {response.status}")
                        return None
        except Exception as e:
            self.debug.error(f"获取随机图片出错：{str(e)}")
            return None
    
    async def get_state(self) -> bool:
        """
        插件运行状态
        """
        return True

    @staticmethod
    def get_command() -> list:
        """
        注册命令
        """
        return ["randompic"]

    def get_api(self) -> list:
        """
        注册API
        """
        return [
            {
                "path": "/randompic",
                "endpoint": self.get_random_image,
                "methods": ["GET"],
                "summary": "获取随机图片",
                "description": "从配置的图片源获取随机图片"
            }
        ]

    async def get_command_state(self) -> bool:
        """
        命令运行状态
        """
        return True 