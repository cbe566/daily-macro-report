#!/usr/bin/env python3
"""
測試新聞事實查核模組
使用今天報告的真實數據來驗證查核機制能否抓到 SpaceX 的錯誤
"""
import json
import sys
import os

os.environ['TZ'] = 'Asia/Taipei'
sys.path.insert(0, '.')

from modules.news_fact_checker import fact_check_news, _structural_checks

# 載入今天的原始數據
with open('reports/raw_data_2026-03-26.json', 'r') as f:
    data = json.load(f)

# 取得 AI 歸納的新聞事件（含錯誤的版本）
news_events = data.get('news_events', [])

print("=" * 70)
print("測試新聞事實查核模組")
print("=" * 70)
print(f"\n待查核新聞事件: {len(news_events)} 條")
for i, event in enumerate(news_events):
    print(f"  [{i}] {event['title']}")

print()

# 先單獨測試 Layer 2（結構化規則）
print("--- 單獨測試 Layer 2: 結構化規則 ---")
structural_issues = _structural_checks(news_events)
if structural_issues:
    print(f"  發現 {len(structural_issues)} 個問題:")
    for issue in structural_issues:
        print(f"    [{issue['type']}] {issue['message']}")
else:
    print("  未發現問題")

print()

# 需要原始新聞文章來做 AI 交叉比對
# 由於原始文章沒有保存在 raw_data 中，我們需要重新收集
# 但為了測試，我們可以用模擬的原始新聞（包含正確信息）
print("--- 測試完整雙層查核（Layer 1 + Layer 2）---")

# 模擬原始新聞（包含 SpaceX 的正確信息）
mock_articles = [
    {
        'title': 'SpaceX aims to file for IPO as soon as this week, could raise over $75 billion',
        'description': 'SpaceX is preparing to file for an IPO that could raise more than $75 billion, seeking a valuation of about $1.75 trillion. The Elon Musk-led company recently merged with xAI.',
        'publisher': 'Reuters',
        'tickers': [],
    },
    {
        'title': 'SpaceX Weighs $75 Billion IPO Target, Far Exceeding Previous Plans',
        'description': 'SpaceX could seek a valuation in the IPO of more than $1.75 trillion. Advisers involved in the preparation expect the company could attempt to raise more than $75 billion.',
        'publisher': 'Bloomberg',
        'tickers': [],
    },
    {
        'title': 'Space stocks rally on reports of SpaceX imminent IPO filing',
        'description': 'SpaceX could raise over $75 billion in what would be the biggest IPO ever, seeking a $1.75 trillion valuation.',
        'publisher': 'CNBC',
        'tickers': ['RKLB', 'ASTS'],
    },
]

# 執行完整查核
corrected_events, check_report = fact_check_news(news_events, mock_articles)

print("\n" + "=" * 70)
print("查核報告")
print("=" * 70)
print(f"  狀態: {check_report['status']}")
print(f"  AI 問題: {check_report['ai_issues_found']}")
print(f"  規則問題: {check_report['structural_issues_found']}")
print(f"  高嚴重度: {check_report['high_severity_count']}")
print(f"  已修正: {check_report['corrections_applied']}")

if check_report['corrections_log']:
    print("\n修正記錄:")
    for corr in check_report['corrections_log']:
        print(f"  [{corr['source']}] [{corr['error_type']}] ({corr['severity']})")
        print(f"    原標題: {corr['original_title']}")
        if corr.get('corrected_title'):
            print(f"    修正為: {corr['corrected_title']}")
        print(f"    原因: {corr['reason']}")

# 比較修正前後
print("\n" + "=" * 70)
print("修正前後對比")
print("=" * 70)
for i in range(len(news_events)):
    orig = news_events[i]
    fixed = corrected_events[i]
    if orig['title'] != fixed['title'] or orig['description'] != fixed['description']:
        print(f"\n  事件 [{i}]:")
        print(f"    原標題: {orig['title']}")
        print(f"    新標題: {fixed['title']}")
        if orig['description'] != fixed['description']:
            print(f"    原描述: {orig['description'][:100]}...")
            print(f"    新描述: {fixed['description'][:100]}...")
    if orig.get('related_tickers') != fixed.get('related_tickers'):
        print(f"  事件 [{i}] Tickers 修正:")
        print(f"    原: {orig.get('related_tickers')}")
        print(f"    新: {fixed.get('related_tickers')}")

print("\n測試完成！")
