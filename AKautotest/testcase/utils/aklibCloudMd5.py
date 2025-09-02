# -- coding: utf-8 --
# @Comment: 此文件涉及到一些加密信息，禁止外传！！

import hashlib
import string
import base64
from Crypto.Cipher import AES


def md5(string):
    m = hashlib.md5()
    m.update(string.encode("utf8"))
    return m.hexdigest()


def md5GBK(str1):
    m = hashlib.md5(str1.encode(encoding='gb2312'))
    # print(m.hexdigest())
    return m.hexdigest()


def kaisa(s, k=3):  # 定义函数 接受一个字符串s 和 一个偏移量k
    """app 用户名加密算法，凯撒加密改造，数字也做偏移"""
    lower = string.ascii_lowercase  # 小写字母
    upper = string.ascii_uppercase  # 大写字母
    before = string.ascii_letters + '0123456789'  # 无偏移的字母顺序 小写+大写
    after = lower[k:] + lower[:k] + upper[k:] + upper[:k] + '3456789012'  # 偏移后的字母顺序 还是小写+大写
    # 分别把小写字母和大写字母偏移后再加到一起
    table = ''.maketrans(before, after)  # 创建映射表
    return s.translate(table)  # 对s进行偏移 即加密


def md5_2(string):
    """app密码加密采用2次md5加密"""
    str1 = md5(string)
    str2 = md5(str1)
    return str2


def base64_encode(input_str):
    """ output:b'aGVsbG93b3JsZA==' """
    bytes_str = input_str.encode("utf-8")  # 变为二进制
    out_str = base64.b64encode(bytes_str)
    return out_str


def base64_decode(input_str):
    """ input:'aGVsbG93b3JsZA==' """
    bytes_str = input_str.encode("utf-8")  # 变为二进制
    out_str = base64.b64decode(bytes_str)
    return out_str


class AkAescrypt:
    """平台AES256加密/解密"""

    def __init__(self, user, model=AES.MODE_CBC, iv=b'1234567887654321'):
        """
        :param user: app为Email，设备为MAC
        :param model:
        :param iv:
        """
        key = md5(user)[0:16] + 'Akuvox55069013!@'
        self.key = self.add_16(key)
        self.model = model
        self.iv = iv
        self.aes = None
        self.encrypt_text = None
        self.decrypt_text = None

    @staticmethod
    def add_16(par):
        if type(par) == str:
            par = par.encode()
        while len(par) % 16 != 0:
            par += b'\x00'
        return par

    def aesencrypt(self, text):
        """AES256加密"""
        text = self.add_16(text)
        if self.model == AES.MODE_CBC:
            self.aes = AES.new(self.key, self.model, self.iv)
        elif self.model == AES.MODE_ECB:
            self.aes = AES.new(self.key, self.model)
        self.encrypt_text = self.aes.encrypt(text)
        return self.encrypt_text

    def aesdecrypt(self, text):
        """AES256解密"""
        if self.model == AES.MODE_CBC:
            self.aes = AES.new(self.key, self.model, self.iv)
        elif self.model == AES.MODE_ECB:
            self.aes = AES.new(self.key, self.model)
        self.decrypt_text = self.aes.decrypt(text).strip(b"\x00")
        return self.decrypt_text


if __name__ == '__main__':
    passwd = 'zhihais02@163.com'
    iv = b'1234567812345678'

    # aescryptor = Aescrypt(passwd) # CBC模式
    # text = "helloworld"
    # en_text = aescryptor.aesencrypt(text)
    # print("密文:",en_text)
    # text = aescryptor.aesdecrypt(en_text)
    # print("明文:",text)
    tx = 'helloworld'
    # tx1=base64.b64decode(tx)
    # print(tx1)
    tx1 = base64_encode(tx)
    print(tx1)
    # tx2=base64_decode('aGVsbG93b3JsZA==')
    # print(tx2)
