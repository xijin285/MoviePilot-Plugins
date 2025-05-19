import os
import random
from flask import Flask, send_file, request
from pathlib import Path
from .image_processor import setup_image_directories
from app.plugins import PluginBase

class RandomPicApi(PluginBase):
    # 插件名称
    plugin_name = "随机图片API"
    # 插件描述
    plugin_desc = "提供随机图片API服务，支持移动端和PC端自适应"
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

    # 图片目录配置
    PORTRAIT_DIR = PLUGIN_ROOT / "portrait"  # 竖屏图片目录
    LANDSCAPE_DIR = PLUGIN_ROOT / "landscape"  # 横屏图片目录
    IMAGES_DIR = PLUGIN_ROOT / "images"  # 原始图片目录

    def get_random_image(self, directory):
        """获取指定目录下的随机图片"""
        if not directory.exists():
            return None
        images = [f for f in directory.glob("*") if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']]
        return random.choice(images) if images else None

    @app.route('/random')
    def random_image(self):
        """随机返回一张图片"""
        # 检测用户代理判断设备类型
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(device in user_agent for device in ['mobile', 'android', 'iphone'])
        
        # 根据设备类型选择图片目录
        target_dir = self.PORTRAIT_DIR if is_mobile else self.LANDSCAPE_DIR
        image_path = self.get_random_image(target_dir)
        
        if not image_path:
            return "No images found", 404
        
        return send_file(str(image_path))

    @app.route('/random/mobile')
    def random_mobile(self):
        """返回竖屏图片"""
        image_path = self.get_random_image(self.PORTRAIT_DIR)
        if not image_path:
            return "No images found", 404
        return send_file(str(image_path))

    @app.route('/random/pc')
    def random_pc(self):
        """返回横屏图片"""
        image_path = self.get_random_image(self.LANDSCAPE_DIR)
        if not image_path:
            return "No images found", 404
        return send_file(str(image_path))

    def init_plugin(self):
        """插件初始化函数"""
        # 确保图片目录存在
        self.PORTRAIT_DIR.mkdir(exist_ok=True)
        self.LANDSCAPE_DIR.mkdir(exist_ok=True)
        self.IMAGES_DIR.mkdir(exist_ok=True)
        
        # 设置图片目录并处理图片
        setup_image_directories()
        
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