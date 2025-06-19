# 🔑 Proxmox VE API Token 获取指南

## 📋 概述

通过 API Token，MoviePilot 插件可安全地连接 Proxmox VE 并执行备份任务，无需使用完整用户密码。本指南将助您快速配置。

## 🛠️ 如何获取 Proxmox VE API Token

### 步骤 1: 登录 Proxmox VE 后台 🖥️

1.  访问 Proxmox VE Web 界面。
2.  使用管理员或有权限的用户登录。

**提示:** 你可以在这里插入登录界面的截图。
![登录界面](https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/pve/1.png)

### 步骤 2: 进入 API Tokens 管理 🔑

1.  点击 `数据中心` -> `权限` -> `API Tokens`。

**提示:** 你可以在这里插入 API Tokens 界面的截图。
![API Tokens界面](https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/pve/2.png)

### 步骤 3: 创建新 API Token ✨

1.  选择用户（如 `root@pam`），点击 `添加`。
2.  输入 Token 名称（如 `moviepilot-backup`）。
3.  **重要**: `Secret` 仅显示一次！务必立即复制并保存，丢失需重建。

**提示:** 你可以在这里插入创建 Token 对话框的截图。
![创建Token对话框](https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/pve/3.png)
![令牌Token对话框](https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/pve/4.png)
### 步骤 4: 分配 API Token 权限 🔒

为确保插件正常备份，Token 需正确权限。建议最小化授权。
![权限界面](https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/pve/5.png)
**推荐权限（针对备份）：**
*   `Datastore.Audit` (查看存储)
*   `VM.Backup` (执行备份)
*   `VM.Audit` (查看虚拟机)
*   `Sys.Audit` (查看系统日志)

**权限分配步骤：**
1.  点击刚创建的 Token。
2.  在右侧权限面板，点击 `添加`。
3.  选择路径（如 `/` 为全部），选择上述推荐角色，点击 `添加`。

**提示:** 你可以在这里插入权限分配界面的截图。
![权限分配](https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/pve/6.png)

> ⚠️ **重要提示：** 权限不足是常见问题。初期可尝试 `Administrator` 角色测试，功能正常后务必收紧权限，只保留最小必要。

### 步骤 5: 插件中填写 Token 📝

1.  在 MoviePilot 插件配置界面。
2.  `API Token ID` 填写：`用户名@认证域!Token名称` (例：`root@pam!moviepilot-backup`)。
3.  `API Token Secret` 填写：刚复制的密钥。
4.  保存配置。

## ❓ 常见问题与排查

*   **"权限不足"或"认证失败"**：请仔细检查 API Token ID 和 Secret 是否填写正确。同时，确保 API Token 已被赋予足够的权限来执行备份任务（参考步骤 4）。
*   **Token Secret 丢失**：如果 Secret 丢失，您将无法恢复。您需要删除现有的 Token 并重新创建一个新的 Token。

## 📚 参考资料

*   Proxmox VE 官方文档 - API Tokens: [https://pve.proxmox.com/wiki/API_Tokens](https://pve.proxmox.com/wiki/API_Tokens)
