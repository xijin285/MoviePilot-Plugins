"""
备份执行模块
负责执行备份任务的核心逻辑
"""
import os
import re
import time
import threading
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import paramiko
from app.log import logger
from ..pve.client import clean_pve_tmp_files


class BackupExecutor:
    """备份执行器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化备份执行器
        :param plugin_instance: ProxmoxVEBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def run_backup_job(self):
        """执行备份任务"""
        # 如果已有任务在运行,直接返回
        if not self.plugin._lock:
            self.plugin._lock = threading.Lock()
        if not self.plugin._global_task_lock:
            self.plugin._global_task_lock = threading.Lock()
            
        # 检查是否有恢复任务正在执行（恢复任务优先级更高）
        if self.plugin._restore_lock and hasattr(self.plugin._restore_lock, 'locked') and self.plugin._restore_lock.locked():
            logger.info(f"{self.plugin_name} 检测到恢复任务正在执行，备份任务跳过（恢复任务优先级更高）！")
            return
            
        # 尝试获取全局任务锁，如果获取不到说明有其他任务在运行
        if not self.plugin._global_task_lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 检测到其他任务正在执行，备份任务跳过！")
            return
            
        # 尝试获取备份锁，如果获取不到说明有备份任务在运行
        if not self.plugin._lock.acquire(blocking=False):
            logger.debug(f"{self.plugin_name} 已有备份任务正在执行，本次调度跳过！")
            self.plugin._global_task_lock.release()  # 释放全局锁
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

            if not self.plugin._pve_host or not self.plugin._ssh_username or (not self.plugin._ssh_password and not self.plugin._ssh_key_file):
                error_msg = "配置不完整：PVE主机地址、SSH用户名或SSH认证信息(密码/密钥)未设置。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._notification_handler.send_backup_notification(success=False, message=error_msg, backup_details={})
                history_entry["message"] = error_msg
                self.plugin._history_handler.save_backup_history_entry(history_entry)
                return

            if not self.plugin._backup_path:
                error_msg = "备份路径未配置且无法设置默认路径。"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._notification_handler.send_backup_notification(success=False, message=error_msg, backup_details={})
                history_entry["message"] = error_msg
                self.plugin._history_handler.save_backup_history_entry(history_entry)
                return

            try:
                Path(self.plugin._backup_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                error_msg = f"创建本地备份目录 {self.plugin._backup_path} 失败: {e}"
                logger.error(f"{self.plugin_name} {error_msg}")
                self.plugin._notification_handler.send_backup_notification(success=False, message=error_msg, backup_details={})
                history_entry["message"] = error_msg
                self.plugin._history_handler.save_backup_history_entry(history_entry)
                return
            
            success_final = False
            error_msg_final = "未知错误"
            downloaded_file_final = None
            backup_details_final = {}
            
            for i in range(self.plugin._retry_count + 1):
                logger.info(f"{self.plugin_name} 开始第 {i+1}/{self.plugin._retry_count +1} 次备份尝试...")
                current_try_success, current_try_error_msg, current_try_downloaded_file, current_try_backup_details = self.perform_backup_once()
                
                if current_try_success:
                    success_final = True
                    downloaded_file_final = current_try_downloaded_file
                    backup_details_final = current_try_backup_details
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
            
            # 只在所有尝试都失败时保存一条失败历史
            if not success_final:
                history_entry["success"] = False
                history_entry["filename"] = None
                history_entry["message"] = f"备份失败: {error_msg_final}"
                self.plugin._history_handler.save_backup_history_entry(history_entry)
            
            self.plugin._notification_handler.send_backup_notification(success=success_final, message="备份成功" if success_final else f"备份失败: {error_msg_final}", filename=downloaded_file_final, backup_details=backup_details_final)
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 任务执行主流程出错：{str(e)}")
            history_entry["message"] = f"任务执行主流程出错: {str(e)}"
            self.plugin._notification_handler.send_backup_notification(success=False, message=history_entry["message"], backup_details={})
            self.plugin._history_handler.save_backup_history_entry(history_entry)
        finally:
            self.plugin._running = False
            self.plugin._backup_activity = "空闲"
            # 不再在finally里保存合并历史
            if self.plugin._lock and hasattr(self.plugin._lock, 'locked') and self.plugin._lock.locked():
                try:
                    self.plugin._lock.release()
                except RuntimeError:
                    pass
            if self.plugin._global_task_lock and hasattr(self.plugin._global_task_lock, 'locked') and self.plugin._global_task_lock.locked():
                try:
                    self.plugin._global_task_lock.release()
                except RuntimeError:
                    pass
            logger.info(f"{self.plugin_name} 任务执行完成。")

    def perform_backup_once(self) -> Tuple[bool, Optional[str], Optional[str], Dict[str, Any]]:
        """
        执行一次备份操作 - 逐个备份并上传，避免PVE存储空间不足
        :return: (是否成功, 错误消息, 备份文件名, 备份详情)
        """
        if not self.plugin._pve_host:
            return False, "未配置PVE主机地址", None, {}

        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sftp = None
        
        try:
            # 尝试SSH连接
            try:
                if self.plugin._ssh_key_file:
                    # 使用密钥认证
                    private_key = paramiko.RSAKey.from_private_key_file(self.plugin._ssh_key_file)
                    ssh.connect(self.plugin._pve_host, port=self.plugin._ssh_port, username=self.plugin._ssh_username, pkey=private_key)
                else:
                    # 使用密码认证
                    ssh.connect(self.plugin._pve_host, port=self.plugin._ssh_port, username=self.plugin._ssh_username, password=self.plugin._ssh_password)
                logger.info(f"{self.plugin_name} SSH连接成功")
            except Exception as e:
                return False, f"SSH连接失败: {str(e)}", None, {}

            logger.info(f"{self.plugin_name} 开始创建备份...")
            
            # 检查PVE端是否有正在运行的备份任务（只检查进程名为vzdump的进程，不检查命令行参数）
            # 使用 pgrep 或 ps -C 只检查进程名，避免误判包含vzdump文件名的curl等进程
            check_running_cmd = "pgrep -x vzdump || ps -C vzdump --no-headers"
            stdin, stdout, stderr = ssh.exec_command(check_running_cmd)
            running_backups = stdout.read().decode().strip()
            
            if running_backups:
                logger.warning(f"{self.plugin_name} 检测到正在运行的vzdump备份进程")
                logger.info(f"{self.plugin_name} 正在运行的备份进程: {running_backups}")
                return False, "PVE端已有备份任务在运行，为避免冲突跳过本次备份", None, {}
            
            # 获取要备份的VMID列表
            if not self.plugin._backup_vmid or self.plugin._backup_vmid.strip() == "":
                # 如果没有指定容器ID，尝试获取所有可用的容器
                logger.info(f"{self.plugin_name} 未指定容器ID，尝试获取所有可用的容器...")
                
                # 获取QEMU虚拟机ID（直接获取所有行，不跳过标题，然后用awk过滤）
                list_cmd = "qm list 2>&1 | grep -E '^[[:space:]]*[0-9]+' | awk '{print $1}' | sort -n | tr '\n' ',' | sed 's/,$//'"
                stdin, stdout, stderr = ssh.exec_command(list_cmd)
                qemu_output = stdout.read().decode().strip()
                qemu_error = stderr.read().decode().strip()
                qemu_vmids = qemu_output if qemu_output else ""
                
                # 如果上面的命令没结果，尝试另一种方式
                if not qemu_vmids:
                    list_cmd = "qm list 2>&1 | tail -n +2 | grep -v '^$' | awk '{print $1}' | grep -E '^[0-9]+$' | sort -n | tr '\n' ',' | sed 's/,$//'"
                    stdin, stdout, stderr = ssh.exec_command(list_cmd)
                    qemu_output = stdout.read().decode().strip()
                    qemu_error = stderr.read().decode().strip()
                    qemu_vmids = qemu_output if qemu_output else ""
                
                # 获取所有LXC容器ID
                list_cmd = "pct list 2>&1 | grep -E '^[[:space:]]*[0-9]+' | awk '{print $1}' | sort -n | tr '\n' ',' | sed 's/,$//'"
                stdin, stdout, stderr = ssh.exec_command(list_cmd)
                lxc_output = stdout.read().decode().strip()
                lxc_error = stderr.read().decode().strip()
                lxc_vmids = lxc_output if lxc_output else ""
                
                # 如果上面的命令没结果，尝试另一种方式
                if not lxc_vmids:
                    list_cmd = "pct list 2>&1 | tail -n +2 | grep -v '^$' | awk '{print $1}' | grep -E '^[0-9]+$' | sort -n | tr '\n' ',' | sed 's/,$//'"
                    stdin, stdout, stderr = ssh.exec_command(list_cmd)
                    lxc_output = stdout.read().decode().strip()
                    lxc_error = stderr.read().decode().strip()
                    lxc_vmids = lxc_output if lxc_output else ""
                
                # 合并QEMU和LXC的ID列表
                available_vmids = []
                if qemu_vmids:
                    qemu_list = [vmid.strip() for vmid in qemu_vmids.split(',') if vmid.strip() and vmid.strip().isdigit()]
                    available_vmids.extend(qemu_list)
                if lxc_vmids:
                    lxc_list = [vmid.strip() for vmid in lxc_vmids.split(',') if vmid.strip() and vmid.strip().isdigit()]
                    available_vmids.extend(lxc_list)
                
                if not available_vmids:
                    return False, "未找到任何可用的虚拟机或容器，请检查PVE主机状态或手动指定容器ID", None, {}
                
                # 去重并排序
                available_vmids = sorted(set(available_vmids), key=lambda x: int(x) if x.isdigit() else 0)
                self.plugin._backup_vmid = ','.join(available_vmids)
                logger.info(f"{self.plugin_name} 自动获取到容器ID: {self.plugin._backup_vmid}")
            
            # 将逗号分隔的VMID列表转换为列表
            if isinstance(self.plugin._backup_vmid, str):
                vmid_list = [vmid.strip() for vmid in self.plugin._backup_vmid.split(',') if vmid.strip()]
            else:
                vmid_list = [str(self.plugin._backup_vmid)]
            
            logger.info(f"{self.plugin_name} 准备逐个备份 {len(vmid_list)} 个容器: {', '.join(vmid_list)}")
            
            # 打开SFTP连接
            sftp = ssh.open_sftp()
            
            # 逐个备份每个容器
            all_downloads_successful = True
            downloaded_files_info = []
            filenames = []
            vmids = []

            for vmid in vmid_list:
                try:
                    logger.info(f"{self.plugin_name} 开始备份容器 {vmid}...")
                    
                    # 构建单个容器的vzdump命令
                    backup_cmd = f"vzdump {vmid} "
                    backup_cmd += f"--compress {self.plugin._compress_mode} "
                    backup_cmd += f"--mode {self.plugin._backup_mode} "
                    backup_cmd += f"--storage {self.plugin._storage_name} "
                    
                    # 执行备份命令
                    logger.info(f"{self.plugin_name} 执行命令: {backup_cmd}")
                    stdin, stdout, stderr = ssh.exec_command(backup_cmd)
                    
                    created_backup_file = None
                    # 实时输出vzdump日志
                    while True:
                        line = stdout.readline()
                        if not line:
                            break
                        line = line.strip()
                        # 从vzdump日志中解析出备份文件名
                        match = re.search(r"creating vzdump archive '(.+)'", line)
                        if match:
                            filepath = match.group(1)
                            logger.info(f"{self.plugin_name} 从日志中检测到备份文件: {filepath}")
                            created_backup_file = filepath
                    
                    # 等待命令完成
                    exit_status = stdout.channel.recv_exit_status()
                    if exit_status != 0:
                        error_output = stderr.read().decode().strip()
                        logger.error(f"{self.plugin_name} 容器 {vmid} 备份失败: {error_output}")
                        all_downloads_successful = False
                        continue
                    
                    if not created_backup_file:
                        logger.error(f"{self.plugin_name} 未能从日志中解析出容器 {vmid} 的备份文件名")
                        all_downloads_successful = False
                        continue
                    
                    # 下载备份文件到本地，然后上传到WebDAV
                    success, error_msg, filename, details = self.plugin._backup_manager.download_single_backup_file(
                        ssh, sftp, created_backup_file, os.path.basename(created_backup_file)
                    )
                    
                    if success:
                        downloaded_files_info.append({
                            "filename": filename,
                            "details": details
                        })
                        filenames.append(filename)
                        vmids.append(vmid)
                        logger.info(f"{self.plugin_name} 容器 {vmid} 备份成功: {filename}")
                    else:
                        logger.error(f"{self.plugin_name} 容器 {vmid} 处理失败: {error_msg}")
                        all_downloads_successful = False
                        
                except Exception as e:
                    logger.error(f"{self.plugin_name} 容器 {vmid} 备份过程中发生错误: {str(e)}")
                    all_downloads_successful = False

            # --- 所有容器处理完成后，统一执行清理 ---
            if self.plugin._enable_local_backup:
                self.plugin._backup_manager.cleanup_old_backups()
            if self.plugin._enable_webdav and self.plugin._webdav_url:
                logger.info(f"{self.plugin_name} 开始清理WebDAV旧备份...")
                self.plugin._backup_manager.cleanup_webdav_backups()

            # 合并历史记录逻辑
            if downloaded_files_info:
                # 成功时保存一条合并历史
                history_entry = {
                    "timestamp": time.time(),
                    "success": True,
                    "filename": ", ".join(filenames),
                    "message": f"备份成功 [VMID: {', '.join(vmids)}]"
                }
                self.plugin._history_handler.save_backup_history_entry(history_entry)
                # 返回最后一个成功下载的文件信息
                last_file = downloaded_files_info[-1]
                return True, None, last_file["filename"], {
                    "downloaded_files": downloaded_files_info,
                    "last_file_details": last_file["details"]
                }
            else:
                # 失败时只保存一条失败历史
                history_entry = {
                    "timestamp": time.time(),
                    "success": False,
                    "filename": None,
                    "message": "所有容器备份失败，详情请查看日志"
                }
                self.plugin._history_handler.save_backup_history_entry(history_entry)
                return False, "所有容器备份失败，详情请查看日志", None, {}

        except Exception as e:
            error_msg = f"备份过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg, None, {}
            
        finally:
            # 确保关闭SFTP和SSH连接
            if sftp:
                try:
                    sftp.close()
                except:
                    pass
            if ssh:
                try:
                    ssh.close()
                except:
                    pass
            try:
                # 优先读取 self.auto_cleanup_tmp，没有就 get_config()
                if hasattr(self.plugin, 'auto_cleanup_tmp'):
                    auto_cleanup = getattr(self.plugin, 'auto_cleanup_tmp', False)
                else:
                    auto_cleanup = self.plugin.get_config().get('auto_cleanup_tmp', False)
                if auto_cleanup:
                    count, error = clean_pve_tmp_files(
                        self.plugin._pve_host,
                        self.plugin._ssh_port,
                        self.plugin._ssh_username,
                        self.plugin._ssh_password,
                        self.plugin._ssh_key_file
                    )
                    if error:
                        logger.warning(f"{self.plugin_name} 自动清理临时空间失败: {error}")
                    else:
                        logger.info(f"{self.plugin_name} 自动清理临时空间完成，已清理 {count} 个 .tmp 文件")
                else:
                    logger.info(f"{self.plugin_name} 未启用自动清理临时空间，跳过清理。")
            except Exception as e:
                logger.warning(f"{self.plugin_name} 自动清理临时空间异常: {e}")

