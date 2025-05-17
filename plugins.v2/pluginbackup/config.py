from typing import Dict, Any

class Config:
    """插件配置类"""
    
    @staticmethod
    def get_config_schema() -> Dict[str, Any]:
        """获取配置表单模式"""
        return {
            "type": "object",
            "properties": {
                "backup_dir": {
                    "type": "string",
                    "title": "临时备份目录",
                    "description": "用于存储临时备份文件的目录，备份完成后会移动到最终目录",
                    "default": "/mnt/user/downloads/backup"
                },
                "final_dest_dir": {
                    "type": "string",
                    "title": "最终备份目录",
                    "description": "用于长期存储备份文件的目录",
                    "default": "/mnt/user/downloads/cloud/aliyun/backup/ikuai_backup"
                },
                "ikuai_base_url": {
                    "type": "string",
                    "title": "爱快路由基础URL",
                    "description": "爱快路由管理页面的基础URL",
                    "default": "http://10.0.0.1"
                },
                "ikuai_username": {
                    "type": "string",
                    "title": "爱快路由用户名",
                    "description": "用于登录爱快路由的用户名",
                    "default": "admin"
                },
                "ikuai_password": {
                    "type": "string",
                    "title": "爱快路由密码",
                    "description": "用于登录爱快路由的密码",
                    "default": "password",
                    "format": "password"
                },
                "keep_backup_num": {
                    "type": "integer",
                    "title": "保留备份文件数量",
                    "description": "最多保留的备份文件数量，超出部分将被自动删除",
                    "default": 30,
                    "minimum": 1
                }
            },
            "required": [
                "backup_dir",
                "final_dest_dir",
                "ikuai_base_url",
                "ikuai_username",
                "ikuai_password"
            ]
        }    
