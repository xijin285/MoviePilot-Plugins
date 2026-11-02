"""API处理模块"""
from typing import Any, Dict
from app.log import logger


class APIHandler:
    """API处理器类"""
    
    def __init__(self, plugin_instance):
        """初始化API处理器"""
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
    
    def backup(self, onlyonce: bool = False):
        """API备份接口"""
        try:
            self.plugin.run_backup_job()
            return {"success": True, "message": "备份任务已启动"}
        except Exception as e:
            return {"success": False, "message": f"启动备份任务失败: {str(e)}"}
    
    def restore_backup(self, filename: str, source: str = "本地备份"):
        """API恢复接口"""
        try:
            self.plugin.run_restore_job(filename, source)
            return {"success": True, "message": "恢复任务已启动"}
        except Exception as e:
            return {"success": False, "message": f"启动恢复任务失败: {str(e)}"}
    
    def sync_ip_groups(self, province: str = "", city: str = "", isp: str = "", 
                      group_prefix: str = "", address_pool: bool = False) -> Dict[str, Any]:
        """API接口：同步IP分组"""
        try:
            if not self.plugin._ikuai_url or not self.plugin._ikuai_username or not self.plugin._ikuai_password:
                return {"success": False, "message": "配置不完整：URL、用户名或密码未设置。"}
            
            # 创建IP分组管理器
            from ..ip_group.manager import IPGroupManager
            ip_manager = IPGroupManager(
                ikuai_url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password
            )
            
            # 执行同步
            success, message = ip_manager.sync_ip_groups_from_22tool(
                province=province,
                city=city,
                isp=isp,
                group_prefix=group_prefix,
                address_pool=address_pool
            )
            
            return {"success": success, "message": message}
            
        except Exception as e:
            error_msg = f"API同步IP分组异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}
    
    def get_ip_blocks_info(self, province: str = "", city: str = "", isp: str = "") -> Dict[str, Any]:
        """API接口：获取IP段信息"""
        try:
            # 创建IP分组管理器
            from ..ip_group.manager import IPGroupManager
            ip_manager = IPGroupManager(
                ikuai_url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password
            )
            
            # 获取IP段信息
            ip_blocks = ip_manager.get_ip_blocks_from_22tool(province, city, isp)
            
            return {
                "success": True,
                "data": ip_blocks,
                "count": len(ip_blocks)
            }
            
        except Exception as e:
            error_msg = f"获取IP段信息异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}
    
    def get_available_options(self) -> Dict[str, Any]:
        """API接口：获取可用的省份、城市、运营商选项"""
        try:
            # 创建IP分组管理器
            from ..ip_group.manager import IPGroupManager
            ip_manager = IPGroupManager(
                ikuai_url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password
            )
            
            provinces = ip_manager.get_available_provinces()
            isps = ip_manager.get_available_isps()
            
            return {
                "success": True,
                "provinces": provinces,
                "isps": isps
            }
            
        except Exception as e:
            error_msg = f"获取可用选项异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}
    
    def get_cities_by_province(self, province: str) -> Dict[str, Any]:
        """API接口：根据省份获取城市列表"""
        try:
            # 创建IP分组管理器
            from ..ip_group.manager import IPGroupManager
            ip_manager = IPGroupManager(
                ikuai_url=self.plugin._ikuai_url,
                username=self.plugin._ikuai_username,
                password=self.plugin._ikuai_password
            )
            
            cities = ip_manager.get_available_cities(province)
            
            return {
                "success": True,
                "cities": cities
            }
            
        except Exception as e:
            error_msg = f"获取城市列表异常: {str(e)}"
            logger.error(f"{self.plugin_name} {error_msg}")
            return {"success": False, "message": error_msg}
    
    def test_ip_group(self) -> Dict[str, Any]:
        """测试IP分组创建API"""
        try:
            if not self.plugin._enable_ip_group:
                return {"code": 1, "msg": "IP分组功能未启用"}
            
            if not self.plugin._ikuai_url or not self.plugin._ikuai_username or not self.plugin._ikuai_password:
                return {"code": 1, "msg": "爱快路由器配置不完整"}
            
            # 创建IP分组管理器
            from ..ip_group.manager import IPGroupManager
            ip_manager = IPGroupManager(self.plugin._ikuai_url, self.plugin._ikuai_username, self.plugin._ikuai_password)
            
            # 测试创建最简单的IP分组
            success, error = ip_manager.test_create_simple_ip_group()
            
            if success:
                return {"code": 0, "msg": "测试IP分组创建成功"}
            else:
                return {"code": 1, "msg": f"测试IP分组创建失败: {error}"}
                
        except Exception as e:
            logger.error(f"{self.plugin_name} 测试IP分组创建异常: {str(e)}")
            return {"code": 1, "msg": f"测试IP分组创建异常: {str(e)}"}

