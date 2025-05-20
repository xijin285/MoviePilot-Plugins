import os
import random
from typing import Optional
from app.plugins import _PluginBase
from app.core.config import settings
from pathlib import Path
from aiohttp import web

class RandomPic(_PluginBase):
    # 插件名称
    plugin_name = "随机图片"
    # 插件描述
    plugin_desc = "图片托管服务插件"
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
    _image_path = None
    
    def init_plugin(self, config: dict):
        # 使用插件目录下的images文件夹存储图片
        self._image_path = os.path.join(os.path.dirname(__file__), 'images')
        if not os.path.exists(self._image_path):
            os.makedirs(self._image_path)
    
    async def serve_image(self, request) -> web.Response:
        """
        提供图片访问服务
        """
        try:
            image_name = request.match_info.get('image_name')
            image_path = os.path.join(self._image_path, image_name)
            if os.path.exists(image_path):
                return web.FileResponse(image_path)
            else:
                return web.Response(status=404, text="Image not found")
        except Exception as e:
            self.debug.error(f"访问图片出错：{str(e)}")
            return web.Response(status=500, text="Internal server error")
    
    async def list_images(self, request) -> web.Response:
        """
        列出所有可用的图片
        """
        try:
            images = []
            for file in os.listdir(self._image_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    images.append({
                        "name": file,
                        "url": f"/api/plugins/randompic/images/{file}",
                        "size": os.path.getsize(os.path.join(self._image_path, file)),
                        "modified": os.path.getmtime(os.path.join(self._image_path, file))
                    })
            return web.json_response(images)
        except Exception as e:
            self.debug.error(f"列出图片出错：{str(e)}")
            return web.Response(status=500, text="Internal server error")
    
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
                "path": "/randompic/images/{image_name}",
                "endpoint": self.serve_image,
                "methods": ["GET"],
                "summary": "获取指定图片",
                "description": "访问指定的图片文件"
            },
            {
                "path": "/randompic/list",
                "endpoint": self.list_images,
                "methods": ["GET"],
                "summary": "列出所有图片",
                "description": "获取所有可用图片的列表及其访问链接"
            }
        ]

    async def get_command_state(self) -> bool:
        """
        命令运行状态
        """
        return True 