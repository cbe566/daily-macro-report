"""
完整數據交叉驗證腳本
從當日 raw_data JSON 動態讀取數據，用 yfinance 交叉驗證
"""
import yfinance as yf
import json
import os
import glob
import datetime

os.environ['TZ'] = 'Asia/Taipei'

# 自動找到最新的 raw_data JSON
json_files = sorted(glob.glob('reports/raw_data_*.json'))
if not json_files:
    print("ERROR: 找不到 raw_data JSON 文件")
    exit(1)

json_path = json_files[-1]
print(f"驗證文件: {json_path}")

with open(json_path, 'r') as f:
    data = json.load(f)

md = data['market_data']
report_date = data.get('report_date', 'unknown')
print(f"報告日期: {report_date}")
print()

errors = []
warnings = []

# ========== 1. 指數驗證 ==========
print("=" * 80)
print("1. 指數驗證（亞洲 + 歐洲 + 美國）")
print("=" * 80)

for category in ['asia_indices', 'europe_indices', 'us_indices', 'emerging_indices']:
    cat_data = md.get(category, {})
    for name, info in cat_data.items():
        symbol = info['symbol']
        pdf_close = info['current']
        pdf_pct = info['change_pct']
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d")
            if len(hist) < 2:
                warnings.append(f"  ⚠️ {name} ({symbol}): 數據不足")
                continue
            latest = hist.iloc[-1]
            prev = hist.iloc[-2]
            yf_close = latest['Close']
            yf_pct = ((yf_close - prev['Close']) / prev['Close']) * 100

            close_diff_pct = abs(yf_close - pdf_close) / pdf_close * 100 if pdf_close else 0
            pct_diff = abs(yf_pct - pdf_pct)

            status = "✅" if close_diff_pct < 1.0 and pct_diff < 0.5 else "❌"
            if status == "❌":
                errors.append(f"  {name} ({symbol}): PDF={pdf_close} ({pdf_pct:+.2f}%) vs YF={yf_close:.2f} ({yf_pct:+.2f}%)")

            date_str = str(latest.name.date()) if hasattr(latest.name, 'date') else str(latest.name)[:10]
            print(f"  {status} {name}: PDF={pdf_close} ({pdf_pct:+.2f}%) | YF={yf_close:.2f} ({yf_pct:+.2f}%) | Date={date_str} | Δ={close_diff_pct:.3f}%")
        except Exception as e:
            warnings.append(f"  ⚠️ {name} ({symbol}): {e}")

# ========== 2. 商品驗證 ==========
print("\n" + "=" * 80)
print("2. 商品驗證")
print("=" * 80)

for name, info in md.get('commodities', {}).items():
    symbol = info['symbol']
    pdf_price = info['current']
    pdf_pct = info['change_pct']
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="5d")
        if len(hist) < 2:
            warnings.append(f"  ⚠️ {name} ({symbol}): 數據不足")
            continue
        latest = hist.iloc[-1]
        prev = hist.iloc[-2]
        yf_close = latest['Close']
        yf_pct = ((yf_close - prev['Close']) / prev['Close']) * 100

        close_diff_pct = abs(yf_close - pdf_price) / pdf_price * 100 if pdf_price else 0
        pct_diff = abs(yf_pct - pdf_pct)

        status = "✅" if close_diff_pct < 1.0 and pct_diff < 0.5 else "❌"
        if status == "❌":
            errors.append(f"  {name}: PDF=${pdf_price} ({pdf_pct:+.2f}%) vs YF=${yf_close:.2f} ({yf_pct:+.2f}%)")

        date_str = str(latest.name.date()) if hasattr(latest.name, 'date') else str(latest.name)[:10]
        print(f"  {status} {name}: PDF=${pdf_price} ({pdf_pct:+.2f}%) | YF=${yf_close:.2f} ({yf_pct:+.2f}%) | Date={date_str} | Δ={close_diff_pct:.3f}%")
    except Exception as e:
        warnings.append(f"  ⚠️ {name} ({symbol}): {e}")

# ========== 3. 外匯驗證 ==========
print("\n" + "=" * 80)
print("3. 外匯驗證")
print("=" * 80)

for name, info in md.get('forex', {}).items():
    symbol = info['symbol']
    pdf_rate = info['current']
    pdf_pct = info['change_pct']
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="5d")
        if len(hist) < 2:
            warnings.append(f"  ⚠️ {name} ({symbol}): 數據不足")
            continue
        latest = hist.iloc[-1]
        prev = hist.iloc[-2]
        yf_close = latest['Close']
        yf_pct = ((yf_close - prev['Close']) / prev['Close']) * 100

        close_diff_pct = abs(yf_close - pdf_rate) / pdf_rate * 100 if pdf_rate else 0
        pct_diff = abs(yf_pct - pdf_pct)

        status = "✅" if close_diff_pct < 0.5 and pct_diff < 0.5 else "❌"
        if status == "❌":
            errors.append(f"  {name}: PDF={pdf_rate} ({pdf_pct:+.2f}%) vs YF={yf_close:.4f} ({yf_pct:+.2f}%)")

        date_str = str(latest.name.date()) if hasattr(latest.name, 'date') else str(latest.name)[:10]
        print(f"  {status} {name}: PDF={pdf_rate} ({pdf_pct:+.2f}%) | YF={yf_close:.4f} ({yf_pct:+.2f}%) | Date={date_str} | Δ={close_diff_pct:.3f}%")
    except Exception as e:
        warnings.append(f"  ⚠️ {name} ({symbol}): {e}")

# ========== 4. 加密貨幣驗證 ==========
print("\n" + "=" * 80)
print("4. 加密貨幣驗證")
print("=" * 80)

for name, info in md.get('crypto', {}).items():
    symbol = info['symbol']
    pdf_price = info['current']
    pdf_pct = info['change_pct']
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="5d")
        if len(hist) < 2:
            warnings.append(f"  ⚠️ {name} ({symbol}): 數據不足")
            continue
        latest = hist.iloc[-1]
        prev = hist.iloc[-2]
        yf_close = latest['Close']
        yf_pct = ((yf_close - prev['Close']) / prev['Close']) * 100

        close_diff_pct = abs(yf_close - pdf_price) / pdf_price * 100 if pdf_price else 0
        pct_diff = abs(yf_pct - pdf_pct)

        # 加密貨幣24/7交易，容許稍大偏差
        status = "✅" if close_diff_pct < 3.0 and pct_diff < 3.0 else "❌"
        if status == "❌":
            errors.append(f"  {name}: PDF=${pdf_price} ({pdf_pct:+.2f}%) vs YF=${yf_close:.2f} ({yf_pct:+.2f}%)")

        date_str = str(latest.name.date()) if hasattr(latest.name, 'date') else str(latest.name)[:10]
        print(f"  {status} {name}: PDF=${pdf_price} ({pdf_pct:+.2f}%) | YF=${yf_close:.2f} ({yf_pct:+.2f}%) | Date={date_str} | Δ={close_diff_pct:.3f}%")
    except Exception as e:
        warnings.append(f"  ⚠️ {name} ({symbol}): {e}")

# ========== 5. 熱門股票抽樣驗證 ==========
print("\n" + "=" * 80)
print("5. 熱門股票抽樣驗證")
print("=" * 80)

hs = data.get('hot_stocks', {})
sample_count = 0
for market in ['美股', '台股', '港股']:
    market_data = hs.get(market, {})
    for cat in ['buy', 'sell']:
        for item in market_data.get(cat, [])[:2]:  # 每類取前2支
            symbol = item['symbol']
            pdf_close = item['close']
            pdf_pct = item['change_pct']
            try:
                t = yf.Ticker(symbol)
                hist = t.history(period="5d")
                if len(hist) < 2:
                    warnings.append(f"  ⚠️ {item.get('name','')} ({symbol}): 數據不足")
                    continue
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]
                yf_close = latest['Close']
                yf_pct = ((yf_close - prev['Close']) / prev['Close']) * 100

                close_diff_pct = abs(yf_close - pdf_close) / pdf_close * 100 if pdf_close else 0
                pct_diff = abs(yf_pct - pdf_pct)

                status = "✅" if close_diff_pct < 1.0 and pct_diff < 0.5 else "❌"
                if status == "❌":
                    errors.append(f"  {item.get('name','')} ({symbol}): PDF={pdf_close} ({pdf_pct:+.2f}%) vs YF={yf_close:.2f} ({yf_pct:+.2f}%)")

                date_str = str(latest.name.date()) if hasattr(latest.name, 'date') else str(latest.name)[:10]
                print(f"  {status} [{market}-{cat}] {item.get('name','')} ({symbol}): PDF={pdf_close} ({pdf_pct:+.2f}%) | YF={yf_close:.2f} ({yf_pct:+.2f}%) | Date={date_str} | Δ={close_diff_pct:.3f}%")
                sample_count += 1
            except Exception as e:
                warnings.append(f"  ⚠️ {item.get('name','')} ({symbol}): {e}")

# ========== 總結 ==========
print("\n" + "=" * 80)
print("驗證總結")
print("=" * 80)

if errors:
    print(f"\n❌ 發現 {len(errors)} 個數據偏差：")
    for e in errors:
        print(e)
else:
    print("\n✅ 所有數據點驗證通過，無重大偏差")

if warnings:
    print(f"\n⚠️ {len(warnings)} 個警告：")
    for w in warnings:
        print(w)

print(f"\n驗證完成時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
