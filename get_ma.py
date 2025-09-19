import yfinance as yf
import pandas as pd
import pandas_ta as ta # 引入 pandas-ta 函式庫

# 設定 Pandas 顯示選項，讓輸出的表格更整齊
pd.set_option('display.expand_frame_repr', False)

def analyze_stock_technicals(ticker, period="1y"):
    """
    獲取並分析指定股票的技術數據，包含 MA, KD 計算與交叉判斷。

    :param ticker: 股票代號，台股需要加上 .TW
    :param period: 獲取數據的時間範圍
    :return: 包含完整技術分析數據的 DataFrame
    """
    print(f"===== 開始分析 {ticker} 的技術數據... =====")
    
    # --- 1. 獲取股價數據 (修改部分) ---
    # 改用 yf.Ticker()，這個方法對於獲取單一股票的數據更穩定，且回傳的 DataFrame 格式更乾淨
    ticker_obj = yf.Ticker(ticker)
    stock_data = ticker_obj.history(period=period, interval="1d", auto_adjust=True)

    if stock_data.empty:
        print(f"錯誤：無法獲取 {ticker} 的數據，請檢查股票代號是否正確。")
        return None

    # 將所有欄位名稱轉為大寫開頭 (e.g. open -> Open)，確保與後續程式碼一致
    stock_data.columns = [col.capitalize() for col in stock_data.columns]

    # 2. 計算移動平均線 (MA)
    stock_data['MA5'] = stock_data['Close'].rolling(window=5).mean()
    stock_data['MA20'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['MA60'] = stock_data['Close'].rolling(window=60).mean()

    # --- 3. 計算 KD 指標 ---
    # 使用 pandas-ta 直接計算 KD 指標 (台股常用參數為 9,3,3)
    # 這會自動新增 STOCHk_9_3_3 和 STOCHd_9_3_3 兩個欄位
    stock_data.ta.stoch(k=9, d=3, smooth_k=3, append=True)
    
    # 為了方便使用，我們將欄位重新命名為 'K' 和 'D'
    stock_data.rename(columns={'STOCHk_9_3_3': 'K', 'STOCHd_9_3_3': 'D'}, inplace=True)

    # --- 4. 判斷均線與 KD 交叉 ---
    # .shift(1) 可以取得前一天的數據
    for col in ['MA5', 'MA20', 'K', 'D']:
        stock_data[f'{col}_yesterday'] = stock_data[col].shift(1)

    # 判斷 5MA 和 20MA 的黃金交叉
    stock_data['Golden_Cross_5_20'] = (stock_data['MA5'] > stock_data['MA20']) & \
                                      (stock_data['MA5_yesterday'] < stock_data['MA20_yesterday'])
    
    # 判斷 5MA 和 20MA 的死亡交叉
    stock_data['Death_Cross_5_20'] = (stock_data['MA5'] < stock_data['MA20']) & \
                                     (stock_data['MA5_yesterday'] > stock_data['MA20_yesterday'])
    
    # 判斷 KD 黃金交叉
    stock_data['Golden_Cross_KD'] = (stock_data['K'] > stock_data['D']) & \
                                    (stock_data['K_yesterday'] < stock_data['D_yesterday'])

    # 判斷 KD 死亡交叉
    stock_data['Death_Cross_KD'] = (stock_data['K'] < stock_data['D']) & \
                                   (stock_data['K_yesterday'] > stock_data['D_yesterday'])

    print(f"===== {ticker} 技術分析完成！ =====")
    return stock_data

# --- 主程式執行 ---
if __name__ == "__main__":
    stock_ticker = "2330.TW"
    tsmc_data = analyze_stock_technicals(stock_ticker)

    if tsmc_data is not None:
        latest_row = tsmc_data.iloc[-1]
        
        # --- 顯示最新數據摘要 ---
        print("\n--- 最新數據摘要 ---")
        print(f"股票代號: {stock_ticker}")
        print(f"最新收盤價: {latest_row['Close']:.2f}")
        print(f"5日均線 (MA5): {latest_row['MA5']:.2f}")
        print(f"20日均線 (MA20): {latest_row['MA20']:.2f}")
        print(f"K值: {latest_row['K']:.2f}")
        print(f"D值: {latest_row['D']:.2f}")
        print("--------------------")

        # --- 顯示 MA 交叉訊號 ---
        print("\n過去一年內發生的【5-20日均線 黃金交叉】：")
        print(tsmc_data[tsmc_data['Golden_Cross_5_20']][['Close', 'MA5', 'MA20']] if not tsmc_data[tsmc_data['Golden_Cross_5_20']].empty else "沒有發生黃金交叉。")
        
        print("\n過去一年內發生的【5-20日均線 死亡交叉】：")
        print(tsmc_data[tsmc_data['Death_Cross_5_20']][['Close', 'MA5', 'MA20']] if not tsmc_data[tsmc_data['Death_Cross_5_20']].empty else "沒有發生死亡交叉。")

        # --- 顯示 KD 交叉訊號 ---
        print("\n過去一年內發生的【KD 黃金交叉】：")
        print(tsmc_data[tsmc_data['Golden_Cross_KD']][['Close', 'K', 'D']] if not tsmc_data[tsmc_data['Golden_Cross_KD']].empty else "沒有發生KD黃金交叉。")

        print("\n過去一年內發生的【KD 死亡交叉】：")
        print(tsmc_data[tsmc_data['Death_Cross_KD']][['Close', 'K', 'D']] if not tsmc_data[tsmc_data['Death_Cross_KD']].empty else "沒有發生KD死亡交叉。")