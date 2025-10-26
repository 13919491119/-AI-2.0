import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os

def send_email_alert(subject, content, to_addr=None, smtp_host=None, smtp_port=None, user=None, password=None):
    """
    邮件告警推送（支持新浪、QQ、163等主流邮箱）
    """
    # 默认参数（新浪邮箱）
    if to_addr is None:
        to_addr = 'david_h_liu@sina.com'
    if smtp_host is None:
        smtp_host = 'smtp.sina.com'
    if smtp_port is None:
        smtp_port = 465
    if user is None:
        user = os.environ.get('EMAIL_USER', 'david_h_liu@sina.com')
    if password is None:
        password = os.environ.get('EMAIL_PASS')  # 请在环境变量中配置授权码
    if not password:
        print('[邮件告警] 未配置邮箱授权码，无法发送邮件')
        return False
    try:
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = Header(user)
        msg['To'] = Header(to_addr)
        msg['Subject'] = Header(subject)
        server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        server.login(user, password)
        server.sendmail(user, [to_addr], msg.as_string())
        server.quit()
        print('[邮件告警] 邮件发送成功')
        return True
    except Exception as e:
        print(f'[邮件告警] 邮件发送失败: {e}')
        return False
