import paramiko
import re

def get_pve_status(host, port, username, password, key_file):
    result = {
        "online": False,
        "error": "",
        "cpu_usage": None,
        "load_avg": None,
        "mem_total": None,
        "mem_used": None,
        "mem_usage": None,
        "swap_total": None,
        "swap_used": None,
        "swap_usage": None,
        "disk_total": None,
        "disk_used": None,
        "disk_usage": None,
        "cpu_model": "",
        "cpu_cores": "",
        "kernel": "",
        "pve_version": "",
        "hostname": "",
        "ip": "-",
        "cpu_temp": None,
        "disk_temp": None,
        "io_delay": None,
    }
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            ssh.connect(host, port=port, username=username, pkey=private_key, timeout=5)
        else:
            ssh.connect(host, port=port, username=username, password=password, timeout=5)
        result["online"] = True

        stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)'")
        cpu_line = stdout.read().decode()
        m = re.search(r'(\d+\.\d+)\s*id', cpu_line)
        if m:
            result["cpu_usage"] = round(100 - float(m.group(1)), 2)

        stdin, stdout, stderr = ssh.exec_command("cat /proc/loadavg")
        load_line = stdout.read().decode().strip()
        result["load_avg"] = load_line.split()[:3]

        stdin, stdout, stderr = ssh.exec_command("free -m")
        lines = stdout.read().decode().splitlines()
        for line in lines:
            if line.startswith("Mem:"):
                parts = line.split()
                result["mem_total"] = int(parts[1])
                result["mem_used"] = int(parts[2])
                result["mem_usage"] = round(int(parts[2]) / int(parts[1]) * 100, 2)
            if line.startswith("Swap:"):
                parts = line.split()
                result["swap_total"] = int(parts[1])
                result["swap_used"] = int(parts[2])
                result["swap_usage"] = round(int(parts[2]) / int(parts[1]) * 100, 2) if int(parts[1]) else 0

        stdin, stdout, stderr = ssh.exec_command("df -m / | tail -1")
        parts = stdout.read().decode().split()
        if len(parts) >= 5:
            result["disk_total"] = int(parts[1])
            result["disk_used"] = int(parts[2])
            result["disk_usage"] = float(parts[4].replace('%', ''))

        stdin, stdout, stderr = ssh.exec_command("lscpu | grep 'Model name'")
        cpu_model = stdout.read().decode().split(':')[-1].strip()
        result["cpu_model"] = cpu_model
        stdin, stdout, stderr = ssh.exec_command("nproc")
        result["cpu_cores"] = stdout.read().decode().strip()

        stdin, stdout, stderr = ssh.exec_command("uname -r")
        result["kernel"] = stdout.read().decode().strip()
        stdin, stdout, stderr = ssh.exec_command("pveversion")
        result["pve_version"] = stdout.read().decode().strip()
        stdin, stdout, stderr = ssh.exec_command("hostname")
        result["hostname"] = stdout.read().decode().strip()

        # 获取主机IP
        stdin, stdout, stderr = ssh.exec_command("hostname -I")
        ip_output = stdout.read().decode().strip()
        ip = "-"
        if ip_output:
            ip = next((x for x in ip_output.split() if x and not x.startswith("127.")), "-")
        result["ip"] = ip

        # 获取CPU温度（多种方法尝试）
        try:
            # 方法1: sensors命令
            stdin, stdout, stderr = ssh.exec_command("sensors 2>/dev/null | grep -E '(Core 0|Tctl|CPU Temperature|Package id)' | head -1")
            sensors_output = stdout.read().decode().strip()
            if sensors_output:
                # 提取温度数值
                temp_match = re.search(r'\+?(\d+\.?\d*)°?C', sensors_output)
                if temp_match:
                    result["cpu_temp"] = float(temp_match.group(1))
                else:
                    result["cpu_temp"] = None
            
            # 如果没有获取到，尝试方法2: /sys/class/thermal
            if result["cpu_temp"] is None:
                stdin, stdout, stderr = ssh.exec_command("cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -1")
                thermal_output = stdout.read().decode().strip()
                if thermal_output:
                    try:
                        temp_raw = int(thermal_output.strip())
                        result["cpu_temp"] = round(temp_raw / 1000.0, 1)  # 转换为摄氏度
                    except ValueError:
                        result["cpu_temp"] = None
                else:
                    result["cpu_temp"] = None
            
            # 如果还没有，尝试方法3: vcgencmd (树莓派)
            if result["cpu_temp"] is None:
                stdin, stdout, stderr = ssh.exec_command("vcgencmd measure_temp 2>/dev/null")
                vcgencmd_output = stdout.read().decode().strip()
                if vcgencmd_output:
                    temp_match = re.search(r'temp=(\d+\.?\d*)', vcgencmd_output)
                    if temp_match:
                        result["cpu_temp"] = float(temp_match.group(1))
                    else:
                        result["cpu_temp"] = None
                else:
                    result["cpu_temp"] = None
        except Exception:
            result["cpu_temp"] = None
        
        # 获取硬盘温度（多种方法尝试）
        try:
            # 先尝试获取第一个可用磁盘设备
            stdin, stdout, stderr = ssh.exec_command("lsblk -dn -o NAME,TYPE 2>/dev/null | grep -E 'disk' | head -1 | awk '{print $1}'")
            disk_device = stdout.read().decode().strip()
            
            if not disk_device:
                # 如果没有找到，尝试硬编码设备
                disk_device = "sda"
            
            # 方法1: smartctl (支持SATA和NVMe)
            if disk_device.startswith('nvme'):
                # NVMe设备
                stdin, stdout, stderr = ssh.exec_command(f"smartctl -A /dev/{disk_device} 2>/dev/null | grep -i 'Temperature:' | head -1 | awk '{{print $2}}'")
            else:
                # SATA/SCSI设备
                stdin, stdout, stderr = ssh.exec_command(f"smartctl -A /dev/{disk_device} 2>/dev/null | grep -i 'Temperature_Celsius' | awk '{{print $10}}' | head -1")
            
            smartctl_output = stdout.read().decode().strip()
            if smartctl_output and smartctl_output.isdigit():
                result["disk_temp"] = int(smartctl_output)
            else:
                result["disk_temp"] = None
            
            # 如果没有，尝试方法2: hddtemp
            if result["disk_temp"] is None and not disk_device.startswith('nvme'):
                stdin, stdout, stderr = ssh.exec_command(f"hddtemp /dev/{disk_device} 2>/dev/null")
                hddtemp_output = stdout.read().decode().strip()
                if hddtemp_output and '°C' in hddtemp_output:
                    temp_match = re.search(r'(\d+)', hddtemp_output)
                    if temp_match:
                        result["disk_temp"] = int(temp_match.group(1))
                    else:
                        result["disk_temp"] = None
                else:
                    result["disk_temp"] = None
            
            # 如果还没有，尝试方法3: 使用smartctl -a (某些NVMe驱动)
            if result["disk_temp"] is None and disk_device.startswith('nvme'):
                stdin, stdout, stderr = ssh.exec_command(f"smartctl -a /dev/{disk_device} 2>/dev/null | grep -i 'temperature sensor' | head -1 | grep -oE '[0-9]+'")
                nvme_temp_output = stdout.read().decode().strip()
                if nvme_temp_output:
                    try:
                        result["disk_temp"] = int(nvme_temp_output)
                    except ValueError:
                        result["disk_temp"] = None
                else:
                    result["disk_temp"] = None
        except Exception:
            result["disk_temp"] = None
        
        # 获取IO延迟（iostat await值，毫秒）
        try:
            # 使用iostat获取平均等待时间（await列，通常是第10列）
            stdin, stdout, stderr = ssh.exec_command("iostat -x 1 1 2>/dev/null | grep -v '^$' | tail -n +4 | awk 'NF>=10 {sum+=$10; count++} END {if(count>0 && sum>0) print sum/count; else print 0}'")
            iostat_output = stdout.read().decode().strip()
            if iostat_output:
                try:
                    io_delay = float(iostat_output)
                    # 只有当延迟值合理时才使用（大于0且小于10000ms）
                    if 0 < io_delay < 10000:
                        result["io_delay"] = round(io_delay, 2)
                    else:
                        result["io_delay"] = None
                except (ValueError, TypeError):
                    result["io_delay"] = None
            else:
                result["io_delay"] = None
            
            # 如果iostat不可用或获取失败，尝试从/proc/stat计算iowait
            if result["io_delay"] is None:
                stdin, stdout, stderr = ssh.exec_command("cat /proc/stat | grep '^cpu ' | head -1")
                cpu_stat = stdout.read().decode().strip()
                if cpu_stat:
                    parts = cpu_stat.split()
                    if len(parts) >= 6:
                        try:
                            # cpu user nice system idle iowait irq softirq
                            iowait = int(parts[5]) if len(parts) > 5 else 0
                            total = sum(int(x) for x in parts[1:] if x.isdigit())
                            if total > 0 and iowait > 0:
                                # iowait百分比转换为近似毫秒延迟（经验公式：1% iowait ≈ 5-15ms延迟）
                                iowait_percent = (iowait / total) * 100
                                # 使用保守的转换：1% = 10ms
                                estimated_delay = iowait_percent * 10
                                result["io_delay"] = round(estimated_delay, 2) if estimated_delay > 0.1 else None
                            else:
                                result["io_delay"] = None
                        except (ValueError, IndexError):
                            result["io_delay"] = None
        except Exception:
            result["io_delay"] = None

        ssh.close()
    except Exception as e:
        result["error"] = str(e)
    return result


def get_node_name(ssh):
    stdin, stdout, stderr = ssh.exec_command('hostname')
    return stdout.read().decode().strip()


def get_qemu_status(host, port, username, password, key_file):
    """
    获取所有QEMU虚拟机的详细状态，补充displayName和tags字段。
    tags 字段通过 qm config <vmid> 解析 tags: 行获得。
    uptime 字段通过 pvesh 命令获取。
    """
    vms = []
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            ssh.connect(host, port=port, username=username, pkey=private_key, timeout=5)
        else:
            ssh.connect(host, port=port, username=username, password=password, timeout=5)
        try:
            node_name = get_node_name(ssh)
            stdin, stdout, stderr = ssh.exec_command("qm list")
            lines = stdout.read().decode().splitlines()
            if not lines or len(lines) < 2:
                ssh.close()
                return []
            headers = [h.lower() for h in re.split(r'\s+', lines[0].strip())]
            for line in lines[1:]:
                if not line.strip():
                    continue
                m = re.search(r'\(([^)]+)\)', line)
                name = m.group(1) if m else ''
                parts = re.split(r'\s+', line.strip())
                data = dict(zip(headers, parts))
                if not name:
                    name = data.get('name','')
                if not name:
                    name = f"QEMU-{data.get('vmid','')}"
                display_name = name
                tags = ''
                vmid = data.get('vmid','')
                # 解析 displayName和tags
                if vmid:
                    try:
                        stdin2, stdout2, stderr2 = ssh.exec_command(f"qm config {vmid}")
                        config_lines = stdout2.read().decode().splitlines()
                        for cl in config_lines:
                            if cl.startswith('name:'):
                                real_name = cl.split(':',1)[1].strip()
                                if real_name:
                                    display_name = real_name
                        for cl in config_lines:
                            if cl.startswith('tags:'):
                                tags = cl.split(':',1)[1].strip()
                                break
                    except Exception:
                        tags = ''
                # 用paramiko invoke_shell方式获取uptime，兼容极端受限环境
                uptime = 0
                if vmid:
                    try:
                        import json
                        stdin_uptime, stdout_uptime, stderr_uptime = ssh.exec_command(f"/usr/bin/pvesh get /nodes/{node_name}/qemu/{vmid}/status/current --output-format json")
                        output = stdout_uptime.read().decode()
                        data_json = json.loads(output)
                        uptime = data_json.get('uptime', '')
                    except Exception as e:
                        uptime = 0
                status = data.get('status','')
                # 移除冗余的status查询，qm list已经包含了status信息
                vms.append({
                    'vmid': data.get('vmid',''),
                    'name': name,
                    'displayName': display_name,
                    'status': status,
                    'lock': data.get('lock',''),
                    'uptime': uptime,
                    'cpu': data.get('cpu',''),
                    'mem': data.get('mem',''),
                    'maxmem': data.get('maxmem',''),
                    'disk': data.get('disk',''),
                    'maxdisk': data.get('maxdisk',''),
                    'pid': data.get('pid',''),
                    'netin': '',
                    'netout': '',
                    'type': 'qemu',
                    'tags': tags
                })
        except Exception as e:
            vms.append({'error': str(e)})
        ssh.close()
    except Exception as e:
        vms.append({'error': str(e)})
    return vms


def get_container_status(host, port, username, password, key_file):
    """
    获取所有LXC容器的详细状态，补充displayName和tags字段。
    tags 字段通过 pct config <vmid> 解析 tags: 行获得。
    uptime 字段通过 pvesh 命令获取。
    """
    containers = []
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            ssh.connect(host, port=port, username=username, pkey=private_key, timeout=5)
        else:
            ssh.connect(host, port=port, username=username, password=password, timeout=5)
        try:
            node_name = get_node_name(ssh)
            stdin, stdout, stderr = ssh.exec_command("pct list")
            lines = stdout.read().decode().splitlines()
            if not lines or len(lines) < 2:
                ssh.close()
                return []
            headers = [h.lower() for h in re.split(r'\s+', lines[0].strip())]
            for line in lines[1:]:
                if not line.strip():
                    continue
                m = re.search(r'\(([^)]+)\)', line)
                name = m.group(1) if m else ''
                parts = re.split(r'\s+', line.strip())
                data = dict(zip(headers, parts))
                if not name:
                    name = data.get('name','')
                if not name:
                    name = f"LXC-{data.get('vmid','')}"
                display_name = name
                tags = ''
                uptime = 0
                vmid = data.get('vmid','')
                if name.startswith('LXC-'):
                    try:
                        stdin2, stdout2, stderr2 = ssh.exec_command(f"pct config {vmid}")
                        config_lines = stdout2.read().decode().splitlines()
                        for cl in config_lines:
                            if cl.startswith('hostname:'):
                                real_name = cl.split(':',1)[1].strip()
                                if real_name:
                                    display_name = real_name
                        for cl in config_lines:
                            if cl.startswith('tags:'):
                                tags = cl.split(':',1)[1].strip()
                                break
                    except Exception:
                        tags = ''
                # 用paramiko invoke_shell方式获取uptime，兼容极端受限环境
                if vmid:
                    try:
                        import json
                        stdin_uptime, stdout_uptime, stderr_uptime = ssh.exec_command(f"/usr/bin/pvesh get /nodes/{node_name}/lxc/{vmid}/status/current --output-format json")
                        output = stdout_uptime.read().decode()
                        data_json = json.loads(output)
                        uptime = data_json.get('uptime', '')
                    except Exception as e:
                        uptime = 0
                status = data.get('status','')
                # 移除冗余的status查询，pct list已经包含了status信息
                containers.append({
                    'vmid': data.get('vmid',''),
                    'name': name,
                    'displayName': display_name,
                    'status': status,
                    'lock': data.get('lock',''),
                    'uptime': uptime,
                    'cpu': data.get('cpu',''),
                    'mem': data.get('mem',''),
                    'maxmem': data.get('maxmem',''),
                    'swap': data.get('swap',''),
                    'maxswap': data.get('maxswap',''),
                    'disk': data.get('disk',''),
                    'maxdisk': data.get('maxdisk',''),
                    'pid': data.get('pid',''),
                    'netin': data.get('netin',''),
                    'netout': data.get('netout',''),
                    'type': 'lxc',
                    'tags': tags
                })
        except Exception as e:
            containers.append({'error': str(e)})
        ssh.close()
    except Exception as e:
        containers.append({'error': str(e)})
    return containers


def clean_pve_tmp_files(host, port, username, password, key_file):
    """
    通过SSH执行 rm -rf /var/lib/vz/dump/*.tmp，彻底清理PVE主机上的所有 .tmp 文件和目录。
    返回 (清理数量, 错误信息)
    """
    import paramiko
    count = 0
    error = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            ssh.connect(host, port=port, username=username, pkey=private_key, timeout=10)
        else:
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
        # 先统计要清理的数量
        stdin, stdout, stderr = ssh.exec_command("ls -1d /var/lib/vz/dump/*.tmp 2>/dev/null | wc -l")
        count_str = stdout.read().decode().strip()
        try:
            count = int(count_str)
        except Exception:
            count = 0
        # 执行清理命令
        stdin, stdout, stderr = ssh.exec_command("rm -rf /var/lib/vz/dump/*.tmp")
        err = stderr.read().decode().strip()
        if err:
            error = err
        ssh.close()
    except Exception as e:
        error = str(e)
    return count, error 


def clean_pve_logs(host, port, username, password, key_file, journal_days=None, log_dirs=None):
    """
    通过SSH清理PVE主机上的系统日志。
    - journal_days: int或None，journalctl保留天数（None则全部清理）
    - log_dirs: dict，key为日志目录（如/var/log/vzdump），value为保留N个文件（None或0为全部清理）
    返回: dict {类别: (清理数量, 错误信息)}
    """
    import paramiko
    result = {}
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            ssh.connect(host, port=port, username=username, pkey=private_key, timeout=10)
        else:
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
        # 1. 清理journalctl
        if journal_days is not None:
            try:
                cmd = f"journalctl --vacuum-time={journal_days}d"
                stdin, stdout, stderr = ssh.exec_command(cmd)
                out, err = stdout.read().decode(), stderr.read().decode()
                err = err.strip() if err else ''
                # 优化：只要包含 Vacuuming done 或为空就不算失败
                if not err or 'Vacuuming done' in err:
                    result['journalctl'] = (None, None)
                else:
                    result['journalctl'] = (None, err)
            except Exception as e:
                result['journalctl'] = (None, str(e))
        else:
            # 全部清理（极端情况，不建议）
            try:
                cmd = "journalctl --rotate && journalctl --vacuum-time=1s"
                stdin, stdout, stderr = ssh.exec_command(cmd)
                out, err = stdout.read().decode(), stderr.read().decode()
                err = err.strip() if err else ''
                if not err or 'Vacuuming done' in err:
                    result['journalctl'] = (None, None)
                else:
                    result['journalctl'] = (None, err)
            except Exception as e:
                result['journalctl'] = (None, str(e))
        # 2. 清理各类日志目录
        if log_dirs:
            import shlex
            for log_dir, keep_num in log_dirs.items():
                try:
                    # 获取所有日志文件，按修改时间倒序
                    list_cmd = f"ls -1t {shlex.quote(log_dir)} 2>/dev/null"
                    stdin, stdout, stderr = ssh.exec_command(list_cmd)
                    files = [f.strip() for f in stdout.read().decode().splitlines() if f.strip()]
                    del_count = 0
                    err = None
                    if files:
                        if keep_num and keep_num > 0:
                            to_delete = files[keep_num:]
                        else:
                            to_delete = files
                        for f in to_delete:
                            del_cmd = f"rm -f {shlex.quote(log_dir.rstrip('/') + '/' + f)}"
                            stdin, stdout, stderr = ssh.exec_command(del_cmd)
                            _ = stdout.read()
                            e = stderr.read().decode().strip()
                            # 优化：如果是 'Is a directory' 错误，忽略
                            if e and 'Is a directory' not in e:
                                err = e
                            elif not e:
                                del_count += 1
                    result[log_dir] = (del_count, err)
                except Exception as e:
                    result[log_dir] = (0, str(e))
        ssh.close()
    except Exception as e:
        result['ssh'] = (0, str(e))
    return result 


def list_template_images(host, port, username, password, key_file):
    """
    列出PVE主机上的所有ISO镜像和CT模板文件。
    返回列表：[{'filename':..., 'type': 'iso'/'ct', 'size_mb':..., 'date':...}]
    """
    import paramiko
    import os
    import datetime
    result = []
    iso_exts = ('.iso', '.img', '.raw', '.qcow2', '.vmdk', '.vdi', '.vhd', '.vhdx')
    ct_exts = ('.tar.gz', '.tar.xz', '.tar.lzo', '.tar.zst', '.tgz', '.txz', '.tlz', '.tbz', '.tar.bz2')
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            ssh.connect(host, port=port, username=username, pkey=private_key, timeout=10)
        else:
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
        # ISO镜像
        for dir_path, exts, ftype in [
            ('/var/lib/vz/template/iso', iso_exts, 'iso'),
            ('/var/lib/vz/template/cache', ct_exts, 'ct')
        ]:
            cmd = f"ls -l --time-style=+%Y-%m-%d\ %H:%M:%S {dir_path}"
            stdin, stdout, stderr = ssh.exec_command(cmd)
            lines = stdout.read().decode().splitlines()
            for line in lines:
                parts = line.strip().split()
                if len(parts) < 6 or parts[0][0] != '-':
                    continue
                fname = parts[-1]
                if not fname.lower().endswith(exts):
                    continue
                size = int(parts[4])
                date = ' '.join(parts[5:7]) if len(parts) >= 7 else ''
                result.append({
                    'filename': fname,
                    'type': ftype,
                    'size_mb': round(size / (1024*1024), 2),
                    'date': date
                })
        ssh.close()
    except Exception as e:
        return []
    return result

def upload_template_image(host, port, username, password, key_file, local_path, filename, filetype):
    """
    上传本地镜像/模板文件到PVE主机指定目录。
    local_path: 本地文件路径
    filename: 目标文件名
    filetype: 'iso' or 'ct'
    """
    import paramiko
    import os
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            ssh.connect(host, port=port, username=username, pkey=private_key, timeout=10)
        else:
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
        sftp = ssh.open_sftp()
        if filetype == 'iso':
            remote_path = f"/var/lib/vz/template/iso/{filename}"
        else:
            remote_path = f"/var/lib/vz/template/cache/{filename}"
        # 路径安全校验
        if not os.path.basename(remote_path) == filename:
            raise Exception("非法文件名")
        sftp.put(local_path, remote_path)
        sftp.close()
        ssh.close()
        return True, None
    except Exception as e:
        return False, str(e)

def download_template_image(host, port, username, password, key_file, filename, filetype, local_path):
    """
    下载指定模板镜像（ISO或CT模板）到本地路径。
    filetype: 'iso' or 'ct'
    """
    import paramiko
    import os
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            ssh.connect(host, port=port, username=username, pkey=private_key, timeout=10)
        else:
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
        sftp = ssh.open_sftp()
        if filetype == 'iso':
            remote_path = f"/var/lib/vz/template/iso/{filename}"
        else:
            remote_path = f"/var/lib/vz/template/cache/{filename}"
        # 路径安全校验
        if not os.path.basename(remote_path) == filename:
            raise Exception("非法文件名")
        sftp.get(remote_path, local_path)
        sftp.close()
        ssh.close()
        return True, None
    except Exception as e:
        return False, str(e)

def delete_template_image(host, port, username, password, key_file, filename, filetype):
    """
    删除指定模板镜像（ISO或CT模板）。
    filetype: 'iso' or 'ct'
    """
    import paramiko
    import os
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            ssh.connect(host, port=port, username=username, pkey=private_key, timeout=10)
        else:
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
        sftp = ssh.open_sftp()
        if filetype == 'iso':
            remote_path = f"/var/lib/vz/template/iso/{filename}"
        else:
            remote_path = f"/var/lib/vz/template/cache/{filename}"
        # 路径安全校验
        if not os.path.basename(remote_path) == filename:
            raise Exception("非法文件名")
        sftp.remove(remote_path)
        sftp.close()
        ssh.close()
        return True, None
    except Exception as e:
        return False, str(e) 

def download_template_image_from_url(host, port, username, password, key_file, url, filename, filetype):
    """
    让PVE主机从指定URL下载镜像/模板到本地目录。
    url: 下载链接
    filename: 目标文件名
    filetype: 'iso' or 'ct'
    """
    import paramiko
    import os
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_file:
            private_key = paramiko.RSAKey.from_private_key_file(key_file)
            ssh.connect(host, port=port, username=username, pkey=private_key, timeout=10)
        else:
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
        if filetype == 'iso':
            remote_path = f"/var/lib/vz/template/iso/{filename}"
        else:
            remote_path = f"/var/lib/vz/template/cache/{filename}"
        # 路径安全校验
        if not os.path.basename(remote_path) == filename:
            raise Exception("非法文件名")
        # 优先用wget
        cmd = f"wget -O '{remote_path}' '{url}' || curl -L -o '{remote_path}' '{url}'"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        err = stderr.read().decode().strip()
        ssh.close()
        if exit_status == 0:
            return True, None
        else:
            return False, err or f"下载失败，exit code {exit_status}"
    except Exception as e:
        return False, str(e) 