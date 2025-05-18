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
    plugin_name = "OpenWrt备份助手"
    # 插件描述
    plugin_desc = "自动备份OpenWrt路由配置，并管理备份文件。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/openwrt.webp"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "openwrt_backup_"
    # 加载顺序
    plugin_order = 11 # 避免与ikuai插件冲突
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
    
    _openwrt_url: str = "" # OpenWrt Luci地址，例如 http://192.168.1.1
    _openwrt_username: str = "root"
    _openwrt_password: str = ""
    _backup_path: str = ""
    _keep_backup_num: int = 7
    _backup_command: str = "sysupgrade -b /tmp/backup-${HOSTNAME}-$(date +%F).tar.gz" # OpenWrt备份命令，可能需要调整
    _backup_download_path: str = "/tmp/" # OpenWrt上备份文件生成的临时路径，需与备份命令中的路径对应
    _ssh_port: int = 22 # OpenWrt SSH端口

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
            self._openwrt_url = str(config.get("openwrt_url", "")).rstrip(\'/\')
            self._openwrt_username = str(config.get("openwrt_username", "root"))
            self._openwrt_password = str(config.get("openwrt_password", ""))
            self._ssh_port = int(config.get("ssh_port", 22))
            self._backup_command = str(config.get("backup_command", "sysupgrade -b /tmp/backup-${HOSTNAME}-$(date +%F).tar.gz"))
            self._backup_download_path = str(config.get("backup_download_path", "/tmp/")).rstrip(\'/\') + \'/\'
            
            configured_backup_path = str(config.get("backup_path", "")).strip()
            if not configured_backup_path:
                self._backup_path = str(self.get_data_path() / "openwrt_backups")
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
                    self._scheduler.add_job(func=self.run_backup_job, trigger=\'date\',
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
        history = self.get_data(\'backup_history\')
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
        
        self.save_data(\'backup_history\', history)
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
            "ssh_port": self._ssh_port,
            "backup_command": self._backup_command,
            "backup_download_path": self._backup_download_path,
            "backup_path": self._backup_path,
            "keep_backup_num": self._keep_backup_num,
            "notification_style": self._notification_style,
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
                        "id": "OpenWrtBackupService",
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
        default_backup_location_desc = f"插件数据目录下的 openwrt_backups 子目录 (默认: {str(self.get_data_path() / 'openwrt_backups')})"
        return [
            {
                \'component\': \'VForm\',
                \'content\': [
                    {
                        \'component\': \'VRow\',
                        \'content\': [
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 4}, \'content\': [{\'component\': \'VSwitch\', \'props\': {\'model\': \'enabled\', \'label\': \'启用插件\'}}]},
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 4}, \'content\': [{\'component\': \'VSwitch\', \'props\': {\'model\': \'notify\', \'label\': \'发送通知\'}}]},
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 4}, \'content\': [{\'component\': \'VSwitch\', \'props\': {\'model\': \'onlyonce\', \'label\': \'立即运行一次\'}}]},
                        ],
                    },
                    {
                        \'component\': \'VRow\',
                        \'content\': [
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 6}, \'content\': [{\'component\': \'VTextField\', \'props\': {\'model\': \'openwrt_url\', \'label\': \'OpenWrt地址\', \'placeholder\': \'例如: http://192.168.1.1 或 192.168.1.1 (仅IP)\'}}]},
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 6}, \'content\': [{\'component\': \'VCronField\', \'props\': {\'model\': \'cron\', \'label\': \'执行周期\'}}]}
                        ],
                    },
                    {
                        \'component\': \'VRow\',
                        \'content\': [
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 6}, \'content\': [{\'component\': \'VTextField\', \'props\': {\'model\': \'openwrt_username\', \'label\': \'SSH用户名\', \'placeholder\': \'默认为 root\'}}]},
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 6}, \'content\': [{\'component\': \'VTextField\', \'props\': {\'model\': \'openwrt_password\', \'label\': \'SSH密码\', \'type\': \'password\'}}]},
                        ],
                    },
                    {
                        \'component\': \'VRow\',
                        \'content\': [
                             {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 6}, \'content\': [{\'component\': \'VTextField\', \'props\': {\'model\': \'ssh_port\', \'label\': \'SSH端口\', \'type\': \'number\', \'placeholder\': \'默认为 22\'}}]},
                             {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 6}, \'content\': [{\'component\': \'VTextField\', \'props\': {\'model\': \'backup_path\', \'label\': \'备份文件存储路径\', \'placeholder\': default_backup_location_desc}}]},
                        ],
                    },
                    {
                        \'component\': \'VRow\',
                        \'content\': [
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 12}, \'content\': [{\'component\': \'VTextField\', \'props\': {\'model\': \'backup_command\', \'label\': \'OpenWrt备份命令\', \'placeholder\': \'例如: sysupgrade -b /tmp/backup-${HOSTNAME}-$(date +%F).tar.gz\'}}]},
                        ]
                    },
                    {
                        \'component\': \'VRow\',
                        \'content\': [
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 12}, \'content\': [{\'component\': \'VTextField\', \'props\': {\'model\': \'backup_download_path\', \'label\': \'OpenWrt备份文件生成路径 (需与备份命令对应)\', \'placeholder\': \'例如: /tmp/\'}}]},
                        ]
                    },
                    {
                        \'component\': \'VRow\',
                        \'content\': [
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 6}, \'content\': [{\'component\': \'VTextField\', \'props\': {\'model\': \'keep_backup_num\', \'label\': \'保留备份数量\', \'type\': \'number\'}}]},
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 6}, \'content\': [{\'component\': \'VSelect\', \'props\': {\'model\': \'notification_style\', \'label\': \'通知样式\', \'items\': [{\'title\': \'完整路径\', \'value\': 1}, {\'title\': \'仅文件名\', \'value\': 2}]}}]},
                        ],
                    },
                    {
                        \'component\': \'VRow\',
                        \'content\': [
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 6}, \'content\': [{\'component\': \'VTextField\', \'props\': {\'model\': \'retry_count\', \'label\': \'重试次数\', \'type\': \'number\'}}]},
                            {\'component\': \'VCol\', \'props\': {\'cols\': 12, \'md\': 6}, \'content\': [{\'component\': \'VTextField\', \'props\': {\'model\': \'retry_interval\', \'label\': \'重试间隔 (秒)\', \'type\': \'number\'}}]},
                        ]
                    },
                ]
            }
        ], {
            "enabled": self._enabled,
            "notify": self._notify,
            "cron": self._cron,
            "onlyonce": self._onlyonce,
            "retry_count": self._retry_count,
            "retry_interval": self._retry_interval,
            "openwrt_url": self._openwrt_url,
            "openwrt_username": self._openwrt_username,
            "openwrt_password": self._openwrt_password,
            "ssh_port": self._ssh_port,
            "backup_command": self._backup_command,
            "backup_download_path": self._backup_download_path,
            "backup_path": self._backup_path if self._backup_path != str(self.get_data_path() / "openwrt_backups") else "",
            "keep_backup_num": self._keep_backup_num,
            "notification_style": self._notification_style,
        }

    def get_page(self) -> List[dict]:
        history_data = self._load_backup_history()
        # 格式化时间戳以便在前端显示
        for entry in history_data:
            if \'timestamp\' in entry and isinstance(entry[\'timestamp\'], (int, float)):\n                try:\n                    dt_object = datetime.fromtimestamp(entry[\'timestamp\'], tz=pytz.timezone(settings.TZ))\n                    entry[\'formatted_time\'] = dt_object.strftime(\'%Y-%m-%d %H:%M:%S\')\n                except Exception as e:\n                    logger.warning(f"格式化时间戳 {entry['timestamp']} 失败: {e}")\n                    entry[\'formatted_time\'] = \'N/A\'\n            else:\n                entry[\'formatted_time\'] = \'N/A\' # 如果时间戳不存在或格式不正确

        return [
            {
                \'name\': \'备份历史\',
                \'component\': \'VCard\',
                \'content\': [
                    {
                        \'component\': \'VDataTable\',
                        \'props\': {
                            \'headers\': [
                                {\'title\': \'时间\', \'key\': \'formatted_time\', \'sortable\': True},
                                {\'title\': \'状态\', \'key\': \'status\', \'sortable\': False},
                                {\'title\': \'文件名\', \'key\': \'filename\', \'sortable\': False},
                                {\'title\': \'消息\', \'key\': \'message\', \'sortable\': False},
                                {\'title\': \'操作\', \'key\': \'actions\', \'sortable\': False},
                            ],
                            \'items\': history_data,
                            \'items-per-page\': 10,
                            \'search\': \'\', # 可以添加搜索功能
                            \'item-key\': \'timestamp\', # 确保每个条目有唯一键
                            \'no-data-text\': \'暂无备份历史记录\' 
                        },
                        # 使用 slot 来自定义列的显示
                        \'slots\': [
                            {
                                \'name\': \'item.status\',
                                \'component\': \'VChip\',
                                \'props\': {
                                    \'color\': \'{item.status == "成功" ? "green" : "red"}\', # 根据状态显示不同颜色
                                    \'text\': \'{item.status}\',
                                    \'size\': \'small\'
                                }
                            },
                            {
                                \'name\': \'item.actions\',
                                \'content\': [
                                     {
                                        \'component\': \'VBtn\',
                                        \'props\': {
                                            \'icon\': True,
                                            \'size\': \'small\',
                                            \'@click\': \'() => downloadBackup(item.filename)\', # 需要实现 downloadBackup 方法
                                            \'title\': \'下载备份\' 
                                        },
                                        \'content\': [{\'component\': \'VIcon\', \'props\': {\'icon\': \'mdi-download\'}}]\n                                    },\n                                    {\n                                        \'component\': \'VBtn\',\n                                        \'props\': {\n                                            \'icon\': True,\n                                            \'size\': \'small\',\n                                            \'color\': \'red\',\n                                            \'@click\': \'() => deleteBackup(item.filename, item.timestamp)\', # 需要实现 deleteBackup 方法\n                                            \'title\': \'删除备份\' \n                                        },\n                                        \'content\': [{\'component\': \'VIcon\', \'props\': {\'icon\': \'mdi-delete\'}}]\n                                    }\n                                ]
                            }
                        ]
                    }
                ]
            }
        ]

    def stop_service(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            self._scheduler = None
            logger.info(f"{self.plugin_name} 服务已停止")

    def run_backup_job(self):
        if not self._enabled and not self._onlyonce:
            logger.info(f"{self.plugin_name} 未启用，跳过备份。")
            return

        if self._running:
            logger.info(f"{self.plugin_name} 备份任务已在运行中，跳过本次执行。")
            return

        with self._lock:
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
                    logger.error(f"{self.plugin_name} 备份失败 (尝试 {attempt + 1}/{self._retry_count + 1}): {message}")
            except Exception as e:
                logger.error(f"{self.plugin_name} 备份过程中发生严重错误 (尝试 {attempt + 1}/{self._retry_count + 1}): {e}")
                message = str(e)
            
            if attempt < self._retry_count:
                logger.info(f"{self.plugin_name} 将在 {self._retry_interval} 秒后重试...")
                time.sleep(self._retry_interval)
        
        # 保存历史记录
        history_entry = {
            "timestamp": time.time(),
            "status": "成功" if success else "失败",
            "filename": backup_filename if backup_filename else "N/A",
            "message": message if message else ("备份成功完成" if success else "备份失败"),
            "filesize": os.path.getsize(Path(self._backup_path) / backup_filename) if success and backup_filename and (Path(self._backup_path) / backup_filename).exists() else 0,
        }
        self._save_backup_history_entry(history_entry)

        if self._notify:
            self._send_notification(success, message, backup_filename)

        if success:
            self._cleanup_old_backups()
            
        with self._lock:
            self._running = False
        logger.info(f"{self.plugin_name} 备份任务执行完毕。")

    def _perform_backup_once(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        通过SSH连接到OpenWrt，执行备份命令，然后通过SCP下载备份文件。
        返回: (是否成功, 消息, 本地备份文件名)
        """
        try:
            import paramiko
        except ImportError:
            logger.error(f"{self.plugin_name}: 依赖 paramiko 未安装，请在MoviePilot中安装此依赖。")
            return False, "Python模块 'paramiko' 未安装，无法执行SSH操作。", None

        openwrt_host = self._openwrt_url.replace("http://", "").replace("https://", "").split("/")[0]
        
        ssh = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            logger.info(f"{self.plugin_name}: 尝试SSH连接到 {openwrt_host}:{self._ssh_port} 用户: {self._openwrt_username}")
            ssh.connect(openwrt_host, port=self._ssh_port, username=self._openwrt_username, password=self._openwrt_password, timeout=30)
            logger.info(f"{self.plugin_name}: SSH连接成功。")

            # 1. 执行备份命令
            logger.info(f"{self.plugin_name}: 在OpenWrt上执行备份命令: {self._backup_command}")
            stdin, stdout, stderr = ssh.exec_command(self._backup_command)
            exit_status = stdout.channel.recv_exit_status() # 等待命令完成
            
            cmd_output = stdout.read().decode(\'utf-8\', errors=\'ignore\').strip()
            cmd_error = stderr.read().decode(\'utf-8\', errors=\'ignore\').strip()

            if exit_status != 0:
                error_msg = f"OpenWrt备份命令执行失败 (退出码: {exit_status})。输出: {cmd_output}。错误: {cmd_error}"
                logger.error(f"{self.plugin_name}: {error_msg}")
                return False, error_msg, None
            logger.info(f"{self.plugin_name}: OpenWrt备份命令执行成功。输出: {cmd_output}")
            
            # 从命令输出或预设路径中提取备份文件名
            # 假设备份命令如 sysupgrade -b /tmp/backup-OpenWrt-2023-10-27.tar.gz
            # 或者命令直接输出文件名
            remote_filename = None
            if cmd_output and (".tar.gz" in cmd_output or ".img" in cmd_output or ".bin" in cmd_output) : # 尝试从命令输出解析
                 # 简单提取文件名逻辑，可能需要根据实际命令输出调整
                match = re.search(r\'([\w\-\.]+\.(tar\.gz|img|bin))\', cmd_output)
                if match:
                    remote_filename = match.group(1)
                    logger.info(f"{self.plugin_name}: 从命令输出中解析得到远程文件名: {remote_filename}")

            if not remote_filename: # 如果无法从输出解析，尝试从备份命令和下载路径推断
                # 这是一个更复杂的场景，需要根据 self._backup_command 和 self._backup_download_path 动态生成
                # 例如，如果命令是 sysupgrade -b /tmp/backup-$(date +%F).tar.gz
                # 需要模拟 date +%F 的输出。为了简化，我们先假设备份文件名是固定的或者可以通过列出目录获取。
                # 更可靠的方式是让备份命令直接输出完整路径和文件名，或者备份到固定文件名。
                # 这里我们假设备份文件名遵循某种模式，比如包含日期
                logger.info(f"{self.plugin_name}: 无法从命令输出解析文件名，尝试从 {self._backup_download_path} 列出最新的备份文件。")
                stdin, stdout, stderr = ssh.exec_command(f"ls -t {self._backup_download_path}*.tar.gz {self._backup_download_path}*.img {self._backup_download_path}*.bin 2>/dev/null | head -n 1")
                potential_file = stdout.read().decode().strip()
                if potential_file and stdout.channel.recv_exit_status() == 0:
                    remote_filename = os.path.basename(potential_file)
                    logger.info(f"{self.plugin_name}: 在远程目录找到最新备份文件: {remote_filename}")
                else:
                    err_msg = f"无法确定远程备份文件名。请确保备份命令输出文件名，或备份到固定文件名，或检查 '{self._backup_download_path}' 路径设置。"
                    logger.error(f"{self.plugin_name}: {err_msg}")
                    return False, err_msg, None
            
            remote_filepath = self._backup_download_path.rstrip(\'/\') + \'/\' + remote_filename
            local_filename = f"openwrt_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{remote_filename}"
            local_filepath_to_save = str(Path(self._backup_path) / local_filename)

            # 2. 下载备份文件
            logger.info(f"{self.plugin_name}: 准备从 {openwrt_host}:{remote_filepath} 下载备份文件到 {local_filepath_to_save}")
            sftp = None
            try:
                sftp = ssh.open_sftp()
                sftp.get(remote_filepath, local_filepath_to_save)
                logger.info(f"{self.plugin_name}: 文件下载成功: {local_filepath_to_save}")
                
                # 3. (可选) 清理远程服务器上的备份文件
                try:
                    logger.info(f"{self.plugin_name}: 尝试删除远程备份文件: {remote_filepath}")
                    sftp.remove(remote_filepath)
                    logger.info(f"{self.plugin_name}: 远程备份文件 {remote_filepath} 删除成功。")
                except Exception as e_rm:
                    logger.warning(f"{self.plugin_name}: 删除远程备份文件 {remote_filepath} 失败: {e_rm}。这可能不是一个严重问题。")

                return True, f"备份文件 {local_filename} 已成功下载。", local_filename
            except FileNotFoundError:
                err_msg = f"SFTP错误：远程文件 {remote_filepath} 未找到。请检查OpenWrt上的备份命令和路径。"
                logger.error(f"{self.plugin_name}: {err_msg}")
                return False, err_msg, None
            except Exception as e_sftp:
                err_msg = f"SFTP下载备份文件失败: {e_sftp}"
                logger.error(f"{self.plugin_name}: {err_msg}")
                return False, err_msg, None
            finally:
                if sftp:
                    sftp.close()
        
        except paramiko.AuthenticationException:
            error_msg = f"SSH认证失败。请检查OpenWrt的地址、端口、用户名和密码。"
            logger.error(f"{self.plugin_name}: {error_msg}")
            return False, error_msg, None
        except paramiko.SSHException as sshException:
            error_msg = f"SSH连接错误: {sshException}。请检查OpenWrt的地址和端口。"
            logger.error(f"{self.plugin_name}: {error_msg}")
            return False, error_msg, None
        except TimeoutError: # socket.timeout often manifested as TimeoutError by paramiko
            error_msg = f"SSH连接超时。请检查OpenWrt是否可达，以及防火墙设置。"
            logger.error(f"{self.plugin_name}: {error_msg}")
            return False, error_msg, None
        except Exception as e:
            error_msg = f"执行备份操作时发生未知错误: {e}"
            logger.error(f"{self.plugin_name}: {error_msg}")
            return False, error_msg, None
        finally:
            if ssh:
                ssh.close()
                logger.info(f"{self.plugin_name}: SSH连接已关闭。")
        return False, "由于未知原因，备份失败。", None


    def _cleanup_old_backups(self):
        if self._keep_backup_num <= 0:
            logger.info(f"{self.plugin_name}: 保留备份数量设置为不限制，不清理旧备份。")
            return

        logger.info(f"{self.plugin_name}: 开始清理旧备份，保留最新的 {self._keep_backup_num} 个文件...")
        try:
            backup_dir = Path(self._backup_path)
            if not backup_dir.exists() or not backup_dir.is_dir():
                logger.warning(f"{self.plugin_name}: 备份目录 {self._backup_path} 不存在或不是一个目录，跳过清理。")
                return

            files = sorted(
                [f for f in backup_dir.iterdir() if f.is_file() and (f.name.startswith("openwrt_backup_") and (f.name.endswith(".tar.gz") or f.name.endswith(".img") or f.name.endswith(".bin")))],
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )

            if len(files) > self._keep_backup_num:
                files_to_delete = files[self._keep_backup_num:]
                deleted_count = 0
                for file_to_delete in files_to_delete:
                    try:
                        file_to_delete.unlink()
                        logger.info(f"{self.plugin_name}: 已删除旧备份文件: {file_to_delete.name}")
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"{self.plugin_name}: 删除旧备份文件 {file_to_delete.name} 失败: {e}")
                if deleted_count > 0:
                     logger.info(f"{self.plugin_name}: 清理完成，共删除了 {deleted_count} 个旧备份文件。")
                else:
                    logger.info(f"{self.plugin_name}: 没有需要删除的旧备份文件。")
            else:
                logger.info(f"{self.plugin_name}: 当前备份数量 ({len(files)}) 未超过限制 ({self._keep_backup_num})，无需清理。")

        except Exception as e:
            logger.error(f"{self.plugin_name}: 清理旧备份文件时发生错误: {e}")

    def _send_notification(self, success: bool, message: str = "", filename: Optional[str] = None):
        if not self._notify:
            return

        title = f"{self.plugin_name} - {'备份成功' if success else '备份失败'}"
        
        content = message if message else ("备份成功完成" if success else "备份失败，请检查日志。")
        if success and filename:
            if self._notification_style == 1: # 完整路径
                content = f"备份文件: {Path(self._backup_path) / filename}\\n{message}"
            else: # 仅文件名
                content = f"备份文件: {filename}\\n{message}"
        
        self.system_notify(
            title=title,
            message=content,
            ttype=NotificationType.Plugin,
            image_url=self.plugin_icon
        )
        logger.info(f"{self.plugin_name}: 已发送通知 - 标题: {title}, 内容: {content[:100]}...")


    # --- 和前端页面交互的方法 ---
    def download_backup_api(self, filename: str) -> Dict[str, Any]:
        """API端点，用于下载指定的备份文件。"""
        if not filename or '..' in filename or filename.startswith('/'): # 基本安全检查
            logger.error(f"{self.plugin_name}: 无效的文件名请求下载: {filename}")
            return {"success": False, "message": "无效的文件名", "filepath": None}

        file_path = Path(self._backup_path) / filename
        if file_path.exists() and file_path.is_file() and file_path.parent.resolve() == Path(self._backup_path).resolve():
            # 确认文件在预期的备份目录下
            logger.info(f"{self.plugin_name}: 请求下载备份文件: {file_path}")
            # MoviePilot框架会自动处理StaticFiles的下载，这里只需要返回文件路径
            # 注意：这里返回的是绝对路径，或者相对于MoviePilot定义的静态目录的路径
            # 为简单起见，如果MoviePilot支持从插件数据目录直接提供下载，则可以直接返回
            # 否则，可能需要将文件复制到一个公共可访问的临时目录
            
            # 假设可以直接从插件数据目录提供下载，返回一个可供前端构造下载链接的标识
            # 或者如果框架要求返回绝对路径以供内部处理：
            # return {"success": True, "message": "文件准备就绪", "filepath": str(file_path.resolve())}
            
            # 简化处理：返回一个标志，前端将构造一个指向特定API的链接，该API负责流式传输文件
            # 这个API需要在这里定义，并在get_api中注册
            # 为了演示，我们假设可以直接下载，或者前端通过其他方式获取
             return {"success": True, "message": "请通过GET请求 /api/v1/plugins/file/{self.plugin_config_prefix}{filename} 下载", "filename": filename}

        else:
            logger.error(f"{self.plugin_name}: 请求下载的文件不存在或无权访问: {filename}")
            return {"success": False, "message": "文件不存在或无法访问", "filepath": None}

    def delete_backup_api(self, filename: str, timestamp: float) -> Dict[str, Any]:
        """API端点，用于删除指定的备份文件和相关的历史记录。"""
        if not filename or '..' in filename or filename.startswith('/'): # 基本安全检查
            logger.error(f"{self.plugin_name}: 无效的文件名请求删除: {filename}")
            return {"success": False, "message": "无效的文件名"}

        file_path = Path(self._backup_path) / filename
        deleted_from_disk = False
        if file_path.exists() and file_path.is_file() and file_path.parent.resolve() == Path(self._backup_path).resolve():
            try:
                file_path.unlink()
                logger.info(f"{self.plugin_name}: 已从磁盘删除备份文件: {filename}")
                deleted_from_disk = True
            except Exception as e:
                logger.error(f"{self.plugin_name}: 删除磁盘备份文件 {filename} 失败: {e}")
                return {"success": False, "message": f"删除磁盘文件失败: {e}"}
        else:
            logger.warning(f"{self.plugin_name}: 请求删除的文件在磁盘上不存在: {filename}，仅尝试清理历史记录。")
            # 即使文件不在磁盘上，也可能需要清理历史记录

        # 清理历史记录
        history = self._load_backup_history()
        original_history_len = len(history)
        # 使用 timestamp (float) 进行匹配，因为文件名可能重复（虽然不太可能同时发生）
        history_to_keep = [entry for entry in history if not (entry.get('filename') == filename and abs(entry.get('timestamp', 0) - timestamp) < 0.001 )]
        
        if len(history_to_keep) < original_history_len:
            self.save_data('backup_history', history_to_keep)
            logger.info(f"{self.plugin_name}: 已从历史记录中删除关于 {filename} (时间戳: {timestamp}) 的条目。")
            action_message = "文件和历史记录已删除。" if deleted_from_disk else "历史记录已删除（文件未在磁盘找到）。"
            return {"success": True, "message": action_message}
        elif deleted_from_disk: # 文件从磁盘删除，但历史记录中没有完全匹配的项（不太可能）
             return {"success": True, "message": "文件已从磁盘删除，但未在历史记录中找到精确匹配项。"}
        else: # 文件不在磁盘，历史记录也没有匹配项
            return {"success": False, "message": "文件未在磁盘找到，也未在历史记录中找到相关条目。"}


    def get_api(self) -> List[Dict[str, Any]]:
        """注册API端点"""
        apis = super().get_api()
        apis.extend([
            {
                "path": "/download_backup/{filename}",
                "endpoint": self.download_backup_api_route, # 需要一个包装器来处理路径参数
                "methods": ["GET"],
                "summary": "下载备份文件"
            },
            {
                "path": "/delete_backup", # 使用查询参数或请求体
                "endpoint": self.delete_backup_api_route,
                "methods": ["POST"], # 使用POST更安全，因为是删除操作
                "summary": "删除备份文件和历史记录"
            }
        ])
        return apis

    # --- API路由包装器 ---
    # FastAPI 会自动处理路径参数和查询/请求体参数的注入
    # 我们需要确保这些方法能被 MoviePilot 的插件加载器正确识别和路由

    async def download_backup_api_route(self, filename: str):
        """
        实际处理下载请求的路由。
        MoviePilot 内部可能使用 FastAPI，可以直接返回 FileResponse。
        如果不是，则需要找到 MoviePilot 提供的文件响应方式。
        """
        from fastapi.responses import FileResponse
        from fastapi import HTTPException

        if not filename or '..' in filename or filename.startswith('/'):
            raise HTTPException(status_code=400, detail="无效的文件名")

        file_path = Path(self._backup_path) / filename
        if file_path.exists() and file_path.is_file() and file_path.parent.resolve() == Path(self._backup_path).resolve():
            logger.info(f"{self.plugin_name}: 提供文件下载: {file_path}")
            # 生成一个安全的文件名供浏览器下载
            safe_filename = quote(filename)
            return FileResponse(path=str(file_path.resolve()), filename=safe_filename, media_type='application/gzip') # 或者 application/octet-stream
        else:
            logger.error(f"{self.plugin_name}: 请求下载的文件不存在或无权访问: {filename}")
            raise HTTPException(status_code=404, detail="文件未找到")
            
    async def delete_backup_api_route(self, request: Dict[str, Any]): # 假设请求体是JSON {"filename": "...", "timestamp": ...}
        """
        实际处理删除请求的路由。
        前端应该发送一个 JSON body，例如: {"filename": "xxx.tar.gz", "timestamp": 1678886400.0}
        """
        from fastapi import HTTPException
        filename = request.get("filename")
        timestamp = request.get("timestamp")

        if not filename or not isinstance(timestamp, (int,float)):
            raise HTTPException(status_code=400, detail="请求参数 'filename' 和 'timestamp' 是必需的。")
        
        result = self.delete_backup_api(filename=str(filename), timestamp=float(timestamp))
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("message", "删除失败"))


# MoviePilot加载时会实例化这个类
plugin_instance = OpenWRTBackup()
