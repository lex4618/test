class Trans:
    def EightHN_8H10D(self, num):
        # 8HN => 8H10D
        # 16进制转10进制, 不组10位补0
        return str(int('0x' + num, 16)).rjust(10, '0')

    def EightHN_6H3D5D(self, num):
        # 8HN => 6H3D5D
        ten = self.EightHN_8H10D(num)
        ret = self.EightH10D_6H3D5D(ten)
        return ret

    def EightHN_6H8D(self, num):
        dec = self.EightHN_8H10D(num)
        ret = int(int(dec) % 16777216)
        return str(ret).rjust(8, '0')

    def EightHN_8HR(self, num):
        # 8HN -> 8HR
        # 倒序, 每两位
        num = str(num)
        ret = num[-2:] + num[-4:-2] + num[-6:-4] + num[-8:-6]
        return ret

    def EightHN_6H3D5DR(self, num):
        # 8HN => 6H3D5DR
        Rev = self.EightHN_8HR(num)
        ten = self.EightHN_8H10D(Rev)
        ret = self.EightH10D_6H3D5D(ten)
        return ret

    def EightH10D_6H3D5D(self, num):
        # 8H10 => 6H3D5D
        # 前三位:  num/65536%256
        # 后五位:  num%65536
        pre = int(int(num) / 65536 % 256)
        pre = str(pre).rjust(3, '0')
        suffix = str(int(int(num) % 65536)).rjust(5, '0')
        return pre + suffix

    def EightHN_8HR10D(self, num):
        rev = self.EightHN_8HR(num)
        ret = self.EightHN_8H10D(rev)
        return ret


class ic_trans_to_wiegand26:
    """
    IC card 转换成wiegand 26.
    1. 取右边3个字节. 左边补0
    """

    def local_to_input(self, num):
        """取3个8位, 左边补00"""
        return '00' + num[2:]

    def local_to_input_reverse(self, num):
        """左边补00,  取原来右边6个数字, 取两两反序"""
        return '00' + num[-2:] + num[-4:-2] + num[-6:-4]

    def local_to_output(self, num):
        """IC card: wiegand 26输出, 返回正序反序两个. """
        # 正序. 左边补00, 右边6个数字正序输出
        ordered = '00' + num[2:]

        # 反序. 左边补00, 右边6个数字, 取两两反序.
        reversed = '00' + num[-2:] + num[-4:-2] + num[-6:-4]
        return ordered, reversed


class ic_trans_to_wiegand34:
    """
    IC card 转换成wiegand 34.
    1. 取4个字节. 左边补0
    """

    def local_to_input(self, num):
        """取4个8位"""
        return num

    def local_to_input_reverse(self, num):
        """左边补00,  取原来右边6个数字, 取两两反序"""
        return num[-2:] + num[-4:-2] + num[-6:-4] + num[-8:-6]

    def local_to_output(self, num):
        """IC card: wiegand 26输出, 返回正序反序两个. """
        # 正序. 左边补00, 右边6个数字正序输出
        ordered = num

        # 反序. 左边补00, 右边6个数字, 取两两反序.
        reversed = num[-2:] + num[-4:-2] + num[-6:-4] + num[-8:-6]
        return ordered, reversed


class id_trans_to_wiegand26:
    """
    ID card 转换成wiegand 26.
    1. 取右边3个字节. 左边补00
    """

    def local_to_input(self, num):
        """取3个8位, 左边补00"""
        return '00' + num[2:]

    def local_to_input_reverse(self, num):
        """左边补00,  取原来右边6个数字, 取两两反序"""
        return '00' + num[-2:] + num[-4:-2] + num[-6:-4]

    def local_to_output(self, num):
        """IC card: wiegand 26输出, 返回正序反序两个. """
        # 正序. 左边补00, 右边6个数字正序输出
        ordered = '00' + num[2:]

        # 反序. 左边补00, 右边6个数字, 取两两反序.
        reversed = '00' + num[-2:] + num[-4:-2] + num[-6:-4]
        return ordered, reversed


class id_trans_to_wiegand34:
    """
    ID card 转换成wiegand 34.
    1. 取4个字节. 左边补0
    """

    def local_to_input(self, num):
        # 915是错的. """取3个8位, 右边补FF""" . 但不改, 会影响以前的刷卡.
        # R20是对的,  先取直接读
        # return num[2:] + 'FF'
        return num

    def local_to_input_reverse(self, num):
        # 915 是错的 """左边补FF,  取原来右边6个数字, 取两两反序"""
        # R20是对的, 直接取反.
        # return 'FF' + num[-2:] + num[-4:-2] + num[-6:-4]
        return num[-2:] + num[-4:-2] + num[-6:-4] + num[-8:-6]

    def local_to_output(self, num):
        """IC card: wiegand 26输出, 返回正序反序两个. """
        # 正序. 左边补00, 右边6个数字正序输出
        # 915错的.
        # ordered = '00' + num[2:]
        #
        # # 反序. 左边补00, 右边6个数字, 取两两反序.
        # reversed = '00' + num[-2:] + num[-4:-2] + num[-6:-4]
        # return ordered, reversed
        return num, num[-2:] + num[-4:-2] + num[-6:-4] + num[-8:-6]


class ic_trans_to_wiegand58:

    def local_to_normal(self, num):
        if len(num) == 8:
            return '000000' + num
        elif len(num) == 14:
            return num


    def local_to_reverse(self, num):
        if len(num) == 8:
            return num[-2:] + num[-4:-2] + num[-6:-4] + num[-8:-6] + '000000'
        elif len(num) == 14:
            return num[-2:] + num[-4:-2] + num[-6:-4] + num[-8:-6] + num[4:6] + num[2:4] + num[:2]


class id_trans_to_wiegand58:

    def local_to_normal(self, num):
        if len(num) == 8:
            return '000000' + num
        elif len(num) == 14:
            return num

    def local_to_reverse(self, num):
        if len(num) == 8:
            return num[-2:] + num[-4:-2] + num[-6:-4] + num[-8:-6] + '000000'
        elif len(num) == 14:
            return num[-2:] + num[-4:-2] + num[-6:-4] + num[-8:-6] + num[4:6] + num[2:4] + num[:2]
