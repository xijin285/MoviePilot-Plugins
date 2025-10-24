import hashlib
import json
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import Dict, List, Optional
from app.log import logger


class IkuaiDNSManager:
    def __init__(self):
        self._ikuai_url: str = ""
        self._ikuai_username: str = ""
        self._ikuai_password: str = ""
        self._session = None
        self._logged_in = False
        self._last_sync_success: bool = False  # 最后一次同步是否成功的标记

    def init_config(self, url: str, username: str, password: str):
        """初始化配置"""
        self._ikuai_url = url.rstrip("/")
        self._ikuai_username = username
        self._ikuai_password = password
        self._session = self._create_session()
        self._logged_in = False

    def _create_session(self) -> requests.Session:
        """创建带重试机制的会话"""
        session = requests.Session()
        retries = Retry(total=3,
                       backoff_factor=0.5,
                       status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session

    def _get_login_params(self) -> Dict:
        """生成登录参数"""
        password_md5 = hashlib.md5(self._ikuai_password.encode('utf-8')).hexdigest()
        return {
            "username": self._ikuai_username,
            "passwd": password_md5
        }

    def login(self) -> bool:
        """登录爱快路由器"""
        if self._logged_in:
            return True

        try:
            url = f"{self._ikuai_url}/Action/login"
            headers = {'Content-Type': 'application/json'}
            params = self._get_login_params()
            logger.debug(f"尝试登录爱快路由器，URL: {url}")
            
            response = self._session.post(url, 
                                       data=json.dumps(params), 
                                       headers=headers, 
                                       timeout=10)
            response.raise_for_status()
            
            try:
                data = response.json()
                if data.get("Result", 0) == 10000:
                    self._logged_in = True
                    logger.info("爱快路由器登录成功")
                    return True
                else:
                    logger.error(f"爱快路由器登录失败: {data}")
                    return False
            except json.JSONDecodeError:
                logger.error("爱快路由器返回的不是有效的JSON响应")
                return False

        except Exception as e:
            logger.error(f"爱快路由器登录异常: {str(e)}")
            return False

    def sync_hosts_to_dns(self, hosts: List[Dict[str, str]]) -> bool:
        """
        将 hosts 同步到爱快路由器的 DNS 服务器
        :param hosts: 列表，每个元素为字典，包含 domain 和 ip
        :return: 是否同步成功
        """
        self._last_sync_success = False  # 重置同步状态
        if not self.login():
            return False

        try:
            success_count = 0
            for host in hosts:
                try:
                    domain = host['domain']
                    ip = host['ip']
                    
                    data = {
                        "func_name": "dns",
                        "action": "add",
                        "param": {
                            "comment": "PT云盾优选",
                            "dns_addr": ip,
                            "domain": domain,
                            "enabled": "yes",
                            "parse_type": "ipv4",
                            "dns_addr_ipv4": ip,
                            "dns_addr_ipv6": "",
                            "dns_addr_proxy": "",
                            "src_addr": ""
                        }
                    }
                    
                    url = f"{self._ikuai_url}/Action/call"
                    headers = {
                        'Content-Type': 'application/json;charset=UTF-8',
                        'Accept': 'application/json, text/plain, */*',
                        'Origin': self._ikuai_url,
                        'Referer': f"{self._ikuai_url}/"
                    }
                    
                    response = self._session.post(
                        url,
                        json=data,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        # 清理响应文本，只保留JSON部分
                        json_text = response.text.split('\n')[0].strip()
                        try:
                            result = json.loads(json_text)
                            if result.get("Result") == 30000:
                                logger.info(f"成功添加DNS记录: {domain} -> {ip}")
                                success_count += 1
                            else:
                                logger.error(f"添加DNS记录失败: {domain} -> {ip}, 错误: {result}")
                        except json.JSONDecodeError:
                            # 如果响应文本包含成功信息，也认为是成功的
                            if "Success" in response.text and "Result\":30000" in response.text:
                                logger.info(f"成功添加DNS记录: {domain} -> {ip}")
                                success_count += 1
                            else:
                                logger.error(f"解析DNS记录响应失败: {response.text}")
                except Exception as e:
                    logger.error(f"添加单条DNS记录异常: {str(e)}")
                    continue
            
            # 如果至少有一条记录添加成功，就认为同步成功
            self._last_sync_success = success_count > 0
            if self._last_sync_success:
                logger.info(f"DNS同步完成: 成功{success_count}/{len(hosts)}条记录")
            else:
                logger.error("DNS同步失败: 没有成功添加任何记录")
            
            return self._last_sync_success
            
        except Exception as e:
            logger.error(f"同步 hosts 到爱快路由器 DNS 时发生错误: {str(e)}")
            return False
            dns_records = []
            for index, host in enumerate(hosts):
                dns_records.append({
                    "id": str(index + 1),
                    "domain": host["domain"],
                    "ip": host["ip"],
                    "enable": "yes",
                    "comment": "由 PT云盾优选 自动同步"
                })

            # 获取现有的 DNS 记录
            existing_records = self._get_dns_records()
            
            # 合并记录（保留非 PT云盾优选 添加的记录）
            merged_records = self._merge_dns_records(existing_records, dns_records)

            # 更新 DNS 记录
            url = f"{self._ikuai_url}/Action/call"
            headers = {'Content-Type': 'application/json'}
            payload = {
                "func_name": "dns",  # 修改为正确的功能名
                "action": "edit",
                "param": {
                    "name": "dns_server",  # 指定DNS服务器配置
                    "data": merged_records
                }
            }
            
            response = self._session.post(url, 
                                       data=json.dumps(payload), 
                                       headers=headers, 
                                       timeout=10)
            response.raise_for_status()
            data = response.json()

            # 检查API响应
            self._last_sync_success = data.get("Result", 0) == 10000  # 爱快API成功返回码是10000
            
            if self._last_sync_success:
                logger.info(f"成功同步 {len(hosts)} 条记录到爱快路由器 DNS")
                return True
            else:
                logger.error(f"同步到爱快路由器 DNS 失败: {data.get('ErrMsg', '未知错误')}")
                return False

        except Exception as e:
            logger.error(f"同步 hosts 到爱快路由器 DNS 时发生错误: {str(e)}")
            return False

    def _get_dns_records(self) -> List[Dict]:
        """获取现有的 DNS 记录"""
        try:
            url = f"{self._ikuai_url}/Action/call"
            headers = {'Content-Type': 'application/json'}
            payload = {
                "func_name": "dns",  # 修改为正确的功能名
                "action": "show",
                "param": {
                    "TYPE": "dns_server",  # 指定要获取的是DNS服务器记录
                    "limit": "0,100",
                    "ORDER_BY": "",
                    "ORDER": ""
                }
            }
            
            response = self._session.post(url, 
                                       data=json.dumps(payload), 
                                       headers=headers, 
                                       timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("Result", 0) == 30000:
                records = data.get("Data", {}).get("data", [])
                logger.debug(f"成功获取到 {len(records)} 条 DNS 记录")
                return records
            
            logger.error(f"获取 DNS 记录失败: {data.get('ErrMsg', '未知错误')}")
            return []

        except Exception as e:
            logger.error(f"获取 DNS 记录失败: {str(e)}")
            return []

    def _merge_dns_records(self, existing: List[Dict], new: List[Dict]) -> List[Dict]:
        """
        合并 DNS 记录，保留非 PT云盾优选 添加的记录
        """
        # 保留非 PT云盾优选 添加的记录
        preserved = [
            record for record in existing
            if not record.get("comment", "").startswith("由 PT云盾优选 自动同步")
        ]
        
        # 生成新的记录列表，重新编号
        merged = preserved + new
        for i, record in enumerate(merged):
            record["id"] = str(i + 1)
            
        return merged