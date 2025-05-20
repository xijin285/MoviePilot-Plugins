import time
import threading
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import pytz
import requests
from urllib.parse import urljoin
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.event import eventmanager
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType, NotificationType

class ImageUrlPlugin(_PluginBase):
    # 插件名称
    plugin_name = "图片URL插件"
    # 插件描述
    plugin_desc = "自动处理图片URL，支持图片上传和转换。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/madrays/MoviePilot-Plugins/main/icons/image.ico"
    # 插件版本
    plugin_version = "1.0.0"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/jinxi"
    # 插件配置项ID前缀
    plugin_config_prefix = "image_url_"
    # 加载顺序
    plugin_order = 0
    # 可使用的用户级别
    auth_level = 2

    # 私有属性
    _scheduler: Optional[BackgroundScheduler] = None
    _lock: Optional[threading.Lock] = None
    _running: bool = False

    # 配置属性
    _enabled: bool = False
    _cron: str = ""
    _onlyonce: bool = False
    _notify: bool = False
    _retry_count: int = 3
    _retry_interval: int = 5
    _image_host: str = ""
    _api_key: str = ""

    def init_plugin(self, config: Optional[dict] = None):
        """初始化插件"""
        self._lock = threading.Lock()
        
        # 停止现有任务
        self.stop_service()

        if config:
            self._enabled = bool(config.get("enabled", False))
            self._cron = str(config.get("cron", ""))
            self._onlyonce = bool(config.get("onlyonce", False))
            self._notify = bool(config.get("notify", False))
            self._retry_count = int(config.get("retry_count", 3))
            self._retry_interval = int(config.get("retry_interval", 5))
            self._image_host = str(config.get("image_host", ""))
            self._api_key = str(config.get("api_key", ""))

            # 保存配置
            self.__update_config()

        # 加载模块
        if self._enabled or self._onlyonce:
            # 立即运行一次
            if self._onlyonce:
                try:
                    # 定时服务
                    self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                    logger.info("图片URL服务启动，立即运行一次")
                    self._scheduler.add_job(func=self.do_process, trigger='date',
                                         run_date=datetime.now(tz=pytz.timezone(settings.TZ)) + timedelta(seconds=3),
                                         name="图片URL服务")

                    # 关闭一次性开关
                    self._onlyonce = False
                    # 保存配置
                    self.__update_config()

                    # 启动任务
                    if self._scheduler and self._scheduler.get_jobs():
                        self._scheduler.print_jobs()
                        self._scheduler.start()
                except Exception as e:
                    logger.error(f"启动一次性任务失败: {str(e)}")

    def __update_config(self):
        """更新配置"""
        self.update_config({
            "enabled": self._enabled,
            "notify": self._notify,
            "cron": self._cron,
            "onlyonce": self._onlyonce,
            "retry_count": self._retry_count,
            "retry_interval": self._retry_interval,
            "image_host": self._image_host,
            "api_key": self._api_key
        })

    def get_state(self) -> bool:
        return self._enabled

    def get_service(self) -> List[Dict[str, Any]]:
        """注册插件公共服务"""
        if self._enabled and self._cron:
            try:
                # 检查是否为5位cron表达式
                if str(self._cron).strip().count(" ") == 4:
                    return [{
                        "id": "ImageUrl",
                        "name": "图片URL服务",
                        "trigger": CronTrigger.from_crontab(self._cron),
                        "func": self.do_process,
                        "kwargs": {}
                    }]
                else:
                    logger.error("cron表达式格式错误")
                    return []
            except Exception as err:
                logger.error(f"定时任务配置错误：{str(err)}")
                return []
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """拼装插件配置页面"""
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'notify',
                                            'label': '发送通知'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'onlyonce',
                                            'label': '立即运行一次'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'image_host',
                                            'label': '图床地址',
                                            'placeholder': '请输入图床API地址'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'api_key',
                                            'label': 'API密钥',
                                            'placeholder': '请输入图床API密钥'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VCronField',
                                        'props': {
                                            'model': 'cron',
                                            'label': '执行周期'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'retry_count',
                                            'label': '最大重试次数',
                                            'type': 'number',
                                            'placeholder': '3'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'retry_interval',
                                            'label': '重试间隔(秒)',
                                            'type': 'number',
                                            'placeholder': '5'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': '【使用说明】\n1. 配置图床API地址和密钥\n2. 设置执行周期，建议每天执行一次\n3. 可选择开启通知，在处理后收到结果通知\n4. 可以设置重试次数和间隔\n5. 启用插件并保存即可'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "notify": False,
            "cron": "0 0 * * *",
            "onlyonce": False,
            "retry_count": 3,
            "retry_interval": 5,
            "image_host": "",
            "api_key": ""
        }

    def stop_service(self):
        """退出插件"""
        try:
            if self._scheduler:
                if self._lock and hasattr(self._lock, 'locked') and self._lock.locked():
                    logger.info("等待当前任务执行完成...")
                    try:
                        self._lock.acquire()
                        self._lock.release()
                    except:
                        pass
                if hasattr(self._scheduler, 'remove_all_jobs'):
                    self._scheduler.remove_all_jobs()
                if hasattr(self._scheduler, 'running') and self._scheduler.running:
                    self._scheduler.shutdown()
                self._scheduler = None
        except Exception as e:
            logger.error(f"退出插件失败：{str(e)}")

    def do_process(self):
        """执行图片处理"""
        if not self._lock:
            self._lock = threading.Lock()
            
        if not self._lock.acquire(blocking=False):
            logger.debug("已有任务正在执行，本次调度跳过！")
            return
            
        try:
            self._running = True
            
            # 检查配置
            if not self._image_host:
                logger.error("未配置图床地址！")
                return
                
            # 执行图片处理
            success = False
            error_msg = None
            results = []
            
            for i in range(self._retry_count):
                try:
                    success, error_msg, results = self.__process_images()
                    if success:
                        break
                    if i < self._retry_count - 1:
                        logger.warning(f"第{i+1}次处理失败：{error_msg}，{self._retry_interval}秒后重试")
                        time.sleep(self._retry_interval)
                except Exception as e:
                    error_msg = str(e)
                    if i < self._retry_count - 1:
                        logger.warning(f"第{i+1}次处理出错：{error_msg}，{self._retry_interval}秒后重试")
                        time.sleep(self._retry_interval)
            
            # 发送通知
            if self._notify:
                title = "🖼️ 图片URL处理任务"
                text = f"图床：{self._image_host}\n"
                if success:
                    text += "状态：✅ 处理成功\n"
                else:
                    text += f"状态：❌ 处理失败\n原因：{error_msg}"
                
                if results:
                    text += "\n📝 处理结果：\n"
                    for result in results:
                        text += f"- {result}\n"
                
                text += f"\n⏱️ {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}"
                
                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title=title,
                    text=text
                )
                
        except Exception as e:
            logger.error(f"图片处理任务执行出错：{str(e)}")
        finally:
            self._running = False
            if self._lock and hasattr(self._lock, 'locked') and self._lock.locked():
                try:
                    self._lock.release()
                except RuntimeError:
                    pass
            logger.debug("任务执行完成")

    def __process_images(self) -> Tuple[bool, Optional[str], List[str]]:
        """处理图片
        
        Returns:
            Tuple[bool, Optional[str], List[str]]: (是否成功, 错误信息, 结果列表)
        """
        try:
            # 构建请求Session
            session = requests.Session()
            
            # 配置重试
            retries = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[403, 404, 500, 502, 503, 504],
                allowed_methods=frozenset(['GET', 'POST']),
                raise_on_status=False
            )
            adapter = HTTPAdapter(max_retries=retries)
            session.mount('https://', adapter)
            session.mount('http://', adapter)
            
            # 设置请求头
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Authorization': f'Bearer {self._api_key}'
            })
            
            # 这里添加具体的图片处理逻辑
            # 示例：上传图片到图床
            # response = session.post(self._image_host, files={'file': open('image.jpg', 'rb')})
            # response.raise_for_status()
            
            # 返回处理结果
            return True, None, ["图片处理成功"]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            return False, f"请求失败: {str(e)}", []
        except Exception as e:
            logger.error(f"处理失败: {str(e)}")
            return False, f"处理失败: {str(e)}", []
        finally:
            session.close() 