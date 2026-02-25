#!/usr/bin/env python3
"""
HTML 報告生成引擎
使用 HTML+CSS 生成專業精美的 PDF 報告
參考 Saxo Bank / Goldman Sachs 風格
"""
import json
from datetime import datetime, timedelta


# ==================== CSS 樣式 ====================

REPORT_CSS = """
@page {
    size: A4;
    margin: 20mm 18mm 20mm 18mm;
    @top-center {
        content: "";
    }
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-size: 9px;
        color: #999;
        font-family: 'Noto Sans TC', 'Noto Sans SC', 'Noto Sans JP', sans-serif;
    }
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Noto Sans TC', 'Noto Sans SC', 'Noto Sans JP', 'Helvetica Neue', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.7;
    color: #2c3e50;
    background: #fff;
}

/* ===== 報告頭部 ===== */
.report-header {
    background: linear-gradient(135deg, #1a2332 0%, #2c3e50 50%, #34495e 100%);
    color: white;
    padding: 28px 30px;
    margin: -20mm -18mm 0 -18mm;
    margin-bottom: 20px;
}

.report-header h1 {
    font-size: 22pt;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 6px;
}

.report-header .subtitle {
    font-size: 11pt;
    color: #bdc3c7;
    font-weight: 300;
}

.report-header .date-line {
    font-size: 10pt;
    color: #95a5a6;
    margin-top: 4px;
}

/* ===== 市場速覽 ===== */
.snapshot-box {
    background: #f8f9fa;
    border-left: 4px solid #1a2332;
    padding: 14px 18px;
    margin-bottom: 22px;
    font-size: 11pt;
    line-height: 1.8;
    color: #2c3e50;
}

.snapshot-box .snapshot-label {
    font-weight: 700;
    color: #1a2332;
    display: inline;
}

.snapshot-line {
    margin-bottom: 4px;
}

/* ===== 章節標題 ===== */
.section-title {
    font-size: 14pt;
    font-weight: 700;
    color: #1a2332;
    border-bottom: 3px solid #1a2332;
    padding-bottom: 6px;
    margin-top: 24px;
    margin-bottom: 14px;
    page-break-after: avoid;
}

.sub-section-title {
    font-size: 12pt;
    font-weight: 600;
    color: #2c3e50;
    margin-top: 14px;
    margin-bottom: 8px;
    padding-left: 10px;
    border-left: 3px solid #3498db;
    page-break-after: avoid;
}

/* ===== 分析段落 ===== */
.analysis-text {
    font-size: 11pt;
    color: #555;
    line-height: 1.7;
    margin-bottom: 10px;
    text-align: justify;
}

/* ===== 表格 ===== */
table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 16px;
    font-size: 10pt;
}

table thead th {
    background: #1a2332;
    color: white;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
    font-size: 9.5pt;
    letter-spacing: 0.5px;
}

table thead th.right {
    text-align: right;
}

table thead th.center {
    text-align: center;
}

table tbody td {
    padding: 7px 10px;
    border-bottom: 1px solid #e8e8e8;
    vertical-align: middle;
}

table tbody tr:nth-child(even) {
    background: #f9fafb;
}

table tbody tr:hover {
    background: #f0f4f8;
}

table tbody tr {
    page-break-inside: avoid;
}

table {
    page-break-inside: auto;
}

td.right {
    text-align: right;
}

td.center {
    text-align: center;
}

td.name-cell {
    font-weight: 600;
    color: #2c3e50;
}

/* ===== 漲跌顏色 ===== */
.up, .snapshot-box .up {
    color: #27ae60 !important;
    font-weight: 600;
}

.down, .snapshot-box .down {
    color: #e74c3c !important;
    font-weight: 600;
}

.flat, .snapshot-box .flat {
    color: #95a5a6 !important;
}

.trend-up {
    color: #27ae60;
    font-weight: 700;
    font-size: 10pt;
}

.trend-down {
    color: #e74c3c;
    font-weight: 700;
    font-size: 10pt;
}

.trend-strong-up {
    color: #1e8449;
    font-weight: 700;
    font-size: 10pt;
}

.trend-strong-down {
    color: #c0392b;
    font-weight: 700;
    font-size: 10pt;
}

/* ===== 新聞卡片 ===== */
.news-card {
    margin-bottom: 16px;
    padding: 12px 16px;
    background: #fdfdfd;
    border: 1px solid #eee;
    border-radius: 4px;
    page-break-inside: avoid;
}

.news-card h3 {
    font-size: 12pt;
    font-weight: 700;
    color: #2c3e50;
    margin-bottom: 6px;
}

.news-meta {
    font-size: 9.5pt;
    margin-bottom: 6px;
}

.badge {
    display: inline-block;
    padding: 1px 8px;
    border-radius: 3px;
    font-size: 9.5pt;
    font-weight: 600;
    margin-right: 6px;
}

.badge-high {
    background: #fde8e8;
    color: #c0392b;
    border: 1px solid #e74c3c;
}

.badge-medium {
    background: #fef9e7;
    color: #d4a017;
    border: 1px solid #f1c40f;
}

.badge-low {
    background: #e8f8f5;
    color: #1e8449;
    border: 1px solid #27ae60;
}

.badge-bullish {
    background: #e8f8f5;
    color: #27ae60;
}

.badge-bearish {
    background: #fde8e8;
    color: #e74c3c;
}

.badge-neutral {
    background: #f0f0f0;
    color: #7f8c8d;
}

.news-body {
    font-size: 11pt;
    color: #555;
    line-height: 1.6;
}

.news-tickers {
    font-size: 9.5pt;
    color: #7f8c8d;
    margin-top: 6px;
}

.news-tickers code {
    background: #ecf0f1;
    padding: 1px 5px;
    border-radius: 2px;
    font-size: 9.5pt;
    color: #2c3e50;
}

/* ===== 熱門股票分析欄 ===== */
.stock-analysis {
    font-size: 10pt;
    color: #666;
    line-height: 1.4;
}

/* ===== 經濟日曆 ===== */
.calendar-highlight {
    background: #fff8e1;
    border-left: 3px solid #f1c40f;
    padding: 10px 14px;
    margin-top: 12px;
    margin-bottom: 8px;
    page-break-inside: avoid;
}

.calendar-highlight strong {
    color: #2c3e50;
}

/* ===== 分隔線 ===== */
.divider {
    border: none;
    border-top: 1px solid #ddd;
    margin: 18px 0;
}

/* ===== 底部 ===== */
.footer {
    margin-top: 24px;
    padding-top: 12px;
    border-top: 2px solid #1a2332;
    font-size: 9pt;
    color: #999;
    line-height: 1.5;
}

.footer strong {
    color: #666;
}

/* ===== 頁面控制 ===== */
.page-break {
    page-break-before: always;
}
"""


# ==================== 輔助函數 ====================

def _change_class(val):
    """根據數值返回 CSS class"""
    if val > 0:
        return "up"
    elif val < 0:
        return "down"
    return "flat"


def _trend_arrow(val):
    """根據漲跌幅返回趨勢箭頭"""
    if val > 1.5:
        return '<span class="trend-strong-up">▲▲</span>'
    elif val > 0:
        return '<span class="trend-up">▲</span>'
    elif val > -1.5:
        return '<span class="trend-down">▼</span>'
    else:
        return '<span class="trend-strong-down">▼▼</span>'


def _format_pct(val):
    """格式化百分比"""
    cls = _change_class(val)
    sign = "+" if val > 0 else ""
    return f'<span class="{cls}">{sign}{val:.2f}%</span>'


def _format_change(val):
    """格式化漲跌值"""
    cls = _change_class(val)
    sign = "+" if val > 0 else ""
    return f'<span class="{cls}">{sign}{val:,.2f}</span>'


def _format_change4(val):
    """格式化漲跌值（4位小數）"""
    cls = _change_class(val)
    sign = "+" if val > 0 else ""
    return f'<span class="{cls}">{sign}{val:.4f}</span>'


# ==================== 市場速覽 ====================

def _gen_snapshot(market_data, news_events):
    """生成市場速覽區塊"""
    html = '<div class="snapshot-box">\n'

    # 股市
    asia = market_data.get('asia_indices', {})
    europe = market_data.get('europe_indices', {})
    us = market_data.get('us_indices', {})

    def _idx_str(indices, names):
        parts = []
        for n in names:
            if n in indices:
                d = indices[n]
                cls = _change_class(d['change_pct'])
                parts.append(f'{n} <span class="{cls}">{d["change_pct"]:+.2f}%</span>')
        return '，'.join(parts) if parts else ''

    us_str = _idx_str(us, ['S&P 500', '納斯達克', '道瓊工業'])
    asia_str = _idx_str(asia, ['日經225', '台灣加權', '香港恆生'])
    europe_str = _idx_str(europe, ['德國DAX', '英國FTSE', '法國CAC'])

    html += f'<div class="snapshot-line"><span class="snapshot-label">股市：</span>{us_str}；亞洲 {asia_str}；歐洲 {europe_str}</div>\n'

    # 商品
    commodities = market_data.get('commodities', {})
    comm_parts = []
    for name, data in list(commodities.items())[:4]:
        cls = _change_class(data['change_pct'])
        comm_parts.append(f'{name} <span class="{cls}">{data["change_pct"]:+.2f}%</span>')
    if comm_parts:
        html += f'<div class="snapshot-line"><span class="snapshot-label">商品：</span>{" ｜ ".join(comm_parts)}</div>\n'

    # 外匯
    forex = market_data.get('forex', {})
    fx_parts = []
    for name, data in list(forex.items())[:3]:
        fx_parts.append(f'{name} {data["current"]:.4f}（<span class="{_change_class(data["change_pct"])}">{data["change_pct"]:+.2f}%</span>）')
    if fx_parts:
        html += f'<div class="snapshot-line"><span class="snapshot-label">外匯：</span>{" ｜ ".join(fx_parts)}</div>\n'

    # 加密貨幣
    crypto = market_data.get('crypto', {})
    if crypto:
        crypto_parts = []
        for coin in ['Bitcoin', 'Ethereum']:
            if coin in crypto:
                d = crypto[coin]
                short = 'BTC' if coin == 'Bitcoin' else 'ETH'
                cls = _change_class(d['change_pct'])
                crypto_parts.append(f'{short} ${d["current"]:,.0f}（<span class="{cls}">{d["change_pct"]:+.2f}%</span>）')
        if crypto_parts:
            html += f'<div class="snapshot-line"><span class="snapshot-label">加密貨幣：</span>{" ｜ ".join(crypto_parts)}</div>\n'

    # 焦點事件
    if news_events:
        top = news_events[0].get('title', '')
        html += f'<div class="snapshot-line"><span class="snapshot-label">焦點事件：</span>{top}</div>\n'

    html += '</div>\n'
    return html


# ==================== 指數表格 ====================

def _gen_index_table(indices_data):
    """生成單個區域的指數表格"""
    if not indices_data:
        return ""

    html = '<table>\n<thead><tr>'
    html += '<th>指數</th><th class="right">收盤價</th><th class="right">漲跌</th><th class="right">漲跌幅</th><th class="center">趨勢</th>'
    html += '</tr></thead>\n<tbody>\n'

    sorted_items = sorted(indices_data.items(), key=lambda x: x[1]['change_pct'], reverse=True)

    for name, data in sorted_items:
        html += '<tr>'
        html += f'<td class="name-cell">{name}</td>'
        html += f'<td class="right">{data["current"]:,.2f}</td>'
        html += f'<td class="right">{_format_change(data["change"])}</td>'
        html += f'<td class="right">{_format_pct(data["change_pct"])}</td>'
        html += f'<td class="center">{_trend_arrow(data["change_pct"])}</td>'
        html += '</tr>\n'

    html += '</tbody></table>\n'
    return html


def _gen_indices_section(market_data, index_analysis):
    """生成各國指數表現章節"""
    html = '<div class="section-title">一、各國指數表現</div>\n'

    for region, key, analysis_key in [
        ('亞洲市場', 'asia_indices', 'asia_analysis'),
        ('歐洲市場', 'europe_indices', 'europe_analysis'),
        ('美國市場', 'us_indices', 'us_analysis')
    ]:
        data = market_data.get(key, {})
        if data:
            html += f'<div class="sub-section-title">{region}</div>\n'
            if index_analysis and analysis_key in index_analysis:
                html += f'<p class="analysis-text">{index_analysis[analysis_key]}</p>\n'
            html += _gen_index_table(data)

    html += '<hr class="divider">\n'
    return html


# ==================== 宏觀新聞 ====================

def _gen_news_section(events):
    """生成宏觀重點新聞章節"""
    if not events:
        return ""

    html = '<div class="section-title">二、宏觀重點新聞</div>\n'

    for i, event in enumerate(events, 1):
        impact = event.get('impact_level', '中')
        if impact == '高':
            badge_cls = 'badge-high'
            badge_text = '高影響'
        elif impact == '中':
            badge_cls = 'badge-medium'
            badge_text = '中影響'
        else:
            badge_cls = 'badge-low'
            badge_text = '低影響'

        direction = event.get('market_direction', '中性')
        if direction == '利多':
            dir_cls = 'badge-bullish'
            dir_text = '▲ 利多'
        elif direction == '利空':
            dir_cls = 'badge-bearish'
            dir_text = '▼ 利空'
        else:
            dir_cls = 'badge-neutral'
            dir_text = '— 中性'

        affected = event.get('affected_markets', '')

        html += '<div class="news-card">\n'
        html += f'<h3>{i}. {event.get("title", "")}</h3>\n'
        html += f'<div class="news-meta">'
        html += f'<span class="badge {badge_cls}">{badge_text}</span>'
        html += f'<span class="badge {dir_cls}">{dir_text}</span>'
        html += f'<span style="font-size:9.5pt;color:#999;">影響範圍：{affected}</span>'
        html += '</div>\n'
        html += f'<div class="news-body">{event.get("description", "")}</div>\n'

        tickers = event.get('related_tickers', [])
        ticker_impact = event.get('ticker_impact', {})
        if tickers:
            if ticker_impact:
                impact_parts = []
                for t in tickers:
                    impact_desc = ticker_impact.get(t, '')
                    if impact_desc:
                        impact_parts.append(f'<code>{t}</code> {impact_desc}')
                    else:
                        impact_parts.append(f'<code>{t}</code>')
                html += f'<div class="news-tickers">相關標的影響：{"；".join(impact_parts)}</div>\n'
            else:
                ticker_html = '、'.join([f'<code>{t}</code>' for t in tickers])
                html += f'<div class="news-tickers">相關標的：{ticker_html}</div>\n'

        html += '</div>\n'

    html += '<hr class="divider">\n'
    return html


# ==================== 商品、外匯、債券 ====================

def _gen_commodities_forex_bonds(market_data):
    """生成商品、外匯與債券章節"""
    html = '<div class="section-title">三、商品、外匯與債券</div>\n'

    # 大宗商品
    commodities = market_data.get('commodities', {})
    if commodities:
        html += '<div class="sub-section-title">大宗商品</div>\n'
        html += '<table>\n<thead><tr>'
        html += '<th>商品</th><th class="right">價格</th><th class="right">漲跌</th><th class="right">漲跌幅</th><th class="center">趨勢</th>'
        html += '</tr></thead>\n<tbody>\n'
        for name, data in commodities.items():
            html += '<tr>'
            html += f'<td class="name-cell">{name}</td>'
            html += f'<td class="right">${data["current"]:,.2f}</td>'
            html += f'<td class="right">{_format_change(data["change"])}</td>'
            html += f'<td class="right">{_format_pct(data["change_pct"])}</td>'
            html += f'<td class="center">{_trend_arrow(data["change_pct"])}</td>'
            html += '</tr>\n'
        html += '</tbody></table>\n'

    # 外匯
    forex = market_data.get('forex', {})
    if forex:
        html += '<div class="sub-section-title">外匯市場</div>\n'
        html += '<table>\n<thead><tr>'
        html += '<th>貨幣對</th><th class="right">匯率</th><th class="right">漲跌</th><th class="right">漲跌幅</th><th class="center">趨勢</th>'
        html += '</tr></thead>\n<tbody>\n'
        for name, data in forex.items():
            html += '<tr>'
            html += f'<td class="name-cell">{name}</td>'
            html += f'<td class="right">{data["current"]:.4f}</td>'
            html += f'<td class="right">{_format_change4(data["change"])}</td>'
            html += f'<td class="right">{_format_pct(data["change_pct"])}</td>'
            html += f'<td class="center">{_trend_arrow(data["change_pct"])}</td>'
            html += '</tr>\n'
        html += '</tbody></table>\n'

    # 債券
    bonds = market_data.get('bonds', {})
    if bonds:
        html += '<div class="sub-section-title">債券殖利率</div>\n'
        html += '<table>\n<thead><tr>'
        html += '<th>債券</th><th class="right">殖利率</th><th class="right">變動</th><th class="right">變動幅度</th><th class="center">趨勢</th>'
        html += '</tr></thead>\n<tbody>\n'
        for name, data in bonds.items():
            html += '<tr>'
            html += f'<td class="name-cell">{name}</td>'
            html += f'<td class="right">{data["current"]:.3f}%</td>'
            html += f'<td class="right">{_format_change4(data["change"])}</td>'
            html += f'<td class="right">{_format_pct(data["change_pct"])}</td>'
            html += f'<td class="center">{_trend_arrow(data["change_pct"])}</td>'
            html += '</tr>\n'
        html += '</tbody></table>\n'

    html += '<hr class="divider">\n'
    return html


# ==================== 熱門股票 ====================

def _gen_stock_table_html(stocks, stock_analysis):
    """渲染一組股票的 HTML 表格"""
    if not stocks:
        return ""
    html = '<table>\n<thead><tr>'
    html += '<th>股票</th><th>代碼</th><th class="right">收盤價</th><th class="right">漲跌幅</th><th class="center">量比</th><th>分析</th>'
    html += '</tr></thead>\n<tbody>\n'
    for s in stocks:
        full_symbol = s['symbol']
        symbol_base = full_symbol.split('.')[0]
        analysis = ""
        if stock_analysis:
            analysis = stock_analysis.get(full_symbol, stock_analysis.get(symbol_base, ''))
        name = s['name']
        if len(name) > 50:
            name = name[:48] + "..."
        vol_ratio = s.get('volume_ratio', 1)
        html += '<tr>'
        html += f'<td class="name-cell">{name}</td>'
        html += f'<td><code style="font-size:9.5pt;">{s["symbol"]}</code></td>'
        html += f'<td class="right">{s["current"]:,.2f}</td>'
        html += f'<td class="right">{_format_pct(s["change_pct"])}</td>'
        html += f'<td class="center">{vol_ratio:.1f}x</td>'
        html += f'<td class="stock-analysis">{analysis}</td>'
        html += '</tr>\n'
    html += '</tbody></table>\n'
    return html


def _extract_stocks_html(market_data):
    """從 v2 格式的 market_data 中提取 inflow 和 outflow 列表"""
    if isinstance(market_data, dict) and 'inflow' in market_data:
        return market_data.get('inflow', []), market_data.get('outflow', [])
    elif isinstance(market_data, list):
        inflow = [s for s in market_data if s.get('flow') == 'inflow']
        outflow = [s for s in market_data if s.get('flow') == 'outflow']
        return inflow, outflow
    return [], []


def _gen_hot_stocks_section(hot_stocks, stock_analysis):
    """生成當日熱門股票章節：分區顯示資金追捧 vs 資金出清"""
    html = '<div class="section-title">四、當日熱門股票</div>\n'
    html += '<p class="analysis-text" style="color:#999;font-size:10pt;font-style:italic;">'
    html += '篩選邏輯：資金追捧（量比 ≥ 1.5x + 上漲）；資金出清（量比 ≥ 2.5x + 下跌）<br/>'
    html += '排序方式：量比門檻（硬篩）→ 漲跌幅排序 → 新聞提及加分 | 每市場最多 5 支買入 + 5 支賣出</p>\n'

    for market in ['美股', '港股', '日股', '台股']:
        if market not in hot_stocks or not hot_stocks[market]:
            continue

        inflow, outflow = _extract_stocks_html(hot_stocks[market])

        if not inflow and not outflow:
            continue

        html += f'<div class="sub-section-title">{market}</div>\n'

        if inflow:
            html += '<p style="font-size:11pt;font-weight:700;color:#27ae60;margin:8px 0 4px 0;">🔥 資金追捧（買入放量 ≥ 1.5x + 上漲）</p>\n'
            html += _gen_stock_table_html(inflow, stock_analysis)

        if outflow:
            html += '<p style="font-size:11pt;font-weight:700;color:#e74c3c;margin:8px 0 4px 0;">⚠️ 資金出清（賣出放量 ≥ 2.5x + 下跌）</p>\n'
            html += _gen_stock_table_html(outflow, stock_analysis)

    html += '<hr class="divider">\n'
    return html


# ==================== 加密貨幣 ====================

def _gen_crypto_section(crypto_data):
    """生成加密貨幣市場章節"""
    if not crypto_data:
        return ""

    html = '<div class="section-title">五、加密貨幣市場</div>\n'
    html += '<table>\n<thead><tr>'
    html += '<th>幣種</th><th class="right">價格（USD）</th><th class="right">24h 漲跌</th><th class="right">漲跌幅</th><th class="center">趨勢</th>'
    html += '</tr></thead>\n<tbody>\n'

    sorted_items = sorted(crypto_data.items(), key=lambda x: x[1].get('change_pct', 0), reverse=True)

    for name, data in sorted_items:
        html += '<tr>'
        html += f'<td class="name-cell">{name}</td>'
        html += f'<td class="right">${data["current"]:,.2f}</td>'
        html += f'<td class="right">{_format_change(data["change"])}</td>'
        html += f'<td class="right">{_format_pct(data["change_pct"])}</td>'
        html += f'<td class="center">{_trend_arrow(data["change_pct"])}</td>'
        html += '</tr>\n'

    html += '</tbody></table>\n'
    html += '<hr class="divider">\n'
    return html


# ==================== 經濟日曆 ====================

def _gen_calendar_section(calendar_events):
    """生成經濟日曆提示章節"""
    html = '<div class="section-title">六、本週經濟日曆</div>\n'

    if not calendar_events:
        html += '<p class="analysis-text">本週暫無重大經濟數據發布。</p>\n'
        return html

    html += '<p class="analysis-text" style="color:#999;font-style:italic;">以下為本週需要關注的重要經濟數據與事件</p>\n'

    html += '<table>\n<thead><tr>'
    html += '<th>日期</th><th>國家/地區</th><th>事件</th><th class="center">重要性</th><th>預期影響</th>'
    html += '</tr></thead>\n<tbody>\n'

    for event in calendar_events:
        importance = event.get('importance', '★')
        # 根據重要性設定顏色
        if '★★★' in importance:
            imp_style = 'color:#c0392b;font-weight:700;'
        elif '★★' in importance:
            imp_style = 'color:#d4a017;font-weight:600;'
        else:
            imp_style = 'color:#999;'

        desc = event.get('description', '')
        if len(desc) > 60:
            desc = desc[:58] + '...'

        html += '<tr>'
        html += f'<td>{event.get("date", "")}</td>'
        html += f'<td>{event.get("country", "")}</td>'
        html += f'<td class="name-cell">{event.get("event", "")}</td>'
        html += f'<td class="center" style="{imp_style}">{importance}</td>'
        html += f'<td style="font-size:10pt;color:#666;">{desc}</td>'
        html += '</tr>\n'

    html += '</tbody></table>\n'

    # 重點關注事件
    high_importance = [e for e in calendar_events if '★★★' in e.get('importance', '')]
    if high_importance:
        html += '<div class="sub-section-title">重點關注</div>\n'
        for event in high_importance:
            html += '<div class="calendar-highlight">\n'
            html += f'<strong>{event.get("event", "")}</strong>（{event.get("country", "")}，{event.get("date", "")}）<br>\n'
            html += f'<span style="font-size:10pt;color:#555;">{event.get("description", "")}</span>\n'
            if event.get('consensus'):
                html += f'<br><span style="font-size:10pt;color:#2c3e50;">市場預期：{event["consensus"]}</span>\n'
            html += '</div>\n'

    return html


# ==================== 主函數 ====================

def generate_html_report(market_data, news_events, hot_stocks, stock_analysis,
                         index_analysis, calendar_events, report_date):
    """生成完整的 HTML 報告"""

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>每日宏觀資訊綜合早報 | {report_date}</title>
<style>
{REPORT_CSS}
</style>
</head>
<body>

<div class="report-header">
    <h1>每日宏觀資訊綜合早報</h1>
    <div class="subtitle">Daily Macro Market Briefing</div>
    <div class="date-line">{report_date} ｜ 綜合早報</div>
</div>

"""

    # 市場速覽
    html += _gen_snapshot(market_data, news_events)

    # 一、各國指數表現
    html += _gen_indices_section(market_data, index_analysis)

    # 二、宏觀重點新聞
    html += _gen_news_section(news_events)

    # 三、商品、外匯與債券
    html += _gen_commodities_forex_bonds(market_data)

    # 四、當日熱門股票
    html += _gen_hot_stocks_section(hot_stocks, stock_analysis)

    # 五、加密貨幣市場
    html += _gen_crypto_section(market_data.get('crypto', {}))

    # 六、經濟日曆提示
    html += _gen_calendar_section(calendar_events)

    # 底部
    html += f"""
<div class="footer">
    <strong>報告生成時間</strong>：{datetime.now().strftime('%Y-%m-%d %H:%M')} (UTC+8)<br>
    <strong>資料來源</strong>：Yahoo Finance、Polygon.io、S&P Global、CNBC、Investing.com
</div>

</body>
</html>
"""

    return html
