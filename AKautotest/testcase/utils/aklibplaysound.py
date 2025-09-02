# -*- coding: UTF-8 -*-

import os
import sys

root_path = os.getcwd()
pos = root_path.find("AKautotest")
if pos == -1:
    print("runtime error")
    exit(1)
root_path = root_path[0:pos + len("AKautotest")]
sys.path.append(root_path)

from akcommon_define import *
from playsound3 import playsound
from gtts import gTTS

hypanel_audio_path = '%s\\testfile\\audio_automation\\HyPanel' % root_path


# intercom_audio_path = '%s\\testfile\\audio_automation\\Akuvox' % (root_path)  #以后对讲可能也会用到，预留路径

def sound_play(audio_type, Interval, command, delay=15):
    """
        audio_type(语音类型):siri,google,alexa
        Interval(播放间隔):1,2,3,4,5
        command：命令
    """
    aklog_info(r'语音路径：%s\%s.mp3' % (hypanel_audio_path, audio_type))
    playsound('%s/%s.mp3' % (hypanel_audio_path, audio_type))
    time.sleep(Interval)
    aklog_info(r'语音路径：%s\%s.mp3' % (hypanel_audio_path, command))
    playsound('%s/%s.mp3' % (hypanel_audio_path, command))
    time.sleep(delay)


def play_command(command, delay=15):
    """
        command：命令
    """
    aklog_info(r'语音路径：%s\%s.mp3' % (hypanel_audio_path, command))
    playsound(r'%s\%s.mp3' % (hypanel_audio_path, command))
    time.sleep(delay)


def text_to_mp3(text, lang, output_file):
    tts = gTTS(text=text, lang=lang)
    tts.save(output_file)
    print(f"文件已保存为: {output_file}")


if __name__ == "__main__":
    text_list = [
        "set dimmer brightness to 10",
        "set heating to 20 centigrade",
        "turn on thermostat",
        "set thermostat to 20 centigrade",
        "set thermostat to cool",
        "turn on Yeelight Blue Color",
        "set Yeelight Blue Color brightness to 1",
        "turn on zigbee Thermostat",
        "Set zigbee Thermostat to heat",
        "Set zigbee Thermostat to 20 centigrade",
        "Set zigbee Thermostat to 20 degrees",
        "set yeelight blue color to cool white",
        "set yeelight blue color to red",
        "set heating to 20 degrees",
    ]  # 你想转换的文本集合
    language = 'en'  # 语言代码，'zh'代表中文

    # 遍历集合并生成相应的语音文件
    for my_text in text_list:
        output_filename = "%s.mp3" % my_text  # 输出的MP3文件名，替换空格为下划线
        full_output_path = os.path.join(hypanel_audio_path, output_filename)
        text_to_mp3(my_text, language, full_output_path)