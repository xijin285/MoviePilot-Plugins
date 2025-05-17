import hashlib
import json
import os
import re
import time
import threading
from datetime import datetime, timedelta
from typing import Any, List, Dict, Tuple, Optional
from urllib.parse import urljoin, quote
from pathlib import Path

import pytz
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import NotificationType

class IkuaiRouterBackup(_PluginBase):
    # 插件名称
    plugin_name = "爱快路由备份"
    # 插件描述
    plugin_desc = "自动备份爱快路由配置，并管理备份文件。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/madrays/MoviePilot-Plugins/main/icons/router.png"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "xijin285"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "ikuai_backup_"
    # 加载顺序
    plugin_order = 10
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _scheduler: Optional[BackgroundScheduler] = None
    _lock: Optional[threading.Lock] = None
    _running: bool = False
    _history_file_path: Optional[Path] = None
    _max_history_entries: int = 100 # Max number of history entries to keep

    # 配置属性
    _enabled: bool = False
    _cron: str = "0 3 * * *"
    _onlyonce: bool = False
    _notify: bool = False
    _retry_count: int = 3
    _retry_interval: int = 60
    
    _ikuai_url: str = ""
    _ikuai_username: str = "admin"
    _ikuai_password: str = ""
    _backup_path: str = ""
    _keep_backup_num: int = 7

    def init_plugin(self, config: Optional[dict] = None):
        self._lock = threading.Lock()
        self.stop_service()
        plugin_data_root = Path(self.get_data_path())
        try:
            plugin_data_root.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"{self.plugin_name} 创建插件数据根目录失败 {plugin_data_root}: {e}")
        self._history_file_path = plugin_data_root / "backup_history.json"

        if config:
            self._enabled = bool(config.get("enabled", False))
            self._cron = str(config.get("cron", "0 3 * * *"))
            self._onlyonce = bool(config.get("onlyonce", False))
            self._notify = bool(config.get("notify", False))
            self._retry_count = int(config.get("retry_count", 3))
            self._retry_interval = int(config.get("retry_interval", 60))
            self._ikuai_url = str(config.get("ikuai_url", "")).rstrip('/')
            self._ikuai_username = str(config.get("ikuai_username", "admin"))
            self._ikuai_password = str(config.get("ikuai_password", ""))
            configured_backup_path = str(config.get("backup_path", "")).strip()
            if not configured_backup_path:
                self._backup_path = str(plugin_data_root / "actual_backups")
                logger.info(f"{self.plugin_name} 备份文件存储路径未配置，使用默认: {self._backup_path}")
            else:
                self._backup_path = configured_backup_path
            self._keep_backup_num = int(config.get("keep_backup_num", 7))
            self.__update_config()

        try:
            Path(self._backup_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
             logger.error(f"{self.plugin_name} 创建实际备份目录 {self._backup_path} 失败: {e}")

        if self._enabled or self._onlyonce:
            if self._onlyonce:
                try:
                    if not self._scheduler or not self._scheduler.running:
                         self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                    job_name = f"{self.plugin_name}服务_onlyonce"
                    if self._scheduler.get_job(job_name):
                        self._scheduler.remove_job(job_name)
                    logger.info(f"{self.plugin_name} 服务启动，立即运行一次")
                    self._scheduler.add_job(func=self.run_backup_job, trigger='date',
                                         run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                         name=job_name, id=job_name)
                    self._onlyonce = False
                    self.__update_config()
                    if self._scheduler and not self._scheduler.running:
                        self._scheduler.print_jobs()
                        self._scheduler.start()
                except Exception as e:
                    logger.error(f"启动一次性 {self.plugin_name} 任务失败: {str(e)}")
    
    def _load_backup_history(self) -> List[Dict[str, Any]]:
        if not self._history_file_path or not self._history_file_path.exists():
            return []
        try:
            with open(self._history_file_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
                return history if isinstance(history, list) else []
        except json.JSONDecodeError:
            logger.error(f"{self.plugin_name} 历史记录文件 {self._history_file_path} 格式错误。")
            return []
        except Exception as e:
            logger.error(f"{self.plugin_name} 加载历史记录 {self._history_file_path} 失败: {e}")
            return []

    def _save_backup_history_entry(self, entry: Dict[str, Any]):
        if not self._history_file_path:
            logger.error(f"{self.plugin_name} 历史记录文件路径未设置。")
            return
        history = self._load_backup_history()
        history.insert(0, entry)
        if len(history) > self._max_history_entries:
            history = history[:self._max_history_entries]
        try:
            with open(self._history_file_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"{self.plugin_name} 保存历史记录到 {self._history_file_path} 失败: {e}")

    def __update_config(self):
        self.update_config({
            "enabled": self._enabled,
            "notify": self._notify,
            "cron": self._cron,
            "onlyonce": self._onlyonce,
            "retry_count": self._retry_count,
            "retry_interval": self._retry_interval,
            "ikuai_url": self._ikuai_url,
            "ikuai_username": self._ikuai_username,
            "ikuai_password": self._ikuai_password,
            "backup_path": self._backup_path,
            "keep_backup_num": self._keep_backup_num,
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
                        "id": "IkuaiRouterBackupService",
                        "name": f"{self.plugin_name}定时服务",
                        "trigger": CronTrigger.from_crontab(self._cron, timezone=settings.TZ),
                        "func": self.run_backup_job,
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
        default_backup_location_desc = "插件数据目录下的 actual_backups 子目录"
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
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'ikuai_url', 'label': '爱快路由地址', 'placeholder': '例如: http://10.0.0.1'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VCronField', 'props': {'model': 'cron', 'label': '执行周期'}}]}
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'ikuai_username', 'label': '用户名', 'placeholder': '默认为 admin'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'ikuai_password', 'label': '密码', 'type': 'password', 'placeholder': '请输入密码'}}]},
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 8}, 'content': [{'component': 'VTextField', 'props': {'model': 'backup_path', 'label': '备份文件存储路径', 'placeholder': f'默认为{default_backup_location_desc}'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VTextField', 'props': {'model': 'keep_backup_num', 'label': '备份保留数量', 'type': 'number', 'placeholder': '例如: 7'}}]},
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                             {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VTextField', 'props': {'model': 'retry_count', 'label': '最大重试次数', 'type': 'number', 'placeholder': '3'}}]},
                             {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VTextField', 'props': {'model': 'retry_interval', 'label': '重试间隔(秒)', 'type': 'number', 'placeholder': '60'}}]},
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [{'component': 'VCol', 'props': {'cols': 12}, 'content': [{'component': 'VAlert', 'props': {'type': 'info', 'variant': 'tonal', 'text': f'【使用说明】\n1. 填写爱快路由的访问地址、用户名和密码。\n2. 备份文件存储路径：可留空，默认为{default_backup_location_desc}。或指定一个绝对路径。确保MoviePilot有权访问和写入此路径。\n3. 设置执行周期，例如每天凌晨3点执行 (0 3 * * *)。\n4. 设置备份文件保留数量，旧的备份会被自动删除。\n5. 可选开启通知，在备份完成后收到结果通知。\n6. 启用插件并保存即可。\n7. 备份文件将以.bak后缀保存。'}}]}]
                    }
                ]
            }
        ], {
            "enabled": False, "notify": False, "cron": "0 3 * * *", "onlyonce": False,
            "retry_count": 3, "retry_interval": 60, "ikuai_url": "", "ikuai_username": "admin",
            "ikuai_password": "", "backup_path": "", "keep_backup_num": 7
        }

    def get_page(self) -> List[dict]:
        history_data = self._load_backup_history()
        table_items = []
        for item in history_data:
            table_items.append({
                "timestamp": datetime.fromtimestamp(item.get("timestamp",0)).strftime('%Y-%m-%d %H:%M:%S') if item.get("timestamp") else "N/A",
                "status": "成功" if item.get("success") else "失败",
                "filename": item.get("filename", "N/A"),
                "message": item.get("message", "")
            })

        return [
            {
                "component": "VCard",
                "props": {"variant": "outlined", "class": "mb-4"},
                "content": [
                    {
                        "component": "VCardTitle",
                        "props": {"class": "text-h6"},
                        "text": "📊 爱快路由备份历史"
                    },
                    {
                        "component": "VCardText",
                        "content": [
                            {
                                "component": "VDataTable",
                                "props": {
                                    "headers": [
                                        {"title": "时间", "key": "timestamp", "sortable": True},
                                        {"title": "状态", "key": "status", "sortable": True},
                                        {"title": "备份文件名 (.bak)", "key": "filename", "sortable": False},
                                        {"title": "消息", "key": "message", "sortable": False},
                                    ],
                                    "items": table_items,
                                    "items-per-page": 15,
                                    "multi-sort": True,
                                    "hover": True,
                                    "density": "compact"
                                }
                            }
                        ]
                    }
                ]
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

    def run_backup_job(self):
        if not self._lock: self._lock = threading.Lock()
        if not self._lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 已有任务正在执行，本次调度跳过！")
            return
            
        history_entry = {
            "timestamp": time.time(),
            "success": False,
            "filename": None,
            "message": "任务开始"
        }
            
        try:
            self._running = True
            logger.info(f"开始执行 {self.plugin_name} 任务...")

            if not self._ikuai_url or not self._ikuai_username or not self._ikuai_password:
                error_msg = "配置不完整：URL、用户名或密码未设置。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_notification(success=False, message=error_msg)
                history_entry["message"] = error_msg
                self._save_backup_history_entry(history_entry)
                return

            if not self._backup_path:
                error_msg = "备份路径未配置且无法设置默认路径。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_notification(success=False, message=error_msg)
                history_entry["message"] = error_msg
                self._save_backup_history_entry(history_entry)
                return

            try:
                Path(self._backup_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                error_msg = f"创建本地备份目录 {self._backup_path} 失败: {e}"
                logger.error(f"{self.plugin_name} {error_msg}")
                self._send_notification(success=False, message=error_msg)
                history_entry["message"] = error_msg
                self._save_backup_history_entry(history_entry)
                return
            
            success_final = False
            error_msg_final = "未知错误"
            downloaded_file_final = None
            
            for i in range(self._retry_count + 1):
                logger.info(f"{self.plugin_name} 开始第 {i+1}/{self._retry_count +1} 次备份尝试...")
                current_try_success, current_try_error_msg, current_try_downloaded_file = self._perform_backup_once()
                
                if current_try_success:
                    success_final = True
                    downloaded_file_final = current_try_downloaded_file
                    error_msg_final = None
                    logger.info(f"{self.plugin_name} 第{i+1}次尝试成功。备份文件: {downloaded_file_final}")
                    break 
                else:
                    error_msg_final = current_try_error_msg
                    logger.warning(f"{self.plugin_name} 第{i+1}次备份尝试失败: {error_msg_final}")
                    if i < self._retry_count:
                        logger.info(f"{self._retry_interval}秒后重试...")
                        time.sleep(self._retry_interval)
                    else:
                        logger.error(f"{self.plugin_name} 所有 {self._retry_count +1} 次尝试均失败。最后错误: {error_msg_final}")
            
            history_entry["success"] = success_final
            history_entry["filename"] = downloaded_file_final
            history_entry["message"] = "备份成功" if success_final else f"备份失败: {error_msg_final}"
            
            self._send_notification(success=success_final, message=history_entry["message"], filename=downloaded_file_final)
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 任务执行主流程出错：{str(e)}")
            history_entry["message"] = f"任务执行主流程出错: {str(e)}"
            self._send_notification(success=False, message=history_entry["message"])
        finally:
            self._running = False
            self._save_backup_history_entry(history_entry)
            if self._lock and hasattr(self._lock, 'locked') and self._lock.locked():
                try: self._lock.release()
                except RuntimeError: pass
            logger.info(f"{self.plugin_name} 任务执行完成。")

    def _perform_backup_once(self) -> Tuple[bool, Optional[str], Optional[str]]:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        
        sess_key_part = self._login_ikuai(session)
        if not sess_key_part:
            return False, "登录爱快路由失败，无法获取SESS_KEY", None
        
        cookie_string = f"username={quote(self._ikuai_username)}; {sess_key_part}; login=1"
        session.headers.update({"Cookie": cookie_string, "User-Agent": settings.USER_AGENT})
        
        create_success, create_msg = self._create_backup_on_router(session)
        if not create_success:
            return False, f"创建备份失败: {create_msg}", None
        logger.info(f"{self.plugin_name} 成功触发创建备份。等待5秒让备份生成...")
        time.sleep(5)

        backup_list = self._get_backup_list(session)
        if backup_list is None:
             return False, "获取备份文件列表时出错", None
        if not backup_list:
            return False, "路由器上没有找到任何备份文件", None
        
        latest_backup = backup_list[0]
        actual_router_filename = latest_backup.get("file_name")
        if not actual_router_filename:
            return False, "无法从备份列表中获取最新备份的文件名", None
            
        if not isinstance(actual_router_filename, str):
             logger.error(f"{self.plugin_name} Router filename is not a string: {actual_router_filename}")
             return False, "路由器返回的文件名格式不正确", None

        display_and_saved_filename = Path(actual_router_filename).stem + ".bak"
        local_filepath_to_save = Path(self._backup_path) / display_and_saved_filename
            
        logger.info(f"{self.plugin_name} 最新备份文件在路由: {actual_router_filename}, 将保存为: {display_and_saved_filename}")

        download_success, download_msg = self._download_backup_file(session, actual_router_filename, str(local_filepath_to_save))
        if not download_success:
            return False, f"下载备份文件 {actual_router_filename} (保存为 {display_and_saved_filename}) 失败: {download_msg}", None
        
        logger.info(f"{self.plugin_name} 备份文件 {display_and_saved_filename} 已成功下载到 {local_filepath_to_save}")
        self._cleanup_old_backups()
        return True, None, display_and_saved_filename

    def _login_ikuai(self, session: requests.Session) -> Optional[str]:
        login_url = urljoin(self._ikuai_url, "/Action/login")
        password_md5 = hashlib.md5(self._ikuai_password.encode('utf-8')).hexdigest()
        login_data = {"username": self._ikuai_username, "passwd": password_md5}
        try:
            logger.info(f"{self.plugin_name} 尝试登录到 {self._ikuai_url}...")
            response = session.post(login_url, data=json.dumps(login_data), headers={'Content-Type': 'application/json', "User-Agent": settings.USER_AGENT}, timeout=10)
            response.raise_for_status()
            cookies = response.cookies
            sess_key_value = cookies.get("sess_key")
            if sess_key_value:
                logger.info(f"{self.plugin_name} 登录成功，获取到 sess_key。")
                return f"sess_key={sess_key_value}"
            set_cookie_header = response.headers.get('Set-Cookie')
            if set_cookie_header:
                match = re.search(r'sess_key=([^;]+)', set_cookie_header)
                if match:
                    logger.info(f"{self.plugin_name} 登录成功，从Set-Cookie头获取到 sess_key。")
                    return f"sess_key={match.group(1)}"
            logger.error(f"{self.plugin_name} 登录成功但未能从Cookie或头部提取 sess_key。响应: {response.text[:200]}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 登录请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} 登录过程中发生未知错误: {e}")
            return None

    def _create_backup_on_router(self, session: requests.Session) -> Tuple[bool, Optional[str]]:
        create_url = urljoin(self._ikuai_url, "/Action/call")
        backup_data = {"func_name": "backup", "action": "create", "param": {}}
        try:
            logger.info(f"{self.plugin_name} 尝试在 {self._ikuai_url} 创建新备份...")
            response = session.post(create_url, data=json.dumps(backup_data), headers={'Content-Type': 'application/json', "User-Agent": settings.USER_AGENT}, timeout=30)
            response.raise_for_status()
            response_text = response.text.strip().lower()
            if "success" in response_text or response_text == '"success"':
                 logger.info(f"{self.plugin_name} 备份创建请求发送成功。响应: {response_text}")
                 return True, None
            try:
                res_json = response.json()
                if res_json.get("Ret") == 0 and "success" in str(res_json.get("Data")).lower():
                    logger.info(f"{self.plugin_name} 备份创建请求成功 (JSON)。响应: {res_json}")
                    return True, None
                err_msg = res_json.get("ErrMsg", "创建备份API未返回成功")
                logger.error(f"{self.plugin_name} 备份创建失败 (JSON)。响应: {res_json}, 错误: {err_msg}")
                return False, f"路由器返回错误: {err_msg}"
            except json.JSONDecodeError:
                logger.error(f"{self.plugin_name} 备份创建失败，非JSON响应且不含 'success'。响应: {response_text}")
                return False, f"路由器返回非预期响应: {response_text[:100]}"
        except requests.exceptions.Timeout:
            logger.warning(f"{self.plugin_name} 创建备份请求超时。备份可能仍在后台进行。")
            return True, "请求超时，但备份可能已开始创建"
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 创建备份请求失败: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"{self.plugin_name} 创建备份过程中发生未知错误: {e}")
            return False, str(e)

    def _get_backup_list(self, session: requests.Session) -> Optional[List[Dict]]:
        list_url = urljoin(self._ikuai_url, "/Action/call")
        list_data = {"func_name": "backup", "action": "show", "param": {"ORDER": "desc", "ORDER_BY": "time", "LIMIT": "0,50"}}
        try:
            logger.info(f"{self.plugin_name} 尝试从 {self._ikuai_url} 获取备份列表...")
            response = session.post(list_url, data=json.dumps(list_data), headers={'Content-Type': 'application/json', "User-Agent": settings.USER_AGENT}, timeout=15)
            response.raise_for_status()
            res_json = response.json()
            if res_json.get("Ret") == 0:
                data = res_json.get("Data", {})
                total = data.get("total", 0)
                backup_items = data.get("data", [])
                if total > 0 and isinstance(backup_items, list) and backup_items:
                    logger.info(f"{self.plugin_name} 成功获取到 {len(backup_items)} 条备份记录 (总计 {total})。")
                    return backup_items
                else:
                    logger.warning(f"{self.plugin_name} 获取备份列表成功，但列表为空或格式不正确。Total: {total}, Data: {backup_items}")
                    return []
            else:
                err_msg = res_json.get("ErrMsg", "获取列表API未返回成功")
                logger.error(f"{self.plugin_name} 获取备份列表失败。响应: {res_json}, 错误: {err_msg}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 获取备份列表请求失败: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"{self.plugin_name} 获取备份列表响应非JSON格式: {response.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取备份列表过程中发生未知错误: {e}")
            return None

    def _download_backup_file(self, session: requests.Session, router_filename: str, local_filepath_to_save: str) -> Tuple[bool, Optional[str]]:
        safe_router_filename = quote(router_filename)
        download_url1 = urljoin(self._ikuai_url, f"/Download/{safe_router_filename}")
        download_url2 = urljoin(self._ikuai_url, f"/Action/download?filename={safe_router_filename}")
        urls_to_try = [download_url1, download_url2]
        last_error = None

        for i, dl_url in enumerate(urls_to_try):
            logger.info(f"{self.plugin_name} 尝试下载备份文件 {router_filename} 从 {dl_url} (尝试 {i+1}/{len(urls_to_try)}), 保存到 {local_filepath_to_save}...")
            try:
                with session.get(dl_url, stream=True, timeout=300, headers={"User-Agent": settings.USER_AGENT}) as r:
                    r.raise_for_status()
                    content_type = r.headers.get('Content-Type', '').lower()
                    if 'text/html' in content_type and dl_url == download_url1:
                        logger.warning(f"{self.plugin_name} 下载 {router_filename} 从 {dl_url} 收到HTML, 可能为错误页面。")
                        last_error = f"收到HTML页面而不是文件从 {dl_url}"
                        continue
                    with open(local_filepath_to_save, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logger.info(f"{self.plugin_name} 文件 {router_filename} 下载完成，保存至 {local_filepath_to_save}")
                    return True, None
            except requests.exceptions.HTTPError as e:
                last_error = f"HTTP错误 ({e.response.status_code}) 从 {dl_url}: {e}"
                logger.warning(f"{self.plugin_name} 下载 {router_filename} 从 {dl_url} 失败: {last_error}")
            except requests.exceptions.RequestException as e:
                last_error = f"请求错误从 {dl_url}: {e}"
                logger.warning(f"{self.plugin_name} 下载 {router_filename} 从 {dl_url} 失败: {last_error}")
            except Exception as e:
                last_error = f"未知错误从 {dl_url}: {e}"
                logger.error(f"{self.plugin_name} 下载 {router_filename} 从 {dl_url} 过程中发生未知错误: {last_error}")
        
        logger.error(f"{self.plugin_name} 所有尝试下载 {router_filename} 均失败。最后错误: {last_error}")
        return False, last_error

    def _cleanup_old_backups(self):
        if not self._backup_path or self._keep_backup_num <= 0: return
        try:
            logger.info(f"{self.plugin_name} 开始清理本地备份目录: {self._backup_path}, 保留数量: {self._keep_backup_num} (仅处理 .bak 文件)")
            backup_dir = Path(self._backup_path)
            if not backup_dir.is_dir():
                logger.warning(f"{self.plugin_name} 本地备份目录 {self._backup_path} 不存在，无需清理。")
                return

            files = []
            for f_path_obj in backup_dir.iterdir():
                if f_path_obj.is_file() and f_path_obj.suffix.lower() == ".bak":
                    try:
                        match = re.search(r'(\d{4}\d{2}\d{2}[_]?\d{2}\d{2}\d{2})', f_path_obj.stem)
                        file_time = None
                        if match:
                            time_str = match.group(1).replace('_','')
                            try:
                                file_time = datetime.strptime(time_str, '%Y%m%d%H%M%S').timestamp()
                            except ValueError:
                                pass 
                        if file_time is None:
                           file_time = f_path_obj.stat().st_mtime
                        files.append({'path': f_path_obj, 'name': f_path_obj.name, 'time': file_time})
                    except Exception as e:
                        logger.error(f"{self.plugin_name} 处理文件 {f_path_obj.name} 时出错: {e}")
                        try:
                            files.append({'path': f_path_obj, 'name': f_path_obj.name, 'time': f_path_obj.stat().st_mtime})
                        except Exception as stat_e:
                            logger.error(f"{self.plugin_name} 无法获取文件状态 {f_path_obj.name}: {stat_e}")

            files.sort(key=lambda x: x['time'], reverse=True)
            
            if len(files) > self._keep_backup_num:
                files_to_delete = files[self._keep_backup_num:]
                logger.info(f"{self.plugin_name} 找到 {len(files_to_delete)} 个旧 .bak 备份文件需要删除。")
                for f_info in files_to_delete:
                    try:
                        f_info['path'].unlink()
                        logger.info(f"{self.plugin_name} 已删除旧备份文件: {f_info['name']}")
                    except OSError as e:
                        logger.error(f"{self.plugin_name} 删除旧备份文件 {f_info['name']} 失败: {e}")
            else:
                logger.info(f"{self.plugin_name} 当前 .bak 备份数量 ({len(files)}) 未超过保留限制 ({self._keep_backup_num})，无需清理。")
        except Exception as e:
            logger.error(f"{self.plugin_name} 清理旧备份文件时发生错误: {e}")

    def _send_notification(self, success: bool, message: str = "", filename: Optional[str] = None):
        if not self._notify: return
        title = f"🛠️ {self.plugin_name} "
        title += "成功" if success else "失败"
        status_emoji = "✅" if success else "❌"
        
        text_content = f"状态：{status_emoji} {'备份成功' if success else '备份失败'}\n"
        text_content += f"路由：{self._ikuai_url}\n"
        if filename:
            text_content += f"文件：{filename}\n"
        if message:
            text_content += f"详情：{message.strip()}\n"
        text_content += f"\n⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            self.post_message(mtype=NotificationType.PluginMessage, title=title, text=text_content)
            logger.info(f"{self.plugin_name} 发送通知: {title}")
        except Exception as e:
            logger.error(f"{self.plugin_name} 发送通知失败: {e}")
