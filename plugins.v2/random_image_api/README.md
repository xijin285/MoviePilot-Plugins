# 随机图片API插件

这是一个为MoviePilot设计的随机图片API插件，提供简单的随机图片获取服务。

## 功能特点

- 支持多个图片源
- 可自定义图片源列表
- 提供REST API接口
- 支持图片缓存
- 简单易用的配置界面

## 安装方法

1. 在MoviePilot的插件商店中搜索"随机图片API"
2. 点击安装按钮
3. 安装完成后，在插件配置页面进行设置

## 配置说明

### 图片源

插件默认提供以下图片源：
- https://picsum.photos/800/600
- https://source.unsplash.com/random/800x600

您可以在配置页面添加或修改图片源。每个图片源需要是一个有效的图片URL。

### 缓存时间

设置图片URL的缓存时间，单位为秒。默认值为3600秒（1小时）。

## API使用

插件提供以下API接口：

### 获取随机图片

- 请求方法：GET
- 接口路径：/api/v1/random_image
- 返回格式：图片URL字符串

示例：
```bash
curl http://your-moviepilot-host/api/v1/random_image
```

## 注意事项

1. 请确保添加的图片源是可访问的
2. 建议使用HTTPS图片源
3. 图片源最好提供固定尺寸的图片

## 许可证

MIT License 