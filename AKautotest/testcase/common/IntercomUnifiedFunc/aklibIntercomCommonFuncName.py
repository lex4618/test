"""
2024.6.13 Lex
统一对讲终端: 门口机, 室内机, 门禁 功能性一样的业务接口命名,  统一命名方便统一维护.
本页面接口用于统一命名 和 查询.
"""


class commonWebName:
    """
    2024.6.13 Lex
    统一一下网页接口名, 这里只是作为提示,查询用.
    PS: lex维护, 其他人勿动
    """

    def web_enter_call_feature(self):
        raise AttributeError('未定义接口')

    def web_enter_test(self):
        raise AttributeError('未定义接口')


class commonBaseName:
    """
    2024.6.13 Lex
    统一一下设备接口名, 这里只是作为提示,查询用.
    PS: lex维护, 其他人勿动
    """

    def callout(self, number):
        raise AttributeError('未定义接口')

    @property
    def ip(self):
        return self.device_info['ip']

    @property
    def mac(self):
        return self.device_info['mac']
