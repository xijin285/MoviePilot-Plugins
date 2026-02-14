import json
import re
import time
import threading
from datetime import datetime
from typing import Any, List, Dict, Tuple, Optional
from urllib.parse import urljoin, quote, urlparse
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from app.log import logger


class IPGroupManager:
    """爱快IP分组管理器"""
    
    def __init__(self, ikuai_url: str, username: str, password: str):
        self.ikuai_url = ikuai_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = None
        self._lock = threading.Lock()
        
    def _create_session(self) -> requests.Session:
        """创建请求会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _login_ikuai(self, session: requests.Session) -> Optional[str]:
        """登录爱快路由器 - 复用__init__.py中的登录逻辑"""
        try:
            import hashlib
            import json
            
            login_url = f"{self.ikuai_url}/Action/login"
            password_md5 = hashlib.md5(self.password.encode('utf-8')).hexdigest()
            login_data = {"username": self.username, "passwd": password_md5}
            
            response = session.post(login_url, data=json.dumps(login_data), headers={'Content-Type': 'application/json'}, timeout=10)
            response.raise_for_status()
            
            cookies = response.cookies
            sess_key_value = cookies.get("sess_key")
            if sess_key_value:
                return f"sess_key={sess_key_value}"
            
            set_cookie_header = response.headers.get('Set-Cookie')
            if set_cookie_header:
                match = re.search(r'sess_key=([^;]+)', set_cookie_header)
                if match:
                    return f"sess_key={match.group(1)}"
            
            logger.error(f"登录成功但未能从Cookie或头部提取 sess_key。响应: {response.text[:200]}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"登录请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"登录过程中发生未知错误: {e}")
            return None
    
    def get_ip_blocks_from_22tool(self, province: str = "", city: str = "", isp: str = "") -> List[Dict[str, Any]]:
        """从IP段信息获取IP段信息"""
        try:
            # 构建正确的URL路径
            url_parts = ["https://www.22tool.com/ip-block", "china"]
            
            # 省份映射
            province_map = {
                "北京": "beijing",
                "天津": "tianjin",
                "河北": "hebei",
                "山西": "shanxi",
                "内蒙古": "neimenggu",
                "辽宁": "liaoning",
                "吉林": "jilin",
                "黑龙江": "heilongjiang",
                "上海": "shanghai",
                "江苏": "jiangsu",
                "浙江": "zhejiang",
                "安徽": "anhui",
                "福建": "fujian",
                "江西": "jiangxi",
                "山东": "shandong",
                "河南": "henan",
                "湖北": "hubei",
                "湖南": "hunan",
                "广东": "guangdong",
                "广西": "guangxi",
                "海南": "hainan",
                "重庆": "chongqing",
                "四川": "sichuan",
                "贵州": "guizhou",
                "云南": "yunnan",
                "西藏": "xizang",
                "陕西": "shaanxi",
                "甘肃": "gansu",
                "青海": "qinghai",
                "宁夏": "ningxia",
                "新疆": "xinjiang",
                "台湾": "taiwan",
                "香港": "hongkong",
                "澳门": "macau",
            }
         
            # 城市映射
            city_map = {
                "北京": "beijing",
                "天津": "tianjin",
                "上海": "shanghai",
                "重庆": "chongqing",
                "石家庄": "shijiazhuang",
                "唐山": "tangshan",
                "秦皇岛": "qinhuangdao",
                "邯郸": "handan",
                "邢台": "xingtai",
                "保定": "baoding",
                "张家口": "zhangjiakou",
                "承德": "chengde",
                "沧州": "cangzhou",
                "廊坊": "langfang",
                "衡水": "hengshui",
                "太原": "taiyuan",
                "大同": "datong",
                "朔州": "shuozhou",
                "忻州": "xinzhou",
                "阳泉": "yangquan",
                "吕梁": "lvliang",
                "晋中": "jinzhong",
                "长治": "changzhi",
                "晋城": "jincheng",
                "临汾": "linfen",
                "运城": "yuncheng",
                "呼和浩特": "huhehaote",
                "包头": "baotou",
                "乌海": "wuhai",
                "赤峰": "chifeng",
                "通辽": "tongliao",
                "鄂尔多斯": "eerduosi",
                "呼伦贝尔": "hulunbeier",
                "巴彦淖尔": "bayannaoer",
                "乌兰察布": "wulanchabu",
                "沈阳": "shenyang",
                "大连": "dalian",
                "鞍山": "anshan",
                "抚顺": "fushun",
                "本溪": "benxi",
                "丹东": "dandong",
                "锦州": "jinzhou",
                "营口": "yingkou",
                "阜新": "fuxin",
                "辽阳": "liaoyang",
                "盘锦": "panjin",
                "铁岭": "tieling",
                "朝阳": "chaoyang",
                "葫芦岛": "huludao",
                "长春": "changchun",
                "吉林": "jilin",
                "四平": "siping",
                "辽源": "liaoyuan",
                "通化": "tonghua",
                "白山": "baishan",
                "松原": "songyuan",
                "白城": "baicheng",
                "哈尔滨": "haerbin",
                "齐齐哈尔": "qiqihaer",
                "鸡西": "jixi",
                "鹤岗": "hegang",
                "双鸭山": "shuangyashan",
                "大庆": "daqing",
                "伊春": "yichun",
                "佳木斯": "jiamusi",
                "七台河": "qitaihe",
                "牡丹江": "mudanjiang",
                "黑河": "heihe",
                "绥化": "suihua",
                "南京": "nanjing",
                "无锡": "wuxi",
                "徐州": "xuzhou",
                "常州": "changzhou",
                "苏州": "suzhou",
                "南通": "nantong",
                "连云港": "lianyungang",
                "淮安": "huaian",
                "盐城": "yancheng",
                "扬州": "yangzhou",
                "镇江": "zhenjiang",
                "泰州": "taizhou",
                "宿迁": "suqian",
                "杭州": "hangzhou",
                "宁波": "ningbo",
                "温州": "wenzhou",
                "嘉兴": "jiaxing",
                "湖州": "huzhou",
                "绍兴": "shaoxing",
                "金华": "jinhua",
                "衢州": "quzhou",
                "舟山": "zhoushan",
                "台州": "taizhou",
                "丽水": "lishui",
                "合肥": "hefei",
                "芜湖": "wuhu",
                "蚌埠": "bengbu",
                "淮南": "huainan",
                "马鞍山": "maanshan",
                "淮北": "huaibei",
                "铜陵": "tongling",
                "安庆": "anqing",
                "黄山": "huangshan",
                "阜阳": "fuyang",
                "宿州": "suzhou",
                "滁州": "chuzhou",
                "六安": "liuan",
                "宣城": "xuancheng",
                "池州": "chizhou",
                "亳州": "bozhou",
                "福州": "fuzhou",
                "泉州": "quanzhou",
                "厦门": "xiamen",
                "漳州": "zhangzhou",
                "莆田": "putian",
                "三明": "sanming",
                "南平": "nanping",
                "龙岩": "longyan",
                "宁德": "ningde",
                "南昌": "nanchang",
                "景德镇": "jingdezhen",
                "萍乡": "pingxiang",
                "九江": "jiujiang",
                "新余": "xinyu",
                "鹰潭": "yingtan",
                "赣州": "ganzhou",
                "吉安": "jian",
                "宜春": "yichun",
                "抚州": "fuzhou",
                "上饶": "shangrao",
                "济南": "jinan",
                "青岛": "qingdao",
                "淄博": "zibo",
                "枣庄": "zaozhuang",
                "东营": "dongying",
                "烟台": "yantai",
                "潍坊": "weifang",
                "济宁": "jining",
                "泰安": "taian",
                "威海": "weihai",
                "日照": "rizhao",
                "临沂": "linyi",
                "德州": "dezhou",
                "聊城": "liaocheng",
                "滨州": "binzhou",
                "菏泽": "heze",
                "郑州": "zhengzhou",
                "开封": "kaifeng",
                "洛阳": "luoyang",
                "平顶山": "pingdingshan",
                "安阳": "anyang",
                "鹤壁": "hebi",
                "新乡": "xinxiang",
                "焦作": "jiaozuo",
                "濮阳": "puyang",
                "许昌": "xuchang",
                "漯河": "luohe",
                "三门峡": "sanmenxia",
                "南阳": "nanyang",
                "商丘": "shangqiu",
                "信阳": "xinyang",
                "周口": "zhoukou",
                "驻马店": "zhumadian",
                "武汉": "wuhan",
                "黄石": "huangshi",
                "十堰": "shiyan",
                "宜昌": "yichang",
                "襄阳": "xiangyang",
                "鄂州": "ezhou",
                "荆门": "jingmen",
                "孝感": "xiaogan",
                "荆州": "jingzhou",
                "黄冈": "huanggang",
                "咸宁": "xianning",
                "随州": "suizhou",
                "长沙": "changsha",
                "株洲": "zhuzhou",
                "湘潭": "xiangtan",
                "衡阳": "hengyang",
                "邵阳": "shaoyang",
                "岳阳": "yueyang",
                "常德": "changde",
                "张家界": "zhangjiajie",
                "益阳": "yiyang",
                "郴州": "chenzhou",
                "永州": "yongzhou",
                "怀化": "huaihua",
                "娄底": "loudi",
                "广州": "guangzhou",
                "深圳": "shenzhen",
                "珠海": "zhuhai",
                "汕头": "shantou",
                "佛山": "foshan",
                "韶关": "shaoguan",
                "湛江": "zhanjiang",
                "肇庆": "zhaoqing",
                "江门": "jiangmen",
                "茂名": "maoming",
                "惠州": "huizhou",
                "梅州": "meizhou",
                "汕尾": "shanwei",
                "河源": "heyuan",
                "阳江": "yangjiang",
                "清远": "qingyuan",
                "东莞": "dongguan",
                "中山": "zhongshan",
                "潮州": "chaozhou",
                "揭阳": "jieyang",
                "云浮": "yunfu",
                "南宁": "nanning",
                "柳州": "liuzhou",
                "桂林": "guilin",
                "梧州": "wuzhou",
                "北海": "beihai",
                "防城港": "fangchenggang",
                "钦州": "qinzhou",
                "贵港": "guigang",
                "玉林": "yulin",
                "百色": "baise",
                "贺州": "hezhou",
                "河池": "hechi",
                "来宾": "laibin",
                "崇左": "chongzuo",
                "海口": "haikou",
                "三亚": "sanya",
                "三沙": "sansha",
                "儋州": "danzhou",
                "成都": "chengdu",
                "自贡": "zigong",
                "攀枝花": "panzhihua",
                "泸州": "luzhou",
                "德阳": "deyang",
                "绵阳": "mianyang",
                "广元": "guangyuan",
                "遂宁": "suining",
                "内江": "neijiang",
                "乐山": "leshan",
                "南充": "nanchong",
                "眉山": "meishan",
                "宜宾": "yibin",
                "广安": "guangan",
                "达州": "dazhou",
                "雅安": "yaan",
                "巴中": "bazhong",
                "资阳": "ziyang",
                "贵阳": "guiyang",
                "六盘水": "liupanshui",
                "遵义": "zunyi",
                "安顺": "anshun",
                "毕节": "bijie",
                "铜仁": "tongren",
                "昆明": "kunming",
                "曲靖": "qujing",
                "玉溪": "yuxi",
                "保山": "baoshan",
                "昭通": "zhaotong",
                "丽江": "lijiang",
                "普洱": "puer",
                "临沧": "lincang",
                "拉萨": "lasa",
                "日喀则": "rikaze",
                "昌都": "changdu",
                "林芝": "linzhi",
                "山南": "shannan",
                "那曲": "naqu",
                "阿里": "ali",
                "西安": "xian",
                "铜川": "tongchuan",
                "宝鸡": "baoji",
                "咸阳": "xianyang",
                "渭南": "weinan",
                "延安": "yanan",
                "汉中": "hanzhong",
                "榆林": "yulin",
                "安康": "ankang",
                "商洛": "shangluo",
                "兰州": "lanzhou",
                "嘉峪关": "jiayuguan",
                "金昌": "jinchang",
                "白银": "baiyin",
                "天水": "tianshui",
                "武威": "wuwei",
                "张掖": "zhangye",
                "平凉": "pingliang",
                "酒泉": "jiuquan",
                "庆阳": "qingyang",
                "定西": "dingxi",
                "陇南": "longnan",
                "西宁": "xining",
                "海东": "haidong",
                "银川": "yinchuan",
                "石嘴山": "shizuishan",
                "吴忠": "wuzhong",
                "固原": "guyuan",
                "中卫": "zhongwei",
                "乌鲁木齐": "wulumuqi",
                "克拉玛依": "kelamayi",
                "吐鲁番": "tulufan",
                "哈密": "hami",
                "台北": "taibei",
                "高雄": "gaoxiong",
                "台中": "taizhong",
                "台南": "tainan",
                "新竹": "xinzhu",
                "嘉义": "jiayi",
                "香港": "hongkong",
                "澳门": "macau",
            }

            
            # 运营商映射
            isp_map = {
                "电信": "4",
                "联通": "10", 
                "移动": "11",
                "铁通": "18",
                "教育网": "30",
                "广电": "133"
            }
            
            # 添加省份
            if province and province != "全部":
                province_code = province_map.get(province, province.lower())
                url_parts.append(province_code)
            else:
                url_parts.append("all")
            
            # 添加城市
            if city and city != "全部":
                city_code = city_map.get(city, city.lower())
                url_parts.append(city_code)
            else:
                url_parts.append("all")
            
            # 添加运营商
            if isp and isp != "全部":
                isp_code = isp_map.get(isp, isp)
                url_parts.append(isp_code)
            else:
                url_parts.append("all")
            
            base_url = "/".join(url_parts)
            
            session = self._create_session()
            
            # 获取所有页面的IP段数据
            all_ip_blocks = []
            page = 1
            max_pages = 10  # 限制最大页数，避免无限循环
            
            logger.info(f"开始获取IP段信息，搜索条件: 省份={province or '全部'}, 城市={city or '全部'}, 运营商={isp or '全部'}")
            
            while page <= max_pages:
                logger.info(f"正在获取第 {page} 页IP段信息...")
                # 构建带页码的URL
                if page == 1:
                    page_url = base_url
                else:
                    page_url = f"{base_url}?page={page}"
                
                response = session.get(page_url, timeout=30)
                response.raise_for_status()
                
                # 解析当前页面的IP段数据
                page_ip_blocks = self._parse_ip_blocks_from_html(response.text, province, city, isp)
                
                if not page_ip_blocks:
                    logger.info(f"第 {page} 页没有找到IP段信息，停止获取")
                    break
                
                logger.info(f"第 {page} 页获取到 {len(page_ip_blocks)} 个IP段")
                all_ip_blocks.extend(page_ip_blocks)
                
                # 检查是否还有下一页
                if not self._has_next_page(response.text):
                    logger.info("已到达最后一页，停止获取")
                    break
                
                page += 1
                time.sleep(1)  # 避免请求过于频繁
            
            logger.info(f"IP段信息获取完成，共获取到 {len(all_ip_blocks)} 个IP段")
            return all_ip_blocks
            
        except Exception as e:
            logger.error(f"从IP段信息获取IP段信息失败: {str(e)}")
            return []
    
    def _parse_ip_blocks_from_html(self, html_content: str, province: str, city: str, isp: str) -> List[Dict[str, Any]]:
        """从HTML内容中解析IP段数据"""
        ip_blocks = []
        
        # 首先尝试简单的表格解析
        try:
            # 查找表格行
            table_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html_content, re.DOTALL)
            
            for row in table_rows:
                # 提取单元格内容
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cells) >= 6:
                    # 清理HTML标签
                    clean_cells = []
                    for cell in cells:
                        # 移除HTML标签
                        clean_cell = re.sub(r'<[^>]+>', '', cell)
                        clean_cell = clean_cell.strip()
                        clean_cells.append(clean_cell)
                    
                    if len(clean_cells) >= 6:
                        ip_start, ip_end, ip_count, province_name, city_name, isp_name = clean_cells[:6]
                        
                        # 验证IP地址格式
                        if (ip_start and ip_end and 
                            re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_start) and
                            re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_end)):
                            
                            ip_blocks.append({
                                'ip_start': ip_start,
                                'ip_end': ip_end,
                                'ip_count': int(ip_count.replace(',', '')) if ip_count.replace(',', '').isdigit() else 0,
                                'province': province_name,
                                'city': city_name,
                                'isp': isp_name
                            })
            
            if ip_blocks:
                return ip_blocks
                
        except Exception as e:
            logger.warning(f"表格解析失败: {e}")
        
        return ip_blocks
    
    def _has_next_page(self, html_content: str) -> bool:
        """检查是否有下一页"""
        # 检查是否有"下一页"链接或页码
        next_page_patterns = [
            r'下一页',
            r'next',
            r'page=\d+',
            r'下一页.*?href'
        ]
        
        for pattern in next_page_patterns:
            if re.search(pattern, html_content, re.IGNORECASE):
                return True
        
        return False
    
    def get_available_provinces(self) -> List[str]:
        """获取可用的省份列表"""
        try:
            session = self._create_session()
            response = session.get("https://www.22tool.com/ip-block", timeout=30)
            response.raise_for_status()
            
            logger.info(f"获取省份列表 - 请求URL: {response.url}")
            logger.info(f"获取省份列表 - 响应状态码: {response.status_code}")
            
            # 提取省份选项
            provinces = []
            
            # 尝试多种模式匹配省份选项
            patterns = [
                r'<option value="([^"]+)">([^<]+)</option>',
                r'<option[^>]*value="([^"]+)"[^>]*>([^<]+)</option>',
                r'<option[^>]*>([^<]+)</option>',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                logger.info(f"省份匹配模式找到 {len(matches)} 个结果")
                
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        value, name = match[:2]
                    elif isinstance(match, str):
                        value, name = match, match
                    else:
                        continue
                        
                    if value and name and value != "全部" and name != "全部":
                        provinces.append(name.strip())
                
                if provinces:
                    break
            
            # 如果没有找到省份，返回一些默认的省份列表
            if not provinces:
                logger.warning("未从网页解析到省份信息，使用默认省份列表")
                provinces = [
                    "北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
                    "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
                    "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州",
                    "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆"
                ]
            
            logger.info(f"获取到 {len(provinces)} 个省份")
            return provinces
            
        except Exception as e:
            logger.error(f"获取省份列表失败: {str(e)}")
            # 返回默认省份列表
            return [
                "北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江",
                "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
                "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州",
                "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆"
            ]
    
    def get_available_cities(self, province: str) -> List[str]:
        """获取指定省份的城市列表"""
        try:
            session = self._create_session()
            response = session.get("https://www.22tool.com/ip-block", params={'province': province}, timeout=30)
            response.raise_for_status()
            
            logger.info(f"获取城市列表 - 请求URL: {response.url}")
            logger.info(f"获取城市列表 - 响应状态码: {response.status_code}")
            
            # 提取城市选项
            cities = []
            
            # 尝试多种模式匹配城市选项
            patterns = [
                r'<option value="([^"]+)">([^<]+)</option>',
                r'<option[^>]*value="([^"]+)"[^>]*>([^<]+)</option>',
                r'<option[^>]*>([^<]+)</option>',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                logger.info(f"城市匹配模式找到 {len(matches)} 个结果")
                
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        value, name = match[:2]
                    elif isinstance(match, str):
                        value, name = match, match
                    else:
                        continue
                        
                    if value and name and value != "全部" and name != "全部":
                        cities.append(name.strip())
                
                if cities:
                    break
            
            # 如果没有找到城市，根据省份返回一些默认城市
            if not cities:
                logger.warning(f"未从网页解析到城市信息，为省份 {province} 使用默认城市列表")
                default_cities = {
                    "北京": ["北京"],
                    "天津": ["天津"],
                    "上海": ["上海"],
                    "重庆": ["重庆"],
                    "广东": ["广州", "深圳", "珠海", "汕头", "佛山", "韶关", "湛江", "肇庆", "江门", "茂名", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮"],
                    "江苏": ["南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁"],
                    "浙江": ["杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水"],
                    "山东": ["济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安", "威海", "日照", "莱芜", "临沂", "德州", "聊城", "滨州", "菏泽"],
                }
                cities = default_cities.get(province, [province])
            
            logger.info(f"为省份 {province} 获取到 {len(cities)} 个城市")
            return cities
            
        except Exception as e:
            logger.error(f"获取城市列表失败: {str(e)}")
            # 返回省份名称作为默认城市
            return [province] if province else []
    
    def get_available_isps(self) -> List[str]:
        """获取可用的运营商列表"""
        try:
            session = self._create_session()
            response = session.get("https://www.22tool.com/ip-block", timeout=30)
            response.raise_for_status()
            
            logger.info(f"获取运营商列表 - 请求URL: {response.url}")
            logger.info(f"获取运营商列表 - 响应状态码: {response.status_code}")
            
            # 提取运营商选项
            isps = []
            
            # 尝试多种模式匹配运营商选项
            patterns = [
                r'<option value="([^"]+)">([^<]+)</option>',
                r'<option[^>]*value="([^"]+)"[^>]*>([^<]+)</option>',
                r'<option[^>]*>([^<]+)</option>',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                logger.info(f"运营商匹配模式找到 {len(matches)} 个结果")
                
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        value, name = match[:2]
                    elif isinstance(match, str):
                        value, name = match, match
                    else:
                        continue
                        
                    if value and name and value != "全部" and name != "全部":
                        isps.append(name.strip())
                
                if isps:
                    break
            
            # 如果没有找到运营商，返回一些默认的运营商列表
            if not isps:
                logger.warning("未从网页解析到运营商信息，使用默认运营商列表")
                isps = [
                    "电信", "联通", "移动", "铁通", "教育网", "广电", "长城宽带", "鹏博士",
                    "阿里云", "腾讯云", "华为云", "百度云", "亚马逊云", "微软云"
                ]
            
            logger.info(f"获取到 {len(isps)} 个运营商")
            return isps
            
        except Exception as e:
            logger.error(f"获取运营商列表失败: {str(e)}")
            # 返回默认运营商列表
            return [
                "电信", "联通", "移动", "铁通", "教育网", "广电", "长城宽带", "鹏博士",
                "阿里云", "腾讯云", "华为云", "百度云", "亚马逊云", "微软云"
            ]
    
    def create_ip_group(self, group_name: str, ip_list: List[str], address_pool: bool = False, use_new_api: bool = True) -> Tuple[bool, Optional[str]]:
        """在爱快路由器上创建IP分组，兼容新旧接口"""
        try:
            session = self._create_session()
            token = self._login_ikuai(session)
            if not token:
                return False, "登录失败"
            create_url = f"{self.ikuai_url}/Action/call"
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self.ikuai_url.rstrip('/'),
                'Referer': self.ikuai_url.rstrip('/') + '/'
            }
            # 新版接口参数
            if use_new_api:
                ip_group_data = {
                    "func_name": "route_object_ip",
                    "action": "add",
                    "param": {
                        "name": group_name,
                        "ip_list": ip_list,
                        "type": 0
                    }
                }
            else:
                ip_group_data = {
                    "func_name": "ipgroup",
                    "action": "add",
                    "param": {
                        "group_name": group_name,
                        "addr_pool": ",".join(ip_list) if ip_list else "",
                        "newRow": True,
                        "type": 0
                    }
                }
            try:
                logger.info(f"正在创建IP分组: {group_name}，包含 {len(ip_list)} 个IP范围")
                response = session.post(create_url, data=json.dumps(ip_group_data), headers=request_headers, timeout=30)
                response.raise_for_status()
                try:
                    res_json = response.json()
                except Exception:
                    res_json = None
                # 新版接口判断
                if use_new_api and res_json:
                    if res_json.get("code") == 0 and res_json.get("message", "").lower() == "success":
                        logger.info(f"IP分组 {group_name} 创建成功 (新版)")
                        return True, None
                    err_msg = res_json.get("message", "创建IP分组API未返回成功或指定错误信息")
                    logger.error(f"IP分组 {group_name} 创建失败 (新版)。响应: {res_json}, 错误: {err_msg}")
                    return False, f"路由器返回错误: {err_msg}"
                # 旧版接口判断
                if not use_new_api and res_json:
                    if res_json.get("Result") == 30000 and res_json.get("ErrMsg", "").lower() == "success":
                        logger.info(f"IP分组 {group_name} 创建成功 (旧版)")
                        return True, None
                    err_msg = res_json.get("ErrMsg") or res_json.get("errmsg", "创建IP分组API未返回成功或指定错误信息")
                    logger.error(f"IP分组 {group_name} 创建失败 (旧版)。响应: {res_json}, 错误: {err_msg}")
                    return False, f"路由器返回错误: {err_msg}"
                # 兜底
                response_text = response.text.strip().lower()
                if "success" in response_text or response_text == '"success"':
                    logger.info(f"IP分组 {group_name} 创建成功 (文本)")
                    return True, None
                logger.error(f"IP分组 {group_name} 创建失败，响应: {response.text[:200]}")
                return False, f"路由器返回非预期响应: {response_text[:100]}"
            except requests.exceptions.Timeout:
                logger.warning(f"创建IP分组 {group_name} 请求超时。")
                return True, "请求超时，但IP分组可能已开始创建"
            except requests.exceptions.RequestException as e:
                logger.error(f"创建IP分组 {group_name} 请求失败: {e}")
                return False, str(e)
            except Exception as e:
                logger.error(f"创建IP分组 {group_name} 过程中发生未知错误: {e}")
                return False, str(e)
        except Exception as e:
            logger.error(f"创建IP分组异常: {str(e)}")
            return False, str(e)
    
    def get_existing_ip_groups(self, use_new_api: bool = True) -> List[Dict[str, Any]]:
        """获取现有的IP分组列表，兼容新旧接口"""
        try:
            session = self._create_session()
            token = self._login_ikuai(session)
            if not token:
                return []
            list_url = f"{self.ikuai_url}/Action/call"
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self.ikuai_url.rstrip('/'),
                'Referer': self.ikuai_url.rstrip('/') + '/'
            }
            if use_new_api:
                list_data = {
                    "func_name": "route_object_ip",
                    "action": "show",
                    "param": {}
                }
            else:
                list_data = {
                    "func_name": "ipgroup",
                    "action": "show",
                    "param": {
                        "ORDER": "desc",
                        "ORDER_BY": "time",
                        "LIMIT": "0,50"
                    }
                }
            try:
                logger.info(f"尝试从 {self.ikuai_url} 获取IP分组列表...")
                response = session.post(list_url, data=json.dumps(list_data), headers=request_headers, timeout=15)
                response.raise_for_status()
                try:
                    res_json = response.json()
                except Exception:
                    res_json = None
                if use_new_api and res_json:
                    if res_json.get("code") == 0 and res_json.get("message", "").lower() == "success":
                        ip_group_items = res_json.get("results", [])
                        logger.info(f"成功获取到 {len(ip_group_items)} 条IP分组记录 (新版)")
                        return ip_group_items
                    else:
                        err_msg = res_json.get("message", "获取IP分组列表API未返回成功或指定错误信息")
                        logger.error(f"获取IP分组列表失败 (新版)。响应: {res_json}, 错误: {err_msg}")
                        return []
                if not use_new_api and res_json:
                    if res_json.get("Result") == 30000 and res_json.get("ErrMsg", "").lower() == "success":
                        data = res_json.get("Data", {})
                        ip_group_items = data.get("data", [])
                        logger.info(f"成功获取到 {len(ip_group_items)} 条IP分组记录 (旧版)")
                        return ip_group_items
                    else:
                        err_msg = res_json.get("ErrMsg") or res_json.get("errmsg", "获取IP分组列表API未返回成功或指定错误信息")
                        logger.error(f"获取IP分组列表失败 (旧版)。响应: {res_json}, 错误: {err_msg}")
                        return []
                logger.error(f"获取IP分组列表失败，响应: {response.text[:200]}")
                return []
            except requests.exceptions.RequestException as e:
                logger.error(f"获取IP分组列表请求失败: {e}")
                return []
            except Exception as e:
                logger.error(f"获取IP分组列表过程中发生未知错误: {e}")
                return []
        except Exception as e:
            logger.error(f"获取IP分组列表异常: {str(e)}")
            return []
    
    def delete_ip_group(self, group_name: str, use_new_api: bool = True) -> Tuple[bool, Optional[str]]:
        """删除IP分组，兼容新旧接口"""
        try:
            session = self._create_session()
            token = self._login_ikuai(session)
            if not token:
                return False, "登录失败"
            delete_url = f"{self.ikuai_url}/Action/call"
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self.ikuai_url.rstrip('/'),
                'Referer': self.ikuai_url.rstrip('/') + '/'
            }
            if use_new_api:
                delete_data = {
                    "func_name": "route_object_ip",
                    "action": "del",
                    "param": {
                        "name": group_name
                    }
                }
            else:
                delete_data = {
                    "func_name": "ipgroup",
                    "action": "del",
                    "param": {
                        "group_name": group_name
                    }
                }
            try:
                logger.info(f"尝试删除IP分组: {group_name}")
                response = session.post(delete_url, data=json.dumps(delete_data), headers=request_headers, timeout=30)
                response.raise_for_status()
                try:
                    res_json = response.json()
                except Exception:
                    res_json = None
                if use_new_api and res_json:
                    if res_json.get("code") == 0 and res_json.get("message", "").lower() == "success":
                        logger.info(f"IP分组删除请求成功 (新版)。响应: {res_json}")
                        return True, None
                    err_msg = res_json.get("message", "删除IP分组API未返回成功或指定错误信息")
                    logger.error(f"IP分组删除失败 (新版)。响应: {res_json}, 错误: {err_msg}")
                    return False, f"路由器返回错误: {err_msg}"
                if not use_new_api and res_json:
                    if res_json.get("result") == 30000 and res_json.get("errmsg", "").lower() == "success":
                        logger.info(f"IP分组删除请求成功 (旧版)。响应: {res_json}")
                        return True, None
                    err_msg = res_json.get("errmsg") or res_json.get("ErrMsg", "删除IP分组API未返回成功或指定错误信息")
                    logger.error(f"IP分组删除失败 (旧版)。响应: {res_json}, 错误: {err_msg}")
                    return False, f"路由器返回错误: {err_msg}"
                response_text = response.text.strip().lower()
                if "success" in response_text or response_text == '"success"':
                    logger.info(f"IP分组删除请求发送成功。响应: {response_text}")
                    return True, None
                logger.error(f"IP分组删除失败，响应: {response.text[:200]}")
                return False, f"路由器返回非预期响应: {response_text[:100]}"
            except requests.exceptions.Timeout:
                logger.warning(f"删除IP分组请求超时。")
                return True, "请求超时，但IP分组可能已开始删除"
            except requests.exceptions.RequestException as e:
                logger.error(f"删除IP分组请求失败: {e}")
                return False, str(e)
            except Exception as e:
                logger.error(f"删除IP分组过程中发生未知错误: {e}")
                return False, str(e)
        except Exception as e:
            logger.error(f"删除IP分组异常: {str(e)}")
            return False, str(e)
    
    def sync_ip_groups_from_22tool(self, province: str = "", city: str = "", isp: str = "", 
                                  group_prefix: str = "22tool_", address_pool: bool = False) -> Tuple[bool, str]:
        """从IP段信息同步IP分组到爱快路由器"""
        try:
            logger.info("开始获取IP段信息...")
            # 获取IP段信息
            ip_blocks = self.get_ip_blocks_from_22tool(province, city, isp)
            if not ip_blocks:
                return False, "未获取到IP段信息"
            
            logger.info(f"成功获取到 {len(ip_blocks)} 个IP段，正在处理分组...")
            # 按省份、城市、运营商分组
            groups = {}
            for block in ip_blocks:
                key = f"{block['province']}_{block['city']}_{block['isp']}"
                if key not in groups:
                    # 如果分组前缀为空，直接使用"省份_城市_运营商"格式
                    if not group_prefix or group_prefix.strip() == "":
                        group_name = f"{block['province']}_{block['city']}_{block['isp']}"
                    else:
                        group_name = f"{group_prefix}{block['province']}_{block['city']}_{block['isp']}"
                    
                    groups[key] = {
                        'name': group_name,
                        'ips': [],
                        'province': block['province'],
                        'city': block['city'],
                        'isp': block['isp']
                    }
                
                # 生成完整的IP范围
                ip_start = block['ip_start']
                ip_end = block['ip_end']
                
                # 直接使用IP范围格式：IP开始-IP结束
                ip_range = f"{ip_start}-{ip_end}"
                groups[key]['ips'].append(ip_range)
                logger.info(f"为分组 {group_name} 添加了IP范围: {ip_range}")
            
            logger.info(f"分组处理完成，共 {len(groups)} 个分组，开始创建IP分组...")
            # 创建IP分组
            success_count = 0
            total_count = len(groups)
            
            for i, group_info in enumerate(groups.values(), 1):
                logger.info(f"正在创建第 {i}/{total_count} 个分组: {group_info['name']}")
                success, error = self.create_ip_group(
                    group_info['name'], 
                    group_info['ips'], 
                    address_pool
                )
                if success:
                    success_count += 1
                    logger.info(f"分组 {group_info['name']} 创建成功")
                else:
                    logger.warning(f"创建分组 {group_info['name']} 失败: {error}")
            
            message = f"同步完成: 成功 {success_count}/{total_count} 个分组"
            logger.info(message)
            return True, message
            
        except Exception as e:
            error_msg = f"同步IP分组失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def ip_to_cidr(self, ip_start: str, ip_end: str) -> List[str]:
        """将IP范围转换为CIDR格式"""
        try:
            def ip_to_int(ip):
                parts = ip.split('.')
                return sum(int(part) << (24 - 8 * i) for i, part in enumerate(parts))
            
            def int_to_ip(ip_int):
                return '.'.join(str((ip_int >> (24 - 8 * i)) & 255) for i in range(4))
            
            start_int = ip_to_int(ip_start)
            end_int = ip_to_int(ip_end)
            
            if start_int > end_int:
                # 交换顺序
                start_int, end_int = end_int, start_int
            
            cidrs = []
            while start_int <= end_int:
                # 找到最大的网络掩码
                max_size = 32
                while max_size > 0:
                    network_size = 2 ** (32 - max_size)
                    network_start = start_int & ~(network_size - 1)
                    if network_start != start_int:
                        max_size += 1
                        break
                    if start_int + network_size - 1 > end_int:
                        max_size += 1
                        break
                    max_size -= 1
                
                network_size = 2 ** (32 - max_size)
                network_end = start_int + network_size - 1
                
                if network_end > end_int:
                    network_end = end_int
                
                cidr = f"{int_to_ip(start_int)}/{max_size}"
                cidrs.append(cidr)
                
                start_int = network_end + 1
            
            logger.info(f"IP范围 {ip_start}-{ip_end} 转换为 {len(cidrs)} 个CIDR: {cidrs}")
            return cidrs
            
        except Exception as e:
            logger.error(f"IP范围转换CIDR失败: {str(e)}")
            # 如果转换失败，返回单个IP地址
            return [ip_start]

    def test_create_simple_ip_group(self) -> Tuple[bool, Optional[str]]:
        """测试创建最简单的IP分组"""
        try:
            session = self._create_session()
            token = self._login_ikuai(session)
            if not token:
                return False, "登录失败"
            
            # 使用与ikuai-bypass相同的JSON格式
            create_url = f"{self.ikuai_url}/Action/call"
            
            # 尝试最简单的IP分组
            test_data = {
                "func_name": "ipgroup",  # 注意：不是 "ip_group"
                "action": "add", 
                "param": {
                    "group_name": "test_group",
                    "addr_pool": "192.168.1.1",  # 使用逗号分隔的IP列表
                    "newRow": True,
                    "type": 0
                }
            }
            
            try:
                logger.info(f"尝试创建测试IP分组...")
                request_headers = {
                    'Content-Type': 'application/json',
                    'Accept': '*/*',
                    'Origin': self.ikuai_url.rstrip('/'),
                    'Referer': self.ikuai_url.rstrip('/') + '/'
                }
                
                response = session.post(create_url, data=json.dumps(test_data), headers=request_headers, timeout=30)
                response.raise_for_status()
                response_text = response.text.strip().lower()
                
                if "success" in response_text or response_text == '"success"':
                    logger.info(f"测试IP分组创建成功。响应: {response_text}")
                    return True, None
                
                try:
                    res_json = response.json()
                    if res_json.get("result") == 30000 and res_json.get("errmsg", "").lower() == "success":
                        logger.info(f"测试IP分组创建成功 (JSON)。响应: {res_json}")
                        return True, None
                    
                    err_msg = res_json.get("errmsg")
                    if not err_msg:
                        err_msg = res_json.get("ErrMsg", "测试IP分组API未返回成功或指定错误信息")

                    logger.error(f"测试IP分组创建失败 (JSON)。响应: {res_json}, 错误: {err_msg}")
                    return False, f"路由器返回错误: {err_msg}"
                except json.JSONDecodeError:
                    logger.error(f"测试IP分组创建失败，非JSON响应且不含 'success'。响应: {response_text}")
                    return False, f"路由器返回非预期响应: {response_text[:100]}"
                    
            except requests.exceptions.Timeout:
                logger.warning(f"测试IP分组创建请求超时。")
                return True, "请求超时，但IP分组可能已开始创建"
            except requests.exceptions.RequestException as e:
                logger.error(f"测试IP分组创建请求失败: {e}")
                return False, str(e)
            except Exception as e:
                logger.error(f"测试IP分组创建过程中发生未知错误: {e}")
                return False, str(e)
                
        except Exception as e:
            logger.error(f"测试IP分组创建异常: {str(e)}")
            return False, str(e)
