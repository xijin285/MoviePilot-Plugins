import os
import time
import random
from typing import Any, List, Dict, Optional
from app.plugins import _PluginBase
from app.core.config import settings
from app.core.meta import MetaInfo
from app.log import logger

class LocalImageAPI(_PluginBase):
    # 插件名称
    plugin_name = "本地图片API"
    # 插件描述
    plugin_desc = "将本地图片文件夹映射为随机图片API服务"
    # 插件图标
    plugin_icon = "图片"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "localimageapi_"
    # 加载顺序
    plugin_order = 21
    # 可使用的用户级别
    auth_level = 2

    # 私有属性
    _image_files: List[str] = []
    _last_scan_time: float = 0
    _scan_interval: int = 3600  # 扫描间隔1小时
    _initialized_successfully: bool = False

    def init_plugin(self, config: Dict[str, Any]) -> None:
        self.image_path = config.get("image_path", "")
        self.api_path = config.get("api_path", "random_image")
        self.allowed_extensions = config.get("allowed_extensions", "jpg,jpeg,png,gif").split(",")
        
        if not self.image_path or not os.path.exists(self.image_path):
            logger.error(f"图片文件夹路径 {self.image_path} 不存在，插件 {self.plugin_name} 初始化失败。")
            self._initialized_successfully = False
            return
        
        # 初始扫描图片文件
        self._scan_images()
        # 即使扫描可能因为某些原因没有找到图片，但只要路径有效，我们认为基础初始化是成功的
        # 功能是否正常取决于是否有图片以及API调用是否成功
        self._initialized_successfully = True
        logger.info(f"插件 {self.plugin_name} 初始化成功。")

    def _scan_images(self) -> None:
        """
        扫描图片文件夹
        """
        current_time = time.time()
        # 如果距离上次扫描时间不足间隔时间，则跳过
        if current_time - self._last_scan_time < self._scan_interval:
            return
        
        self._image_files = []
        try:
            for root, _, files in os.walk(self.image_path):
                for file in files:
                    if any(file.lower().endswith(f".{ext.lower()}") for ext in self.allowed_extensions):
                        self._image_files.append(os.path.join(root, file))
            logger.info(f"扫描到 {len(self._image_files)} 个图片文件")
        except Exception as e:
            logger.error(f"扫描图片文件夹出错: {str(e)}")
        
        self._last_scan_time = current_time

    @property
    def _webapi(self) -> List[Dict[str, Any]]:
        """
        注册Web API
        """
        return [{
            "path": f"/api/v1/{self.api_path}",
            "endpoint": self.get_random_image,
            "methods": ["GET"],
            "summary": "获取随机图片",
            "description": "从配置的图片文件夹中随机返回一张图片"
        }]

    async def get_random_image(self) -> Any:
        """
        获取随机图片
        """
        # 重新扫描图片
        self._scan_images()
        
        if not self._image_files:
            return {"code": 404, "message": "没有找到图片文件"}
        
        # 随机选择一个图片文件
        image_path = random.choice(self._image_files)
        
        try:
            # 读取图片文件
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # 获取文件扩展名
            file_ext = os.path.splitext(image_path)[1].lower()
            
            # 设置响应头
            content_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif"
            }.get(file_ext, "application/octet-stream")
            
            # 返回图片数据
            from fastapi.responses import Response
            return Response(content=image_data, media_type=content_type)
            
        except Exception as e:
            logger.error(f"读取图片文件出错: {str(e)}")
            return {"code": 500, "message": f"读取图片文件出错: {str(e)}"}

    def get_state(self) -> bool:
        return self._initialized_successfully 