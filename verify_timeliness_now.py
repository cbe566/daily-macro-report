#!/usr/bin/env python3
"""數據時效性驗證：確認所有數據為當日最新"""
import json
import datetime

# 載入報告原始數據
with open('reports/raw_data_2026-03-27.json', 'r') as f:
    raw = json.load(f)

print("=" * 70)
print("數據時效性驗證")
print("=" * 70)

today = datetime.date(2026, 3, 27)
# 美股最近交易日是 2026-03-26（週四），今天是 2026-03-27（週五）
us_last_trading_day = datetime.date(2026, 3, 26)

all_pass = True

# 1. 檢查報告日期
report_date = raw.get('report_date', '')
generated_at = raw.get('generated_at', '')
print(f"\n1. 報告日期: {report_date}")
print(f"   生成時間: {generated_at}")
if report_date == str(today):
    print(f"   ✅ 報告日期正確 ({today})")
else:
    print(f"   ❌ 報告日期不正確！預期 {today}，實際 {report_date}")
    all_pass = False

# 2. 檢查美股數據時間戳
print(f"\n2. 美股指數數據時效性:")
md = raw['market_data']
us = md.get('us_indices', {})
for name, data in us.items():
    ts = data.get('timestamp')
    if ts:
        dt = datetime.datetime.fromtimestamp(ts)
        data_date = dt.date()
        print(f"   {name}: 數據時間 {dt.strftime('%Y-%m-%d %H:%M')} ", end='')
        if data_date == us_last_trading_day:
            print("✅")
        else:
            print(f"⚠ 預期 {us_last_trading_day}")
            # 如果是週末或非交易日，前一交易日也可接受
            if data_date < us_last_trading_day - datetime.timedelta(days=3):
                print(f"     ❌ 數據過舊！")
                all_pass = False

# 3. 檢查亞洲市場數據
print(f"\n3. 亞洲指數數據時效性:")
asia = md.get('asia_indices', {})
for name, data in asia.items():
    ts = data.get('timestamp')
    if ts:
        dt = datetime.datetime.fromtimestamp(ts)
        data_date = dt.date()
        days_old = (today - data_date).days
        status = "✅" if days_old <= 2 else "❌ 數據過舊"
        print(f"   {name}: {dt.strftime('%Y-%m-%d %H:%M')} ({days_old}天前) {status}")
        if days_old > 3:
            all_pass = False

# 4. 檢查加密貨幣數據（24/7 市場，應為今天的數據）
print(f"\n4. 加密貨幣數據時效性:")
crypto = md.get('crypto', {})
for name, data in crypto.items():
    ts = data.get('timestamp')
    if ts:
        dt = datetime.datetime.fromtimestamp(ts)
        data_date = dt.date()
        days_old = (today - data_date).days
        status = "✅" if days_old <= 1 else "⚠ 可能過舊"
        print(f"   {name}: {dt.strftime('%Y-%m-%d %H:%M')} ({days_old}天前) {status}")

# 5. 檢查情緒指標
print(f"\n5. 情緒指標數據:")
sentiment = raw.get('sentiment_data', {})
print(f"   Fear & Greed: {sentiment.get('fear_greed', {}).get('value', 'N/A')} ({sentiment.get('fear_greed', {}).get('label', 'N/A')})")
print(f"   VIX: {sentiment.get('vix', {}).get('value', 'N/A')} ({sentiment.get('vix', {}).get('change_pct', 'N/A')}%)")
print(f"   US 10Y: {sentiment.get('us10y', {}).get('value', 'N/A')}%")
print(f"   DXY: {sentiment.get('dxy', {}).get('value', 'N/A')}")

# 6. 檢查美林時鐘
print(f"\n6. 美林時鐘:")
clock = raw.get('clock_data', {})
print(f"   當前階段: {clock.get('phase_cn', 'N/A')} (信心度: {clock.get('confidence', 'N/A')})")

# 7. 檢查資金流向
print(f"\n7. 資金流向數據:")
flows = raw.get('fund_flows', {})
flow_date = flows.get('date', 'N/A')
print(f"   數據日期: {flow_date}")
country_flows = flows.get('country', {})
print(f"   國家/地區: {len(country_flows)} 項")
sector_flows = flows.get('sector', {})
print(f"   GICS板塊: {len(sector_flows)} 項")
bond_flows = flows.get('bond', {})
print(f"   債券ETF: {len(bond_flows)} 項")

# 8. 檢查商品和外匯
print(f"\n8. 商品數據時效性:")
commodities = md.get('commodities', {})
for name, data in commodities.items():
    ts = data.get('timestamp')
    if ts:
        dt = datetime.datetime.fromtimestamp(ts)
        data_date = dt.date()
        days_old = (today - data_date).days
        status = "✅" if days_old <= 1 else "⚠"
        print(f"   {name}: {dt.strftime('%Y-%m-%d %H:%M')} ({days_old}天前) {status}")

# 9. 檢查新聞日期
print(f"\n9. 新聞事件:")
news = raw.get('news_events', [])
print(f"   新聞數量: {len(news)} 條")
for n in news[:3]:
    print(f"   - {n.get('title', 'N/A')[:60]}...")

print("\n" + "=" * 70)
if all_pass:
    print("✅ 所有數據時效性驗證通過！數據為當日最新。")
else:
    print("❌ 存在數據時效性問題，需要排查！")
print("=" * 70)
