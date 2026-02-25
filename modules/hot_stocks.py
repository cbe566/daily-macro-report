#!/usr/bin/env python3
"""
熱門股票偵測模組（v3 — 混合 API 高效版）

數據來源：
  - 美股：Polygon.io Grouped Daily Bars（一次呼叫獲取全市場 OHLCV）
  - 日股/台股/港股：Yahoo Finance（分批多線程查詢）

候選池：
  - 美股：道瓊30 + S&P 500 + NASDAQ 100（~536 支）
  - 日股：日經 225（~226 支）
  - 台股：台灣 50 + 中型 100（~150 支）
  - 港股：恆生指數（~85 支）

分層漏斗篩選：
  第一層（硬門檻）：量比 ≥ 1.5x + 上漲 → 資金追捧
                     量比 ≥ 2.5x + 下跌 → 資金出清
  第二層（排序）：  按漲跌幅絕對值排序
  第三層（加分）：  有新聞提及的優先（tiebreaker）

顯示上限：每市場最多 5 支買入 + 5 支賣出
"""
import sys
sys.path.append('/opt/.manus/.sandbox-runtime')

import json
import os
import time
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_api import ApiClient

# ==================== 量比門檻設定 ====================
MIN_VOLUME_RATIO_BUY = 1.5    # 買入放量：量比 ≥ 1.5x + 上漲
MIN_VOLUME_RATIO_SELL = 2.5   # 賣出放量：量比 ≥ 2.5x + 下跌

# ==================== 資金流向分類 ====================
FLOW_BUY = 'inflow'           # 資金追捧（買入放量上漲）
FLOW_SELL = 'outflow'         # 資金出清（賣出放量下跌）

# ==================== 顯示上限 ====================
MAX_PER_FLOW = 5              # 每市場每方向最多顯示 5 支

# ==================== Yahoo Finance 查詢設定 ====================
YF_MAX_WORKERS = 5            # Yahoo Finance 並行線程數
YF_BATCH_SIZE = 40            # 每批查詢股票數
YF_BATCH_DELAY = 5            # 批次間休息秒數
YF_RETRY_DELAY = 8            # 重試前等待秒數

# ==================== Polygon API 設定 ====================
POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', '')
POLYGON_HISTORY_DAYS = 10     # 查詢歷史天數（用於計算平均成交量）
POLYGON_REQUEST_DELAY = 13    # Polygon 請求間隔（秒），免費版限 5 req/min

# ==================== 成分股快取路徑 ====================
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
COMPONENTS_FILE = os.path.join(DATA_DIR, 'index_components.json')


# ================================================================
#  通用函數
# ================================================================

def load_stock_pool(market_code):
    """從本地快取載入指定市場的成分股清單"""
    if not os.path.exists(COMPONENTS_FILE):
        print(f"  [警告] 成分股快取不存在: {COMPONENTS_FILE}")
        print(f"  請先執行 fetch_index_components.py 建立快取")
        return []

    with open(COMPONENTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    market = data.get('markets', {}).get(market_code, {})
    stocks = market.get('stocks', [])
    symbols = [s['symbol'] for s in stocks]
    print(f"  [{market.get('name', market_code)}] 載入 {len(symbols)} 支成分股（{market.get('indices', '')}）")
    return symbols


def get_trading_dates(end_date, num_days):
    """
    生成指定日期往前的 N 個交易日（排除週末）
    
    Args:
        end_date: datetime.date 物件
        num_days: 需要的交易日數量
    Returns:
        list of date strings ['2026-02-24', '2026-02-23', ...]，最新日期在前
    """
    dates = []
    d = end_date
    while len(dates) < num_days:
        if d.weekday() < 5:  # 0=Mon, 4=Fri
            dates.append(d.strftime('%Y-%m-%d'))
        d -= datetime.timedelta(days=1)
    return dates


# ================================================================
#  美股：Polygon.io Grouped Daily Bars（批量查詢）
# ================================================================

def polygon_fetch_grouped_daily(date_str):
    """
    用 Polygon Grouped Daily Bars API 獲取某天所有美股的 OHLCV
    
    一次呼叫返回 ~11,000+ 支股票的數據
    
    Returns:
        dict: {ticker: {open, high, low, close, volume, vwap, n_transactions}} or None
    """
    url = f'https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{date_str}'
    params = {'adjusted': 'true', 'apiKey': POLYGON_API_KEY}
    
    try:
        resp = requests.get(url, params=params, timeout=30)
        
        if resp.status_code == 429:
            # 速率限制，等待後重試
            print(f"    {date_str}: 速率限制，等待 15 秒重試...")
            time.sleep(15)
            resp = requests.get(url, params=params, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('results', [])
            ticker_data = {}
            for r in results:
                ticker_data[r['T']] = {
                    'open': r.get('o', 0),
                    'high': r.get('h', 0),
                    'low': r.get('l', 0),
                    'close': r.get('c', 0),
                    'volume': r.get('v', 0),
                    'vwap': r.get('vw', 0),
                    'n_transactions': r.get('n', 0),
                }
            return ticker_data
        else:
            print(f"    {date_str}: HTTP {resp.status_code}")
            return None
            
    except Exception as e:
        print(f"    {date_str}: 錯誤 - {e}")
        return None


def polygon_scan_us_market(symbols, target_date=None):
    """
    用 Polygon API 批量掃描美股
    
    策略：
    1. 先探測最近有數據的交易日
    2. 查詢該日 + 前 N-1 天的 Grouped Daily Bars
    3. 計算每支成分股的量比和漲跌幅
    
    Args:
        symbols: 成分股代碼列表
        target_date: 目標日期 (datetime.date)，默認為今天
    
    Returns:
        list of stock dicts
    """
    if not POLYGON_API_KEY:
        print("  [警告] POLYGON_API_KEY 未設定，改用 Yahoo Finance")
        return yahoo_scan_market(symbols, '美股')
    
    if target_date is None:
        target_date = datetime.date.today()
    
    # 生成足夠多的候選交易日（多生成幾天以應對假日）
    candidate_dates = get_trading_dates(target_date, POLYGON_HISTORY_DAYS + 5)
    
    # 逐天查詢，找到第一個有數據的日期作為目標日
    daily_data = {}  # {date_str: {ticker: data}}
    start_time = time.time()
    dates_with_data = []  # 有數據的日期列表（按時間倒序）
    
    print(f"  [美股-Polygon] 查詢最近 {POLYGON_HISTORY_DAYS} 個有數據的交易日...")
    
    for i, date_str in enumerate(candidate_dates):
        if len(dates_with_data) >= POLYGON_HISTORY_DAYS:
            break
            
        data = polygon_fetch_grouped_daily(date_str)
        if data and len(data) > 1000:  # 有效數據（正常應有 11000+ 支）
            daily_data[date_str] = data
            dates_with_data.append(date_str)
            count = len(data)
            elapsed = time.time() - start_time
            print(f"    [{len(dates_with_data)}/{POLYGON_HISTORY_DAYS}] {date_str}: {count} 支 ({elapsed:.0f}s)")
        else:
            elapsed = time.time() - start_time
            print(f"    [跳過] {date_str}: 無數據或非交易日 ({elapsed:.0f}s)")
        
        # 速率限制：每次間隔 13 秒
        if len(dates_with_data) < POLYGON_HISTORY_DAYS and i < len(candidate_dates) - 1:
            time.sleep(POLYGON_REQUEST_DELAY)
    
    elapsed = time.time() - start_time
    print(f"  [美股-Polygon] 數據收集完成: {len(dates_with_data)} 天成功, 耗時 {elapsed:.0f}s")
    
    if len(dates_with_data) < 2:
        print("  [警告] 數據不足，改用 Yahoo Finance")
        return yahoo_scan_market(symbols, '美股')
    
    # 最新有數據的日期 = 目標日
    target_date_str = dates_with_data[0]
    prev_date_str = dates_with_data[1]
    print(f"  [美股-Polygon] 目標交易日: {target_date_str}")
    
    if target_date_str not in daily_data:
        print(f"  [警告] 目標日 {target_date_str} 無數據")
        return []
    
    target_day = daily_data[target_date_str]
    prev_day = daily_data.get(prev_date_str, {})
    
    # 建立成分股 symbol 集合（去掉後綴）
    symbol_set = set(symbols)
    
    results = []
    for symbol in symbols:
        if symbol not in target_day:
            continue
        
        today = target_day[symbol]
        curr_close = today['close']
        curr_volume = today['volume']
        
        if not curr_close or not curr_volume or curr_volume == 0:
            continue
        
        # 漲跌幅：用前一天收盤價
        prev_close = None
        if symbol in prev_day:
            prev_close = prev_day[symbol]['close']
        
        if not prev_close or prev_close == 0:
            continue
        
        change_pct = ((curr_close - prev_close) / prev_close) * 100
        
        # 量比：當日成交量 / 前 N-1 天平均成交量
        history_volumes = []
        for date_str in dates_with_data[1:]:  # 排除當日
            if date_str in daily_data and symbol in daily_data[date_str]:
                vol = daily_data[date_str][symbol]['volume']
                if vol and vol > 0:
                    history_volumes.append(vol)
        
        if history_volumes:
            avg_volume = sum(history_volumes) / len(history_volumes)
        else:
            avg_volume = curr_volume  # 無歷史數據，量比為 1
        
        volume_ratio = curr_volume / avg_volume if avg_volume > 0 else 1
        
        results.append({
            'symbol': symbol,
            'name': symbol,  # Polygon 不提供公司名，後續可從快取補充
            'current': round(curr_close, 2),
            'previous': round(prev_close, 2),
            'change': round(curr_close - prev_close, 2),
            'change_pct': round(change_pct, 2),
            'volume': int(curr_volume),
            'avg_volume': round(avg_volume),
            'volume_ratio': round(volume_ratio, 2),
            'market': '美股',
        })
    
    print(f"  [美股-Polygon] 成分股匹配: {len(results)}/{len(symbols)} 支")
    
    # 補充公司名稱（從成分股快取）
    _enrich_names(results, 'US')
    
    return results


def _enrich_names(stocks, market_code):
    """從成分股快取補充公司名稱"""
    try:
        with open(COMPONENTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        market = data.get('markets', {}).get(market_code, {})
        name_map = {s['symbol']: s.get('name', s['symbol']) for s in market.get('stocks', [])}
        for stock in stocks:
            if stock['symbol'] in name_map:
                stock['name'] = name_map[stock['symbol']]
    except Exception:
        pass


# ================================================================
#  日股/台股/港股：Yahoo Finance（分批多線程查詢）
# ================================================================

def fetch_single_stock_yf(symbol):
    """用 Yahoo Finance 查詢單支股票的最新交易數據"""
    try:
        client = ApiClient()
        response = client.call_api('YahooFinance/get_stock_chart', query={
            'symbol': symbol,
            'region': 'US',
            'interval': '1d',
            'range': '1mo'
        })

        if not response or 'chart' not in response or 'result' not in response['chart']:
            return None

        result = response['chart']['result'][0]
        meta = result['meta']
        quotes = result['indicators']['quote'][0]
        timestamps = result.get('timestamp', [])

        if len(timestamps) < 5:
            return None

        curr_close = quotes['close'][-1]
        prev_close = quotes['close'][-2]
        curr_volume = quotes['volume'][-1]

        if curr_close is None or prev_close is None or curr_volume is None:
            return None
        if curr_volume == 0:
            return None

        change_pct = ((curr_close - prev_close) / prev_close * 100) if prev_close else 0

        # 計算過去天數的平均成交量（排除最近一天）
        valid_volumes = [v for v in quotes['volume'][:-1] if v is not None and v > 0]
        avg_volume = sum(valid_volumes) / len(valid_volumes) if valid_volumes else curr_volume
        volume_ratio = curr_volume / avg_volume if avg_volume > 0 else 1

        return {
            'symbol': symbol,
            'name': meta.get('longName', meta.get('shortName', symbol)),
            'current': round(curr_close, 2),
            'previous': round(prev_close, 2),
            'change': round(curr_close - prev_close, 2),
            'change_pct': round(change_pct, 2),
            'volume': curr_volume,
            'avg_volume': round(avg_volume),
            'volume_ratio': round(volume_ratio, 2),
        }

    except Exception:
        return None


def yahoo_scan_market(symbols, market_name):
    """
    用 Yahoo Finance 分批多線程掃描一個市場
    
    策略：每批 YF_BATCH_SIZE 支，YF_MAX_WORKERS 線程並行，
    批次間休息 YF_BATCH_DELAY 秒，失敗的自動重試一次
    """
    results = []
    success = 0
    failed_symbols = []
    start_time = time.time()
    total_batches = (len(symbols) + YF_BATCH_SIZE - 1) // YF_BATCH_SIZE

    print(f"  [{market_name}-Yahoo] 開始掃描 {len(symbols)} 支（{total_batches} 批 x {YF_BATCH_SIZE} 支，{YF_MAX_WORKERS} 線程）...")

    # === 第一輪：分批查詢 ===
    for batch_idx in range(0, len(symbols), YF_BATCH_SIZE):
        batch = symbols[batch_idx:batch_idx + YF_BATCH_SIZE]
        batch_num = batch_idx // YF_BATCH_SIZE + 1

        with ThreadPoolExecutor(max_workers=YF_MAX_WORKERS) as executor:
            future_to_symbol = {}
            for symbol in batch:
                future = executor.submit(fetch_single_stock_yf, symbol)
                future_to_symbol[future] = symbol

            for future in as_completed(future_to_symbol):
                sym = future_to_symbol[future]
                data = future.result()
                if data:
                    data['market'] = market_name
                    results.append(data)
                    success += 1
                else:
                    failed_symbols.append(sym)

        elapsed = time.time() - start_time
        print(f"    批次 {batch_num}/{total_batches}: {success} 成功, {len(failed_symbols)} 失敗 ({elapsed:.0f}s)")

        if batch_idx + YF_BATCH_SIZE < len(symbols):
            time.sleep(YF_BATCH_DELAY)

    # === 第二輪：重試失敗的 ===
    if failed_symbols:
        print(f"  [{market_name}-Yahoo] 重試 {len(failed_symbols)} 支失敗股票...")
        time.sleep(YF_RETRY_DELAY)
        
        retry_success = 0
        still_failed = 0

        for batch_idx in range(0, len(failed_symbols), YF_BATCH_SIZE):
            batch = failed_symbols[batch_idx:batch_idx + YF_BATCH_SIZE]

            with ThreadPoolExecutor(max_workers=YF_MAX_WORKERS) as executor:
                future_to_symbol = {}
                for symbol in batch:
                    future = executor.submit(fetch_single_stock_yf, symbol)
                    future_to_symbol[future] = symbol

                for future in as_completed(future_to_symbol):
                    data = future.result()
                    if data:
                        data['market'] = market_name
                        results.append(data)
                        retry_success += 1
                    else:
                        still_failed += 1

            if batch_idx + YF_BATCH_SIZE < len(failed_symbols):
                time.sleep(YF_BATCH_DELAY)

        success += retry_success
        print(f"  [{market_name}-Yahoo] 重試結果: {retry_success} 成功, {still_failed} 仍失敗")

    elapsed = time.time() - start_time
    rate = len(results) / len(symbols) * 100 if symbols else 0
    print(f"  [{market_name}-Yahoo] 掃描完成: {len(results)}/{len(symbols)} 成功 ({rate:.0f}%), 耗時 {elapsed:.1f}s")
    return results


# ================================================================
#  分層漏斗篩選
# ================================================================

def apply_funnel_filter(stocks, market_name):
    """
    分層漏斗篩選

    第一層（硬門檻）：
      - 買入放量：量比 ≥ 1.5x + 上漲 → inflow
      - 賣出放量：量比 ≥ 2.5x + 下跌 → outflow
      - 其餘淘汰

    第二層（排序）：
      - 按漲跌幅絕對值排序（大→小）

    Returns:
        (inflow_list, outflow_list) — 各最多 MAX_PER_FLOW 支
    """
    inflow = []
    outflow = []
    skipped = 0

    for stock in stocks:
        change_pct = stock['change_pct']
        volume_ratio = stock['volume_ratio']

        if change_pct > 0 and volume_ratio >= MIN_VOLUME_RATIO_BUY:
            stock['flow'] = FLOW_BUY
            inflow.append(stock)
        elif change_pct < 0 and volume_ratio >= MIN_VOLUME_RATIO_SELL:
            stock['flow'] = FLOW_SELL
            outflow.append(stock)
        else:
            skipped += 1

    # 第二層：按漲跌幅絕對值排序
    inflow.sort(key=lambda x: abs(x['change_pct']), reverse=True)
    outflow.sort(key=lambda x: abs(x['change_pct']), reverse=True)

    print(f"  [{market_name}] 篩選結果: 買入放量 {len(inflow)} 支, 賣出放量 {len(outflow)} 支, 淘汰 {skipped} 支")

    return inflow[:MAX_PER_FLOW], outflow[:MAX_PER_FLOW]


def apply_news_tiebreaker(stocks, news_trending_tickers):
    """
    第三層：新聞提及作為 tiebreaker
    同漲跌幅時，有新聞提及的排前面
    """
    if not news_trending_tickers:
        for s in stocks:
            s['news_mentions'] = 0
            s['news_sentiment'] = {}
        return stocks

    news_tickers = {t['ticker']: t for t in news_trending_tickers}

    for stock in stocks:
        symbol_base = stock['symbol'].split('.')[0]
        if symbol_base in news_tickers:
            stock['news_mentions'] = news_tickers[symbol_base]['mention_count']
            stock['news_sentiment'] = news_tickers[symbol_base].get('sentiment', {})
        else:
            stock['news_mentions'] = 0
            stock['news_sentiment'] = {}

    # 穩定排序：先按漲跌幅絕對值，再按新聞提及數
    stocks.sort(key=lambda x: (abs(x['change_pct']), x['news_mentions']), reverse=True)
    return stocks


# ================================================================
#  主入口
# ================================================================

def detect_hot_stocks_v2(market_code, market_name, news_trending_tickers=None):
    """
    完整流程：載入成分股 → 掃描 → 分層篩選 → 新聞加分

    Returns:
        dict with 'inflow' and 'outflow' lists
    """
    symbols = load_stock_pool(market_code)
    if not symbols:
        return {'inflow': [], 'outflow': []}

    # 根據市場選擇 API
    if market_code == 'US':
        raw_data = polygon_scan_us_market(symbols)
    else:
        raw_data = yahoo_scan_market(symbols, market_name)

    # 分層漏斗篩選
    inflow, outflow = apply_funnel_filter(raw_data, market_name)

    # 新聞 tiebreaker
    inflow = apply_news_tiebreaker(inflow, news_trending_tickers)
    outflow = apply_news_tiebreaker(outflow, news_trending_tickers)

    return {'inflow': inflow, 'outflow': outflow}


def get_all_hot_stocks(news_trending_tickers=None):
    """
    獲取所有市場的熱門股票

    Returns:
        dict: {
            '美股': {'inflow': [...], 'outflow': [...]},
            '日股': {'inflow': [...], 'outflow': [...]},
            '台股': {'inflow': [...], 'outflow': [...]},
            '港股': {'inflow': [...], 'outflow': [...]},
        }
    """
    markets = [
        ('US', '美股'),
        ('JP', '日股'),
        ('TW', '台股'),
        ('HK', '港股'),
    ]

    results = {}
    total_start = time.time()

    for market_code, market_name in markets:
        print(f"\n{'='*50}")
        print(f"掃描 {market_name}...")
        results[market_name] = detect_hot_stocks_v2(
            market_code, market_name, news_trending_tickers
        )

    total_elapsed = time.time() - total_start
    print(f"\n{'='*50}")
    print(f"全部掃描完成，總耗時: {total_elapsed:.1f}s")

    for market_name, data in results.items():
        in_count = len(data['inflow'])
        out_count = len(data['outflow'])
        print(f"  {market_name}: 買入放量 {in_count} 支, 賣出放量 {out_count} 支")

    return results


# ==================== 向後兼容函數 ====================
def split_by_flow(stocks):
    """將舊格式的股票列表按資金流向分成兩組"""
    inflow = [s for s in stocks if s.get('flow') == FLOW_BUY]
    outflow = [s for s in stocks if s.get('flow') == FLOW_SELL]
    return inflow, outflow


def merge_with_news_tickers(hot_stocks, news_trending_tickers):
    """向後兼容：合併新聞數據"""
    return apply_news_tiebreaker(hot_stocks, news_trending_tickers)


if __name__ == '__main__':
    print(f"買入放量門檻：{MIN_VOLUME_RATIO_BUY}x（量比 + 上漲）")
    print(f"賣出放量門檻：{MIN_VOLUME_RATIO_SELL}x（量比 + 下跌）")
    print(f"每市場上限：買入 {MAX_PER_FLOW} 支 + 賣出 {MAX_PER_FLOW} 支")
    print()

    # 測試美股（Polygon）
    print("=" * 50)
    print("測試美股（Polygon Grouped Daily Bars）...")
    us_symbols = load_stock_pool('US')
    if us_symbols:
        us_data = polygon_scan_us_market(us_symbols[:10])  # 先測 10 支
        print(f"測試結果: {len(us_data)} 支")
        for s in us_data[:3]:
            print(f"  {s['symbol']:8s} {s['change_pct']:+6.2f}% | Vol {s['volume_ratio']:.1f}x")
