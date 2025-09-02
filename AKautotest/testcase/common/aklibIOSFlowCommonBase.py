from akcommon_define import *
from testcase.common.aklibIOSBaseU2 import IOSBaseU2
import itertools


class IOSFlowCommonBase(object):

    def __init__(self):
        self.device_name = ''
        self.page_switch = None
        self.app: Optional[IOSBaseU2] = None

    def init(self, page_obj_list: dict, page_switch_cb):
        aklog_debug(f'{self.__class__.__name__} init')
        self.page_init(page_obj_list)
        self.device_name = getattr(self.app, 'device_name', '')
        self.page_switch = page_switch_cb

    def page_init(self, page_obj_list: dict):
        for attr in self.__dict__:
            if not attr.endswith("_page"):
                continue
            if getattr(self, attr, None) is not None:
                continue
            if attr not in page_obj_list:
                aklog_warn(f'页面 {attr} 不在page_obj_list里面，可能当前Flow声明的Page名称没有跟base模块统一')
            setattr(self, attr, page_obj_list[attr])
            if self.app is None:
                self.app = getattr(page_obj_list[attr], 'app', None)

    def screen_shot(self):
        self.app.screen_shot()

    def get_translations(self, key, default=None, add_warn=False):
        """
        获取翻译词条
        Args:
            key (str): 原始词条名称
            default (str): 如果为空，则默认使用英语词条
            add_warn (bool): 是否添加警告
        """
        try:
            cur_lang = self.app.get_device_language(regain=False)
            translations = self.app.get_translations()
            value = None
            if translations:
                value = translations.get(key)
            if value:
                return value
            if default:
                if add_warn:
                    unittest_results(
                        ['warn', f'当前语言 {cur_lang} 缺少词条key: {key}, 使用默认翻译: {default}'])
                return default

            en_translations = self.app.get_translations('en')
            if en_translations:
                value = en_translations.get(key)
            if value:
                if add_warn:
                    unittest_results(
                        ['warn', f'当前语言 {cur_lang} 缺少词条key: {key}, 使用英文词条翻译: {value}'])
                return value

            # 如果仍为空，则将key作为英语词条，反向查找原始词条
            matching_keys = [k for k, v in en_translations.items() if v == key]  # 获取所有匹配的 key

            # 创建循环迭代器
            key_iterator = itertools.cycle(matching_keys) if matching_keys else None

            # 获取下一个 key
            if key_iterator:
                for i in range(len(matching_keys)):
                    key1 = next(key_iterator)
                    if translations:
                        value = translations.get(key1)
                    if value:
                        if add_warn:
                            unittest_results(
                                ['warn',
                                 f'当前语言 {cur_lang} 缺少词条key: {key}, 将key作为英语词条反向查找翻译: {value}'])
                        return value
            if add_warn:
                unittest_results(
                    ['warn', f'当前语言 {cur_lang} 缺少词条key: {key}, 直接将key作为英语词条翻译: {key}'])
            return key
        except Exception as e:
            unittest_results([False, f'获取词条 {key} 失败: {e}'])
            return None

    @property
    def user_info(self) -> dict:
        return self.app.get_user_info()

    @user_info.setter
    def user_info(self, value):
        if self.app and hasattr(self.app, 'put_user_info'):
            self.app.put_user_info(value)
