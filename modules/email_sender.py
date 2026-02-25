"""
郵件發送模組
- 讀取 recipients.json 管理收件人
- 自動從報告數據生成精簡摘要郵件正文
- 支持群組發送
- 使用 SMTP 全自動發送（無需人工介入）
"""

import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

RECIPIENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'recipients.json')

# SMTP 配置
SMTP_CONFIG = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'sender_email': 'cbe566@gmail.com',
    'app_password': 'uetubaoeuhizkhlu',  # Google 應用程式密碼
    'sender_name': '何宣逸'
}


def load_recipients(group=None):
    """讀取收件人清單"""
    with open(RECIPIENTS_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    if group is None:
        group = config.get('active_group', 'default')
    
    group_data = config['groups'].get(group, {})
    return {
        'to': group_data.get('to', []),
        'cc': group_data.get('cc', []),
        'bcc': group_data.get('bcc', [])
    }


def add_recipient(email, group='default', role='to'):
    """新增收件人"""
    with open(RECIPIENTS_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    if group not in config['groups']:
        config['groups'][group] = {
            'description': f'{group} 群組',
            'to': [],
            'cc': [],
            'bcc': []
        }
    
    if email not in config['groups'][group][role]:
        config['groups'][group][role].append(email)
    
    with open(RECIPIENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"已新增 {email} 到 {group} 群組的 {role} 清單")


def remove_recipient(email, group='default', role='to'):
    """移除收件人"""
    with open(RECIPIENTS_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    if group in config['groups'] and email in config['groups'][group].get(role, []):
        config['groups'][group][role].remove(email)
        with open(RECIPIENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"已從 {group} 群組的 {role} 清單移除 {email}")
    else:
        print(f"未找到 {email} 在 {group} 群組的 {role} 清單中")


def list_recipients():
    """列出所有收件人"""
    with open(RECIPIENTS_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print(f"當前啟用群組：{config.get('active_group', 'default')}")
    print("=" * 50)
    
    for group_name, group_data in config['groups'].items():
        desc = group_data.get('description', '')
        print(f"\n群組：{group_name} ({desc})")
        print(f"  收件人 (To)：{', '.join(group_data.get('to', [])) or '無'}")
        print(f"  副本 (CC)：{', '.join(group_data.get('cc', [])) or '無'}")
        print(f"  密件副本 (BCC)：{', '.join(group_data.get('bcc', [])) or '無'}")


def _format_pct(pct):
    """格式化漲跌幅"""
    if pct is None or pct == 0:
        return "0.00%"
    return f"{pct:+.2f}%"


def _format_price(price, symbol=""):
    """格式化價格"""
    if price is None or price == 0:
        return ""
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    else:
        return f"${price:.4f}"


def generate_email_summary(json_path):
    """從 JSON 數據自動生成精簡摘要郵件正文"""
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    report_date = data.get('report_date', '')
    md = data.get('market_data', {})
    news = data.get('news_events', [])
    index_analysis = data.get('index_analysis', {})
    calendar = data.get('calendar_events', [])
    
    lines = []
    lines.append(f"以下為 {report_date} 每日宏觀資訊綜合早報摘要：")
    lines.append("")
    
    # ===== 市場總覽 =====
    overall = index_analysis.get('overall_summary', '')
    if overall:
        lines.append("【市場總覽】")
        lines.append(overall)
        lines.append("")
    
    # ===== 宏觀重點新聞 =====
    if news:
        lines.append("【宏觀重點新聞】")
        for i, n in enumerate(news[:5], 1):
            title = n.get('title', '')
            lines.append(f"{i}. {title}")
        lines.append("")
    
    # ===== 指數表現亮點 =====
    lines.append("【指數表現亮點】")
    
    # 亞洲
    asia = md.get('asia_indices', {})
    if asia:
        asia_items = []
        sorted_asia = sorted(asia.items(), key=lambda x: abs(x[1].get('change_pct', 0)) if isinstance(x[1], dict) else 0, reverse=True)
        for name, v in sorted_asia[:3]:
            if isinstance(v, dict):
                pct = v.get('change_pct', 0)
                asia_items.append(f"{name} {_format_pct(pct)}")
        if asia_items:
            lines.append(f"- 亞洲：{'、'.join(asia_items)}")
    
    # 歐洲
    europe = md.get('europe_indices', {})
    if europe:
        europe_items = []
        sorted_europe = sorted(europe.items(), key=lambda x: abs(x[1].get('change_pct', 0)) if isinstance(x[1], dict) else 0, reverse=True)
        for name, v in sorted_europe[:3]:
            if isinstance(v, dict):
                pct = v.get('change_pct', 0)
                europe_items.append(f"{name} {_format_pct(pct)}")
        if europe_items:
            lines.append(f"- 歐洲：{'、'.join(europe_items)}")
    
    # 美國
    us = md.get('us_indices', {})
    if us:
        us_items = []
        sorted_us = sorted(us.items(), key=lambda x: abs(x[1].get('change_pct', 0)) if isinstance(x[1], dict) else 0, reverse=True)
        for name, v in sorted_us[:3]:
            if isinstance(v, dict):
                pct = v.get('change_pct', 0)
                us_items.append(f"{name} {_format_pct(pct)}")
        if us_items:
            lines.append(f"- 美國：{'、'.join(us_items)}")
    
    lines.append("")
    
    # ===== 加密貨幣 =====
    crypto = md.get('crypto', {})
    if crypto:
        lines.append("【加密貨幣】")
        crypto_items = []
        priority = ['Bitcoin', 'Ethereum', 'Solana', 'XRP', 'BNB']
        for name in priority:
            if name in crypto and isinstance(crypto[name], dict):
                v = crypto[name]
                pct = v.get('change_pct', 0)
                price = v.get('price', 0)
                price_str = _format_price(price) if price else ""
                if price_str:
                    crypto_items.append(f"{name} {_format_pct(pct)} ({price_str})")
                else:
                    crypto_items.append(f"{name} {_format_pct(pct)}")
        if crypto_items:
            lines.append(f"- {'、'.join(crypto_items)}")
        lines.append("")
    
    # ===== 本週經濟日曆重點 =====
    if calendar:
        lines.append("【本週經濟日曆重點】")
        for evt in calendar[:6]:
            if isinstance(evt, dict):
                date = evt.get('date', '')
                event_name = evt.get('event', '')
                if date and '-' in date:
                    parts = date.split('-')
                    short_date = f"{int(parts[1])}/{int(parts[2])}"
                else:
                    short_date = date
                lines.append(f"- {short_date} {event_name}")
        lines.append("")
    
    # ===== 結尾 =====
    lines.append("完整報告請見附件 PDF。")
    lines.append("")
    lines.append("資料來源：Yahoo Finance、Polygon.io、S&P Global、CNBC、Investing.com")
    
    return "\n".join(lines)


def send_report_email(report_date, pdf_path, json_path=None, group=None):
    """通過 SMTP 全自動發送報告郵件（無需人工介入）
    
    Args:
        report_date: 報告日期字串 (如 '2026-02-24')
        pdf_path: PDF 報告的絕對路徑
        json_path: JSON 數據文件路徑（用於生成摘要），None 則自動推斷
        group: 收件群組名稱，None 則使用 active_group
    """
    recipients = load_recipients(group)
    
    # 所有收件人統一放入 BCC 保護隱私
    all_bcc = list(recipients.get('to', [])) + list(recipients.get('cc', [])) + list(recipients.get('bcc', []))
    if not all_bcc:
        print("錯誤：沒有收件人")
        return False
    
    # 自動推斷 JSON 路徑
    if json_path is None:
        report_dir = os.path.dirname(pdf_path)
        json_path = os.path.join(report_dir, f"raw_data_{report_date}.json")
    
    # 生成郵件正文
    subject = f"每日宏觀資訊綜合早報 | {report_date}"
    
    if os.path.exists(json_path):
        try:
            content = generate_email_summary(json_path)
            print("已從數據自動生成郵件摘要")
        except Exception as e:
            print(f"生成摘要失敗，使用預設正文：{e}")
            content = _fallback_content(report_date)
    else:
        print(f"JSON 數據文件不存在：{json_path}，使用預設正文")
        content = _fallback_content(report_date)
    
    # 構建郵件（全部使用 BCC，保護收件者隱私）
    msg = MIMEMultipart()
    msg['From'] = f"{SMTP_CONFIG['sender_name']} <{SMTP_CONFIG['sender_email']}>"
    msg['To'] = SMTP_CONFIG['sender_email']  # To 只放發件人自己
    # 不設定 Cc，所有收件人透過 BCC 發送，彼此看不到
    msg['Subject'] = subject
    
    # 郵件正文
    msg.attach(MIMEText(content, 'plain', 'utf-8'))
    
    # 附加 PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            pdf_attachment = MIMEBase('application', 'pdf')
            pdf_attachment.set_payload(f.read())
            encoders.encode_base64(pdf_attachment)
            pdf_filename = os.path.basename(pdf_path)
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
            msg.attach(pdf_attachment)
        print(f"已附加 PDF：{pdf_filename}")
    else:
        print(f"警告：PDF 文件不存在：{pdf_path}")
    
    # 通過 SMTP 發送（全部走 BCC）
    print(f"\n正在通過 SMTP 發送郵件...")
    print(f"  發件人：{SMTP_CONFIG['sender_name']} <{SMTP_CONFIG['sender_email']}>")
    print(f"  BCC 收件人：{len(all_bcc)} 位")
    
    try:
        server = smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port'])
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_CONFIG['sender_email'], SMTP_CONFIG['app_password'])
        server.sendmail(SMTP_CONFIG['sender_email'], all_bcc, msg.as_string())
        server.quit()
        
        print(f"\n✅ 郵件發送成功！已發送給 {len(all_bcc)} 位收件人（BCC）。")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ SMTP 認證失敗：{e}")
        print("請確認應用程式密碼是否正確。")
        return False
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP 發送失敗：{e}")
        return False
    except Exception as e:
        print(f"\n❌ 郵件發送異常：{e}")
        return False


def _fallback_content(report_date):
    """預設郵件正文（當 JSON 不可用時）"""
    return f"""以下為 {report_date} 每日宏觀資訊綜合早報：

完整報告請見附件 PDF。

資料來源：Yahoo Finance、Polygon.io、S&P Global、CNBC、Investing.com"""


# CLI 介面
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法：")
        print("  python email_sender.py list                              - 列出所有收件人")
        print("  python email_sender.py add <email> [group] [role]        - 新增收件人")
        print("  python email_sender.py remove <email> [group] [role]     - 移除收件人")
        print("  python email_sender.py send <date> <pdf_path> [json_path] - 發送報告")
        print("  python email_sender.py preview <json_path>               - 預覽郵件摘要")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'list':
        list_recipients()
    elif cmd == 'add':
        email = sys.argv[2]
        group = sys.argv[3] if len(sys.argv) > 3 else 'default'
        role = sys.argv[4] if len(sys.argv) > 4 else 'to'
        add_recipient(email, group, role)
    elif cmd == 'remove':
        email = sys.argv[2]
        group = sys.argv[3] if len(sys.argv) > 3 else 'default'
        role = sys.argv[4] if len(sys.argv) > 4 else 'to'
        remove_recipient(email, group, role)
    elif cmd == 'send':
        report_date = sys.argv[2]
        pdf_path = sys.argv[3]
        json_path = sys.argv[4] if len(sys.argv) > 4 else None
        send_report_email(report_date, pdf_path, json_path)
    elif cmd == 'preview':
        json_path = sys.argv[2]
        print(generate_email_summary(json_path))
    else:
        print(f"未知命令：{cmd}")
