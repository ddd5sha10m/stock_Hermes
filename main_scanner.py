# main_scanner.py

import pandas as pd
from datetime import datetime
import time

# 從我們自訂的模組中，匯入需要的函式和資料
from stock_list import STOCK_LIST
from technical_analyzer import analyze_stock_technicals
from main import calculate_technical_score # 直接從舊的 main.py 匯入評分函式
from trading_signals import TradingSignalGenerator # 匯入交易訊號產生器

def run_full_analysis_for_stock(stock_code: str, stock_name: str):
    """
    對單一股票執行完整的技術分析、評分與訊號生成
    """
    stock_ticker = f"{stock_code}.TW"
    
    # 執行技術分析
    tech_data = analyze_stock_technicals(stock_ticker)
    
    if tech_data is None or tech_data.empty:
        # print(f"無法獲取 {stock_code} 的數據，跳過分析。")
        return None

    # 計算技術分數
    technical_score, scoring_details = calculate_technical_score(tech_data)
    
    # 產生交易訊號
    signal_generator = TradingSignalGenerator()
    trading_signal = signal_generator.generate_signal(tech_data, technical_score)
    
    # 回傳一個簡潔的結果字典
    return {
        "代號": stock_code,
        "名稱": stock_name,
        "評分": technical_score,
        "訊號": trading_signal.signal_type,
        "信心度": f"{trading_signal.confidence:.0f}%",
        "訊號理由": trading_signal.reasons[0] # 只取第一個最重要的理由
    }

# --- 主程式執行 ---
if __name__ == "__main__":
    start_time = time.time()
    
    # 存放所有股票的分析結果
    all_results = []

    # 遍歷股票清單
    total_stocks = len(STOCK_LIST)
    for i, (stock_code, stock_name) in enumerate(STOCK_LIST.items(), 1):
        
        print(f"[{i}/{total_stocks}] 正在分析: {stock_code} {stock_name}...")
        
        try:
            # 對每一支股票執行完整分析
            result = run_full_analysis_for_stock(stock_code, stock_name)
            
            # 如果分析成功，將結果加入列表
            if result:
                all_results.append(result)
                
        except Exception as e:
            print(f"!!! 分析 {stock_code} {stock_name} 時發生未預期的錯誤: {e}")
            continue # 即使單一股票失敗，也要繼續分析下一支
            
    print("\n\n===== 所有股票分析完成！開始進行排序與報告生成... =====")

    # 將結果列表轉換為 Pandas DataFrame
    results_df = pd.DataFrame(all_results)
    
    # 根據「評分」進行降序排序
    ranked_df = results_df.sort_values(by="評分", ascending=False)
    
    # 選出前 50 名
    top_50_df = ranked_df.head(50)

    # --- 產生最終報告 ---
    
    # 1. 在終端機印出 Top 50 排行榜
    print("\n\n==================================================")
    print(f"      投資荷密斯 Top 50 技術面強勢股排行榜")
    print(f"      掃描時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("==================================================")
    
    # 為了美觀，設定 pandas 的顯示選項
    pd.set_option('display.unicode.east_asian_width', True)
    # 將 DataFrame 的索引設為排名 (從 1 開始)
    top_50_df.index = range(1, len(top_50_df) + 1)
    print(top_50_df)
    
    # 2. 將 Top 50 結果儲存為 CSV 檔案
    today_str = datetime.now().strftime('%Y-%m-%d')
    csv_filename = f"top_50_scan_result_{today_str}.csv"
    
    try:
        top_50_df.to_csv(csv_filename, index_label="排名", encoding='utf-8-sig')
        print(f"\n\n>>> Top 50 結果已成功儲存至檔案: {csv_filename}")
    except Exception as e:
        print(f"\n\n>>> 儲存 CSV 檔案失敗: {e}")
        
    end_time = time.time()
    print(f"\n--- 本次掃描共耗時: {end_time - start_time:.2f} 秒 ---")