import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.config import settings
from app.log import logger
from app.plugins import PluginManager
from app.schemas.types import NotificationType
from app.utils.http import RequestUtils
from app.utils.singleton import Singleton


class SiteLoginMonitor(PluginManager, metaclass=Singleton):
    """
    站点登录监控插件
    """
    # 插件名称
    plugin_name = "站点登录监控"
    # 插件描述
    plugin_desc = "监控站点登录状态，超过指定天数未登录时发送通知"
    # 插件图标
    plugin_icon = "monitor.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "siteloginmonitor_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 2

    def __init__(self):
        super().__init__()
        # 站点列表
        self._sites: Dict[str, Dict] = {}
        # 上次检查时间
        self._last_check_time = None
        # 检查间隔（小时）
        self._check_interval = 24
        # 通知阈值（天）
        self._notify_threshold = 7

    def init_plugin(self, config: dict = None):
        """
        初始化插件
        """
        if not config:
            return
        # 加载配置
        self._sites = config.get("sites", {})
        self._check_interval = config.get("check_interval", 24)
        self._notify_threshold = config.get("notify_threshold", 7)
        
        # 启动定时任务
        self.start_service()

    def get_state(self) -> bool:
        """
        获取插件状态
        """
        return True

    def stop_service(self):
        """
        停止插件
        """
        pass

    def start_service(self):
        """
        启动插件
        """
        # 启动定时任务
        self.scheduler.add_job(
            self.check_sites_login,
            'interval',
            hours=self._check_interval,
            id="site_login_monitor"
        )

    def check_sites_login(self):
        """
        检查站点登录状态
        """
        if not self._sites:
            return

        current_time = datetime.now()
        for site_name, site_info in self._sites.items():
            last_login = site_info.get("last_login")
            if not last_login:
                continue

            last_login_time = datetime.fromisoformat(last_login)
            days_not_login = (current_time - last_login_time).days

            if days_not_login >= self._notify_threshold:
                # 发送通知
                self.send_notify(
                    title=f"站点登录提醒",
                    text=f"站点 {site_name} 已经 {days_not_login} 天未登录，请及时登录！",
                    notification_type=NotificationType.SiteMessage
                )

    def update_site_login_time(self, site_name: str):
        """
        更新站点登录时间
        """
        if site_name in self._sites:
            self._sites[site_name]["last_login"] = datetime.now().isoformat()
            # 保存配置
            self.save_config()

    def save_config(self):
        """
        保存配置
        """
        self.update_config({
            "sites": self._sites,
            "check_interval": self._check_interval,
            "notify_threshold": self._notify_threshold
        }) 