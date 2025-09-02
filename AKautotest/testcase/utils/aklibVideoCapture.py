
import os
import sys

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
if root_path not in sys.path:
    sys.path.append(root_path)

from akcommon_define import *
import cv2
import time
import re
import tempfile
import threading
import shutil
import base64
import traceback
import subprocess
from collections import Counter, deque
from urllib.parse import urlparse
from rapidfuzz import fuzz  # 安装: pip install rapidfuzz


__all__ = [
    'AKVideoCapture',
    'AKRTSPCapture',
    'video_capture_check_image',
    'thread_video_captures_check_image',
    'compress_video',
    'get_camera_capture_ocr_texts',
    'wait_camera_capture_ocr_to_texts',
]


class AKVideoCapture(object):

    def __init__(self, video_url, username=None, password=None, temp_index=None):
        self.video_url = video_url
        if username and password:
            self.video_url = video_url.replace('://', f'://{username}:{password}@')
        self.cap = None
        self.PATH = lambda p: os.path.abspath(p)

        # 生成唯一子目录名
        sub_dir = self._get_unique_subdir_name()

        # 临时目录路径
        base_temp_dir = os.path.join(tempfile.gettempdir(), sub_dir)
        os.makedirs(base_temp_dir, exist_ok=True)

        # 临时文件名
        if temp_index is not None:
            self.TEMP_IMAGE = self.PATH(os.path.join(base_temp_dir, f"temp{temp_index}_screen.png"))
            self.TEMP_VIDEO = self.PATH(os.path.join(base_temp_dir, f"temp{temp_index}_video.mkv"))
        else:
            self.TEMP_IMAGE = self.PATH(os.path.join(base_temp_dir, "temp_screen.png"))
            self.TEMP_VIDEO = self.PATH(os.path.join(base_temp_dir, "temp_video.mkv"))

    def _get_unique_subdir_name(self) -> str:
        """
        根据视频路径或RTSP流地址生成唯一的子目录名
        """
        if '://' in self.video_url:
            # 提取 IP 地址或主机名
            parsed = urlparse(self.video_url)
            host = parsed.hostname or "unknown"
            return f"akvideo_{host}"
        else:
            # 本地文件路径，使用文件名（不含扩展名）
            filename = os.path.basename(self.video_url)
            name, _ = os.path.splitext(filename)
            return f"akvideo_{name}"

    def get_video_size(self):
        aklog_printf('get_video_size')
        if not self.cap:
            self.cap = cv2.VideoCapture(self.video_url)
        width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        high = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        # self.cap.release()
        size = (int(width), int(high))
        aklog_printf(size)
        return size

    def get_video_frame_rate(self, duration=5):
        """有点问题，同样设置为25帧，E16和R29获取的帧率不一样，会差两倍"""
        aklog_printf('get_video_frame_rate')
        if not self.cap:
            self.cap = cv2.VideoCapture(self.video_url)
        time.sleep(2)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        for i in range(3):
            if fps > 60:
                aklog_printf('获取帧率异常: %s，重新获取' % fps)
                time.sleep(2)
                fps = self.cap.get(cv2.CAP_PROP_FPS)
            else:
                aklog_printf(fps)
                return fps

        # 如果获取失败，则重新获取
        aklog_printf('获取帧率失败，改用获取帧数除以时间方法')
        self.cap_release()
        time.sleep(1)
        self.cap = cv2.VideoCapture(self.video_url)
        ret, frame = self.cap.read()
        frame_counts = 0
        # 历史帧
        oldFrame = 0.0  # float类型
        start = time.time()
        end_time = start + duration
        now_time = time.time()
        while now_time < end_time:
            now_time = time.time()
            # 当前帧的位置
            frameTag = self.cap.get(0)
            if ret and frameTag != oldFrame:
                frame_counts += 1
                oldFrame = frameTag  # 成为历史帧
            ret, frame = self.cap.read()
        # print(frame_counts)
        fps = frame_counts / duration
        # 有些机型获取到的帧率会变成两倍大小
        if fps > 50:
            fps = fps / 2
        aklog_printf(fps)
        return fps

    def get_video_bit_rage(self, duration=10):
        """
        获取视频比特率
        如果是rtsp视频流，则保存成视频之后再通过文件大小除以时长来计算码率，会不太准确，只能比较两个码率相差比较大的情况
        """
        aklog_printf()
        self.capture_video(duration, 'mp4v')
        file_size = File_process.get_file_size(self.TEMP_VIDEO, 'KB')
        bit_rate = round(file_size * 8 / duration, 2)
        aklog_printf('bit_rate: %s kbps' % bit_rate)
        return bit_rate

    def capture_video(self, duration=10, codec_fmt='mp4v'):
        """截取视频录像"""
        aklog_printf()
        File_process.remove_file(self.TEMP_VIDEO)
        try:
            if not self.cap:
                self.cap = cv2.VideoCapture(self.video_url)

            frame_s = self.get_video_frame_rate()
            aklog_printf(f'frame: {frame_s}')
            fourcc = cv2.VideoWriter_fourcc(*codec_fmt)
            size = (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            aklog_printf(f'size: {size}')
            ret, frame = self.cap.read()
            time_frame = frame_s * duration
            video_writer = cv2.VideoWriter(self.TEMP_VIDEO, fourcc, frame_s, size, True)  # 参数：视频文件名，格式，每秒帧数，宽高，是否灰度
            num = 0
            while ret:
                ret, frame = self.cap.read()
                video_writer.write(frame)
                num = num + 1
                if num == time_frame:
                    video_writer.release()
                    break
            # self.cap.release()
        except:
            aklog_printf(traceback.format_exc())
        return self

    def capture_image(self, wait_time=None):
        """截取视频流图像"""
        File_process.remove_file(self.TEMP_IMAGE)
        try:
            # cap = cv2.VideoCapture(self.video_url)
            if wait_time:
                time.sleep(wait_time)
            ret, frame = self.cap.read()
            if ret:
                cv2.imwrite(self.TEMP_IMAGE, frame)  # 存储为图像
            # self.cap.release()
            # cv2.destroyAllWindows()
        except:
            aklog_printf(traceback.format_exc())
        return self

    def screen_shot(self, max_width=None, max_height=None, quality=70):
        """
        截取视频流图像，按需压缩后返回base64编码的JPEG图像数据

        Args:
            max_width (int or None): 压缩后图片最大宽度，None表示不限制
            max_height (int or None): 压缩后图片最大高度，None表示不限制
            quality (int): JPEG压缩质量，1-100，默认70

        Returns:
            str: base64编码的JPEG图像数据，失败返回None

        关键步骤说明：
            1. 读取视频帧
            2. 按比例缩放（如超出max_width或max_height）
            3. JPEG压缩编码
            4. 转base64字符串
        """
        try:
            # 1. 读取视频帧
            ret, frame = self.cap.read()
            if not ret:
                aklog_error("视频流读取失败，未获取到帧。")
                param_append_screenshots_imgs('')
                return None

            # 2. 按比例缩放（仅当超出max_width或max_height）
            h, w = frame.shape[:2]
            scale_w = scale_h = 1.0

            if max_width is not None and w > max_width:
                scale_w = max_width / w
            if max_height is not None and h > max_height:
                scale_h = max_height / h

            # 取最小缩放因子，保证宽高都不超过限制
            scale = min(scale_w, scale_h)
            if scale < 1.0:
                new_size = (int(w * scale), int(h * scale))
                frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)
                aklog_debug(f"原始分辨率: {w}x{h}，缩放后: {new_size[0]}x{new_size[1]}")  # 行注释：缩放图片以减小体积

            # 3. JPEG压缩编码
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            ret, buf = cv2.imencode('.jpg', frame, encode_param)
            if not ret:
                aklog_error("图像编码为JPEG失败。")
                param_append_screenshots_imgs('')
                return None

            # 4. 转base64字符串
            img_base64 = base64.b64encode(buf).decode("utf-8")
        except Exception as e:
            aklog_error(f"捕获图像或编码base64时发生异常: {e}")
            aklog_debug(traceback.format_exc())
            param_append_screenshots_imgs('')
            return None

        aklog_debug('screen_shot_as_base64, the screenshots is shown below: ')
        param_append_screenshots_imgs(img_base64)
        return img_base64

    def save_image_to_file(self, img_file):
        """将截屏文件保存到指定目录下"""
        try:
            if not os.path.exists(self.TEMP_IMAGE):
                aklog_printf('截取图片不存在')
                return False
            save_dir, file_name = os.path.split(img_file)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            shutil.copyfile(self.TEMP_IMAGE, img_file)
            aklog_debug(f'save image file to: {img_file}')
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    def save_video_to_file(self, video_file):
        """将视频文件保存到指定目录下"""
        try:
            if not os.path.exists(self.TEMP_VIDEO):
                aklog_printf('保存的临时视频文件不存在')
                return False
            save_dir, file_name = os.path.split(video_file)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            shutil.copyfile(self.TEMP_VIDEO, video_file)
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    def is_correct_video_image(self, duration=10, interval=2):
        """判断视频图像是否正常"""
        aklog_printf('is_correct_video_image')
        if not self.cap:
            self.cap = cv2.VideoCapture(self.video_url)
            time.sleep(2)
        try:
            # 历史帧
            oldFrame = 0.0  # float类型

            start_time = time.time()
            end_time = start_time + duration
            now_time = start_time
            n = 1
            flag = True

            while now_time < end_time:
                ret, frame = self.cap.read()
                now_time = time.time()
                # 当前帧的位置
                frameTag = self.cap.get(0)

                # 未获得帧
                if not ret:
                    flag = False
                    continue

                # 相机卡帧（一直卡在同一帧上）
                if (oldFrame == frameTag) and (oldFrame != 0.0):
                    flag = False
                    continue
                else:
                    oldFrame = frameTag  # 成为历史帧
                    flag = True

                # 间隔时间去判断视频图像是否为纯色（主要是黑屏），以此来判断图像是否正常
                if flag and now_time >= start_time + interval * n:
                    n += 1
                    cv2.imwrite(self.TEMP_IMAGE, frame)
                    if check_image_is_pure_color(self.TEMP_IMAGE, 0.9):
                        aklog_printf('视频图像异常')
                        # self.cap.release()
                        File_process.remove_file(self.TEMP_IMAGE)
                        return False
                    else:
                        File_process.remove_file(self.TEMP_IMAGE)
                        continue
            if not flag:
                # self.cap.release()
                aklog_printf('获取视频异常')
                return False
            else:
                # self.cap.release()
                return True

        except:
            aklog_printf("异常错误，请检查：%s" % traceback.format_exc())
            # self.cap.release()
            return False

    def wait_video_image(self, percent=0.8, timeout=10):
        """等待视频画面出现"""
        aklog_printf()
        if not self.cap:
            self.cap = cv2.VideoCapture(self.video_url)
        try:
            # 历史帧
            oldFrame = 0.0  # float类型
            end_time = time.time() + timeout
            while time.time() < end_time:
                ret, frame = self.cap.read()
                # 当前帧的位置
                frameTag = self.cap.get(0)
                # 未获得帧
                if not ret:
                    continue
                # 相机卡帧（一直卡在同一帧上）
                if (oldFrame == frameTag) and (oldFrame != 0.0):
                    continue
                else:
                    oldFrame = frameTag  # 成为历史帧
                    # 间隔时间去判断视频图像是否为纯色（主要是黑屏），以此来判断图像是否正常
                    File_process.remove_file(self.TEMP_IMAGE)
                    cv2.imwrite(self.TEMP_IMAGE, frame)
                    if not check_image_is_pure_color(self.TEMP_IMAGE, percent):
                        aklog_printf('视频图像正常')
                        return True
                time.sleep(1)
                continue
            aklog_printf('获取视频异常')
            return False
        except:
            aklog_printf("异常错误，请检查：%s" % traceback.format_exc())
            return False

    def stable_ocr_text(self, retry=5, min_count=4) -> str:
        """
        多次截图 + OCR，返回稳定识别文本（只保留字母和数字）

        Args:
            retry (int): OCR 重试次数
            min_count (int): 至少匹配次数
        Returns:
            str: 稳定识别结果（拼接后的纯字母数字字符串）
        """
        tmp_contents = []

        for i in range(retry):
            self.capture_image()
            texts = image_ocr_to_texts(self.TEMP_IMAGE)
            if texts:
                joined_text = ''.join(texts)
                cleaned_text = re.sub(r'[^A-Za-z0-9]', '', joined_text)
                aklog_debug(f"OCR 第 {i + 1} 次识别结果: {cleaned_text}")
                tmp_contents.append(cleaned_text)
            time.sleep(0.2)

        stable_text = ''
        if tmp_contents:
            # 统计出现频率
            most_common = Counter(tmp_contents).most_common()
            # 只保留出现次数 >= min_count 的文本
            for text, count in most_common:
                if count >= min_count:
                    stable_text = text

        aklog_debug(f"稳定识别文本: {stable_text}")
        return stable_text

    def cap_release(self):
        if self.cap:
            self.cap.release()
            self.cap = None


class AKRTSPCapture(object):

    def __init__(self, rtsp_url, username=None, password=None, temp_index=None):
        self.rtsp_url = rtsp_url
        parsed = urlparse(self.rtsp_url)
        self._host = parsed.hostname or "unknown"
        if username and password:
            self.rtsp_url = rtsp_url.replace('://', f'://{username}:{password}@')
        self.cap = None
        self.latest_frame = None
        self.frame_count = 0  # 帧计数器，记录已读取帧数
        self.frame_buffer = deque(maxlen=500)  # 最多缓存 500 帧，防止爆内存
        self.frame_buffer_lock = threading.Lock()
        self.running = True
        self.frame_lock = threading.Lock()
        self.thread = None

        self.PATH = lambda p: os.path.abspath(p)

        # 临时目录路径
        base_temp_dir = os.path.join(tempfile.gettempdir(), f"akrtsp_{self._host}")
        os.makedirs(base_temp_dir, exist_ok=True)

        # 临时文件名
        if temp_index is not None:
            self.TEMP_IMAGE = self.PATH(os.path.join(base_temp_dir, f"temp{temp_index}_screen.png"))
            self.TEMP_VIDEO = self.PATH(os.path.join(base_temp_dir, f"temp{temp_index}_video.mp4"))
        else:
            self.TEMP_IMAGE = self.PATH(os.path.join(base_temp_dir, "temp_screen.png"))
            self.TEMP_VIDEO = self.PATH(os.path.join(base_temp_dir, "temp_video.mp4"))

        # 录像相关
        self.recording = False
        self.video_writer = None
        self.record_thread = None

        # 先删除临时文件
        self.clear_temp_fle()

    @property
    def host(self):
        return self._host

    def clear_temp_fle(self):
        if os.path.exists(self.TEMP_IMAGE):
            os.remove(self.TEMP_IMAGE)
        if os.path.exists(self.TEMP_VIDEO):
            os.remove(self.TEMP_VIDEO)

    def _update_frame(self):
        """后台线程持续读取帧，支持断流自动重连"""
        fail_count = 0
        while self.running:
            try:
                if self.cap is None or not self.cap.isOpened():
                    aklog_debug("RTSP流断开，尝试重连")
                    self.cap = cv2.VideoCapture(self.rtsp_url)
                    time.sleep(1)
                    continue
                ret, frame = self.cap.read()
                if ret:
                    with self.frame_lock:
                        self.latest_frame = frame
                        self.frame_count += 1  # 每读取到一帧，计数加1
                    # 推入缓冲队列
                    if self.recording:
                        with self.frame_buffer_lock:
                            self.frame_buffer.append(frame.copy())
                    fail_count = 0
                else:
                    fail_count += 1
                    if fail_count >= 10:
                        aklog_debug("连续10次读取帧失败，重连RTSP流")
                        self.cap.release()
                        self.cap = None
                        fail_count = 0
                    time.sleep(0.1)
            except Exception as e:
                aklog_error(f"拉流线程异常: {e}")
                aklog_debug(traceback.format_exc())
                time.sleep(1)

    def thread_start_video(self):
        """启动视频流拉流线程，防止重复启动"""
        aklog_debug()
        if self.thread and self.thread.is_alive():
            aklog_debug("视频流线程已启动，无需重复启动")
            return
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.rtsp_url)
        self.running = True
        self.thread = threading.Thread(target=self._update_frame, daemon=True)
        self.thread.start()

    def _record_from_buffer(self):
        """录像线程，从缓冲区写入视频文件"""
        while self.recording or len(self.frame_buffer) > 0:
            with self.frame_buffer_lock:
                if self.frame_buffer:
                    frame = self.frame_buffer.popleft()
                else:
                    frame = None
            if frame is not None:
                self.video_writer.write(frame)
            else:
                time.sleep(0.01)
        aklog_debug('录像已结束')

    def start_recording(self, codec_fmt='mp4v'):
        """开始录像"""
        if self.recording:
            aklog_debug("录像已在进行中")
            return
        if self.latest_frame is None:
            self.wait_video_image()
        if self.latest_frame is None:
            aklog_error("暂无视频帧，无法开始录像")
            return

        # 1. 清空缓冲区，确保只录制从现在开始的帧
        with self.frame_buffer_lock:
            self.frame_buffer.clear()

        # 初始化 VideoWriter
        if os.path.exists(self.TEMP_VIDEO):
            os.remove(self.TEMP_VIDEO)
        height, width = self.latest_frame.shape[:2]

        # 用实时检测帧率（如果 cap 有值，否则默认 25）
        src_fps = int(self.cap.get(cv2.CAP_PROP_FPS) or 25)
        fourcc = cv2.VideoWriter_fourcc(*codec_fmt)  # 使用 H.264 编码
        self.video_writer = cv2.VideoWriter(self.TEMP_VIDEO, fourcc, src_fps, (width, height))
        aklog_debug(f"开始录像，保存至: {self.TEMP_VIDEO}, fps: {src_fps}")
        self.recording = True
        self.record_thread = threading.Thread(target=self._record_from_buffer, daemon=True)
        self.record_thread.start()

    def stop_recording(self, record_file=None):
        """停止录像并释放资源"""
        if not self.recording:
            aklog_debug("录像未开始")
            return
        self.recording = False
        if self.record_thread:
            self.record_thread.join(timeout=3)
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        if record_file and os.path.exists(self.TEMP_VIDEO):
            # 压缩视频文件体积
            if not compress_video(self.TEMP_VIDEO, record_file):
                File_process.copy_file(self.TEMP_VIDEO, record_file)
            aklog_debug(f"录像已保存: {record_file}")
        with self.frame_buffer_lock:
            self.frame_buffer.clear()

    def capture_image(self):
        """保存当前最新帧"""
        frame = None
        frame_index = 0  # 当前帧序号
        with self.frame_lock:
            if self.latest_frame is not None:
                frame = self.latest_frame.copy()
                frame_index = self.frame_count  # 获取当前帧序号
        if frame is not None:
            if os.path.exists(self.TEMP_IMAGE):
                os.remove(self.TEMP_IMAGE)
            cv2.imwrite(self.TEMP_IMAGE, frame)
            aklog_debug(f"当前截图为视频流读取的第 {frame_index} 帧")  # 日志输出帧序号
            return True
        else:
            aklog_warn("未能获取到有效帧，截图失败")
            return False

    def screen_shot(self, max_width=None, max_height=None, quality=70, reshot=True):
        """
        截取视频流图像，按需压缩后返回base64编码的JPEG图像数据

        Args:
            max_width (int or None): 压缩后图片最大宽度，None表示不限制
            max_height (int or None): 压缩后图片最大高度，None表示不限制
            quality (int): JPEG压缩质量，1-100，默认70
            reshot (bool): 是否重新截图
                - True: 从最新帧self.latest_frame截取
                - False: 使用上一次保存的临时图片文件self.TEMP_IMAGE
        Returns:
            str: base64编码的JPEG图像数据，失败返回None
        """
        try:
            frame = None
            if reshot or not os.path.exists(self.TEMP_IMAGE):
                # 1. 从视频流读取最新帧
                with self.frame_lock:
                    frame = self.latest_frame.copy() if self.latest_frame is not None else None
                if frame is None:
                    aklog_warn("未能获取到有效帧，截图失败")
                    param_append_screenshots_imgs('')
                    return None
            else:
                frame = cv2.imread(self.TEMP_IMAGE)  # 行注释：从本地读取上一次截图
                if frame is None:
                    aklog_warn(f"无法读取临时截图文件: {self.TEMP_IMAGE}")
                    param_append_screenshots_imgs('')
                    return None

            # 2. 按比例缩放（仅当超出max_width或max_height）
            h, w = frame.shape[:2]
            scale_w = scale_h = 1.0
            if max_width is not None and w > max_width:
                scale_w = max_width / w
            if max_height is not None and h > max_height:
                scale_h = max_height / h
            scale = min(scale_w, scale_h)
            if scale < 1.0:
                new_size = (int(w * scale), int(h * scale))
                frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)
                aklog_debug(f"原始分辨率: {w}x{h}，缩放后: {new_size[0]}x{new_size[1]}")

            # 3. 将frame保存到临时文件（便于下次reshot=False复用）
            cv2.imwrite(self.TEMP_IMAGE, frame)

            # 4. JPEG压缩编码
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            ret, buf = cv2.imencode('.jpg', frame, encode_param)
            if not ret:
                aklog_error("图像编码为JPEG失败。")
                param_append_screenshots_imgs('')
                return None

            # 5. 转base64字符串
            img_base64 = base64.b64encode(buf).decode("utf-8")

        except Exception as e:
            aklog_error(f"捕获图像或编码base64时发生异常: {e}")
            aklog_debug(traceback.format_exc())
            param_append_screenshots_imgs('')
            return None

        aklog_debug('screen_shot_as_base64, the screenshots is shown below: ')
        param_append_screenshots_imgs(img_base64)
        return img_base64

    def save_image_to_file(self, img_file):
        """将截屏文件保存到指定目录下"""
        try:
            if not os.path.exists(self.TEMP_IMAGE):
                aklog_printf('截取图片不存在')
                return False
            save_dir = os.path.dirname(img_file)
            os.makedirs(save_dir, exist_ok=True)
            shutil.copyfile(self.TEMP_IMAGE, img_file)
            aklog_debug(f'save image file to: {img_file}')
            return True
        except:
            aklog_printf(traceback.format_exc())
            return False

    def wait_video_image(self, timeout=10, stop_event: threading.Event = None):
        """等待视频画面出现"""
        aklog_printf()
        try:
            end_time = time.time() + timeout
            while time.time() < end_time:
                if stop_event and stop_event.is_set():
                    break
                with self.frame_lock:
                    frame = self.latest_frame.copy() if self.latest_frame is not None else None
                # 未获得有效帧
                if frame is None:
                    time.sleep(0.01)
                    continue
                # 1. 先判断是否不是全黑（极快）
                if self.is_not_black(frame, threshold=10):
                    # 2. 再用缩放纯色检测（极快）
                    if not self.fast_is_pure_color(frame):
                        self.clear_temp_fle()
                        aklog_printf('视频图像正常')
                        return True
                    else:
                        aklog_printf('画面亮点过少，可能是真黑屏')  # 新增日志
                time.sleep(0.1)
            aklog_printf('获取视频异常')
            self.screen_shot()
            return False
        except:
            aklog_printf("异常错误，请检查：%s" % traceback.format_exc())
            return False

    @staticmethod
    def fast_is_pure_color(
            frame, percent=0.9, size=(320, 240),
            dark_threshold=20, min_bright_pixel_ratio=0.001):
        """
        缩放后判断是否纯色（支持深色背景+小面积亮文字场景）
        Args:
            frame: 输入帧(BGR)
            percent: 单一颜色最大占比阈值
            size: 缩放尺寸
            dark_threshold: 灰度低于此值的像素视为暗像素
            min_bright_pixel_ratio: 亮像素最小占比
        """
        # 缩放图像，加快处理速度
        small = cv2.resize(frame, size, interpolation=cv2.INTER_LINEAR)

        # 灰度图计算亮像素占比
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        bright_ratio = np.count_nonzero(gray > dark_threshold) / gray.size
        if bright_ratio >= min_bright_pixel_ratio:
            return False  # 有足够亮细节 => 认为不是纯色

        # 边缘检测，用于检测小面积文字/细节
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.count_nonzero(edges) / edges.size
        if edge_density > 0.001:  # 0.1%的边缘像素即可判定
            return False

        # 检查颜色通道波动
        color_std = np.std(small.reshape(-1, 3), axis=0).mean()
        if color_std > 3:
            return False

        # 计算单一颜色占比
        pixels_tuple = [tuple(p) for p in small.reshape(-1, 3)]
        colors, counts = np.unique(pixels_tuple, axis=0, return_counts=True)
        max_idx = np.argmax(counts)  # 占比最高颜色的索引
        max_color = colors[max_idx]  # BGR颜色元组
        max_ratio = counts[max_idx] / counts.sum()

        # 如果判定为纯色，增加日志输出颜色和占比
        if max_ratio >= percent:
            aklog_debug(
                f"纯色判定: 占比最高颜色 {max_color} 占比 {max_ratio:.2%} (阈值: {percent:.0%})"
            )
            return True

        return False

    @staticmethod
    def is_not_black(frame, threshold=10):
        """
        判断帧是否不是全黑（有像素大于阈值就认为有画面）
        """
        return np.any(frame > threshold)

    def capture_ocr_to_texts(self, ocr_type=None) -> list:
        self.capture_image()
        return image_ocr_to_texts(self.TEMP_IMAGE, ocr_type=ocr_type)

    def ocr_stable_keywords(
            self,
            retry: int = 5,
            min_count: int = 3,
            coverage_threshold: float = 1.0,
            similarity_threshold: int = 85,
    ) -> List[str]:
        """
        多次截图 + OCR，提取多个稳定字母关键字（支持空格、相似度聚类）

        Args:
            retry (int): OCR 重试次数
            min_count (int): 稳定识别的最小出现次数
            coverage_threshold (float): 覆盖率要求（0~1）
            similarity_threshold (int): 模糊匹配相似度阈值（0-100）

        Returns:
            List[str]: 稳定的字母关键字列表
        """
        # 分组结构：{group_id: {"representative": str, "variants": [], "rounds": set()}}
        groups: Dict[int, Dict] = {}
        group_id_counter = 0

        for round_idx in range(retry):
            texts = self.capture_ocr_to_texts()

            if not texts:
                aklog_debug(f"OCR 第 {round_idx + 1} 次OCR返回为空")
                continue

            for raw_text in texts:
                alpha_part = extract_alpha_with_spaces(raw_text)
                if not alpha_part:
                    continue

                # 查找已存在的相似组
                matched_group_id = None
                for gid, ginfo in groups.items():
                    if fuzz.ratio(alpha_part.lower(), ginfo["representative"].lower()) >= similarity_threshold:
                        matched_group_id = gid
                        break

                if matched_group_id is not None:
                    groups[matched_group_id]["variants"].append(alpha_part)
                    groups[matched_group_id]["rounds"].add(round_idx)
                else:
                    # 新建分组
                    groups[group_id_counter] = {
                        "representative": alpha_part,
                        "variants": [alpha_part],
                        "rounds": {round_idx},
                    }
                    group_id_counter += 1

            aklog_debug(f"OCR 第 {round_idx + 1} 次识别: {[extract_alpha_with_spaces(t) for t in texts]}")
            time.sleep(0.2)

        final_stable_words: List[str] = []

        for gid, ginfo in groups.items():
            occur_times = len(ginfo["rounds"])
            coverage = occur_times / retry

            if coverage >= coverage_threshold:
                # 统计该组内出现频率最高的变体作为稳定值
                most_common = Counter(ginfo["variants"]).most_common()
                stable_word = ''
                for text, count in most_common:
                    if count >= min_count:
                        stable_word = text
                        aklog_debug(f"[OCR稳定] '{text}' 覆盖率 {coverage:.2f}")
                        break

                # 仍未选出，用相似度总分兜底
                if not stable_word and len(set(ginfo["variants"])) > 1:
                    best_text = max(
                        set(ginfo["variants"]),
                        key=lambda cand: sum(fuzz.ratio(cand, other) for other in ginfo["variants"] if other != cand)
                    )
                    stable_word = best_text
                    aklog_debug(f"[OCR不稳定] 组 {gid} 投票选出: {stable_word}")

                if stable_word:
                    final_stable_words.append(stable_word)
            else:
                aklog_debug(f"[OCR丢弃] 组 {gid} 覆盖率 {coverage:.2f} < 阈值 {coverage_threshold:.2f}")

        aklog_debug(f"最终稳定关键字列表: {final_stable_words}")
        return final_stable_words

    def release(self):
        """释放RTSP视频流资源，线程安全，支持重复调用"""
        aklog_debug("准备释放RTSP流资源")
        try:
            # 如果没有 cap 对象，说明已经释放过
            if not self.cap and not (self.thread and self.thread.is_alive()):
                aklog_debug("资源已释放，无需重复释放")
                return

            # 停止录制视频
            if self.recording and self.record_thread:
                self.stop_recording()

            # 停止拉流
            self.running = False

            # 如果拉流线程存在，且不是当前线程，则等待结束
            if self.thread and self.thread.is_alive():
                if threading.current_thread() != self.thread:
                    # aklog_debug("等待拉流线程结束")
                    self.thread.join(timeout=2)
                else:
                    aklog_debug("当前在线程内部调用 release，跳过 join 防止死锁")

            # 释放 OpenCV VideoCapture
            if self.cap:
                self.cap.release()
                self.cap = None
                # aklog_debug("OpenCV VideoCapture 已释放")

            self.thread = None
            aklog_debug("RTSP流资源释放完成")
        except Exception as e:
            aklog_error(f"释放资源异常: {e}")
            aklog_debug(traceback.format_exc())
        finally:
            self.frame_buffer.clear()

    def __del__(self):
        """对象被销毁时自动释放资源（兜底用）"""
        try:
            if self.running:
                self.running = False
            if self.cap:  # 只做最小化释放
                self.cap.release()
                self.cap = None
        except Exception:
            pass
        finally:
            self.frame_buffer.clear()

    def __enter__(self):
        """上下文管理协议，进入时启动视频流"""
        self.thread_start_video()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理协议，退出时释放资源"""
        self.release()


def video_capture_check_image(rtsp_url, duration, temp_index=None):
    """查看视频流图像是否正常"""
    cap = AKVideoCapture(rtsp_url, temp_index=temp_index)
    ret = cap.is_correct_video_image(duration)
    cap.cap_release()
    return ret


def thread_video_captures_check_image(rtsp_url, lines, duration=20):
    """同时多路查看视频流"""
    thread_list = []
    for i in range(0, lines):
        thread = AkThread(target=video_capture_check_image, args=(rtsp_url, duration, i+1), wait_time=5*i)
        thread_list.append(thread)
    for t in thread_list:
        t.daemon = True
        t.start()
    for t in thread_list:
        t.join(duration + 60)
    time.sleep(1)
    results = []
    for t in thread_list:
        ret = t.get_result()
        results.append(ret)
    return results


def get_camera_capture_ocr_texts(
        rtsp_url, username=None, password=None, timeout=10, ocr_type=None):
    """摄像头监控截图，OCR文本检查"""
    cap = AKRTSPCapture(rtsp_url, username, password)
    cap.thread_start_video()
    if not cap.wait_video_image(timeout):
        cap.screen_shot(reshot=False)
        cap.release()
        return None
    texts = cap.capture_ocr_to_texts(ocr_type)
    cap.release()
    return texts


def compress_video(input_file, output_file, width=1280, height=720, video_bitrate="800k"):
    """
    压缩视频文件（调整分辨率和码率）

    Args:
        input_file (str): 原始视频路径
        output_file (str): 输出视频路径
        width (int): 输出视频宽度
        height (int): 输出视频高度
        video_bitrate (str): 视频目标码率，例如'800k'
    """
    # 检查源文件是否存在
    if not os.path.exists(input_file):
        aklog_error(f"源视频文件不存在: {input_file}")
        return False

    # 生成 FFmpeg 命令
    cmd = [
        "ffmpeg", "-y", "-loglevel", "quiet",  # -y 表示覆盖输出文件
        "-i", input_file,
        "-vf", f"scale={width}:{height}",
        "-b:v", video_bitrate,
        "-an",  # 去掉音频
        output_file
    ]

    aklog_debug(f"开始压缩视频: {input_file} -> {output_file}, 分辨率 {width}x{height}, 码率 {video_bitrate}")

    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        aklog_debug(f"视频压缩完成: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        aklog_error(f"视频压缩失败: {e}")
        return False


def wait_camera_capture_ocr_to_texts(
        rtsp_url, username=None, password=None, contents=None, check_text_cb=None,
        timeout=10, stop_event: threading.Event = None, ocr_type=None,
        is_exists=True, record_file=None, exec_before_check_cb=None, fail_to_exec_cb=None) -> bool:
    """
    摄像头监控截图，OCR文本检查
    要注意摄像头画面要清晰，光线足够
    Args:
        contents (list): 如果为空，将截取多张截图，获取稳定识别的文本，作为后续检查对象，会将识别到的文本列表进行合并，并只保留字母+数字
        检查contents中的字符串是否在识别的文本内，可以只判断部分文本
        rtsp_url:
        username:
        password:
        check_text_cb: 检查文本回调函数，该函数必须要有个ocr_texts参数，如果传入该函数，contents将不作为检查
        timeout: 等待画面识别到指定文字的超时时间，可以设为None，将不等待，只识别一遍
        stop_event:
        ocr_type: OCR识别方式，为None时，将会使用多种方法轮流检查
        is_exists (bool): 为True时检查文本存在，为False时检查文本不存在
        record_file (str): 如果传入视频文件，将保存视频录制，但只在失败时，才保存视频文件
        exec_before_check_cb (): 在检查之前执行的回调函数，RTSP视频流建立需要时间，所以在RTSP视频流建立后再进行其他操作，然后再检查画面
        fail_to_exec_cb (): 识别失败时执行回调函数
    """
    aklog_info()
    if contents is None:
        contents = []
    result = False
    cap = None

    # 检查OCR识别文本
    def check_ocr_texts(texts):
        if not check_text_cb:
            if is_exists:
                ocr_data = find_and_extract_ocr_data(texts, contents)
                if ocr_data:
                    return True
            else:
                ocr_data = check_ocr_keyword_absence(texts, contents)
                if not ocr_data:
                    return True
        else:
            # 通过回调函数来检查OCR文本是否匹配
            if check_text_cb(texts):
                return True
        return False

    try:
        cap = AKRTSPCapture(rtsp_url, username, password)
        cap.thread_start_video()
        wait_video_timeout = timeout
        if not timeout:
            wait_video_timeout = 10
        if not cap.wait_video_image(wait_video_timeout, stop_event):
            cap.screen_shot(reshot=False)
            return False
        if record_file:
            cap.start_recording()
            time.sleep(1)
        if not check_text_cb:
            # 如果要检查的文本为空，截取多张截图，获取稳定识别的文本
            if not contents:
                stable_keywords = cap.ocr_stable_keywords()
                if stable_keywords:
                    contents.extend(stable_keywords)
            if not contents:
                aklog_error('文本识别失败')
                cap.screen_shot(reshot=False)
                return False

        # 在RTSP视频流建立后再进行其他操作，然后再检查画面
        if exec_before_check_cb is not None:
            exec_before_check_cb()

        # 摄像头画面截图，OCR获取文本
        if not timeout:
            timeout = 0.5
        attempt = 0
        retry = 2
        interval = min(timeout / 10, 1)
        end_time = time.time() + timeout
        # 确保至少识别2次，避免因OCR识别时间还长，导致超时时间内只识别了一次就退出循环了
        while time.time() < end_time or attempt < retry:
            if stop_event and stop_event.is_set():
                break
            attempt += 1
            check_time = time.time()
            # 第一种方法OCR识别失败，将使用另一种方法识别
            if ocr_type is None:
                ocr_type_list = ['wechat_ocr', 'paddleocr']
            else:
                ocr_type_list = [ocr_type]
            for _type in ocr_type_list:
                texts = cap.capture_ocr_to_texts(_type)
                result = check_ocr_texts(texts)
                if result:
                    break
            if result:
                break
            interval_remain_time = interval - (time.time() - check_time)
            if interval_remain_time > 0:
                time.sleep(interval_remain_time)
            continue
        # 保存摄像头截图
        if not result:
            # 识别失败时，执行某个方法后，再截图
            if fail_to_exec_cb is not None:
                fail_to_exec_cb()
            cap.screen_shot(max_width=1280, reshot=False)
    except Exception as e:
        aklog_error(e)
    finally:
        if record_file:
            if result:
                record_file = None
            cap.stop_recording(record_file)
        if cap:
            cap.release()
    return result


if __name__ == '__main__':
    print('test')
    rtsp_url = 'rtsp://admin:123456@192.168.88.194/stream0'
    ret = wait_camera_capture_ocr_to_texts(rtsp_url)
    print(ret)
