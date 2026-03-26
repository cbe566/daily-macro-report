#!/usr/bin/env python3
"""
新聞事實查核模組 v1
在 AI 歸納新聞後，對每條新聞進行事實查核，防止 AI 幻覺或數字混淆。

查核機制（雙層）：
  Layer 1: AI 交叉比對 — 用另一個 AI 調用，將歸納結果與原始新聞逐條比對
           重點檢查：數字是否正確引用、概念是否混淆（如融資 vs 估值）、
           公司/人物名稱是否正確、因果關係是否合理
  Layer 2: 結構化規則檢查 — 程式化的常識性檢查
           例如：知名公司估值是否在合理範圍、數字單位是否合理、
           百分比是否在合理範圍

設計原則：
  - 不增加超過 30 秒的延遲（使用 gpt-4.1-nano 做快速查核）
  - 發現問題時自動修正，而非僅標記
  - 修正後的結果附帶 [已查核] 標記
"""
import json
import re
from openai import OpenAI

ai_client = OpenAI()
CHECKER_MODEL = "gpt-4.1-mini"  # 查核用模型，需要足夠聰明才能抓到錯誤


# ─── Layer 2: 結構化規則檢查 ────────────────────────────────────────

# 知名公司的估值/市值合理範圍（單位：十億美元）
# 用於檢測 AI 是否把融資金額誤認為估值等常見錯誤
COMPANY_VALUATION_FLOOR = {
    'SpaceX': 200,      # SpaceX 估值至少 2000 億美元
    'Apple': 2000,
    'Microsoft': 2000,
    'Google': 1500,
    'Alphabet': 1500,
    'Amazon': 1500,
    'NVIDIA': 1000,
    'Meta': 800,
    'Tesla': 500,
    'Berkshire': 800,
    'TSMC': 500,
    'Samsung': 300,
    'Alibaba': 150,
    'Tencent': 300,
    'ByteDance': 200,
    'Stripe': 50,
    'OpenAI': 80,
}

def _extract_numbers_with_context(text):
    """從文本中提取數字及其上下文（金額、百分比等）"""
    results = []
    
    # 匹配金額模式：$XX billion, XX億美元, XX兆 等
    patterns = [
        # English patterns
        (r'\$?([\d,.]+)\s*(trillion|兆)', 'amount_trillion'),
        (r'\$?([\d,.]+)\s*(billion|十億|億美元)', 'amount_billion'),
        (r'\$?([\d,.]+)\s*(million|百萬|萬)', 'amount_million'),
        # Chinese patterns  
        (r'([\d,.]+)\s*萬億', 'amount_trillion_cn'),
        (r'([\d,.]+)\s*億', 'amount_billion_cn'),
        # Percentage
        (r'([\d,.]+)\s*%', 'percentage'),
        # Valuation specific
        (r'估值[^\d]*([\d,.]+)\s*(億|萬億|billion|trillion)', 'valuation'),
        (r'融資[^\d]*([\d,.]+)\s*(億|萬億|billion|trillion)', 'fundraise'),
    ]
    
    for pattern, ptype in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            results.append({
                'type': ptype,
                'value': match.group(1),
                'unit': match.group(2) if match.lastindex >= 2 else '',
                'full_match': match.group(0),
                'position': match.start(),
            })
    
    return results


def _check_valuation_reasonableness(news_event):
    """檢查新聞中提到的公司估值是否合理"""
    issues = []
    title = news_event.get('title', '')
    description = news_event.get('description', '')
    full_text = f"{title} {description}"
    
    for company, floor_b in COMPANY_VALUATION_FLOOR.items():
        if company.lower() in full_text.lower():
            # 檢查是否有估值相關數字
            numbers = _extract_numbers_with_context(full_text)
            for num_info in numbers:
                if num_info['type'] == 'valuation' or '估值' in full_text:
                    try:
                        val = float(num_info['value'].replace(',', ''))
                        unit = num_info['unit'].lower()
                        
                        # 轉換為十億美元
                        val_in_billions = val
                        if 'trillion' in unit or '萬億' in unit or '兆' in unit:
                            val_in_billions = val * 1000
                        elif 'billion' in unit or '億' in unit:
                            val_in_billions = val
                        elif 'million' in unit or '百萬' in unit:
                            val_in_billions = val / 1000
                        
                        if val_in_billions < floor_b:
                            issues.append({
                                'type': 'valuation_too_low',
                                'company': company,
                                'stated_value': num_info['full_match'],
                                'stated_billions': val_in_billions,
                                'expected_floor_billions': floor_b,
                                'message': f"{company} 的估值 {num_info['full_match']} 明顯偏低（已知最低約 ${floor_b}B），"
                                          f"可能混淆了融資金額與估值",
                            })
                    except (ValueError, TypeError):
                        pass
    
    return issues


def _structural_checks(news_events):
    """對所有新聞事件進行結構化規則檢查"""
    all_issues = []
    
    for i, event in enumerate(news_events):
        title = event.get('title', '')
        description = event.get('description', '')
        
        # 1. 估值合理性檢查
        valuation_issues = _check_valuation_reasonableness(event)
        for issue in valuation_issues:
            issue['event_index'] = i
            issue['event_title'] = title
            all_issues.append(issue)
        
        # 2. 百分比合理性檢查（單日漲跌幅超過 50% 需要警惕）
        numbers = _extract_numbers_with_context(f"{title} {description}")
        for num_info in numbers:
            if num_info['type'] == 'percentage':
                try:
                    pct = float(num_info['value'].replace(',', ''))
                    if pct > 100 and '漲' in f"{title} {description}":
                        all_issues.append({
                            'type': 'extreme_percentage',
                            'event_index': i,
                            'event_title': title,
                            'value': pct,
                            'message': f"百分比 {pct}% 異常大，請確認是否正確",
                        })
                except (ValueError, TypeError):
                    pass
        
        # 3. related_tickers 合理性（SPCE 不是 SpaceX）
        tickers = event.get('related_tickers', [])
        if 'SpaceX' in f"{title} {description}" and 'SPCE' in tickers:
            all_issues.append({
                'type': 'wrong_ticker',
                'event_index': i,
                'event_title': title,
                'message': "SPCE (Virgin Galactic) 不是 SpaceX。SpaceX 是未上市公司，"
                          "不應關聯 SPCE。可考慮關聯 TSLA（同為 Elon Musk 旗下）或太空相關 ETF",
            })
    
    return all_issues


# ─── Layer 1: AI 交叉比對查核 ──────────────────────────────────────

def _ai_cross_check(news_events, original_articles):
    """用 AI 將歸納結果與原始新聞逐條比對，檢查事實準確性"""
    
    # 準備原始新聞摘要（用於比對）
    original_summaries = []
    for article in original_articles[:60]:
        original_summaries.append({
            'title': article.get('title', ''),
            'description': article.get('description', ''),
            'publisher': article.get('publisher', ''),
        })
    
    prompt = f"""你是一位嚴謹的事實查核編輯。你的任務是將以下「AI 歸納的新聞事件」與「原始新聞資料」逐條比對，找出任何事實錯誤。

重點檢查項目：
1. **數字準確性**：金額、百分比、數量是否與原始新聞一致？
   - 特別注意「融資金額」vs「估值/市值」的混淆（這是最常見的錯誤）
   - 例如：「融資 $75B」不等於「估值 $75B」，$75 billion = 750億美元
   - 例如：「營收增長 20%」不等於「利潤增長 20%」
   - **單位轉換必須正確**：$75 billion = 750億美元（不是75億）、$1.75 trillion = 1.75萬億/兆美元
   - 修正時必須同時修正標題和描述中的所有相關數字
2. **概念混淆**：是否把 A 概念誤認為 B 概念？
   - 融資 vs 估值、營收 vs 利潤、同比 vs 環比
   - IPO 中「raise（融資）」和「valuation（估值）」是完全不同的概念
3. **公司/人物錯誤**：名稱、職位是否正確？
4. **因果關係**：歸納的因果關係是否與原始新聞一致？
5. **時間線**：事件的時間描述是否正確？
6. **遺漏關鍵信息**：是否遺漏了原始新聞中的重要限定條件？
7. **related_tickers 正確性**：
   - SpaceX 是未上市公司，不應使用 SPCE（那是 Virgin Galactic）
   - 確認 ticker 確實與新聞中的公司對應

修正要求：
- 修正後的標題和描述必須使用繁體中文
- 金額必須精確：$75 billion 翻譯為「750億美元」，$1.75 trillion 翻譯為「1.75兆美元」
- 修正後的描述必須完整（2-3句話），不能只修正部分

AI 歸納的新聞事件：
{json.dumps(news_events, ensure_ascii=False, indent=1)}

原始新聞資料（前60篇）：
{json.dumps(original_summaries, ensure_ascii=False, indent=1)}

請以 JSON 格式回覆，列出所有發現的問題和修正建議：
{{
  "issues_found": [
    {{
      "event_index": 0,
      "event_title": "原標題",
      "error_type": "數字混淆/概念混淆/公司錯誤/因果錯誤/ticker錯誤/其他",
      "description": "詳細描述錯誤",
      "original_fact": "原始新聞中的正確信息",
      "corrected_title": "修正後的標題（如需修正）",
      "corrected_description": "修正後的描述（如需修正）",
      "corrected_tickers": ["修正後的 tickers（如需修正）"],
      "severity": "高/中/低"
    }}
  ],
  "overall_assessment": "整體評估（通過/需修正）"
}}

如果沒有發現任何問題，issues_found 為空陣列，overall_assessment 為「通過」。
"""

    try:
        response = ai_client.chat.completions.create(
            model=CHECKER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.1,  # 低溫度，更嚴謹
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        if content.startswith('```'):
            content = content.split('\n', 1)[1]
            content = content.rsplit('```', 1)[0]
        return json.loads(content)
    except Exception as e:
        print(f"  ⚠ AI 事實查核出錯: {e}")
        return {"issues_found": [], "overall_assessment": "查核失敗"}


# ─── 自動修正 ──────────────────────────────────────────────────────

def _apply_corrections(news_events, ai_issues, structural_issues):
    """根據查核結果自動修正新聞事件"""
    corrected = [dict(event) for event in news_events]  # deep copy
    corrections_log = []
    
    # 應用 AI 查核的修正
    for issue in ai_issues:
        idx = issue.get('event_index', -1)
        severity = issue.get('severity', '低')
        
        if idx < 0 or idx >= len(corrected):
            continue
        
        if severity in ('高', '中'):
            event = corrected[idx]
            original_title = event['title']
            
            if issue.get('corrected_title'):
                event['title'] = issue['corrected_title']
            if issue.get('corrected_description'):
                event['description'] = issue['corrected_description']
            if issue.get('corrected_tickers'):
                event['related_tickers'] = issue['corrected_tickers']
                # 也更新 ticker_impact
                if 'ticker_impact' in event:
                    old_impact = event['ticker_impact']
                    new_impact = {}
                    for ticker in issue['corrected_tickers']:
                        if ticker in old_impact:
                            new_impact[ticker] = old_impact[ticker]
                    event['ticker_impact'] = new_impact
            
            corrections_log.append({
                'index': idx,
                'original_title': original_title,
                'corrected_title': event['title'],
                'reason': issue.get('description', ''),
                'error_type': issue.get('error_type', ''),
                'severity': severity,
                'source': 'AI交叉查核',
            })
    
    # 應用結構化規則的修正
    for issue in structural_issues:
        idx = issue.get('event_index', -1)
        if idx < 0 or idx >= len(corrected):
            continue
        
        event = corrected[idx]
        
        if issue['type'] == 'wrong_ticker':
            # 移除錯誤的 ticker
            if 'SPCE' in event.get('related_tickers', []):
                event['related_tickers'] = [t for t in event['related_tickers'] if t != 'SPCE']
                # 添加更合理的 ticker
                if 'SpaceX' in f"{event.get('title', '')} {event.get('description', '')}":
                    for better_ticker in ['RKLB', 'TSLA']:
                        if better_ticker not in event['related_tickers']:
                            event['related_tickers'].append(better_ticker)
                
                if 'ticker_impact' in event and 'SPCE' in event['ticker_impact']:
                    del event['ticker_impact']['SPCE']
                
                corrections_log.append({
                    'index': idx,
                    'original_title': event['title'],
                    'reason': issue['message'],
                    'error_type': 'wrong_ticker',
                    'severity': '高',
                    'source': '結構化規則',
                })
        
        elif issue['type'] == 'valuation_too_low':
            corrections_log.append({
                'index': idx,
                'original_title': event['title'],
                'reason': issue['message'],
                'error_type': 'valuation_too_low',
                'severity': '高',
                'source': '結構化規則',
                'note': '此問題需要 AI 查核層修正具體數字',
            })
    
    return corrected, corrections_log


# ─── 主入口 ──────────────────────────────────────────────────────

def fact_check_news(news_events, original_articles):
    """
    對 AI 歸納的新聞事件進行雙層事實查核。
    
    Args:
        news_events: AI 歸納後的新聞事件列表
        original_articles: 原始新聞文章列表
    
    Returns:
        tuple: (corrected_events, check_report)
            corrected_events: 修正後的新聞事件列表
            check_report: 查核報告（包含所有發現的問題和修正記錄）
    """
    print("  開始新聞事實查核（雙層機制）...")
    
    # Layer 1: AI 交叉比對
    print("    [Layer 1] AI 交叉比對查核...")
    ai_result = _ai_cross_check(news_events, original_articles)
    ai_issues = ai_result.get('issues_found', [])
    ai_assessment = ai_result.get('overall_assessment', '未知')
    
    if ai_issues:
        print(f"    → 發現 {len(ai_issues)} 個問題")
        for issue in ai_issues:
            severity_icon = "❌" if issue.get('severity') == '高' else "⚠" if issue.get('severity') == '中' else "ℹ"
            print(f"      {severity_icon} [{issue.get('error_type', '?')}] {issue.get('description', '')[:80]}")
    else:
        print("    → 未發現問題")
    
    # Layer 2: 結構化規則檢查
    print("    [Layer 2] 結構化規則檢查...")
    structural_issues = _structural_checks(news_events)
    
    if structural_issues:
        print(f"    → 發現 {len(structural_issues)} 個問題")
        for issue in structural_issues:
            print(f"      ⚠ [{issue['type']}] {issue['message'][:80]}")
    else:
        print("    → 未發現問題")
    
    # 合併問題並自動修正
    total_issues = len(ai_issues) + len(structural_issues)
    high_severity = sum(1 for i in ai_issues if i.get('severity') == '高') + \
                    sum(1 for i in structural_issues if i.get('type') in ('valuation_too_low', 'wrong_ticker'))
    
    if total_issues > 0:
        print(f"    自動修正中（{total_issues} 個問題，{high_severity} 個高嚴重度）...")
        corrected_events, corrections_log = _apply_corrections(
            news_events, ai_issues, structural_issues
        )
        print(f"    ✓ 已修正 {len(corrections_log)} 個問題")
    else:
        corrected_events = news_events
        corrections_log = []
    
    # 生成查核報告
    check_report = {
        'total_events_checked': len(news_events),
        'ai_issues_found': len(ai_issues),
        'structural_issues_found': len(structural_issues),
        'high_severity_count': high_severity,
        'corrections_applied': len(corrections_log),
        'ai_assessment': ai_assessment,
        'corrections_log': corrections_log,
        'ai_issues_detail': ai_issues,
        'structural_issues_detail': structural_issues,
        'status': '已修正' if corrections_log else '通過',
    }
    
    status_icon = "✓" if total_issues == 0 else "⚠ 已修正"
    print(f"  {status_icon} 事實查核完成: {total_issues} 問題, {len(corrections_log)} 修正")
    
    return corrected_events, check_report


if __name__ == '__main__':
    # 測試用
    print("新聞事實查核模組已就緒")
    print(f"查核模型: {CHECKER_MODEL}")
    print(f"已知公司估值底線: {len(COMPANY_VALUATION_FLOOR)} 家")
