# main.py
'''
from technical_analyzer import analyze_stock_technicals, CANDLESTICK_PATTERNS

def calculate_technical_score(data,pattern_info):
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
    if pattern_info:
        if pattern_info['type'] == '看漲':
            score += 15
            details.append(f"出現看漲型態: {pattern_info['pattern_name']} (+15)")
        elif pattern_info['type'] == '看跌':
            score -= 15
            details.append(f"出現看跌型態: {pattern_info['pattern_name']} (-15)")

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
    DEBUG_CANDLESTICK = True
    STOCK_MAP = {"2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2308": "台達電"}
    stock_code = "2308"
    stock_ticker = f"{stock_code}.TW"
    stock_name = STOCK_MAP.get(stock_code, stock_code)

    analysis_result = analyze_stock_technicals(stock_ticker)
    
    if analysis_result and analysis_result["data"] is not None:
        tech_data = analysis_result["data"]
        latest_pattern = analysis_result["pattern"]
        
        if DEBUG_CANDLESTICK:
            print("\n\n=========================================")
            print("      K棒型態偵錯模式 (DEBUG MODE)")
            print("=========================================")
            
            all_pattern_codes = list(CANDLESTICK_PATTERNS['bullish'].keys()) + list(CANDLESTICK_PATTERNS['bearish'].keys())
            all_pattern_codes = list(dict.fromkeys(all_pattern_codes))
            
            # 【修正】產生正確的欄位名稱列表 (e.g., 'CDLHAMMER')
            pattern_columns = [f"CDL{p.replace('cdl_', '').upper()}" for p in all_pattern_codes]
            
            # 篩選出實際存在於 tech_data 中的欄位，避免因 pandas-ta 版本不同缺少某些型態而報錯
            existing_pattern_columns = [col for col in pattern_columns if col in tech_data.columns]
            
            if existing_pattern_columns:
                df_patterns = tech_data[existing_pattern_columns]
                detected_days = df_patterns[(df_patterns != 0).any(axis=1)]
                if not detected_days.empty:
                    print("在過去一年中，pandas-ta 函式庫偵測到以下K棒型態：")
                    print(detected_days.loc[:, (detected_days != 0).any(axis=0)])
                else:
                    print(">>> 驗證結果：pandas-ta 在整個期間內未偵測到任何指定的K棒型態。")
            else:
                print(">>> 警告：找不到任何 K 棒型態的結果欄位。")
            print("=========================================")
        
        technical_score, scoring_details = calculate_technical_score(tech_data, latest_pattern)
        
        # --- 產生報告 ---
        print("\n\n=========================================")
        print(f"      投資荷密斯-技術分析報告 ({stock_code} {stock_name})")
        print("=========================================")
        print(f"\n技術面綜合評分: {technical_score} / 100")
        
        print("\n--- K棒型態分析 (漸進式搜尋) ---")
        if latest_pattern:
            print(f"最近期發現型態: {latest_pattern['pattern_name']} ({latest_pattern['type']})")
            print(f"出現日期: {latest_pattern['date']}")
            print(f"分析週期: 最近{latest_pattern['window']}")
            print(f"型態解釋: {latest_pattern['explanation']}")
        else:
            print("狀態：最近一季內未發現明顯的K棒型態。")

        print("\n--- 評分理由 ---")
        for detail in scoring_details:
            print(f"  • {detail}")
    else:
        print(f"無法獲取 {stock_code} 的技術資料，程式終止。")

'''
# main.py (最終穩定版)

from technical_analyzer import analyze_stock_technicals

def calculate_technical_score(data):
    """根據最新的技術數據計算綜合分數"""
    score=0
    total_possible_score=100
    details=[]
    
    if data is None or data.empty:
        return 0, ["技術數據不足"]
        
    latest = data.iloc[-1]
    
    # 檢查必要的指標欄位是否存在
    required_cols = ['Close', 'MA60', 'MA20', 'MA5', 'K', 'D', 'DIF', 'DEM', 'OSC', 'BB_Upper', 'BB_Lower', 'Volume_Price_Signal']
    if not all(col in latest.index for col in required_cols):
        return 0, ["部分技術指標計算失敗，無法評分"]

    # --- 評分規則 ---
    if latest['Close'] > latest['MA60']: score += 15; details.append("價格 > 60MA (+15)")
    if latest['MA20'] > latest['MA60']: score += 10; details.append("20MA > 60MA (+10)")
    if latest['Close'] > latest['MA20']: score += 10; details.append("價格 > 20MA (+10)")
    if latest['MA5'] > latest['MA20']: score += 5; details.append("5MA > 20MA (+5)")

    if latest['K'] > latest['D']: score += 5; details.append("K > D (+5)")
    if latest['K'] < 20: score += 5; details.append("K < 20 超賣區 (+5)")
    if latest['DIF'] > latest['DEM']: score += 5; details.append("DIF > DEM (+5)")
    if latest['OSC'] > 0: score += 5; details.append("OSC > 0 (+5)")
    
    if latest.get('Golden_Cross_KD', False) or latest.get('Golden_Cross_MACD', False):
        score += 10; details.append("當日發生黃金交叉 (+10)")

    if latest['Close'] > latest['BB_Upper']: score += 10; details.append("突破布林上軌 (+10)")
    elif latest['Close'] < latest['BB_Lower']: score -= 10; details.append("跌破布林下軌 (-10)")
    
    vp_signal = latest['Volume_Price_Signal']
    if vp_signal == '價漲量增': score += 10; details.append("價漲量增 (+10)")
    elif vp_signal == '價跌量縮': score += 5; details.append("價跌量縮 (+5)")
    elif vp_signal == '價跌量增': score -= 10; details.append("價跌量增 (-10)")

    score = max(0, min(score, total_possible_score))
    return score, details

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

    # 執行分析
    tech_data = analyze_stock_technicals(stock_ticker)
    
    if tech_data is not None:
        # 計算分數
        technical_score, scoring_details = calculate_technical_score(tech_data)
        
        # --- 產生報告 ---
        print("\n\n=========================================")
        print(f"      投資荷密斯-技術分析報告 ({stock_code} {stock_name})")
        print("=========================================")
        
        print(f"\n技術面綜合評分: {technical_score} / 100")

        print("\n--- 評分理由 ---")
        if scoring_details:
            for detail in scoring_details:
                print(f"  • {detail}")
        else:
            print("  - 無法產生評分理由。")
    else:
        print(f"無法獲取 {stock_code} 的技術資料，程式終止。")