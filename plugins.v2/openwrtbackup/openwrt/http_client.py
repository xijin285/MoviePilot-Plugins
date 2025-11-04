"""
OpenWrt HTTP客户端模块
负责通过LuCI Web API连接和操作OpenWrt路由器
"""
import re
import time
import requests
from typing import Tuple, Optional, Dict
from urllib.parse import urljoin
from app.log import logger


class OpenWrtHTTPClient:
    """OpenWrt HTTP客户端"""
    
    def __init__(self, plugin_instance):
        """
        初始化OpenWrt HTTP客户端
        :param plugin_instance: OpenWrtBackup插件实例
        """
        self.plugin = plugin_instance
        self.plugin_name = plugin_instance.plugin_name
        self.session = None
        self.base_url = None
        self.auth_token = None
        
    def _get_base_url(self) -> str:
        """获取基础URL"""
        host = self.plugin._openwrt_host.strip()
        # 如果host不包含协议，添加http://
        if not host.startswith(('http://', 'https://')):
            host = f"http://{host}"
        # 移除末尾的斜杠
        base_url = host.rstrip('/')
        logger.debug(f"{self.plugin_name} 基础URL: {base_url}")
        return base_url
    
    def login(self) -> Tuple[bool, Optional[str]]:
        """
        登录OpenWrt，获取ubus session ID
        返回: (成功, 错误信息)
        """
        try:
            self.base_url = self._get_base_url()
            username = self.plugin._openwrt_username
            password = self.plugin._openwrt_password
            
            # 创建session（参考iKuai实现，添加重试机制）
            self.session = requests.Session()
            self.session.verify = False  # 忽略SSL证书验证
            self.session.timeout = 5
            
            # 添加重试机制（参考iKuai）
            try:
                from urllib3.util.retry import Retry
                from requests.adapters import HTTPAdapter
                retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
                self.session.mount('http://', HTTPAdapter(max_retries=retries))
                self.session.mount('https://', HTTPAdapter(max_retries=retries))
            except ImportError:
                pass  # 如果urllib3版本不支持，忽略
            
            # 统一User-Agent（参考iKuai，使用浏览器User-Agent）
            browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
            self.session.headers.update({"User-Agent": browser_user_agent})
            
            # 使用ubus API登录
            ubus_url = urljoin(self.base_url, '/ubus')
            
            # 首先尝试ubus session.login
            login_payload = {
                "jsonrpc": "2.0",
                "id": int(time.time()),
                "method": "call",
                "params": [
                    "00000000000000000000000000000000",  # ubus session ID (0表示未认证)
                    "session",
                    "login",
                    {
                        "username": username,
                        "password": password
                    }
                ]
            }
            
            try:
                logger.debug(f"{self.plugin_name} 尝试ubus登录，URL: {ubus_url}")
                response = self.session.post(ubus_url, json=login_payload, timeout=5)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data.get('result'):
                            # ubus返回格式可能是:
                            # 1. [0, {"ubus_rpc_session": "..."}] - 状态码0表示成功，第二个元素是session
                            # 2. [{"ubus_rpc_session": "..."}] - 直接是session字典
                            # 3. {"ubus_rpc_session": "..."} - 直接是字典
                            # 4. 数字 - 0表示失败，1表示成功
                            result = data['result']
                            
                            # 处理返回格式
                            if isinstance(result, list):
                                if len(result) == 0:
                                    logger.error(f"{self.plugin_name} ubus登录返回空列表")
                                    return False, "ubus登录返回空列表"
                                
                                # 如果第一个元素是数字（状态码），第二个元素应该是session字典
                                if len(result) >= 2 and isinstance(result[0], (int, float)):
                                    if result[0] == 0:  # 0表示成功
                                        result = result[1]  # 取第二个元素（session字典）
                                    else:
                                        logger.error(f"{self.plugin_name} ubus登录返回错误状态码: {result[0]}")
                                        return False, f"ubus登录失败，状态码: {result[0]}"
                                else:
                                    # 否则尝试找字典类型的元素
                                    found_dict = False
                                    for item in result:
                                        if isinstance(item, dict) and item.get('ubus_rpc_session'):
                                            result = item
                                            found_dict = True
                                            break
                                    if not found_dict:
                                        # 如果只有一个元素，尝试取第一个
                                        if len(result) == 1:
                                            result = result[0]
                                        else:
                                            logger.error(f"{self.plugin_name} ubus登录返回列表但未找到session字典")
                                            return False, "ubus登录返回格式错误"
                            
                            # 如果返回的是数字（单独的数字，不是列表中的状态码）
                            if isinstance(result, (int, float)):
                                logger.error(f"{self.plugin_name} ubus登录返回数字: {result}")
                                return False, f"ubus登录失败，返回码: {result}"
                            
                            # 如果是字典，检查是否有session
                            if isinstance(result, dict):
                                if result.get('ubus_rpc_session'):
                                    self.auth_token = result['ubus_rpc_session']
                                    logger.debug(f"{self.plugin_name} web登录成功")
                                    return True, None
                                else:
                                    logger.error(f"{self.plugin_name} ubus登录返回字典但无session: {result}")
                                    return False, "ubus登录返回数据中缺少session"
                            else:
                                # 其他格式
                                logger.error(f"{self.plugin_name} ubus登录返回格式异常: {result} (type: {type(result)})")
                                return False, f"ubus登录返回格式错误: {type(result)}"
                        else:
                            error = data.get('error')
                            if error:
                                error_msg = error.get('message', '未知错误')
                                error_code = error.get('code', 0)
                                logger.error(f"{self.plugin_name} ubus登录错误: {error_msg} (code: {error_code})")
                                if error_code in [-32002, -1] or 'Invalid' in error_msg or 'invalid' in error_msg.lower() or 'denied' in error_msg.lower():
                                    return False, "登录失败：用户名或密码错误"
                                return False, f"ubus登录失败: {error_msg}"
                            else:
                                # 无错误但无结果
                                logger.error(f"{self.plugin_name} ubus登录无结果")
                                return False, "ubus登录无响应结果"
                    except ValueError as e:
                        # JSON解析失败，可能是非JSON响应
                        logger.error(f"{self.plugin_name} ubus响应非JSON格式: {response.text[:100]}")
                        return False, f"ubus响应格式错误: {str(e)}"
                else:
                    # HTTP状态码不是200
                    logger.error(f"{self.plugin_name} ubus HTTP状态码: {response.status_code}")
                    return False, f"ubus登录失败，HTTP状态码: {response.status_code}"
            except requests.exceptions.Timeout:
                return False, "连接超时，请检查OpenWrt地址和网络连接"
            except requests.exceptions.ConnectionError:
                return False, "无法连接到OpenWrt路由器，请检查地址和端口"
            except Exception as e:
                logger.error(f"{self.plugin_name} ubus登录异常: {e}")
                return False, f"ubus登录失败: {str(e)}"
                
        except Exception as e:
            logger.error(f"{self.plugin_name} HTTP登录异常: {e}")
            return False, f"登录失败: {str(e)}"
    
    def _call_rpc(self, namespace: str, method: str, params: dict = None) -> Optional[Dict]:
        """
        调用ubus RPC接口
        :param namespace: ubus命名空间，如 'system', 'network', 'file'
        :param method: 方法名，如 'info', 'exec', 'read'
        :param params: 方法参数
        :return: RPC响应数据
        """
        if not self.session:
            return None
        
        try:
            ubus_url = urljoin(self.base_url, '/ubus')
            
            # 使用获取的session ID，如果没有则使用0
            session_id = self.auth_token or "00000000000000000000000000000000"
            
            payload = {
                "jsonrpc": "2.0",
                "id": int(time.time()),
                "method": "call",
                "params": [
                    session_id,
                    namespace,
                    method,
                    params or {}
                ]
            }
            
            response = self.session.post(ubus_url, json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('result'):
                    result = data['result']
                    # ubus返回格式可能是:
                    # 1. [0, {...}] - 状态码0表示成功，第二个元素是实际数据
                    # 2. [1, {...}] - 状态码非0表示错误
                    # 3. [{...}] - 直接是数据字典
                    # 4. {...} - 直接是字典
                    if isinstance(result, list):
                        if len(result) >= 2 and isinstance(result[0], (int, float)):
                            # 第一个元素是状态码
                            if result[0] == 0:
                                # 状态码0表示成功，返回第二个元素
                                return result[1] if isinstance(result[1], dict) else result
                            else:
                                # 状态码非0表示错误（可能是认证错误）
                                # 如果是认证错误（通常状态码为-32002或-1），清除session并返回None
                                if result[0] in [-32002, -1, 6]:
                                    logger.debug(f"{self.plugin_name} 检测到认证错误（状态码{result[0]}），清除session")
                                    self.auth_token = None
                                    self.session = None
                                logger.warning(f"{self.plugin_name} RPC返回错误状态码: {result[0]}")
                                return None
                        elif len(result) > 0:
                            # 如果只有一个元素或第一个元素不是状态码，返回第一个元素
                            return result[0]
                        else:
                            return None
                    else:
                        # 直接返回结果
                        return result
                else:
                    error = data.get('error')
                    if error:
                        error_code = error.get('code', 0)
                        error_msg = error.get('message', '未知错误')
                        # 如果是认证错误，清除session
                        if error_code in [-32002, -1, 6] or 'Access denied' in error_msg or 'Invalid session' in error_msg:
                            logger.debug(f"{self.plugin_name} 检测到认证错误（code {error_code}），清除session")
                            self.auth_token = None
                            self.session = None
                        logger.warning(f"{self.plugin_name} RPC错误: {error_msg}")
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} RPC调用失败: {e}")
            return None
    
    def download_backup_direct(self, backup_filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        通过cgi-backup接口直接下载备份文件到本地临时目录
        :param backup_filename: 备份文件名
        :return: (成功, 错误信息, 本地临时文件路径)
        """
        if not self.session:
            return False, "未登录", None
        
        if not self.auth_token:
            return False, "未获取ubus session", None
        
        try:
            import tempfile
            from pathlib import Path
            
            # 创建临时目录
            temp_dir = Path(tempfile.gettempdir()) / "openwrt_backup"
            temp_dir.mkdir(parents=True, exist_ok=True)
            local_temp_path = temp_dir / backup_filename
            
            # 使用cgi-backup接口下载备份（使用ubus session作为sessionid）
            cgi_backup_url = urljoin(self.base_url, '/cgi-bin/cgi-backup')
            logger.info(f"{self.plugin_name} 通过官方接口下载备份")
            
            # 使用成功的参数组合
            backup_params = {'sessionid': self.auth_token, 'backup': '1'}
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': urljoin(self.base_url, '/cgi-bin/luci/admin/system/flash'),
                'Origin': self.base_url
            }
            
            response = self.session.post(
                cgi_backup_url,
                data=backup_params,
                headers=headers,
                timeout=300,
                stream=True,
                allow_redirects=True
            )
            
            logger.debug(f"{self.plugin_name} cgi-backup响应: 状态码={response.status_code}, Content-Type={response.headers.get('Content-Type', '')}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '').lower()
                content_disposition = response.headers.get('Content-Disposition', '').lower()
                
                # 检查是否是备份文件
                is_backup_file = (
                    'application/octet-stream' in content_type or 
                    'application/x-tar' in content_type or 
                    'application/gzip' in content_type or
                    'application/x-targz' in content_type or
                    'attachment' in content_disposition or
                    '.tar.gz' in content_disposition or
                    (response.headers.get('Content-Length') and int(response.headers.get('Content-Length', '0')) > 1000)
                )
                
                if is_backup_file:
                    # 下载到本地临时文件
                    with open(local_temp_path, 'wb') as f:
                        file_size = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                file_size += len(chunk)
                    
                    # 验证文件大小
                    if file_size > 1000:  # 至少1KB
                        logger.info(f"{self.plugin_name} 成功通过官方接口下载备份文件: {backup_filename}, 大小: {file_size} 字节")
                        return True, None, str(local_temp_path)
                    else:
                        logger.warning(f"{self.plugin_name} 下载的文件太小: {file_size} 字节")
                        if local_temp_path.exists():
                            local_temp_path.unlink()
                        return False, f"下载的文件太小: {file_size} 字节", None
                else:
                    return False, f"响应不是备份文件格式，Content-Type: {content_type}", None
            else:
                return False, f"cgi-backup接口返回错误状态码: {response.status_code}", None
            
        except Exception as e:
            logger.error(f"{self.plugin_name} 下载备份失败: {e}")
            return False, f"下载备份失败: {str(e)}", None
    
    def close(self):
        """关闭连接"""
        if self.session:
            try:
                self.session.close()
            except:
                pass
            self.session = None
            self.auth_token = None

