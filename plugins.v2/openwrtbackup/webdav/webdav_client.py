"""
WebDAV客户端模块
提供标准WebDAV上传、下载、列表等功能
"""
import os
import time
import re
from datetime import datetime
from typing import Tuple, Optional, List, Dict
from urllib.parse import urlparse, quote
from requests import Session
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class WebDAVClient:
    """标准WebDAV客户端"""
    
    def __init__(self, url: str, username: str, password: str, path: str = "", 
                 skip_dir_check: bool = True, logger=None, plugin_name: str = ""):
        """
        初始化WebDAV客户端
        
        :param url: WebDAV服务器URL
        :param username: 用户名
        :param password: 密码
        :param path: WebDAV路径
        :param skip_dir_check: 是否跳过目录检查
        :param logger: 日志记录器
        :param plugin_name: 插件名称
        """
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.path = path.lstrip('/')
        self.skip_dir_check = skip_dir_check
        self.logger = logger
        self.plugin_name = plugin_name or "WebDAV"
        
        # 解析URL
        self.parsed_url = urlparse(self.url)
        self.is_alist = self.parsed_url.port == 5244 or '5244' in self.url
        
        # 构建基础URL
        if self.is_alist and '/dav' not in self.url:
            self.base_url = f"{self.url}/dav"
        else:
            self.base_url = self.url
        
        # 创建Session并配置认证
        self.session = None
        self.auth = None
        
    def _get_session(self) -> Optional[Session]:
        """获取配置好的Session"""
        if self.session:
            return self.session
        
        # 尝试Basic认证
        auth = HTTPBasicAuth(self.username, self.password)
        
        # 创建Session
        session = Session()
        session.auth = auth
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            pool_connections=1,
            pool_maxsize=1,
            max_retries=retry_strategy
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 测试连接（不设置超时限制）
        try:
            response = session.request(
                'PROPFIND',
                self.base_url,
                headers={'Depth': '0'},
                timeout=None,
                verify=False
            )
            
            if response.status_code in [200, 207]:
                self.session = session
                self.auth = auth
                return session
            elif response.status_code == 401:
                # 尝试Digest认证（不设置超时限制）
                auth = HTTPDigestAuth(self.username, self.password)
                session.auth = auth
                response = session.request(
                    'PROPFIND',
                    self.base_url,
                    headers={'Depth': '0'},
                    timeout=None,
                    verify=False
                )
                if response.status_code in [200, 207]:
                    self.session = session
                    self.auth = auth
                    return session
            
            if self.logger:
                self.logger.error(f"{self.plugin_name} WebDAV认证失败，状态码: {response.status_code}")
            return None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"{self.plugin_name} WebDAV连接失败: {str(e)}")
            return None
    
    def _build_upload_url(self, filename: str) -> str:
        """构建上传URL"""
        if self.path:
            return f"{self.base_url}/{self.path}/{quote(filename)}"
        else:
            return f"{self.base_url}/{quote(filename)}"
    
    def get_upload_url(self, filename: str) -> str:
        """
        获取完整的上传URL
        
        :param filename: 文件名
        :return: 完整的上传URL
        """
        return self._build_upload_url(filename)
    
    def _create_directories(self) -> Tuple[bool, Optional[str]]:
        """创建目录结构"""
        if not self.path or self.skip_dir_check:
            return True, None
        
        try:
            session = self._get_session()
            if not session:
                return False, "无法建立WebDAV连接"
            
            # 分割路径
            path_parts = [p for p in self.path.split('/') if p]
            current_path = self.base_url
            
            # 逐级创建目录
            for part in path_parts:
                current_path = f"{current_path}/{part}"
                
                # 检查目录是否存在（不设置超时限制）
                response = session.request(
                    'PROPFIND',
                    current_path,
                    headers={'Depth': '0'},
                    timeout=None,
                    verify=False
                )
                
                if response.status_code == 404:
                    # 目录不存在，创建它（不设置超时限制）
                    mkdir_response = session.request(
                        'MKCOL',
                        current_path,
                        timeout=None,
                        verify=False
                    )
                    
                    if mkdir_response.status_code not in [200, 201, 204, 405]:
                        return False, f"创建目录失败: {current_path}, 状态码: {mkdir_response.status_code}"
                elif response.status_code not in [200, 207]:
                    return False, f"检查目录失败: {current_path}, 状态码: {response.status_code}"
            
            return True, None
            
        except Exception as e:
            return False, f"创建目录时发生错误: {str(e)}"
    
    def upload(self, local_file_path: str, filename: str, 
               progress_callback=None) -> Tuple[bool, Optional[str]]:
        """
        上传文件到WebDAV
        
        :param local_file_path: 本地文件路径
        :param filename: 远程文件名
        :param progress_callback: 进度回调函数 (uploaded, total, speed) -> None
        :return: (成功, 错误信息)
        """
        if not os.path.exists(local_file_path):
            return False, f"本地文件不存在: {local_file_path}"
        
        # 获取Session
        session = self._get_session()
        if not session:
            return False, "无法建立WebDAV连接"
        
        # 创建目录
        create_success, create_error = self._create_directories()
        if not create_success and self.logger:
            self.logger.warning(f"{self.plugin_name} 创建目录失败，继续尝试上传: {create_error}")
        
        # 获取文件大小
        file_size = os.path.getsize(local_file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        # 构建上传URL
        upload_url = self._build_upload_url(filename)
        
        # 对于小文件（< 10MB），直接一次性读取并上传，避免流式上传的开销
        SMALL_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB
        
        if file_size < SMALL_FILE_THRESHOLD:
            # 小文件：直接读取整个文件并一次性上传
            if self.logger:
                self.logger.info(f"{self.plugin_name} 准备上传小文件: {filename}, 大小: {file_size_mb:.2f}MB")
            
            try:
                start_time = time.time()
                
                # 直接读取整个文件
                with open(local_file_path, 'rb') as f:
                    file_data = f.read()
                
                # 一次性上传
                response = session.put(
                    upload_url,
                    data=file_data,
                    headers={
                        'Content-Type': 'application/octet-stream',
                        'User-Agent': 'MoviePilot/1.0'
                    },
                    timeout=30,  # 小文件设置30秒超时足够
                    verify=False
                )
                
                # 检查响应
                if response.status_code in [200, 201, 204]:
                    total_time = time.time() - start_time
                    total_speed = file_size / total_time / 1024 / 1024 if total_time > 0 else 0  # MB/s
                    if self.logger:
                        self.logger.info(f"{self.plugin_name} 文件上传成功: {filename}, 耗时: {total_time:.2f}秒, 速度: {total_speed:.2f}MB/s")
                    return True, None
                elif response.status_code == 409:
                    # 文件冲突，使用Overwrite头重新上传
                    response = session.put(
                        upload_url,
                        data=file_data,
                        headers={
                            'Content-Type': 'application/octet-stream',
                            'User-Agent': 'MoviePilot/1.0',
                            'Overwrite': 'T'
                        },
                        timeout=30,
                        verify=False
                    )
                    if response.status_code in [200, 201, 204]:
                        if self.logger:
                            self.logger.info(f"{self.plugin_name} 文件上传成功（覆盖）: {filename}")
                        return True, None
                    else:
                        error_msg = f"上传失败（覆盖后）: HTTP {response.status_code}"
                        if self.logger:
                            self.logger.error(f"{self.plugin_name} {error_msg}")
                        return False, error_msg
                else:
                    error_msg = f"上传失败: HTTP {response.status_code}"
                    if self.logger:
                        self.logger.error(f"{self.plugin_name} {error_msg}")
                    return False, error_msg
            except Exception as e:
                error_msg = f"上传过程中发生错误: {str(e)}"
                if self.logger:
                    self.logger.error(f"{self.plugin_name} {error_msg}")
                return False, error_msg
        
        # 大文件：使用流式上传
        # 根据文件大小选择块大小
        if file_size < 100 * 1024 * 1024:  # < 100MB
            chunk_size = 16 * 1024 * 1024  # 16MB
        elif file_size < 500 * 1024 * 1024:  # < 500MB
            chunk_size = 32 * 1024 * 1024  # 32MB
        elif file_size < 5 * 1024 * 1024 * 1024:  # < 5GB
            chunk_size = 64 * 1024 * 1024  # 64MB
        elif file_size < 50 * 1024 * 1024 * 1024:  # < 50GB
            chunk_size = 128 * 1024 * 1024  # 128MB
        else:  # >= 50GB
            chunk_size = 256 * 1024 * 1024  # 256MB
        
        # 不设置超时限制（使用None表示无限制）
        timeout = None
        
        if self.logger:
            file_size_gb = file_size_mb / 1024
            if file_size_gb >= 1:
                size_display = f"{file_size_gb:.2f}GB ({file_size_mb:.2f}MB)"
            else:
                size_display = f"{file_size_mb:.2f}MB"
            self.logger.info(f"{self.plugin_name} 准备上传大文件: {filename}, 大小: {size_display}, 块大小: {chunk_size / 1024 / 1024:.0f}MB")
        
        # 流式上传（大文件）
        try:
            start_time = time.time()
            uploaded_size = [0]  # 使用列表以便在嵌套函数中修改
            last_report_time = [start_time]
            last_progress = [-1]
            
            data_sent_complete = [False]  # 标记数据是否发送完成
            
            def file_generator():
                with open(local_file_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            # 数据发送完成
                            if not data_sent_complete[0] and self.logger:
                                self.logger.info(f"{self.plugin_name} 数据已全部发送，等待服务器确认...")
                                data_sent_complete[0] = True
                            break
                        
                        uploaded_size[0] += len(chunk)
                        current_time = time.time()
                        
                        # 计算进度和速度
                        if file_size > 0:
                            progress = (uploaded_size[0] / file_size) * 100
                            elapsed_time = current_time - start_time
                            
                            # 计算平均速度
                            if elapsed_time > 0:
                                avg_speed = uploaded_size[0] / elapsed_time / 1024 / 1024  # MB/s
                            else:
                                avg_speed = 0
                            
                            # 进度报告逻辑：
                            # - 0-90%: 每10%报告一次
                            # - 90-100%: 每5%或更小间隔报告（90%, 95%, 97%, 99%, 99.5%, 99.9%, 100%）
                            # - 或者每30秒报告一次（确保长时间上传也有反馈）
                            time_since_report = current_time - last_report_time[0]
                            
                            # 根据进度范围决定报告节点
                            report_progress = None
                            if progress < 90:
                                # 0-90%: 每10%
                                report_progress = int(progress / 10) * 10
                            elif progress >= 90 and last_progress[0] < 90:
                                report_progress = 90
                            elif progress >= 95 and last_progress[0] < 95:
                                report_progress = 95
                            elif progress >= 97 and last_progress[0] < 97:
                                report_progress = 97
                            elif progress >= 99 and last_progress[0] < 99:
                                report_progress = 99
                            elif progress >= 99.5 and last_progress[0] < 99.5:
                                report_progress = 99.5
                            elif progress >= 99.9 and last_progress[0] < 99.9:
                                report_progress = 99.9
                            elif progress >= 99.9:
                                # 99.9%之后显示实际进度（保留1位小数）
                                report_progress = round(progress, 1)
                            
                            # 判断是否需要报告
                            should_report = False
                            if report_progress is not None:
                                # 到达了新的报告节点
                                should_report = report_progress > last_progress[0]
                            # 或者超过30秒没有报告（使用实际进度）
                            if not should_report and time_since_report >= 30:
                                should_report = True
                                report_progress = round(progress, 1)
                            
                            if should_report and progress_callback:
                                progress_callback(uploaded_size[0], file_size, avg_speed)
                                last_report_time[0] = current_time
                                if report_progress is not None and report_progress > last_progress[0]:
                                    last_progress[0] = report_progress
                            
                        yield chunk
            
            # 执行PUT请求（标准WebDAV方法）
            response = session.put(
                upload_url,
                data=file_generator(),
                headers={
                    'Content-Type': 'application/octet-stream',
                    'User-Agent': 'MoviePilot/1.0'
                },
                timeout=timeout,
                verify=False
            )
            
            # 检查响应
            if response.status_code in [200, 201, 204]:
                total_time = time.time() - start_time
                total_speed = file_size / total_time / 1024 / 1024  # MB/s
                if self.logger:
                    self.logger.info(f"{self.plugin_name} 文件上传成功: {filename}")
                    self.logger.info(f"{self.plugin_name} 上传耗时: {total_time:.1f}秒, 平均速度: {total_speed:.2f}MB/s")
                return True, None
            elif response.status_code == 405:
                # Method Not Allowed - WebDAV服务器可能不支持PUT方法，或URL格式不正确
                error_msg = f"WebDAV服务器不支持PUT方法（405），请检查WebDAV服务器配置和URL路径。上传URL: {upload_url}"
                if self.logger:
                    self.logger.error(f"{self.plugin_name} {error_msg}")
                return False, error_msg
            elif response.status_code == 409:
                # 文件冲突，尝试使用Overwrite头重新上传
                def file_generator_with_overwrite():
                    with open(local_file_path, 'rb') as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            yield chunk
                
                response = session.put(
                    upload_url,
                    data=file_generator_with_overwrite(),
                    headers={
                        'Content-Type': 'application/octet-stream',
                        'User-Agent': 'MoviePilot/1.0',
                        'Overwrite': 'T'
                    },
                    timeout=timeout,
                    verify=False
                )
                if response.status_code in [200, 201, 204]:
                    if self.logger:
                        self.logger.info(f"{self.plugin_name} 文件上传成功（覆盖）: {filename}")
                    return True, None
                else:
                    return False, f"上传失败，状态码: {response.status_code}"
            elif response.status_code == 507:
                return False, "WebDAV服务器存储空间不足"
            else:
                return False, f"上传失败，状态码: {response.status_code}, 响应: {response.text[:200]}"
                
        except Exception as e:
            return False, f"上传过程中发生错误: {str(e)}"
    
    def list_files(self, pattern: str = None) -> Tuple[List[Dict], Optional[str]]:
        """
        列出WebDAV目录中的文件
        
        :param pattern: 文件名模式（可选）
        :return: (文件列表, 错误信息)
        """
        session = self._get_session()
        if not session:
            return [], "无法建立WebDAV连接"
        
        try:
            # 构建列表URL
            list_url = self._build_upload_url("")
            
            # 执行PROPFIND请求（不设置超时限制）
            response = session.request(
                'PROPFIND',
                list_url,
                headers={'Depth': '1'},
                timeout=None,
                verify=False
            )
            
            if response.status_code not in [200, 207]:
                return [], f"列表请求失败，状态码: {response.status_code}"
            
            # 解析XML响应
            from xml.etree import ElementTree
            root = ElementTree.fromstring(response.content)
            
            files = []
            ns = {'D': 'DAV:'}
            
            for response_elem in root.findall('.//D:response', ns):
                href_elem = response_elem.find('D:href', ns)
                if href_elem is None:
                    continue
                
                href = href_elem.text
                if not href:
                    continue
                
                # 跳过目录本身
                if href.endswith('/') or href == list_url:
                    continue
                
                # 获取文件名
                filename = href.split('/')[-1]
                
                # 如果指定了模式，进行过滤
                if pattern and pattern not in filename:
                    continue
                
                # 获取文件大小和修改时间
                propstat = response_elem.find('D:propstat', ns)
                if propstat is not None:
                    prop = propstat.find('D:prop', ns)
                    if prop is not None:
                        size_elem = prop.find('D:getcontentlength', ns)
                        date_elem = prop.find('D:getlastmodified', ns)
                        
                        size = int(size_elem.text) if size_elem is not None and size_elem.text else 0
                        
                        # 解析修改时间
                        file_time = None
                        if date_elem is not None and date_elem.text:
                            try:
                                from email.utils import parsedate_to_datetime
                                file_time = parsedate_to_datetime(date_elem.text).timestamp()
                            except:
                                # 如果解析失败，尝试从文件名提取时间戳
                                import re
                                match = re.search(r'(\d{4}[_-]\d{2}[_-]\d{2}[_-]\d{2}[_-]\d{2}[_-]\d{2})', filename)
                                if match:
                                    try:
                                        time_str = match.group(1).replace('_', '')
                                        file_time = datetime.strptime(time_str, '%Y%m%d%H%M%S').timestamp()
                                    except:
                                        pass
                                if file_time is None:
                                    file_time = time.time()  # 使用当前时间作为默认值
                        
                        files.append({
                            'filename': filename,
                            'size': size,
                            'size_mb': size / (1024 * 1024),
                            'href': href,
                            'time': file_time or time.time()
                        })
            
            return files, None
            
        except Exception as e:
            return [], f"列表文件时发生错误: {str(e)}"
    
    def download(self, filename: str, local_path: str, 
                 progress_callback=None) -> Tuple[bool, Optional[str]]:
        """
        从WebDAV下载文件
        
        :param filename: 远程文件名
        :param local_path: 本地保存路径
        :param progress_callback: 进度回调函数 (downloaded, total, speed) -> None
        :return: (成功, 错误信息)
        """
        session = self._get_session()
        if not session:
            return False, "无法建立WebDAV连接"
        
        try:
            download_url = self._build_upload_url(filename)
            
            # 执行GET请求（不设置超时限制）
            response = session.get(download_url, stream=True, timeout=None, verify=False)
            
            if response.status_code not in [200, 206]:  # 206支持断点续传
                return False, f"下载失败，状态码: {response.status_code}, 响应: {response.text[:200]}"
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 创建本地目录
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # 下载文件
            start_time = time.time()
            downloaded_size = 0
            last_report_time = start_time
            chunk_size = 8192  # 8KB块
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 进度回调
                        if progress_callback and total_size > 0:
                            current_time = time.time()
                            elapsed_time = current_time - start_time
                            speed = downloaded_size / elapsed_time / 1024 / 1024 if elapsed_time > 0 else 0
                            
                            # 每25%或每30秒报告一次
                            progress = (downloaded_size / total_size) * 100
                            current_progress = int(progress / 25) * 25
                            time_since_report = current_time - last_report_time
                            
                            should_report = (current_progress > 0 and downloaded_size == current_progress * total_size / 100) or \
                                          (time_since_report >= 30)
                            
                            if should_report:
                                progress_callback(downloaded_size, total_size, speed)
                                last_report_time = current_time
            
            if self.logger:
                total_time = time.time() - start_time
                total_speed = downloaded_size / total_time / 1024 / 1024 if total_time > 0 else 0
                self.logger.info(f"{self.plugin_name} 文件下载成功: {filename}, 大小: {downloaded_size / 1024 / 1024:.2f}MB, 速度: {total_speed:.2f}MB/s")
            
            return True, None
            
        except Exception as e:
            return False, f"下载文件时发生错误: {str(e)}"
    
    def delete_file(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        删除WebDAV文件
        
        :param filename: 文件名
        :return: (成功, 错误信息)
        """
        session = self._get_session()
        if not session:
            return False, "无法建立WebDAV连接"
        
        try:
            delete_url = self._build_upload_url(filename)
            response = session.delete(delete_url, timeout=None, verify=False)
            
            if response.status_code in [200, 201, 204]:
                return True, None
            elif response.status_code == 404:
                return False, "文件不存在"
            else:
                return False, f"删除失败，状态码: {response.status_code}"
                
        except Exception as e:
            return False, f"删除文件时发生错误: {str(e)}"
    
    def cleanup_old_files(self, keep_count: int, pattern: str = None) -> Tuple[int, Optional[str]]:
        """
        清理旧文件，只保留最新的N个文件
        
        :param keep_count: 保留文件数量
        :param pattern: 文件名模式（可选）
        :return: (删除的文件数量, 错误信息)
        """
        if keep_count <= 0:
            return 0, None
        
        files, error = self.list_files(pattern)
        if error:
            return 0, error
        
        if len(files) <= keep_count:
            return 0, None
        
        # 按时间排序（优先使用时间，如果没有则使用文件名）
        files.sort(key=lambda x: (x.get('time', 0), x['filename']), reverse=True)
        
        # 删除旧文件
        deleted_count = 0
        for file_info in files[keep_count:]:
            success, error = self.delete_file(file_info['filename'])
            if success:
                deleted_count += 1
                if self.logger:
                    self.logger.info(f"{self.plugin_name} 已删除旧文件: {file_info['filename']}")
            else:
                if self.logger:
                    self.logger.warning(f"{self.plugin_name} 删除文件失败: {file_info['filename']}, 错误: {error}")
        
        return deleted_count, None
    
    def close(self):
        """关闭连接"""
        if self.session:
            self.session.close()
            self.session = None

