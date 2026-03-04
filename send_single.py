#!/usr/bin/env python3
"""發送單封報告 Email 給指定收件人"""
import os, sys, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

os.environ['TZ'] = 'Asia/Taipei'
sys.path.insert(0, os.path.dirname(__file__))

from modules.email_sender import generate_email_summary, SMTP_CONFIG

recipient = sys.argv[1]
report_date = sys.argv[2]
pdf_path = sys.argv[3]
json_path = sys.argv[4]

content = generate_email_summary(json_path)
print("已生成郵件摘要")

subject = f"每日宏觀資訊綜合早報 | {report_date}"

with open(pdf_path, 'rb') as f:
    pdf_payload = f.read()
pdf_filename = os.path.basename(pdf_path)

msg = MIMEMultipart()
msg['From'] = f"{SMTP_CONFIG['sender_name']} <{SMTP_CONFIG['sender_email']}>"
msg['To'] = recipient
msg['Subject'] = subject
msg.attach(MIMEText(content, 'plain', 'utf-8'))

pdf_attachment = MIMEBase('application', 'pdf')
pdf_attachment.set_payload(pdf_payload)
encoders.encode_base64(pdf_attachment)
pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
msg.attach(pdf_attachment)

server = smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port'])
server.ehlo()
server.starttls()
server.ehlo()
server.login(SMTP_CONFIG['sender_email'], SMTP_CONFIG['app_password'])
server.sendmail(SMTP_CONFIG['sender_email'], [recipient], msg.as_string())
server.quit()

print(f"✅ 已成功發送給 {recipient}")
