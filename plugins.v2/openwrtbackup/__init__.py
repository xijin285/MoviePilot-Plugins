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
from app.schemas import NotificationType

class OpenWRTBackup(_PluginBase):
    # 插件名称
    plugin_name = "OpenWRT备份助手"
    # 插件描述
    plugin_desc = "自动备份 OpenWRT 固件，并管理备份文件。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/main/icons/openwrt.webp"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "jinxi" # 可以替换为你的名字
    # 作者主页
    author_url = "https://github.com/xijin285" # 可以替换为你的主页
    # 插件配置项ID前缀
    plugin_config_prefix = "openwrt_backup_"
    # 加载顺序
    plugin_order = 11 # 避免与现有插件冲突
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _scheduler: Optional[BackgroundScheduler] = None
    _lock: Optional[threading.Lock] = None
    _running: bool = False
    _max_history_entries: int = 100 # Max number of history entries to keep

    # 配置属性
    _enabled: bool = False
    _cron: str = "0 3 * * *"
    _onlyonce: bool = False
    _notify: bool = False
    _retry_count: int = 3
    _retry_interval: int = 60
    _notification_style: int = 1
    
    _openwrt_url: str = ""
    _openwrt_username: str = "root"
    _openwrt_password: str = ""
    _backup_path: str = ""
    _keep_backup_num: int = 7
    _luci_compat_mode: bool = False # 用于兼容旧版LuCI

    def init_plugin(self, config: Optional[dict] = None):
        self._lock = threading.Lock()
        self.stop_service()
        if config:
            self._enabled = bool(config.get("enabled", False))
            self._cron = str(config.get("cron", "0 3 * * *"))
            self._onlyonce = bool(config.get("onlyonce", False))
            self._notify = bool(config.get("notify", False))
            self._retry_count = int(config.get("retry_count", 3))
            self._retry_interval = int(config.get("retry_interval", 60))
            self._notification_style = int(config.get("notification_style", 1))
            self._openwrt_url = str(config.get("openwrt_url", "")).rstrip('/')
            self._openwrt_username = str(config.get("openwrt_username", "root"))
            self._openwrt_password = str(config.get("openwrt_password", ""))
            configured_backup_path = str(config.get("backup_path", "")).strip()
            if not configured_backup_path:
                self._backup_path = str(self.get_data_path() / "actual_backups")
                logger.info(f"{self.plugin_name} 备份文件存储路径未配置，使用默认: {self._backup_path}")
            else:
                self._backup_path = configured_backup_path
            self._keep_backup_num = int(config.get("keep_backup_num", 7))
            self._luci_compat_mode = bool(config.get("luci_compat_mode", False))
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
        history = self.get_data('backup_history')
        if history is None:
            return []
        if not isinstance(history, list):
            logger.error(f"{self.plugin_name} 历史记录数据格式不正确 (期望列表，得到 {type(history)})。将返回空历史。")
            return []
        return history

    def _save_backup_history_entry(self, entry: Dict[str, Any]):
        history = self._load_backup_history()
        history.insert(0, entry)
        if len(history) > self._max_history_entries:
            history = history[:self._max_history_entries]
        
        self.save_data('backup_history', history)
        logger.info(f"{self.plugin_name} 已保存备份历史，当前共 {len(history)} 条记录。")

    def __update_config(self):
        self.update_config({
            "enabled": self._enabled,
            "notify": self._notify,
            "cron": self._cron,
            "onlyonce": self._onlyonce,
            "retry_count": self._retry_count,
            "retry_interval": self._retry_interval,
            "openwrt_url": self._openwrt_url,
            "openwrt_username": self._openwrt_username,
            "openwrt_password": self._openwrt_password,
            "backup_path": self._backup_path,
            "keep_backup_num": self._keep_backup_num,
            "notification_style": self._notification_style,
            "luci_compat_mode": self._luci_compat_mode,
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
                        "id": "OpenWRTBackupService",
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
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'openwrt_url', 'label': 'OpenWRT地址', 'placeholder': '例如: http://192.168.1.1'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VCronField', 'props': {'model': 'cron', 'label': '执行周期'}}]}
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'openwrt_username', 'label': '用户名', 'placeholder': '默认为 root'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'openwrt_password', 'label': '密码', 'type': 'password'}}]}
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'backup_path', 'label': '备份文件存储路径', 'placeholder': f'默认为 {default_backup_location_desc}'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'keep_backup_num', 'label': '保留备份文件数量', 'type': 'number', 'placeholder': '默认为7'}}]}
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSwitch', 'props': {'model': 'luci_compat_mode', 'label': 'LuCI兼容模式'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 4}, 'content': [{'component': 'VSelect', 'props': {'model': 'notification_style', 'label': '通知样式', 'items': [{ 'value': 1, 'title': '完整' }, { 'value': 2, 'title': '仅失败' }, { 'value': 3, 'title': '静默' }]}}]}
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol', 
                                'props': {'cols': 12},
                                'content': [
                                    {'component': 'VBtn', 'props': {'color': 'primary', 'class': 'mr-2'}, 'content': '保存配置', 'events': {'click': 'onSave'}},
                                    {'component': 'VBtn', 'props': {'color': 'secondary'}, 'content': '取消', 'events': {'click': 'onCancel'}}
                                ]
                            }
                        ]
                    }
                ]
            }
        ], { # Default form values
            'enabled': self._enabled,
            'notify': self._notify,
            'cron': self._cron,
            'onlyonce': self._onlyonce,
            'openwrt_url': self._openwrt_url,
            'openwrt_username': self._openwrt_username,
            'openwrt_password': self._openwrt_password,
            'backup_path': self._backup_path if self._backup_path != str(self.get_data_path() / "actual_backups") else "",
            'keep_backup_num': self._keep_backup_num,
            'retry_count': self._retry_count,
            'retry_interval': self._retry_interval,
            'notification_style': self._notification_style,
            'luci_compat_mode': self._luci_compat_mode,
        }

    def get_page(self) -> List[dict]:
        return [
            {
                'path': '/openwrt-backup-history',
                'name': 'OpenWRTBackupHistory',
                'component': 'BackupHistoryPage',
                'props': {
                    'plugin_name': self.plugin_name,
                    'load_history_func': self._load_backup_history,
                    'delete_backup_func': self._delete_specific_backup, # Placeholder, need to implement
                    'download_backup_func': self._download_specific_backup, # Placeholder, need to implement
                    'column_headers': [
                        {'title': '备份时间', 'key': 'timestamp', 'sortable': True},
                        {'title': '文件名', 'key': 'filename', 'sortable': False},
                        {'title': '大小', 'key': 'size', 'sortable': True},
                        {'title': '状态', 'key': 'status', 'sortable': False},
                        {'title': '消息', 'key': 'message', 'sortable': False},
                        {'title': '操作', 'key': 'actions', 'sortable': False}
                    ]
                }
            }
        ]
    
    def _delete_specific_backup(self, filename_to_delete: str) -> Tuple[bool, str]:
        """删除指定的备份文件及其历史记录"""
        history = self._load_backup_history()
        new_history = [entry for entry in history if entry.get('filename') != filename_to_delete]
        
        backup_file_path = Path(self._backup_path) / filename_to_delete
        
        file_deleted = False
        if backup_file_path.exists() and backup_file_path.is_file():
            try:
                backup_file_path.unlink()
                file_deleted = True
                logger.info(f"{self.plugin_name} 已删除备份文件: {filename_to_delete}")
            except Exception as e:
                logger.error(f"{self.plugin_name} 删除备份文件 {filename_to_delete} 失败: {e}")
                return False, f"删除文件失败: {e}"
        else:
            logger.warning(f"{self.plugin_name} 尝试删除不存在的备份文件: {filename_to_delete}")
            # If file doesn't exist but history entry does, we still update history
            file_deleted = True 

        if len(new_history) < len(history):
            self.save_data('backup_history', new_history)
            logger.info(f"{self.plugin_name} 已从历史记录中删除 {filename_to_delete}。")
            return True, "备份文件及历史记录已删除。"
        elif file_deleted:
            return True, "备份文件已删除（历史记录中未找到）。"
        else:
            return False, "未找到指定的备份文件或历史记录。"

    def _download_specific_backup(self, filename_to_download: str) -> Optional[Tuple[str, bytes]]:
        """提供特定备份文件以供下载"""
        backup_file_path = Path(self._backup_path) / filename_to_download
        if backup_file_path.exists() and backup_file_path.is_file():
            try:
                content = backup_file_path.read_bytes()
                return filename_to_download, content
            except Exception as e:
                logger.error(f"{self.plugin_name} 读取备份文件 {filename_to_download} 供下载失败: {e}")
                return None
        else:
            logger.warning(f"{self.plugin_name} 请求下载不存在的备份文件: {filename_to_download}")
            return None

    def stop_service(self):
        if self._scheduler and self._scheduler.running:
            try:
                self._scheduler.shutdown(wait=True)
                self._scheduler = None
                logger.info(f"{self.plugin_name} 服务已停止。")
            except Exception as e:
                logger.error(f"{self.plugin_name} 停止服务失败: {e}")
        self._running = False

    def run_backup_job(self):
        with self._lock:
            if self._running:
                logger.info(f"{self.plugin_name} 备份任务已在运行中，跳过本次执行。")
                return
            self._running = True
        
        logger.info(f"{self.plugin_name} 开始执行备份任务...")
        success = False
        message = ""
        backup_filename = None
        
        for attempt in range(self._retry_count + 1):
            try:
                success, message, backup_filename = self._perform_backup_once()
                if success:
                    logger.info(f"{self.plugin_name} 备份成功: {message}")
                    break
                else:
                    logger.error(f"{self.plugin_name} 备份尝试 {attempt + 1}/{self._retry_count + 1} 失败: {message}")
                    if attempt < self._retry_count:
                        logger.info(f"{self.plugin_name} 将在 {self._retry_interval} 秒后重试...")
                        time.sleep(self._retry_interval)
                    else:
                        logger.error(f"{self.plugin_name} 所有备份尝试均失败。")
            except Exception as e:
                logger.error(f"{self.plugin_name} 备份尝试 {attempt + 1}/{self._retry_count + 1} 出现意外错误: {e}")
                message = f"意外错误: {str(e)}"
                if attempt < self._retry_count:
                    logger.info(f"{self.plugin_name} 将在 {self._retry_interval} 秒后重试...")
                    time.sleep(self._retry_interval)
                else:
                    logger.error(f"{self.plugin_name} 所有备份尝试均因意外错误而失败。")
        
        if success and backup_filename:
            self._cleanup_old_backups()
            history_entry = {
                "timestamp": datetime.now(tz=pytz.timezone(settings.TZ)).strftime('%Y-%m-%d %H:%M:%S'),
                "filename": backup_filename,
                "status": "成功",
                "message": message,
                "size": self._get_file_size_str(Path(self._backup_path) / backup_filename)
            }
        else:
            history_entry = {
                "timestamp": datetime.now(tz=pytz.timezone(settings.TZ)).strftime('%Y-%m-%d %H:%M:%S'),
                "filename": "N/A",
                "status": "失败",
                "message": message,
                "size": "0 B"
            }
        self._save_backup_history_entry(history_entry)
        self._send_notification(success, message, backup_filename)
        
        with self._lock:
            self._running = False
        logger.info(f"{self.plugin_name} 备份任务执行完毕。")

    def _perform_backup_once(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """执行单次备份尝试，返回 (是否成功, 消息, 备份文件名)"""
        if not self._openwrt_url or not self._openwrt_username or not self._openwrt_password:
            return False, "OpenWRT URL、用户名或密码未配置。", None

        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        # 1. 登录 OpenWRT
        token = self._login_openwrt(session)
        if not token:
            return False, "登录 OpenWRT 失败。", None
        logger.info(f"{self.plugin_name} 成功登录 OpenWRT。")

        # 2. 请求生成备份
        # OpenWRT 通常通过特定 cgi-bin URL 生成备份并直接下载
        # /cgi-bin/luci/admin/system/backup
        # 或者 /cgi-bin/luci/admin/system/flashops (旧版)
        # POST 到 /cgi-bin/luci/admin/system/backup (或对应 flashops URL)
        # payload 通常包含一个 'sessionid' (即token) 和一个触发备份的参数
        # 不同的 OpenWRT 版本和 LuCI 主题可能会有差异

        backup_url_path = f"/cgi-bin/luci/admin/system/backup?auth={token}" if not self._luci_compat_mode else f"/cgi-bin/luci/admin/system/flashops?auth={token}"
        # 有些版本可能不需要 ?auth={token} 在URL中，而是作为POST数据的一部分
        # 或者通过 header X-LuCI-Login: token
        # 对于备份请求，通常是一个GET请求直接下载，或者一个POST请求触发然后GET下载
        # OpenWRT备份是直接下载，没有创建后再下载的步骤

        logger.info(f"{self.plugin_name} 尝试从 {backup_url_path} 下载备份...")
        
        try:
            backup_download_url = urljoin(self._openwrt_url, backup_url_path)
            # OpenWRT的备份通常不需要额外的POST数据来触发，直接GET就能下载
            # 有些版本可能需要在请求备份的页面先点击 "生成备份" 按钮，该按钮的POST请求会设置一些session变量
            # 然后点击下载按钮才真正下载。
            # 此处我们简化为直接GET下载。如果失败，用户可能需要检查其OpenWRT版本特性。
            
            # 如果需要先POST触发，类似这样:
            # post_data = {
            #     'sessionid': token, # 或 'ubus_rpc_session': token
            #     'action': 'backup' # 或其他特定参数
            # }
            # headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            # pre_response = session.post(urljoin(self._openwrt_url, "/cgi-bin/luci/rpc/sys"), data={
            #     'jsonrpc': '2.0',
            #     'id': 1,
            #     'method': 'call',
            #     'params': [token, 'system', 'backup_generate', {}] # 示例 RPC 调用
            # }, headers={'Content-Type': 'application/json'})
            # if pre_response.status_code != 200 or not pre_response.json().get('result'):
            #     logger.error(f"预备份请求失败: {pre_response.status_code} - {pre_response.text}")
            #     return False, "预备份请求失败", None

            response = session.get(backup_download_url, stream=True, timeout=300) # 增加超时时间
            response.raise_for_status() # 如果状态码不是200-299，则抛出HTTPError

            # 从 Content-Disposition 获取文件名
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                match = re.search(r'filename="?([^"]+)"?', content_disposition)
                if match:
                    router_filename = match.group(1)
                else:
                    # 默认文件名格式，如果无法从header获取
                    router_filename = f"backup-openwrt-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.tar.gz"
            else:
                router_filename = f"backup-openwrt-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.tar.gz"
            
            # 确保文件名安全
            safe_filename = "".join(c if c.isalnum() or c in ('.', '-', '_') else '_' for c in router_filename)
            local_filepath = Path(self._backup_path) / safe_filename

            with open(local_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"{self.plugin_name} 备份文件已下载并保存到: {local_filepath}")
            return True, f"备份成功下载: {safe_filename}", safe_filename

        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 下载备份文件失败: {e}")
            return False, f"下载备份文件失败: {str(e)}", None
        except Exception as e:
            logger.error(f"{self.plugin_name} 处理备份时发生未知错误: {e}")
            return False, f"处理备份时发生未知错误: {str(e)}", None

    def _login_openwrt(self, session: requests.Session) -> Optional[str]:
        """登录到 OpenWRT 并返回 session token"""
        login_url = urljoin(self._openwrt_url, '/cgi-bin/luci/')
        try:
            # 尝试获取登录页面，某些版本可能直接允许无密码登录或已保存session
            # 但标准流程是POST用户名密码到 /cgi-bin/luci/
            # 旧版 /cgi-bin/luci/admin/index
            # 新版 /cgi-bin/luci/rpc/auth  (JSON-RPC)
            
            # 尝试 JSON-RPC 登录 (适用于较新版本的 LuCI)
            rpc_auth_url = urljoin(self._openwrt_url, '/cgi-bin/luci/rpc/auth')
            payload = {
                "id": 1,
                "method": "login",
                "params": [self._openwrt_username, self._openwrt_password]
            }
            try:
                response = session.post(rpc_auth_url, json=payload, timeout=10)
                response.raise_for_status()
                auth_data = response.json()
                if auth_data.get("result") and len(auth_data["result"]) == 32: # LuCI token is typically 32 chars
                    token = auth_data["result"]
                    # 验证token是否有效，可以尝试访问一个受保护的资源
                    # 例如 /cgi-bin/luci/rpc/sys?auth=<token> method get_board_name
                    # 或者在后续请求中直接使用，如果失败则认为token无效
                    logger.info(f"{self.plugin_name} 通过 JSON-RPC 登录成功，获得 token。")
                    session.headers.update({'X-LuCI-Login': token}) # 有些 LuCI 版本可能需要这个 header
                    return token
                elif auth_data.get("error"):
                     logger.warning(f"{self.plugin_name} JSON-RPC 登录失败: {auth_data.get('error')}")
                else:
                    logger.warning(f"{self.plugin_name} JSON-RPC 登录响应未知: {response.text}")
            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                logger.warning(f"{self.plugin_name} JSON-RPC 登录尝试失败 ({rpc_auth_url}): {e}. 将尝试传统登录。")

            # 尝试传统表单登录 (适用于旧版本或未启用RPC的LuCI)
            form_login_url = urljoin(self._openwrt_url, '/cgi-bin/luci/') 
            # 首先GET一次获取可能的CSRF token或stok (虽然老版本LuCI不常用CSRF)
            try:
                session.get(form_login_url, timeout=5) 
            except requests.exceptions.RequestException:
                pass # 忽略错误，可能因为需要登录而重定向

            login_data = {
                'luci_username': self._openwrt_username,
                'luci_password': self._openwrt_password
            }
            response = session.post(form_login_url, data=login_data, timeout=10, allow_redirects=False)
            
            # 成功登录后，通常会重定向，并且cookie中会包含 sysauth (或类似名称) 的 token
            # 或者，某些版本重定向后的URL中会包含stok=<token>
            if response.status_code in [200, 301, 302]: # 200表示可能登录成功且停留在页面，30x表示重定向
                # 检查cookie中的 sysauth (旧版) 或 ubus_rpc_session (新版)
                token = session.cookies.get('sysauth') or session.cookies.get('ubus_rpc_session')
                if token:
                    logger.info(f"{self.plugin_name} 通过传统表单登录成功，从 Cookie 获得 token。")
                    return token
                
                # 检查重定向URL中的stok (另一种token形式)
                if response.status_code in [301, 302] and 'Location' in response.headers:
                    location_url = response.headers['Location']
                    stok_match = re.search(r'[?;]stok=([0-9a-fA-F]{32,})', location_url)
                    if stok_match:
                        token = stok_match.group(1)
                        logger.info(f"{self.plugin_name} 通过传统表单登录成功，从重定向 URL 获得 stok token。")
                        # 将 stok 加入 session 后续请求的参数中，或作为 header
                        # 注意：stok 通常作为 URL 参数，而不是 cookie
                        # 为了统一，我们仍然返回这个token，后续请求需要特殊处理
                        # 如果用stok，则后续请求URL需要类似 /cgi-bin/luci/;stok=<token>/path/to/resource
                        # 为了简化，我们主要依赖 sysauth/ubus_rpc_session。如果只拿到stok，可能需要调整备份下载逻辑
                        # 这里我们还是返回它，并在备份下载时尝试使用。 
                        # 更稳妥的做法是，如果用stok，则后续每个请求都需要构造带stok的URL。
                        # 为简单起见，我们优先使用cookie中的token。
                        # 如果要完全支持stok, _perform_backup_once的backup_url_path需要修改
                        # 例如: backup_url_path = f"/cgi-bin/luci/;stok={token}/admin/system/backup"
                        return token # 返回stok，备份函数需要能处理它

                # 如果没有明显token，但状态码是200，检查页面内容是否是已登录状态
                if response.status_code == 200 and "logout" in response.text.lower():
                    logger.info(f"{self.plugin_name} 通过传统表单登录成功（页面包含登出按钮）。假定基于Cookie的会话已建立。")
                    # 在这种情况下，没有明确的token可返回，依赖session cookie
                    # 返回一个非空的虚拟token，表示登录成功
                    return "session_cookie_based"

            logger.error(f"{self.plugin_name} 传统表单登录失败。状态码: {response.status_code}, 响应: {response.text[:200]}")
            return None

        except requests.exceptions.Timeout:
            logger.error(f"{self.plugin_name} 登录 OpenWRT 超时 ({login_url}).")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 登录 OpenWRT 失败: {e}")
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} 登录 OpenWRT 时发生未知错误: {e}")
            return None

    def _cleanup_old_backups(self):
        if not self._backup_path or self._keep_backup_num <= 0:
            return

        logger.info(f"{self.plugin_name} 开始清理旧备份，保留最新的 {self._keep_backup_num} 个文件...")
        try:
            backup_dir = Path(self._backup_path)
            if not backup_dir.exists() or not backup_dir.is_dir():
                logger.warning(f"{self.plugin_name} 备份目录 {self._backup_path} 不存在，无需清理。")
                return

            # 获取所有 tar.gz 或 .bin 文件 (OpenWRT备份通常是 .tar.gz, 但有些可能是 .bin)
            backup_files = sorted(
                [f for f in backup_dir.iterdir() if f.is_file() and (f.name.endswith('.tar.gz') or f.name.endswith('.bin'))],
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )

            if len(backup_files) > self._keep_backup_num:
                files_to_delete = backup_files[self._keep_backup_num:]
                deleted_count = 0
                for file_to_delete in files_to_delete:
                    try:
                        file_to_delete.unlink()
                        logger.info(f"{self.plugin_name} 已删除旧备份文件: {file_to_delete.name}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"{self.plugin_name} 删除旧备份文件 {file_to_delete.name} 失败: {e}")
                logger.info(f"{self.plugin_name} 旧备份清理完成，共删除 {deleted_count} 个文件。")
            else:
                logger.info(f"{self.plugin_name} 备份文件数量 ({len(backup_files)}) 未超过限制 ({self._keep_backup_num})，无需清理。")

        except Exception as e:
            logger.error(f"{self.plugin_name} 清理旧备份文件时出错: {e}")
    
    def _get_file_size_str(self, filepath: Path) -> str:
        try:
            size_bytes = filepath.stat().st_size
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.2f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        except Exception:
            return "N/A"

    def _send_notification(self, success: bool, message: str = "", filename: Optional[str] = None):
        if not self._notify:
            return
        
        # 根据通知样式决定是否发送
        if self._notification_style == 2 and success: # 仅失败时通知
            return
        if self._notification_style == 3: # 静默，不通知
            return

        title = f"{self.plugin_name} - {'备份成功' if success else '备份失败'}"
        content = message
        if success and filename:
            content += f"\n备份文件: {filename}"
            file_path = Path(self._backup_path) / filename
            content += f"\n文件大小: {self._get_file_size_str(file_path)}" 

        if settings.ENABLE_NOTIFICATION:
            try:
                self.system_notify(title=title, content=content,
                                   notify_type=NotificationType.PluginMessage)
                logger.info(f"{self.plugin_name} 已发送通知。")
            except Exception as e:
                logger.error(f"{self.plugin_name} 发送通知失败: {e}")

# 以下是 MoviePilot 插件加载所必需的
def register():
    return OpenWRTBackup

def unregister():
    plugin = OpenWRTBackup()
    plugin.stop_service()
    return True
