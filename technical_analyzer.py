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