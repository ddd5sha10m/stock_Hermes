# technical_analyzer.py

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np

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