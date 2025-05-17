import json
import time
import hashlib
import requests
from typing import List, Dict, Optional
from app.core.config import settings
from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import NotificationType
from app.utils.http import RequestUtils
from app.utils.system import SystemUtils
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 插件配置项 ID 前缀
PLUGIN_CONFIG_PREFIX = "ikuaibackup_"

class IKuaiBackup(_PluginBase):
    # 插件基础信息
    plugin_name = "爱快路由备份"
    plugin_desc = "定时备份爱快路由配置到本地"
    plugin_version = "1.0.0"
    plugin_author = "jinxi"
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/ikuai.png"
    author_url = "https://github.com/xijin285"
    auth_level = 1  # 普通用户可使用
    plugin_order = 70  # 加载顺序

    # 配置项
    _enabled: bool = False          # 是否启用插件
    _cron_enabled: bool = True      # 是否启用定时任务
    _cron: str = "0 0 2 * * *"      # 定时任务表达式（每天凌晨 2 点）
    _ikuai_url: str = ""            # 爱快路由管理地址（如 http://192.168.1.1）
    _username: str = ""             # 管理员用户名
    _password: str = ""             # 管理员密码
    _backup_dir: str = ""           # 本地备份目录（默认使用系统临时目录）
    _keep_days: int = 7             # 保留备份天数
    _notify: bool = True            # 是否发送通知
    _msg_type: NotificationType = NotificationType.Plugin  # 通知类型

    # 内部状态
    _scheduler = BackgroundScheduler(timezone=settings.TZ)
    _session_cookie: Optional[str] = None
    _login_token: Optional[str] = None

    def init_plugin(self, config: dict = None):
        if not config:
            return

        # 加载配置
        self._enabled = config.get("enabled", False)
        self._cron_enabled = config.get("cron_enabled", True)
        self._cron = config.get("cron", "0 0 2 * * *")
        self._ikuai_url = config.get("ikuai_url", "").rstrip("/")
        self._username = config.get("username", "")
        self._password = config.get("password", "")
        self._backup_dir = config.get("backup_dir", SystemUtils.get_temp_dir())
        self._keep_days = config.get("keep_days", 7)
        self._notify = config.get("notify", True)
        self._msg_type = NotificationType(config.get("msg_type", NotificationType.Plugin.value))

        # 初始化定时任务
        self.stop_service()
        if self._enabled and self._cron_enabled:
            self._scheduler.add_job(
                self.full_backup,
                trigger=CronTrigger.from_crontab(self._cron),
                name="爱快路由全量备份"
            )
            self._scheduler.start()

    def get_state(self) -> bool:
        return self._enabled

    def get_form(self) -> tuple[List[dict], Dict[str, Any]]:
        """
        配置页面表单定义
        """
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enabled",
                                            "label": "启用插件",
                                            "hint": "开启后插件将自动执行备份任务"
                                        }
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "cron_enabled",
                                            "label": "启用定时任务",
                                            "hint": "按指定周期自动备份"
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 8},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "ikuai_url",
                                            "label": "爱快路由地址",
                                            "placeholder": "http://192.168.1.1",
                                            "required": True
                                        }
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "username",
                                            "label": "用户名",
                                            "placeholder": "admin"
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "password",
                                            "label": "密码",
                                            "type": "password",
                                            "required": True
                                        }
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "backup_dir",
                                            "label": "备份目录",
                                            "placeholder": "系统临时目录（默认）"
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "keep_days",
                                            "label": "保留天数",
                                            "type": "number",
                                            "min": 1,
                                            "max": 90,
                                            "hint": "自动清理过期备份"
                                        }
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "notify",
                                            "label": "发送通知",
                                            "hint": "备份成功/失败时发送消息"
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
            "cron_enabled": True,
            "cron": "0 0 2 * * *",
            "ikuai_url": "",
            "username": "",
            "password": "",
            "backup_dir": "",
            "keep_days": 7,
            "notify": True,
            "msg_type": NotificationType.Plugin.value
        }

    def full_backup(self):
        """
        全量备份流程
        """
        try:
            # 1. 登录获取会话
            if not self._login():
                raise Exception("登录失败，检查用户名/密码")

            # 2. 创建配置备份
            backup_id = self._create_backup()
            if not backup_id:
                raise Exception("创建备份失败")

            # 3. 等待备份完成（爱快备份可能需要短暂时间）
            time.sleep(5)

            # 4. 获取最新备份文件
            backup_file = self._get_latest_backup()
            if not backup_file:
                raise Exception("获取备份文件列表失败")

            # 5. 下载备份文件
            save_path = self._download_backup(backup_file)
            if not save_path:
                raise Exception("下载备份失败")

            # 6. 清理过期备份
            self._clean_old_backups()

            # 发送通知
            self.__send_message(
                title="爱快路由备份成功",
                text=f"备份文件已保存至：{save_path}"
            )
            return True

        except Exception as e:
            logger.error(f"备份失败：{str(e)}")
            self.__send_message(
                title="爱快路由备份失败",
                text=f"错误信息：{str(e)}"
            )
            return False

    def _login(self) -> bool:
        """
        模拟登录爱快路由
        """
        login_url = f"{self._ikuai_url}/Action/Signin"
        password_md5 = hashlib.md5(self._password.encode()).hexdigest()  # 爱快密码使用 MD5 加密

        payload = {
            "username": self._username,
            "password": password_md5,
            "remember": "on"
        }

        try:
            response = RequestUtils().post(
                url=login_url,
                data=payload,
                allow_redirects=False
            )
            if response.status_code != 302:
                logger.error("登录失败，状态码异常")
                return False

            # 从响应头获取 sess_key
            sess_key = response.headers.get("Set-Cookie", "").split(";")[0]
            if not sess_key:
                logger.error("未获取到会话 Cookie")
                return False

            self._session_cookie = sess_key
            self._login_token = response.cookies.get("csrf_token")
            return True

        except Exception as e:
            logger.error(f"登录请求失败：{str(e)}")
            return False

    def _create_backup(self) -> Optional[str]:
        """
        创建配置备份
        """
        backup_url = f"{self._ikuai_url}/Action/Backup/Config"
        headers = {"Cookie": self._session_cookie}

        try:
            response = RequestUtils().post(
                url=backup_url,
                headers=headers,
                data={"type": "config"}
            )
            if response.status_code != 200:
                logger.error(f"创建备份失败，状态码：{response.status_code}")
                return None

            result = response.json()
            if result.get("status") != "success":
                logger.error(f"创建备份失败：{result.get('msg', '未知错误')}")
                return None

            return result.get("data", {}).get("id")

        except Exception as e:
            logger.error(f"创建备份请求失败：{str(e)}")
            return None

    def _get_latest_backup(self) -> Optional[str]:
        """
        获取最新备份文件名称
        """
        list_url = f"{self._ikuai_url}/Action/Backup/List"
        headers = {"Cookie": self._session_cookie}

        try:
            response = RequestUtils().get(
                url=list_url,
                headers=headers
            )
            if response.status_code != 200:
                logger.error(f"获取备份列表失败，状态码：{response.status_code}")
                return None

            backups = response.json().get("data", [])
            if not backups:
                logger.warning("无可用备份")
                return None

            # 按时间倒序排序，取最新
            latest = max(backups, key=lambda x: x["time"])
            return latest.get("filename")

        except Exception as e:
            logger.error(f"解析备份列表失败：{str(e)}")
            return None

    def _download_backup(self, filename: str) -> Optional[str]:
        """
        下载备份文件
        """
        download_url = f"{self._ikuai_url}/Action/Backup/Download?filename={filename}"
        headers = {"Cookie": self._session_cookie}

        try:
            response = requests.get(
                url=download_url,
                headers=headers,
                stream=True,
                timeout=300
            )
            if response.status_code != 200:
                logger.error(f"下载备份失败，状态码：{response.status_code}")
                return None

            # 保存文件
            save_path = f"{self._backup_dir}/{filename}"
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return save_path

        except Exception as e:
            logger.error(f"下载备份文件失败：{str(e)}")
            return None

    def _clean_old_backups(self):
        """
        清理过期备份文件
        """
        try:
            # 遍历目录，删除超过保留天数的文件
            now = time.time()
            for file in SystemUtils.list_files(self._backup_dir):
                if file.endswith(".bak"):
                    file_path = f"{self._backup_dir}/{file}"
                    mtime = SystemUtils.get_file_mtime(file_path)
                    if (now - mtime) > (self._keep_days * 86400):
                        SystemUtils.delete_file(file_path)
                        logger.info(f"删除过期备份：{file}")

        except Exception as e:
            logger.error(f"清理备份失败：{str(e)}")

    def __send_message(self, title: str, text: str):
        """
        发送通知
        """
        if not self._notify:
            return

        try:
            self.post_message(
                mtype=self._msg_type,
                title=title,
                text=text
            )
        except Exception as e:
            logger.error(f"发送通知失败：{str(e)}")

    def stop_service(self):
        """
        停止定时任务
        """
        if self._scheduler:
            self._scheduler.shutdown()
            self._scheduler = None

    def get_command(self) -> List[Dict[str, Any]]:
        """
        定义远程控制命令（可选）
        """
        return [
            {
                "cmd": "/ikuai_backup_now",
                "event": EventType.PluginAction,
                "desc": "立即执行爱快路由备份",
                "data": {"action": "backup_now"}
            }
        ]

    @eventmanager.register(EventType.PluginAction)
    def handle_command(self, event: Event):
        """
        处理远程命令
        """
        if event.event_data.get("action") == "backup_now":
            self.full_backup()

# 插件实例化
plugin = IKuaiBackup()
