from typing import Any, List, Dict, Tuple
from datetime import datetime, timedelta
import os
import json
from moviepilot.core.event import EventManager
from moviepilot.core.plugin import PluginBase
from moviepilot.core.meta import MetaBase

class SiteLoginMonitor(PluginBase):
    # 插件名称
    plugin_name = "站点登录监控"
    # 插件描述
    plugin_desc = "监控站点多久没有登录访问，并发送通知"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/sitemonitor.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    _config_prefix = "siteloginmonitor_"
    # 权重
    plugin_order = 21
    # 可使用的用户级别
    user_level = 2

    # 配置项
    _sites_config = {
        "monitor_sites": {
            "name": "监控站点",
            "type": "list",
            "required": True,
            "default": [],
            "help": "需要监控的站点列表"
        },
        "notify_days": {
            "name": "通知天数",
            "type": "int",
            "required": True,
            "default": 7,
            "help": "超过多少天未登录时发送通知"
        }
    }

    def init_plugin(self, config: dict) -> None:
        self.monitor_sites = config.get('monitor_sites', [])
        self.notify_days = config.get('notify_days', 7)
        self.login_records_file = os.path.join(self.get_data_path(), "login_records.json")
        
        # 创建数据目录
        if not os.path.exists(self.get_data_path()):
            os.makedirs(self.get_data_path())
            
        # 加载登录记录
        self.login_records = self._load_login_records()
        
        # 注册定时任务
        self.register_scheduler(self.check_login_status, "interval", hours=24)

    def get_state(self) -> bool:
        return True

    def _load_login_records(self) -> Dict[str, str]:
        if os.path.exists(self.login_records_file):
            with open(self.login_records_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_login_records(self) -> None:
        with open(self.login_records_file, 'w', encoding='utf-8') as f:
            json.dump(self.login_records, f, ensure_ascii=False, indent=2)

    def update_login_time(self, site: str) -> None:
        """
        更新站点登录时间
        """
        self.login_records[site] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_login_records()

    def check_login_status(self) -> None:
        """
        检查登录状态
        """
        current_time = datetime.now()
        for site in self.monitor_sites:
            last_login = self.login_records.get(site)
            if not last_login:
                continue
                
            last_login_time = datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S")
            days_diff = (current_time - last_login_time).days
            
            if days_diff >= self.notify_days:
                self.send_notify(
                    title="站点登录提醒",
                    text=f"站点 {site} 已经 {days_diff} 天没有登录了，请注意查看！",
                    channel="web"
                )

    # 接收登录事件
    def on_site_login(self, site: str) -> None:
        """
        处理站点登录事件
        """
        if site in self.monitor_sites:
            self.update_login_time(site)

    def get_login_status(self) -> List[Dict[str, Any]]:
        """
        获取所有监控站点的登录状态
        """
        current_time = datetime.now()
        status_list = []
        
        for site in self.monitor_sites:
            last_login = self.login_records.get(site)
            if not last_login:
                days_diff = None
            else:
                last_login_time = datetime.strptime(last_login, "%Y-%m-%d %H:%M:%S")
                days_diff = (current_time - last_login_time).days
                
            status_list.append({
                "site": site,
                "last_login": last_login,
                "days_since_login": days_diff
            })
            
        return status_list 