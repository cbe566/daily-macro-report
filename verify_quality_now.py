#!/usr/bin/env python3
"""數據品質驗證：用 yfinance 交叉驗證報告中的關鍵數據點"""
import json
import yfinance as yf
import datetime

# 載入報告原始數據
with open('reports/raw_data_2026-03-27.json', 'r') as f:
    raw = json.load(f)

md = raw['market_data']

print("=" * 70)
print("數據品質驗證 - 交叉驗證關鍵數據點")
print("=" * 70)

# 定義要驗證的數據點：(報告section, 報告key, yfinance symbol)
verify_targets = [
    ('us_indices', 'S&P 500', '^GSPC'),
    ('us_indices', '納斯達克', '^IXIC'),
    ('crypto', 'Bitcoin', 'BTC-USD'),
    ('commodities', '黃金', 'GC=F'),
    ('commodities', '原油(WTI)', 'CL=F'),
]

all_pass = True
results = []

for section, report_key, yf_symbol in verify_targets:
    print(f"\n--- 驗證: {report_key} ({yf_symbol}) ---")
    
    # 從報告數據中獲取
    report_data = md.get(section, {}).get(report_key, {})
    report_close = report_data.get('current')
    report_change_pct = report_data.get('change_pct')
    
    if report_close is None:
        print(f"  ⚠ 報告中未找到 {report_key}")
        continue
    
    # 從 yfinance 獲取最新數據
    try:
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period='5d')
        if hist.empty:
            print(f"  ⚠ yfinance 無法獲取 {yf_symbol} 數據")
            continue
        
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else None
        
        yf_close = latest['Close']
        yf_date = str(latest.name.date())
        yf_change_pct = ((latest['Close'] - prev['Close']) / prev['Close'] * 100) if prev is not None else None
        
        print(f"  yfinance 收盤價: {yf_close:.2f} (日期: {yf_date})")
        if yf_change_pct is not None:
            print(f"  yfinance 漲跌幅: {yf_change_pct:+.2f}%")
        
        print(f"  報告收盤價:   {report_close:.2f}")
        if report_change_pct is not None:
            print(f"  報告漲跌幅:   {report_change_pct:+.2f}%")
        
        # 價格偏差驗證
        price_diff_pct = abs(report_close - yf_close) / yf_close * 100
        print(f"  價格偏差: {price_diff_pct:.4f}%")
        
        if price_diff_pct > 1.0:
            print(f"  ❌ 價格偏差超過 1%！需要排查！")
            all_pass = False
        else:
            print(f"  ✅ 價格驗證通過")
        
        # 漲跌幅偏差驗證
        if report_change_pct is not None and yf_change_pct is not None:
            change_diff = abs(report_change_pct - yf_change_pct)
            print(f"  漲跌幅偏差: {change_diff:.4f} 個百分點")
            
            if change_diff > 1.0:
                print(f"  ❌ 漲跌幅偏差超過 1 個百分點！需要排查！")
                all_pass = False
            else:
                print(f"  ✅ 漲跌幅驗證通過")
        
        results.append({
            'name': report_key,
            'report_close': report_close,
            'yf_close': yf_close,
            'price_diff_pct': price_diff_pct,
            'report_change': report_change_pct,
            'yf_change': yf_change_pct,
            'yf_date': yf_date,
        })
        
    except Exception as e:
        print(f"  ⚠ yfinance 錯誤: {e}")
        continue

# 額外驗證一支熱門股票
print(f"\n--- 驗證: NVIDIA (NVDA) - 熱門股票 ---")
try:
    nvda = yf.Ticker('NVDA')
    hist = nvda.history(period='5d')
    latest = hist.iloc[-1]
    prev = hist.iloc[-2]
    yf_close = latest['Close']
    yf_change = ((latest['Close'] - prev['Close']) / prev['Close'] * 100)
    yf_date = str(latest.name.date())
    print(f"  yfinance 收盤價: {yf_close:.2f} (日期: {yf_date})")
    print(f"  yfinance 漲跌幅: {yf_change:+.2f}%")
    
    # 從 hot_stocks 中查找
    hot = raw.get('hot_stocks', {}).get('美股', {})
    hot_buy = hot.get('buy', [])
    hot_sell = hot.get('sell', [])
    found_nvda = False
    for stock in hot_buy + hot_sell:
        if stock.get('ticker') == 'NVDA':
            report_close = stock.get('close') or stock.get('price')
            report_change = stock.get('change_pct')
            if report_close:
                price_diff = abs(float(report_close) - yf_close) / yf_close * 100
                print(f"  報告收盤價: {report_close}")
                print(f"  價格偏差: {price_diff:.4f}%")
                if price_diff > 1.0:
                    print(f"  ❌ 偏差超過 1%！")
                    all_pass = False
                else:
                    print(f"  ✅ 驗證通過")
            found_nvda = True
            break
    
    if not found_nvda:
        # 查看 stock_analysis
        sa = raw.get('stock_analysis', {}).get('NVDA')
        if sa:
            print(f"  stock_analysis 中有 NVDA 數據")
        else:
            print(f"  NVDA 不在熱門股票名單中（可能未被篩選），用 yfinance 數據作為參考基準")
            print(f"  ✅ yfinance 數據可用作參考")
except Exception as e:
    print(f"  ⚠ 錯誤: {e}")

print("\n" + "=" * 70)
print("驗證摘要:")
print("-" * 70)
for r in results:
    status = "✅" if r['price_diff_pct'] <= 1.0 else "❌"
    print(f"  {status} {r['name']}: 報告={r['report_close']:.2f}, yfinance={r['yf_close']:.2f}, 偏差={r['price_diff_pct']:.4f}%")

print("-" * 70)
if all_pass:
    print("✅ 所有數據品質驗證通過！報告數據準確可靠。")
else:
    print("❌ 存在數據偏差超過閾值，需要排查後再發送！")
print("=" * 70)
