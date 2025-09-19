import yfinance as yf
import pandas as pd

# 設定 Pandas 顯示選項，讓輸出的表格更整齊
pd.set_option('display.expand_frame_repr', False)

def analyze_stock_technicals(ticker, period="1y"):
    """
    獲取並分析指定股票的技術數據，包含 MA 計算與交叉判斷。

    :param ticker: 股票代號，台股需要加上 .TW
    :param period: 獲取數據的時間範圍
    :return: 包含完整技術分析數據的 DataFrame
    """
    print(f"===== 開始分析 {ticker} 的技術數據... =====")
    
    # 1. 獲取股價數據
    stock_data = yf.download(ticker, period=period, interval="1d")

    if stock_data.empty:
        print(f"錯誤：無法獲取 {ticker} 的數據，請檢查股票代號是否正確。")
        return None

    # 2. 計算移動平均線 (MA)
    stock_data['MA5'] = stock_data['Close'].rolling(window=5).mean()
    stock_data['MA20'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['MA60'] = stock_data['Close'].rolling(window=60).mean()

    # --- 3. 判斷均線交叉 ---
    # 我們需要昨天的數據來判斷是否發生 "穿越"
    # .shift(1) 可以取得前一天的數據
    stock_data['MA5_yesterday'] = stock_data['MA5'].shift(1)
    stock_data['MA20_yesterday'] = stock_data['MA20'].shift(1)

    # 判斷 5MA 和 20MA 的黃金交叉
    stock_data['Golden_Cross_5_20'] = (stock_data['MA5'] > stock_data['MA20']) & \
                                      (stock_data['MA5_yesterday'] < stock_data['MA20_yesterday'])
    
    # 判斷 5MA 和 20MA 的死亡交叉
    stock_data['Death_Cross_5_20'] = (stock_data['MA5'] < stock_data['MA20']) & \
                                     (stock_data['MA5_yesterday'] > stock_data['MA20_yesterday'])

    print(f"===== {ticker} 技術分析完成！ =====")
    return stock_data

# --- 主程式執行 ---
if __name__ == "__main__":
    stock_ticker = "2330.TW"
    
    # 呼叫函式進行分析
    tsmc_data = analyze_stock_technicals(stock_ticker)

    if tsmc_data is not None:
        # --- 顯示最新數據 ---
        print("\n--- 最新數據摘要 ---")
        latest_data = tsmc_data.iloc[-1]
        print(f"股票代號: {stock_ticker}")
        print(f"最新收盤價: {latest_data['Close']:.2f}")
        print(f"5日均線 (MA5): {latest_data['MA5']:.2f}")
        print(f"20日均線 (MA20): {latest_data['MA20']:.2f}")
        print("--------------------")

        # --- 顯示交叉訊號 ---
        golden_crosses = tsmc_data[tsmc_data['Golden_Cross_5_20']]
        death_crosses = tsmc_data[tsmc_data['Death_Cross_5_20']]

        print("\n過去一年內發生的【5-20日均線 黃金交叉】：")
        if golden_crosses.empty:
            print("沒有發生黃金交叉。")
        else:
            print(golden_crosses[['Close', 'MA5', 'MA20']])

        print("\n過去一年內發生的【5-20日均線 死亡交叉】：")
        if death_crosses.empty:
            print("沒有發生死亡交叉。")
        else:
            print(death_crosses[['Close', 'MA5', 'MA20']])