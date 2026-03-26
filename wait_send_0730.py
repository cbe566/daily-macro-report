#!/usr/bin/env python3
"""等待到 07:30 整點，然後發送報告 Email"""
import time
import datetime
import sys
import os

# 確保在項目目錄
os.chdir('/home/ubuntu/daily-macro-report')
sys.path.insert(0, '/home/ubuntu/daily-macro-report')

DATE = '2026-03-27'
PDF_PATH = f'reports/daily_report_{DATE}.pdf'
JSON_PATH = f'reports/raw_data_{DATE}.json'

# 確認文件存在
if not os.path.exists(PDF_PATH):
    print(f"❌ PDF 文件不存在: {PDF_PATH}")
    sys.exit(1)
if not os.path.exists(JSON_PATH):
    print(f"❌ JSON 文件不存在: {JSON_PATH}")
    sys.exit(1)

print(f"PDF: {PDF_PATH} ({os.path.getsize(PDF_PATH)/1024:.0f} KB)")
print(f"JSON: {JSON_PATH} ({os.path.getsize(JSON_PATH)/1024:.0f} KB)")

# 等待到 07:30
now = datetime.datetime.now()
target = now.replace(hour=7, minute=30, second=0, microsecond=0)
diff = (target - now).total_seconds()

if diff > 0:
    print(f"\n當前時間: {now.strftime('%H:%M:%S')}")
    print(f"目標時間: 07:30:00")
    print(f"等待 {diff:.0f} 秒 ({diff/60:.1f} 分鐘)...")
    
    # 每分鐘報告一次
    while True:
        now = datetime.datetime.now()
        remaining = (target - now).total_seconds()
        if remaining <= 0:
            break
        if remaining > 60:
            print(f"  [{now.strftime('%H:%M:%S')}] 剩餘 {remaining/60:.1f} 分鐘...")
            time.sleep(min(60, remaining))
        else:
            print(f"  [{now.strftime('%H:%M:%S')}] 剩餘 {remaining:.0f} 秒...")
            time.sleep(remaining)
else:
    print(f"\n已過 07:30，立即發送！")

# 發送 Email
print(f"\n{'='*50}")
print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 開始發送 Email...")
print(f"{'='*50}")

from modules.email_sender import send_report_email
result = send_report_email(DATE, PDF_PATH, JSON_PATH)
print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Email 發送完成！")
print(f"結果: {result}")
