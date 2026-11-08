"""
恢复管理模块
负责处理备份文件的恢复操作
"""
import os
import re
import time
from pathlib import Path
from typing import Tuple, Optional
import paramiko
from app.log import logger
from ..pve.client import clean_pve_tmp_files


class RestoreManager:
    """恢复管理器类"""
    
    def __init__(self, plugin_instance):
        """
        初始化恢复管理器
        :param plugin_instance: ProxmoxVEBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def perform_restore_once(self, filename: str, source: str, restore_vmid: str = "", restore_force: bool = False, restore_skip_existing: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        执行一次恢复操作
        :return: (是否成功, 错误消息, 目标VMID)
        """
        if not self.plugin._pve_host:
            return False, "未配置PVE主机地址", None

        # 创建SSH客户端
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sftp = None
        
        try:
            # 尝试SSH连接
            try:
                if self.plugin._ssh_key_file:
                    private_key = paramiko.RSAKey.from_private_key_file(self.plugin._ssh_key_file)
                    ssh.connect(self.plugin._pve_host, port=self.plugin._ssh_port, username=self.plugin._ssh_username, pkey=private_key)
                else:
                    ssh.connect(self.plugin._pve_host, port=self.plugin._ssh_port, username=self.plugin._ssh_username, password=self.plugin._ssh_password)
                #logger.info(f"{self.plugin_name} SSH连接成功")
            except Exception as e:
                return False, f"SSH连接失败: {str(e)}", None

            # 1. 获取备份文件
            backup_file_path = None
            if source == "本地备份":
                backup_file_path = os.path.join(self.plugin._backup_path, filename)
                if not os.path.exists(backup_file_path):
                    return False, f"本地备份文件不存在: {backup_file_path}", None
            elif source == "WebDAV备份":
                # 从WebDAV下载备份文件到临时目录
                temp_dir = Path(self.plugin.get_data_path()) / "temp"
                temp_dir.mkdir(parents=True, exist_ok=True)
                backup_file_path = str(temp_dir / filename)
                
                self.plugin._restore_activity = f"下载WebDAV中: {filename}"
                download_success, download_error = self.plugin._backup_manager.download_from_webdav(filename, backup_file_path)
                if not download_success:
                    self.plugin._restore_activity = "空闲"
                    return False, f"从WebDAV下载备份文件失败: {download_error}", None
            else:
                return False, f"不支持的备份来源: {source}", None

            # 2. 上传备份文件到PVE
            sftp = ssh.open_sftp()
            remote_backup_path = f"/tmp/{filename}"
            
            self.plugin._restore_activity = f"上传PVE中: {filename}"
            logger.info(f"{self.plugin_name} 开始上传备份文件到PVE...")
            logger.info(f"{self.plugin_name} 本地路径: {backup_file_path}")
            logger.info(f"{self.plugin_name} 远程路径: {remote_backup_path}")
            
            # 获取文件大小
            local_stat = os.stat(backup_file_path)
            total_size = local_stat.st_size
            
            # 使用回调函数显示进度
            last_progress = -1  # 记录上次显示的进度
            def progress_callback(transferred: int, total: int):
                nonlocal last_progress
                if total > 0:
                    progress = (transferred / total) * 100
                    # 每20%显示一次进度
                    current_progress = int(progress / 20) * 20
                    if current_progress > last_progress or progress > 99.9:
                        self.plugin._restore_activity = f"上传PVE中: {progress:.1f}%"
                        logger.info(f"{self.plugin_name} 上传进度: {progress:.1f}%")
                        last_progress = current_progress
            
            # 上传文件
            sftp.put(backup_file_path, remote_backup_path, callback=progress_callback)
            logger.info(f"{self.plugin_name} 备份文件上传完成")

            # 3. 检查备份文件中的VMID
            original_vmid = self.extract_vmid_from_backup(filename)
            target_vmid = str(restore_vmid) if restore_vmid else original_vmid
            
            if not target_vmid:
                return False, "无法从备份文件名中提取VMID，请手动指定目标VMID", None

            # 4. 检查目标VM是否已存在
            vm_exists = self.check_vm_exists(ssh, target_vmid)
            if vm_exists:
                if restore_skip_existing:
                    return False, f"目标VM {target_vmid} 已存在，跳过恢复", target_vmid
                elif not restore_force:
                    return False, f"目标VM {target_vmid} 已存在，请启用强制恢复或跳过已存在选项", target_vmid
                else:
                    # 强制恢复：删除现有VM
                    logger.info(f"{self.plugin_name} 目标VM {target_vmid} 已存在，执行强制恢复")
                    is_lxc = 'lxc' in filename.lower()
                    delete_success, delete_error = self.delete_vm(ssh, target_vmid, is_lxc)
                    if not delete_success:
                        return False, f"删除现有VM失败: {delete_error}", target_vmid

            # 5. 执行恢复命令
            is_lxc = 'lxc' in filename.lower()
            if is_lxc:
                restore_cmd = f"pct restore {target_vmid} {remote_backup_path}"
            else:
                restore_cmd = f"qmrestore {remote_backup_path} {target_vmid}"

            if self.plugin._restore_storage:
                restore_cmd += f" --storage {self.plugin._restore_storage}"
            
            self.plugin._restore_activity = "等待PVE恢复中..."
            logger.info(f"{self.plugin_name} 执行恢复命令: {restore_cmd}")
            stdin, stdout, stderr = ssh.exec_command(restore_cmd)
    
            # 实时输出恢复日志
            while True:
                line = stdout.readline()
                if not line:
                    break
                logger.info(f"{self.plugin_name} 恢复输出: {line.strip()}")
            
            # 等待命令完成
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error_output = stderr.read().decode().strip()
                return False, f"恢复失败: {error_output}", target_vmid

            logger.info(f"{self.plugin_name} 恢复成功完成，目标VMID: {target_vmid}")
            
            # 6. 清理临时文件
            try:
                sftp.remove(remote_backup_path)
                logger.info(f"{self.plugin_name} 已删除远程临时文件: {remote_backup_path}")
            except Exception as e:
                logger.warning(f"{self.plugin_name} 删除远程临时文件失败: {str(e)}")
            
            # 如果是WebDAV备份，删除本地临时文件
            if source == "WebDAV备份":
                try:
                    os.remove(backup_file_path)
                    logger.info(f"{self.plugin_name} 已删除本地临时文件: {backup_file_path}")
                except Exception as e:
                    logger.warning(f"{self.plugin_name} 删除本地临时文件失败: {str(e)}")
            
            return True, None, target_vmid

        except Exception as e:
            error_msg = f"恢复过程中发生错误: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return False, error_msg, None
            
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
            # 自动清理PVE临时空间（受开关控制）
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

    def extract_vmid_from_backup(self, filename: str) -> Optional[str]:
        """从备份文件名中提取VMID"""
        try:
            # 备份文件名格式通常是: vzdump-{type}-{VMID}-{timestamp}.{format}.{compression}
            # 支持格式: tar.gz, tar.lzo, tar.zst, vma.gz, vma.lzo, vma.zst
            match = re.search(r'vzdump-(?:qemu|lxc)-(\d+)-', filename)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} 从备份文件名提取VMID失败: {e}")
            return None

    def check_vm_exists(self, ssh: paramiko.SSHClient, vmid: str) -> bool:
        """检查VM或CT是否存在"""
        try:
            # 检查QEMU VM
            check_qm_cmd = f"qm list | grep -q '^{vmid}\\s'"
            stdin, stdout, stderr = ssh.exec_command(check_qm_cmd)
            if stdout.channel.recv_exit_status() == 0:
                return True
            
            # 检查LXC容器
            check_pct_cmd = f"pct list | grep -q '^{vmid}\\s'"
            stdin, stdout, stderr = ssh.exec_command(check_pct_cmd)
            if stdout.channel.recv_exit_status() == 0:
                return True
                
            return False
        except Exception as e:
            logger.error(f"{self.plugin_name} 检查VM/CT存在性失败: {e}")
            return False

    def delete_vm(self, ssh: paramiko.SSHClient, vmid: str, is_lxc: bool) -> Tuple[bool, Optional[str]]:
        """删除VM或CT"""
        try:
            cmd_prefix = "pct" if is_lxc else "qm"
            # 先停止VM/CT
            stop_cmd = f"{cmd_prefix} stop {vmid}"
            logger.info(f"{self.plugin_name} 尝试停止VM/CT: {stop_cmd}")
            stdin, stdout, stderr = ssh.exec_command(stop_cmd)
            stdout.channel.recv_exit_status()
            
            # 等待VM/CT完全停止
            time.sleep(5)
            
            # 删除VM/CT
            delete_cmd = f"{cmd_prefix} destroy {vmid}"
            logger.info(f"{self.plugin_name} 尝试删除VM/CT: {delete_cmd}")
            stdin, stdout, stderr = ssh.exec_command(delete_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode().strip()
                if "does not exist" in error_output:
                    logger.warning(f"{self.plugin_name} 删除VM/CT {vmid} 时未找到，可能已被删除。")
                    return True, None
                return False, error_output
            
            logger.info(f"{self.plugin_name} 成功删除VM/CT {vmid}")
            return True, None
        except Exception as e:
            return False, str(e)

