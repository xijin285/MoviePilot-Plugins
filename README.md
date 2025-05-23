# 🎬 MoviePilot-Plugins

MoviePilot第三方插件库，提供了一系列实用的插件来增强MoviePilot的功能。

> ⚠️ 注意：本插件库为个人维护，代码结构参考了其他开源项目。推荐优先使用[官方插件库](https://github.com/jxxghp/MoviePilot-Plugins)。

## 📖 使用说明

**本仓库为第三方插件库，需在MoviePilot中添加仓库地址使用**

1. 在MoviePilot的插件商店页面，点击"添加第三方仓库"
2. 添加本仓库地址：`https://github.com/xijin285/MoviePilot-Plugins`
3. 添加成功后，在插件列表中找到需要的插件
4. 安装并启用插件
5. 根据下方说明配置插件参数

## 📦 插件列表

### 🛡️ 爱快路由备份助手 (IkuaiRouterBackup)
-   **版本**: `v1.1.6`
-   **作者**: [@jinxi](https://github.com/xijin285)
-   **简介**: 自动备份您的爱快(iKuai)路由器配置，管理备份文件，为您的网络设置提供一道额外的安全保障。
-   **主要功能**:
    -   ⏰ **定时任务**: 自动执行备份，无需人工干预。
    -   💾 **配置备份**: 完整备份路由器当前配置。
    -   📂 **备份管理**:
        -   自定义备份文件存储路径。
        -   设置备份文件保留数量，自动清理旧备份。
        -   支持本地备份和WebDAV远程备份。
    -   🔔 **结果通知**:
        -   支持5种美观通知样式选择。
        -   清晰反馈备份成功或失败状态。
    -   ⚡ **即时执行**: 支持通过UI触发"立即运行一次"备份。
    -   📊 **历史记录**: 在插件页面查看详细的备份历史。
    -   🔄 **智能重试**: 登录和备份过程中的自动重试机制。
-   **最新更新 (`v1.1.6`)**:
    -   🎨 新增波浪边框和科技风格两种通知样式。
    -   🎯 优化配置界面设计，采用卡片式布局。
    -   ✨ 为所有输入框添加相关图标，提升视觉体验。
-   **历史更新**:
    -   `v1.1.3`:
        -   ☁️ 支持WebDAV远程备份功能。
        -   📦 支持本地备份文件管理。
    -   `v1.1.1`:
        -   🎨 通知功能全面美化，引入多种可选通知样式(简约星线、方块花边、箭头主题)。
        -   ⚠️ 增强失败通知的视觉提示，使其更加醒目。
        -   ⚙️ 配置界面添加通知样式选择器。
    -   `v1.0.0`: 🎉 初始版本发布，提供基础的爱快路由备份功能。

### 🎬 国语视界签到V2 (CnlangSigninV2)
-   **版本**: `v2.2`
-   **作者**: [@jinxi](https://github.com/xijin285)
-   **简介**: 一键自动签到，通知推送，历史美观展示。
-   **主要功能**:
    -   🚀 **一键自动签到**：每日自动完成国语视界论坛签到。
    -   🕒 **灵活定时**：支持自定义签到周期与随机延迟，防止风控。
    -   🔔 **多样通知**：多种通知样式可选，签到结果实时推送。
    -   📅 **历史记录**：签到历史卡片式美观展示，便于查询。
    -   ⚙️ **配置便捷**：表单美观，参数设置直观。
-   **最新更新 (`v2.2`)**:
    -   🆕 新增"使用说明"卡片。
    -   🖼️ 历史记录卡片式展示。
    -   🎨 优化配置表单与通知样式布局。
-   **历史更新**:
    -   `v2.1`:
        -   🔔 增加多种通知样式，整体界面更美观。
    -   `v2.0`:
        -   🛠️ 基于imaliang大佬插件二次开发，优化数据保存与界面，增加通知样式选择、历史记录保留等功能。

## ⚠️ 注意事项

1.  本插件库中的插件均为个人维护，使用前请仔细阅读说明。
2.  部分插件需要特定权限或配置才能正常使用。
3.  如遇到问题，请先查看插件说明或提交Issue。
4.  建议定期更新插件以获取最新功能和修复。

## 🤝 贡献

欢迎提交Issue和Pull Request来帮助改进插件。

## 📄 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。
