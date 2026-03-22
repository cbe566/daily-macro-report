#!/usr/bin/env python3
"""交叉驗證：用 yfinance 驗證報告中的關鍵數據點"""

import json
import yfinance as yf
import os
from datetime import datetime

os.environ['TZ'] = 'Asia/Taipei'

with open('reports/raw_data_2026-03-23.json', 'r') as f:
    data = json.load(f)

md = data['market_data']

print("=" * 80)
print("數據品質交叉驗證 - 2026-03-23")
print("=" * 80)

# 定義要驗證的 5+ 個關鍵數據點
verify_items = [
    ("S&P 500", "^GSPC", md['us_indices']['S&P 500']['current'], md['us_indices']['S&P 500']['change_pct']),
    ("納斯達克", "^IXIC", md['us_indices']['納斯達克']['current'], md['us_indices']['納斯達克']['change_pct']),
    ("Bitcoin", "BTC-USD", md['crypto']['Bitcoin']['current'], md['crypto']['Bitcoin']['change_pct']),
    ("黃金", "GC=F", md['commodities']['黃金']['current'], md['commodities']['黃金']['change_pct']),
    ("Ethereum", "ETH-USD", md['crypto']['Ethereum']['current'], md['crypto']['Ethereum']['change_pct']),
    ("美元指數", "DX-Y.NYB", md['forex']['美元指數']['current'], md['forex']['美元指數']['change_pct']),
    ("日經225", "^N225", md['asia_indices']['日經225']['current'], md['asia_indices']['日經225']['change_pct']),
]

errors = []
warnings = []

print(f"\n{'指標':<15} {'報告收盤':<15} {'YF收盤':<15} {'價格偏差%':<10} {'報告漲跌%':<10} {'YF漲跌%':<10} {'結果':<8}")
print("-" * 90)

for name, symbol, report_close, report_pct in verify_items:
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period='5d')
        if len(hist) < 2:
            warnings.append(f"{name}: 數據不足")
            continue
        
        latest = hist.iloc[-1]
        prev = hist.iloc[-2]
        yf_close = latest['Close']
        yf_pct = ((yf_close - prev['Close']) / prev['Close']) * 100
        yf_date = str(hist.index[-1].date()) if hasattr(hist.index[-1], 'date') else str(hist.index[-1])[:10]
        
        # 價格偏差
        price_dev = abs(yf_close - report_close) / yf_close * 100 if yf_close else 0
        
        # 漲跌幅偏差
        pct_dev = abs(yf_pct - report_pct)
        
        # 判斷
        if price_dev > 1.0:
            status = "FAIL"
            errors.append(f"{name}: 價格偏差 {price_dev:.2f}% (報告={report_close:.2f}, YF={yf_close:.2f})")
        elif pct_dev > 1.0:
            status = "WARN"
            warnings.append(f"{name}: 漲跌幅偏差 {pct_dev:.2f}pp (報告={report_pct:.2f}%, YF={yf_pct:.2f}%)")
        else:
            status = "PASS"
        
        print(f"{name:<15} {report_close:<15.2f} {yf_close:<15.2f} {price_dev:<10.4f} {report_pct:<10.2f} {yf_pct:<10.2f} {status:<8} [{yf_date}]")
        
    except Exception as e:
        warnings.append(f"{name}: {e}")
        print(f"{name:<15} {report_close:<15.2f} {'ERROR':<15} {'N/A':<10} {report_pct:<10.2f} {'N/A':<10} {'ERROR':<8}")

print("-" * 90)

# 額外驗證：檢查熱門股票中的 SMCI（跌幅最大的）
print("\n額外驗證：熱門股票抽樣")
print("-" * 90)
hot = data.get('hot_stocks', {})
us_outflow = hot.get('美股', {}).get('outflow', [])
if us_outflow:
    for stock in us_outflow[:3]:
        sym = stock.get('symbol', '')
        rpct = stock.get('change_pct', 0)
        try:
            t = yf.Ticker(sym)
            hist = t.history(period='5d')
            if len(hist) >= 2:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]
                yf_close = latest['Close']
                yf_pct = ((yf_close - prev['Close']) / prev['Close']) * 100
                pct_dev = abs(yf_pct - rpct)
                status = "PASS" if pct_dev < 1.0 else "WARN"
                if pct_dev > 2.0:
                    status = "FAIL"
                    errors.append(f"{stock.get('name','')}: 漲跌幅偏差 {pct_dev:.2f}pp")
                print(f"  {stock.get('name',''):<20} ({sym}): 報告={rpct:+.2f}%, YF={yf_pct:+.2f}%, 偏差={pct_dev:.2f}pp [{status}]")
        except Exception as e:
            print(f"  {stock.get('name',''):<20} ({sym}): ERROR - {e}")

# 總結
print("\n" + "=" * 80)
print("驗證總結")
print("=" * 80)

if errors:
    print(f"\n❌ 發現 {len(errors)} 個嚴重偏差（>1%）：")
    for e in errors:
        print(f"  - {e}")
else:
    print("\n✅ 所有關鍵數據點價格偏差均在 1% 以內")

if warnings:
    print(f"\n⚠️ {len(warnings)} 個警告：")
    for w in warnings:
        print(f"  - {w}")

# 特別檢查：S&P 500 和 NASDAQ 漲跌幅為 0 的問題
print("\n" + "=" * 80)
print("特別檢查：漲跌幅為 0 的指數")
print("=" * 80)
zero_pct_items = []
for cat_name, cat_data in md.items():
    if isinstance(cat_data, dict):
        for item_name, item_data in cat_data.items():
            if isinstance(item_data, dict) and item_data.get('change_pct') == 0.0:
                zero_pct_items.append(f"{item_name} (current={item_data.get('current')}, prev={item_data.get('previous')})")

if zero_pct_items:
    print(f"以下 {len(zero_pct_items)} 個指標漲跌幅為 0.00%：")
    for item in zero_pct_items:
        print(f"  - {item}")
    print("\n說明：這些指標的 current 和 previous 相同，可能是因為數據源在週末/非交易時段返回相同值。")
    print("如果今天是週一且這些市場上週五有交易，則漲跌幅應反映上週五的變化。")
else:
    print("無漲跌幅為 0 的指標。")
