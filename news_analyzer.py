# news_analyzer.py
KEYWORD_DB = {
    "positive": [
        "營收創高", "雙位數成長", "優於預期", "訂單滿載", "毛利率提升", "獲利", "法說會釋樂觀",
        "上修", "外資買超", "投信買超", "庫藏股", "新產能", "擴廠", "結盟", "併購", "獨家供應", "前景看好",    "營收創高",
    "訂單滿載",
    "利潤成長",
    "獲利提升",
    "營運穩健",
    "股價上揚",
    "成長動能",
    "獲得訂單",
    "大幅增加",
    "持續攀升",
    "產品熱銷",
    "產能擴大",
    "投資擴增",
    "降低成本",
    "市場擴展",
    "客戶增加",
    "新產品成功",
    "業績報喜",
    "良好表現",
    "預期提升",
    "獲利創新高",
    "財務健康",
    "績效卓越",
    "業務上升",
    "營收成長",
    "高成長率",
    "投資回報率提高",
    "收益穩定",
    "銷售成長",
    "增加市占率",
    "營收達標",
    "企業擴張",
    "訂單暴增",
    "市場機會",
    "預期獲利增加",
    "資本增加",
    "股票回購",
    "策略成功",
    "保持競爭優勢",
    "新客戶拓展",
    "風險降低",
    "負債減少",
    "現金流增強",
    "產品創新",
    "正面回饋",
    "長期成長",
    "紅利增加",
    "獲得認證",
    "合作擴大",
    "業績亮眼"
    ],
    "negative": [
        "營收衰退", "不如預期", "下修", "虧損", "毛利率下滑", "法說會釋保守", "外資賣超",
        "投信賣超", "訴訟", "違約", "調查", "前景看淡", "地緣政治風險", "斷鏈", "庫存調整","財報不如預期",
    "違約",
    "虧損擴大",
    "營收下降",
    "獲利下滑",
    "債務增加",
    "法律訴訟",
    "股價下跌",
    "業績不佳",
    "營運困難",
    "減少訂單",
    "產能不足",
    "降價競爭",
    "成本上升",
    "預期不達標",
    "風險暴露",
    "資金短缺",
    "管理問題",
    "客戶流失",
    "產品召回",
    "稅務問題",
    "營收疲軟",
    "訴訟風險",
    "資產減損",
    "債券違約",
    "營業額下降",
    "投資失敗",
    "經營風險",
    "營業外損失",
    "不良債權",
    "審計異常",
    "現金流吃緊",
    "股東權益減少",
    "破產傳聞",
    "經濟衰退影響",
    "營運虧損",
    "管制加嚴",
    "員工裁員",
    "高負債率",
    "銷售下降",
    "風暴來襲",
    "減資",
    "營收遲滯",
    "品質問題",
    "合約爭議",
    "違反合規",
    "停牌風險",
    "業務萎縮",
    "股價波動大",
    "信用下降"
    ]
}
'''
import time
import random
import requests


class CnyesNewsSpider():
    
    def get_newslist_info(self, page=1, limit=30):
        """ 房屋詳情

        :param page: 頁數
        :param limit: 一頁新聞數量
        :return newslist_info: 新聞資料
        """
        headers = {
            'Origin': 'https://news.cnyes.com/',
            'Referer': 'https://news.cnyes.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
        r = requests.get(f"https://api.cnyes.com/media/api/v1/newslist/category/headline?page={page}&limit={limit}", headers=headers)
        if r.status_code != requests.codes.ok:
            print('請求失敗', r.status_code)
            return None
        newslist_info = r.json()['items']
        return newslist_info


if __name__ == "__main__":
    cnyes_news_spider = CnyesNewsSpider()
    newslist_info = cnyes_news_spider.get_newslist_info()
    
    print(f'搜尋結果 > 全部新聞總數：{newslist_info["total"]}')
    print(f'搜尋結果 > 一頁新聞數：{newslist_info["per_page"]}')
    print(f'搜尋結果 > 當前頁數：{newslist_info["current_page"]}')
    print(f'搜尋結果 > 最後頁數：{newslist_info["last_page"]}')
    print(f'搜尋結果 > 前一頁網址：{newslist_info["prev_page_url"]}')
    print(f'搜尋結果 > 下一頁網址：{newslist_info["next_page_url"]}')
    print(f'搜尋結果 > 此頁新聞第一筆：{newslist_info["from"]}')
    print(f'搜尋結果 > 此頁新聞最後一筆：{newslist_info["to"]}')
    
    for news in newslist_info["data"]:
        print(f'    ------------ {news["newsId"]} ------------')
        print(f'    新聞 > URL：https://news.cnyes.com/news/id/{news["newsId"]}')
        print(f'    新聞 > 標題：{news["title"]}')
        print(f'    新聞 > 概要：{news["summary"]}')
        # print(f'    新聞 > 內文：{news["content"]}')
        print(f'    新聞 > 關鍵字：{news["keyword"]}')
        print(f'    新聞 > 發布時間：{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(news["publishAt"]))}')
        print(f'    新聞 > 分類：{news["categoryName"]} (id:{news["categoryId"]})')
        print()
        

    # 如果要爬取多頁新聞，建議加入隨機 delay 一段時間，避免被反爬蟲偵測
    # time.sleep(random.uniform(2, 5))
'''
import time
import requests

class CnyesNewsSpider:

    def get_tw_stock_news(self, page=1, limit=30, startAt=None, endAt=None):
        """抓台股相關新聞 (分頁)"""
        headers = {
            'Origin': 'https://news.cnyes.com/',
            'Referer': 'https://news.cnyes.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
        url = "https://api.cnyes.com/media/api/v1/newslist/category/tw_stock"
        params = {"limit": limit, "page": page}
        if startAt:
            params["startAt"] = startAt
        if endAt:
            params["endAt"] = endAt

        r = requests.get(url, headers=headers, params=params)
        if r.status_code != requests.codes.ok:
            print("請求失敗", r.status_code, r.text)
            return None
        return r.json().get("items", {}).get("data", [])

    def get_news_content(self, news_id):
        """抓單篇新聞全文 (穩定版)"""
        url = f"https://api.cnyes.com/media/api/v1/news/{news_id}"
        r = requests.get(url)
        if r.status_code == 200:
            try:
                data = r.json()
            except Exception as e:
                print(f"解析 JSON 失敗: {e}")
                return ""

            if isinstance(data, dict):
                items = data.get("items", {})
                if isinstance(items, dict):
                    return items.get("content", "")
            elif isinstance(data, list) and len(data) > 0:
                return data[0].get("content", "")
        return ""

    def filter_by_stock(self, symbol_id, keyword, max_count=10):
        """依照股票代號與關鍵字過濾新聞"""
        all_news = self.fetch_all_news(symbol_id=symbol_id, pages=3)  # 多抓幾頁
        results = []

        for news in all_news:
            title = news.get("title", "") or ""     # 保證是 str
            summary = news.get("summary", "") or "" # 保證是 str

            if keyword in title or keyword in summary:
                news_id = news.get("newsId")
                content = self.get_news_content(news_id)
                news["content"] = content
                results.append(news)

            if len(results) >= max_count:
                break

        return results


if __name__ == "__main__":
    spider = CnyesNewsSpider()
    filtered = spider.filter_by_stock(symbol_id="2330", keyword="台積電", max_count=10)

    for news in filtered:
        print(f"------------ {news['newsId']} ------------")
        print("標題:", news.get("title"))
        print("摘要:", news.get("summary"))
        print("發佈時間:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(news.get("publishAt", 0))))
        print("分類:", news.get("categoryName"))
        print("URL:", f"https://news.cnyes.com/news/id/{news.get('newsId')}")
        print()