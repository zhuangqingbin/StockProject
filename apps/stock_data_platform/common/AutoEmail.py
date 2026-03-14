import os
import smtplib
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import MAIL_HOST, MAIL_TOKEN, MAIL_USER, RECEVIERS, RECEIVERS, SENDER, SENDER_NAME, RECEVIER_NAME


class EMAIL:
    def __init__(
        self,
        mail_host=MAIL_HOST,
        mail_user=MAIL_USER,
        mail_token=MAIL_TOKEN,
        sender=SENDER,
        receivers=None,
        sender_name=SENDER_NAME,
        receiver_name=RECEVIER_NAME,
    ):
        self.__mail_host = mail_host
        self.__mail_user = mail_user
        self.__mail_token = mail_token
        self.sender = sender
        self.receivers = receivers if receivers is not None else (RECEIVERS or RECEVIERS)
        self.sender_name = sender_name
        self.receiver_name = receiver_name
        self.smtp_obj = None
        self.connect()

    def connect(self):
        if not self.__mail_host or not self.__mail_user or not self.__mail_token:
            print("邮件配置不完整，跳过 SMTP 连接。")
            return
        try:
            smtp_obj = smtplib.SMTP_SSL(self.__mail_host, 465)
            smtp_obj.login(self.__mail_user, self.__mail_token)
            self.smtp_obj = smtp_obj
        except smtplib.SMTPException:
            print("连接失败")
            self.smtp_obj = None


class TextEmail(EMAIL):
    def __init__(self, title="每日快报"):
        super().__init__()
        self.title = title

    def send(self, message):
        if self.smtp_obj is None:
            print("SMTP 未连接，邮件未发送。")
            return

        email_message = MIMEText(message, "html", "utf-8")
        email_message["Subject"] = Header(self.title, "utf-8")
        email_message["From"] = Header(self.sender_name, "utf-8")
        email_message["To"] = Header(self.receiver_name, "utf-8")

        try:
            self.smtp_obj.sendmail(self.sender, self.receivers, email_message.as_string())
            print("邮件发送成功")
        except smtplib.SMTPException:
            print("Error: 无法发送邮件")


class ImageEmail(EMAIL):
    def __init__(self, title="每日快报"):
        super().__init__()
        self.title = title
        self._html = "<html>%s</html>"

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
        if self.smtp_obj is None:
            print("SMTP 未连接，邮件未发送。")
            return

        message = MIMEMultipart("related")
        message["Subject"] = Header(self.title, "utf-8")
        message["From"] = Header(self.sender_name, "utf-8")
        message["To"] = Header(self.receiver_name, "utf-8")

        image_html = "<body>"
        for stock in stock_list:
            image_html += f'<a href="www.baidu.com"><img src="cid:{stock}" height="70" width="110"></a>'
        image_html += "</body>"
        self._html = self._html % image_html

        message.attach(MIMEText(self._html, "html", "utf-8"))

        for stock in stock_list:
            with open(os.path.join(store_dir, f"{stock}.jpg"), "rb") as file_obj:
                image = MIMEImage(file_obj.read())
            image.add_header("Content-ID", stock)
            message.attach(image)

        try:
            self.smtp_obj.sendmail(self.sender, self.receivers, message.as_string())
            print("邮件发送成功")
        except smtplib.SMTPException:
            print("Error: 无法发送邮件")


def test(message):
    email = TextEmail("Test For AutoEmail")
    email.send(message)


if __name__ == "__main__":
    test("Hello World.")
