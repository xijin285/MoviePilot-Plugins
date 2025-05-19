import json
import time
import threading
from datetime import datetime, timedelta
from typing import Any, List, Dict, Tuple, Optional
from pathlib import Path

import pytz
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from moviepilot.core.plugin import PluginBase

class SiteLoginMonitor(PluginBase):
    # 插件名称
    plugin_name = "站点登录监控"
    # 插件描述
    plugin_desc = "监控站点登录状态，超过指定天数未登录时发送通知。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/sitemonitor.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    _config_prefix = "site_login_monitor_"
    # 加载顺序
    plugin_order = 10
    # 可使用的用户级别
    user_level = 1

    # 私有属性
    _scheduler: Optional[BackgroundScheduler] = None
    _lock: Optional[threading.Lock] = None
    _running: bool = False
    _max_history_entries: int = 100

    # 配置属性
    _enabled: bool = False
    _cron: str = "0 9 * * *"  # 每天早上9点检查
    _onlyonce: bool = False
    _notify: bool = False
    _max_days: int = 90  # 最大未登录天数
    _sites: List[Dict[str, Any]] = []  # 站点列表

    def init_plugin(self, config: Optional[dict] = None):
        self._lock = threading.Lock()
        self.stop_service()
        if config:
            self._enabled = bool(config.get("enabled", False))
            self._cron = str(config.get("cron", "0 9 * * *"))
            self._onlyonce = bool(config.get("onlyonce", False))
            self._notify = bool(config.get("notify", False))
            self._max_days = int(config.get("max_days", 90))
            self._sites = list(config.get("sites", []))
            self.__update_config()

        if self._enabled or self._onlyonce:
            if self._onlyonce:
                try:
                    if not self._scheduler or not self._scheduler.running:
                        self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                    job_name = f"{self.plugin_name}服务_onlyonce"
                    if self._scheduler.get_job(job_name):
                        self._scheduler.remove_job(job_name)
                    logger.info(f"{self.plugin_name} 服务启动，立即运行一次")
                    self._scheduler.add_job(func=self.run_check_job, trigger='date',
                                         run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                         name=job_name, id=job_name)
                    self._onlyonce = False
                    self.__update_config()
                    if self._scheduler and not self._scheduler.running:
                        self._scheduler.print_jobs()
                        self._scheduler.start()
                except Exception as e:
                    logger.error(f"启动一次性 {self.plugin_name} 任务失败: {str(e)}")

    def __update_config(self):
        self.update_config({
            "enabled": self._enabled,
            "notify": self._notify,
            "cron": self._cron,
            "onlyonce": self._onlyonce,
            "max_days": self._max_days,
            "sites": self._sites,
        })

    def get_state(self) -> bool:
        return self._enabled

    def get_command(self) -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []

    def get_service(self) -> List[Dict[str, Any]]:
        if self._enabled and self._cron:
            try:
                if str(self._cron).strip().count(" ") == 4:
                    return [{
                        "id": "SiteLoginMonitorService",
                        "name": f"{self.plugin_name}定时服务",
                        "trigger": CronTrigger.from_crontab(self._cron, timezone=settings.TZ),
                        "func": self.run_check_job,
                        "kwargs": {}
                    }]
                else:
                    logger.error(f"{self.plugin_name} cron表达式格式错误: {self._cron}")
                    return []
            except Exception as err:
                logger.error(f"{self.plugin_name} 定时任务配置错误：{str(err)}")
                return []
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSwitch', 'props': {'model': 'enabled', 'label': '启用插件'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSwitch', 'props': {'model': 'notify', 'label': '发送通知'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSwitch', 'props': {'model': 'onlyonce', 'label': '立即运行一次'}}]},
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'max_days', 'label': '最大未登录天数', 'type': 'number', 'min': 1, 'max': 365}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VCronField', 'props': {'model': 'cron', 'label': '执行周期'}}]}
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12}, 'content': [{'component': 'VDataTable', 'props': {'headers': [
                                {'title': '站点名称', 'key': 'name'},
                                {'title': '站点地址', 'key': 'url'},
                                {'title': '用户名', 'key': 'username'},
                                {'title': '密码', 'key': 'password', 'type': 'password'},
                                {'title': '上次登录时间', 'key': 'last_login'},
                            ], 'items': 'sites', 'editable': True}}]}
                        ],
                    },
                ],
            }
        ], {
            "enabled": False,
            "notify": False,
            "cron": "0 9 * * *",
            "onlyonce": False,
            "max_days": 90,
            "sites": [],
        }

    def get_page(self) -> List[dict]:
        return [
            {
                'component': 'VAlert',
                'props': {
                    'type': 'info',
                    'variant': 'tonal',
                    'text': '站点登录监控插件，用于监控站点登录状态，超过指定天数未登录时发送通知。',
                    'class': 'mb-2'
                }
            }
        ]

    def stop_service(self):
        try:
            if self._scheduler:
                job_name = f"{self.plugin_name}服务_onlyonce"
                if self._scheduler.get_job(job_name):
                    self._scheduler.remove_job(job_name)
                if self._lock and hasattr(self._lock, 'locked') and self._lock.locked():
                    logger.info(f"等待 {self.plugin_name} 当前任务执行完成...")
                    acquired = self._lock.acquire(timeout=300)
                    if acquired: self._lock.release()
                    else: logger.warning(f"{self.plugin_name} 等待任务超时。")
                if hasattr(self._scheduler, 'remove_all_jobs') and not self._scheduler.get_jobs(jobstore='default'):
                    pass
                elif hasattr(self._scheduler, 'remove_all_jobs'):
                    self._scheduler.remove_all_jobs()
                if hasattr(self._scheduler, 'running') and self._scheduler.running:
                    if not self._scheduler.get_jobs():
                        self._scheduler.shutdown(wait=False)
                        self._scheduler = None
                logger.info(f"{self.plugin_name} 服务已停止或已无任务。")
        except Exception as e:
            logger.error(f"{self.plugin_name} 退出插件失败：{str(e)}")

    def run_check_job(self):
        if not self._lock: self._lock = threading.Lock()
        if not self._lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 已有任务正在执行，本次调度跳过！")
            return

        try:
            self._running = True
            logger.info(f"开始执行 {self.plugin_name} 任务...")

            if not self._sites:
                logger.warning(f"{self.plugin_name} 未配置任何站点")
                return

            for site in self._sites:
                try:
                    self._check_site_login(site)
                except Exception as e:
                    logger.error(f"{self.plugin_name} 检查站点 {site.get('name', '未知')} 时出错: {str(e)}")

        except Exception as e:
            logger.error(f"{self.plugin_name} 任务执行主流程出错：{str(e)}")
        finally:
            self._running = False
            if self._lock and hasattr(self._lock, 'locked') and self._lock.locked():
                try: self._lock.release()
                except RuntimeError: pass
            logger.info(f"{self.plugin_name} 任务执行完成。")

    def _check_site_login(self, site: Dict[str, Any]):
        site_name = site.get('name', '未知站点')
        site_url = site.get('url', '')
        username = site.get('username', '')
        password = site.get('password', '')
        last_login = site.get('last_login', '')

        if not site_url or not username or not password:
            logger.warning(f"{self.plugin_name} 站点 {site_name} 配置不完整")
            return

        try:
            # 尝试登录站点
            session = requests.Session()
            response = session.post(site_url, data={
                'username': username,
                'password': password
            }, timeout=10)
            
            if response.status_code == 200:
                # 登录成功，更新最后登录时间
                site['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.__update_config()
                logger.info(f"{self.plugin_name} 站点 {site_name} 登录成功")
            else:
                logger.warning(f"{self.plugin_name} 站点 {site_name} 登录失败，状态码: {response.status_code}")
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 站点 {site_name} 登录出错: {str(e)}")
            return

        # 检查未登录天数
        if last_login:
            try:
                last_login_time = datetime.strptime(last_login, '%Y-%m-%d %H:%M:%S')
                days_since_login = (datetime.now() - last_login_time).days
                
                if days_since_login >= self._max_days:
                    message = f"站点 {site_name} 已超过 {self._max_days} 天未登录，请及时登录！"
                    logger.warning(message)
                    if self._notify:
                        self._send_notification(message=message)
            except Exception as e:
                logger.error(f"{self.plugin_name} 计算站点 {site_name} 未登录天数时出错: {str(e)}")

    def _send_notification(self, message: str):
        if not self._notify:
            return
        try:
            self.post_message(
                mtype=NotificationType.SiteMessage,
                title=f"{self.plugin_name}通知",
                text=message
            )
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送通知失败: {str(e)}") 