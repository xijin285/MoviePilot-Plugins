# 随机图片API插件

这是一个MoviePilot的随机图片API插件，提供随机图片服务，支持PC和移动端不同尺寸的图片。

## 功能特点

- 支持PC和移动端不同尺寸的图片
- 可自定义配置多个图片源
- 支持缓存机制
- 提供REST API接口
- 支持异步请求处理

## 安装说明

1. 在MoviePilot的插件商店页面，点击"添加第三方仓库"
2. 添加仓库地址：`https://github.com/madrays/MoviePilot-Plugins`
3. 在插件列表中找到"随机图片API"插件
4. 点击安装并启用插件

## 配置说明

### 基本配置

- 启用插件：开启或关闭插件功能
- 图片源配置：配置PC端和移动端的图片源URL列表

### 默认图片源

PC端默认图片源：
- https://picsum.photos/1920/1080
- https://source.unsplash.com/random/1920x1080

移动端默认图片源：
- https://picsum.photos/1080/1920
- https://source.unsplash.com/random/1080x1920

## API接口

### 获取随机图片

- 接口路径：`/api/random_image`
- 请求方法：GET
- 请求参数：
  - device_type：设备类型（pc/mobile），默认为pc
- 返回格式：图片URL字符串

示例请求：
```bash
# PC端图片
curl "http://your-moviepilot-host/api/random_image?device_type=pc"

# 移动端图片
curl "http://your-moviepilot-host/api/random_image?device_type=mobile"
```

## 注意事项

1. 请确保配置的图片源URL可访问
2. 建议使用HTTPS协议的图片源
3. 图片源应返回适当尺寸的图片
4. 如遇到图片加载失败，会自动使用默认图片源

## 更新日志

### v1.0.0 (2024-03-20)
- 初始版本发布
- 支持PC和移动端图片
- 支持自定义图片源
- 实现缓存机制

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 作者

- jinxi
- GitHub: [xijin285](https://github.com/xijin285) 