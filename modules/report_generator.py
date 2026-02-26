#!/usr/bin/env python3
"""
報告生成引擎 v2
參考 Saxo Bank Market Quick Take 專業排版風格
整合所有數據模組和AI分析，生成綜合早報
"""
import json
from datetime import datetime, timedelta


def format_change(change_pct):
    """格式化漲跌幅顯示"""
    if change_pct > 0:
        return f"+{change_pct:.2f}%"
    elif change_pct < 0:
        return f"{change_pct:.2f}%"
    else:
        return f"{change_pct:.2f}%"


def format_number(num):
    """格式化數字"""
    if num is None:
        return "N/A"
    if abs(num) >= 1e9:
        return f"{num/1e9:.2f}B"
    elif abs(num) >= 1e6:
        return f"{num/1e6:.2f}M"
    elif abs(num) >= 1e3:
        return f"{num/1e3:.1f}K"
    else:
        return f"{num:,.2f}"


def get_trend_icon(change_pct):
    """根據漲跌幅返回趨勢圖標"""
    if change_pct > 1.5:
        return "📈"
    elif change_pct > 0:
        return "🟢"
    elif change_pct > -1.5:
        return "🔴"
    else:
        return "📉"


# ==================== 市場速覽區塊 ====================

def generate_market_snapshot(market_data, news_events, hot_stocks, index_analysis):
    """生成市場速覽摘要（報告開頭一目了然的區塊）"""
    md = "## 市場速覽\n\n"

    # 股市
    asia = market_data.get('asia_indices', {})
    europe = market_data.get('europe_indices', {})
    us = market_data.get('us_indices', {})

    # 找出各區域代表性指數
    asia_summary = _get_region_summary(asia, ['日經225', '恆生指數', '台灣加權'])
    europe_summary = _get_region_summary(europe, ['英國FTSE', '德國DAX', '法國CAC'])
    us_summary = _get_region_summary(us, ['S&P 500', '納斯達克', '道瓊工業'])

    md += f"> **股市**：{us_summary}；亞洲方面{asia_summary}；歐洲{europe_summary}\n>\n"

    # 商品
    commodities = market_data.get('commodities', {})
    comm_parts = []
    for name, data in commodities.items():
        icon = get_trend_icon(data['change_pct'])
        comm_parts.append(f"{name} {icon} {data['change_pct']:+.2f}%")
    if comm_parts:
        md += f"> **商品**：{' | '.join(comm_parts[:4])}\n>\n"

    # 外匯
    forex = market_data.get('forex', {})
    fx_parts = []
    for name, data in forex.items():
        fx_parts.append(f"{name} {data['current']:.4f}（{data['change_pct']:+.2f}%）")
    if fx_parts:
        md += f"> **外匯**：{' | '.join(fx_parts[:3])}\n>\n"

    # 加密貨幣
    crypto = market_data.get('crypto', {})
    if crypto:
        btc = crypto.get('Bitcoin', {})
        eth = crypto.get('Ethereum', {})
        crypto_str = ""
        if btc:
            crypto_str += f"BTC ${btc.get('current', 0):,.0f}（{btc.get('change_pct', 0):+.2f}%）"
        if eth:
            crypto_str += f" | ETH ${eth.get('current', 0):,.0f}（{eth.get('change_pct', 0):+.2f}%）"
        if crypto_str:
            md += f"> **加密貨幣**：{crypto_str}\n>\n"

    # 宏觀事件摘要
    if news_events:
        top_event = news_events[0].get('title', '') if news_events else ''
        md += f"> **焦點事件**：{top_event}\n"

    md += "\n---\n\n"
    return md


def _get_region_summary(indices, priority_names):
    """生成區域指數摘要文字"""
    parts = []
    for name in priority_names:
        if name in indices:
            data = indices[name]
            icon = get_trend_icon(data['change_pct'])
            parts.append(f"{name} {icon} {data['change_pct']:+.2f}%")
    if not parts:
        # 取前兩個
        for name, data in list(indices.items())[:2]:
            icon = get_trend_icon(data['change_pct'])
            parts.append(f"{name} {icon} {data['change_pct']:+.2f}%")
    return '，'.join(parts) if parts else '暫無數據'


# ==================== 指數表格 ====================

def generate_indices_section(market_data, index_analysis):
    """生成各國指數表現章節"""
    md = "## 一、各國指數表現\n\n"

    # 亞洲市場
    asia = market_data.get('asia_indices', {})
    if asia:
        md += "### 亞洲市場\n\n"
        if index_analysis and 'asia_analysis' in index_analysis:
            md += f"{index_analysis['asia_analysis']}\n\n"
        md += _generate_index_table(asia)

    # 歐洲市場
    europe = market_data.get('europe_indices', {})
    if europe:
        md += "### 歐洲市場\n\n"
        if index_analysis and 'europe_analysis' in index_analysis:
            md += f"{index_analysis['europe_analysis']}\n\n"
        md += _generate_index_table(europe)

    # 美國市場
    us = market_data.get('us_indices', {})
    if us:
        md += "### 美國市場\n\n"
        if index_analysis and 'us_analysis' in index_analysis:
            md += f"{index_analysis['us_analysis']}\n\n"
        md += _generate_index_table(us)

    md += "---\n\n"
    return md


def _generate_index_table(indices_data):
    """生成單個區域的指數表格"""
    if not indices_data:
        return ""

    md = "| 指數 | 收盤價 | 漲跌 | 漲跌幅 | 趨勢 |\n"
    md += "|:-----|-------:|------:|-------:|:----:|\n"

    sorted_items = sorted(indices_data.items(), key=lambda x: x[1]['change_pct'], reverse=True)

    for name, data in sorted_items:
        trend = get_trend_icon(data['change_pct'])
        md += f"| **{name}** | {data['current']:,.2f} | {data['change']:+,.2f} | {data['change_pct']:+.2f}% | {trend} |\n"

    md += "\n"
    return md


# ==================== 宏觀新聞 ====================

def generate_news_section(events):
    """生成宏觀重點新聞章節"""
    if not events:
        return ""

    md = "## 二、宏觀重點新聞\n\n"

    for i, event in enumerate(events, 1):
        impact = event.get('impact_level', '中')
        if impact == '高':
            impact_badge = "🔴 高影響"
        elif impact == '中':
            impact_badge = "🟡 中影響"
        else:
            impact_badge = "🟢 低影響"

        direction = event.get('market_direction', '中性')
        if direction == '利多':
            dir_badge = "📈 利多"
        elif direction == '利空':
            dir_badge = "📉 利空"
        else:
            dir_badge = "➡️ 中性"

        affected = event.get('affected_markets', '')

        md += f"### {i}. {event.get('title', '')}\n\n"
        md += f"> {impact_badge} ｜ {dir_badge} ｜ 影響範圍：{affected}\n\n"
        md += f"{event.get('description', '')}\n\n"

        tickers = event.get('related_tickers', [])
        ticker_impact = event.get('ticker_impact', {})
        if tickers:
            if ticker_impact:
                # 顯示每個標的的具體影響方向
                impact_parts = []
                for t in tickers:
                    impact_desc = ticker_impact.get(t, '')
                    if impact_desc:
                        impact_parts.append(f"`{t}` {impact_desc}")
                    else:
                        impact_parts.append(f"`{t}`")
                md += f"**相關標的影響**：{'；'.join(impact_parts)}\n\n"
            else:
                md += f"**相關標的**：`{'`、`'.join(tickers)}`\n\n"

    md += "---\n\n"
    return md


# ==================== 商品、外匯、債券 ====================

def generate_commodities_forex_bonds_section(market_data):
    """生成商品、外匯與債券章節"""
    md = "## 三、商品、外匯與債券\n\n"

    # 大宗商品
    commodities = market_data.get('commodities', {})
    if commodities:
        md += "### 大宗商品\n\n"
        md += "| 商品 | 價格 | 漲跌 | 漲跌幅 | 趨勢 |\n"
        md += "|:-----|-----:|------:|-------:|:----:|\n"
        for name, data in commodities.items():
            trend = get_trend_icon(data['change_pct'])
            md += f"| **{name}** | ${data['current']:,.2f} | {data['change']:+,.2f} | {data['change_pct']:+.2f}% | {trend} |\n"
        md += "\n"

    # 外匯
    forex = market_data.get('forex', {})
    if forex:
        md += "### 外匯市場\n\n"
        md += "| 貨幣對 | 匯率 | 漲跌 | 漲跌幅 | 趨勢 |\n"
        md += "|:-------|-----:|------:|-------:|:----:|\n"
        for name, data in forex.items():
            trend = get_trend_icon(data['change_pct'])
            md += f"| **{name}** | {data['current']:.4f} | {data['change']:+.4f} | {data['change_pct']:+.2f}% | {trend} |\n"
        md += "\n"

    # 債券
    bonds = market_data.get('bonds', {})
    if bonds:
        md += "### 債券殖利率\n\n"
        md += "| 債券 | 殖利率 | 變動 | 變動幅度 | 趨勢 |\n"
        md += "|:-----|-------:|-----:|--------:|:----:|\n"
        for name, data in bonds.items():
            trend = get_trend_icon(data['change_pct'])
            md += f"| **{name}** | {data['current']:.3f}% | {data['change']:+.3f} | {data['change_pct']:+.2f}% | {trend} |\n"
        md += "\n"

    md += "---\n\n"
    return md


# ==================== 熱門股票 ====================

def _render_stock_table(stocks, stock_analysis):
    """渲染一組股票的表格"""
    if not stocks:
        return ""
    md = "| 股票 | 代碼 | 收盤價 | 漲跌幅 | 量比 | 分析 |\n"
    md += "|:-----|:-----|-------:|-------:|-----:|:-----|\n"
    for s in stocks:
        trend = get_trend_icon(s['change_pct'])
        full_symbol = s['symbol']
        symbol_base = full_symbol.split('.')[0]
        analysis = ""
        if stock_analysis:
            analysis = stock_analysis.get(full_symbol, stock_analysis.get(symbol_base, ''))
        name = s['name']
        if len(name) > 40:
            name = name[:38] + "..."
        md += f"| {trend} **{name}** | `{s['symbol']}` | {s['current']:,.2f} | {s['change_pct']:+.2f}% | {s.get('volume_ratio', 1):.1f}x | {analysis} |\n"
    md += "\n"
    return md


def _extract_stocks_from_market(market_data):
    """從 v2 格式的 market_data 中提取 inflow 和 outflow 列表"""
    if isinstance(market_data, dict) and 'inflow' in market_data:
        # v2 格式: {'inflow': [...], 'outflow': [...]}
        return market_data.get('inflow', []), market_data.get('outflow', [])
    elif isinstance(market_data, list):
        # v1 向後兼容: flat list with 'flow' field
        inflow = [s for s in market_data if s.get('flow') == 'inflow']
        outflow = [s for s in market_data if s.get('flow') == 'outflow']
        return inflow, outflow
    return [], []


def generate_hot_stocks_section(hot_stocks, stock_analysis):
    """生成當日熱門股票章節：分區顯示資金追捧 vs 資金出清"""
    md = "## 四、當日熱門股票\n\n"
    md += "> 篩選邏輯：資金追捧（量比 ≥ 1.5x + 上漲）；資金出清（量比 ≥ 2.5x + 下跌）\n>\n"
    md += "> 排序方式：量比門檻（硬篩）→ 漲跌幅排序 → 新聞提及加分\n>\n"
    md += "> 每市場最多顯示 5 支買入 + 5 支賣出\n\n"

    for market in ['美股', '港股', '日股', '台股']:
        if market not in hot_stocks or not hot_stocks[market]:
            continue

        inflow, outflow = _extract_stocks_from_market(hot_stocks[market])

        if not inflow and not outflow:
            continue

        md += f"### {market}\n\n"

        if inflow:
            md += f"🔥 **資金追捧**（買入放量 ≥ 1.5x + 上漲）\n\n"
            md += _render_stock_table(inflow, stock_analysis)

        if outflow:
            md += f"⚠️ **資金出清**（賣出放量 ≥ 2.5x + 下跌）\n\n"
            md += _render_stock_table(outflow, stock_analysis)

        if not inflow and not outflow:
            md += "_（今日無符合條件的股票）_\n\n"

    md += "---\n\n"
    return md


# ==================== 加密貨幣 ====================

def generate_crypto_section(crypto_data):
    """生成加密貨幣市場章節"""
    if not crypto_data:
        return ""

    md = "## 五、加密貨幣市場\n\n"
    md += "| 幣種 | 價格（USD） | 24h 漲跌 | 漲跌幅 | 趨勢 |\n"
    md += "|:-----|----------:|--------:|-------:|:----:|\n"

    sorted_items = sorted(crypto_data.items(), key=lambda x: x[1]['change_pct'], reverse=True)

    for name, data in sorted_items:
        trend = get_trend_icon(data['change_pct'])
        md += f"| **{name}** | ${data['current']:,.2f} | {data['change']:+,.2f} | {data['change_pct']:+.2f}% | {trend} |\n"

    md += "\n---\n\n"
    return md


# ==================== 經濟日曆 ====================

def generate_calendar_section(calendar_events):
    """生成經濟日曆提示章節"""
    md = "## 六、本週經濟日曆\n\n"

    if not calendar_events:
        md += "本週暫無重大經濟數據發布。\n\n"
        return md

    md += "> 以下為本週需要關注的重要經濟數據與事件\n\n"
    md += "| 日期 | 國家/地區 | 事件 | 重要性 | 預期影響 |\n"
    md += "|:-----|:---------|:-----|:------:|:--------|\n"

    for event in calendar_events:
        importance = event.get('importance', '★')
        md += f"| {event.get('date', '')} | {event.get('country', '')} | **{event.get('event', '')}** | {importance} | {event.get('description', '')[:80]} |\n"

    md += "\n"

    # 重點關注事件詳述
    high_importance = [e for e in calendar_events if '★★★' in e.get('importance', '')]
    if high_importance:
        md += "### 重點關注\n\n"
        for event in high_importance:
            md += f"**{event.get('event', '')}**（{event.get('country', '')}，{event.get('date', '')}）— "
            md += f"{event.get('description', '')}"
            if event.get('consensus'):
                md += f"　市場預期：{event['consensus']}"
            md += "\n\n"

    md += "---\n\n"
    return md


# ==================== 休市提醒區塊 ====================

def _generate_holiday_section(holiday_alerts):
    """生成休市提醒 Markdown 區塊"""
    md = ""
    today_closed = holiday_alerts.get('today_closed', [])
    tomorrow_closed = holiday_alerts.get('tomorrow_closed', [])
    upcoming = holiday_alerts.get('upcoming_holidays', [])

    if not (today_closed or tomorrow_closed or upcoming):
        return md

    md += "## \u26a0\ufe0f \u5e02\u5834\u4f11\u5e02\u63d0\u9192\n\n"

    if today_closed:
        names = [a['name_zh'] if isinstance(a, dict) else a for a in today_closed]
        joined = '\u3001'.join(names)
        md += "> **\u4eca\u65e5\u4f11\u5e02**\uff1a" + joined + "\uff08\u6578\u64da\u70ba\u524d\u4e00\u4ea4\u6613\u65e5\u6536\u76e4\uff09\n\n"

    if tomorrow_closed:
        names = [a['name_zh'] if isinstance(a, dict) else a for a in tomorrow_closed]
        joined = '\u3001'.join(names)
        next_biz = holiday_alerts.get('next_business_day', '')
        if hasattr(next_biz, 'strftime'):
            date_str = next_biz.strftime('%m/%d')
        else:
            date_str = str(next_biz)
        md += "> **\u660e\u65e5\u4f11\u5e02\u63d0\u9192**\uff1a" + joined + "\uff08" + date_str + "\uff09\n\n"

    if upcoming:
        md += "| \u65e5\u671f | \u661f\u671f | \u4f11\u5e02\u5e02\u5834 |\n"
        md += "|------|------|----------|\n"
        for h in upcoming:
            if isinstance(h, dict):
                date_val = h.get('date', '')
                if hasattr(date_val, 'strftime'):
                    date_str = date_val.strftime('%m/%d')
                else:
                    date_str = str(date_val)
                    if '-' in date_str:
                        parts = date_str.split('-')
                        date_str = parts[1] + "/" + parts[2]
                weekday = h.get('weekday', '')
                market_names = h.get('market_names', h.get('markets', []))
                if isinstance(market_names, list):
                    mkt_str = '\u3001'.join(market_names)
                else:
                    mkt_str = str(market_names)
                md += "| " + date_str + " | \u9031" + weekday + " | " + mkt_str + " |\n"
        md += "\n"

    md += "---\n\n"
    return md


# ==================== \u7d9c\u5408\u65e9\u5831\u4e3b\u51fd\u6578 ====================

def generate_daily_report(market_data, news_events, hot_stocks, stock_analysis,
                          index_analysis, calendar_events, report_date,
                          holiday_alerts=None):
    """生成每日宏觀資訊綜合早報"""

    # 標題區
    md = "# 每日宏觀資訊綜合早報\n\n"
    md += f"**{report_date}** ｜ 綜合早報\n\n"

    # 休市提醒（如有）
    if holiday_alerts and holiday_alerts.get('has_alerts'):
        md += _generate_holiday_section(holiday_alerts)

    # 市場速覽（開頭一目了然）
    md += generate_market_snapshot(market_data, news_events, hot_stocks, index_analysis)

    # 一、各國指數表現
    md += generate_indices_section(market_data, index_analysis)

    # 二、宏觀重點新聞
    md += generate_news_section(news_events)

    # 三、商品、外匯與債券
    md += generate_commodities_forex_bonds_section(market_data)

    # 四、當日熱門股票
    md += generate_hot_stocks_section(hot_stocks, stock_analysis)

    # 五、加密貨幣市場
    md += generate_crypto_section(market_data.get('crypto', {}))

    # 六、經濟日曆提示
    md += generate_calendar_section(calendar_events)

    # 底部資料來源
    md += f"*報告生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M')} (UTC+8)*\n\n"
    md += "**資料來源**：Yahoo Finance、Polygon.io、S&P Global、CNBC、Investing.com\n"

    return md


# ==================== 保留分盤報告（簡化版） ====================

def generate_asia_report(market_data, news_events, hot_stocks, stock_analysis, index_analysis, report_date):
    """生成亞洲盤報告"""
    md = f"# 亞洲盤市場報告 ｜ {report_date}\n\n---\n\n"

    if index_analysis and 'asia_analysis' in index_analysis:
        md += f"> {index_analysis['asia_analysis']}\n\n---\n\n"

    asia_events = [e for e in news_events if any(kw in e.get('affected_markets', '').lower()
                   for kw in ['亞洲', '日本', '中國', '台灣', '韓國', '全球', '香港'])]
    if asia_events:
        md += "## 宏觀重點新聞（亞洲相關）\n\n"
        for i, event in enumerate(asia_events[:5], 1):
            impact = event.get('impact_level', '中')
            icon = "🔴" if impact == '高' else ("🟡" if impact == '中' else "🟢")
            md += f"**{icon} {event.get('title', '')}** — {event.get('description', '')}\n\n"
        md += "---\n\n"

    asia = market_data.get('asia_indices', {})
    if asia:
        md += "## 亞洲指數表現\n\n"
        md += _generate_index_table(asia)

    for market in ['日股', '台股', '港股']:
        if market in hot_stocks and hot_stocks[market]:
            inflow, outflow = _extract_stocks_from_market(hot_stocks[market])
            if inflow:
                md += f"### {market} — 資金追捧\n\n"
                md += "| 股票 | 代碼 | 收盤價 | 漲跌幅 | 量比 |\n"
                md += "|:-----|:-----|-------:|-------:|-----:|\n"
                for s in inflow:
                    trend = get_trend_icon(s['change_pct'])
                    md += f"| {trend} **{s['name'][:28]}** | `{s['symbol']}` | {s['current']:,.2f} | {s['change_pct']:+.2f}% | {s.get('volume_ratio', 1):.1f}x |\n"
                md += "\n"
            if outflow:
                md += f"### {market} — 資金出清\n\n"
                md += "| 股票 | 代碼 | 收盤價 | 漲跌幅 | 量比 |\n"
                md += "|:-----|:-----|-------:|-------:|-----:|\n"
                for s in outflow:
                    trend = get_trend_icon(s['change_pct'])
                    md += f"| {trend} **{s['name'][:28]}** | `{s['symbol']}` | {s['current']:,.2f} | {s['change_pct']:+.2f}% | {s.get('volume_ratio', 1):.1f}x |\n"
                md += "\n"

    md += "---\n\n**資料來源**：Yahoo Finance、Polygon.io、S&P Global、CNBC、Investing.com\n"
    return md


def generate_europe_report(market_data, news_events, hot_stocks, stock_analysis, index_analysis, report_date):
    """生成歐洲盤報告"""
    md = f"# 歐洲盤市場報告 ｜ {report_date}\n\n---\n\n"

    if index_analysis and 'europe_analysis' in index_analysis:
        md += f"> {index_analysis['europe_analysis']}\n\n---\n\n"

    europe_events = [e for e in news_events if any(kw in e.get('affected_markets', '').lower()
                     for kw in ['歐洲', '英國', '德國', '法國', '全球', '歐元區'])]
    if europe_events:
        md += "## 宏觀重點新聞（歐洲相關）\n\n"
        for i, event in enumerate(europe_events[:5], 1):
            impact = event.get('impact_level', '中')
            icon = "🔴" if impact == '高' else ("🟡" if impact == '中' else "🟢")
            md += f"**{icon} {event.get('title', '')}** — {event.get('description', '')}\n\n"
        md += "---\n\n"

    europe = market_data.get('europe_indices', {})
    if europe:
        md += "## 歐洲指數表現\n\n"
        md += _generate_index_table(europe)

    md += "---\n\n**資料來源**：Yahoo Finance、Polygon.io、S&P Global、CNBC、Investing.com\n"
    return md


def generate_us_report(market_data, news_events, hot_stocks, stock_analysis, index_analysis, report_date):
    """生成美洲盤報告"""
    md = f"# 美洲盤市場報告 ｜ {report_date}\n\n---\n\n"

    if index_analysis and 'us_analysis' in index_analysis:
        md += f"> {index_analysis['us_analysis']}\n\n---\n\n"

    us_events = [e for e in news_events if any(kw in e.get('affected_markets', '').lower()
                 for kw in ['美國', '美洲', '全球', '聯準會'])]
    if us_events:
        md += "## 宏觀重點新聞（美洲相關）\n\n"
        for i, event in enumerate(us_events[:5], 1):
            impact = event.get('impact_level', '中')
            icon = "🔴" if impact == '高' else ("🟡" if impact == '中' else "🟢")
            md += f"**{icon} {event.get('title', '')}** — {event.get('description', '')}\n\n"
        md += "---\n\n"

    us = market_data.get('us_indices', {})
    if us:
        md += "## 美股指數表現\n\n"
        md += _generate_index_table(us)

    if '美股' in hot_stocks and hot_stocks['美股']:
        inflow, outflow = _extract_stocks_from_market(hot_stocks['美股'])
        if inflow:
            md += "### 美股 — 資金追捧\n\n"
            md += "| 股票 | 代碼 | 收盤價 | 漲跌幅 | 量比 |\n"
            md += "|:-----|:-----|-------:|-------:|-----:|\n"
            for s in inflow:
                trend = get_trend_icon(s['change_pct'])
                md += f"| {trend} **{s['name'][:28]}** | `{s['symbol']}` | {s['current']:,.2f} | {s['change_pct']:+.2f}% | {s.get('volume_ratio', 1):.1f}x |\n"
            md += "\n"
        if outflow:
            md += "### 美股 — 資金出清\n\n"
            md += "| 股票 | 代碼 | 收盤價 | 漲跌幅 | 量比 |\n"
            md += "|:-----|:-----|-------:|-------:|-----:|\n"
            for s in outflow:
                trend = get_trend_icon(s['change_pct'])
                md += f"| {trend} **{s['name'][:28]}** | `{s['symbol']}` | {s['current']:,.2f} | {s['change_pct']:+.2f}% | {s.get('volume_ratio', 1):.1f}x |\n"
            md += "\n"

    md += "---\n\n**資料來源**：Yahoo Finance、Polygon.io、S&P Global、CNBC、Investing.com\n"
    return md
