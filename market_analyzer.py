# market_analyzer.py - 大盤趨勢分析模組

import yfinance as yf
import pandas_ta as ta

def get_market_state():
    """
    分析台灣加權指數 (^TWII) 以判斷當前大盤狀態。
    
    返回:
        str: '多頭' (Bull), '空頭' (Bear), or '盤整' (Sideways)
    """
    print("\n===== 開始分析大盤趨勢... =====")
    try:
        # 抓取台灣加權指數最近一年的數據
        twii = yf.Ticker("^TWII").history(period="1y", auto_adjust=True)
        
        if twii.empty:
            print("警告：無法獲取大盤數據，將以『盤整』作為預設狀態。")
            return "盤整"
            
        # 計算所需指標
        twii['MA20'] = twii['Close'].rolling(window=20).mean()
        twii['MA60'] = twii['Close'].rolling(window=60).mean()
        
        # 獲取最新一天（最後一列）的數據
        latest = twii.iloc[-1]
        
        # 判斷大盤狀態
        is_above_ma60 = latest['Close'] > latest['MA60']
        is_ma20_above_ma60 = latest['MA20'] > latest['MA60']
        
        state = ""
        if is_above_ma60 and is_ma20_above_ma60:
            state = "多頭"
        elif not is_above_ma60 and not is_ma20_above_ma60:
            state = "空頭"
        else:
            state = "盤整"
            
        print(f"===== 大盤趨勢分析完成！當前狀態: {state} =====")
        return state

    except Exception as e:
        print(f"錯誤：分析大盤趨勢時發生錯誤: {e}")
        return "盤整" # 如果出錯，預設為中性的盤整市