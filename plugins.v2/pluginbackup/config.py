{
    "enabled": true,
    "cron": "0 0 * * *",        // 每天0点执行备份（Cron表达式）
    "keep_backup": 30,          // 最多保留30个备份文件
    "backup_dir": "/mnt/user/backups/ikuai/tmp",  // 临时备份目录
    "final_dir": "/mnt/user/backups/ikuai/final",  // 最终存储目录
    "ikuai_url": "http://10.0.0.1",               // 爱快路由管理地址
    "username": "admin",                           // 登录用户名
    "password": "your_encrypted_password"          // 建议存储加密后的密码
}
