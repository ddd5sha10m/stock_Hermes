# technical_analyzer.py
'''
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

CANDLESTICK_PATTERNS = {
    'bullish': {
        'cdl_hammer': '鎚子線 (Hammer)',
        'cdl_inversehammer': '倒鎚子線 (Inverse Hammer)',
        'cdl_engulfing': '多頭吞噬 (Bullish Engulfing)',
        'cdl_piercing': '穿刺線 (Piercing Line)',
        'cdl_morningstar': '早晨之星 (Morning Star)',
        'cdl_3whitesoldiers': '三個白兵 (Three White Soldiers)',
    },
    'bearish': {
        'cdl_hangingman': '上吊線 (Hanging Man)',
        'cdl_shootingstar': '射擊之星 (Shooting Star)',
        'cdl_engulfing': '空頭吞噬 (Bearish Engulfing)',
        'cdl_eveningstar': '黃昏之星 (Evening Star)',
        'cdl_3blackcrows': '三隻烏鴉 (Three Black Crows)',
        'cdl_darkcloudcover': '烏雲罩頂 (Dark Cloud Cover)',
    }
}

PATTERN_EXPLANATIONS = {
    '鎚子線 (Hammer)': '通常在下跌趨勢中出現，帶長下影線，實體部分較小，可能為底部反轉訊號。',
    '倒鎚子線 (Inverse Hammer)': '在下跌趨勢中出現，帶長上影線，實體部分較小，也是可能的底部反轉訊號。',
    '多頭吞噬 (Bullish Engulfing)': '一根長紅 K 棒完全包覆前一根黑 K 棒的實體，是強烈的底部反轉訊號。',
    '穿刺線 (Piercing Line)': '下跌趨勢中，一根長紅 K 棒的開盤價低於前一日最低價，收盤價深入前一日黑 K 棒實體的一半以上，為反轉訊號。',
    '早晨之星 (Morning Star)': '由一根長黑 K、一根跳空向下的十字星/小實體、以及一根長紅 K 組成，是強烈的底部反轉訊號。',
    '三個白兵 (Three White Soldiers)': '連續三根收盤價持續走高的長紅 K 棒，是強勁的看漲訊號。',
    '上吊線 (Hanging Man)': '通常在上升趨勢中出現，形狀與鎚子線相同，但可能為頭部反轉訊號。',
    '射擊之星 (Shooting Star)': '在上升趨勢中出現，形狀與倒鎚子線相同，是可能的頭部反轉訊號。',
    '空頭吞噬 (Bearish Engulfing)': '一根長黑 K 棒完全包覆前一根紅 K 棒的實體，是強烈的頭部反轉訊號。',
    '黃昏之星 (Evening Star)': '由一根長紅 K、一根跳空向上的十字星/小實體、以及一根長黑 K 組成，是強烈的頭部反轉訊號。',
    '三隻烏鴉 (Three Black Crows)': '連續三根收盤價持續走低的長黑 K 棒，是強勁的看跌訊號。',
    '烏雲罩頂 (Dark Cloud Cover)': '上升趨勢中，一根長黑 K 棒的開盤價高於前一日最高價，收盤價深入前一日紅 K 棒實體的一半以上，為反轉訊號。'
}
def find_latest_candlestick_pattern(data):
    """
    在已經包含 K 棒型態欄位的資料中，由近到遠搜尋訊號
    """
    windows = {'一週': 5, '兩週': 10, '一個月': 22, '兩個月': 44, '一季': 66}
    
    for window_name, window_size in windows.items():
        if len(data) < window_size: continue
        
        recent_data = data.tail(window_size)

        for i in range(len(recent_data) - 1, -1, -1):
            row = recent_data.iloc[i]
            # 檢查看漲型態
            for pattern_code, pattern_name in CANDLESTICK_PATTERNS['bullish'].items():
                col_name = f"CDL{pattern_code.replace('cdl_', '').upper()}"
                if col_name in row.index and row[col_name] > 0:
                    return {
                        "date": row.name.strftime('%Y-%m-%d'),
                        "pattern_name": pattern_name,
                        "type": "看漲",
                        "explanation": PATTERN_EXPLANATIONS[pattern_name],
                        "window": window_name
                    }
            # 檢查看跌型態
            for pattern_code, pattern_name in CANDLESTICK_PATTERNS['bearish'].items():
                col_name = f"CDL{pattern_code.replace('cdl_', '').upper()}"
                if col_name in row.index and row[col_name] < 0:
                    return {
                        "date": row.name.strftime('%Y-%m-%d'),
                        "pattern_name": pattern_name,
                        "type": "看跌",
                        "explanation": PATTERN_EXPLANATIONS[pattern_name],
                        "window": window_name
                    }
                    
    return None
    '''
'''
# 【新增】漸進式搜尋 K 棒型態的函式
def find_latest_candlestick_pattern(data):
    """
    由近到遠，在不同的時間週期內搜尋最近出現的 K 棒型態
    """
    windows = {'一週': 5, '兩週': 10, '一個月': 22, '兩個月': 44, '一季': 66}
    
    all_pattern_codes = list(CANDLESTICK_PATTERNS['bullish'].keys()) + list(CANDLESTICK_PATTERNS['bearish'].keys())
    all_pattern_codes = list(dict.fromkeys(all_pattern_codes))

    for window_name, window_size in windows.items():
        if len(data) < window_size: continue
        
        recent_data = data.tail(window_size).copy()
        
        # --- 【核心修正】 ---
        # 逐一呼叫每種 K 棒型態的分析函式
        for pattern_code in all_pattern_codes:
            # 取得對應的函式名稱 (例如 'cdl_hammer' -> 'hammer')
            func_name = pattern_code.replace('cdl_', '')
            
            # 檢查 pandas-ta 是否支援這個函式
            if hasattr(recent_data.ta, func_name):
                # 動態呼叫函式
                getattr(recent_data.ta, func_name)(append=True)

        # 從最近的一天開始，往前尋找訊號
        for i in range(len(recent_data) - 1, -1, -1):
            row = recent_data.iloc[i]
            # 檢查看漲型態
            for pattern_code, pattern_name in CANDLESTICK_PATTERNS['bullish'].items():
                # 【修正】產生正確的欄位名稱 (例如 CDLHAMMER)
                col_name = f"CDL{pattern_code.replace('cdl_', '').upper()}"
                if col_name in row.index and row[col_name] > 0:
                    return {
                        "date": row.name.strftime('%Y-%m-%d'),
                        "pattern_name": pattern_name,
                        "type": "看漲",
                        "explanation": PATTERN_EXPLANATIONS[pattern_name],
                        "window": window_name
                    }
            # 檢查看跌型態
            for pattern_code, pattern_name in CANDLESTICK_PATTERNS['bearish'].items():
                col_name = f"CDL{pattern_code.replace('cdl_', '').upper()}"
                if col_name in row.index and row[col_name] < 0:
                    return {
                        "date": row.name.strftime('%Y-%m-%d'),
                        "pattern_name": pattern_name,
                        "type": "看跌",
                        "explanation": PATTERN_EXPLANATIONS[pattern_name],
                        "window": window_name
                    }
                    
    return None



def analyze_stock_technicals(ticker, period="1y"):
    """
    獲取並分析指定股票的技術數據，整合 MA, KD, MACD, BBands 及量價分析。
    """
    print(f"===== 開始分析 {ticker} 的技術數據... =====")
    
    # 1. 獲取股價數據
    ticker_obj = yf.Ticker(ticker)
    stock_data = ticker_obj.history(period=period, interval="1d", auto_adjust=True)

    if stock_data.empty:
        print(f"錯誤：無法獲取 {ticker} 的數據。")
        return None

    stock_data.columns = [col.capitalize() for col in stock_data.columns]

    # --- 2. 計算各項技術指標 ---
    
    # 計算 MA
    stock_data['MA5'] = stock_data['Close'].rolling(window=5).mean()
    stock_data['MA20'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['MA60'] = stock_data['Close'].rolling(window=60).mean()
    
    # 計算 KD
    stock_data.ta.stoch(k=9, d=3, smooth_k=3, append=True)
    stock_data.rename(columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'}, inplace=True)

    # 計算 MACD
    stock_data.ta.macd(append=True)
    stock_data.rename(columns={'MACD_12_26_9': 'DIF', 'MACDh_12_26_9': 'OSC', 'MACDs_12_26_9': 'DEM'}, inplace=True)

    # 計算布林通道
    bbands_df = stock_data.ta.bbands(length=20, std=2)
    if bbands_df is not None and not bbands_df.empty:
        stock_data['BB_Lower'] = bbands_df.iloc[:, 0]
        stock_data['BB_Middle'] = bbands_df.iloc[:, 1]
        stock_data['BB_Upper'] = bbands_df.iloc[:, 2]
    
    # 3. 分析量價結構
    stock_data['Close_yesterday'] = stock_data['Close'].shift(1)
    stock_data['Volume_yesterday'] = stock_data['Volume'].shift(1)

    conditions = [
        (stock_data['Close'] > stock_data['Close_yesterday']) & (stock_data['Volume'] > stock_data['Volume_yesterday']),
        (stock_data['Close'] > stock_data['Close_yesterday']) & (stock_data['Volume'] <= stock_data['Volume_yesterday']),
        (stock_data['Close'] < stock_data['Close_yesterday']) & (stock_data['Volume'] > stock_data['Volume_yesterday']),
        (stock_data['Close'] < stock_data['Close_yesterday']) & (stock_data['Volume'] <= stock_data['Volume_yesterday'])
    ]
    choices = ['價漲量增', '價漲量縮', '價跌量增', '價跌量縮']
    stock_data['Volume_Price_Signal'] = np.select(conditions, choices, default='價平')

    # 4. 判斷交叉
    for col in ['MA5', 'MA20', 'K', 'D', 'DIF', 'DEM']:
        if col in stock_data.columns: stock_data[f'{col}_yesterday'] = stock_data[col].shift(1)

    if all(x in stock_data.columns for x in ['MA5', 'MA20', 'MA5_yesterday', 'MA20_yesterday']):
        stock_data['Golden_Cross_5_20'] = (stock_data['MA5'] > stock_data['MA20']) & (stock_data['MA5_yesterday'] < stock_data['MA20_yesterday'])
    if all(x in stock_data.columns for x in ['K', 'D', 'K_yesterday', 'D_yesterday']):
        stock_data['Golden_Cross_KD'] = (stock_data['K'] > stock_data['D']) & (stock_data['K_yesterday'] < stock_data['D_yesterday'])
    if all(x in stock_data.columns for x in ['DIF', 'DEM', 'DIF_yesterday', 'DEM_yesterday']):
        stock_data['Golden_Cross_MACD'] = (stock_data['DIF'] > stock_data['DEM']) & (stock_data['DIF_yesterday'] < stock_data['DEM_yesterday'])
    
    
    
    print(f"===== {ticker} 技術分析完成！ =====")
    return stock_data
'''
# technical_analyzer.py - 完整優化版

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

def find_support_resistance(data, window=20):
    """尋找近期重要支撐壓力位"""
    if len(data) < window:
        return None, None
    
    recent_data = data.tail(window)
    resistance = recent_data['High'].rolling(5).max().max()
    support = recent_data['Low'].rolling(5).min().min()
    return support, resistance

def bull_bear_balance(data):
    """評估多空力道平衡 (-1到1之間，1為強多頭，-1為強空頭)"""
    if data.empty or len(data) < 2:
        return 0
        
    latest = data.iloc[-1]
    
    bull_signals = 0
    bear_signals = 0
    total_signals = 0
    
    # 趨勢訊號
    if 'MA20' in latest.index and 'MA60' in latest.index:
        if latest['Close'] > latest['MA20']: bull_signals += 1
        else: bear_signals += 1
        total_signals += 1
        
        if latest['MA20'] > latest['MA60']: bull_signals += 1
        else: bear_signals += 1
        total_signals += 1
    
    # 動量訊號
    if 'RSI' in latest.index:
        if latest['RSI'] > 50: bull_signals += 1
        else: bear_signals += 1
        total_signals += 1
    
    if 'K' in latest.index and 'D' in latest.index:
        if latest['K'] > latest['D']: bull_signals += 1
        else: bear_signals += 1
        total_signals += 1
    
    if 'DIF' in latest.index and 'DEM' in latest.index:
        if latest['DIF'] > latest['DEM']: bull_signals += 1
        else: bear_signals += 1
        total_signals += 1
    
    if total_signals == 0:
        return 0
        
    balance_score = (bull_signals - bear_signals) / total_signals
    return balance_score

def analyze_stock_technicals(ticker, period="1y"):
    """
    獲取並分析指定股票的技術數據，整合完整的技術分析指標
    """
    print(f"===== 開始分析 {ticker} 的技術數據... =====")
    
    # 1. 獲取股價數據
    ticker_obj = yf.Ticker(ticker)
    stock_data = ticker_obj.history(period=period, interval="1d", auto_adjust=True)

    if stock_data.empty:
        print(f"錯誤：無法獲取 {ticker} 的數據。")
        return None

    stock_data.columns = [col.capitalize() for col in stock_data.columns]

    # --- 2. 計算基礎技術指標 ---
    
    # 計算 MA
    stock_data['MA5'] = stock_data['Close'].rolling(window=5).mean()
    stock_data['MA20'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['MA60'] = stock_data['Close'].rolling(window=60).mean()
    
    # 計算乖離率
    stock_data['Deviation_MA20'] = (stock_data['Close'] - stock_data['MA20']) / stock_data['MA20'] * 100
    stock_data['Deviation_MA60'] = (stock_data['Close'] - stock_data['MA60']) / stock_data['MA60'] * 100
    
    # 計算 KD
    stock_data.ta.stoch(k=9, d=3, smooth_k=3, append=True)
    if 'STOCHk_9_3_3' in stock_data.columns:
        stock_data.rename(columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'}, inplace=True)

    # 計算 RSI
    stock_data.ta.rsi(length=14, append=True)
    if 'RSI_14' in stock_data.columns:
        stock_data.rename(columns={'RSI_14': 'RSI'}, inplace=True)

    # 計算 MACD
    stock_data.ta.macd(append=True)
    if all(col in stock_data.columns for col in ['MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9']):
        stock_data.rename(columns={
            'MACD_12_26_9': 'DIF', 
            'MACDh_12_26_9': 'OSC', 
            'MACDs_12_26_9': 'DEM'
        }, inplace=True)

    # 計算 ATR (風險指標)
    stock_data.ta.atr(length=14, append=True)
    if 'ATR_14' in stock_data.columns:
        stock_data.rename(columns={'ATR_14': 'ATR'}, inplace=True)
    
    # 計算 ADX (趨勢強度)
    stock_data.ta.adx(length=14, append=True)
    # ADX相關欄位可能包含 ADX_14, DMP_14, DMN_14

    # 計算布林通道
    bbands_df = stock_data.ta.bbands(length=20, std=2)
    if bbands_df is not None and not bbands_df.empty:
        stock_data['BB_Lower'] = bbands_df.iloc[:, 0]
        stock_data['BB_Middle'] = bbands_df.iloc[:, 1]
        stock_data['BB_Upper'] = bbands_df.iloc[:, 2]
        
        # 計算布林通道位置 (0-1之間，0.5為中線)
        stock_data['BB_Position'] = ((stock_data['Close'] - stock_data['BB_Lower']) / 
                                   (stock_data['BB_Upper'] - stock_data['BB_Lower']))
    
    # --- 3. 優化成交量分析 ---
    stock_data['Volume_MA20'] = stock_data['Volume'].rolling(20).mean()
    stock_data['Volume_Ratio'] = stock_data['Volume'] / stock_data['Volume_MA20']
    
    stock_data['Close_yesterday'] = stock_data['Close'].shift(1)
    stock_data['Volume_yesterday'] = stock_data['Volume'].shift(1)

    # 改進量價關係分析
    conditions = [
        (stock_data['Close'] > stock_data['Close_yesterday']) & (stock_data['Volume_Ratio'] > 1.2),  # 放量上漲
        (stock_data['Close'] > stock_data['Close_yesterday']) & (stock_data['Volume_Ratio'] <= 1.2),  # 縮量上漲
        (stock_data['Close'] < stock_data['Close_yesterday']) & (stock_data['Volume_Ratio'] > 1.2),   # 放量下跌
        (stock_data['Close'] < stock_data['Close_yesterday']) & (stock_data['Volume_Ratio'] <= 1.2),  # 縮量下跌
    ]
    choices = ['價漲量增', '價漲量縮', '價跌量增', '價跌量縮']
    stock_data['Volume_Price_Signal'] = np.select(conditions, choices, default='價平')

    # 4. 判斷各種交叉訊號
    for col in ['MA5', 'MA20', 'K', 'D', 'DIF', 'DEM']:
        if col in stock_data.columns: 
            stock_data[f'{col}_yesterday'] = stock_data[col].shift(1)

    # MA交叉
    if all(x in stock_data.columns for x in ['MA5', 'MA20', 'MA5_yesterday', 'MA20_yesterday']):
        stock_data['Golden_Cross_5_20'] = (stock_data['MA5'] > stock_data['MA20']) & (stock_data['MA5_yesterday'] < stock_data['MA20_yesterday'])
        stock_data['Death_Cross_5_20'] = (stock_data['MA5'] < stock_data['MA20']) & (stock_data['MA5_yesterday'] > stock_data['MA20_yesterday'])
    
    # KD交叉
    if all(x in stock_data.columns for x in ['K', 'D', 'K_yesterday', 'D_yesterday']):
        stock_data['Golden_Cross_KD'] = (stock_data['K'] > stock_data['D']) & (stock_data['K_yesterday'] < stock_data['D_yesterday'])
        stock_data['Death_Cross_KD'] = (stock_data['K'] < stock_data['D']) & (stock_data['K_yesterday'] > stock_data['D_yesterday'])
    
    # MACD交叉
    if all(x in stock_data.columns for x in ['DIF', 'DEM', 'DIF_yesterday', 'DEM_yesterday']):
        stock_data['Golden_Cross_MACD'] = (stock_data['DIF'] > stock_data['DEM']) & (stock_data['DIF_yesterday'] < stock_data['DEM_yesterday'])
        stock_data['Death_Cross_MACD'] = (stock_data['DIF'] < stock_data['DEM']) & (stock_data['DIF_yesterday'] > stock_data['DEM_yesterday'])
    
    # --- 5. 計算綜合指標 ---
    
    # 多空力道平衡
    stock_data['Bull_Bear_Balance'] = stock_data.apply(
        lambda row: bull_bear_balance(stock_data.loc[:row.name]), axis=1
    )
    
    # 計算支撐壓力位（最新的）
    support, resistance = find_support_resistance(stock_data)
    if support is not None and resistance is not None:
        stock_data['Support_Level'] = support
        stock_data['Resistance_Level'] = resistance
        # 計算當前價格相對於支撐壓力的位置
        stock_data['SR_Position'] = ((stock_data['Close'] - support) / (resistance - support))
    
    # 波動率風險評估
    if 'ATR' in stock_data.columns:
        stock_data['Volatility_Risk'] = stock_data['ATR'] / stock_data['Close'] * 100
    
    print(f"===== {ticker} 完整技術分析完成！ =====")
    return stock_data