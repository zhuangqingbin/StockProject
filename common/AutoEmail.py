from abc import  abstractclassmethod
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import parseaddr, formataddr
from email.header import Header

from config import MAIL_HOST ,MAIL_USER
from config import MAIL_TOKEN, SENDER, RECEVIERS
from config import SENDER_NAME, RECEVIER_NAME


import os
mail_msg = """
<p>Python 邮件发送测试...</p>
<p><a href="http://www.runoob.com">这是一个链接</a></p>
"""

class EMAIL:
    def __init__(self, mail_host = MAIL_HOST, mail_user = MAIL_USER,
                 mail_token = MAIL_TOKEN, sender = SENDER,
                 receivers = RECEVIERS, sender_name = SENDER_NAME,
                 receiver_name = RECEVIER_NAME):
        self.__mail_host = mail_host
        self.__mail_user = mail_user
        self.__mail_token = mail_token
        self.sender = sender
        self.receivers = receivers
        self.sender_name = sender_name
        self.receiver_name = receiver_name

        self.connect()

    def connect(self):
        try:
            self.smtpObj = smtplib.SMTP_SSL(self.__mail_host, 465)
            # 发件人邮箱中的SMTP服务器，端口是25
            # self.smtpObj.connect(self.__mail_host, 25)
            self.smtpObj.login(self.__mail_user, self.__mail_token)
        except:
            print("连接失败")
            self.smtpObj = None




class TextEmail(EMAIL):

    def __init__(self, title = '每日快报'):
        super(TextEmail, self).__init__()
        # title邮件名
        self.title = title

    def send(self, message):
        message = MIMEText(message, 'html', 'utf-8')

        # 邮件名
        message['Subject'] = Header(self.title, 'utf-8')
        # 括号里的对应发件人邮箱昵称（随便起）、发件人邮箱账号
        message['From'] = Header(self.sender_name, 'utf-8')
        # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        message['To'] = Header(self.receiver_name, 'utf-8')

        try:
            self.smtpObj.sendmail(self.sender, self.receivers,
                                  message.as_string())
            print("邮件发送成功")
        except smtplib.SMTPException:
            print("Error: 无法发送邮件")


class ImageEmail(EMAIL):

    def __init__(self, title = '每日快报'):
        super(ImageEmail, self).__init__()
        # title邮件名
        self.title = title
        self._html = """
        <html>
            %s
        </html>
        """

    def add_text(self, message):
        message_html = """
            <p style="text-align:center">
                {}
            </p>
            <br>
            %s
        """.format(message)
        self._html = self._html % message_html

    def send(self, store_dir, stock_list):
        message = MIMEMultipart('related')

        # 邮件名
        message['Subject'] = Header(self.title, 'utf-8')
        # 括号里的对应发件人邮箱昵称（随便起）、发件人邮箱账号
        message['From'] = Header(self.sender_name, 'utf-8')
        # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        message['To'] = Header(self.receiver_name, 'utf-8')

        image_html = '<body>'
        #html_content += '<head><style>#string{text-align:center;font-size:25px;}</style><div id="string">我是居中显示的标题<div></head>'
        for stock in stock_list:
            image_html += '<a href="www.baidu.com"><img src="cid:{}" height="70" width="110"></a>'.format(stock)
        image_html += '</body>'
        self._html = self._html % image_html


        content = MIMEText(self._html , 'html', 'utf-8')
        message.attach(content)

        for stock in stock_list:
            with open(os.path.join(store_dir, stock + '.jpg'), 'rb') as fp:
            #fp = open('/Users/jimmy/python/FinTech/DataStore/monitor_stocks/002049.jpg', 'rb')
                msgImage = MIMEImage(fp.read())
            #fp.close()
            # 这个id用于上面html获取图片
                msgImage.add_header('Content-ID', stock)
                message.attach(msgImage)

        try:
            self.smtpObj.sendmail(self.sender, self.receivers,
                                  message.as_string())
            print("邮件发送成功")
        except smtplib.SMTPException:
            print("Error: 无法发送邮件")




def test(message):
    # 第三方 SMTP 服务
    mail_host = "smtp.gmail.com"  # 设置服务器
    mail_user = "jimmyzqb@gmail.com"  # 用户名
    mail_pass = 'dqdrnkqkplkakdzj'  # 授权码

    sender = 'jimmyzqb@gmail.com'
    receivers = ['360650538@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱


    message = MIMEText(message, 'html', 'utf-8')


    message['From'] = Header("量化机器人", 'utf-8')  # 括号里的对应发件人邮箱昵称（随便起）、发件人邮箱账号
    message['To'] = Header("终端用户", 'utf-8')  # 括号里的对应收件人邮箱昵称、收件人邮箱账号

    subject = '每日涨停股快报'
    message['Subject'] = Header(subject, 'utf-8')

    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_host, 25)  # 发件人邮箱中的SMTP服务器，端口是25
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException:
        print("Error: 无法发送邮件")

if __name__ == '__main__':
    email = TextEmail("Test For AutoEmail")
    email.send("Hello World.")