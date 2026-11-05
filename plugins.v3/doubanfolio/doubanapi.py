import re
from typing import List, Tuple
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from http.cookies import SimpleCookie
from app.core.config import settings
from app.core.meta import MetaBase
from app.log import logger
from app.utils.http import RequestUtils


class DoubanApi:

    def __init__(self, user_cookie: str = None):
        self.cookies = user_cookie
        self.cookies = {k: v.value for k, v in SimpleCookie(self.cookies).items()}

        self.headers = {
            'User-Agent': settings.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,en-GB;q=0.2,zh-TW;q=0.2',
            'Connection': 'keep-alive',
            'DNT': '1',
            'HOST': 'www.douban.com'
        }

        self.cookies.pop("__utmz", None)

        # 移除用户传进来的comment-key
        self.cookies.pop("ck", None)

        # 获取最新的ck
        self.set_ck()

        self.ck = self.cookies.get('ck')
        # logger.debug(f"ck:{self.ck} cookie:{self.cookies}")

        if not self.cookies:
            logger.error(f"cookie获取为空，请在插件配置中扫码登录或手动填写 Cookie")
        if not self.ck:
            logger.error(f"请求ck失败，请检查传入的cookie登录状态")

    def set_ck(self):
        self.headers["Cookie"] = ";".join([f"{key}={value}" for key, value in self.cookies.items()])
        response = requests.get("https://www.douban.com/", headers=self.headers)
        ck_str = response.headers.get('Set-Cookie', '')
        # logger.debug(ck_str)
        if not ck_str:
            self.cookies['ck'] = ''
            return
        cookie_parts = ck_str.split(";")
        ck = cookie_parts[0].split("=")[1].strip()
        # logger.debug(ck)
        if ck == '"deleted"':
            self.cookies['ck'] = ''
        else:
            self.cookies['ck'] = ck

    def get_subject_id(self, title: str = None, meta: MetaBase = None) -> Tuple | None:
        if not title:
            title = meta.title
            year = meta.year
        url = f"https://www.douban.com/search?cat=1002&q={title}"
        response = RequestUtils(headers=self.headers).get_res(url)
        if not response.status_code == 200:
            # 检测cookie时静默处理
            if title == "肖申克的救赎":
                return None, None
            error_msg = f"搜索 {title} 失败 状态码：{response.status_code}"
            if "The resource you requested could not be found." in error_msg:
                logger.error("请求的资源未找到（可能是条目不存在或ID错误）")
            else:
                logger.error(error_msg)
            return None, None
        # self.headers["Cookie"] = response.cookies
        soup = BeautifulSoup(response.text.encode('utf-8'), 'lxml')
        title_divs = soup.find_all("div", class_="title")
        subject_items: List = []
        # 遍历所有找到的div标签
        for div in title_divs:
            item = {}

            # title
            a_tag = div.find_all("a")[0]
            item["title"] = a_tag.string
            item["title"] = item["title"].strip()
            link = unquote(a_tag["href"])
            if link.count("subject/"):
                pattern = r"subject/(\d+)/"
                match = re.search(pattern, link)
                if match:
                    subject_id = match.group(1)
                    item["subject_id"] = subject_id
            subject_items.append(item)

        if not subject_items:
            # 检测cookie时静默处理
            if title == "肖申克的救赎":
                return None, None
            logger.warn(f"找不到 {title} 相关条目，本条目不存在于豆瓣")
            return None, None
        for subject_item in subject_items:
            # logger.debug(f"{subject_item['title']} {subject_item['subject_id']}")
            return subject_item["title"], subject_item["subject_id"]
        return None, None

    def delete_watching_mark(self, subject_id: str, category: str = "movie",
                             mark_id: str = "") -> bool:
        """
        删除豆瓣上该条目的标记（豆瓣网页收藏页里叫「删除 / 删除该标记」）。

        优先走网页版「删除」按钮同款接口 /j/mine/j_cat_ui（sid + ck），
        sid 依次尝试收藏页解析出的标记 ID（d_link rel / data-cid）与条目 ID；
        都不行再回退移动端 frodo 的 DELETE /rexxar/api/v2/<cat>/<sid>/interest。
        """
        sid = str(subject_id or "").strip()
        if not sid or not self.ck:
            return False
        host = "movie" if category == "movie" else category
        headers = dict(self.headers)
        headers["Referer"] = f"https://{host}.douban.com/"
        headers["Origin"] = f"https://{host}.douban.com"
        headers["Host"] = f"{host}.douban.com"
        headers["Cookie"] = ";".join([f"{key}={value}" for key, value in self.cookies.items()])
        # 方案一：网页版收藏页「删除」按钮
        candidates = []
        for value in (str(mark_id or "").strip(), sid):
            if value and value not in candidates:
                candidates.append(value)
        for value in candidates:
            try:
                resp = requests.post(
                    url=f"https://{host}.douban.com/j/mine/j_cat_ui",
                    headers=headers,
                    data={"sid": value, "ck": self.ck},
                    timeout=10,
                )
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        # 豆瓣 j_cat_ui 成功时返回 {'result': 'y'}（y=yes），也兼容 True/1
                        ok = data.get("result") in (True, 1, "y", "Y", "yes", "true") or data.get("r") in (0, True)
                    except Exception:
                        ok = "true" in (resp.text or "").lower()
                    if ok:
                        logger.info(f"删除豆瓣标记成功（j_cat_ui, sid={value}）：{sid}")
                        return True
                    logger.warn(f"删除豆瓣标记 j_cat_ui(sid={value}) 返回异常：{(resp.text or '')[:120]}")
                else:
                    logger.warn(f"删除豆瓣标记 j_cat_ui(sid={value}) HTTP {resp.status_code}：{(resp.text or '')[:120]}")
            except Exception as exc:
                logger.warn(f"删除豆瓣标记 j_cat_ui(sid={value}) 请求失败：{exc}")
        # 方案二：移动端 frodo 删除标记
        try:
            mobile_headers = {
                "User-Agent": settings.USER_AGENT,
                "Referer": f"https://m.douban.com/movie/subject/{sid}/",
                "Cookie": headers["Cookie"],
            }
            resp2 = requests.delete(
                f"https://m.douban.com/rexxar/api/v2/{host}/{sid}/interest",
                headers=mobile_headers,
                params={"ck": self.ck},
                timeout=10,
            )
            if resp2.status_code in (200, 204):
                try:
                    data2 = resp2.json()
                    if not data2.get("code") and not data2.get("msg"):
                        logger.info(f"删除豆瓣标记成功（frodo）：{sid}")
                        return True
                except Exception:
                    logger.info(f"删除豆瓣标记成功（frodo）：{sid}")
                    return True
                logger.warn(f"删除豆瓣标记 frodo 返回异常：{(resp2.text or '')[:120]}")
            else:
                logger.warn(f"删除豆瓣标记 frodo HTTP {resp2.status_code}：{(resp2.text or '')[:120]}")
        except Exception as exc:
            logger.warn(f"删除豆瓣标记 frodo 请求失败：{exc}")
        return False

    def set_watching_status(self, subject_id: str, status: str = "do", private: bool = True) -> bool:
        self.headers["Referer"] = f"https://movie.douban.com/subject/{subject_id}/"
        self.headers["Origin"] = "https://movie.douban.com"
        self.headers["Host"] = "movie.douban.com"
        self.headers["Cookie"] = ";".join([f"{key}={value}" for key, value in self.cookies.items()])
        data_json = {
            "ck": self.ck,
            "interest": "do",
            "rating": "",
            "foldcollect": "U",
            "tags": "",
            "comment": ""
        }
        if private:
            data_json["private"] = "on"
        data_json["interest"] = status
        response = requests.post(
            url=f"https://movie.douban.com/j/subject/{subject_id}/interest",
            headers=self.headers,
            data=data_json)
        if not response:
            logger.error(response.text)
            return False
        if response.status_code == 200:
            # 正常情况 {"r":0}
            ret = response.json().get("r")
            r = False if (isinstance(ret, bool) and ret is False) else True
            if r:
                return True
            # 未开播 {"r": false}
            else:
                logger.error(f"douban_id: {subject_id} 未开播")
                return False
        logger.error(response.text)
        return False


if __name__ == "__main__":
    doubanApi = DoubanApi()
    subject_title, subject_id = doubanApi.get_subject_id("太阳的后裔")