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

class OpenWrtBackup(_PluginBase):
    # 插件名称
    plugin_name = "OpenWrt备份助手"
    # 插件描述
    plugin_desc = "自动备份 OpenWrt 配置，并管理备份文件。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/main/icons/openwrt.png" # Placeholder icon
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "jinxi" # Or your name
    # 作者主页
    author_url = "https://github.com/xijin285" # Or your URL
    # 插件配置项ID前缀
    plugin_config_prefix = "openwrt_backup_"
    # 加载顺序
    plugin_order = 11 # Different from ikuai
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
    
    _openwrt_host: str = ""
    _openwrt_port: int = 22
    _openwrt_username: str = "root"
    _openwrt_password: str = ""
    _backup_path: str = ""
    _keep_backup_num: int = 7
    _backup_command: str = "sysupgrade -b /tmp/backup-{timestamp}.tar.gz"
    _remote_backup_path: str = "/tmp/" # Path on OpenWrt where backup is temporarily stored

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
            self._openwrt_host = str(config.get("openwrt_host", ""))
            self._openwrt_port = int(config.get("openwrt_port", 22))
            self._openwrt_username = str(config.get("openwrt_username", "root"))
            self._openwrt_password = str(config.get("openwrt_password", ""))
            configured_backup_path = str(config.get("backup_path", "")).strip()
            if not configured_backup_path:
                self._backup_path = str(self.get_data_path() / "openwrt_backups")
                logger.info(f"{self.plugin_name} 备份文件存储路径未配置，使用默认: {self._backup_path}")
            else:
                self._backup_path = configured_backup_path
            self._keep_backup_num = int(config.get("keep_backup_num", 7))
            self._backup_command = str(config.get("backup_command", "sysupgrade -b /tmp/backup-{timestamp}.tar.gz"))
            self._remote_backup_path = str(config.get("remote_backup_path", "/tmp/"))
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
            "openwrt_host": self._openwrt_host,
            "openwrt_port": self._openwrt_port,
            "openwrt_username": self._openwrt_username,
            "openwrt_password": self._openwrt_password,
            "backup_path": self._backup_path,
            "keep_backup_num": self._keep_backup_num,
            "notification_style": self._notification_style,
            "backup_command": self._backup_command,
            "remote_backup_path": self._remote_backup_path,
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
        default_backup_location_desc = "插件数据目录下的 openwrt_backups 子目录"
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
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'openwrt_host', 'label': 'OpenWrt 主机地址', 'placeholder': '例如: 192.168.1.1'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VCronField', 'props': {'model': 'cron', 'label': '执行周期'}}]}
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 3}, 'content': [{'component': 'VTextField', 'props': {'model': 'openwrt_username', 'label': '用户名', 'placeholder': '默认为 root'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 3}, 'content': [{'component': 'VTextField', 'props': {'model': 'openwrt_password', 'label': '密码', 'type': 'password'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 3}, 'content': [{'component': 'VTextField', 'props': {'model': 'openwrt_port', 'label': 'SSH端口', 'type': 'number', 'placeholder': '默认为 22'}}]}
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 12}, 'content': [{'component': 'VTextField', 'props': {'model': 'backup_path', 'label': '备份文件存储路径', 'placeholder': f'默认为: {default_backup_location_desc}'}}]}
                        ],
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'keep_backup_num', 'label': '保留备份数量', 'type': 'number', 'placeholder': '默认为 7'}}]},
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VSelect', 'props': {'model': 'notification_style', 'label': '通知方式', 'items': [{'value':1, 'title': '简洁通知'}, {'value':2, 'title': '详细通知'}]}}]}
                        ],
                    },
                     {
                        'component': 'VRow',
                        'content': [
                            {'component': 'VCol', 'props': {'cols': 12, 'md': 12}, 'content': [{'component': 'VTextField', 'props': {'model': 'backup_command', 'label': 'OpenWrt备份命令', 'placeholder': '例如: sysupgrade -b /tmp/backup-{timestamp}.tar.gz', 'hint': '支持占位符: {timestamp} (YYYYMMDDHHMMSS) 和 {date} (YYYY-MM-DD)', 'persistent-hint': True}}]}
                        ],
                    },
                    {
                        'component': 'VExpansionPanels',
                        'props': {'title': '高级设置'},
                        'content': [
                            {
                                'component': 'VExpansionPanel',
                                'content': [
                                    {
                                        'component': 'VExpansionPanelTitle',
                                        'content': '重试设置'
                                    },
                                    {
                                        'component': 'VExpansionPanelText',
                                        'content': [
                                            {
                                                'component': 'VRow',
                                                'content': [
                                                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'retry_count', 'label': '重试次数', 'type': 'number'}}]},
                                                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6}, 'content': [{'component': 'VTextField', 'props': {'model': 'retry_interval', 'label': '重试间隔 (秒)', 'type': 'number'}}]}
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": self._enabled,
            "notify": self._notify,
            "cron": self._cron,
            "onlyonce": self._onlyonce,
            "retry_count": self._retry_count,
            "retry_interval": self._retry_interval,
            "openwrt_host": self._openwrt_host,
            "openwrt_port": self._openwrt_port,
            "openwrt_username": self._openwrt_username,
            "openwrt_password": self._openwrt_password,
            "backup_path": self._backup_path,
            "keep_backup_num": self._keep_backup_num,
            "notification_style": self._notification_style,
            "backup_command": self._backup_command,
            "remote_backup_path": self._remote_backup_path,
        }

    def get_page(self) -> List[dict]:
        history = self._load_backup_history()
        table_headers = [
            {"title": "备份时间", "key": "backup_time", "align": "center", "sortable": True},
            {"title": "文件名", "key": "filename", "align": "center", "sortable": False},
            {"title": "大小", "key": "size", "align": "center", "sortable": False},
            {"title": "状态", "key": "status", "align": "center", "sortable": False},
            {"title": "消息", "key": "message", "align": "left", "sortable": False, "width": "30%"},
        ]
        return [
            {
                "component": "VCard",
                "props": {"title": "备份历史"},
                "content": [
                    {
                        "component": "VDataTable",
                        "props": {
                            "headers": table_headers,
                            "items": history,
                            "items-per-page": 10,
                            "multi-sort": True,
                            "hover": True,
                            "density": "compact"
                        }
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
        with self._lock:
            if self._running:
                logger.info(f"{self.plugin_name} 备份任务已在运行中，跳过此次执行")
                return
            self._running = True
        
        logger.info(f"{self.plugin_name} 开始执行备份任务")
        success = False
        backup_file_path = None
        error_message = ""

        for i in range(self._retry_count + 1):
            try:
                success, backup_file_path, error_message = self._perform_backup_once()
                if success:
                    logger.info(f"{self.plugin_name} 备份成功: {backup_file_path}")
                    break
                else:
                    logger.error(f"{self.plugin_name} 备份尝试 {i+1}/{self._retry_count + 1} 失败: {error_message}")
                    if i < self._retry_count:
                        logger.info(f"将在 {self._retry_interval} 秒后重试...")
                        time.sleep(self._retry_interval)
            except Exception as e:
                logger.error(f"{self.plugin_name} 备份尝试 {i+1}/{self._retry_count + 1} 出现意外错误: {e}")
                error_message = str(e)
                if i < self._retry_count:
                    logger.info(f"将在 {self._retry_interval} 秒后重试...")
                    time.sleep(self._retry_interval)
        
        # Save history entry
        status_message = "成功" if success else "失败"
        if not success and not error_message:
            error_message = "未知错误"
        elif success and error_message: # Should not happen, but good to cover
             status_message = f"成功但有警告: {error_message}"

        file_size_str = "N/A"
        if success and backup_file_path and Path(backup_file_path).exists():
            try:
                file_size = Path(backup_file_path).stat().st_size
                if file_size < 1024:
                    file_size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    file_size_str = f"{file_size / 1024:.2f} KB"
                else:
                    file_size_str = f"{file_size / (1024 * 1024):.2f} MB"
            except Exception as e:
                logger.error(f"{self.plugin_name} 获取文件大小失败 {backup_file_path}: {e}")
                file_size_str = "错误"

        history_entry = {
            "backup_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filename": Path(backup_file_path).name if backup_file_path else "N/A",
            "size": file_size_str,
            "status": status_message,
            "message": error_message if not success else ""
        }
        self._save_backup_history_entry(history_entry)

        if self._notify:
            self._send_notification(success, message=error_message, filename=Path(backup_file_path).name if backup_file_path else None)
        
        if success:
            self._cleanup_old_backups()

        with self._lock:
            self._running = False
        logger.info(f"{self.plugin_name} 备份任务执行完毕")

    def _perform_backup_once(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Performs a single backup attempt for OpenWrt.
        This method needs to be implemented with SSH logic.
        Returns: Tuple (success: bool, local_backup_filepath: Optional[str], error_message: Optional[str])
        """
        logger.info(f"{self.plugin_name} 开始连接 OpenWrt 主机: {self._openwrt_host}:{self._openwrt_port}")

        timestamp_dt = datetime.now()
        ts_full = timestamp_dt.strftime("%Y%m%d%H%M%S") # YYYYMMDDHHMMSS
        ts_date = timestamp_dt.strftime("%Y-%m-%d")   # YYYY-MM-DD

        actual_backup_command = self._backup_command
        command_parts = list(self._backup_command.split(' ')) # Make it a list for modification
        if not command_parts:
            return False, None, "Backup command is empty."
        
        # Assume the filename template is the last argument of the command
        filename_template_in_command = command_parts[-1]
        
        final_filename_part_for_command: str

        if '{timestamp}' in filename_template_in_command:
            final_filename_part_for_command = filename_template_in_command.replace('{timestamp}', ts_full)
            actual_backup_command = actual_backup_command.replace('{timestamp}', ts_full) # Replace in whole command string too
        elif '{date}' in filename_template_in_command:
            final_filename_part_for_command = filename_template_in_command.replace('{date}', ts_date)
            actual_backup_command = actual_backup_command.replace('{date}', ts_date) # Replace in whole command string too
        else:
            # No specific placeholder in the filename part. Append full timestamp for uniqueness.
            base, ext = os.path.splitext(filename_template_in_command)
            # Ensure extension is correctly handled, e.g. .tar.gz
            if ext.lower() == '.gz' and base.lower().endswith('.tar'):
                ext = ".tar.gz"
                base = base[:-4]

            unique_suffix = f"-{ts_full}{ext}"
            final_filename_part_for_command = f"{base}{unique_suffix}"
            
            # Update the command string with this unique filename
            temp_command_parts = self._backup_command.split(' ') # re-split original command
            temp_command_parts[-1] = final_filename_part_for_command
            actual_backup_command = ' '.join(temp_command_parts)
            logger.info(f"备份命令的文件名部分未使用 {{timestamp}} 或 {{date}} 占位符。追加时间戳确保唯一性: {final_filename_part_for_command}")

        # Determine the final absolute path on the remote system for SFTP/SCP
        final_remote_path_for_sftp: str
        if os.path.isabs(final_filename_part_for_command):
            final_remote_path_for_sftp = os.path.normpath(final_filename_part_for_command)
        else:
            # If _remote_backup_path is empty, this effectively means relative to SSH user's home or CWD.
            # It's generally better to have _remote_backup_path set.
            final_remote_path_for_sftp = os.path.normpath(os.path.join(self._remote_backup_path or '.', final_filename_part_for_command))

        # Update the actual_backup_command to use this potentially modified (e.g., made absolute) path
        # This makes the command more explicit.
        command_parts_for_final_cmd = actual_backup_command.split(' ')
        if command_parts_for_final_cmd[-1] != final_remote_path_for_sftp:
             logger.debug(f"Updating command's last argument from '{command_parts_for_final_cmd[-1]}' to '{final_remote_path_for_sftp}'")
             command_parts_for_final_cmd[-1] = final_remote_path_for_sftp
             actual_backup_command = ' '.join(command_parts_for_final_cmd)
        
        # Security check: Is final_remote_path_for_sftp under _remote_backup_path (if configured)?
        if self._remote_backup_path.strip(): # Only perform check if _remote_backup_path is configured
            # Normalize both paths for a robust check
            norm_remote_base_path = os.path.normpath(self._remote_backup_path)
            # Add a separator to base path if it's not root, for correct prefix checking
            if norm_remote_base_path != os.path.dirname(norm_remote_base_path): # not root
                 norm_remote_base_path += os.sep
            
            norm_final_sftp_path = os.path.normpath(final_remote_path_for_sftp)

            if not norm_final_sftp_path.startswith(norm_remote_base_path):
                return False, None, f"备份命令输出文件 '{final_filename_part_for_command}' 解析为 '{norm_final_sftp_path}', 该路径不在配置的远程备份路径 '{self._remote_backup_path}' ({norm_remote_base_path}) 下。"

        local_filename = os.path.basename(final_remote_path_for_sftp) # Use the name part of the SFTP path
        local_filepath_to_save = str(Path(self._backup_path) / local_filename)

        logger.info(f"将在 OpenWrt 上执行备份命令: {actual_backup_command}")
        logger.info(f"预期远程备份文件 (供下载): {final_remote_path_for_sftp}")
        logger.info(f"备份文件将下载到: {local_filepath_to_save}")

        # --- SSH LOGIC NEEDED HERE ---
        # try:
        #     import paramiko
        # except ImportError:
        #     logger.error(f"{self.plugin_name} 依赖 paramiko 未安装，请先安装: pip install paramiko")
        #     return False, None, "SSH library (paramiko) not installed."
        #
        # client = paramiko.SSHClient()
        # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # try:
        #     client.connect(self._openwrt_host, port=self._openwrt_port, username=self._openwrt_username, password=self._openwrt_password, timeout=10)
        #     
        #     # Execute backup command
        #     logger.info(f"Executing remote command: {actual_backup_command}")
        #     stdin, stdout, stderr = client.exec_command(actual_backup_command)
        #     exit_status = stdout.channel.recv_exit_status()
        #     stdout_output = stdout.read().decode(errors='ignore').strip()
        #     stderr_output = stderr.read().decode(errors='ignore').strip()
        #
        #     if exit_status != 0:
        #         error_msg = f"远程命令执行失败 (代码: {exit_status})."
        #         if stdout_output: error_msg += f"\nSTDOUT: {stdout_output}"
        #         if stderr_output: error_msg += f"\nSTDERR: {stderr_output}"
        #         logger.error(error_msg)
        #         client.close()
        #         return False, None, error_msg
        #     
        #     logger.info(f"远程命令成功执行. STDOUT: {stdout_output}, STDERR: {stderr_output}")
        #
        #     # Download the file via SCP or SFTP
        #     sftp = client.open_sftp()
        #     logger.info(f"尝试从 {final_remote_path_for_sftp} 下载到 {local_filepath_to_save}")
        #     sftp.get(final_remote_path_for_sftp, local_filepath_to_save)
        #     sftp.close()
        #     logger.info(f"文件成功下载到 {local_filepath_to_save}")
        #
        #     # Clean up remote backup file
        #     logger.info(f"删除远程备份文件: {final_remote_path_for_sftp}")
        #     sftp = client.open_sftp() 
        #     sftp.remove(final_remote_path_for_sftp)
        #     sftp.close()
        #     logger.info(f"远程文件 {final_remote_path_for_sftp} 已删除")
        #     
        #     client.close()
        #     return True, local_filepath_to_save, None
        #
        # except paramiko.AuthenticationException:
        #     logger.error(f"SSH 认证失败 for {self._openwrt_username}@{self._openwrt_host}:{self._openwrt_port}")
        #     return False, None, "SSH authentication failed."
        # except paramiko.SSHException as ssh_ex:
        #     logger.error(f"SSH 连接错误: {ssh_ex}")
        #     return False, None, f"SSH connection error: {ssh_ex}"
        # except FileNotFoundError: # For sftp.get or sftp.remove if remote file isn't there
        #      logger.error(f"远程文件未找到: {final_remote_path_for_sftp}")
        #      return False, None, f"Remote file not found: {final_remote_path_for_sftp}"
        # except Exception as e:
        #     logger.error(f"备份过程中发生未知错误: {e}")
        #     if 'client' in locals() and client.get_transport() and client.get_transport().is_active():
        #         client.close()
        #     return False, None, f"An unexpected error occurred: {e}"
        # --- END SSH LOGIC PLACEHOLDER ---

        # Simulate success for now until SSH is implemented
        logger.warning(f"{self.plugin_name} _perform_backup_once 尚未完全实现SSH逻辑，当前为模拟成功。")
        try:
            Path(local_filepath_to_save).touch() # Create a dummy file
            logger.info(f"创建模拟备份文件: {local_filepath_to_save}")
            return True, local_filepath_to_save, None
        except Exception as e:
            logger.error(f"创建模拟备份文件失败: {e}")
            return False, None, f"Failed to create dummy backup file: {e}"

    def _cleanup_old_backups(self):
        logger.info(f"{self.plugin_name} 开始清理旧备份，保留数量: {self._keep_backup_num}")
        try:
            backup_dir = Path(self._backup_path)
            if not backup_dir.exists() or not backup_dir.is_dir():
                logger.warning(f"备份目录 {self._backup_path} 不存在或不是一个目录，跳过清理。")
                return

            backup_files = []
            for item in backup_dir.iterdir():
                if item.is_file() and item.name.lower().endswith(".tar.gz") and item.name.lower().startswith("backup-"):
                    dt_obj = None
                    try:
                        # 1. Try parsing YYYYMMDDHHMMSS format (plugin's default timestamped format)
                        #    e.g., backup-20231027153000.tar.gz
                        match_timestamp = re.search(r"backup-(\d{14})\.tar\.gz", item.name, re.IGNORECASE)
                        if match_timestamp:
                            dt_str = match_timestamp.group(1)
                            dt_obj = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
                        
                        if not dt_obj:
                            # 2. Try parsing backup-ANYNAME-YYYY-MM-DD.tar.gz format
                            #    e.g., backup-immortalwrt-2023-10-27.tar.gz
                            match_named_date = re.search(r"backup-(?:.*?)-(\d{4}-\d{2}-\d{2})\.tar\.gz", item.name, re.IGNORECASE)
                            if match_named_date:
                                dt_str = match_named_date.group(1)
                                dt_obj = datetime.strptime(dt_str, "%Y-%m-%d")

                        if not dt_obj:
                            # 3. Try parsing a more generic YYYY-MM-DD from anywhere after "backup-"
                            #    e.g., backup-OpenWrt-Snapshot-2023-10-27-generic.tar.gz
                            match_generic_date = re.search(r"backup-.*?(\d{4}-\d{2}-\d{2})", item.name, re.IGNORECASE)
                            if match_generic_date:
                                dt_str = match_generic_date.group(1)
                                dt_obj = datetime.strptime(dt_str, "%Y-%m-%d")
                        
                        if not dt_obj:
                            # 4. Fallback to file modification time if no date pattern matched
                            logger.debug(f"无法从文件名 {item.name} 解析日期，将使用文件修改时间。")
                            dt_obj = datetime.fromtimestamp(item.stat().st_mtime)
                        
                        backup_files.append((dt_obj, item))

                    except ValueError as ve:
                        logger.warning(f"解析备份文件 {item.name} 日期/时间出错: {ve}，将使用文件修改时间。")
                        backup_files.append((datetime.fromtimestamp(item.stat().st_mtime), item))
                    except Exception as e:
                        logger.error(f"处理备份文件 {item.name} 时发生意外错误: {e}，将使用文件修改时间。")
                        backup_files.append((datetime.fromtimestamp(item.stat().st_mtime), item))
            
            # Sort files by date (oldest first)
            backup_files.sort(key=lambda x: x[0])
            
            num_to_delete = len(backup_files) - self._keep_backup_num
            if num_to_delete > 0:
                logger.info(f"发现 {len(backup_files)} 个备份文件，需要删除 {num_to_delete} 个旧备份。")
                files_deleted_count = 0
                for i in range(num_to_delete):
                    file_to_delete = backup_files[i][1]
                    try:
                        file_to_delete.unlink()
                        logger.info(f"已删除旧备份: {file_to_delete.name}")
                        files_deleted_count += 1
                    except Exception as e:
                        logger.error(f"删除旧备份 {file_to_delete.name} 失败: {e}")
                logger.info(f"成功删除 {files_deleted_count} 个旧备份文件。")
            else:
                logger.info(f"备份文件数量 ({len(backup_files)}) 未超过限制 ({self._keep_backup_num})，无需清理。")

        except Exception as e:
            logger.error(f"{self.plugin_name} 清理旧备份时出错: {e}")

    def _send_notification(self, success: bool, message: str = "", filename: Optional[str] = None):
        if not self._notify:
            return
        
        title = f"{self.plugin_name} - {'备份成功' if success else '备份失败'}"
        
        if self._notification_style == 1: # 简洁通知
            content = title
            if success and filename:
                content += f"\n文件名: {filename}"
            elif not success and message:
                content += f"\n原因: {message}"
        else: # 详细通知 (style 2)
            content = f"## {title}\n\n"
            if success:
                content += f"**状态**: ✅ 成功\n"
                if filename:
                    content += f"**文件名**: `{filename}`\n"
                content += f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            else:
                content += f"**状态**: ❌ 失败\n"
                if message:
                    content += f"**原因**: {message}\n"
                content += f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            content += f"\n主机: {self._openwrt_host}"

        self.send_message(title=title, message=content, messagetype=NotificationType.Plugin)
        logger.info(f"{self.plugin_name} 已发送通知: {title}")

    # --- Helper methods for OpenWrt interaction (to be implemented with SSH) ---
    # These methods would replace the ikuai-specific ones like _login_ikuai, _create_backup_on_router, etc.
    # For OpenWrt, it's mainly about:
    # 1. Establishing SSH connection
    # 2. Running the backup command (e.g., sysupgrade -b ...)
    # 3. Downloading the file (e.g., using SCP/SFTP)
    # 4. Cleaning up the temp file on the router

    # Example (these are not called directly in the current placeholder _perform_backup_once)
    def _connect_ssh(self):
        # Placeholder for establishing SSH connection
        # Needs paramiko or similar library
        # Should return an SSH client object or raise an exception
        pass

    def _execute_remote_command(self, client, command: str) -> Tuple[bool, str, str]:
        # Placeholder for executing a command over SSH
        # Returns (success_bool, stdout_str, stderr_str)
        return False, "", "Not Implemented"

    def _download_file_sftp(self, client, remote_path: str, local_path: str) -> bool:
        # Placeholder for downloading a file via SFTP
        return False

    def _delete_remote_file_sftp(self, client, remote_path: str) -> bool:
        # Placeholder for deleting a remote file via SFTP
        return False


