# 随机图片API插件

这是一个为 MoviePilot 提供的简单随机图片API插件。

## 功能特点

- 从本地图片目录随机返回图片
- 支持多种图片格式（PNG、JPG、JPEG、GIF、WEBP）
- 提供REST API接口
- 支持命令行调用

## 安装说明

1. 确保已安装 MoviePilot
2. 将插件文件夹复制到 MoviePilot 的插件目录
3. 在插件目录下创建 `images` 文件夹并放入图片
4. 重启 MoviePilot
5. 在插件管理页面启用插件

## 使用方法

### API调用

```
GET /api/v1/randompic
```

### 命令行调用

```
/randompic
```

## 注意事项

- 请确保 `images` 目录中有图片文件
- 支持的图片格式：PNG、JPG、JPEG、GIF、WEBP
- 图片文件名不要包含特殊字符

## 许可证

MIT License 