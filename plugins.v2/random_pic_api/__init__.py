import os
import random
from flask import Flask, send_file
from pathlib import Path
from moviepilot.core.plugin import PluginBase

class RandomPicApi(PluginBase):
    # 插件名称
    plugin_name = "随机图片API"
    # 插件描述
    plugin_desc = "提供简单的随机图片API服务"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/random.png"
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
    user_level = 1

    app = Flask(__name__)

    # 获取插件根目录
    PLUGIN_ROOT = Path(__file__).parent
    # 图片目录
    IMAGES_DIR = PLUGIN_ROOT / "images"

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
        image_path = self.get_random_image()
        if not image_path:
            return "没有找到图片", 404
        return send_file(str(image_path))

    def init_plugin(self):
        """插件初始化函数"""
        # 确保图片目录存在
        self.IMAGES_DIR.mkdir(exist_ok=True)
        
        # 检查图片目录是否为空
        if not any(self.IMAGES_DIR.glob("*")):
            return {
                "name": self.plugin_name,
                "description": self.plugin_desc,
                "version": self.plugin_version,
                "author": self.plugin_author,
                "url": self.author_url,
                "priority": self.plugin_order,
                "app": self.app,
                "api_prefix": "/random_pic_api",
                "error": "404-Not Found: 图片目录为空，请先在 plugins.v2/random_pic_api/images 目录添加图片"
            }
        
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