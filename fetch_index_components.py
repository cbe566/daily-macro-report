#!/usr/bin/env python3
"""
抓取四大市場指數成分股清單並存為本地 JSON 快取
- 美股：道瓊30 + S&P 500 + NASDAQ 100（去重合併）
- 日股：日經 225
- 台股：台灣加權指數（全部上市股票）
- 港股：恆生指數 + 國企股

來源：Wikipedia + TWSE + AASTOCKS
快取位置：data/index_components.json
"""
import json
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
CACHE_FILE = os.path.join(DATA_DIR, 'index_components.json')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}


def fetch_sp500():
    """從 Wikipedia 抓取 S&P 500 成分股"""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    resp = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', {'id': 'constituents'})
    symbols = []
    if table:
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if cols:
                symbol = cols[0].text.strip().replace('.', '-')
                name = cols[1].text.strip() if len(cols) > 1 else symbol
                sector = cols[2].text.strip() if len(cols) > 2 else ''
                symbols.append({'symbol': symbol, 'name': name, 'sector': sector})
    print(f"  S&P 500: {len(symbols)} 支")
    return symbols


def fetch_nasdaq100():
    """從 Wikipedia 抓取 NASDAQ 100 成分股"""
    url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
    resp = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
    symbols = []
    tables = soup.find_all('table', class_='wikitable')
    for table in tables:
        headers = [th.text.strip().lower() for th in table.find_all('th')]
        if 'ticker' in headers or 'symbol' in headers:
            ticker_idx = headers.index('ticker') if 'ticker' in headers else headers.index('symbol')
            name_idx = headers.index('company') if 'company' in headers else (
                headers.index('security') if 'security' in headers else -1
            )
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if cols and len(cols) > ticker_idx:
                    symbol = cols[ticker_idx].text.strip()
                    name = cols[name_idx].text.strip() if name_idx >= 0 and len(cols) > name_idx else symbol
                    if symbol and len(symbol) <= 5:
                        symbols.append({'symbol': symbol, 'name': name})
            if symbols:
                break
    print(f"  NASDAQ 100: {len(symbols)} 支")
    return symbols


def fetch_djia():
    """從 Wikipedia 抓取道瓊工業指數 30 成分股"""
    url = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
    resp = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
    symbols = []
    tables = soup.find_all('table', class_='wikitable')
    for table in tables:
        headers = [th.text.strip().lower() for th in table.find_all('th')]
        if 'symbol' in headers or 'ticker' in headers:
            sym_idx = headers.index('symbol') if 'symbol' in headers else headers.index('ticker')
            name_idx = headers.index('company') if 'company' in headers else -1
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if cols and len(cols) > sym_idx:
                    symbol = cols[sym_idx].text.strip()
                    name = cols[name_idx].text.strip() if name_idx >= 0 and len(cols) > name_idx else symbol
                    if symbol:
                        symbols.append({'symbol': symbol, 'name': name})
            if symbols:
                break
    print(f"  道瓊 30: {len(symbols)} 支")
    return symbols


def fetch_nikkei225():
    """從 Wikipedia 抓取日經 225 成分股（透過 JPX 連結中的代碼）"""
    url = 'https://en.wikipedia.org/wiki/Nikkei_225'
    resp = requests.get(url, headers=HEADERS, timeout=30)
    # 從 JPX 連結中提取代碼：topSearchStr=XXXX">XXXX</a>
    codes = re.findall(r'topSearchStr=(\d{4})">\d{4}</a>', resp.text)
    codes_unique = sorted(set(codes))

    # 同時提取公司名稱
    soup = BeautifulSoup(resp.text, 'html.parser')
    symbols = []
    seen = set()

    # 找 Components 章節之後的所有列表項
    for li in soup.find_all('li'):
        text = str(li)
        code_match = re.search(r'topSearchStr=(\d{4})', text)
        if code_match:
            code = code_match.group(1)
            if code not in seen:
                seen.add(code)
                # 提取公司名稱（第一個 <a> 標籤的文字）
                first_link = li.find('a')
                name = first_link.text.strip() if first_link else ''
                symbols.append({'symbol': f'{code}.T', 'name': name})

    # 如果解析不完整，用純代碼補充
    for code in codes_unique:
        if code not in seen:
            symbols.append({'symbol': f'{code}.T', 'name': ''})

    print(f"  日經 225: {len(symbols)} 支")
    return symbols


def fetch_twse_all():
    """從 TWSE 抓取台灣加權指數全部上市股票"""
    symbols = []
    seen = set()

    try:
        url = 'https://isin.twse.com.tw/isin/C_public.jsp?strMode=2'
        resp = requests.get(url, headers=HEADERS, timeout=60)
        resp.encoding = 'big5'
        soup = BeautifulSoup(resp.text, 'html.parser')
        rows = soup.find_all('tr')

        in_stock_section = False
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 1:
                text = cols[0].text.strip()
                if '股票' in text and 'ETF' not in text and '權證' not in text:
                    in_stock_section = True
                elif in_stock_section and ('上櫃' in text or 'ETF' in text or '權證' in text or '特別股' in text):
                    in_stock_section = False
            elif len(cols) >= 4 and in_stock_section:
                code_name = cols[0].text.strip().replace('\u3000', ' ')
                match = re.match(r'^(\d{4})\s+(.+)', code_name)
                if match:
                    code = match.group(1)
                    name = match.group(2).strip()
                    sym = f'{code}.TW'
                    if sym not in seen:
                        seen.add(sym)
                        symbols.append({'symbol': sym, 'name': name})
    except Exception as e:
        print(f"  TWSE 抓取失敗: {e}")

    print(f"  台灣加權指數: {len(symbols)} 支")

    # 如果 TWSE 抓取失敗或數量過少，使用備用方案（台灣50 + 中型100）
    if len(symbols) < 100:
        print("  [警告] TWSE 抓取數量不足，嘗試備用方案...")
        symbols = _fetch_twse_fallback()

    return symbols


def _fetch_twse_fallback():
    """備用方案：從 Wikipedia 抓取台灣 50 + 中型 100 硬編碼清單"""
    symbols = []
    seen = set()

    # 台灣 50：從中文 Wikipedia
    try:
        url = 'https://zh.wikipedia.org/wiki/%E8%87%BA%E7%81%A350%E6%8C%87%E6%95%B8'
        resp = requests.get(url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(resp.text, 'html.parser')
        tables = soup.find_all('table', class_='wikitable')
        if tables:
            table = tables[0]
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                for td in cols:
                    text = td.text.strip()
                    match = re.search(r'[：:](\d{4})', text)
                    if match:
                        code = match.group(1)
                        idx = list(cols).index(td)
                        name = cols[idx + 1].text.strip() if idx + 1 < len(cols) else ''
                        sym = f'{code}.TW'
                        if sym not in seen:
                            seen.add(sym)
                            symbols.append({'symbol': sym, 'name': name})
    except Exception as e:
        print(f"  台灣 50 備用抓取失敗: {e}")

    print(f"  備用方案: 台灣 50 抓到 {len(symbols)} 支")

    # 中型 100 硬編碼備用清單
    mid100_backup = [
        ('3037', '欣興'), ('2449', '京元電子'), ('2344', '華邦電'), ('2368', '金像電'),
        ('6770', '力積電'), ('3443', '創意'), ('6446', '藥華藥'), ('2313', '華通'),
        ('1101', '台泥'), ('3481', '群創'), ('3044', '健鼎'), ('6239', '力成'),
        ('2404', '漢唐'), ('1326', '台化'), ('1590', '亞德客-KY'), ('2801', '彰銀'),
        ('5871', '中租-KY'), ('5876', '上海商銀'), ('1519', '華城'), ('3533', '嘉澤'),
        ('4958', '臻鼎-KY'), ('4938', '和碩'), ('6515', '穎崴'), ('2324', '仁寶'),
        ('2376', '技嘉'), ('3036', '文曄'), ('2356', '英業達'), ('8046', '南電'),
        ('2834', '臺企銀'), ('1504', '東元'), ('1605', '華新'), ('6442', '光聖'),
        ('2618', '長榮航'), ('2474', '可成'), ('3702', '大聯大'), ('2609', '陽明'),
        ('2409', '友達'), ('6415', '矽力*-KY'), ('1402', '遠東新'), ('2347', '聯強'),
        ('6139', '亞翔'), ('1102', '亞泥'), ('1476', '儒鴻'), ('2812', '台中銀'),
        ('2353', '宏碁'), ('6805', '富世達'), ('2385', '群光'), ('3706', '神達'),
        ('1513', '中興電'), ('1477', '聚陽'), ('2027', '大成鋼'), ('8464', '億豐'),
        ('9904', '寶成'), ('2049', '上銀'), ('6285', '啟碁'), ('1503', '士電'),
        ('2377', '微星'), ('6409', '旭隼'), ('6176', '瑞儀'), ('1802', '台玻'),
        ('2610', '華航'), ('2354', '鴻準'), ('5434', '崇越'), ('2105', '正新'),
        ('2633', '台灣高鐵'), ('3023', '信邦'), ('8210', '勤誠'), ('2542', '興富發'),
        ('5269', '祥碩'), ('9945', '潤泰新'), ('3005', '神基'), ('6531', '愛普*'),
        ('1229', '聯華'), ('2371', '大同'), ('9910', '豐泰'), ('1319', '東陽'),
        ('2451', '創見'), ('1795', '美時'), ('3406', '玉晶光'), ('2006', '東和鋼鐵'),
        ('6781', 'AES-KY'), ('2915', '潤泰全'), ('7799', '禾榮科'), ('2845', '遠東銀'),
        ('6472', '保瑞'), ('6789', '采鈺'), ('6191', '精成科'), ('1722', '台肥'),
        ('2206', '三陽工業'), ('2646', '星宇航空'), ('4763', '材料*-KY'), ('9917', '中保科'),
        ('2645', '長榮航太'), ('9941', '裕融'), ('6526', '達發'), ('2539', '櫻花建'),
        ('8454', '富邦媒'), ('6890', '來億-KY'), ('4583', '台灣精銳'), ('2258', '鴻華先進-創'),
    ]
    for code, name in mid100_backup:
        sym = f'{code}.TW'
        if sym not in seen:
            seen.add(sym)
            symbols.append({'symbol': sym, 'name': name})

    print(f"  備用方案合計: {len(symbols)} 支")
    return symbols


def fetch_hsi():
    """從 Wikipedia 抓取恆生指數成分股"""
    url = 'https://en.wikipedia.org/wiki/Hang_Seng_Index'
    resp = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
    symbols = []
    tables = soup.find_all('table', class_='wikitable')
    for table in tables:
        headers_list = [th.text.strip().lower() for th in table.find_all('th')]
        has_ticker = any(h in headers_list for h in ['ticker', 'symbol', 'code', 'stock code', 'no.'])
        has_company = any(h in headers_list for h in ['company', 'company name', 'name', 'stock name'])
        if has_ticker and has_company:
            ticker_idx = next(i for i, h in enumerate(headers_list) if h in ['ticker', 'symbol', 'code', 'stock code', 'no.'])
            name_idx = next(i for i, h in enumerate(headers_list) if h in ['company', 'company name', 'name', 'stock name'])
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if cols and len(cols) > max(ticker_idx, name_idx):
                    code = cols[ticker_idx].text.strip()
                    name = cols[name_idx].text.strip()
                    code_clean = ''.join(c for c in code if c.isdigit())
                    if code_clean:
                        code_padded = code_clean.zfill(4)
                        symbols.append({'symbol': f'{code_padded}.HK', 'name': name})
            if symbols:
                break
    print(f"  恆生指數: {len(symbols)} 支")
    return symbols


def fetch_hscei():
    """從 Wikipedia 抓取恆生中國企業指數（國企股）成分股"""
    url = 'https://en.wikipedia.org/wiki/Hang_Seng_China_Enterprises_Index'
    resp = requests.get(url, headers=HEADERS, timeout=30)
    soup = BeautifulSoup(resp.text, 'html.parser')
    symbols = []
    tables = soup.find_all('table', class_='wikitable')
    for table in tables:
        headers_list = [th.text.strip().lower() for th in table.find_all('th')]
        has_ticker = any(h in headers_list for h in ['ticker', 'symbol', 'code', 'stock code', 'no.'])
        has_company = any(h in headers_list for h in ['company', 'company name', 'name', 'stock name'])
        if has_ticker and has_company:
            ticker_idx = next(i for i, h in enumerate(headers_list) if h in ['ticker', 'symbol', 'code', 'stock code', 'no.'])
            name_idx = next(i for i, h in enumerate(headers_list) if h in ['company', 'company name', 'name', 'stock name'])
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if cols and len(cols) > max(ticker_idx, name_idx):
                    code = cols[ticker_idx].text.strip()
                    name = cols[name_idx].text.strip()
                    code_clean = ''.join(c for c in code if c.isdigit())
                    if code_clean:
                        code_padded = code_clean.zfill(4)
                        symbols.append({'symbol': f'{code_padded}.HK', 'name': name})
            if symbols:
                break
    print(f"  恆生中國企業指數（HSCEI）: {len(symbols)} 支")
    return symbols


def load_hk_soe_from_cache():
    """從本地快取載入國企股清單（AASTOCKS 匯出）"""
    soe_file = os.path.join(DATA_DIR, 'hk_soe_stocks.json')
    if os.path.exists(soe_file):
        with open(soe_file, 'r', encoding='utf-8') as f:
            stocks = json.load(f)
        print(f"  國企股快取: {len(stocks)} 支")
        return stocks
    print("  [警告] 國企股快取不存在，將僅使用恆生指數 + HSCEI")
    return []


def merge_hk_stocks(hsi, hscei, soe):
    """合併港股三個來源，去重"""
    seen = set()
    merged = []
    for stock in hsi + hscei + soe:
        sym = stock['symbol']
        # 標準化為 4 位數格式
        code = sym.replace('.HK', '')
        code_padded = str(int(code)).zfill(4) + '.HK'
        if code_padded not in seen:
            seen.add(code_padded)
            stock['symbol'] = code_padded
            merged.append(stock)
    print(f"  港股合併去重: {len(merged)} 支")
    return merged


def merge_us_stocks(djia, sp500, nasdaq100):
    """合併美股三大指數，去重"""
    seen = set()
    merged = []
    for stock in djia + sp500 + nasdaq100:
        sym = stock['symbol']
        if sym not in seen:
            seen.add(sym)
            merged.append(stock)
    print(f"  美股合併去重: {len(merged)} 支")
    return merged


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    print("=== 抓取四大市場指數成分股 ===\n")

    print("[美股]")
    djia = fetch_djia()
    sp500 = fetch_sp500()
    nasdaq100 = fetch_nasdaq100()
    us_stocks = merge_us_stocks(djia, sp500, nasdaq100)

    print("\n[日股]")
    jp_stocks = fetch_nikkei225()

    print("\n[台股]")
    tw_stocks = fetch_twse_all()

    print("\n[港股]")
    hsi = fetch_hsi()
    hscei = fetch_hscei()
    soe = load_hk_soe_from_cache()
    hk_stocks = merge_hk_stocks(hsi, hscei, soe)

    result = {
        'updated_at': datetime.now().isoformat(),
        'markets': {
            'US': {
                'name': '美股',
                'indices': '道瓊30 + S&P 500 + NASDAQ 100',
                'count': len(us_stocks),
                'stocks': us_stocks,
            },
            'JP': {
                'name': '日股',
                'indices': '日經 225',
                'count': len(jp_stocks),
                'stocks': jp_stocks,
            },
            'TW': {
                'name': '台股',
                'indices': '台灣加權指數（全部上市股票）',
                'count': len(tw_stocks),
                'stocks': tw_stocks,
            },
            'HK': {
                'name': '港股',
                'indices': '恆生指數 + 國企股',
                'count': len(hk_stocks),
                'stocks': hk_stocks,
            },
        },
        'total_count': len(us_stocks) + len(jp_stocks) + len(tw_stocks) + len(hk_stocks),
    }

    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完成 ===")
    print(f"總計: {result['total_count']} 支")
    print(f"快取已存: {CACHE_FILE}")

    return result


if __name__ == '__main__':
    main()
