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
import requests
from WorkWeixinRobot.work_weixin_robot import WWXRobot
import time

report_today = False


def robot_get_receivers_id(robot_id_list: list, *receivers):
    robot_info = param_get_robot_info()
    if not robot_info:
        config_file = os.path.join(g_config_path, g_robot_info_file)
        readconfig = ReadConfig(config_file)
        robot_info = readconfig.get_dict('robot_info')
        param_put_robot_info(robot_info)

    unknown_robot_text = ''
    for receiver in receivers:
        if receiver in robot_info:
            receiver = receiver.lower()
            robot_id = robot_info[receiver]
        else:
            unknown_robot_text += "\n(未知robot: %s)" % receiver
            robot_id = robot_info['default']
        if robot_id not in robot_id_list:
            robot_id_list.append(robot_id)
    return unknown_robot_text


def robot_send_text_msg(text, *receivers):
    """
    发送消息给企业微信
    添加机器人步骤：任意拉两个人建立一个群聊，然后踢掉，这样就可以保存一个只有一个人的群聊，之后添加机器人
    将获取到的webhook连接中的key值，添加到机器人信息字典里
    """
    aklog_printf()
    robot_id_list = []
    unknown_robot_text = robot_get_receivers_id(robot_id_list, *receivers)
    text += unknown_robot_text
    try:
        for robot_id in robot_id_list:
            robot = WWXRobot(robot_id)
            robot.send_text(text)
        return True
    except:
        aklog_printf('发送失败')
        aklog_printf(traceback.format_exc())
        return False


def robot_send_image(image_path, *receivers):
    """
    发送消息给企业微信
    添加机器人步骤：任意拉两个人建立一个群聊，然后踢掉，这样就可以保存一个只有一个人的群聊，之后添加机器人
    将获取到的webhook连接中的key值，添加到机器人信息字典里
    """
    aklog_printf()
    robot_id_list = []
    robot_get_receivers_id(robot_id_list, *receivers)
    try:
        for robot_id in robot_id_list:
            robot = WWXRobot(robot_id)
            robot.sender('image', msg_file_path=image_path)
        return True
    except:
        aklog_printf('发送失败')
        aklog_printf(traceback.format_exc())
        return False


def robot_send_file(file_path, *receivers):
    """发送文件给企业微信，file_path是指文件路径"""
    aklog_printf()
    robot_id_list = []
    robot_get_receivers_id(robot_id_list, *receivers)
    try:
        for robot_id in robot_id_list:
            file_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key=%s&type=file" % robot_id
            file = {'file': open(file_path, 'rb')}
            result = requests.post(file_url, files=file)
            # json_res = result.json()
            # aklog_printf("json_res:%s" % json_res)
            file_id = eval(result.text)['media_id']
            url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=" + robot_id
            data = {
                "msgtype": "file",
                "file": {"media_id": file_id, }
            }
            r = requests.post(url, json=data)
            aklog_printf(r.text)
        return True
    except:
        aklog_printf('发送失败')
        aklog_printf(traceback.format_exc())
        return False


def robot_send_to_door_halfat(msg):
    """
    门口机半自动化使用.
    """
    robot_send_text_msg(msg, 'door_semi_automation')


def report_every_day(result, *receiver):
    """
    2024.7.11 lex: 30天压测日报
    """
    global report_today
    result = ' - 压测日报 - \n' + str(result)
    if not report_today and ('09:35:00' > time.strftime('%H:%M:%S') > '09:30:00'):
        report_today = True
        robot_send_text_msg(result, *receiver)
    else:
        if time.strftime('%H:%M:%S') > '09:35:00':
            report_today = False


if __name__ == '__main__':
    robot_send_image(r'D:\Users\Administrator\Desktop\Report.png', 'jason@akuvox.com')
    # robot_send_file(r'D:\Users\Administrator\Desktop\Result.txt', 'jason@akuvox.com')
