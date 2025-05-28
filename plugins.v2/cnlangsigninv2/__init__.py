import random
import re
import time
from datetime import datetime, timedelta

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.core.event import eventmanager, Event
from app.plugins import _PluginBase
from typing import Any, List, Dict, Tuple, Optional
from app.log import logger
from app.schemas.types import EventType
from app.utils.http import RequestUtils
from app.schemas import Notification, NotificationType, MessageChannel


class CnlangSigninV2(_PluginBase):
    # 插件名称
    plugin_name = "国语视界签到V2"
    # 插件描述
    plugin_desc = "美观实用的签到助手，支持账号监控、数据统计、自动签到。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/xijin285/MoviePilot-Plugins/refs/heads/main/icons/cnlang.png"
    # 插件版本
    plugin_version = "2.5.5"
    # 插件作者
    plugin_author = "jinxi"
    # 作者主页
    author_url = "https://github.com/xijin285"
    # 插件配置项ID前缀
    plugin_config_prefix = "cnlangsignin_v2_"
    # 加载顺序
    plugin_order = 2
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    # 任务执行间隔
    _cron = None
    _cookie = None
    _onlyonce = False
    _notify = False
    _history_days = None
    _random_delay = None
    _clear = False
    _notify_style = None
    # 定时器
    _scheduler: Optional[BackgroundScheduler] = None
    # 基础域名
    _base_domain = "cnlang.org"

    def init_plugin(self, config: dict = None):
        logger.info("开始初始化插件...")
        # 停止现有任务
        self.stop_service()

        if config:
            self._enabled = config.get("enabled")
            self._cron = config.get("cron")
            self._cookie = config.get("cookie")
            self._notify = config.get("notify")
            self._onlyonce = config.get("onlyonce")
            self._history_days = config.get("history_days") or 30
            self._random_delay = config.get("random_delay")
            self._clear = config.get("clear")
            self._notify_style = config.get("notify_style")

        # 清除历史
        if self._clear:
            self.del_data('history')
            self._clear = False
            self.__update_config()

        if self._onlyonce:
            try:
                # 确保旧的调度器已关闭
                if self._scheduler and self._scheduler.running:
                    self._scheduler.shutdown()
                    self._scheduler = None
                
                # 创建新的调度器
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                logger.info(f"国语视界签到服务启动，立即运行一次")
                
                # 直接调用签到方法，不使用调度器
                self.signin()
                
                # 关闭一次性开关
                self._onlyonce = False
                self.__update_config()
                
            except Exception as e:
                logger.error(f"启动签到服务失败: {str(e)}")
                if self._scheduler:
                    self._scheduler.shutdown()
                    self._scheduler = None
        elif self._enabled and self._cron:
            # 如果不是一次性运行且启用了定时任务，添加定时任务
            self.__add_task()

    def __update_config(self):
        self.update_config({
            "onlyonce": False,
            "cron": self._cron,
            "enabled": self._enabled,
            "cookie": self._cookie,
            "notify": self._notify,
            "history_days": self._history_days,
            "random_delay": self._random_delay,
            "clear": self._clear,
            "notify_style": self._notify_style
        })

    def __send_fail_msg(self, text):
        logger.info(text)
        if self._notify:
            sign_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            
            # 根据选择的样式发送通知
            if self._notify_style == "style1":
                # 简约现代风格
                title = "🎬 国语视界签到"
                content = f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"❌ 签到失败\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"📝 失败原因：{text}\n" \
                         f"⏰ 执行时间：{sign_time}\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━"
            elif self._notify_style == "style2":
                # 清新风格
                title = "🌸 国语视界签到"
                content = f"┏━━━━━━━━━━━━━━━━━━━━┓\n" \
                         f"┃ ❌ 签到失败\n" \
                         f"┃ 📝 {text}\n" \
                         f"┃ ⏰ {sign_time}\n" \
                         f"┗━━━━━━━━━━━━━━━━━━━━┛"
            elif self._notify_style == "style3":
                # 科技风格
                title = "🚀 国语视界签到"
                content = f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"⚡ 任务执行失败\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"🔍 错误信息：{text}\n" \
                         f"⏱️ 执行时间：{sign_time}\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━"
            elif self._notify_style == "style4":
                # 商务风格
                title = "📊 国语视界签到"
                content = f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"📌 签到状态：失败\n" \
                         f"📋 错误详情：{text}\n" \
                         f"🕒 执行时间：{sign_time}\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━"
            else:
                # 优雅风格
                title = "✨ 国语视界签到"
                content = f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"💫 签到任务执行失败\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"📌 失败原因：{text}\n" \
                         f"🕰️ 执行时间：{sign_time}\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━"
            
            self.post_message(
                mtype=NotificationType.Plugin,
                title=title,
                text=content
            )

    def __send_success_msg(self, text):
        logger.info(text)
        if self._notify:
            sign_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            
            # 根据选择的样式发送通知
            if self._notify_style == "style1":
                # 简约风格
                title = "🎬 国语视界签到"
                content = f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"✅ 签到成功\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"📝 详细信息：\n" \
                         f"{text}\n" \
                         f"⏰ 执行时间：{sign_time}\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━"
            elif self._notify_style == "style2":
                # 清新风格
                title = "🌸 国语视界签到"
                content = f"┏━━━━━━━━━━━━━━━━━━━━┓\n" \
                         f"┃ ✅ 签到成功\n" \
                         f"┃ 📝 {text}\n" \
                         f"┃ ⏰ {sign_time}\n" \
                         f"┗━━━━━━━━━━━━━━━━━━━━┛"
            elif self._notify_style == "style3":
                # 科技风格
                title = "🚀 国语视界签到"
                content = f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"⚡ 任务执行成功\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"🔍 详细信息：\n" \
                         f"{text}\n" \
                         f"⏱️ 执行时间：{sign_time}\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━"
            elif self._notify_style == "style4":
                # 商务风格
                title = "📊 国语视界签到"
                content = f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"📌 签到状态：成功\n" \
                         f"📋 详细信息：\n" \
                         f"{text}\n" \
                         f"🕒 执行时间：{sign_time}\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━"
            else:
                # 优雅风格
                title = "✨ 国语视界签到"
                content = f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"💫 签到任务执行成功\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━\n" \
                         f"📌 详细信息：\n" \
                         f"{text}\n" \
                         f"🕰️ 执行时间：{sign_time}\n" \
                         f"━━━━━━━━━━━━━━━━━━━━━━"
            
            self.post_message(
                mtype=NotificationType.Plugin,
                title=title,
                text=content
            )

    @eventmanager.register(EventType.PluginAction)
    def signin(self, event: Event = None):
        """
        国语视界签到
        """
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "cnlang_signin":
                return
            logger.info("收到命令，开始执行...")

        if not self._cookie:
            self.__send_fail_msg("未配置Cookie")
            return

        _url = "cnlang.org"
        headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                   'Accept - Encoding': 'gzip, deflate, br',
                   'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                   'cache-control': 'max-age=0',
                   'Upgrade-Insecure-Requests': '1',
                   'Host': _url,
                   'Cookie': self._cookie,
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62'}

        res = RequestUtils(headers=headers).get_res(
            url='https://' + _url + '/dsu_paulsign-sign.html?mobile=no')
        if not res or res.status_code != 200:
            self.__send_fail_msg("获取基本信息失败-status_code=" + str(res.status_code if res else "无响应"))
            return

        user_info = res.text
        user_name = re.search(r'title="访问我的空间">(.*?)</a>', user_info)
        if user_name:
            user_name = user_name.group(1)
            logger.info("登录用户名为：" + user_name)
        else:
            self.__send_fail_msg("未获取到用户名-cookie或许已失效")
            return

        is_sign = re.search(r'(您今天已经签到过了或者签到时间还未开始)', user_info)
        if is_sign:
            self.__send_success_msg("您今天已经签到过了或者签到时间还未开始")
            return

        # 使用正则表达式查找 formhash 的值
        formhash_value = re.search(
            r'<input[^>]*name="formhash"[^>]*value="([^"]*)"', user_info)

        if formhash_value:
            formhash_value = formhash_value.group(1)
            logger.info("formhash：" + formhash_value)
        else:
            self.__send_fail_msg("未获取到 formhash 值")
            return

        totalContinuousCheckIn = re.search(
            r'<p>您本月已累计签到:<b>(.*?)</b>', user_info)
        if totalContinuousCheckIn:
            totalContinuousCheckIn = int(totalContinuousCheckIn.group(1)) + 1
            logger.info(f"您本月已累计签到：{totalContinuousCheckIn}")
        else:
            totalContinuousCheckIn = 1

        # 随机获取心情
        default_text = "一别之后，两地相思，只道是三四月，又谁知五六年。"
        max_attempts = 10
        xq = RequestUtils().get_res("https://v1.hitokoto.cn/?encode=text").text
        attempts = 1  # 初始化计数器
        logger.info(f"尝试想说的话-{attempts}: {xq}")

        # 保证字数符合要求并且不超过最大尝试次数
        while (len(xq) < 6 or len(xq) > 50) and attempts < max_attempts:
            xq = RequestUtils().get_res("https://v1.hitokoto.cn/?encode=text").text
            attempts += 1
            logger.info(f"尝试想说的话-{attempts}: {xq}")

        # 如果循环结束后仍不符合要求，使用默认值
        if len(xq) < 6 or len(xq) > 50:
            xq = default_text

        logger.info("最终想说的话：" + xq)

        # 获取签到链接,并签到
        qd_url = 'plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1'

        qd_data = {
            "formhash": formhash_value,
            "qdxq": "kx",
            "qdmode": "1",
            "todaysay": xq,
            "fastreply": "0",
        }

        # 开始签到
        res = RequestUtils(headers=headers).post_res(
            url=f"https://{_url}/{qd_url}", data=qd_data)
        if not res or res.status_code != 200:
            self.__send_fail_msg("请求签到接口失败-status_code=" + str(res.status_code if res else "无响应"))
            return

        sign_html = res.text

        # 使用正则表达式查找 class 为 'c' 的 div 标签中的内容
        content = re.search(r'<div class="c">(.*?)</div>',
                            sign_html, re.DOTALL)
        if content:
            content = content.group(1).strip()
            logger.info(content)
        else:
            self.__send_fail_msg("获取签到后的响应内容失败")
            return

        # 获取积分
        user_info = RequestUtils(headers=headers).get_res(
            url=f'https://{_url}/home.php?mod=spacecp&ac=credit&showcredit=1&inajax=1&ajaxtarget=extcreditmenu_menu').text

        money = re.search(
            r'<span id="hcredit_2">(\d+)</span>', user_info).group(1)

        logger.info(f"当前大洋余额：{money}")

        sign_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        text = (f"签到账号：{user_name}\n"
                f"累计签到：{totalContinuousCheckIn} 天\n"
                f"当前大洋：{money}\n"
                f"签到时间：{sign_time}\n"
                f"{content}")
        # 发送通知
        self.__send_success_msg(text)

        # 读取历史记录
        history = self.get_data('history') or []

        history.append({
            "date": sign_time,
            "username": user_name,
            "totalContinuousCheckIn": totalContinuousCheckIn,
            "money": money,
            "content": content,
        })

        thirty_days_ago = time.time() - int(self._history_days) * 24 * 60 * 60
        history = [record for record in history if
                   datetime.strptime(record["date"],
                                     '%Y-%m-%d %H:%M:%S').timestamp() >= thirty_days_ago]
        # 保存签到历史
        self.save_data(key="history", value=history)

    def __add_task(self):
        """
        增加任务
        """
        try:
            if self._scheduler and self._scheduler.running:
                self._scheduler.shutdown(wait=False)
            
            random_seconds = 5
            if self._random_delay:
                # 拆分字符串获取范围
                start, end = map(int, self._random_delay.split('-'))
                # 生成随机秒数
                random_seconds = random.randint(start, end)

            self._scheduler = BackgroundScheduler(timezone=settings.TZ)
            
            # 如果启用了定时任务，添加定时任务
            if self._enabled and self._cron:
                logger.info(f"添加定时签到任务，cron：{self._cron}")
                self._scheduler.add_job(func=self.signin,
                                      trigger=CronTrigger.from_crontab(self._cron),
                                      name="国语视界定时签到",
                                      id="cnlang_signin_cron")
            
            # 启动任务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()
                logger.info("国语视界签到服务已启动")
        except Exception as e:
            logger.error(f"启动签到服务失败：{str(e)}")
            if self._scheduler:
                self._scheduler.shutdown(wait=False)
                self._scheduler = None

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        定义远程控制命令
        :return: 命令关键字、事件、描述、附带数据
        """
        return [{
            "cmd": "/cnlang_signin",
            "event": EventType.PluginAction,
            "desc": "国语视界签到",
            "category": "站点",
            "data": {
                "action": "cnlang_signin"
            }
        }]

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件公共服务
        """
        if self._enabled and self._cron:
            return [{
                "id": "CnlangSignin",
                "name": "国语视界签到服务",
                "trigger": CronTrigger.from_crontab(self._cron),
                "func": self.signin,  # 直接调用签到函数，而不是__add_task
                "kwargs": {}
            }]
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        return [
            {
                'component': 'VForm',
                'content': [
                    # 基础设置卡片
                    {
                        'component': 'VCard',
                        'props': {
                            'title': '基础设置',
                            'variant': 'outlined',
                            'class': 'mb-4'
                        },
                        'content': [
                            {
                                'component': 'VCardText',
                                'content': [
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
                                                        'component': 'VSwitch',
                                                        'props': {
                                                            'model': 'enabled',
                                                            'label': '启用插件',
                                                            'color': 'primary',
                                                            'prepend-icon': 'mdi-power'
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
                                                        'component': 'VSwitch',
                                                        'props': {
                                                            'model': 'notify',
                                                            'label': '开启通知',
                                                            'color': 'info',
                                                            'prepend-icon': 'mdi-bell'
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
                                                        'component': 'VSwitch',
                                                        'props': {
                                                            'model': 'onlyonce',
                                                            'label': '立即运行一次',
                                                            'color': 'success',
                                                            'prepend-icon': 'mdi-play'
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
                                                        'component': 'VSwitch',
                                                        'props': {
                                                            'model': 'clear',
                                                            'label': '清除历史记录',
                                                            'color': 'warning',
                                                            'prepend-icon': 'mdi-delete'
                                                        }
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    # 运行设置卡片
                    {
                        'component': 'VCard',
                        'props': {
                            'title': '运行设置',
                            'variant': 'outlined',
                            'class': 'mb-4'
                        },
                        'content': [
                            {
                                'component': 'VCardText',
                                'content': [
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
                                                            'label': '签到周期',
                                                            'placeholder': '0 7 * * *',
                                                            'hint': 'Cron表达式，默认每天7点执行',
                                                            'prepend-inner-icon': 'mdi-clock-outline'
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
                                                            'model': 'random_delay',
                                                            'label': '随机延迟(秒)',
                                                            'placeholder': '100-200 随机延迟100-200秒',
                                                            'prepend-inner-icon': 'mdi-timer-outline',
                                                            'hint': '设置随机延迟范围，防止被风控'
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
                                                            'model': 'history_days',
                                                            'label': '保留历史天数',
                                                            'type': 'number',
                                                            'prepend-inner-icon': 'mdi-calendar-clock',
                                                            'hint': '设置历史记录保留天数'
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
                                                        'component': 'VSelect',
                                                        'props': {
                                                            'model': 'notify_style',
                                                            'label': '通知样式',
                                                            'items': [
                                                                {'title': '简约风格', 'value': 'style1', 'prepend-icon': 'mdi-view-dashboard'},
                                                                {'title': '清新风格', 'value': 'style2', 'prepend-icon': 'mdi-flower'},
                                                                {'title': '科技风格', 'value': 'style3', 'prepend-icon': 'mdi-rocket'},
                                                                {'title': '商务风格', 'value': 'style4', 'prepend-icon': 'mdi-briefcase'},
                                                                {'title': '优雅风格', 'value': 'style5', 'prepend-icon': 'mdi-star'}
                                                            ],
                                                            'prepend-inner-icon': 'mdi-palette',
                                                            'hint': '选择通知消息的显示样式',
                                                            'persistent-hint': True
                                                        }
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    # Cookie设置卡片
                    {
                        'component': 'VCard',
                        'props': {
                            'title': 'Cookie设置',
                            'variant': 'outlined',
                            'class': 'mb-4'
                        },
                        'content': [
                            {
                                'component': 'VCardText',
                                'content': [
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
                                                        'component': 'VTextarea',
                                                        'props': {
                                                            'model': 'cookie',
                                                            'label': 'Cnlang Cookie',
                                                            'rows': 5,
                                                            'placeholder': '请填写您的Cookie信息',
                                                            'prepend-inner-icon': 'mdi-cookie',
                                                            'hint': '从浏览器中获取的Cookie信息'
                                                        }
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    # 使用说明卡片
                    {
                        'component': 'VCard',
                        'props': {
                            'variant': 'outlined',
                            'class': 'mb-4'
                        },
                        'content': [
                            {
                                'component': 'VCardTitle',
                                'content': [
                                    {'component': 'VIcon', 'props': {'color': 'info', 'class': 'me-2'}, 'text': 'mdi-help-circle'},
                                    {'component': 'span', 'props': {'class': 'font-weight-bold'}, 'text': '使用说明'}
                                ]
                            },
                            {
                                'component': 'VCardText',
                                'content': [
                                    {
                                        'component': 'div',
                                        'content': [
                                            {'component': 'span', 'text': '🙏 特别鸣谢 imaliang 大佬，插件源码来自于他的脚本。'}
                                        ]
                                    },
                                    {
                                        'component': 'div',
                                        'content': [
                                            {'component': 'span', 'text': '🚀 一键自动签到，省心省力。'}
                                        ]
                                    },
                                    {
                                        'component': 'div',
                                        'content': [
                                            {'component': 'span', 'text': '🕒 灵活定时，支持自定义周期与随机延迟。'}
                                        ]
                                    },
                                    {
                                        'component': 'div',
                                        'content': [
                                            {'component': 'span', 'text': '🔔 多样通知，签到结果实时推送。'}
                                        ]
                                    },
                                    {
                                        'component': 'div',
                                        'content': [
                                            {'component': 'span', 'text': '📅 历史记录清晰可查，数据本地安全保存。'}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "onlyonce": False,
            "notify": False,
            "clear": False,
            "cookie": "",
            "random_delay": "",
            "history_days": 30,
            "cron": "0 7 * * *",
            "notify_style": "style1"
        }

    def get_page(self) -> List[dict]:
        status = self.get_status_summary()
        history = self.get_data('history') or []
        stats = self.__analyze_signin_history(history)

        # 账号信息卡片
        account_card = {
            'component': 'VCard',
            'props': {
                'variant': 'outlined',
                'class': 'mb-4'
            },
            'content': [
                {
                    'component': 'VCardTitle',
                    'props': {
                        'class': 'text-h6'
                    },
                    'content': [
                        {
                            'component': 'VIcon',
                            'props': {
                                'color': 'primary',
                                'class': 'me-2'
                            },
                            'text': 'mdi-account'
                        },
                        {
                            'component': 'span',
                            'text': '账号信息'
                        }
                    ]
                },
                {
                    'component': 'VCardText',
                    'content': [
                        {
                            'component': 'VRow',
                            'props': {
                                'dense': True
                            },
                            'content': [
                                # 用户名
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 3
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'primary',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-account-circle'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '用户名'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': status.get("account", {}).get("username", "未知")
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # 用户组
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 3
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'info',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-account-group'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '用户组'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': status.get("account", {}).get("usergroup", "未知")
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # 大洋余额
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 3
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'success',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-currency-usd'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '大洋余额'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': status.get("account", {}).get("money", "0")
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # Cookie状态
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 3
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'success' if status.get("account", {}).get("cookie_status") == "有效" else 'error',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-cookie' if status.get("account", {}).get("cookie_status") == "有效" else 'mdi-cookie-off'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': 'Cookie状态'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': status.get("account", {}).get("cookie_status", "无效")
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        # 状态展示卡片
        status_card = {
            'component': 'VCard',
            'props': {
                'variant': 'outlined',
                'class': 'mb-4'
            },
            'content': [
                {
                    'component': 'VCardTitle',
                    'props': {
                        'class': 'text-h6'
                    },
                    'content': [
                        {
                            'component': 'VIcon',
                            'props': {
                                'color': 'primary',
                                'class': 'me-2'
                            },
                            'text': 'mdi-information'
                        },
                        {
                            'component': 'span',
                            'text': '签到状态'
                        }
                    ]
                },
                {
                    'component': 'VCardText',
                    'content': [
                        {
                            'component': 'VRow',
                            'props': {
                                'dense': True
                            },
                            'content': [
                                # 服务状态
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 4
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'success' if status["status"] == "运行中" else 'error',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-power' if status["status"] == "运行中" else 'mdi-power-off'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '服务状态'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': status["status"]
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # 下次签到时间
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 4
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'info',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-clock-outline'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '下次签到'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': status["next_sign_time"]
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # 连续签到
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 4
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'warning',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-calendar-check'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '连续签到'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': f"{status['continuous_days']} 天"
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # 本月签到
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 4
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'primary',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-calendar-month'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '本月签到'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': f"{status['month_signs']} 次"
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # 总签到次数
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 4
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'success',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-counter'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '总签到'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': f"{status['total_signs']} 次"
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # 最后签到状态
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 4
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'success' if status["last_sign_status"] == "成功" else 'error',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-check-circle' if status["last_sign_status"] == "成功" else 'mdi-alert-circle'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '最后签到'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': status["last_sign_status"]
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        # 统计分析卡片
        stats_card = {
            'component': 'VCard',
            'props': {
                'variant': 'outlined',
                'class': 'mb-4'
            },
            'content': [
                {
                    'component': 'VCardTitle',
                    'props': {
                        'class': 'text-h6'
                    },
                    'content': [
                        {
                            'component': 'VIcon',
                            'props': {
                                'color': 'primary',
                                'class': 'me-2'
                            },
                            'text': 'mdi-chart-box'
                        },
                        {
                            'component': 'span',
                            'text': '签到统计'
                        }
                    ]
                },
                {
                    'component': 'VCardText',
                    'content': [
                        # 统计数据行
                        {
                            'component': 'VRow',
                            'props': {
                                'dense': True
                            },
                            'content': [
                                # 签到成功率
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 3
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'success',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-percent'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '签到成功率'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': stats["success_rate"]
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # 累计获得大洋
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 3
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'warning',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-currency-usd'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '累计大洋'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': str(stats["total_money"])
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # 平均每次大洋
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 3
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'info',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-calculator'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '平均大洋'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': str(stats["avg_money"])
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # 最佳签到时间
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'sm': 6,
                                        'md': 3
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined',
                                                'class': 'mb-2'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardText',
                                                    'props': {
                                                        'class': 'd-flex align-center'
                                                    },
                                                    'content': [
                                                        {
                                                            'component': 'VIcon',
                                                            'props': {
                                                                'color': 'primary',
                                                                'class': 'me-2'
                                                            },
                                                            'text': 'mdi-clock-outline'
                                                        },
                                                        {
                                                            'component': 'div',
                                                            'content': [
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-subtitle-2'
                                                                    },
                                                                    'text': '最佳时间'
                                                                },
                                                                {
                                                                    'component': 'div',
                                                                    'props': {
                                                                        'class': 'text-h6'
                                                                    },
                                                                    'text': stats["best_time"]
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        # 历史记录表格
                        {
                            'component': 'VDivider',
                            'props': {
                                'class': 'my-4'
                            }
                        },
                        {
                            'component': 'div',
                            'props': {
                                'class': 'text-subtitle-1 d-flex align-center mb-4'
                            },
                            'content': [
                                {
                                    'component': 'VIcon',
                                    'props': {
                                        'color': 'primary',
                                        'class': 'me-2',
                                        'size': 'small'
                                    },
                                    'text': 'mdi-history'
                                },
                                {
                                    'component': 'span',
                                    'text': '签到历史'
                                }
                            ]
                        },
                        {
                            'component': 'VTable',
                            'props': {
                                'hover': True,
                                'density': 'compact',
                                'class': 'sign-history-table',
                                'style': 'background: transparent;'
                            },
                            'content': [
                                {
                                    'component': 'thead',
                                    'content': [
                                        {
                                            'component': 'tr',
                                            'props': {
                                                'style': 'background: rgba(var(--v-theme-surface-variant), 0.1);'
                                            },
                                            'content': [
                                                {
                                                    'component': 'th',
                                                    'props': {
                                                        'class': 'text-caption font-weight-bold text-primary'
                                                    },
                                                    'text': '时间'
                                                },
                                                {
                                                    'component': 'th',
                                                    'props': {
                                                        'class': 'text-caption font-weight-bold text-primary'
                                                    },
                                                    'text': '账号'
                                                },
                                                {
                                                    'component': 'th',
                                                    'props': {
                                                        'class': 'text-caption font-weight-bold text-primary'
                                                    },
                                                    'text': '连续签到次数'
                                                },
                                                {
                                                    'component': 'th',
                                                    'props': {
                                                        'class': 'text-caption font-weight-bold text-primary'
                                                    },
                                                    'text': '当前大洋'
                                                },
                                                {
                                                    'component': 'th',
                                                    'props': {
                                                        'class': 'text-caption font-weight-bold text-primary'
                                                    },
                                                    'text': '响应'
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    'component': 'tbody',
                                    'content': [
                                        {
                                            'component': 'tr',
                                            'props': {
                                                'style': 'background: rgba(var(--v-theme-surface), 0.02);'
                                            },
                                            'content': [
                                                {
                                                    'component': 'td',
                                                    'props': {
                                                        'class': 'text-caption text-medium-emphasis'
                                                    },
                                                    'text': h.get("date")
                                                },
                                                {
                                                    'component': 'td',
                                                    'props': {
                                                        'class': 'text-caption text-medium-emphasis'
                                                    },
                                                    'text': h.get("username")
                                                },
                                                {
                                                    'component': 'td',
                                                    'props': {
                                                        'class': 'text-caption text-medium-emphasis'
                                                    },
                                                    'text': str(h.get("totalContinuousCheckIn"))
                                                },
                                                {
                                                    'component': 'td',
                                                    'props': {
                                                        'class': 'text-caption text-medium-emphasis'
                                                    },
                                                    'text': str(h.get("money"))
                                                },
                                                {
                                                    'component': 'td',
                                                    'props': {
                                                        'class': 'text-caption text-medium-emphasis'
                                                    },
                                                    'text': h.get("content")
                                                }
                                            ]
                                        } for h in sorted(history, key=lambda x: x.get("date", ""), reverse=True)
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        return [account_card, status_card, stats_card]

    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                # 移除所有任务
                self._scheduler.remove_all_jobs()
                # 如果调度器正在运行，则关闭它
                if self._scheduler.running:
                    self._scheduler.shutdown(wait=False)
                # 清空调度器引用
                self._scheduler = None
                logger.info("国语视界签到服务已停止")
        except Exception as e:
            logger.error(f"停止签到服务失败：{str(e)}")
            # 确保调度器被清理
            self._scheduler = None

    def post_message(self, channel: MessageChannel = None, mtype: NotificationType = None, title: str = None,
                     text: str = None, image: str = None, link: str = None, userid: str = None):
        """
        发送消息
        """
        self.chain.post_message(Notification(
            channel=channel, mtype=mtype, title=title, text=text,
            image=image, link=link, userid=userid
        ))

    def __analyze_signin_history(self, history: list) -> dict:
        """
        分析签到历史数据
        """
        if not history:
            return {
                "success_rate": "0%",
                "total_days": 0,
                "success_days": 0,
                "fail_days": 0,
                "total_money": 0,
                "avg_money": 0,
                "max_continuous": 0,
                "current_continuous": 0,
                "best_time": "无",
                "month_stats": {}
            }

        total_days = len(history)
        success_days = len([h for h in history if "签到成功" in h.get("content", "")])
        fail_days = total_days - success_days
        success_rate = f"{(success_days/total_days*100):.1f}%" if total_days > 0 else "0%"

        # 计算大洋统计
        total_money = sum(int(h.get("money", 0)) for h in history if h.get("money", "").isdigit())
        avg_money = f"{total_money/success_days:.1f}" if success_days > 0 else 0

        # 计算最大连续签到天数和当前连续天数
        max_continuous = 0
        current_continuous = 0
        continuous_count = 0
        last_date = None

        for h in sorted(history, key=lambda x: x.get("date", ""), reverse=True):
            current_date = datetime.strptime(h.get("date", ""), '%Y-%m-%d %H:%M:%S').date()
            if "签到成功" in h.get("content", ""):
                if last_date is None:
                    continuous_count = 1
                    current_continuous = 1
                elif (last_date - current_date).days == 1:
                    continuous_count += 1
                    if continuous_count > max_continuous:
                        max_continuous = continuous_count
                    if current_continuous == continuous_count:
                        current_continuous = continuous_count
                else:
                    continuous_count = 1
                last_date = current_date

        # 找出最佳签到时间段
        hour_stats = {}
        for h in history:
            if "签到成功" in h.get("content", ""):
                hour = datetime.strptime(h.get("date", ""), '%Y-%m-%d %H:%M:%S').hour
                hour_stats[hour] = hour_stats.get(hour, 0) + 1
        
        best_time = max(hour_stats.items(), key=lambda x: x[1])[0] if hour_stats else None
        best_time = f"{best_time:02d}:00" if best_time is not None else "无"

        return {
            "success_rate": success_rate,
            "total_days": total_days,
            "success_days": success_days,
            "fail_days": fail_days,
            "total_money": total_money,
            "avg_money": avg_money,
            "max_continuous": max_continuous,
            "current_continuous": current_continuous,
            "best_time": best_time,
            "month_stats": {}
        }

    def get_status_summary(self) -> dict:
        """
        获取服务状态摘要，通过实时请求获取用户信息
        """
        next_run = None
        if self._enabled and self._cron:
            try:
                cron_trigger = CronTrigger.from_crontab(self._cron)
                next_run = cron_trigger.get_next_fire_time(None, datetime.now(tz=pytz.timezone(settings.TZ)))
            except Exception as e:
                logger.error(f"获取下次运行时间失败：{str(e)}")

        # 初始化默认返回数据
        status_data = {
            "status": "运行中" if self._enabled else "已停止",
            "next_sign_time": next_run.strftime('%Y-%m-%d %H:%M:%S') if next_run else "未设置",
            "last_sign_time": "无",
            "last_sign_status": "无",
            "continuous_days": 0,
            "month_signs": 0,
            "total_signs": 0,
            "account": {
                "username": "未知",
                "money": "0",
                "usergroup": "用户",
                "cookie_status": "无效"
            }
        }

        # 如果没有cookie，直接返回默认值
        if not self._cookie:
            return status_data

        try:
            # 设置请求头
            _url = "cnlang.org"
            headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                       'Accept - Encoding': 'gzip, deflate, br',
                       'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                       'cache-control': 'max-age=0',
                       'Upgrade-Insecure-Requests': '1',
                       'Host': _url,
                       'Cookie': self._cookie,
                       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62'}

            # 获取签到页面信息
            res = RequestUtils(headers=headers).get_res(
                url='https://' + _url + '/dsu_paulsign-sign.html?mobile=no')
            
            if res and res.status_code == 200:
                sign_info = res.text
                
                # 获取用户名
                username_match = re.search(r'title="访问我的空间">(.*?)</a>', sign_info)
                if username_match:
                    status_data["account"]["username"] = username_match.group(1)
                    status_data["account"]["cookie_status"] = "有效"
                
                # 获取本月签到次数
                month_signs_match = re.search(r'您本月已累计签到:<b>(\d+)</b>', sign_info)
                if month_signs_match:
                    status_data["month_signs"] = int(month_signs_match.group(1))
                
                # 获取连续签到天数
                continuous_days_match = re.search(r'您已经连续签到<b>(\d+)</b>天', sign_info)
                if continuous_days_match:
                    status_data["continuous_days"] = int(continuous_days_match.group(1))

                # 检查今日是否已签到
                is_signed = re.search(r'您今天已经签到过了或者签到时间还未开始', sign_info)
                if is_signed:
                    status_data["last_sign_status"] = "成功"

            # 获取用户信息和大洋余额
            user_info_res = RequestUtils(headers=headers).get_res(
                url=f'https://{_url}/home.php?mod=spacecp&ac=credit&showcredit=1&inajax=1&ajaxtarget=extcreditmenu_menu')
            
            if user_info_res and user_info_res.status_code == 200:
                user_info = user_info_res.text
                
                # 获取大洋余额
                money_match = re.search(r'<span id="hcredit_2">(\d+)</span>', user_info)
                if money_match:
                    status_data["account"]["money"] = money_match.group(1)

            # 获取用户组信息
            usergroup_res = RequestUtils(headers=headers).get_res(
                url=f'https://{_url}/home.php?mod=spacecp&ac=usergroup')
            
            if usergroup_res and usergroup_res.status_code == 200:
                usergroup_info = usergroup_res.text
                usergroup_match = re.search(r'您目前属于用户组: <strong>(.*?)</strong>', usergroup_info)
                if usergroup_match:
                    status_data["account"]["usergroup"] = usergroup_match.group(1)

            # 获取历史记录用于补充信息
            history = self.get_data('history') or []
            sorted_history = sorted(history, key=lambda x: x.get("date", ""), reverse=True)
            
            # 更新最后签到时间
            if sorted_history:
                status_data["last_sign_time"] = sorted_history[0].get("date", "无")
                if "签到成功" in sorted_history[0].get("content", ""):
                    status_data["last_sign_status"] = "成功"
            
            # 更新总签到次数
            status_data["total_signs"] = len(sorted_history)

        except Exception as e:
            logger.error(f"获取状态信息失败：{str(e)}")

        return status_data