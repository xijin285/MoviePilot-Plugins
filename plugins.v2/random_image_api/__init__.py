from typing import Any, Dict, List, Optional
from app.core.plugin import Plugin
from app.schemas.types import EventType
from app.utils.http import RequestUtils
import random

class SimpleRandomImagePlugin(Plugin):
    # 插件名称
    plugin_name = "简易随机图片"
    # 插件描述
    plugin_desc = "提供简单的随机图片API服务，支持多个图片源"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项
    plugin_config = {
        "image_sources": {
            "name": "图片源",
            "value": [
                "https://picsum.photos/800/600",
                "https://source.unsplash.com/random/800x600"
            ],
            "type": "list",
            "help": "随机图片源列表，每行一个URL"
        },
        "cache_time": {
            "name": "缓存时间",
            "value": 3600,
            "type": "int",
            "help": "图片缓存时间（秒）"
        }
    }

    def __init__(self):
        super().__init__()
        self._image_sources = []
        self._cache_time = 3600

    def init_plugin(self, config: Dict[str, Any] = None):
        if config:
            self._image_sources = config.get("image_sources", [])
            self._cache_time = config.get("cache_time", 3600)

    def get_random_image(self) -> Optional[str]:
        """获取随机图片URL"""
        if not self._image_sources:
            return None
        
        source = random.choice(self._image_sources)
        try:
            # 使用RequestUtils发送请求获取图片URL
            response = RequestUtils().get_res(source)
            if response and response.status_code == 200:
                return response.url
        except Exception as e:
            self.error(f"获取随机图片失败: {str(e)}")
        return None

    def get_plugin_apis(self) -> List[Dict[str, Any]]:
        """获取插件API"""
        return [
            {
                "path": "/api/v1/random_image",
                "endpoint": self.get_random_image,
                "methods": ["GET"],
                "summary": "获取随机图片",
                "description": "返回一个随机图片的URL"
            }
        ] 