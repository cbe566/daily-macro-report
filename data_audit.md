# 數據來源審查結果 (2026-02-26)

## 1. 市場指數（data_api → Yahoo Finance）
- S&P 500: 最新 timestamp = 2026-02-26 06:19 (2/25 收盤) ✅ 正確
- 亞洲指數: 2/25-2/26 盤中數據 ✅ 正確
- 歐洲指數: 2/26 凌晨收盤 ✅ 正確
- **結論: data_api 的指數數據是即時的，沒有問題**

## 2. 大宗商品、外匯、債券（data_api → Yahoo Finance）
- 黃金、原油等: timestamp 都是 2/26 ✅ 正確
- **結論: 沒有問題**

## 3. 加密貨幣（data_api → Yahoo Finance）
- BTC, ETH, SOL: 最新 close 有值，但 2/25 08:00 的 close = None
- data_api 的 fetch_quote 邏輯是「從後往前找最新有效 close」，所以會跳過 None
- BTC 最新: 68297 (2/26 09:03) vs 前一天: 64080 (2/24 08:00)
- **問題: 因為 2/25 close=None，漲跌幅計算會用 2/24 的 close 作為 prev_close**
- **這會導致漲跌幅計算不準確（跨了兩天）**
- 但這是 Yahoo Finance 數據本身的問題（當天未結束的 bar close=None）
- **影響程度: 中等，加密貨幣漲跌幅可能偏差**

## 4. 熱門股票 — 美股（Polygon Grouped Daily Bars）
- **問題: Polygon 免費方案無法取得當天（2/25 美東時間）的數據**
- 2/25 回傳 NOT_AUTHORIZED: "Attempted to request today's data before end of day"
- 導致最新數據停在 2/24
- **影響程度: 嚴重 — 美股熱門股票用的是前一天的數據**
- **解決方案: 改用 yfinance 批量下載，測試 536 支耗時 74 秒，成功率 96%**

## 5. 熱門股票 — 日股/台股/港股（Yahoo Finance via data_api）
- 使用 data_api 的 ApiClient，數據即時 ✅
- 但成功率偏低（台股 66%、港股 68%），可能是 data_api 限流
- **可考慮也改用 yfinance 直接查詢提高成功率**

## 修正計畫
1. **美股熱門股票**: Polygon → yfinance (yf.download 批量)
2. **加密貨幣**: 加密貨幣 close=None 的問題需要處理
3. **成分股快取**: 清理行業名稱（19 個非 ticker 的項目）
