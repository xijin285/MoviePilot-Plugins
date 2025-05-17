import json
import os
import time
import hashlib
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List

from plugins.common import (
    PluginBase,
    Retry,
    logger,
    scheduler,
    run_in_thread,
    download_file
)
from plugins.autobackup.config import Config

class AutoBackup(PluginBase):
    def __init__(self):
        super().__init__()
        self.config = {}
        self.plugin_path = None
        self.backup_path = None
        self.final_dest = None
        self.ikuai_base_url = None
        self.ikuai_username = None
        self.ikuai_password = None
        self.keep_backup_num = 30
        self.cookie = None
        self._scheduler = None

    def init_config(self, config: Dict[str, Any]):
        self.config = config
        self.plugin_path = os.path.dirname(os.path.abspath(__file__))
        self.backup_path = config.get('backup_dir', '/mnt/user/downloads/backup')
        self.final_dest = config.get('final_dest_dir', '/mnt/user/downloads/cloud/aliyun/backup/ikuai_backup')
        self.ikuai_base_url = config.get('ikuai_base_url', 'http://10.0.0.1')
        self.ikuai_username = config.get('ikuai_username', 'admin')
        self.ikuai_password = config.get('ikuai_password', 'password')
        self.keep_backup_num = config.get('keep_backup_num', 30)
        
        # 确保目录存在
        os.makedirs(self.backup_path, exist_ok=True)
        os.makedirs(self.final_dest, exist_ok=True)
        
        # 设置定时任务
        self._scheduler = scheduler.new_job(
            func=self._auto_backup_task,
            trigger='interval',
            hours=24,
            name="爱快路由自动备份"
        )

    def get_state(self) -> bool:
        return True if self._scheduler else False

    @staticmethod
    def get_command_hooks() -> Dict[str, Any]:
        return {
            "ikuai_backup": "手动触发爱快路由备份"
        }

    def execute(self, command: str, *args, **kwargs) -> Any:
        if command == "ikuai_backup":
            return self.manual_backup()
        return None

    def manual_backup(self):
        """手动触发备份"""
        return self._backup_ikuai_router()

    @run_in_thread
    def _auto_backup_task(self):
        """自动备份定时任务"""
        logger.info("开始执行爱快路由自动备份任务...")
        self._backup_ikuai_router()

    def _backup_ikuai_router(self) -> bool:
        """执行爱快路由备份流程"""
        try:
            # 登录获取Cookie
            if not self._login():
                logger.error("爱快路由登录失败")
                return False
                
            # 创建备份
            if not self._create_backup():
                logger.error("创建爱快路由备份失败")
                return False
                
            # 等待备份文件生成
            time.sleep(5)
            
            # 获取备份文件列表并下载最新备份
            backup_file = self._get_latest_backup_file()
            if not backup_file:
                logger.error("获取爱快路由备份文件列表失败")
                return False
                
            if not self._download_backup(backup_file):
                logger.error("下载爱快路由备份文件失败")
                return False
                
            # 清理旧备份
            self._cleanup_old_backups()
            
            logger.info("爱快路由备份完成")
            return True
        except Exception as e:
            logger.error(f"爱快路由备份过程中发生错误: {str(e)}")
            return False

    @Retry(tries=3, delay=2)
    def _login(self) -> bool:
        """登录爱快路由并获取Cookie"""
        login_url = f"{self.ikuai_base_url}/Action/login"
        md5_hash = hashlib.md5(self.ikuai_password.encode('utf-8')).hexdigest()
        
        login_data = {
            "username": self.ikuai_username,
            "passwd": md5_hash
        }
        
        logger.info(f"尝试登录爱快路由: {self.ikuai_base_url}")
        
        try:
            # 发送登录请求
            response = self.post(login_url, json=login_data, allow_redirects=False)
            
            # 检查响应头中的Set-Cookie
            set_cookie = response.headers.get('Set-Cookie', '')
            if not set_cookie:
                logger.error("登录响应中未找到Set-Cookie头")
                return False
                
            # 提取sess_key
            for cookie_part in set_cookie.split(';'):
                if 'sess_key=' in cookie_part:
                    sess_key = cookie_part.strip()
                    self.cookie = f"username={self.ikuai_username}; {sess_key}; login=1"
                    logger.info(f"成功获取会话Cookie: {self.cookie[:30]}...")
                    return True
                    
            logger.error("未能从Set-Cookie中提取sess_key")
            return False
        except Exception as e:
            logger.error(f"登录请求失败: {str(e)}")
            return False

    @Retry(tries=3, delay=2)
    def _create_backup(self) -> bool:
        """创建爱快路由备份"""
        if not self.cookie:
            logger.error("没有有效的会话Cookie，无法创建备份")
            return False
            
        create_backup_url = f"{self.ikuai_base_url}/Action/call"
        backup_data = {
            "func_name": "backup",
            "action": "create",
            "param": {}
        }
        
        logger.info("尝试创建爱快路由备份...")
        
        try:
            response = self.post(
                create_backup_url,
                json=backup_data,
                headers={"Cookie": self.cookie}
            )
            
            if "success" in response.text:
                logger.info("成功创建爱快路由备份")
                return True
            else:
                logger.error(f"创建备份失败，响应: {response.text[:100]}...")
                return False
        except Exception as e:
            logger.error(f"创建备份请求失败: {str(e)}")
            return False

    @Retry(tries=3, delay=2)
    def _get_latest_backup_file(self) -> Optional[str]:
        """获取最新的备份文件名"""
        if not self.cookie:
            logger.error("没有有效的会话Cookie，无法获取备份文件列表")
            return None
            
        list_backup_url = f"{self.ikuai_base_url}/Action/call"
        list_data = {
            "func_name": "backup",
            "action": "list",
            "param": {}
        }
        
        logger.info("尝试获取爱快路由备份文件列表...")
        
        try:
            response = self.post(
                list_backup_url,
                json=list_data,
                headers={"Cookie": self.cookie}
            )
            
            try:
                data = response.json()
                if not isinstance(data, dict) or 'data' not in data:
                    logger.error(f"解析备份文件列表失败，响应格式不正确: {response.text[:100]}...")
                    return None
                    
                backup_files = data.get('data', [])
                if not backup_files:
                    logger.error("没有找到爱快路由备份文件")
                    return None
                    
                # 按时间排序，获取最新的备份文件
                backup_files.sort(key=lambda x: x.get('time', 0), reverse=True)
                latest_file = backup_files[0].get('filename')
                logger.info(f"找到最新备份文件: {latest_file}")
                return latest_file
            except json.JSONDecodeError:
                logger.error(f"解析备份文件列表失败，非JSON响应: {response.text[:100]}...")
                return None
        except Exception as e:
            logger.error(f"获取备份文件列表请求失败: {str(e)}")
            return None

    @Retry(tries=3, delay=2)
    def _download_backup(self, filename: str) -> bool:
        """下载备份文件"""
        if not self.cookie or not filename:
            logger.error("缺少必要参数，无法下载备份文件")
            return False
            
        download_url = f"{self.ikuai_base_url}/Action/download?filename={filename}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_filename = f"ikuai_backup_{timestamp}.bin"
        local_path = os.path.join(self.backup_path, local_filename)
        final_path = os.path.join(self.final_dest, local_filename)
        
        logger.info(f"开始下载爱快路由备份文件: {filename}")
        
        try:
            # 下载文件
            response = self.get(
                download_url,
                headers={"Cookie": self.cookie},
                stream=True
            )
            
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                # 移动到最终目标位置
                shutil.move(local_path, final_path)
                logger.info(f"备份文件已保存到: {final_path}")
                return True
            else:
                logger.error(f"下载备份文件失败，状态码: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"下载备份文件过程中发生错误: {str(e)}")
            return False

    def _cleanup_old_backups(self):
        """清理旧的备份文件"""
        try:
            if not os.path.exists(self.final_dest):
                return
                
            # 获取备份目录中的所有文件并按修改时间排序
            backup_files = [f for f in os.listdir(self.final_dest) 
                           if os.path.isfile(os.path.join(self.final_dest, f)) 
                           and f.startswith("ikuai_backup_")]
                           
            if not backup_files:
                return
                
            backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.final_dest, x)))
            
            # 计算需要删除的文件数量
            files_to_delete = len(backup_files) - self.keep_backup_num
            if files_to_delete <= 0:
                return
                
            # 删除旧文件
            for i in range(files_to_delete):
                file_to_delete = os.path.join(self.final_dest, backup_files[i])
                os.remove(file_to_delete)
                logger.info(f"删除旧备份文件: {file_to_delete}")
        except Exception as e:
            logger.error(f"清理旧备份文件时发生错误: {str(e)}")

instance = AutoBackup()

def init_config(config: Dict[str, Any]):
    instance.init_config(config)

def get_state() -> bool:
    return instance.get_state()

def get_command_hooks() -> Dict[str, Any]:
    return instance.get_command_hooks()

def execute(command: str, *args, **kwargs) -> Any:
    return instance.execute(command, *args, **kwargs)    
