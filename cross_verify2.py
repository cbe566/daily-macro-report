#!/usr/bin/env python3
"""交叉驗證：用 yfinance 驗證修復後報告中的關鍵數據點"""

import json
import yfinance as yf
import os

os.environ['TZ'] = 'Asia/Taipei'

with open('reports/raw_data_2026-03-23.json', 'r') as f:
    data = json.load(f)

md = data['market_data']

print("=" * 80)
print("數據品質交叉驗證（修復後）- 2026-03-23")
print("=" * 80)

# 定義要驗證的關鍵數據點
verify_items = [
    ("S&P 500", "^GSPC", md['us_indices']['S&P 500']),
    ("納斯達克", "^IXIC", md['us_indices']['納斯達克']),
    ("道瓊斯", "^DJI", md['us_indices']['道瓊斯']),
    ("Bitcoin", "BTC-USD", md['crypto']['Bitcoin']),
    ("黃金", "GC=F", md['commodities']['黃金']),
    ("Ethereum", "ETH-USD", md['crypto']['Ethereum']),
    ("日經225", "^N225", md['asia_indices']['日經225']),
]

errors = []
warnings = []

print(f"\n{'指標':<15} {'報告收盤':<15} {'YF收盤':<15} {'偏差%':<10} {'報告漲跌%':<12} {'YF漲跌%':<12} {'漲跌偏差':<10} {'結果':<8}")
print("-" * 100)

for name, symbol, report_data in verify_items:
    report_close = report_data['current']
    report_pct = report_data['change_pct']
    
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
        
        # 價格偏差
        price_dev = abs(yf_close - report_close) / yf_close * 100 if yf_close else 0
        
        # 漲跌幅偏差
        pct_dev = abs(yf_pct - report_pct)
        
        # 判斷
        if price_dev > 1.0:
            status = "FAIL"
            errors.append(f"{name}: 價格偏差 {price_dev:.2f}%")
        elif pct_dev > 1.0:
            status = "WARN"
            warnings.append(f"{name}: 漲跌幅偏差 {pct_dev:.2f}pp (報告={report_pct:.2f}%, YF={yf_pct:.2f}%)")
        else:
            status = "PASS"
        
        print(f"{name:<15} {report_close:<15.2f} {yf_close:<15.2f} {price_dev:<10.3f} {report_pct:<12.2f} {yf_pct:<12.2f} {pct_dev:<10.3f} {status:<8}")
        
    except Exception as e:
        warnings.append(f"{name}: {e}")

print("-" * 100)

# 驗證熱門股票
print("\n額外驗證：熱門股票抽樣")
print("-" * 80)
hot = data.get('hot_stocks', {})
for market in ['美股', '港股', '台股']:
    stocks = hot.get(market, {})
    for cat in ['inflow', 'outflow']:
        items = stocks.get(cat, [])
        for stock in items[:2]:
            sym = stock.get('symbol', '')
            rpct = stock.get('change_pct', 0)
            try:
                t = yf.Ticker(sym)
                hist = t.history(period='5d')
                if len(hist) >= 2:
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    yf_pct = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
                    pct_dev = abs(yf_pct - rpct)
                    status = "PASS" if pct_dev < 1.0 else ("WARN" if pct_dev < 2.0 else "FAIL")
                    if status == "FAIL":
                        errors.append(f"{stock.get('name','')}: 漲跌幅偏差 {pct_dev:.2f}pp")
                    print(f"  [{market}-{cat}] {stock.get('name',''):<20} ({sym}): 報告={rpct:+.2f}%, YF={yf_pct:+.2f}%, 偏差={pct_dev:.2f}pp [{status}]")
            except Exception as e:
                pass

# 總結
print("\n" + "=" * 80)
print("驗證總結")
print("=" * 80)

if errors:
    print(f"\n❌ 發現 {len(errors)} 個嚴重偏差：")
    for e in errors:
        print(f"  - {e}")
else:
    print("\n✅ 所有關鍵數據點驗證通過，無嚴重偏差")

if warnings:
    print(f"\n⚠️ {len(warnings)} 個警告：")
    for w in warnings:
        print(f"  - {w}")
else:
    print("無警告。")
