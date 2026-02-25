#!/usr/bin/env python3
"""
新聞收集模組 v3
雙來源架構：
  1. NewsAPI.org（主要）— 高品質主流財經媒體新聞（WSJ, CNBC, Bloomberg, Reuters 等）
  2. Polygon.io（補充）— 提供 ticker 關聯度和市場情緒數據

品質控制：
  - 過濾律師事務所集體訴訟廣告
  - 過濾市場研究報告廣告
  - 嚴格日期過濾，只保留目標日期的新聞
  - 去重合併
"""
import os
import re
import json
import requests
from datetime import datetime, timedelta
from collections import Counter

POLYGON_API_KEY = os.environ.get('POLYGON_API_KEY', '')
NEWSAPI_KEY = os.environ.get('NEWSAPI_KEY', '919b1fdb80a340f2b3080464664d7178')

# ─── 垃圾新聞過濾規則 ─────────────────────────────────────────────
# 標題/描述中包含這些關鍵詞的新聞將被過濾掉
JUNK_TITLE_PATTERNS = [
    r'class action',
    r'securities fraud',
    r'shareholder alert',
    r'investor alert',
    r'reminds investors',
    r'encourages.*investors.*to\s+(inquire|contact)',
    r'announces.*class action',
    r'announces.*lawsuit',
    r'investigating.*securities',
    r'lead plaintiff deadline',
    r'securities litigation',
    r'loss recovery',
    r'investors with.*losses',
]

# 已知的律師事務所 / 垃圾來源 publisher 名稱
JUNK_PUBLISHERS = {
    'halper sadeh', 'bragar eagel', 'rosen law', 'robbins llp',
    'bernstein liebhard', 'pomerantz', 'levi & korsinsky',
    'kessler topaz', 'schall law', 'faruqi & faruqi',
    'bronstein, gewirtz', 'rigrodsky & long', 'johnson fistel',
    'kirby mcinerney', 'glancy prongay', 'block & leviton',
    'scott+scott', 'labaton sucharow',
}

# 編譯正則表達式（提升效能）
_JUNK_RE = re.compile('|'.join(JUNK_TITLE_PATTERNS), re.IGNORECASE)


def _is_junk_article(article):
    """判斷是否為垃圾新聞（律師事務所廣告、訴訟招攬等）"""
    title = article.get('title', '')
    desc = article.get('description', '') or ''
    publisher = article.get('publisher', '').lower()

    # 檢查 publisher 是否為已知垃圾來源
    for junk_pub in JUNK_PUBLISHERS:
        if junk_pub in publisher:
            return True

    # 檢查標題和描述是否匹配垃圾模式
    combined = f"{title} {desc}"
    if _JUNK_RE.search(combined):
        return True

    return False


# ─── NewsAPI.org 新聞來源 ──────────────────────────────────────────

def get_newsapi_headlines(category='business', country='us', page_size=50):
    """從 NewsAPI 獲取頭條新聞"""
    try:
        resp = requests.get('https://newsapi.org/v2/top-headlines', params={
            'category': category,
            'country': country,
            'pageSize': page_size,
            'apiKey': NEWSAPI_KEY,
        }, timeout=15)
        data = resp.json()
        if data.get('status') != 'ok':
            print(f"  NewsAPI headlines error: {data.get('message', 'unknown')}")
            return []
        return _process_newsapi_articles(data.get('articles', []))
    except Exception as e:
        print(f"  NewsAPI headlines error: {e}")
        return []


def get_newsapi_everything(query, from_date, to_date, sort_by='relevancy', page_size=30):
    """從 NewsAPI 搜尋特定主題的新聞"""
    try:
        resp = requests.get('https://newsapi.org/v2/everything', params={
            'q': query,
            'language': 'en',
            'sortBy': sort_by,
            'from': from_date,
            'to': to_date,
            'pageSize': page_size,
            'apiKey': NEWSAPI_KEY,
        }, timeout=15)
        data = resp.json()
        if data.get('status') != 'ok':
            print(f"  NewsAPI everything error: {data.get('message', 'unknown')}")
            return []
        return _process_newsapi_articles(data.get('articles', []))
    except Exception as e:
        print(f"  NewsAPI everything error: {e}")
        return []


def _process_newsapi_articles(raw_articles):
    """處理 NewsAPI 返回的文章，轉換為統一格式"""
    processed = []
    for article in raw_articles:
        # 跳過被移除的文章
        if article.get('title') == '[Removed]':
            continue

        processed.append({
            'title': article.get('title', ''),
            'description': article.get('description', '') or '',
            'publisher': article.get('source', {}).get('name', ''),
            'published_utc': article.get('publishedAt', ''),
            'tickers': [],  # NewsAPI 不提供 tickers，後續由 Polygon 補充
            'keywords': [],
            'insights': [],
            'url': article.get('url', ''),
            'source': 'newsapi',
        })
    return processed


# ─── Polygon.io 新聞來源（補充） ──────────────────────────────────

def get_polygon_news(limit=100, ticker=None, published_after=None, published_before=None):
    """從 Polygon.io 獲取金融新聞，支持日期範圍過濾"""
    params = {
        'limit': limit,
        'apiKey': POLYGON_API_KEY,
        'order': 'desc',
        'sort': 'published_utc',
    }
    if ticker:
        params['ticker'] = ticker
    if published_after:
        params['published_utc.gte'] = published_after
    if published_before:
        params['published_utc.lte'] = published_before

    try:
        url = "https://api.polygon.io/v2/reference/news"
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        articles = data.get('results', [])

        processed = []
        for article in articles:
            pub_date = article.get('published_utc', '')
            processed.append({
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'publisher': article.get('publisher', {}).get('name', ''),
                'published_utc': pub_date,
                'tickers': article.get('tickers', []),
                'keywords': article.get('keywords', []),
                'insights': article.get('insights', []),
                'url': article.get('article_url', ''),
                'source': 'polygon',
            })
        return processed
    except Exception as e:
        print(f"  Polygon news error: {e}")
        return []


# ─── 日期過濾 ─────────────────────────────────────────────────────

def filter_articles_by_date(articles, target_date_str):
    """嚴格過濾：只保留目標日期當天的新聞"""
    filtered = []
    for article in articles:
        pub_utc = article.get('published_utc', '')
        if pub_utc:
            article_date = pub_utc[:10]  # 取 YYYY-MM-DD
            if article_date == target_date_str:
                filtered.append(article)
    return filtered


# ─── Ticker 關聯度提取 ────────────────────────────────────────────

def get_trending_tickers_from_news(articles):
    """從新聞中提取熱門股票（出現頻率最高的 tickers）"""
    ticker_counter = Counter()
    ticker_sentiment = {}

    for article in articles:
        for ticker in article.get('tickers', []):
            ticker_counter[ticker] += 1

        for insight in article.get('insights', []):
            t = insight.get('ticker', '')
            sentiment = insight.get('sentiment', 'neutral')
            reasoning = insight.get('sentiment_reasoning', '')
            if t:
                if t not in ticker_sentiment:
                    ticker_sentiment[t] = {'positive': 0, 'negative': 0, 'neutral': 0, 'reasons': []}
                ticker_sentiment[t][sentiment] = ticker_sentiment[t].get(sentiment, 0) + 1
                if reasoning:
                    ticker_sentiment[t]['reasons'].append(reasoning)

    top_tickers = ticker_counter.most_common(20)

    results = []
    for ticker, count in top_tickers:
        sentiment_info = ticker_sentiment.get(ticker, {})
        results.append({
            'ticker': ticker,
            'mention_count': count,
            'sentiment': sentiment_info,
        })

    return results


# ─── 新聞分類 ─────────────────────────────────────────────────────

def categorize_news(articles):
    """將新聞分類為宏觀事件類別"""
    categories = {
        'central_bank': [],
        'economic_data': [],
        'geopolitics': [],
        'tech_industry': [],
        'commodities': [],
        'crypto': [],
        'earnings': [],
        'other': [],
    }

    rules = {
        'central_bank': ['fed', 'federal reserve', 'ecb', 'boj', 'pboc', 'rate cut', 'rate hike',
                         'interest rate', 'monetary policy', 'inflation target', 'quantitative',
                         'central bank', 'fomc', 'powell', 'lagarde'],
        'economic_data': ['gdp', 'cpi', 'ppi', 'employment', 'payroll', 'jobs report', 'retail sales',
                          'unemployment', 'inflation', 'consumer price', 'producer price',
                          'manufacturing', 'pmi', 'trade balance', 'housing'],
        'geopolitics': ['tariff', 'sanction', 'trade war', 'geopolitical', 'war', 'conflict',
                        'nuclear', 'iran', 'china', 'russia', 'ukraine', 'middle east', 'trump',
                        'election', 'government shutdown', 'executive order', 'policy'],
        'tech_industry': ['ai', 'artificial intelligence', 'semiconductor', 'chip', 'nvidia',
                          'openai', 'tech', 'software', 'data center', 'cloud'],
        'commodities': ['gold', 'oil', 'crude', 'silver', 'copper', 'commodity', 'opec',
                        'precious metal', 'natural gas', 'energy'],
        'crypto': ['bitcoin', 'ethereum', 'crypto', 'blockchain', 'token', 'defi', 'btc', 'eth'],
        'earnings': ['earnings', 'revenue', 'profit', 'quarterly', 'fiscal', 'guidance',
                     'beat expectations', 'miss expectations', 'financial results'],
    }

    for article in articles:
        text = (article.get('title', '') + ' ' + article.get('description', '')).lower()
        categorized = False

        for category, keywords in rules.items():
            if any(kw in text for kw in keywords):
                categories[category].append(article)
                categorized = True
                break

        if not categorized:
            categories['other'].append(article)

    return categories


# ─── 主入口：雙來源新聞收集 ───────────────────────────────────────

def get_news_for_date(target_date=None):
    """
    獲取指定日期的新聞（雙來源架構）

    1. NewsAPI（主要）：高品質主流財經媒體新聞
       - Top Headlines（商業類）
       - Everything（多主題搜尋：宏觀、科技、大宗商品、地緣政治）
    2. Polygon（補充）：提供 ticker 關聯度
    3. 品質過濾：移除律師事務所廣告等垃圾新聞
    4. 去重合併
    """
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"  新聞目標日期: {target_date}")
    all_articles = []

    # ── 來源 1：NewsAPI Top Headlines ──
    print(f"  [NewsAPI] 抓取 Top Headlines...")
    headlines = get_newsapi_headlines(category='business', page_size=50)
    headlines = filter_articles_by_date(headlines, target_date)
    print(f"    Top Headlines (當日): {len(headlines)} 篇")
    all_articles.extend(headlines)

    # ── 來源 2：NewsAPI Everything（多主題搜尋） ──
    search_queries = [
        ('stock market OR Wall Street OR S&P 500 OR Dow Jones OR NASDAQ', '股市'),
        ('Fed OR interest rate OR central bank OR monetary policy', '央行'),
        ('NVIDIA OR semiconductor OR AI chip OR data center', 'AI/科技'),
        ('oil price OR gold price OR commodity OR OPEC', '大宗商品'),
        ('tariff OR trade war OR geopolitics OR sanctions', '地緣政治'),
        ('earnings OR quarterly results OR revenue guidance', '財報'),
        ('bitcoin OR crypto OR ethereum', '加密貨幣'),
        ('merger OR acquisition OR IPO OR buyout', '併購/IPO'),
    ]

    for query, label in search_queries:
        print(f"  [NewsAPI] 搜尋 {label}...")
        articles = get_newsapi_everything(
            query=query,
            from_date=target_date,
            to_date=target_date,
            sort_by='relevancy',
            page_size=15
        )
        articles = filter_articles_by_date(articles, target_date)
        print(f"    {label}: {len(articles)} 篇")
        all_articles.extend(articles)

    # ── 來源 3：Polygon（補充 ticker 關聯） ──
    published_after = f"{target_date}T00:00:00Z"
    published_before = f"{target_date}T23:59:59Z"
    print(f"  [Polygon] 抓取新聞（ticker 關聯）...")
    polygon_articles = get_polygon_news(
        limit=100,
        published_after=published_after,
        published_before=published_before
    )
    polygon_articles = filter_articles_by_date(polygon_articles, target_date)
    print(f"    Polygon 新聞: {len(polygon_articles)} 篇")
    all_articles.extend(polygon_articles)

    # ── 品質過濾：移除垃圾新聞 ──
    before_filter = len(all_articles)
    all_articles = [a for a in all_articles if not _is_junk_article(a)]
    junk_removed = before_filter - len(all_articles)
    print(f"  垃圾新聞過濾: 移除 {junk_removed} 篇（律師事務所廣告等）")

    # ── 去重（根據標題相似度） ──
    seen_titles = set()
    unique_articles = []
    for article in all_articles:
        title = article.get('title', '').strip()
        if not title:
            continue
        # 簡單去重：完全相同標題
        title_key = title.lower()[:80]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_articles.append(article)

    all_articles = unique_articles
    print(f"  去重後總新聞數: {len(all_articles)}")

    # ── 按來源品質排序（NewsAPI 優先） ──
    def _article_priority(a):
        # NewsAPI 來源排前面
        source_score = 0 if a.get('source') == 'newsapi' else 1
        # 有 ticker 關聯的排前面
        ticker_score = 0 if a.get('tickers') else 1
        return (source_score, ticker_score)

    all_articles.sort(key=_article_priority)

    return {
        'articles': all_articles,
        'categorized': categorize_news(all_articles),
        'trending_tickers': get_trending_tickers_from_news(all_articles),
        'date': target_date,
    }


if __name__ == '__main__':
    data = get_news_for_date('2026-02-24')
    with open('/home/ubuntu/daily-macro-report/reports/news_test.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n新聞收集完成 - {data['date']}")
    print(f"總新聞數: {len(data['articles'])}")

    print(f"\n前 10 篇新聞:")
    for a in data['articles'][:10]:
        src = a.get('source', 'unknown')
        pub = a.get('publisher', '')
        title = a.get('title', '')[:80]
        print(f"  [{src}|{pub}] {title}")

    print(f"\n新聞分類:")
    for cat, articles in data['categorized'].items():
        if articles:
            print(f"  {cat}: {len(articles)} articles")

    print(f"\n熱門股票:")
    for t in data['trending_tickers'][:10]:
        print(f"  {t['ticker']}: {t['mention_count']} mentions")
