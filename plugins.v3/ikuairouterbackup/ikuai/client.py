"""爱快路由器客户端"""
import hashlib
import json
import re
import time
import urllib3
from typing import Optional, Dict, List, Tuple
from urllib.parse import urljoin, quote

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# 禁用爱快路由器自签名证书的InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from app.log import logger
from .client_v4 import IkuaiClientV4


class IkuaiClient:
    """爱快路由器客户端（v3 密码会话 + v4 API 令牌混合）"""
    
    def __init__(self, url: str, username: str, password: str, plugin_name: str = "",
                 auth_mode: str = "auto", api_token: str = ""):
        """
        初始化爱快客户端
        
        认证方式：
        - auth_mode="password"：强制用 v3 账号密码（/Action/call + /Action/download），全链路密码。
        - auth_mode="token"   ：强制用 v4 API 令牌（/api/v4.0 Bearer）做备份控制，
                               备份文件下载回退 v3 密码会话（需同时配置密码）。
        - auth_mode="auto"    ：自动检测。若提供了 api_token 且令牌有效则按 token 模式，
                               否则回退 password 模式（3.x 用账号密码，4.x 自动切令牌）。
        
        :param url: 爱快路由器URL
        :param username: 用户名
        :param password: 密码
        :param plugin_name: 插件名称
        :param auth_mode: 认证方式（auto/password/token）
        :param api_token: 爱快个人 API 令牌（4.x）
        """
        self.url = url
        self.username = username
        self.password = password
        self.plugin_name = plugin_name
        self.auth_mode = (auth_mode or "auto").lower()
        self.api_token = (api_token or "").strip()
        self.session = None
        self._v4 = None
        self._v4_active = False  # 令牌模式是否已生效（auto 检测后置位）
        self._v4_login_attempted = False
        # 仅当配置了令牌且认证方式允许时，初始化 v4 客户端
        if self.api_token and self.auth_mode in ("token", "auto"):
            self._v4 = IkuaiClientV4(self.url, self.api_token, self.plugin_name)
        self._init_session()
    
    def _init_session(self):
        """初始化Session"""
        self.session = requests.Session()
        # 爱快4.x强制HTTPS登录且使用自签名证书，禁用SSL证书验证
        self.session.verify = False
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        # 统一的User-Agent
        browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
        self.session.headers.update({"User-Agent": browser_user_agent})
    
    def _use_v4(self) -> bool:
        """是否应使用 v4 令牌进行备份控制面操作"""
        if self._v4 is None:
            return False
        if self.auth_mode == "token":
            return True
        if self.auth_mode == "auto":
            return self._v4_active
        return False

    def login(self) -> bool:
        """
        登录爱快路由器（自动适配认证方式）
        
        :return: 是否登录成功
        """
        # token 模式（或 auto 且配置了令牌）：先校验 v4 令牌
        if self._v4 is not None and self.auth_mode in ("token", "auto"):
            ok = self._v4.validate()
            if ok:
                self._v4_active = True
                logger.info(f"{self.plugin_name} v4 API 令牌校验通过（备份控制走令牌）。")
                # 令牌模式下仍需密码会话用于"下载"，建会话失败仅告警，不阻塞控制面
                try:
                    self._login_v3_password()
                except Exception as e:
                    logger.warning(f"{self.plugin_name} 密码会话创建失败（影响备份文件下载）: {e}")
                return True
            elif self.auth_mode == "token":
                logger.error(f"{self.plugin_name} v4 API 令牌无效或权限不足。")
                return False
            else:
                # auto 模式下令牌无效 → 回退 v3 账号密码
                logger.warning(f"{self.plugin_name} v4 API 令牌无效，回退到账号密码模式。")
                self._v4_active = False
                return self._login_v3_password()

        # password 模式（或 auto 无令牌）
        return self._login_v3_password()

    def _login_v3_password(self) -> bool:
        """
        v3 账号密码登录，获取会话 sess_key（供 /Action/call 与 /Action/download 使用）
        
        :return: 是否登录成功
        """
        login_url = urljoin(self.url, "/Action/login")
        password_md5 = hashlib.md5(self.password.encode('utf-8')).hexdigest()
        login_data = {"username": self.username, "passwd": password_md5}
        
        try:
            logger.debug(f"{self.plugin_name} 尝试登录到 {self.url}...")
            response = self.session.post(login_url, data=json.dumps(login_data), 
                                        headers={'Content-Type': 'application/json'}, 
                                        timeout=10)
            response.raise_for_status()
            
            cookies = response.cookies
            sess_key_value = cookies.get("sess_key")
            if sess_key_value:
                logger.debug(f"{self.plugin_name} 登录成功，获取到 sess_key。")
                cookie_string = f"username={quote(self.username)}; sess_key={sess_key_value}; login=1"
                self.session.headers.update({"Cookie": cookie_string})
                return True
            
            set_cookie_header = response.headers.get('Set-Cookie')
            if set_cookie_header:
                match = re.search(r'sess_key=([^;]+)', set_cookie_header)
                if match:
                    logger.debug(f"{self.plugin_name} 登录成功，从Set-Cookie头获取到 sess_key。")
                    cookie_string = f"username={quote(self.username)}; sess_key={match.group(1)}; login=1"
                    self.session.headers.update({"Cookie": cookie_string})
                    return True
            
            logger.error(f"{self.plugin_name} 登录成功但未能从Cookie或头部提取 sess_key。响应: {response.text[:200]}")
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 登录请求失败: {e}")
            return False
        except Exception as e:
            logger.error(f"{self.plugin_name} 登录过程中发生未知错误: {e}")
            return False
    
    def create_backup(self) -> Tuple[bool, Optional[str]]:
        """
        在路由器上创建备份
        
        :return: (是否成功, 错误信息)
        """
        # v4 令牌模式：用 /api/v4.0/system/backup POST 创建
        if self._use_v4():
            result = self._v4.create_backup()
            if result and not result.get("_error"):
                logger.info(f"{self.plugin_name} v4 备份创建请求成功。响应: {result}")
                return True, None
            err = result.get("message", "创建备份失败") if isinstance(result, dict) else "创建备份失败"
            logger.error(f"{self.plugin_name} v4 备份创建失败: {result}")
            return False, f"路由器返回错误: {err}"

        create_url = urljoin(self.url, "/Action/call")
        backup_data = {"func_name": "backup", "action": "create", "param": {}}
        
        try:
            logger.info(f"{self.plugin_name} 尝试在 {self.url} 创建新备份...")
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self.url.rstrip('/'),
                'Referer': self.url.rstrip('/') + '/'
            }
            response = self.session.post(create_url, data=json.dumps(backup_data), 
                                       headers=request_headers, timeout=30)
            response.raise_for_status()
            
            response_text = response.text.strip().lower()
            if "success" in response_text or response_text == '"success"':
                logger.info(f"{self.plugin_name} 备份创建请求发送成功。响应: {response_text}")
                return True, None
            
            try:
                res_json = response.json()
                if res_json.get("result") == 30000 and res_json.get("errmsg", "").lower() == "success":
                    logger.info(f"{self.plugin_name} 备份创建请求成功 (JSON)。响应: {res_json}")
                    return True, None
                
                err_msg = res_json.get("errmsg")
                if not err_msg:
                    err_msg = res_json.get("ErrMsg", "创建备份API未返回成功或指定错误信息")
                
                logger.error(f"{self.plugin_name} 备份创建失败 (JSON)。响应: {res_json}, 错误: {err_msg}")
                return False, f"路由器返回错误: {err_msg}"
                
            except json.JSONDecodeError:
                logger.error(f"{self.plugin_name} 备份创建失败，非JSON响应且不含 'success'。响应: {response_text}")
                return False, f"路由器返回非预期响应: {response_text[:100]}"
                
        except requests.exceptions.Timeout:
            logger.warning(f"{self.plugin_name} 创建备份请求超时。备份可能仍在后台进行。")
            return True, "请求超时，但备份可能已开始创建"
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 创建备份请求失败: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"{self.plugin_name} 创建备份过程中发生未知错误: {e}")
            return False, str(e)
    
    def get_backup_list(self) -> Optional[List[Dict]]:
        """
        获取备份文件列表，自动兼容4.x及老版本API
        :return: 备份列表或None
        """
        # v4 令牌模式：用 /api/v4.0/system/backup GET 获取列表
        if self._use_v4():
            return self._v4.get_backup_list()

        list_url = urljoin(self.url, "/Action/call")
        # 新版优先用 TYPE=backup_info 获取 filename
        list_data_new = {"func_name": "backup", "action": "show", "param": {"TYPE": "backup_info"}}
        list_data_old = {"func_name": "backup", "action": "show", "param": {}}  # 老版本无TYPE参数
        request_headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Origin': self.url.rstrip('/'),
            'Referer': self.url.rstrip('/') + '/'
        }
        try:
            logger.info(f"{self.plugin_name} 尝试从 {self.url} 获取备份列表...")
            response = self.session.post(list_url, data=json.dumps(list_data_new), headers=request_headers, timeout=15)
            response.raise_for_status()
            res_json = response.json()
            # 新版API成功
            if res_json.get("code") == 0 and str(res_json.get("message", "")).lower() in ["success", "ok", "成功"]:
                results = res_json.get("results", {})
                backup_info = results.get("backup_info", [])
                if isinstance(backup_info, list) and backup_info:
                    logger.info(f"{self.plugin_name} 成功获取到 {len(backup_info)} 条备份记录。")
                    logger.debug(f"{self.plugin_name} 备份记录示例: {backup_info[0]}")
                    return backup_info
                else:
                    logger.warning(f"{self.plugin_name} 获取备份列表成功，但 backup_info 为空或格式不正确。results content: {results}")
                    return []
            # 新版API失败，且Result=30006或unknown TYPE，自动切换老版本
            if (
                (res_json.get("Result") == 30006 and "unknown TYPE" in res_json.get("ErrMsg", "")) or
                ("unknown TYPE" in str(res_json))
            ):
                logger.warning(f"{self.plugin_name} 检测到老版本API（unknown TYPE），尝试兼容老版本参数...")
                response_old = self.session.post(list_url, data=json.dumps(list_data_old), headers=request_headers, timeout=15)
                response_old.raise_for_status()
                res_json_old = response_old.json()
                # 老版本格式1
                if res_json_old.get("Result") == 30000 and res_json_old.get("ErrMsg", "").lower() == "success":
                    data = res_json_old.get("Data", [])
                    # 兼容Data为dict且含data键的情况
                    if isinstance(data, list) and data:
                        logger.info(f"{self.plugin_name} (老版本) 成功获取到 {len(data)} 条备份记录。")
                        logger.debug(f"{self.plugin_name} (老版本) 备份记录示例: {data[0]}")
                        return data
                    elif isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                        logger.info(f"{self.plugin_name} (老版本) 成功获取到 {len(data['data'])} 条备份记录。")
                        # 自动补全 filename 字段，兼容后续处理
                        for item in data["data"]:
                            if isinstance(item, dict) and "name" in item and "filename" not in item:
                                item["filename"] = item["name"]
                        if data['data']:
                            logger.debug(f"{self.plugin_name} (老版本) 备份记录示例: {data['data'][0]}")
                        return data["data"]
                    else:
                        logger.warning(f"{self.plugin_name} (老版本) 获取备份列表成功，但Data格式不正确。Data: {data}")
                        return []
                # 老版本格式2
                elif res_json_old.get("code") == 0 and str(res_json_old.get("message", "")).lower() in ["success", "ok", "成功"]:
                    results = res_json_old.get("results", {})
                    if isinstance(results, list) and results:
                        logger.info(f"{self.plugin_name} (老版本) 成功获取到 {len(results)} 条备份记录。")
                        logger.debug(f"{self.plugin_name} (老版本) 备份记录示例: {results[0]}")
                        return results
                    else:
                        logger.warning(f"{self.plugin_name} (老版本) 获取备份列表成功，但results为空或格式不正确。results: {results}")
                        return []
                else:
                    err_msg = res_json_old.get("ErrMsg") or res_json_old.get("message") or "老版本获取列表API未返回成功或指定错误信息"
                    logger.error(f"{self.plugin_name} (老版本) 获取备份列表失败。响应: {res_json_old}, 错误: {err_msg}")
                    return None
            # 其它失败
            err_msg = res_json.get("message") or res_json.get("ErrMsg") or "获取列表API未返回成功或指定错误信息"
            logger.error(f"{self.plugin_name} 获取备份列表失败。响应: {res_json}, 错误: {err_msg}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 获取备份列表请求失败: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"{self.plugin_name} 获取备份列表响应非JSON格式: {getattr(e, 'response', None) or ''}")
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取备份列表过程中发生未知错误: {e}")
            return None
    
    def download_backup(self, router_filename: str, local_filepath: str) -> Tuple[bool, Optional[str]]:
        """
        下载备份文件（需 v3 密码会话；爱快4.x 官方网页端下载同样走此通道）
        
        :param router_filename: 路由器上的文件名
        :param local_filepath: 本地保存路径
        :return: (是否成功, 错误信息)
        """
        # 对齐官方网页端行为：下载前先触发 EXPORT（/Action/call），失败不阻塞下载
        try:
            export_url = urljoin(self.url, "/Action/call")
            export_payload = {"func_name": "backup", "action": "EXPORT", "param": {"srcfile": router_filename}}
            self.session.post(export_url, json=export_payload, timeout=15)
        except Exception as e:
            logger.debug(f"{self.plugin_name} 下载前 EXPORT 触发失败（忽略，继续直接下载）: {e}")

        safe_router_filename = quote(router_filename)
        download_url = urljoin(self.url, f"/Action/download?filename={safe_router_filename}")
        
        request_headers = {
            "Referer": self.url.rstrip('/') + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        }
        
        logger.info(f"{self.plugin_name} 尝试下载备份文件 {router_filename} 从 {download_url}, 保存到 {local_filepath}...")
        
        try:
            with self.session.get(download_url, stream=True, timeout=300, headers=request_headers) as r:
                r.raise_for_status()
                with open(local_filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"{self.plugin_name} 文件 {router_filename} 下载完成，保存至 {local_filepath}")
                return True, None
                
        except requests.exceptions.HTTPError as e:
            error = f"HTTP错误 ({e.response.status_code}) 从 {download_url}: {e}"
            logger.warning(f"{self.plugin_name} 下载 {router_filename} 从 {download_url} 失败: {error}")
            return False, error
        except requests.exceptions.RequestException as e:
            error = f"请求错误从 {download_url}: {e}"
            logger.warning(f"{self.plugin_name} 下载 {router_filename} 从 {download_url} 失败: {error}")
            return False, error
        except Exception as e:
            error = f"未知错误从 {download_url}: {e}"
            logger.error(f"{self.plugin_name} 下载 {router_filename} 从 {download_url} 过程中发生未知错误: {error}")
            return False, error
    
    def restore_backup(self, filename: str, backup_content: bytes) -> Tuple[bool, Optional[str]]:
        """
        恢复备份
        
        :param filename: 备份文件名
        :param backup_content: 备份文件内容
        :return: (是否成功, 错误信息)
        """
        # 发送RESTORE请求
        restore_url = urljoin(self.url, "/Action/call")
        restore_payload = {
            "func_name": "backup",
            "action": "RESTORE",
            "param": {}
        }
        
        try:
            logger.info(f"{self.plugin_name} 发送恢复请求...")
            response = self.session.post(restore_url, json=restore_payload, timeout=30)
            response.raise_for_status()
            
            # 上传备份文件
            upload_url = urljoin(self.url, "/Action/upload")
            files = {
                'file': (filename, backup_content, 'application/octet-stream')
            }
            upload_response = self.session.post(upload_url, files=files, timeout=300)
            upload_response.raise_for_status()
            
            # 检查响应
            try:
                result = upload_response.json()
                # 新版格式: {'code': 0, 'message': 'Success'}
                if isinstance(result, dict) and result.get("code") == 0 and str(result.get("message", "")).lower() in ["success", "ok", "成功"]:
                    logger.info(f"{self.plugin_name} 恢复成功完成")
                    return True, None
                if (isinstance(result, dict) and result.get("Result") == 30000) or (isinstance(result, str) and "success" in result.lower()):
                    logger.info(f"{self.plugin_name} 恢复成功完成")
                    return True, None
                if "success" in str(result).lower():
                    logger.info(f"{self.plugin_name} 恢复成功完成 (宽松匹配)")
                    return True, None
                else:
                    error_msg = result.get("ErrMsg") or result.get("errmsg") or result.get("message", "恢复失败，未知错误")
                    return False, error_msg
            except json.JSONDecodeError:
                if "success" in upload_response.text.lower():
                    return True, None
                return False, f"恢复失败，响应解析错误: {upload_response.text[:200]}"
                
        except requests.exceptions.RequestException as e:
            return False, f"恢复请求失败: {str(e)}"
        except Exception as e:
            return False, f"恢复过程中发生错误: {str(e)}"
    
    def delete_backup(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        删除路由器上的备份文件
        
        :param filename: 文件名
        :return: (是否成功, 错误信息)
        """
        # v4 令牌模式：用 DELETE /api/v4.0/system/backup?srcfile=<文件名>
        if self._use_v4():
            result = self._v4.delete_backup(filename)
            if result and not result.get("_error"):
                logger.info(f"{self.plugin_name} v4 删除备份文件请求成功。响应: {result}")
                return True, None
            err = result.get("message", "删除备份失败") if isinstance(result, dict) else "删除备份失败"
            logger.error(f"{self.plugin_name} v4 删除备份文件失败: {result}")
            return False, f"路由器返回错误: {err}"

        delete_url = urljoin(self.url, "/Action/call")
        delete_data = {"func_name": "backup", "action": "delete", "param": {"srcfile": filename}}
        
        try:
            logger.info(f"{self.plugin_name} 尝试在 {self.url} 删除备份文件: {filename}...")
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self.url.rstrip('/'),
                'Referer': self.url.rstrip('/') + '/'
            }
            response = self.session.post(delete_url, data=json.dumps(delete_data), 
                                       headers=request_headers, timeout=30)
            response.raise_for_status()
            
            # 检查响应
            try:
                res_json = response.json()
                # 新版格式: {'code': 0, 'message': 'Success'}
                if res_json.get("code") == 0 and str(res_json.get("message", "")).lower() in ["success", "ok", "成功"]:
                    logger.info(f"{self.plugin_name} 删除备份文件请求成功 (新版JSON)。响应: {res_json}")
                    return True, None
                # 旧版格式: {'Result': 30000, 'ErrMsg': 'success'}
                if res_json.get("Result") == 30000 and "success" in res_json.get("ErrMsg", "").lower():
                    logger.info(f"{self.plugin_name} 删除备份文件请求成功 (旧版JSON)。响应: {res_json}")
                    return True, None
                # 直接含 success 字样的宽松匹配
                if "success" in str(res_json).lower():
                    logger.info(f"{self.plugin_name} 删除备份文件请求成功 (宽松匹配)。响应: {res_json}")
                    return True, None
                
                err_msg = res_json.get("ErrMsg") or res_json.get("message") or "删除备份API未返回成功或指定错误信息"
                logger.error(f"{self.plugin_name} 删除备份文件失败 (JSON)。响应: {res_json}, 错误: {err_msg}")
                return False, f"路由器返回错误: {err_msg}"
                
            except json.JSONDecodeError:
                if "success" in response.text.lower():
                    logger.info(f"{self.plugin_name} 删除备份文件请求发送成功。响应: {response.text}")
                    return True, None
                logger.error(f"{self.plugin_name} 删除备份文件失败，非JSON响应且不含 'success'。响应: {response.text}")
                return False, f"路由器返回非预期响应: {response.text[:100]}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 删除备份文件请求失败: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"{self.plugin_name} 删除备份文件过程中发生未知错误: {e}")
            return False, str(e)
    
    def get_system_info(self) -> Optional[Dict]:
        """
        获取爱快路由器系统信息（CPU、内存、运行时间、在线用户、流量等）
        
        :return: 系统信息字典或None
        """
        # v4 令牌模式：GET /api/v4.0/monitoring/system
        if self._use_v4():
            info = self._v4.get_system_info()
            if info:
                logger.debug(f"{self.plugin_name} v4 成功获取系统信息")
            else:
                logger.error(f"{self.plugin_name} v4 获取系统信息失败")
            return info

        info_url = urljoin(self.url, "/Action/call")
        try:
            logger.debug(f"{self.plugin_name} 尝试从 {self.url} 获取系统信息...")
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self.url.rstrip('/'),
                'Referer': self.url.rstrip('/') + '/'
            }
            all_data = {"func_name": "sysstat", "action": "show", "param": {"TYPE": "all"}}
            response = self.session.post(info_url, data=json.dumps(all_data), headers=request_headers, timeout=10)
            response.raise_for_status()
            res_json = response.json()
            # 新版优先
            data = None
            if res_json.get("code") == 0 and str(res_json.get("message", "")).lower() in ["success", "ok", "成功"]:
                data = res_json.get("results", {})
            elif res_json.get("Result") == 30000 and res_json.get("ErrMsg", "").lower() == "success":
                data = res_json.get("Data", {})
            if data is not None:
                system_info = {}
                cpu_list = data.get("cpu", [])
                if cpu_list:
                    latest_cpu = cpu_list[-1] if cpu_list else "0%"
                    cpu_value = float(latest_cpu.replace("%", ""))
                    system_info["cpu_usage"] = cpu_value
                memory = data.get("memory", {})
                if memory:
                    mem_used = memory.get("used", "0%")
                    mem_value = float(mem_used.replace("%", ""))
                    system_info["mem_usage"] = mem_value
                uptime = data.get("uptime", 0)
                if uptime:
                    system_info["uptime"] = uptime
                online_user = data.get("online_user", {})
                if online_user:
                    system_info["online_users"] = online_user.get("count", 0)
                    system_info["online_wired"] = online_user.get("count_wired", 0)
                    system_info["online_wireless"] = online_user.get("count_wireless", 0)
                stream = data.get("stream", {})
                if stream:
                    system_info["connect_num"] = stream.get("connect_num", 0)
                    system_info["upload_speed"] = stream.get("upload", 0)
                    system_info["download_speed"] = stream.get("download", 0)
                verinfo = data.get("verinfo", {})
                if verinfo:
                    system_info["version"] = verinfo.get("verstring", "")
                    system_info["hostname"] = data.get("hostname", "")
                logger.debug(f"{self.plugin_name} 成功获取系统信息")
                return system_info
            else:
                logger.error(f"{self.plugin_name} 获取系统信息失败")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 获取系统信息请求失败: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"{self.plugin_name} 获取系统信息响应非JSON格式")
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取系统信息过程中发生未知错误: {e}")
            return None
    
    def get_monitor_info(self) -> Optional[Dict]:
        """
        获取爱快路由器监控信息（CPU使用率、内存使用率等）
        
        :return: 监控信息字典或None
        """
        monitor_url = urljoin(self.url, "/Action/call")
        monitor_data = {"func_name": "monitor", "action": "show"}
        
        try:
            logger.debug(f"{self.plugin_name} 尝试从 {self.url} 获取监控信息...")
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self.url.rstrip('/'),
                'Referer': self.url.rstrip('/') + '/'
            }
            response = self.session.post(monitor_url, data=json.dumps(monitor_data), 
                                       headers=request_headers, timeout=10)
            response.raise_for_status()
            
            res_json = response.json()
            if res_json.get("Result") == 30000 and res_json.get("ErrMsg", "").lower() == "success":
                data = res_json.get("Data", {})
                logger.debug(f"{self.plugin_name} 成功获取监控信息")
                return data
            else:
                logger.error(f"{self.plugin_name} 获取监控信息失败: {res_json}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 获取监控信息请求失败: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"{self.plugin_name} 获取监控信息响应非JSON格式")
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取监控信息过程中发生未知错误: {e}")
            return None
    
    def get_interface_info(self) -> Optional[Dict]:
        """
        获取爱快路由器接口信息（兼容4.x及3.x/2.x老版本）
        :return: 接口信息字典或None
        """
        call_url = urljoin(self.url, "/Action/call")
        try:
            logger.debug(f"{self.plugin_name} 尝试从 {self.url} 获取接口信息...")
            request_headers = {
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Origin': self.url.rstrip('/'),
                'Referer': self.url.rstrip('/') + '/'
            }
            # 4.x优先，老版本降级
            lan_data = {"func_name": "lan", "action": "show", "param": {"TYPE": "ether_info,snapshoot,wan_vlan_fail,stream"}}
            monitor_data = {"func_name": "monitor_iface", "action": "show", "param": {"TYPE": "iface_check,iface_stream"}}
            wan_data = {"func_name": "wan", "action": "show"}
            # 先请求新版接口
            lan_response = self.session.post(call_url, data=json.dumps(lan_data), headers=request_headers, timeout=10)
            monitor_response = self.session.post(call_url, data=json.dumps(monitor_data), headers=request_headers, timeout=10)
            lan_response.raise_for_status()
            monitor_response.raise_for_status()
            lan_json = lan_response.json()
            monitor_json = monitor_response.json()
            interface_info = {}
            # 4.x新版字段优先
            snapshoot_lan = None
            iface_check = None
            iface_stream = None
            if lan_json.get("code") == 0 and str(lan_json.get("message", "")).lower() in ["success", "ok", "成功"]:
                lan_data_obj = lan_json.get("results", {})
                snapshoot_lan = lan_data_obj.get("snapshoot_lan")
            elif lan_json.get("Result") == 30000 and lan_json.get("ErrMsg", "").lower() == "success":
                lan_data_obj = lan_json.get("Data", {})
                snapshoot_lan = lan_data_obj.get("snapshoot_lan")
            if monitor_json.get("code") == 0 and str(monitor_json.get("message", "")).lower() in ["success", "ok", "成功"]:
                monitor_data_obj = monitor_json.get("results", {})
                iface_check = monitor_data_obj.get("iface_check")
                iface_stream = monitor_data_obj.get("iface_stream")
            elif monitor_json.get("Result") == 30000 and monitor_json.get("ErrMsg", "").lower() == "success":
                monitor_data_obj = monitor_json.get("Data", {})
                iface_check = monitor_data_obj.get("iface_check")
                iface_stream = monitor_data_obj.get("iface_stream")
            # 如果新版字段都存在，直接返回
            if snapshoot_lan or iface_check or iface_stream:
                if snapshoot_lan:
                    interface_info["snapshoot_lan"] = snapshoot_lan
                if iface_check:
                    interface_info["iface_check"] = iface_check
                if iface_stream:
                    interface_info["iface_stream"] = iface_stream
                logger.debug(f"{self.plugin_name} 4.x线路状态接口数据已获取")
                return interface_info
            # 否则降级兼容老版本（3.x/2.x）
            logger.debug(f"{self.plugin_name} 未获取到4.x线路状态字段，尝试兼容老版本接口...")
            # 老版本只请求WAN/LAN基本信息
            wan_response = self.session.post(call_url, data=json.dumps(wan_data), headers=request_headers, timeout=10)
            wan_response.raise_for_status()
            wan_json = wan_response.json()
            # WAN
            if wan_json.get("code") == 0 and str(wan_json.get("message", "")).lower() in ["success", "ok", "成功"]:
                interface_info["wan"] = wan_json.get("results", {})
                logger.debug(f"{self.plugin_name} 成功获取WAN接口信息(老版本)")
            elif wan_json.get("Result") == 30000 and wan_json.get("ErrMsg", "").lower() == "success":
                interface_info["wan"] = wan_json.get("Data", {})
                logger.debug(f"{self.plugin_name} 成功获取WAN接口信息(老版本)")
            # LAN
            if lan_json.get("code") == 0 and str(lan_json.get("message", "")).lower() in ["success", "ok", "成功"]:
                interface_info["lan"] = lan_json.get("results", {})
                logger.debug(f"{self.plugin_name} 成功获取LAN接口信息(老版本)")
            elif lan_json.get("Result") == 30000 and lan_json.get("ErrMsg", "").lower() == "success":
                interface_info["lan"] = lan_json.get("Data", {})
                logger.debug(f"{self.plugin_name} 成功获取LAN接口信息(老版本)")
            if interface_info:
                return interface_info
            else:
                logger.error(f"{self.plugin_name} 获取接口信息失败")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"{self.plugin_name} 获取接口信息请求失败: {e}")
            return None
        except json.JSONDecodeError:
            logger.error(f"{self.plugin_name} 获取接口信息响应非JSON格式")
            return None
        except Exception as e:
            logger.error(f"{self.plugin_name} 获取接口信息过程中发生未知错误: {e}")
            return None

