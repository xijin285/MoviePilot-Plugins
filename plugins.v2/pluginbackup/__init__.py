import os
import time
import hashlib
import requests
from typing import Dict, Optional, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

class IkuaiBackupPlugin:
    def __init__(self):
        self.enabled = False
        self.cron_expr = "0 0 * * *"  # 默认每天0点备份
        self.keep_backup_count = 30
        self.backup_dir = "/mnt/user/backups/ikuai/tmp"
        self.final_dir = "/mnt/user/backups/ikuai/final"
        self.ikuai_url = "http://10.0.0.1"
        self.username = "admin"
        self.password = "your_password"
        self.cookie = None
        self.scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    def init_plugin(self, config: Dict[str, Any]):
        """初始化插件配置"""
        self.enabled = config.get("enabled", False)
        self.cron_expr = config.get("cron", "0 0 * * *")
        self.keep_backup_count = config.get("keep_backup", 30)
        self.backup_dir = config.get("backup_dir", "/mnt/user/backups/ikuai/tmp")
        self.final_dir = config.get("final_dir", "/mnt/user/backups/ikuai/final")
        self.ikuai_url = config.get("ikuai_url", "http://10.0.0.1")
        self.username = config.get("username", "admin")
        self.password = config.get("password", "password")
        
        # 确保目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.final_dir, exist_ok=True)
        
        # 启动定时任务
        if self.enabled:
            self.start_scheduler()

    def start_scheduler(self):
        """启动定时备份任务"""
        self.scheduler.remove_all_jobs()
        trigger = CronTrigger.from_crontab(self.cron_expr)
        self.scheduler.add_job(
            self.run_backup,
            trigger=trigger,
            name="Ikuai Auto Backup"
        )
        self.scheduler.start()

    def run_backup(self):
        """执行完整备份流程"""
        if not self.login():
            print("登录失败，无法继续")
            return
        
        if not self.create_backup():
            print("创建备份失败")
            return
        
        time.sleep(5)  # 等待备份生成
        latest_file = self.get_latest_backup_file()
        
        if latest_file:
            if self.download_backup(latest_file):
                self.clean_old_backups()
                print("备份完成")
            else:
                print("下载备份失败")
        else:
            print("未找到最新备份文件")

    def login(self) -> bool:
        """登录爱快路由获取Cookie"""
        url = f"{self.ikuai_url}/Action/login"
        md5_pwd = hashlib.md5(self.password.encode()).hexdigest()
        payload = {"username": self.username, "passwd": md5_pwd}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            cookie_header = response.headers.get("Set-Cookie", "")
            
            # 提取sess_key
            sess_key = next((c for c in cookie_header.split(";") if "sess_key=" in c), None)
            if sess_key:
                self.cookie = f"username={self.username}; {sess_key.strip()}; login=1"
                return True
            return False
        except Exception as e:
            print(f"登录失败: {str(e)}")
            return False

    def create_backup(self) -> bool:
        """调用接口创建备份"""
        if not self.cookie:
            return False
        
        url = f"{self.ikuai_url}/Action/call"
        payload = {
            "func_name": "backup",
            "action": "create",
            "param": {}
        }
        headers = {"Cookie": self.cookie}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            return "success" in response.text.lower()
        except Exception as e:
            print(f"创建备份失败: {str(e)}")
            return False

    def get_latest_backup_file(self) -> Optional[str]:
        """获取最新备份文件名"""
        if not self.cookie:
            return None
        
        url = f"{self.ikuai_url}/Action/call"
        payload = {
            "func_name": "backup",
            "action": "list",
            "param": {}
        }
        headers = {"Cookie": self.cookie}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            data = response.json()
            backups = data.get("data", [])
            
            if backups:
                # 按时间戳降序排序，取第一个
                return max(backups, key=lambda x: x["time"])["filename"]
            return None
        except Exception as e:
            print(f"获取备份列表失败: {str(e)}")
            return None

    def download_backup(self, filename: str) -> bool:
        """下载备份文件到临时目录"""
        url = f"{self.ikuai_url}/download/{filename}"
        local_path = os.path.join(self.backup_dir, filename)
        
        try:
            headers = {"Cookie": self.cookie}
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 移动到最终目录
            final_path = os.path.join(self.final_dir, filename)
            shutil.move(local_path, final_path)
            return True
        except Exception as e:
            print(f"下载失败: {str(e)}")
            return False

    def clean_old_backups(self):
        """清理旧备份文件"""
        files = sorted(
            [f for f in os.listdir(self.final_dir) if f.startswith("backup_")],
            key=lambda x: os.path.getmtime(os.path.join(self.final_dir, x)),
            reverse=False
        )
        
        to_delete = files[:-self.keep_backup_count] if len(files) > self.keep_backup_count else []
        for f in to_delete:
            os.remove(os.path.join(self.final_dir, f))
            print(f"删除旧备份: {f}")

# 插件实例化
plugin = IkuaiBackupPlugin()

# 框架调用入口（示例）
def initialize_plugin(config: Dict[str, Any]):
    plugin.init_plugin(config)

def trigger_backup():
    plugin.run_backup()
