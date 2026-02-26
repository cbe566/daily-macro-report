#!/usr/bin/env python3
"""
市場休市偵測模組

使用 exchange_calendars 套件精確偵測各交易所的休市日。

功能：
  1. 偵測今日各市場是否休市（報告中標註「今日休市」）
  2. 偵測明日（或下一個工作日）是否休市（報告中提前提醒）
  3. 列出未來 7 天內的所有休市日（經濟日曆區塊顯示）

支援市場：
  - US: 紐約證交所 (NYSE) — XNYS
  - JP: 東京證交所 (TSE) — XTKS
  - TW: 台灣證交所 (TWSE) — XTAI
  - HK: 香港交易所 (HKEX) — XHKG

依賴：pip install exchange_calendars
"""

import datetime
import exchange_calendars as xcals

# ==================== 交易所對應表 ====================
EXCHANGE_MAP = {
    'US': {
        'xcal_code': 'XNYS',
        'name_zh': '美股',
        'exchange_name': '紐約證交所 (NYSE)',
    },
    'JP': {
        'xcal_code': 'XTKS',
        'name_zh': '日股',
        'exchange_name': '東京證交所 (TSE)',
    },
    'TW': {
        'xcal_code': 'XTAI',
        'name_zh': '台股',
        'exchange_name': '台灣證交所 (TWSE)',
    },
    'HK': {
        'xcal_code': 'XHKG',
        'name_zh': '港股',
        'exchange_name': '香港交易所 (HKEX)',
    },
}

# 快取已載入的日曆物件
_calendar_cache = {}


def _get_calendar(xcal_code):
    """取得交易所日曆（帶快取）"""
    if xcal_code not in _calendar_cache:
        _calendar_cache[xcal_code] = xcals.get_calendar(xcal_code)
    return _calendar_cache[xcal_code]


def is_trading_day(market_code, date=None):
    """
    檢查指定市場在指定日期是否為交易日

    Args:
        market_code: 市場代碼（US/JP/TW/HK）
        date: datetime.date，預設為今天

    Returns:
        bool: True = 交易日, False = 休市
    """
    if date is None:
        date = datetime.date.today()

    exchange = EXCHANGE_MAP.get(market_code)
    if not exchange:
        return True  # 未知市場預設為交易日

    cal = _get_calendar(exchange['xcal_code'])
    try:
        return cal.is_session(date.isoformat())
    except Exception:
        # 如果日期超出日曆範圍，根據是否為工作日判斷
        return date.weekday() < 5


def get_next_business_day(date=None):
    """取得下一個工作日（不含今天）"""
    if date is None:
        date = datetime.date.today()
    next_day = date + datetime.timedelta(days=1)
    while next_day.weekday() >= 5:  # 跳過週末
        next_day += datetime.timedelta(days=1)
    return next_day


def get_market_status(date=None):
    """
    取得所有市場在指定日期的開休市狀態

    Args:
        date: datetime.date，預設為今天

    Returns:
        dict: {
            'US': {'is_open': True, 'name_zh': '美股', ...},
            'JP': {'is_open': False, 'name_zh': '日股', ...},
            ...
        }
    """
    if date is None:
        date = datetime.date.today()

    status = {}
    for code, exchange in EXCHANGE_MAP.items():
        is_open = is_trading_day(code, date)
        status[code] = {
            'is_open': is_open,
            'name_zh': exchange['name_zh'],
            'exchange_name': exchange['exchange_name'],
            'date': date,
        }
    return status


def get_holiday_alerts(today=None):
    """
    生成休市提醒資訊，包含：
    1. 今日休市的市場
    2. 明日（下一個工作日）休市的市場
    3. 未來 7 天內的休市日

    Args:
        today: datetime.date，預設為今天

    Returns:
        dict: {
            'today_closed': [{'market': 'TW', 'name_zh': '台股', ...}],
            'tomorrow_closed': [{'market': 'US', 'name_zh': '美股', ...}],
            'upcoming_holidays': [
                {'date': datetime.date, 'weekday': '五', 'markets': ['TW']}
            ],
            'has_alerts': bool,
        }
    """
    if today is None:
        today = datetime.date.today()

    next_biz_day = get_next_business_day(today)

    today_closed = []
    tomorrow_closed = []

    for code, exchange in EXCHANGE_MAP.items():
        # 今日休市檢查（僅工作日才檢查，週末本來就不開）
        if today.weekday() < 5 and not is_trading_day(code, today):
            today_closed.append({
                'market': code,
                'name_zh': exchange['name_zh'],
                'exchange_name': exchange['exchange_name'],
            })

        # 下一個工作日休市檢查
        if not is_trading_day(code, next_biz_day):
            tomorrow_closed.append({
                'market': code,
                'name_zh': exchange['name_zh'],
                'exchange_name': exchange['exchange_name'],
                'date': next_biz_day,
            })

    # 未來 7 天內的休市日
    upcoming_holidays = []
    weekday_names = ['一', '二', '三', '四', '五', '六', '日']

    for delta in range(1, 8):
        check_date = today + datetime.timedelta(days=delta)
        if check_date.weekday() >= 5:
            continue  # 跳過週末

        closed_markets = []
        for code in EXCHANGE_MAP:
            if not is_trading_day(code, check_date):
                closed_markets.append(code)

        if closed_markets:
            market_names = [EXCHANGE_MAP[c]['name_zh'] for c in closed_markets]
            upcoming_holidays.append({
                'date': check_date,
                'weekday': weekday_names[check_date.weekday()],
                'markets': closed_markets,
                'market_names': market_names,
            })

    has_alerts = bool(today_closed or tomorrow_closed or upcoming_holidays)

    return {
        'today_closed': today_closed,
        'tomorrow_closed': tomorrow_closed,
        'next_business_day': next_biz_day,
        'upcoming_holidays': upcoming_holidays,
        'has_alerts': has_alerts,
    }


def format_holiday_alerts_text(alerts=None, today=None):
    """
    將休市提醒格式化為純文字（用於 Email 內文）

    Returns:
        str: 格式化的休市提醒文字，如果沒有提醒則回傳空字串
    """
    if alerts is None:
        alerts = get_holiday_alerts(today)

    if not alerts['has_alerts']:
        return ''

    lines = []

    # 今日休市
    if alerts['today_closed']:
        names = '、'.join(a['name_zh'] for a in alerts['today_closed'])
        lines.append(f'⚠️ 今日休市：{names}（數據為前一交易日收盤）')

    # 明日休市提醒
    if alerts['tomorrow_closed']:
        names = '、'.join(a['name_zh'] for a in alerts['tomorrow_closed'])
        date_str = alerts['next_business_day'].strftime('%m/%d')
        lines.append(f'📅 明日休市提醒：{names}（{date_str}）')

    # 未來一週休市
    if alerts['upcoming_holidays']:
        lines.append('')
        lines.append('【未來一週休市日】')
        for h in alerts['upcoming_holidays']:
            date_str = h['date'].strftime('%m/%d')
            names = '、'.join(h['market_names'])
            lines.append(f'- {date_str}（週{h["weekday"]}）{names} 休市')

    return '\n'.join(lines)


def format_holiday_alerts_markdown(alerts=None, today=None):
    """
    將休市提醒格式化為 Markdown（用於 PDF 報告）

    Returns:
        str: 格式化的 Markdown 文字，如果沒有提醒則回傳空字串
    """
    if alerts is None:
        alerts = get_holiday_alerts(today)

    if not alerts['has_alerts']:
        return ''

    lines = []
    lines.append('## 市場休市提醒')
    lines.append('')

    # 今日休市
    if alerts['today_closed']:
        names = '、'.join(a['name_zh'] for a in alerts['today_closed'])
        lines.append(f'> **今日休市**：{names}（數據為前一交易日收盤）')
        lines.append('')

    # 明日休市提醒
    if alerts['tomorrow_closed']:
        names = '、'.join(a['name_zh'] for a in alerts['tomorrow_closed'])
        date_str = alerts['next_business_day'].strftime('%m/%d')
        lines.append(f'> **明日休市提醒**：{names}（{date_str}）')
        lines.append('')

    # 未來一週休市表格
    if alerts['upcoming_holidays']:
        lines.append('| 日期 | 星期 | 休市市場 |')
        lines.append('|------|------|----------|')
        for h in alerts['upcoming_holidays']:
            date_str = h['date'].strftime('%m/%d')
            names = '、'.join(h['market_names'])
            lines.append(f'| {date_str} | 週{h["weekday"]} | {names} |')
        lines.append('')

    return '\n'.join(lines)


# ==================== 測試 ====================
if __name__ == '__main__':
    import os
    os.environ['TZ'] = 'Asia/Taipei'

    today = datetime.date.today()
    print(f'今天: {today}')
    print()

    # 測試今日狀態
    print('=== 今日市場狀態 ===')
    status = get_market_status(today)
    for code, s in status.items():
        state = '✅ 交易日' if s['is_open'] else '❌ 休市'
        print(f'  {s["name_zh"]} ({s["exchange_name"]}): {state}')

    print()

    # 測試休市提醒
    print('=== 休市提醒 ===')
    alerts = get_holiday_alerts(today)
    text = format_holiday_alerts_text(alerts)
    if text:
        print(text)
    else:
        print('  無休市提醒')

    print()

    # 測試 Markdown 格式
    print('=== Markdown 格式 ===')
    md = format_holiday_alerts_markdown(alerts)
    if md:
        print(md)
    else:
        print('  無休市提醒')

    # 模擬美國假日（2026-04-03 耶穌受難日）
    print()
    print('=== 模擬 2026-04-02（耶穌受難日前一天）===')
    test_date = datetime.date(2026, 4, 2)
    alerts2 = get_holiday_alerts(test_date)
    text2 = format_holiday_alerts_text(alerts2)
    if text2:
        print(text2)
    else:
        print('  無休市提醒')

    # 模擬台灣假日
    print()
    print('=== 模擬 2026-02-26（台股明天 2/27 休市）===')
    test_date3 = datetime.date(2026, 2, 26)
    alerts3 = get_holiday_alerts(test_date3)
    text3 = format_holiday_alerts_text(alerts3)
    if text3:
        print(text3)
    else:
        print('  無休市提醒')
