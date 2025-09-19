# main.py

from technical_analyzer import analyze_stock_technicals
from news_analyzer import analyze_news_sentiment

def calculate_technical_score(data):
    score=0;total_possible_score=100;details=[];
    if data is None or data.empty:return 0,["技術數據不足"];
    latest=data.iloc[-1];required_cols=['Close','MA60','MA20','MA5','K','D','DIF','DEM','OSC','BB_Upper','BB_Lower','Volume_Price_Signal'];
    if not all(col in latest.index for col in required_cols):return 0,["部分技術指標計算失敗"];
    if latest['Close']>latest['MA60']:score+=15;details.append("價格 > 60MA (+15)");
    if latest['MA20']>latest['MA60']:score+=10;details.append("20MA > 60MA (+10)");
    if latest['Close']>latest['MA20']:score+=10;details.append("價格 > 20MA (+10)");
    if latest['MA5']>latest['MA20']:score+=5;details.append("5MA > 20MA (+5)");
    if latest['K']>latest['D']:score+=5;details.append("K > D (+5)");
    if latest['K']<20:score+=5;details.append("K < 20 超賣區 (+5)");
    if latest['DIF']>latest['DEM']:score+=5;details.append("DIF > DEM (+5)");
    if latest['OSC']>0:score+=5;details.append("OSC > 0 (+5)");
    if latest.get('Golden_Cross_KD',False) or latest.get('Golden_Cross_MACD',False):score+=10;details.append("當日發生黃金交叉 (+10)");
    if latest['Close']>latest['BB_Upper']:score+=10;details.append("突破布林上軌 (+10)");
    elif latest['Close']<latest['BB_Lower']:score-=10;details.append("跌破布林下軌 (-10)");
    vp_signal=latest['Volume_Price_Signal'];
    if vp_signal=='價漲量增':score+=10;details.append("價漲量增 (+10)");
    elif vp_signal=='價跌量縮':score+=5;details.append("價跌量縮 (+5)");
    elif vp_signal=='價跌量增':score-=10;details.append("價跌量增 (-10)");
    score=max(0,min(score,total_possible_score));
    return score,details
    
def calculate_news_score(news_results):
    if not news_results:return 50;
    raw_score=0;
    for news in news_results:
        if news['sentiment']=='正面':raw_score+=20;
        elif news['sentiment']=='負面':raw_score-=20;
    normalized_score=(raw_score+100)/2;
    return normalized_score

# --- 主程式執行 ---
if __name__ == "__main__":
    STOCK_MAP = {
        "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2308": "台達電",
        "2382": "廣達", "2881": "富邦金", "2891": "中信金", "2882": "國泰金",
        "2357": "華碩", "3231": "緯創"
    }

    stock_code = "2330"
    stock_ticker = f"{stock_code}.TW"
    stock_name = STOCK_MAP.get(stock_code, stock_code)

    tech_data = analyze_stock_technicals(stock_ticker)
    
    # --- 暫時不執行新聞分析 ---
    # news_results = analyze_news_sentiment(stock_ticker, limit=10)
    
    technical_score, scoring_details = calculate_technical_score(tech_data)
    # news_score = calculate_news_score(news_results)
    
    # --- 總分暫時只看技術面分數 ---
    total_score = technical_score

    print("\n\n=========================================")
    print(f"      投資荷密斯分析報告 ({stock_code} {stock_name})")
    print("=========================================")
    
    print(f"\n綜合評分: {total_score:.1f} / 100.0")
    print(f"(僅計算技術面分數)")
    
    print("\n--- 技術面評分 ---")
    print(f"分數: {technical_score} / 100")
    for detail in scoring_details:
        print(f"  - {detail}")