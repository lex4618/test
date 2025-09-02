# -*- coding: utf-8 -*-

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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.header import Header
from email.mime.application import MIMEApplication
import email.mime.multipart
import email.mime.text
import traceback
import smtplib
from testcase.common.aklibApiRequests import ApiRequests
from imap_tools import MailBoxUnencrypted, AND
import time
import datetime
import re


def sendEmail(receivers, title, content):
    # receivers支持list
    device_config = param_get_device_config()
    # device_config=config_NORMAL()
    mailUser = device_config.GetEmailUserName()
    mailPwd = device_config.GetEmailPassword()

    message = MIMEText(content, 'plain', 'utf-8')
    message['Subject'] = Header(title, 'utf-8')
    message['From'] = 'AutoTestReport<%s>' % mailUser
    message['To'] = ", ".join(receivers)

    try:
        smtpObj = smtplib.SMTP_SSL(device_config.GetEmailHost(), device_config.GetEmailHostPort())
        smtpObj.login(mailUser, mailPwd)
        smtpObj.sendmail(mailUser, receivers, message.as_string())
        smtpObj.quit()
    except Exception:
        aklog_printf("无法发送邮件, 异常为: " + str(traceback.format_exc()), 2)
        result = False
    else:
        aklog_printf("邮件发送成功, 目标为: " + str(receivers), 2)
        result = True

    return result


def sendEmailWithFiles(receivers, files, title, content):
    # receivers和files都支持list
    device_config = param_get_device_config()
    mailUser = device_config.GetEmailUserName()
    mailPwd = device_config.GetEmailPassword()

    message = MIMEMultipart()
    message['Subject'] = Header(title, 'utf-8')
    message['From'] = 'AutoTestReport<%s>' % mailUser
    message['To'] = ", ".join(receivers)

    # 正文
    message.attach(MIMEText(content, 'plain', 'utf-8'))

    for attName in files:
        att = MIMEText(open(attName, 'rb').read().decode(encoding='utf-8'), 'base64', 'utf-8')
        # TODO: 这里可以根据文件后缀设置恰当的Content-Type
        att["Content-Type"] = 'application/octet-stream'
        att["Content-Disposition"] = 'attachment; filename="' \
                                     + str(os.path.basename(attName)) + '"'
        message.attach(att)

    try:
        smtpObj = smtplib.SMTP_SSL(device_config.GetEmailHost(), device_config.GetEmailHostPort())
        smtpObj.login(mailUser, mailPwd)
        smtpObj.sendmail(mailUser, receivers, message.as_string())
        smtpObj.quit()
    except Exception:
        aklog_printf("无法发送邮件, 异常为: " + str(traceback.format_exc()), 2)
        result = False
    else:
        aklog_printf("邮件发送成功, 目标为: " + str(receivers) + '; 携带附件为: ' + str(files), 2)
        result = True

    return result


def sendEmailHTMLWithFile(receivers, file, title, content):
    # receivers和files都支持list
    device_config = param_get_device_config()
    mailUser = device_config.GetEmailUserName()
    mailPwd = device_config.GetEmailPassword()

    message = MIMEMultipart()
    message['Subject'] = Header(title, 'utf-8')
    message['From'] = 'AutoTestReport<%s>' % mailUser
    message['To'] = ", ".join(receivers)

    # 正文
    message.attach(MIMEText(content, 'html', 'utf-8'))

    att = MIMEText(open(file, 'rb').read().decode(encoding='utf-8'), 'html', 'utf-8')
    # TODO: 这里可以根据文件后缀设置恰当的Content-Type
    att["Content-Type"] = 'application/octet-stream'
    att["Content-Disposition"] = 'attachment; filename="' \
                                 + str(os.path.basename(file)) + '"'
    message.attach(att)

    try:
        smtpObj = smtplib.SMTP_SSL(device_config.GetEmailHost(), device_config.GetEmailHostPort())
        smtpObj.login(mailUser, mailPwd)
        smtpObj.sendmail(mailUser, receivers, message.as_string())
        smtpObj.quit()
    except Exception:
        aklog_printf("无法发送邮件, 异常为: " + str(traceback.format_exc()), 2)
        result = False
    else:
        aklog_printf("邮件发送成功, 目标为: " + str(receivers) + '; 携带附件为: ' + str(file), 2)
        result = True

    return result


class SendEmailHandler(object):
    """create by zhihais 2019-12-6"""

    def __init__(self, smtp_host='smtp.exmail.qq.com', smtp_port=465,
                 send_addr='tools-reports@akuvox.com', send_addr_pwd='9v9e5YDitptiCwgG',
                 login_user=None):
        self.smtp_host = smtp_host
        self.send_addr = send_addr
        self.send_addr_pwd = send_addr_pwd
        self.smtp_port = smtp_port
        if login_user:
            self.login_user = login_user
        else:
            self.login_user = send_addr
        # self.receiver_addrs=','.join(receiver_addr)
        # print(self.receiver_addrs)

    def smtp_ssl_send(self, receiver_addr, msg):
        aklog_debug(f'send email: {receiver_addr}')
        try:
            smtp_ssl = smtplib.SMTP_SSL(host=self.smtp_host, port=self.smtp_port)
            # smtp_ssl.connect(host=self.smtp_host, port=self.smtp_port)
            smtp_ssl.login(self.login_user, self.send_addr_pwd)
            smtp_ssl.sendmail(self.send_addr, receiver_addr, str(msg))
            smtp_ssl.quit()
            aklog_printf("邮件发送成功, 目标为: " + str(receiver_addr))
            return True
        except:
            aklog_printf("邮件发送失败, 异常为: " + str(traceback.format_exc()), 2)
            return False

    def send_email(self, receiver_addr, subject, content):
        # 邮件列表去重
        receiver_addr_new = list(set(receiver_addr))
        receiver_addr_new.sort(key=receiver_addr.index)
        receiver_addr = receiver_addr_new

        msg = email.mime.multipart.MIMEMultipart()
        msg['from'] = 'AutoTestReport<%s>' % self.send_addr
        msg['to'] = ','.join(receiver_addr)
        msg['subject'] = subject
        content = content
        txt = email.mime.text.MIMEText(content, 'plain', 'utf-8')
        msg.attach(MIMEText(content, 'html', 'utf-8'))
        msg.attach(txt)

        smtp = smtplib.SMTP()
        smtp.connect(self.smtp_host, 25)
        smtp.login(self.send_addr, self.send_addr_pwd)
        smtp.sendmail(self.send_addr, receiver_addr, str(msg))
        print("send email ok")
        smtp.quit()

    def send_email_with_attachment(self, receiver_addr, subject, content, *attachment_path):
        """*attachment_path:以元组的形式传入，可以传多个附件"""
        # 邮件列表去重
        receiver_addr_new = list(set(receiver_addr))
        receiver_addr_new.sort(key=receiver_addr.index)
        receiver_addr = receiver_addr_new

        msg = email.mime.multipart.MIMEMultipart()
        msg['from'] = 'AutoTestReport<%s>' % self.send_addr
        msg['to'] = ','.join(receiver_addr)
        msg['subject'] = subject
        txt = email.mime.text.MIMEText(content, 'plain', 'utf-8')
        msg.attach(txt)

        # 添加附件
        for attach in attachment_path:
            part = MIMEApplication(open(attach, 'rb').read())
            (filepath, file_name) = os.path.split(attach)
            part.add_header('Content-Disposition', 'attachment', filename=file_name)
            msg.attach(part)

        smtp = smtplib.SMTP()
        smtp.connect(self.smtp_host, 25)
        smtp.login(self.send_addr, self.send_addr_pwd)
        smtp.sendmail(self.send_addr, receiver_addr, str(msg))
        print("send email with attachemnt OK")
        smtp.quit()

    def send_email_with_img_attachment(self, receiver_addr, subject, content, *attachment_path):
        """
        :param receiver_addr: list类型
        :param subject: 
        :param content: 支持多行字符串
        :param attachment_path: *attachment_path:以元组的形式传入，可以传多个附件，如果不传入则没有附件
        :return: 
        """""
        # 检查收件人
        if not receiver_addr:
            aklog_error("收件人为空，无法发送邮件")
            return False
        if isinstance(receiver_addr, str):
            receiver_addr = [receiver_addr]  # 转为列表
        elif not isinstance(receiver_addr, list):
            aklog_error(f"收件人类型错误: {type(receiver_addr)}")
            return False
        # 检查每个收件人格式
        receiver_addr_new = []
        for addr in receiver_addr:
            if '@' not in addr:
                aklog_error(f"无效的收件人邮箱: {addr}")
            if addr not in receiver_addr_new:
                receiver_addr_new.append(addr)
        if not receiver_addr_new:
            aklog_error("未找到有效的收件人，无法发送邮件")
            return False
        receiver_addr_new.sort(key=receiver_addr.index)
        receiver_addr = receiver_addr_new

        msg = MIMEMultipart()
        msg['from'] = 'AutoTestReport<%s>' % self.send_addr
        msg['to'] = ','.join(receiver_addr)
        msg['subject'] = subject

        html_content = """"""
        content_list = content.splitlines()
        for content_line in content_list:
            html_content += '<p>%s</p>\n' % content_line

        html_content += '<p></p>\n'

        # 添加附件或图片,图片将直接显示在邮件里，不作为附件
        imgs = []
        attachments = []
        for attach in attachment_path:
            if not attach:
                continue
            file_dir, file_name = os.path.split(attach)
            file_extension = os.path.splitext(file_name)[1]
            file_extension = file_extension.lower()
            if file_extension == '.png' or file_extension == '.jpg':
                imgs.append(attach)
            else:
                attachments.append(attach)

        if imgs:
            img_id_list = []
            for i in range(len(imgs)):
                img_id = 'image' + str(i+1)
                img_name = os.path.basename(imgs[i])
                html_content += '<p>%s : </p>\n' % img_name
                html_content += '<p><img src="cid:%s"></p>\n' % img_id
                img_id_list.append(img_id)

            msg_content = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(msg_content)

            # 读取图片
            for j in range(len(imgs)):
                fp = open(imgs[j], 'rb')
                msg_image = MIMEImage(fp.read())
                fp.close()

                # 定义图片 ID，在 HTML 文本中引用
                msg_image.add_header('Content-ID', '<%s>' % img_id_list[j])
                msg.attach(msg_image)
        else:
            msg_content = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(msg_content)

        # 添加附件
        for attachment in attachments:
            part = MIMEApplication(open(attachment, 'rb').read())
            (filepath, file_name) = os.path.split(attachment)
            part.add_header('Content-Disposition', 'attachment', filename=file_name)
            msg.attach(part)

        return self.smtp_ssl_send(receiver_addr, msg)


# 修改类名，兼容旧的名称
send_email = SendEmailHandler


def get_last_email_content(username, passwd, mail_server, mail_subject=None, start_time=None,
                           mail_content=None, limit=10, start_index=1):
    """
    获取最后一封满足条件的邮件内容，邮箱登录不使用SSL加密
    mail_subject: 匹配邮箱标题，可以传入list类型，多个匹配只要有一个匹配成功即可
    mail_content: 匹配邮件内容，可以传入list类型，多个匹配只要有一个匹配成功即可
    start_time: 从哪个时间开始匹配，过滤掉这个时间之前的邮件，只获取最新的，格式：'%Y-%m-%d %H:%M:%S'
    limit: 查找邮件数量上限
    start_index: 从第几封邮件开始
    """
    aklog_info()
    mail_msg = {}
    try:
        # 先在收件箱里面查找
        with MailBoxUnencrypted(mail_server).login(username, passwd) as mailbox:
            i = 1
            for msg in mailbox.fetch(limit=limit, reverse=True):
                if i < start_index:
                    i += 1
                    continue
                # 先匹配邮箱标题
                subject = msg.subject
                if not subject and mail_subject:
                    continue
                if mail_subject and isinstance(mail_subject, list) and subject:
                    subject_ret = False
                    for x in mail_subject:
                        if x in subject:
                            subject_ret = True
                    if not subject_ret:
                        continue
                elif mail_subject and isinstance(mail_subject, str) and mail_subject not in subject:
                    continue
                # 转换为+8时区
                msg_date_time = msg.date.replace(tzinfo=datetime.timezone.utc).astimezone()
                msg_date_time_str = msg_date_time.strftime('%Y-%m-%d %H:%M:%S')
                if start_time:
                    msg_date_time_stamp = time.mktime(time.strptime(msg_date_time_str, '%Y-%m-%d %H:%M:%S'))
                    start_time_stamp = time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
                    if msg_date_time_stamp < start_time_stamp:
                        continue
                # 匹配邮件内容
                msg_html = msg.html
                if not msg_html and mail_content:
                    continue
                if mail_content and isinstance(mail_content, list) and msg_html:
                    content_ret = False
                    for x in mail_content:
                        if x in msg_html:
                            content_ret = True
                            break
                    if not content_ret:
                        continue
                if mail_content and isinstance(mail_content, str) and mail_content not in msg_html:
                    continue
                mail_msg['subject'] = subject
                mail_msg['date'] = msg_date_time_str
                mail_msg['content'] = msg_html
                aklog_debug(mail_msg)
                return mail_msg

        aklog_warn('收件箱未找到邮件，从垃圾箱继续找')
        with MailBoxUnencrypted(mail_server).login(username, passwd, 'Spam') as mailbox:
            i = 1
            for msg in mailbox.fetch(limit=limit, reverse=True):
                if i < start_index:
                    i += 1
                    continue
                # 先匹配邮箱标题
                subject = msg.subject
                if not subject and mail_subject:
                    continue
                if mail_subject and isinstance(mail_subject, list) and subject:
                    subject_ret = False
                    for x in mail_subject:
                        if x in subject:
                            subject_ret = True
                    if not subject_ret:
                        continue
                elif mail_subject and isinstance(mail_subject, str) and mail_subject not in subject:
                    continue
                # 转换为+8时区
                msg_date_time = msg.date.replace(tzinfo=datetime.timezone.utc).astimezone()
                msg_date_time_str = msg_date_time.strftime('%Y-%m-%d %H:%M:%S')
                if start_time:
                    msg_date_time_stamp = time.mktime(time.strptime(msg_date_time_str, '%Y-%m-%d %H:%M:%S'))
                    start_time_stamp = time.mktime(time.strptime(start_time, '%Y-%m-%d %H:%M:%S'))
                    if msg_date_time_stamp < start_time_stamp:
                        continue
                # 匹配邮件内容
                msg_html = msg.html
                if not msg_html and mail_content:
                    continue
                if mail_content and isinstance(mail_content, list) and msg_html:
                    content_ret = False
                    for x in mail_content:
                        if x in msg_html:
                            content_ret = True
                            break
                    if not content_ret:
                        continue
                if mail_content and isinstance(mail_content, str) and mail_content not in msg_html:
                    continue
                mail_msg['subject'] = subject
                mail_msg['date'] = msg_date_time_str
                mail_msg['content'] = msg_html
                aklog_debug(mail_msg)
                return mail_msg
        aklog_warn('垃圾箱也未找到邮件')
        return None
    except:
        aklog_error(traceback.format_exc())
        return None


class SmartHomeEmailProcess:
    """家居云邮件内容处理"""

    def __init__(self, email, email_pwd=None, mail_server=None):
        self.email = email

        self.email_pwd = email_pwd
        if not email_pwd and email.endswith('aktest.top'):
            # 如果未传入邮箱密码，将从config.ini中获取
            self.email_pwd = config_get_value_from_ini_file('environment', 'aktest_email_password')
            if self.email_pwd and (((self.email_pwd.startswith('"') and self.email_pwd.endswith('"'))
                                    or (self.email_pwd.startswith("'") and self.email_pwd.endswith("'")))):
                self.email_pwd = self.email_pwd[1:-1]
            else:
                self.email_pwd = 'Ak#123456'

        self.mail_server = mail_server
        if not mail_server:
            host = self.email.split('@')[1]
            self.mail_server = 'imap.%s' % host

    def get_pwd_from_email(self, mail_content=None, limit=1, start_index=1):
        """从邮箱获取帐号密码"""
        msg = get_last_email_content(self.email, self.email_pwd, self.mail_server,
                                     mail_subject='【akubela】Welcome to akubela smart home world.',
                                     mail_content=mail_content, limit=limit, start_index=start_index)
        if not msg:
            return ''
        try:
            pwd = re.search(r'Password:</td>.\n*.*>(.*)</td>', msg['content']).group(1)
        except:
            pwd = str_get_content_between_two_characters(
                msg['content'], '<td style="color:#000000;font-weight:600;">', '</td>').strip()
        aklog_info('user: %s, password: %s' % (self.email, pwd))
        return pwd

    def reset_pwd_from_email(self, new_passwd, mail_content=None, limit=1, start_index=1):
        """
        忘记密码后，登录邮箱获取重置密码的链接，然后通过链接重置密码
        Args:
            new_passwd (str):
            mail_content (str): 邮件内容需要包含的内容过滤条件
            limit (int): 获取满足条件的最新几封邮件
            start_index (int): 从哪一封邮件开始查找
        """
        try:
            msg = get_last_email_content(self.email, self.email_pwd, self.mail_server,
                                         mail_subject='【akubela】Reset your password.',
                                         mail_content=mail_content, limit=limit, start_index=start_index)
            if not msg:
                return False
            html_content = msg.get('content')
            reset_link = re.search(r'href="(https://[^"]+\.akubela\.com/#/reset\?code=[^"]+)"', html_content).group(1)
            aklog_debug(reset_link)
            code = re.search(r'[?&]code=([^&]+)', reset_link).group(1)
            base_url = re.search(r'(https://[^"]+\.akubela\.com)', reset_link).group(1)
            url = f"{base_url}/api/user-entry/v1.0/invoke/user-entry/method/account/general/forgot-password-codes/{code}"

            api = ApiRequests()
            resp = api.post(url=url, data=dict_dumps_2_json({"password": new_passwd}), headers={'user-platform': 'pc'})
            ret = resp.json()
            if ret.get('success'):
                return True
            else:
                return False
        except:
            aklog_error(traceback.format_exc())
            return False

    def click_link_join_family_from_email(self, mail_content=None, limit=1, start_index=1):
        """
        点击链接加入家庭
        Args:
            new_passwd (str):
            mail_content (str): 邮件内容需要包含的内容过滤条件
            limit (int): 获取满足条件的最新几封邮件
            start_index (int): 从哪一封邮件开始查找
        """
        try:
            msg = get_last_email_content(self.email, self.email_pwd, self.mail_server,
                                         mail_subject='【akubela】Welcome to akubela smart home world.',
                                         mail_content=mail_content, limit=limit, start_index=start_index)
            if not msg:
                return False
            html_content = msg.get('content')
            join_link = re.search(r'href="(https://[^"]+\.akubela\.com/#/joinHomeVerification\?code=[^"]+)"', html_content).group(1)
            aklog_debug(join_link)
            code = re.search(r'[?&]code=([^&]+)', join_link).group(1)
            base_url = re.search(r'(https://[^"]+\.akubela\.com)', join_link).group(1)
            url = f"{base_url}/api/user-entry/v1.0/invoke/user-entry/method/user-portal/user/join-families/{code}"

            api = ApiRequests()
            resp = api.post(url=url, headers={'user-platform': 'pc'})
            ret = resp.json()
            if ret.get('success'):
                return True
            else:
                return False
        except:
            aklog_error(traceback.format_exc())
            return False

    @staticmethod
    def login_email_reset_screen_lock_password(email_user, email_pwd, mail_server=None):
        """重置锁屏密码，主账号邮箱建议使用aktest.top"""
        aklog_info()
        start_time = get_date_time_add_delta(get_os_current_date_time(), -20)
        time.sleep(20)
        if not mail_server:
            aklog_info(email_user)
            host = email_user.split('@')[1]
            mail_server = 'imap.%s' % host
        for i in range(5):
            msg = get_last_email_content(email_user, email_pwd, mail_server,
                                         '【akubela】Reset screen password.', start_time)
            if msg:
                reset_url = str_get_content_between_two_characters(msg['content'], 'href="', '">')
                clean_url = reset_url.split('"')[0]
                aklog_info(clean_url)
                reset_url = clean_url.replace('/#/mailboxVerification?code=',
                                              '/api/user-entry/v1.0/invoke/user-entry/method/user-portal/push-devices-passwords/')
                aklog_info(reset_url)
                api = ApiRequests()
                resp = api.get(url=reset_url, headers={'user-platform': 'pc'})
                ret = resp.json()
                if ret.get('success'):
                    return True
                break
            elif i < 4:
                aklog_error('获取邮件失败，重试')
                time.sleep(10)
                continue
            else:
                aklog_error('获取邮件失败')
                return False


if __name__ == '__main__':
    print('debug')
    send_email = SendEmailHandler()
    send_email.send_email_with_img_attachment(
        ['jason.huang@akubela.com'], '自动化测试报告', '自动化测试报告')
    # msg = get_last_email_content('hzs01_cbuat_user1@aktest.top', 'Ak#123456', 'imap.aktest.top',
    #                              '【akubela】Welcome to akubela smart home world.', mail_content='Password:')
    # print(msg)
