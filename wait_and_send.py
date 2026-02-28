"""
等待至 8:00 (GMT+8) 後發送 Email
"""
import os
import sys
import time
import datetime

os.environ['TZ'] = 'Asia/Taipei'
time.tzset()

sys.path.insert(0, os.path.dirname(__file__))
from modules.email_sender import send_report_email

report_date = '2026-02-28'
pdf_path = os.path.join(os.path.dirname(__file__), 'reports', f'daily_report_{report_date}.pdf')
json_path = os.path.join(os.path.dirname(__file__), 'reports', f'raw_data_{report_date}.json')

# Wait until 8:00
now = datetime.datetime.now()
target = now.replace(hour=8, minute=0, second=0, microsecond=0)
if now < target:
    diff = (target - now).total_seconds()
    print(f"[{now.strftime('%H:%M:%S')}] 等待 {diff:.0f} 秒至 08:00:00...")
    time.sleep(diff)

# Send at 8:00
now = datetime.datetime.now()
print(f"\n[{now.strftime('%H:%M:%S')}] 開始發送 Email...")
result = send_report_email(report_date, pdf_path, json_path)
print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] 發送結果: {'成功' if result else '失敗'}")
