# 随机图片API

提供随机图片API服务，支持横竖屏图片分类。

## 功能特点

- 支持横屏（PC）和竖屏（移动设备）图片分类
- 支持多种图片格式：jpg、jpeg、png、gif、webp
- 简单易用的API接口
- 支持获取图片时发送通知

## 安装说明

1. 将插件文件夹复制到MoviePilot的plugins.v2目录下
2. 在MoviePilot中启用插件
3. 在插件数据目录下会自动创建`pc`和`mobile`文件夹
4. 将对应的图片放入相应文件夹中

## API使用说明

### 获取随机图片

**请求路径：** `/random`

**请求方法：** GET

**参数：**
- `type`: 设备类型（可选）
  - `pc`: 获取横屏图片（默认）
  - `mobile`: 获取竖屏图片

**响应示例：**
```json
{
    "url": "path/to/random/image.jpg"
}
```
