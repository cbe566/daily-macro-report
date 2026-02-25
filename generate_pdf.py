#!/usr/bin/env python3
"""
從已有的 JSON 數據生成精美 HTML+CSS PDF 報告
用法：
  python3 generate_pdf.py              # 使用今天的日期
  python3 generate_pdf.py 2026-02-24   # 指定日期
"""
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.html_report_generator import generate_html_report
from weasyprint import HTML


def main():
    report_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')
    json_path = f"reports/raw_data_{report_date}.json"

    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    market_data = raw.get('market_data', {})
    news_events = raw.get('news_events', [])
    hot_stocks = raw.get('hot_stocks', {})
    stock_analysis = raw.get('stock_analysis', {})
    index_analysis = raw.get('index_analysis', {})
    calendar_events = raw.get('calendar_events', [])

    print(f"Report date: {report_date}")
    print(f"Hot stocks markets: {list(hot_stocks.keys())}")
    for m, s in hot_stocks.items():
        print(f"  {m}: {len(s)} stocks")

    print("Generating HTML report...")
    html_content = generate_html_report(
        market_data, news_events, hot_stocks, stock_analysis,
        index_analysis, calendar_events, report_date
    )

    # Save HTML
    html_path = f"reports/daily_report_{report_date}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML saved: {html_path}")

    # Convert to PDF with WeasyPrint
    print("Converting to PDF...")
    pdf_path = f"reports/daily_report_{report_date}.pdf"
    HTML(string=html_content).write_pdf(pdf_path)
    print(f"PDF saved: {pdf_path}")

    print("Done!")


if __name__ == '__main__':
    main()
