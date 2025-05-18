import json
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Any, List, Dict, Tuple, Optional
from pathlib import Path

import pytz
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import ping3

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType

class DeviceMonitor(_PluginBase):
    # 插件名称
    plugin_name = "网络设备在线状态监控助手"
    # 插件描述
    plugin_desc = "监控家庭网络中设备的在线状态，统计使用时长，发送状态通知。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/monitor.png"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "device_monitor_"
    # 加载顺序
    plugin_order = 11
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _scheduler: Optional[BackgroundScheduler] = None
    _lock: Optional[threading.Lock] = None
    _running: bool = False
    _devices: Dict[str, Dict] = {}  # 存储设备信息
    
    # 配置属性
    _enabled: bool = False
    _check_interval: int = 5  # 检查间隔（分钟）
    _notify: bool = False
    _notification_style: int = 1
    
    def init_plugin(self, config: Optional[dict] = None):
        self._lock = threading.Lock()
        
        if config:
            self._enabled = bool(config.get("enabled", False))
            self._check_interval = int(config.get("check_interval", 5))
            self._notify = bool(config.get("notify", False))
            self._notification_style = int(config.get("notification_style", 1))
            
            # 加载设备列表
            devices = config.get("devices", [])
            for device in devices:
                name = device.get("name")
                ip = device.get("ip")
                if name and ip:
                    self._devices[ip] = {
                        "name": name,
                        "ip": ip,
                        "last_online": None,
                        "is_online": False,
                        "total_online_time": 0,
                        "status_history": []
                    }
            
            self.__update_config()

        # 启动监控服务
        if self._enabled:
            self.start_monitor_service()

    def start_monitor_service(self):
        """启动监控服务"""
        if not self._scheduler:
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
        
        job_id = f"{self.plugin_name}_monitor"
        if self._scheduler.get_job(job_id):
            self._scheduler.remove_job(job_id)
        
        self._scheduler.add_job(
            func=self.check_devices_status,
            trigger='interval',
            minutes=self._check_interval,
            id=job_id,
            name=job_id
        )
        
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info(f"{self.plugin_name} 监控服务已启动")

    def stop_service(self):
        """停止监控服务"""
        if self._scheduler:
            self._scheduler.shutdown()
            self._scheduler = None
        self._running = False
        logger.info(f"{self.plugin_name} 监控服务已停止")

    def check_devices_status(self):
        """检查所有设备状态"""
        with self._lock:
            current_time = datetime.now(tz=pytz.timezone(settings.TZ))
            
            for ip, device in self._devices.items():
                try:
                    # 使用ping检查设备在线状态
                    response_time = ping3.ping(ip, timeout=2)
                    is_online = response_time is not None
                    
                    # 更新设备状态
                    prev_status = device["is_online"]
                    device["is_online"] = is_online
                    
                    if is_online:
                        if not prev_status:  # 设备刚上线
                            device["last_online"] = current_time
                            if self._notify:
                                self._send_notification(
                                    title=f"设备上线通知",
                                    message=f"设备 {device['name']} ({ip}) 已上线"
                                )
                    else:
                        if prev_status:  # 设备刚下线
                            if device["last_online"]:
                                # 计算在线时长
                                online_duration = (current_time - device["last_online"]).total_seconds()
                                device["total_online_time"] += online_duration
                                
                                # 添加历史记录
                                device["status_history"].append({
                                    "start_time": device["last_online"].strftime("%Y-%m-%d %H:%M:%S"),
                                    "end_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "duration": online_duration
                                })
                                
                                if self._notify:
                                    self._send_notification(
                                        title=f"设备离线通知",
                                        message=f"设备 {device['name']} ({ip}) 已离线\n本次在线时长: {self._format_duration(online_duration)}"
                                    )
                    
                except Exception as e:
                    logger.error(f"检查设备 {ip} 状态时出错: {str(e)}")

    def _format_duration(self, seconds: float) -> str:
        """格式化时间长度"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}小时{minutes}分钟"

    def _send_notification(self, title: str, message: str):
        """发送通知"""
        if self._notification_style == 1:
            template = "★ {} ★\n{}"
            formatted_msg = template.format(title, message)
        elif self._notification_style == 2:
            template = "▇▇▇▇▇▇▇▇▇▇\n  {}\n{}\n▇▇▇▇▇▇▇▇▇▇"
            formatted_msg = template.format(title, message)
        else:
            template = "→→→ {} ←←←\n{}"
            formatted_msg = template.format(title, message)

        self.notify_module.send_message(
            title=title,
            text=formatted_msg,
            mtype=NotificationType.Message
        )

    def get_state(self) -> bool:
        return self._enabled

    def __update_config(self):
        config_data = {
            "enabled": self._enabled,
            "check_interval": self._check_interval,
            "notify": self._notify,
            "notification_style": self._notification_style,
            "devices": [
                {"name": device["name"], "ip": device["ip"]}
                for device in self._devices.values()
            ]
        }
        self.update_config(config_data)

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
                                'props': {'cols': 12, 'md': 4},
                                'content': [{'component': 'VSwitch', 'props': {'model': 'enabled', 'label': '启用插件'}}]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 4},
                                'content': [{'component': 'VSwitch', 'props': {'model': 'notify', 'label': '状态变化通知'}}]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'check_interval',
                                            'label': '检查间隔(分钟)',
                                            'type': 'number',
                                            'placeholder': '默认5分钟'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'notification_style',
                                            'label': '通知样式',
                                            'items': [
                                                {'title': '样式1 - 星星主题', 'value': 1},
                                                {'title': '样式2 - 方块主题', 'value': 2},
                                                {'title': '样式3 - 箭头主题', 'value': 3}
                                            ]
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
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'devices',
                                            'label': '监控设备列表',
                                            'placeholder': '每行一个设备，格式：设备名称,IP地址\n例如：\n我的手机,192.168.1.100\n电视盒子,192.168.1.101',
                                            'rows': 5
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
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': '【使用说明】\n1. 在设备列表中添加要监控的设备，每行一个，格式为：设备名称,IP地址\n2. 设置检查间隔时间（分钟）\n3. 可选开启状态变化通知，当设备上线或离线时收到通知\n4. 选择喜欢的通知样式\n5. 启用插件并保存即可开始监控'
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
            "notify": False,
            "check_interval": 5,
            "notification_style": 1,
            "devices": "我的手机,192.168.1.100\n电视盒子,192.168.1.101"
        }

    def get_page(self) -> List[dict]:
        """获取插件页面"""
        if not self._devices:
            return [
                {
                    'component': 'VAlert',
                    'props': {
                        'type': 'info',
                        'variant': 'tonal',
                        'text': '暂无监控设备。请在插件设置中添加要监控的设备。',
                        'class': 'mb-2'
                    }
                }
            ]

        device_cards = []
        for device in self._devices.values():
            # 计算在线时间
            total_time = self._format_duration(device["total_online_time"])
            status = "在线" if device["is_online"] else "离线"
            status_color = "success" if device["is_online"] else "error"
            last_online = device["last_online"].strftime("%Y-%m-%d %H:%M:%S") if device["last_online"] else "从未在线"

            device_cards.append({
                'component': 'VCard',
                'props': {'class': 'mb-4'},
                'content': [
                    {
                        'component': 'VCardItem',
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'content': [
                                    {'component': 'span', 'content': device["name"]},
                                    {
                                        'component': 'VChip',
                                        'props': {
                                            'color': status_color,
                                            'class': 'ml-2'
                                        },
                                        'content': status
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VCardText',
                        'content': [
                            f"IP地址：{device['ip']}\n",
                            f"最后在线：{last_online}\n",
                            f"累计在线时长：{total_time}"
                        ]
                    }
                ]
            })

        return device_cards 