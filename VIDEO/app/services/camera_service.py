import os
import random
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import cv2
import requests
from PIL import Image as PILImage
from requests.auth import HTTPDigestAuth, HTTPBasicAuth

from app.services.project_service import ProjectService
from models import db, Image

class CameraService:
    """摄像头截图管理器，支持RTSP和ONVIF摄像头"""

    def __init__(self):
        self.rtsp_threads = {}
        self.onvif_threads = {}

    def capture_rtsp_images(self, project_id, rtsp_url, interval, max_count):
        """
        从RTSP流中截取图片并保存到项目目录
        
        Args:
            project_id (int): 项目ID
            rtsp_url (str): RTSP地址
            interval (int): 截图间隔（秒）
            max_count (int): 最大截图数量
        """
        thread_id = f"rtsp_{project_id}"
        self.rtsp_threads[thread_id] = {
            'running': True,
            'captured_count': 0,
            'max_count': max_count
        }

        # 确保项目上传目录存在
        project_upload_dir = ProjectService.ensure_project_upload_dir(project_id)

        # 打开RTSP流
        cap = cv2.VideoCapture(rtsp_url)

        # 设置缓冲区大小为1，减少延迟
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            self.rtsp_threads[thread_id]['error'] = "无法打开RTSP流"
            cap.release()
            return

        try:
            # 记录开始时间，用于精确控制时间间隔
            start_time = time.time()

            while (self.rtsp_threads[thread_id]['running'] and
                   self.rtsp_threads[thread_id]['captured_count'] < max_count):

                # 计算下一次截图的准确时间
                next_capture_time = start_time + (self.rtsp_threads[thread_id]['captured_count'] + 1) * interval

                # 当前时间
                current_time = time.time()

                # 如果还没到截图时间，则继续读取帧（避免灰色图片）
                while current_time < next_capture_time:
                    ret, frame = cap.read()
                    if not ret:
                        self.rtsp_threads[thread_id]['error'] = "无法读取视频帧"
                        return

                    # 更新当前时间
                    current_time = time.time()

                    # 短暂休眠以减少CPU使用
                    time.sleep(0.01)

                # 现在到了截图时间，获取最新的帧
                ret, latest_frame = cap.read()
                if not ret:
                    self.rtsp_threads[thread_id]['error'] = "无法读取视频帧"
                    break

                # 检查图像是否有效（避免灰色图片）
                if latest_frame is None or latest_frame.size == 0:
                    self.rtsp_threads[thread_id]['error'] = "获取到无效帧"
                    break

                # 检查图像是否全黑或全白（灰色图片问题）
                gray_frame = cv2.cvtColor(latest_frame, cv2.COLOR_BGR2GRAY)
                if cv2.mean(gray_frame)[0] < 10:  # 几乎全黑
                    # 再读取几帧尝试获取有效图像
                    for _ in range(5):
                        ret, extra_frame = cap.read()
                        if ret and extra_frame is not None and extra_frame.size > 0:
                            gray_extra = cv2.cvtColor(extra_frame, cv2.COLOR_BGR2GRAY)
                            if cv2.mean(gray_extra)[0] >= 10:  # 不是全黑
                                latest_frame = extra_frame
                                break

                # 生成文件名
                timestamp = int(datetime.now().timestamp() * 1000)
                filename = f"{timestamp}_rtsp.jpg"
                file_path = os.path.join(project_upload_dir, filename)

                # 保存图片
                success = cv2.imwrite(file_path, latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
                if success:
                    # 获取图片尺寸
                    img = PILImage.open(file_path)
                    width, height = img.size

                    # 计算相对路径和POSIX路径
                    relative_path = ProjectService.get_relative_path(file_path)
                    posix_path = ProjectService.get_posix_path(relative_path)

                    # 保存到数据库
                    from app import create_app
                    application = create_app()
                    with application.app_context():
                        image = Image(
                            filename=filename,
                            original_filename=f"rtsp_capture_{timestamp}.jpg",
                            path=posix_path,
                            project_id=project_id,
                            width=width,
                            height=height
                        )
                        db.session.add(image)
                        db.session.commit()

                    self.rtsp_threads[thread_id]['captured_count'] += 1
                else:
                    self.rtsp_threads[thread_id]['error'] = "保存图片失败"
                    break

                # 注意：这里不再使用time.sleep，而是通过计算时间来控制间隔

        except Exception as e:
            self.rtsp_threads[thread_id]['error'] = f"截图过程中出错: {str(e)}"
        finally:
            cap.release()
            self.rtsp_threads[thread_id]['running'] = False

    def stop_rtsp_capture(self, project_id):
        """
        停止RTSP截图
        
        Args:
            project_id (int): 项目ID
        """
        thread_id = f"rtsp_{project_id}"
        if thread_id in self.rtsp_threads:
            self.rtsp_threads[thread_id]['running'] = False

    def get_rtsp_status(self, project_id):
        """
        获取RTSP截图状态
        
        Args:
            project_id (int): 项目ID
            
        Returns:
            dict: RTSP截图状态
        """
        thread_id = f"rtsp_{project_id}"
        return self.rtsp_threads.get(thread_id, {})

    def discover_onvif_devices(self):
        """
        使用WS-Discovery发现局域网内的ONVIF设备
        
        Returns:
            list: 设备列表 [{ip, port, name}, ...]
        """
        # 实现WS-Discovery协议来发现ONVIF设备
        import socket
        import uuid

        # WS-Discovery Probe消息
        probe_message = f'''<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope
            xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
            xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:tns="http://schemas.xmlsoap.org/ws/2005/04/discovery">
            <soap:Header>
                <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
                <wsa:MessageID>urn:uuid:{uuid.uuid4()}</wsa:MessageID>
                <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
            </soap:Header>
            <soap:Body>
                <tns:Probe />
            </soap:Body>
        </soap:Envelope>'''

        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)  # 5秒超时

        # 设置广播
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        devices = []

        try:
            # 发送Probe消息到WS-Discovery多播地址
            sock.sendto(probe_message.encode('utf-8'), ('239.255.255.250', 3702))

            # 接收响应
            while True:
                try:
                    data, addr = sock.recvfrom(1024)
                    response = data.decode('utf-8')

                    # 解析响应，提取设备信息
                    if 'onvif' in response.lower() or 'www.onvif.org' in response:
                        ip, port = addr
                        # 简化处理，实际应该解析XML获取详细信息
                        devices.append({
                            'ip': ip,
                            'port': 80,  # 默认端口，实际应该从响应中解析
                            'name': f'ONVIF_Camera_{ip}'
                        })
                except socket.timeout:
                    break  # 超时后停止接收

        except Exception as e:
            print(f"设备发现过程中出错: {e}")
        finally:
            sock.close()

        return devices

    def get_onvif_profiles(self, device_ip, device_port, username, password):
        """
        获取ONVIF设备的配置文件列表
        
        Args:
            device_ip (str): 设备IP地址
            device_port (int): 设备端口
            username (str): 用户名
            password (str): 密码
            
        Returns:
            list: 配置文件列表 [{token, name}, ...]
        """
        try:
            # 构建ONVIF设备服务URL
            device_service_url = f"http://{device_ip}:{device_port}/onvif/device_service"

            # 获取服务信息
            services = self._get_onvif_services(device_service_url, username, password)
            media_service_url = services.get('media', f"http://{device_ip}:{device_port}/onvif/media_service")

            # 获取配置文件
            profiles = self._get_profiles(media_service_url, username, password)
            return profiles
        except Exception as e:
            print(f"获取ONVIF配置文件时出错: {e}")
            return []

    def _get_onvif_services(self, device_service_url, username, password):
        """获取ONVIF服务列表"""
        # 构建SOAP请求
        soap_body = '''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
                       xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
            <soap:Header/>
            <soap:Body>
                <tds:GetServices>
                    <tds:IncludeCapability>false</tds:IncludeCapability>
                </tds:GetServices>
            </soap:Body>
        </soap:Envelope>'''

        # 发送请求
        response = self._send_soap_request(device_service_url, soap_body, username, password)

        # 解析响应
        services = {}
        if response:
            try:
                # 定义命名空间
                namespaces = {
                    'soap': 'http://www.w3.org/2003/05/soap-envelope',
                    'tds': 'http://www.onvif.org/ver10/device/wsdl',
                    'tt': 'http://www.onvif.org/ver10/schema'
                }

                root = ET.fromstring(response)
                for service in root.findall('.//tds:Service', namespaces):
                    namespace_elem = service.find('tds:Namespace', namespaces)
                    xaddr_elem = service.find('tds:XAddr', namespaces)

                    if namespace_elem is not None and xaddr_elem is not None:
                        ns = namespace_elem.text
                        addr = xaddr_elem.text
                        if ns and addr:
                            if 'media' in ns.lower():
                                services['media'] = addr
                            elif 'imaging' in ns.lower():
                                services['imaging'] = addr
            except Exception as e:
                print(f"解析服务信息时出错: {e}")

        return services

    def _get_profiles(self, media_service_url, username, password):
        """获取配置文件列表"""
        # 构建SOAP请求
        soap_body = '''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
                       xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <soap:Header/>
            <soap:Body>
                <trt:GetProfiles/>
            </soap:Body>
        </soap:Envelope>'''

        # 发送请求
        response = self._send_soap_request(media_service_url, soap_body, username, password)

        # 解析响应
        profiles = []
        if response:
            try:
                # 定义命名空间
                namespaces = {
                    'soap': 'http://www.w3.org/2003/05/soap-envelope',
                    'trt': 'http://www.onvif.org/ver10/media/wsdl',
                    'tt': 'http://www.onvif.org/ver10/schema'
                }

                root = ET.fromstring(response)
                for profile in root.findall('.//trt:Profiles', namespaces):
                    token = profile.get('token')
                    name_element = profile.find('tt:Name', namespaces)
                    name = name_element.text if name_element is not None else token

                    if token:
                        profiles.append({
                            'token': token,
                            'name': name
                        })
            except Exception as e:
                print(f"解析配置文件时出错: {e}")

        return profiles

    def get_snapshot_uri(self, media_service_url, profile_token, username, password):
        """获取快照URI"""
        # 构建SOAP请求
        soap_body = f'''<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
                       xmlns:trt="http://www.onvif.org/ver10/media/wsdl">
            <soap:Header/>
            <soap:Body>
                <trt:GetSnapshotUri>
                    <trt:ProfileToken>{profile_token}</trt:ProfileToken>
                </trt:GetSnapshotUri>
            </soap:Body>
        </soap:Envelope>'''

        # 发送请求
        response = self._send_soap_request(media_service_url, soap_body, username, password)

        # 解析响应
        snapshot_uri = None
        if response:
            try:
                # 定义命名空间
                namespaces = {
                    'soap': 'http://www.w3.org/2003/05/soap-envelope',
                    'trt': 'http://www.onvif.org/ver10/media/wsdl',
                    'tt': 'http://www.onvif.org/ver10/schema'
                }

                root = ET.fromstring(response)
                uri_element = root.find('.//tt:Uri', namespaces)
                if uri_element is not None:
                    snapshot_uri = uri_element.text
            except Exception as e:
                print(f"解析快照URI时出错: {e}")

        return snapshot_uri

    def capture_onvif_images(self, project_id, device_ip, device_port, username, password,
                             profile_token, interval, max_count):
        """
        从ONVIF设备截取图片并保存到项目目录
        
        Args:
            project_id (int): 项目ID
            device_ip (str): 设备IP
            device_port (int): 设备端口
            username (str): 用户名
            password (str): 密码
            profile_token (str): 配置文件token
            interval (int): 截图间隔（秒）
            max_count (int): 最大截图数量
        """
        thread_id = f"onvif_{project_id}_{profile_token}"
        self.onvif_threads[thread_id] = {
            'running': True,
            'captured_count': 0,
            'max_count': max_count
        }

        try:
            # 获取设备服务URL
            device_service_url = f"http://{device_ip}:{device_port}/onvif/device_service"

            # 获取媒体服务URL
            services = self._get_onvif_services(device_service_url, username, password)
            media_service_url = services.get('media', f"http://{device_ip}:{device_port}/onvif/media_service")

            # 获取快照URI
            snapshot_uri = self.get_snapshot_uri(media_service_url, profile_token, username, password)
            if not snapshot_uri:
                self.onvif_threads[thread_id]['error'] = "无法获取快照URI"
                return

            # 确保项目上传目录存在
            upload_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            project_upload_dir = os.path.join(os.getcwd(), 'uploads')  # 使用固定目录

            while (self.onvif_threads[thread_id]['running'] and
                   self.onvif_threads[thread_id]['captured_count'] < max_count):

                try:
                    # 获取快照
                    auth = HTTPDigestAuth(username, password)
                    response = requests.get(snapshot_uri, auth=auth, timeout=10)

                    # 如果摘要认证失败，尝试基本认证
                    if response.status_code == 401:
                        auth = HTTPBasicAuth(username, password)
                        response = requests.get(snapshot_uri, auth=auth, timeout=10)

                    if response.status_code == 200:
                        # 生成文件名
                        timestamp = int(datetime.now().timestamp() * 1000)
                        filename = f"{timestamp}_onvif_{profile_token}.jpg"
                        file_path = os.path.join(project_upload_dir, filename)

                        # 保存图片
                        with open(file_path, 'wb') as f:
                            f.write(response.content)

                        # 获取图片尺寸
                        img = PILImage.open(file_path)
                        width, height = img.size

                        # 计算相对路径和POSIX路径
                        relative_path = ProjectService.get_relative_path(file_path)
                        posix_path = ProjectService.get_posix_path(relative_path)

                        # 保存到数据库
                        from app import create_app
                        application = create_app()
                        with application.app_context():
                            image = Image(
                                filename=filename,
                                original_filename=f"onvif_capture_{profile_token}_{timestamp}.jpg",
                                path=posix_path,
                                project_id=project_id,
                                width=width,
                                height=height
                            )
                            db.session.add(image)
                            db.session.commit()

                        self.onvif_threads[thread_id]['captured_count'] += 1
                    else:
                        self.onvif_threads[thread_id]['error'] = f"获取快照失败: {response.status_code}"

                except Exception as e:
                    self.onvif_threads[thread_id]['error'] = f"获取快照时出错: {str(e)}"

                # 等待下一次截图
                time.sleep(interval)

        except Exception as e:
            self.onvif_threads[thread_id]['error'] = f"截图过程中出错: {str(e)}"
        finally:
            self.onvif_threads[thread_id]['running'] = False

    def capture_onvif_images_improved(self, project_id, device_ip, device_port, username, password,
                                      profile_token, interval, max_count):
        """
        从ONVIF设备截取图片并保存到项目目录（改进版，解决缓存问题）
        
        Args:
            project_id (int): 项目ID
            device_ip (str): 设备IP
            device_port (int): 设备端口
            username (str): 用户名
            password (str): 密码
            profile_token (str): 配置文件token
            interval (int): 截图间隔（秒）
            max_count (int): 最大截图数量
        """
        thread_id = f"onvif_{project_id}_{profile_token}"
        self.onvif_threads[thread_id] = {
            'running': True,
            'captured_count': 0,
            'max_count': max_count
        }

        try:
            # 获取设备服务URL
            device_service_url = f"http://{device_ip}:{device_port}/onvif/device_service"

            # 获取媒体服务URL
            services = self._get_onvif_services(device_service_url, username, password)
            media_service_url = services.get('media', f"http://{device_ip}:{device_port}/onvif/media_service")

            # 获取快照URI
            snapshot_uri = self.get_snapshot_uri(media_service_url, profile_token, username, password)
            if not snapshot_uri:
                self.onvif_threads[thread_id]['error'] = "无法获取快照URI"
                return

            # 确保项目上传目录存在
            upload_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            project_upload_dir = os.path.join(os.getcwd(), 'uploads')  # 使用固定目录

            # 记录开始时间，用于精确控制时间间隔
            start_time = time.time()

            while (self.onvif_threads[thread_id]['running'] and
                   self.onvif_threads[thread_id]['captured_count'] < max_count):

                try:
                    # 计算下一次截图的准确时间
                    next_capture_time = start_time + (self.onvif_threads[thread_id]['captured_count'] + 1) * interval

                    # 当前时间
                    current_time = time.time()

                    # 如果还没到截图时间，则等待
                    if current_time < next_capture_time:
                        sleep_time = next_capture_time - current_time
                        time.sleep(sleep_time)

                    # 添加随机延迟，避免设备返回缓存图像
                    random_delay = random.uniform(0.1, 0.3)  # 减少随机延迟范围
                    time.sleep(random_delay)

                    # 在URL中添加随机参数，进一步避免各层缓存
                    separator = '&' if '?' in snapshot_uri else '?'
                    random_param = f"{separator}_={int(time.time() * 1000)}_{random.randint(1000, 9999)}"
                    snapshot_uri_with_param = snapshot_uri + random_param

                    # 获取快照
                    auth = HTTPDigestAuth(username, password)
                    response = requests.get(snapshot_uri_with_param, auth=auth, timeout=10)

                    # 如果摘要认证失败，尝试基本认证
                    if response.status_code == 401:
                        auth = HTTPBasicAuth(username, password)
                        response = requests.get(snapshot_uri_with_param, auth=auth, timeout=10)

                    if response.status_code == 200:
                        # 生成文件名
                        timestamp = int(datetime.now().timestamp() * 1000)
                        filename = f"{timestamp}_onvif_{profile_token}.jpg"
                        file_path = os.path.join(project_upload_dir, filename)

                        # 保存图片
                        with open(file_path, 'wb') as f:
                            f.write(response.content)

                        # 检查文件是否有效
                        if os.path.getsize(file_path) < 1024:  # 文件太小，可能是无效图像
                            os.remove(file_path)  # 删除无效文件
                            self.onvif_threads[thread_id]['error'] = "获取到无效图像文件"
                            continue

                        # 获取图片尺寸
                        img = PILImage.open(file_path)
                        width, height = img.size

                        # 计算相对路径和POSIX路径
                        relative_path = ProjectService.get_relative_path(file_path)
                        posix_path = ProjectService.get_posix_path(relative_path)

                        # 保存到数据库
                        from app import create_app
                        application = create_app()
                        with application.app_context():
                            image = Image(
                                filename=filename,
                                original_filename=f"onvif_capture_{profile_token}_{timestamp}.jpg",
                                path=posix_path,
                                project_id=project_id,
                                width=width,
                                height=height
                            )
                            db.session.add(image)
                            db.session.commit()

                        self.onvif_threads[thread_id]['captured_count'] += 1
                    else:
                        self.onvif_threads[thread_id]['error'] = f"获取快照失败: {response.status_code}"

                except Exception as e:
                    self.onvif_threads[thread_id]['error'] = f"获取快照时出错: {str(e)}"

                # 注意：这里不再使用额外的time.sleep，而是通过计算时间来控制间隔

        except Exception as e:
            self.onvif_threads[thread_id]['error'] = f"截图过程中出错: {str(e)}"
        finally:
            self.onvif_threads[thread_id]['running'] = False

    def stop_onvif_capture(self, project_id, profile_token):
        """
        停止ONVIF截图
        
        Args:
            project_id (int): 项目ID
            profile_token (str): 配置文件token
        """
        thread_id = f"onvif_{project_id}_{profile_token}"
        if thread_id in self.onvif_threads:
            self.onvif_threads[thread_id]['running'] = False

    def start_onvif_capture(self, project_id, device_ip, device_port, username, password,
                            profile_token, interval, max_count):
        """
        启动ONVIF截图（使用改进版本）
        
        Args:
            project_id (int): 项目ID
            device_ip (str): 设备IP
            device_port (int): 设备端口
            username (str): 用户名
            password (str): 密码
            profile_token (str): 配置文件token
            interval (int): 截图间隔（秒）
            max_count (int): 最大截图数量
        """
        # 启动改进版的ONVIF截图功能
        from app import create_app
        application = create_app()

        def onvif_thread():
            with application.app_context():
                self.capture_onvif_images_improved(project_id, device_ip, device_port, username,
                                                   password, profile_token, interval, max_count)

        thread = threading.Thread(target=onvif_thread)
        thread.daemon = True
        thread.start()

        return thread

    def get_onvif_status(self, project_id, profile_token):
        """
        获取ONVIF截图状态
        
        Args:
            project_id (int): 项目ID
            profile_token (str): 配置文件token
            
        Returns:
            dict: ONVIF截图状态
        """
        thread_id = f"onvif_{project_id}_{profile_token}"
        return self.onvif_threads.get(thread_id, {})

    def _send_soap_request(self, url, soap_body, username, password):
        """发送SOAP请求"""
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'SOAPAction': ''
        }

        try:
            # 尝试使用摘要认证
            auth = HTTPDigestAuth(username, password)
            response = requests.post(url, data=soap_body, headers=headers, auth=auth, timeout=10)

            # 如果摘要认证失败，尝试基本认证
            if response.status_code == 401:
                auth = HTTPBasicAuth(username, password)
                response = requests.post(url, data=soap_body, headers=headers, auth=auth, timeout=10)

            if response.status_code == 200:
                return response.text
            else:
                print(f"SOAP请求失败: {response.status_code}")
                return None

        except Exception as e:
            print(f"发送SOAP请求时出错: {e}")
            return None
