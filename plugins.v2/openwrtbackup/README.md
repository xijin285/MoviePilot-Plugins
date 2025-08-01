# OpenWrt备份助手

这是一个用于自动备份OpenWrt路由器配置的插件。它支持本地备份和WebDAV远程备份，可以定期自动执行备份任务。

## 功能特点

- 自动备份OpenWrt路由器配置
- 支持本地备份和WebDAV远程备份
- 可配置备份保留数量
- 支持定时任务
- 支持重试机制
- 支持通知功能
- 备份历史记录查看

## 安装说明

1. 在MoviePilot的插件市场中搜索"OpenWrt备份助手"
2. 点击安装按钮进行安装
3. 安装完成后，在插件列表中启用该插件

## 配置说明

### 基础设置

- 启用插件：开启/关闭插件功能
- 启用通知：开启/关闭通知功能
- 立即运行一次：立即执行一次备份任务
- 执行周期：设置定时备份的执行周期，使用cron表达式
- 通知方式：选择通知的触发条件
- 重试次数：备份失败时的重试次数
- 重试间隔：重试之间的等待时间（秒）

### OpenWrt设置

- OpenWrt地址：路由器的Web管理地址，例如：http://192.168.1.1
- 用户名：OpenWrt的管理员用户名，默认为root
- 密码：OpenWrt的管理员密码

### 备份设置

- 启用本地备份：开启/关闭本地备份功能
- 备份文件存储路径：本地备份文件的存储位置
- 本地备份保留数量：本地保留的备份文件数量

### WebDAV远程备份设置

- 启用WebDAV远程备份：开启/关闭WebDAV远程备份功能
- WebDAV服务器地址：WebDAV服务器的地址
- WebDAV用户名：WebDAV服务器的用户名
- WebDAV密码：WebDAV服务器的密码
- WebDAV备份路径：WebDAV服务器上的备份存储路径
- WebDAV备份保留数量：WebDAV服务器上保留的备份文件数量

## 使用说明

1. 完成配置后，插件会自动按照设定的周期执行备份任务
2. 可以点击"立即运行一次"按钮手动触发备份
3. 在插件页面可以查看备份历史记录
4. 如果启用了通知功能，备份成功或失败都会收到通知

## 注意事项

1. 确保OpenWrt路由器的Web管理界面可以正常访问
2. 确保配置的用户名和密码正确
3. 如果使用WebDAV远程备份，确保WebDAV服务器配置正确且可访问
4. 建议定期检查备份文件是否正常生成
5. 建议定期清理过期的备份文件

## 常见问题

1. Q: 备份失败怎么办？
   A: 检查OpenWrt地址、用户名和密码是否正确，确保路由器可以正常访问。

2. Q: WebDAV上传失败怎么办？
   A: 检查WebDAV服务器地址、用户名和密码是否正确，确保服务器可以正常访问。

3. Q: 如何修改备份周期？
   A: 在基础设置中修改"执行周期"，使用cron表达式设置。

4. Q: 备份文件保存在哪里？
   A: 本地备份文件保存在配置的备份路径中，WebDAV备份文件保存在WebDAV服务器的指定路径中。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持OpenWrt路由器配置备份
- 支持本地备份和WebDAV远程备份
- 支持定时任务和通知功能 