"""
OpenWrt客户端模块
负责通过HTTP API连接和操作OpenWrt路由器（替代SSH）
"""
from datetime import datetime
from typing import Tuple, Optional
from app.log import logger

from .http_client import OpenWrtHTTPClient


class OpenWrtClient:
    """OpenWrt HTTP客户端（替代SSH）"""
    
    def __init__(self, plugin_instance):
        """
        初始化OpenWrt客户端
        :param plugin_instance: OpenWrtBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        self.http_client = OpenWrtHTTPClient(plugin_instance)
    
    def connect(self) -> Tuple[Optional[OpenWrtHTTPClient], Optional[str]]:
        """
        建立HTTP连接到OpenWrt路由器
        返回: (HTTP客户端实例, 错误信息)
        """
        try:
            # 检查必要的配置项
            if not self.plugin._openwrt_host:
                return None, "未配置OpenWrt地址"
            
            if not self.plugin._openwrt_username:
                return None, "未配置OpenWrt用户名"
            
            if not self.plugin._openwrt_password:
                return None, "未配置OpenWrt密码"
            
            # 执行HTTP登录
            success, error = self.http_client.login()
            if not success:
                return None, error
            
            return self.http_client, None
            
        except Exception as e:
            logger.error(f"{self.plugin_name} HTTP连接异常: {e}")
            return None, f"连接OpenWrt失败: {str(e)}"
    
    def create_backup(self, http_client: OpenWrtHTTPClient) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """
        通过cgi-backup接口直接下载备份文件到本地
        返回: (成功, 错误信息, 备份文件名, 本地临时文件路径)
        """
        try:
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"backup_{timestamp}.tar.gz"
            
            # 直接通过cgi-backup接口下载备份
            logger.info(f"{self.plugin_name} 开始通过官方接口下载备份...")
            success, error, local_temp_path = http_client.download_backup_direct(backup_filename)
            
            if success and local_temp_path:
                return True, None, backup_filename, local_temp_path
            else:
                return False, f"无法下载备份: {error or '下载失败'}", None, None
            
        except Exception as e:
            return False, f"创建备份过程中发生错误: {str(e)}", None, None
    
