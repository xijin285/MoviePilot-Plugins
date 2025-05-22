import json
import time
import threading
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urljoin, quote

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType
from app.utils.http import RequestUtils
from app.utils.singleton import Singleton
from app.utils.string import StringUtils
from app.utils.system import SystemUtils
from app.scheduler import Scheduler
from apscheduler.triggers.cron import CronTrigger

class _115sign(_PluginBase):
    # 插件名称
    plugin_name = "115云盘签到"
    # 插件描述
    plugin_desc = "自动完成115云盘每日签到，支持相关配置功能"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/jxxghp/MoviePilot-Plugins/main/icons/115.png"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "115sign_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 2

    # 私有属性
    _enabled = False
    _cookie = None
    _notify = False
    _onlyonce = False
    _cron = None
    _history_days = 30  # 历史保留天数

    # 定时器
    _scheduler: Optional[BackgroundScheduler] = None
    _manual_trigger = False

    def init_plugin(self, config: Optional[dict] = None):
        if config:
            self._enabled = bool(config.get("enabled", False))
            self._cookie = str(config.get("cookie", ""))
            self._notify = bool(config.get("notify", False))
            self._onlyonce = bool(config.get("onlyonce", False))
            self._cron = str(config.get("cron", "0 9 * * *"))
            self._history_days = int(config.get("history_days", 30))

        # 停止现有任务
        self.stop_service()

        # 启动定时任务
        if self._enabled:
            self._scheduler = Scheduler()
            if self._cron:
                self._scheduler.add_job(self.sign,
                                     CronTrigger.from_crontab(self._cron),
                                     id="115sign")
                logger.info(f"115云盘签到服务启动，执行周期：{self._cron}")

            # 立即执行一次
            if self._onlyonce:
                self._scheduler.add_job(self.sign, 'date',
                                     run_date=datetime.now(),
                                     id="115sign_once")
                # 关闭一次性开关
                self._onlyonce = False
                self.update_config({
                    "enabled": self._enabled,
                    "cookie": self._cookie,
                    "notify": self._notify,
                    "onlyonce": self._onlyonce,
                    "cron": self._cron,
                    "history_days": self._history_days
                })

    def get_state(self) -> bool:
        return self._enabled

    def stop_service(self):
        """
        停止服务
        """
        try:
            if self._scheduler:
                self._scheduler.remove_job("115sign")
                self._scheduler.remove_job("115sign_once")
                self._scheduler = None
        except Exception as e:
            logger.error(f"停止115云盘签到服务失败：{str(e)}")

    def sign(self):
        """
        执行签到
        """
        if not self._cookie:
            logger.error("115云盘签到失败：未配置Cookie")
            self._send_notification(success=False, message="未配置Cookie")
            return

        try:
            # 构建请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Cookie": self._cookie
            }

            # 签到URL
            sign_url = "https://115.com/?ct=ajax&ac=user_sign"
            
            # 发送签到请求
            response = requests.get(sign_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            if result.get("state"):
                sign_days = result.get("data", {}).get("sign_days", 0)
                message = f"签到成功！已连续签到 {sign_days} 天"
                logger.info(f"115云盘签到成功：{message}")
                self._send_notification(success=True, message=message)
            else:
                error_msg = result.get("message", "未知错误")
                logger.error(f"115云盘签到失败：{error_msg}")
                self._send_notification(success=False, message=f"签到失败：{error_msg}")

        except Exception as e:
            logger.error(f"115云盘签到出错：{str(e)}")
            self._send_notification(success=False, message=f"签到出错：{str(e)}")

    def _send_notification(self, success: bool, message: str = ""):
        """
        发送通知
        """
        if not self._notify:
            return

        title = f"115云盘签到{'成功' if success else '失败'}"
        status_emoji = "✅" if success else "❌"
        
        # 构建通知内容
        content = f"{status_emoji} {message}"
        
        # 发送通知
        self.post_message(
            mtype=EventType.Notification,
            title=title,
            text=content
        )

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
                                    'md': 3
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
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'notify',
                                            'label': '开启通知',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'onlyonce',
                                            'label': '立即运行一次',
                                        }
                                    }
                                ]
                            },
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'cookie',
                                            'label': '115云盘Cookie',
                                            'placeholder': '请输入115云盘Cookie'
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
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VCronField',
                                        'props': {
                                            'model': 'cron',
                                            'label': '签到周期'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'history_days',
                                            'label': '历史保留天数',
                                            'type': 'number',
                                            'placeholder': '30'
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
                                            'text': '【使用说明】\n1. 填写115云盘的Cookie。\n2. 设置签到周期，例如每天上午9点执行 (0 9 * * *)。\n3. 可选开启通知，在签到完成后收到结果通知。\n4. 启用插件并保存即可。'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": self._enabled,
            "cookie": self._cookie,
            "notify": self._notify,
            "onlyonce": self._onlyonce,
            "cron": self._cron,
            "history_days": self._history_days
        }

    def get_page(self) -> List[dict]:
        pass

    def get_service(self) -> List[Dict[str, Any]]:
        if self._enabled and self._cron:
            logger.info(f"注册定时服务: {self._cron}")
            return [{
                "id": "115sign",
                "name": "115云盘签到",
                "trigger": CronTrigger.from_crontab(self._cron),
                "func": self.sign,
                "kwargs": {}
            }]
        return [] 