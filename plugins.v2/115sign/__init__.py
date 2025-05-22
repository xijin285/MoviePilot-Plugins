from typing import Any, Dict, Optional
from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import NotificationType
import requests
import json

class Sign115(_PluginBase):
    # 插件名称
    plugin_name = "115云盘签到"
    # 插件描述
    plugin_desc = "自动完成115云盘每日签到"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/115.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "115sign_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    def __init__(self):
        super().__init__()
        self._cookie = None
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def get_state(self) -> bool:
        return self._cookie is not None

    @staticmethod
    def get_command() -> Optional[Dict[str, Any]]:
        pass

    def get_api(self) -> Optional[Dict[str, Any]]:
        pass

    def get_form(self) -> Optional[Dict[str, Any]]:
        return {
            "type": "form",
            "content": [
                {
                    "component": "VForm",
                    "content": [
                        {
                            "component": "VTextField",
                            "props": {
                                "model": "cookie",
                                "label": "115云盘Cookie",
                                "placeholder": "请输入115云盘Cookie"
                            }
                        }
                    ]
                }
            ]
        }

    def get_page(self) -> Optional[Dict[str, Any]]:
        pass

    def stop_service(self):
        pass

    def start_service(self):
        pass

    def sign(self):
        """
        执行签到
        """
        if not self._cookie:
            logger.error("未配置115云盘Cookie")
            return False

        try:
            # 设置Cookie
            self._headers["Cookie"] = self._cookie
            
            # 签到URL
            sign_url = "https://115.com/?ct=ajax&ac=user_sign"
            
            # 发送签到请求
            response = requests.get(sign_url, headers=self._headers)
            result = response.json()
            
            if result.get("state"):
                logger.info("115云盘签到成功")
                return True
            else:
                logger.error(f"115云盘签到失败: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"115云盘签到出错: {str(e)}")
            return False

    def update_config(self, config: Dict[str, Any] = None) -> None:
        if config:
            self._cookie = config.get("cookie")
            if self._cookie:
                self.sign() 