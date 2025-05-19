from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import aiohttp
import random
import json
import os
from datetime import datetime, timedelta

from moviepilot.core.plugin import PluginBase

class RandomImageAPI(PluginBase):
    """随机图片API插件
    
    提供随机图片API服务，支持PC和移动端不同尺寸的图片。
    支持自定义图片源配置，可配置多个图片源URL。
    """
    
    # 插件基本信息
    plugin_name = "随机图片API"
    plugin_desc = "提供随机图片API服务，支持PC和移动端不同尺寸的图片，可自定义配置多个图片源"
    plugin_icon = "image"
    plugin_version = "1.0.0"
    plugin_author = "jinxi"
    author_url = "https://github.com/xijin285"
    plugin_order = 10
    user_level = 1
    plugin_config_prefix = "random_image_api_"
    plugin_config = {
        "enabled": False,
        "image_sources": {
            "pc": [
                "https://picsum.photos/1920/1080",
                "https://source.unsplash.com/random/1920x1080"
            ],
            "mobile": [
                "https://picsum.photos/1080/1920",
                "https://source.unsplash.com/random/1080x1920"
            ]
        }
    }

    # 私有属性
    _enabled: bool = False
    _cache_dir: Path = None
    _cache_file: Path = None
    _cache: Dict = None
    _config: Dict = None

    def init_plugin(self, config: Optional[dict] = None):
        """初始化插件
        
        Args:
            config: 插件配置信息
        """
        if config:
            self._enabled = bool(config.get("enabled", False))
            self._config = config
            self._init_cache()
            self.__update_config()

    def _init_cache(self):
        """初始化缓存"""
        self._cache_dir = Path(self.get_data_path() / "cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_file = self._cache_dir / "cache.json"
        self._load_cache()

    def _load_cache(self):
        """加载缓存数据"""
        if self._cache_file.exists():
            with open(self._cache_file, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
        else:
            self._cache = {"images": {}, "last_update": None}
            
    def _save_cache(self):
        """保存缓存数据"""
        with open(self._cache_file, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)

    def get_state(self) -> bool:
        """获取插件状态"""
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        """获取命令列表"""
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        """获取API接口列表"""
        return [{
            "path": "/api/random_image",
            "endpoint": self.get_random_image,
            "methods": ["GET"],
            "summary": "获取随机图片",
            "description": "获取随机图片URL，支持PC和移动端不同尺寸",
            "parameters": [{
                "name": "device_type",
                "in": "query",
                "description": "设备类型",
                "required": False,
                "schema": {
                    "type": "string",
                    "enum": ["pc", "mobile"],
                    "default": "pc"
                }
            }]
        }]

    def get_service(self) -> List[Dict[str, Any]]:
        """获取服务列表"""
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """获取表单配置"""
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 4},
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {'model': 'enabled', 'label': '启用插件'}
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
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'image_sources',
                                            'label': '图片源配置',
                                            'rows': 5,
                                            'placeholder': '每行一个图片源URL'
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
            "image_sources": {
                "pc": [
                    "https://picsum.photos/1920/1080",
                    "https://source.unsplash.com/random/1920x1080"
                ],
                "mobile": [
                    "https://picsum.photos/1080/1920",
                    "https://source.unsplash.com/random/1080x1920"
                ]
            }
        }

    def get_page(self) -> List[dict]:
        """获取页面配置"""
        return []

    def __update_config(self):
        """更新配置"""
        self.update_config({
            "enabled": self._enabled,
            "image_sources": self._config.get("image_sources", {})
        })

    async def get_random_image(self, device_type: str = "pc") -> Optional[str]:
        """获取随机图片URL
        
        Args:
            device_type: 设备类型，pc或mobile
            
        Returns:
            str: 图片URL，获取失败返回None
        """
        if not self._enabled:
            return None

        # 默认图片源
        default_sources = {
            "pc": [
                "https://picsum.photos/1920/1080",
                "https://source.unsplash.com/random/1920x1080",
            ],
            "mobile": [
                "https://picsum.photos/1080/1920",
                "https://source.unsplash.com/random/1080x1920",
            ]
        }
        
        # 使用配置的图片源或默认源
        sources = self._config.get("image_sources", {}).get(device_type, default_sources[device_type])
        
        if not sources:
            return None
            
        # 随机选择一个图片源
        source = random.choice(sources)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source) as response:
                    if response.status == 200:
                        return str(response.url)
        except Exception as e:
            print(f"获取随机图片失败: {str(e)}")
            
        return None

    def get_api_endpoints(self) -> Dict[str, Any]:
        """获取API端点信息"""
        return {
            "random_image": {
                "url": "/api/random_image",
                "method": "GET",
                "params": {
                    "device_type": {
                        "type": "string",
                        "enum": ["pc", "mobile"],
                        "default": "pc",
                        "description": "设备类型"
                    }
                },
                "description": "获取随机图片URL"
            }
        }
        
    def get_config_schema(self) -> Dict[str, Any]:
        """获取配置模式"""
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "是否启用插件"
                },
                "image_sources": {
                    "type": "object",
                    "properties": {
                        "pc": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "PC端图片源列表"
                        },
                        "mobile": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "移动端图片源列表"
                        }
                    }
                }
            }
        }
        
    def update_config(self, config: Dict[str, Any]):
        """更新配置
        
        Args:
            config: 新配置
        """
        self._config = config 