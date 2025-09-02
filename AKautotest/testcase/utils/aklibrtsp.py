# -*- coding: UTF-8 -*-
from akcommon_define import *
import cv2
import threading
import numpy as np

rtsp_result = []
root_path = os.getcwd()
pos = root_path.find("AKautotest")

if pos == -1:
    print("runtime error")
    exit(1)

root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

import subprocess


def run_ffmpeg(input_file, output_url, video_bitrate='4096k', frame_rate='25', buffer_size='2M', profile='high', preset='slow', tune='zerolatency',
               transport='udp', duration=None, video_codec='libx264'):
    """
    运行 FFmpeg 命令，将本地视频流传输到 RTSP 服务器。

    参数:
    input_file (str): 输入视频文件路径。
    output_url (str): 输出 RTSP URL。
    video_bitrate (str): 视频比特率（默认 '4096k'）。
    frame_rate(str):帧率（默认 '25'）。
    profile(str):baseline/main/high
    buffer_size (str): 缓冲区大小（默认 '2M'）。
    preset (str): FFmpeg 预设（默认 'veryfast'）。
    tune (str): FFmpeg 调优参数（默认 'zerolatency'）。
    transport (str): 传输协议（默认 'udp'）。
    """
    # FFmpeg 命令和参数
    aklog_info()
    ffmpeg_command = [
        'ffmpeg',
        '-re',
        '-i', input_file,
        '-c:v', video_codec,
        '-preset', preset,
        '-tune', tune,
        '-b:v', video_bitrate,
        # '-r', frame_rate,     # H265不支持这两个参数
        # '-profile:v', profile,
        '-bufsize', buffer_size,
        '-f', 'rtsp',
        '-rtsp_transport', transport,
        output_url
    ]

    try:
        # 运行 FFmpeg 命令
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(10)
        # 如果指定了持续时间，设置一个定时器来停止 FFmpeg 进程
        if duration is not None:
            def stop_ffmpeg():
                process.terminate()
                aklog_info(f"FFmpeg 进程已在 {duration} 秒后停止。")

            timer = threading.Timer(duration, stop_ffmpeg)
            timer.start()

        # 返回输出和错误信息
        return True

    except Exception as e:
        aklog_info(f"运行 FFmpeg 命令时出错: {e}")
        return None, str(e)


def create_color_video(output_file, width=640, height=480, fps=25, duration=60, color=(255, 0, 0)):
    """
    创建一个指定颜色的视频文件。

    参数：
    output_file (str): 输出视频文件的路径。
    width (int): 视频宽度，默认值为 640。
    height (int): 视频高度，默认值为 480。
    fps (int): 视频帧率，默认值为 30。
    duration (int): 视频持续时间（秒），默认值为 10。
    color (tuple): RGB 颜色值，默认值为 (255, 0, 0)（红色）。
    """
    # 计算总帧数
    total_frames = fps * duration

    # 创建视频写入对象
    fourcc = cv2.VideoWriter_fourcc(*'H264')  # 使用 H.264 编码
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

    # 创建指定颜色的帧
    color_frame = np.zeros((height, width, 3), dtype=np.uint8)
    color_frame[:] = color  # 设置帧的颜色

    # 写入帧到视频文件
    for _ in range(total_frames):
        out.write(color_frame)

    # 释放视频写入对象
    out.release()

    print(f"指定颜色的视频已保存为 {output_file}")


def get_img_from_rtsp(folder_path, ip, channel):
    """
    src: https://www.cnblogs.com/jieliu8080/p/10826323.html
    功能: 保存两张python rtsp截图, 在使用check_image_rgb_by_id(同live stream)做判断
    参数:
        folder_path: 保存文件地址, .jpg. 自动化脚本里通常是存放在chrome_download文件夹下一起使用
        ip: 终端ip
        channel:  0, 1 两个通道
    """
    try:
        import time
        cap = cv2.VideoCapture(f"rtsp://{ip}/live/ch00_{str(channel)}")  # 获取网络摄像机
        i = 1
        while i < 3:
            ret, frame = cap.read()
            # cv2.imshow("capture", frame)

            cv2.imwrite(folder_path + str(i) + '.jpg', frame)  # 存储为图像
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            i += 1
        time.sleep(60)
        cap.release()
        cv2.destroyAllWindows()
    except:
        rtsp_result.append(False)
        return False
    else:
        rtsp_result.append(True)
        return True

def check_rtsp_stream(rtsp_url):
    # 尝试打开RTSP流
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        aklog_info(f"无法打开RTSP流: {rtsp_url}")
        return False

    # 尝试读取一帧
    ret, frame = cap.read()
    if not ret or frame is None:
        aklog_info(f"无法读取RTSP流的帧: {rtsp_url}")
        cap.release()
        return False

    # 检查帧的内容（可以根据具体需求进行进一步检查）
    height, width, channels = frame.shape
    aklog_info(f"成功读取RTSP流的帧: {rtsp_url}, 帧尺寸: {width}x{height}, 通道数: {channels}")
    # 获取其他参数
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
    frame_number = cap.get(cv2.CAP_PROP_POS_FRAMES)
    aspect_ratio = width / height
    brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)
    contrast = cap.get(cv2.CAP_PROP_CONTRAST)
    saturation = cap.get(cv2.CAP_PROP_SATURATION)

    # 打印获取的参数
    aklog_info(f"视频帧率: {fps} fps")
    aklog_info(f"视频格式: {fourcc_str}")
    aklog_info(f"当前帧编号: {frame_number}")
    aklog_info(f"视频宽高比: {aspect_ratio}")
    aklog_info(f"亮度: {brightness}, 对比度: {contrast}, 饱和度: {saturation}")

    # 释放资源
    cap.release()
    return [width, height]

def calculate_average_ratios(capture, frame_count=100):
    total_mosaic_ratio = 0
    total_green_ratio = 0
    valid_frames = 0

    for _ in range(frame_count):
        ret, frame = capture.read()
        if not ret:
            break

        mosaic_ratio = RTSP_Analysis.calculate_mosaic_ratio(frame)
        green_ratio = RTSP_Analysis.calculate_green_screen_ratio(frame)

        total_mosaic_ratio += mosaic_ratio
        total_green_ratio += green_ratio
        valid_frames += 1

    avg_mosaic_ratio = total_mosaic_ratio / valid_frames
    avg_green_ratio = total_green_ratio / valid_frames

    return avg_mosaic_ratio, avg_green_ratio

if __name__ == '__main__':
    # 示例RTSP流URL
    # rtsp_urls = [
    #     # "rtsp://admin:clh123456@192.168.88.122:554",
    #     # "rtsp://admin:clh12345@192.168.88.122:554",
    #     "rtsp://192.168.88.100:8554/video",
    #     # "rtsp://192.168.88.123:8554",
    #     # "rtsp://admin:admin@192.168.88.123/live/ch00-0"
    # ]
    #
    # # 检查每个RTSP流
    # for url in rtsp_urls:
    #     result = check_rtsp_stream(url)
    #     if result:
    #         print(f"RTSP流 {url} 正常播放")
    #     else:
    #         print(f"RTSP流 {url} 无法正常播放")

    # 生成视频
    # create_color_video('yellow_video_4cif.mp4', width=704, height=576, color=(255, 255, 255))

    input_file = 'C:/Users/Administrator/Videos/Captures/VGA.avi'
    output_url = 'rtsp://192.168.88.100:8554/video'
    run_ffmpeg(input_file, output_url, duration=60, video_codec='libx265')

    # cap = cv2.VideoCapture('rtsp://192.168.88.123')
    # avg_mosaic, avg_green = calculate_average_ratios(cap)
    # print(f"Average Mosaic Ratio: {avg_mosaic:.2f}%")
    # print(f"Average Green Screen Ratio: {avg_green:.2f}%")
    # cap.release()




