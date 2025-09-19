import yfinance as yf
import pandas as pd
import pandas_ta as ta
from scipy.signal import find_peaks
import numpy as np # 引入 numpy 函式庫

# 設定 Pandas 顯示選項
pd.set_option('display.expand_frame_repr', False)
'''
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
    
    # 計算 KD (rename 相對穩定，暫時保留)
    stock_data.ta.stoch(k=9, d=3, smooth_k=3, append=True)
    stock_data.rename(columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'}, inplace=True)

    # 計算 MACD (rename 相對穩定，暫時保留)
    stock_data.ta.macd(append=True)
    stock_data.rename(columns={'MACD_12_26_9': 'DIF', 'MACDh_12_26_9': 'OSC', 'MACDs_12_26_9': 'DEM'}, inplace=True)

    # 【終極修正】不再依賴寫死的欄位名稱，而是根據欄位的「順序」來賦值
    bbands_df = stock_data.ta.bbands(length=20, std=2)
    if bbands_df is not None and not bbands_df.empty:
        # pandas-ta bbands 回傳的順序固定是：Lower, Middle, Upper, Width, ...
        stock_data['BB_Lower'] = bbands_df.iloc[:, 0]  # 第 1 欄: Lower Band
        stock_data['BB_Middle'] = bbands_df.iloc[:, 1] # 第 2 欄: Middle Band
        stock_data['BB_Upper'] = bbands_df.iloc[:, 2]  # 第 3 欄: Upper Band
        stock_data['BB_Width'] = bbands_df.iloc[:, 3]  # 第 4 欄: Bandwidth
    
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
        # 檢查欄位是否存在，避免因計算失敗而出錯
        if col in stock_data.columns:
            stock_data[f'{col}_yesterday'] = stock_data[col].shift(1)

    # 同樣檢查欄位是否存在，再進行判斷
    if 'MA5' in stock_data.columns and 'MA20' in stock_data.columns:
        stock_data['Golden_Cross_5_20'] = (stock_data['MA5'] > stock_data['MA20']) & (stock_data['MA5_yesterday'] < stock_data['MA20_yesterday'])
    if 'K' in stock_data.columns and 'D' in stock_data.columns:
        stock_data['Golden_Cross_KD'] = (stock_data['K'] > stock_data['D']) & (stock_data['K_yesterday'] < stock_data['D_yesterday'])
    if 'DIF' in stock_data.columns and 'DEM' in stock_data.columns:
        stock_data['Golden_Cross_MACD'] = (stock_data['DIF'] > stock_data['DEM']) & (stock_data['DIF_yesterday'] < stock_data['DEM_yesterday'])
    
    print(f"===== {ticker} 技術分析完成！ =====")
    return stock_data

# --- 主程式執行 ---
if __name__ == "__main__":
    stock_ticker = "2330.TW"
    tsmc_data = analyze_stock_technicals(stock_ticker)

    if tsmc_data is not None:
        latest_row = tsmc_data.iloc[-1]
        
        print("\n--- 最新數據摘要 ---")
        print(f"股票代號: {stock_ticker}")
        print(f"最新收盤價: {latest_row['Close']:.2f}")
        print(f"布林通道 (上/中/下): {latest_row['BB_Upper']:.2f} / {latest_row['BB_Middle']:.2f} / {latest_row['BB_Lower']:.2f}")
        print(f"K值: {latest_row['K']:.2f}, D值: {latest_row['D']:.2f}")
        print(f"DIF: {latest_row['DIF']:.2f}, DEM: {latest_row['DEM']:.2f}")
        print("--------------------")

        print("\n--- 即時訊號分析 ---")
        # 量價關係
        print(f"量價關係: {latest_row['Volume_Price_Signal']}")
        # 布林通道狀態
        if latest_row['Close'] > latest_row['BB_Upper']:
            print("訊號：股價觸及布林通道【上軌】，趨勢強勁或超買。")
        elif latest_row['Close'] < latest_row['BB_Lower']:
            print("訊號：股價觸及布林通道【下軌】，趨勢疲弱或超賣。")
        else:
            print("狀態：股價在布林通道區間內震盪。")
        print(f"布林帶寬: {latest_row['BB_Width']:.4f}")
        
        # 交叉訊號
        if latest_row['Golden_Cross_5_20']: print("訊號：5日與20日均線黃金交叉")
        if latest_row['Golden_Cross_KD']: print("訊號：KD指標黃金交叉")
        if latest_row['Golden_Cross_MACD']: print("訊號：MACD指標黃金交叉")
        
        print("\n--- MACD 底背離分析 (近半年) ---")
        # (此區塊程式碼不變，故省略以保持簡潔)
        search_range = tsmc_data.tail(120)
        price_lows_indices, _ = find_peaks(-search_range['Low'], distance=10)
        osc_lows_indices, _ = find_peaks(-search_range['OSC'], distance=10)
        
        divergence_found = False
        if len(price_lows_indices) >= 2 and len(osc_lows_indices) >= 2:
            last_price_low_idx = price_lows_indices[-1]
            prev_price_low_idx = price_lows_indices[-2]
            last_osc_low_idx = osc_lows_indices[-1]
            prev_osc_low_idx = osc_lows_indices[-2]
            
            last_price_low_date = search_range.index[last_price_low_idx]
            last_price_low = search_range['Low'].iloc[last_price_low_idx]
            prev_price_low_date = search_range.index[prev_price_low_idx]
            prev_price_low = search_range['Low'].iloc[prev_price_low_idx]
            last_osc_low = search_range['OSC'].iloc[last_osc_low_idx]
            prev_osc_low = search_range['OSC'].iloc[prev_osc_low_idx]
            
            if (last_price_low < prev_price_low) and (last_osc_low > prev_osc_low):
                divergence_found = True
                print("訊號：發現潛在的 MACD 底背離！")
                print(f"  - 前期低點: {prev_price_low_date.date()} 價格={prev_price_low:.2f}, OSC={prev_osc_low:.2f}")
                print(f"  - 近期低點: {last_price_low_date.date()} 價格={last_price_low:.2f} (新低), OSC={last_osc_low:.2f} (更高)")
        
        if not divergence_found:
            print("狀態：近期未發現明顯的 MACD 底背離訊號。")
'''
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from scipy.signal import find_peaks
import numpy as np

pd.set_option('display.expand_frame_repr', False)

def analyze_stock_technicals(ticker, period="1y"):
    """分析股票技術數據"""
    print(f"===== 開始分析 {ticker} 的技術數據... =====")
    ticker_obj = yf.Ticker(ticker)
    stock_data = ticker_obj.history(period=period, interval="1d", auto_adjust=True)
    if stock_data.empty: return None
    stock_data.columns = [col.capitalize() for col in stock_data.columns]
    
    # 計算指標
    stock_data['MA5'] = stock_data['Close'].rolling(window=5).mean()
    stock_data['MA20'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['MA60'] = stock_data['Close'].rolling(window=60).mean()
    
    stock_data.ta.stoch(k=9, d=3, smooth_k=3, append=True)
    stock_data.rename(columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'}, inplace=True)

    stock_data.ta.macd(append=True)
    stock_data.rename(columns={'MACD_12_26_9': 'DIF', 'MACDh_12_26_9': 'OSC', 'MACDs_12_26_9': 'DEM'}, inplace=True)

    bbands_df = stock_data.ta.bbands(length=20, std=2)
    if bbands_df is not None and not bbands_df.empty:
        stock_data['BB_Lower'] = bbands_df.iloc[:, 0]
        stock_data['BB_Middle'] = bbands_df.iloc[:, 1]
        stock_data['BB_Upper'] = bbands_df.iloc[:, 2]

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

def calculate_technical_score(data):
    """根據最新的技術數據計算綜合分數"""
    score = 0
    total_possible_score = 100
    details = []
    latest = data.iloc[-1]

    # 趨勢狀態 (40分)
    if latest['Close'] > latest['MA60']: score += 15; details.append("價格 > 60MA (+15)")
    if latest['MA20'] > latest['MA60']: score += 10; details.append("20MA > 60MA (+10)")
    if latest['Close'] > latest['MA20']: score += 10; details.append("價格 > 20MA (+10)")
    if latest['MA5'] > latest['MA20']: score += 5; details.append("5MA > 20MA (+5)")

    # 動能狀態 (30分)
    if latest['K'] > latest['D']: score += 5; details.append("K > D (+5)")
    if latest['K'] < 20: score += 5; details.append("K < 20 超賣區 (+5)")
    if latest['DIF'] > latest['DEM']: score += 5; details.append("DIF > DEM (+5)")
    if latest['OSC'] > 0: score += 5; details.append("OSC > 0 (+5)")
    if latest.get('Golden_Cross_KD', False) or latest.get('Golden_Cross_MACD', False):
        score += 10; details.append("當日發生黃金交叉 (+10)")

    # 波動與量價 (30分)
    if latest['Close'] > latest['BB_Upper']: score += 10; details.append("突破布林上軌 (+10)")
    elif latest['Close'] < latest['BB_Lower']: score -= 10; details.append("跌破布林下軌 (-10)")
    
    vp_signal = latest['Volume_Price_Signal']
    if vp_signal == '價漲量增': score += 10; details.append("價漲量增 (+10)")
    elif vp_signal == '價跌量縮': score += 5; details.append("價跌量縮 (+5)")
    elif vp_signal == '價跌量增': score -= 10; details.append("價跌量增 (-10)")

    # Clamp score to be within 0 and total_possible_score
    score = max(0, min(score, total_possible_score))
    
    return score, details

# --- 主程式執行 ---
if __name__ == "__main__":
    stock_ticker = "2330.TW"
    tsmc_data = analyze_stock_technicals(stock_ticker)

    if tsmc_data is not None:
        technical_score, scoring_details = calculate_technical_score(tsmc_data)

        print("\n--- 最新數據摘要 ---")
        latest_row = tsmc_data.iloc[-1]
        print(f"股票代號: {stock_ticker}")
        print(f"最新收盤價: {latest_row['Close']:.2f}")
        
        print("\n--- 技術面綜合評分 ---")
        print(f"總分: {technical_score} / 100")
        print("評分細節:")
        for detail in scoring_details:
            print(f"  - {detail}")