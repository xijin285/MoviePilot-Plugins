# 备份处理模块 - backup_handler.py
import requests
import hashlib
import json
import os
from datetime import datetime

class IkuaiBackupHandler:
    def __init__(self, config):
        self.ikuai_url = config.get('ikuai_url')
        self.username = config.get('username')
        self.password = config.get('password')
        self.session = requests.Session()
        self.cookie = None
        
    def login(self):
        """登录爱快路由并获取会话Cookie"""
        try:
            # 加密密码（需与爱快接口要求一致）
            hashed_password = hashlib.md5(self.password.encode()).hexdigest()
            payload = {"username": self.username, "password": hashed_password}
            response = self.session.post(f"{self.ikuai_url}/api/login", data=payload)
            
            if response.status_code == 200:
                # 从响应头获取 sess_key 并构建 Cookie
                cookie_header = response.headers.get("Set-Cookie")
                if cookie_header:
                    sess_key = cookie_header.split(";")[0]
                    self.cookie = {sess_key.split("=")[0]: sess_key.split("=")[1]}
                    return True
            raise Exception("登录失败: 认证错误")
            
        except Exception as e:
            print(f"登录异常: {str(e)}")
            return False

    def create_backup(self):
        """创建备份文件"""
        if not self.cookie:
            if not self.login():
                return False, "未登录或登录失败"
                
        backup_url = f"{self.ikuai_url}/api/backup/create"
        response = self.session.post(backup_url, cookies=self.cookie)
        
        try:
            result = response.json()
            if "success" in str(result).lower():
                return True, "备份创建成功"
            else:
                return False, f"备份失败: {result.get('message', '未知错误')}"
        except json.JSONDecodeError:
            return False, f"备份失败: 无效的响应格式 {response.text}"

    def get_backup_list(self):
        """获取备份文件列表"""
        if not self.cookie:
            if not self.login():
                return []
                
        list_url = f"{self.ikuai_url}/api/backup/list"
        response = self.session.get(list_url, cookies=self.cookie)
        
        try:
            result = response.json()
            if "data" in result and isinstance(result["data"], list):
                # 假设返回格式包含文件名和时间戳
                return sorted(result["data"], key=lambda x: x.get("time", 0), reverse=True)
            return []
        except Exception:
            return []

    def download_backup(self, file_name, save_path="./backups"):
        """下载指定备份文件"""
        if not self.cookie:
            if not self.login():
                return False, "下载失败: 未登录"
                
        os.makedirs(save_path, exist_ok=True)
        download_url = f"{self.ikuai_url}/api/backup/download?filename={file_name}"
        
        try:
            response = self.session.get(download_url, cookies=self.cookie, stream=True)
            if response.status_code == 200:
                save_file = os.path.join(save_path, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}")
                with open(save_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        f.write(chunk)
                return True, save_file
            return False, f"下载失败: HTTP状态码 {response.status_code}"
        except Exception as e:
            return False, f"下载异常: {str(e)}"
