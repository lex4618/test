# -*- coding: utf-8 -*-

import sys
import os

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *
import tempfile
import shutil
import math
import operator
import functools
import traceback
import PIL.Image as Image
import cv2
import numpy as np
import base64
import re
import adbutils.errors
import requests
from typing import List, Union, Dict, Optional
from wda import Client, Element
from uiautomator2 import Device
from uiautomator2.xpath import XMLElement
from uiautomator2 import UiObject
from uiautomator2.utils import image_convert
from io import BytesIO
from concurrent.futures import ProcessPoolExecutor
from WeChatOCR.OCR import wechat_ocr
from rapidfuzz import fuzz

easyocr_instance = None
paddleocr_instance = None


__all__ = [
    'Image_process',
    'ImageProcessU2',
    'ImageProcessIOS',
    'png_2_jpg',
    'image_compare',
    'image_crop_by_pixel',
    'image_compare_after_convert_resolution',
    'check_image_is_pure_color',
    'check_video_image_is_normal',
    'detect_image_anomalies_with_url',
    'detect_obstruction',
    'detect_image_anomalies',
    'image_ocr_to_string',
    'image_easyocr_read_text',
    'preprocess_image',
    'image_paddleocr_to_text',
    'batch_image_paddleocr_to_texts',
    'image_ocr_to_texts',
    'image_2_base64',
    'image_append_screenshots_imgs',
    'fix_rgb_error_range',
    'judge_no_pure_with_error_range',
    'extract_similar_region',
    'intercom_compare_two_picture',
    'crop_image',
    'extract_alpha_with_spaces',
    'find_and_extract_ocr_data',
    'check_ocr_keyword_absence',
    'check_record_video',
]


class Image_process(object):

    def __init__(self, driver, device_name=''):
        self.driver = driver
        self.device_name = device_name or ''
        self.PATH = lambda p: os.path.abspath(p)
        if self.device_name:
            os.makedirs(os.path.join(tempfile.gettempdir(), self.device_name), exist_ok=True)
            temp_dir = self.PATH(os.path.join(tempfile.gettempdir(), self.device_name))
        else:
            temp_dir = tempfile.gettempdir()
        self.TEMP_FILE = self.PATH(os.path.join(temp_dir, "temp_screen.png"))
        self.temp_file_data = None

    def screenshots_as_base64(self):
        try:
            img_base64 = self.driver.get_screenshot_as_base64()
            return img_base64
        except:
            error = str(traceback.format_exc())
            if 'selenium.common.exceptions.UnexpectedAlertPresentException' in error:
                aklog_printf('截图失败，存在系统弹窗!')
            else:
                aklog_printf('截图失败，' + error)
            return None

    def is_pure_color(self, element, percent):
        """检查图片是否是纯色"""
        aklog_printf('is_pure_color')
        if element is None:
            return None
        try:
            self.get_screenshot_by_element(element)
            h = element.size.get("height")
            w = element.size.get("width")
            list_all = []
            el_rgb_dict = {}
            # 遍历像素，并将相同颜色的像素进行归类成字典，key为像素颜色，value为该颜色的像素数量
            for xk in range(0, w):
                for yk in range(0, h):
                    f1 = (xk, yk)
                    list_all.append(f1)
                    el_rgb = self.temp_file_data.getpixel((xk, yk))
                    # print(el_rgb)
                    if str(el_rgb) not in el_rgb_dict:
                        el_rgb_dict[str(el_rgb)] = []
                        el_rgb_dict[str(el_rgb)].append(f1)
                    else:
                        el_rgb_dict[str(el_rgb)].append(f1)
            # 然后比较相同颜色的像素数量占比
            max_rgb_len = 0
            most_colors = ''
            for key in el_rgb_dict.keys():
                rgb_len = len(el_rgb_dict[key])
                if rgb_len > max_rgb_len:
                    max_rgb_len = rgb_len
                    most_colors = key
            max_ratio = max_rgb_len / len(list_all)
            if max_ratio > percent:
                aklog_printf('color %s, ratio: %s' % (most_colors, max_ratio))
                return True
            else:
                aklog_printf('color %s is most，ratio: %s' % (most_colors, max_ratio))
                aklog_printf('No color is more than %s' % percent)
                return False
        except:
            aklog_printf(traceback.format_exc())
            return False

    def check_screen_color(self, element, fix_rgb=(0, 0, 0)):
        """
        如何查看颜色
        https://www.sioe.cn/yingyong/yanse-rgb-16/
        结果
        安卓室内机黑色的结果
        (0,0,0)
        """
        aklog_printf('check_screen_color')
        if element is None:
            return None
        self.get_screenshot_by_element(element)
        # self.get_screenshot_by_element(element).write_to_file(root_path, 'image', form="png")
        # screenshot_image = Image.open(root_path + "/" + 'image' + ".png")
        # x1 = element.location.get("x")
        # y1 = element.location.get("y")
        h = element.size.get("height")
        w = element.size.get("width")
        # x2 = x1 + w
        # y2 = y1 + h
        # aklog_printf((x1, y1, x2, y2))
        # el_img = screenshot_image.crop(box=(x1, y1, x2, y2))
        lista = []
        listt = []
        listc = []
        for xk in range(0, w):
            for yk in range(0, h):
                f1 = (xk, yk)
                lista.append(f1)
                el_rgb = self.temp_file_data.getpixel((xk, yk))
                # print(el_rgb)
                if len(el_rgb) != len(fix_rgb):
                    aklog_printf('len(el_rgb) != len(fix_rgb)')
                    return None
                if el_rgb == fix_rgb:
                    f2 = (xk, yk)
                    listt.append(f2)
                else:
                    f3 = (xk, yk)
                    listc.append(f3)
        ratio = len(listt) / len(lista)
        aklog_printf('ratio: %s' % ratio)
        return ratio

    def check_screen_color_rgba(self, element, fix_rgb=(0, 0, 0, 0)):
        """
        如何查看颜色
        https://www.sioe.cn/yingyong/yanse-rgb-16/
        结果
        安卓室内机黑色的结果
        (0,0,0,0)
        """
        aklog_printf('check_screen_color_rgba')
        if element is None:
            return None
        self.get_screenshot_by_element(element)
        # self.get_screenshot_by_element(element).write_to_file(root_path, 'image', form="png")
        # screenshot_image = Image.open(root_path + "/" + 'image' + ".png")
        # x1 = element.location.get("x")
        # y1 = element.location.get("y")
        h = element.size.get("height")
        w = element.size.get("width")
        # x2 = x1 + w
        # y2 = y1 + h
        # aklog_printf((x1, y1, x2, y2))
        # el_img = screenshot_image.crop(box=(x1, y1, x2, y2))
        lista = []
        listt = []
        listc = []
        for xk in range(0, w):
            for yk in range(0, h):
                f1 = (xk, yk)
                lista.append(f1)
                el_rgb = self.temp_file_data.getpixel((xk, yk))
                # print(el_rgb)
                if len(el_rgb) != len(fix_rgb):
                    aklog_printf('len(el_rgb) != len(fix_rgb)')
                    return None
                if el_rgb == fix_rgb:
                    f2 = (xk, yk)
                    listt.append(f2)
                else:
                    f3 = (xk, yk)
                    listc.append(f3)
        ratio = len(listt) / len(lista)
        aklog_printf('ratio: %s' % ratio)
        return ratio

    def check_custom_area_color(self, area, fix_rgb):
        """

        :param area: (start_x, start_y, end_x, end_y)
        :param fix_rgb: (0,0,0,0) or (0,0,0)
        :return:
        """
        aklog_printf('check_custom_area_color')

        self.get_screenshot_by_custom_size(*area)

        h = area[3] - area[1]
        w = area[2] - area[0]
        lista = []
        listt = []
        listc = []
        for xk in range(0, w):
            for yk in range(0, h):
                f1 = (xk, yk)
                lista.append(f1)
                el_rgb = self.temp_file_data.getpixel((xk, yk))
                # print(el_rgb)
                if len(el_rgb) != len(fix_rgb):
                    aklog_printf('len(el_rgb) != len(fix_rgb)')
                    return None
                if el_rgb == fix_rgb:
                    f2 = (xk, yk)
                    listt.append(f2)
                else:
                    f3 = (xk, yk)
                    listc.append(f3)
        ratio = len(listt) / len(lista)
        aklog_printf('ratio: %s' % ratio)
        return ratio

    def get_canvas_missing_piece_loc(self, element):
        """
        获取滑块拼图验证码图片中缺块的X坐标，并以此来计算滑块移动距离
        适用于家居云登录的验证码
        """
        aklog_printf('get_canvas_missing_piece_loc')
        if element is None:
            return None
        self.get_screenshot_by_element(element)
        h = element.size.get("height")
        w = element.size.get("width")
        # 检查每一列像素点的颜色，缺块边缘一圈的颜色比较深（RGB像素相加少于300认为出现缺块），获取出现缺块的第一列的X坐标
        for xk in range(60, w):
            lista = []
            el_rgb_dict = {}
            for yk in range(0, h):
                f1 = (xk, yk)
                el_rgb = self.temp_file_data.getpixel((xk, yk))
                # aklog_printf('%s, %s' % (el_rgb, (xk, yk)))
                if el_rgb[0] + el_rgb[1] + el_rgb[2] < 300:
                    if str(el_rgb) not in el_rgb_dict:
                        el_rgb_dict[str(el_rgb)] = []
                    el_rgb_dict[str(el_rgb)].append(f1)
            # 过滤掉一整块为深色的颜色，缺块边缘深色的像素点色值不会完全一致
            for x in el_rgb_dict:
                if len(el_rgb_dict[x]) < 4:
                    lista.extend(el_rgb_dict[x])
            if 0 < len(lista) < 32:
                return xk
        return None

    def get_screenshot_by_element(self, element):
        aklog_printf('get_screenshot_by_element')
        try:
            File_process.remove_file(self.TEMP_FILE)
            # # android V5.1版本 R48G 采用该方式截图会失败
            # element.screenshot(self.TEMP_FILE)
            # self.temp_file_data = Image.open(self.TEMP_FILE)

            # 先截取整个屏幕，存储至系统临时目录下
            self.driver.get_screenshot_as_file(self.TEMP_FILE)
            # 获取元素bounds
            location = element.location
            size = element.size
            box = (location["x"], location["y"], location["x"] + size["width"], location["y"] + size["height"])
            # 截取图片
            image = Image.open(self.TEMP_FILE)
            self.temp_file_data = image.crop(box)
            self.temp_file_data.save(self.TEMP_FILE)

            return self
        except:
            aklog_printf(str(traceback.format_exc()))
            return None

    def get_screenshot_by_custom_size(self, start_x, start_y, end_x, end_y):
        # 自定义截取范围
        try:
            aklog_printf('get_screenshot_by_custom_size: (%s, %s, %s, %s)' % (start_x, start_y, end_x, end_y))
            File_process.remove_file(self.TEMP_FILE)
            self.driver.get_screenshot_as_file(self.TEMP_FILE)
            box = (start_x, start_y, end_x, end_y)

            image = Image.open(self.TEMP_FILE)
            self.temp_file_data = image.crop(box)
            self.temp_file_data.save(self.TEMP_FILE)

            return self
        except:
            aklog_printf(str(traceback.format_exc()))
            return None

    def get_temp_file_by_custom_size(self, start_x, start_y, end_x, end_y):
        # 当前temp_file文件 截取范围
        try:
            aklog_printf('get_screenshot_by_custom_size: (%s, %s, %s, %s)' % (start_x, start_y, end_x, end_y))

            box = (start_x, start_y, end_x, end_y)

            image = Image.open(self.TEMP_FILE)
            self.temp_file_data = image.crop(box)
            self.temp_file_data.save(self.TEMP_FILE)

            return self
        except:
            aklog_printf(str(traceback.format_exc()))
            return None

    def get_screenshot_as_file(self):
        """整个屏幕截图"""
        try:
            self.driver.get_screenshot_as_file(self.TEMP_FILE)
            return self
        except:
            aklog_printf(str(traceback.format_exc()))
            return None

    def write_to_file(self, image_dir, image_name, form="png"):
        # 将截屏文件复制到指定目录下
        try:
            if not os.path.isdir(image_dir):
                os.makedirs(image_dir)
            shutil.copyfile(self.TEMP_FILE, self.PATH(image_dir + "/" + image_name + "." + form))
            return True
        except:
            aklog_printf(str(traceback.format_exc()))
            return False

    @staticmethod
    def load_image(image_path):
        # 加载目标图片供对比用
        try:
            if os.path.isfile(image_path):
                load = Image.open(image_path)
                return load
            else:
                aklog_printf("%s is not exist" % image_path)
                return None
        except:
            aklog_printf(str(traceback.format_exc()))
            return None

    def same_as(self, load_image, percent):
        """对比图片，percent值设为0，则100%相似时返回True，设置的值越大，相差越大"""
        aklog_printf('same_as')
        try:
            # image1 = Image.open(self.TEMP_FILE)
            image1 = self.temp_file_data
            image2 = load_image

            histogram1 = image1.histogram()
            histogram2 = image2.histogram()

            differ = math.sqrt(functools.reduce(operator.add, list(map(lambda a, b: (a - b) ** 2,
                                                                       histogram1, histogram2))) / len(histogram1))
            aklog_printf('differ : %s' % differ)
            if differ <= percent:
                return True
            else:
                return False
        except:
            aklog_printf(str(traceback.format_exc()))
            return False

    def compare_image(self, element, image_path, percent):
        """判断元素图片跟预期的图片是否一致"""
        aklog_printf('compare_image')
        load_image = self.load_image(image_path)
        result = self.get_screenshot_by_element(element).same_as(load_image, percent)
        return result

    def convert_resolution(self, dst_resolution):
        """
        将截图转换成对应的分辨率
        :param dst_resolution: (800, 480)
        :return:
        """
        aklog_printf('convert_resolution')
        try:
            # image1 = Image.open(self.TEMP_FILE)
            self.temp_file_data.thumbnail(dst_resolution)
            return self
        except:
            aklog_printf(str(traceback.format_exc()))
            return False

    def png_2_jpg(self):
        """PNG格式转JPG格式图片"""
        aklog_printf('png_2_jpg')
        infile = self.TEMP_FILE
        outfile = os.path.splitext(infile)[0] + ".jpg"
        try:
            im = cv2.imread(infile)
            cv2.imwrite(outfile, im)
            self.temp_file_data = Image.open(outfile)
            return self
        except:
            aklog_printf("PNG转换JPG 错误" + str(traceback.format_exc()))
            return None

    def compare_image_after_convert_resolution(self, element, image_path, percent):
        """截图转换成跟对比的图片相同分辨率之后再对比"""
        aklog_printf('compare_image_after_convert_resolution')
        load_image = self.load_image(image_path)
        img_size = load_image.size
        self.get_screenshot_by_element(element)
        self.png_2_jpg()
        result = self.convert_resolution(img_size).same_as(load_image, percent)
        return result

    def image_ocr_to_string(self):
        """
        识别图片中的文字并输出，可以识别获取安卓室内机状态中的时间日期
        """
        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = root_path + '\\tools\\Tesseract-OCR\\tesseract.exe'
            string = pytesseract.image_to_string(Image.open(self.TEMP_FILE), timeout=10)
            aklog_printf(string)
            return string
        except:
            aklog_printf(traceback.format_exc())
            return None

    def image_easyocr_read_text(self):
        """
        用easyocr模块来识别，会比pytesseract更准确，建议使用这种方式
        注意easyocr（版本1.5.0）跟opencv的高版本会冲突，需要使用4.5.1.48版本
        """
        try:
            global easyocr_instance
            if easyocr_instance is None:
                import easyocr

                model_folder = root_path + '\\testcase\\utils\\EasyOCR\\model'
                easyocr_instance = easyocr.Reader(['ch_sim', 'en'], gpu=False, model_storage_directory=model_folder)

            ret = easyocr_instance.readtext(self.TEMP_FILE)
            if not ret:
                return None
            text_list = []
            for i in ret:
                text = i[1]
                text_list.append(text)
            if len(text_list) == 1:
                aklog_printf(text_list[0])
                return text_list[0]
            else:
                aklog_printf(text_list)
                return text_list
        except:
            aklog_printf(traceback.format_exc())
            return None

    def image_ocr_to_texts(self) -> list:
        """使用微信OCR识别文本"""
        aklog_printf()
        self.temp_file_data.save(self.TEMP_FILE)
        texts = wechat_ocr(self.TEMP_FILE)
        aklog_debug(f'texts: {texts}')
        return texts


class ImageProcessU2(object):

    def __init__(self, driver=None, device_name=''):
        self.driver: Optional[Device] = driver
        self.device_name = device_name or ''
        self.PATH = lambda p: os.path.abspath(p)
        if self.device_name:
            os.makedirs(os.path.join(tempfile.gettempdir(), self.device_name), exist_ok=True)
            temp_dir = self.PATH(os.path.join(tempfile.gettempdir(), self.device_name))
        else:
            temp_dir = tempfile.gettempdir()
        self.TEMP_FILE = self.PATH(os.path.join(temp_dir, "temp_screen.png"))
        self.temp_file_data = None

    def init(self, driver, device_name=''):
        self.driver = driver
        if device_name:
            self.device_name = device_name

    def screenshots_as_base64(self, re_shot=True):
        try:
            if re_shot:
                self.temp_file_data = self.driver.screenshot(format="pillow")  # 获取PIL对象
            buffer = BytesIO()
            self.temp_file_data.save(buffer, format="JPEG")
            base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return base64_data
        except adbutils.errors.AdbError:
            aklog_printf('截图失败，adb链接出现异常')
            return None
        except:
            aklog_printf('截图失败，' + str(traceback.format_exc()))
            return None

    def is_pure_color(self, element=None, area=None, percent=0, save_path=None, re_shot=True):
        """
        检查图片是否是纯色
        area: 坐标元组: (start_x, start_y, end_x, end_y)
        save_path: 将截图数据保存到文件
        """
        aklog_printf('is_pure_color, percent: %s' % percent)
        try:
            if element is not None:
                bounds = element.info.get('bounds')
                lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
                h = int(ry) - int(ly)
                w = int(rx) - int(lx)
                area = [lx, ly, rx, ry]
            elif area:
                h = int(area[3]) - int(area[1])
                w = int(area[2]) - int(area[0])
            else:
                return None
            if re_shot:
                self.temp_file_data = self.driver.screenshot(format='pillow')
            area_data = self.temp_file_data.crop(area)
            if save_path:
                aklog_printf('save screenshot to %s' % save_path)
                self.temp_file_data.save(save_path)
            pixel_count = h * w
            el_rgb_dict = {}
            # 遍历像素，并将相同颜色的像素进行归类成字典，key为像素颜色，value为该颜色的像素数量
            for xk in range(0, w):
                for yk in range(0, h):
                    el_rgb = area_data.getpixel((xk, yk))
                    # print(el_rgb)
                    if str(el_rgb) not in el_rgb_dict:
                        el_rgb_dict[str(el_rgb)] = 1
                    else:
                        el_rgb_dict[str(el_rgb)] += 1
            # 然后比较相同颜色的像素数量占比
            max_rgb_len = 0
            most_colors = ''
            for key in el_rgb_dict.keys():
                rgb_len = el_rgb_dict[key]
                if rgb_len > max_rgb_len:
                    max_rgb_len = rgb_len
                    most_colors = key
            max_ratio = max_rgb_len / pixel_count
            if max_ratio > percent:
                aklog_warn('颜色 %s 占比最多: %s, 超过 %s' % (most_colors, max_ratio, percent))
                return True
            else:
                aklog_printf('颜色 %s 占比最多: %s, 没有超过 %s' % (most_colors, max_ratio, percent))
                return False
        except:
            aklog_printf(traceback.format_exc())
            return None

    def is_light_color(self, element=None, area=None, rgb_sum=300, percent=0.5, save_path=None):
        """
        检查图片颜色是否为浅色
        rgb_sum: rgb三种数值相加，
        大于rgb_sum的占比超过percent，表示为浅色，否则为深色
        """
        aklog_printf('is_light_color: rgb_sum: %s, percent: %s' % (rgb_sum, percent))
        try:
            if element is not None:
                self.get_screenshot_by_element(element)
                bounds = element.info.get('bounds')
                lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
                h = int(ry) - int(ly)
                w = int(rx) - int(lx)
            elif area:
                self.temp_file_data = self.driver.screenshot(format='pillow').crop(area)
                h = int(area[3]) - int(area[1])
                w = int(area[2]) - int(area[0])
            else:
                return None
            if not self.temp_file_data:
                return None
            if save_path:
                aklog_printf('save screenshot to %s' % save_path)
                self.temp_file_data.save(save_path)
            list_all = []
            el_rgb_list = []
            # 遍历像素，并将相同颜色的像素进行归类成字典，key为像素颜色，value为该颜色的像素数量
            for xk in range(0, w):
                for yk in range(0, h):
                    f1 = (xk, yk)
                    list_all.append(f1)
                    el_rgb = self.temp_file_data.getpixel((xk, yk))
                    # 将颜色rgb三个数字相加
                    el_rgb_sum = el_rgb[0] + el_rgb[1] + el_rgb[2]
                    if el_rgb_sum > rgb_sum:
                        el_rgb_list.append(el_rgb)

            # 然后比较相同颜色的像素数量占比
            ratio = len(el_rgb_list) / len(list_all)
            aklog_printf('el_rgb_sum > rgb_sum, ratio: %s' % ratio)
            if ratio > percent:
                aklog_printf('Color is light')
                return True
            else:
                aklog_printf('Color is dark')
                return False
        except:
            aklog_printf(traceback.format_exc())
            return None

    def check_rgb_sum(self, element=None, area=None, rgb_sum=300, save_path=None):
        """
        获取rgb_sum占比
        rgb_sum: rgb三种数值相加
        """
        aklog_printf(f'check_rgb_sum: {rgb_sum}')
        try:
            if element is not None:
                self.get_screenshot_by_element(element)
                bounds = element.info.get('bounds')
                lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
                h = int(ry) - int(ly)
                w = int(rx) - int(lx)
            elif area:
                self.temp_file_data = self.driver.screenshot(format='pillow').crop(area)
                h = int(area[3]) - int(area[1])
                w = int(area[2]) - int(area[0])
            else:
                return None
            if not self.temp_file_data:
                return None
            if save_path:
                aklog_printf('save screenshot to %s' % save_path)
                self.temp_file_data.save(save_path)
            list_all = []
            el_rgb_list = []
            # 遍历像素，并将相同颜色的像素进行归类成字典，key为像素颜色，value为该颜色的像素数量
            for xk in range(0, w):
                for yk in range(0, h):
                    f1 = (xk, yk)
                    list_all.append(f1)
                    el_rgb = self.temp_file_data.getpixel((xk, yk))
                    # 将颜色rgb三个数字相加
                    el_rgb_sum = el_rgb[0] + el_rgb[1] + el_rgb[2]
                    if el_rgb_sum > rgb_sum:
                        el_rgb_list.append(el_rgb)

            # 然后比较相同颜色的像素数量占比
            ratio = len(el_rgb_list) / len(list_all)
            aklog_printf(f'rgb_sum: {rgb_sum}, ratio: {ratio}')
            return ratio
        except:
            aklog_printf(traceback.format_exc())
            return None

    def check_screen_color(self, element=None, area=None, fix_rgb=None, save_path=None):
        """
        检查界面某种颜色占比
        fix_rgb: (0,0,0)
        """
        aklog_printf(f'check_screen_color: {fix_rgb}')

        if element is not None:
            self.get_screenshot_by_element(element)
            bounds = element.info.get('bounds')
            lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
            h = int(ry) - int(ly)
            w = int(rx) - int(lx)
        elif area:
            self.temp_file_data = self.driver.screenshot(format='pillow').crop(area)
            h = int(area[3]) - int(area[1])
            w = int(area[2]) - int(area[0])
        else:
            return None
        if not self.temp_file_data:
            return None
        if save_path:
            aklog_printf('save screenshot to %s' % save_path)
            self.temp_file_data.save(save_path)
        lista = []
        listt = []
        listc = []
        for xk in range(0, w):
            for yk in range(0, h):
                f1 = (xk, yk)
                lista.append(f1)
                el_rgb = self.temp_file_data.getpixel((xk, yk))
                # print(el_rgb)
                if len(el_rgb) != len(fix_rgb):
                    aklog_printf('len(el_rgb) != len(fix_rgb)')
                    return None
                if el_rgb == fix_rgb:
                    f2 = (xk, yk)
                    listt.append(f2)
                else:
                    f3 = (xk, yk)
                    listc.append(f3)
        ratio = len(listt) / len(lista)
        aklog_printf('ratio: %s' % ratio)
        return ratio

    def is_similar_color(self, element=None, area=None, color=None, lower_hsv=None, upper_hsv=None,
                         threshold=0.1, save_path=None) -> Optional[bool]:
        """
        检查颜色跟哪一种比较相似，比如可以区分元素的颜色是橙色还是蓝色
        偏蓝色的HSV范围：
        下限：H = 90, S = 150, V = 0
        上限：H = 140, S = 255, V = 255
        偏橙色黄色的HSV范围：
        下限：H = 10, S = 100, V = 100
        上限：H = 35, S = 255, V = 255

        以下是几种常见颜色的 HSV 范围：
        1. 红色
           - 低范围：([0, 70, 50])
           - 高范围：([10, 255, 255])
           - 低范围：([170, 70, 50])
           - 高范围：([180, 255, 255])

        2. 绿色
           - 低范围：([35, 70, 50])
           - 高范围：([85, 255, 255])

        3. 蓝色（包括深蓝色和浅蓝色）
           - 低范围：([90, 70, 50])
           - 高范围：([140, 255, 255])

        4. 黄色
           - 低范围：([25, 70, 50])
           - 高范围：([35, 255, 255])

        5. 橙色（包括深橙色和浅橙色）
           - 低范围：([10, 70, 50])
           - 高范围：([25, 255, 255])

        6. 紫色
           - 低范围：([130, 70, 50])
           - 高范围：([160, 255, 255])
        这些范围可以根据具体需求进行微调，以适应不同的光照条件和图像质量。
        Args:
            element (class):
            area (tuple):
            color (str): blue/red/green/yellow/orange/purple，可以传入list多个颜色，多个颜色占比之和大于阈值即可
            lower_hsv (list): [90, 50, 0]
            upper_hsv (list): [140, 255, 255]
            threshold (float): 颜色占比阈值
            save_path (str): 保存图片路径
        """
        if element is not None:
            bounds = element.info.get('bounds')
            lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
            area = [lx, ly, rx, ry]
        elif not area:
            return None
        self.temp_file_data = self.driver.screenshot(format='pillow')
        area_data = self.temp_file_data.crop(area)
        if save_path:
            aklog_printf('save screenshot to %s' % save_path)
            self.temp_file_data.save(save_path)
        # 打开图像并转换为 OpenCV 格式
        image_cv = cv2.cvtColor(np.array(area_data), cv2.COLOR_RGB2BGR)
        # 转换为 HSV 色彩空间
        hsv_image = cv2.cvtColor(image_cv, cv2.COLOR_BGR2HSV)
        hsv_data = {
            'red': [
                ([0, 70, 50], [10, 255, 255]),
                ([170, 70, 50], [180, 255, 255])
            ],
            'orange': [([10, 70, 50], [25, 255, 255])],
            'brown': [([10, 51, 51], [30, 255, 229])],
            'yellow': [([25, 70, 50], [35, 255, 255])],
            'green': [([35, 70, 50], [85, 255, 255])],
            'blue': [([90, 70, 50], [140, 255, 255])],
            'purple': [([130, 70, 50], [160, 255, 255])]
        }
        # 获取颜色的 HSV 范围
        if color:
            if isinstance(color, str):
                colors = [color]
            else:
                colors = color
            color_ratio_sum = 0
            for x in colors:
                x = x.lower()
                color_ranges = hsv_data.get(x, [])
                if len(color_ranges) == 2:
                    range_pair1, range_pair2 = color_ranges
                    mask1 = cv2.inRange(hsv_image, np.array(range_pair1[0]), np.array(range_pair1[1]))
                    mask2 = cv2.inRange(hsv_image, np.array(range_pair2[0]), np.array(range_pair2[1]))
                    combined_mask = cv2.bitwise_or(mask1, mask2)
                else:
                    range_pair = color_ranges[0]
                    combined_mask = cv2.inRange(hsv_image, np.array(range_pair[0]), np.array(range_pair[1]))
                # 计算颜色占比
                total_pixels = combined_mask.size
                color_pixels = cv2.countNonZero(combined_mask)
                color_ratio = color_pixels / total_pixels
                color_ratio_sum += color_ratio
            ret = color_ratio_sum > threshold
            if ret:
                aklog_printf(f'colors: {colors}, ratio_sum: {color_ratio_sum}, greater than {threshold}')
                return True
            else:
                aklog_printf(f'colors: {colors}, ratio_sum: {color_ratio_sum}, less than {threshold}')
                return False
        elif lower_hsv and upper_hsv:
            combined_mask = cv2.inRange(hsv_image, np.array(lower_hsv), np.array(upper_hsv))
            # 计算颜色占比
            total_pixels = combined_mask.size
            color_pixels = cv2.countNonZero(combined_mask)
            color_ratio = color_pixels / total_pixels
            ret = color_ratio > threshold
            if ret:
                aklog_printf(f'color ratio: {color_ratio}, greater than {threshold}')
                return True
            else:
                aklog_printf(f'color ratio: {color_ratio}, less than {threshold}')
                return False
        else:
            return None

    def check_screen_colors(self, *fix_rgbs, element=None, area=None, save_path=None):
        """
        检查界面某几种颜色总共占比
        fix_rgbs: (0,0,0)
        """
        aklog_printf(f'check_screen_colors: {fix_rgbs}')

        if element is not None:
            self.get_screenshot_by_element(element)
            bounds = element.info.get('bounds')
            lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
            h = int(ry) - int(ly)
            w = int(rx) - int(lx)
        elif area:
            self.temp_file_data = self.driver.screenshot(format='pillow').crop(area)
            h = int(area[3]) - int(area[1])
            w = int(area[2]) - int(area[0])
        else:
            return None
        if not self.temp_file_data:
            return None
        if save_path:
            aklog_printf('save screenshot to %s' % save_path)
            self.temp_file_data.save(save_path)
        lista = []
        listt = []
        listc = []
        fix_rgbs = list(fix_rgbs)
        for xk in range(0, w):
            for yk in range(0, h):
                f1 = (xk, yk)
                lista.append(f1)
                el_rgb = self.temp_file_data.getpixel((xk, yk))
                # print(el_rgb)
                if len(el_rgb) != len(fix_rgbs[0]):
                    aklog_printf('len(el_rgb) != len(fix_rgb)')
                    return None
                if el_rgb in fix_rgbs:
                    f2 = (xk, yk)
                    listt.append(f2)
                else:
                    f3 = (xk, yk)
                    listc.append(f3)
        ratio = len(listt) / len(lista)
        aklog_printf('ratio: %s' % ratio)
        return ratio

    def check_video_image_is_normal(self, element=None, area=None, threshold=10, save_path=None, re_shot=True):
        """
        用OpenCV方式检查画面是否正常，当为全黑、全白、全绿，或其他接近纯色的，返回False
        save_path: 将截图数据保存到文件
        re_shot: 是否重新截图，或者使用上一次的temp_file_data
        """
        aklog_printf('check_video_image_is_normal, threshold: %s' % threshold)
        try:
            # 获取元素的坐标和大小
            if element is not None:
                bounds = element.info['bounds']
                left, top, right, bottom = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
            elif area:
                left, top, right, bottom = area
            else:
                return None
            # 截取视频画面截图
            if re_shot:
                self.temp_file_data = self.driver.screenshot(format='pillow')
            screenshot = image_convert(self.temp_file_data, format='opencv')
            if save_path:
                aklog_printf('save screenshot to %s' % save_path)
                self.temp_file_data.save(save_path)
            image = screenshot[top:bottom, left:right]
            # 将截图转换成灰度图像
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 判断是否为纯绿色
            green_color = [0, 255, 0]
            green_diff = np.abs(image - green_color)
            if np.mean(green_diff) < threshold:
                aklog_debug('画面显示为纯绿色')
                return False

            # 判断是否为纯红色
            red_color = [0, 0, 255]
            red_diff = np.abs(image - red_color)
            if np.mean(red_diff) < threshold:
                aklog_debug('画面显示为纯红色')
                return False

            # 判断是否为纯蓝色
            blue_color = [255, 0, 0]
            blue_diff = np.abs(image - blue_color)
            if np.mean(blue_diff) < threshold:
                aklog_debug('画面显示为纯蓝色')
                return False

            # 判断是否为纯黑或纯白
            mean_deviation = np.mean(gray_image)
            if mean_deviation < threshold:
                aklog_debug('画面显示为纯黑色')
                return False
            if mean_deviation > 255 - threshold:
                aklog_debug('画面显示为纯白色')
                return False

            # 计算灰度图像的标准差，判断图像的颜色信息
            std_deviation = np.std(gray_image)
            # 设置阈值来判断画面是否正常
            if std_deviation < threshold:
                aklog_debug("画面显示异常")
                return False

            aklog_debug("画面显示正常")
            return True
        except:
            aklog_debug(traceback.format_exc())
            return None

    def detect_image_anomalies(self, element=None, area=None, save_path=None):
        """
        检测静态图片中的异常情况（黑屏、白屏、纯色屏、花屏、马赛克、静止画面等）
        自动检测遮挡区域并排除其影响
        """
        aklog_printf('detect_image_anomalies')
        try:
            # 获取元素的坐标和大小
            if element is not None:
                bounds = element.info['bounds']
                left, top, right, bottom = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
            elif area:
                left, top, right, bottom = area
            else:
                return None

            # 截取视频画面截图
            screenshot = self.driver.screenshot(format='opencv')
            if save_path:
                image = screenshot[top:bottom, left:right]
                aklog_printf('save screenshot to %s' % save_path)
                cv2.imwrite(save_path, image)
            image = screenshot[top:bottom, left:right]

            # 转换为灰度图
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 自动检测遮挡区域
            mask = self.detect_obstruction(gray_image)

            # 将遮挡区域设置为黑色
            gray_image[mask == 1] = 0

            # 初始化异常列表
            anomalies = []

            # 1. 检测黑屏
            if np.mean(gray_image) < 10:  # 平均亮度接近 0
                anomalies.append("黑屏")

            # 2. 检测白屏
            if np.mean(gray_image) > 245:  # 平均亮度接近 255
                anomalies.append("白屏")

            # 3. 检测纯色屏
            mean_color = np.mean(image, axis=(0, 1))  # 计算每个通道的平均值
            if np.std(image) < 10:  # 图像标准差很低，说明颜色几乎不变
                if mean_color[2] > 200 and mean_color[1] < 50 and mean_color[0] < 50:
                    anomalies.append("红屏")
                elif mean_color[1] > 200 and mean_color[0] < 50 and mean_color[2] < 50:
                    anomalies.append("绿屏")
                elif mean_color[0] > 200 and mean_color[1] < 50 and mean_color[2] < 50:
                    anomalies.append("蓝屏")
                else:
                    anomalies.append("其他纯色")

            # 4. 检测花屏（改进逻辑）
            edges = cv2.Canny(gray_image, 100, 200)
            edge_density = np.sum(edges) / (image.shape[0] * image.shape[1])
            # laplacian_var = cv2.Laplacian(gray_image, cv2.CV_64F).var()  # 纹理复杂度分析

            # 局部纹理分析
            h, w = gray_image.shape
            block_size = 50  # 分块大小
            local_laplacian_vars = []
            for i in range(0, h, block_size):
                for j in range(0, w, block_size):
                    block = gray_image[i:i + block_size, j:j + block_size]
                    if block.size > 0:
                        local_laplacian_vars.append(cv2.Laplacian(block, cv2.CV_64F).var())
            avg_local_laplacian = np.mean(local_laplacian_vars)

            # 判断花屏
            if edge_density > 0.5 and avg_local_laplacian < 80:  # 联合判断
                anomalies.append("花屏")

            # 5. 检测马赛克（像素块均匀性异常）
            resized_image = cv2.resize(image, (10, 10), interpolation=cv2.INTER_NEAREST)
            diff = cv2.absdiff(image, cv2.resize(resized_image, image.shape[:2][::-1], interpolation=cv2.INTER_NEAREST))
            if np.mean(diff) < 5:  # 平均差异过低，说明画面马赛克化
                anomalies.append("马赛克")

            # 6. 检测亮度异常
            # brightness = np.mean(gray_image)
            # if brightness < 50:  # 亮度过低
            #     anomalies.append("太暗")
            # elif brightness > 200:  # 亮度过高
            #     anomalies.append("太亮")

            # 返回异常列表
            if anomalies:
                aklog_debug(f'当前画面检测结果：{anomalies}')
                return False
            aklog_debug('当前画面检测结果正常')
            return True
        except:
            aklog_debug(traceback.format_exc())
            return None

    @staticmethod
    def detect_obstruction(gray_image):
        """
        自动检测遮挡区域
        :param gray_image: 灰度图像
        :return: 遮挡区域的掩码（mask），遮挡区域为 1，其他区域为 0
        """
        # 1. 边缘检测
        edges = cv2.Canny(gray_image, 50, 150)

        # 2. 轮廓检测
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 3. 创建掩码
        mask = np.zeros_like(gray_image, dtype=np.uint8)

        # 4. 遍历轮廓，筛选可能的遮挡区域
        for contour in contours:
            # 计算轮廓的边界框
            x, y, w, h = cv2.boundingRect(contour)

            # 筛选规则：面积较小且形状规则的区域可能是遮挡区域
            area = cv2.contourArea(contour)
            aspect_ratio = w / h
            if 100 < area < 5000 and 0.8 < aspect_ratio < 1.2:  # 面积和长宽比限制
                cv2.rectangle(mask, (x, y), (x + w, y + h), 1, -1)  # 将遮挡区域标记为 1

        return mask

    def get_canvas_missing_piece_loc(self, element):
        """
        获取滑块拼图验证码图片中缺块的X坐标，并以此来计算滑块移动距离
        适用于家居云登录的验证码
        """
        aklog_printf('get_canvas_missing_piece_loc')
        if element is None:
            return None
        self.temp_file_data = element.screenshot()
        bounds = element.info.get('bounds')
        lx, ly, rx, ry = bounds['left'], bounds['top'], bounds['right'], bounds['bottom']
        h = int(ry) - int(ly)
        w = int(rx) - int(lx)
        # 检查每一列像素点的颜色，缺块边缘一圈的颜色比较深（RGB像素相加少于300认为出现缺块），获取出现缺块的第一列的X坐标
        for xk in range(60, w):
            lista = []
            el_rgb_dict = {}
            for yk in range(0, h):
                f1 = (xk, yk)
                el_rgb = self.temp_file_data.getpixel((xk, yk))
                # aklog_printf('%s, %s' % (el_rgb, (xk, yk)))
                if el_rgb[0] + el_rgb[1] + el_rgb[2] < 300:
                    if str(el_rgb) not in el_rgb_dict:
                        el_rgb_dict[str(el_rgb)] = []
                    el_rgb_dict[str(el_rgb)].append(f1)
            # 过滤掉一整块为深色的颜色，缺块边缘深色的像素点色值不会完全一致
            for x in el_rgb_dict:
                if len(el_rgb_dict[x]) < 4:
                    lista.extend(el_rgb_dict[x])
            if 0 < len(lista) < 32:
                return xk
        return None

    def get_screenshot_by_element(self, element: Union[UiObject, XMLElement], save_path=None):
        aklog_printf('get_screenshot_by_element')
        try:
            self.temp_file_data = element.screenshot()
            if save_path:
                aklog_printf('save screenshot to %s' % save_path)
                self.temp_file_data.save(save_path)
            return self
        except:
            aklog_error('截图失败')
            self.temp_file_data = None
            aklog_printf(str(traceback.format_exc()))
            return self

    def get_rgb_by_location(self, x, y):
        """获取指定坐标的rgb色值"""
        temp_file_data = self.driver.screenshot(format='pillow')
        el_rgb = temp_file_data.getpixel((x, y))
        return el_rgb

    def get_screenshot_by_custom_size(self, start_x, start_y, end_x, end_y):
        # 自定义截取范围
        try:
            aklog_printf('get_screenshot_by_custom_size: (%s, %s, %s, %s)' % (start_x, start_y, end_x, end_y))
            box = (start_x, start_y, end_x, end_y)
            self.temp_file_data = self.driver.screenshot(format='pillow').crop(box)
            return self
        except:
            self.temp_file_data = None
            aklog_printf(str(traceback.format_exc()))
            return self

    def write_to_file(self, image_dir, image_name, form="png"):
        # 将截屏文件复制到指定目录下
        try:
            if not os.path.isdir(image_dir):
                os.makedirs(image_dir)
            self.temp_file_data.save(self.PATH(image_dir + "/" + image_name + "." + form))
            return True
        except:
            aklog_printf(str(traceback.format_exc()))
            return False

    @staticmethod
    def load_image(image_path):
        # 加载目标图片供对比用
        try:
            if os.path.isfile(image_path):
                load = Image.open(image_path)
                return load
            else:
                aklog_printf("%s is not exist" % image_path)
                return None
        except:
            aklog_printf(str(traceback.format_exc()))
            return None

    def same_as(self, load_image, percent):
        """对比图片，percent值设为0，则100%相似时返回True，设置的值越大，相差越大"""
        try:
            if self.temp_file_data is None:
                return False
            image1 = self.temp_file_data
            image2 = load_image
            histogram1 = image1.histogram()
            histogram2 = image2.histogram()
            differ = math.sqrt(functools.reduce(operator.add, list(map(lambda a, b: (a - b) ** 2,
                                                                       histogram1, histogram2))) / len(histogram1))
            aklog_printf('differ : %s' % differ)
            if differ <= percent:
                return True
            else:
                return False
        except:
            aklog_printf(str(traceback.format_exc()))
            return False

    def compare_image(self, element, image_path, percent):
        """判断元素图片跟预期的图片是否一致"""
        aklog_printf('compare_image')
        load_image = self.load_image(image_path)
        result = self.get_screenshot_by_element(element).same_as(load_image, percent)
        return result

    def convert_resolution(self, dst_resolution):
        """
        将截图转换成对应的分辨率
        :param dst_resolution: (800, 480)
        :return:
        """
        aklog_printf('convert_resolution')
        try:
            self.temp_file_data.thumbnail(dst_resolution)
            return self
        except:
            aklog_printf(str(traceback.format_exc()))
            return self

    def png_2_jpg(self):
        """PNG格式转JPG格式图片"""
        aklog_printf('png_2_jpg')
        self.temp_file_data.save(self.TEMP_FILE)
        infile = self.TEMP_FILE
        outfile = os.path.splitext(infile)[0] + ".jpg"
        try:
            im = cv2.imread(infile)
            cv2.imwrite(outfile, im)
            self.temp_file_data = Image.open(outfile)
            return self
        except:
            aklog_printf("PNG转换JPG 错误" + str(traceback.format_exc()))
            return self

    def compare_image_after_convert_resolution(self, element, image_path, percent):
        """截图转换成跟对比的图片相同分辨率之后再对比"""
        aklog_printf('compare_image_after_convert_resolution')
        load_image = self.load_image(image_path)
        img_size = load_image.size
        self.get_screenshot_by_element(element)
        self.png_2_jpg()
        result = self.convert_resolution(img_size).same_as(load_image, percent)
        return result

    def image_ocr_to_string(self):
        """
        识别图片中的文字并输出，可以识别获取安卓室内机状态中的时间日期
        """
        if self.temp_file_data is None:
            return None
        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = root_path + '\\tools\\Tesseract-OCR\\tesseract.exe'
            string = pytesseract.image_to_string(self.temp_file_data, timeout=10)
            aklog_printf(string)
            return string
        except:
            aklog_printf(traceback.format_exc())
            return None

    def image_easyocr_read_text(self):
        """
        用easyocr模块来识别，会比pytesseract更准确，建议使用这种方式
        注意easyocr（版本1.5.0）跟opencv的高版本会冲突，需要使用4.5.1.48版本
        """
        try:
            if self.temp_file_data is None:
                return None

            global easyocr_instance
            if easyocr_instance is None:
                import easyocr

                model_folder = root_path + '\\testcase\\utils\\EasyOCR\\model'
                easyocr_instance = easyocr.Reader(['ch_sim', 'en'], gpu=False, model_storage_directory=model_folder)

            self.temp_file_data.save(self.TEMP_FILE)
            ret = easyocr_instance.readtext(self.TEMP_FILE)
            if not ret:
                return None
            text_list = []
            for i in ret:
                text = i[1]
                text_list.append(text)
            if len(text_list) == 1:
                aklog_printf(text_list[0])
                return text_list[0]
            else:
                aklog_printf(text_list)
                return text_list
        except:
            aklog_printf(traceback.format_exc())
            return None

    def preprocess_image(self, max_width=None, max_height=None, quality=85):
        """
        预处理图片，限制最大宽高，避免OCR崩溃和提升速度
        Args:
            max_width (int): 最大宽度
            max_height (int): 最大高度
            quality (int): 图片压缩质量 0-100
        Returns:
            str: 预处理后的图片路径（临时文件）
        """
        try:
            img = self.temp_file_data
            w, h = img.size
            scale_w = scale_h = 1.0

            if max_width is not None and w > max_width:
                scale_w = max_width / w
            if max_height is not None and h > max_height:
                scale_h = max_height / h
            # 取最小缩放因子，保证宽高都不超过限制
            scale = min(scale_w, scale_h)

            # 判断是否需要缩放
            need_resize = scale < 1.0
            # 判断是否需要格式转换
            need_convert = img.format is None or img.format.lower() != 'jpeg'
            # 判断是否需要压缩
            need_compress = quality < 100

            # 只要有一项需要处理，就生成临时文件
            if need_resize or need_convert or need_compress:
                # 统一转换为RGB，防止PNG等带透明通道报错
                img = img.convert('RGB')
                if need_resize:
                    new_size = (int(w * scale), int(h * scale))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    # aklog_debug(f"图片已缩放到{new_size}")
                # 生成临时文件名，防止重复
                temp_file = os.path.splitext(self.TEMP_FILE)[0] + f".{quality}_ocr_tmp.jpg"
                img.save(temp_file, format='JPEG', quality=quality)
                # aklog_debug(f"图片已保存为JPG格式，路径: {temp_file}，压缩质量: {quality}")
                return temp_file
            else:
                # aklog_debug("图片无需缩放、格式转换或压缩，直接返回原图路径")
                return self.TEMP_FILE
        except Exception as e:
            aklog_error(f"图片预处理失败: {e}")
            return self.TEMP_FILE

    def image_paddleocr_to_text(self, preprocess=True) -> list:
        """图片识别，精准度比较高"""
        aklog_printf()
        self.temp_file_data.save(self.TEMP_FILE)
        if preprocess:
            image_file = self.preprocess_image(max_width=1280)
        else:
            image_file = self.TEMP_FILE
        try:
            global paddleocr_instance
            if paddleocr_instance is None:
                from paddlex import create_pipeline
                from paddlex.utils.logging import setup_logging

                setup_logging('WARNING')
                pipe_file = root_path + '\\testcase\\utils\\.paddlex\\OCR.yaml'
                paddleocr_instance = create_pipeline(pipeline=pipe_file)

            output = paddleocr_instance.predict(
                input=image_file,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            texts = []
            for res in output:
                texts = res.json.get('res').get('rec_texts')
                break
            aklog_printf('paddleocr texts: %s' % texts)
            return texts
        except Exception as e:
            aklog_error(f'Exception: {e}')
            # aklog_printf(traceback.format_exc())
            return []
        finally:
            # 用完后可删除临时文件
            if image_file.endswith("ocr_tmp.jpg"):
                os.remove(image_file)

    def image_ocr_to_texts(self) -> list:
        """使用微信OCR识别文本"""
        aklog_printf()
        self.temp_file_data.save(self.TEMP_FILE)
        texts = wechat_ocr(self.TEMP_FILE)
        aklog_debug(f'texts: {texts}')
        return texts


class ImageProcessIOS(object):

    def __init__(self, driver: Optional[Client], device_name=''):
        self.driver: Optional[Client] = driver
        self.device_name = device_name or ''
        self.PATH = lambda p: os.path.abspath(p)
        if self.device_name:
            os.makedirs(os.path.join(tempfile.gettempdir(), self.device_name), exist_ok=True)
            temp_dir = self.PATH(os.path.join(tempfile.gettempdir(), self.device_name))
        else:
            temp_dir = tempfile.gettempdir()
        self.TEMP_FILE = self.PATH(os.path.join(temp_dir, "temp_screen.png"))
        self.temp_file_data = None

    def screenshots_as_base64(self):
        try:
            data = self.driver.screenshot(format='raw')
            # b64encode是编码，b64decode是解码
            base64_data = base64.b64encode(data).decode('utf-8')
            return base64_data
        except:
            aklog_printf('截图失败，' + str(traceback.format_exc()))
            return None

    def is_pure_color(self, element: Element = None, area=None, percent=0, save_path=None):
        """检查图片是否是纯色"""
        aklog_printf('is_pure_color, percent: %s' % percent)
        try:
            if element is not None:
                self.get_screenshot_by_element(element)
                bounds = element.bounds
                lx, ly, w, h = bounds[0] * 3, bounds[1] * 3, bounds[2] * 3, bounds[3] * 3
            elif area:
                self.temp_file_data = self.driver.screenshot(format='pillow').crop(area)
                h = int(area[3]) - int(area[1])
                w = int(area[2]) - int(area[0])
            else:
                return None
            if not self.temp_file_data:
                return None
            if save_path:
                aklog_printf('save screenshot to %s' % save_path)
                self.temp_file_data.save(save_path)
            list_all = []
            el_rgb_dict = {}
            # 遍历像素，并将相同颜色的像素进行归类成字典，key为像素颜色，value为该颜色的像素数量
            for xk in range(0, w):
                for yk in range(0, h):
                    f1 = (xk, yk)
                    list_all.append(f1)
                    el_rgb = self.temp_file_data.getpixel((xk, yk))
                    # print(el_rgb)
                    if str(el_rgb) not in el_rgb_dict:
                        el_rgb_dict[str(el_rgb)] = []
                        el_rgb_dict[str(el_rgb)].append(f1)
                    else:
                        el_rgb_dict[str(el_rgb)].append(f1)
            # 然后比较相同颜色的像素数量占比
            max_rgb_len = 0
            most_colors = ''
            for key in el_rgb_dict.keys():
                rgb_len = len(el_rgb_dict[key])
                if rgb_len > max_rgb_len:
                    max_rgb_len = rgb_len
                    most_colors = key
            max_ratio = max_rgb_len / len(list_all)
            if max_ratio > percent:
                aklog_printf('color %s, ratio: %s' % (most_colors, max_ratio))
                aklog_printf('画面显示异常，颜色 %s 占比超过 %s' % (most_colors, percent))
                return True
            else:
                aklog_printf('color %s is most，ratio: %s' % (most_colors, max_ratio))
                aklog_printf('画面显示正常，没有颜色占比超过 %s' % percent)
                return False
        except:
            aklog_printf(traceback.format_exc())
            return None

    def is_light_color(self, element: Element = None, area=None, rgb_sum=300, percent=0.5):
        """
        检查图片颜色是否为浅色
        rgb_sum: rgb三种数值相加，
        大于rgb_sum的占比超过percent，表示为浅色，否则为深色
        """
        aklog_printf('check_color_depth: rgb_sum: %s, percent: %s' % (rgb_sum, percent))
        try:
            if element is not None:
                self.get_screenshot_by_element(element)
                bounds = element.bounds
                lx, ly, w, h = bounds[0] * 3, bounds[1] * 3, bounds[2] * 3, bounds[3] * 3
            elif area:
                self.temp_file_data = self.driver.screenshot(format='pillow').crop(area)
                h = int(area[3]) - int(area[1])
                w = int(area[2]) - int(area[0])
            else:
                return None
            if not self.temp_file_data:
                return None
            list_all = []
            el_rgb_list = []
            # 遍历像素，并将相同颜色的像素进行归类成字典，key为像素颜色，value为该颜色的像素数量
            for xk in range(0, w):
                for yk in range(0, h):
                    f1 = (xk, yk)
                    list_all.append(f1)
                    el_rgb = self.temp_file_data.getpixel((xk, yk))
                    # 将颜色rgb三个数字相加
                    el_rgb_sum = el_rgb[0] + el_rgb[1] + el_rgb[2]
                    if el_rgb_sum > rgb_sum:
                        el_rgb_list.append(el_rgb)

            # 然后比较相同颜色的像素数量占比
            ratio = len(el_rgb_list) / len(list_all)
            aklog_printf('el_rgb_sum > rgb_sum, ratio: %s' % ratio)
            if ratio > percent:
                aklog_printf('Color is light')
                return True
            else:
                aklog_printf('Color is dark')
                return False
        except:
            aklog_printf(traceback.format_exc())
            return None

    def check_rgb_sum(self, element: Element = None, area=None, rgb_sum=300):
        """
        获取rgb_sum占比
        rgb_sum: rgb三种数值相加
        """
        aklog_printf(f'check_rgb_sum: {rgb_sum}')
        try:
            if element is not None:
                self.get_screenshot_by_element(element)
                bounds = element.bounds
                lx, ly, w, h = bounds[0] * 3, bounds[1] * 3, bounds[2] * 3, bounds[3] * 3
            elif area:
                self.temp_file_data = self.driver.screenshot(format='pillow').crop(area)
                h = int(area[3]) - int(area[1])
                w = int(area[2]) - int(area[0])
            else:
                return None
            if not self.temp_file_data:
                return None
            list_all = []
            el_rgb_list = []
            # 遍历像素，并将相同颜色的像素进行归类成字典，key为像素颜色，value为该颜色的像素数量
            for xk in range(0, w):
                for yk in range(0, h):
                    f1 = (xk, yk)
                    list_all.append(f1)
                    el_rgb = self.temp_file_data.getpixel((xk, yk))
                    # 将颜色rgb三个数字相加
                    el_rgb_sum = el_rgb[0] + el_rgb[1] + el_rgb[2]
                    if el_rgb_sum > rgb_sum:
                        el_rgb_list.append(el_rgb)

            # 然后比较相同颜色的像素数量占比
            ratio = len(el_rgb_list) / len(list_all)
            aklog_printf(f'rgb_sum: {rgb_sum}, ratio: {ratio}')
            return ratio
        except:
            aklog_printf(traceback.format_exc())
            return None

    def check_screen_color(self, element: Element = None, area=None, fix_rgb=None):
        """
        检查界面某种颜色占比
        fix_rgb: (0,0,0)
        """
        aklog_printf('check_screen_color')

        if element is not None:
            self.get_screenshot_by_element(element)
            bounds = element.bounds
            lx, ly, w, h = bounds[0] * 3, bounds[1] * 3, bounds[2] * 3, bounds[3] * 3
        elif area:
            self.temp_file_data = self.driver.screenshot(format='pillow').crop(area)
            h = int(area[3]) - int(area[1])
            w = int(area[2]) - int(area[0])
        else:
            return None
        if not self.temp_file_data:
            return None
        lista = []
        listt = []
        listc = []
        for xk in range(0, w):
            for yk in range(0, h):
                f1 = (xk, yk)
                lista.append(f1)
                el_rgb = self.temp_file_data.getpixel((xk, yk))
                # print(el_rgb)
                if len(el_rgb) != len(fix_rgb):
                    aklog_printf('len(el_rgb) != len(fix_rgb)')
                    return None
                if el_rgb == fix_rgb:
                    f2 = (xk, yk)
                    listt.append(f2)
                else:
                    f3 = (xk, yk)
                    listc.append(f3)
        ratio = len(listt) / len(lista)
        aklog_printf('ratio: %s' % ratio)
        return ratio

    def is_similar_color(self, element: Element = None, area=None, color=None,
                         lower_hsv=None, upper_hsv=None, threshold=0.1):
        """
        检查颜色跟哪一种比较相似，比如可以区分元素的颜色是橙色还是蓝色
        偏蓝色的HSV范围：
        下限：H = 90, S = 150, V = 0
        上限：H = 140, S = 255, V = 255
        偏橙色黄色的HSV范围：
        下限：H = 10, S = 100, V = 100
        上限：H = 35, S = 255, V = 255

        以下是几种常见颜色的 HSV 范围：
        1. 红色
           - 低范围：([0, 70, 50])
           - 高范围：([10, 255, 255])
           - 低范围：([170, 70, 50])
           - 高范围：([180, 255, 255])

        2. 绿色
           - 低范围：([35, 70, 50])
           - 高范围：([85, 255, 255])

        3. 蓝色（包括深蓝色和浅蓝色）
           - 低范围：([90, 70, 50])
           - 高范围：([140, 255, 255])

        4. 黄色
           - 低范围：([25, 70, 50])
           - 高范围：([35, 255, 255])

        5. 橙色（包括深橙色和浅橙色）
           - 低范围：([10, 70, 50])
           - 高范围：([25, 255, 255])

        6. 紫色
           - 低范围：([130, 70, 50])
           - 高范围：([160, 255, 255])
        这些范围可以根据具体需求进行微调，以适应不同的光照条件和图像质量。
        Args:
            element (class):
            area (tuple):
            color (str): blue/red/green/yellow/orange/purple
            lower_hsv (list): [90, 50, 0]
            upper_hsv (list): [140, 255, 255]
            threshold (float): 颜色占比阈值
        """
        if element is not None:
            self.get_screenshot_by_element(element)
        elif area:
            self.temp_file_data = self.driver.screenshot(format='pillow').crop(area)
        else:
            return None
        if not self.temp_file_data:
            return None
        # 打开图像并转换为 OpenCV 格式
        image_cv = cv2.cvtColor(np.array(self.temp_file_data), cv2.COLOR_RGB2BGR)
        # 转换为 HSV 色彩空间
        hsv_image = cv2.cvtColor(image_cv, cv2.COLOR_BGR2HSV)
        hsv_data = {
            'red': [
                ([0, 70, 50], [10, 255, 255]),
                ([170, 70, 50], [180, 255, 255])
            ],
            'orange': [([10, 70, 50], [25, 255, 255])],
            'brown': [([10, 51, 51], [30, 255, 229])],
            'yellow': [([25, 70, 50], [35, 255, 255])],
            'green': [([35, 70, 50], [85, 255, 255])],
            'blue': [([90, 70, 50], [140, 255, 255])],
            'purple': [([130, 70, 50], [160, 255, 255])]
        }
        # 获取颜色的 HSV 范围
        if color:
            color_ranges = hsv_data.get(color, [])

            if len(color_ranges) == 2:
                range_pair1, range_pair2 = color_ranges
                mask1 = cv2.inRange(hsv_image, np.array(range_pair1[0]), np.array(range_pair1[1]))
                mask2 = cv2.inRange(hsv_image, np.array(range_pair2[0]), np.array(range_pair2[1]))
                combined_mask = cv2.bitwise_or(mask1, mask2)
            else:
                range_pair = color_ranges[0]
                combined_mask = cv2.inRange(hsv_image, np.array(range_pair[0]), np.array(range_pair[1]))
        elif lower_hsv and upper_hsv:
            combined_mask = cv2.inRange(hsv_image, np.array(lower_hsv), np.array(upper_hsv))
        else:
            return None

        # 计算颜色占比
        total_pixels = combined_mask.size
        color_pixels = cv2.countNonZero(combined_mask)
        color_ratio = color_pixels / total_pixels
        aklog_printf(f'color_ratio: {color_ratio}')
        return color_ratio > threshold

    def check_screen_colors(self, *fix_rgbs, element: Element = None, area=None):
        """
        检查界面某几种颜色总共占比
        fix_rgbs: (0,0,0)
        """
        aklog_printf(f'check_screen_colors: {fix_rgbs}')

        if element is not None:
            self.get_screenshot_by_element(element)
            bounds = element.bounds
            lx, ly, w, h = bounds[0] * 3, bounds[1] * 3, bounds[2] * 3, bounds[3] * 3
        elif area:
            self.temp_file_data = self.driver.screenshot(format='pillow').crop(area)
            h = int(area[3]) - int(area[1])
            w = int(area[2]) - int(area[0])
        else:
            return None
        if not self.temp_file_data:
            return None
        lista = []
        listt = []
        listc = []
        fix_rgbs = list(fix_rgbs)
        for xk in range(0, w):
            for yk in range(0, h):
                f1 = (xk, yk)
                lista.append(f1)
                el_rgb = self.temp_file_data.getpixel((xk, yk))
                # print(el_rgb)
                if len(el_rgb) != len(fix_rgbs[0]):
                    aklog_printf('len(el_rgb) != len(fix_rgb)')
                    return None
                if el_rgb in fix_rgbs:
                    f2 = (xk, yk)
                    listt.append(f2)
                else:
                    f3 = (xk, yk)
                    listc.append(f3)
        ratio = len(listt) / len(lista)
        aklog_printf('ratio: %s' % ratio)
        return ratio

    def check_video_image_is_normal(self, element: Element = None, area=None, threshold=10, save_path=None):
        """用OpenCV方式检查画面是否正常，当为全黑、全白、全绿，或其他接近纯色的，返回False"""
        aklog_debug()
        try:
            # 获取元素的坐标和大小
            if element is not None:
                bounds = element.bounds
                lx, ly, w, h = bounds[0] * 3, bounds[1] * 3, bounds[2] * 3, bounds[3] * 3
                rx = lx + w
                ry = ly + h
            elif area:
                lx, ly, rx, ry = area
            else:
                return None
            # 截取视频画面截图
            raw_value = self.driver.screenshot(format='pillow')
            nparr = np.fromstring(raw_value, np.uint8)
            screenshot = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if save_path:
                aklog_printf('save screenshot to %s' % save_path)
                cv2.imwrite(save_path, screenshot)

            image = screenshot[ly:ry, lx:rx]
            # 将截图转换成灰度图像
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 判断是否为纯绿色
            green_color = [0, 255, 0]
            green_diff = np.abs(image - green_color)
            if np.mean(green_diff) < threshold:
                aklog_debug('画面显示为纯绿色')
                return False

            # 判断是否为纯红色
            red_color = [0, 0, 255]
            red_diff = np.abs(image - red_color)
            if np.mean(red_diff) < threshold:
                aklog_debug('画面显示为纯红色')
                return False

            # 判断是否为纯蓝色
            blue_color = [255, 0, 0]
            blue_diff = np.abs(image - blue_color)
            if np.mean(blue_diff) < threshold:
                aklog_debug('画面显示为纯蓝色')
                return False

            # 判断是否为纯黑或纯白
            mean_deviation = np.mean(gray_image)
            if mean_deviation < threshold:
                aklog_debug('画面显示为纯黑色')
                return False
            if mean_deviation > 255 - threshold:
                aklog_debug('画面显示为纯白色')
                return False

            # 计算灰度图像的标准差，判断图像的颜色信息
            std_deviation = np.std(gray_image)
            # 设置阈值来判断画面是否正常
            if std_deviation < threshold:
                aklog_debug("画面显示异常")
                return False

            aklog_debug("画面显示正常")
            return True
        except:
            aklog_debug(traceback.format_exc())
            return None

    def get_canvas_missing_piece_loc(self, element: Element):
        """
        获取滑块拼图验证码图片中缺块的X坐标，并以此来计算滑块移动距离
        适用于家居云登录的验证码
        """
        aklog_printf('get_canvas_missing_piece_loc')
        if element is None:
            return None
        # 先截取整个屏幕，存储至系统临时目录下
        self.driver.screenshot(self.TEMP_FILE)
        # 获取元素bounds
        bounds = element.bounds
        lx, ly, w, h = bounds[0] * 3, bounds[1] * 3, bounds[2] * 3, bounds[3] * 3
        box = (lx, ly, lx + w, ly + h)
        self.temp_file_data = self.driver.screenshot(format='pillow').crop(box)
        # 检查每一列像素点的颜色，缺块边缘一圈的颜色比较深（RGB像素相加少于300认为出现缺块），获取出现缺块的第一列的X坐标
        for xk in range(60, w):
            lista = []
            el_rgb_dict = {}
            for yk in range(0, h):
                f1 = (xk, yk)
                el_rgb = self.temp_file_data.getpixel((xk, yk))
                # aklog_printf('%s, %s' % (el_rgb, (xk, yk)))
                if el_rgb[0] + el_rgb[1] + el_rgb[2] < 300:
                    if str(el_rgb) not in el_rgb_dict:
                        el_rgb_dict[str(el_rgb)] = []
                    el_rgb_dict[str(el_rgb)].append(f1)
            # 过滤掉一整块为深色的颜色，缺块边缘深色的像素点色值不会完全一致
            for x in el_rgb_dict:
                if len(el_rgb_dict[x]) < 4:
                    lista.extend(el_rgb_dict[x])
            if 0 < len(lista) < 32:
                return xk
        return None

    def get_screenshot_by_element(self, element: Element):
        aklog_printf('get_screenshot_by_element')
        try:
            # 先截取整个屏幕，存储至系统临时目录下
            self.driver.screenshot(self.TEMP_FILE)
            # 获取元素bounds
            bounds = element.bounds
            lx, ly, w, h = bounds[0] * 3, bounds[1] * 3, bounds[2] * 3, bounds[3] * 3
            box = (lx, ly, lx + w, ly + h)
            self.temp_file_data = self.driver.screenshot(format='pillow').crop(box)
            # 截取图片
            image = Image.open(self.TEMP_FILE)
            self.temp_file_data = image.crop(box)
            self.temp_file_data.save(self.TEMP_FILE)
            return self
        except:
            aklog_error('截图失败')
            self.temp_file_data = None
            aklog_printf(str(traceback.format_exc()))
            return self

    def get_screenshot_by_custom_size(self, start_x, start_y, end_x, end_y):
        # 自定义截取范围
        try:
            aklog_printf('get_screenshot_by_custom_size: (%s, %s, %s, %s)' % (start_x, start_y, end_x, end_y))
            box = (start_x, start_y, end_x, end_y)
            self.temp_file_data = self.driver.screenshot(format='pillow').crop(box)
            return self
        except:
            self.temp_file_data = None
            aklog_printf(str(traceback.format_exc()))
            return self

    def write_to_file(self, image_dir, image_name, form="png"):
        # 将截屏文件复制到指定目录下
        try:
            if not os.path.isdir(image_dir):
                os.makedirs(image_dir)
            self.temp_file_data.save(self.PATH(image_dir + "/" + image_name + "." + form))
            return True
        except:
            aklog_printf(str(traceback.format_exc()))
            return False

    @staticmethod
    def load_image(image_path):
        # 加载目标图片供对比用
        try:
            if os.path.isfile(image_path):
                load = Image.open(image_path)
                return load
            else:
                aklog_printf("%s is not exist" % image_path)
                return None
        except:
            aklog_printf(str(traceback.format_exc()))
            return None

    def same_as(self, load_image, percent):
        """对比图片，percent值设为0，则100%相似时返回True，设置的值越大，相差越大"""
        try:
            if self.temp_file_data is None:
                return False
            image1 = self.temp_file_data
            image2 = load_image
            histogram1 = image1.histogram()
            histogram2 = image2.histogram()
            differ = math.sqrt(functools.reduce(operator.add, list(map(lambda a, b: (a - b) ** 2,
                                                                       histogram1, histogram2))) / len(histogram1))
            aklog_printf('differ : %s' % differ)
            if differ <= percent:
                return True
            else:
                return False
        except:
            aklog_printf(str(traceback.format_exc()))
            return False

    def compare_image(self, element, image_path, percent):
        """判断元素图片跟预期的图片是否一致"""
        aklog_printf('compare_image')
        load_image = self.load_image(image_path)
        result = self.get_screenshot_by_element(element).same_as(load_image, percent)
        return result

    def convert_resolution(self, dst_resolution):
        """
        将截图转换成对应的分辨率
        :param dst_resolution: (800, 480)
        :return:
        """
        aklog_printf('convert_resolution')
        try:
            self.temp_file_data.thumbnail(dst_resolution)
            return self
        except:
            aklog_printf(str(traceback.format_exc()))
            return self

    def png_2_jpg(self):
        """PNG格式转JPG格式图片"""
        aklog_printf('png_2_jpg')
        self.temp_file_data.save(self.TEMP_FILE)
        infile = self.TEMP_FILE
        outfile = os.path.splitext(infile)[0] + ".jpg"
        try:
            im = cv2.imread(infile)
            cv2.imwrite(outfile, im)
            self.temp_file_data = Image.open(outfile)
            return self
        except:
            aklog_printf("PNG转换JPG 错误" + str(traceback.format_exc()))
            return self

    def compare_image_after_convert_resolution(self, element, image_path, percent):
        """截图转换成跟对比的图片相同分辨率之后再对比"""
        aklog_printf('compare_image_after_convert_resolution')
        load_image = self.load_image(image_path)
        img_size = load_image.size
        self.get_screenshot_by_element(element)
        self.png_2_jpg()
        result = self.convert_resolution(img_size).same_as(load_image, percent)
        return result

    def image_ocr_to_string(self):
        """
        识别图片中的文字并输出，可以识别获取安卓室内机状态中的时间日期
        """
        if self.temp_file_data is None:
            return None
        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = root_path + '\\tools\\Tesseract-OCR\\tesseract.exe'
            string = pytesseract.image_to_string(self.temp_file_data, timeout=10)
            aklog_printf(string)
            return string
        except:
            aklog_printf(traceback.format_exc())
            return None

    def image_easyocr_read_text(self):
        """
        用easyocr模块来识别，会比pytesseract更准确，建议使用这种方式
        注意easyocr（版本1.5.0）跟opencv的高版本会冲突，需要使用4.5.1.48版本
        """
        try:
            if self.temp_file_data is None:
                return None

            global easyocr_instance
            if easyocr_instance is None:
                import easyocr

                model_folder = root_path + '\\testcase\\utils\\EasyOCR\\model'
                easyocr_instance = easyocr.Reader(['ch_sim', 'en'], gpu=False, model_storage_directory=model_folder)

            self.temp_file_data.save(self.TEMP_FILE)
            ret = easyocr_instance.readtext(self.TEMP_FILE)
            if not ret:
                return None
            text_list = []
            for i in ret:
                text = i[1]
                text_list.append(text)
            if len(text_list) == 1:
                aklog_printf(text_list[0])
                return text_list[0]
            else:
                aklog_printf(text_list)
                return text_list
        except:
            aklog_printf(traceback.format_exc())
            return None

    def image_ocr_to_texts(self) -> list:
        """使用微信OCR识别文本"""
        aklog_printf()
        self.temp_file_data.save(self.TEMP_FILE)
        texts = wechat_ocr(self.TEMP_FILE)
        aklog_debug(f'texts: {texts}')
        return texts


# region 图像比对单独使用接口

def png_2_jpg(src_path, dst_path=None):
    """PNG格式转JPG格式"""
    if src_path.endswith('.jpg'):
        aklog_printf('图片已经是jpg格式')
        return src_path
    if not src_path.endswith('.png'):
        aklog_printf('原图片不是png格式')
        return None
    if not dst_path:
        outfile = src_path.replace('.png', '.jpg')
    else:
        outfile = dst_path
    # img = Image.open(infile)
    # img = img.resize((int(w / 2), int(h / 2)), Image.ANTIALIAS)
    try:
        # colors = img.split()
        # if len(colors) == 4:
        #     # prevent IOError: cannot write mode RGBA as BMP
        #     r, g, b, a = colors
        #     img = Image.merge("RGB", (r, g, b))
        #
        # img.convert('RGB').save(outfile, quality=100)
        im = cv2.imread(src_path)
        cv2.imwrite(outfile, im)
        return outfile
    except:
        aklog_printf("PNG转换JPG 错误" + str(traceback.format_exc()))
        return None


def image_compare(image1_path, image2_path, percent):
    """
    2025.5.14 后面慢慢不用这个接口. 使用intercombase里的image_compare.


    eg:
        self.master_android_door.image_compare(eleid, 'C:\\1.png', 0.95)
        self.master_linux_door.image_compare('C:\\22.png', 'C:\\1.png', 0.95)

    percent: 不相似度.
    # 对比图片，percent值设为0，则100%相似时返回True，设置的值越大，相差越大
    """
    aklog_printf()
    try:
        if not os.path.exists(image1_path):
            aklog_error('%s 不存在' % image1_path)
            return None
        if not os.path.exists(image2_path):
            aklog_error('%s 不存在' % image2_path)
            return None
        image1 = Image.open(image1_path)
        image2 = Image.open(image2_path)

        histogram1 = image1.histogram()
        histogram2 = image2.histogram()

        differ = math.sqrt(functools.reduce(operator.add, list(map(lambda a, b: (a - b) ** 2,
                                                                   histogram1, histogram2))) / len(histogram1))
        aklog_printf('differ : %s' % differ)
        if differ <= percent:
            return True
        else:
            return False
    except:
        aklog_printf(str(traceback.format_exc()))
        return False


def image_crop_by_pixel(imagepath, aftimagepath, startx, starty, width, height):
    """
    2024.5.24 lex 根据像素裁剪图片
        ele = self.get_element(eleid)
        startx = int(ele.value_of_css_property('left').replace('px', ''))
        starty = int(ele.value_of_css_property('top').replace('px', ''))
        width = int(ele.value_of_css_property('width').replace('px', ''))
        height = int(ele.value_of_css_property('height').replace('px', ''))
    """
    img = cv2.imread(imagepath)
    if img is None:
        aklog_error("Error: Could not read image")
        return
    cropped_img = img[starty:starty + height, startx:startx + width]
    cv2.imwrite(aftimagepath, cropped_img)


def image_compare_after_convert_resolution(image1_path, image2_path, percent):
    # 对比图片，percent值设为0，则100%相似时返回True，设置的值越大，相差越大
    # 如果为png格式的图片，需要转换成jpg格式，然后再对比
    aklog_printf()
    if not os.path.exists(image1_path):
        aklog_error('对比图片: {} 不存在!'.format(image1_path))
        return False
    if not os.path.exists(image2_path):
        aklog_error('对比图片: {} 不存在!'.format(image2_path))
        return False
    try:
        image1_tmp = png_2_jpg(image1_path)
        image2_tmp = png_2_jpg(image2_path)

        image1 = Image.open(image1_tmp)
        image1_size = image1.size
        # print(image1_size)
        image2 = Image.open(image2_tmp)
        image2.thumbnail(image1_size)
        # image2.save(r'D:\Users\Administrator\Desktop\333.jpg')

        histogram1 = image1.histogram()
        histogram2 = image2.histogram()

        differ = math.sqrt(functools.reduce(operator.add, list(map(lambda a, b: (a - b) ** 2,
                                                                   histogram1, histogram2))) / len(histogram1))
        aklog_printf('differ : %s' % differ)

        # 删除临时文件
        if image1_tmp != image1_path:
            File_process.remove_file(image1_tmp)
        if image2_tmp != image2_path:
            File_process.remove_file(image2_tmp)

        if differ <= percent:
            return True
        else:
            return False
    except:
        aklog_printf(str(traceback.format_exc()))
        return None


def check_image_is_pure_color(image_file, percent):
    """检查图片是否是纯色"""
    aklog_printf('check_image_is_pure_color')
    img = Image.open(image_file)
    h = img.height
    w = img.width
    lista = []
    el_rgb_dict = {}
    for xk in range(0, w):
        for yk in range(0, h):
            f1 = (xk, yk)
            lista.append(f1)
            el_rgb = img.getpixel((xk, yk))
            # print(el_rgb)
            if str(el_rgb) not in el_rgb_dict:
                el_rgb_dict[str(el_rgb)] = []
                el_rgb_dict[str(el_rgb)].append(f1)
            else:
                el_rgb_dict[str(el_rgb)].append(f1)
    max_ratio = 0
    most_colors = ''
    for key in el_rgb_dict.keys():
        ratio = len(el_rgb_dict[key]) / len(lista)
        if ratio > max_ratio:
            max_ratio = ratio
            most_colors = key
    if max_ratio > percent:
        aklog_printf('color %s, ratio: %s' % (most_colors, max_ratio))
        return True
    else:
        aklog_printf('color %s is most，ratio: %s' % (most_colors, max_ratio))
        aklog_printf('No color is more than %s' % percent)
        return False


def check_video_image_is_normal(image_file, threshold=10):
    """用OpenCV方式检查画面是否正常，当为全黑、全白、全绿，或其他接近纯色的，返回False"""
    aklog_debug()
    try:
        # 截取视频画面截图
        image = cv2.imread(image_file)
        # 将截图转换成灰度图像
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 判断是否为纯绿色
        green_color = [0, 255, 0]
        green_diff = np.abs(image - green_color)
        if np.mean(green_diff) < threshold:
            aklog_debug('画面显示为纯绿色')
            return False

        # 判断是否为纯红色
        red_color = [0, 0, 255]
        red_diff = np.abs(image - red_color)
        if np.mean(red_diff) < threshold:
            aklog_debug('画面显示为纯红色')
            return False

        # 判断是否为纯蓝色
        blue_color = [255, 0, 0]
        blue_diff = np.abs(image - blue_color)
        if np.mean(blue_diff) < threshold:
            aklog_debug('画面显示为纯蓝色')
            return False

        # 判断是否为纯黑或纯白
        mean_deviation = np.mean(gray_image)
        if mean_deviation < threshold:
            aklog_debug('画面显示为纯黑色')
            return False
        if mean_deviation > 255 - threshold:
            aklog_debug('画面显示为纯白色')
            return False

        # 计算灰度图像的标准差，判断图像的颜色信息
        std_deviation = np.std(gray_image)
        # 设置阈值来判断画面是否正常
        if std_deviation < threshold:
            aklog_debug("画面显示异常")
            return False

        aklog_debug("画面显示正常")
        return True
    except:
        aklog_debug(traceback.format_exc())
        return None


def detect_image_anomalies_with_url(image_url, threshold=10):
    """用OpenCV方式检查画面是否正常，当为全黑、全白、全绿，或其他接近纯色的，返回False"""
    aklog_debug()
    try:
        # 下载截图
        response = requests.get(image_url, timeout=15)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        # 转换为RGB模式
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 打开图像并转换为 OpenCV 格式
        image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # 将截图转换成灰度图像
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 判断是否为纯绿色
        green_color = [0, 255, 0]
        green_diff = np.abs(image - green_color)
        if np.mean(green_diff) < threshold:
            aklog_debug('画面显示为纯绿色')
            return False

        # 判断是否为纯红色
        red_color = [0, 0, 255]
        red_diff = np.abs(image - red_color)
        if np.mean(red_diff) < threshold:
            aklog_debug('画面显示为纯红色')
            return False

        # 判断是否为纯蓝色
        blue_color = [255, 0, 0]
        blue_diff = np.abs(image - blue_color)
        if np.mean(blue_diff) < threshold:
            aklog_debug('画面显示为纯蓝色')
            return False

        # 判断是否为纯黑或纯白
        mean_deviation = np.mean(gray_image)
        if mean_deviation < threshold:
            aklog_debug('画面显示为纯黑色')
            return False
        if mean_deviation > 255 - threshold:
            aklog_debug('画面显示为纯白色')
            return False

        # 计算灰度图像的标准差，判断图像的颜色信息
        std_deviation = np.std(gray_image)
        # 设置阈值来判断画面是否正常
        if std_deviation < threshold:
            aklog_debug("画面显示异常")
            return False

        aklog_debug("画面显示正常")
        return True
    except:
        aklog_debug(traceback.format_exc())
        return None


def detect_obstruction(gray_image):
    """
    自动检测遮挡区域
    :param gray_image: 灰度图像
    :return: 遮挡区域的掩码（mask），遮挡区域为 1，其他区域为 0
    """
    # 1. 边缘检测
    edges = cv2.Canny(gray_image, 50, 150)

    # 2. 轮廓检测
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 3. 创建掩码
    mask = np.zeros_like(gray_image, dtype=np.uint8)

    # 4. 遍历轮廓，筛选可能的遮挡区域
    for contour in contours:
        # 计算轮廓的边界框
        x, y, w, h = cv2.boundingRect(contour)

        # 筛选规则：面积较小且形状规则的区域可能是遮挡区域
        area = cv2.contourArea(contour)
        aspect_ratio = w / h
        if 100 < area < 5000 and 0.8 < aspect_ratio < 1.2:  # 面积和长宽比限制
            cv2.rectangle(mask, (x, y), (x + w, y + h), 1, -1)  # 将遮挡区域标记为 1

    return mask


def detect_image_anomalies(image_path):
    """
    检测静态图片中的异常情况（黑屏、白屏、纯色屏、花屏、马赛克、静止画面等）
    :param image_path: 当前截图路径
    :return: 异常类型列表
    """
    # 读取图片
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("无法读取图片，请检查路径是否正确")

    # 转换为灰度图
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 自动检测遮挡区域
    mask = detect_obstruction(gray_image)

    # 将遮挡区域设置为黑色
    gray_image[mask == 1] = 0

    # 初始化异常列表
    anomalies = []

    # 1. 检测黑屏
    if np.mean(gray_image) < 10:  # 平均亮度接近 0
        anomalies.append("黑屏")

    # 2. 检测白屏
    if np.mean(gray_image) > 245:  # 平均亮度接近 255
        anomalies.append("白屏")

    # 3. 检测纯色屏
    mean_color = np.mean(image, axis=(0, 1))  # 计算每个通道的平均值
    if np.std(image) < 10:  # 图像标准差很低，说明颜色几乎不变
        if mean_color[2] > 200 and mean_color[1] < 50 and mean_color[0] < 50:
            anomalies.append("红屏")
        elif mean_color[1] > 200 and mean_color[0] < 50 and mean_color[2] < 50:
            anomalies.append("绿屏")
        elif mean_color[0] > 200 and mean_color[1] < 50 and mean_color[2] < 50:
            anomalies.append("蓝屏")
        else:
            anomalies.append("其他纯色")

    # 4. 检测花屏（改进逻辑）
    edges = cv2.Canny(gray_image, 100, 200)
    edge_density = np.sum(edges) / (image.shape[0] * image.shape[1])
    # laplacian_var = cv2.Laplacian(gray_image, cv2.CV_64F).var()  # 纹理复杂度分析

    # 局部纹理分析
    h, w = gray_image.shape
    block_size = 50  # 分块大小
    local_laplacian_vars = []
    for i in range(0, h, block_size):
        for j in range(0, w, block_size):
            block = gray_image[i:i + block_size, j:j + block_size]
            if block.size > 0:
                local_laplacian_vars.append(cv2.Laplacian(block, cv2.CV_64F).var())
    avg_local_laplacian = np.mean(local_laplacian_vars)

    # 判断花屏
    if edge_density > 0.5 and avg_local_laplacian < 80:  # 联合判断
        anomalies.append("花屏")

    # 5. 检测马赛克（像素块均匀性异常）
    resized_image = cv2.resize(image, (10, 10), interpolation=cv2.INTER_NEAREST)
    diff = cv2.absdiff(image, cv2.resize(resized_image, image.shape[:2][::-1], interpolation=cv2.INTER_NEAREST))
    if np.mean(diff) < 5:  # 平均差异过低，说明画面马赛克化
        anomalies.append("马赛克")

    # 6. 检测亮度异常
    # brightness = np.mean(gray_image)
    # if brightness < 50:  # 亮度过低
    #     anomalies.append("太暗")
    # elif brightness > 200:  # 亮度过高
    #     anomalies.append("太亮")

    # 返回异常列表
    if anomalies:
        aklog_debug(f'当前画面检测结果：{anomalies}')
        return False
    aklog_debug('当前画面检测结果正常')
    return True


def image_ocr_to_string(image_path):
    """
    识别图片中的文字并输出，可以识别获取安卓室内机状态中的时间日期
    有些图片识别不是很准确，建议使用image_easyocr_read_text方法
    """
    try:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = root_path + '\\tools\\Tesseract-OCR\\tesseract.exe'
        string = pytesseract.image_to_string(Image.open(image_path), timeout=10)
        return string
    except:
        aklog_printf(traceback.format_exc())
        return None


def image_easyocr_read_text(image_path):
    """
    用easyocr模块来识别，会比pytesseract更准确，建议使用这种方式
    """
    try:
        global easyocr_instance
        if easyocr_instance is None:
            import easyocr

            model_folder = root_path + '\\testcase\\utils\\EasyOCR\\model'
            easyocr_instance = easyocr.Reader(['ch_sim', 'en'], gpu=False, model_storage_directory=model_folder)

        ret = easyocr_instance.readtext(image_path)
        text_list = []
        for i in ret:
            text = i[1]
            text_list.append(text)
        if len(text_list) == 1:
            aklog_printf(text_list[0])
            return text_list[0]
        else:
            aklog_printf(text_list)
            return text_list
    except:
        aklog_printf(traceback.format_exc())
        return None


def preprocess_image(image_file, max_width=None, max_height=None, quality=85):
    """
    预处理图片，限制最大宽高，避免OCR崩溃和提升速度
    Args:
        image_file (str): 原始图片路径
        max_width (int): 最大宽度
        max_height (int): 最大高度
        quality (int): 图片压缩质量 0-100
    Returns:
        str: 预处理后的图片路径（临时文件）
    """
    try:
        img = Image.open(image_file)
        w, h = img.size
        scale_w = scale_h = 1.0

        if max_width is not None and w > max_width:
            scale_w = max_width / w
        if max_height is not None and h > max_height:
            scale_h = max_height / h
        # 取最小缩放因子，保证宽高都不超过限制
        scale = min(scale_w, scale_h)

        # 判断是否需要缩放
        need_resize = scale < 1.0
        # 判断是否需要格式转换
        need_convert = img.format is None or img.format.lower() != 'jpeg'
        # 判断是否需要压缩
        need_compress = quality < 100

        # 只要有一项需要处理，就生成临时文件
        if need_resize or need_convert or need_compress:
            # 统一转换为RGB，防止PNG等带透明通道报错
            img = img.convert('RGB')
            if need_resize:
                new_size = (int(w * scale), int(h * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                # aklog_debug(f"图片已缩放到{new_size}")
            # 生成临时文件名，防止重复
            temp_file = os.path.splitext(image_file)[0] + f".{quality}_ocr_tmp.jpg"
            img.save(temp_file, format='JPEG', quality=quality)
            # aklog_debug(f"图片已保存为JPG格式，路径: {temp_file}，压缩质量: {quality}")
            return temp_file
        else:
            # aklog_debug("图片无需缩放、格式转换或压缩，直接返回原图路径")
            return image_file
    except Exception as e:
        aklog_error(f"图片预处理失败: {e}")
        return image_file


def image_paddleocr_to_text(image_file, preprocess=True) -> list:
    """图片识别，精准度比较高"""
    aklog_printf()
    try:
        if preprocess:
            image_file = preprocess_image(image_file, max_width=1280)

        global paddleocr_instance
        if paddleocr_instance is None:
            from paddlex import create_pipeline
            from paddlex.utils.logging import setup_logging

            setup_logging('WARNING')
            pipe_file = root_path + '\\testcase\\utils\\.paddlex\\OCR.yaml'
            paddleocr_instance = create_pipeline(pipeline=pipe_file)

        output = paddleocr_instance.predict(
            input=image_file,
            use_doc_orientation_classify=False,  # 是否启用文档方向分类（自动判断图片是否需要旋转90/180/270度）
            use_doc_unwarping=False,  # 是否启用文档去畸变（自动拉正拍摄时产生的弯曲、透视变形）
            use_textline_orientation=False,  # 是否启用文本行方向检测（判断每一行文字的方向，适用于多方向文本）
        )
        texts = []
        for res in output:
            texts = res.json.get('res').get('rec_texts')
            break
        aklog_printf('paddleocr texts: %s' % texts)
        return texts
    except:
        aklog_printf(traceback.format_exc())
        return []
    finally:
        # 用完后可删除临时文件
        if image_file.endswith("ocr_tmp.jpg"):
            os.remove(image_file)


def batch_image_paddleocr_to_texts(image_list, max_workers=4):
    """多进程批量识别图片，但CPU性能不足，识别一个就已经CPU100%了，多个同时并不会提升速度"""
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(image_paddleocr_to_text, image_list))
    return results


def image_wechat_ocr_to_texts(image_file) -> list:
    """使用微信OCR识别文本"""
    aklog_printf()
    texts = wechat_ocr(image_file)
    aklog_debug(f'texts: {texts}')
    return texts


def image_ocr_to_texts(image_file, preprocess=True, ocr_type=None) -> list:
    """OCR识别统一接口"""
    if ocr_type == 'paddleocr':
        return image_paddleocr_to_text(image_file, preprocess)
    else:
        return image_wechat_ocr_to_texts(image_file)


def image_2_base64(image_path):
    """
    将图片转成base64，会先转成png格式，再转成base64，可以用于HTML测试报告截图
    比如：param_append_screenshots_imgs(image_2_base64(image_path))
    """
    aklog_printf()
    try:
        ext = os.path.splitext(image_path)[1]
        if ext != '.png':
            outfile = image_path.replace(ext, '.png')
            if os.path.exists(outfile):
                os.remove(outfile)
            im = cv2.imread(image_path)
            cv2.imwrite(outfile, im)
        else:
            outfile = image_path
        with open(outfile, 'rb') as file:
            data = file.read()
        base64_data = base64.b64encode(data).decode()
        if outfile != image_path and os.path.exists(outfile):
            os.remove(outfile)
        return base64_data
    except:
        aklog_printf(traceback.format_exc())
        return None


def image_append_screenshots_imgs():
    """
    将图片转成base64，并添加到param_append_screenshots_imgs，作为HTML测试报告的截图
    需要配合 param_put_temp_images() 使用
    """
    images = param_get_temp_images()
    for image in images:
        base64_data = image_2_base64(image)
        if base64_data:
            param_append_screenshots_imgs(base64_data)
    param_put_temp_images()


def fix_rgb_error_range(color_int, error_range=50):
    if error_range == 0:
        return color_int
    return int(color_int / error_range) * error_range


def judge_no_pure_with_error_range(png, percent=50, rgb_error_range=20):
    """
    percent: 超过50%, 认为是纯色. rgb_error_range: RGB值的误差范围, 需要比较恰当的值. 超过40基本就不准确了.
    1. 对于纯黑的, 可达到99%.
    2. 对于通话的黑暗环境下的黑屏, 只有50+%,
    3. 对于live stream 的网页截图, 考虑到网页背景, 也只有60%
    """
    retdict = {}
    percent_dict = {}
    image = Image.open(png)
    pixels = image.load()
    width, height = image.size

    for x in range(width):
        for y in range(height):
            if len(pixels[x, y]) == 4:
                rgb = pixels[x, y][:3]
            else:
                rgb = pixels[x, y]
            red, green, blue = rgb
            red = fix_rgb_error_range(red, rgb_error_range)
            green = fix_rgb_error_range(green, rgb_error_range)
            blue = fix_rgb_error_range(blue, rgb_error_range)
            if (red, green, blue) not in retdict:
                retdict[(red, green, blue)] = 1
            else:
                retdict[(red, green, blue)] += 1
    totol_count = sum(list(retdict.values()))
    for rgb, each_count in retdict.items():
        percent_dict[rgb] = round(each_count / totol_count, 4)
        if each_count / totol_count > (percent / 100):
            aklog_error(
                'RGB: {} 颜色占比过多. {}% > {}%'.format(rgb, round(each_count * 100 / totol_count, 2), percent))
            return False

    max_percent = max(list(percent_dict.values())) * 100
    max_percent = str(max_percent)
    max_percent = max_percent[:5] if len(max_percent) > 5 else max_percent
    aklog_info('RGB 占比最大值: {}%'.format(max_percent))
    return True


def extract_similar_region(big_image_path, small_image_path, output_path, threshold=0.8):
    """图像模板匹配，从大图中找到跟小图匹配相似的区域，并抠图保存"""
    # 读取大图和小图
    big_img = cv2.imread(big_image_path)
    small_img = cv2.imread(small_image_path)

    if big_img is None or small_img is None:
        raise FileNotFoundError("图片路径错误或图片无法读取")

    # 转为灰度图（提高匹配效率）
    big_gray = cv2.cvtColor(big_img, cv2.COLOR_BGR2GRAY)
    small_gray = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)

    # 模板匹配
    result = cv2.matchTemplate(big_gray, small_gray, cv2.TM_CCOEFF_NORMED)

    # 获取最大匹配值及其位置
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    print(f"最大匹配度：{max_val:.4f}，位置：{max_loc}")

    if max_val < threshold:
        raise ValueError(f"匹配度过低（{max_val:.4f}），未找到相似区域")

    # 获取小图尺寸
    h, w = small_img.shape[:2]

    # 计算匹配区域的左上角和右下角坐标
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)

    # 从大图中裁剪该区域
    matched_region = big_img[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]

    # 保存抠图结果
    cv2.imwrite(output_path, matched_region)
    print(f"相似区域已保存为：{output_path}")


def intercom_compare_two_picture(image1, image2, percent=90, fx=None, fy=None, tx=None, ty=None, error_range=0):
    """
    2025.5.21. lex: 两张图片对比.
        image1: 只能是一张图片.
        image2: 一张图片或者多张图片.
        percent: 90/0.9 都代表90%的相似度.
        fx, fy, tx, ty: 有填写的情况下, 只对图片的部分内容进行对比.
    """
    def compare(image1, image2):
        if not os.path.exists(image1):
            aklog_error('图片对比失败!, 不存在图片: {}'.format(image1))
            return None
        if not os.path.exists(image2):
            aklog_error('图片对比失败!, 不存在图片: {}'.format(image2))
            return None
        diff_count = 0
        same_count = 0
        img1 = Image.open(image1)
        img2 = Image.open(image2)
        width1, height1 = img1.size
        width2, height2 = img2.size
        min_width = min(width1, width2)
        min_height = min(height1, height2)
        img1 = img1.resize((min_width, min_height))
        img2 = img2.resize((min_width, min_height))
        for x in range(img1.width):
            for y in range(img1.height):
                pixel1 = img1.getpixel((x, y))
                pixel2 = img2.getpixel((x, y))
                if math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(pixel1, pixel2))) <= error_range:
                    same_count += 1
                else:
                    diff_count += 1

        similarity_ratio = (same_count / (same_count + diff_count)) * 100
        # 设备端的图片, 用于错误时去提取图片
        img1.save(r'C:\\11.png')

        aklog_debug('图片相似度: {:.2f}%'.format(similarity_ratio))
        if percent > 1:
            return similarity_ratio >= percent
        else:
            return similarity_ratio >= percent * 100

    if isinstance(image2, str):
        if fx is not None or fy is not None or tx is not None or ty is not None:
            crop_image(image1, r'C:\\aft2.png', fx, fy, tx, ty)
            crop_image(image2, r'C:\\aft.png', fx, fy, tx, ty)
            return compare(r'C:\\aft.png', r'C:\\aft2.png')
        else:
            return compare(image1, image2)
    else:
        for i in image2:
            if fx is not None or fy is not None or tx is not None or ty is not None:
                crop_image(i, r'C:\\aft.png', fx, fy, tx, ty)
                crop_image(image1, r'C:\\aft2.png', fx, fy, tx, ty)
                ret = compare(r'C:\\aft.png', r'C:\\aft2.png')
            else:
                ret = compare(image1, i)
            if ret:
                return True
        return False


def crop_image(imgfile, outfile, fx, fy, tx, ty):
    """
    2025.5.21 lex: 根据坐标截取图片
    """
    with Image.open(imgfile) as img:
        # 使用crop()方法裁剪图片，参数是一个四元组(左, 上, 右, 下)
        # 注意：这里的右和下坐标是裁剪区域之外的边界
        cropped_img = img.crop((fx, fy, tx, ty))
        # 保存裁剪后的图片
        cropped_img.save(outfile)


def extract_alpha_with_spaces(text: str) -> str:
    """提取第一段连续的字母，可包含空格"""
    match = re.search(r'[A-Za-z]+(?: [A-Za-z]+)*', text)
    return match.group(0).strip() if match else ''


def find_and_extract_ocr_data(
        texts: List[str],
        keywords: Union[str, List[str]],
        threshold: int = 80,
) -> List[Dict[str, Union[str, float]]]:
    """从OCR文本中查找匹配关键字的片段，并提取数值与单位

    Args:
        texts (list[str]): OCR识别的文本片段列表
        keywords (str | list[str]): 目标关键字（支持多个相似关键字）
        threshold (int): 模糊匹配相似度阈值（0-100）

    Returns:
        list[dict] | dict | None:
            匹配结果包含：
            {
                "raw_text": str,       # 原片段
                "matched_keyword": str,# 匹配到的关键字
                "similarity": float, # 相似度
                "value": float | None, # 提取到的数字
            }
    """
    if not texts:
        aklog_warn("OCR识别文本为空")
        return []

    if isinstance(keywords, str):
        keywords = [keywords]

    results = []
    for raw_text in texts:
        if not raw_text.strip():
            continue

        alpha_part = extract_alpha_with_spaces(raw_text)
        for target_word in keywords:
            similarity = fuzz.ratio(target_word.lower(), alpha_part.lower())
            if similarity >= threshold:
                numbers = re.findall(r'\d+(?:\.\d+)?', raw_text)  # 获取数字/小数

                result = {
                    "raw_text": raw_text.strip(),
                    "matched_keyword": target_word,
                    "similarity": similarity,
                    "value": float(numbers[0]) if numbers else None,
                }
                results.append(result)
                break  # 避免同片段被多个关键字重复匹配

    if results:
        aklog_debug(f"匹配成功，结果: {results}")
    else:
        aklog_warn('匹配失败')
    return results


def check_ocr_keyword_absence(
        texts: List[str],
        keywords: Union[str, List[str]],
        threshold: int = 80,
) -> List[Dict[str, Union[str, float]]]:
    """检查OCR文本中是否不存在指定关键字

    Args:
        texts (list[str]): OCR识别的文本片段列表
        keywords (str | list[str]): 待检测关键字（支持多个）
        threshold (int): 模糊匹配相似度阈值（0-100）

    Returns:
        bool | list:
    """
    if not texts:
        aklog_debug("OCR识别文本为空，视为不存在关键字")
        return []

    if isinstance(keywords, str):
        keywords = [keywords]

    matched_results = []
    for raw_text in texts:
        if not raw_text.strip():
            continue

        alpha_part = extract_alpha_with_spaces(raw_text)
        for target_word in keywords:
            similarity = fuzz.ratio(target_word.lower(), alpha_part.lower())

            if similarity >= threshold:
                match_info = {
                    "raw_text": raw_text.strip(),
                    "matched_keyword": target_word,
                    "similarity": similarity
                }
                matched_results.append(match_info)
                break  # 避免同片段重复匹配

    if matched_results:
        aklog_warn(f"[OCR检查] 发现关键字: {matched_results}")
    else:
        aklog_debug("[OCR检查] 未发现匹配关键字，检查通过")
    return matched_results


# endregion


# region 视频文件检查

def check_record_video(record_file):
    """
    检查录制的视频是否正常
    待实现
    Args:
        record_file ():
    """
    aklog_debug('待实现!!!')


# endregion


if __name__ == '__main__':
    print('debug')
    find_and_extract_ocr_data(['curent:32.4℃', 'd'], 'Current')
