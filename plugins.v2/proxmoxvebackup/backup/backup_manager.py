"""
备份文件管理模块
负责处理备份文件的下载、上传、清理、列表等操作
"""
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import paramiko
from app.log import logger


class BackupManager:
    """备份文件管理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化备份文件管理器
        :param plugin_instance: ProxmoxVEBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def cleanup_old_backups(self):
        """清理本地旧备份文件"""
        if not self.plugin._backup_path:
            return
        # 如果保留数量为0，表示保留全部备份，不进行清理
        if self.plugin._keep_backup_num <= 0:
            logger.info(f"{self.plugin_name} 保留数量设置为0，保留全部本地备份文件")
            return
        try:
            logger.info(f"{self.plugin_name} 开始清理本地备份目录: {self.plugin._backup_path}")
            backup_dir = Path(self.plugin._backup_path)
            if not backup_dir.is_dir():
                logger.warning(f"{self.plugin_name} 本地备份目录 {self.plugin._backup_path} 不存在，无需清理。")
                return

            files = []
            for f_path_obj in backup_dir.iterdir():
                if f_path_obj.is_file() and (
                    f_path_obj.name.endswith('.tar.gz') or 
                    f_path_obj.name.endswith('.tar.lzo') or 
                    f_path_obj.name.endswith('.tar.zst') or
                    f_path_obj.name.endswith('.vma.gz') or 
                    f_path_obj.name.endswith('.vma.lzo') or 
                    f_path_obj.name.endswith('.vma.zst')
                ):
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
            
            if len(files) > self.plugin._keep_backup_num:
                files_to_delete = files[self.plugin._keep_backup_num:]
                logger.info(f"{self.plugin_name} 找到 {len(files_to_delete)} 个旧 Proxmox 备份文件需要删除。")
                for f_info in files_to_delete:
                    try:
                        f_info['path'].unlink()
                        logger.info(f"{self.plugin_name} 已删除旧备份文件: {f_info['name']}")
                    except OSError as e:
                        logger.error(f"{self.plugin_name} 删除旧备份文件 {f_info['name']} 失败: {e}")
            else:
                logger.info(f"{self.plugin_name} 当前 Proxmox 备份文件数量 ({len(files)}) 未超过保留限制 ({self.plugin._keep_backup_num})，无需清理。")
        except Exception as e:
            logger.error(f"{self.plugin_name} 清理旧备份文件时发生错误: {e}")

    def upload_to_webdav(self, local_file_path: str, filename: str) -> Tuple[bool, Optional[str]]:
        """上传文件到WebDAV服务器（使用新的WebDAV客户端）"""
        if not self.plugin._enable_webdav or not self.plugin._webdav_url:
            return False, "WebDAV未启用或URL未配置"
        
        try:
            from ..storage.webdav import WebDAVClient
            
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
            
            # 定义进度回调
            def progress_callback(uploaded: int, total: int, speed: float):
                progress = (uploaded / total) * 100 if total > 0 else 0
                self.plugin._backup_activity = f"上传WebDAV中: {progress:.1f}% 平均速度: {speed:.2f}MB/s"
                logger.info(f"{self.plugin_name} WebDAV上传进度: {progress:.1f}% 平均速度: {speed:.2f}MB/s")
            
            # 执行上传
            success, error = client.upload(local_file_path, filename, progress_callback)
            client.close()
            
            return success, error

        except Exception as e:
            error_msg = f"WebDAV上传过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg

    def cleanup_webdav_backups(self):
        """清理WebDAV上的旧备份文件（使用新的WebDAV客户端）"""
        if not self.plugin._enable_webdav or not self.plugin._webdav_url:
            return
        # 如果保留数量为0，表示保留全部备份，不进行清理
        if self.plugin._webdav_keep_backup_num <= 0:
            logger.info(f"{self.plugin_name} WebDAV保留数量设置为0，保留全部WebDAV备份文件")
            return

        try:
            from ..storage.webdav import WebDAVClient
            
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
            
            # 执行清理（保留最新的N个文件）
            deleted_count, error = client.cleanup_old_files(
                keep_count=self.plugin._webdav_keep_backup_num,
                pattern=None  # 可以根据需要添加文件名模式
            )
            
            if error:
                logger.error(f"{self.plugin_name} WebDAV清理失败: {error}")
            else:
                logger.info(f"{self.plugin_name} WebDAV清理完成，已删除 {deleted_count} 个旧备份文件")

            client.close()

        except Exception as e:
            logger.error(f"{self.plugin_name} WebDAV清理过程中发生错误: {str(e)}")

    def get_available_backups(self) -> List[Dict[str, Any]]:
        """获取可用的备份文件列表"""
        backups = []
        
        # 获取本地备份文件
        if self.plugin._enable_local_backup:
            try:
                # 如果_backup_path为空，使用默认路径
                backup_dir = Path(self.plugin._backup_path) if self.plugin._backup_path else Path(self.plugin.get_data_path()) / "actual_backups"
                if backup_dir.is_dir():
                    for file_path in backup_dir.iterdir():
                        if file_path.is_file() and (
                            file_path.name.endswith('.tar.gz') or 
                            file_path.name.endswith('.tar.lzo') or 
                            file_path.name.endswith('.tar.zst') or
                            file_path.name.endswith('.vma.gz') or 
                            file_path.name.endswith('.vma.lzo') or 
                            file_path.name.endswith('.vma.zst')
                        ):
                            try:
                                stat = file_path.stat()
                                size_mb = stat.st_size / (1024 * 1024)
                                time_str = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                                
                                backups.append({
                                    'filename': file_path.name,
                                    'path': str(file_path),
                                    'size_mb': size_mb,
                                    'time_str': time_str,
                                    'source': '本地备份'
                                })
                            except Exception as e:
                                logger.error(f"{self.plugin_name} 处理本地备份文件 {file_path.name} 时出错: {e}")
            except Exception as e:
                logger.error(f"{self.plugin_name} 获取本地备份文件列表失败: {e}")
        
        # 获取WebDAV备份文件
        if self.plugin._enable_webdav and self.plugin._webdav_url:
            try:
                webdav_backups = self.get_webdav_backups()
                backups.extend(webdav_backups)
            except Exception as e:
                logger.error(f"{self.plugin_name} 获取WebDAV备份文件列表失败: {e}")
        
        # 按时间排序（最新的在前）
        backups.sort(key=lambda x: datetime.strptime(x['time_str'], '%Y-%m-%d %H:%M:%S'), reverse=True)
        
        return backups

    def get_webdav_backups(self) -> List[Dict[str, Any]]:
        """获取WebDAV上的备份文件列表（使用新的WebDAV客户端）"""
        backups = []
        
        try:
            from ..storage.webdav import WebDAVClient
            
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
            
            # 获取文件列表（只获取Proxmox备份文件）
            files, error = client.list_files()
            
            if error:
                logger.error(f"{self.plugin_name} 获取WebDAV文件列表失败: {error}")
                client.close()
                return backups

            # 过滤并格式化备份文件
            backup_extensions = ('.tar.gz', '.tar.lzo', '.tar.zst', '.vma.gz', '.vma.lzo', '.vma.zst')
            for file_info in files:
                filename = file_info.get('filename', '')
                if not any(filename.lower().endswith(ext) for ext in backup_extensions):
                    continue

                # 格式化时间
                file_time = file_info.get('time')
                if file_time:
                    try:
                        time_str = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        time_str = "未知"
                else:
                    time_str = "未知"
                
                backups.append({
                    'filename': filename,
                    'path': file_info.get('href', ''),
                    'size_mb': file_info.get('size_mb', 0),
                    'time_str': time_str,
                    'source': 'WebDAV备份'
                })

            client.close()

        except Exception as e:
            logger.error(f"{self.plugin_name} 获取WebDAV备份文件列表时发生错误: {str(e)}")
        
        return backups

    def download_single_backup_file(self, ssh: paramiko.SSHClient, sftp: paramiko.SFTPClient, remote_file: str, backup_filename: str) -> Tuple[bool, Optional[str], Optional[str], Dict[str, Any]]:
        """
        下载单个备份文件
        :return: (是否成功, 错误消息, 备份文件名, 备份详情)
        """
        try:
            # 构建备份详情
            backup_details = {
                "local_backup": {
                    "enabled": self.plugin._enable_local_backup,
                    "success": False,
                    "path": self.plugin._backup_path,
                    "filename": backup_filename
                },
                "webdav_backup": {
                    "enabled": self.plugin._enable_webdav and bool(self.plugin._webdav_url),
                    "success": False,
                    "url": self.plugin._webdav_url,
                    "path": self.plugin._webdav_path,
                    "filename": backup_filename,
                    "error": None
                }
            }
            
            local_path = None
            
            # 如果启用了本地备份，先下载到本地
            if self.plugin._enable_local_backup:
                try:
                    # 确保备份目录存在
                    backup_dir = Path(self.plugin._backup_path)
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    local_path = str(backup_dir / backup_filename)
                    
                    # 下载文件
                    self.plugin._backup_activity = f"下载本地中: {backup_filename}"
                    logger.info(f"{self.plugin_name} 开始下载备份文件到本地: {remote_file} -> {local_path}")
                    sftp.get(remote_file, local_path)
                    
                    logger.info(f"{self.plugin_name} 本地备份成功: {backup_filename}")
                    backup_details["local_backup"]["success"] = True
                except Exception as e:
                    error_msg = f"本地下载失败: {str(e)}"
                    logger.error(f"{self.plugin_name} {error_msg}")
                    backup_details["local_backup"]["success"] = False
                    # 如果本地备份失败，但WebDAV备份启用，仍然尝试上传到WebDAV
                    if not (self.plugin._enable_webdav and self.plugin._webdav_url):
                        return False, error_msg, None, {}
                    # 如果没有本地路径，使用远程文件直接上传（需要临时下载）
                    if not local_path:
                        # 如果本地下载失败，尝试创建临时文件用于WebDAV上传
                        import tempfile
                        temp_dir = Path(tempfile.gettempdir()) / "proxmoxvebackup_temp"
                        temp_dir.mkdir(parents=True, exist_ok=True)
                        local_path = str(temp_dir / backup_filename)
                        try:
                            sftp.get(remote_file, local_path)
                        except Exception as temp_e:
                            return False, f"本地和临时下载都失败: {error_msg}, 临时下载错误: {str(temp_e)}", None, {}
            
            # 如果启用了WebDAV备份，上传到WebDAV
            if self.plugin._enable_webdav and self.plugin._webdav_url:
                # 如果没有本地路径（只启用WebDAV），需要先下载到临时位置
                if not local_path:
                    import tempfile
                    temp_dir = Path(tempfile.gettempdir()) / "proxmoxvebackup_temp"
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    local_path = str(temp_dir / backup_filename)
                    try:
                        self.plugin._backup_activity = f"下载临时文件: {backup_filename}"
                        logger.info(f"{self.plugin_name} 开始下载备份文件到临时位置: {remote_file} -> {local_path}")
                        sftp.get(remote_file, local_path)
                    except Exception as e:
                        error_msg = f"临时下载失败: {str(e)}"
                        logger.error(f"{self.plugin_name} {error_msg}")
                        return False, error_msg, None, {}
                
                try:
                    self.plugin._backup_activity = f"上传WebDAV中: {backup_filename}"
                    logger.info(f"{self.plugin_name} 开始上传到WebDAV: {backup_filename}")
                    webdav_success, webdav_error = self.upload_to_webdav(local_path, backup_filename)
                    
                    if webdav_success:
                        logger.info(f"{self.plugin_name} WebDAV备份成功: {backup_filename}")
                        self.plugin._backup_activity = "WebDAV上传完成"
                        backup_details["webdav_backup"]["success"] = True
                        backup_details["webdav_backup"]["error"] = None
                    else:
                        logger.error(f"{self.plugin_name} WebDAV备份失败: {backup_filename} - {webdav_error}")
                        self.plugin._backup_activity = f"WebDAV上传失败: {webdav_error[:50]}..."
                        backup_details["webdav_backup"]["success"] = False
                        backup_details["webdav_backup"]["error"] = webdav_error
                except Exception as e:
                    error_msg = f"WebDAV上传异常: {str(e)}"
                    logger.error(f"{self.plugin_name} {error_msg}")
                    self.plugin._backup_activity = f"WebDAV上传异常: {str(e)[:50]}..."
                    backup_details["webdav_backup"]["success"] = False
                    backup_details["webdav_backup"]["error"] = error_msg
                
                # 如果是临时文件且WebDAV成功，删除临时文件
                if local_path and str(local_path).startswith(str(Path(tempfile.gettempdir()))):
                    try:
                        os.remove(local_path)
                        logger.info(f"{self.plugin_name} 已删除临时文件: {local_path}")
                    except Exception as e:
                        logger.warning(f"{self.plugin_name} 删除临时文件失败: {e}")
            
            # 上传完成后，如果配置了自动删除，再删除PVE上的备份文件
            if self.plugin._auto_delete_after_download:
                try:
                    sftp.remove(remote_file)
                    logger.info(f"{self.plugin_name} 已删除远程备份文件: {remote_file}")
                except Exception as e:
                    logger.error(f"{self.plugin_name} 删除远程备份文件失败: {str(e)}")
            
            return True, None, backup_filename, backup_details
            
        except Exception as e:
            error_msg = f"下载备份文件 {backup_filename} 时发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg, None, {}

    def download_from_webdav(self, filename: str, local_path: str) -> Tuple[bool, Optional[str]]:
        """从WebDAV下载文件（使用新的WebDAV客户端）"""
        if not self.plugin._enable_webdav or not self.plugin._webdav_url:
            return False, "WebDAV未启用或URL未配置"
        
        try:
            from ..storage.webdav import WebDAVClient
            
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
            
            # 定义进度回调
            def progress_callback(downloaded: int, total: int, speed: float):
                progress = (downloaded / total) * 100 if total > 0 else 0
                self.plugin._restore_activity = f"下载WebDAV中: {progress:.1f}% 速度: {speed:.2f}MB/s"
                logger.info(f"{self.plugin_name} WebDAV下载进度: {progress:.1f}% 速度: {speed:.2f}MB/s")
            
            # 执行下载
            success, error = client.download(filename, local_path, progress_callback)
            client.close()
            
            return success, error
            
        except Exception as e:
            error_msg = f"WebDAV下载过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg

