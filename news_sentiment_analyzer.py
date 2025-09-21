# news_sentiment_analyzer.py - 台股新聞情緒分析器

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from dataclasses import dataclass
import jieba
from collections import Counter
import urllib.parse

@dataclass
class NewsArticle:
    """新聞文章資料結構"""
    title: str
    content: str
    url: str
    publish_time: str
    source: str

@dataclass
class SentimentAnalysis:
    """情緒分析結果"""
    sentiment: str  # 'POSITIVE', 'NEGATIVE', 'NEUTRAL'
    confidence: float  # 信心度 0-100
    positive_score: int
    negative_score: int
    key_positive_words: List[str]
    key_negative_words: List[str]
    summary: str

class NewsEmotionAnalyzer:
    """新聞情緒分析器"""
    
    def __init__(self):
        # 台股專用情緒字典
        self.positive_keywords = {
            # 業績相關
            '獲利': 3, '營收': 2, '成長': 3, '增長': 3, '突破': 3, '創新高': 4, '新高': 3,
            '超越': 3, '優於': 2, '勝過': 2, '領先': 3, '龍頭': 3, '第一': 2,
            
            # 技術面相關  
            '上漲': 2, '漲幅': 2, '強勢': 3, '突破': 3, '攻克': 3, '站上': 2, '收復': 2,
            '反彈': 2, '回升': 2, '走強': 2, '轉強': 3, '多頭': 3, '買盤': 2,
            
            # 基本面相關
            '利多': 3, '看好': 3, '樂觀': 3, '正面': 2, '積極': 2, '有利': 2,
            '受惠': 2, '助益': 2, '推升': 2, '帶動': 2, '激勵': 3, '刺激': 2,
            
            # 公司營運
            '擴廠': 2, '併購': 2, '合作': 2, '簽約': 2, '得標': 3, '訂單': 2,
            '投資': 1, '布局': 2, '進軍': 2, '拓展': 2, '開發': 2, '研發': 2,
            
            # 市場評價
            '看漲': 3, '推薦': 2, '買進': 3, '加碼': 3, '調升': 3, '上修': 3,
            '目標價': 2, '潛力': 2, '機會': 2, '轉機': 3, '題材': 2, '概念': 1,
            
            # 一般正面詞彙
            '好': 1, '佳': 2, '優': 2, '強': 2, '高': 1, '大': 1, '多': 1,
            '升': 2, '漲': 2, '增': 2, '賺': 3, '盈': 2, '豐': 2
        }
        
        self.negative_keywords = {
            # 業績相關
            '虧損': 4, '衰退': 3, '下滑': 3, '減少': 2, '縮水': 3, '慘淡': 4,
            '低迷': 3, '疲弱': 3, '不振': 3, '表現差': 3, '失望': 3,
            
            # 技術面相關
            '下跌': 2, '跌幅': 2, '弱勢': 3, '跌破': 3, '失守': 3, '重挫': 4,
            '大跌': 4, '暴跌': 4, '崩跌': 5, '殺盤': 4, '賣壓': 3, '空頭': 3,
            
            # 風險相關
            '利空': 3, '看壞': 3, '悲觀': 3, '負面': 2, '擔憂': 2, '憂慮': 2,
            '警告': 3, '危機': 4, '風險': 2, '威脅': 3, '衝擊': 3, '壓力': 2,
            
            # 市場評價
            '看跌': 3, '賣出': 3, '減碼': 3, '調降': 3, '下修': 3, '降評': 3,
            '不推薦': 3, '避開': 3, '出場': 3, '套牢': 3, '被套': 3,
            
            # 營運問題
            '停產': 4, '關廠': 4, '裁員': 3, '倒閉': 5, '退出': 3, '終止': 3,
            '延後': 2, '暫停': 2, '取消': 3, '失利': 3, '失敗': 3,
            
            # 一般負面詞彙
            '差': 2, '劣': 3, '弱': 2, '低': 1, '少': 1, '小': 1,
            '跌': 2, '降': 2, '減': 2, '虧': 3, '損': 3, '慘': 4
        }
        
        # 中性但重要的關鍵字（用於識別重要議題）
        self.important_keywords = {
            '財報', '法說會', '董事會', '股東會', '除權', '除息', '股利', '配息',
            '合併', '分割', '重組', '轉投資', '子公司', '關係企業',
            '產能', '稼動率', '毛利率', '營業利益', '稅後淨利', 'EPS',
            '現金流', '負債比', 'ROE', 'ROA', '本益比', '股價淨值比',
            '市場占有率', '競爭對手', '產業鏈', '供應商', '客戶',
            '法規', '政策', '補助', '關稅', '匯率', '利率', '通膨'
        }
        
        # 設置 jieba 分詞
        jieba.initialize()
        
    def crawl_cnyes_news(self, stock_code: str, stock_name: str, max_articles: int = 10) -> List[NewsArticle]:
        """爬取鉅亨網新聞 - 增強版"""
        print(f"正在爬取鉅亨網關於 {stock_code} {stock_name} 的新聞...")
        articles = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        # 嘗試多個搜尋策略
        search_urls = [
            f"https://news.cnyes.com/news/cat/tw_stock?keyword={urllib.parse.quote(stock_code)}",
            f"https://news.cnyes.com/news/cat/tw_stock?keyword={urllib.parse.quote(stock_name)}",
            f"https://news.cnyes.com/news/cat/tw_stock",  # 一般台股新聞
        ]
        
        for search_url in search_urls:
            try:
                print(f"嘗試URL: {search_url}")
                response = requests.get(search_url, headers=headers, timeout=15)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 多種選擇器策略
                selectors = [
                    'a[href*="/news/id/"]',
                    '.news-list a',
                    '.title a',
                    'h3 a',
                    'h2 a',
                    '.item-title a'
                ]
                
                news_links = []
                for selector in selectors:
                    found_links = soup.select(selector)
                    if found_links:
                        news_links.extend(found_links)
                        break
                
                print(f"找到 {len(news_links)} 個新聞連結")
                
                for link in news_links:
                    if len(articles) >= max_articles:
                        break
                        
                    try:
                        news_url = link.get('href', '')
                        if not news_url:
                            continue
                            
                        if not news_url.startswith('http'):
                            news_url = 'https://news.cnyes.com' + news_url
                        
                        news_title = link.get_text(strip=True)
                        if not news_title or len(news_title) < 5:
                            continue
                        
                        # 檢查是否與目標股票相關
                        if self._is_stock_related(news_title, stock_code, stock_name):
                            article_content = self._fetch_article_content(news_url, headers)
                            if article_content and len(article_content) > 50:
                                articles.append(NewsArticle(
                                    title=news_title,
                                    content=article_content,
                                    url=news_url,
                                    publish_time=self._extract_publish_time(soup, link),
                                    source='鉅亨網'
                                ))
                                print(f"✓ 已收集: {news_title}")
                                time.sleep(2)  # 增加延遲避免被封
                        
                    except Exception as e:
                        print(f"處理單條新聞時出錯: {e}")
                        continue
                
                if len(articles) >= max_articles // 2:
                    break
                    
            except Exception as e:
                print(f"爬取鉅亨網搜尋頁面失敗: {e}")
                continue
        
        print(f"鉅亨網共收集到 {len(articles)} 篇新聞")
        return articles
    
    def crawl_yahoo_news(self, stock_code: str, stock_name: str, max_articles: int = 10) -> List[NewsArticle]:
        """爬取雅虎股市新聞 - 增強版"""
        print(f"正在爬取Yahoo財經關於 {stock_code} {stock_name} 的新聞...")
        articles = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
        
        # 多個Yahoo新聞來源
        yahoo_urls = [
            f"https://tw.stock.yahoo.com/quote/{stock_code}.TW/news",
            f"https://tw.news.yahoo.com/股市/",
            "https://tw.stock.yahoo.com/news/category-tw-stock",
        ]
        
        for base_url in yahoo_urls:
            try:
                print(f"嘗試Yahoo URL: {base_url}")
                response = requests.get(base_url, headers=headers, timeout=15)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 多種Yahoo新聞選擇器
                selectors = [
                    'h3[data-test-locator="cStreamItem"] a',
                    'div[data-testid*="news"] a',
                    '.news-stream-item a',
                    '.stream-item a', 
                    'h3 a[href*="news"]',
                    'a[href*="/news/"]',
                    '.title a',
                    '.newsTitle a'
                ]
                
                found_links = []
                for selector in selectors:
                    links = soup.select(selector)
                    if links:
                        found_links.extend(links)
                
                print(f"Yahoo找到 {len(found_links)} 個新聞連結")
                
                for link in found_links:
                    if len(articles) >= max_articles:
                        break
                        
                    try:
                        news_url = link.get('href', '')
                        if not news_url:
                            continue
                            
                        if news_url.startswith('//'):
                            news_url = 'https:' + news_url
                        elif not news_url.startswith('http'):
                            news_url = 'https://tw.stock.yahoo.com' + news_url
                        
                        news_title = link.get_text(strip=True)
                        if not news_title or len(news_title) < 5:
                            continue
                        
                        # 檢查相關性
                        if self._is_stock_related(news_title, stock_code, stock_name):
                            article_content = self._fetch_article_content(news_url, headers)
                            if article_content and len(article_content) > 50:
                                articles.append(NewsArticle(
                                    title=news_title,
                                    content=article_content,
                                    url=news_url,
                                    publish_time=self._extract_publish_time(soup, link),
                                    source='Yahoo財經'
                                ))
                                print(f"✓ Yahoo已收集: {news_title}")
                                time.sleep(2)
                        
                    except Exception as e:
                        print(f"處理Yahoo新聞時出錯: {e}")
                        continue
                
                if len(articles) >= max_articles // 2:
                    break
                    
            except Exception as e:
                print(f"爬取Yahoo新聞頁面失敗: {e}")
                continue
        
        print(f"Yahoo財經共收集到 {len(articles)} 篇新聞")
        return articles
    
    def crawl_udn_news(self, stock_code: str, stock_name: str, max_articles: int = 5) -> List[NewsArticle]:
        """爬取聯合新聞網股市新聞"""
        print(f"正在爬取聯合新聞網關於 {stock_code} {stock_name} 的新聞...")
        articles = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        }
        
        try:
            # 聯合新聞網股市版
            udn_url = "https://udn.com/news/cate/2/6644"
            response = requests.get(udn_url, headers=headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尋找新聞連結
            news_links = soup.select('a[href*="/news/story/"]')
            
            for link in news_links:
                if len(articles) >= max_articles:
                    break
                    
                try:
                    news_url = link.get('href', '')
                    if not news_url.startswith('http'):
                        news_url = 'https://udn.com' + news_url
                    
                    news_title = link.get_text(strip=True)
                    if not news_title:
                        continue
                    
                    if self._is_stock_related(news_title, stock_code, stock_name):
                        article_content = self._fetch_article_content(news_url, headers)
                        if article_content and len(article_content) > 50:
                            articles.append(NewsArticle(
                                title=news_title,
                                content=article_content,
                                url=news_url,
                                publish_time=datetime.now().strftime('%Y-%m-%d %H:%M'),
                                source='聯合新聞網'
                            ))
                            print(f"✓ UDN已收集: {news_title}")
                            time.sleep(1)
                
                except Exception as e:
                    print(f"處理UDN新聞時出錯: {e}")
                    continue
        
        except Exception as e:
            print(f"爬取聯合新聞網失敗: {e}")
        
        print(f"聯合新聞網共收集到 {len(articles)} 篇新聞")
        return articles
    
    def crawl_chinatimes_news(self, stock_code: str, stock_name: str, max_articles: int = 5) -> List[NewsArticle]:
        """爬取中時新聞網財經新聞"""
        print(f"正在爬取中時新聞網關於 {stock_code} {stock_name} 的新聞...")
        articles = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        try:
            # 中時財經新聞
            chinatimes_url = "https://www.chinatimes.com/money/?chdtv"
            response = requests.get(chinatimes_url, headers=headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尋找新聞連結
            news_links = soup.select('a[href*="/realtimenews/"]')
            
            for link in news_links:
                if len(articles) >= max_articles:
                    break
                    
                try:
                    news_url = link.get('href', '')
                    if not news_url.startswith('http'):
                        news_url = 'https://www.chinatimes.com' + news_url
                    
                    news_title = link.get_text(strip=True)
                    if not news_title:
                        continue
                    
                    if self._is_stock_related(news_title, stock_code, stock_name):
                        article_content = self._fetch_article_content(news_url, headers)
                        if article_content and len(article_content) > 50:
                            articles.append(NewsArticle(
                                title=news_title,
                                content=article_content,
                                url=news_url,
                                publish_time=datetime.now().strftime('%Y-%m-%d %H:%M'),
                                source='中時新聞網'
                            ))
                            print(f"✓ 中時已收集: {news_title}")
                            time.sleep(1)
                
                except Exception as e:
                    print(f"處理中時新聞時出錯: {e}")
                    continue
        
        except Exception as e:
            print(f"爬取中時新聞網失敗: {e}")
        
        print(f"中時新聞網共收集到 {len(articles)} 篇新聞")
        return articles
    
    def _is_stock_related(self, text: str, stock_code: str, stock_name: str) -> bool:
        """更智能的股票相關性檢查"""
        text_lower = text.lower()
        stock_code_lower = stock_code.lower()
        stock_name_lower = stock_name.lower()
        
        # 直接匹配
        direct_matches = [
            stock_code in text,
            stock_name in text,
            stock_code_lower in text_lower,
            stock_name_lower in text_lower,
            f"({stock_code})" in text,
            f"（{stock_code}）" in text,
            f" {stock_code} " in f" {text} ",
        ]
        
        if any(direct_matches):
            return True
        
        # 模糊匹配 - 針對常見的股票簡稱
        stock_name_parts = stock_name_lower.replace('股份有限公司', '').replace('公司', '')
        for part in stock_name_parts.split():
            if len(part) >= 2 and part in text_lower:
                return True
        
        # 行業關鍵字匹配 (可以根據不同股票自定義)
        industry_keywords = {
            '2330': ['半導體', '晶圓', '台積電', 'tsmc', '製程'],
            '2317': ['鴻海', '富士康', 'iPhone', '代工', '組裝'],
            '2454': ['聯發科', '晶片', 'IC', '處理器', 'mediatek'],
            # 可以繼續擴充...
        }
        
        if stock_code in industry_keywords:
            for keyword in industry_keywords[stock_code]:
                if keyword in text_lower:
                    return True
        
        return False
    
    def _extract_publish_time(self, soup, link_element) -> str:
        """嘗試提取發布時間"""
        try:
            # 常見的時間元素選擇器
            time_selectors = [
                'time',
                '.time',
                '.date',
                '.publish-time',
                '[datetime]',
                '.meta-info time'
            ]
            
            for selector in time_selectors:
                time_elem = soup.select_one(selector)
                if time_elem:
                    time_text = time_elem.get('datetime') or time_elem.get_text(strip=True)
                    if time_text:
                        return time_text
            
            return datetime.now().strftime('%Y-%m-%d %H:%M')
        except:
            return datetime.now().strftime('%Y-%m-%d %H:%M')
    
    def _fetch_article_content(self, url: str, headers: dict) -> str:
        """增強版新聞內容獲取"""
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除不需要的元素
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
                tag.decompose()
            
            # 移除廣告和無關內容
            for class_name in ['ad', 'advertisement', 'sidebar', 'related', 'comment', 'social', 'share']:
                for elem in soup.find_all(class_=re.compile(class_name, re.I)):
                    elem.decompose()
            
            # 多種內容選擇器策略
            content_selectors = [
                # Yahoo財經
                'div.caas-body',
                'div[data-module="ArticleBody"]',
                '.article-wrap .article-body',
                
                # 鉅亨網
                '.news-content',
                '.article-body',
                '#newsText',
                
                # 聯合新聞網
                'section.article-content__editor',
                '.article-content',
                
                # 中時新聞網
                '.article-body',
                '.article-content',
                
                # 通用選擇器
                'article',
                '.content',
                '.post-content',
                '.entry-content',
                'main',
                
                # 段落選擇器 (最後手段)
                'p'
            ]
            
            content = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    # 提取文字並清理
                    texts = []
                    for elem in elements:
                        text = elem.get_text(separator=' ', strip=True)
                        if text and len(text) > 20:  # 過濾太短的內容
                            texts.append(text)
                    
                    content = ' '.join(texts)
                    if len(content) > 100:  # 確保有足夠內容
                        break
            
            # 如果還是沒有內容，嘗試提取所有段落
            if not content or len(content) < 100:
                paragraphs = soup.find_all('p')
                texts = []
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 10:
                        texts.append(text)
                content = ' '.join(texts)
            
            # 清理內容
            content = re.sub(r'\s+', ' ', content)  # 合併多餘空白
            content = re.sub(r'[^\u4e00-\u9fff\w\s.,!?;:()「」『』【】〈〉《》]', '', content)  # 保留中文和基本標點
            content = content.strip()
            
            # 去除常見的無用內容
            useless_patterns = [
                r'.*延伸閱讀.*',
                r'.*相關新聞.*',
                r'.*更多新聞.*',
                r'.*推薦閱讀.*',
                r'.*免責聲明.*',
                r'.*版權所有.*',
                r'.*本文由.*提供.*',
            ]
            
            for pattern in useless_patterns:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            
            return content.strip() if len(content) > 50 else ""
            
        except Exception as e:
            print(f"獲取文章內容失敗 {url}: {e}")
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text(strip=True) for elem in elements])
                    if len(content) > 100:  # 確保有足夠內容
                        break
            
            # 清理內容
            content = re.sub(r'\s+', ' ', content)
            content = content.strip()
            
            return content if len(content) > 50 else ""
            
        except Exception as e:
            print(f"獲取文章內容失敗 {url}: {e}")
            return ""
    
    def analyze_sentiment(self, article: NewsArticle) -> SentimentAnalysis:
        """分析單篇文章的情緒"""
        # 合併標題和內容進行分析
        full_text = f"{article.title} {article.content}"
        
        # 使用jieba進行中文分詞
        words = list(jieba.cut(full_text))
        
        positive_score = 0
        negative_score = 0
        positive_words_found = []
        negative_words_found = []
        
        # 計算情緒分數
        for word in words:
            word = word.strip()
            if len(word) < 2:  # 忽略單字元
                continue
                
            # 正面詞彙檢查
            for pos_word, weight in self.positive_keywords.items():
                if pos_word in word or word in pos_word:
                    positive_score += weight
                    if pos_word not in positive_words_found:
                        positive_words_found.append(pos_word)
            
            # 負面詞彙檢查
            for neg_word, weight in self.negative_keywords.items():
                if neg_word in word or word in neg_word:
                    negative_score += weight
                    if neg_word not in negative_words_found:
                        negative_words_found.append(neg_word)
        
        # 計算最終情緒
        total_score = positive_score + negative_score
        if total_score == 0:
            sentiment = 'NEUTRAL'
            confidence = 30
        else:
            net_score = positive_score - negative_score
            if net_score > 2:
                sentiment = 'POSITIVE'
                confidence = min(70 + (net_score * 5), 95)
            elif net_score < -2:
                sentiment = 'NEGATIVE'  
                confidence = min(70 + (abs(net_score) * 5), 95)
            else:
                sentiment = 'NEUTRAL'
                confidence = 40
        
        # 生成摘要
        sentiment_text = {'POSITIVE': '正面', 'NEGATIVE': '負面', 'NEUTRAL': '中性'}
        summary = f"情緒傾向：{sentiment_text[sentiment]} (信心度: {confidence}%)"
        
        if positive_words_found:
            summary += f"，正面關鍵字：{', '.join(positive_words_found[:5])}"
        if negative_words_found:
            summary += f"，負面關鍵字：{', '.join(negative_words_found[:5])}"
        
        return SentimentAnalysis(
            sentiment=sentiment,
            confidence=confidence,
            positive_score=positive_score,
            negative_score=negative_score,
            key_positive_words=positive_words_found[:10],
            key_negative_words=negative_words_found[:10],
            summary=summary
        )
    
    def analyze_stock_news(self, stock_code: str, stock_name: str, max_articles: int = 10) -> Dict:
        """分析指定股票的新聞情緒 - 增強版多來源爬取"""
        print(f"開始分析股票 {stock_code} {stock_name} 的新聞情緒...")
        print("=" * 50)
        
        all_articles = []
        
        # 並行爬取多個新聞源，確保能獲得足夠的新聞
        news_sources = [
            ('Yahoo財經', lambda: self.crawl_yahoo_news(stock_code, stock_name, max_articles//3)),
            ('鉅亨網', lambda: self.crawl_cnyes_news(stock_code, stock_name, max_articles//3)),
            ('聯合新聞網', lambda: self.crawl_udn_news(stock_code, stock_name, max_articles//4)),
            ('中時新聞網', lambda: self.crawl_chinatimes_news(stock_code, stock_name, max_articles//4)),
        ]
        
        for source_name, crawl_func in news_sources:
            try:
                print(f"\n🔍 正在爬取 {source_name}...")
                articles = crawl_func()
                if articles:
                    all_articles.extend(articles)
                    print(f"✅ {source_name} 成功獲取 {len(articles)} 篇新聞")
                else:
                    print(f"⚠️ {source_name} 未獲取到相關新聞")
                
                # 如果已經收集到足夠的新聞，可以提前結束
                if len(all_articles) >= max_articles:
                    print(f"✅ 已收集到足夠的新聞 ({len(all_articles)} 篇)，停止爬取")
                    break
                    
            except Exception as e:
                print(f"❌ {source_name} 爬取失敗: {e}")
                continue
        
        # 去重處理 (基於標題相似性)
        unique_articles = self._remove_duplicate_articles(all_articles)
        
        print(f"\n📊 爬取總結:")
        print(f"   原始收集: {len(all_articles)} 篇")
        print(f"   去重後: {len(unique_articles)} 篇")
        
        if not unique_articles:
            # 如果沒有找到相關新聞，嘗試更寬鬆的搜尋
            print(f"\n🔄 未找到直接相關新聞，嘗試行業新聞...")
            industry_articles = self._crawl_industry_news(stock_code, stock_name)
            unique_articles.extend(industry_articles)
        
        if not unique_articles:
            return {
                'success': False,
                'message': f'未能獲取到 {stock_code} {stock_name} 的相關新聞。可能原因：1.該股票近期新聞較少 2.網站反爬蟲限制 3.股票代碼或名稱需要調整',
                'sentiment_summary': None,
                'articles': []
            }
        
        # 限制分析的新聞數量
        articles_to_analyze = unique_articles[:max_articles]
        
        print(f"\n🎯 開始分析 {len(articles_to_analyze)} 篇新聞的情緒...")
        print("-" * 50)
        
        # 分析每篇文章
        analyzed_articles = []
        total_positive = 0
        total_negative = 0
        all_positive_words = []
        all_negative_words = []
        
        for i, article in enumerate(articles_to_analyze, 1):
            print(f"分析第 {i} 篇: {article.title[:50]}...")
            
            sentiment_result = self.analyze_sentiment(article)
            analyzed_articles.append({
                'article': article,
                'sentiment': sentiment_result
            })
            
            total_positive += sentiment_result.positive_score
            total_negative += sentiment_result.negative_score
            all_positive_words.extend(sentiment_result.key_positive_words)
            all_negative_words.extend(sentiment_result.key_negative_words)
            
            # 顯示每篇文章的簡要結果
            sentiment_icon = {'POSITIVE': '📈', 'NEGATIVE': '📉', 'NEUTRAL': '📊'}[sentiment_result.sentiment]
            print(f"   結果: {sentiment_icon} {sentiment_result.sentiment} ({sentiment_result.confidence}%)")
        
        # 計算整體情緒
        if total_positive + total_negative == 0:
            overall_sentiment = 'NEUTRAL'
            overall_confidence = 30
        else:
            net_sentiment = total_positive - total_negative
            positive_ratio = total_positive / (total_positive + total_negative)
            
            if net_sentiment > 5:
                overall_sentiment = 'POSITIVE'
                overall_confidence = min(60 + (net_sentiment * 2), 90)
            elif net_sentiment < -5:
                overall_sentiment = 'NEGATIVE'
                overall_confidence = min(60 + (abs(net_sentiment) * 2), 90)
            else:
                overall_sentiment = 'NEUTRAL'
                overall_confidence = max(40, min(60, 50 + abs(net_sentiment) * 2))
        
        # 統計關鍵字
        positive_word_counts = Counter(all_positive_words)
        negative_word_counts = Counter(all_negative_words)
        
        sentiment_summary = {
            'overall_sentiment': overall_sentiment,
            'confidence': overall_confidence,
            'total_articles': len(analyzed_articles),
            'positive_articles': len([a for a in analyzed_articles if a['sentiment'].sentiment == 'POSITIVE']),
            'negative_articles': len([a for a in analyzed_articles if a['sentiment'].sentiment == 'NEGATIVE']),
            'neutral_articles': len([a for a in analyzed_articles if a['sentiment'].sentiment == 'NEUTRAL']),
            'total_positive_score': total_positive,
            'total_negative_score': total_negative,
            'net_sentiment_score': total_positive - total_negative,
            'top_positive_keywords': positive_word_counts.most_common(10),
            'top_negative_keywords': negative_word_counts.most_common(10),
            'news_sources': list(set([article.source for article in articles_to_analyze]))
        }
        
        print(f"\n✅ 情緒分析完成！")
        print(f"   整體情緒: {overall_sentiment} (信心度: {overall_confidence}%)")
        print(f"   正面分數: {total_positive}, 負面分數: {total_negative}")
        
        return {
            'success': True,
            'sentiment_summary': sentiment_summary,
            'articles': analyzed_articles
        }
    
    def _remove_duplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """去除重複的新聞文章"""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            # 簡化標題用於比較
            simplified_title = re.sub(r'[^\u4e00-\u9fff\w]', '', article.title.lower())
            
            # 檢查是否為重複
            is_duplicate = False
            for seen_title in seen_titles:
                # 如果兩個標題有80%以上的相似性，視為重複
                if self._text_similarity(simplified_title, seen_title) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.add(simplified_title)
        
        return unique_articles
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """計算兩個文本的相似性"""
        if not text1 or not text2:
            return 0.0
        
        # 簡單的字符集合相似性計算
        set1 = set(text1)
        set2 = set(text2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _crawl_industry_news(self, stock_code: str, stock_name: str) -> List[NewsArticle]:
        """當找不到直接相關新聞時，搜尋行業相關新聞"""
        print("🔍 搜尋行業相關新聞...")
        
        # 根據股票代碼確定行業關鍵字
        industry_map = {
            '2330': ['半導體', '晶圓', '台積電'],
            '2317': ['電子代工', '鴻海', '組裝'],
            '2454': ['IC設計', '聯發科', '晶片'],
            '2881': ['金融', '銀行', '富邦'],
            '2891': ['金融', '銀行', '中信'],
            # 可以繼續擴充...
        }
        
        industry_keywords = industry_map.get(stock_code, [stock_name])
        articles = []
        
        # 這裡可以實作更寬鬆的行業新聞搜尋
        # 為了簡化，這裡先返回空列表
        
        return articles

def format_sentiment_report(analysis_result: Dict, stock_code: str, stock_name: str) -> str:
    """格式化情緒分析報告"""
    if not analysis_result['success']:
        return f"❌ {stock_code} {stock_name} 新聞情緒分析失敗：{analysis_result['message']}"
    
    summary = analysis_result['sentiment_summary']
    articles = analysis_result['articles']
    
    # 情緒emoji對應
    sentiment_emoji = {
        'POSITIVE': '📈',
        'NEGATIVE': '📉', 
        'NEUTRAL': '📊'
    }
    
    sentiment_text = {
        'POSITIVE': '正面',
        'NEGATIVE': '負面',
        'NEUTRAL': '中性'
    }
    
    output = []
    output.append("=" * 60)
    output.append(f"📰 新聞情緒分析報告 - {stock_code} {stock_name}")
    output.append("=" * 60)
    output.append("")
    
    # 整體情緒
    overall = summary['overall_sentiment']
    output.append(f"{sentiment_emoji[overall]} 整體新聞情緒: {sentiment_text[overall]}")
    output.append(f"🎯 信心程度: {summary['confidence']}%")
    output.append("")
    
    # 統計資訊
    output.append("📊 新聞統計:")
    output.append(f"   總新聞數: {summary['total_articles']} 篇")
    output.append(f"   正面新聞: {summary['positive_articles']} 篇")
    output.append(f"   負面新聞: {summary['negative_articles']} 篇")
    output.append(f"   中性新聞: {summary['neutral_articles']} 篇")
    output.append("")
    
    # 情緒分數
    output.append(f"📈 正面情緒分數: {summary['total_positive_score']}")
    output.append(f"📉 負面情緒分數: {summary['total_negative_score']}")
    net_score = summary['total_positive_score'] - summary['total_negative_score']
    output.append(f"⚖️  淨情緒分數: {net_score:+d}")
    output.append("")
    
    # 關鍵字分析
    if summary['top_positive_keywords']:
        output.append("🔑 正面關鍵字:")
        for word, count in summary['top_positive_keywords'][:8]:
            output.append(f"   • {word} (出現{count}次)")
    
    if summary['top_negative_keywords']:
        output.append("")
        output.append("⚠️  負面關鍵字:")
        for word, count in summary['top_negative_keywords'][:8]:
            output.append(f"   • {word} (出現{count}次)")
    
    output.append("")
    output.append("📋 各篇新聞分析:")
    output.append("-" * 40)
    
    # 顯示每篇新聞的簡要分析
    for i, item in enumerate(articles[:5], 1):  # 只顯示前5篇詳細資訊
        article = item['article']
        sentiment = item['sentiment']
        
        output.append(f"{i}. {sentiment_emoji[sentiment.sentiment]} {article.title}")
        output.append(f"   來源: {article.source}")
        output.append(f"   情緒: {sentiment_text[sentiment.sentiment]} ({sentiment.confidence}%)")
        if sentiment.key_positive_words:
            output.append(f"   正面詞: {', '.join(sentiment.key_positive_words[:3])}")
        if sentiment.key_negative_words:
            output.append(f"   負面詞: {', '.join(sentiment.key_negative_words[:3])}")
        output.append("")
    
    if len(articles) > 5:
        output.append(f"... 還有 {len(articles) - 5} 篇新聞未詳細顯示")
    
    output.append("")
    output.append("💡 投資參考建議:")
    
    if overall == 'POSITIVE':
        if summary['confidence'] > 70:
            output.append("   • 新聞面整體偏向正面，可能對股價有正面助益")
            output.append("   • 但仍需搭配技術面與基本面分析")
        else:
            output.append("   • 新聞面略偏正面，但訊號不夠強烈")
    elif overall == 'NEGATIVE':
        if summary['confidence'] > 70:
            output.append("   • 新聞面整體偏向負面，可能對股價造成壓力")
            output.append("   • 建議謹慎評估投資風險")
        else:
            output.append("   • 新聞面略偏負面，需持續觀察")
    else:
        output.append("   • 新聞面整體中性，對股價影響有限")
        output.append("   • 建議以技術面分析為主要參考")
    
    output.append("")
    output.append("⚠️  重要提醒:")
    output.append("   • 新聞情緒分析僅供參考，不構成投資建議")
    output.append("   • 請搭配技術分析與基本面分析綜合判斷")
    output.append("   • 市場情緒變化快速，需持續追蹤最新消息")
    output.append("   • 建議將此分析結果與技術評分一併考量")
    
    return "\n".join(output)

# 使用範例
if __name__ == "__main__":
    # 測試用的股票清單
    STOCK_MAP = {
        "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2308": "台達電",
        "2382": "廣達", "2881": "富邦金", "2891": "中信金", "2882": "國泰金",
        "2357": "華碩", "3231": "緯創", "2412": "中華電", "1301": "台塑",
        "1303": "南亞", "2002": "中鋼", "2886": "兆豐金", "2603": "長榮"
    }
    
    # 創建分析器實例
    analyzer = NewsEmotionAnalyzer()
    
    # 測試股票 - 可以修改這裡
    test_stock_code = "2330"
    test_stock_name = STOCK_MAP[test_stock_code]
    
    print(f"開始分析 {test_stock_code} {test_stock_name} 的新聞情緒...")
    
    # 執行分析
    result = analyzer.analyze_stock_news(test_stock_code, test_stock_name, max_articles=10)
    
    # 輸出格式化報告
    report = format_sentiment_report(result, test_stock_code, test_stock_name)
    print(report)