import os
import random
from pathlib import Path
from flask import jsonify, send_from_directory, current_app

# 假设 MoviePilot 的 PluginBase 和 logger 可用
# from moviepilot.core.plugin import PluginBase
# from moviepilot.utils.logger import logger # 假设 logger 的导入方式
# 如果没有通用的 PluginBase，我们需要定义一个或者简化

# 临时模拟 PluginBase，如果实际环境中没有提供
class PluginBase:
    plugin_name = "Base Plugin"
    
    def __init__(self, app=None):
        self._app = app # MoviePilot app instance

    def init_plugin(self, config: dict = None):
        pass

    def get_data_path(self):
        # 模拟获取插件数据路径的方法
        # 理想情况下，这应该由 MoviePilot 的 PluginBase 提供
        # 返回插件目录下的 'data' 文件夹
        # 注意：这里的 __file__ 指向 __init__.py
        return Path(os.path.dirname(__file__)) / 'data'

    def get_api(self) -> list:
        return []

    # 其他 PluginBase 可能需要的方法
    def get_state(self) -> bool:
        return True # 示例

    def get_command(self) -> list:
        return []

    def get_service(self) -> list:
        return []

    def get_form(self) -> tuple[list, dict]:
        return [], {}

    def get_page(self) -> list:
        return []
    
    def stop_service(self):
        pass

# 全局 logger 模拟 (实际应由 MoviePilot 提供)
class LoggerMock:
    def info(self, msg):
        print(f"INFO: {msg}")
    def error(self, msg):
        print(f"ERROR: {msg}")
    def warning(self, msg):
        print(f"WARNING: {msg}")

logger = LoggerMock() # 使用模拟的 logger

class RandomImageService(PluginBase):
    # 插件名称
    plugin_name = "随机API服务"
    # 插件描述
    plugin_desc = "提供一个API接口，用于获取随机图片。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/sitemonitor.png"  # 替换为实际图标URL或留空
    # 插件版本
    plugin_version = "0.2.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀 (如果插件有配置项，则需要)
    _config_prefix = "random_image_"
    # 加载顺序
    plugin_order = 18
    # 可使用的用户级别
    user_level = 1

    _image_dir_name = "images" # 图片子目录名
    _image_dir_path: Path = None

    def init_plugin(self, config: dict = None):
        super().init_plugin(config)
        # 图片存放的目录，相对于插件的数据路径或者插件根目录
        # 为了简单和独立性，我们将其放在插件自己的目录下
        self._image_dir_path = Path(os.path.dirname(__file__)) / self._image_dir_name
        
        try:
            if not self._image_dir_path.exists():
                self._image_dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"插件 [{self.plugin_name}]: 图片目录 {self._image_dir_path} 已创建，请向其中添加图片。")
            else:
                logger.info(f"插件 [{self.plugin_name}]: 图片目录 {self._image_dir_path} 已存在。")
        except Exception as e:
            logger.error(f"插件 [{self.plugin_name}]: 创建图片目录 {self._image_dir_path} 失败: {e}")
        
        logger.info(f"插件 [{self.plugin_name}] v{self.plugin_version} 已加载。")

    def get_api(self) -> list:
        return [
            {
                "path": "/random-image",
                "endpoint": f"{self.plugin_name}_random_image", # Endpoint 必须唯一
                "func": self._api_random_image,
                "methods": ["GET"]
            },
            {
                # 注意路径需要与 image_url 匹配，并且是相对于插件的 "namespace"
                # MoviePilot 可能会给插件API加上前缀，例如 /plugins/RandomImageService/images/<filename>
                # 这里我们定义的是插件内部的相对路径
                "path": f"/{self._image_dir_name}/<filename>", 
                "endpoint": f"{self.plugin_name}_serve_image", # Endpoint 必须唯一
                "func": self._api_serve_image,
                "methods": ["GET"]
            }
        ]

    def _api_random_image(self):
        if not self._image_dir_path or not self._image_dir_path.exists():
            return jsonify({"error": "图片目录未初始化或不存在。"}), 500
            
        try:
            image_files = [f.name for f in self._image_dir_path.iterdir() if f.is_file()]
            if not image_files:
                return jsonify({"error": "图片目录中没有找到图片。"}), 404
            
            random_image_name = random.choice(image_files)
            
            # 构建图片的完整访问URL。
            # 这里的URL构建方式取决于MoviePilot如何映射插件API的路径。
            # 假设MoviePilot会将插件API挂载在 /plugins/<plugin_name_lower_case>/ 这样的路径下
            # 或者它有一个辅助函数来生成插件资源的URL。
            # 为简化，我们先假设一个基础路径，如果 MoviePilot 的 Flask app context (`current_app`) 
            # 和请求上下文 (`request`) 可用，可以更精确地构建。
            # 例如: url_for(f"{self.plugin_name}_serve_image", filename=random_image_name, _external=True)
            # 但 `get_api` 返回的是函数，不是在请求上下文中。
            # 我们返回一个相对路径，客户端或MoviePilot前端需要知道如何解析。
            
            # 基于 MoviePilot 的插件 API 路由方式，这里的 URL 应该相对于插件的根路径
            # 例如，如果 MoviePilot 将此插件的 API 挂载到 /mp-plugin-api/randomimageservice/
            # 那么这个 URL 应该是 images/your_image.jpg
            # image_url = f"images/{random_image_name}" 
            
            # 从ikuairouterbackup看，它似乎不直接提供web服务，而是任务型
            # 但我们的目标是API服务。
            # 假设MoviePilot会将插件名作为API路径的一部分
            # 例如: /api/v1/plugins/RandomImageService/images/image.jpg
            # 或者更简单地，MoviePilot会有一个统一的静态文件服务机制
            # 此处我们返回相对于插件API根的路径
            
            # 最终URL需要由MoviePilot在注册API时确定前缀。
            # 这里我们提供相对于插件API根的路径。
            # 例如，如果插件API根是 /plugins/random_image_service/
            # 那么返回的URL就是 images/the_image.jpg
            # 对应的 get_api 中的 serve_image 路径也应该是 'images/<filename>'
            
            # 让我们遵循原始逻辑，但让URL更清晰地表示它是一个相对路径
            # 这个路径将由 MoviePilot 的路由系统与插件的基础 URL 拼接
            api_relative_image_url = f"{self._image_dir_name}/{random_image_name}"

            # 如果MoviePilot在注册API时会自动添加插件的URL前缀, 
            # 例如 /plugins/random_image_service/images/xxx.jpg
            # 那么这个是正确的。
            # 或者，MoviePilot可能期望插件返回一个完整的、可公开访问的URL。
            # 这取决于MoviePilot的实现。
            # 为了安全和通用，我们返回一个指示性的路径，让MoviePilot的路由系统或调用者处理。
            
            # 参照原逻辑，我们构建一个插件内部的路由路径
            # MoviePilot 应该将插件的 API 路由到例如 /plugins/random_image_service/ 这样的路径下
            # 那么， image_url 就可以是 /plugins/random_image_service/images/xxx.jpg
            # 这样，前端可以直接使用。
            
            # 为了适应 MoviePilot 可能的路由方式，这里我们假设插件的根路径会被 MoviePilot 自动添加。
            # 例如，如果插件在 MoviePilot 中被映射到 /randomimageservice/
            # 则这个 URL 会变成 /randomimageservice/images/some_image.jpg
            image_access_path = f"images/{random_image_name}"


            # 考虑到 MoviePilot 的 get_api 可能会将插件API注册到类似 /plugin_api/<plugin_name>/ 的路径下
            # 为了确保链接的正确性，最好的方式是让 MoviePilot 提供一个生成插件内部URL的辅助函数
            # 如果没有，我们就只能返回一个相对路径。
            # 假设 MoviePilot 会将插件的 `get_api` 路径直接映射到 `/plugins/<plugin_name_lower>/<path>`
            # `plugin_name` 可能需要规范化（例如小写）
            plugin_url_base = f"/plugins/{self.plugin_name.lower().replace(' ', '_')}"
            full_image_url = f"{plugin_url_base}/{self._image_dir_name}/{random_image_name}"

            return jsonify({"image_url": full_image_url})
        except Exception as e:
            logger.error(f"插件 [{self.plugin_name}]: 处理 /random-image 失败: {e}")
            return jsonify({"error": str(e)}), 500

    def _api_serve_image(self, filename: str):
        if not self._image_dir_path or not self._image_dir_path.exists():
            # 即使图片目录不存在，也尝试用 send_from_directory，它会处理
            # 但为了日志清晰，先检查
            logger.error(f"插件 [{self.plugin_name}]: 图片目录 {self._image_dir_path} 不存在或未初始化。")
            return jsonify({"error": "图片目录配置错误"}), 404
            
        try:
            # logger.info(f"插件 [{self.plugin_name}]: 尝试从 {self._image_dir_path} 提供文件: {filename}")
            return send_from_directory(self._image_dir_path, filename)
        except Exception as e:
            # send_from_directory 内部会处理 FileNotFoundError 并返回 404
            # 此处捕获其他可能的异常
            logger.error(f"插件 [{self.plugin_name}]: 提供图片 {filename} 失败: {e}")
            return jsonify({"error": f"提供图片失败: {str(e)}"}), 500

    def stop_service(self):
        logger.info(f"插件 [{self.plugin_name}] 已停止。")
        # 如果有后台服务或资源需要清理，在这里处理
        pass

# MoviePilot 期望导出一个名为 `plugin_class` 的变量，指向插件类
plugin_class = RandomImageService

# 下面的 __main__ 部分不再需要，因为插件是由 MoviePilot 加载的
# if __name__ == '__main__':
#     # 这部分代码在插件模式下通常不执行
#     # MoviePilot 会实例化 plugin_class 并调用其方法
#     print("此插件设计为在 MoviePilot 中运行，不直接启动。") 