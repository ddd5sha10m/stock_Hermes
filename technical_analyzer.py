
# technical_analyzer.py (效能優化版)

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

def find_support_resistance(data, window=20):
    """尋找近期重要支撐壓力位"""
    if len(data) < window:
        return None, None
    
    recent_data = data.tail(window * 3) # 放大尋找範圍以提高準確性
    
    # 使用 find_peaks 尋找波峰波谷 (更精準的作法)
    try:
        from scipy.signal import find_peaks
        # 尋找高點 (壓力)
        resistance_indices, _ = find_peaks(recent_data['High'], distance=5, prominence=recent_data['High'].std()*0.5)
        # 尋找低點 (支撐)
        support_indices, _ = find_peaks(-recent_data['Low'], distance=5, prominence=recent_data['Low'].std()*0.5)
        
        highs = recent_data['High'].iloc[resistance_indices].values
        lows = recent_data['Low'].iloc[support_indices].values
        
    except (ImportError, Exception):
        # 如果 scipy 未安裝或出錯，則退回簡易版
        highs = recent_data['High'].rolling(5, center=True).max().dropna().values
        lows = recent_data['Low'].rolling(5, center=True).min().dropna().values

    current_price = data['Close'].iloc[-1]
    
    resistance_levels = [h for h in highs if h > current_price]
    support_levels = [l for l in lows if l < current_price]
    
    # 找出最接近的一個支撐和一個壓力
    resistance = min(resistance_levels) if resistance_levels else current_price * 1.15
    support = max(support_levels) if support_levels else current_price * 0.85
        
    return support, resistance

def bull_bear_balance(data):
    """評估多空力道平衡 (-1到1之間)"""
    if data.empty or len(data) < 2:
        return 0
        
    # 【效能優化】此函式現在只會被呼叫一次，所以直接取最後一筆資料即可
    latest = data.iloc[-1]
    
    bull_signals = 0
    bear_signals = 0
    total_signals = 0
    
    required_indicators = ['MA20', 'MA60', 'RSI', 'K', 'D', 'DIF', 'DEM']
    if not all(ind in latest.index for ind in required_indicators):
        # 如果缺少任一指標，無法計算
        return 0

    # 趨勢訊號
    if latest['Close'] > latest['MA20']: bull_signals += 1
    else: bear_signals += 1
    total_signals += 1
    if latest['MA20'] > latest['MA60']: bull_signals += 1
    else: bear_signals += 1
    total_signals += 1
    
    # 動量訊號
    if latest['RSI'] > 50: bull_signals += 1
    else: bear_signals += 1
    total_signals += 1
    if latest['K'] > latest['D']: bull_signals += 1
    else: bear_signals += 1
    total_signals += 1
    if latest['DIF'] > latest['DEM']: bull_signals += 1
    else: bear_signals += 1
    total_signals += 1
    
    if total_signals == 0:
        return 0
        
    balance_score = (bull_signals - bear_signals) / total_signals
    return balance_score

def analyze_stock_technicals(ticker_obj, period="1y"):
    """
    獲取並分析指定股票的技術數據
    """
    # print(f"===== 開始分析 {ticker} 的技術數據... =====") # 在掃描器模式下，為保持畫面乾淨可註解此行
    
    # 1. 獲取股價數據
    stock_data = ticker_obj.history(period=period, interval="1d", auto_adjust=True)

    if stock_data.empty or len(stock_data) < 60: # 確保有足夠數據計算長天期MA
        # print(f"錯誤：無法獲取 {ticker} 的數據或數據量不足。")
        return None

    stock_data.columns = [col.capitalize() for col in stock_data.columns]

    # --- 2. 計算所有需要的基礎技術指標 ---
    stock_data['MA5'] = stock_data['Close'].rolling(window=5).mean()
    stock_data['MA20'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['MA60'] = stock_data['Close'].rolling(window=60).mean()
    
    stock_data['Deviation_MA20'] = (stock_data['Close'] - stock_data['MA20']) / stock_data['MA20'] * 100
    stock_data['Deviation_MA60'] = (stock_data['Close'] - stock_data['MA60']) / stock_data['MA60'] * 100
    
    # 使用 pandas-ta 一次性計算多個指標，效率更高
    stock_data.ta.stoch(k=9, d=3, smooth_k=3, append=True)
    stock_data.ta.rsi(length=14, append=True)
    stock_data.ta.macd(append=True)
    stock_data.ta.atr(length=14, append=True)
    stock_data.ta.adx(length=14, append=True)
    stock_data.ta.obv(append=True)
    
    bbands_df = stock_data.ta.bbands(length=20, std=2)
    if bbands_df is not None and not bbands_df.empty:
        stock_data['BB_Lower'] = bbands_df.iloc[:, 0]
        stock_data['BB_Middle'] = bbands_df.iloc[:, 1]
        stock_data['BB_Upper'] = bbands_df.iloc[:, 2]
        stock_data['BB_Position'] = ((stock_data['Close'] - stock_data['BB_Lower']) / 
                                   (stock_data['BB_Upper'] - stock_data['BB_Lower']))
    
    # 重新命名 pandas-ta 產生的欄位
    stock_data.rename(columns={
        'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D',
        'RSI_14': 'RSI',
        'MACD_12_26_9': 'DIF', 'MACDh_12_26_9': 'OSC', 'MACDs_12_26_9': 'DEM',
        'ATR_14': 'ATR',
    }, inplace=True)

    # --- 3. 優化成交量分析 ---
    stock_data['Volume_MA20'] = stock_data['Volume'].rolling(20).mean()
    stock_data['Volume_Ratio'] = stock_data['Volume'] / stock_data['Volume_MA20']
    
    stock_data['Close_yesterday'] = stock_data['Close'].shift(1)
    conditions = [
        (stock_data['Close'] > stock_data['Close_yesterday']) & (stock_data['Volume_Ratio'] > 1.1),
        (stock_data['Close'] > stock_data['Close_yesterday']),
        (stock_data['Close'] < stock_data['Close_yesterday']) & (stock_data['Volume_Ratio'] > 1.1),
        (stock_data['Close'] < stock_data['Close_yesterday']),
    ]
    choices = ['價漲量增', '價漲量縮', '價跌量增', '價跌量縮']
    stock_data['Volume_Price_Signal'] = np.select(conditions, choices, default='價平')

    # --- 4. 判斷交叉訊號 (僅判斷最後一天) ---
    for col in ['MA5', 'MA20', 'K', 'D', 'DIF', 'DEM']:
        if col in stock_data.columns: 
            stock_data[f'{col}_yesterday'] = stock_data[col].shift(1)
            
    latest_index = stock_data.index[-1]
    latest_row = stock_data.iloc[-1]

    if 'MA5' in latest_row and 'MA20' in latest_row and 'MA5_yesterday' in latest_row and 'MA20_yesterday' in latest_row:
        stock_data.loc[latest_index, 'Golden_Cross_5_20'] = (latest_row['MA5'] > latest_row['MA20']) and (latest_row['MA5_yesterday'] < latest_row['MA20_yesterday'])
    if 'K' in latest_row and 'D' in latest_row and 'K_yesterday' in latest_row and 'D_yesterday' in latest_row:
        stock_data.loc[latest_index, 'Golden_Cross_KD'] = (latest_row['K'] > latest_row['D']) and (latest_row['K_yesterday'] < latest_row['D_yesterday'])
    if 'DIF' in latest_row and 'DEM' in latest_row and 'DIF_yesterday' in latest_row and 'DEM_yesterday' in latest_row:
        stock_data.loc[latest_index, 'Golden_Cross_MACD'] = (latest_row['DIF'] > latest_row['DEM']) and (latest_row['DIF_yesterday'] < latest_row['DEM_yesterday'])

    # --- 5. 計算綜合指標 ---
    
    # 【效能優化】移除 apply 迴圈，只計算一次最新的多空力道平衡分數
    latest_balance_score = bull_bear_balance(stock_data)
    stock_data.loc[latest_index, 'Bull_Bear_Balance'] = latest_balance_score
    
    support, resistance = find_support_resistance(stock_data)
    if support is not None and resistance is not None:
        stock_data.loc[latest_index, 'Support_Level'] = support
        stock_data.loc[latest_index, 'Resistance_Level'] = resistance
    
    if 'ATR' in stock_data.columns:
        stock_data['Volatility_Risk'] = stock_data['ATR'] / stock_data['Close'] * 100
    
    # print(f"===== {ticker} 完整技術分析完成！ =====") # 在掃描器模式下可註解
    return stock_data