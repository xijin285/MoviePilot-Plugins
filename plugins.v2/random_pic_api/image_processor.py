from PIL import Image
import os
from pathlib import Path

def get_image_orientation(image_path):
    """获取图片方向"""
    with Image.open(image_path) as img:
        width, height = img.size
        return "landscape" if width > height else "portrait"

def convert_to_webp(image_path, output_folder, max_pixels=178956970):
    """将图片转换为WebP格式"""
    try:
        with Image.open(image_path) as img:
            # 检查图片大小
            width, height = img.size
            if width * height > max_pixels:
                print(f"跳过 {image_path} 因为超过大小限制")
                return
            
            # 保存为WebP格式
            output_path = Path(output_folder) / f"{Path(image_path).stem}.webp"
            img.save(str(output_path), "webp")
    except Exception as e:
        print(f"转换 {image_path} 失败: {e}")

def process_images(input_folder, output_folder_landscape, output_folder_portrait):
    """处理图片文件夹"""
    input_path = Path(input_folder)
    if not input_path.exists():
        return
        
    for image_path in input_path.glob("*"):
        if image_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            orientation = get_image_orientation(str(image_path))
            try:
                if orientation == "landscape":
                    convert_to_webp(str(image_path), output_folder_landscape)
                else:
                    convert_to_webp(str(image_path), output_folder_portrait)
            except Exception as e:
                print(f"处理 {image_path} 时出错: {e}. 跳过此图片。")

def setup_image_directories():
    """设置图片目录"""
    # 获取插件根目录
    plugin_root = Path(__file__).parent
    
    # 创建必要的目录
    portrait_dir = plugin_root / "portrait"
    landscape_dir = plugin_root / "landscape"
    images_dir = plugin_root / "images"
    
    portrait_dir.mkdir(exist_ok=True)
    landscape_dir.mkdir(exist_ok=True)
    images_dir.mkdir(exist_ok=True)
    
    # 如果存在原始图片目录，则处理图片
    if images_dir.exists():
        process_images(
            str(images_dir),
            str(landscape_dir),
            str(portrait_dir)
        ) 