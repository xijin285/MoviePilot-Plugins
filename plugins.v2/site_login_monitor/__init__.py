from datetime import datetime, timedelta
from typing import Dict, Any
from app.core.config import settings
from app.log import logger
from app.plugins import Plugin
from app.schemas.types import NotificationType

class SiteLoginMonitor(Plugin):
    """
    站点登录状态监控插件
    监控站点多久没有登录，超过设定时间后发送通知
    """
    # 插件名称
    plugin_name = "站点登录监控"
    # 插件描述
    plugin_desc = "监控站点登录状态，超时未登录发送通知"
   # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/sitemonitor.png"    # 插件版本
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "xijin285"
    # 作者主页
    author_url = "https://github.com/xijin285/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "siteloginmonitor_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    def __init__(self):
        super().__init__()
        self._scheduler = None
        self._last_login_time = {}
        self._check_interval = 60  # 检查间隔（分钟）
        self._timeout_hours = 24   # 超时时间（小时）

    def init_plugin(self, config: Dict[str, Any] = None):
        """
        初始化插件
        """
        if config:
            self._check_interval = config.get("check_interval", 60)
            self._timeout_hours = config.get("timeout_hours", 24)

        # 启动定时任务
        self._scheduler = self.start_scheduler(
            func=self.check_site_login,
            interval=timedelta(minutes=self._check_interval)
        )

    def get_state(self) -> bool:
        """
        获取插件状态
        """
        return True if self._scheduler else False

    def stop_service(self):
        """
        停止插件
        """
        if self._scheduler:
            self._scheduler.remove_all_jobs()
            self._scheduler = None

    def check_site_login(self):
        """
        检查站点登录状态
        """
        try:
            # 获取所有站点
            sites = self.get_sites()
            current_time = datetime.now()

            for site in sites:
                site_name = site.get("name")
                last_login = site.get("last_login_time")

                if not last_login:
                    continue

                last_login_time = datetime.fromisoformat(last_login)
                time_diff = current_time - last_login_time

                # 如果超过设定时间未登录
                if time_diff > timedelta(hours=self._timeout_hours):
                    # 发送通知
                    self.send_notification(
                        title=f"站点登录提醒",
                        text=f"站点 {site_name} 已经 {int(time_diff.total_seconds() / 3600)} 小时未登录",
                        mtype=NotificationType.SiteMessage
                    )
                    logger.warning(f"站点 {site_name} 已经 {int(time_diff.total_seconds() / 3600)} 小时未登录")

        except Exception as e:
            logger.error(f"检查站点登录状态失败: {str(e)}")

    def get_sites(self) -> list:
        """
        获取所有站点信息
        """
        # 这里需要根据实际情况实现获取站点信息的逻辑
        # 返回格式示例：[{"name": "站点1", "last_login_time": "2024-01-01T00:00:00"}]
        return [] 