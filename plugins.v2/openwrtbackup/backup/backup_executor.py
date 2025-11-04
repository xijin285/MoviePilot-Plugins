"""
备份执行模块
负责执行备份任务的主要逻辑
"""
import threading
import time
from pathlib import Path
from typing import Optional, Tuple
from app.log import logger

from ..openwrt.client import OpenWrtClient
from ..backup.backup_manager import BackupManager
from ..webdav.webdav_client import WebDAVClient


class BackupExecutor:
    """备份执行器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化备份执行器
        :param plugin_instance: OpenWrtBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        self.openwrt_client = OpenWrtClient(plugin_instance)
        self.backup_manager = BackupManager(plugin_instance)
    
    def run_backup_job(self):
        """执行备份任务"""
        if not self.plugin._lock:
            self.plugin._lock = threading.Lock()
        if not self.plugin._lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 已有任务正在执行，本次调度跳过！")
            return
        
        try:
            self.plugin._running = True
            logger.info(f"开始执行 {self.plugin_name} 任务...")

            if not self.plugin._openwrt_host or not self.plugin._openwrt_username or not self.plugin._openwrt_password:
                error_msg = "配置不完整：URL、用户名或密码未设置。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._send_notification(success=False, message=error_msg)
                return

            if not self.plugin._backup_path:
                error_msg = "备份路径未配置且无法设置默认路径。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._send_notification(success=False, message=error_msg)
                return

            try:
                Path(self.plugin._backup_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                error_msg = f"创建本地备份目录 {self.plugin._backup_path} 失败: {e}"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._send_notification(success=False, message=error_msg)
                return
            
            success_final = False
            error_msg_final = "未知错误"
            downloaded_file_final = None
            
            for i in range(self.plugin._retry_count + 1):
                logger.info(f"{self.plugin_name} 开始第 {i+1}/{self.plugin._retry_count + 1} 次备份尝试...")
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
                    if i < self.plugin._retry_count:
                        logger.info(f"{self.plugin._retry_interval}秒后重试...")
                        time.sleep(self.plugin._retry_interval)
                    else:
                        logger.error(f"{self.plugin_name} 所有 {self.plugin._retry_count + 1} 次尝试均失败。最后错误: {error_msg_final}")
            
            message = "备份成功" if success_final else f"备份失败: {error_msg_final}"
            self.plugin._send_notification(success=success_final, message=message, filename=downloaded_file_final)
            
        except Exception as e:
            error_msg = f"任务执行主流程出错: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            self.plugin._send_notification(success=False, message=error_msg)
        finally:
            self.plugin._running = False
            if self.plugin._lock and hasattr(self.plugin._lock, 'locked') and self.plugin._lock.locked():
                try:
                    self.plugin._lock.release()
                except RuntimeError:
                    pass
            logger.debug(f"{self.plugin_name} 任务执行完成。")
    
    def _perform_backup_once(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """执行一次备份操作"""
        http_client = None
        
        try:
            # 连接到OpenWrt
            http_client, error = self.openwrt_client.connect()
            if not http_client:
                return False, f"HTTP连接失败: {error}", None
            
            # 创建备份
            success, error_msg, backup_filename, local_temp_path = self.openwrt_client.create_backup(http_client)
            if not success:
                return False, error_msg, None
            
            local_filepath = None
            
            # 备份已经直接下载到本地临时文件，移动到备份目录
            if self.plugin._enable_local_backup:
                try:
                    # 确保本地备份目录存在
                    Path(self.plugin._backup_path).mkdir(parents=True, exist_ok=True)
                    local_filepath = Path(self.plugin._backup_path) / backup_filename
                    
                    # 移动文件从临时目录到备份目录
                    import shutil
                    shutil.move(local_temp_path, str(local_filepath))
                    logger.info(f"{self.plugin_name} 备份文件已从临时目录移动到: {local_filepath}")
                    
                    # 验证文件是否存在
                    if not local_filepath.exists():
                        return False, f"移动文件后文件不存在: {local_filepath}", None
                    
                    # 清理本地旧备份
                    self.backup_manager.cleanup_old_backups()
                except Exception as e:
                    return False, f"移动备份文件失败: {str(e)}", None
            
            # 如果启用了WebDAV，上传到WebDAV
            if self.plugin._enable_webdav:
                # 确定要上传的文件路径
                upload_file_path = None
                if self.plugin._enable_local_backup:
                    # 如果启用了本地备份，使用备份目录的文件
                    if local_filepath and local_filepath.exists():
                        upload_file_path = str(local_filepath)
                    else:
                        return False, f"WebDAV上传失败: 本地备份文件不存在: {local_filepath}", None
                else:
                    # 如果只使用WebDAV，从临时文件上传（此时文件还在临时目录）
                    if local_temp_path and Path(local_temp_path).exists():
                        upload_file_path = local_temp_path
                    else:
                        return False, f"WebDAV上传失败: 临时文件不存在: {local_temp_path}", None
                
                # 执行上传
                webdav_success, webdav_msg = self._upload_to_webdav(upload_file_path, backup_filename)
                
                if not webdav_success:
                    return False, f"WebDAV上传失败: {webdav_msg}", None
                
                # 清理WebDAV上的旧备份
                self._cleanup_webdav_backups()
                
                # 如果只使用WebDAV（没有启用本地备份），上传成功后删除临时文件
                if not self.plugin._enable_local_backup:
                    try:
                        Path(local_temp_path).unlink()
                    except:
                        pass
            
            return True, None, backup_filename
            
        except Exception as e:
            return False, f"备份过程中发生错误: {str(e)}", None
        
        finally:
            # 关闭连接
            if http_client:
                try:
                    http_client.close()
                except Exception as e:
                    logger.warning(f"{self.plugin_name} 关闭HTTP连接失败: {e}")
    
    def _upload_to_webdav(self, local_file_path: str, filename: str) -> Tuple[bool, Optional[str]]:
        """上传文件到WebDAV服务器"""
        if not self.plugin._enable_webdav or not self.plugin._webdav_url:
            return False, "WebDAV未启用或URL未配置"
        
        try:
            # 创建WebDAV客户端
            client = WebDAVClient(
                url=self.plugin._webdav_url,
                username=self.plugin._webdav_username,
                password=self.plugin._webdav_password,
                path=self.plugin._webdav_path,
                skip_dir_check=True,
                logger=logger,
                plugin_name=self.plugin_name
            )
            
            # 执行上传
            success, error = client.upload(local_file_path, filename)
            client.close()
            
            return success, error
            
        except Exception as e:
            error_msg = f"WebDAV上传过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg
    
    def _cleanup_webdav_backups(self):
        """清理WebDAV上的旧备份文件"""
        if not self.plugin._enable_webdav or not self.plugin._webdav_url or self.plugin._webdav_keep_backup_num <= 0:
            return
        
        try:
            # 创建WebDAV客户端
            client = WebDAVClient(
                url=self.plugin._webdav_url,
                username=self.plugin._webdav_username,
                password=self.plugin._webdav_password,
                path=self.plugin._webdav_path,
                skip_dir_check=True,
                logger=logger,
                plugin_name=self.plugin_name
            )
            
            # 执行清理，只保留指定数量的.tar.gz文件
            deleted_count, error = client.cleanup_old_files(self.plugin._webdav_keep_backup_num, '.tar.gz')
            client.close()
            
            if error:
                logger.error(f"{self.plugin_name} WebDAV清理失败: {error}")
            elif deleted_count > 0:
                logger.info(f"{self.plugin_name} WebDAV清理完成，删除了 {deleted_count} 个旧备份文件")
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 清理WebDAV旧备份文件时发生错误: {str(e)}")

