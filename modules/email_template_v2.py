"""
Morning Briefing Email Template v2.0
=====================================
專業級晨報郵件模板 — 參考 Goldman Sachs / JPMorgan / Bloomberg 風格

設計原則：
1. 敘事導向（Narrative-driven）而非數據堆砌
2. 兩分鐘可讀完（scannable）
3. 先結論後細節（inverted pyramid）
4. 明確的 "So What" — 每條資訊都帶觀點
5. Email 正文只做摘要引導，完整數據留給 PDF 附件

佔位符說明：
  {report_date}          — 報告日期，如 "2026-03-28"
  {market_verdict}       — 一句話市場定調
  {verdict_color}        — 定調顏色 (#27ae60 多頭 / #e74c3c 空頭 / #e67e22 中性)
  {focus_1_title}        — 焦點一標題
  {focus_1_body}         — 焦點一說明（2-3 句）
  {focus_2_title}        — 焦點二標題
  {focus_2_body}         — 焦點二說明
  {focus_3_title}        — 焦點三標題
  {focus_3_body}         — 焦點三說明
  {sp500_val}            — S&P 500 收盤值
  {sp500_pct}            — S&P 500 漲跌幅（含 +/- 號）
  {sp500_color}          — 漲跌顏色
  {nasdaq_val}           — Nasdaq 收盤值
  {nasdaq_pct}           — Nasdaq 漲跌幅
  {nasdaq_color}         — 漲跌顏色
  {dxy_val}              — 美元指數
  {dxy_pct}              — 美元指數漲跌幅
  {dxy_color}            — 漲跌顏色
  {us10y_val}            — 美國10年期殖利率
  {us10y_pct}            — 變動幅度
  {us10y_color}          — 漲跌顏色
  {vix_val}              — VIX 值
  {vix_color}            — VIX 顏色
  {gold_val}             — 黃金價格
  {gold_pct}             — 黃金漲跌幅
  {gold_color}           — 漲跌顏色
  {btc_val}              — BTC 價格
  {btc_pct}              — BTC 漲跌幅
  {btc_color}            — 漲跌顏色
  {oil_val}              — 原油價格
  {oil_pct}              — 原油漲跌幅
  {oil_color}            — 漲跌顏色
  {risk_items}           — 風險項目 HTML（<li> 列表）
  {opportunity_items}    — 機會項目 HTML（<li> 列表）
  {watch_items}          — 今日關注 HTML（<li> 列表）
  {sender_name}          — 發送者姓名
  {holiday_alert_html}   — 休市提醒 HTML（可為空字串）
"""


def get_morning_briefing_template():
    """返回專業晨報 HTML 郵件模板字串"""

    return '''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>每日宏觀早報</title>
</head>
<body style="margin:0;padding:0;background-color:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'PingFang TC','Microsoft JhengHei','Helvetica Neue',Arial,sans-serif;-webkit-font-smoothing:antialiased;">

<!-- Outer wrapper -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f0f2f5;">
<tr><td align="center" style="padding:24px 16px;">

<!-- Main container -->
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 1px 8px rgba(0,0,0,0.06);">

<!-- ============ HEADER ============ -->
<tr>
<td style="background:linear-gradient(135deg,#0f2027 0%,#203a43 50%,#2c5364 100%);padding:24px 32px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td>
      <div style="font-size:11px;letter-spacing:2px;color:rgba(255,255,255,0.6);text-transform:uppercase;margin-bottom:6px;">Daily Macro Briefing</div>
      <div style="font-size:20px;font-weight:700;color:#ffffff;letter-spacing:0.5px;">每日宏觀早報</div>
      <div style="font-size:13px;color:rgba(255,255,255,0.7);margin-top:4px;">{report_date}</div>
    </td>
    <td align="right" valign="top">
      <div style="font-size:11px;color:rgba(255,255,255,0.5);text-align:right;">Research Note</div>
    </td>
  </tr>
  </table>
</td>
</tr>

<!-- ============ HOLIDAY ALERT (conditional) ============ -->
{holiday_alert_html}

<!-- ============ SECTION 1: 市場判斷 ============ -->
<tr>
<td style="padding:28px 32px 0 32px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-left:4px solid {verdict_color};padding-left:20px;">
  <tr>
    <td>
      <div style="font-size:11px;letter-spacing:1.5px;color:#999;text-transform:uppercase;margin-bottom:6px;">Market Verdict</div>
      <div style="font-size:17px;font-weight:700;color:#1a1a1a;line-height:1.5;">{market_verdict}</div>
    </td>
  </tr>
  </table>
</td>
</tr>

<!-- ============ SECTION 2: 三大焦點 ============ -->
<tr>
<td style="padding:28px 32px 0 32px;">
  <div style="font-size:13px;font-weight:700;letter-spacing:1px;color:#999;text-transform:uppercase;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #eee;">Key Focus</div>

  <!-- Focus 1 -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
  <tr>
    <td width="28" valign="top">
      <div style="width:24px;height:24px;border-radius:50%;background:#0f2027;color:#fff;font-size:12px;font-weight:700;line-height:24px;text-align:center;">1</div>
    </td>
    <td style="padding-left:12px;">
      <div style="font-size:14px;font-weight:700;color:#1a1a1a;margin-bottom:4px;">{focus_1_title}</div>
      <div style="font-size:13px;color:#555;line-height:1.7;">{focus_1_body}</div>
    </td>
  </tr>
  </table>

  <!-- Focus 2 -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;">
  <tr>
    <td width="28" valign="top">
      <div style="width:24px;height:24px;border-radius:50%;background:#0f2027;color:#fff;font-size:12px;font-weight:700;line-height:24px;text-align:center;">2</div>
    </td>
    <td style="padding-left:12px;">
      <div style="font-size:14px;font-weight:700;color:#1a1a1a;margin-bottom:4px;">{focus_2_title}</div>
      <div style="font-size:13px;color:#555;line-height:1.7;">{focus_2_body}</div>
    </td>
  </tr>
  </table>

  <!-- Focus 3 -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:4px;">
  <tr>
    <td width="28" valign="top">
      <div style="width:24px;height:24px;border-radius:50%;background:#0f2027;color:#fff;font-size:12px;font-weight:700;line-height:24px;text-align:center;">3</div>
    </td>
    <td style="padding-left:12px;">
      <div style="font-size:14px;font-weight:700;color:#1a1a1a;margin-bottom:4px;">{focus_3_title}</div>
      <div style="font-size:13px;color:#555;line-height:1.7;">{focus_3_body}</div>
    </td>
  </tr>
  </table>
</td>
</tr>

<!-- ============ SECTION 3: 關鍵指標速覽 ============ -->
<tr>
<td style="padding:28px 32px 0 32px;">
  <div style="font-size:13px;font-weight:700;letter-spacing:1px;color:#999;text-transform:uppercase;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #eee;">Key Metrics</div>

  <!-- Row 1: Equities + USD -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td width="25%" style="padding:8px 6px;">
      <div style="background:#f8f9fb;border-radius:6px;padding:12px 14px;">
        <div style="font-size:10px;color:#999;letter-spacing:0.5px;">S&P 500</div>
        <div style="font-size:16px;font-weight:700;color:#1a1a1a;margin:4px 0 2px;">{sp500_val}</div>
        <div style="font-size:12px;font-weight:600;color:{sp500_color};">{sp500_pct}</div>
      </div>
    </td>
    <td width="25%" style="padding:8px 6px;">
      <div style="background:#f8f9fb;border-radius:6px;padding:12px 14px;">
        <div style="font-size:10px;color:#999;letter-spacing:0.5px;">Nasdaq</div>
        <div style="font-size:16px;font-weight:700;color:#1a1a1a;margin:4px 0 2px;">{nasdaq_val}</div>
        <div style="font-size:12px;font-weight:600;color:{nasdaq_color};">{nasdaq_pct}</div>
      </div>
    </td>
    <td width="25%" style="padding:8px 6px;">
      <div style="background:#f8f9fb;border-radius:6px;padding:12px 14px;">
        <div style="font-size:10px;color:#999;letter-spacing:0.5px;">DXY</div>
        <div style="font-size:16px;font-weight:700;color:#1a1a1a;margin:4px 0 2px;">{dxy_val}</div>
        <div style="font-size:12px;font-weight:600;color:{dxy_color};">{dxy_pct}</div>
      </div>
    </td>
    <td width="25%" style="padding:8px 6px;">
      <div style="background:#f8f9fb;border-radius:6px;padding:12px 14px;">
        <div style="font-size:10px;color:#999;letter-spacing:0.5px;">US 10Y</div>
        <div style="font-size:16px;font-weight:700;color:#1a1a1a;margin:4px 0 2px;">{us10y_val}</div>
        <div style="font-size:12px;font-weight:600;color:{us10y_color};">{us10y_pct}</div>
      </div>
    </td>
  </tr>
  </table>

  <!-- Row 2: VIX + Commodities + Crypto -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td width="25%" style="padding:8px 6px;">
      <div style="background:#f8f9fb;border-radius:6px;padding:12px 14px;">
        <div style="font-size:10px;color:#999;letter-spacing:0.5px;">VIX</div>
        <div style="font-size:16px;font-weight:700;color:{vix_color};margin:4px 0 2px;">{vix_val}</div>
        <div style="font-size:10px;color:#999;">波動率指數</div>
      </div>
    </td>
    <td width="25%" style="padding:8px 6px;">
      <div style="background:#f8f9fb;border-radius:6px;padding:12px 14px;">
        <div style="font-size:10px;color:#999;letter-spacing:0.5px;">Gold</div>
        <div style="font-size:16px;font-weight:700;color:#1a1a1a;margin:4px 0 2px;">{gold_val}</div>
        <div style="font-size:12px;font-weight:600;color:{gold_color};">{gold_pct}</div>
      </div>
    </td>
    <td width="25%" style="padding:8px 6px;">
      <div style="background:#f8f9fb;border-radius:6px;padding:12px 14px;">
        <div style="font-size:10px;color:#999;letter-spacing:0.5px;">WTI Oil</div>
        <div style="font-size:16px;font-weight:700;color:#1a1a1a;margin:4px 0 2px;">{oil_val}</div>
        <div style="font-size:12px;font-weight:600;color:{oil_color};">{oil_pct}</div>
      </div>
    </td>
    <td width="25%" style="padding:8px 6px;">
      <div style="background:#f8f9fb;border-radius:6px;padding:12px 14px;">
        <div style="font-size:10px;color:#999;letter-spacing:0.5px;">Bitcoin</div>
        <div style="font-size:16px;font-weight:700;color:#1a1a1a;margin:4px 0 2px;">{btc_val}</div>
        <div style="font-size:12px;font-weight:600;color:{btc_color};">{btc_pct}</div>
      </div>
    </td>
  </tr>
  </table>
</td>
</tr>

<!-- ============ SECTION 4: 風險與機會 ============ -->
<tr>
<td style="padding:28px 32px 0 32px;">
  <div style="font-size:13px;font-weight:700;letter-spacing:1px;color:#999;text-transform:uppercase;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #eee;">Risk &amp; Opportunity</div>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <!-- Risks -->
    <td width="50%" valign="top" style="padding-right:12px;">
      <div style="background:#fef5f5;border-radius:6px;padding:14px 16px;">
        <div style="font-size:12px;font-weight:700;color:#c0392b;margin-bottom:8px;letter-spacing:0.5px;">RISK</div>
        <ul style="margin:0;padding-left:16px;font-size:12px;color:#555;line-height:1.8;">
          {risk_items}
        </ul>
      </div>
    </td>
    <!-- Opportunities -->
    <td width="50%" valign="top" style="padding-left:12px;">
      <div style="background:#f0faf0;border-radius:6px;padding:14px 16px;">
        <div style="font-size:12px;font-weight:700;color:#27ae60;margin-bottom:8px;letter-spacing:0.5px;">OPPORTUNITY</div>
        <ul style="margin:0;padding-left:16px;font-size:12px;color:#555;line-height:1.8;">
          {opportunity_items}
        </ul>
      </div>
    </td>
  </tr>
  </table>
</td>
</tr>

<!-- ============ SECTION 5: 今日關注 ============ -->
<tr>
<td style="padding:28px 32px 0 32px;">
  <div style="font-size:13px;font-weight:700;letter-spacing:1px;color:#999;text-transform:uppercase;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #eee;">What to Watch</div>
  <ul style="margin:0;padding-left:18px;font-size:13px;color:#333;line-height:2.0;">
    {watch_items}
  </ul>
</td>
</tr>

<!-- ============ SECTION 6: 附件提示 ============ -->
<tr>
<td style="padding:28px 32px;">
  <div style="background:linear-gradient(135deg,#f8f9fb 0%,#eef1f5 100%);border-radius:6px;padding:16px 20px;text-align:center;border:1px solid #e8eaed;">
    <div style="font-size:13px;font-weight:600;color:#333;">完整數據、圖表及各區域指數明細，請參閱附件 PDF 報告</div>
    <div style="font-size:11px;color:#999;margin-top:6px;">Full report with charts, tables, and regional breakdowns attached</div>
  </div>
</td>
</tr>

<!-- ============ FOOTER ============ -->
<tr>
<td style="background:#f8f9fb;padding:20px 32px;border-top:1px solid #eee;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td>
      <div style="font-size:12px;color:#666;">{sender_name}</div>
      <div style="font-size:10px;color:#bbb;margin-top:4px;">每日宏觀早報 | Daily Macro Briefing</div>
    </td>
    <td align="right" valign="bottom">
      <div style="font-size:9px;color:#ccc;">此為自動發送，請勿直接回覆</div>
      <div style="font-size:9px;color:#ddd;margin-top:2px;">Yahoo Finance / Polygon / S&P Global / CNBC / Investing.com</div>
    </td>
  </tr>
  </table>
</td>
</tr>

</table>
<!-- /Main container -->

</td></tr>
</table>
<!-- /Outer wrapper -->

</body>
</html>'''


def get_holiday_alert_block():
    """返回休市提醒 HTML 區塊模板（嵌入 header 下方）"""
    return '''<tr>
<td style="padding:0 32px;">
  <div style="background:#fffbeb;border-left:3px solid #f59e0b;padding:10px 16px;margin-top:0;font-size:12px;color:#92400e;line-height:1.6;">
    {holiday_text}
  </div>
</td>
</tr>'''


def build_list_items(items):
    """將文字列表轉為 <li> HTML 字串

    Args:
        items: list of str，每一條為一個要點

    Returns:
        str: 拼接好的 <li>...</li> HTML
    """
    return '\n          '.join(f'<li>{item}</li>' for item in items)


def format_pct(pct):
    """格式化漲跌幅為帶正負號字串"""
    if pct is None:
        return "N/A"
    return f"{pct:+.2f}%"


def pct_color(pct):
    """根據漲跌幅返回顏色"""
    if pct is None or pct == 0:
        return "#666"
    return "#27ae60" if pct > 0 else "#e74c3c"


def vix_color_fn(val):
    """根據 VIX 值返回顏色"""
    if val is None:
        return "#666"
    if val < 18:
        return "#27ae60"
    if val < 25:
        return "#e67e22"
    return "#e74c3c"


def verdict_color_fn(sentiment):
    """根據情緒返回顏色

    Args:
        sentiment: 'bullish', 'bearish', or 'neutral'
    """
    return {
        'bullish': '#27ae60',
        'bearish': '#e74c3c',
        'neutral': '#e67e22',
    }.get(sentiment, '#e67e22')


# ============ EXAMPLE USAGE ============
if __name__ == '__main__':
    # 範例：用假數據填充模板
    template = get_morning_briefing_template()

    sample_data = {
        'report_date': '2026-03-28',
        'market_verdict': '關稅陰霾壓制風險偏好，美股連續第二日回落；資金轉向防禦性資產，黃金與美債同步走強。短期市場情緒偏空，但超賣訊號浮現。',
        'verdict_color': '#e74c3c',
        'focus_1_title': '美國對等關稅政策 4/2 生效在即',
        'focus_1_body': '白宮確認 4 月 2 日將啟動新一輪對等關稅，涵蓋汽車、半導體等關鍵產業。市場擔憂供應鏈成本攀升，費城半導體指數單日下挫 2.3%。企業端已出現提前拉貨跡象，短期進口數據可能失真。',
        'focus_2_title': 'Fed 利率路徑重新定價',
        'focus_2_body': '聯邦基金利率期貨顯示 6 月降息機率降至 40%，較一週前大幅回落。鮑威爾重申「需要看到更多數據」，通膨黏性與就業韌性使 Fed 陷入兩難。利率市場目前定價全年僅降息一碼。',
        'focus_3_title': '中國 PMI 邊際改善但力度不足',
        'focus_3_body': '3 月官方製造業 PMI 報 50.5，重回擴張區間但低於預期的 51.0。新出口訂單分項仍在收縮，反映外需受關稅預期拖累。政策面預計將加大內需刺激力度。',
        'sp500_val': '5,580',
        'sp500_pct': '-0.87%',
        'sp500_color': '#e74c3c',
        'nasdaq_val': '17,322',
        'nasdaq_pct': '-1.21%',
        'nasdaq_color': '#e74c3c',
        'dxy_val': '104.3',
        'dxy_pct': '+0.15%',
        'dxy_color': '#27ae60',
        'us10y_val': '4.22%',
        'us10y_pct': '-3bp',
        'us10y_color': '#27ae60',
        'vix_val': '22.5',
        'vix_color': '#e67e22',
        'gold_val': '$3,082',
        'gold_pct': '+0.64%',
        'gold_color': '#27ae60',
        'oil_val': '$69.8',
        'oil_pct': '-1.12%',
        'oil_color': '#e74c3c',
        'btc_val': '$84,200',
        'btc_pct': '-2.34%',
        'btc_color': '#e74c3c',
        'risk_items': build_list_items([
            '4/2 關稅落地後若超預期，可能觸發新一輪拋售',
            'VIX 維持 20 以上，短期波動率偏高',
            '科技股集中度風險 — Mag7 估值仍處歷史高位',
        ]),
        'opportunity_items': build_list_items([
            'S&P 500 RSI 跌至 24，技術面超賣反彈機率升高',
            '黃金突破 $3,050 後動能強勁，避險配置仍有空間',
            '中國刺激政策預期升溫，港股估值具吸引力',
        ]),
        'watch_items': build_list_items([
            '20:30 美國 PCE 物價指數（Fed 首選通膨指標）— 預期 +2.7% YoY',
            '22:00 密歇根大學消費者信心指數終值',
            '關注歐盟對美國關稅反制措施的最新表態',
            'A 股、港股季末資金面變動',
        ]),
        'sender_name': '何宣逸',
        'holiday_alert_html': '',
    }

    html = template.format(**sample_data)

    # 寫出預覽
    import os
    preview_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports', 'email_preview_v2.html')
    with open(preview_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Preview saved to {preview_path}")
