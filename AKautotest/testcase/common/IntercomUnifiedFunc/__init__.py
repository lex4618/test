__all__ = ['get_base_object', 'get_web_object']

from .aklibIntercomCommonFuncName import commonBaseName, commonWebName


class Web(commonWebName):
    """
    PS: lex维护, 其他人勿动
    """

    def __init__(self, Obj):
        self.__Obj = Obj
        self.__appendMethod()

    def __appendMethod(self):
        for i in dir(self.__Obj):
            self.__dict__.setdefault(i, getattr(self.__Obj, i))


class Base(commonBaseName):
    """
    PS: lex维护, 其他人勿动
    """

    def __init__(self, Obj):
        self.__Obj = Obj
        self.__appendMethod()

    def __appendMethod(self):
        for i in dir(self.__Obj):
            self.__dict__.setdefault(i, getattr(self.__Obj, i))


from .aklibDeviceWebName import *


def get_web_object(webObj):
    """
    PS: lex维护, 其他人勿动
    """
    webObj = str(webObj).lower()
    if 'linuxdoor' in webObj:
        return WebLinuxDoor(webObj)
    elif 'linuxindoor' in webObj:
        return WebLinuxInDoor(webObj)
    # elif 'androiddoor' in webObj:
    #     self.androiddoor = True
    # elif 'accessdoor' in webObj:
    #     self.accessdoor = True
    # elif 'accesscontrol' in webObj:
    #     self.accesscontrol = True

    # elif 'androidindoor' in webObj:
    #     self.androidindoor = True
    # elif 'androidindoorv6' in webObj:
    #     self.androidindoorv6 = True
    # elif 'guardphone' in webObj:
    #     self.guardphone = True


def get_base_object(baseObj):
    """
    PS: lex维护, 其他人勿动
    """
    baseObj = str(baseObj).lower()
    if 'linuxdoor' in baseObj:
        return BaseLinuxDoor(baseObj)
    elif 'linuxindoor' in baseObj:
        return WebLinuxInDoor(baseObj)
    # elif 'androiddoor' in webObj:
    #     self.androiddoor = True
    # elif 'accessdoor' in webObj:
    #     self.accessdoor = True
    # elif 'accesscontrol' in webObj:
    #     self.accesscontrol = True

    # elif 'androidindoor' in webObj:
    #     self.androidindoor = True
    # elif 'androidindoorv6' in webObj:
    #     self.androidindoorv6 = True
    # elif 'guardphone' in webObj:
    #     self.guardphone = True
