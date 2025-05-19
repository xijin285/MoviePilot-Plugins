# 随机图片API插件

这是一个为 MoviePilot 提供的随机图片API插件，支持多个图片源。

## 功能特点

- 支持多个图片源（Picsum、Unsplash、RandomUser）
- 提供REST API接口
- 支持命令行调用
- 可配置的图片源选择

## 安装说明

1. 确保已安装 MoviePilot
2. 将插件文件夹复制到 MoviePilot 的插件目录
3. 重启 MoviePilot
4. 在插件管理页面启用插件

## 使用方法

### API调用

```
GET /api/v1/randompic
```

### 命令行调用

```
/randompic
```

## 配置说明

在插件配置页面可以：

1. 启用/禁用插件
2. 选择图片源（Picsum/Unsplash/RandomUser）

## 注意事项

- Unsplash API 可能需要 API Key
- 部分图片源可能有访问限制
- 建议使用 Picsum 作为默认图片源

## 许可证

MIT License 