"""
等待至 07:30 (GMT+8) 後發送 Email
"""
import os
import sys
import time
import datetime

os.environ['TZ'] = 'Asia/Taipei'
time.tzset()

sys.path.insert(0, os.path.dirname(__file__))
from modules.email_sender import send_report_email

report_date = '2026-03-25'
pdf_path = os.path.join(os.path.dirname(__file__), 'reports', f'daily_report_{report_date}.pdf')
json_path = os.path.join(os.path.dirname(__file__), 'reports', f'raw_data_{report_date}.json')

# Wait until 07:30
now = datetime.datetime.now()
target = now.replace(hour=7, minute=30, second=0, microsecond=0)
if now < target:
    diff = (target - now).total_seconds()
    print(f"[{now.strftime('%H:%M:%S')}] 等待 {diff:.0f} 秒至 07:30:00...")
    # 每 60 秒輸出一次進度
    remaining = diff
    while remaining > 0:
        sleep_time = min(60, remaining)
        time.sleep(sleep_time)
        remaining -= sleep_time
        now_check = datetime.datetime.now()
        if remaining > 0:
            print(f"[{now_check.strftime('%H:%M:%S')}] 距離 07:30 還有 {remaining:.0f} 秒...")
else:
    print(f"[{now.strftime('%H:%M:%S')}] 已過 07:30，立即發送")

# Send at 07:30
now = datetime.datetime.now()
print(f"\n[{now.strftime('%H:%M:%S')}] 開始發送 Email...")
result = send_report_email(report_date, pdf_path, json_path)
print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] 發送結果: {'成功' if result else '失敗'}")
