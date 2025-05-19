from typing import Any, Dict, List, Optional, Tuple
from moviepilot.core.plugin import PluginBase
from moviepilot.core.scheduler import Scheduler
from moviepilot.core.config import settings
import random
import time
import threading
from pathlib import Path
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

class SimpleRandomImagePlugin(PluginBase):
    # 插件名称
    plugin_name = "简易随机图片"
    # 插件描述
    plugin_desc = "提供简单的随机图片API服务，支持多个图片源，自动重试和缓存机制"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/image.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    _config_prefix = "simple_random_image_"
    # 加载顺序
    plugin_order = 10
    # 可使用的用户级别
    user_level = 2

    # 私有属性
    _scheduler: Optional[Scheduler] = None
    _lock: Optional[threading.Lock] = None
    _running: bool = False
    _session: Optional[requests.Session] = None

    # 配置属性
    _enabled: bool = False
    _image_sources: List[str] = []
    _cache_time: int = 3600
    _cache: Dict[str, Tuple[str, float]] = {}
    _retry_count: int = 3
    _retry_interval: int = 5

    def init_plugin(self, config: Optional[dict] = None):
        self._lock = threading.Lock()
        self._session = requests.Session()
        retries = Retry(total=self._retry_count, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        self._session.mount('http://', HTTPAdapter(max_retries=retries))
        self._session.mount('https://', HTTPAdapter(max_retries=retries))
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        })

        if config:
            self._enabled = bool(config.get("enabled", False))
            self._image_sources = config.get("image_sources", [])
            self._cache_time = int(config.get("cache_time", 3600))
            self._retry_count = int(config.get("retry_count", 3))
            self._retry_interval = int(config.get("retry_interval", 5))
            self.__update_config()

    def __update_config(self):
        self.update_config({
            "enabled": self._enabled,
            "image_sources": self._image_sources,
            "cache_time": self._cache_time,
            "retry_count": self._retry_count,
            "retry_interval": self._retry_interval
        })

    def get_state(self) -> bool:
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return [
            {
                "path": "/api/v1/random_image",
                "endpoint": self.get_random_image,
                "methods": ["GET"],
                "summary": "获取随机图片",
                "description": "返回一个随机图片的URL"
            }
        ]

    def get_service(self) -> List[Dict[str, Any]]:
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
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
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'image_sources',
                                            'label': '图片源列表',
                                            'rows': 5,
                                            'placeholder': '每行一个图片URL'
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
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'cache_time',
                                            'label': '缓存时间(秒)',
                                            'type': 'number'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'retry_count',
                                            'label': '重试次数',
                                            'type': 'number'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'retry_interval',
                                            'label': '重试间隔(秒)',
                                            'type': 'number'
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
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': '【使用说明】\n1. 启用插件后即可通过API获取随机图片\n2. 在图片源列表中添加图片URL，每行一个\n3. 设置缓存时间，单位为秒\n4. 设置重试次数和间隔，提高稳定性\n5. API接口：/api/v1/random_image'
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
            "image_sources": [
                "https://picsum.photos/800/600",
                "https://source.unsplash.com/random/800x600"
            ],
            "cache_time": 3600,
            "retry_count": 3,
            "retry_interval": 5
        }

    def get_random_image(self) -> Optional[str]:
        """获取随机图片URL"""
        if not self._enabled or not self._image_sources:
            return None
        
        # 检查缓存
        current_time = time.time()
        for source, (url, timestamp) in list(self._cache.items()):
            if current_time - timestamp > self._cache_time:
                del self._cache[source]
        
        # 随机选择一个图片源
        source = random.choice(self._image_sources)
        
        # 如果源在缓存中且未过期，直接返回
        if source in self._cache:
            return self._cache[source][0]
        
        try:
            # 使用session发送请求获取图片URL
            response = self._session.get(source, timeout=10)
            response.raise_for_status()
            # 更新缓存
            self._cache[source] = (response.url, current_time)
            return response.url
        except Exception as e:
            self.error(f"获取随机图片失败: {str(e)}")
            return None 