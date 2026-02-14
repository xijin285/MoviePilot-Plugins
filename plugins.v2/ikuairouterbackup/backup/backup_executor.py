"""备份执行模块"""
import os
import json
import time
import threading
from pathlib import Path
from typing import Tuple, Optional
from urllib.parse import urljoin
from app.log import logger
from ..ikuai.client import IkuaiClient
from ..backup.backup_manager import BackupManager


class BackupExecutor:
    """备份执行器类"""
    
    def __init__(self, plugin_instance):
        """初始化备份执行器"""
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        self._backup_manager = BackupManager(plugin_instance)
    
    def run_backup_job(self):
        """执行备份任务（带重试逻辑）"""
        if not self.plugin._lock:
            self.plugin._lock = threading.Lock()
        
        if not self.plugin._lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 已有任务正在执行，本次调度跳过！")
            return
            
        history_entry = {
            "timestamp": time.time(),
            "success": False,
            "filename": None,
            "message": "任务开始"
        }
        self.plugin._backup_activity = "任务开始"
            
        try:
            self.plugin._running = True
            logger.info(f"开始执行 {self.plugin_name} 任务...")

            if not self.plugin._ikuai_url or not self.plugin._ikuai_username or not self.plugin._ikuai_password:
                error_msg = "配置不完整：URL、用户名或密码未设置。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._send_notification(success=False, message=error_msg)
                history_entry["message"] = error_msg
                self.plugin._save_backup_history_entry(history_entry)
                return

            if not self.plugin._backup_path:
                error_msg = "备份路径未配置且无法设置默认路径。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._send_notification(success=False, message=error_msg)
                history_entry["message"] = error_msg
                self.plugin._save_backup_history_entry(history_entry)
                return

            try:
                Path(self.plugin._backup_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                error_msg = f"创建本地备份目录 {self.plugin._backup_path} 失败: {e}"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._send_notification(success=False, message=error_msg)
                history_entry["message"] = error_msg
                self.plugin._save_backup_history_entry(history_entry)
                return
            
            success_final = False
            error_msg_final = "未知错误"
            downloaded_file_final = None
            
            for i in range(self.plugin._retry_count + 1):
                logger.info(f"{self.plugin_name} 开始第 {i+1}/{self.plugin._retry_count +1} 次备份尝试...")
                current_try_success, current_try_error_msg, current_try_downloaded_file = self.perform_backup_once()
                
                if current_try_success:
                    success_final = True
                    downloaded_file_final = current_try_downloaded_file
                    error_msg_final = None
                    logger.info(f"{self.plugin_name} 第{i+1}次尝试成功。备份文件: {downloaded_file_final}")
                    break 
                else:
                    error_msg_final = current_try_error_msg
                    logger.warning(f"{self.plugin_name} 第{i+1}次备份尝试失败: {error_msg_final}")
                    if i < self.plugin._retry_count:
                        logger.info(f"{self.plugin._retry_interval}秒后重试...")
                        time.sleep(self.plugin._retry_interval)
                    else:
                        logger.error(f"{self.plugin_name} 所有 {self.plugin._retry_count +1} 次尝试均失败。最后错误: {error_msg_final}")
            
            history_entry["success"] = success_final
            history_entry["filename"] = downloaded_file_final
            history_entry["message"] = "备份成功" if success_final else f"备份失败: {error_msg_final}"
            
            self.plugin._send_notification(success=success_final, message=history_entry["message"], filename=downloaded_file_final)
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 任务执行主流程出错：{str(e)}")
            history_entry["message"] = f"任务执行主流程出错: {str(e)}"
            self.plugin._send_notification(success=False, message=history_entry["message"])
        finally:
            self.plugin._running = False
            self.plugin._backup_activity = "空闲"
            self.plugin._save_backup_history_entry(history_entry)
            if self.plugin._lock and hasattr(self.plugin._lock, 'locked') and self.plugin._lock.locked():
                try: self.plugin._lock.release()
                except RuntimeError: pass
            logger.info(f"{self.plugin_name} 任务执行完成。")
    
    def perform_backup_once(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        执行一次备份操作
        
        :return: (是否成功, 错误信息, 备份文件名)
        """
        # 初始化iKuai客户端
        client = IkuaiClient(
            url=self.plugin._ikuai_url,
            username=self.plugin._ikuai_username,
            password=self.plugin._ikuai_password,
            plugin_name=self.plugin_name
        )
        
        # 登录
        if not client.login():
            return False, "登录爱快路由失败，无法获取SESS_KEY", None
        
        # 创建备份
        create_success, create_msg = client.create_backup()
        if not create_success:
            return False, f"创建备份失败: {create_msg}", None
        
        logger.info(f"{self.plugin_name} 成功触发创建备份。等待2秒让备份生成和准备就绪...")
        time.sleep(2)
        
        # 获取备份列表
        backup_list = client.get_backup_list()
        if backup_list is None:
            return False, "获取备份文件列表时出错 (在下载前调用)", None
        if not backup_list:
            return False, "路由器上没有找到任何备份文件 (在下载前获取列表为空)", None
        
        # 兼容新老版本，按 date 字段降序排序，优先取 filename，没有则取 name
        def get_date(x):
            # 兼容各种字段名
            return x.get("date") or x.get("backup_time") or ""
        sorted_backups = sorted(backup_list, key=get_date, reverse=True)
        latest_backup = sorted_backups[0] if sorted_backups else None
        actual_router_filename_from_api = None
        if latest_backup:
            actual_router_filename_from_api = latest_backup.get("filename") or latest_backup.get("name")
        if not actual_router_filename_from_api:
            return False, "无法从备份列表中获取最新备份的文件名", None
        # 确定文件名
        filename_for_download_url = actual_router_filename_from_api
        base_name_for_local_file = os.path.splitext(actual_router_filename_from_api)[0]
        local_display_and_saved_filename = base_name_for_local_file + ".bak"
        local_filepath_to_save = Path(self.plugin._backup_path) / local_display_and_saved_filename
        logger.info(f"{self.plugin_name} API列表最新备份名: {actual_router_filename_from_api}. 将尝试以此名下载.")
        logger.info(f"{self.plugin_name} 最终本地保存文件名将为: {local_display_and_saved_filename}")
        
        # 发送EXPORT请求
        if not self._send_export_request(client.session, local_display_and_saved_filename):
            return False, "EXPORT请求失败", None
        
        # 执行本地备份
        download_success = False
        if self.plugin._enable_local_backup:
            if not self.plugin._backup_path:
                return False, "本地备份已启用但备份路径未配置且无法设置默认路径", None
            
            try:
                Path(self.plugin._backup_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"创建本地备份目录失败: {e}", None
            
            download_success, download_msg = client.download_backup(
                filename_for_download_url, 
                str(local_filepath_to_save)
            )
            if not download_success:
                error_detail = f"尝试下载 {filename_for_download_url} 失败: {download_msg}"
                return False, error_detail, None
            
            # 清理本地旧备份
            self._backup_manager.cleanup_old_backups()
        else:
            logger.info(f"{self.plugin_name} 本地备份已禁用，跳过本地备份步骤")
        
        # 执行WebDAV备份
        webdav_success = False
        if self.plugin._enable_webdav:
            webdav_success = self._upload_to_webdav(client, 
                                                  download_success, 
                                                  filename_for_download_url,
                                                  local_display_and_saved_filename,
                                                  str(local_filepath_to_save))
        
        # 如果开启备份后删除，执行删除操作
        if self.plugin._delete_after_backup and (download_success or webdav_success):
            self._delete_backup_after_success(client, actual_router_filename_from_api)
        
        return True, None, local_display_and_saved_filename
    
    def _send_export_request(self, session, filename: str) -> bool:
        """发送EXPORT请求"""
        export_payload = {
            "func_name": "backup",
            "action": "EXPORT",
            "param": {"srcfile": filename}
        }
        export_url = urljoin(self.plugin._ikuai_url, "/Action/call")
        
        try:
            logger.info(f"{self.plugin_name} 尝试向 {export_url} 发送 EXPORT 请求...")
            response = session.post(
                export_url, 
                data=json.dumps(export_payload), 
                headers={'Content-Type': 'application/json'}, 
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"{self.plugin_name} EXPORT 请求发送成功。响应: {response.text[:200]}")
            return True
        except Exception as e:
            logger.error(f"{self.plugin_name} EXPORT请求失败: {e}")
            return False
    
    def _upload_to_webdav(self, client, local_backup_enabled, 
                         router_filename, local_filename, local_filepath) -> bool:
        """处理WebDAV上传"""
        try:
            if local_backup_enabled:
                # 使用已下载的文件上传
                webdav_success, webdav_msg = self.plugin._upload_to_webdav(local_filepath, local_filename)
            else:
                # 下载到临时文件再上传
                temp_dir = Path(self.plugin.get_data_path()) / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                temp_filepath = temp_dir / local_filename
                
                download_success, download_msg = client.download_backup(router_filename, str(temp_filepath))
                if not download_success:
                    logger.error(f"{self.plugin_name} WebDAV临时下载失败: {download_msg}")
                    return False
                
                webdav_success, webdav_msg = self.plugin._upload_to_webdav(str(temp_filepath), local_filename)
                
                # 删除临时文件
                try:
                    temp_filepath.unlink()
                except Exception as e:
                    logger.warning(f"{self.plugin_name} 删除临时文件失败: {e}")
            
            if webdav_success:
                logger.info(f"{self.plugin_name} 成功上传备份到WebDAV服务器")
                self.plugin._cleanup_webdav_backups()
            else:
                logger.error(f"{self.plugin_name} WebDAV上传失败: {webdav_msg}")
            
            return webdav_success
            
        except Exception as e:
            logger.error(f"{self.plugin_name} WebDAV上传过程中发生错误: {e}")
            return False
    
    def _delete_backup_after_success(self, client, filename: str):
        """备份成功后删除路由器上的备份文件"""
        logger.info(f"{self.plugin_name} 备份成功，将删除路由器上的备份文件: {filename}")
        delete_success, delete_msg = client.delete_backup(filename)
        if delete_success:
            logger.info(f"{self.plugin_name} 成功删除路由器上的备份文件。")
        else:
            logger.warning(f"{self.plugin_name} 删除路由器上的备份文件失败: {delete_msg}")

