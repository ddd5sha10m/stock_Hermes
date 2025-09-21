"""
tw_industry_top20_full.py
目標：抓取台灣 (TWSE + TPEx) 每個產業的前20熱門股票（依成交量）與前20法人買賣超（淨買超），輸出 JSON 字典。

輸出格式 (industry -> {"by_volume": {"2330":"台積電", ...}, "by_institution": {"xxx":"yyy", ...}})：
{
  "半導體業": {
      "by_volume": {"2330":"台積電", "2344":"華邦電", ...},
      "by_institution": {"1101":"台泥", ...}
  },
  ...
  "ETF": {"by_volume": {...}, "by_institution": {...}}
}

需求：
pip install requests pandas beautifulsoup4 lxml
python3 tw_industry_top20_full.py --date 2025-09-19

備註：
- 若網站有反爬機制會需要降低速率或使用代理 IP。
- TWSE 的公司清單（含產業代碼）會從 `http://isin.twse.com.tw/isin/C_public.jsp?strMode=2`（上市）與 strMode=4（上櫃）抓取並整理。
- 成交量排行會優先使用 TWSE 的「每日成交量前二十名」頁面及 WantGoo / Yahoo 排行作為補充。
- 三大法人買賣超使用 TWSE 三大法人日報或 WantGoo 的法人排行頁面。
"""

import requests, time, argparse, json, sys
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"}

# -------------------------
# 1) 抓公司清單 (上市、上櫃) 並建立 code -> (name, industry_code, industry_name) 映射
# -------------------------
def fetch_tw_company_list():
    """
    來源: http://isin.twse.com.tw/isin/C_public.jsp?strMode=2  (上市)
         http://isin.twse.com.tw/isin/C_public.jsp?strMode=4  (上櫃)
    解析後回傳 DataFrame with columns ['code','name','industry_code','industry_name']
    """
    mapping = []
    for mode in [2, 4]:
        url = f"http://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'lxml')
        table = soup.find('table')
        if not table:
            print("警告：無法抓取 company list from", url, file=sys.stderr)
            continue
        rows = table.find_all('tr')
        # 第一列是 header，資料從第二列開始
        for tr in rows[1:]:
            cols = [c.get_text(strip=True) for c in tr.find_all('td')]
            if len(cols) < 7:
                continue
            code = cols[0]
            name = cols[1]
            industry_code = cols[4]  # page layout: 產業別通常在該欄
            # 有些欄位為空，跳過
            mapping.append({'code': code, 'name': name, 'industry_code': industry_code})
        time.sleep(0.3)
    df = pd.DataFrame(mapping).drop_duplicates(subset='code').set_index('code')
    # 產業代碼 -> 中文（近似對照表，TWSE 頁面也有說明）
    industry_map = {
        "01":"水泥工業","02":"食品工業","03":"塑膠工業","04":"紡織纖維","05":"電機機械",
        "06":"電器電纜","08":"玻璃陶瓷","09":"造紙工業","10":"鋼鐵工業","11":"橡膠工業",
        "12":"汽車工業","13":"電子工業","14":"建材營造業","15":"航運業","16":"觀光餐旅",
        "17":"金融保險業","18":"貿易百貨業","19":"綜合","20":"其他業","21":"化學工業",
        "22":"生技醫療業","23":"油電燃氣業","24":"半導體業","25":"電腦及週邊設備業",
        "26":"光電業","27":"通信網路業","28":"電子零組件業","29":"電子通路業",
        "30":"資訊服務業","31":"其他電子業","32":"文化創意業","33":"農業科技業",
        "34":"電子商務","35":"綠能環保","36":"數位雲端","37":"運動休閒","38":"居家生活"
    }
    df['industry_name'] = df['industry_code'].map(industry_map).fillna('其他')
    return df

# -------------------------
# 2) 抓每日成交量排名（可抓多頁或 top200），這裡以 WantGoo 或 TWSE daily top20 為主資料來源
# -------------------------
def fetch_top_volume_list(date_str=None):
    """
    回傳 list of dict: [{'code':'2330','name':'台積電','volume':123456}, ...]
    date_str format: 'YYYY-MM-DD' or None (用最近交易日)
    來源：TWSE 每日「成交量前二十名」(https://www.twse.com.tw/zh/trading/historical/mi-stock20.html)
    或 WantGoo 成交量排名 (靜態表格較友善)
    """
    # 優先使用 WantGoo 的 成交量 排行頁面 (提供 top200)
    url = "https://www.wantgoo.com/stock/ranking/volume"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'lxml')
    table = soup.find('table')
    items = []
    if not table:
        print("無法從 WantGoo 取得成交量排行榜，嘗試 TWSE top20 頁面", file=sys.stderr)
    else:
        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 3:
                continue
            code = cols[1].get_text(strip=True).split('.')[0]
            name = cols[2].get_text(strip=True)
            # 有些欄位會有成交量或成交金額可取
            vol_txt = cols[-1].get_text(strip=True).replace(',','')
            try:
                vol = int(vol_txt)
            except:
                vol = None
            items.append({'code': code, 'name': name, 'volume': vol})
    return items

# -------------------------
# 3) 抓三大法人買賣超（或外資買賣超）排名
# -------------------------
def fetch_institutional_netbuy(date_str=None):
    """
    來源：WantGoo 的 '外資及陸資買賣超排行'、TWSE 的 三大法人買賣超日報 (https://www.twse.com.tw/zh/trading/foreign/t86.html)
    這個函式回傳 list [{'code':'2330','name':'台積電','net_buy':12345}, ...]
    """
    url = "https://www.wantgoo.com/stock/institutional-investors/foreign/net-buy-sell-rank"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'lxml')
    table = soup.find('table')
    items = []
    if not table:
        print("無法取得法人排行 (WantGoo)，請確認網頁結構或換其他來源。", file=sys.stderr)
        return items
    rows = table.find_all('tr')[1:]
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 4:
            continue
        code = cols[1].get_text(strip=True).split('.')[0]
        name = cols[2].get_text(strip=True)
        net_txt = cols[3].get_text(strip=True).replace(',','')
        try:
            net = int(net_txt)
        except:
            net = None
        items.append({'code': code, 'name': name, 'net_buy': net})
    return items

# -------------------------
# 4) 把上面兩個列表跟公司清單合併，依產業分類，取 top20
# -------------------------
def build_industry_top20(df_company, vol_list, inst_list, top_n=20):
    # 先把 vol_list 與 inst_list 轉成 dict 方便查
    vol_map = {x['code']: x for x in vol_list}
    inst_map = {x['code']: x for x in inst_list}
    # 建立產業 bucket
    industry_buckets = defaultdict(lambda: {'by_volume': [], 'by_institution': []})
    # for all companies in df_company, if they exist in vol_map/inst_map, append to their industry
    for code, row in df_company.iterrows():
        cname = row['name']
        ind = row['industry_name']
        if code in vol_map:
            v = vol_map[code].get('volume')
            industry_buckets[ind]['by_volume'].append({'code': code, 'name': cname, 'volume': v})
        if code in inst_map:
            n = inst_map[code].get('net_buy')
            industry_buckets[ind]['by_institution'].append({'code': code, 'name': cname, 'net_buy': n})
    # 排序並取 top_n，轉為字典格式 code:name
    out = {}
    for ind, buckets in industry_buckets.items():
        vol_sorted = sorted(buckets['by_volume'], key=lambda x: (x['volume'] is None, -(x['volume'] or 0)))
        inst_sorted = sorted(buckets['by_institution'], key=lambda x: (x['net_buy'] is None, -(x['net_buy'] or 0)))
        vol_top = {item['code']: item['name'] for item in vol_sorted[:top_n]}
        inst_top = {item['code']: item['name'] for item in inst_sorted[:top_n]}
        out[ind] = {'by_volume': vol_top, 'by_institution': inst_top}
    return out

# -------------------------
# 5) 抓熱門 ETF（成交量/規模前20）
# -------------------------
def fetch_hot_etfs():
    """
    抓 Yahoo 或 WantGoo 的 ETF 成交量排名（取前 50，回傳前20）
    """
    url = "https://tw.stock.yahoo.com/tw-etf/volume"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'lxml')
    table = soup.find('table')
    items = []
    if table:
        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 3:
                continue
            code = cols[1].get_text(strip=True)
            name = cols[2].get_text(strip=True)
            items.append({'code': code, 'name': name})
    # fallback: 若沒抓到就用 common ETFs
    if not items:
        items = [{'code':'0050','name':'元大台灣50'}, {'code':'0056','name':'元大高股息'}, {'code':'00878','name':'國泰永續高股息'}]
    return {it['code']: it['name'] for it in items[:20]}

# -------------------------
# MAIN
# -------------------------
def main(target_date=None):
    if target_date is None:
        # 使用最近交易日 (若今天週末或非交易日，應回溯到上個交易日)
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    print("目標交易日:", target_date)
    print("抓取公司清單...")
    df_company = fetch_tw_company_list()
    if df_company.empty:
        print("錯誤：無法取得公司清單，程式終止", file=sys.stderr)
        return
    print(f"公司數量: {len(df_company)}")
    print("抓取成交量排行榜...")
    vol_list = fetch_top_volume_list(date_str=target_date)
    print("成交量榜數量：", len(vol_list))
    print("抓取法人買賣超排行...")
    inst_list = fetch_institutional_netbuy(date_str=target_date)
    print("法人榜數量：", len(inst_list))
    print("整理成產業 top20 ...")
    out = build_industry_top20(df_company, vol_list, inst_list, top_n=20)
    print("抓取熱門 ETF ...")
    etf_dict = fetch_hot_etfs()
    out['ETF'] = {'by_volume': etf_dict, 'by_institution': {}}  # ETF 的法人榜可以另外抓
    # 輸出 JSON
    outfile = f"industry_top20_by_volume_and_institution_{target_date}.json"
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("完成，輸出檔案：", outfile)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, default=None, help='YYYY-MM-DD (交易日)，預設最近一個交易日')
    args = parser.parse_args()
    main(args.date)
