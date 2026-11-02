# 🎬 MoviePilot-Plugins

MoviePilot第三方插件库，提供了一系列实用的插件来增强MoviePilot的功能。

> ⚠️ 注意：本插件库为个人维护，代码结构参考了其他开源项目。推荐优先使用[官方插件库](https://github.com/jxxghp/MoviePilot-Plugins)。

## 📦 插件列表

| 序号 | 插件名称 | 版本 | 功能描述 | 标签 |
|------|----------|------|----------|------|
| 1 | [🖼️ 随机图库 (RandomPic)](#随机图库-randompic) | v2.0.0 | 智能横竖屏分类的图片API服务 | API/工具 |
| 2 | [☁️ 夸克网盘 (QuarkDisk)](#夸克网盘-quarkdisk) | v1.1.0 | 夸克网盘存储系统集成，支持浏览、整理、下载、上传与刮削保存 | 存储/工具 |
| 3 | [🖥️ PVE虚拟机守护神 (ProxmoxVEBackup)](#pve虚拟机守护神-proxmoxvebackup) | v2.3.4 | 全面的PVE虚拟化管理与备份方案 | 虚拟化/备份 |
| 4 | [🔧 OpenWrt路由备份助手 (OpenWrtBackup)](#openwrt路由备份助手-openwrtbackup) | v1.1.4 | 全自动的OpenWrt配置备份方案 | 网络/备份 |
| 5 | [🌐 爱快路由备份助手 (IkuaiRouterBackup)](#爱快路由备份助手-ikuairouterbackup) | v1.4.0 | 轻松配置您的爱快路由，让路由管理更简单 | 网络/备份 |
| 6 | [📚 豆瓣档案 (DoubanFolio)](#豆瓣收藏夹-doubanfolio) | v1.0.3 | 豆瓣读书/电影收藏夹同步工具 | 媒体/工具 |
| 7 | [🎯 国语视界签到V2 (CnlangSigninV2)](#国语视界签到v2-cnlangsigninv2) | v2.5.8 | 美观实用的站点签到助手 | 站点/工具 |
| 8 | [🛡️ PT云盾优选 (CFIPSelector)](#pt云盾优选-cfipselector) | v1.3.0 | Cloudflare智能IP优选与站点加速 | 网络/PT |


## 📖 使用说明

1. 在MoviePilot的插件商店页面，点击"添加第三方仓库"
2. 添加本仓库地址：`https://github.com/xijin285/MoviePilot-Plugins`
3. 添加成功后，在插件列表中找到需要的插件
4. 安装并启用插件

## 🔄 V2 / V3 双版本说明

MoviePilot V2 与 V3 使用不同的插件加载规则，本仓库同时维护两套索引：

| 宿主版本 | 市场索引 | 源码目录 | 说明 |
|---------|---------|---------|------|
| V2 | `package.v2.json` | `plugins.v2/` | 原有版本，功能与配置保持不变 |
| V3 | `package.v3.json` | `plugins.v3/` | 按 V3 插件规范独立发布，版本号独立递增 |

**已提供 V3 版本**：随机图床API、PT云盾优选、爱快路由时光机、豆瓣档案(自用版)、夸克网盘存储（原「Vue-夸克网盘存储」）。

其余插件暂由 V3 兼容层按 V2 版本加载，后续逐步迁移到 `plugins.v3/`。

V3 插件说明：
- 安装方式与 V2 相同，添加仓库后在插件列表直接安装
- 插件升级后如侧边栏入口未出现，刷新一次浏览器页面即可
- 发布 V3 更新前运行 `python scripts/validate_v3_plugins.py`，该检查会阻止市场 ID、目录、类名、版本号不一致以及缺少前端产物的插件发布

## ⚠️ 注意事项

1.  本插件库中的插件均为个人维护，使用前请仔细阅读说明。
2.  部分插件需要特定权限或配置才能正常使用。
3.  如遇到问题，请先查看插件说明或提交Issue。
4.  建议定期更新插件以获取最新功能和修复。

## 🤝 贡献

欢迎提交Issue和Pull Request来帮助改进插件。

## 📄 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。
