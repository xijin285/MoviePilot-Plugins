import os
import time
import requests
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from app.plugins import _PluginBase
from app.schemas import NotificationType
from app.log import logger

class ImageHostPlugin(_PluginBase):
    # 插件名称
    plugin_name = "图床上传助手"
    # 插件描述
    plugin_desc = "将本地图片上传到图床并获取URL"
    # 插件图标
    plugin_icon = "imagehost.png"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/yourusername"
    # 插件配置项ID前缀
    plugin_config_prefix = "imagehost_"
    # 加载顺序
    plugin_order = 10
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled: bool = False
    _notify: bool = False
    _api_key: str = ""
    _upload_url: str = ""
    _retry_count: int = 3
    _retry_interval: int = 60
    _notification_style: int = 1

    def init_plugin(self, config: Optional[dict] = None):
        if config:
            self._enabled = bool(config.get("enabled", False))
            self._notify = bool(config.get("notify", False))
            self._api_key = str(config.get("api_key", ""))
            self._upload_url = str(config.get("upload_url", "")).rstrip('/')
            self._retry_count = int(config.get("retry_count", 3))
            self._retry_interval = int(config.get("retry_interval", 60))
            self._notification_style = int(config.get("notification_style", 1))

    def get_state(self) -> bool:
        return self._enabled

    def get_form(self) -> tuple[list[dict], dict]:
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSwitch', 'props': {'model': 'enabled', 'label': '启用插件'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSwitch', 'props': {'model': 'notify', 'label': '发送通知'}}]},
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'api_key', 'label': 'API密钥', 'placeholder': '请输入图床API密钥'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'upload_url', 'label': '上传地址', 'placeholder': '请输入图床上传API地址'}}]},
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VTextField', 'props': {'model': 'retry_count', 'label': '最大重试次数', 'type': 'number', 'placeholder': '3'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VTextField', 'props': {'model': 'retry_interval', 'label': '重试间隔(秒)', 'type': 'number', 'placeholder': '60'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSelect', 'props': {'model': 'notification_style', 'label': '通知样式', 'items': [{'title': '样式1 - 简约星线', 'value': 1}, {'title': '样式2 - 方块花边', 'value': 2}, {'title': '样式3 - 箭头主题', 'value': 3}]}}]},
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [{'component': 'VCol', 'props': {'cols': 12}, 'content': [{'component': 'VAlert', 'props': {'type': 'info', 'variant': 'tonal', 'text': '【使用说明】\n1. 填写图床服务的API密钥和上传地址。\n2. 设置上传失败时的重试次数和间隔时间。\n3. 可选择是否启用通知功能，以及通知的显示样式。\n4. 启用插件后即可使用。'}}]}]
                    }
                ]
            }
        ], {
            "enabled": False,
            "notify": False,
            "api_key": "",
            "upload_url": "https://api.example.com/upload",
            "retry_count": 3,
            "retry_interval": 60,
            "notification_style": 1
        }

    def upload_image(self, image_path: str) -> Optional[str]:
        """
        上传图片到图床并返回URL
        
        Args:
            image_path: 本地图片路径
            
        Returns:
            str: 图片URL，如果上传失败则返回None
        """
        if not self._enabled:
            logger.error(f"{self.plugin_name} 插件未启用")
            return None

        if not os.path.exists(image_path):
            logger.error(f"{self.plugin_name} 图片文件不存在: {image_path}")
            return None

        session = requests.Session()
        retries = Retry(total=self._retry_count, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        headers = {
            'Authorization': f'Bearer {self._api_key}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
        }

        try:
            with open(image_path, 'rb') as f:
                files = {'file': (Path(image_path).name, f, 'image/jpeg')}
                response = session.post(self._upload_url, files=files, headers=headers, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                if 'url' in result:
                    self._send_notification(True, f"图片上传成功: {result['url']}")
                    return result['url']
                else:
                    error_msg = f"上传响应中未找到URL: {response.text}"
                    logger.error(f"{self.plugin_name} {error_msg}")
                    self._send_notification(False, error_msg)
                    return None
                    
        except Exception as e:
            error_msg = f"上传过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            self._send_notification(False, error_msg)
            return None

    def _send_notification(self, success: bool, message: str = ""):
        if not self._notify:
            return
            
        title = f"🖼️ {self.plugin_name} "
        title += "成功" if success else "失败"
        status_emoji = "✅" if success else "❌"
        
        # 根据选择的通知样式设置分隔符和风格
        if self._notification_style == 1:
            # 样式1 - 简约星线
            divider = "★━━━━━━━━━━━━━━━━━━━━━━━★"
            status_prefix = "📌"
            info_prefix = "ℹ️"
        elif self._notification_style == 2:
            # 样式2 - 方块花边
            divider = "■□■□■□■□■□■□■□■□■□■□■□■□■"
            status_prefix = "🔰"
            info_prefix = "📝"
        else:
            # 样式3 - 箭头主题
            divider = "➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤➤"
            status_prefix = "🔔"
            info_prefix = "📢"
        
        text_content = f"{divider}\n"
        text_content += f"{status_prefix} 状态：{status_emoji} {'上传成功' if success else '上传失败'}\n"
        if message:
            text_content += f"{info_prefix} 详情：{message}\n"
        text_content += f"\n{divider}\n"
        text_content += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            self.post_message(mtype=NotificationType.Plugin, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送通知失败: {e}")

    def get_api(self) -> list[dict]:
        return [{
            "path": "/upload",
            "method": "POST",
            "description": "上传图片到图床",
            "params": {
                "image_path": {
                    "type": "string",
                    "description": "本地图片路径"
                }
            }
        }]

    def get_command(self) -> list[dict]:
        return [{
            "cmd": "/upload",
            "description": "上传图片到图床",
            "params": {
                "image_path": {
                    "type": "string",
                    "description": "本地图片路径"
                }
            }
        }] 